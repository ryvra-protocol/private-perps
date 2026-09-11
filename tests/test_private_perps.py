from __future__ import annotations

import unittest

from private_perps.adapters.asset_registry import AssetRegistryAdapter
from private_perps.adapters.confidential_compute import InMemoryPrivateExecutionAdapter
from private_perps.adapters.oracle import OracleAdapter
from private_perps.adapters.settlement import SettlementAdapter
from private_perps.adapters.zk_proof import ZKProofAdapter
from private_perps.engines.funding import FundingEngine
from private_perps.engines.liquidation import LiquidationEngine
from private_perps.engines.margin import MarginEngine
from private_perps.engines.position import PositionEngine
from private_perps.gateway import PrivateOrderGateway
from private_perps.models import AuthorityRefs, ExecutionMode, LifecycleStage, OracleObservation, PrivacyMode, TradeIntent
from private_perps.storage.encrypted_position_store import EncryptedPositionStore


class PrivatePerpsPhase9Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.compute = InMemoryPrivateExecutionAdapter()
        self.store = EncryptedPositionStore(self.compute)
        self.gateway = PrivateOrderGateway(
            position_engine=PositionEngine(self.store),
            margin_engine=MarginEngine(AssetRegistryAdapter()),
            funding_engine=FundingEngine(),
            liquidation_engine=LiquidationEngine(),
            oracle_adapter=OracleAdapter(),
            proof_adapter=ZKProofAdapter(accepted_proofs={"proof-ok"}),
            settlement_adapter=SettlementAdapter(),
            policy_hashes_by_version={"v1": "hash-v1"},
        )

    @staticmethod
    def authority(**kwargs):
        base = dict(
            actorType="TRADER",
            actorId="actor-1",
            agentId="agent-1",
            mandateId="mandate-1",
            riskAssessmentId="risk-1",
            authorizationId="auth-1",
            policyVersion="v1",
            policyHash="hash-v1",
            intentId="intent-1",
            correlationId="corr-1",
            idempotencyKey="idem-1",
            privacyMode=PrivacyMode.CONFIDENTIAL,
            executionMode=ExecutionMode.CONFIDENTIAL,
        )
        base.update(kwargs)
        return AuthorityRefs(**base)

    def intent(self, **kwargs):
        base = dict(
            order_id="ord-1",
            account_id="acct-1",
            market="BTC-PERP",
            side="LONG",
            size=1.0,
            leverage=5.0,
            collateral=8000.0,
            entry_price=50000.0,
            collateral_asset="USDC",
            authority=self.authority(),
            requires_proof=True,
        )
        base.update(kwargs)
        return TradeIntent(**base)

    @staticmethod
    def oracle(**kwargs):
        base = dict(
            oracle_id="oracle-1",
            market="BTC-PERP",
            price=50000.0,
            confidence=0.99,
            min_confidence=0.95,
            staleness_ms=100,
            max_staleness_ms=500,
            source="primary",
            fallback_used=False,
            fallback_allowed=True,
        )
        base.update(kwargs)
        return OracleObservation(**base)

    def test_confidential_order_flow_valid(self):
        result = self.gateway.process_confidential_order(
            intent=self.intent(),
            oracle_observation=self.oracle(),
            proof_id="proof-ok",
            funding_rate_per_interval=0.0001,
        )
        self.assertEqual(result.status, LifecycleStage.SETTLEMENT_PREPARED)
        self.assertIn(LifecycleStage.AUTHORITY_VALIDATED, result.stages)
        self.assertIn(LifecycleStage.PROOF_VERIFIED, result.stages)
        self.assertTrue(result.position_id)
        self.assertTrue(result.commitment_hash)
        self.assertEqual(result.settlement_delta, -1.0 * 50000.0 * 0.0001)

    def test_funding_delta_side_dependent(self):
        short_result = self.gateway.process_confidential_order(
            intent=self.intent(order_id="ord-short", side="SHORT"),
            oracle_observation=self.oracle(),
            proof_id="proof-ok",
            funding_rate_per_interval=0.0001,
        )
        self.assertEqual(short_result.status, LifecycleStage.SETTLEMENT_PREPARED)
        self.assertEqual(short_result.settlement_delta, 1.0 * 50000.0 * 0.0001)

    def test_missing_authority_rejected(self):
        bad_intent = self.intent(authority=self.authority(mandateId=""))
        result = self.gateway.process_confidential_order(
            intent=bad_intent,
            oracle_observation=self.oracle(),
            proof_id="proof-ok",
            funding_rate_per_interval=0.0001,
        )
        self.assertEqual(result.status, LifecycleStage.REJECTED)
        self.assertIn("AUTHORITY_MISSING", result.rejection_reason)

    def test_policy_mismatch_rejected(self):
        bad_intent = self.intent(authority=self.authority(policyHash="wrong"))
        result = self.gateway.process_confidential_order(
            intent=bad_intent,
            oracle_observation=self.oracle(),
            proof_id="proof-ok",
            funding_rate_per_interval=0.0001,
        )
        self.assertEqual(result.status, LifecycleStage.REJECTED)
        self.assertEqual(result.rejection_reason, "POLICY_MISMATCH")

    def test_unsupported_privacy_mode_rejected(self):
        # Simulate untyped mode by object with invalid .value
        authority = self.authority()
        object.__setattr__(authority, "privacyMode", type("BadMode", (), {"value": "PUBLIC"})())
        bad_intent = self.intent(authority=authority)
        result = self.gateway.process_confidential_order(
            intent=bad_intent,
            oracle_observation=self.oracle(),
            proof_id="proof-ok",
            funding_rate_per_interval=0.0001,
        )
        self.assertEqual(result.status, LifecycleStage.REJECTED)
        self.assertEqual(result.rejection_reason, "UNSUPPORTED_PRIVACY_MODE")

    def test_private_mode_rejected_for_confidential_gateway(self):
        bad_intent = self.intent(authority=self.authority(privacyMode=PrivacyMode.PRIVATE))
        result = self.gateway.process_confidential_order(
            intent=bad_intent,
            oracle_observation=self.oracle(),
            proof_id="proof-ok",
            funding_rate_per_interval=0.0001,
        )
        self.assertEqual(result.status, LifecycleStage.REJECTED)
        self.assertEqual(result.rejection_reason, "UNSUPPORTED_PRIVACY_MODE")

    def test_insufficient_margin_rejected(self):
        result = self.gateway.process_confidential_order(
            intent=self.intent(collateral=100.0),
            oracle_observation=self.oracle(),
            proof_id="proof-ok",
            funding_rate_per_interval=0.0001,
        )
        self.assertEqual(result.status, LifecycleStage.MARGIN_INSUFFICIENT)
        self.assertIsNotNone(result.liquidation_decision)
        self.assertTrue(result.liquidation_decision.should_liquidate)

    def test_unsupported_collateral_rejected(self):
        result = self.gateway.process_confidential_order(
            intent=self.intent(collateral_asset="UNKNOWN"),
            oracle_observation=self.oracle(),
            proof_id="proof-ok",
            funding_rate_per_interval=0.0001,
        )
        self.assertEqual(result.status, LifecycleStage.REJECTED)
        self.assertEqual(result.rejection_reason, "UNSUPPORTED_COLLATERAL_ASSET")

    def test_invalid_proof_rejected(self):
        result = self.gateway.process_confidential_order(
            intent=self.intent(),
            oracle_observation=self.oracle(),
            proof_id="proof-bad",
            funding_rate_per_interval=0.0001,
        )
        self.assertEqual(result.status, LifecycleStage.PROOF_FAILED)
        self.assertEqual(result.rejection_reason, "PROOF_INVALID")
        self.assertEqual(self.store.get_history("pos-acct-1-BTC-PERP"), [])

    def test_proof_required_blocked_without_proof(self):
        result = self.gateway.process_confidential_order(
            intent=self.intent(),
            oracle_observation=self.oracle(),
            proof_id=None,
            funding_rate_per_interval=0.0001,
        )
        self.assertEqual(result.status, LifecycleStage.PROOF_FAILED)
        self.assertEqual(result.rejection_reason, "PROOF_REQUIRED")
        self.assertEqual(self.store.get_history("pos-acct-1-BTC-PERP"), [])

    def test_stale_oracle_rejected(self):
        result = self.gateway.process_confidential_order(
            intent=self.intent(),
            oracle_observation=self.oracle(staleness_ms=1000),
            proof_id="proof-ok",
            funding_rate_per_interval=0.0001,
        )
        self.assertEqual(result.status, LifecycleStage.ORACLE_INVALID)
        self.assertEqual(result.rejection_reason, "ORACLE_STALE")

    def test_low_confidence_oracle_rejected(self):
        result = self.gateway.process_confidential_order(
            intent=self.intent(),
            oracle_observation=self.oracle(confidence=0.5),
            proof_id="proof-ok",
            funding_rate_per_interval=0.0001,
        )
        self.assertEqual(result.status, LifecycleStage.ORACLE_INVALID)
        self.assertEqual(result.rejection_reason, "ORACLE_LOW_CONFIDENCE")

    def test_fallback_handling_rejected(self):
        result = self.gateway.process_confidential_order(
            intent=self.intent(),
            oracle_observation=self.oracle(fallback_used=True, fallback_allowed=False),
            proof_id="proof-ok",
            funding_rate_per_interval=0.0001,
        )
        self.assertEqual(result.status, LifecycleStage.ORACLE_INVALID)
        self.assertEqual(result.rejection_reason, "ORACLE_FALLBACK_NOT_ALLOWED")

    def test_sensitive_fields_encrypted_and_unauthorized_denied(self):
        result = self.gateway.process_confidential_order(
            intent=self.intent(),
            oracle_observation=self.oracle(),
            proof_id="proof-ok",
            funding_rate_per_interval=0.0001,
        )
        version = self.store.get_latest(result.position_id)
        self.assertIsNotNone(version)
        self.assertNotIn("50000", version.ciphertext)
        with self.assertRaises(PermissionError):
            self.store.decrypt_version(version, authorization_id="auth-other")

    def test_reconciliation_traceable_refs(self):
        result = self.gateway.process_confidential_order(
            intent=self.intent(),
            oracle_observation=self.oracle(),
            proof_id="proof-ok",
            funding_rate_per_interval=0.0001,
        )
        self.assertEqual(result.status, LifecycleStage.SETTLEMENT_PREPARED)
        self.assertTrue(result.settlement_id.startswith("set-"))


if __name__ == "__main__":
    unittest.main()
