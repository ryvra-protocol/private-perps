from __future__ import annotations

from dataclasses import dataclass

from private_perps.adapters.oracle import OracleAdapter, OracleValidationError
from private_perps.adapters.settlement import SettlementAdapter
from private_perps.adapters.zk_proof import ZKProofAdapter
from private_perps.engines.funding import FundingEngine
from private_perps.engines.liquidation import LiquidationDecision, LiquidationEngine
from private_perps.engines.margin import MarginEngine, MarginResult
from private_perps.engines.position import PositionEngine, PositionEngineResult
from private_perps.models import LifecycleStage, OracleObservation, ProofVerificationResult, TradeIntent, VerificationStatus


@dataclass(frozen=True)
class GatewayResult:
    order_id: str
    status: LifecycleStage
    stages: list[LifecycleStage]
    position_id: str | None = None
    commitment_hash: str | None = None
    settlement_id: str | None = None
    settlement_delta: float | None = None
    rejection_reason: str | None = None
    proof_result: ProofVerificationResult | None = None
    liquidation_decision: LiquidationDecision | None = None


class PrivateOrderGateway:
    def __init__(
        self,
        *,
        position_engine: PositionEngine,
        margin_engine: MarginEngine,
        funding_engine: FundingEngine,
        liquidation_engine: LiquidationEngine,
        oracle_adapter: OracleAdapter,
        proof_adapter: ZKProofAdapter,
        settlement_adapter: SettlementAdapter,
        policy_hashes_by_version: dict[str, str],
    ):
        self._position_engine = position_engine
        self._margin_engine = margin_engine
        self._funding_engine = funding_engine
        self._liquidation_engine = liquidation_engine
        self._oracle_adapter = oracle_adapter
        self._proof_adapter = proof_adapter
        self._settlement_adapter = settlement_adapter
        self._policy_hashes_by_version = policy_hashes_by_version

    def _validate_authority(self, intent: TradeIntent) -> None:
        missing = intent.authority.missing_fields()
        if missing:
            raise ValueError(f"AUTHORITY_MISSING:{','.join(sorted(missing))}")
        privacy_mode = getattr(intent.authority.privacyMode, "value", None)
        execution_mode = getattr(intent.authority.executionMode, "value", None)
        if privacy_mode != "CONFIDENTIAL":
            raise ValueError("UNSUPPORTED_PRIVACY_MODE")
        if execution_mode != "CONFIDENTIAL":
            raise ValueError("UNSUPPORTED_EXECUTION_MODE")
        expected_hash = self._policy_hashes_by_version.get(intent.authority.policyVersion)
        if expected_hash is None or expected_hash != intent.authority.policyHash:
            raise ValueError("POLICY_MISMATCH")

    def process_confidential_order(
        self,
        *,
        intent: TradeIntent,
        oracle_observation: OracleObservation,
        proof_id: str | None,
        funding_rate_per_interval: float,
    ) -> GatewayResult:
        stages: list[LifecycleStage] = [LifecycleStage.INTENT_RECEIVED]
        try:
            self._validate_authority(intent)
        except ValueError as exc:
            return GatewayResult(
                order_id=intent.order_id,
                status=LifecycleStage.REJECTED,
                stages=stages + [LifecycleStage.REJECTED],
                rejection_reason=str(exc),
            )
        stages.append(LifecycleStage.AUTHORITY_VALIDATED)

        try:
            self._oracle_adapter.validate(oracle_observation)
        except OracleValidationError as exc:
            return GatewayResult(
                order_id=intent.order_id,
                status=LifecycleStage.ORACLE_INVALID,
                stages=stages + [LifecycleStage.ORACLE_INVALID],
                rejection_reason=str(exc),
            )
        if oracle_observation.market != intent.market:
            return GatewayResult(
                order_id=intent.order_id,
                status=LifecycleStage.ORACLE_INVALID,
                stages=stages + [LifecycleStage.ORACLE_INVALID],
                rejection_reason="ORACLE_MARKET_MISMATCH",
            )

        try:
            margin: MarginResult = self._margin_engine.evaluate(intent)
        except ValueError as exc:
            return GatewayResult(
                order_id=intent.order_id,
                status=LifecycleStage.REJECTED,
                stages=stages + [LifecycleStage.REJECTED],
                rejection_reason=str(exc),
            )
        if not margin.is_sufficient:
            liquidation_proof_result = None
            if intent.requires_proof:
                if proof_id is None:
                    liquidation_proof_result = ProofVerificationResult(
                        proof_id="missing",
                        verifier=self._proof_adapter.verifier_name,
                        status=VerificationStatus.REJECTED,
                        reason_code="PROOF_REQUIRED",
                        metadata={"proof_type": "LIQUIDATION_SOLVENCY"},
                    )
                else:
                    liquidation_proof_result = self._proof_adapter.verify(
                        proof_id=proof_id,
                        proof_type="LIQUIDATION_SOLVENCY",
                        commitment_hash=f"margin:{intent.order_id}",
                    )
            liquidation_decision = self._liquidation_engine.evaluate(
                margin_result=margin,
                proof_result=liquidation_proof_result,
            )
            rejection_reason = (
                liquidation_proof_result.reason_code
                if liquidation_proof_result and liquidation_proof_result.status != VerificationStatus.VERIFIED
                else "MARGIN_INSUFFICIENT"
            )
            return GatewayResult(
                order_id=intent.order_id,
                status=LifecycleStage.MARGIN_INSUFFICIENT,
                stages=stages + [LifecycleStage.MARGIN_INSUFFICIENT],
                rejection_reason=rejection_reason,
                liquidation_decision=liquidation_decision,
                proof_result=liquidation_proof_result,
            )
        stages.append(LifecycleStage.MARGIN_VALIDATED)

        try:
            position_payload = self._position_engine.build_payload(intent)
        except ValueError as exc:
            return GatewayResult(
                order_id=intent.order_id,
                status=LifecycleStage.REJECTED,
                stages=stages + [LifecycleStage.REJECTED],
                rejection_reason=str(exc),
            )
        precomputed_commitment = self._position_engine.commitment_for_payload(position_payload)

        proof_result = None
        if intent.requires_proof:
            if proof_id is None:
                return GatewayResult(
                    order_id=intent.order_id,
                    status=LifecycleStage.PROOF_FAILED,
                    stages=stages + [LifecycleStage.PROOF_FAILED],
                    position_id=position_payload["position_id"],
                    commitment_hash=precomputed_commitment,
                    rejection_reason="PROOF_REQUIRED",
                )
            stages.append(LifecycleStage.PROOF_GENERATED)
            proof_result = self._proof_adapter.verify(
                proof_id=proof_id,
                proof_type="POSITION_TRANSITION",
                commitment_hash=precomputed_commitment,
            )
            if proof_result.status != VerificationStatus.VERIFIED:
                return GatewayResult(
                    order_id=intent.order_id,
                    status=LifecycleStage.PROOF_FAILED,
                    stages=stages + [LifecycleStage.PROOF_FAILED],
                    position_id=position_payload["position_id"],
                    commitment_hash=precomputed_commitment,
                    proof_result=proof_result,
                    rejection_reason=proof_result.reason_code,
                )
            stages.append(LifecycleStage.PROOF_VERIFIED)

        position_result: PositionEngineResult = self._position_engine.open_or_adjust(intent, payload=position_payload)
        stages.append(LifecycleStage.POSITION_RESERVED)
        stages.append(LifecycleStage.ORDER_ACCEPTED)
        stages.append(LifecycleStage.ORDER_MATCHED)
        stages.append(LifecycleStage.EXECUTED)

        try:
            funding_delta = self._funding_engine.compute_delta(
                side=intent.side,
                size=intent.size,
                mark_price=oracle_observation.price,
                funding_rate_per_interval=funding_rate_per_interval,
            )
        except ValueError as exc:
            return GatewayResult(
                order_id=intent.order_id,
                status=LifecycleStage.REJECTED,
                stages=stages + [LifecycleStage.REJECTED],
                rejection_reason=str(exc),
            )

        liquidation_decision = self._liquidation_engine.evaluate(margin_result=margin, proof_result=proof_result)

        settlement_id = f"set-{intent.order_id}"
        settlement_delta = funding_delta
        self._settlement_adapter.prepare_record(
            settlement_id=settlement_id,
            order_id=intent.order_id,
            account_id=intent.account_id,
            position_id=position_result.transition.position_id,
            settlement_delta=settlement_delta,
            authority=intent.authority,
            commitment_hash=position_result.transition.commitment_hash,
            proof_id=proof_result.proof_id if proof_result else None,
            proof_status=proof_result.status.value if proof_result else None,
        )
        stages.append(LifecycleStage.SETTLEMENT_PREPARED)

        return GatewayResult(
            order_id=intent.order_id,
            status=LifecycleStage.SETTLEMENT_PREPARED,
            stages=stages,
            position_id=position_result.transition.position_id,
            commitment_hash=position_result.transition.commitment_hash,
            settlement_id=settlement_id,
            settlement_delta=settlement_delta,
            proof_result=proof_result,
            liquidation_decision=liquidation_decision,
        )
