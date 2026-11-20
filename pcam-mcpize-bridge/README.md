# NEOMA P-CAM: Room-Temperature Physical Ising & 10-Domain MCP Server

Deterministic, room-temperature analog silicon 64-spin Ising Hamiltonian solver, 10-domain physical equilibrium, physical-trust security, and AI governance co-processor (`< 0.02 ms` silicon relaxation, Zero-PRNG).

## 🛠️ Official 5 MCP Tools
1. `solve_nonlinear_equilibrium`: Multi-domain physical equilibrium solver across all 10 official domains (`universal`, `quant`, `battery`, `pharma`, `robotics`, `mobility`, `chemistry`, `security`, `governance`, `ising`).
2. `solve_ising_optimization`: Native 64-spin Ising Hamiltonian ground-state minimization on room-temperature silicon.
3. `verify_silicon_seal`: Free provenance audit tool to verify cryptographic PUF dynamic receipts (`SEAL-PCAM003-COM3-*`).
4. `pcam_physical_trust_gate`: Hardware-rooted wave-response medium physical fingerprint trusted execution gate (Patent Pending) (Domain 9).
5. `pcam_ai_governance_audit`: Hardware-anchored zero-PRNG AI governance and EU AI Act regulatory compliance audit gate (Domain 10).

## 🏛️ Domain-Specific & Legacy Compatibility Tools
- `solve_ising_64spin`: Minimize $H = -\sum_{i<j} J_{ij}\sigma_i\sigma_j - \sum_i h_i\sigma_i$ for up to 64 coupled spins (Domain 8).
- `solve_universal_equilibrium`: Sub-ms non-linear physical equilibrium damping solver across 10 domains (Domain 1).
- `predict_battery_energetics`: Electrochemical stress & thermal runaway suppression (`SoC`, `cell_temperature_c`, `c_rate`) (Domain 3).
- `predict_precision_chemistry`: Exothermic quenching & thermal runaway margin (`reactor_temp_k`, `exothermic_heat_flux_w_m2`, `catalyst_activity_index`) (Domain 7).
- `predict_mobility_dynamics`: Hydroplaning recovery & lateral stability (`surface_friction_mu`, `tire_slip_ratio`, `yaw_rate_deg_s`) (Domain 6).
- `predict_quant_microstructure`: Order book shock damping & slice throttle (`order_book_imbalance`, `spread_bps`, `slice_participation_rate`) (Domain 2).
- `predict_robotic_compliance`: Compliant impedance & impact attenuation (`joint_torque_nm`, `contact_stiffness_n_m`, `singularity_proximity`) (Domain 5).
- `predict_pharma_bioreactor`: Cellular viability & shear stress reduction (`impeller_shear_stress_pa`, `dissolved_oxygen_pct`, `broth_viscosity_cp`) (Domain 4).
- `get_pcam_hardware_telemetry`: Live analog silicon substrate telemetry (`V_OUT`, `ENT`, `GEN`, `UID`).

## 🔑 Authentication
Set `NEOMA_API_KEY` in environment variables:
```bash
export NEOMA_API_KEY="<YOUR_NEOMA_API_KEY>"
npm start
```
When set, the bridge automatically attaches `x-neoma-api-key: <key>` and `Authorization: Bearer <key>` to all gateway requests. On startup, the bridge logs `[NEOMA] API key loaded: true/false` without revealing sensitive credentials.
