"""Porta di invocazione per il runner federato black-box.

Il modulo definisce il contratto minimo che il layer di handoff runtime
può utilizzare per invocare un runner reale, mantenendo il runner isolato
rispetto al frontdoor e alla response contrattuale A/B.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Mapping


class RunnerInvocationError(RuntimeError):
    """Errore tecnico di invocazione del runner black-box."""


class RunnerInvocationPort(ABC):
    """Contratto minimo di invocazione del runner reale.

    Il port non interpreta i risultati del runner e non modifica la logica
    interna del runner stesso. Restituisce esclusivamente il payload raw.
    """

    @abstractmethod
    def invoke(self, runner_request: Mapping[str, Any]) -> Dict[str, Any]:
        """Invoca il runner reale e restituisce un payload raw.

        Args:
            runner_request: richiesta minima già normalizzata per il runner.

        Returns:
            Un dizionario grezzo proveniente dal runner.

        Raises:
            RunnerInvocationError: in caso di errore tecnico di invocazione.
        """
        raise NotImplementedError
