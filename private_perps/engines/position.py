from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from private_perps.models import LifecycleStage, PositionTransition, TradeIntent
from private_perps.storage.encrypted_position_store import EncryptedPositionStore


@dataclass(frozen=True)
class PositionEngineResult:
    transition: PositionTransition


class PositionEngine:
    def __init__(self, position_store: EncryptedPositionStore):
        self._position_store = position_store

    @staticmethod
    def build_payload(intent: TradeIntent) -> dict[str, float | str]:
        if intent.side.upper() == "LONG":
            liquidation_threshold = intent.entry_price * (1 - (1 / (intent.leverage + 1)))
        elif intent.side.upper() == "SHORT":
            liquidation_threshold = intent.entry_price * (1 + (1 / (intent.leverage + 1)))
        else:
            raise ValueError("UNSUPPORTED_SIDE")
        return {
            "position_id": f"pos-{intent.account_id}-{intent.market}",
            "account_id": intent.account_id,
            "order_id": intent.order_id,
            "market": intent.market,
            "side": intent.side,
            "size": intent.size,
            "leverage": intent.leverage,
            "collateral": intent.collateral,
            "entry_price": intent.entry_price,
            "liquidation_threshold": liquidation_threshold,
        }

    @staticmethod
    def commitment_for_payload(payload: dict[str, float | str]) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def open_or_adjust(
        self,
        intent: TradeIntent,
        *,
        payload: dict[str, float | str] | None = None,
    ) -> PositionEngineResult:
        payload = payload or self.build_payload(intent)
        version = self._position_store.append_encrypted_version(
            position_id=payload["position_id"],
            payload=payload,
            authorization_id=intent.authority.authorizationId,
        )
        transition = PositionTransition(
            position_id=payload["position_id"],
            account_id=intent.account_id,
            order_id=intent.order_id,
            commitment_hash=version.commitment_hash,
            version_ref=version.version_ref,
            lifecycle_stage=LifecycleStage.POSITION_RESERVED,
        )
        return PositionEngineResult(transition=transition)
