# Final AB Runtime Response-Envelope Gate Spec v1

## 1. Scopo

Questo cantiere introduce un gate tecnico **post-mapper** sul percorso runtime controllato A→B→A.

Il gate si colloca **dopo**:
- invocazione del runner federato reale;
- raw validation gate pre-mapper già consolidato;
- response mapper.

Il gate si colloca **prima** della consegna dell'`ABResponseEnvelope` finale al Livello A.

## 2. Obiettivo operativo

Il gate deve intercettare e bloccare o degradare almeno i seguenti casi:

1. envelope finale incompleto;
2. incoerenza tra `status` e contenuto di `warnings` / `errors` / `blocks`;
3. perdita o attenuazione impropria di blocchi critici emersi a monte;
4. ricomparsa di campi vietati del Livello B nel payload finale;
5. `DocumentaryPacket` finale incompleto o non tracciabile;
6. incompletezza di audit/shadow nei casi critici;
7. downgrade improprio di `BLOCKED` o `REJECTED`;
8. incoerenza tra raw validation result e response finale.

## 3. Regole non derogabili

Il gate:
- **non sostituisce** il raw validator pre-mapper;
- **non modifica** il runner federato black-box;
- **non altera** retrieval, ranking, router o corpus;
- **non chiude** M07;
- **non produce** output opponibili;
- **rafforza** la separazione tra Livello A e Livello B.

## 4. Posizionamento architetturale

Pipeline canonica:

`frontdoor runtime -> handoff service -> runner invoker -> raw validation gate -> response mapper -> response-envelope gate -> ABResponseEnvelope finale`

## 5. Regole di validazione del gate

### 5.1 Envelope contract

Campi minimi obbligatori:
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

Se uno di tali campi manca, il gate deve:
- aggiungere errore tecnico;
- aprire almeno `OUTPUT_NOT_OPPONIBLE`;
- forzare stato finale almeno a `BLOCKED`.

### 5.2 DocumentaryPacket minimo

Il `payload.documentary_packet` deve contenere almeno:
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

Se incompleto, il gate deve bloccare l'opponibilità tecnica del pacchetto.

### 5.3 Campi vietati del Livello B

Il gate deve rigettare o bloccare la ricomparsa di campi vietati, tra cui almeno:
- `final_decision`
- `decision_status`
- `final_applicability`
- `output_authorized`
- `compliance_go`
- `m07_closed`
- `rac_finalized`
- `signature_ready`

Esito minimo:
- errore tecnico dedicato;
- blocco `RAG_SCOPE_VIOLATION`;
- stato finale almeno `REJECTED`.

### 5.4 Propagazione blocchi critici

Se il raw validation result o la response grezza contenevano blocchi critici finali, il mapper non può eliminarli o attenuarli.

Se ciò accade, il gate deve:
- rilevare la perdita;
- reintegrare i blocchi mancanti;
- registrare mismatch;
- forzare stato finale coerente.

### 5.5 Audit / SHADOW completeness guard

Nei casi critici (`DEGRADED`, `BLOCKED`, `REJECTED`, `ERROR`, presenza di errori o blocchi critici), il gate richiede:
- frammento audit minimo;
- frammento shadow minimo.

In mancanza di uno dei due:
- apertura `AUDIT_INCOMPLETE`;
- degradazione o blocco del rilascio verso il Livello A.

## 6. Regola di status reconciliation

Il gate ricalcola lo stato finale secondo regole minime:
- campi vietati o `RAG_SCOPE_VIOLATION` -> `REJECTED`;
- blocchi critici aperti -> `BLOCKED`;
- errori senza blocchi critici -> `DEGRADED`;
- warnings senza errori/blocchi -> `SUCCESS_WITH_WARNINGS`;
- assenza di criticità -> `SUCCESS`.

Il gate non può consentire un downgrade rispetto a un esito raw più restrittivo.

## 7. Integrazione nel servizio di handoff

Il servizio di handoff deve:
1. invocare il runner;
2. eseguire il raw validator consolidato;
3. mappare la response grezza;
4. passare envelope mappato, raw validation result e raw response al response-envelope gate;
5. restituire l'envelope finale validato.

## 8. Test minimi richiesti

Devono essere verdi almeno i seguenti gruppi:
- contratti envelope finali;
- perdita blocchi critici;
- campi vietati nel payload finale;
- audit/shadow completeness guard;
- mismatch raw validation vs final response;
- end-to-end del servizio di handoff con gate post-mapper attivo.

## 9. Decisione raccomandata

La soluzione raccomandata è introdurre **un modulo autonomo** `final_ab_response_envelope_gate.py` e innestarlo nel `final_ab_runtime_handoff_service.py` senza modificare il runner.

Questa soluzione è raccomandata perché:
- mantiene il runner black-box;
- non sostituisce il raw validator già consolidato;
- rende il controllo post-mapper esplicito, testabile e regressibile;
- protegge meglio propagazione blocchi, auditabilità e separazione tra Livello A e Livello B.
