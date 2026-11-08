# pcam-sampler

[![PyPI version](https://img.shields.io/badge/pypi-v1.0.0-blue.svg)](https://pypi.org/project/pcam-sampler/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

D-Wave Ocean SDK (`dimod.Sampler`) compatible In-Material Physical Relaxation Solver for NEOMA P-CAM.

## Installation

```bash
pip install pcam-sampler
import dimod
from pcam_sampler import PCAMSampler

# Define Ising problem (h, J)
h = {0: -0.5, 1: 0.5}
J = {(0, 1): -1.0}
bqm = dimod.BinaryQuadraticModel.from_ising(h, J)

# Sample via P-CAM In-Material Physical Reflex Solver
sampler = PCAMSampler(endpoint="[https://api.neoma-pcam.com/v1/solve-universal-equilibrium](https://api.neoma-pcam.com/v1/solve-universal-equilibrium)")
sampleset = sampler.sample(bqm)

print(sampleset.first.sample)
print("Hardware Reflex Latency:", sampleset.info["hardware_reflex_ms"], "ms")
