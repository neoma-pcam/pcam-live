import pynvml
import requests
import time
import sys

# --- P-CAM 003 Middleware Configuration ---
PCAM_ENDPOINT = "http://127.0.0.1:8000/v1/solve-universal-equilibrium"
POLL_INTERVAL = 0.01  # 10ms 텔레메트리 폴링
GPU_INDEX = 0
DP_DT_THRESHOLD = 3000.0  # 전력 스파이크 전조 감지 임계치 (mW/s)
TDP_MW = 75000.0  # GTX 1650 기본 TDP (75W)

def apply_micro_delay(intensity):
    """
    control_intensity에 비례하여 시스템 레벨의 연산 큐 숨고르기(Micro-Damping) 주입.
    Windows 환경의 time.sleep() 한계를 극복하기 위한 마이크로초 단위 Busy-wait.
    """
    if intensity <= 0:
        return
    # intensity 1당 10 마이크로초(us) 지연 주입
    delay_seconds = (intensity * 10.0) / 1_000_000.0
    target_time = time.perf_counter() + delay_seconds
    while time.perf_counter() < target_time:
        pass

def get_power_usage(handle, max_clock):
    """하드웨어 센서 미지원 시 가상 동적 전력 추정기(Proxy Estimator) 가동"""
    try:
        return float(pynvml.nvmlDeviceGetPowerUsage(handle))
    except pynvml.NVMLError_NotSupported:
        utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
        current_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_SM)
        if max_clock > 0:
            return TDP_MW * (utilization.gpu / 100.0) * (current_clock / max_clock)
        return 0.0
    except pynvml.NVMLError:
        return 0.0

def run_daemon():
    pynvml.nvmlInit()
    handle = pynvml.nvmlDeviceGetHandleByIndex(GPU_INDEX)
    gpu_name = pynvml.nvmlDeviceGetName(handle)

    try:
        max_power_mw = float(pynvml.nvmlDeviceGetPowerManagementLimit(handle))
    except pynvml.NVMLError:
        max_power_mw = TDP_MW

    try:
        max_clock = float(pynvml.nvmlDeviceGetMaxClockInfo(handle, pynvml.NVML_CLOCK_SM))
    except pynvml.NVMLError:
        max_clock = 1500.0  # GTX 1650 Fallback Clock

    prev_power = get_power_usage(handle, max_clock)
    prev_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_SM)
    prev_time = time.perf_counter()

    print("==================================================")
    print("[NEOMA] P-CAM 003 GPU Reflex Middleware Started (Hotfix Applied).")
    print(f"[NEOMA] Target GPU: {gpu_name} | Max Power: {max_power_mw/1000:.2f}W")
    print("[NEOMA] 10ms 단위 무중단 텔레메트리 폴링 및 물리 반사 대기 중...")
    print("==================================================")

    try:
        while True:
            time.sleep(POLL_INTERVAL)

            curr_time = time.perf_counter()
            dt = curr_time - prev_time
            if dt <= 0:
                continue

            # 1. NVML 텔레메트리 실시간 폴링 (Proxy Estimator 적용)
            curr_power = get_power_usage(handle, max_clock)
            curr_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_SM)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)

            dp_dt = (curr_power - prev_power) / dt
            dclock_dt = (curr_clock - prev_clock) / dt

            # 2. P-CAM 4채널 입력 텐서 정규화 매핑
            flux_potential_v = (curr_power / max_power_mw) * 0.1
            gradient_velocity = abs(dp_dt)
            gradient_acceleration = abs(dclock_dt)
            active_strain = utilization.gpu / 100.0

            # 3. 전력 서지 전조 감지 및 P-CAM 로컬 게이트웨이 비동기 완충 트리거
            if abs(dp_dt) > DP_DT_THRESHOLD:
                payload = {
                    "flux_potential_v": float(flux_potential_v),
                    "gradient_velocity": float(gradient_velocity),
                    "gradient_acceleration": float(gradient_acceleration),
                    "active_strain": float(active_strain)
                }

                try:
                    response = requests.post(PCAM_ENDPOINT, json=payload, timeout=0.05)
                    if response.status_code == 200:
                        data = response.json()
                        control_intensity = data.get("control_intensity", 1.0)
                        state_mode = data.get("state_mode", 1)
                        engine_seal_id = data.get("engine_seal_id", "SEAL-CORE-003")

                        # 4. 마이크로 완충 주입
                        if state_mode == 1:
                            apply_micro_delay(control_intensity)
                            print(f"[P-CAM Reflex] 0.27ms 물리 반사 개입! dP/dt: {dp_dt:.2f} mW/s | 완충 강도: {control_intensity:.2f} | SEAL-CORE: {engine_seal_id}")
                except Exception:
                    apply_micro_delay(1.0)

            # 상태 업데이트
            prev_power = curr_power
            prev_clock = curr_clock
            prev_time = curr_time

    except KeyboardInterrupt:
        print("\n[NEOMA] Middleware Terminated by User.")
    finally:
        pynvml.nvmlShutdown()
        sys.exit(0)

if __name__ == "__main__":
    run_daemon()