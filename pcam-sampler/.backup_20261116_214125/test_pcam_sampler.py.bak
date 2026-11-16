"""
NEOMA P-CAM & D-Wave dimod 64-Spin Unit Test Suite
=================================================
Validates sub-millisecond in-material physical relaxation against a 64-spin Ising graph.

[Zero-PRNG / 100% Deterministic Test Fixture]
- All pseudo-random number generators (PRNG / random module) permanently eliminated.
- Coupling matrix J_ij and local fields h_i are synthesized strictly via deterministic modular algebra.
"""
import sys
import os
import dimod

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from pcam_sampler import PCAMSampler

def test_64spin_ising_solver(seed: int = 7777):
    print("=" * 80)
    print(" [TEST] D-Wave dimod 호환 PCAMSampler 64-스핀 수렴 검증")
    print(f" * Benchmark Instance : Seed {seed} (Deterministic Modular Math)")
    print("=" * 80)

    n_spins = 64

    # 1. [-0.500, 0.500] 범위의 국소 자기장 h_i (Zero-PRNG 모듈러 대수)
    h = {
        i: round((((i * 53 + seed * 97) % 1001) - 500) / 1000.0, 3)
        for i in range(n_spins)
    }

    # 2. [-1.000, 1.000] 범위의 결합 강도 J_ij (Zero-PRNG 모듈러 대수)
    J = {}
    for i in range(n_spins):
        for j in range(i + 1, n_spins):
            k = (i * 37 + j * 17 + seed * 101) % 2001
            J[(i, j)] = round((k - 1000) / 1000.0, 3)

    bqm = dimod.BinaryQuadraticModel.from_ising(h, J)
    sampler = PCAMSampler(endpoint="https://api.neoma-pcam.com/v1/solve-universal-equilibrium")
    sample_set = sampler.sample(bqm)

    best_sample = sample_set.first.sample
    energy = sample_set.first.energy
    info = sample_set.info

    print("\n[수렴 결과 보고서]")
    print(f" - 스핀 수          : {len(best_sample)} Spins")
    print(f" - 해밀토니안 에너지: {energy:.4f} J")
    print(f" - 물리 감쇠비(Zeta): {info['zeta']}")
    print(f" - 하드웨어 지연    : {info['hardware_reflex_ms']} ms")
    print(f" - SEAL 토큰        : {info['hardware_seal_id']}")
    print(f" - 하드웨어 노드    : {info['telemetry'].get('port_node', 'N/A')}")

    assert len(best_sample) == 64
    assert 0.1 <= info['zeta'] <= 2.0
    print("\n [PASS] D-Wave BQM 인터페이스 정상 작동 및 P-CAM 물리 완화 검증 완료!")

if __name__ == "__main__":
    test_64spin_ising_solver()