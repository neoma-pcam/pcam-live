# n8n-nodes-neoma-pcam

Official **n8n** community node for **NEOMA P-CAM** — connect spreadsheets, databases, webhooks, and enterprise workflows directly to the Room-Temperature Physical AI & 64-Spin Ising Solver (**2,000 free calls/month** via RapidAPI).

## Installation in n8n

1. Open your n8n instance and go to **Settings → Community Nodes**.
2. Click **Install a community node** and enter:
   `n8n-nodes-neoma-pcam`
3. Add your **NEOMA P-CAM API** credential using your free or paid [RapidAPI Key](https://rapidapi.com/shs15199702/api/neoma-p-cam-hyper-physical-control).

## Included Operations

- **Industrial Risk & Equilibrium Diagnosis:** Map spreadsheet or database columns (`flux_potential_v`, `gradient_velocity`, `gradient_acceleration`, `active_strain`) across 10 operational domains (Universal Supply Chain, Quant Execution, Battery Thermal Safety, Chemical Process, Biopharma, Mobility, Robotics, 64-Spin Ising, Physical Trust & Security, AI Governance & Compliance) and receive `zeta`, `control_intensity`, `action_recommendation`, and cryptographic `SEAL-PoPW` receipts.
- **64-Spin Combinatorial Optimization:** Offload routing, scheduling, and resource allocation matrices (`fields`, `couplings`) to `/v1/ising/solve` in sub-millisecond hardware time.
## One-Click Workflow Template

Copy the contents of [examples/pcam_operations_workflow.json](examples/pcam_operations_workflow.json) and paste directly onto any n8n workflow canvas (`Ctrl+V` / `Cmd+V`) to run an end-to-end physical risk diagnosis and alert pipeline.
