from __future__ import annotations

from dataclasses import dataclass

from private_perps.models import LifecycleStage, PositionTransition, TradeIntent
from private_perps.storage.encrypted_position_store import EncryptedPositionStore


@dataclass(frozen=True)
class PositionEngineResult:
    transition: PositionTransition


class PositionEngine:
    def __init__(self, position_store: EncryptedPositionStore):
        self._position_store = position_store

    def open_or_adjust(self, intent: TradeIntent) -> PositionEngineResult:
        payload = {
            "position_id": f"pos-{intent.account_id}-{intent.market}",
            "account_id": intent.account_id,
            "order_id": intent.order_id,
            "market": intent.market,
            "side": intent.side,
            "size": intent.size,
            "leverage": intent.leverage,
            "collateral": intent.collateral,
            "entry_price": intent.entry_price,
            "liquidation_threshold": intent.entry_price * (1 - (1 / (intent.leverage + 1))),
        }
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
