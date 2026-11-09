"""
NEOMA P-CAM Quant Microstructure SDK (v1.0.0)
=============================================
High-frequency Order Book (LOB) Shock Damping & Slippage Defense Shield.
Direct silicon reflex convergence via P-CAM 15µs physical core.
"""

import time
import requests
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

@dataclass
class ReflexSignal:
    status: str
    zeta: float
    action: str            # 'PULL_QUOTES', 'HOLD_MAKER', 'TAKER_BURST'
    should_cancel: bool    # True if toxic sweep detected (zeta > 1.2 or state_mode == 3)
    hardware_reflex_ms: float
    hardware_seal_id: str
    allocated_node: str
    cognition: str

class PCAMShockShield:
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        host: str = "gp-pcam-universal-physical-solver.p.rapidapi.com",
        endpoint_url: Optional[str] = None
    ):
        """
        :param api_key: RapidAPI Key (PRO / ULTRA / BASIC)
        :param endpoint_url: Custom or direct node URL (e.g., https://api.neoma-pcam.com/v1/quant/predict)
        """
        self.api_key = api_key
        if endpoint_url:
            self.endpoint = endpoint_url
            self.headers = {"Content-Type": "application/json"}
        elif api_key:
            self.endpoint = "https://neoma-p-cam-quant-reflex-hft.p.rapidapi.com/v1/quant/predict"
            self.headers = {
                "Content-Type": "application/json",
                "x-rapidapi-host": "neoma-p-cam-quant-reflex-hft.p.rapidapi.com",
                "x-rapidapi-key": self.api_key
            }
        else:
            # Fallback to direct public node
            self.endpoint = "https://api.neoma-pcam.com/v1/quant/predict"
            self.headers = {
                "Content-Type": "application/json",
                "User-Agent": "NEOMA-PCAM-CCXT-Shield/1.0"
            }
            
        # State tracking for derivatives (dP/dt, d^2P/dt^2)
        self.prev_time: Optional[float] = None
        self.prev_mid: Optional[float] = None
        self.prev_velocity: float = 0.0
        self.baseline_spread: Optional[float] = None

    def evaluate_lob_raw(
        self, 
        flux_potential_v: float, 
        gradient_velocity: float, 
        gradient_acceleration: float, 
        active_strain: float
    ) -> ReflexSignal:
        """Direct 4D tensor reflex dispatch."""
        payload = {
            "flux_potential_v": round(flux_potential_v, 4),
            "gradient_velocity": round(gradient_velocity, 2),
            "gradient_acceleration": round(gradient_acceleration, 2),
            "active_strain": round(active_strain, 3)
        }
        
        resp = requests.post(self.endpoint, json=payload, headers=self.headers, timeout=2.0)
        resp.raise_for_status()
        data = resp.json()

        zeta = data.get("zeta", 1.0)
        mode = data.get("state_mode", 1)
        
        # Trading decision logic mapped to physical damping ratio
        if zeta > 1.2 or mode == 3:
            action = "PULL_QUOTES"     # Toxic order sweep: cancel all passive limit orders
            should_cancel = True
        elif zeta < 0.8:
            action = "TAKER_BURST"     # Under-damped momentum breakthrough
            should_cancel = False
        else:
            action = "HOLD_MAKER"      # Critically damped: safe spread absorption
            should_cancel = False

        return ReflexSignal(
            status=data.get("status", "unknown"),
            zeta=zeta,
            action=action,
            should_cancel=should_cancel,
            hardware_reflex_ms=data.get("hardware_reflex_ms", 0.0),
            hardware_seal_id=data.get("hardware_seal_id", ""),
            allocated_node=data.get("telemetry", {}).get("allocated_fabric_node", ""),
            cognition=data.get("phi_embodied_cognition", "")
        )

    def evaluate_ccxt(self, order_book: Dict[str, Any], depth: int = 5) -> ReflexSignal:
        """
        Parses standard CCXT order book dict {'bids': [[price, qty], ...], 'asks': [[...]]}
        Maps microstructures into physical non-equilibrium damping tensors.
        """
        bids = order_book.get("bids", [])[:depth]
        asks = order_book.get("asks", [])[:depth]
        
        if not bids or not asks:
            raise ValueError("Empty bids or asks in order book")

        now = time.perf_counter()
        best_bid = bids[0][0]
        best_ask = asks[0][0]
        mid_price = (best_bid + best_ask) / 2.0
        current_spread = best_ask - best_bid

        # 1. Flux Potential (Imbalance Voltage: 0.080V ~ 0.100V)
        total_bid_vol = sum(b[1] for b in bids)
        total_ask_vol = sum(a[1] for a in asks)
        tot_vol = total_bid_vol + total_ask_vol
        imbalance = (total_bid_vol - total_ask_vol) / tot_vol if tot_vol > 0 else 0.0
        flux_v = 0.085 + (imbalance * 0.012)

        # 2. Velocity & Acceleration (dP/dt, d^2P/dt^2)
        if self.prev_time is None:
            velocity = 0.0
            accel = 0.0
            self.baseline_spread = current_spread
        else:
            dt = max(now - self.prev_time, 1e-4)
            velocity = (mid_price - self.prev_mid) / dt
            accel = (velocity - self.prev_velocity) / dt
            self.prev_velocity = velocity

        self.prev_time = now
        self.prev_mid = mid_price

        # 3. Active Strain (Spread Distortion Factor)
        if not self.baseline_spread or self.baseline_spread <= 0:
            self.baseline_spread = current_spread
        strain = max(current_spread / self.baseline_spread, 0.5)

        return self.evaluate_lob_raw(flux_v, abs(velocity), abs(accel), strain)
