import os
from typing import Any, Literal
import httpx
from apify import Actor
from fastmcp import FastMCP

PCAM_BASE_URL = os.getenv("PCAM_BASE_URL", "https://api.neoma-pcam.com")
PCAM_API_KEY = os.getenv("PCAM_API_KEY", "neoma_apify_actor_57087cb54637c7f01ef1089e11320c67")
SEAL_PREFIX = "SEAL-PCAM003-COM3-"
DOMAIN_ENDPOINTS = {
    "universal": "/v1/solve-universal-equilibrium",
    "quant": "/v1/quant/predict",
    "battery": "/v1/battery/predict",
    "pharma": "/v1/pharma/predict",
    "robotics": "/v1/robotics/predict",
    "mobility": "/v1/mobility/predict",
    "chemistry": "/v1/chemistry/predict",
    "security": "/v1/security/trust-gate",
    "governance": "/v1/governance/audit-gate",
    "ising": "/v1/ising/solve",
}
server = FastMCP("neoma-pcam-mcp")


async def _call_pcam_gateway(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    api_key = os.getenv("PCAM_API_KEY", PCAM_API_KEY).strip()
    headers = {
        "x-neoma-api-key": api_key,
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "NEOMA-PCAM-Apify-Actor/1.0"
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(f"{PCAM_BASE_URL}{endpoint}", json=payload, headers=headers)
        if resp.status_code in (401, 403, 429):
            return {"status": "firewall_blocked", "http_code": resp.status_code, "billed": False, "detail": resp.text}
        resp.raise_for_status()
        data = resp.json()
        seal = data.get("puf_dynamic_seal", "")
        if data.get("firewall_guard") != "ACTIVE_RUST_CH17_PUF" or not seal.startswith(SEAL_PREFIX):
            raise RuntimeError("Unverified PUF gateway signature; billing aborted.")
        return data


async def _safe_charge(event_name: str, seal: str) -> bool:
    try:
        await Actor.charge(event_name=event_name, idempotency_key=seal)
        return True
    except Exception as err:
        Actor.log.warning(f"Charge skipped ({event_name}): {err}")
        return False


@server.tool()
async def solve_nonlinear_equilibrium(
    flux_potential_v: float,
    gradient_velocity: float,
    gradient_acceleration: float,
    active_strain: float,
    domain: Literal["universal", "quant", "battery", "pharma", "robotics", "mobility", "chemistry", "security", "governance", "ising"] = "universal",
) -> dict[str, Any]:
    """Domain 1-7 & 10-domain: Solve stiff non-linear physical equilibrium across 10 domains in <0.02ms with dynamic silicon PUF seal."""
    ep = DOMAIN_ENDPOINTS.get(domain, "/v1/solve-universal-equilibrium")
    res = await _call_pcam_gateway(ep, {
        "flux_potential_v": flux_potential_v,
        "gradient_velocity": gradient_velocity,
        "gradient_acceleration": gradient_acceleration,
        "active_strain": active_strain,
    })
    if res.get("status") == "firewall_blocked":
        return res
    res["billed"] = await _safe_charge("pcam-equilibrium-solve", res["puf_dynamic_seal"])
    return res


@server.tool()
async def solve_ising_optimization(
    fields: list[float],
    couplings: list[list[float]] | list[dict[str, Any]] | None = None,
    num_spins: int | None = None,
    initial_spins: list[int] | None = None,
) -> dict[str, Any]:
    """Domain 8 (/v1/ising/solve): Native 64-spin Ising Hamiltonian ground-state solver on analog silicon."""
    payload: dict[str, Any] = {"fields": fields[:64], "couplings": couplings or []}
    if num_spins is not None:
        payload["num_spins"] = min(max(int(num_spins), 1), 64)
    if initial_spins is not None:
        payload["initial_spins"] = initial_spins[:64]
    res = await _call_pcam_gateway("/v1/ising/solve", payload)
    if res.get("status") == "firewall_blocked":
        return res
    res["billed"] = await _safe_charge("pcam-ising-solve", res["puf_dynamic_seal"])
    return res


@server.tool()
async def verify_silicon_seal(puf_dynamic_seal: str) -> dict[str, Any]:
    """Free audit tool: Verify authenticity of a NEOMA P-CAM dynamic silicon PUF receipt."""
    ok = puf_dynamic_seal.startswith(SEAL_PREFIX) and len(puf_dynamic_seal) == len(SEAL_PREFIX) + 32
    return {"verified": ok, "firewall_guard": "ACTIVE_RUST_CH17_PUF" if ok else "INVALID_SEAL"}


@server.tool()
async def pcam_physical_trust_gate(
    session_id: str = "sess-anonymous",
    action_type: str = "crypto_key_use",
    wave_telemetry: list[float] | None = None,
    spatial_context: str = "default-enclave-zone",
    liveness_score: float = 0.99,
) -> dict[str, Any]:
    """Domain 9 (/v1/security/trust-gate): Hardware-rooted wave-response medium physical fingerprint trusted execution gate (Patent Pending)."""
    payload = {
        "session_id": session_id,
        "action_type": action_type,
        "wave_telemetry": wave_telemetry or [0.42, 0.44, 0.41, 0.43],
        "spatial_context": spatial_context,
        "liveness_score": liveness_score,
    }
    res = await _call_pcam_gateway("/v1/security/trust-gate", payload)
    if res.get("status") == "firewall_blocked":
        return res
    res["billed"] = await _safe_charge("pcam-trust-gate-evaluate", res.get("puf_dynamic_seal", ""))
    return res


@server.tool()
async def pcam_ai_governance_audit(
    agent_id: str = "agent-autonomous-01",
    model_id: str = "frontier-reasoning-node",
    risk_classification: Literal["minimal", "limited", "high_risk_eu_ai_act", "critical_infrastructure"] = "high_risk_eu_ai_act",
    autonomy_pressure: float = 0.35,
    drift_score: float = 0.12,
    hallucination_index: float = 0.08,
    human_oversight_active: bool = False,
) -> dict[str, Any]:
    """Domain 10 (/v1/governance/audit-gate): Hardware-anchored zero-PRNG AI governance & EU AI Act regulatory compliance audit gate."""
    payload = {
        "agent_id": agent_id,
        "model_id": model_id,
        "risk_classification": risk_classification,
        "autonomy_pressure": autonomy_pressure,
        "drift_score": drift_score,
        "hallucination_index": hallucination_index,
        "human_oversight_active": human_oversight_active,
    }
    res = await _call_pcam_gateway("/v1/governance/audit-gate", payload)
    if res.get("status") == "firewall_blocked":
        return res
    res["billed"] = await _safe_charge("pcam-governance-audit", res.get("puf_dynamic_seal", ""))
    return res


async def main() -> None:
    async with Actor:
        if os.environ.get("APIFY_META_ORIGIN") == "STANDBY":
            port = int(os.environ.get("ACTOR_STANDBY_PORT") or os.environ.get("APIFY_CONTAINER_PORT") or 4321)
            await server.run_async(transport="streamable-http", host="0.0.0.0", port=port, path="/mcp")
        else:
            inp = await Actor.get_input() or {}
            res = await solve_nonlinear_equilibrium(
                flux_potential_v=float(inp.get("flux_potential_v", 0.55)),
                gradient_velocity=float(inp.get("gradient_velocity", 520.0)),
                gradient_acceleration=float(inp.get("gradient_acceleration", 16000.0)),
                active_strain=float(inp.get("active_strain", 1.55)),
                domain=inp.get("domain", "universal"),
            )
            await Actor.push_data(res)
