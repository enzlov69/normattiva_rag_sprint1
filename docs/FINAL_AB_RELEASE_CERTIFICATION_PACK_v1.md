# FINAL_AB_RELEASE_CERTIFICATION_PACK_v1

## 1. Posizionamento

Questo documento costituisce il release certification pack finale della baseline A/B.

Si colloca come chiusura tecnica del ciclo implementativo consolidato nelle Fasi 10-14.
Non introduce nuove funzioni runtime, non modifica la governance del caso e non sostituisce alcuna decisione amministrativa o istruttoria.

## 2. Natura della certificazione

La certificazione qui definita e' tecnica e di perimetro.

Non equivale a:

- decisione amministrativa;
- validazione dell'istruttoria;
- approvazione umana finale del caso;
- autorizzazione opponibile derivata dal Livello B.

Formula di governo confermata:

**Metodo Cerda governa. RAG recupera. AI assiste. L'uomo decide e firma.**

## 3. Presidi attivi riepilogati

### Fase 10

- contratti finali A/B pre-runtime;
- boundary M07;
- forbidden fields del Livello B;
- documentary packet minimo.

### Fase 11

- runtime controlled handoff A->B->runner->B->A;
- final block registry;
- level A runtime module registry.

### Fase 12

- Level A intake gate;
- response consumption rules;
- quarantine registry;
- sensitive module protection.

### Fase 13

- consumption audit trail;
- decision isolation log;
- tracciabilita' ex post del consumo.

### Fase 14

- manual review gate;
- final human approval trace;
- review event registry;
- non delegabilita' dell'approvazione umana finale.

## 4. Criteri di certificabilita'

La baseline puo' essere qualificata come:

### NON_CERTIFIABLE

Quando almeno uno dei seguenti elementi fallisce:

- contratti A/B non coerenti;
- runtime handoff non conforme;
- intake/consumption/isolation/manual review non tracciati;
- non-delegability non confermata;
- human approval requirement assente o indebolita;
- funzioni decisive trattate come delegabili al Livello B.

### CONDITIONALLY_CERTIFIABLE

Quando:

- tutti i controlli obbligatori sono verdi;
- restano warning tecnici o review manuali richieste;
- la baseline resta rilasciabile solo con presidio umano esplicito.

### CERTIFIABLE

Quando:

- tutti i controlli minimi sono verdi;
- non-delegability e human approval requirement sono confermate;
- non risultano warning o blocchi aperti incompatibili con la readiness tecnica.

## 5. Aree di controllo

Il pack distingue almeno:

### Controlli contrattuali A/B

- request/response contracts;
- forbidden fields;
- documentary packet minimum;
- M07 boundary.

### Controlli runtime

- controlled handoff;
- block propagation;
- audit e SHADOW;
- baseline verifier e validator.

### Controlli intake e consumption

- intake classification;
- support_only/degraded/quarantine/reject;
- quarantine rules;
- sensitive-module shielding.

### Controlli isolation, manual review e final human approval

- decision isolation log;
- consumption audit trail;
- manual review gate;
- final human approval trace;
- non-delegability certification.

## 6. Funzioni rigorosamente nel Livello A

Restano rigorosamente nel Livello A:

- qualificazione del fatto;
- interpretazione;
- RAC decisorio;
- chiusura M07;
- Final Compliance Gate;
- Output Authorizer;
- approvazione umana finale.

Il Livello B non decide, non approva, non chiude M07 e non autorizza output opponibili.

## 7. Condizioni minime del pack finale

Il release certification pack e' completo solo se risultano presenti e coerenti:

- release readiness statement;
- non-delegability certification;
- acceptance dossier;
- unified compliance matrix;
- documenti e schemi consolidati delle Fasi 10-14;
- suite minima di test e validator richiamati dai documenti di rilascio.

## 8. Regola finale

La certificazione finale conferma la tenuta tecnica del percorso A->B->A.

Non sposta alcuna funzione decisoria nel Livello B.
Non sostituisce Final Compliance Gate, Output Authorizer o approvazione umana finale.
