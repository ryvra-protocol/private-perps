from __future__ import annotations

from private_perps.models import AuthorityRefs, SettlementRecord


class SettlementAdapter:
    """Adapter boundary for ledger-settlement handoff."""

    def prepare_record(
        self,
        *,
        settlement_id: str,
        order_id: str,
        account_id: str,
        position_id: str,
        settlement_delta: float,
        authority: AuthorityRefs,
        commitment_hash: str,
        proof_id: str | None,
        proof_status: str | None,
    ) -> SettlementRecord:
        return SettlementRecord(
            settlement_id=settlement_id,
            order_id=order_id,
            account_id=account_id,
            position_id=position_id,
            settlement_delta=settlement_delta,
            intent_id=authority.intentId,
            mandate_id=authority.mandateId,
            risk_assessment_id=authority.riskAssessmentId,
            authorization_id=authority.authorizationId,
            policy_version=authority.policyVersion,
            policy_hash=authority.policyHash,
            proof_id=proof_id,
            proof_status=proof_status,
            commitment_hash=commitment_hash,
        )
