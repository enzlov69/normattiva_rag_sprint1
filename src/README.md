# Sistema standard di bootstrap Normattiva

Questo pacchetto contiene un sistema riusabile per acquisire norme da Normattiva in modo stabile e controllato.

## File inclusi

* `src/tools/normattiva\\\_bootstrap\\\_config.json`
* `src/tools/extract\\\_normattiva\\\_article\\\_index.py`
* `src/tools/bootstrap\\\_normattiva\\\_articles.py`
* `src/tools/build\\\_normattiva\\\_commi.py`
* `src/tools/fix\\\_encoding\\\_normattiva.py`
* `src/tools/generate\\\_normattiva\\\_manifests.py`

## Flusso operativo standard

1. salvare l’atto intero HTML di Normattiva in `data/raw/...`
2. aggiornare `normattiva\\\_bootstrap\\\_config.json`
3. eseguire:

```powershell
py src/tools/extract\\\_normattiva\\\_article\\\_index.py
py src/tools/bootstrap\\\_normattiva\\\_articles.py
py src/tools/build\\\_normattiva\\\_commi.py
py src/tools/fix\\\_encoding\\\_normattiva.py
py src/tools/generate\\\_normattiva\\\_manifests.py
```

## Esempio preconfigurato

La configurazione allegata è già impostata per il `D.Lgs. 33/2013` versione `vigente`.

