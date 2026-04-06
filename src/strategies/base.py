# Aquí defines la interfaz base de estrategia, por ejemplo algo como 
# on_market_event(event) -> Optional[SignalEvent]. Esto te obliga a que 
# todas las estrategias futuras hablen el mismo idioma, y esa consistencia
# es muy útil cuando quieras comparar Mark II contra Mark III o variantes 
# del mismo sistema.

# src/strategies/base.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from src.core.events import MarketEvent, SignalEvent


class BaseStrategy(ABC):
    """
    Contrato base para cualquier estrategia del laboratorio.

    Regla importante:
        La estrategia observa mercado y emite señales.
        No actualiza portafolio, no ejecuta órdenes y no calcula PnL.
    """

    def __init__(self, strategy_id: str) -> None:
        self.strategy_id = strategy_id

    @abstractmethod
    def on_market_event(self, event: MarketEvent) -> List[SignalEvent]:
        """
        Procesa una nueva barra y devuelve cero o más señales.
        """
        raise NotImplementedError