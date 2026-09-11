from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CollateralMetadata:
    initial_margin_ratio: float
    maintenance_margin_ratio: float


class AssetRegistryAdapter:
    """Adapter boundary for asset-registry collateral/margin metadata."""

    def __init__(self, metadata: dict[str, CollateralMetadata] | None = None):
        self._metadata = metadata or {
            "USDC": CollateralMetadata(initial_margin_ratio=0.1, maintenance_margin_ratio=0.06),
            "USDt": CollateralMetadata(initial_margin_ratio=0.12, maintenance_margin_ratio=0.08),
        }

    def get_collateral_metadata(self, collateral_asset: str) -> CollateralMetadata:
        if collateral_asset not in self._metadata:
            raise ValueError("UNSUPPORTED_COLLATERAL_ASSET")
        return self._metadata[collateral_asset]
