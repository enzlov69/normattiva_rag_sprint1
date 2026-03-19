# CANTIERE FIP-IND GATE v1

## 1. Scopo

Questo pacchetto introduce il modulo **FIP-IND (Filtro Indirizzo vs Provvedimento)** come **gate del Livello A**
con supporto documentale subordinato del Livello B.

Il modulo serve a impedire la confusione tra:
- atto di indirizzo politico-amministrativo;
- provvedimento gestionale con effetti amministrativi concreti.

## 2. Collocazione nel flusso

Il gate FIP-IND è da usare:
- dopo FASE 0-bis;
- dopo FASE 0-ter;
- prima di RAP-ATTI;
- ogni volta che l'atto è presentato come indirizzo oppure contiene linguaggio/dispositivo gestionale.

## 3. Funzione

Il modulo:
- previene il falso indirizzo;
- protegge la separazione tra indirizzo e gestione;
- obbliga il Livello A a una qualificazione governata;
- consente al Livello B solo supporto documentale alle singole domande del test.

## 4. Test delle 10 domande

Il gate si basa su 10 domande con risposta:
- `YES`
- `NO`
- `UNKNOWN`

Soglie:
- `0 YES` e `0 UNKNOWN` → `INDIRIZZO_PURO`
- `1-2 YES` oppure presenza di `UNKNOWN` → `RISCHIO_FIP_IND`
- `3-4 YES` → `PROVVEDIMENTO_SOSTANZIALE`
- `>= 5 YES` → `FALSO_INDIRIZZO_BLOCKED`

## 5. Separazione A/B

### Livello A
Resta titolare di:
- attivazione del gate;
- compilazione del questionario;
- conteggio delle risposte;
- applicazione delle soglie;
- esito finale del gate;
- eventuale riqualificazione dell'atto.

### Livello B
Può solo restituire:
- fonti;
- citazioni;
- vigenza;
- rinvii;
- coverage;
- supporto documentale alle domande del test;
- warning/errori/blocchi.

Il Livello B non può:
- classificare definitivamente l'atto;
- emettere l'esito finale del gate;
- sostituire il giudizio metodologico del Livello A.

## 6. File del pacchetto

- `schemas/fip_ind_questionnaire_schema_v1.json`
- `schemas/fip_ind_gate_result_schema_v1.json`
- `schemas/fip_ind_documentary_support_request_schema_v1.json`
- `schemas/fip_ind_documentary_support_response_schema_v1.json`
- `schemas/fip_ind_evidence_pack_schema_v1.json`
- `runtime/fip_ind_gate.py`
- `tests/test_fip_ind_gate_contracts.py`
- `tests/test_fip_ind_gate_thresholds.py`
- `tests/test_fip_ind_boundary_no_decision_in_level_b.py`
- `tests/test_fip_ind_gate_end_to_end.py`

## 7. Blocchi del modulo

Blocchi specifici:
- `FIP_IND_REQUIRED`
- `FIP_IND_THRESHOLD_BLOCK`
- `FIP_IND_EVIDENCE_MISSING`
- `FIP_IND_SCOPE_VIOLATION`

Blocchi ereditati:
- `CITATION_INCOMPLETE`
- `VIGENZA_UNCERTAIN`
- `CROSSREF_UNRESOLVED`
- `AUDIT_INCOMPLETE`
- `OUTPUT_NOT_OPPONIBLE`
- `COVERAGE_INADEQUATE`

## 8. Criterio di accettazione

Il pacchetto è accettabile solo se:
- il questionario è valido;
- il risultato del gate è calcolato solo nel Livello A;
- il supporto documentale del Livello B resta non decisorio;
- il boundary respinge semantiche conclusive nel Livello B;
- i test sulle soglie risultano coerenti con il modulo.
