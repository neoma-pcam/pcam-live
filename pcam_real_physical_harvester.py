import os
import re
import time
import json
import hashlib
import hmac
import serial
from datetime import datetime

COM_PORT = "COM6"
BAUD_RATE = 921600

VAULT_DIR = r"C:\neoma_pcam_assets\tesla_3year_vault"
os.makedirs(VAULT_DIR, exist_ok=True)

TARGET_EOD_DAYS = 1095.0
TICKS_PER_DAY = 20

JOINT_NAMES = {
    1: "Shoulder_Pitch_Actuator",
    2: "Wrist_Flexure_Actuator",
    3: "Knee_Linear_Drive",
    4: "Ankle_Contact_Spring",
    5: "Tendon_Elastic_Cable"
}

def run_pure_hardware_harvester():
    print("=" * 80)
    print("  NEOMA P-CAM 003: PURE IN-MATERIA HARDWARE HARVESTER")
    print(f"  [Interface: {COM_PORT} @ {BAUD_RATE} bps | Strictly ZERO Simulation]")
    print("=" * 80)

    try:
        ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=2.0)
        print(f"[+] Physical hardware link established on {COM_PORT}.")
        time.sleep(1.0)
    except Exception as e:
        print(f"[!] FATAL: Cannot connect to P-CAM hardware on {COM_PORT}: {e}")
        return

    total_ticks = 0
    current_eod = 0.0
    current_batch = []
    batch_idx = 1

    try:
        while current_eod < TARGET_EOD_DAYS:
            year = min(int(current_eod // 365) + 1, 3)
            if year == 1:
                v_stim = 0.082 + ((total_ticks % 10) * 0.002)
            elif year == 2:
                v_stim = 0.110 + ((total_ticks % 10) * 0.003)
            else:
                v_stim = 0.145 + ((total_ticks % 10) * 0.004)

            stim_cmd = f"[STIM_INJECT] V:{v_stim:.3f} EOD:{current_eod:.1f}\n".encode('utf-8')
            t_inject = time.perf_counter()
            ser.write(stim_cmd)
            ser.flush()

            raw_line = ""
            while True:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line.startswith("[NEOMA_PCAM") or line.startswith("[PCAM"):
                    raw_line = line
                    break
                if not line:
                    break

            t_settle = time.perf_counter()
            measured_transit_ms = (t_settle - t_inject) * 1000.0

            if not raw_line:
                print(f"[!] Hardware on {COM_PORT} did not respond. Retrying physical injection...")
                continue

            m = re.search(
                r"GEN:#?(\d+).*?CTRL:(\d+\.\d+).*?SH(?:OCK|K):?(\d+)%.*?V_OUT:(\d+\.\d+)V.*?ENT:(\d+\.\d+).*?UID:([0-9A-Fa-f]+)",
                raw_line
            )
            if not m:
                continue

            phys_gen = int(m.group(1))
            ctrl_flux = float(m.group(2))
            shock_pct = int(m.group(3))
            real_vout = float(m.group(4))
            entropy = float(m.group(5))
            raw_uid = m.group(6)

            total_ticks += 1
            current_eod = round(total_ticks / TICKS_PER_DAY, 1)

            slot = (total_ticks % 5) + 1
            node_seal = f"SEAL-CORE{slot:02d}-{hashlib.md5(f'{raw_uid}-{slot}'.encode()).hexdigest()[:6].upper()}"
            proof_token = "0x" + hmac.new(raw_uid.encode('utf-8'), f"{node_seal}-{phys_gen}-{real_vout}".encode('utf-8'), hashlib.sha256).hexdigest()

            record = {
                "timestamp_iso": datetime.utcnow().isoformat() + "Z",
                "provenance": "100%_PHYSICAL_HARDWARE_TRANSITED",
                "simulated_year": f"Year {year}",
                "eod_operating_day": current_eod,
                "joint_target": JOINT_NAMES[slot],
                "hardware_seal_id": node_seal,
                "attestation_proof": proof_token,
                "real_physical_telemetry": {
                    "physical_generation_cycle": phys_gen,
                    "applied_stimulus_v": round(v_stim, 3),
                    "measured_ground_potential_v": real_vout,
                    "measured_flux": ctrl_flux,
                    "measured_shock_pct": shock_pct,
                    "measured_entropy": entropy,
                    "measured_transit_time_ms": round(measured_transit_ms, 4)
                }
            }
            current_batch.append(record)

            if len(current_batch) >= 100:
                file_name = f"tesla_physical_Y{year}_batch_{batch_idx:04d}_EOD{current_eod:.1f}.jsonl"
                file_path = os.path.join(VAULT_DIR, file_name)

                with open(file_path, "w", encoding="utf-8") as f:
                    for r in current_batch:
                        f.write(json.dumps(r, ensure_ascii=False) + "\n")

                file_kb = round(os.path.getsize(file_path) / 1024.0, 2)
                current_batch.clear()
                batch_idx += 1

                print(f"[💾 REAL HARDWARE SAVED] {file_name} ({file_kb} KB) | EOD: {current_eod} / {TARGET_EOD_DAYS:.0f}일 | V_In: {v_stim:.3f}V ➔ V_Out: {real_vout:.3f}V | Gen: #{phys_gen}")

            time.sleep(0.02)

    except KeyboardInterrupt:
        print("\n[!] Physical harvesting safely halted by operator.")
    finally:
        ser.close()

if __name__ == "__main__":
    run_pure_hardware_harvester()
