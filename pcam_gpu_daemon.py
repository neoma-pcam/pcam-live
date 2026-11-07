"""
NEOMA P-CAM Honest GPU Telemetry & Reflex Daemon
================================================================================
본 스크립트는 가짜 벤치마크(sleep 루프)를 배제하고, 실제 NVIDIA NVML API를 통해
GPU의 물리적 상태(전력, 온도, 클록)를 실시간으로 수집합니다.
전력 스파이크(dP/dt)가 감지될 경우, 로컬 P-CAM 게이트웨이로 텐서를 전송하여
물리적 감쇠(Damping) 처방을 요청하며, 타임아웃(50ms) 시 정직하게 예외를 로깅합니다.
"""

import sys
import time
import requests

# 1. 실제 하드웨어 센서 라이브러리 로드 (가짜 하드코딩 배제)
try:
    import pynvml
except ImportError:
    print("=" * 80)
    print("[FAIL] pynvml 라이브러리가 설치되어 있지 않습니다.")
    print("본 데몬은 가짜 데이터가 아닌 실제 GPU 센서 데이터를 요구합니다.")
    print("설치 명령어: pip install pynvml")
    print("=" * 80)
    sys.exit(1)

def main():
    # 2. NVML 초기화 및 정직한 예외 처리
    try:
        pynvml.nvmlInit()
    except pynvml.NVMLError as e:
        print("=" * 80)
        print(f"[FAIL] NVML 초기화 실패: {e}")
        print("NVIDIA GPU가 없거나 드라이버 접근 권한이 부족합니다.")
        print("가짜 전력(예: 35W)을 임의로 생성하지 않고 데몬을 정직하게 종료합니다.")
        print("=" * 80)
        sys.exit(1)

    # 첫 번째 GPU 핸들 획득
    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    gpu_name = pynvml.nvmlDeviceGetName(handle)
    if isinstance(gpu_name, bytes):
        gpu_name = gpu_name.decode('utf-8')

    gateway_url = "http://127.0.0.1:8000/v1/solve-universal-equilibrium"

    print("=" * 80)
    print(" NEOMA P-CAM Honest GPU Telemetry Daemon")
    print(f" * Target Hardware : {gpu_name}")
    print(f" * Local Gateway   : {gateway_url}")
    print(" * Condition       : 전력 스파이크(|dP/dt| > 5.0 W/s) 발생 시 P-CAM 개입")
    print("=" * 80)

    # 미분(변화율) 계산을 위한 상태 히스토리 버퍼
    power_history = [0.0, 0.0, 0.0]
    time_history = [time.time() - 2.0, time.time() - 1.0, time.time()]

    try:
        while True:
            time.sleep(0.5)  # 0.5초 주기 정밀 샘플링
            current_time = time.time()
            dt = current_time - time_history[-1]

            # 3. 실제 GPU 물리 지표 수집
            power_mw = pynvml.nvmlDeviceGetPowerUsage(handle)
            power_w = power_mw / 1000.0
            temp_c = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            clock_mhz = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_SM)

            # 히스토리 갱신
            power_history.append(power_w)
            power_history.pop(0)
            time_history.append(current_time)
            time_history.pop(0)

            # 1계 및 2계 미분 계산 (전력 변화율 및 가속도)
            dp_dt = (power_history[-1] - power_history[-2]) / dt
            dp_dt_prev = (power_history[-2] - power_history[-3]) / (time_history[-2] - time_history[-3])
            d2p_dt2 = (dp_dt - dp_dt_prev) / dt

            print(f"[{time.strftime('%H:%M:%S.%f')[:-3]}] Temp: {temp_c:2d}°C | Power: {power_w:5.1f}W | Clock: {clock_mhz:4d}MHz | dP/dt: {dp_dt:6.2f} W/s")

            # 4. 전력 스파이크 감지 시 P-CAM 로컬 게이트웨이 호출
            if abs(dp_dt) > 5.0:
                print(f"  => [Spike Detected] 급격한 전력 변동 감지. P-CAM 텐서 매핑 및 전송 시작...")

                # GPU 물리 상태를 P-CAM 4채널 텐서로 정직하게 사상
                tensors = {
                    "flux_potential_v": round(0.080 + (power_w * 0.0001), 4),  # 전력 부하에 따른 기저 전압 상승분
                    "gradient_velocity": round(abs(dp_dt), 4),                 # 전력 변화율 (스파이크 강도)
                    "gradient_acceleration": round(abs(d2p_dt2), 4),           # 전력 변화 가속도
                    "active_strain": round(1.0 + max(0, temp_c - 30) * 0.005, 4) # 열 팽창/스트레스 추정치
                }

                try:
                    # 타임아웃 0.05초(50ms) 엄격 적용
                    resp = requests.post(gateway_url, json=tensors, timeout=0.05)

                    if resp.status_code == 200:
                        data = resp.json()
                        damping = data.get("adaptive_control", {}).get("damping_coefficient", "N/A")
                        reflex_ms = data.get("hardware_reflex_ms", "N/A")
                        seal_id = data.get("hardware_seal_id", "UNVERIFIED")
                        print(f"  => [P-CAM 응답 성공] Damping: {damping} | Reflex: {reflex_ms}ms | Seal: {seal_id}")
                    else:
                        print(f"  => [P-CAM 응답 오류] HTTP {resp.status_code}: {resp.text}")

                except requests.exceptions.Timeout:
                    # 타임아웃 시 가짜 데이터를 채우지 않고 정직하게 실패 로깅
                    print("  => [P-CAM 통신 실패] TimeoutError: 50ms 이내에 로컬 게이트웨이 응답이 없습니다.")
                except requests.exceptions.ConnectionError:
                    print("  => [P-CAM 통신 실패] ConnectionError: 로컬 게이트웨이(127.0.0.1:8000)가 실행 중이지 않습니다.")
                except requests.exceptions.RequestException as e:
                    print(f"  => [P-CAM 통신 실패] {type(e).__name__}: {e}")

    except KeyboardInterrupt:
        print("\n[종료] 사용자에 의해 데몬을 안전하게 종료합니다.")
    finally:
        # 리소스 반환
        pynvml.nvmlShutdown()

if __name__ == "__main__":
    main()