"""
NEOMA P-CAM x Hummingbot Market-Making Toxic Flow & Spread Guard
-----------------------------------------------------------------
Drop-in co-processor helper for Hummingbot ScriptStrategyBase / PMM loops.
Maps live L1/L2 order book pressure into P-CAM silicon equilibrium control
to widen spreads or pause quoting before toxic order flow sweeps inventory.
"""

import os
import requests
from dataclasses import dataclass


@dataclass
class QuoteAdjustment:
    bid_spread_multiplier: float
    ask_spread_multiplier: float
    halt_quoting: bool
    zeta: float
    hardware_reflex_ms: float
    hardware_seal_id: str


class PCAMHummingbotGuard:
    def __init__(self, rapidapi_key: str | None = None):
        self.api_key = rapidapi_key or os.getenv("PCAM_RAPIDAPI_KEY", "YOUR_RAPIDAPI_KEY")
        self.endpoint = "[https://neoma-p-cam-hyper-physical-control.p.rapidapi.com/v1/quant/predict](https://neoma-p-cam-hyper-physical-control.p.rapidapi.com/v1/quant/predict)"
        self.headers = {
            "Content-Type": "application/json",
            "x-rapidapi-host": "neoma-p-cam-hyper-physical-control.p.rapidapi.com",
            "x-rapidapi-key": self.api_key,
        }

    def evaluate_order_book(
        self,
        bid_depth: float,
        ask_depth: float,
        mid_price_velocity: float,
        flow_acceleration: float,
        inventory_skew: float,
    ) -> QuoteAdjustment:
        """
        Parameters:
            bid_depth / ask_depth : Top-of-book liquidity volume
            mid_price_velocity    : Short-window mid-price rate of change
            flow_acceleration     : Second derivative of order flow / trade intensity
            inventory_skew        : Normalized inventory deviation [-1.0, 1.0]
        """
        total_depth = max(bid_depth + ask_depth, 1e-9)
        imbalance = (bid_depth - ask_depth) / total_depth  # [-1, 1]

        payload = {
            "flux_potential_v": round(1.0 + abs(imbalance) * 1.5, 4),
            "gradient_velocity": round(abs(mid_price_velocity), 4),
            "gradient_acceleration": round(abs(flow_acceleration), 4),
            "active_strain": round(abs(inventory_skew), 4),
        }

        res = requests.post(self.endpoint, json=payload, headers=self.headers, timeout=2.0)
        res.raise_for_status()
        out = res.json()

        zeta = float(out.get("zeta", 1.0))
        intensity = float(out.get("control_intensity", 0.0))
        converged = bool(out.get("equilibrium_converged", True))

        # Dynamic spread widening & directional skew protection
        base_mult = 1.0 + (intensity * 2.5)
        bid_mult = base_mult * (1.25 if imbalance < -0.2 else 1.0)
        ask_mult = base_mult * (1.25 if imbalance > 0.2 else 1.0)

        return QuoteAdjustment(
            bid_spread_multiplier=round(bid_mult, 3),
            ask_spread_multiplier=round(ask_mult, 3),
            halt_quoting=(not converged or intensity > 0.85),
            zeta=zeta,
            hardware_reflex_ms=float(out.get("hardware_reflex_ms", 0.0)),
            hardware_seal_id=str(out.get("hardware_seal_id", "")),
        )


if __name__ == "__main__":
    # Simulated Hummingbot tick callback
    guard = PCAMHummingbotGuard()
    adj = guard.evaluate_order_book(
        bid_depth=12.4,
        ask_depth=48.9,          # Heavy sell-side pressure
        mid_price_velocity=-0.38,
        flow_acceleration=11.2,
        inventory_skew=0.35,
    )
    print("Hummingbot Quote Adjustment:", adj)