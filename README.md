# Sistema standard di bootstrap Normattiva

Questo pacchetto contiene un sistema riusabile per acquisire norme da Normattiva in modo stabile e controllato.

## File inclusi
- `src/tools/normattiva_bootstrap_config.json`
- `src/tools/extract_normattiva_article_index.py`
- `src/tools/bootstrap_normattiva_articles.py`
- `src/tools/build_normattiva_commi.py`
- `src/tools/fix_encoding_normattiva.py`
- `src/tools/generate_normattiva_manifests.py`

## Flusso operativo standard
1. salvare l’atto intero HTML di Normattiva in `data/raw/...`
2. aggiornare `normattiva_bootstrap_config.json`
3. eseguire:

```powershell
py src/tools/extract_normattiva_article_index.py
py src/tools/bootstrap_normattiva_articles.py
py src/tools/build_normattiva_commi.py
py src/tools/fix_encoding_normattiva.py
py src/tools/generate_normattiva_manifests.py
```

## Esempio preconfigurato
La configurazione allegata è già impostata per il `D.Lgs. 33/2013` versione `vigente`.
