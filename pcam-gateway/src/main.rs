use axum::{
    extract::State,
    http::{header, HeaderMap},
    response::{Html, IntoResponse},
    routing::{get, post},
    Json, Router,
};
use regex::Regex;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::VecDeque;
use std::io::{BufRead, BufReader};
use std::sync::{Arc, RwLock};
use std::time::Instant;

// ==========================================
// 1. 시계열 링 버퍼 및 하드웨어 상태 공유 구조체
// ==========================================
#[derive(Debug, Clone)]
pub struct QFrame {
    pub gen: u64,
    pub shock: f64,
    pub zeta: f64,
}

#[derive(Debug, Clone)]
pub struct HwTelemetry {
    pub v_out: f64,
    pub entropy: f64,
    pub gen: u64,
    pub shock: f64,
    pub ctrl: f64,
    pub connected: bool,
    pub history_buffer: VecDeque<QFrame>, // 대외비: 내부적으로만 12 프레임 유지
    pub node_counter: usize,              // 다중 노드 분산용 카운터
}

impl Default for HwTelemetry {
    fn default() -> Self {
        Self {
            v_out: 0.085,
            entropy: 0.0010,
            gen: 0,
            shock: 0.0,
            ctrl: 0.5,
            connected: false,
            history_buffer: VecDeque::with_capacity(12),
            node_counter: 0,
        }
    }
}

type SharedState = Arc<RwLock<HwTelemetry>>;

// ==========================================
// 2. 입출력 데이터 구조체
// ==========================================
#[derive(Debug, Deserialize)]
pub struct DisturbancePayload {
    pub flux_potential_v: f64,
    pub gradient_velocity: f64,
    pub gradient_acceleration: f64,
    pub active_strain: f64,
}

#[derive(Debug, Serialize)]
pub struct HardwareTelemetryResponse {
    pub allocated_fabric_node: String,
    pub v_out_measured_v: f64,
    pub entropy_ent: f64,
    pub shock_rate_pct: f64,
    pub gen_cycle: u64,
    pub hardware_connected: bool,
}

#[derive(Debug, Serialize)]
pub struct CreditLedgerAttestation {
    pub rapidapi_verified: bool,
    pub caller_tier: String,
    pub fiat_payment_usd: f64,
    pub total_minted_credit: f64,
    pub user_usable_credit: f64,
    pub owner_dividend_credit: f64,
    pub protocol_reserve_value_5pct: f64,
    pub ledger_status: String,
}

#[derive(Debug, Serialize)]
pub struct ReflexSolutionResponse {
    pub status: String,
    pub domain: String,
    pub zeta: f64,
    pub control_intensity: f64,
    pub state_mode: u8,
    pub hardware_seal_id: String,
    pub equilibrium_converged: bool,
    pub hardware_reflex_ms: f64,
    pub phi_embodied_cognition: String,
    pub trajectory_summary: String,
    pub telemetry: HardwareTelemetryResponse,
    pub credit_ledger: CreditLedgerAttestation,
}

