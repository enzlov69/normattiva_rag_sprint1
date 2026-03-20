# FEDERATED_RUNNER_LIVE_SMOKE_TEST_PLAN_v1

## 1. Oggetto del micro-cantiere

Il presente micro-cantiere ha funzione esclusivamente **verificativa e non evolutiva**.

Scopo:
- accertare che `final_aba_runner_real_invoker.py` possa interrogare un **runner federato vivo**;
- verificare che la risposta reale rientri nel layer contrattuale A→B→A già stabilizzato;
- confermare che il Livello B resti **documentale, subordinato, tracciabile e bloccabile**.

Questo micro-cantiere **non** modifica il fondativo v2, **non** modifica il runner federato salvo necessità eccezionale e **non** introduce campi decisori o validativi nel Livello B.

## 2. Perimetro metodologico vincolante

Restano inderogabili le seguenti regole:
- nessun bypass del layer di handoff;
- nessuna response del Livello B può produrre GO/NO-GO, `firma_ready`, `output_authorized`, `final_opposability` o equivalenti;
- nessuna response del Livello B può chiudere `M07-LPR`;
- i blocchi critici del Livello B devono propagarsi al Livello A e non sono ignorabili;
- il pacchetto documentale reale non equivale a RAC, decisione, motivazione o output opponibile.

## 3. Architettura minima del test vivo

Flusso ammesso:

`test smoke live -> FederatedRunnerRealInvoker -> transport reale configurato -> runner federato vivo -> response reale validata -> FinalABARuntimeHandoffService -> ritorno controllato a Livello A`

Punto di controllo:
- il test **non** chiama direttamente il runner dal Livello A applicativo;
- il test verifica il runner **tramite** l'adapter già approvato.

## 4. Prerequisiti tecnici

Prima di eseguire i test live devono essere disponibili:
- endpoint/transport reale del runner federato;
- eventuali credenziali o token di accesso;
- configurazione locale del transport in forma importabile da Python;
- ambiente opt-in per evitare esecuzioni involontarie nei test ordinari.

## 5. Convenzione di esecuzione consigliata

I test live devono essere eseguiti **solo** quando l'operatore imposta:

- `FEDERATED_RUNNER_LIVE_SMOKE=1`
- `FEDERATED_RUNNER_LIVE_TRANSPORT_IMPORT=<modulo>:<callable>`

Esempio di valore ammesso per il secondo parametro:
- `runtime.federated_runner_live_transport:build_transport`
- `runtime.federated_runner_live_transport:get_transport`
- `runtime.federated_runner_live_transport:transport`

Il callable importato può essere:
- una factory senza argomenti che restituisce il transport callable;
- direttamente il transport callable.

## 6. Contratto minimo atteso dal runner vivo

La response reale deve contenere almeno:
- `request_id`
- `case_id`
- `trace_id`
- `api_version`
- `responder_module`
- `status`
- `payload`
- `warnings`
- `errors`
- `blocks`
- `timestamp`

Nel `documentary_packet` devono risultare almeno:
- `sources`
- `norm_units`
- `citations_valid`
- `citations_blocked`
- `vigenza_records`
- `cross_reference_records`
- `coverage_assessment`
- `warnings`
- `errors`
- `blocks`
- `shadow_fragment`

## 7. Blocchi di rigetto automatico

La response reale va rigettata o degradata immediatamente se presenta uno dei seguenti profili:
- campi vietati del Livello B (`final_decision`, `go_no_go`, `firma_ready`, `output_authorized`, `m07_closed`, `m07_completed`, `m07_approved`, ecc.);
- mancata corrispondenza tra `request_id` / `case_id` / `trace_id` e quelli della request;
- packet documentale incompleto;
- `coverage_assessment` non strutturato;
- `shadow_fragment` assente o non strutturato;
- blocchi critici non propagati all'envelope;
- tentativo di far apparire opponibile il risultato del Livello B.

## 8. Esiti attesi dei tre test smoke

### 8.1 Connectivity smoke
Verifica che:
- il transport reale sia configurato;
- il runner vivo risponda;
- il contratto minimo di envelope sia presente.

### 8.2 Documentary contract smoke
Verifica che:
- il pacchetto reale sia documentale;
- il ritorno passi nell'handoff A→B→A;
- il risultato resti `NOT_OPPONIBLE_OUTSIDE_LEVEL_A`;
- il next step resti in capo al Livello A.

### 8.3 Forbidden fields smoke
Verifica che:
- la response reale non contenga campi vietati;
- se compaiono, il test fallisca immediatamente;
- M07 non venga mai chiuso dal runner.

## 9. Criterio di successo

Il micro-cantiere è chiuso positivamente solo se:
- il runner vivo è effettivamente raggiunto;
- la response reale rientra nell'adapter senza errori di contratto;
- la response resta documentale e non opponibile;
- non compaiono campi decisori o validativi;
- non compare chiusura M07;
- audit trail e shadow risultano coerenti nel passaggio di handoff.

## 10. Criterio di stop

Il micro-cantiere va fermato immediatamente se:
- il runner vivo risponde con payload non contrattuale;
- emergono campi vietati di Livello B;
- si verifica chiusura o approvazione di M07;
- il transport reale richiede modifica distruttiva del layer di handoff;
- i test live obbligano a spostare il primo punto di accoppiamento fuori dall'adapter controllato.

## 11. Comandi consigliati

```bash
python -m pytest tests/test_final_aba_runner_live_smoke_connectivity.py -q -rs
python -m pytest tests/test_final_aba_runner_live_smoke_documentary_contract.py -q -rs
python -m pytest tests/test_final_aba_runner_live_smoke_forbidden_fields.py -q -rs
python -m pytest tests/test_final_aba_runner_live_smoke_connectivity.py tests/test_final_aba_runner_live_smoke_documentary_contract.py tests/test_final_aba_runner_live_smoke_forbidden_fields.py -q -rs
```

Nota operativa: senza le variabili ambiente di opt-in, i test devono risultare **skipped** e non fallire, per non contaminare la suite ordinaria.
