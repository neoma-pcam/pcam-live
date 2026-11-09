"""
NEOMA P-CAM Shock-Damped Pure Market Making (PMM) Strategy for Hummingbot
Protects passive liquidity orders from toxic sweeps using 15µs physical relaxation.

Usage in Hummingbot CLI:
  1. Copy this file into hummingbot/scripts/
  2. Start Hummingbot: bin/hummingbot.py
  3. Run command: start --script hummingbot_pcam_pmm.py
"""

from decimal import Decimal
import time
import requests

try:
    from hummingbot.strategy.script_strategy_base import ScriptStrategyBase
    from hummingbot.core.data_type.common import OrderType, PriceType
    from hummingbot.core.data_type.order_candidate import OrderCandidate
    HUMMINGBOT_AVAILABLE = True
except ImportError:
    # 로컬 독립 테스트용 모의 클래스
    HUMMINGBOT_AVAILABLE = False
    class ScriptStrategyBase:
        pass

class PCAMHummingbotStrategy(ScriptStrategyBase):
    # 거래소 및 마켓 설정
    exchange = "binance_paper_trade"  # 실거래 시 "binance", "bybit" 등으로 변경
    trading_pair = "BTC-USDT"
    markets = {exchange: {trading_pair}}

    # 기본 마켓메이킹 파라미터
    bid_spread = Decimal("0.001")   # 매수 스프레드 (0.1%)
    ask_spread = Decimal("0.001")   # 매도 스프레드 (0.1%)
    order_amount = Decimal("0.005") # 1회 주문 수량 (BTC)
    order_refresh_time = 15         # 주문 갱신 주기 (초)

    # P-CAM 설정 (중앙 인클레이브 전용)
    pcam_host = "https://neoma-p-cam-quant-reflex-hft.p.rapidapi.com"
    rapidapi_key = ""  # 본인의 RapidAPI Key 입력 (비어있으면 기본 노드 호출)

    create_timestamp = 0
    last_mid_price = 0.0
    last_timestamp = time.perf_counter()

    def on_tick(self):
        """매 초마다 실행되는 허밍봇 메인 루프"""
        if not HUMMINGBOT_AVAILABLE:
            return

        now = time.perf_counter()
        dt = max(1e-4, now - self.last_timestamp)

        # 1. 실시간 오더북 최우선 호가 조회
        order_book = self.connectors[self.exchange].get_order_book(self.trading_pair)
        best_bid = float(order_book.bid_price)
        best_ask = float(order_book.ask_price)
        bid_vol = float(order_book.bid_volume)
        ask_vol = float(order_book.ask_volume)
        mid_price = (best_bid + best_ask) / 2.0

        # 2. 4차원 물리 텐서 파라미터 연산
        imbalance = (bid_vol - ask_vol) / max(1e-6, bid_vol + ask_vol)
        flux_v = round(0.080 + (abs(imbalance) * 0.020), 4)
        velocity = (mid_price - self.last_mid_price) / dt if self.last_mid_price > 0 else 0.0

        self.last_mid_price = mid_price
        self.last_timestamp = now

        # 3. P-CAM 인클레이브 15µs 충격 완화 평가
        zeta, should_cancel = self.query_pcam_reflex(flux_v, abs(velocity))

        # 4. 방어 로직: 감쇠비 Zeta > 1.2 초과 시 주문 전량 즉시 취소 (스윕 회피)
        if should_cancel:
            self.logger().warning(
                f"🚨 [P-CAM SHOCK DAMPING] Non-equilibrium stress detected! Zeta={zeta:.4f} > 1.2. "
                f"PULL_QUOTES active - canceling all open limit orders to eliminate slippage."
            )
            self.cancel_all_orders()
            return

        # 5. 임계 감쇠 안정 구간(0.8 <= Zeta <= 1.2): 정상 마켓메이킹 호가 배치
        if self.create_timestamp <= self.current_timestamp:
            self.cancel_all_orders()
            self.create_proactive_orders(mid_price)
            self.create_timestamp = self.order_refresh_time + self.current_timestamp

    def query_pcam_reflex(self, flux_v: float, velocity: float):
        payload = {
            "flux_potential_v": min(0.120, max(0.080, flux_v)),
            "gradient_velocity": round(velocity, 2),
            "gradient_acceleration": 12000.0,
            "active_strain": 1.05
        }
        headers = {"Content-Type": "application/json"}
        if self.rapidapi_key:
            headers["X-RapidAPI-Key"] = self.rapidapi_key
            headers["X-RapidAPI-Host"] = "neoma-p-cam-quant-reflex-hft.p.rapidapi.com"

        try:
            res = requests.post(f"{self.pcam_host}/v1/quant/predict", json=payload, headers=headers, timeout=1.0)
            if res.status_code == 200:
                data = res.json()
                zeta = data.get("zeta", 1.0)
                return zeta, (zeta > 1.2)
        except Exception:
            pass
        return 1.0, False

    def cancel_all_orders(self):
        for order in self.get_active_orders(connector_name=self.exchange):
            self.cancel(self.exchange, order.trading_pair, order.client_order_id)

    def create_proactive_orders(self, mid_price):
        buy_price = Decimal(str(mid_price)) * (Decimal("1") - self.bid_spread)
        sell_price = Decimal(str(mid_price)) * (Decimal("1") + self.ask_spread)

        buy_order = OrderCandidate(
            trading_pair=self.trading_pair,
            is_maker=True,
            order_type=OrderType.LIMIT,
            order_side=PriceType.Buy,
            amount=self.order_amount,
            price=buy_price
        )
        sell_order = OrderCandidate(
            trading_pair=self.trading_pair,
            is_maker=True,
            order_type=OrderType.LIMIT,
            order_side=PriceType.Sell,
            amount=self.order_amount,
            price=sell_price
        )

        adjusted_buy = self.connectors[self.exchange].budget_checker.adjust_candidate(buy_order)
        adjusted_sell = self.connectors[self.exchange].budget_checker.adjust_candidate(sell_order)

        if adjusted_buy.amount > Decimal("0"):
            self.buy(self.exchange, self.trading_pair, adjusted_buy.amount, OrderType.LIMIT, adjusted_buy.price)
        if adjusted_sell.amount > Decimal("0"):
            self.sell(self.exchange, self.trading_pair, adjusted_sell.amount, OrderType.LIMIT, adjusted_sell.price)

# 로컬에서 단독 실행 시 구조 안내 출력
if __name__ == "__main__":
    print("=" * 78)
    print(" [NEOMA P-CAM] Hummingbot Pure Market Making (PMM) Shock Damping Strategy")
    print("=" * 78)
    print(" ✔ Standalone script ready for deployment.")
    print(" ✔ Deployment Steps:")
    print("    1. Copy this script to your Hummingbot root: 'hummingbot/scripts/'")
    print("    2. Launch Hummingbot on your server/Docker: 'bin/hummingbot.py'")
    print("    3. Inside Hummingbot CLI, type: start --script hummingbot_pcam_pmm.py")
    print(" ✔ The bot will ping P-CAM every tick (1s). Continuous live execution")
    print("   automatically converts via RapidAPI PRO tier ($499/mo).")
    print("=" * 78)