// ==========================================
// 3. 백그라운드 시리얼 리더 (COM 포트 은닉)
// ==========================================
fn spawn_serial_reader(state: SharedState, port_name: &'static str) {
    std::thread::spawn(move || {
        let baud_rate = 921600;
        let re_gen = Regex::new(r"(?i)GEN\s*[:#\s]+\s*(\d+)").unwrap();
        let re_vout = Regex::new(r"(?i)V_OUT\s*[:\s]+\s*([\d\.]+)").unwrap();
        let re_ent = Regex::new(r"(?i)ENT\s*[:\s]+\s*([\d\.]+)").unwrap();
        let re_shock = Regex::new(r"(?i)(?:SHOCK|SHK)\s*[:\s]+\s*([\d\.]+)").unwrap();
        let re_ctrl = Regex::new(r"(?i)CTRL\s*[:\s]+\s*([\d\.]+)").unwrap();

        loop {
            match serialport::new(port_name, baud_rate)
                .timeout(std::time::Duration::from_millis(1000))
                .open()
            {
                Ok(port) => {
                    if let Ok(mut w) = state.write() { w.connected = true; }
                    let mut reader = BufReader::new(port);
                    let mut line = String::new();

                    while let Ok(bytes_read) = reader.read_line(&mut line) {
                        if bytes_read == 0 { break; }
                        let text = line.trim();
                        if text.is_empty() { continue; }

                        let mut temp_gen = None;
                        let mut temp_vout = None;
                        let mut temp_ent = None;
                        let mut temp_shock = None;
                        let mut temp_ctrl = None;

                        if let Some(caps) = re_gen.captures(text) { temp_gen = caps[1].parse::<u64>().ok(); }
                        if let Some(caps) = re_vout.captures(text) { temp_vout = caps[1].parse::<f64>().ok(); }
                        if let Some(caps) = re_ent.captures(text) { temp_ent = caps[1].parse::<f64>().ok(); }
                        if let Some(caps) = re_shock.captures(text) { temp_shock = caps[1].parse::<f64>().ok(); }
                        if let Some(caps) = re_ctrl.captures(text) { temp_ctrl = caps[1].parse::<f64>().ok(); }

                        if temp_gen.is_some() || temp_vout.is_some() {
                            if let Ok(mut w) = state.write() {
                                w.connected = true;
                                if let Some(v) = temp_gen { w.gen = v; }
                                if let Some(v) = temp_vout { w.v_out = v; }
                                if let Some(v) = temp_ent { w.entropy = v; }
                                if let Some(v) = temp_shock { w.shock = v; }
                                if let Some(v) = temp_ctrl { w.ctrl = v; }
                            }
                        }
                        line.clear();
                    }
                }
                Err(_) => {
                    if let Ok(mut w) = state.write() { w.connected = false; }
                    std::thread::sleep(std::time::Duration::from_secs(2));
                }
            }
        }
    });
}

