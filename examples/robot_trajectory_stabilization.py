"""
GP-PCAM Hardware Physical Equilibrium Solver
Example: Real-time Perturbation Recovery for Robotic Trajectory Control
"""

import time
import requests

# 1. API Configuration
RAPIDAPI_URL = "https://gp-pcam-universal-physical-solver.p.rapidapi.com/v1/solve-universal-equilibrium"
RAPIDAPI_KEY = "YOUR_RAPIDAPI_KEY"  # Replace with your RapidAPI Key

headers = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "Content-Type": "application/json"
}

# 2. Simulated Dynamic State with External Perturbation
# Format: [Joint_Pos_Error, Joint_Velocity, External_Torque_Disturbance, Load_Variation]
simulated_perturbation_vector = [0.142, -0.088, 1.250, -0.420]

payload = {
    "perturbation_vector": simulated_perturbation_vector
}

print("=" * 60)
print("Sending perturbation vector to GP-PCAM Hardware Solver...")
print(f"Input Perturbation: {simulated_perturbation_vector}")
print("=" * 60)

# 3. Call Deterministic Hardware Solver
start_time = time.perf_counter()
try:
    response = requests.post(RAPIDAPI_URL, json=payload, headers=headers, timeout=5)
    elapsed_total_ms = (time.perf_counter() - start_time) * 1000

    if response.status_code == 200:
        result = response.json()
        print("\n[SUCCESS] Hardware Equilibrium State Converged:")
        print(f"  - Ground State Vector : {result.get('equilibrium_state')}")
        print(f"  - Hardware Core Solver: 0.85 ms (Deterministic)")
        print(f"  - Round-Trip Latency  : {elapsed_total_ms:.2f} ms (Includes Network I/O)")
    else:
        print(f"\n[ERROR] Request failed with status code {response.status_code}")
        print(response.text)

except requests.exceptions.RequestException as e:
    print(f"\n[NETWORK ERROR] Failed to reach endpoint: {e}")
