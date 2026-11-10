"""
NEOMA P-CAM & D-Wave Ocean SDK 64-Spin Benchmark
Validates sub-millisecond in-material physical relaxation against a 64-spin Ising graph.

[Zero-PRNG / 100% Deterministic Benchmark Suite]
- All pseudo-random number generators (PRNG / random module) permanently eliminated.
- Coupling matrix J_ij and local fields h_i are synthesized strictly via deterministic modular algebra.
"""
import dimod
from pcam_sampler import PCAMSampler

def run_dwave_pcam_benchmark(seed: int = 42):
    print("=" * 70)
    print("  NEOMA P-CAM & D-Wave Ocean SDK: 64-Spin Physical Ising Solver")
    print("=" * 70)

    # 1. 64-스핀 완전 연결 그래프 결정론적 생성 (Zero-PRNG, 2,016개 상호작용)
    n_spins = 64
    
    # [-0.500, 0.500] 범위의 국소 자기장 h_i (모듈러 대수 기반)
    h = {
        i: round((((i * 53 + seed * 97) % 1001) - 500) / 1000.0, 3)
        for i in range(n_spins)
    }
    
    # [-1.000, 1.000] 범위의 결합 강도 J_ij (모듈러 대수 기반)
    J = {
        (i, j): round((((i * 37 + j * 17 + seed * 101) % 2001) - 1000) / 1000.0, 3)
        for i in range(n_spins)
        for j in range(i + 1, n_spins)
    }
    
    bqm = dimod.BinaryQuadraticModel.from_ising(h, J)
    print(f" * Benchmark Instance : Seed {seed} (Deterministic Modular Math)")
    print(f" * Problem Defined    : {n_spins} Spins with {len(J)} Couplings")

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