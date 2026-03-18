"""Invocatore reale del runner federato.

Questo modulo fornisce un adapter controllato verso un runner reale, visto
come black-box. L'invocatore può lavorare con un callable Python esplicito o
con un entrypoint risolto dinamicamente tramite dotted path.
"""

from __future__ import annotations

import importlib
from typing import Any, Callable, Dict, Mapping, Optional

from runtime.final_ab_runner_invocation_port import (
    RunnerInvocationError,
    RunnerInvocationPort,
)


class FinalABRunnerRealInvoker(RunnerInvocationPort):
    """Invocatore reale del runner federato black-box."""

    def __init__(
        self,
        *,
        runner_callable: Optional[Callable[[Mapping[str, Any]], Dict[str, Any]]] = None,
        dotted_path: Optional[str] = None,
        entrypoint_name: Optional[str] = None,
    ) -> None:
        self._runner_callable = runner_callable
        self._dotted_path = dotted_path
        self._entrypoint_name = entrypoint_name

        if self._runner_callable is None and self._dotted_path is None:
            raise ValueError(
                "Occorre fornire runner_callable oppure dotted_path per invocare il runner reale."
            )

    @property
    def entrypoint_label(self) -> str:
        """Etichetta tecnica dell'entrypoint attivo."""
        if self._runner_callable is not None:
            return getattr(self._runner_callable, "__name__", "callable_runner")
        assert self._dotted_path is not None
        return self._dotted_path

    def _resolve_callable(self) -> Callable[[Mapping[str, Any]], Dict[str, Any]]:
        if self._runner_callable is not None:
            return self._runner_callable

        assert self._dotted_path is not None
        module_path, separator, attr_name = self._dotted_path.partition(":")
        if not separator:
            raise RunnerInvocationError(
                "Il dotted_path del runner deve avere formato 'modulo:callable'."
            )

        try:
            module = importlib.import_module(module_path)
        except Exception as exc:  # pragma: no cover - protezione tecnica
            raise RunnerInvocationError(
                f"Impossibile importare il modulo runner '{module_path}': {exc}"
            ) from exc

        try:
            target = getattr(module, attr_name)
        except AttributeError as exc:  # pragma: no cover - protezione tecnica
            raise RunnerInvocationError(
                f"Il callable '{attr_name}' non esiste nel modulo '{module_path}'."
            ) from exc

        if self._entrypoint_name:
            try:
                target = getattr(target, self._entrypoint_name)
            except AttributeError as exc:  # pragma: no cover - protezione tecnica
                raise RunnerInvocationError(
                    f"Il metodo '{self._entrypoint_name}' non esiste nell'oggetto runner risolto."
                ) from exc

        if not callable(target):
            raise RunnerInvocationError("L'entrypoint risolto per il runner non è invocabile.")

        return target

    def invoke(self, runner_request: Mapping[str, Any]) -> Dict[str, Any]:
        runner_callable = self._resolve_callable()
        try:
            raw_response = runner_callable(runner_request)
        except Exception as exc:
            raise RunnerInvocationError(f"Errore tecnico nell'invocazione del runner: {exc}") from exc

        if not isinstance(raw_response, dict):
            raise RunnerInvocationError(
                "Il runner reale ha restituito una risposta non conforme: atteso dict."
            )

        return raw_response
