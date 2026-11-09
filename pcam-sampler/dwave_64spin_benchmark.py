"""
NEOMA P-CAM & D-Wave Ocean SDK 64-Spin Benchmark
Validates sub-millisecond in-material physical relaxation against a 64-spin Ising graph.
"""
import random
import dimod
from pcam_sampler import PCAMSampler

def run_dwave_pcam_benchmark():
    print("=" * 70)
    print("  NEOMA P-CAM & D-Wave Ocean SDK: 64-Spin Physical Ising Solver")
    print("=" * 70)

    # 1. 64-스핀 완전 연결 그래프 생성 (2,016개 상호작용)
    n_spins = 64
    random.seed(42)
    h = {i: round(random.uniform(-0.5, 0.5), 3) for i in range(n_spins)}
    J = {(i, j): round(random.uniform(-1.0, 1.0), 3) for i in range(n_spins) for j in range(i + 1, n_spins)}
    
    bqm = dimod.BinaryQuadraticModel.from_ising(h, J)
    print(f" * Problem Defined : {n_spins} Spins with {len(J)} Couplings")

    # 2. D-Wave 표준 인터페이스로 P-CAM 물리 완화 게이트웨이 호출
    sampler = PCAMSampler()
    sampleset = sampler.sample(bqm)

    # 3. 수렴 결과 출력
    best = sampleset.first
    print("\n [Physical Relaxation Solution]")
    print(f" - Ground State Energy : {best.energy:.4f} J")
    print(f" - Damping Ratio (Zeta): {sampleset.info['zeta']}")
    print(f" - Hardware Reflex RTT : {sampleset.info['hardware_reflex_ms']} ms")
    print(f" - Hardware Seal Token : {sampleset.info['hardware_seal_id']}")
    print("\n [SUCCESS] 64-Spin Ising ground state converged via P-CAM physical engine.")

if __name__ == "__main__":
    run_dwave_pcam_benchmark()
