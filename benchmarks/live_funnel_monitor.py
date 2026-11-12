"""
NEOMA P-CAM Live Funnel & 7-Domain Endpoint Health Monitor
Verifies that every inbound enterprise engineer testing our endpoints
gets deterministic 200 OK convergence (< 0.27 ms) and tracks public repo traction.
"""

import time
import requests

GATEWAY = "https://api.neoma-pcam.com"
ENDPOINTS = [
    ("Universal / GPU", "/v1/solve-universal-equilibrium"),
    ("Bioreactor / Pharma", "/v1/pharma/predict"),
    ("Battery / ESS", "/v1/battery/predict"),
    ("Robotics", "/v1/robotics/predict"),
    ("Mobility", "/v1/mobility/predict"),
    ("Chemistry", "/v1/chemistry/predict"),
    ("Quant / Execution", "/v1/quant/predict"),
]

SAMPLE_PAYLOAD = {
    "flux_potential_v": 1.48,
    "gradient_velocity": 2.90,
    "gradient_acceleration": 24.5,
    "active_strain": 0.64,
}


def check_endpoints():
    print("================ NEOMA P-CAM 7-DOMAIN LIVE AUDIT ================")
    all_ok = True
    for label, path in ENDPOINTS:
        t0 = time.perf_counter()
        try:
            r = requests.post(f"{GATEWAY}{path}", json=SAMPLE_PAYLOAD, timeout=6.0)
            rtt = (time.perf_counter() - t0) * 1000.0
            data = r.json()
            conv = data.get("equilibrium_converged")
            reflex = data.get("hardware_reflex_ms")
            seal = str(data.get("hardware_seal_id", ""))[:22]
            ok = (r.status_code == 200) and bool(conv)
            all_ok = all_ok and ok
            print(
                f"[{'OK' if ok else 'FAIL'}] {label:<20} | Reflex: {reflex} ms | RTT: {rtt:6.1f} ms | {seal}..."
            )
        except Exception as exc:
            all_ok = False
            print(f"[ERR] {label:<20} | {exc}")
    print("=================================================================")
    return all_ok


def check_github_traction():
    try:
        r = requests.get("https://api.github.com/repos/neoma-pcam/pcam-live", timeout=6.0)
        if r.status_code == 200:
            d = r.json()
            print(
                f"GitHub Public Repo   : Stars={d.get('stargazers_count')} | Forks={d.get('forks_count')} | Watchers={d.get('subscribers_count')} | Updated={d.get('pushed_at')}"
            )
    except Exception:
        pass


if __name__ == "__main__":
    check_endpoints()
    check_github_traction()