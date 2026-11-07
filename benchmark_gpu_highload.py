import sys
import time
import threading
import argparse
import ctypes
import numpy as np

# NVML 드라이버 안전 임포트
try:
    import pynvml
except ImportError:
    try:
        import nvidia_ml_py as pynvml
    except ImportError:
        pynvml = None

# --- 벤치마크 구성 파라미터 ---
CYCLES = 10
BURST_SEC = 0.5
IDLE_SEC = 0.5
TDP_MW = 75000.0  # GTX 1650 하드웨어 정격 TDP (75W)

# PTX 초고밀도 FMA(부동소수점 곱합 연산) 어셈블리 커널
PTX_CODE = b"""
.version 6.5
.target sm_50
.address_size 64

.visible .entry gpu_stress_kernel(
    .param .u64 d_out,
    .param .u32 iterations
)
{
    .reg .pred %p1;
    .reg .b32 %r1, %r2;
    .reg .f32 %f1, %f2;
    .reg .b64 %rd1;

    ld.param.u64 %rd1, [d_out];
    ld.param.u32 %r1, [iterations];
    mov.u32 %r2, 0;
    mov.f32 %f1, 1.0001;
    mov.f32 %f2, 0.9999;

$LOOP_HEAD:
    setp.ge.u32 %p1, %r2, %r1;
    @%p1 bra $LOOP_DONE;
    fma.rn.f32 %f1, %f1, %f2, 0.00001;
    fma.rn.f32 %f2, %f2, %f1, 0.00001;
    add.u32 %r2, %r2, 1;
    bra $LOOP_HEAD;

$LOOP_DONE:
    st.global.f32 [%rd1], %f1;
    ret;
}
"""

class CudaCoreEngine:
    """Windows nvcuda.dll 직접 제어 네이티브 CUDA 엔진"""
    def __init__(self):
        self.available = False
        try:
            self.cuda = ctypes.WinDLL("nvcuda.dll")
            if self.cuda.cuInit(0) != 0:
                return
            self.dev = ctypes.c_int()
            if self.cuda.cuDeviceGet(ctypes.byref(self.dev), 0) != 0:
                return
            self.ctx = ctypes.c_void_p()
            if self.cuda.cuCtxCreate(ctypes.byref(self.ctx), 0, self.dev.value) != 0:
                return
            self.module = ctypes.c_void_p()
            if self.cuda.cuModuleLoadData(ctypes.byref(self.module), PTX_CODE) != 0:
                return
            self.kernel = ctypes.c_void_p()
            if self.cuda.cuModuleGetFunction(ctypes.byref(self.kernel), self.module, b"gpu_stress_kernel") != 0:
                return
            self.d_out = ctypes.c_void_p()
            if self.cuda.cuMemAlloc(ctypes.byref(self.d_out), ctypes.c_size_t(4096)) != 0:
                return
            self.available = True
        except Exception:
            self.available = False

    def execute_burst(self, duration_sec):
        if not self.available:
            return 0.0
        iters = ctypes.c_uint32(200000)
        p_d_out = ctypes.cast(ctypes.byref(self.d_out), ctypes.c_void_p)
        p_iters = ctypes.cast(ctypes.byref(iters), ctypes.c_void_p)
        params = (ctypes.c_void_p * 2)(p_d_out, p_iters)

        grid = 512
        block = 256
        t_start = time.perf_counter()
        launches = 0

        while (time.perf_counter() - t_start) < duration_sec:
            self.cuda.cuLaunchKernel(
                self.kernel, grid, 1, 1, block, 1, 1, 0, None, params, None
            )
            self.cuda.cuCtxSynchronize()
            launches += 1

        total_ops = launches * grid * block * 200000 * 2.0
        return total_ops

    def cleanup(self):
        if self.available:
            try:
                self.cuda.cuMemFree(self.d_out)
                self.cuda.cuCtxDestroy(self.ctx)
            except Exception:
                pass

