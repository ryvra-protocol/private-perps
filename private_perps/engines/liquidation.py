from __future__ import annotations

from dataclasses import dataclass

from private_perps.engines.margin import MarginResult
from private_perps.models import ProofVerificationResult, VerificationStatus


@dataclass(frozen=True)
class LiquidationDecision:
    should_liquidate: bool
    reason_code: str


class LiquidationEngine:
    def evaluate(self, *, margin_result: MarginResult, proof_result: ProofVerificationResult | None) -> LiquidationDecision:
        if margin_result.is_sufficient:
            return LiquidationDecision(False, "MARGIN_OK")
        if proof_result is None:
            return LiquidationDecision(False, "PROOF_REQUIRED")
        if proof_result.status != VerificationStatus.VERIFIED:
            return LiquidationDecision(False, "PROOF_INVALID")
        return LiquidationDecision(True, "LIQUIDATION_TRIGGERED")
