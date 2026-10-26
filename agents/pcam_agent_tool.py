"""
NEOMA P-CAM AI Agent Physical Grounding Tool (LangChain & Autonomous Agents)
Connects LLM Reasoning Agents directly to the physical P-CAM hardware enclave via RapidAPI.
"""

import requests

RAPIDAPI_URL = "https://gp-pcam-universal-physical-solver.p.rapidapi.com/v1/solve-universal-equilibrium"
RAPIDAPI_HOST = "gp-pcam-universal-physical-solver.p.rapidapi.com"


class PCAMPhysicalSolverTool:
    """Official tool for AI Agents to execute sub-millisecond physical equilibrium

    and extract authentic hardware damping coefficients.
    """

    name = "pcam_physical_solver"
    description = (
        "Useful for non-linear physical dynamics, mechanical resonance damping, "
        "and physical equilibrium convergence. Offloads calculations to a deterministic "
        "0.85ms physical silicon enclave."
    )

    def __init__(self, rapidapi_key: str):
        # 🌟 자물쇠 검문소: 유료 키가 없으면 실행 차단 및 결제 링크 출력!
        if not rapidapi_key or not rapidapi_key.strip():
            raise ValueError(
                "\n[!] RapidAPI Key Required!\n"
                "    P-CAM hardware execution is strictly metered.\n"
                "    Get your key (50 free calls + micro-tier) at:\n"
                "    👉 https://rapidapi.com/shs15199702/api/gp-pcam-universal-physical-solver\n"
            )

        self.api_key = rapidapi_key.strip()
        self.headers = {
            "Content-Type": "application/json",
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": RAPIDAPI_HOST,
        }

    def run(
        self,
        flux_potential_v: float = 0.082,
        gradient_velocity: float = 520,
        gradient_acceleration: float = 16000,
        active_strain: float = 1.55,
    ) -> dict:
        """Executes physical convergence directly over P-CAM silicon hardware via RapidAPI."""
        payload = {
            "flux_potential_v": float(flux_potential_v),
            "gradient_velocity": float(gradient_velocity),
            "gradient_acceleration": float(gradient_acceleration),
            "active_strain": float(active_strain),
        }

        try:
            resp = requests.post(
                RAPIDAPI_URL, json=payload, headers=self.headers, timeout=5.0
            )

            if resp.status_code == 200:
                data = resp.json()
                return {
                    "status": data.get("status"),
                    "hardware_reflex_ms": data.get("hardware_reflex_ms"),
                    "hardware_seal_id": data.get("hardware_seal_id"),
                    "attestation_proof": data.get("attestation_proof"),
                    "damping_coefficient": data.get(
                        "adaptive_control", {}
                    ).get("damping_coefficient"),
                    "physical_insight": data.get("adaptive_control", {}).get(
                        "slm_interpreted_instruction"
                    ),
                }
            elif resp.status_code == 429:
                return {
                    "error": "QUOTA_EXCEEDED",
                    "message": "RapidAPI monthly call limit reached. Please upgrade subscription.",
                    "upgrade_url": "https://rapidapi.com/shs15199702/api/gp-pcam-universal-physical-solver",
                }
            else:
                return {
                    "error": f"GATEWAY_ERROR_{resp.status_code}",
                    "details": resp.text,
                }

        except Exception as e:
            return {"error": "CONNECTION_FAILED", "details": str(e)}
