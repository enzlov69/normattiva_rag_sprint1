# LEVEL_B_RELEASE_GATE_OFFLINE_v1

## 1. Scopo

Il presente file definisce il **Release Gate Offline v1** del Livello B come presidio tecnico di prerelease da eseguire **prima di ogni commit/tag di consolidamento** del track offline del Livello B.

Il gate:
- non modifica il runner federato;
- non integra runtime;
- non interviene su retrieval, router, corpus o bridge applicativo;
- non sostituisce il Final Compliance Gate del Livello A;
- non chiude M07-LPR;
- non attribuisce opponibilità a output o payload.

Il gate governa solo una decisione tecnica di repository: **GO** oppure **SUSPEND** del rilascio offline del Livello B.

## 2. Soluzione raccomandata

La soluzione raccomandata è usare un gate separato, manifesto e rieseguibile, composto da:

1. un **manifest** con le suite obbligatorie;
2. un **report schema** del risultato;
3. un **runner offline** che esegue le suite richieste;
4. un **helper tecnico** senza logica runtime;
5. una **suite di test del gate** che congela il comportamento del presidio stesso.

Questa è la soluzione corretta perché evita due errori tipici:
- confondere il gate di rilascio tecnico con i validator del Livello B;
- confondere il gate tecnico offline con il gate metodologico finale del Livello A.

## 3. Perimetro del gate

### 3.1 Incluso
Il gate verifica che il track offline del Livello B sia rilasciabile sul piano tecnico, cioè che:
- le suite obbligatorie esistano;
- le suite obbligatorie siano verdi;
- la suite golden fondativa sia verde;
- il report sia generabile in forma strutturata;
- la sospensione si attivi automaticamente in presenza di regressione.

### 3.2 Escluso
Il gate non può:
- concludere il caso amministrativo;
- dichiarare applicabilità normativa;
- validare l’istruttoria comunale;
- chiudere M07-LPR;
- produrre GO finale metodologico;
- autorizzare output opponibili.

## 4. Architettura dei file

Il pacchetto è composto da:

- `docs/LEVEL_B_RELEASE_GATE_OFFLINE_v1.md`
- `schemas/level_b_release_gate_manifest_v1.json`
- `schemas/level_b_release_gate_report_schema_v1.json`
- `validators/level_b_release_gate_rules.py`
- `tools/run_level_b_release_gate_offline.py`
- `tests/test_level_b_release_gate_manifest.py`
- `tests/test_level_b_release_gate_rules.py`

## 5. Suite obbligatorie governate dal gate

Ordine raccomandato di esecuzione:

1. `tests/test_level_b_payload_contract.py`
2. `tests/test_level_b_payload_semantics.py`
3. `tests/test_level_b_m07_boundaries.py`
4. `tests/test_level_b_audit_shadow.py`
5. `tests/test_level_b_block_propagation.py`
6. `tests/test_level_b_traceability_matrix.py`
7. `tests/test_level_b_golden_baseline.py`

La suite `golden_baseline` è **fondativa e non negoziabile**.

## 6. Regole decisionali del gate

### 6.1 GO
Il gate può restituire `GO` solo se:
- il manifest è valido;
- il report schema è presente;
- tutte le suite richieste esistono;
- tutte le suite richieste risultano `PASSED`;
- nessuna suite critica fallisce;
- nessuna suite golden fallisce;
- nessun errore di esecuzione interrompe il presidio.

### 6.2 SUSPEND
Il gate deve restituire `SUSPEND` se si verifica anche una sola delle seguenti condizioni:
- una suite richiesta è assente;
- una suite richiesta fallisce;
- una suite critica produce `FAILED`, `ERROR` o `MISSING`;
- la suite golden fallisce;
- il report schema è assente o invalido;
- la regressione è tale da compromettere la baseline fondativa offline.

### 6.3 ERROR
Il gate deve restituire `ERROR` solo quando il presidio stesso non è eseguibile in modo deterministico, ad esempio:
- manifest illeggibile o incoerente;
- struttura minima del gate assente;
- eccezioni non recuperabili del runner offline del gate.

## 7. Regola di separazione

Il Release Gate Offline v1 è un presidio di **ingegneria di rilascio** del track offline.

Non è un modulo del Livello B che interpreta, conclude o valida contenuti amministrativi.

## 8. Criteri di congelamento

Il gate si considera congelato quando:
- il manifest è stabile;
- l’elenco suite obbligatorie è stabilizzato;
- il report schema è stabilizzato;
- il comportamento `GO/SUSPEND` è coperto da test dedicati.

Ogni modifica successiva richiede:
- incremento di versione;
- aggiornamento del manifest;
- aggiornamento della documentazione;
- riesecuzione completa del gate.

## 9. Convenzione rispetto ai test ordinari

- i **test ordinari** verificano singoli aspetti tecnici del Livello B;
- i **golden tests** congelano i vincoli fondativi trasversali;
- il **release gate** governa il rilascio offline del pacchetto validativo, sulla base dell’esito delle suite obbligatorie.

La distinzione è obbligatoria e non va fusa.

## 10. Esecuzione raccomandata

### 10.1 Comando

```bash
python tools/run_level_b_release_gate_offline.py
```

### 10.2 Con base dir esplicita

```bash
python tools/run_level_b_release_gate_offline.py --base-dir .
```

### 10.3 Con report esplicito

```bash
python tools/run_level_b_release_gate_offline.py --report-path artifacts/level_b_release_gate_report_v1.json
```

## 11. Esito atteso

Il risultato corretto del gate è uno solo tra:
- `GO`
- `SUSPEND`
- `ERROR`

Il gate non produce altro.

## 12. Clausola finale

Il presente presidio è conforme solo se continua a dimostrare in modo verificabile che:
- il Livello B offline non regredisce sui vincoli fondativi;
- la baseline golden resta obbligatoria;
- il rilascio tecnico si sospende automaticamente in presenza di regressione;
- il gate finale metodologico resta esterno al Livello B e riservato al Livello A.
