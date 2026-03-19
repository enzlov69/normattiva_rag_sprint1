# FINAL_AB_ACCEPTANCE_DOSSIER_v1

## 1. Baseline di partenza

- tag: `stable-final-ab-manual-review-gate-v1`
- commit: `bbabc4f`
- working tree clean
- master locale e remoto allineati

## 2. Presidi consolidati

### Fase 10

- contratti finali A/B pre-runtime;
- boundary M07;
- forbidden fields;
- documentary packet minimo.

### Fase 11

- controlled runtime handoff A->B->runner->B->A;
- final block registry;
- level A runtime module registry.

### Fase 12

- intake gate lato Livello A;
- response consumption rules;
- quarantine registry;
- protezione moduli sensibili.

### Fase 13

- consumption audit trail;
- decision isolation log;
- tracciabilita' del consumo.

### Fase 14

- manual review gate;
- final human approval trace;
- review event registry.

## 3. Test minimi eseguiti

Il dossier assume come minimo i seguenti controlli:

- validator runtime anomaly governance;
- baseline verifier;
- test contrattuali A/B;
- test runtime controlled handoff;
- test intake/consumption/quarantine;
- test decision isolation;
- test manual review e final human approval non delegability.

## 4. Condizioni di rilascio

La baseline e' presentabile come:

- `NON_CERTIFIABLE` se mancano presidi critici o non-delegability;
- `CONDITIONALLY_CERTIFIABLE` se i controlli obbligatori sono verdi ma restano warning/review richieste;
- `CERTIFIABLE` se tutti i presidi minimi sono integri e la readiness tecnica e' completa.

## 5. Condizioni escluse

Il presente dossier esclude espressamente:

- delega decisoria al Livello B;
- delega approvativa al Livello B;
- chiusura M07 dal Livello B;
- autorizzazione di output opponibili da parte del Livello B;
- confusione tra certificazione tecnica e decisione amministrativa.

## 6. Stato del Livello B

Il Livello B resta:

- documentale;
- tecnico;
- tracciabile;
- bloccabile;
- subordinato al governo del Livello A.

Il Livello B non decide.
Il Livello B non approva.
Il Livello B non chiude M07.
Il Livello B non autorizza output opponibili.

## 7. Chiusura tecnica del dossier

Il dossier attesta una baseline tecnicamente accettabile solo nei limiti del perimetro A/B consolidato.

La chiusura del caso, la decisione finale e la firma restano umane e nel Livello A.
