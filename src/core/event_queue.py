# Este archivo encapsula la cola de eventos, normalmente una Queue, 
# para que el resto del sistema no dependa de una implementación concreta. 
# Su responsabilidad es simple: recibir eventos y entregarlos en orden,
# nada más.

# src/core/event_queue.py

from __future__ import annotations

from queue import Empty, Queue
from typing import Optional

from src.core.events import Event


class EventQueue:
    """
    Cola de eventos en memoria para el motor event-driven.

    Propósito:
        Centralizar el paso de mensajes internos del sistema.
        Todos los módulos publican aquí y el runner consume desde aquí.

    Qué hace:
        - Recibe eventos
        - Los entrega en orden FIFO
        - Oculta la implementación concreta de queue.Queue

    Qué no hace:
        - No interpreta eventos
        - No decide lógica de trading
        - No persiste nada
    """

    def __init__(self) -> None:
        self._queue: Queue[Event] = Queue()

    def publish(self, event: Event) -> None:
        """
        Inserta un evento en la cola.
        """
        self._queue.put(event)

    def get(self) -> Optional[Event]:
        """
        Extrae un evento de la cola si existe.
        Devuelve None si la cola está vacía.
        """
        try:
            return self._queue.get(block=False)
        except Empty:
            return None

    def is_empty(self) -> bool:
        """
        Indica si la cola está vacía.
        """
        return self._queue.empty()

    def size(self) -> int:
        """
        Retorna el número actual de eventos pendientes.
        """
        return self._queue.qsize()