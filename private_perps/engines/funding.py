from __future__ import annotations


class FundingEngine:
    def compute_delta(self, *, size: float, mark_price: float, funding_rate_per_interval: float) -> float:
        return size * mark_price * funding_rate_per_interval
