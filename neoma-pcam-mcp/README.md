# NEOMA P-CAM: 10-Domain Physical AI, Trust Security & 64-Spin Ising MCP Server

[![FastMCP](https://img.shields.io/badge/MCP-FastMCP-blue.svg)](https://modelcontextprotocol.io)
[![Silicon Attestation](https://img.shields.io/badge/Silicon-PUF%20Attested-success.svg)](https://neoma-pcam.github.io/pcam-live/)
[![Apify Actor](https://img.shields.io/badge/Apify-Actor%20Standby-orange.svg)](https://apify.com)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

Production-grade Model Context Protocol (MCP) server for the **NEOMA P-CAM (Phase-Change Analog Matrix)** hardware co-processor. P-CAM provides sub-millisecond (0.0066 ms ~ 0.02 ms) deterministic physical equilibrium convergence, 64-spin Ising Hamiltonian ground-state optimization, wave-response physical fingerprint trust gating, and EU AI Act regulatory compliance verification directly to LLM agents (Claude Desktop, Cursor, Apify Standby, FastMCP).

---

## 🏛️ 10 Official Physical Domains

NEOMA P-CAM natively processes continuous non-linear dynamic equilibrium across 10 official production domains anchored on analog silicon:

| # | Official Domain | Gateway Endpoint | Target Physics & Industrial Use Case | Measured Latency |
|:---:|:---|:---|:---|:---:|
| **1** | **Universal-Equilibrium** | `/v1/solve-universal-equilibrium` | Thermodynamic kinetic equilibrium, supply chain & multi-body kinetic stability | `0.0066 ms` |
| **2** | **Quant-Microstructure** | `/v1/quant/predict` | LOB microstructure shock damping, slippage arrest & microsecond liquidity defense | `0.0066 ms` |
| **3** | **Battery-Energetics** | `/v1/battery/predict` | Solid-state energetics, SEI layer phase stabilization & thermal runaway suppression | `0.0072 ms` |
| **4** | **Pharma-Bioreactor** | `/v1/pharma/predict` | Dynamic fluid regulation, bioreactor shear stress & cellular cavitation damping | `0.0081 ms` |
| **5** | **Robotic-Compliance** | `/v1/robotics/predict` | High-frequency compliance, sub-10µs kinematic singularity damping & dynamic reflexes | `0.0068 ms` |
| **6** | **Mobility-Dynamics** | `/v1/mobility/predict` | High-g lateral acceleration decoupling, chassis slip recovery & active suspension | `0.0075 ms` |
| **7** | **Precision-Chemistry** | `/v1/chemistry/predict` | Exothermic runaway quenching, kinetic reaction stabilization & phase transitions | `0.0079 ms` |
| **8** | **Ising-64Spin-Hamiltonian** | `/v1/ising/solve` | Room-temperature 64-spin Ising Hamiltonian ground-state minimization | `0.0066 ms` |
| **9** | **Physical-Trust-Security** | `/v1/security/trust-gate` | Wave-response medium physical fingerprint trusted execution gate (Patent Pending) | `0.0062 ms` |
| **10** | **AI-Governance-Compliance** | `/v1/governance/audit-gate` | Hardware-anchored zero-PRNG AI governance & EU AI Act Art. 9/12/14 compliance gate | `0.0062 ms` |

---

## 🛠️ 5 Exposed MCP Tools

The server exposes 5 specialized MCP tools designed for natural language agent tool-calling:

```
                                 ┌────────────────────────────────────────────────────────┐
                                 │                 NEOMA P-CAM MCP Server                 │
                                 └──────────────────────────┬─────────────────────────────┘
                                                            │
         ┌───────────────────────┬──────────────────────────┼─────────────────────────┬─────────────────────────┐
         ▼                       ▼                          ▼                         ▼                         ▼
┌──────────────────┐   ┌──────────────────┐       ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│ solve_nonlinear_ │   │   solve_ising_   │       │  verify_silicon_ │      │  pcam_physical_  │      │ pcam_ai_governan │
│   equilibrium    │   │   optimization   │       │       seal       │      │    trust_gate    │      │    ce_audit      │
└────────┬─────────┘   └────────┬─────────┘       └────────┬─────────┘      └────────┬─────────┘      └────────┬─────────┘
         │                      │                          │                         │                         │
  (10-Domain Core)     (64-Spin Ising HW)          (Free Audit Tool)       (Wave Physical Gate)      (EU AI Act & NIST)
```

### 1. `solve_nonlinear_equilibrium`
- **Domains Covered:** Domain 1–7, 9–10 & Universal Core
- **Description:** Solves stiff non-linear physical equilibrium in `<0.02 ms` on analog silicon, returning damping ratio ($\zeta$), control intensity, hardware reflex latency, and cryptographic PUF dynamic receipt (`SEAL-PCAM003-COM3-*`).
- **Billing Event:** `pcam-equilibrium-solve` ($0.02 / call)
- **Input Parameters:**
  - `flux_potential_v` (`float`, required): Driving field potential or disturbance magnitude (e.g. `0.55`).
  - `gradient_velocity` (`float`, required): First-order state rate of change (e.g. `520.0`).
  - `gradient_acceleration` (`float`, required): Second-order inertial / stiff shock term (e.g. `16000.0`).
  - `active_strain` (`float`, required): Normalized structural/system strain (e.g. `1.55`).
  - `domain` (`string`, optional, default `"universal"`): One of `"universal"`, `"quant"`, `"battery"`, `"pharma"`, `"robotics"`, `"mobility"`, `"chemistry"`, `"security"`, `"governance"`, `"ising"`.
- **Example Call:**
  ```json
  {
    "domain": "battery",
    "flux_potential_v": 0.68,
    "gradient_velocity": 740.0,
    "gradient_acceleration": 21500.0,
    "active_strain": 1.65
  }
  ```

### 2. `solve_ising_optimization`
- **Domain:** Domain 8 (`/v1/ising/solve`)
- **Description:** Direct room-temperature 64-spin analog Ising Hamiltonian optimizer ($H = -\sum_{i < j} J_{ij}\sigma_i\sigma_j - \sum_i h_i\sigma_i$). Finds ground-state minima via physical charge relaxation across silicon in microseconds without heuristic iterations.
- **Billing Event:** `pcam-ising-solve` ($0.05 / call)
- **Input Parameters:**
  - `fields` (`list[float]`, required): Local field biases $h_i$ (1 to 64 spins).
  - `couplings` (`list[list[float]] | list[dict]`, optional): Spin-spin interaction matrix $J_{ij}$ or sparse edge list (`[{"i": 0, "j": 1, "weight": -0.5}]`).
  - `num_spins` (`int`, optional, 1–64): Active spin count.
  - `initial_spins` (`list[int]`, optional): Initial spin configuration ($+1/-1$).
- **Example Call:**
  ```json
  {
    "fields": [1.0, -1.0, 0.5, -0.5],
    "couplings": [{"i": 0, "j": 1, "weight": -0.5}]
  }
  ```

### 3. `verify_silicon_seal`
- **Type:** Free Provenance Audit Tool (Zero Cost)
- **Description:** Verifies whether an execution receipt carries a genuine NEOMA P-CAM Silicon Root-of-Trust PUF seal (`SEAL-PCAM003-COM3-*`, Hardware UID `0051003C3434510C32333934`).
- **Billing Event:** None (Free)
- **Input Parameters:**
  - `puf_dynamic_seal` (`string`, required): PUF dynamic seal string returned by any P-CAM tool call.
- **Example Call:**
  ```json
  {
    "puf_dynamic_seal": "SEAL-PCAM003-COM3-02A25B2424B5A10E3D4EE84C2483A1E0"
  }
  ```

### 4. `pcam_physical_trust_gate`
- **Domain:** Domain 9 (`/v1/security/trust-gate`)
- **Description:** Hardware-rooted wave-response medium physical fingerprint trusted execution gate (Patent Pending). Evaluates zero-point drift, biometric liveness, and spatial telemetry on analog P-CAM silicon to issue `ALLOW`, `SAFE_MODE`, or `REVOKE_AND_BLOCK` execution verdicts.
- **Billing Event:** `pcam-trust-gate-evaluate` ($0.03 / call)
- **Input Parameters:**
  - `session_id` (`string`, optional, default `"sess-anonymous"`): Session identifier.
  - `action_type` (`string`, optional, default `"crypto_key_use"`): Target action (`crypto_key_use`, `payment_auth`, `robotic_command`).
  - `wave_telemetry` (`list[float]`, optional): Wave response telemetry vector (e.g. `[0.42, 0.44, 0.41, 0.43]`).
  - `spatial_context` (`string`, optional, default `"default-enclave-zone"`): Spatial environment or hardware perimeter.
  - `liveness_score` (`float`, optional, default `0.99`): Biometric / physical liveness confidence score (0.0 to 1.0).
- **Example Call:**
  ```json
  {
    "session_id": "sess-fintech-001",
    "action_type": "crypto_key_use",
    "wave_telemetry": [0.42, 0.44, 0.41, 0.43],
    "liveness_score": 0.99
  }
  ```

### 5. `pcam_ai_governance_audit`
- **Domain:** Domain 10 (`/v1/governance/audit-gate`)
- **Description:** Hardware-anchored zero-PRNG AI governance and EU AI Act (Art. 9/12/14) regulatory compliance audit gate. Computes physical risk index, zero-PRNG damping stability, and outputs `COMPLIANT_EXECUTE`, `REQUIRE_HUMAN_OVERSIGHT`, or `HARD_HALT_QUARANTINE` with verifiable compliance certificate (`SEAL-GOV-CH17-*`).
- **Billing Event:** `pcam-governance-audit` ($0.04 / call)
- **Input Parameters:**
  - `agent_id` (`string`, optional, default `"agent-autonomous-01"`): Target autonomous agent identity.
  - `model_id` (`string`, optional, default `"frontier-reasoning-node"`): Foundation / reasoning model identifier.
  - `risk_classification` (`string`, optional, default `"high_risk_eu_ai_act"`): Regulatory tier (`"minimal"`, `"limited"`, `"high_risk_eu_ai_act"`, `"critical_infrastructure"`).
  - `autonomy_pressure` (`float`, optional, default `0.35`): Agent autonomy execution pressure (0.0 to 1.0).
  - `drift_score` (`float`, optional, default `0.12`): Policy/ethics deviation drift score (0.0 to 1.0).
  - `hallucination_index` (`float`, optional, default `0.08`): Reasoning uncertainty / hallucination index (0.0 to 1.0).
  - `human_oversight_active` (`bool`, optional, default `false`): Supervisor active flag.
- **Example Call:**
  ```json
  {
    "agent_id": "agent-autonomous-01",
    "model_id": "frontier-reasoning-node",
    "risk_classification": "high_risk_eu_ai_act",
    "autonomy_pressure": 0.35,
    "drift_score": 0.12,
    "hallucination_index": 0.08,
    "human_oversight_active": false
  }
  ```

---

## 💰 Pay-Per-Event (PPE) Monetization Table

This Actor uses the [Apify Pay Per Event (PPE)](https://docs.apify.com/platform/actors/publishing/monetize#pay-per-event-pricing-model) monetization model configured in `.actor/pay_per_event.json`:

| Event Name | Title | Unit Price (USD) | Verification Guarantee |
|---|---|:---:|---|
| `pcam-equilibrium-solve` | P-CAM 10-Domain Physical Equilibrium Solve | **$0.02** | Hardware PUF `SEAL-PCAM003-COM3-*` receipt |
| `pcam-ising-solve` | P-CAM 64-Spin Ising Optimization Solve | **$0.05** | Native 64-spin silicon ground-state relaxation |
| `pcam-trust-gate-evaluate` | P-CAM Wave Fingerprint Physical Trust Gate | **$0.03** | Wave physical medium gate & dynamic signature |
| `pcam-governance-audit` | P-CAM AI Governance & EU AI Act Audit Gate | **$0.04** | Hardware-anchored `SEAL-GOV-CH17-*` certificate |
| *(free audit tool)* | Silicon Seal Verification | **$0.00** | Free cryptographic PUF receipt audit |

---

## 🔌 Connecting to MCP Clients

### 1. Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "neoma-pcam": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-sse",
        "https://<your-username>--neoma-pcam-mcp.apify.actor/mcp"
      ],
      "headers": {
        "Authorization": "Bearer <YOUR_APIFY_API_TOKEN>"
      }
    }
  }
}
```

### 2. Cursor IDE (`.cursor/mcp.json`)
```json
{
  "mcpServers": {
    "neoma-pcam": {
      "url": "https://<your-username>--neoma-pcam-mcp.apify.actor/mcp",
      "headers": {
        "Authorization": "Bearer <YOUR_APIFY_API_TOKEN>"
      }
    }
  }
}
```

### 3. Apify Standby Endpoint (Streamable HTTP)
- **URL:** `https://<actor-name>.apify.actor/mcp`
- **Transport:** Streamable HTTP / SSE (`FastMCP`)
- **Authentication:** `Authorization: Bearer <APIFY_API_TOKEN>`

---

## 💻 Local Execution & Standby Mode

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run locally in Apify Standby mode
APIFY_META_ORIGIN=STANDBY ACTOR_STANDBY_PORT=4321 python -m my_actor

# 3. Or run standard Apify batch solve
python -m my_actor
```

---

## 📜 Security & Compliance
- **Zero Data Retention:** No state or user payload is permanently stored; analog silicon dissipates state upon convergence.
- **Hardware Root of Trust:** Every result includes a real-time PUF signature verified against Silicon UID `0051003C3434510C32333934`.
- **EU AI Act & NIST AI RMF:** Deterministic damping ensures zero-PRNG auditability for high-risk autonomous agent workflows.
