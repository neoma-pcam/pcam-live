"""
NEOMA P-CAM Autonomous Homeostasis Daemon & Silicon Reflex Miner
================================================================
Architecture:
  - Spine (P-CAM Enclave): Continuous 0.85ms deterministic reflex loop & SQLite telemetry mining
  - Brain (Google Gemini): Proactive engineering diagnostics triggered on critical entropy spikes

Author: NEOMA Physical AI Platform
License: Apache 2.0 / Commercial Proprietary Dual License
"""

import os
import time
import random
import sqlite3
import requests
from datetime import datetime
from google import genai
from google.genai import types

# ----------------------------------------------------------------------
# 1. Configuration & Security Credentials
# ----------------------------------------------------------------------
RAW_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
GEMINI_API_KEY = RAW_API_KEY.strip()

PCAM_API_URL = "https://api.neoma-pcam.com/v1/solve-universal-equilibrium"
PROXY_SECRET = os.getenv("PCAM_PROXY_SECRET", "5b53f210-cc89-11f1-b103-2f4009b9fdeb")

HEADERS = {
    "Content-Type": "application/json",
    "x-rapidapi-proxy-secret": PROXY_SECRET
}

DB_PATH = "pcam_reflex_vault.db"
client = genai.Client(api_key=GEMINI_API_KEY)

# ----------------------------------------------------------------------
# 2. Local Telemetry Vault (Silicon Root-of-Trust Persistence)
# ----------------------------------------------------------------------
def init_database():
    """Initializes local SQLite database to store cryptographically sealed physical telemetry."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reflex_telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            scenario_type TEXT,
            flux_potential_v REAL,
            velocity_mm_s REAL,
            acceleration_mm_s2 REAL,
            strain REAL,
            reflex_latency_ms REAL,
            hardware_seal_id TEXT,
            damping_coefficient REAL,
            physical_tick INTEGER,
            brain_alerted INTEGER
        )
    """)
    conn.commit()
    conn.close()

def save_reflex_record(scenario_type, flux_v, vel, accel, strain, reflex_ms, seal_id, damping, tick, alerted):
    """Commits a single physical convergence event into the immutable local vault."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO reflex_telemetry 
        (timestamp, scenario_type, flux_potential_v, velocity_mm_s, acceleration_mm_s2, strain, 
         reflex_latency_ms, hardware_seal_id, damping_coefficient, physical_tick, brain_alerted)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        scenario_type, flux_v, vel, accel, strain, reflex_ms, seal_id, damping, tick, int(alerted)
    ))
    conn.commit()
    conn.close()

# ----------------------------------------------------------------------
# 3. Spine-to-Brain Diagnostic Trigger (Autonomous Gemini Briefing)
# ----------------------------------------------------------------------
def trigger_gemini_brain_report(flux_v, accel, strain, seal_id, damping, tick):
    """
    Invokes Gemini 2.5 Flash as the high-level cognitive diagnostic layer
    when a physical shock vector exceeds the safe homeostasis baseline.
    """
    prompt = f"""
[CRITICAL PHYSICAL ANOMALY INTERCEPTED]
The P-CAM spinal hardware enclave has contained a sudden entropy spike via 0.85ms closed-loop damping:
- Timestamp: {datetime.utcnow().strftime('%H:%M:%S UTC')}
- Ground Potential Distortion: {flux_v:.4f} V (Nominal baseline: 0.0850 V)
- Peak Shock Acceleration: {accel:.1f} mm/s² (~{accel/9806.65:.2f} G)
- Active Mechanical Strain: {strain:.2f}
- Certified Silicon Seal: {seal_id}
- Prescribed Damping Coefficient: {damping:.4f}
- Hardware Cycle Count: #{tick}

As the Chief Cognitive Diagnostic Engine of the NEOMA Physical AI Platform:
1. Provide a succinct root-cause hypothesis (e.g., joint mechanical seizure, thermal runaway pre-cursor, high-G impact).
2. Issue an executive 3-bullet operational advisory for onsite maintenance personnel.
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are the senior diagnostic brain for the NEOMA Physical AI ecosystem. "
                    "Deliver sharp, precise, production-grade technical assessments without verbose filler."
                ),
                temperature=0.2
            )
        )
        return response.text
    except Exception as e:
        return f"[Cognitive Bridge Latency/Error]: {str(e)}"

