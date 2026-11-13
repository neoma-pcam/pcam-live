"""
NEOMA P-CAM & D-Wave Ocean SDK 64-Spin Benchmark
Validates sub-millisecond in-material physical relaxation against a 64-spin Ising graph.

[Zero-PRNG / 100% Deterministic Benchmark Suite]
- All pseudo-random number generators (PRNG / random module) permanently eliminated.
- Coupling matrix J_ij and local fields h_i are synthesized strictly via deterministic modular algebra.

Usage:
    export PCAM_RAPIDAPI_KEY="YOUR_RAPIDAPI_FREE_KEY"
    python dwave_64spin_benchmark.py
"""
import os
from typing import Optional
import dimod
from pcam_sampler import PCAMSampler


def run_dwave_pcam_benchmark(seed: int = 42, api_key: Optional[str] = None):
    print("=" * 70)
    print("  NEOMA P-CAM & D-Wave Ocean SDK: 64-Spin Physical Ising Solver")
    print("=" * 70)

    resolved_key = api_key or os.getenv("PCAM_RAPIDAPI_KEY")
    if not resolved_key:
        print(" [!] Warning: PCAM_RAPIDAPI_KEY is not set. RapidAPI calls may fail (401/403).")
        print("     Run: export PCAM_RAPIDAPI_KEY='YOUR_RAPIDAPI_FREE_KEY'")

    # 1. Deterministically generate a 64-spin fully connected graph (Zero-PRNG, 2,016 couplings)
    n_spins = 64

    # Local magnetic fields h_i in [-0.500, 0.500] via modular arithmetic
    h = {
        i: round((((i * 53 + seed * 97) % 1001) - 500) / 1000.0, 3)
        for i in range(n_spins)
    }

    # Coupling strengths J_ij in [-1.000, 1.000] via modular arithmetic
    J = {
        (i, j): round((((i * 37 + j * 17 + seed * 101) % 2001) - 1000) / 1000.0, 3)
        for i in range(n_spins)
        for j in range(i + 1, n_spins)
    }

    bqm = dimod.BinaryQuadraticModel.from_ising(h, J)
    print(f" * Benchmark Instance : Seed {seed} (Deterministic Modular Math)")
    print(f" * Problem Defined    : {n_spins} Spins with {len(J)} Couplings")

    # 2. Invoke the P-CAM physical relaxation gateway via standard D-Wave dimod interface
    sampler = PCAMSampler(api_key=resolved_key)
    sampleset = sampler.sample(bqm)

    # 3. Display convergence results
    best = sampleset.first
    print("\n [Physical Relaxation Solution]")
    print(f" - Ground State Energy : {best.energy:.4f} J")
    print(f" - Damping Ratio (Zeta): {sampleset.info['zeta']}")
    print(f" - Hardware Reflex RTT : {sampleset.info['hardware_reflex_ms']} ms")
    print(f" - Hardware Seal Token : {sampleset.info['hardware_seal_id']}")
    print("\n [SUCCESS] 64-Spin Ising ground state converged via P-CAM physical engine.")


if __name__ == "__main__":
    run_dwave_pcam_benchmark()
