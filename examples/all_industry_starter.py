"""
NEOMA P-CAM: Cross-Industry Universal Physical Reflex Starter Kit
-------------------------------------------------------------------
Because non-linear boundary stabilization follows the exact same physical
law across all domains, every P-CAM industrial endpoint accepts the same
4 normalized boundary variables:
  1. flux_potential_v       : Driving energy / potential / liquidity flux
  2. gradient_velocity      : First-derivative rate of change / drift
  3. gradient_acceleration  : Second-derivative shock / jerk / spike
  4. active_strain          : Cumulative structural / thermal / inventory load

Free Sandbox (2,000 calls/mo across all 7 domains):
https://rapidapi.com/shs15199702/api/neoma-p-cam-hyper-physical-control
"""

import argparse
import os
import time
import requests


DOMAIN_ENDPOINTS = {
    "universal": "/v1/solve-universal-equilibrium",
    "bioreactor": "/v1/pharma/predict",
    "battery": "/v1/battery/predict",
    "robotics": "/v1/robotics/predict",
    "mobility": "/v1/mobility/predict",
    "chemistry": "/v1/chemistry/predict",
    "quant": "/v1/quant/predict",
}

DOMAIN_PRESETS = {
    "universal": {
        "description": "GPU / Stiff PDE Non-Linear State Offload",
        "payload": {
            "flux_potential_v": 1.42,
            "gradient_velocity": 3.15,
            "gradient_acceleration": 28.4,
            "active_strain": 0.62,
        },
    },
    "bioreactor": {
        "description": "Bioreactor Cellular Shear & pH Drift Stabilization",
        "payload": {
            "flux_potential_v": 1.18,
            "gradient_velocity": 0.45,
            "gradient_acceleration": 6.2,
            "active_strain": 0.34,
        },
    },
    "battery": {
        "description": "Li-Ion / ESS Electrochemical Stress & Thermal Runaway Guard",
        "payload": {
            "flux_potential_v": 2.05,
            "gradient_velocity": 1.80,
            "gradient_acceleration": 19.5,
            "active_strain": 0.78,
        },
    },
    "robotics": {
        "description": "Robotic Joint Collision Reflex & Elastic Compliance",
        "payload": {
            "flux_potential_v": 1.65,
            "gradient_velocity": 4.20,
            "gradient_acceleration": 42.0,
            "active_strain": 0.51,
        },
    },
    "mobility": {
        "description": "Active Suspension Damping & Extreme Yaw Recovery",
        "payload": {
            "flux_potential_v": 1.74,
            "gradient_velocity": 5.10,
            "gradient_acceleration": 35.8,
            "active_strain": 0.49,
        },
    },
    "chemistry": {
        "description": "Exothermic Synthesis Runaway & Phase Transition Control",
        "payload": {
            "flux_potential_v": 1.92,
            "gradient_velocity": 2.35,
            "gradient_acceleration": 22.1,
            "active_strain": 0.66,
        },
    },
    "quant": {
        "description": "Institutional TWAP/VWAP Order Book Impact & Slippage Damping",
        "payload": {
            "flux_potential_v": 2.297,
            "gradient_velocity": 0.64,
            "gradient_acceleration": 9.8,
            "active_strain": 0.70,
        },
    },
}


class PCAMUniversalClient:
    """Drop-in Python client for all 7 NEOMA P-CAM industrial endpoints."""

    def __init__(self, rapidapi_key: str | None = None, use_direct_gateway: bool = False):
        self.api_key = rapidapi_key or os.getenv("PCAM_RAPIDAPI_KEY", "YOUR_RAPIDAPI_FREE_KEY")
        self.use_direct = use_direct_gateway
        self.base_url = (
            "https://api.neoma-pcam.com"
            if use_direct_gateway
            else "https://neoma-p-cam-hyper-physical-control.p.rapidapi.com"
        )

    def solve(
        self,
        domain: str,
        flux_potential_v: float,
        gradient_velocity: float,
        gradient_acceleration: float,
        active_strain: float,
    ) -> dict:
        if domain not in DOMAIN_ENDPOINTS:
            raise ValueError(f"Unsupported domain '{domain}'. Choose from: {list(DOMAIN_ENDPOINTS)}")

        url = f"{self.base_url}{DOMAIN_ENDPOINTS[domain]}"
        headers = {"Content-Type": "application/json"}
        if not self.use_direct:
            headers["x-rapidapi-host"] = "neoma-p-cam-hyper-physical-control.p.rapidapi.com"
            headers["x-rapidapi-key"] = self.api_key

        payload = {
            "flux_potential_v": float(flux_potential_v),
            "gradient_velocity": float(gradient_velocity),
            "gradient_acceleration": float(gradient_acceleration),
            "active_strain": float(active_strain),
        }

        t0 = time.perf_counter()
        res = requests.post(url, json=payload, headers=headers, timeout=5.0)
        rtt_ms = (time.perf_counter() - t0) * 1000.0
        res.raise_for_status()
        data = res.json()
        data["_client_rtt_ms"] = round(rtt_ms, 2)
        return data


def main():
    parser = argparse.ArgumentParser(description="NEOMA P-CAM All-Industry Starter")
    parser.add_argument(
        "--domain",
        default="all",
        choices=["all"] + list(DOMAIN_ENDPOINTS.keys()),
        help="Target industrial domain or 'all' to benchmark every endpoint",
    )
    parser.add_argument(
        "--direct",
        action="store_true",
        help="Use direct production gateway (api.neoma-pcam.com) instead of RapidAPI",
    )
    args = parser.parse_args()

    client = PCAMUniversalClient(use_direct_gateway=args.direct)
    targets = list(DOMAIN_ENDPOINTS.keys()) if args.domain == "all" else [args.domain]

    for dom in targets:
        preset = DOMAIN_PRESETS[dom]
        print(f"\n=== [{dom.upper()}] {preset['description']} ===")
        try:
            out = client.solve(dom, **preset["payload"])
            print(f"Endpoint             : {DOMAIN_ENDPOINTS[dom]}")
            print(f"Damping Ratio (Zeta) : {out.get('zeta')}")
            print(f"Control Intensity    : {out.get('control_intensity')}")
            print(f"Equilibrium Converged: {out.get('equilibrium_converged')}")
            print(f"Silicon Reflex (ms)  : {out.get('hardware_reflex_ms')} ms (RTT: {out.get('_client_rtt_ms')} ms)")
            print(f"Hardware PUF Seal    : {out.get('hardware_seal_id')}")
        except Exception as exc:
            print(f"Request Note ({DOMAIN_ENDPOINTS[dom]}): {exc}")


if __name__ == "__main__":
    main()