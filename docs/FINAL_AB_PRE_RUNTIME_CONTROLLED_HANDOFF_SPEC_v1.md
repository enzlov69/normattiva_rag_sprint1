# FINAL_AB_PRE_RUNTIME_CONTROLLED_HANDOFF_SPEC_v1

## 1. Posizionamento

Questa specifica formalizza il **collegamento finale A/B pre-runtime controllato** della Fase 10.

Il collegamento corretto non consiste nell'attaccare il RAG al Metodo Cerda come motore unico.
Consiste invece in una frontiera controllata e testabile tra:

- Livello A / Metodo Cerda - PPAV
- Livello B / RAG Normativo Governato e Federato

## 2. Regola di governo

Il Livello A governa.
Il Livello B documenta.

Formula vincolante:

**Metodo Cerda governa. RAG recupera. AI assiste. L'uomo decide e firma.**

Conseguenze:

- il Livello A mantiene orchestrazione AI-assistita;
- il Livello A mantiene governo del caso;
- il Livello A mantiene M07-LPR;
- il Livello A mantiene Final Compliance Gate;
- il Livello A mantiene approvazione umana finale, decisione e firma;
- il Livello B restituisce solo contenuti documentali e tecnici ammessi.

## 3. Flusso canonico

utente/caso -> Livello A / Metodo Cerda -> orchestrazione AI-assistita -> Livello B / RAG Normativo Governato e Federato -> pacchetto documentale -> Livello A / Metodo Cerda -> valutazione umana finale -> decisione e firma

Nessun output opponibile puo' chiudersi positivamente senza approvazione umana finale.

## 4. Input A->B

La request A->B e' documentale e contrattuale.
Contiene solo:

- identificativi di tracciabilita';
- contesto di richiesta;
- modulo chiamante;
- obiettivo documentale;
- perimetro normativo;
- output documentali richiesti;
- vincoli di coverage e propagazione;
- contesto M07 non conclusivo;
- contesto audit.

Non puo' contenere richieste di:

- decisione finale;
- motivazione finale;
- scelta della norma prevalente;
- chiusura M07;
- validazione finale;
- autorizzazione di output opponibile.

## 5. Output B->A

La response B->A e' solo tecnico-documentale.
Contiene:

- documentary packet minimo;
- warnings;
- errors;
- blocks;
- audit trace;
- shadow trace;
- stato tecnico di risposta.

Non puo' contenere:

- decision;
- final_decision;
- approval;
- human_approval;
- normative_prevalence_choice;
- legal_applicability_decision;
- final_motivation;
- m07_closed;
- output_authorized;
- final_compliance_passed;
- provvedimento_generato;
- rac_finale_decisorio;
- esito_istruttoria_conclusivo.

## 6. Pacchetto documentale minimo

Il pacchetto documentale minimo restituito dal Livello B al Livello A comprende:

- `source_set`
- `citation_set`
- `vigenza_findings`
- `cross_reference_findings`
- `coverage_findings`
- `documentary_warnings`
- `documentary_errors`
- `documentary_blocks`
- `completeness_flags`
- `audit_trace`
- `shadow_trace`

Questo schema finale deriva dal preliminare `schemas/level_b_documentary_packet_schema_v1.json` e ne consolida il naming finale Fase 10 senza cambiare la natura documentale del Livello B.

## 7. Boundary M07

Il supporto documentale a M07 non equivale a chiusura di M07.

Il Livello B puo':

- ordinare la lettura;
- segnalare allegati;
- segnalare rinvii;
- evidenziare omissioni;
- mantenere `human_completion_required = true`.

Il Livello B non puo':

- chiudere M07;
- certificare lettura integrale;
- sostituire il presidio metodologico;
- sostituire il presidio umano.

Il registry `schemas/final_ab_m07_boundary_registry_v1.json` resta il riferimento operativo per i campi vietati e la reazione di blocco.

## 8. Blocco e propagazione

I blocchi critici che incidono su opponibilita', vigenza, rinvii, M07, audit o sconfinamento del RAG prevalgono sul collegamento finale A/B.

Relazione tra registry:

- `SystemBlockRegistry`: livello di governo superiore del sistema e del Livello A; in caso di conflitto prevale sempre la regola piu' restrittiva.
- `FinalABBlockRegistry`: registry del collegamento finale A/B che disciplina la propagazione dei blocchi tecnico-documentali dal Livello B al Livello A.

Il file operativo riusato in Fase 10 e':

- `schemas/final_ab_block_propagation_registry_v1.json`

Regole:

- i blocchi critici si propagano al Livello A senza downgrade;
- `RAG_SCOPE_VIOLATION` prevale sul rientro documentale;
- `M07_REQUIRED`, `AUDIT_INCOMPLETE`, `OUTPUT_NOT_OPPONIBLE` e gli altri blocchi critici gia' consolidati restano obbligatoriamente visibili al Livello A.

## 9. Errori da prevenire

Sono non conformi almeno questi casi:

- campi decisori o validativi nel payload del Livello B;
- chiusura impropria di M07;
- assenza del pacchetto documentale minimo;
- assenza di audit_trace o shadow_trace;
- response non risolvibile verso il Livello A;
- blocchi critici non propagati;
- confusione tra supporto documentale e decisione finale.

## 10. Test di accettazione

La Fase 10 e' accettabile solo se sono verificati almeno:

- contract request A->B;
- contract response B->A;
- registry campi vietati del Livello B;
- pacchetto documentale minimo;
- boundary M07;
- flusso end-to-end prehandoff solo documentale;
- nessuna decisione o approvazione dal Livello B.

## 11. Decisione implementativa

La soluzione consolidata di Fase 10 e' minima, conservativa e contrattuale:

- riuso degli artefatti preliminari gia' presenti;
- rafforzamento in place degli schemi `final_ab_request_schema_v1.json` e `final_ab_response_schema_v1.json`;
- riuso dei registry `final_ab_block_propagation_registry_v1.json` e `final_ab_m07_boundary_registry_v1.json`;
- riuso delle basi `level_b_forbidden_fields_registry_v1.json` e `level_b_documentary_packet_schema_v1.json`;
- nessuna duplicazione dei componenti runtime gia' sufficienti al presidio contrattuale minimo.
