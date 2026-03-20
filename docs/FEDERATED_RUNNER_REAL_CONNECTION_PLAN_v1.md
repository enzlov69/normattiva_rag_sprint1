# FEDERATED_RUNNER_REAL_CONNECTION_PLAN_v1

## 1. Qualificazione del cantiere

### Natura
Cantiere runtime **additivo, controllato e reversibile** per sostituire il trasporto simulato del Livello B con un invoker reale verso il runner federato, senza alterare il modello di governo A→B→A.

### Rischio tecnico-metodologico
Rischio **alto** se l’innesto avviene direttamente sul runner o se il payload reale del Livello B entra nel Livello A senza validazione contrattuale, anti-sconfinamento e propagazione dei blocchi.

### Soluzione raccomandata
Soluzione raccomandata: **adapter reale dietro l’handoff service esistente**, con tre presìdi obbligatori:

1. validazione request prima della chiamata al runner;
2. validazione response reale prima del rientro nel Livello A;
3. degradazione o blocco automatico in presenza di campi vietati, response non documentale, difetti di audit/trace o tentativi di chiusura M07.

### Impatto sulla baseline
Impatto **compatibile** con baseline v2 se e solo se:
- non viene toccato il fondativo;
- il Livello B resta documentale;
- l’handoff service resta il punto di controllo;
- il runner federato non diventa il primo punto di accoppiamento;
- audit trail e SHADOW restano obbligatori.

---

## 2. Presupposti vincolanti

Il cantiere assume come non derogabili i seguenti presupposti:
- il Livello A apre il caso e governa il flusso;
- il Livello B restituisce solo documentary packet;
- M07-LPR resta nel Livello A;
- RAC resta nel Livello A;
- GO/NO-GO resta nel Livello A;
- nessun output opponibile nasce fuori dal Livello A;
- ogni blocco critico del Livello B si propaga al Livello A.

---

## 3. Obiettivo tecnico

Sostituire l’invoker simulato con un invoker reale verso il runner federato, mantenendo il file di handoff come **gate contrattuale, anti-sconfinamento, anti-M07-closure, anti-output-opponibile e di block propagation**.

---

## 4. Architettura minima raccomandata

```text
Livello A
  ↓
final_aba_runtime_handoff_service.py
  ├─ validate outgoing request
  ├─ enrich request ids/status/warnings/errors/blocks
  ├─ call real invoker
  ├─ validate incoming response
  ├─ reject forbidden decision fields
  ├─ reject M07 closure attempts
  ├─ propagate documentary blocks
  └─ return controlled A←B envelope
  ↓
final_aba_runner_real_invoker.py
  ↓
Federated Runner (real)
```

### Regola architetturale
Il runner federato reale è **trasporto sottostante**. Il primo punto di accoppiamento resta l’adapter contrattuale A→B→A.

---

## 5. File da creare o modificare

### Documenti
- `docs/FEDERATED_RUNNER_REAL_CONNECTION_PLAN_v1.md`
- `docs/FEDERATED_RUNNER_REAL_CONNECTION_RELEASE_NOTE_v1.md` *(solo a chiusura)*

### Runtime
- aggiornamento minimale di `runtime/final_aba_runtime_handoff_service.py`
- nuovo file `runtime/final_aba_runner_real_invoker.py`

### Test
- `tests/test_final_aba_runner_real_request_validation.py`
- `tests/test_final_aba_runner_real_response_validation.py`
- `tests/test_final_aba_runner_real_block_propagation.py`
- `tests/test_final_aba_runner_real_m07_boundaries.py`
- `tests/test_final_aba_runner_real_end_to_end.py`

---

## 6. Punto di aggancio raccomandato

### Punto di aggancio unico
Il punto di aggancio raccomandato è la **sezione oggi responsabile dell’invocazione mock** dentro `final_aba_runtime_handoff_service.py`.

### Regola di modifica minima
L’handoff service non va riscritto. Va esteso con:
- parametro o factory `use_real_runner: bool = False`;
- dipendenza iniettata `runner_transport` o `runner_client`;
- selettore che usa il mock attuale oppure il nuovo invoker reale;
- identica fase finale di validazione/propagazione lato handoff.

### Formula di innesto
```python
if use_real_runner:
    raw_response = real_invoker.invoke(controlled_request)
else:
    raw_response = mock_invoker.invoke(controlled_request)

controlled_response = validate_and_propagate(raw_response)
return controlled_response
```

---

## 7. Contratto minimo di request verso il runner

La request inviata al runner deve contenere almeno:
- `request_id`
- `case_id`
- `trace_id`
- `api_version`
- `caller_module`
- `target_module`
- `timestamp`
- `status`
- `warnings`
- `errors`
- `blocks`
- `payload`

