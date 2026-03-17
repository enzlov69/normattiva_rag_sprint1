# MINI-CANTIERE DI RIPRISTINO — `normattiva_l241_1990`

## Obiettivo
Ripristinare in modo pulito la sola collection `normattiva_l241_1990` senza toccare le altre collection attive.

## File inclusi
- `_common.py`
- `00_verify_l241_sources.py`
- `01_delete_l241_collection_safe.py`
- `02_reingest_l241_collection.py`
- `03_smoke_test_l241.py`
- `04_stress_test_l241.py`

## Presupposti
1. Il repository di lavoro è la root del progetto `normattiva_rag_sprint1`.
2. I file devono essere copiati in: `tools/l241_repair/`
3. Il corpus sorgente L. 241/1990 è già disponibile in uno dei percorsi `rag_ready` previsti.
4. Il modello embedding in uso resta: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

## Ordine di esecuzione consigliato
```powershell
py tools\l241_repair\00_verify_l241_sources.py
py tools\l241_repair\01_delete_l241_collection_safe.py --yes-delete
py tools\l241_repair\02_reingest_l241_collection.py
py tools\l241_repair\03_smoke_test_l241.py
py tools\l241_repair\04_stress_test_l241.py --loops 8
python tools\federated_tests\run_federated_active_corpora_tests.py
```

## Note operative
- Lo script di delete è blindato e cancella solo `normattiva_l241_1990`.
- Lo script di reingest si rifiuta di sovrascrivere una collection esistente.
- Smoke e stress test usano la stessa embedding function del reingest per evitare falsi negativi.
- Se il file sorgente non viene trovato automaticamente, usare `--source-file <percorso>` nello script `02_reingest_l241_collection.py`.
