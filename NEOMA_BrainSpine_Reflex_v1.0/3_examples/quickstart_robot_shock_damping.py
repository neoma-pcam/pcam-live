import os
import sys

# 2_sdk 디렉토리 모듈 자동 등록
sdk_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "2_sdk"))
if sdk_dir not in sys.path:
    sys.path.insert(0, sdk_dir)

from neoma_brain_spine_adapter import NeomaBrainSpineAdapter

def main():
    print("=" * 65)
    print(" NEOMA Physical AI Brain-Spine Quickstart")
    print("=" * 65)
    
    adapter = NeomaBrainSpineAdapter()
    
    # 1. 고주파 충격/전압 외란 감지
    disturbed_voltage = 0.0985
    shock_velocity = 650.0
    print(f"[*] Destructive Perturbation Detected: Voltage={disturbed_voltage}V, Vel={shock_velocity}m/s")
    
    # 2. 척수(P-CAM) 0.27ms 물리 수렴 개입
    spine = adapter.dispatch_reflex(disturbed_voltage, shock_velocity)
    print(f"[*] Spine Intervention: Reflex Latency = {spine['latency_ms']}ms")
    print(f"[*] Loop Bypass: {spine['bypassed_stiff_loops']} Stiff Integration Steps Skipped (-90%)")
    print(f"[*] Energy Dissipation: {spine['dissipation_efficiency_pct']}%")
    print(f"[*] Silicon Execution Seal: {spine['hardware_seal']}")
    
    # 3. 대뇌(LLM) 시맨틱 인지 피드백
    directive = adapter.synthesize_brain_directive(spine, disturbed_voltage)
    print("")
    print(f"[+] {directive}")
    print("")

if __name__ == "__main__":
    main()
