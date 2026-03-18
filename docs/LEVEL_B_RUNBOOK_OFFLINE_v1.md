# LEVEL_B_RUNBOOK_OFFLINE_v1

## 1. Scopo

Il presente documento definisce il **Runbook Offline v1 del Livello B** come fascicolo operativo di esecuzione, controllo e consolidamento del track offline già dotato di:

- Validation Kit offline;
- Golden Baseline Pack;
- Release Gate Offline.

Il runbook non introduce runtime, non modifica il runner federato e non anticipa integrazioni applicative.

La sua funzione è una sola: **governare in modo ordinato l'esecuzione operativa del cantiere offline**, prima di commit, tag o ulteriori evoluzioni pre-runtime.

## 2. Soluzione raccomandata

La soluzione raccomandata è un runbook separato, versionato e rieseguibile, composto da:

1. documento prescrittivo;
2. checklist JSON versionata;
3. schema del report di preflight;
4. helper offline di supporto;
5. piccolo runner di preflight;
6. test dedicati del runbook.

Questa è la soluzione corretta perché distingue tre piani che non devono confondersi:

- **validator offline** del Livello B;
- **release gate** del track offline;
- **disciplina operativa** con cui l'operatore esegue, controlla e consolida il cantiere.

## 3. Perimetro e limiti

### 3.1 Incluso
Il runbook governa:
- ordine di esecuzione delle verifiche offline;
- preflight di presenza file e suite minime;
- lettura corretta dell'esito del Release Gate Offline;
- housekeeping locale prima del consolidamento Git;
- criteri di congelamento del fascicolo operativo.

### 3.2 Escluso
Il runbook non può:
- sostituire il Release Gate Offline;
- dichiarare rilasciabile il Livello B in assenza di gate `GO`;
- validare istruttorie amministrative;
- chiudere M07-LPR;
- autorizzare output opponibili;
- introdurre scorciatoie sul runner federato, sul runtime o sui corpus.

## 4. Architettura del pacchetto

Il pacchetto è composto da:

- `docs/LEVEL_B_RUNBOOK_OFFLINE_v1.md`
- `schemas/level_b_runbook_checklist_v1.json`
- `schemas/level_b_runbook_preflight_report_schema_v1.json`
- `validators/level_b_runbook_rules.py`
- `tools/run_level_b_runbook_preflight.py`
- `tests/test_level_b_runbook_checklist.py`
- `tests/test_level_b_runbook_rules.py`
- `artifacts/level_b_runbook_preflight_report_example_v1.json`

## 5. Principi operativi non negoziabili

1. il runbook resta nel solo perimetro offline del Livello B;
2. runner federato, runtime, retrieval, router, corpus e bridge applicativo restano esclusi;
3. la Golden Baseline resta benchmark regressivo non negoziabile;
4. il Release Gate Offline si esegue solo dopo la sequenza ordinata delle suite minime;
5. audit trail e SHADOW restano obbligatori sui casi critici;
6. il supporto M07 del Livello B non equivale mai a chiusura M07;
7. l'ultima autorizzazione resta sempre esterna al Livello B e riservata al Livello A.

## 6. Ordine raccomandato di esecuzione

### 6.1 Step 1 — Igiene repository
Verificare che il repository sia pulito o che eventuali differenze locali siano intenzionali e compatibili con il cantiere in corso.

Comando minimo:

```bash
git status
```

### 6.2 Step 2 — Preflight del runbook
Verificare presenza di:
- asset della Golden Baseline;
- asset del Release Gate Offline;
- file del presente runbook;
- suite minime richiamate dal fascicolo.

Comando raccomandato:

```bash
py tools/run_level_b_runbook_preflight.py
```

Esiti ammessi del solo preflight:
- `READY`
- `HOLD`
- `ERROR`

Il preflight **non** decide il rilascio del Livello B. Dice solo se il fascicolo è eseguibile in modo ordinato.

### 6.3 Step 3 — Suite critiche del Livello B
Eseguire in questo ordine:

