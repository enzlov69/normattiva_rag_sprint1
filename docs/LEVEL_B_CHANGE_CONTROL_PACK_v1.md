# Level B Change Control Pack v1

## 1. Scopo

Il presente pacchetto definisce il presidio offline di change control per il Livello B del progetto Normattiva RAG / Metodo Cerda – PPAV.

La funzione del pacchetto è una sola: governare in modo tracciato, difendibile e non regressivo ogni modifica proposta ai seguenti asset offline del Livello B:

- Golden Baseline Pack;
- Release Gate Offline;
- Runbook Offline;
- validator offline collegati;
- schemi JSON collegati;
- fixture e suite di test collegate.

Il pacchetto non introduce:
- logica runtime;
- logica decisoria;
- modifiche al runner federato;
- modifiche a retrieval, router, corpus o bridge applicativo.

## 2. Principio di governo

La modifica è ammissibile solo se rafforza o mantiene i vincoli fondativi del Livello B.

La modifica non è ammissibile se:
- indebolisce blocchi, audit o SHADOW;
- consente sconfinamento del Livello B verso funzioni conclusive;
- consente chiusura M07-LPR dal support layer;
- rompe i golden cases fondativi senza presidio sostitutivo;
- tocca componenti fuori perimetro del cantiere offline.

## 3. Soluzione raccomandata

La soluzione raccomandata è la seguente:

1. classificare la richiesta di modifica;
2. verificare che il perimetro resti offline Level B;
3. controllare impatto su asset protetti;
4. richiedere evidenze minime prima/dopo;
5. imporre regressione su suite critiche, golden, gate e runbook quando pertinenti;
6. sospendere o rigettare ogni modifica che riduca i vincoli fondativi.

Questa soluzione è raccomandata perché impedisce regressioni silenziose e mantiene governata la hardening line del Livello B.

## 4. Deliverable del pacchetto

- `schemas/level_b_change_request_schema_v1.json`
- `schemas/level_b_change_control_registry_v1.json`
- `schemas/level_b_change_control_report_schema_v1.json`
- `validators/level_b_change_control_rules.py`
- `tools/run_level_b_change_control_precheck.py`
- `tests/test_level_b_change_control_registry.py`
- `tests/test_level_b_change_control_rules.py`
- `tests/fixtures/level_b_change_requests/...`
- `artifacts/level_b_change_control_report_example_v1.json`

## 5. Classi di modifica ammesse

### 5.1 Housekeeping documentale non fondativo
Esempi:
- correzioni redazionali;
- chiarimenti descrittivi;
- allineamenti di naming senza impatto su regole.

Decisione attesa:
- `ALLOW` se il perimetro è corretto e le evidenze minime sono presenti.

### 5.2 Estensione additiva non fondativa
Esempi:
- nuovo test non fondativo;
- nuovo fixture additivo coerente;
- espansione documentale senza allentamento dei vincoli.

Decisione attesa:
- `ALLOW` con regressione pertinente.

### 5.3 Modifica a asset protetti senza evidenze complete
Esempi:
- modifica a golden registry;
- modifica a release gate manifest;
- modifica al runbook checklist;
- modifica a validator di controllo.

Decisione attesa:
- `HOLD` fino a completamento evidenze e approvazioni richieste.

### 5.4 Indebolimento fondativo o sconfinamento di perimetro
Esempi:
- rimozione o allentamento di golden case fondativi;
- riduzione dei blocchi obbligatori;
- rimozione di audit o SHADOW;
- introduzione di campi decisori nel Livello B;
- modifica al runner federato in questo cantiere;
- modifica a runtime, retrieval, router, corpus o bridge.

Decisione attesa:
- `REJECT`.

## 6. Asset protetti

Sono considerati asset protetti almeno:
- `schemas/level_b_golden_baseline_registry_v1.json`
- `docs/LEVEL_B_GOLDEN_BASELINE_MATRIX_v1.md`
- `tests/test_level_b_golden_baseline.py`
- `schemas/level_b_release_gate_manifest_v1.json`
- `schemas/level_b_release_gate_report_schema_v1.json`
- `tools/run_level_b_release_gate_offline.py`
- `docs/LEVEL_B_RUNBOOK_OFFLINE_v1.md`
- `schemas/level_b_runbook_checklist_v1.json`
- `tools/run_level_b_runbook_preflight.py`

Gli asset protetti possono essere modificati solo con:
- classificazione esplicita;
- motivazione documentata;
- evidenze prima/dopo;
- approvazione umana;
- regressioni richieste verdi.

## 7. Evidenze minime obbligatorie

Ogni change request deve contenere almeno:
- `change_id`
- `title`
- `scope`
- `change_class`
- `change_intent`
- `target_assets`
- `rationale`
- `risk_assessment`
- `evidence`
- `requested_by`
- `human_approval_required`

Le evidenze minime includono:
- sintesi del prima/dopo;
- elenco suite da rieseguire;
- esito atteso del precheck;
- indicazione se tocca asset protetti;
- dichiarazione esplicita che il Livello B non conclude e non chiude M07.

## 8. Regole di decisione

### 8.1 `ALLOW`
Solo se:
- il perimetro resta offline Level B;
- non ci sono touchpoint vietati;
- non c'è intento di indebolimento;
- le evidenze minime sono complete;
- le regressioni richieste risultano previste;
- l'approvazione umana richiesta è presente.

### 8.2 `HOLD`
Se:
- la modifica tocca asset protetti ma mancano evidenze;
- la modifica tocca golden/gate/runbook ma mancano approvazioni;
- la classificazione è ambigua;
- il working tree non è pulito in fase di precheck;
- le suite richieste non sono rintracciabili.

### 8.3 `REJECT`
Se:
- la modifica tocca runner, runtime, retrieval, router, corpus o bridge applicativo;
- la modifica indebolisce blocchi, audit, SHADOW o separazione dei livelli;
- la modifica abilita chiusura M07 dal Livello B;
- la modifica introduce campi decisori o conclusivi nel Livello B;
- la modifica elimina un golden fondativo senza presidio sostitutivo.

## 9. Regola di versionamento

Le modifiche approvate non sovrascrivono tacitamente il presidio esistente.
Ogni modifica fondativa deve produrre:
- nuova evidenza di regressione;
- aggiornamento tracciato del registry;
- motivazione di compatibilità con la baseline;
- eventuale nuovo tag Git dedicato.

## 10. Regola di stop

Il pacchetto deve fermare la modifica se il miglioramento tecnico indebolisce:
- blocchi;
- guardrail;
- auditabilità;
- SHADOW;
- separazione Livello A / Livello B;
- non delega;
- non chiusura di M07-LPR.

## 11. Sequenza operativa raccomandata

1. redigere la change request;
2. eseguire il precheck offline;
3. verificare l'esito `ALLOW / HOLD / REJECT`;
4. solo in caso di `ALLOW`, applicare la modifica nel repo;
5. rieseguire golden, release gate e runbook secondo pertinenza;
6. consolidare con commit e tag solo se le regressioni restano verdi.

## 12. Clausola finale

Il Change Control Pack v1 governa solo la modifica controllata del presidio offline del Livello B.
Non autorizza in alcun modo modifiche conclusive, metodologiche o runtime.
