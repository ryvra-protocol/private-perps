from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PrivacyMode(str, Enum):
    CONFIDENTIAL = "CONFIDENTIAL"
    PRIVATE = "PRIVATE"


class ExecutionMode(str, Enum):
    PRIVATE = "PRIVATE"
    CONFIDENTIAL = "CONFIDENTIAL"


class LifecycleStage(str, Enum):
    INTENT_RECEIVED = "INTENT_RECEIVED"
    AUTHORITY_VALIDATED = "AUTHORITY_VALIDATED"
    MARGIN_VALIDATED = "MARGIN_VALIDATED"
    POSITION_RESERVED = "POSITION_RESERVED"
    ORDER_ACCEPTED = "ORDER_ACCEPTED"
    ORDER_MATCHED = "ORDER_MATCHED"
    EXECUTED = "EXECUTED"
    PROOF_GENERATED = "PROOF_GENERATED"
    PROOF_VERIFIED = "PROOF_VERIFIED"
    SETTLEMENT_PREPARED = "SETTLEMENT_PREPARED"
    SETTLED = "SETTLED"
    RECONCILED = "RECONCILED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    PROOF_FAILED = "PROOF_FAILED"
    ORACLE_INVALID = "ORACLE_INVALID"
    MARGIN_INSUFFICIENT = "MARGIN_INSUFFICIENT"
    PARTIAL = "PARTIAL"
    DISPUTED = "DISPUTED"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class AuthorityRefs:
    actorType: str
    actorId: str
    agentId: str
    mandateId: str
    riskAssessmentId: str
    authorizationId: str
    policyVersion: str
    policyHash: str
    intentId: str
    correlationId: str
    idempotencyKey: str
    privacyMode: PrivacyMode
    executionMode: ExecutionMode

    def missing_fields(self) -> list[str]:
        missing: list[str] = []
        for key, value in self.__dict__.items():
            if value is None or (isinstance(value, str) and value.strip() == ""):
                missing.append(key)
        return missing


@dataclass(frozen=True)
class TradeIntent:
    order_id: str
    account_id: str
    market: str
    side: str
    size: float
    leverage: float
    collateral: float
    entry_price: float
    collateral_asset: str
    authority: AuthorityRefs
    requires_proof: bool = True


@dataclass(frozen=True)
class OracleObservation:
    oracle_id: str
    market: str
    price: float
    confidence: float
    min_confidence: float
    staleness_ms: int
    max_staleness_ms: int
    source: str
    fallback_used: bool = False
    fallback_allowed: bool = True
    observed_at: datetime = field(default_factory=utcnow)


@dataclass(frozen=True)
class ProofVerificationResult:
    proof_id: str
    verifier: str
    status: VerificationStatus
    reason_code: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PositionTransition:
    position_id: str
    account_id: str
    order_id: str
    commitment_hash: str
    version_ref: str
    lifecycle_stage: LifecycleStage
    created_at: datetime = field(default_factory=utcnow)


@dataclass(frozen=True)
class SettlementRecord:
    settlement_id: str
    order_id: str
    account_id: str
    position_id: str
    settlement_delta: float
    intent_id: str
    mandate_id: str
    risk_assessment_id: str
    authorization_id: str
    policy_version: str
    policy_hash: str
    proof_id: str | None
    proof_status: str | None
    commitment_hash: str
    created_at: datetime = field(default_factory=utcnow)
