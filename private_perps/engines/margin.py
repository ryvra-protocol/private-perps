from __future__ import annotations

from dataclasses import dataclass

from private_perps.adapters.asset_registry import AssetRegistryAdapter
from private_perps.models import TradeIntent


@dataclass(frozen=True)
class MarginResult:
    is_sufficient: bool
    required_initial_margin: float
    maintenance_margin: float
    risk_flag: str


class MarginEngine:
    def __init__(self, asset_registry: AssetRegistryAdapter):
        self._asset_registry = asset_registry

    def evaluate(self, intent: TradeIntent) -> MarginResult:
        metadata = self._asset_registry.get_collateral_metadata(intent.collateral_asset)
        notional = intent.size * intent.entry_price
        required = notional * metadata.initial_margin_ratio
        maintenance = notional * metadata.maintenance_margin_ratio
        sufficient = intent.collateral >= required
        risk_flag = "LOW" if sufficient else "LIQUIDATION_RISK"
        return MarginResult(
            is_sufficient=sufficient,
            required_initial_margin=required,
            maintenance_margin=maintenance,
            risk_flag=risk_flag,
        )
