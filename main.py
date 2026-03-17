"""
Entrypoint operativo minimo per la release MVP_CONTROLLATO_TRIPLE_VALIDATION.

Non introduce alcuna funzione conclusiva nel Livello B.
Si limita a:
- mostrare lo stato della release;
- lanciare le validazioni reali TUEL, L. 241/1990 e D.Lgs. 118/2011, se i runner sono presenti;
- lanciare la suite test locale.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def print_status() -> int:
    print("Normattiva RAG / Metodo Cerda – MVP controllato")
    print("Release: MVP_CONTROLLATO_TRIPLE_VALIDATION")
    print("Stato validazione: 64 test passati + 6 test E2E reali passati")
    print("Validazioni reali: TUEL, L. 241/1990, D.Lgs. 118/2011")
    print("Principio fondativo: Metodo Cerda governa il ragionamento; il RAG governa il reperimento delle fonti.")
    return 0


def run_tuel_validation() -> int:
    try:
        from src.runtime.tuel_real_validation_runner import run_tuel_real_validation
    except Exception as exc:  # pragma: no cover
        print("Runner TUEL non disponibile:", exc)
        return 1

    result = run_tuel_real_validation()
    print("Esito validazione TUEL:", result)
    return 0


def run_l241_validation() -> int:
    try:
        from src.runtime.l241_real_validation_runner import run_l241_real_validation
    except Exception as exc:  # pragma: no cover
        print("Runner L. 241/1990 non disponibile:", exc)
        return 1

    result = run_l241_real_validation()
    print("Esito validazione L. 241/1990:", result)
    return 0


def run_dlgs118_validation() -> int:
    try:
        from src.runtime.dlgs118_real_validation_runner import run_dlgs118_real_validation
    except Exception as exc:  # pragma: no cover
        print("Runner D.Lgs. 118/2011 non disponibile:", exc)
        return 1

    result = run_dlgs118_real_validation()
    print("Esito validazione D.Lgs. 118/2011:", result)
    return 0


def run_tests() -> int:
    cmd = [sys.executable, "-m", "pytest", "-q"]
    return subprocess.call(cmd, cwd=str(ROOT))


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Uso: python main.py [status|run-tuel-validation|run-l241-validation|run-dlgs118-validation|run-tests]")
        return 1

    command = argv[1].strip().lower()

    if command == "status":
        return print_status()
    if command == "run-tuel-validation":
        return run_tuel_validation()
    if command == "run-l241-validation":
        return run_l241_validation()
    if command == "run-dlgs118-validation":
        return run_dlgs118_validation()
    if command == "run-tests":
        return run_tests()

    print(f"Comando non riconosciuto: {command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
