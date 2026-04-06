# El portafolio recibe señales y genera órdenes, además de actualizar 
# posiciones y holdings cuando llegan fills, que es exactamente el rol 
# que aparece en los diseños clásicos de backtesting orientado a eventos. 
# En implementaciones más sofisticadas parte del riesgo puede delegarse a 
# otra clase, pero incluso así el portafolio sigue siendo el lugar donde se 
# refleja el estado financiero del sistema.

# src/portfolio/portfolio.py

from __future__ import annotations
from src.analytics.metrics import TradeRecord
from dataclasses import dataclass
from typing import List, Optional

from src.core.events import FillEvent, MarketEvent, OrderEvent, SignalEvent


@dataclass
class PositionState:
    """
    Estado simplificado de la posición actual.
    """
    side: Optional[str] = None          # LONG / SHORT / None
    quantity: float = 0.0
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    entry_timestamp: Optional[object] = None


class Portfolio:
    """
    Portfolio V1 para una estrategia y un símbolo.

    Reglas V1:
    - Solo una posición abierta a la vez
    - Tamaño fijo por orden
    - El SL/TP se calcula a partir del ATR incluido en el SignalEvent
    - Detecta salida por stop o take profit usando MarketEvent
    """

    def __init__(
        self,
        symbol: str,
        initial_cash: float = 1000.0,
        fixed_quantity: float = 1.0,
        stop_atr_multiple: float = 1.0,
        take_profit_atr_multiple: float = 2.0,
    ) -> None:
        self.symbol = symbol
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.fixed_quantity = fixed_quantity
        self.stop_atr_multiple = stop_atr_multiple
        self.take_profit_atr_multiple = take_profit_atr_multiple

        self.position = PositionState()
        self.last_market_event: Optional[MarketEvent] = None
        self.realized_pnl: float = 0.0
        self.closed_trades: List[TradeRecord] = []

    def on_market_event(self, event: MarketEvent) -> List[OrderEvent]:
        """
        Actualiza referencia de mercado y evalúa SL/TP.
        """
        self.last_market_event = event
        exit_orders: List[OrderEvent] = []

        if self.position.side == "LONG":
            if self.position.stop_loss is not None and event.low <= self.position.stop_loss:
                exit_orders.append(self._build_exit_order(event, "SELL", "long_stop_loss"))
            elif self.position.take_profit is not None and event.high >= self.position.take_profit:
                exit_orders.append(self._build_exit_order(event, "SELL", "long_take_profit"))

        elif self.position.side == "SHORT":
            if self.position.stop_loss is not None and event.high >= self.position.stop_loss:
                exit_orders.append(self._build_exit_order(event, "BUY", "short_stop_loss"))
            elif self.position.take_profit is not None and event.low <= self.position.take_profit:
                exit_orders.append(self._build_exit_order(event, "BUY", "short_take_profit"))

        return exit_orders

    def on_signal_event(self, event: SignalEvent) -> List[OrderEvent]:
        """
        Traduce una señal a una orden si no hay posición abierta.
        """
        if event.symbol != self.symbol:
            return []

        if self.last_market_event is None:
            return []

        if self.position.side is not None:
            return []

        atr = event.metadata.get("atr14")
        if atr is None or atr <= 0:
            return []

        entry_price = self.last_market_event.close

        if event.side == "LONG":
            stop_loss = entry_price - (self.stop_atr_multiple * atr)
            take_profit = entry_price + (self.take_profit_atr_multiple * atr)
            return [
                OrderEvent(
                    event_type="ORDER",
                    timestamp=event.timestamp,
                    symbol=event.symbol,
                    side="BUY",
                    quantity=self.fixed_quantity,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    reason=event.reason,
                    metadata={"signal_side": "LONG", "entry_price_reference": entry_price},
                )
            ]

        if event.side == "SHORT":
            stop_loss = entry_price + (self.stop_atr_multiple * atr)
            take_profit = entry_price - (self.take_profit_atr_multiple * atr)
            return [
                OrderEvent(
                    event_type="ORDER",
                    timestamp=event.timestamp,
                    symbol=event.symbol,
                    side="SELL",
                    quantity=self.fixed_quantity,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    reason=event.reason,
                    metadata={"signal_side": "SHORT", "entry_price_reference": entry_price},
                )
            ]

        return []

    def on_fill_event(self, event: FillEvent) -> None:
        """
        Actualiza estado luego de una ejecución.
        """
        if event.symbol != self.symbol:
            return

        if event.side == "BUY":
            # Abrir una nueva posición LONG
            if self.position.side is None:
                self.position.side = "LONG"
                self.position.quantity = event.quantity
                self.position.entry_price = event.fill_price
                self.position.stop_loss = event.metadata.get("stop_loss")
                self.position.take_profit = event.metadata.get("take_profit")
                self.position.entry_timestamp = event.timestamp
                self.cash -= event.fill_price * event.quantity + event.commission

            # Cerrar una posición SHORT existente
            elif self.position.side == "SHORT":
                pnl = (self.position.entry_price - event.fill_price) * event.quantity - event.commission
                self.realized_pnl += pnl
                self.cash += pnl

                trade = TradeRecord(
                    entry_timestamp=self.position.entry_timestamp,
                    exit_timestamp=event.timestamp,
                    side="SHORT",
                    entry_price=self.position.entry_price,
                    exit_price=event.fill_price,
                    quantity=event.quantity,
                    pnl=pnl,
                    return_pct=(self.position.entry_price - event.fill_price) / self.position.entry_price,
                    exit_reason=event.reason or "unknown",
                )
                self.closed_trades.append(trade)

                self._reset_position()

        elif event.side == "SELL":
            # Abrir una nueva posición SHORT
            if self.position.side is None:
                self.position.side = "SHORT"
                self.position.quantity = event.quantity
                self.position.entry_price = event.fill_price
                self.position.stop_loss = event.metadata.get("stop_loss")
                self.position.take_profit = event.metadata.get("take_profit")
                self.position.entry_timestamp = event.timestamp
                self.cash += event.fill_price * event.quantity - event.commission

            # Cerrar una posición LONG existente
            elif self.position.side == "LONG":
                pnl = (event.fill_price - self.position.entry_price) * event.quantity - event.commission
                self.realized_pnl += pnl
                self.cash += pnl

                trade = TradeRecord(
                    entry_timestamp=self.position.entry_timestamp,
                    exit_timestamp=event.timestamp,
                    side="LONG",
                    entry_price=self.position.entry_price,
                    exit_price=event.fill_price,
                    quantity=event.quantity,
                    pnl=pnl,
                    return_pct=(event.fill_price - self.position.entry_price) / self.position.entry_price,
                    exit_reason=event.reason or "unknown",
                )
                self.closed_trades.append(trade)

                self._reset_position()

    def _build_exit_order(self, event: MarketEvent, side: str, reason: str) -> OrderEvent:
        return OrderEvent(
            event_type="ORDER",
            timestamp=event.timestamp,
            symbol=event.symbol,
            side=side,
            quantity=self.position.quantity,
            stop_loss=None,
            take_profit=None,
            reason=reason,
            metadata={"exit_reason": reason},
        )

    def _reset_position(self) -> None:
        self.position = PositionState()