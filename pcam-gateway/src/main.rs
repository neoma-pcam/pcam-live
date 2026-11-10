use axum::{
    extract::State,
    http::{HeaderMap, StatusCode},
    response::IntoResponse,
    routing::post,
    Json, Router,
};
use regex::Regex;
use reqwest::Client;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{HashMap, VecDeque};
use std::io::{BufRead, BufReader};
use std::sync::{atomic::{AtomicUsize, Ordering}, Arc, RwLock};
use std::time::Instant;

// ==========================================
// 1. 하드웨어 상태 및 원장(Ledger) 구조체
// ==========================================
#[derive(Debug, Clone)]
pub struct QFrame {
    pub gen: u64,
    pub shock: f64,
    pub zeta: f64,
}

#[derive(Debug, Clone)]
pub struct HwTelemetry {
    pub uid: String,
    pub v_out: f64,
    pub entropy: f64,
    pub gen: u64,
    pub shock: f64,
    pub ctrl: f64,
    pub connected: bool,
    pub history_buffer: VecDeque<QFrame>,
}

impl Default for HwTelemetry {
    fn default() -> Self {
        Self {
            uid: "3511733393432".to_string(),
            v_out: 0.0, entropy: 0.0, gen: 0, shock: 0.0, ctrl: 0.5,
            connected: false,
            history_buffer: VecDeque::with_capacity(12),
        }
    }
}

// [신규] 이중 가치 평가 모델 원장 상태
#[derive(Debug, Default)]
pub struct LedgerState {
    pub user_balances: HashMap<String, f64>, // 고객별 CR 잔고
    pub owner_dividend_cr: f64,              // 오너 기여 배당 (0.10 CR 누적)
    pub protocol_reserve_usd: f64,           // 프로토콜 준비금 ($0.10 누적)
    pub total_minted_cr: f64,                // 총 발행량
    pub total_burned_cr: f64,                // 총 소각량 (연산 및 리딤)
}

pub struct AppState {
    pub hw: Arc<RwLock<HwTelemetry>>,
    pub http_client: Client,
    pub demo_counter: AtomicUsize,
    pub ledger: Arc<RwLock<LedgerState>>,
}
type SharedState = Arc<AppState>;

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
    pub hardware_uid: String,
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
    pub redeem_reserve_usd_10pct: f64,
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
    pub cognitive_synthesis: String,
    pub trajectory_summary: String,
    pub telemetry: HardwareTelemetryResponse,
    pub credit_ledger: CreditLedgerAttestation,
}

#[derive(Debug, Serialize)]
pub struct ErrorResponse {
    pub error: String,
    pub code: u16,
    pub message: String,
}

#[derive(Debug, Deserialize)]
pub struct RedeemRequest {
    pub amount_cr: f64,
}

#[derive(Debug, Serialize)]
pub struct RedeemResponse {
    pub status: String,
    pub user_id: String,
    pub redeemed_cr: f64,
    pub payout_usd: f64,
    pub remaining_reserve_usd: f64,
    pub message: String,
}

// ==========================================
// 3. 백그라운드 시리얼 리더 (순수 실측)
// ==========================================
fn spawn_serial_reader(hw_state: Arc<RwLock<HwTelemetry>>, port_name: String) {
    std::thread::spawn(move || {
        let baud_rate = 921600;
        let re_gen = Regex::new(r"(?i)GEN\s*[:#\s]+\s*(\d+)").unwrap();
        let re_vout = Regex::new(r"(?i)V_OUT\s*[:\s]+\s*([\d\.]+)").unwrap();
        let re_ent = Regex::new(r"(?i)ENT\s*[:\s]+\s*([\d\.]+)").unwrap();
        let re_shock = Regex::new(r"(?i)(?:SHOCK|SHK)\s*[:\s]+\s*([\d\.]+)").unwrap();
        let re_ctrl = Regex::new(r"(?i)CTRL\s*[:\s]+\s*([\d\.]+)").unwrap();
        let re_uid = Regex::new(r"(?i)UID\s*[:\s]+\s*([A-Za-z0-9]+)").unwrap();

        loop {
            match serialport::new(&port_name, baud_rate).timeout(std::time::Duration::from_millis(1000)).open() {
                Ok(port) => {
                    if let Ok(mut w) = hw_state.write() { w.connected = true; }
                    let mut reader = BufReader::new(port);
                    let mut line = String::new();
                    while let Ok(bytes_read) = reader.read_line(&mut line) {
                        if bytes_read == 0 { break; }
                        let text = line.trim();
                        if text.is_empty() { continue; }
                        if let Ok(mut w) = hw_state.write() {
                            w.connected = true;
                            if let Some(caps) = re_gen.captures(text) { w.gen = caps[1].parse().unwrap_or(w.gen); }
                            if let Some(caps) = re_vout.captures(text) { w.v_out = caps[1].parse().unwrap_or(w.v_out); }
                            if let Some(caps) = re_ent.captures(text) { w.entropy = caps[1].parse().unwrap_or(w.entropy); }
                            if let Some(caps) = re_shock.captures(text) { w.shock = caps[1].parse().unwrap_or(w.shock); }
                            if let Some(caps) = re_ctrl.captures(text) { w.ctrl = caps[1].parse().unwrap_or(w.ctrl); }
                            if let Some(caps) = re_uid.captures(text) { w.uid = caps[1].to_string(); }
                        }
                        line.clear();
                    }
                }
                Err(_) => {
                    if let Ok(mut w) = hw_state.write() { w.connected = false; }
                    std::thread::sleep(std::time::Duration::from_secs(2));
                }
            }
        }
    });
}

