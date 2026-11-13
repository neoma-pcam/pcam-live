# NEOMA P-CAM MCP Server (`pcam-mcp`)

A native **Rust Model Context Protocol (MCP) server** that lets LLM agents (Claude Desktop, Cursor, Windsurf) offload stiff non-linear physical equilibrium calculations and 64-spin Ising optimization directly to the **NEOMA P-CAM** silicon co-processor via RapidAPI (`2,000 free calls/month`).

## Exposed MCP Tools

| Tool Name | Description |
| :--- | :--- |
| `solve_nonlinear_equilibrium` | Offloads non-linear damping & equilibrium (`flux_potential_v`, `gradient_velocity`, `gradient_acceleration`, `active_strain`) across 7 physical domains (`universal`, `quant`, `robotics`, `battery`, `pharma`, `mobility`, `chemistry`). |
| `solve_ising_optimization` | Maps linear biases ($h_i$) and quadratic couplings ($J_{ij}$) onto the P-CAM 64-spin physical equilibrium core. |
| `verify_silicon_seal` | Audits cryptographic `SEAL-0051003C...` hardware attestation tokens and critical damping bounds ($0.1 \le \zeta \le 2.0$). |

## Build from Source

```bash
cd pcam-mcp
cargo build --release
```

## Claude Desktop / Cursor Configuration

Add the following entry to your `claude_desktop_config.json` or `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "neoma-pcam": {
      "command": "/path/to/pcam-live/pcam-mcp/target/release/pcam-mcp",
      "env": {
        "PCAM_RAPIDAPI_KEY": "YOUR_RAPIDAPI_FREE_KEY"
      }
    }
  }
}
```