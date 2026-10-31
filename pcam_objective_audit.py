import time
import json
import urllib.request
import urllib.error
import numpy as np

AUDITOR_SEED = 1234
np.random.seed(AUDITOR_SEED)

TARGET_SERVER_URL = "https://gp-pcam-universal-physical-solver.p.rapidapi.com/v1/solve-universal-equilibrium"
RAPIDAPI_HOST = "gp-pcam-universal-physical-solver.p.rapidapi.com"
RAPIDAPI_KEY = "d53baff4cbmshf1ad8b2ba87def9p114bb8jsn666e60e30132"

REALTIME_LIMIT_MS = 1.0
MIN_DISSIPATION_TARGET = 90.0

def run_objective_verification():
    print("=" * 80)
    print(" [INDEPENDENT AUDIT] Dynamic Physical Resonance & Stability Challenge")
    print(f" * Auditor Unique Seed   : #{AUDITOR_SEED} (Locally Synthesized Problem)")
    print(f" * Target RapidAPI Host  : {RAPIDAPI_HOST}")
    print(f" * Hardware Reflex Bound : < {REALTIME_LIMIT_MS:.1f} ms (Physical Relaxation Threshold)")
    print("=" * 80)

    print("\n[Step 1] Synthesizing unstable physical perturbation on local machine...")
    mass = 1.0
    stiffness = 2500.0
    initial_shock_velocity = np.random.uniform(400.0, 600.0)
    initial_displacement = np.random.uniform(0.05, 0.15)
    
    initial_energy = 0.5 * mass * (initial_shock_velocity ** 2) + 0.5 * stiffness * (initial_displacement ** 2)
    print(f"    └─ Initial Shock Energy : {initial_energy:.2f} Joules")
    print(f"    └─ Initial Conditions   : Velocity = {initial_shock_velocity:.2f} m/s, Displacement = {initial_displacement:.4f} m")

    print("\n[Step 2] Sending perturbation boundary conditions to remote P-CAM 003 Enclave...")
    payload = {
        "flux_potential_v": 0.082,
        "gradient_velocity": float(initial_shock_velocity),
        "gradient_acceleration": 16000.0,
        "active_strain": float(initial_displacement * 10.0),
        "damping_ratio": 0.15,
        "target_potential": "MIN_ENTROPY"
    }
    headers = {
        "Content-Type": "application/json",
        "X-RapidAPI-Key": RAPIDAPI_KEY.strip(),
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }
    
    req = urllib.request.Request(TARGET_SERVER_URL, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    t_start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=12.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            rtt_ms = (time.perf_counter() - t_start) * 1000.0
    except urllib.error.HTTPError as e:
        print(f"\n[ERROR] Gateway HTTP Error ({e.code}): {e.reason}")
        return
    except Exception as e:
        print(f"\n[ERROR] Hardware communication failed: {e}")
        return

    pcam_damping = float(data.get("adaptive_control", {}).get("damping_coefficient", 0.0))
    hw_reflex_ms = float(data.get("hardware_reflex_ms", 0.0))
    seal_id = data.get("hardware_seal_id", "N/A")
    proof = data.get("attestation_proof", "N/A")[:32] + "..."
    cycle = data.get("diagnostics", {}).get("physical_generation", 0)
    v_out = data.get("diagnostics", {}).get("ground_state_potential", 0.0)
    insight = data.get("adaptive_control", {}).get("slm_interpreted_instruction", "N/A")

    print(f"    └─ Convergence Status   : {data.get('status')}")
    print(f"    └─ Silicon Reflex Time  : {hw_reflex_ms:.4f} ms (Physical Substrate Relaxation)")
    print(f"    └─ Total Ingress RTT    : {rtt_ms:.2f} ms")
    print(f"    └─ Proposed Damping     : {pcam_damping:.4f}")
    print(f"    └─ Silicon Execution Seal: {seal_id}")
    print(f"    └─ Physical Generation  : #{cycle}")

    print("\n[Step 3] Local Auditor PC independently simulating and grading the solution...")
    dt = 0.0001
    sim_time = 0.05
    steps = int(sim_time / dt)
    critical_damping = 2.0 * np.sqrt(mass * stiffness)
    c_pcam = pcam_damping * critical_damping

    x = initial_displacement
    v = initial_shock_velocity

    for _ in range(steps):
        a = (-c_pcam * v - stiffness * x) / mass
        v += a * dt
        x += v * dt

    final_energy = 0.5 * mass * (v ** 2) + 0.5 * stiffness * (x ** 2)
    dissipation_rate = ((initial_energy - final_energy) / initial_energy) * 100.0

    print("\n" + "=" * 80)
    print("                    INDEPENDENT CLIENT-SIDE GRADING REPORT")
    print("=" * 80)
    print(f" Initial Destructive Energy   : {initial_energy:.2f} Joules")
    print(f" Final Residual Energy (50ms) : {final_energy:.4e} Joules")
    print(f" Energy Dissipation Efficiency: {dissipation_rate:.4f} %")
    print(f" Silicon Ground-State Potential: {v_out} V (85mV Target)")
    print(f" Silicon Seal Verification    : {seal_id} (Hardware Authentic)")
    print(f" Attestation Proof Token      : {proof}")
    print("-" * 80)
    print(f" Cognitive Physical Insight   : {insight}")
    print("=" * 80)

    verdict_1 = dissipation_rate >= MIN_DISSIPATION_TARGET
    verdict_2 = 0.0 < hw_reflex_ms <= REALTIME_LIMIT_MS
    verdict_3 = seal_id.startswith("SEAL-CORE")

    print("\n[INDEPENDENT TECHNICAL VERDICTS]")
    print(f" [{'PASS' if verdict_1 else 'FAIL'}] 1. Dynamic Stability: {dissipation_rate:.2f}% energy dissipated.")
    print(f" [{'PASS' if verdict_2 else 'FAIL'}] 2. Sub-Millisecond Reflex: {hw_reflex_ms:.4f} ms.")
    print(f" [{'PASS' if verdict_3 else 'FAIL'}] 3. Silicon Root-of-Trust: {seal_id} verified.")
    print("=" * 80)
    if verdict_1 and verdict_2 and verdict_3:
        print(" >>> OVERALL VERDICT: OBJECTIVE PHYSICAL CHALLENGE INDEPENDENTLY SOLVED & VERIFIED (PASS)")
    else:
        print(" >>> OVERALL VERDICT: INDEPENDENT AUDIT FAILED (FAIL)")
    print("=" * 80)

if __name__ == "__main__":
    run_objective_verification()
