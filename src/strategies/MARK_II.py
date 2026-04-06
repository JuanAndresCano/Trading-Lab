# Esta será tu implementación real de la estrategia congelada, usando tu 
# lógica actual de EMAs, ATR, pullback y confirmación. La idea es que 
# Mark II quede como baseline reproducible, separado del resto, para que 
# cualquier mejora posterior se compare contra una referencia estable y no 
# contra una versión que cambia cada semana.

# src/strategies/mark2.py

from __future__ import annotations

from collections import deque
from statistics import mean
from typing import Deque, List, Optional

from src.core.events import MarketEvent, SignalEvent
from src.strategies.base import BaseStrategy


class Mark2Strategy(BaseStrategy):
    """
    Baseline oficial del proyecto basado en el notebook Mark II.

    Lógica baseline:
    - Tendencia long: EMA21 > EMA55 > EMA100
    - Tendencia short: EMA21 < EMA55 < EMA100
    - Pullback dinámico: abs(close - EMA21) < ATR14
    - Confirmación long: close > open
    - Confirmación short: close < open
    - Anti-repetición: no emitir la misma señal en barras consecutivas

    Notas:
    - Esta clase solo genera señales.
    - Stop loss, take profit, sizing y ejecución viven en otros módulos.
    """

    def __init__(
        self,
        symbol: str = "EURUSD=X",
        ema_fast_period: int = 21,
        ema_mid_period: int = 55,
        ema_slow_period: int = 100,
        atr_period: int = 14,
    ) -> None:
        super().__init__(strategy_id="mark2")
        self.symbol = symbol
        self.ema_fast_period = ema_fast_period
        self.ema_mid_period = ema_mid_period
        self.ema_slow_period = ema_slow_period
        self.atr_period = atr_period

        self.history: Deque[MarketEvent] = deque(maxlen=max(ema_slow_period, atr_period) + 5)
        self.last_signal_side: Optional[str] = None

    def on_market_event(self, event: MarketEvent) -> List[SignalEvent]:
        """
        Procesa una barra y devuelve una lista con cero o una señal.
        """
        if event.symbol != self.symbol:
            return []

        self.history.append(event)

        if not self._has_enough_data():
            return []

        ema21 = self._calculate_ema(self.ema_fast_period)
        ema55 = self._calculate_ema(self.ema_mid_period)
        ema100 = self._calculate_ema(self.ema_slow_period)
        atr14 = self._calculate_atr(self.atr_period)

        if atr14 is None or atr14 <= 0:
            return []

        trend_long = ema21 > ema55 > ema100
        trend_short = ema21 < ema55 < ema100
        pullback = abs(event.close - ema21) < atr14
        bullish_candle = event.close > event.open
        bearish_candle = event.close < event.open

        long_signal = trend_long and pullback and bullish_candle
        short_signal = trend_short and pullback and bearish_candle

        signals: List[SignalEvent] = []

        if long_signal and self.last_signal_side != "LONG":
            signals.append(
                SignalEvent(
                    event_type="SIGNAL",
                    timestamp=event.timestamp,
                    symbol=event.symbol,
                    side="LONG",
                    strategy_id=self.strategy_id,
                    reason="trend_pullback_confirmation_long",
                    metadata={
                        "ema21": ema21,
                        "ema55": ema55,
                        "ema100": ema100,
                        "atr14": atr14,
                    },
                )
            )
            self.last_signal_side = "LONG"
            return signals

        if short_signal and self.last_signal_side != "SHORT":
            signals.append(
                SignalEvent(
                    event_type="SIGNAL",
                    timestamp=event.timestamp,
                    symbol=event.symbol,
                    side="SHORT",
                    strategy_id=self.strategy_id,
                    reason="trend_pullback_confirmation_short",
                    metadata={
                        "ema21": ema21,
                        "ema55": ema55,
                        "ema100": ema100,
                        "atr14": atr14,
                    },
                )
            )
            self.last_signal_side = "SHORT"
            return signals

        if not long_signal and not short_signal:
            self.last_signal_side = None

        return signals

    def _has_enough_data(self) -> bool:
        required = max(self.ema_fast_period, self.ema_mid_period, self.ema_slow_period, self.atr_period) + 1
        return len(self.history) >= required

    def _calculate_ema(self, period: int) -> float:
        closes = [bar.close for bar in self.history]
        window = closes[-period:]

        alpha = 2 / (period + 1)
        ema = window[0]
        for price in window[1:]:
            ema = alpha * price + (1 - alpha) * ema
        return ema

    def _calculate_atr(self, period: int) -> Optional[float]:
        bars = list(self.history)
        if len(bars) < period + 1:
            return None

        true_ranges = []
        relevant = bars[-(period + 1):]

        for i in range(1, len(relevant)):
            current = relevant[i]
            previous = relevant[i - 1]

            high_low = current.high - current.low
            high_close = abs(current.high - previous.close)
            low_close = abs(current.low - previous.close)

            tr = max(high_low, high_close, low_close)
            true_ranges.append(tr)

        return mean(true_ranges)