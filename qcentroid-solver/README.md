# NEOMA P-CAM 64-Spin Physical Ising Solver — QCentroid Adapter

Official QCentroid platform solver adapter for the **NEOMA P-CAM 64-Spin Room-Temperature Physical Ising Co-Processor**.

This adapter connects QCentroid Workbench users directly to live physical analog silicon to solve combinatorial optimization problems (Max-Cut, QUBO, and native Ising Hamiltonians) with sub-0.02ms hardware reflex latencies and cryptographic Silicon Root-of-Trust receipts.

---

## Features

- **QCentroid Specification Compliant**: Implements the official `def run(input_data: dict, solver_params: dict, extra_arguments: dict) -> dict:` signature.
- **Zero External Dependencies**: Implemented strictly with the Python Standard Library (`urllib`, `json`, `os`, `logging`).
- **3 Optimization Problem Modes**:
  1. **Max-Cut Graphs** (`adj_matrix`): Automatically converts adjacency / weight matrices to anti-ferromagnetic Ising couplings ($J_{ij} = -W_{ij} / 2$, $h_i = 0$).
  2. **QUBO Optimization** (`qubo_matrix`): Converts binary quadratic models ($x^T Q x$) to Ising variables ($s_i \in \{-1, +1\}$).
  3. **Native 64-Spin Ising** (`fields`, `couplings`): Direct mapping of local magnetic biases $h_i$ and interaction couplings $J_{ij}$.
- **Hardware-Rooted Proofs**: Returns physical execution metrics (`hardware_reflex_ms`), Root-of-Trust token (`hardware_seal_id`), and real-time physical unclonable function seal (`puf_dynamic_seal`).

---

## Configuration & Credentials

In the QCentroid Solver Workbench, configure the following credentials under **Settings / Environment Variables** or pass them via `extra_arguments`:

| Parameter | Required | Description |
| :--- | :---: | :--- |
| `NEOMA_API_KEY` | **Yes** | Your NEOMA Gateway API key (passed via `x-neoma-api-key` header). |
| `NEOMA_GATEWAY_URL` | Optional | Custom gateway URL (defaults to `https://api.neoma-pcam.com/v1/ising/solve`). |

---

## Problem Schemas

### 1. Max-Cut Graph (`adj_matrix`)

Pass an $N \times N$ adjacency matrix (up to 64 nodes):

```python
input_data = {
    "adj_matrix": [
        [0, 1, 0, 1],
        [1, 0, 1, 0],
        [0, 1, 0, 1],
        [1, 0, 1, 0]
    ]
}
```

### 2. QUBO Matrix (`qubo_matrix`)

Pass an $N \times N$ upper-triangular or symmetric QUBO matrix:

```python
input_data = {
    "qubo_matrix": [
        [-1.0,  2.0,  0.0],
        [ 0.0, -1.0,  2.0],
        [ 0.0,  0.0, -1.0]
    ]
}
```

### 3. Native 64-Spin Ising Model

Pass local fields $h_i$ and pairwise couplings $J_{ij}$:

```python
input_data = {
    "num_spins": 4,
    "fields": [0.5, -0.3, 0.2, -0.4],
    "couplings": [
        [0, 1, 1.0],
        [1, 2, -0.8],
        [2, 3, 0.6]
    ]
}
```

---

## Output Response Schema

The solver returns a dictionary with the following fields:

```json
{
  "status": "hardware_active",
  "problem_type": "max_cut",
  "spins": [1, -1, 1, -1],
  "binary_solution": [1, 0, 1, 0],
  "partitions": [1, 0, 1, 0],
  "ground_state_energy": -2.0,
  "magnetization": 0.0,
  "hardware_reflex_ms": 0.0111,
  "hardware_seal_id": "SEAL-0051003C-...",
  "puf_dynamic_seal": "SEAL-PCAM003-COM3-...",
  "firewall_guard": "ACTIVE_RUST_CH17_PUF",
  "num_spins": 4,
  "couplings_count": 4,
  "relaxation_sweeps": 1,
  "equilibrium_converged": true,
  "domain": "Ising-64Spin-Hamiltonian",
  "zeta": 1.05
}
```

- `partitions`: For Max-Cut problems, an array of `0` and `1` indicating the partition assignment for each vertex.
- `hardware_reflex_ms`: Pure physical silicon convergence time in milliseconds.
- `puf_dynamic_seal`: Live cryptographic attestation derived from physical silicon entropy and substrate state.

---

## Local Verification

To run a verification test locally against the live NEOMA P-CAM enclave:

```bash
cd qcentroid-solver
python app.py
```

This runs a 4-node Max-Cut square graph ($C_4$), verifying sub-millisecond physical convergence, spin partitioning, and PUF attestation.
