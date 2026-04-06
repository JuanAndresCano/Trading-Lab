#Carga el histórico y lo entrega barra por barra al sistema, generando 
# MarketEvent cada vez que avanza. Más adelante podrás tener otra versión 
# para datos live, y justo una de las metas del diseño event-driven es 
# minimizar duplicación entre backtest y ejecución real cambiando 
# principalmente el componente de datos.

# src/data/loader.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import pandas as pd

from src.core.event_queue import EventQueue
from src.core.events import MarketEvent


@dataclass
class DataSnapshot:
    """
    Representa la barra actual ya leída por el loader.
    """
    timestamp: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None


class HistoricalCSVDataHandler:
    """
    Data handler histórico basado en un pandas DataFrame.

    Requisitos del DataFrame:
    - Índice temporal
    - Columnas: Open, High, Low, Close
    - Volume es opcional
    """

    def __init__(self, data: pd.DataFrame, symbol: str, event_queue: EventQueue) -> None:
        self.symbol = symbol
        self.event_queue = event_queue
        self.data = data.copy()
        self._validate_input()

        self._cursor = 0
        self._latest_bar: Optional[DataSnapshot] = None

    def _validate_input(self) -> None:
        required = {"Open", "High", "Low", "Close"}
        missing = required - set(self.data.columns)
        if missing:
            raise ValueError(f"Faltan columnas requeridas: {sorted(missing)}")

        if not isinstance(self.data.index, pd.DatetimeIndex):
            raise ValueError("El índice del DataFrame debe ser DatetimeIndex")

        self.data = self.data.sort_index()

    def has_next(self) -> bool:
        """
        Indica si quedan barras por procesar.
        """
        return self._cursor < len(self.data)

    def stream_next(self) -> None:
        """
        Avanza una barra y publica un MarketEvent.
        """
        if not self.has_next():
            return

        row = self.data.iloc[self._cursor]
        timestamp = self.data.index[self._cursor].to_pydatetime()

        snapshot = DataSnapshot(
            timestamp=timestamp,
            symbol=self.symbol,
            open=float(row["Open"]),
            high=float(row["High"]),
            low=float(row["Low"]),
            close=float(row["Close"]),
            volume=float(row["Volume"]) if "Volume" in self.data.columns and pd.notna(row["Volume"]) else None,
        )

        self._latest_bar = snapshot
        self._cursor += 1

        self.event_queue.publish(
            MarketEvent(
                event_type="MARKET",
                timestamp=snapshot.timestamp,
                symbol=snapshot.symbol,
                open=snapshot.open,
                high=snapshot.high,
                low=snapshot.low,
                close=snapshot.close,
                volume=snapshot.volume,
            )
        )

    def get_latest_bar(self) -> Optional[DataSnapshot]:
        """
        Retorna la última barra leída.
        """
        return self._latest_bar