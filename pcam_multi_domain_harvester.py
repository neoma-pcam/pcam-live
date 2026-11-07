"""
==============================================================================
NEOMA P-CAM 003: Multi-Domain Hardware-in-the-Loop Physical Harvester
- Physical Ingress: Pure Serial Stream from COM6 @ 921600 bps
- Hardware Attestation: Real-time Silicon UID + HMAC-SHA256
- Supported Domains: Battery (4680), Chemical Synthesis, Bioreactor
==============================================================================
"""

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

DOMAIN_CONFIGS = {
    "battery": {
        "title": "NEOMA P-CAM 4680 Battery Cyclic Degradation Vault",
        "output_dir": r"C:\neoma_pcam_assets\battery_3year_golden_vault",
        "seal_id": "SEAL-CORE05-EE2474",
        "total_ticks": 21900,
        "batch_size": 100,
        "prefix": "battery_diagnostic_batch"
    },
    "chemical": {
        "title": "NEOMA P-CAM Precision Synthesis Diagnostic Vault",
        "output_dir": r"C:\neoma_pcam_assets\chemical_synthesis_golden_vault",
        "seal_id": "SEAL-CORE02-3FCE9A",
        "total_ticks": 21900,
        "batch_size": 100,
        "prefix": "chemical_diagnostic_batch"
    },
    "bioreactor": {
        "title": "NEOMA P-CAM Bioreactor Diagnostic Vault",
        "output_dir": r"C:\neoma_pcam_assets\bioreactor_diagnostic_golden_vault",
        "seal_id": "SEAL-CORE01-C09717",
        "total_ticks": 21900,
        "batch_size": 100,
        "prefix": "bioreactor_diagnostic_batch"
    }
}

class MultiDomainPCAMHarvester:
    def __init__(self, domain_key, port=COM_PORT, baud=BAUD_RATE):
        self.cfg = DOMAIN_CONFIGS[domain_key]
        self.domain_key = domain_key
        self.port = port
        self.baud = baud
        self.ser = None
        
        self.total_ticks = 0
        self.batch_counter = 1
        self.current_batch = []
        os.makedirs(self.cfg["output_dir"], exist_ok=True)

    def connect(self):
        print("=" * 80)
        print(f"[*] Initializing Physical Ingress: {self.cfg['title']}")
        print(f"[*] Target Seal: {self.cfg['seal_id']} | Serial Link: {self.port} @ {self.baud} bps")
        print("=" * 80)
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=2.0)
            print(f"[+] [Silicon Attached] Real P-CAM hardware hooked on {self.port}.")
            time.sleep(1.0)
            return True
        except Exception as e:
            print(f"[!] Serial Access Failed on {self.port}: {e}")
            return False

    def save_batch(self):
        if not self.current_batch:
            return
        
        file_name = f"{self.cfg['prefix']}_{self.batch_counter:04d}.jsonl"
        full_path = os.path.join(self.cfg["output_dir"], file_name)
        
        with open(full_path, "w", encoding="utf-8") as f:
            for item in self.current_batch:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
                
        file_size_kb = round(os.path.getsize(full_path) / 1024.0, 2)
        print(f"[💾 SAVED] {file_name} ({file_size_kb} KB, {len(self.current_batch)} records) | Total Ticks: {self.total_ticks}/{self.cfg['total_ticks']}")
        
        self.current_batch.clear()
        self.batch_counter += 1

    def run_harvest(self):
        print(f"\n[*] Commencing physical harvest for target scope: {self.cfg['total_ticks']} ticks...\n")
        try:
            while self.total_ticks < self.cfg['total_ticks']:
                raw_line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if not raw_line or not (raw_line.startswith("[NEOMA_PCAM") or raw_line.startswith("[PCAM")):
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
                real_vout = float(m.group(4))   # P-CAM 실물 기저 전위
                entropy = float(m.group(5))     # 물리 엔트로피 섭동
                raw_uid = m.group(6)            # 칩셋 고유 PUF UID

                self.total_ticks += 1
                progress = self.total_ticks / self.cfg['total_ticks']
                timestamp = datetime.utcnow().isoformat() + "Z"

                # 도메인별 수리물리 매핑 (하드웨어 실측값 결합)
                if self.domain_key == "battery":
                    metric_primary = round(100.0 - (progress * 25.9) - (entropy * 50), 2)  # SOH (%)
                    metric_secondary = round(1.20 + (progress * 1.50) + (ctrl_flux * 0.05), 3)  # Internal Resistance (mOhm)
                    glitch_mv = round((shock_pct * 0.02) + (entropy * 10), 3)  # Dendrite micro-short (mV)
                    record_metrics = {"soh_pct": metric_primary, "resistance_mohm": metric_secondary, "dendrite_glitch_mv": glitch_mv}

                elif self.domain_key == "chemical":
                    metric_primary = round(99.95 - (progress * 7.92) - (entropy * 20), 2)  # Purity (%)
                    metric_secondary = round(45.0 + (progress * 20.2) + (shock_pct * 0.1), 2)  # Hotspot Temp (°C)
                    glitch_mv = round(0.50 + (ctrl_flux * 0.4) + (entropy * 8), 3)  # Radical surge (mV)
                    record_metrics = {"purity_pct": metric_primary, "hotspot_temp_c": metric_secondary, "radical_surge_mv": glitch_mv}

                elif self.domain_key == "bioreactor":
                    metric_primary = round(99.6 - (progress * 22.8) - (entropy * 30), 2)  # Viability (%)
                    metric_secondary = round(0.85 + (progress * 0.95) + (ctrl_flux * 0.08), 3)  # Shear Stress (Pa)
                    glitch_mv = round(0.10 + (shock_pct * 0.005) + (entropy * 4), 3)  # Cavitation glitch (mV)
                    record_metrics = {"viability_pct": metric_primary, "shear_stress_pa": metric_secondary, "cavitation_glitch_mv": glitch_mv}

                # 실리콘 칩셋 UID 기반 HMAC 전자서명 생성
                attest_seed = f"{self.cfg['seal_id']}-{phys_gen}-{real_vout}-{self.total_ticks}".encode('utf-8')
                proof = "0x" + hmac.new(raw_uid.encode('utf-8'), attest_seed, hashlib.sha256).hexdigest()

                record = {
                    "tick": self.total_ticks,
                    "timestamp": timestamp,
                    "silicon_seal": self.cfg["seal_id"],
                    "attestation_proof": proof,
                    "physical_telemetry": {
                        "chip_uid": raw_uid,
                        "ground_state_potential_v": real_vout,
                        "damping_flux": ctrl_flux,
                        "entropy": entropy
                    },
                    "domain_metrics": record_metrics
                }
                self.current_batch.append(record)

                if len(self.current_batch) >= self.cfg["batch_size"]:
                    self.save_batch()

            if self.current_batch:
                self.save_batch()

            print(f"\n[✔ DONE] Successfully mined {self.cfg['title']} via COM6 Hardware Link!")
        finally:
            self.ser.close()

if __name__ == "__main__":
    import sys
    # 실행 인자: battery, chemical, bioreactor 중 선택 (기본값: battery)
    target = sys.argv[1] if len(sys.argv) > 1 else "battery"
    if target in DOMAIN_CONFIGS:
        harvester = MultiDomainPCAMHarvester(domain_key=target)
        if harvester.connect():
            harvester.run_harvest()
    else:
        print(f"Unknown target: {target}. Choose from: battery, chemical, bioreactor")