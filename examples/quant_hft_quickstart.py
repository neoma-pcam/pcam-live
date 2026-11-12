"""
NEOMA P-CAM: Quant HFT & LOB Shock Damping Quickstart
Free Tier (2,000 requests/mo): [https://rapidapi.com/shs15199702/api/neoma-p-cam-hyper-physical-control](https://rapidapi.com/shs15199702/api/neoma-p-cam-hyper-physical-control)
"""

import os
import time
import requests

RAPIDAPI_KEY = os.getenv("PCAM_RAPIDAPI_KEY", "YOUR_RAPIDAPI_KEY")
URL = "[https://neoma-p-cam-hyper-physical-control.p.rapidapi.com/v1/quant/predict](https://neoma-p-cam-hyper-physical-control.p.rapidapi.com/v1/quant/predict)"

HEADERS = {
    "Content-Type": "application/json",
    "x-rapidapi-host": "neoma-p-cam-hyper-physical-control.p.rapidapi.com",
    "x-rapidapi-key": RAPIDAPI_KEY,
}

# Example Order Book Shock State (normalized into physical boundary variables)
payload = {
    "flux_potential_v": 1.85,        # Normalized LOB imbalance / liquidity shock potential
    "gradient_velocity": 0.42,       # Mid-price velocity (ticks/sec)
    "gradient_acceleration": 14.6,   # Order flow acceleration / volatility spike
    "active_strain": 0.015           # Current net inventory skew ratio
}

t0 = time.perf_counter()
response = requests.post(URL, json=payload, headers=HEADERS, timeout=5)
rtt_ms = (time.perf_counter() - t0) * 1000

data = response.json()
print(f"HTTP Status          : {response.status_code}")
print(f"Network Round-Trip   : {rtt_ms:.2f} ms")
print(f"Silicon Reflex Time  : {data.get('hardware_reflex_ms')} ms")
print(f"Damping Ratio (Zeta) : {data.get('zeta')}")
print(f"Control Intensity    : {data.get('control_intensity')}")
print(f"Equilibrium Converged: {data.get('equilibrium_converged')}")
print(f"Hardware PUF Seal    : {data.get('hardware_seal_id')}")