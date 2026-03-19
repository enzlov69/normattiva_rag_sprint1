# CANTIERE M07 DOCUMENTARY SUPPORT ADAPTER RUNTIME v1

## 1. Scopo

Questo pacchetto introduce un adapter runtime minimale del Livello A per il cantiere
"M07 Documentary Support Adapter", sopra la baseline congelata:

- tag: `stable-final-ab-master-cycle-v1`
- commit baseline: `e0ea436`
- fondazione cantiere: `stable-m07-documentary-support-foundation-v1`
- commit fondazione cantiere: `f6285b4`

L'adapter:
- costruisce request conformi agli schemi del cantiere;
- valida preventivamente le request;
- consuma response del Livello B conformi agli schemi;
- propaga warnings, errors e blocks;
- vieta semantiche conclusive o decisorie nel Livello B.

## 2. Perimetro

### Incluso
- build request A→B
- validazione request
- validazione response
- consumo response documentale
- propagazione blocchi
- guardrail anti-sconfinamento

### Escluso
- nessuna modifica del runner federato
- nessuna modifica di retrieval/router/ranking/corpus
- nessuna chiusura M07
- nessuna costruzione RAC
- nessun GO/NO_GO
- nessuna autorizzazione finale output

## 3. File del pacchetto

- `runtime/m07_documentary_support_adapter.py`
- `tests/test_m07_documentary_support_adapter_contracts.py`
- `tests/test_m07_documentary_support_adapter_block_propagation.py`
- `tests/test_m07_documentary_support_adapter_no_decision.py`

## 4. Regole di blocco

L'adapter deve bloccare o rigettare:
- `final_decision`
- `final_applicability`
- `legal_conclusion`
- `motivazione_finale`
- `output_authorized`
- `m07_closed`
- `ppav_closed`
- `go_finale`

L'adapter deve inoltre rigettare ogni response in cui:
- `support_only_flag != true`
- `M07EvidencePack.human_completion_required != true`
- `M07EvidencePack.source_layer != "B"`

## 5. Output dell'adapter

L'adapter restituisce solo un envelope tecnico di consumo Livello A, con:
- `adapter_status`
- `response_status`
- `documentary_packet`
- `warnings`
- `errors`
- `blocks`
- `requires_human_m07_completion`
- `decision_fields_detected = false`
- `can_close_m07 = false`
- `can_authorize_output = false`

## 6. Test minimi

- costruzione request valida
- consumo response valida
- propagazione `BLOCKED`
- propagazione `DEGRADED`
- esecuzione transport controllato
- rigetto campi decisori top-level
- rigetto campi decisori nested
- rigetto di packet non support-only

## 7. Criterio di accettazione

Il pacchetto è accettabile solo se:
- tutti i test sono verdi;
- il Livello B resta confinato a supporto documentale;
- l'adapter non prende decisioni;
- il core A/B baseline non viene toccato.