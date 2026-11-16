# pcam-sampler

[![PyPI version](https://img.shields.io/pypi/v/pcam-sampler.svg)]([https://pypi.org/project/pcam-sampler/](https://pypi.org/project/pcam-sampler/))
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

`dimod.Sampler` compatible client for the **NEOMA P-CAM 64-Spin Room-Temperature Physical Ising Solver** (`/v1/ising/solve` — **2,000 free solves/month** via RapidAPI).

## Installation

```bash
pip install pcam-sampler
```

## Quickstart

```python
import dimod
from pcam_sampler import PCAMSampler

# Define Ising or QUBO problem (up to 64 coupled spins)
h = {0: -0.5, 1: 0.5}
J = {(0, 1): -1.0}
bqm = dimod.BinaryQuadraticModel.from_ising(h, J)

# Solve directly on NEOMA P-CAM physical silicon enclave
sampler = PCAMSampler(api_key="YOUR_RAPIDAPI_FREE_KEY")
sampleset = sampler.sample(bqm)

print("Ground-State Sample :", sampleset.first.sample)
print("Hamiltonian Energy  :", sampleset.first.energy)
print("Silicon Reflex (ms) :", sampleset.info["hardware_reflex_ms"])
print("Hardware SEAL-PoPW  :", sampleset.info["hardware_seal_id"])
```