# Este es el orquestador del backtest: pide nuevos datos, toma eventos de la 
# cola y decide qué módulo reacciona a cada tipo de evento. El patrón clásico 
# es MARKET -> STRATEGY/PORTFOLIO -> SIGNAL -> ORDER -> FILL, así que este 
# archivo es básicamente el “director de tráfico” del laboratorio.

# src/core/runner.py

from __future__ import annotations

from dataclasses import dataclass

from src.core.event_queue import EventQueue
from src.core.events import FillEvent, MarketEvent, OrderEvent, SignalEvent


@dataclass
class BacktestStats:
    """
    Métricas simples del loop para debugging inicial.
    """
    market_events: int = 0
    signal_events: int = 0
    order_events: int = 0
    fill_events: int = 0
    processed_events: int = 0


class BacktestRunner:
    """
    Orquestador principal del backtest.

    Flujo general:
        1. El data handler avanza una barra.
        2. El data handler publica un MarketEvent.
        3. El runner consume eventos y los enruta.
        4. Strategy -> SignalEvent
        5. Portfolio/Risk -> OrderEvent
        6. Execution -> FillEvent
        7. Portfolio actualiza estado con FillEvent
    """

    def __init__(
        self,
        data_handler,
        strategy,
        portfolio,
        execution_handler,
        event_queue: EventQueue,
    ) -> None:
        self.data_handler = data_handler
        self.strategy = strategy
        self.portfolio = portfolio
        self.execution_handler = execution_handler
        self.event_queue = event_queue
        self.stats = BacktestStats()

    def run(self) -> BacktestStats:
        """
        Ejecuta el backtest completo hasta que se acaben los datos.
        """
        while self.data_handler.has_next():
            self.data_handler.stream_next()

            while not self.event_queue.is_empty():
                event = self.event_queue.get()
                if event is None:
                    break

                self.stats.processed_events += 1
                self._dispatch(event)

        return self.stats

    def _dispatch(self, event) -> None:
        """
        Envía cada evento al componente correcto.
        """
        if isinstance(event, MarketEvent):
            self.stats.market_events += 1
            signals = self.strategy.on_market_event(event)
            for signal in signals:
                self.event_queue.publish(signal)

            self.execution_handler.on_market_event(event)

            exit_orders = self.portfolio.on_market_event(event)
            for order in exit_orders:
                self.event_queue.publish(order)
            return

        if isinstance(event, SignalEvent):
            self.stats.signal_events += 1
            orders = self.portfolio.on_signal_event(event)
            for order in orders:
                self.event_queue.publish(order)
            return

        if isinstance(event, OrderEvent):
            self.stats.order_events += 1
            fills = self.execution_handler.on_order_event(event)
            for fill in fills:
                self.event_queue.publish(fill)
            return

        if isinstance(event, FillEvent):
            self.stats.fill_events += 1
            self.portfolio.on_fill_event(event)
            return

        raise ValueError(f"Tipo de evento no soportado: {type(event).__name__}")