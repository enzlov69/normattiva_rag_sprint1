# FINAL_AB_RUNTIME_REAL_HANDOFF_SPEC_v1

## 1. Scopo

Questo documento definisce la Fase 3 del cantiere di runtime controlled handoff tra il frontdoor già validato del collegamento finale A→B→A e un invocatore reale del runner federato.

La finalità è sostituire il dummy bridge con un invocatore reale e controllato, senza modificare la logica interna del runner federato e senza alterare il perimetro documentale del Livello B.

## 2. Vincoli non derogabili

Restano integralmente vincolanti i seguenti presìdi:

- nessuna modifica distruttiva del runner federato;
- nessun intervento su retrieval, router, ranking o corpus;
- nessuna alterazione del fondativo v2;
- nessun cambiamento al system prompt;
- separazione tecnica, contrattuale e verificabile tra Livello A e Livello B;
- propagazione dei blocchi critici dal Livello B al Livello A;
- boundary M07 intatto;
- nessun payload decisorio, conclusivo o validativo nel Livello B.

## 3. Decisione architetturale raccomandata

La soluzione corretta consiste nell’inserire un layer di handoff runtime che operi come adapter controllato tra:

1. il frontdoor contrattuale del collegamento finale A/B;
2. un port di invocazione del runner reale;
3. un mapper di normalizzazione della risposta raw;
4. la response contrattuale del Livello B verso il Livello A.

Il runner federato resta black-box sottostante.

Il primo punto di accoppiamento continua a essere il frontdoor/adapter controllato e non il runner.

## 4. Componenti introdotte

### 4.1 `runtime/final_ab_runner_invocation_port.py`

Definisce il contratto minimo di invocazione del runner.

Responsabilità:
- esporre una interfaccia astratta di invocazione;
- mantenere il runner isolato dal frontdoor;
- vietare scorciatoie di integrazione informale.

### 4.2 `runtime/final_ab_runner_real_invoker.py`

Implementa il port di invocazione reale.

Responsabilità:
- risolvere un callable reale del runner;
- invocarlo come black-box;
- restituire il risultato raw senza interpretarlo.

Limiti:
- non modifica il runner;
- non riordina risultati;
- non cambia ranking;
- non aggiunge giudizi applicativi.

### 4.3 `runtime/final_ab_runner_response_mapper.py`

Normalizza la risposta raw del runner in un `DocumentaryPacket` conforme.

Responsabilità:
- estrarre il payload documentale;
- intercettare campi vietati o semantiche conclusive;
- garantire la presenza minima del pacchetto documentale;
- aprire o propagare blocchi, warning ed errori;
- costruire una traccia `shadow_fragment` coerente con il lineage finale.

### 4.4 `runtime/final_ab_runtime_handoff_service.py`

Coordina il flusso runtime end-to-end.

Responsabilità:
- validare la request contrattuale A/B;
- mappare la request nel formato minimo del runner;
- invocare il port reale;
- normalizzare la risposta;
- costruire la `ABResponseEnvelope`;
- restituire solo output tecnici e documentali.

## 5. Flusso canonico della Fase 3

1. Il frontdoor riceve una `ABRequestEnvelope`.
2. L’handoff service valida i campi minimi contrattuali.
3. La request viene tradotta nel mapping minimo per il runner.
4. Il port invoca il runner reale come black-box.
5. Il servizio riceve il payload raw del runner.
6. Il response mapper estrae il pacchetto documentale.
7. Il mapper rileva eventuali campi vietati del Livello B.
8. Il mapper integra warning/errors/blocks mancanti e costruisce il `shadow_fragment`.
9. Il servizio restituisce una `ABResponseEnvelope` verso il Livello A.
10. Il Livello A governa M07, RAC, compliance finale e output opponibile.

## 6. Request contrattuale minima

La request in ingresso deve contenere almeno:

- `request_id`
- `case_id`
- `trace_id`
- `api_version`
- `caller_module`
- `target_module`
- `timestamp`
- `payload`

Se uno di questi campi manca, la request è non conforme e deve essere rigettata o degradata.

## 7. Response contrattuale minima

La response deve contenere almeno:

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

Stati ammessi:

- `SUCCESS`
- `SUCCESS_WITH_WARNINGS`
- `DEGRADED`
- `BLOCKED`
- `REJECTED`
- `ERROR`

## 8. DocumentaryPacket minimo

Il `DocumentaryPacket` minimo restituito dal Livello B deve contenere almeno:

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

