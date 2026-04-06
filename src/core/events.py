# Aquí defines los tipos de evento del sistema: MarketEvent, SignalEvent, 
# OrderEvent y FillEvent, que son la base típica de un backtester orientado 
# a eventos. Este archivo no hace cálculos de trading; solo define “qué 
# #información viaja” entre módulos, y documentar bien esos formatos es clave
# porque las interfaces deben dejar claro qué servicios ofrecen y qué datos
# transportan.

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional


EventType = Literal["MARKET", "SIGNAL", "ORDER", "FILL"]
SignalSide = Literal["LONG", "SHORT", "EXIT"]
OrderSide = Literal["BUY", "SELL"]
OrderType = Literal["MARKET"]


@dataclass(frozen=True)
class Event:
    """
    Clase base para todos los eventos del sistema.

    Propósito:
        Proveer una estructura mínima común para los mensajes internos
        del motor event-driven.

    Campos:
        event_type:
            Tipo del evento. Ej: MARKET, SIGNAL, ORDER, FILL.
        timestamp:
            Momento lógico del evento dentro del backtest.
    """
    event_type: EventType
    timestamp: datetime


@dataclass(frozen=True)
class MarketEvent(Event):
    """
    Evento emitido por el data loader cuando llega una nueva barra.

    Este evento representa la unidad mínima de información de mercado
    que la estrategia procesa en el baseline actual.
    """
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None


@dataclass(frozen=True)
class SignalEvent(Event):
    """
    Evento generado por una estrategia.

    La estrategia solo expresa intención de trading.
    No decide ejecución final, comisiones ni impacto en portafolio.
    """
    symbol: str
    side: SignalSide
    strategy_id: str
    strength: float = 1.0
    reason: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class OrderEvent(Event):
    """
    Evento generado por portfolio/risk a partir de una señal.

    Representa una orden concreta lista para ejecución simulada.
    """
    symbol: str
    side: OrderSide
    quantity: float
    order_type: OrderType = "MARKET"
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reason: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class FillEvent(Event):
    """
    Evento emitido por execution luego de simular una ejecución.

    Este evento confirma que una orden fue ejecutada y con qué precio/costo.
    """
    symbol: str
    side: OrderSide
    quantity: float
    fill_price: float
    commission: float = 0.0
    slippage: float = 0.0
    reason: Optional[str] = None
    metadata: dict = field(default_factory=dict)