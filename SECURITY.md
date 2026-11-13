# Security Policy & Zero-Retention Architecture

## 1. Architectural Security Guarantees

NEOMA P-CAM is designed as a **stateless, hardware-isolated physical co-processor**. Enterprise security teams, CISOs, and infrastructure auditors can independently verify the following five guarantees:

1. **Zero Raw Data Egress (4-Scalar Boundary Normalization):**
   Proprietary source code, neural weights, prompts, raw sensor streams, and PII never leave client infrastructure. Client-side middleware normalizes local state into **4 dimensionless boundary scalars** (`flux_potential_v`, `gradient_velocity`, `gradient_acceleration`, `active_strain`) totaling under 200 bytes per HTTPS TLS 1.3 request.
2. **End-to-End Stateless Pass-Through (Zero Data Accumulation):**
   Neither the client middleware wrapper nor the NEOMA API gateway (`api.neoma-pcam.com` / RapidAPI) logs, stores, aggregates, or retains customer request payloads. Client traffic is never written to persistent storage or used to train models.
3. **Hardware-Level Air-Gapped Silicon Isolation:**
   The P-CAM 003 room-temperature analog silicon substrate possesses **no Flash, SSD, or addressable non-volatile memory**. Physical charge dissipates into equilibrium (`zeta`, `control_intensity`) in under `0.02 ms` and resets immediately, making cross-tenant data persistence or extraction physically impossible.
4. **0ms Fail-Safe Circuit Breaker:**
   Client middleware wrappers enforce strict sub-second timeouts and immediately bypass (`0 ms`) to local fallback control if network connectivity degrades, ensuring uninterrupted availability.
5. **Cryptographic Auditability Without Data Retention (`SEAL-PoPW`):**
   Every response returns a single-use SHA-256 hardware attestation seal (`hardware_seal_id`) bound to silicon UID `0051003C3434510C32333934`, allowing clients to maintain tamper-proof compliance logs locally without storing payloads on external servers.

## 2. Independent Client-Side Verification Tools

Before deploying in production, security engineers can run two open-source verification scripts directly inside their firewall boundary:

* **Outbound Zero-Leak Packet Auditor:** [`examples/verify_zero_leak_packet.py`](examples/verify_zero_leak_packet.py) — Inspects exact serialized HTTP bytes leaving the client host and verifies zero proprietary strings, tensors, or PII are transmitted.
* **Zero-Trust Silicon Attestation Verifier:** [`pcam_objective_audit.py`](pcam_objective_audit.py) — Audits Round-Trip Time (RTT), damping convergence (`0.1 <= zeta <= 2.0`), and live hardware `SEAL-PoPW` signatures.

## 3. Supported Versions

| Version | Component | Security Support |
| :--- | :--- | :--- |
| `v5.3.x` | Production API Gateway & Client SDKs (`Python`, `Rust MCP`, `ROS 2`) | Active |
| `< v5.3` | Legacy Pre-v5.3 Interfaces | End of Life |

## 4. Reporting a Vulnerability

If you discover a potential security issue in our public client SDKs, MCP server, or API gateway boundary, please report it responsibly rather than opening a public issue:

* **Security & Engineering Contact:** `contact@neoma-pcam.com`
* **Executive Office:** `ceo@neoma-pcam.com`
* **Response SLA:** Initial acknowledgment within **24 hours**, with reproducible mitigation guidance provided as soon as verified.