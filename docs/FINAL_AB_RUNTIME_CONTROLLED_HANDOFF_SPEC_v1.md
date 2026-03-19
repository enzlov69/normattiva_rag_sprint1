# FINAL_AB_RUNTIME_CONTROLLED_HANDOFF_SPEC_v1

## 1. Posizionamento

Questa specifica definisce il primo cantiere runtime post-Fase 10 per il collegamento controllato A->B->runner->B->A.

Non sostituisce la Fase 10.
Usa la Fase 10 come prerequisito congelato per il primo innesto runtime effettivo e controllato.

## 2. Principio di governo

Il runtime non sostituisce la governance del Livello A.

Regole vincolanti:

- Livello A governa.
- Livello B documenta.
- Il runner resta black-box, sottostante e non decisorio.

## 3. Flusso runtime

Il flusso controllato e':

Livello A -> controlled handoff runtime -> Livello B documentale -> runner federato black-box -> Livello B documentale -> response envelope gate -> Livello A

Il primo punto logico di accoppiamento non e' il runner.
Il primo punto logico di accoppiamento resta lo strato controllato di handoff.

## 4. Componenti per livello

### Livello A

- Orchestratore PPAV / Metodo Cerda
- M07 Governor
- RAC Builder
- Final Compliance Gate
- Output Authorizer
- Audit Logger
- SHADOW Tracer

### Livello B

- runtime handoff service
- raw validator
- response mapper
- response envelope gate
- runner black-box

## 5. Registry coinvolti

### FinalABBlockRegistry

Il registry finale dei blocchi runtime e' `schemas/final_block_registry_v1.json`.

Funzione:

- vista contrattuale runtime del perimetro blocchi finale A/B;
- nessun downgrade dei blocchi critici gia' consolidati;
- propagazione obbligatoria dei blocchi rilevanti al Livello A.

### Registry consolidati Fasi 8-9

Restano vincolanti:

- `schemas/final_ab_runtime_anomaly_registry_v1.json`
- `schemas/final_ab_runtime_severity_canon_v1.json`
- `schemas/final_ab_runtime_propagation_matrix_v1.json`

Il `FinalABBlockRegistry` non li sostituisce.
Ne fornisce una vista operativa runtime coerente col controlled handoff.

## 6. Audit trail e SHADOW

Audit e SHADOW restano obbligatori.

Nel runtime controllato devono restare verificabili almeno:

- `trace_id`
- `request_id`
- passaggi critici del handoff
- warning, errori e blocchi
- boundary M07
- eventuale perdita di blocchi critici
- presenza del documentary packet minimo

## 7. Regole di blocco runtime

Il runtime handoff e' non conforme almeno se:

- il runner viene usato come primo punto logico di accoppiamento;
- compaiono campi decisori o autorizzativi nel payload del Livello B;
- il Livello B chiude M07 in modo implicito o esplicito;
- un blocco critico non viene propagato al Livello A;
- audit o SHADOW mancano su punti critici;
- il documentary packet e' mancante o incoerente;
- l'output del Livello B viene trattato come opponibile;
- Final Compliance Gate o Output Authorizer slittano nel Livello B.

## 8. Natura del runtime handoff

Il runtime handoff resta:

- tecnico;
- contrattuale;
- documentale;
- bloccabile;
- non autorizzativo.

Non puo':

- scegliere norme prevalenti;
- valutare applicabilita' concreta;
- chiudere M07;
- autorizzare output opponibili;
- creare scorciatoie verso GO/NO-GO.

## 9. Decisione implementativa

La soluzione runtime raccomandata e' minimale e conservativa:

- riuso di `runtime/final_ab_runtime_handoff_service.py` come candidato principale;
- stabilita' di `runtime/final_ab_runner_frontdoor.py` salvo necessita' meccanica provata;
- consolidamento in place dei registry e dei documenti endpoint gia' esistenti;
- collaudo end-to-end del flusso A->B->runner->B->A senza refactor distruttivo.