// ==========================================
// 4. 순수 물리 연산 & AI 결합 엔진
// ==========================================
async fn compute_reflex(
    domain: &str, p: &DisturbancePayload, bias_damping: f64, state: SharedState,
    is_rapidapi_paid: bool, tier_name: String, user_id: String, use_llm: bool
) -> ReflexSolutionResponse {
    let start_time = Instant::now();

    let (real_uid, real_gen, real_vout, real_ent, real_shock, real_ctrl, is_connected) = {
        let hw = state.hw.read().unwrap();
        (hw.uid.clone(), hw.gen, hw.v_out, hw.entropy, hw.shock, hw.ctrl, hw.connected)
    };

    let acceleration = p.gradient_acceleration + (real_shock * 100.0);
    let strain = p.active_strain + (real_ctrl - 0.5) * 0.1;
    let shock_index = ((acceleration / 20000.0) * 0.6 + (strain / 2.0) * 0.4).clamp(0.0, 1.0);
    let raw_zeta = bias_damping + (real_vout * 0.15) + (strain * 0.03) + (real_shock * 0.01);
    let zeta = raw_zeta.clamp(0.1, 2.0);
    let control_intensity = (0.25 + (shock_index * 0.55) + (real_vout * 0.2)).clamp(0.1, 1.0);
    let state_mode = if shock_index > 0.75 { 3 } else if shock_index > 0.35 { 2 } else { 1 };

    let trend = {
        let mut hw = state.hw.write().unwrap();
        hw.history_buffer.push_back(QFrame { gen: real_gen, shock: shock_index, zeta });
        if hw.history_buffer.len() > 12 { hw.history_buffer.pop_front(); }
        if let Some(oldest) = hw.history_buffer.front() {
            if shock_index > oldest.shock { "ESCALATING" } else { "SUBSIDING" }
        } else { "INITIALIZING" }
    };

    let cognitive_synthesis = if use_llm {
        let prompt = format!("System: Physical AI. Domain: {}. V_OUT: {:.4}V, ENT: {:.4}. Trend: {}. Explain Zeta {:.4}.", domain, real_vout, real_ent, trend, zeta);
        match state.http_client.post("http://localhost:11434/api/generate").json(&serde_json::json!({ "model": "phi3:12q", "prompt": prompt, "stream": false })).send().await {
            Ok(res) => res.json::<serde_json::Value>().await.ok().and_then(|v| v["response"].as_str().map(|s| format!("[Cognitive Synthesis] {}", s))).unwrap_or_else(|| "Failed to parse.".to_string()),
            Err(_) => "[Cognitive Engine Offline] Pure hardware reflex executed.".to_string()
        }
    } else { format!("[HFT Mode] Ultra-low latency reflex. Zeta: {:.4}", zeta) };

    let entropy_input = format!("PCAM-{}-{}-{}-{}-{}", domain, real_uid, real_vout, real_ent, real_gen);
    let mut hasher = Sha256::new();
    hasher.update(entropy_input.as_bytes());
    let hardware_seal_id = format!("SEAL-{}-{}", real_uid, hex::encode(hasher.finalize()).to_uppercase());

    let elapsed_ms = start_time.elapsed().as_secs_f64() * 1000.0;

    // [수정 완료: 참조자 충돌(E0499) 해결]
    let fiat_payment = if is_rapidapi_paid { 1.00 } else { 0.00 };
    let (user_usable_credit, owner_dividend_credit, redeem_reserve_usd_10pct, total_minted_credit) = {
        let mut ledger = state.ledger.write().unwrap();
        if is_rapidapi_paid {
            let user_mint = fiat_payment * 1.0;
            let owner_mint = fiat_payment * 0.10;
            let reserve_usd = fiat_payment * 0.10;

            ledger.owner_dividend_cr += owner_mint;
            ledger.protocol_reserve_usd += reserve_usd;
            ledger.total_minted_cr += user_mint + owner_mint;

            let current_bal = ledger.user_balances.get(&user_id).copied().unwrap_or(0.0) + user_mint;
            let cost_cr = 1.0;
            if current_bal >= cost_cr {
                ledger.user_balances.insert(user_id.clone(), current_bal - cost_cr);
                ledger.total_burned_cr += cost_cr;
            } else {
                ledger.user_balances.insert(user_id.clone(), current_bal);
            }
        }
        (
            *ledger.user_balances.get(&user_id).unwrap_or(&0.0),
            ledger.owner_dividend_cr,
            ledger.protocol_reserve_usd,
            ledger.total_minted_cr
        )
    };

    let credit_ledger = CreditLedgerAttestation {
        rapidapi_verified: is_rapidapi_paid,
        caller_tier: tier_name,
        fiat_payment_usd: fiat_payment,
        total_minted_credit: (total_minted_credit * 1000.0).round() / 1000.0,
        user_usable_credit: (user_usable_credit * 1000.0).round() / 1000.0,
        owner_dividend_credit: (owner_dividend_credit * 1000.0).round() / 1000.0,
        redeem_reserve_usd_10pct: (redeem_reserve_usd_10pct * 1000.0).round() / 1000.0,
        ledger_status: if is_rapidapi_paid { "1:1_MINTED_OWNER_10PCT_CREDITED_AND_BURNED".to_string() } else { "LEDGER_MINT_LOCKED_EVALUATION".to_string() },
    };

    ReflexSolutionResponse {
        status: if is_connected { "hardware_active".to_string() } else { "hardware_disconnected".to_string() },
        domain: domain.to_string(),
        zeta: (zeta * 10000.0).round() / 10000.0,
        control_intensity: (control_intensity * 1000.0).round() / 1000.0,
        state_mode, hardware_seal_id, equilibrium_converged: true,
        hardware_reflex_ms: (elapsed_ms * 10000.0).round() / 10000.0,
        cognitive_synthesis,
        trajectory_summary: "Temporal Buffer Active: Secure frames retained.".to_string(),
        telemetry: HardwareTelemetryResponse {
            hardware_uid: real_uid, v_out_measured_v: real_vout, entropy_ent: real_ent,
            shock_rate_pct: real_shock * 100.0, gen_cycle: real_gen, hardware_connected: is_connected,
        },
        credit_ledger,
    }
}

