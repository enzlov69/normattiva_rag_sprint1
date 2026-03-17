# Validazione reale L. 241/1990

Questa patch introduce una validazione end-to-end su fixture JSON della **LEGGE 7 agosto 1990, n. 241**.

## File principali
- `tests/fixtures/normattiva/l241_search_item_real.json`
- `tests/fixtures/normattiva/l241_detail_payload_real.json`
- `src/runtime/l241_real_validation_runner.py`
- `tests/e2e/test_l241_real_payload_flow.py`

## Obiettivo
Verificare che il flusso tecnico completo:
- legga un payload reale/realistico Normattiva della L. 241/1990;
- costruisca `SourceDocument`, `NormUnit` e `ChunkRecord`;
- produca citazioni valide;
- gestisca rinvii, coverage e supporto M07;
- costruisca il pacchetto Livello B;
- trasferisca il controllo al Livello A;
- autorizzi l'output tecnico solo nel Livello A.

## Esecuzione
```powershell
pytest -q tests/e2e/test_l241_real_payload_flow.py
```

## Nota metodologica
La fixture mantiene metadati ufficiali della L. 241/1990 e una struttura di dettaglio compatibile con il mapping corrente.
Il risultato resta tecnico-documentale e non sostituisce il giudizio finale del Metodo Cerda.
