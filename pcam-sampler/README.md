# pcam-sampler

[![PyPI version](https://img.shields.io/pypi/v/pcam-sampler.svg)](https://pypi.org/project/pcam-sampler/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Dimod BQM Compatible compatible In-Material Physical Relaxation Solver for NEOMA P-CAM (authenticated via RapidAPI — **2,000 free solves/month**).

## Installation

```bash
pip install pcam-sampler
```

## Quickstart

```python
import dimod
from pcam_sampler import PCAMSampler

# Define Ising problem (h, J)
h = {0: -0.5, 1: 0.5}
J = {(0, 1): -1.0}
bqm = dimod.BinaryQuadraticModel.from_ising(h, J)

# Sample via P-CAM In-Material Physical Reflex Solver (uses PCAM_RAPIDAPI_KEY or explicit key)
sampler = PCAMSampler(api_key="YOUR_RAPIDAPI_FREE_KEY")
sampleset = sampler.sample(bqm)

print(sampleset.first.sample)
print("Hardware Reflex Latency:", sampleset.info["hardware_reflex_ms"], "ms")
```
