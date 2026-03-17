# Validazione reale D.Lgs. 118/2011

Questa patch introduce una validazione end-to-end su fixture JSON del **DECRETO LEGISLATIVO 23 giugno 2011, n. 118**.

## File principali
- `tests/fixtures/normattiva/dlgs118_search_item_real.json`
- `tests/fixtures/normattiva/dlgs118_detail_payload_real.json`
- `src/runtime/dlgs118_real_validation_runner.py`
- `tests/e2e/test_dlgs118_real_payload_flow.py`

## Obiettivo
Verificare che il flusso tecnico completo:
- legga un payload reale/realistico Normattiva del D.Lgs. 118/2011;
- costruisca `SourceDocument`, `NormUnit` e `ChunkRecord`;
- produca citazioni valide;
- gestisca rinvii, coverage e supporto M07;
- costruisca il pacchetto Livello B;
- trasferisca il controllo al Livello A;
- autorizzi l'output tecnico solo nel Livello A.

## Esecuzione
```powershell
pytest -q tests/e2e/test_dlgs118_real_payload_flow.py
```

## Facoltativo: comando CLI
Se vuoi un comando analogo a `run-tuel-validation`, puoi integrare in `main.py`:
- import di `run_dlgs118_real_validation`
- funzione `run_dlgs118_validation()`
- ramo CLI `run-dlgs118-validation`

## Nota metodologica
La fixture mantiene metadati ufficiali del D.Lgs. 118/2011 e una struttura di dettaglio compatibile con il mapping corrente.
Il risultato resta tecnico-documentale e non sostituisce il giudizio finale del Metodo Cerda.
