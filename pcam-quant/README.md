# P-CAM Quant Core (pcam-quant)

## 📌 Commercial License & Free-Rider Protection Notice

The code and sample client in this package are provided strictly for **academic verification, local latency benchmarking, and objective silicon reflex attestation**.

### 1. Free Evaluation Quota (50 Ticks)
- Public executions are limited to **50 ticks** of live market data for objective attestation.
- Once 50 ticks are processed, the runtime automatically halts.

### 2. Commercial & High-Frequency Trading Policy
- Utilizing P-CAM silicon equilibrium reflex (`zeta`) for live exchange trading, prop trading, algorithmic market making, or slippage elimination without an authorized **RapidAPI Institutional Enterprise License** is strictly prohibited.
- The **$30/mo Universal Solver Plan** is explicitly reserved for academic non-equilibrium physics experiments and does **NOT** grant authorization for live exchange order flows.
- Continuous live exchange streams require verified enterprise authentication via RapidAPI:
  - **Plan**: `RapidAPI Enterprise Quant Tier`
  - **Environment Variable**: `PCAM_RAPIDAPI_KEY`

### 3. Verification Command
```powershell
cargo run --release
