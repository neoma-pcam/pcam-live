"""
NEOMA P-CAM: 3-Year Prognostic Trajectory & Multi-Fault Dataset Generator
=========================================================================
Generates physics-grounded datasets for:
  1. Real-time baseline physical diagnosis (Day 0)
  2. 3-year (1,095-day) long-horizon degradation & prescriptive remediation control
  3. Multi-fault shock simulation & controllable recovery pathways

100% Zero-PRNG (Deterministic trajectory progression + Silicon SEAL-PoPW attestation).
Uses existing Swagger 7-domain endpoints without schema modification.
"""

import argparse
import csv
import os
import requests

BASE_HOST = "neoma-p-cam-hyper-physical-control.p.rapidapi.com"

DOMAIN_ENDPOINTS = {
    "universal": f"https://{BASE_HOST}/v1/solve-universal-equilibrium",
    "battery": f"https://{BASE_HOST}/v1/battery/predict",
    "robotics": f"https://{BASE_HOST}/v1/robotics/predict",
    "mobility": f"https://{BASE_HOST}/v1/mobility/predict",
    "chemistry": f"https://{BASE_HOST}/v1/chemistry/predict",
    "pharma": f"https://{BASE_HOST}/v1/pharma/predict",
    "quant": f"https://{BASE_HOST}/v1/quant/predict",
}


def build_deterministic_scenarios(full_36m: bool = False):
    """Builds deterministic 3-year prognostic horizon + fault-state regimes (Zero-PRNG)."""
    scenarios = []
    step_months = 1 if full_36m else 3  # Default: 13 quarterly points + 3 fault regimes = 16 API calls

    for month in range(0, 37, step_months):
        progress = month / 36.0
        nonlinear_aging = progress ** 1.35
        stage_type = "baseline_diagnosis" if month == 0 else "3yr_prognostic_horizon"
        scenarios.append({
            "horizon_label": f"Month_{month:02d}",
            "elapsed_days": int(round(month * 30.4167)),
            "scenario_type": stage_type,
            "flux_potential_v": round(0.5504 + 0.1450 * nonlinear_aging, 4),
            "gradient_velocity": round(520.0 + 240.0 * progress, 2),
            "gradient_acceleration": round(16000.0 + 6500.0 * nonlinear_aging, 1),
            "active_strain": round(1.10 + 0.58 * progress, 3),
        })

    fault_regimes = [
        {
            "horizon_label": "Fault_01_Thermal_or_Load_Spike",
            "elapsed_days": 1095,
            "scenario_type": "fault_shock_simulation",
            "flux_potential_v": 0.7850,
            "gradient_velocity": 860.0,
            "gradient_acceleration": 26500.0,
            "active_strain": 1.82,
        },
        {
            "horizon_label": "Fault_02_Severe_Nonlinear_Drift",
            "elapsed_days": 1095,
            "scenario_type": "fault_shock_simulation",
            "flux_potential_v": 0.8920,
            "gradient_velocity": 980.0,
            "gradient_acceleration": 32000.0,
            "active_strain": 2.00,
        },
        {
            "horizon_label": "Fault_03_Post_Remediation_Recovery",
            "elapsed_days": 1095,
            "scenario_type": "remediation_verification",
            "flux_potential_v": 0.5620,
            "gradient_velocity": 535.0,
            "gradient_acceleration": 16400.0,
            "active_strain": 1.15,
        },
    ]
    scenarios.extend(fault_regimes)
    return scenarios


def generate_dataset(domain: str, api_key: str, output_csv: str, full_36m: bool = False):
    endpoint = DOMAIN_ENDPOINTS[domain]
    headers = {
        "Content-Type": "application/json",
        "x-rapidapi-host": BASE_HOST,
        "x-rapidapi-key": api_key,
    }

    scenarios = build_deterministic_scenarios(full_36m=full_36m)
    rows = []

    print(f"[*] Generating P-CAM 3-Year Prognostic & Fault Dataset | Domain: {domain} ({len(scenarios)} states)")
    for sc in scenarios:
        payload = {
            "flux_potential_v": sc["flux_potential_v"],
            "gradient_velocity": sc["gradient_velocity"],
            "gradient_acceleration": sc["gradient_acceleration"],
            "active_strain": sc["active_strain"],
        }
        resp = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        res = resp.json()

        row = {
            "horizon_label": sc["horizon_label"],
            "elapsed_days": sc["elapsed_days"],
            "scenario_type": sc["scenario_type"],
            "domain": res.get("domain", domain),
            "flux_potential_v": sc["flux_potential_v"],
            "gradient_velocity": sc["gradient_velocity"],
            "gradient_acceleration": sc["gradient_acceleration"],
            "active_strain": sc["active_strain"],
            "diagnosed_state_mode": res.get("state_mode"),
            "remediation_zeta": res.get("zeta"),
            "control_intensity": res.get("control_intensity"),
            "equilibrium_converged": res.get("equilibrium_converged"),
            "hardware_reflex_ms": res.get("hardware_reflex_ms"),
            "hardware_seal_id": res.get("hardware_seal_id"),
            "cognitive_synthesis": res.get("cognitive_synthesis"),
        }
        rows.append(row)
        print(
            f"  -> {sc['horizon_label']:34s} | Mode: {row['diagnosed_state_mode']} | "
            f"Zeta: {row['remediation_zeta']} | Gain: {row['control_intensity']} | "
            f"Seal: {str(row['hardware_seal_id'])[:26]}..."
        )

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"[+] Saved {len(rows)} verified physical records to: {output_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NEOMA P-CAM 3-Year Prognostic & Fault Dataset Generator")
    parser.add_argument("--domain", choices=list(DOMAIN_ENDPOINTS.keys()), default="universal")
    parser.add_argument("--api-key", default=os.getenv("PCAM_RAPIDAPI_KEY", "YOUR_RAPIDAPI_FREE_KEY"))
    parser.add_argument("--output", default="pcam_3yr_prognostic_fault_dataset.csv")
    parser.add_argument("--full-36m", action="store_true", help="Generate all 36 monthly steps instead of quarterly")
    args = parser.parse_args()

    generate_dataset(args.domain, args.api_key, args.output, args.full_36m)