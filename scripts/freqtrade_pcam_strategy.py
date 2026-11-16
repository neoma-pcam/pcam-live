"""
NEOMA P-CAM Dual-Engine Quant Strategy for Freqtrade (IStrategy)
================================================================
Combines two room-temperature silicon physical solvers for live execution:
  1. /v1/quant/predict : Sub-millisecond LOB/volatility shock damping (zeta, control_intensity)
  2. /v1/ising/solve   : 64-spin Ising Hamiltonian ground-state consensus across multi-horizon signals

Authentication:
  Set PCAM_RAPIDAPI_KEY environment variable (2,000 free calls/month via RapidAPI)
  or configure `rapidapi_key` in your Freqtrade config.json.
"""
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import requests

try:
    from freqtrade.strategy import IStrategy, DecimalParameter, IntParameter
    from freqtrade.persistence import Trade
except ImportError:
    # Lightweight fallback base so standalone verification runs without Freqtrade installed
    class IStrategy:
        INTERFACE_VERSION = 3
        def __init__(self, config: dict) -> None:
            self.config = config

    class DecimalParameter:
        def __init__(self, low, high, default, space="buy", optimize=False):
            self.value = default

    class IntParameter:
        def __init__(self, low, high, default, space="buy", optimize=False):
            self.value = default

    class Trade:
        pass


logger = logging.getLogger(__name__)


