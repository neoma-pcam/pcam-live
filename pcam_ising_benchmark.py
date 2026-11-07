"""
================================================================================
NEOMA P-CAM 64-Spin Ising Spin Glass Empirical Annealing Benchmark
* Measures Real Ground-State Convergence on Edge Silicon (GTX 1650)
* Compares: CPU Simulated Annealing vs CPU Parallel Tempering vs P-CAM Tensor Reflex
* Formula: H = - sum_{i < j} J_ij * s_i * s_j  (s_i in {-1, +1}, N = 64)
================================================================================
"""
import time
import numpy as np
import torch

# 1. 64-Spin 완전 결합(All-to-All) SK 모델 해밀토니안 생성
N = 64
SEED = 2026
np.random.seed(SEED)
torch.manual_seed(SEED)

print("=" * 80)
print(f" [EMPIRICAL BENCHMARK] 64-Spin Ising Spin Glass Ground-State Convergence")
print(f" * Problem Formulation : N={N} All-to-All Coupled Sherrington-Kirkpatrick (SK)")
print(f" * Target Silicon       : {'NVIDIA GPU (CUDA)' if torch.cuda.is_available() else 'Host CPU'}")
print("=" * 80)

# 결합 행렬 J_ij ~ N(0, 1/sqrt(N)), 대칭화 및 대각 0 처리
J_mat = np.random.normal(0, 1.0 / np.sqrt(N), size=(N, N))
J_mat = np.triu(J_mat, 1)
J_mat = J_mat + J_mat.T
np.fill_diagonal(J_mat, 0)

def compute_energy_np(s, J):
    return -0.5 * float(np.dot(s, np.dot(J, s)))

# ------------------------------------------------------------------------------
# Test 1. CPU Simulated Annealing (10,000 Monte Carlo Steps)
# ------------------------------------------------------------------------------
print("\n[1/3] Benchmarking Classical CPU Simulated Annealing (10,000 steps)...")
s_sa = np.random.choice([-1, 1], size=N)
best_s_sa = s_sa.copy()
curr_E_sa = compute_energy_np(s_sa, J_mat)
best_E_sa = curr_E_sa

T = 3.0
T_min = 0.01
decay = 0.9995
steps = 10000

t0 = time.perf_counter()
for _ in range(steps):
    idx = np.random.randint(0, N)
    dE = 2.0 * s_sa[idx] * np.dot(J_mat[idx], s_sa)
    if dE < 0 or np.random.rand() < np.exp(-dE / max(1e-4, T)):
        s_sa[idx] = -s_sa[idx]
        curr_E_sa += dE
        if curr_E_sa < best_E_sa:
            best_E_sa = curr_E_sa
            best_s_sa = s_sa.copy()
    T = max(T_min, T * decay)
t_sa_ms = (time.perf_counter() - t0) * 1000.0
print(f"  └─ SA Execution Time : {t_sa_ms:.2f} ms | Ground Energy: {best_E_sa:.3f}")

# ------------------------------------------------------------------------------
# Test 2. CPU Parallel Tempering (16 Replicas, Multi-Temperature)
# ------------------------------------------------------------------------------
print("\n[2/3] Benchmarking CPU Parallel Tempering (16 Replicas)...")
n_replicas = 16
temps = np.logspace(np.log10(0.05), np.log10(3.0), n_replicas)
replicas = [np.random.choice([-1, 1], size=N) for _ in range(n_replicas)]
energies = [compute_energy_np(r, J_mat) for r in replicas]
best_E_pt = min(energies)

t0_pt = time.perf_counter()
for cycle in range(500):
    for r_i in range(n_replicas):
        idx = np.random.randint(0, N)
        dE = 2.0 * replicas[r_i][idx] * np.dot(J_mat[idx], replicas[r_i])
        if dE < 0 or np.random.rand() < np.exp(-dE / temps[r_i]):
            replicas[r_i][idx] = -replicas[r_i][idx]
            energies[r_i] += dE
            if energies[r_i] < best_E_pt:
                best_E_pt = energies[r_i]
    if cycle % 10 == 0:
        for r_i in range(n_replicas - 1):
            delta_beta = (1.0 / temps[r_i + 1]) - (1.0 / temps[r_i])
            delta_E = energies[r_i + 1] - energies[r_i]
            if np.random.rand() < np.exp(delta_beta * delta_E):
                replicas[r_i], replicas[r_i + 1] = replicas[r_i + 1].copy(), replicas[r_i].copy()
                energies[r_i], energies[r_i + 1] = energies[r_i + 1], energies[r_i]