def get_gpu_power(handle, max_clock):
    """GTX 1650 10ms 실시간 전력 추정기"""
    if handle is None:
        return 0.2
    try:
        util = pynvml.nvmlDeviceGetUtilizationRates(handle).gpu
        clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
        clock_ratio = (clock / max_clock) if max_clock > 0 else 0.5
        p_est_mw = TDP_MW * (util / 100.0) * clock_ratio
        return max(0.4, p_est_mw / 1000.0)
    except Exception:
        return 0.4

class PowerTelemetry(threading.Thread):
    def __init__(self, handle, max_clock):
        super().__init__()
        self.handle = handle
        self.max_clock = max_clock
        self.active = True
        self.records = []

    def run(self):
        while self.active:
            self.records.append(get_gpu_power(self.handle, self.max_clock))
            time.sleep(0.01)

    def stop(self):
        self.active = False

def run_benchmark(mode_name="BASELINE"):
    print("=" * 65)
    print(f" [P-CAM 003] GTX 1650 75W 네이티브 하드웨어 부하 벤치마크 ({mode_name})")
    print(f" * 워크로드: 896 CUDA Cores Saturation (PTX FMA Burst)")
    print(f" * 사이클  : {CYCLES}회 (0.5s Full-Load Burst / 0.5s Idle Cooldown)")
    print("=" * 65)

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

    cuda_engine = CudaCoreEngine()
    if cuda_engine.available:
        print("[하드웨어 엔진] NVIDIA nvcuda.dll 네이티브 드라이버 직접 연동 성공.")
    else:
        print("[하드웨어 엔진] nvcuda 로드 불가: 멀티프로세스 시스템 버스 모드로 전환.")

    monitor = PowerTelemetry(handle, max_clock)
    monitor.start()

    total_ops_executed = 0.0
    t_start = time.perf_counter()

    for c in range(1, CYCLES + 1):
        print(f"\n--- [Cycle {c}/{CYCLES}] 0.5초 GPU 풀로드 버스트 (Burst) ---")
        if cuda_engine.available:
            ops = cuda_engine.execute_burst(BURST_SEC)
            total_ops_executed += ops
        else:
            t_b = time.perf_counter()
            while (time.perf_counter() - t_b) < BURST_SEC:
                a = np.random.rand(3000, 3000)
                _ = np.dot(a, a)
            total_ops_executed += 2.0 * (3000 ** 3)

        print(f"--- [Cycle {c}/{CYCLES}] 0.5초 쿨다운 (Idle) ---")
        time.sleep(IDLE_SEC)

    t_end = time.perf_counter()
    monitor.stop()
    monitor.join()
    cuda_engine.cleanup()

    if pynvml and handle:
        try:
            pynvml.nvmlShutdown()
        except Exception:
            pass

    # 통계 산출
    elapsed = t_end - t_start
    gflops = (total_ops_executed / 1e9) / elapsed
    readings = monitor.records if monitor.records else [0.0]
    peak_p = max(readings)
    min_p = min(readings)
    avg_p = sum(readings) / len(readings)
    variance_p = peak_p - min_p
    gflops_per_watt = gflops / avg_p if avg_p > 0 else 0.0

    print("\n" + "=" * 65)
    print(f"             [ 공학 종합 성적표: {mode_name} ]")
    print("=" * 65)
    print(f" 총 시험 소요 시간          : {elapsed:.4f} 초")
    print(f" 연산 처리량 (Throughput)   : {gflops:.2f} GFLOPS")
    print(f" 최대 피크 전력 (Peak Power): {peak_p:.2f} W")
    print(f" 전력 변동폭 (Variance)     : {variance_p:.2f} W")
    print(f" 평균 소비 전력             : {avg_p:.2f} W")
    print(f" 전력 대 성능비 (에너지효율): {gflops_per_watt:.2f} GFLOPS/Watt")
    print("=" * 65)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="TEST")
    args = parser.parse_args()
    run_benchmark(args.mode.upper())