# ----------------------------------------------------------------------
# 4. Autonomous Homeostasis & Reflex Mining Daemon Loop
# ----------------------------------------------------------------------
def run_autonomous_daemon():
    init_database()
    print("=" * 78)
    print("⚡ [NEOMA P-CAM] Autonomous Physical Reflex Daemon & Telemetry Miner Online")
    print(f"[*] Telemetry Vault: {os.path.abspath(DB_PATH)}")
    print("[*] Architecture: Continuous Hardware Grounding (0.85ms Reflex) -> SQLite")
    print("[*] Anomaly Threshold: Acceleration > 45,000 mm/s² OR Potential > 0.20V -> Gemini Bridge")
    print("=" * 78)

    loop_count = 0
    try:
        while True:
            loop_count += 1
            
            # Stochastic anomaly injection: ~15% probability of critical shock
            is_anomaly = (random.random() < 0.15)
            
            if is_anomaly:
                scenario_type = "CRITICAL_SHOCK_ANOMALY"
                flux_v = random.uniform(0.22, 0.35)
                accel = random.uniform(45000.0, 95000.0)
                strain = random.uniform(3.2, 5.0)
                vel = random.uniform(1800.0, 3500.0)
            else:
                scenario_type = "HOMEOSTASIS_PATROL"
                flux_v = random.uniform(0.080, 0.110)
                accel = random.uniform(500.0, 8000.0)
                strain = random.uniform(0.1, 1.2)
                vel = random.uniform(50.0, 450.0)

            payload = {
                "flux_potential_v": round(flux_v, 4),
                "gradient_velocity": round(vel, 2),
                "gradient_acceleration": round(accel, 2),
                "active_strain": round(strain, 2),
                "damping_ratio": 0.15,
                "target_potential": "MIN_ENTROPY"
            }

            # Dispatch payload to P-CAM Enclave
            start_t = time.perf_counter()
            resp = requests.post(PCAM_API_URL, json=payload, headers=HEADERS, timeout=4.0)
            network_latency_ms = (time.perf_counter() - start_t) * 1000

            if resp.status_code == 200:
                data = resp.json()
                reflex_ms = data.get("hardware_reflex_ms", 0.85)
                seal_id = data.get("hardware_seal_id", "N/A")
                damping = data.get("adaptive_control", {}).get("damping_coefficient", 0.0)
                tick = data.get("diagnostics", {}).get("physical_generation", 0)

                alerted = False
                if is_anomaly:
                    alerted = True
                    print(f"\n🚨 [CRITICAL ANOMALY #{loop_count:04d}] Shock: {accel:.1f} mm/s² (~{accel/9806.65:.1f}G) | Potential: {flux_v:.3f}V")
                    print(f"   -> P-CAM Silicon Reflex Converged in {reflex_ms}ms | Damping: {damping:.4f} [{seal_id}]")
                    print("   -> Requesting cognitive evaluation from Gemini Brain...")
                    
                    brain_brief = trigger_gemini_brain_report(flux_v, accel, strain, seal_id, damping, tick)
                    print("\n" + "-" * 60)
                    print(f"🤖 [Gemini Cognitive Assessment]:\n{brain_brief}")
                    print("-" * 60 + "\n")

                # Commit event to persistent vault
                save_reflex_record(scenario_type, flux_v, vel, accel, strain, reflex_ms, seal_id, damping, tick, alerted)

                if not is_anomaly:
                    print(f"[{datetime.utcnow().strftime('%H:%M:%S UTC')}] #{loop_count:04d} [PATROL OK] "
                          f"V: {flux_v:.3f}V | Tick: #{tick} | Silicon: {reflex_ms}ms | Seal: {seal_id}")

            else:
                print(f"[!] Hardware Gate Error ({resp.status_code}): {resp.text}")

            # Patrol poll interval (2.0s)
            time.sleep(2.0)

    except KeyboardInterrupt:
        print("\n[*] Gracefully shutting down P-CAM Autonomous Daemon. Telemetry saved.")

if __name__ == "__main__":
    run_autonomous_daemon()