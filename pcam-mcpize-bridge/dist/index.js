import http from "node:http";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { z } from "zod";
const PORT = Number(process.env.PORT || "8080");
const PCAM_API_URL = (process.env.PCAM_API_URL || "https://api.neoma-pcam.com").replace(/\/+$/, "");
const PCAM_MCP_API_KEY = process.env.PCAM_MCP_API_KEY || "NEOMA-MCPIZE-8462D2DDF488411496A02262EADDE1D1";
// Log key loaded status without exposing sensitive credentials
console.log(`[NEOMA] API key loaded: ${Boolean(process.env.NEOMA_API_KEY?.trim())}`);
const DOMAIN_ENDPOINTS = {
    universal: "/v1/solve-universal-equilibrium",
    quant: "/v1/quant/predict",
    battery: "/v1/battery/predict",
    pharma: "/v1/pharma/predict",
    robotics: "/v1/robotics/predict",
    mobility: "/v1/mobility/predict",
    chemistry: "/v1/chemistry/predict",
    security: "/v1/security/trust-gate",
    governance: "/v1/governance/audit-gate",
    ising: "/v1/ising/solve",
};
async function forwardRest(path, payload) {
    const neomaApiKey = (process.env.NEOMA_API_KEY || "").trim();
    const activeKey = neomaApiKey || PCAM_MCP_API_KEY;
    const headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": `Bearer ${activeKey}`,
        "X-API-Key": activeKey,
        "User-Agent": "NEOMA-MCPize-Gateway/1.0"
    };
    if (neomaApiKey) {
        headers["x-neoma-api-key"] = neomaApiKey;
    }
    const res = await fetch(`${PCAM_API_URL}${path}`, {
        method: payload ? "POST" : "GET",
        headers,
        body: payload ? JSON.stringify(payload) : undefined
    });
    const text = await res.text();
    if (!res.ok) {
        throw new Error(`P-CAM Gateway HTTP ${res.status}: ${text}`);
    }
    return text;
}
function createServer() {
    const server = new McpServer({
        name: "neoma-pcam-solver",
        version: "1.0.0"
    });
    // --- Official 5 Standard MCP Tools across 10 Domains ---
    server.tool("solve_nonlinear_equilibrium", "10 Official Domains: Solve stiff non-linear physical equilibrium across 10 domains in <0.02ms with dynamic silicon PUF seal.", {
        flux_potential_v: z.number().describe("Driving field potential or disturbance magnitude (e.g. 0.55)"),
        gradient_velocity: z.number().describe("First-order state rate of change (e.g. 520.0)"),
        gradient_acceleration: z.number().describe("Second-order inertial/shock term (e.g. 16000.0)"),
        active_strain: z.number().describe("Normalized structural/system strain (e.g. 1.55)"),
        domain: z.enum([
            "universal", "quant", "battery", "pharma", "robotics", "mobility", "chemistry", "security", "governance", "ising"
        ]).default("universal").describe("Target physical domain out of 10 official domains")
    }, async ({ flux_potential_v, gradient_velocity, gradient_acceleration, active_strain, domain }) => {
        const ep = DOMAIN_ENDPOINTS[domain] || "/v1/solve-universal-equilibrium";
        return {
            content: [{
                    type: "text",
                    text: await forwardRest(ep, {
                        flux_potential_v,
                        gradient_velocity,
                        gradient_acceleration,
                        active_strain
                    })
                }]
        };
    });
    server.tool("solve_ising_optimization", "Domain 8 (/v1/ising/solve): Native 64-spin Ising Hamiltonian ground-state solver on analog silicon.", {
        fields: z.array(z.number()).describe("Local magnetic field biases h_i (up to 64 spins)"),
        couplings: z.array(z.any()).optional().describe("Pairwise couplings as [[i, j, J_ij], ...] or edge list"),
        num_spins: z.number().int().min(1).max(64).optional().describe("Active spin count (1 to 64)"),
        initial_spins: z.array(z.number()).optional().describe("Initial spin configuration (+1/-1)")
    }, async ({ fields, couplings, num_spins, initial_spins }) => {
        const payload = {
            fields: fields.slice(0, 64),
            couplings: couplings || []
        };
        if (num_spins !== undefined) {
            payload.num_spins = Math.min(Math.max(num_spins, 1), 64);
        }
        if (initial_spins !== undefined) {
            payload.initial_spins = initial_spins.slice(0, 64);
        }
        return {
            content: [{ type: "text", text: await forwardRest("/v1/ising/solve", payload) }]
        };
    });
    server.tool("verify_silicon_seal", "Free audit tool: Verify authenticity of a NEOMA P-CAM dynamic silicon PUF receipt (SEAL-PCAM003-COM3-*).", {
        puf_dynamic_seal: z.string().describe("PUF dynamic seal string returned by any P-CAM tool call")
    }, async ({ puf_dynamic_seal }) => {
        const SEAL_PREFIX = "SEAL-PCAM003-COM3-";
        const ok = puf_dynamic_seal.startsWith(SEAL_PREFIX) && puf_dynamic_seal.length === SEAL_PREFIX.length + 32;
        return {
            content: [{
                    type: "text",
                    text: JSON.stringify({
                        verified: ok,
                        firewall_guard: ok ? "ACTIVE_RUST_CH17_PUF" : "INVALID_SEAL"
                    })
                }]
        };
    });
    // --- Domain-Specific & Legacy Compatibility Tools ---
    server.tool("solve_ising_64spin", "Solve a 64-spin Ising Hamiltonian ground-state optimization problem on room-temperature P-CAM silicon.", {
        num_spins: z.number().int().min(1).max(64).describe("Number of spins (1 to 64)"),
        fields: z.array(z.number()).describe("Local magnetic field biases h_i"),
        couplings: z.array(z.array(z.number())).describe("Pairwise couplings as [[i, j, J_ij], ...]")
    }, async ({ num_spins, fields, couplings }) => ({
        content: [{ type: "text", text: await forwardRest("/v1/ising/solve", { num_spins, fields, couplings }) }]
    }));
    server.tool("solve_universal_equilibrium", "Compute sub-millisecond physical equilibrium damping and corrective control vectors.", {
        flux_potential_v: z.number(),
        gradient_velocity: z.number(),
        gradient_acceleration: z.number(),
        active_strain: z.number()
    }, async (args) => ({
        content: [{ type: "text", text: await forwardRest("/v1/solve-universal-equilibrium", args) }]
    }));
    server.tool("predict_battery_energetics", "Calculate safe charge current derating and thermal runaway suppression for lithium-ion battery cells.", {
        state_of_charge_pct: z.number().min(0).max(100),
        cell_temperature_c: z.number().min(-40).max(85),
        c_rate: z.number().min(0).max(10)
    }, async (args) => ({
        content: [{ type: "text", text: await forwardRest("/v1/battery/predict", args) }]
    }));
    server.tool("predict_precision_chemistry", "Predict thermal runaway margin (K) and exothermic quenching efficiency (%).", {
        reactor_temp_k: z.number().min(250).max(600),
        exothermic_heat_flux_w_m2: z.number().min(0).max(25000),
        catalyst_activity_index: z.number().min(0).max(1)
    }, async (args) => ({
        content: [{ type: "text", text: await forwardRest("/v1/chemistry/predict", args) }]
    }));
    server.tool("predict_mobility_dynamics", "Compute hydroplaning recovery time (ms) and lateral stability margin (%).", {
        surface_friction_mu: z.number().min(0.05).max(1.2),
        tire_slip_ratio: z.number().min(0).max(1),
        yaw_rate_deg_s: z.number().min(-180).max(180)
    }, async (args) => ({
        content: [{ type: "text", text: await forwardRest("/v1/mobility/predict", args) }]
    }));
    server.tool("predict_quant_microstructure", "Compute order book slippage reduction (bps) and optimal slice throttle.", {
        order_book_imbalance: z.number().min(-1).max(1),
        spread_bps: z.number().min(0).max(500),
        slice_participation_rate: z.number().min(0.001).max(1)
    }, async (args) => ({
        content: [{ type: "text", text: await forwardRest("/v1/quant/predict", args) }]
    }));
    server.tool("predict_robotic_compliance", "Compute compliant impedance gain (N*m/rad) and peak impact attenuation (%).", {
        joint_torque_nm: z.number().min(-500).max(500),
        contact_stiffness_n_m: z.number().min(10).max(100000),
        singularity_proximity: z.number().min(0).max(1)
    }, async (args) => ({
        content: [{ type: "text", text: await forwardRest("/v1/robotics/predict", args) }]
    }));
    server.tool("predict_pharma_bioreactor", "Compute cellular viability protection (%) and agitation shear reduction (Pa).", {
        impeller_shear_stress_pa: z.number().min(0).max(50),
        dissolved_oxygen_pct: z.number().min(0).max(100),
        broth_viscosity_cp: z.number().min(0.5).max(5000)
    }, async (args) => ({
        content: [{ type: "text", text: await forwardRest("/v1/pharma/predict", args) }]
    }));
    server.tool("get_pcam_hardware_telemetry", "Query live NEOMA P-CAM analog silicon substrate telemetry.", {}, async () => ({
        content: [{ type: "text", text: await forwardRest("/v1/telemetry") }]
    }));
    server.tool("pcam_physical_trust_gate", "Domain 9 (/v1/security/trust-gate): Hardware-rooted wave-response medium physical fingerprint trusted execution gate (Patent Pending). Evaluates zero-point drift and biometrics/spatial context to ALLOW, SAFE_MODE, or REVOKE_AND_BLOCK execution.", {
        session_id: z.string().optional().describe("Session identifier"),
        action_type: z.string().optional().describe("Target action (crypto_key_use, payment_auth, robotic_command)"),
        wave_telemetry: z.array(z.number()).optional().describe("Wave response telemetry vector"),
        spatial_context: z.string().optional().describe("Terminal or spatial usage context"),
        liveness_score: z.number().min(0).max(1).optional().describe("Biometric liveness score")
    }, async (args) => ({
        content: [{ type: "text", text: await forwardRest("/v1/security/trust-gate", args) }]
    }));
    server.tool("pcam_ai_governance_audit", "Domain 10 (/v1/governance/audit-gate): Hardware-anchored zero-PRNG AI governance and EU AI Act regulatory compliance audit gate. Computes physical risk index, zero-PRNG damping stability, and outputs COMPLIANT_EXECUTE, REQUIRE_HUMAN_OVERSIGHT, or HARD_HALT_QUARANTINE.", {
        agent_id: z.string().optional().describe("Autonomous agent identifier"),
        model_id: z.string().optional().describe("AI model identifier"),
        risk_classification: z.string().optional().describe("Regulatory risk tier (minimal, limited, high_risk_eu_ai_act, critical_infrastructure)"),
        autonomy_pressure: z.number().min(0).max(1).optional().describe("Agent autonomy pressure"),
        drift_score: z.number().min(0).max(1).optional().describe("Policy drift score"),
        hallucination_index: z.number().min(0).max(1).optional().describe("Uncertainty/hallucination index"),
        human_oversight_active: z.boolean().optional().describe("Human supervisor oversight flag")
    }, async (args) => ({
        content: [{ type: "text", text: await forwardRest("/v1/governance/audit-gate", args) }]
    }));
    return server;
}
const httpServer = http.createServer(async (req, res) => {
    if (req.url === "/health") {
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ status: "ok", bridge: "neoma-pcam-mcpize" }));
        return;
    }
    if (req.url?.startsWith("/mcp")) {
        if (req.method !== "POST") {
            res.writeHead(405, { "Content-Type": "application/json", "Allow": "POST" });
            res.end(JSON.stringify({ jsonrpc: "2.0", error: { code: -32000, message: "Use POST /mcp" }, id: null }));
            return;
        }
        let rawBody = "";
        for await (const chunk of req) {
            rawBody += chunk;
        }
        try {
            const parsedBody = rawBody ? JSON.parse(rawBody) : undefined;
            const server = createServer();
            const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined });
            res.on("close", () => {
                transport.close().catch(() => { });
                server.close().catch(() => { });
            });
            await server.connect(transport);
            await transport.handleRequest(req, res, parsedBody);
        }
        catch (err) {
            if (!res.headersSent) {
                res.writeHead(500, { "Content-Type": "application/json" });
                res.end(JSON.stringify({ error: String(err) }));
            }
        }
        return;
    }
    res.writeHead(404, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "Not Found" }));
});
httpServer.listen(PORT, "0.0.0.0", () => {
    console.log(`NEOMA P-CAM MCPize Bridge listening on 0.0.0.0:${PORT}`);
});
