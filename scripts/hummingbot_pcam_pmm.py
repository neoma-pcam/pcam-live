import asyncio
from decimal import Decimal
from typing import Dict, Optional
import aiohttp
from pydantic import Field

from hummingbot.connector.connector_base import ConnectorBase
from hummingbot.core.data_type.common import OrderType, TradeType
from hummingbot.core.data_type.order_candidate import OrderCandidate
from hummingbot.strategy.strategy_v2_base import StrategyV2Base, StrategyV2ConfigBase


class PcamPmmConfig(StrategyV2ConfigBase):
    exchange: str = Field(default="binance")
    trading_pair: str = Field(default="BTC-USDT")
    order_amount: Decimal = Field(default=Decimal("0.001"))
    bid_spread: Decimal = Field(default=Decimal("0.001"))
    ask_spread: Decimal = Field(default=Decimal("0.001"))
    order_refresh_time: float = Field(default=2.0)
    pcam_host: str = Field(default="http://localhost:8000")
    rapidapi_key: Optional[str] = Field(default=None)


class PcamPmmStrategy(StrategyV2Base):
    def __init__(self, connectors: Dict[str, ConnectorBase], config: PcamPmmConfig):
        super().__init__(connectors, config)
        self.config = config

        self.latest_zeta: float = 1.0
        self.is_safety_valid: bool = False
        self.last_mid_price: Optional[float] = None
        self.last_velocity: float = 0.0
        self.last_timestamp: float = 0.0
        self.create_timestamp: float = 0.0
        self.is_querying: bool = False

    def on_tick(self):
        connector = self.connectors[self.config.exchange]
        order_book = connector.get_order_book(self.config.trading_pair)

        # 1. OrderBook 규격 조회
        best_bid = float(order_book.get_price(True))
        best_ask = float(order_book.get_price(False))
        bids = list(order_book.bid_entries())
        asks = list(order_book.ask_entries())
        bid_vol = float(bids[0].amount) if bids else 0.0
        ask_vol = float(asks[0].amount) if asks else 0.0

        mid_price = (best_bid + best_ask) / 2.0
        now = self.current_timestamp

        # 2. 연속 속도 변화로 동적 가속도 산출
        dt = now - self.last_timestamp if self.last_timestamp > 0 else 1.0
        dt = max(dt, 0.001)

        velocity = (mid_price - self.last_mid_price) / dt if self.last_mid_price else 0.0
        acceleration = (velocity - self.last_velocity) / dt if self.last_velocity else 0.0

        self.last_mid_price = mid_price
        self.last_velocity = velocity
        self.last_timestamp = now

        flux_v = 0.100 + (bid_vol - ask_vol) / (bid_vol + ask_vol + 1e-6) * 0.020

        # 3. 비동기 논블로킹 예측 호출
        if not self.is_querying:
            self.is_querying = True
            asyncio.create_task(self._fetch_prediction(flux_v, velocity, acceleration))

        # 4. Fail-Safe: 비정상 통신 또는 시장 충격 감지 시 호가 즉시 철회
        if (not self.is_safety_valid) or (self.latest_zeta > 1.2):
            self.cancel_all_orders()
            return

        # 5. 호가 생성/갱신
        if self.create_timestamp <= now:
            self.cancel_all_orders()
            self.create_proactive_orders(Decimal(str(mid_price)))
            self.create_timestamp = now + self.config.order_refresh_time

    async def _fetch_prediction(self, flux_v: float, velocity: float, acceleration: float):
        payload = {
            "flux_potential_v": min(0.120, max(0.080, flux_v)),
            "gradient_velocity": round(velocity, 2),
            "gradient_acceleration": round(acceleration, 2),
            "active_strain": 1.05
        }
        headers = {"Content-Type": "application/json"}
        if self.config.rapidapi_key:
            headers["X-RapidAPI-Key"] = self.config.rapidapi_key
            headers["X-RapidAPI-Host"] = "neoma-p-cam-quant-reflex-hft.p.rapidapi.com"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.config.pcam_host}/v1/quant/predict",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=0.5)
                ) as res:
                    if res.status == 200:
                        data = await res.json()
                        self.latest_zeta = data.get("zeta", 1.0)
                        self.is_safety_valid = True
                    else:
                        self.is_safety_valid = False
        except Exception:
            self.is_safety_valid = False
        finally:
            self.is_querying = False

    def cancel_all_orders(self):
        connector = self.connectors[self.config.exchange]
        for order in connector.active_orders:
            if order.trading_pair == self.config.trading_pair:
                self.cancel(self.config.exchange, order.trading_pair, order.client_order_id)

    def create_proactive_orders(self, mid_price: Decimal):
        buy_price = mid_price * (Decimal("1") - self.config.bid_spread)
        sell_price = mid_price * (Decimal("1") + self.config.ask_spread)

        buy_order = OrderCandidate(
            trading_pair=self.config.trading_pair,
            is_maker=True,
            order_type=OrderType.LIMIT,
            order_side=TradeType.BUY,
            amount=self.config.order_amount,
            price=buy_price
        )
        sell_order = OrderCandidate(
            trading_pair=self.config.trading_pair,
            is_maker=True,
            order_type=OrderType.LIMIT,
            order_side=TradeType.SELL,
            amount=self.config.order_amount,
            price=sell_price
        )

        connector = self.connectors[self.config.exchange]
        buy_adjusted = connector.budget_checker.adjust_candidate(buy_order)
        sell_adjusted = connector.budget_checker.adjust_candidate(sell_order)

        if buy_adjusted.amount > 0:
            self.buy(self.config.exchange, self.config.trading_pair, buy_adjusted.amount, OrderType.LIMIT, buy_adjusted.price)
        if sell_adjusted.amount > 0:
            self.sell(self.config.exchange, self.config.trading_pair, sell_adjusted.amount, OrderType.LIMIT, sell_adjusted.price)