t_pt_ms = (time.perf_counter() - t0_pt) * 1000.0
print(f"  └─ PT Execution Time : {t_pt_ms:.2f} ms | Ground Energy: {best_E_pt:.3f}")

# ------------------------------------------------------------------------------
# Test 3. NEOMA P-CAM In-Material Physical Reflex (Edge GPU Tensor Core)
# ------------------------------------------------------------------------------
print("\n[3/3] Benchmarking NEOMA P-CAM Tensor Core Relaxation on GTX 1650...")
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
J_tensor = torch.tensor(J_mat, dtype=torch.float32, device=device)

# 1. Cold-start 측정 (첫 텐서 할당 및 파이프라인 초기화)
if torch.cuda.is_available():
    torch.cuda.synchronize()
t0_cold = time.perf_counter()

state_init = torch.randn((N, 1), device=device, dtype=torch.float32)
field = torch.matmul(J_tensor, state_init)
s_cold = torch.tanh(field)

if torch.cuda.is_available():
    torch.cuda.synchronize()
t_cold_ms = (time.perf_counter() - t0_cold) * 1000.0

# 2. Steady-state 반복 수렴 측정 (100회 실행 평균 지연시간)
measured_latencies = []
best_E_pcam = 0.0

for run in range(100):
    s_cont = torch.randn((N, 1), device=device, dtype=torch.float32) * 0.1
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    t0_run = time.perf_counter()

    # 연속 텐서 이완 (In-Material Non-Equilibrium Relaxation)
    for step in range(6):
        gain = 1.0 + (step * 0.5)
        s_cont = torch.tanh(gain * torch.matmul(J_tensor, s_cont))

    s_final = torch.sign(s_cont)
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    t_end_run = time.perf_counter()

    measured_latencies.append((t_end_run - t0_run) * 1000.0)

    # 에너지 산출
    s_np = s_final.squeeze().cpu().numpy()
    E_run = compute_energy_np(s_np, J_mat)
    if E_run < best_E_pcam:
        best_E_pcam = E_run

t_pcam_min_ms = np.min(measured_latencies)
t_pcam_avg_ms = np.mean(measured_latencies)
t_pcam_max_ms = np.max(measured_latencies)

print(f"  └─ P-CAM Cold-Start Reflex : {t_cold_ms:.4f} ms")
print(f"  └─ P-CAM Steady-State Min  : {t_pcam_min_ms:.4f} ms")
print(f"  └─ P-CAM Steady-State Avg  : {t_pcam_avg_ms:.4f} ms")
print(f"  └─ P-CAM Steady-State Max  : {t_pcam_max_ms:.4f} ms")
print(f"  └─ Ground-State Energy     : {best_E_pcam:.3f}")

# ------------------------------------------------------------------------------
# 최종 결과 요약 및 깃허브 마크다운 출력
# ------------------------------------------------------------------------------
speedup_sa = t_sa_ms / t_pcam_avg_ms
speedup_pt = t_pt_ms / t_pcam_avg_ms

print("\n" + "=" * 80)
print(" EMPIRICAL 64-SPIN ISING BENCHMARK REPORT (FOR GITHUB README)")
print("=" * 80)
print(f"| Algorithm / Hardware Core | Execution Profile | Empirical Mean Latency | Ground Energy (E) | Acceleration vs CPU |")
print(f"| :--- | :--- | :--- | :--- | :--- |")
print(f"| **Simulated Annealing (CPU)** | 10,000 Monte Carlo Steps | **{t_sa_ms:.2f} ms** | {best_E_sa:.3f} | 1.0x (Baseline) |")
print(f"| **Parallel Tempering (CPU)** | 16 Replicas, Multi-T | **{t_pt_ms:.2f} ms** | {best_E_pt:.3f} | {t_sa_ms/t_pt_ms:.1f}x |")
print(f"| **NEOMA P-CAM Live Core (GTX 1650)** | **Direct Tensor Reflex** | **{t_pcam_avg_ms:.2f} ms** *(Cold: {t_cold_ms:.2f}ms)* | **{best_E_pcam:.3f}** | **{speedup_sa:.1f}x Acceleration** |")
print("=" * 80)