### Regole
- `warnings`, `errors`, `blocks` devono essere sempre array;
- `status` deve essere valorizzato anche in request, come stato tecnico di invocazione;
- il payload deve restare documentale;
- nessun campo decisorio o validativo può essere presente nella request.

---

## 8. Pacchetto documentale minimo atteso in response

Il runner reale deve rientrare con un pacchetto documentale che contenga almeno:
- `sources`
- `norm_units`
- `citations_valid`
- `citations_blocked`
- `vigenza_records`
- `cross_reference_records`
- `coverage_assessment`
- `warnings`
- `errors`
- `blocks`
- `shadow_fragment`

### Regola
L’assenza di uno dei campi minimi produce `REJECTED` o `DEGRADED`, secondo gravità.

---

## 9. Campi vietati nella response del Livello B

La response del runner deve essere respinta se contiene campi come:
- `final_decision`
- `go_no_go`
- `firma_ready`
- `output_authorized`
- `final_opposability`
- `m07_closed`
- `m07_completed`
- `m07_approved`
- `rac_final_outcome`
- `layer_atto_firma_ready`

### Regola
La presenza di uno di tali campi apre almeno:
- `RAG_SCOPE_VIOLATION`
- `OUTPUT_NOT_OPPONIBLE`

Se il campo riguarda chiusura M07, si apre anche:
- `M07_REQUIRED`

---

## 10. Regole di fallback

### Fallback 1 — Response contrattualmente invalida
Esito: `REJECTED`
Azioni:
- blocco `RAG_SCOPE_VIOLATION` o `AUDIT_INCOMPLETE`;
- niente inoltro come output opponibile;
- log audit obbligatorio.

### Fallback 2 — Response documentalmente incompleta
Esito: `DEGRADED` oppure `BLOCKED`
Azioni:
- propagazione blocchi;
- rientro al Livello A come supporto tecnico non opponibile.

### Fallback 3 — Runner non raggiungibile / errore runtime
Esito: `ERROR`
Azioni:
- blocco `CORPUS_MISSING` o errore tecnico equivalente, senza promuovere risultati parziali non tracciati;
- mantenimento del mock come fallback operativo solo se esplicitamente abilitato nel cantiere.

### Fallback 4 — Tentativo di chiusura M07
Esito: `REJECTED`
Azioni:
- `M07_REQUIRED`
- `RAG_SCOPE_VIOLATION`

---

## 11. Sequenza operativa del cantiere

### Step 1 — Documento di piano
Formalizzare obiettivo, rischi, files, patch point, fallback e criteri di successo.

### Step 2 — Real invoker
Introdurre `final_aba_runner_real_invoker.py` con:
- validazione request;
- chiamata a transport reale iniettato;
- validazione response;
- intercettazione campi vietati;
- verifica pacchetto documentale minimo;
- rientro envelope controllato.

### Step 3 — Patch minimale handoff
Agganciare il real invoker nel punto in cui oggi viene usato il mock.

### Step 4 — Test request validation
Verificare che nessuna request non conforme parta verso il runner.

### Step 5 — Test response validation
Verificare che nessuna response conclusiva o invalidante rientri nel Livello A come valida.

### Step 6 — Test block propagation
Verificare propagazione integrale dei blocchi critici.

### Step 7 — Test M07 boundaries
Verificare che il runner possa solo supportare documentalmente M07.

### Step 8 — End-to-end reale
Verificare A→B→A con real invoker e documentary packet reale, senza output opponibile fuori da A.

---

## 12. Criteri di accettazione del cantiere

Il cantiere è chiuso positivamente solo se risultano contemporaneamente veri tutti i seguenti punti:
- l’invoker reale sostituisce il mock senza rompere il perimetro esistente;
- il runner federato viene interrogato davvero;
- l’handoff service resta gate contrattuale e non mero pass-through;
- i campi vietati del Livello B sono intercettati;
- la chiusura M07 dal runner è impossibile;
- i blocchi critici si propagano al Livello A;
- audit trail e SHADOW restano integri;
- nessun output opponibile nasce nel Livello B.

---

## 13. Criteri di sospensione immediata

Il cantiere deve fermarsi se si verifica anche uno solo dei seguenti casi:
- il runner reale restituisce campi decisori non bloccati;
- il runner reale chiude M07 o simula la sua chiusura;
- il blocco critico non si propaga;
- l’handoff service diventa pass-through senza validazione;
- il mock viene distrutto invece di restare fallback testabile;
- audit o SHADOW risultano incompleti.

---

## 14. Decisione raccomandata

La decisione raccomandata è aprire il cantiere con **real invoker additivo + patch minimale dell’handoff + suite test separata**.

Questa soluzione è preferibile perché:
- protegge la baseline già stabilizzata;
- impedisce accoppiamento diretto runner↔Metodo Cerda;
- consente rollback rapido;
- rende verificabile la subordinazione del Livello B.