// ==========================================
// 5. 리딤(Redemption) 트랜잭션 핸들러
// ==========================================
async fn process_redemption(
    headers: HeaderMap,
    State(state): State<SharedState>,
    Json(req): Json<RedeemRequest>,
) -> impl IntoResponse {
    let user_id = headers.get("x-rapidapi-user").and_then(|v| v.to_str().ok()).unwrap_or("anonymous").to_string();
    let mut ledger = state.ledger.write().unwrap();

    let user_balance = *ledger.user_balances.get(&user_id).unwrap_or(&0.0);

    // 1. 잔고 검증
    if user_balance < req.amount_cr {
        return (StatusCode::BAD_REQUEST, Json(serde_json::json!({
            "error": "Insufficient CR balance",
            "current_balance": user_balance,
            "requested_amount": req.amount_cr
        }))).into_response();
    }

    // 2. 10% Floor 가치 산정
    let payout_usd = req.amount_cr * 0.10; 

    // 3. 프로토콜 리저브 가드레일 (뱅크런 방지)
    if ledger.protocol_reserve_usd < payout_usd {
        return (StatusCode::INTERNAL_SERVER_ERROR, Json(serde_json::json!({
            "error": "Floor Protection Guardrail: Insufficient Protocol Reserve",
            "available_reserve_usd": ledger.protocol_reserve_usd,
            "required_payout_usd": payout_usd
        }))).into_response();
    }

    // 4. 원장 차감 및 소각 실행
    ledger.user_balances.insert(user_id.clone(), user_balance - req.amount_cr);
    ledger.total_burned_cr += req.amount_cr;
    ledger.protocol_reserve_usd -= payout_usd;

    let resp = RedeemResponse {
        status: "success".to_string(),
        user_id,
        redeemed_cr: req.amount_cr,
        payout_usd,
        remaining_reserve_usd: ledger.protocol_reserve_usd,
        message: "CR successfully redeemed at 10% cash floor. Tokens burned.".to_string(),
    };

    (StatusCode::OK, Json(resp)).into_response()
}

