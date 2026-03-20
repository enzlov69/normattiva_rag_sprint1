# FEDERATED_RUNNER_LIVE_HARDENING_PLAN_v1

## 1. Finalità del cantiere

Il cantiere rafforza il percorso live già collegato e già osservabile, senza modificare il principio fondativo del progetto:

- il primo punto di accoppiamento resta il layer contrattuale A→B→A;
- il Livello B resta sottosistema documentale subordinato;
- nessuna funzione decisoria, validativa o opponibile può nascere nel transport o nel runner;
- i blocchi tecnici e documentali devono propagarsi al Livello A.

## 2. Obiettivi specifici

Il cantiere introduce tre presìdi aggiuntivi:

1. hardening del transport live su errori HTTP, timeout, response non JSON e retry controllato;
2. fallback documentale bloccante e non opponibile in caso di errore del percorso live;
3. matrice tecnica di evidenze documentali per coverage, vigenza e rinvii, utile al Livello A ma non sostitutiva di M07-LPR, RAC o Final Compliance Gate.

## 3. Rischi da presidiare

### 3.1 Rischi tecnici
- timeout o indisponibilità del runner federato;
- response HTTP 429/502/503/504 con necessità di retry limitato;
- response formalmente ricevuta ma non JSON;
- response JSON non conforme al contratto minimo documentale.

### 3.2 Rischi metodologici
- degradazione silenziosa di un errore tecnico in warning non bloccante;
- uso del fallback come surrogato di decisione;
- trasformazione della matrice documentale in esito applicativo;
- perdita di tracciabilità tra request, fallback, blocchi e SHADOW.

## 4. Soluzione raccomandata

### 4.1 Runtime
Aggiornare `runtime/federated_runner_live_transport.py` con:
- retry configurabile e limitato;
- distinzione tra errori di connessione, errori HTTP e response non valide;
- wrapper `invoke_transport_with_guarded_fallback(...)` che restituisce un envelope documentale bloccato e non opponibile;
- helper `append_documentary_evidence_matrix(...)` che ricava indicatori sintetici su coverage, vigenza e rinvii.

### 4.2 Handoff integration point
Il punto corretto resta nel handoff service, in coda alla validazione contrattuale e prima della restituzione finale al Livello A:

1. invocazione transport reale;
2. eventuale fallback bloccante se il transport fallisce;
3. costruzione matrice evidenze documentali;
4. ritorno al Livello A per i gate metodologici veri.

## 5. Regole di blocco

1. nessun retry infinito;
2. nessun fallback con status “OK” o equivalente;
3. ogni fallback deve contenere almeno i blocchi:
   - `CRITICAL_DOCUMENTARY_BLOCK`
   - `LIVE_TRANSPORT_ERROR`
   - `OUTPUT_NOT_OPPONIBLE`
4. la matrice coverage/vigenza/rinvii non può chiudere M07-LPR;
5. la matrice non può produrre `go_no_go`, `firma_ready`, `output_authorized`, `final_decision` o equivalenti.

## 6. File del cantiere

- `docs/FEDERATED_RUNNER_LIVE_HARDENING_PLAN_v1.md`
- `runtime/federated_runner_live_transport.py` (versione aggiornata completa)
- `tests/test_final_aba_live_transport_error_handling.py`
- `tests/test_final_aba_live_transport_retry_fallback.py`
- `tests/test_final_aba_live_documentary_evidence_matrix.py`

## 7. Criteri di accettazione

Il cantiere è chiuso positivamente solo se:

- il transport retrya solo su errori configurati;
- il fallback è bloccante, tracciato e non opponibile;
- la matrice documentale segnala coverage/vigenza/rinvii senza sconfinare in valutazioni applicative;
- i test dedicati passano senza rompere i test live già chiusi.

## 8. Sequenza minima di test

```powershell
python -m pytest tests/test_final_aba_live_transport_error_handling.py -q
python -m pytest tests/test_final_aba_live_transport_retry_fallback.py -q
python -m pytest tests/test_final_aba_live_documentary_evidence_matrix.py -q
python -m pytest tests/test_final_aba_live_transport_error_handling.py tests/test_final_aba_live_transport_retry_fallback.py tests/test_final_aba_live_documentary_evidence_matrix.py -q
```
