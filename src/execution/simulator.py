# Este archivo simula la ejecución de órdenes: precio de entrada/salida, 
# fills, comisiones y slippage. Esto importa mucho porque el valor del 
# enfoque event-driven está en representar mejor el ciclo completo de 
# trading y no solo detectar señales “bonitas” sobre datos históricos.

# src/execution/simulator.py

from __future__ import annotations

from typing import List, Optional

from src.core.events import FillEvent, MarketEvent, OrderEvent


class SimulatedExecutionHandler:
    """
    Execution handler V1.

    Supuestos:
    - Fill inmediato
    - Precio basado en el close de la última barra conocida
    - Slippage fijo opcional
    - Comisión fija opcional
    """

    def __init__(
        self,
        slippage_per_unit: float = 0.0,
        commission_per_order: float = 0.0,
    ) -> None:
        self.slippage_per_unit = slippage_per_unit
        self.commission_per_order = commission_per_order
        self.last_market_event: Optional[MarketEvent] = None

    def on_market_event(self, event: MarketEvent) -> None:
        """
        Guarda la última referencia de mercado.
        """
        self.last_market_event = event

    def on_order_event(self, event: OrderEvent) -> List[FillEvent]:
        """
        Convierte una orden en una ejecución simulada.
        """
        if self.last_market_event is None:
            return []

        base_price = self.last_market_event.close

        if event.side == "BUY":
            fill_price = base_price + self.slippage_per_unit
        else:
            fill_price = base_price - self.slippage_per_unit

        return [
            FillEvent(
                event_type="FILL",
                timestamp=event.timestamp,
                symbol=event.symbol,
                side=event.side,
                quantity=event.quantity,
                fill_price=fill_price,
                commission=self.commission_per_order,
                slippage=self.slippage_per_unit,
                reason=event.reason,
                metadata={
                    "stop_loss": event.stop_loss,
                    "take_profit": event.take_profit,
                },
            )
        ]