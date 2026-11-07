import time
import requests
import dimod
from neal import SimulatedAnnealingSampler

print("==================================================")
print("1. D-Wave 공식 양자 어닐링(SA) 알고리즘 연산 시작")
print("==================================================")

# P-CAM과 동일한 물리계 엔트로피 최소화 모델 (Ising/QUBO)
bqm = dimod.BinaryQuadraticModel(
    {'s1': -1.0, 's2': -1.0, 's3': 0.5},
    {('s1', 's2'): 2.0, ('s2', 's3'): -1.5},
    0.0,
    dimod.BINARY
)

t0 = time.perf_counter()
sampler = SimulatedAnnealingSampler()
# 양자 어닐링 상태 1,000회 탐색
sampleset = sampler.sample(bqm, num_reads=1000)
dwave_latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

best_energy = sampleset.first.energy
print(f"D-Wave 수렴 에너지 (최적값): {best_energy}")
print(f"D-Wave 소프트웨어 연산 소요 시간: {dwave_latency_ms} ms\n")

print("==================================================")
print("2. NEOMA P-CAM 로컬 물리 게이트웨이 연산 시작")
print("==================================================")

t1 = time.perf_counter()
try:
    resp = requests.post(
        "http://127.0.0.1:8000/v1/actuate",
        json={"sensor_input": 1.0, "engine_mode": "PRECISION"},
        timeout=1.0
    )
    pcam_total_ms = round((time.perf_counter() - t1) * 1000.0, 2)
    pcam_data = resp.json()
    
    print(f"P-CAM 상태: {pcam_data.get('status')}")
    print(f"P-CAM 하드웨어 수렴 지연 시간: {pcam_data['physical_telemetry']['physical_latency_ms']} ms")
    print(f"P-CAM 게이트웨이 왕복 시간 (RTT): {pcam_total_ms} ms")
    print(f"암호학적 영수증 (Proof Hash): {pcam_data['receipt']['proof_hash'][:16]}...")
except Exception as e:
    print(f"P-CAM 게이트웨이 호출 실패 (서버 구동 확인 필요): {e}")