```bash
py -m pytest tests/test_level_b_payload_contract.py -q
py -m pytest tests/test_level_b_payload_semantics.py -q
py -m pytest tests/test_level_b_m07_boundaries.py -q
py -m pytest tests/test_level_b_audit_shadow.py -q
py -m pytest tests/test_level_b_block_propagation.py -q
py -m pytest tests/test_level_b_traceability_matrix.py -q
py -m pytest tests/test_level_b_golden_baseline.py -q
```

Regola: la suite golden si esegue **dentro** la sequenza critica, non fuori percorso.

### 6.4 Step 4 — Release Gate Offline
Solo dopo la sequenza critica completa:

```bash
py tools/run_level_b_release_gate_offline.py
```

### 6.5 Step 5 — Lettura del report del gate
Leggere il report strutturato generato dal gate e verificare:
- decisione `GO`;
- assenza di motivi residui `SUSPEND` o `ERROR`;
- assenza di suite mancanti;
- assenza di regressioni sui golden cases;
- assenza di sconfinamento del Livello B.

### 6.6 Step 6 — Housekeeping locale
Prima del consolidamento:
- rimuovere report transitori non destinati al versionamento;
- controllare il working tree;
- evitare di trascinare file di altro cantiere.

### 6.7 Step 7 — Consolidamento Git
Solo a valle di tutto il percorso verde:
- `git add ...`
- `git commit -m "..."`
- `git tag ...`
- `git log --oneline -n 3`
- `git status`

## 7. Regole di lettura degli esiti

### 7.1 Preflight del runbook
- `READY` → il fascicolo è eseguibile;
- `HOLD` → mancano file, suite o pulizia minima del repository;
- `ERROR` → il fascicolo stesso è incoerente o malformato.

### 7.2 Release Gate Offline
- `GO` → il track offline è rilasciabile sul piano tecnico del cantiere;
- `SUSPEND` → regressione o mancanza bloccante;
- `ERROR` → il gate è diventato non deterministico o strutturalmente invalido.

Regola chiave: il preflight del runbook e il release gate hanno **funzioni diverse** e non vanno sovrapposti.

## 8. Condizioni di stop

Il runbook si interrompe immediatamente se si verifica anche una sola delle seguenti condizioni:

1. working tree non pulito su file rilevanti al cantiere;
2. file minimi golden o release gate mancanti;
3. suite critica assente;
4. suite critica fallita;
5. golden baseline fallita;
6. gate offline con esito `SUSPEND` o `ERROR`;
7. presenza di file appartenenti a cantieri sul runner federato o altre aree escluse;
8. proposta di modifica che introduca semantica conclusiva, validativa o certificativa nel Livello B.

## 9. Housekeeping raccomandato

### 9.1 Da rimuovere localmente
Esempio tipico:
- `artifacts/level_b_release_gate_report_v1.json`

### 9.2 Da mantenere come artefatto stabile
Esempio tipico:
- `artifacts/level_b_release_gate_report_example_v1.json`

### 9.3 Regola generale
I report di esecuzione locale non vanno confusi con artefatti stabili di progetto.

## 10. Regole di congelamento

Il Runbook Offline v1 si considera congelato quando:
- documento, checklist JSON e helper esprimono la stessa sequenza operativa;
- i test del runbook risultano verdi;
- il fascicolo richiama correttamente Golden Baseline e Release Gate;
- non esistono sovrapposizioni con runtime o runner.

## 11. Quando cambia la versione

Serve una nuova versione del runbook se cambia anche uno solo dei seguenti elementi:
- ordine degli step;
- elenco delle suite minime richiamate;
- criteri di stop;
- criteri di lettura degli esiti;
- politica di housekeeping;
- rapporto tra runbook, golden baseline e release gate.

Le sole correzioni editoriali che non alterano l'esecuzione possono restare nella stessa versione.

## 12. Clausola finale

Il presente runbook è conforme solo se continua a garantire in modo verificabile che:
- il Livello B resti subordinato al Metodo Cerda;
- il fascicolo operativo non diventi un gate metodologico occulto;
- la Golden Baseline resti fondativa;
- il Release Gate resti l'unico presidio tecnico di prerelease del track offline;
- l'ultima decisione opponibile resti esterna al Livello B.