// ==========================================
// 6. 라우팅 및 유틸리티
// ==========================================
fn check_rapidapi_auth(headers: &HeaderMap) -> (bool, String, String) {
    let user_id = headers.get("x-rapidapi-user").and_then(|v| v.to_str().ok()).unwrap_or("anonymous").to_string();
    let sub_tier = headers.get("x-rapidapi-subscription").and_then(|v| v.to_str().ok()).unwrap_or("NONE").to_string();
    let is_paid_tier = user_id != "anonymous" && sub_tier != "NONE" && !sub_tier.eq_ignore_ascii_case("BASIC") && !sub_tier.eq_ignore_ascii_case("FREE");
    (is_paid_tier, sub_tier, user_id)
}

fn verify_access_quota(is_paid: bool, state: &SharedState) -> Result<(), ErrorResponse> {
    if !is_paid {
        let current_count = state.demo_counter.fetch_add(1, Ordering::SeqCst);
        if current_count >= 50 {
            return Err(ErrorResponse { error: "Payment Required".to_string(), code: 402, message: "Evaluation Quota Exceeded (50 calls limit).".to_string() });
        }
    }
    Ok(())
}

async fn handle_rest_request(domain: &str, bias: f64, headers: HeaderMap, State(state): State<SharedState>, Json(p): Json<DisturbancePayload>) -> impl IntoResponse {
    let (is_paid, tier, user_id) = check_rapidapi_auth(&headers);
    if let Err(err) = verify_access_quota(is_paid, &state) { return (StatusCode::PAYMENT_REQUIRED, Json(serde_json::to_value(err).unwrap())).into_response(); }
    let response = compute_reflex(domain, &p, bias, state, is_paid, tier, user_id, true).await;
    (StatusCode::OK, Json(serde_json::to_value(response).unwrap())).into_response()
}

async fn solve_universal(headers: HeaderMap, state: State<SharedState>, p: Json<DisturbancePayload>) -> impl IntoResponse { handle_rest_request("Universal-Equilibrium", 0.95, headers, state, p).await }
async fn predict_quant(headers: HeaderMap, state: State<SharedState>, p: Json<DisturbancePayload>) -> impl IntoResponse { handle_rest_request("Quant-Microstructure", 0.99, headers, state, p).await }
async fn predict_pharma(headers: HeaderMap, state: State<SharedState>, p: Json<DisturbancePayload>) -> impl IntoResponse { handle_rest_request("Pharma-Bioreactor", 0.91, headers, state, p).await }
async fn predict_battery(headers: HeaderMap, state: State<SharedState>, p: Json<DisturbancePayload>) -> impl IntoResponse { handle_rest_request("Battery-Energetics", 0.98, headers, state, p).await }
async fn predict_robotics(headers: HeaderMap, state: State<SharedState>, p: Json<DisturbancePayload>) -> impl IntoResponse { handle_rest_request("Robotic-Compliance", 0.93, headers, state, p).await }
async fn predict_mobility(headers: HeaderMap, state: State<SharedState>, p: Json<DisturbancePayload>) -> impl IntoResponse { handle_rest_request("Mobility-Dynamics", 0.96, headers, state, p).await }
async fn predict_chemistry(headers: HeaderMap, state: State<SharedState>, p: Json<DisturbancePayload>) -> impl IntoResponse { handle_rest_request("Precision-Chemistry", 0.94, headers, state, p).await }

// ==========================================
// 7. 메인 서버 실행
// ==========================================
#[tokio::main]
async fn main() {
    let serial_port = std::env::var("PCAM_SERIAL_PORT").unwrap_or_else(|_| "COM3".to_string());

    let hw_state = Arc::new(RwLock::new(HwTelemetry::default()));
    spawn_serial_reader(hw_state.clone(), serial_port.clone());

    let shared_state = Arc::new(AppState {
        hw: hw_state,
        http_client: Client::new(),
        demo_counter: AtomicUsize::new(0),
        ledger: Arc::new(RwLock::new(LedgerState::default())),
    });

    let app = Router::new()
        .route("/v1/quant/predict", post(predict_quant))
        .route("/v1/solve-universal-equilibrium", post(solve_universal))
        .route("/v1/pharma/predict", post(predict_pharma))
        .route("/v1/battery/predict", post(predict_battery))
        .route("/v1/robotics/predict", post(predict_robotics))
        .route("/v1/mobility/predict", post(predict_mobility))
        .route("/v1/chemistry/predict", post(predict_chemistry))
        .route("/v1/tokenomics/redeem", post(process_redemption))
        .with_state(shared_state);

    let addr = "0.0.0.0:8000";
    println!("==================================================");
    println!(" [P-CAM 7-DOMAIN GATEWAY] Dual-Valuation Ledger Active");
    println!(" * Hardware Port : {} (Default: COM3)", serial_port);
    println!(" * Tokenomics    : Utility $1.00 | Redeem Floor $0.10");
    println!(" * Endpoints     : 7 Domains + /v1/tokenomics/redeem");
    println!("==================================================");

    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}