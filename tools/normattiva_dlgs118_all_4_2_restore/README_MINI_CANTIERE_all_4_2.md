# MINI-CANTIERE DI RIPRISTINO — `normattiva_dlgs118_2011_all_4_2`

## 1. Diagnosi tecnica sintetica

La collection `normattiva_dlgs118_2011_all_4_2` risulta logicamente registrata in Chroma e con `count > 0`, ma fallisce in query runtime con errore:

`Error creating hnsw segment reader: Nothing found on disk`

Questo quadro è tipico di una collection con **registry ancora presente** ma con **artefatti fisici HNSW corrotti, mancanti o disallineati** sul disco.  
Poiché le altre collection attive risultano interrogabili, il problema è **localizzato** e il ripristino corretto è **solo chirurgico** sulla collection target.

---

## 2. Perimetro sorgenti da verificare sul disco

Verifica questi percorsi operativi del cantiere `all_4_2`:

### Sorgenti primarie attese
- `data\normalized\annexes_118\all_4_2\all_4_2_canonical_cleantext.txt`
- `data\chunks\annexes_118\all_4_2_chunks.jsonl`
- `data\rag_ready\normattiva_dlgs118_2011_all_4_2.jsonl`

### Sorgenti secondarie/fallback
- `data\processed\annexes_118\all_4_2\`
- `data\normalized\norm_units\dlgs118_2011_all_4_2\`
- `data\processed\dlgs118_2011\all_4_2\`

### Storage Chroma
- `data\chroma\`

Gli script inclusi fanno **autodiscovery** sui path più probabili e lavorano solo sulla collection target.

---

## 3. Ordine esatto di esecuzione

Con venv attivo, dalla root del progetto:

```powershell
py tools\dlgs118_all_4_2_restore\01_check_all_4_2_sources.py
py tools\dlgs118_all_4_2_restore\02_rebuild_all_4_2_rag_ready.py
py tools\dlgs118_all_4_2_restore\03_delete_collection_all_4_2.py --yes
py tools\dlgs118_all_4_2_restore\04_reingest_collection_all_4_2.py --replace
py tools\dlgs118_all_4_2_restore\05_smoke_test_all_4_2.py
py tools\dlgs118_all_4_2_restore\06_stress_test_all_4_2.py
python tools\federated_tests\run_federated_active_corpora_tests.py
```

---

## 4. Note operative

- `02_rebuild...` non rifà crawling.
- `03_delete...` cancella **solo** `normattiva_dlgs118_2011_all_4_2`.
- `04_reingest...` reingesta **solo** la collection target.
- `05_smoke...` verifica count e query base.
- `06_stress...` simula query multi-run sulla sola collection per intercettare recidive HNSW.

---

## 5. Criterio di uscita dal mini-cantiere

Il mini-cantiere può considerarsi riuscito se, contemporaneamente:

1. `05_smoke_test_all_4_2.py` passa senza eccezioni;
2. `06_stress_test_all_4_2.py` chiude con `Failures = 0`;
3. il federated runner non registra più runtime failure su `normattiva_dlgs118_2011_all_4_2`.

Se il federated test resta non consolidato dopo azzeramento dei runtime failure, allora il problema residuo non è più infrastrutturale ma di pairing/ranking inter-corpus.