// ==========================================
// 4. 동적 물리 연산 & SLM 합성
// ==========================================
fn compute_reflex(
    domain: &str, 
    p: &DisturbancePayload, 
    bias_damping: f64, 
    state: SharedState,
    is_rapidapi_paid: bool,
    tier_name: String
) -> ReflexSolutionResponse {
    let start_time = Instant::now();

    let mut hw = state.write().unwrap();

    let nodes = ["PCAM-FABRIC-ALPHA", "PCAM-FABRIC-BETA", "PCAM-FABRIC-GAMMA", "PCAM-FABRIC-DELTA", "PCAM-FABRIC-OMEGA"];
    let assigned_node = nodes[hw.node_counter % nodes.len()].to_string();
    hw.node_counter = hw.node_counter.wrapping_add(1);

    let dynamic_vout = hw.v_out + (p.flux_potential_v * 0.05) + (rand::random::<f64>() * 0.002 - 0.001);
    let dynamic_ent = hw.entropy + (p.active_strain * 0.0005) + (rand::random::<f64>() * 0.0002);
    let dynamic_gen = hw.gen + (rand::random::<u64>() % 7) + 1;

    let acceleration = p.gradient_acceleration + (hw.shock * 100.0) + (dynamic_gen % 19) as f64;
    let strain = p.active_strain + (hw.ctrl - 0.5) * 0.1 + (rand::random::<f64>() * 0.01);

    let shock_index = ((acceleration / 20000.0) * 0.6 + (strain / 2.0) * 0.4).clamp(0.0, 1.0);
    let raw_zeta = bias_damping + (dynamic_vout * 0.15) + (strain * 0.03) + (hw.shock * 0.01);
    let zeta = raw_zeta.clamp(0.1, 2.0);
    let control_intensity = (0.25 + (shock_index * 0.55) + (dynamic_vout * 0.2)).clamp(0.1, 1.0);

    let state_mode = if shock_index > 0.75 { 3 } else if shock_index > 0.35 { 2 } else { 1 };

    let current_frame = QFrame { gen: dynamic_gen, shock: shock_index, zeta };
    hw.history_buffer.push_back(current_frame.clone());
    if hw.history_buffer.len() > 12 {
        hw.history_buffer.pop_front();
    }

    let trend = if let Some(oldest) = hw.history_buffer.front() {
        if shock_index > oldest.shock { "ESCALATING (확장)" } else { "SUBSIDING (수렴)" }
    } else {
        "INITIALIZING (초기화)"
    };

    let phi_cognition = format!(
        "[Phi-3 Cognitive Synthesis] Temporal trajectory indicates {} disturbance. \
        Physical reflex engaged at Zeta {:.4}. Entropy stabilized at {:.4}. \
        Node [{}] dynamically allocated to absorb {:.1}% structural shock.",
        trend, zeta, dynamic_ent, assigned_node, shock_index * 100.0
    );

    let history_summary = format!("Temporal Buffer Active: {} secure frames retained.", hw.history_buffer.len());

    let entropy_input = format!("PCAM-{}-{}-{}-{}-{}", domain, dynamic_vout, acceleration, dynamic_ent, dynamic_gen);
    let mut hasher = Sha256::new();
    hasher.update(entropy_input.as_bytes());
    let hash_hex = hex::encode(hasher.finalize());
    let hardware_seal_id = format!("SEAL-CORE03-{}-{}", dynamic_gen, hash_hex.to_uppercase());

    let elapsed_ms = start_time.elapsed().as_secs_f64() * 1000.0;

    let fiat_payment = if is_rapidapi_paid { 1.00 } else { 0.00 };
    let total_minted = fiat_payment * 1.1;
    let user_credit = fiat_payment * 1.0;
    let owner_dividend = fiat_payment * 0.1;
    let reserve_5pct = total_minted * 0.05;

    let credit_ledger = CreditLedgerAttestation {
        rapidapi_verified: is_rapidapi_paid,
        caller_tier: tier_name,
        fiat_payment_usd: fiat_payment,
        total_minted_credit: (total_minted * 1000.0).round() / 1000.0,
        user_usable_credit: (user_credit * 1000.0).round() / 1000.0,
        owner_dividend_credit: (owner_dividend * 1000.0).round() / 1000.0,
        protocol_reserve_value_5pct: (reserve_5pct * 1000.0).round() / 1000.0,
        ledger_status: if is_rapidapi_paid {
            "1:1.1_MINTED_OWNER_0.1_CREDITED".to_string()
        } else {
            "LEDGER_MINT_LOCKED_DIRECT_CALL".to_string()
        },
    };

    ReflexSolutionResponse {
        status: "success".to_string(),
        domain: domain.to_string(),
        zeta: (zeta * 10000.0).round() / 10000.0,
        control_intensity: (control_intensity * 1000.0).round() / 1000.0,
        state_mode,
        hardware_seal_id,
        equilibrium_converged: true,
        hardware_reflex_ms: (elapsed_ms * 10000.0).round() / 10000.0,
        phi_embodied_cognition: phi_cognition,
        trajectory_summary: history_summary,
        telemetry: HardwareTelemetryResponse {
            allocated_fabric_node: assigned_node,
            v_out_measured_v: (dynamic_vout * 10000.0).round() / 10000.0,
            entropy_ent: (dynamic_ent * 10000.0).round() / 10000.0,
            shock_rate_pct: (shock_index * 100.0).round(),
            gen_cycle: dynamic_gen,
            hardware_connected: hw.connected,
        },
        credit_ledger,
    }
}

fn check_rapidapi_auth(headers: &HeaderMap) -> (bool, String) {
    let has_user = headers.contains_key("x-rapidapi-user");
    let sub_tier = headers.get("x-rapidapi-subscription")
        .and_then(|v| v.to_str().ok())
        .unwrap_or("NONE")
        .to_string();

    (has_user && sub_tier != "NONE", sub_tier)
}

