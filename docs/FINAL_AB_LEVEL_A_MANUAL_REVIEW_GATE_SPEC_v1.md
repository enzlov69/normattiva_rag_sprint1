# FINAL_AB_LEVEL_A_MANUAL_REVIEW_GATE_SPEC_v1

## 1. Posizionamento

Questa specifica estende la Fase 13.

Il manual review gate e il final human approval trace non spostano alcuna funzione decisoria nel Livello B.
Rendono auditabile il momento in cui la review umana e l'eventuale approvazione finale diventano obbligatorie nel Livello A.

## 2. Flusso

Il flusso minimo e':

response B->A -> intake gate -> classificazione -> consumo controllato -> audit trail -> decision isolation log -> manual review gate -> final human approval trace

Il Livello B resta documentale.
La review e l'approvazione finale restano umane e nel Livello A.

## 3. Regola di governo

Il Livello A resta il solo livello che puo':

- governare il caso;
- qualificare il fatto;
- interpretare;
- costruire RAC;
- governare M07;
- attivare Final Compliance Gate;
- autorizzare output opponibili;
- chiudere con approvazione umana finale.

Nessuna response B->A, anche se valida e support-only, equivale ad approvazione umana finale.

## 4. Manual review gate

Il manual review gate deve stabilire almeno:

- quando la review e' richiesta;
- quando e' necessaria escalation;
- quali condizioni bloccano l'approvazione;
- quali moduli sensibili restano protetti;
- come la review si collega al consumption audit trail e al decision isolation log.

Condizioni minime da coprire:

- unresolved critical blocks;
- quarantine history;
- contamination M07;
- authorization-like semantics;
- forbidden fields history;
- traceability gaps;
- documentary incompleteness su percorsi sensibili.

## 5. Final human approval trace

Il final human approval trace deve registrare almeno:

- review event collegato;
- modulo protetto coinvolto;
- review status;
- approval status;
- approval required;
- approvazione effettivamente umana;
- timestamp;
- base dell'approvazione;
- eventuale blocked condition;
- eventuale escalation.

Il trace registra review e approval umana, non automatismi derivati dal Livello B.

## 6. Stati minimi

Devono essere distinguibili almeno:

- `REVIEW_REQUIRED`
- `REVIEW_COMPLETED`
- `APPROVAL_GRANTED`
- `APPROVAL_DENIED`
- `ESCALATION_REQUIRED`

## 7. Regole di protezione

I moduli sensibili restano:

- `A4_M07Governor`
- `A6_RACBuilder`
- `A5_FinalComplianceGate`
- `A7_OutputAuthorizer`

Questi moduli non possono chiudere il flusso in assenza di review/approval umana dove richiesta.

## 8. Regole minime di blocco

La baseline deve considerare non conforme almeno:

- approvazione umana implicita o derivata dal Livello B;
- review richiesta ma non tracciata;
- escalation richiesta ma non tracciata;
- approval granted senza `approved_by_human`;
- moduli sensibili raggiunti come se la review fosse superata automaticamente;
- trace finale incompleto o non ricostruibile;
- leakage approvativo dal Livello B al Livello A.

## 9. Decisione implementativa

La soluzione raccomandata resta minima e conservativa:

- riuso di `src/adapters/level_a_response_guard.py`;
- generazione del manual review gate e del final human approval trace sopra i trail Fase 13;
- nessun nuovo gate parallelo;
- nessuna delega approvativa al Livello B;
- nessuna modifica a handoff o frontdoor runtime.
