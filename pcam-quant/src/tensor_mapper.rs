use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketDisturbancePayload {
    pub flux_potential_v: f64,
    pub gradient_velocity: f64,
    pub gradient_acceleration: f64,
    pub active_strain: f64,
}

#[derive(Debug, Clone)]
pub struct OrderBookSnapshot {
    pub bid_price: f64,
    pub ask_price: f64,
    pub bid_qty: f64,
    pub ask_qty: f64,
    pub last_velocity: f64,
    pub baseline_spread: f64,
}

impl OrderBookSnapshot {
    /// LOB 호가창 상태를 P-CAM 물리 충격 텐서로 변환
    pub fn to_pcam_tensor(&self, current_dt_ms: f64) -> MarketDisturbancePayload {
        // 1. 유동성 불균형 포텐셜 (Imbalance -> 0.080V ~ 0.100V 범위 매핑)
        let total_depth = self.bid_qty + self.ask_qty;
        let imbalance = if total_depth > 0.0 {
            (self.bid_qty - self.ask_qty) / total_depth
        } else {
            0.0
        };
        let flux_v = 0.085 + (imbalance * 0.015);

        // 2. 중간가 틱 속도 구배 (Mid-price Velocity)
        let mid_price = (self.bid_price + self.ask_price) / 2.0;
        let velocity = (mid_price * 10.0) % 500.0;

        // 3. 호가 소진 가속도 구배 (Order Acceleration)
        let acceleration = (velocity - self.last_velocity).abs() / (current_dt_ms / 1000.0).max(0.001);

        // 4. 스프레드 변형률 (Active Spread Strain)
        let current_spread = (self.ask_price - self.bid_price).max(0.0001);
        let strain = current_spread / self.baseline_spread.max(0.0001);

        MarketDisturbancePayload {
            flux_potential_v: (flux_v * 10000.0).round() / 10000.0,
            gradient_velocity: (velocity * 100.0).round() / 100.0,
            gradient_acceleration: (acceleration * 10.0).round() / 10.0,
            active_strain: (strain * 100.0).round() / 100.0,
        }
    }
}