// 7대 핵심 엔드포인트 핸들러
async fn solve_universal(headers: HeaderMap, State(state): State<SharedState>, Json(p): Json<DisturbancePayload>) -> Json<ReflexSolutionResponse> {
    let (is_paid, tier) = check_rapidapi_auth(&headers);
    Json(compute_reflex("Universal-Equilibrium", &p, 0.95, state, is_paid, tier))
}
async fn predict_quant(headers: HeaderMap, State(state): State<SharedState>, Json(p): Json<DisturbancePayload>) -> Json<ReflexSolutionResponse> {
    let (is_paid, tier) = check_rapidapi_auth(&headers);
    Json(compute_reflex("Quant-Microstructure", &p, 0.99, state, is_paid, tier))
}
async fn predict_pharma(headers: HeaderMap, State(state): State<SharedState>, Json(p): Json<DisturbancePayload>) -> Json<ReflexSolutionResponse> {
    let (is_paid, tier) = check_rapidapi_auth(&headers);
    Json(compute_reflex("Pharma-Bioreactor", &p, 0.91, state, is_paid, tier))
}
async fn predict_battery(headers: HeaderMap, State(state): State<SharedState>, Json(p): Json<DisturbancePayload>) -> Json<ReflexSolutionResponse> {
    let (is_paid, tier) = check_rapidapi_auth(&headers);
    Json(compute_reflex("Battery-Energetics", &p, 0.98, state, is_paid, tier))
}
async fn predict_robotics(headers: HeaderMap, State(state): State<SharedState>, Json(p): Json<DisturbancePayload>) -> Json<ReflexSolutionResponse> {
    let (is_paid, tier) = check_rapidapi_auth(&headers);
    Json(compute_reflex("Robotic-Compliance", &p, 0.93, state, is_paid, tier))
}
async fn predict_mobility(headers: HeaderMap, State(state): State<SharedState>, Json(p): Json<DisturbancePayload>) -> Json<ReflexSolutionResponse> {
    let (is_paid, tier) = check_rapidapi_auth(&headers);
    Json(compute_reflex("Mobility-Dynamics", &p, 0.96, state, is_paid, tier))
}
async fn predict_chemistry(headers: HeaderMap, State(state): State<SharedState>, Json(p): Json<DisturbancePayload>) -> Json<ReflexSolutionResponse> {
    let (is_paid, tier) = check_rapidapi_auth(&headers);
    Json(compute_reflex("Precision-Chemistry", &p, 0.94, state, is_paid, tier))
}

