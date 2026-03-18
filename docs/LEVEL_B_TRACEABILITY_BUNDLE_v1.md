# Level B Traceability Bundle v1

## 1. Scopo

Il presente bundle definisce il fascicolo unitario di tracciabilità del Livello B offline del progetto Normattiva RAG / Metodo Cerda – PPAV.

La funzione del bundle è una sola: collegare in una vista coerente, verificabile e rieseguibile i seguenti presìdi già consolidati del Livello B offline:

- Validation Kit;
- Golden Baseline Pack;
- Release Gate Offline;
- Runbook Offline;
- Change Control Pack;
- checkpoint Git e tag di consolidamento;
- ordine di esecuzione e dipendenze minime.

Il bundle non introduce:
- logica runtime;
- modifiche al runner federato;
- modifiche a retrieval, router, corpus o bridge applicativo;
- logica decisoria o conclusiva nel Livello B;
- chiusura di M07-LPR.

## 2. Soluzione raccomandata

La soluzione raccomandata è trattare la tracciabilità del Livello B come un fascicolo tecnico autonomo composto da:

1. registry unitario dei componenti e dei checkpoint;
2. report strutturato di controllo della coerenza;
3. runner offline di ricostruzione della bundle view;
4. test dedicati sul registry, sulle regole e sul runner.

Questa soluzione è raccomandata perché evita che validation, golden, gate, runbook e change control restino isole separate e rende verificabile l'intera linea di hardening offline del Livello B.

## 3. Deliverable del bundle

- `docs/LEVEL_B_TRACEABILITY_BUNDLE_v1.md`
- `schemas/level_b_traceability_bundle_registry_v1.json`
- `schemas/level_b_traceability_bundle_report_schema_v1.json`
- `validators/level_b_traceability_bundle_rules.py`
- `tools/run_level_b_traceability_bundle.py`
- `tests/test_level_b_traceability_bundle_registry.py`
- `tests/test_level_b_traceability_bundle_rules.py`
- `tests/test_level_b_traceability_bundle_runner.py`
- `artifacts/level_b_traceability_bundle_report_example_v1.json`

## 4. Oggetto della tracciabilità

Il bundle deve ricostruire almeno:

- i componenti offline Level B attivi;
- i file-ancora minimi per ciascun componente;
- i test o runner associati;
- i checkpoint Git/tag richiesti;
- l'ordine di esecuzione raccomandato;
- le dipendenze minime tra i componenti;
- i motivi di `COMPLETE`, `HOLD` o `ERROR`.

## 5. Componenti tracciati

### 5.1 Validation Kit
Anchor minimi:
- `docs/LEVEL_B_VALIDATION_TRACEABILITY_MATRIX_v1.md`
- `schemas/level_b_validation_traceability_matrix_v1.json`
- `tests/test_level_b_payload_contract.py`
- `tests/test_level_b_traceability_matrix.py`

Checkpoint minimo richiesto:
- `stable-level-b-validation-v2`

### 5.2 Golden Baseline Pack
Anchor minimi:
- `docs/LEVEL_B_GOLDEN_BASELINE_MATRIX_v1.md`
- `schemas/level_b_golden_baseline_registry_v1.json`
- `tests/test_level_b_golden_baseline.py`

Checkpoint minimo richiesto:
- `stable-level-b-golden-release-v1`

### 5.3 Release Gate Offline
Anchor minimi:
- `docs/LEVEL_B_RELEASE_GATE_OFFLINE_v1.md`
- `schemas/level_b_release_gate_manifest_v1.json`
- `tools/run_level_b_release_gate_offline.py`

Checkpoint minimo richiesto:
- `stable-level-b-golden-release-v1`

### 5.4 Runbook Offline
Anchor minimi:
- `docs/LEVEL_B_RUNBOOK_OFFLINE_v1.md`
- `schemas/level_b_runbook_checklist_v1.json`
- `tools/run_level_b_runbook_preflight.py`

Checkpoint minimo richiesto:
- `stable-level-b-runbook-v1`

### 5.5 Change Control Pack
Anchor minimi:
- `docs/LEVEL_B_CHANGE_CONTROL_PACK_v1.md`
- `schemas/level_b_change_control_registry_v1.json`
- `tools/run_level_b_change_control_precheck.py`

Checkpoint minimo richiesto:
- `stable-level-b-change-control-v1`

### 5.6 Traceability Bundle
Anchor minimi:
- `docs/LEVEL_B_TRACEABILITY_BUNDLE_v1.md`
- `schemas/level_b_traceability_bundle_registry_v1.json`
- `tools/run_level_b_traceability_bundle.py`

Checkpoint Git futuro raccomandato:
- `stable-level-b-traceability-v1`

## 6. Ordine di esecuzione raccomandato

1. Validation Kit
2. Golden Baseline Pack
3. Release Gate Offline
4. Runbook Offline
5. Change Control Pack
6. Traceability Bundle

Il bundle non sostituisce l'ordine sopra: lo rende leggibile e verificabile.

## 7. Regole di decisione

### 7.1 `COMPLETE`
Solo se:
- il registry è valido;
- tutti i file-ancora minimi esistono;
- tutti i tag richiesti sono presenti;
- tutti i componenti risultano ricostruibili;
- il working tree è pulito.

### 7.2 `HOLD`
Se:
- manca anche un solo file-ancora;
- manca un tag richiesto;
- un componente non è ricostruibile;
- il working tree non è pulito;
- il bundle è presente ma la linea offline non è completa.

### 7.3 `ERROR`
Se:
- il registry è invalido;
- il report non è costruibile;
- la bundle view è incoerente sul piano strutturale.

## 8. Stop conditions

Il bundle deve fermarsi e non dichiarare `COMPLETE` se:
- il Livello B appare scollegato da uno dei checkpoint minimi;
- manca la Golden Baseline;
- manca il Release Gate;
- manca il Runbook;
- manca il Change Control;
- mancano i tag di consolidamento minimi;
- il working tree è sporco in fase di controllo.

## 9. Regola di manutenzione

Il Traceability Bundle non è un sostituto del Change Control Pack.
Ogni modifica alla bundle view deve restare subordinata a:
- baseline golden vigente;
- release gate vigente;
- runbook vigente;
- change control vigente.

## 10. Clausola finale

Il Traceability Bundle v1 ricostruisce e rende leggibile la linea di hardening offline del Livello B.
Non conclude l'istruttoria, non valida esiti opponibili, non chiude M07-LPR e non modifica il perimetro del progetto.
