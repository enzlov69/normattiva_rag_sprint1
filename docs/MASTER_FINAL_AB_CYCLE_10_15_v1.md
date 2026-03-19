# MASTER_FINAL_AB_CYCLE_10_15_v1

## 1. Scopo generale del ciclo

Questo documento e' il riferimento unitario del ciclo A/B Fasi 10-15 del progetto Normattiva RAG / Metodo Cerda - PPAV.

Il suo scopo e':

- descrivere il percorso consolidato A->B->A;
- rendere leggibile la progressione fase per fase;
- fissare guardrail invarianti e funzioni non delegabili;
- collegare documenti, schemi, componenti runtime e test;
- identificare le baseline e i tag di congelamento del percorso.

Questo master e' un documento di governo tecnico-documentale.
Non sostituisce atti, pareri, RAC, decisioni amministrative o responsabilita' umane finali.

## 2. Relazione tra Livello A e Livello B

Il ciclo consolidato conferma che:

- il Livello B resta subordinato, documentale, tecnico, tracciabile e bloccabile;
- il Livello A resta l'unico livello che governa, interpreta, conclude, valida e chiude con approvazione umana finale;
- il runner resta black-box, sottostante e non decisorio;
- i blocchi critici del Livello B propagano al Livello A;
- il supporto documentale non equivale mai a decisione, validazione, autorizzazione opponibile o chiusura M07.

Il Livello B non decide.
Il Livello B non approva.
Il Livello B non chiude M07.
Il Livello B non autorizza output opponibili.

## 3. Logica di progressione fase per fase

### Fase 10

Obiettivo:

- chiudere il perimetro contrattuale A/B pre-runtime.

Output principali:

- request/response contracts;
- forbidden fields registry;
- documentary packet minimo;
- boundary M07.

### Fase 11

Obiettivo:

- innestare il primo runtime controlled handoff A->B->runner->B->A.

Output principali:

- handoff runtime controllato;
- final block registry;
- level A runtime module registry.

### Fase 12

Obiettivo:

- introdurre il gate di intake lato Livello A.

Output principali:

- intake policy;
- response consumption rules;
- quarantine registry;
- protezione moduli sensibili.

### Fase 13

Obiettivo:

- rendere auditabile il consumo lato Livello A e dimostrare l'isolamento decisionale.

Output principali:

- consumption audit trail;
- decision isolation log;
- event registry del consumo.

### Fase 14

Obiettivo:

- formalizzare manual review gate e final human approval trace.

Output principali:

- manual review gate policy;
- final human approval trace;
- manual review event registry.

### Fase 15

Obiettivo:

- chiudere tecnicamente il ciclo con certification pack, acceptance dossier, unified compliance matrix, readiness e non-delegability.

Output principali:

- release certification pack;
- acceptance dossier;
- unified compliance matrix;
- release readiness statement;
- non-delegability certification.

## 4. Guardrail invarianti

I guardrail invarianti dell'intero ciclo sono:

- separazione netta tra Livello A e Livello B;
- boundary M07 intatto;
- support_only_flag come ancoraggio semantico del supporto documentale;
- nessun campo decisorio o validativo nel Livello B;
- propagazione dei blocchi critici al Livello A;
- audit e SHADOW obbligatori;
- manual review e approvazione umana finale non delegabili;
- assenza di qualunque leakage decisorio o approvativo dal Livello B.

## 5. Documenti principali per fase

- Fase 10: `docs/FINAL_AB_PRE_RUNTIME_CONTROLLED_HANDOFF_SPEC_v1.md`
- Fase 11: `docs/FINAL_AB_RUNTIME_CONTROLLED_HANDOFF_SPEC_v1.md`
- Fase 12: `docs/FINAL_AB_LEVEL_A_INTAKE_GATE_SPEC_v1.md`
- Fase 13: `docs/FINAL_AB_LEVEL_A_CONSUMPTION_AUDIT_SPEC_v1.md`
- Fase 14: `docs/FINAL_AB_LEVEL_A_MANUAL_REVIEW_GATE_SPEC_v1.md`
- Fase 15: `docs/FINAL_AB_RELEASE_CERTIFICATION_PACK_v1.md`

Rinvii operativi finali:

- indice rapido delle fasi: `docs/FINAL_AB_PHASES_10_15_INDEX_v1.md`
- registry tag di baseline: `docs/FINAL_AB_BASELINE_TAG_REGISTRY_v1.md`
- trace matrix: `docs/FINAL_AB_DOCUMENT_TO_RUNTIME_TRACE_MATRIX_v1.md`

## 6. Baseline tag finali

Le baseline finali del percorso sono raccolte nel registry dedicato e coprono almeno:

- `stable-final-ab-controlled-handoff-v1`
- `stable-final-ab-runtime-controlled-handoff-v2`
- `stable-final-ab-level-a-intake-gate-v1`
- `stable-final-ab-consumption-audit-v1`
- `stable-final-ab-manual-review-gate-v1`
- `stable-final-ab-release-certification-v1`

## 7. Funzioni non delegabili

Restano rigorosamente nel Livello A:

- qualificazione del fatto;
- interpretazione;
- RAC decisorio;
- chiusura M07;
- Final Compliance Gate;
- Output Authorizer;
- approvazione umana finale.

Il perimetro di non delegabilita' e' confermato dal certification pack finale.

## 8. Stato consolidato del percorso

Il ciclo Fasi 10-15 risulta tecnicamente consolidato come percorso A/B:

- contrattualmente definito;
- runtime controllato;
- protetto lato intake e consumption;
- auditabile e tracciabile;
- schermato sui moduli sensibili;
- sottoposto a manual review e final human approval non delegabili;
- tecnicamente certificato a livello di baseline.

Questa certificazione tecnica non sostituisce la responsabilita' umana finale nel procedimento amministrativo.
