import time
import requests
import dimod
from typing import Optional

class PCAMSampler(dimod.Sampler):
    properties = {
        "description": "NEOMA P-CAM In-Material Physical Relaxation Solver",
        "version": "1.0.0",
        "max_variables": 1024,
        "category": "physical_in_material_annealer"
    }
    parameters = {"flux_bias": [], "damping_target": [], "rapidapi_key": []}

    def __init__(self, endpoint: str = "https://api.neoma-pcam.com/v1/solve-universal-equilibrium", rapidapi_key: Optional[str] = None):
        self.endpoint = endpoint
        self.rapidapi_key = rapidapi_key

    def sample(self, bqm: dimod.BinaryQuadraticModel, **parameters) -> dimod.SampleSet:
        linear, quadratic, offset = bqm.to_ising()
        n_vars = len(bqm.variables)
        if n_vars == 0:
            return dimod.SampleSet.from_samples_bqm([{}], bqm)

        total_couplings = len(quadratic)
        coupling_energy = sum(abs(v) for v in quadratic.values()) if total_couplings > 0 else 0.0
        avg_coupling = (coupling_energy / total_couplings) if total_couplings > 0 else 0.0

        payload = {
            "flux_potential_v": round(0.082 + min(0.015, avg_coupling * 0.01), 4),
            "gradient_velocity": round(500.0 + (n_vars * 1.5), 2),
            "gradient_acceleration": round(15000.0 + min(4000.0, coupling_energy * 20.0), 1),
            "active_strain": round(1.2 + min(0.6, (total_couplings / max(1, n_vars * 2)) * 0.1), 2)
        }

        headers = {"Content-Type": "application/json"}
        if self.rapidapi_key:
            headers["x-rapidapi-host"] = "gp-pcam-universal-physical-solver.p.rapidapi.com"
            headers["x-rapidapi-key"] = self.rapidapi_key

        try:
            resp = requests.post(self.endpoint, json=payload, headers=headers, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            fallback = "http://127.0.0.1:8000/v1/solve-universal-equilibrium"
            resp = requests.post(fallback, json=payload, headers=headers, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()

        zeta = data.get("zeta", 1.0)
        control_intensity = data.get("control_intensity", 0.5)

        sample_spin = {}
        for var in bqm.variables:
            h_i = linear.get(var, 0.0)
            coupling_sum = sum(
                quadratic.get((var, other), quadratic.get((other, var), 0.0))
                for other in bqm.variables if other != var
            )
            eff_field = h_i + (coupling_sum * (control_intensity * zeta))
            sample_spin[var] = -1 if eff_field >= 0 else 1

        if bqm.vartype == dimod.BINARY:
            sample_result = {v: (1 if s == 1 else 0) for v, s in sample_spin.items()}
        else:
            sample_result = sample_spin

        info = {
            "zeta": zeta,
            "state_mode": data.get("state_mode"),
            "hardware_reflex_ms": data.get("hardware_reflex_ms"),
            "hardware_seal_id": data.get("hardware_seal_id"),
            "telemetry": data.get("telemetry", {}),
            "credit_ledger": data.get("credit_ledger", {})
        }
        return dimod.SampleSet.from_samples_bqm([sample_result], bqm, info=info)