Regola:
se il runner restituisce una struttura incompleta, il wrapper non può inventare contenuti sostanziali mancanti. Può solo:

- degradare la response;
- aprire blocchi;
- evidenziare la carenza;
- completare esclusivamente campi tecnici vuoti con placeholder neutrali.

## 9. Campi vietati del Livello B

Il mapper deve intercettare e rigettare almeno i seguenti campi, o equivalenti semantici:

- `final_decision`
- `applicability_final`
- `m07_closed`
- `m07_certified`
- `reading_integral_certified`
- `compliance_go`
- `go_no_go`
- `output_authorized`
- `final_validation`
- `opponible_output`
- `rac_opponibile`

Esito atteso:

- status `REJECTED`
- blocco `RAG_SCOPE_VIOLATION`

## 10. Boundary M07

Il supporto del Livello B a M07 resta esclusivamente documentale.

Sono ammessi soltanto output come:
- evidenze documentali;
- pacchetti di supporto;
- `human_completion_required = true`.

Sono vietati output equivalenti a:
- chiusura di M07;
- certificazione finale di lettura integrale;
- completamento sostitutivo del presidio umano/metodologico.

## 11. Propagazione dei blocchi

Il servizio deve propagare integralmente al Livello A almeno i seguenti blocchi critici, se presenti o rilevati:

- `CORPUS_MISSING`
- `SOURCE_UNVERIFIED`
- `CITATION_INCOMPLETE`
- `VIGENZA_UNCERTAIN`
- `CROSSREF_UNRESOLVED`
- `M07_REQUIRED`
- `RAG_SCOPE_VIOLATION`
- `AUDIT_INCOMPLETE`
- `OUTPUT_NOT_OPPONIBLE`
- `COVERAGE_INADEQUATE`

Il Livello A non può ignorare un blocco critico proveniente dal Livello B.

## 12. Mapping controllato della request

La request contrattuale viene convertita in un `RunnerInvocationRequest` minimo.

Campi raccomandati lato runner:

- `request_id`
- `case_id`
- `trace_id`
- `query_text`
- `domain_target`
- `metadata_filters`
- `top_k`
- `runtime_flags`

Il mapping resta minimale per non contaminare il runner con logiche metodologiche.

## 13. Mapping controllato della response

La risposta raw del runner può assumere forme diverse, ma il wrapper deve accettare solo strutture normalizzabili in chiave documentale.

Sorgenti accettabili per l’estrazione del payload documentale:

- `documentary_packet`
- `payload`
- `result`
- `results`
- root object già conforme

Qualunque semantica conclusiva o validativa produce rigetto.

## 14. Audit e SHADOW

Il wrapper deve garantire un `shadow_fragment` minimo con:

- `source_layer`
- `schema_version`
- `record_version`
- `case_id`
- `trace_id`
- `created_at`
- `updated_at`
- `runner_entrypoint`
- `mapping_version`
- `normalization_notes`

Audit trail e SHADOW restano obbligatori e non sostituiscono i controlli del Metodo Cerda.

## 15. Errori da prevenire

Il cantiere è da considerarsi non conforme se si verifica anche uno solo dei seguenti casi:

1. il runner diventa il primo punto di accoppiamento;
2. il wrapper introduce logica interpretativa o decisoria;
3. il payload del Livello B contiene campi conclusivi;
4. M07 risulta chiuso dal support layer;
5. i blocchi critici non vengono propagati;
6. il DocumentaryPacket minimo non è costruibile;
7. il wrapper “completa” in modo arbitrario elementi documentali assenti;
8. il working tree richiede modifiche al runner per funzionare.

## 16. Test di accettazione

Il pacchetto minimo di test deve coprire:

- contratti request/response;
- campi vietati del Livello B;
- propagazione blocchi;
- boundary M07;
- flusso end-to-end A→B→runner→B→A.

## 17. Ordine di esecuzione raccomandato

1. salvare i file runtime e schema;
2. salvare il pacchetto test;
3. eseguire i test del nuovo cantiere;
4. rieseguire i test del frontdoor runtime già consolidato;
5. verificare working tree pulito;
6. eseguire commit e tag solo dopo test verdi.

## 18. Clausola finale di conformità

La Fase 3 è conforme solo se:

- il Livello A continua a governare integralmente il caso;
- il Livello B continua a rispondere soltanto come sottosistema documentale;
- il runner federato resta black-box;
- il wrapper reale non altera retrieval, router, ranking o corpus;
- la separazione tecnica A/B resta verificabile nei dati, nei contratti e nei test.
