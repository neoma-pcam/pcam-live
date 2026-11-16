"""
PCAMSampler: dimod BQM Compatible In-Material Physical Ising Solver
"""
import os
from typing import Optional
from urllib.parse import urlparse
import requests
import dimod


class PCAMSampler(dimod.Sampler):
    """
    Standard dimod.Sampler interface connected directly to the
    NEOMA P-CAM 64-Spin Room-Temperature Physical Ising Solver (/v1/ising/solve).
    """

    properties = {
        "description": "NEOMA P-CAM 64-Spin Room-Temperature Physical Ising Solver",
        "version": "1.0.3",
        "max_variables": 64,
        "category": "physical_in_material_ising_solver",
    }
    parameters = {
        "api_key": [],
        "rapidapi_key": [],
        "timeout": [],
    }

    DEFAULT_ENDPOINT = "https://neoma-p-cam-hyper-physical-control.p.rapidapi.com/v1/ising/solve"
    DEFAULT_RAPIDAPI_HOST = "neoma-p-cam-hyper-physical-control.p.rapidapi.com"

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: str = DEFAULT_ENDPOINT,
        rapidapi_key: Optional[str] = None,
        timeout: float = 10.0,
    ):
        if api_key and api_key.startswith(("http://", "https://")):
            endpoint = api_key
            api_key = None

        self.endpoint = endpoint
        self.rapidapi_key = api_key or rapidapi_key or os.getenv("PCAM_RAPIDAPI_KEY")
        self.timeout = timeout

    def sample(self, bqm: dimod.BinaryQuadraticModel, **parameters) -> dimod.SampleSet:
        """
        Submits a dimod BinaryQuadraticModel directly to the P-CAM physical Ising solver
        and returns the converged ground-state SampleSet with hardware attestation.
        """
        variables = list(bqm.variables)
        n_vars = len(variables)
        if n_vars == 0:
            return dimod.SampleSet.from_samples_bqm([{}], bqm)
        if n_vars > 64:
            raise ValueError(
                f"NEOMA P-CAM 64-spin physical core supports up to 64 variables (got {n_vars})."
            )

        linear, quadratic, _ = bqm.to_ising()
        var_to_idx = {v: idx for idx, v in enumerate(variables)}

        fields = [round(-float(linear.get(v, 0.0)), 6) for v in variables]
        couplings = [
            [var_to_idx[u], var_to_idx[v], round(-float(w), 6)]
            for (u, v), w in quadratic.items()
            if u != v and abs(w) > 0.0
        ]

        payload = {
            "num_spins": n_vars,
            "fields": fields,
            "couplings": couplings,
        }

        headers = {"Content-Type": "application/json"}
        parsed_host = urlparse(self.endpoint).netloc.lower()
        if self.rapidapi_key and "rapidapi.com" in parsed_host:
            headers["x-rapidapi-host"] = parsed_host or self.DEFAULT_RAPIDAPI_HOST
            headers["x-rapidapi-key"] = self.rapidapi_key

        req_timeout = float(parameters.get("timeout", self.timeout))
        try:
            resp = requests.post(self.endpoint, json=payload, headers=headers, timeout=req_timeout)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            raise RuntimeError(f"NEOMA P-CAM Enclave Request Failed: {exc}") from exc

        raw_spins = data.get("spins")
        if not isinstance(raw_spins, list) or len(raw_spins) < n_vars:
            raise RuntimeError(f"Unexpected response from P-CAM enclave: {data}")

        if bqm.vartype == dimod.BINARY:
            sample_result = {
                var: (1 if int(raw_spins[idx]) >= 0 else 0)
                for idx, var in enumerate(variables)
            }
        else:
            sample_result = {
                var: (1 if int(raw_spins[idx]) >= 0 else -1)
                for idx, var in enumerate(variables)
            }

        info = {
            "domain": data.get("domain", "Ising-64Spin-Hamiltonian"),
            "zeta": data.get("zeta"),
            "hardware_reflex_ms": data.get("hardware_reflex_ms"),
            "hardware_seal_id": data.get("hardware_seal_id"),
            "telemetry": data.get("telemetry", {}),
        }

        return dimod.SampleSet.from_samples_bqm([sample_result], bqm, info=info)