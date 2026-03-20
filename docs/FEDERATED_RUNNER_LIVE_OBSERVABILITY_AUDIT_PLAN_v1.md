# FEDERATED_RUNNER_LIVE_OBSERVABILITY_AUDIT_PLAN_v1

## 1. Oggetto del cantiere

Il presente cantiere ha natura **additiva, non distruttiva e reversibile**.

Scopo:
- rendere osservabile il percorso live del runner federato;
- produrre prova tecnica minima del tragitto `A -> handoff -> invoker reale -> transport live -> runner -> handoff -> A`;
- irrobustire audit trail e SHADOW del passaggio documentale senza alterare la baseline v2.

Il cantiere **non** modifica il fondativo v2, **non** trasferisce poteri decisori al Livello B, **non** muta il punto di primo accoppiamento, che resta il layer contrattuale A→B→A.

## 2. Vincoli non derogabili

Restano vincolanti le seguenti regole:
- nessun bypass dell'handoff service;
- nessuna osservabilità può trasformarsi in decisione, validazione finale o output opponibile;
- nessun log tecnico del Livello B equivale a RAC, motivazione o chiusura M07-LPR;
- i blocchi del Livello B devono essere tracciati e propagati, non attenuati;
- audit trail e SHADOW devono essere **descrittivi**, non decisori;
- eventuali dati sensibili o credenziali di trasporto devono essere redatti/mascherati.

## 3. Soluzione raccomandata

Soluzione raccomandata:
- introdurre un modulo helper dedicato `runtime/federated_runner_live_observability.py`;
- usarlo **dopo** la validazione contrattuale del response envelope e **prima** della restituzione finale al Livello A;
- registrare nel tracciato tecnico solo metadati, contatori, blocchi, esiti di contratto e indicatori di non opponibilità.

Questa soluzione è preferibile perché:
- evita di riscrivere l'handoff service;
- separa la responsabilità di osservabilità dal controllo contrattuale;
- mantiene reversibile il cantiere;
- consente test unitari dedicati senza toccare il runner.

## 4. Architettura minima

Flusso raccomandato:

`Livello A -> handoff service -> invoker reale -> transport live -> runner federato -> invoker reale -> handoff service -> helper osservabilità -> Livello A`

Il modulo di osservabilità deve produrre almeno:
- evento audit di invocazione live;
- evento audit di ritorno live;
- snapshot SHADOW tecnico del request envelope;
- snapshot SHADOW tecnico del response envelope;
- sintesi strutturata del documentary packet;
- indicatore esplicito di `not_opponible_outside_level_a`.

## 5. File da creare

### Documenti
- `docs/FEDERATED_RUNNER_LIVE_OBSERVABILITY_AUDIT_PLAN_v1.md`
- `docs/FEDERATED_RUNNER_LIVE_OBSERVABILITY_RELEASE_NOTE_v1.md` (solo a chiusura)

### Runtime
- `runtime/federated_runner_live_observability.py`

### Test
- `tests/test_final_aba_live_observability_envelope.py`
- `tests/test_final_aba_live_observability_block_trace.py`
- `tests/test_final_aba_live_observability_non_opponibility.py`

## 6. Contratto minimo dell'osservabilità

Il helper di osservabilità deve poter ricevere:
- `request_envelope`
- `response_envelope`
- `transport_name`
- `transport_endpoint` (opzionale, solo in forma redatta)
- `live_mode` (bool)

E deve restituire un response envelope arricchito con:
- `audit.trail_events[]`
- `shadow.fragments[]`
- `payload.live_observability`

### 6.1 Campi minimi in `payload.live_observability`

- `live_path_observed`
- `transport_name`
- `transport_endpoint_redacted`
- `request_identity`
- `response_identity`
- `documentary_summary`
- `block_propagation_state`
- `level_b_documentary_only`
- `opponibility_status`
- `level_a_next_step`

## 7. Regole di blocco

Il modulo di osservabilità deve:
- rifiutare endpoint non stringa quando valorizzati;
- mascherare eventuali credenziali o token in endpoint/header/metadata;
- bloccare la marcatura positiva dell'osservabilità se il response envelope non è documentale;
- segnalare come `INCOMPLETE` l'osservabilità se mancano `request_id`, `case_id`, `trace_id` o `timestamp`;
- segnalare come `BLOCKS_PRESENT` la propagazione se il packet contiene blocchi;
- preservare sempre `NOT_OPPONIBLE_OUTSIDE_LEVEL_A`.

## 8. Criteri di successo

Il cantiere è chiuso positivamente solo se:
- il percorso live genera prova tecnica leggibile e strutturata;
- audit trail e SHADOW sono coerenti con il response reale;
- la propagazione dei blocchi è visibile nel tracciato;
- nessun dato di sicurezza viene esposto in chiaro;
- l'arricchimento di osservabilità non altera status, blocchi o regole del Livello B;
- il risultato resta non opponibile fuori dal Livello A.

## 9. Criteri di stop

Il cantiere va fermato se:
- l'osservabilità richiede bypass del layer di handoff;
- l'osservabilità introduce campi decisori nel payload del Livello B;
- il modulo tenta di certificare chiusura M07-LPR;
- i log contengono token, segreti o endpoint con credenziali non redatte;
- l'arricchimento altera o sopprime blocchi critici.

## 10. Patch point raccomandato

Punto di innesto consigliato nel `FinalABARuntimeHandoffService`:
- dopo `_enrich_shadow(response, request)`;
- prima di `_enrich_audit(response)` finale, oppure immediatamente dopo, purché l'ordine sia stabile e testato.

La chiamata raccomandata è del tipo:

```python
response = append_live_observability(
    request_envelope=request,
    response_envelope=response,
    transport_name="federated_runner_live_transport",
    transport_endpoint=os.getenv("FEDERATED_RUNNER_LIVE_ENDPOINT"),
    live_mode=(self.mode == "real"),
)
```

## 11. Sequenza di test raccomandata

```bash
python -m pytest tests/test_final_aba_live_observability_envelope.py -q
python -m pytest tests/test_final_aba_live_observability_block_trace.py -q
python -m pytest tests/test_final_aba_live_observability_non_opponibility.py -q
python -m pytest tests/test_final_aba_live_observability_envelope.py tests/test_final_aba_live_observability_block_trace.py tests/test_final_aba_live_observability_non_opponibility.py -q
```

## 12. Nota finale

Questo cantiere non cambia la sostanza del collegamento: il runner federato resta un sottosistema documentale subordinato. L'osservabilità aggiunge prova tecnica, non potere istruttorio o conclusivo.
