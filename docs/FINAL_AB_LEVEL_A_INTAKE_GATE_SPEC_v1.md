# FINAL_AB_LEVEL_A_INTAKE_GATE_SPEC_v1

## 1. Posizionamento

Questa specifica definisce il primo gate di intake lato Livello A post-Fase 11.

Il gate non trasferisce decisione al Livello B.
Introduce un presidio forte di consumo controllato delle response runtime B->A prima che qualunque modulo sensibile del Livello A possa usarle.

## 2. Flusso

Il flusso di intake e':

runtime response B->A -> intake gate -> classification -> quarantine/degrade/accept-for-support -> moduli Livello A

Nessun modulo sensibile del Livello A puo' consumare direttamente response non classificate.

## 3. Regola di governo

Il Livello B resta documentale, tecnico, tracciabile e bloccabile.
Il Livello A resta unico livello che puo':

- governare il caso;
- qualificare il fatto;
- interpretare;
- costruire RAC;
- governare M07;
- attivare Final Compliance Gate;
- autorizzare output opponibili;
- chiudere con approvazione umana finale.

## 4. Classificazione intake

Il gate distingue almeno quattro esiti:

- `ACCEPT_SUPPORT_ONLY`
- `ACCEPT_WITH_DEGRADATION`
- `QUARANTINE`
- `REJECT`

### ACCEPT_SUPPORT_ONLY

La response e' ammissibile solo come supporto documentale.
Non puo' essere trattata come base opponibile e non puo' alimentare direttamente Final Compliance Gate o Output Authorizer.

### ACCEPT_WITH_DEGRADATION

La response e' tecnicamente utilizzabile ma degradata.
Richiede governo del Livello A e review umana/metodologica.
Non puo' scivolare nei moduli decisori.

### QUARANTINE

La response e' isolata per review manuale obbligatoria.
Questo vale almeno in caso di:

- forbidden fields;
- semantiche autorizzative o decisorie;
- contamination del boundary M07;
- gap di traceability o documentary packet incompleto;
- anomalie che rendono insicuro il consumo diretto.

### REJECT

La response e' non consumabile nel flusso metodologico.
I blocchi critici restano propagati al Livello A ma la response non puo' alimentare moduli sensibili.

## 5. Moduli sensibili protetti

I moduli sensibili protetti sono:

- M07 Governor
- RAC Builder
- Final Compliance Gate
- Output Authorizer

Regole:

- M07 non puo' essere chiuso dal supporto documentale;
- RAC non puo' essere generato in forma decisoria dal Livello B;
- Final Compliance Gate non puo' ricevere semantiche autorizzative dal Livello B;
- Output Authorizer non puo' essere alimentato direttamente da response B->A.

## 6. Condizioni minime di intake

Una response e' ammissibile al gate solo se presenta almeno:

- `support_only_flag = true` quando disponibile;
- `trace_id` e `request_id` ricostruibili;
- documentary packet presente;
- audit e SHADOW verificabili sui punti critici;
- assenza di campi decisori o validativi;
- assenza di chiusura M07.

## 7. Regole di blocco

Il gate deve considerare non conforme almeno:

- response consumata direttamente dai moduli sensibili senza intake gate;
- response con semantica autorizzativa o decisoria non quarantinata;
- M07 contamination non intercettata;
- documentary packet incompleto accettato come pienamente consumabile;
- traceability o audit mancanti non trattati;
- blocchi critici non propagati;
- response trattata come base opponibile.

## 8. Auditabilita'

L'intake gate deve lasciare traccia almeno di:

- intake decision;
- motivazione tecnica minima;
- eventuale quarantine code;
- moduli Level A consentiti o vietati;
- presenza di trace, documentary packet, blocks, audit e SHADOW.

## 9. Decisione implementativa

La soluzione raccomandata e' minima e conservativa:

- riuso di `src/adapters/level_a_response_guard.py` come punto di intake lato Livello A;
- definizione esplicita di policy, consumption rules e quarantine registry;
- nessuna scorciatoia decisoria dal Livello B;
- nessun refactor del runtime controlled handoff gia' consolidato.
