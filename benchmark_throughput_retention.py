import numpy as np
import time
import threading
import sys
import argparse

# pynvml / nvidia-ml-py 안전 임포트
try:
    import pynvml
except ImportError:
    try:
        import nvidia_ml_py as pynvml
    except ImportError:
        pynvml = None

# --- 설정 ---
MATRIX_SIZE = 4000
CYCLES = 10
TDP_MW = 75000.0  # GTX 1650 가상 TDP (75W)
TOTAL_FLOPS = 2 * (MATRIX_SIZE ** 3) * CYCLES

def get_gpu_power(handle, max_clock):
    """GTX 1650 하드웨어 센서 미지원 대응: 가상 동적 전력 추정기"""
    if handle is None:
        return 0.0
    try:
        # 하드웨어 센서 직접 조회 시도
        return pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0
    except Exception:
        # 센서 미지원 시 이용률 + 클록 기반 프록시 추정
        try:
            util = pynvml.nvmlDeviceGetUtilizationRates(handle).gpu
            clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
            clock_ratio = (clock / max_clock) if max_clock > 0 else 0.5
            p_est_mw = TDP_MW * (util / 100.0) * clock_ratio
            return max(0.2, p_est_mw / 1000.0)
        except Exception:
            return 0.2

class PowerMonitor(threading.Thread):
    def __init__(self, handle, max_clock, interval=0.01):
        super().__init__()
        self.handle = handle
        self.max_clock = max_clock
        self.interval = interval
        self.running = True
        self.readings = []

    def run(self):
        while self.running:
            p = get_gpu_power(self.handle, self.max_clock)
            self.readings.append(p)
            time.sleep(self.interval)

    def stop(self):
        self.running = False

def run_benchmark(mode_name="BASELINE"):
    print("=" * 60)
    print(f" [P-CAM 벤치마크] 연산 처리량 & 전력 보존 테스트 ({mode_name})")
    print(f" * 행렬 크기: {MATRIX_SIZE}x{MATRIX_SIZE} (FP64)")
    print(f" * 반복 횟수: {CYCLES} 사이클")
    print(f" * 총 부동소수점 연산량: {TOTAL_FLOPS / 1e9:.2f} GFLOPs")
    print("=" * 60)

    # NVML 초기화
    handle = None
    max_clock = 1665
    if pynvml:
        try:
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            max_clock = pynvml.nvmlDeviceGetMaxClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
        except Exception:
            handle = None

    # 모니터링 스레드 시작
    monitor = PowerMonitor(handle, max_clock, interval=0.01)
    monitor.start()

    # 연산 부하 인가 및 정밀 시간 측정
    print("\n[연산 실행 중...]")
    t_start = time.perf_counter()

    for i in range(1, CYCLES + 1):
        a = np.random.rand(MATRIX_SIZE, MATRIX_SIZE)
        b = np.random.rand(MATRIX_SIZE, MATRIX_SIZE)
        _ = np.dot(a, b)
        print(f"  └─ 사이클 {i}/{CYCLES} 완료")

    t_end = time.perf_counter()
    monitor.stop()
    monitor.join()

    # NVML 종료
    if pynvml and handle:
        try:
            pynvml.nvmlShutdown()
        except Exception:
            pass

    # 통계 산출
    elapsed_time = t_end - t_start
    gflops = (TOTAL_FLOPS / 1e9) / elapsed_time
    readings = monitor.readings if monitor.readings else [0.0]
    peak_power = max(readings)
    min_power = min(readings)
    avg_power = sum(readings) / len(readings)
    variance = peak_power - min_power
    perf_per_watt = gflops / avg_power if avg_power > 0 else 0.0

    print("\n" + "=" * 60)
    print(f"             [ 공학 성적표: {mode_name} ]")
    print("=" * 60)
    print(f" 총 연산 소요 시간          : {elapsed_time:.4f} 초")
    print(f" 연산 처리량 (Throughput)   : {gflops:.2f} GFLOPS")
    print(f" 피크 전력 (Peak Power)     : {peak_power:.2f} W")
    print(f" 전력 변동폭 (Variance)     : {variance:.2f} W")
    print(f" 평균 소비 전력             : {avg_power:.2f} W")
    print(f" 전력 대 성능비 (에너지효율): {perf_per_watt:.2f} GFLOPS/Watt")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="TEST", help="테스트 모드 명칭 (예: BASELINE 또는 PCAM)")
    args = parser.parse_args()
    run_benchmark(args.mode.upper())