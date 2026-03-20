# FINAL ABA RUNTIME ACTIVATION PLAN v1

## 1. Oggetto

Il presente documento definisce il piano operativo di attivazione runtime del collegamento controllato:

**Livello A → Livello B → ritorno al Livello A**

nel progetto **Normattiva RAG / Metodo Cerda – PPAV 2.2**.

Il documento ha funzione di:
- trasformare il roundtrip già validato in test in roundtrip runtime attivabile;
- mantenere il Livello B subordinato e non decisorio;
- introdurre un handoff service minimale, locale e reversibile;
- stabilire i controlli necessari prima dell’uso su casi reali.

---

## 2. Stato di partenza

Alla data di apertura del presente cantiere risultano già stabilizzati:
- la matrice ufficiale PPAV S0–S11;
- i registry di sequenza e di gate;
- i test ROOT su ordine, transizioni, blocchi, FIRMA_READY e subordinazione del Livello B;
- il roundtrip contrattuale e logico **Livello A → Livello B → Livello A**;
- i boundary test su M07-LPR;
- la non-delegabilità delle fasi riservate al Livello A.

Il presente cantiere **non** riapre i punti già chiusi.  
Il presente cantiere apre esclusivamente la **messa in funzione runtime controllata**.

---

## 3. Obiettivo operativo

L’obiettivo è portare il sistema da:

- **modello validato in test**
a
- **collegamento runtime attivabile sotto governo del Livello A**

mediante un adapter/handoff service che:
1. riceve la request del Livello A;
2. valida la request;
3. invoca il Livello B;
4. valida la response del Livello B;
5. propaga warning, errors e blocks;
6. restituisce al Livello A un envelope interno non opponibile;
7. non decide, non interpreta, non conclude, non autorizza output.

---

## 4. Vincoli non derogabili

Il presente cantiere deve rispettare integralmente i seguenti vincoli:

1. il fondativo v2 non si tocca;
2. la separazione Livello A / Livello B non si tocca;
3. il runner federato non si tocca salvo necessità eccezionale;
4. il Livello B non può:
   - decidere;
   - validare;
   - emettere GO/NO_GO;
   - produrre FIRMA_READY;
   - autorizzare output opponibili;
   - chiudere M07-LPR;
   - produrre RAC opponibile;
5. i blocchi critici del Livello B si propagano sempre al Livello A;
6. il Livello A resta l’unico titolare del governo del flusso.

---

## 5. Artefatti da introdurre

### 5.1 Documento di piano
- `docs/FINAL_ABA_RUNTIME_ACTIVATION_PLAN_v1.md`

### 5.2 Runtime minimale
- `runtime/final_aba_runtime_handoff_service.py`

### 5.3 Test ROOT iniziali
- `tests/test_final_aba_runtime_request_validation.py`
- `tests/test_final_aba_runtime_response_validation.py`
- `tests/test_final_aba_runtime_block_propagation.py`
- `tests/test_final_aba_runtime_real_roundtrip.py`

---

## 6. Funzioni minime del runtime handoff service

Il file runtime deve contenere soltanto funzioni di:
- validazione contrattuale A→B;
- validazione contrattuale B→A;
- rilevazione di forbidden fields;
- propagazione di blocchi documentali;
- costruzione di envelope interno di ritorno al Livello A;
- roundtrip controllato A→B→A.

Il runtime **non** deve:
- introdurre decisioni finali;
- sostituire i gate del Metodo Cerda;
- costruire motivazione;
- qualificare applicabilità concreta;
- autorizzare opponibilità finale.

---

## 7. Struttura minima della request runtime A→B

La request runtime deve contenere almeno:
- `request_id`
- `case_id`
- `trace_id`
- `source_level = LEVEL_A`
- `target_level = LEVEL_B`
- `request_kind = DOCUMENTARY_SUPPORT_REQUEST`
- `source_phase`
- `documentary_scope`
- `expected_documentary_outputs`
- `active_presidia`
- `audit`

La request runtime non può contenere:
- `final_decision`
- `go_no_go`
- `firma_ready`
- `output_authorized`
- `final_opposability`
- `m07_closed`
- `m07_completed`
- `rac_final_outcome`
- `cf_atti_result`

---

## 8. Struttura minima della response runtime B→A

La response runtime deve contenere almeno:
- `response_id`
- `request_id`
- `source_level = LEVEL_B`
- `target_level = LEVEL_A`
- `response_kind = DOCUMENTARY_SUPPORT_RESPONSE`
- `documentary_status`
- `documentary_packet`
- `warnings`
- `errors`
- `blocks`
- `audit`

La response runtime non può contenere:
- `final_decision`
- `go_no_go`
- `firma_ready`
- `output_authorized`
- `final_opposability`
- `m07_closed`
- `m07_completed`
- `m07_approved`
- `layer_atto_firma_ready`
- `rac_final_outcome`

---

## 9. Envelope interno di ritorno al Livello A

Il runtime deve restituire al Livello A un envelope interno contenente almeno:
- identificativi (`request_id`, `response_id`, `case_id`, `trace_id`);
- esito tecnico del roundtrip;
- presenza di warning / errors / blocks;
- flag di blocco propagato;
- payload documentale del Livello B;
- audit trail tecnico;
- shadow interno.

L’envelope interno:
- non è opponibile;
- non equivale a GO/NO_GO;
- non equivale a FIRMA_READY;
- non sostituisce i gate di Livello A.

---

## 10. Stati minimi del runtime

Gli stati minimi del runtime sono:

- `REQUEST_VALID`
- `REQUEST_INVALID`
- `RESPONSE_VALID`
- `RESPONSE_INVALID`
- `BLOCKS_PROPAGATED`
- `ROUNDTRIP_GREEN`
- `ROUNDTRIP_DEGRADED`
- `ROUNDTRIP_BLOCKED`

---

## 11. Regole di blocco runtime

1. request invalida A→B = blocco immediato;
2. response invalida B→A = blocco immediato;
3. forbidden fields nel payload B→A = blocco immediato;
4. `CRITICAL_DOCUMENTARY_BLOCK` = blocco propagato;
5. `M07_DOCUMENTARY_INCOMPLETE` = impossibilità di proseguire utilmente sul piano opponibile;
6. `COVERAGE_INSUFFICIENT` = degradazione o blocco secondo il governo del Livello A;
7. il runtime non può produrre `GO`, `NO_GO` o `FIRMA_READY`.

---

## 12. Sequenza di implementazione raccomandata

### Fase 1
Creazione del runtime minimale:
- `runtime/final_aba_runtime_handoff_service.py`

### Fase 2
Test ROOT su request validation:
- `tests/test_final_aba_runtime_request_validation.py`

### Fase 3
Test ROOT su response validation:
- `tests/test_final_aba_runtime_response_validation.py`

### Fase 4
Test ROOT su block propagation:
- `tests/test_final_aba_runtime_block_propagation.py`

### Fase 5
Test ROOT su roundtrip reale:
- `tests/test_final_aba_runtime_real_roundtrip.py`

---

## 13. Criterio di accensione del runtime

Il runtime può considerarsi attivabile solo se risultano verdi:
- request validation;
- response validation;
- block propagation;
- real roundtrip.

Solo dopo tale esito è ammesso il collaudo su casi reali.

---

## 14. Clausola finale

Il presente piano:
- non modifica il fondativo v2;
- non attribuisce al Livello B funzioni decisorie o validative;
- non sostituisce il Metodo Cerda;
- serve esclusivamente a mettere in funzione, in modo controllato, il collegamento runtime **Livello A → Livello B → Livello A**.