class NeomaPCAMQuantStrategy(IStrategy):
    """
    Physical AI Quantitative Strategy driven directly by NEOMA P-CAM Silicon Enclave.
    """

    INTERFACE_VERSION = 3
    can_short: bool = False
    timeframe: str = "5m"
    startup_candle_count: int = 64

    # Base risk guardrails (dynamically modulated by live P-CAM zeta & Ising magnetization)
    minimal_roi = {
        "0": 0.045,
        "30": 0.025,
        "90": 0.012,
    }
    stoploss = -0.035
    use_custom_stoploss = True
    process_only_new_candles = True

    # Tunable physical thresholds
    min_magnetization = DecimalParameter(0.15, 0.75, default=0.30, space="buy", optimize=False)
    min_damping_zeta = DecimalParameter(0.75, 1.25, default=0.90, space="buy", optimize=False)
    ising_horizon = IntParameter(16, 64, default=32, space="buy", optimize=False)

    DEFAULT_QUANT_URL = "https://neoma-p-cam-hyper-physical-control.p.rapidapi.com/v1/quant/predict"
    DEFAULT_ISING_URL = "https://neoma-p-cam-hyper-physical-control.p.rapidapi.com/v1/ising/solve"
    DEFAULT_RAPIDAPI_HOST = "neoma-p-cam-hyper-physical-control.p.rapidapi.com"

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        cfg = config if isinstance(config, dict) else {}
        self.rapidapi_key: Optional[str] = cfg.get("pcam_rapidapi_key") or os.getenv("PCAM_RAPIDAPI_KEY")
        self.quant_endpoint: str = cfg.get("pcam_quant_endpoint", self.DEFAULT_QUANT_URL)
        self.ising_endpoint: str = cfg.get("pcam_ising_endpoint", self.DEFAULT_ISING_URL)
        self.timeout: float = float(cfg.get("pcam_timeout", 5.0))
        self._pair_physics_cache: Dict[str, dict] = {}

    def _build_headers(self, endpoint: str) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        host = urlparse(endpoint).netloc.lower()
        if self.rapidapi_key and "rapidapi.com" in host:
            headers["x-rapidapi-host"] = host or self.DEFAULT_RAPIDAPI_HOST
            headers["x-rapidapi-key"] = self.rapidapi_key
        return headers

    def compute_pcam_quant_state(
        self,
        liquidity_pressure: float,
        spread_drift_bps: float,
        depletion_accel: float,
        drawdown_strain: float,
        order_book_imbalance: float,
    ) -> dict:
        """
        Calls P-CAM /v1/quant/predict to compute physical damping ratio (zeta),
        optimal control gain (control_intensity), and regime mode.
        """
        payload = {
            "flux_potential_v": round(min(2.5, max(0.1, 0.55 + liquidity_pressure * 1.4)), 4),
            "gradient_velocity": round(min(5000.0, max(10.0, 520.0 + abs(spread_drift_bps) * 18.0)), 2),
            "gradient_acceleration": round(min(100000.0, max(100.0, 16000.0 + abs(depletion_accel) * 250.0)), 1),
            "active_strain": round(min(2.0, max(0.1, 0.65 + drawdown_strain)), 4),
            "order_book_imbalance": round(min(1.0, max(-1.0, order_book_imbalance)), 4),
            "spread_bps": round(max(0.1, abs(spread_drift_bps)), 4),
            "slice_participation_rate": round(min(1.0, max(0.01, liquidity_pressure)), 4),
        }
        resp = requests.post(
            self.quant_endpoint,
            json=payload,
            headers=self._build_headers(self.quant_endpoint),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def compute_pcam_ising_consensus(
        self,
        returns: np.ndarray,
        vol_ratios: np.ndarray,
        zeta_gain: float,
    ) -> Tuple[float, float, List[int], str, float]:
        """
        Maps multi-bar return & volume-pressure features into an N-spin Ising Hamiltonian
        (N <= 64) and solves for ground-state spin alignment directly on P-CAM /v1/ising/solve.
        """
        n = min(64, max(8, int(self.ising_horizon.value), len(returns)))
        r_slice = returns[-n:]
        v_slice = vol_ratios[-n:]

        scale = max(float(np.std(r_slice)), 1e-6)
        fields = [
            round(float(np.clip((r_slice[i] / scale) * (0.6 + 0.4 * v_slice[i]), -2.0, 2.0)), 5)
            for i in range(n)
        ]

        couplings = []
        coupling_strength = round(0.35 * min(1.5, max(0.2, zeta_gain)), 5)
        for i in range(n - 1):
            # Adjacent temporal coherence coupling
            couplings.append([i, i + 1, coupling_strength])
            # Multi-scale harmonic coupling across lookback windows
            if i + 4 < n:
                couplings.append([i, i + 4, round(coupling_strength * 0.5, 5)])

        payload = {
            "num_spins": n,
            "fields": fields,
            "couplings": couplings,
        }
        resp = requests.post(
            self.ising_endpoint,
            json=payload,
            headers=self._build_headers(self.ising_endpoint),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        spins = data.get("spins", [])
        magnetization = float(data.get("magnetization", 0.0))
        ground_energy = float(data.get("ground_state_energy", 0.0))
        seal_id = str(data.get("hardware_seal_id", ""))
        reflex_ms = float(data.get("hardware_reflex_ms", 0.0))
        return magnetization, ground_energy, spins, seal_id, reflex_ms

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        pair = metadata.get("pair", "BTC/USDT")
        dataframe["ret_1"] = dataframe["close"].pct_change().fillna(0.0)
        dataframe["ret_accel"] = dataframe["ret_1"].diff().fillna(0.0)
        dataframe["range_bps"] = ((dataframe["high"] - dataframe["low"]) / dataframe["close"].replace(0, np.nan)).fillna(0.0) * 10000.0
        vol_ma = dataframe["volume"].rolling(20, min_periods=1).mean().replace(0, 1.0)
        dataframe["vol_ratio"] = (dataframe["volume"] / vol_ma).clip(0.1, 5.0)
        dataframe["imbalance_proxy"] = (
            (dataframe["close"] - dataframe["open"])
            / (dataframe["high"] - dataframe["low"]).replace(0, np.nan)
        ).fillna(0.0).clip(-1.0, 1.0)

        # Default neutral physics columns
        dataframe["pcam_zeta"] = 1.0
        dataframe["pcam_control_intensity"] = 0.5
        dataframe["pcam_state_mode"] = 2
        dataframe["pcam_magnetization"] = 0.0
        dataframe["pcam_ground_energy"] = 0.0

        if len(dataframe) < 16:
            return dataframe

        latest = dataframe.iloc[-1]
        n_window = min(64, max(16, int(self.ising_horizon.value)), len(dataframe))
        recent = dataframe.iloc[-n_window:]

        try:
            q_res = self.compute_pcam_quant_state(
                liquidity_pressure=float(min(1.0, latest["vol_ratio"] * 0.25)),
                spread_drift_bps=float(latest["range_bps"]),
                depletion_accel=float(latest["ret_accel"] * 10000.0),
                drawdown_strain=float(min(1.2, abs(latest["ret_1"]) * 25.0)),
                order_book_imbalance=float(latest["imbalance_proxy"]),
            )
            zeta = float(q_res.get("zeta", 1.0))
            ctrl_gain = float(q_res.get("control_intensity", 0.5))
            state_mode = int(q_res.get("state_mode", 2))

            mag, energy, _, seal_id, reflex_ms = self.compute_pcam_ising_consensus(
                returns=recent["ret_1"].to_numpy(dtype=float),
                vol_ratios=recent["vol_ratio"].to_numpy(dtype=float),
                zeta_gain=zeta * ctrl_gain,
            )

            idx = dataframe.index[-1]
            dataframe.loc[idx, "pcam_zeta"] = zeta
            dataframe.loc[idx, "pcam_control_intensity"] = ctrl_gain
            dataframe.loc[idx, "pcam_state_mode"] = state_mode
            dataframe.loc[idx, "pcam_magnetization"] = mag
            dataframe.loc[idx, "pcam_ground_energy"] = energy

            self._pair_physics_cache[pair] = {
                "zeta": zeta,
                "control_intensity": ctrl_gain,
                "state_mode": state_mode,
                "magnetization": mag,
                "ground_energy": energy,
                "seal_id": seal_id,
                "reflex_ms": reflex_ms,
            }
        except Exception as exc:
            logger.warning("P-CAM enclave unreachable for %s (%s); holding neutral state.", pair, exc)

        return dataframe

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe.loc[
            (
                (dataframe["pcam_magnetization"] >= float(self.min_magnetization.value))
                & (dataframe["pcam_zeta"] >= float(self.min_damping_zeta.value))
                & (dataframe["pcam_ground_energy"] < 0.0)
                & (dataframe["volume"] > 0)
            ),
            "enter_long",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe.loc[
            (
                (dataframe["pcam_magnetization"] <= -float(self.min_magnetization.value) * 0.5)
                | (dataframe["pcam_zeta"] < 0.70)
            ),
            "exit_long",
        ] = 1
        return dataframe

    def custom_stake_amount(
        self,
        pair: str,
        current_time: datetime,
        current_rate: float,
        proposed_stake: float,
        min_stake: Optional[float],
        max_stake: float,
        leverage: float,
        entry_tag: Optional[str],
        side: str,
        **kwargs,
    ) -> float:
        """
        Scales capital allocation using P-CAM physical control_intensity & Ising magnetization.
        """
        phys = self._pair_physics_cache.get(pair)
        if not phys:
            return proposed_stake

        coherence = min(1.0, max(0.25, abs(phys["magnetization"])))
        damping_gain = min(1.25, max(0.35, phys["control_intensity"] * phys["zeta"]))
        scaled_stake = proposed_stake * coherence * damping_gain

        if min_stake is not None and scaled_stake < min_stake:
            return min_stake
        return min(max_stake, scaled_stake)

    def custom_stoploss(
        self,
        pair: str,
        trade: "Trade",
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        after_fill: bool,
        **kwargs,
    ) -> Optional[float]:
        """
        Dynamically tightens stop-loss boundary when P-CAM detects shock overdamping (state_mode == 3).
        """
        phys = self._pair_physics_cache.get(pair)
        if not phys:
            return None

        if phys["state_mode"] == 3 and phys["magnetization"] < 0.0:
            return -0.015
        if current_profit > 0.02 and phys["zeta"] >= 1.05:
            return -0.012
        return None


if __name__ == "__main__":
    # Zero-PRNG deterministic smoke test against live P-CAM enclave
    print("=" * 76)
    print(" [TEST] Freqtrade NEOMA P-CAM Dual-Engine Quant Strategy Live Verification")
    print("=" * 76)

    n_bars = 48
    t = np.arange(n_bars, dtype=float)
    closes = 65000.0 + np.cumsum(np.sin(t * 0.25) * 45.0 + 18.0)
    df = pd.DataFrame({
        "open": closes - 12.0,
        "high": closes + 28.0,
        "low": closes - 24.0,
        "close": closes,
        "volume": 120.0 + (t % 7) * 15.0,
    })

    strat = NeomaPCAMQuantStrategy({
        "pcam_quant_endpoint": "https://api.neoma-pcam.com/v1/quant/predict",
        "pcam_ising_endpoint": "https://api.neoma-pcam.com/v1/ising/solve",
    })
    out = strat.populate_indicators(df, {"pair": "BTC/USDT"})
    out = strat.populate_entry_trend(out, {"pair": "BTC/USDT"})
    last = out.iloc[-1]
    cache = strat._pair_physics_cache.get("BTC/USDT", {})

    print(f" - P-CAM Damping (Zeta)      : {last['pcam_zeta']:.4f}")
    print(f" - Control Gain (Intensity)  : {last['pcam_control_intensity']:.4f}")
    print(f" - Ising Magnetization (M)   : {last['pcam_magnetization']:.4f}")
    print(f" - Ising Ground Energy (E0)  : {last['pcam_ground_energy']:.4f}")
    print(f" - Silicon Reflex Latency    : {cache.get('reflex_ms')} ms")
    print(f" - Hardware SEAL-PoPW Token  : {cache.get('seal_id', '')[:48]}...")
    assert cache.get("seal_id", "").startswith("SEAL-"), "Missing hardware SEAL token!"
    print("\n [PASS] Freqtrade P-CAM 듀얼 엔진 연산 및 시그널 생성 검증 완료!")