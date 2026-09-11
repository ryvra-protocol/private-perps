from __future__ import annotations

from private_perps.models import OracleObservation


class OracleValidationError(ValueError):
    pass


class OracleAdapter:
    """Deterministic oracle confidence/staleness/fallback validation."""

    def validate(self, observation: OracleObservation) -> None:
        if observation.confidence < observation.min_confidence:
            raise OracleValidationError("ORACLE_LOW_CONFIDENCE")
        if observation.staleness_ms > observation.max_staleness_ms:
            raise OracleValidationError("ORACLE_STALE")
        if observation.fallback_used and not observation.fallback_allowed:
            raise OracleValidationError("ORACLE_FALLBACK_NOT_ALLOWED")
