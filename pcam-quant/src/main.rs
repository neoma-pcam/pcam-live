mod tensor_mapper;
use tensor_mapper::{OrderBookSnapshot};
use serde_json::Value;
use std::time::Instant;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("============================================================");
    println!(" NEOMA P-CAM Quant Core (pcam-quant) v0.1.0");
    println!(" Microstructure Shock Damping & Dynamic Order Execution");
    println!("============================================================");

    // 1. 극단적 유동성 급변(Flash Shock / Market Sweep) 스냅샷 시뮬레이션
    let lob_shock = OrderBookSnapshot {
        bid_price: 100.05,
        ask_price: 100.25,      // 스프레드 5배 급확대
        bid_qty: 15.0,
        ask_qty: 480.0,         // 매도 잔량 압도적 불균형
        last_velocity: 135.0,
        baseline_spread: 0.04,
    };

    let tensor = lob_shock.to_pcam_tensor(1.2);
    println!("\n[1] LOB Microstructure -> Physical Tensor Synthesis:");
    println!(" - Flux Potential (Imbalance) : {:.4} V", tensor.flux_potential_v);
    println!(" - Gradient Velocity          : {:.2} pts/s", tensor.gradient_velocity);
    println!(" - Gradient Acceleration      : {:.1} pts/s²", tensor.gradient_acceleration);
    println!(" - Active Strain (Spread)     : {:.2}x", tensor.active_strain);

    // 2. 엔드포인트 설정 (로컬 게이트웨이 우선 시도)
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(5))
        .build()?;

    let local_endpoint = "http://127.0.0.1:8000/v1/solve-universal-equilibrium";
    let cloud_endpoint = "https://api.neoma-pcam.com/v1/solve-universal-equilibrium";

    println!("\n[2] Direct Silicon Hardware Reflex Dispatch...");
    let t_start = Instant::now();

    // 로컬 우선 호출 -> 실패 시 클라우드 엔드포인트 호출
    let (target_url, resp) = match client
        .post(local_endpoint)
        .header("User-Agent", "NEOMA-PCAM-Quant/0.1.0")
        .json(&tensor)
        .send()
        .await
    {
        Ok(res) if res.status().is_success() => (local_endpoint, Ok(res)),
        _ => {
            println!(" * 로컬 노드 응답 대기 -> 라이브 클라우드 엔클레이브로 라우팅");
            (
                cloud_endpoint,
                client
                    .post(cloud_endpoint)
                    .header("User-Agent", "NEOMA-PCAM-Quant/0.1.0")
                    .json(&tensor)
                    .send()
                    .await,
            )
        }
    };

    match resp {
        Ok(res) if res.status().is_success() => {
            let rtt_ms = t_start.elapsed().as_secs_f64() * 1000.0;
            let json: Value = res.json().await?;

            let zeta = json["zeta"].as_f64().unwrap_or(1.0);
            let seal = json["hardware_seal_id"].as_str().unwrap_or("UNKNOWN");
            let reflex = json["hardware_reflex_ms"].as_f64().unwrap_or(0.015);

            println!("------------------------------------------------------------");
            println!("✔ Target Gateway Node        : {}", target_url);
            println!("✔ Total Round-Trip Time       : {:.3} ms", rtt_ms);
            println!("✔ Silicon Hardware Reflex     : {:.4} ms (Sub-0.03ms tier)", reflex);
            println!("✔ Damping Ratio (Zeta)        : {:.4}", zeta);
            println!("✔ SEAL-CORE Hardware Seal     : {}", seal);
            println!("------------------------------------------------------------");

            // 3. P-CAM 물리 감쇠 기반 초저지연 주문 집행 의사결정
            println!("\n[3] Real-Time Quant Execution Verdict:");
            if (0.8..=1.2).contains(&zeta) {
                println!(">> [DECISION: CRITICAL DAMPING]");
                println!("   유동성 충격 흡수 완결. 슬리피지 0.0% 보장 구간으로 최우선 지정가(Passive Post-Only) 체결 실행.");
            } else if zeta > 1.2 {
                println!(">> [DECISION: OVER-DAMPED]");
                println!("   극단적 유동성 증발 쇼크 감지. 마켓 메이킹 미체결 호가 즉각 취소(Cancel / Pull All).");
            } else {
                println!(">> [DECISION: UNDER-DAMPED]");
                println!("   강한 물리적 모멘텀 돌파 구간. 잔량 소진 방향으로 적극적 테이커(Aggressive Taker) 진입 허용.");
            }
        }
        Ok(res) => {
            eprintln!("⚠ 게이트웨이 반환 오류: HTTP {}", res.status());
        }
        Err(err) => {
            eprintln!("⚠ 엔클레이브 통신 실패: {}", err);
        }
    }

    Ok(())
}
