# CANTIERE M07 DOCUMENTARY SUPPORT ORCHESTRATOR v1

## 1. Scopo

Questo pacchetto introduce la facade locale di orchestrazione del Livello A
per il cantiere "M07 Documentary Support Adapter", sopra i checkpoint già fissati:

- baseline A/B: `stable-final-ab-master-cycle-v1`
- foundation cantiere: `stable-m07-documentary-support-foundation-v1`
- runtime adapter: `stable-m07-documentary-support-runtime-adapter-v1`

La facade unifica:
- registry del modulo;
- build request;
- dispatch controllato;
- transport A→B→A;
- consumption response;
- propagazione di warning, errors e blocks.

## 2. Obiettivo operativo

Consentire al Livello A di eseguire un flusso locale completo di orchestrazione documentale,
senza:
- toccare il runner federato;
- spostare funzioni decisorie nel Livello B;
- chiudere M07;
- costruire RAC;
- autorizzare output opponibili.

## 3. Perimetro

### Incluso
- orchestrazione locale controllata del modulo
- validazione caller tramite registry
- costruzione request conforme
- invocazione transport controllato
- consumo response
- blocco se manca `M07EvidencePack`
- envelope finale di orchestrazione non decisorio

### Escluso
- nessuna integrazione nel runner federato
- nessuna decisione finale
- nessun GO/NO-GO
- nessuna chiusura M07
- nessuna autorizzazione output
- nessuna costruzione RAC
- nessun Final Compliance Gate

## 4. Regole di governo

La facade:
- opera solo nel Livello A
- usa il registry locale controllato
- può essere invocata solo da caller autorizzati
- richiede `M07EvidencePack` quando richiesto in output
- propaga i blocchi del Livello B
- non può ignorare blocchi critici
- non abilita alcun esito opponibile

## 5. Output ammesso

L'output della facade è un envelope tecnico di orchestrazione con:
- `session_id`
- `request_id`
- `case_id`
- `trace_id`
- `orchestrator_module`
- `caller_module`
- `resolved_module_id`
- `dispatch_mode`
- `target_module`
- `request_payload`
- `response_consumption`
- `orchestration_status`
- `warnings`
- `errors`
- `blocks`
- `requires_human_m07_completion`
- flag negativi di non decisione

## 6. Flag obbligatori

Devono restare sempre:
- `can_close_m07 = false`
- `can_build_rac = false`
- `can_finalize_compliance = false`
- `can_authorize_output = false`
- `can_emit_go_no_go = false`
- `manual_level_a_only = true`
- `runner_federated_touched = false`

## 7. Test minimi

- successo contrattuale dell’orchestrazione
- propagazione di `BLOCKED`
- blocco se manca `M07EvidencePack`
- rigetto di caller non autorizzato
- permanenza dei flag di non decisione

## 8. Criterio di accettazione

Il pacchetto è accettabile solo se:
- la facade chiude il mini-ciclo locale del modulo;
- il Livello B resta puro supporto documentale;
- i blocchi si propagano correttamente;
- il runner federato resta intatto;
- non emerge alcuna semantica conclusiva o autorizzativa.