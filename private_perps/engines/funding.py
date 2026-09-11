from __future__ import annotations


class FundingEngine:
    def compute_delta(self, *, side: str, size: float, mark_price: float, funding_rate_per_interval: float) -> float:
        if side.upper() == "LONG":
            sign = -1.0
        elif side.upper() == "SHORT":
            sign = 1.0
        else:
            raise ValueError("UNSUPPORTED_SIDE")
        return sign * size * mark_price * funding_rate_per_interval
