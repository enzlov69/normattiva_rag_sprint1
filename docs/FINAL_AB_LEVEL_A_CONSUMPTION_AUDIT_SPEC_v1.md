# FINAL_AB_LEVEL_A_CONSUMPTION_AUDIT_SPEC_v1

## 1. Posizionamento

Questa specifica estende la Fase 12.

Non sposta alcuna funzione decisoria nel Livello B.
Rende auditabile il consumo lato Livello A delle response B->A gia' classificate dal gate di intake.

## 2. Flusso

Il flusso minimo e':

response B->A -> intake gate -> classificazione -> consumo controllato -> audit trail -> decision isolation log

L'audit trail registra il consumo consentito o negato.
Il decision isolation log registra che i moduli sensibili del Livello A non ricevono direttamente semantiche decisorie dal Livello B.

## 3. Regola di governo

Il Livello B continua a produrre solo output documentali, tecnici, tracciabili, bloccabili.
Il Livello A resta il solo livello che puo':

- governare il caso;
- qualificare il fatto;
- interpretare;
- costruire RAC;
- governare M07;
- attivare Final Compliance Gate;
- autorizzare output opponibili;
- chiudere con approvazione umana finale.

## 4. Audit trail del consumo

Il consumption audit trail deve registrare almeno:

- identificativo evento;
- trace e case;
- response sorgente consumata o tentata;
- intake decision applicata;
- stato e classe del segnale sorgente;
- modulo destinatario nel Livello A;
- modalita' di consumo;
- flag support_only/degraded/quarantine/reject;
- uso consentito;
- uso vietato;
- timestamp audit;
- note tecniche minime.

Le modalita' minime sono:

- `DOCUMENTARY_SUPPORT_ONLY`
- `DEGRADED_SUPPORT`
- `QUARANTINED_NOT_CONSUMED`
- `REJECTED_NOT_CONSUMED`

## 5. Decision isolation log

Il decision isolation log deve provare almeno:

- tentativo di inoltro improprio a modulo sensibile;
- consumo negato per support_only breach;
- consumo negato per contamination M07;
- consumo negato per authorization-like semantics;
- consumo negato per forbidden fields;
- consumo negato per unresolved critical blocks.

Il log registra isolamento e limiti d'uso, non una decisione finale amministrativa.

## 6. Moduli protetti

I moduli sensibili protetti restano:

- `A4_M07Governor`
- `A6_RACBuilder`
- `A5_FinalComplianceGate`
- `A7_OutputAuthorizer`

Questi moduli non possono consumare direttamente semantiche decisorie provenienti dal Livello B.

## 7. Ricostruibilita' ex post

Deve essere possibile ricostruire ex post:

- se la response e' entrata come `support_only`;
- se e' stata degradata;
- se e' stata quarantinata;
- se e' stata rifiutata;
- quale modulo del Livello A e' stato destinatario del consumo o del tentativo di consumo;
- se l'isolamento decisionale e' stato rispettato.

## 8. Regole minime di blocco

Il sistema deve considerare non conforme almeno:

- response consumata senza audit trail;
- modulo sensibile raggiunto senza decision isolation log;
- support_only response trattata come input decisorio;
- quarantine o reject risultano comunque consumati;
- traceability del consumo incompleta;
- manual review richiesta ma non tracciata;
- leakage decisorio dal Livello B verso moduli sensibili del Livello A.

## 9. Decisione implementativa

La soluzione raccomandata resta minima e conservativa:

- riuso di `src/adapters/level_a_response_guard.py`;
- generazione di audit trail e decision isolation log sopra la classificazione intake gia' esistente;
- nessun nuovo gate parallelo;
- nessuna espansione funzionale del runner;
- nessuna scorciatoia decisoria dal Livello B.
