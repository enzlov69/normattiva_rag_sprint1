# Validazione reale TUEL

Questa patch introduce una validazione end-to-end su fixture JSON del TUEL.

## File principali
- `tests/fixtures/normattiva/tuel_search_item_real.json`
- `tests/fixtures/normattiva/tuel_detail_payload_real.json`
- `src/runtime/tuel_real_validation_runner.py`
- `tests/e2e/test_tuel_real_payload_flow.py`

## Obiettivo
Verificare che il flusso tecnico completo:
- legga un payload reale/realistico Normattiva del TUEL;
- costruisca `SourceDocument`, `NormUnit` e `ChunkRecord`;
- produca citazioni valide;
- gestisca rinvii, coverage e supporto M07;
- costruisca il pacchetto Livello B;
- trasferisca il controllo al Livello A;
- autorizzi l'output tecnico solo nel Livello A.

## Esecuzione
```powershell
pytest -q tests/e2e/test_tuel_real_payload_flow.py
```

## Nota metodologica
La fixture mantiene metadati ufficiali del TUEL e una struttura di dettaglio compatibile con il mapping corrente.
Il risultato resta tecnico-documentale e non sostituisce il giudizio finale del Metodo Cerda.