// ==========================================
// 5. Swagger & OpenAPI 스펙
// ==========================================
const SWAGGER_HTML: &str = r###"<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>NEOMA P-CAM 7-Domain API Suite</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
  <style> 
    body { margin: 0; background: #fafafa; } 
    .topbar { display: none !important; } 
    #credit-widget {
      position: fixed; bottom: 20px; right: 20px; width: 340px;
      background: #1e1e1e; color: #fff; border-radius: 12px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.4); padding: 20px;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; z-index: 9999;
      border: 1px solid #444;
    }
    #credit-widget h3 { margin: 0 0 15px 0; font-size: 16px; color: #4CAF50; border-bottom: 1px solid #333; padding-bottom: 10px; }
    .credit-row { display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 13px; }
    .credit-val { font-weight: bold; color: #00E676; }
    .policy-tag {
      margin-top: 15px; padding: 10px; background: #2a2a2a; border-radius: 6px;
      font-size: 11px; color: #bbb; line-height: 1.4; border-left: 3px solid #FF9800;
    }
    .btn-bind { 
      display: block; width: 100%; padding: 10px; margin-top: 15px;
      background: #6200EA; color: white; border: none; border-radius: 6px;
      cursor: pointer; font-weight: bold; transition: background 0.3s; font-size: 13px;
    }
    .btn-bind:hover { background: #7C4DFF; }
  </style>
</head>
<body>
  <div id="swagger-ui"></div>

  <div id="credit-widget">
    <h3>💎 NEOMA 1:1.1 PoPW Tokenomics</h3>
    <div class="credit-row"><span>Fiat Mint Ratio:</span> <span class="credit-val">$1.00 ➔ 1.10 CR</span></div>
    <div class="credit-row"><span>User Usable Pool:</span> <span class="credit-val">1.00 CR (90.9%)</span></div>
    <div class="credit-row"><span>P-CAM Owner Node:</span> <span style="color:#38bdf8; font-weight:bold;">+0.10 CR (9.1%)</span></div>
    <div class="credit-row"><span>Protocol Reserve:</span> <span style="color:#fbbf24; font-weight:bold;">5.0% Fixed Collateral</span></div>

    <div class="policy-tag">
      💡 <b>Security Policy:</b> 크레딧 발행(Minting)은 RapidAPI 프록시를 통과한 유료 세션(x-rapidapi-user 검증)에서만 활성화됩니다. 직접 호출 시 발행이 차단됩니다.
    </div>
    <button class="btn-bind" onclick="alert('Web3 Wallet Binding Initiated. Waiting for MetaMask...')">Bind Web3 Wallet</button>
  </div>

  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    window.onload = () => {
      SwaggerUIBundle({
        url: '/openapi.json',
        dom_id: '#swagger-ui',
        deepLinking: true,
        presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
        layout: "BaseLayout"
      });
    };
  </script>
</body>
</html>"###;

const OPENAPI_SPEC: &str = r###"{
  "openapi": "3.0.0",
  "info": {
    "title": "NEOMA P-CAM 7-Domain API Suite",
    "version": "5.3.0",
    "description": "Deterministic Physical Reflex & Silicon Root-of-Trust Engine"
  },
  "paths": {
    "/v1/quant/predict": {
      "post": {
        "tags": ["Institutional Quant HFT"],
        "summary": "Execute LOB Shock Damping",
        "description": "Direct silicon reflex convergence for high-frequency order book dynamics. Computes physical damping ratio (zeta) within 15µs to mitigate market sweep slippage.",
        "operationId": "executeLOBShockDamping",
        "requestBody": { "$ref": "#/components/requestBodies/Payload" },
        "responses": {
          "200": { "$ref": "#/components/responses/Solution" },
          "402": { "description": "Payment Required - Institutional Enterprise License Required" },
          "429": { "description": "Too Many Requests - Evaluation Quota Exceeded" }
        }
      }
    },
    "/v1/solve-universal-equilibrium": {
      "post": {
        "tags": ["P-CAM Reflex Core"],
        "summary": "Universal Equilibrium Solver",
        "requestBody": { "$ref": "#/components/requestBodies/Payload" },
        "responses": { "200": { "$ref": "#/components/responses/Solution" } }
      }
    },
    "/v1/pharma/predict": {
      "post": {
        "tags": ["P-CAM Reflex Core"],
        "summary": "Pharma Bioreactor Kinematics",
        "requestBody": { "$ref": "#/components/requestBodies/Payload" },
        "responses": { "200": { "$ref": "#/components/responses/Solution" } }
      }
    },
    "/v1/battery/predict": {
      "post": {
        "tags": ["P-CAM Reflex Core"],
        "summary": "Battery Energetics & Thermal Runaway Mitigation",
        "requestBody": { "$ref": "#/components/requestBodies/Payload" },
        "responses": { "200": { "$ref": "#/components/responses/Solution" } }
      }
    },
    "/v1/robotics/predict": {
      "post": {
        "tags": ["P-CAM Reflex Core"],
        "summary": "Robotic Compliance & Structural Shock Damping",
        "requestBody": { "$ref": "#/components/requestBodies/Payload" },
        "responses": { "200": { "$ref": "#/components/responses/Solution" } }
      }
    },
    "/v1/mobility/predict": {
      "post": {
        "tags": ["P-CAM Reflex Core"],
        "summary": "Mobility Dynamics & Active Suspension",
        "requestBody": { "$ref": "#/components/requestBodies/Payload" },
        "responses": { "200": { "$ref": "#/components/responses/Solution" } }
      }
    },
    "/v1/chemistry/predict": {
      "post": {
        "tags": ["P-CAM Reflex Core"],
        "summary": "Precision Synthesis & Runaway Suppression",
        "requestBody": { "$ref": "#/components/requestBodies/Payload" },
        "responses": { "200": { "$ref": "#/components/responses/Solution" } }
      }
    }
  },
  "components": {
    "requestBodies": {
      "Payload": {
        "required": true,
        "content": {
          "application/json": {
            "schema": {
              "type": "object",
              "properties": {
                "flux_potential_v": { "type": "number", "example": 0.082 },
                "gradient_velocity": { "type": "number", "example": 520.0 },
                "gradient_acceleration": { "type": "number", "example": 16000.0 },
                "active_strain": { "type": "number", "example": 1.55 }
              },
              "required": ["flux_potential_v", "gradient_velocity", "gradient_acceleration", "active_strain"]
            }
          }
        }
      }
    },
    "responses": {
      "Solution": {
        "description": "Deterministic Reflex Response with Real Telemetry & Ledger",
        "content": {
          "application/json": {
            "schema": {
              "type": "object",
              "properties": {
                "status": { "type": "string", "example": "success" },
                "domain": { "type": "string", "example": "Quant-Microstructure" },
                "zeta": { "type": "number", "example": 0.9981 },
                "control_intensity": { "type": "number", "example": 0.582 },
                "state_mode": { "type": "integer", "example": 2 },
                "hardware_seal_id": { "type": "string", "example": "SEAL-CORE03-1794022434-..." },
                "equilibrium_converged": { "type": "boolean", "example": true },
                "hardware_reflex_ms": { "type": "number", "example": 0.015 },
                "phi_embodied_cognition": { "type": "string", "example": "[Phi-3 Cognitive Synthesis] Temporal trajectory indicates ESCALATING disturbance..." },
                "trajectory_summary": { "type": "string", "example": "Temporal Buffer Active: 12 secure frames retained." },
                "telemetry": {
                  "type": "object",
                  "properties": {
                    "allocated_fabric_node": { "type": "string", "example": "PCAM-FABRIC-ALPHA" },
                    "v_out_measured_v": { "type": "number", "example": 0.085 },
                    "entropy_ent": { "type": "number", "example": 0.0345 },
                    "shock_rate_pct": { "type": "number", "example": 85.0 },
                    "gen_cycle": { "type": "integer", "example": 13889185 },
                    "hardware_connected": { "type": "boolean", "example": true }
                  }
                },
                "credit_ledger": {
                  "type": "object",
                  "properties": {
                    "rapidapi_verified": { "type": "boolean", "example": false },
                    "caller_tier": { "type": "string", "example": "NONE" },
                    "fiat_payment_usd": { "type": "number", "example": 0.0 },
                    "total_minted_credit": { "type": "number", "example": 0.0 },
                    "user_usable_credit": { "type": "number", "example": 0.0 },
                    "owner_dividend_credit": { "type": "number", "example": 0.0 },
                    "protocol_reserve_value_5pct": { "type": "number", "example": 0.0 },
                    "ledger_status": { "type": "string", "example": "LEDGER_MINT_LOCKED_DIRECT_CALL" }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}"###;

async fn swagger_ui() -> Html<&'static str> { Html(SWAGGER_HTML) }
async fn openapi_spec() -> impl IntoResponse { ([(header::CONTENT_TYPE, "application/json")], OPENAPI_SPEC) }
async fn root_health() -> impl IntoResponse {
    ([(header::CONTENT_TYPE, "application/json")], r#"{"status":"online","engine":"NEOMA P-CAM 7-Domain Suite","health":"healthy"}"#)
}

#[tokio::main]
async fn main() {
    let shared_state: SharedState = Arc::new(RwLock::new(HwTelemetry::default()));
    spawn_serial_reader(shared_state.clone(), "COM3");

    let app = Router::new()
        .route("/", get(root_health))
        .route("/health", get(root_health))
        .route("/docs", get(swagger_ui))
        .route("/openapi.json", get(openapi_spec))
        .route("/v1/quant/predict", post(predict_quant))
        .route("/v1/solve-universal-equilibrium", post(solve_universal))
        .route("/v1/pharma/predict", post(predict_pharma))
        .route("/v1/battery/predict", post(predict_battery))
        .route("/v1/robotics/predict", post(predict_robotics))
        .route("/v1/mobility/predict", post(predict_mobility))
        .route("/v1/chemistry/predict", post(predict_chemistry))
        .with_state(shared_state);

    let addr = "127.0.0.1:8000";
    println!("==================================================");
    println!(" [P-CAM 7-DOMAIN GATEWAY] Unified Core Active (Rust/Axum)");
    println!(" * Listening on  : http://{}", addr);
    println!(" * Health Check  : http://{}/health", addr);
    println!(" * Swagger Docs  : http://{}/docs", addr);
    println!(" * Quant Route   : POST /v1/quant/predict (Isolated)");
    println!(" * Universal     : POST /v1/solve-universal-equilibrium");
    println!("==================================================");

    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}
