# FINAL ABA ROUNDTRIP VALIDATION MATRIX v1

## 1. Oggetto

Il presente documento formalizza la matrice di validazione del flusso:

**Livello A → Livello B → ritorno al Livello A**

all’interno del progetto **Normattiva RAG / Metodo Cerda – PPAV 2.2**.

La matrice ha funzione di:
- rendere testabile il collegamento controllato tra Livello A e Livello B;
- verificare che il Livello B resti sottosistema documentale subordinato;
- verificare che il ritorno dal Livello B non introduca funzioni decisorie o validative;
- verificare che i blocchi documentali si propaghino correttamente al Livello A;
- impedire che il roundtrip A→B→A generi scorciatoie fuori dal governo metodologico del Livello A.

---

## 2. Perimetro del cantiere

Il presente cantiere riguarda esclusivamente:
- la costruzione della richiesta A→B;
- la risposta documentale B→A;
- la propagazione dei blocchi dal Livello B al Livello A;
- la verifica del rispetto dei confini su M07-LPR;
- la verifica end-to-end del roundtrip.

Il presente cantiere **non**:
- modifica il fondativo v2;
- modifica retrieval / router / ranking / corpus;
- attribuisce al Livello B funzioni decisorie;
- riapre il runner federato salvo necessità eccezionale;
- sostituisce i gate del Metodo Cerda con output documentali del Livello B.

---

## 3. Baseline richiamate

Baseline di riferimento:
- baseline A/B: `stable-final-ab-master-cycle-v1`
- baseline locale M07: `stable-m07-documentary-support-acceptance-pack-v1`
- baseline locale FIP-IND: `stable-fip-ind-gate-foundation-v1`
- baseline matrice PPAV S0–S11: ultimo tag stabile della validazione ROOT già chiusa

---

## 4. Principi vincolanti del roundtrip

### 4.1 Governo del flusso
Il flusso è governato dal **Livello A**.

### 4.2 Ruolo del Livello B
Il Livello B:
- riceve una richiesta documentale controllata;
- recupera e struttura supporto documentale;
- restituisce citazioni, coverage, warning, errors e blocks;
- non decide;
- non valida;
- non conclude;
- non autorizza output opponibili;
- non chiude M07-LPR.

### 4.3 Regola di ritorno
Il ritorno dal Livello B:
- non equivale a decisione;
- non equivale a RAC opponibile;
- non equivale a completamento del gate finale;
- non equivale a `FIRMA_READY`.

### 4.4 Propagazione dei blocchi
Ogni blocco critico generato dal Livello B deve:
- essere trasmesso al Livello A;
- restare visibile nella trace;
- impedire esiti utili opponibili finché non è governato dal Livello A.

### 4.5 Regola M07
Il supporto documentale del Livello B a M07-LPR:
- è ammesso;
- è utile;
- è tracciabile;
- **non** equivale mai a chiusura di M07-LPR.

---

## 5. Obiettivi di test del roundtrip

La validazione deve coprire almeno i seguenti obiettivi:

1. correttezza contrattuale della richiesta A→B;
2. correttezza contrattuale della risposta B→A;
3. assenza di campi decisori nel payload A→B;
4. assenza di campi decisori o conclusivi nel payload B→A;
5. propagazione dei blocchi documentali verso A;
6. rispetto dei confini M07;
7. impossibilità per B di produrre `GO`, `NO_GO`, `FIRMA_READY`, opponibilità finale o output authorizer;
8. mantenimento della decisione finale in capo al Livello A.

---

## 6. Blocchi ufficiali del cantiere

### 6.1 Blocco 1 — Request contracts A→B
File:
- `tests/test_final_aba_request_contracts.py`

Controlli minimi:
- payload formalmente valido;
- solo campi ammessi;
- nessun campo decisorio;
- nessun campo validativo;
- nessun `go_no_go`;
- nessun `firma_ready`;
- nessun `final_decision`;
- nessun `output_authorized`;
- nessuna chiusura M07.

### 6.2 Blocco 2 — Response contracts B→A
File:
- `tests/test_final_aba_response_contracts.py`

Controlli minimi:
- payload di ritorno solo documentale;
- warnings / errors / blocks ammessi;
- citazioni / vigenza / coverage ammessi;
- nessuna decisione finale;
- nessun gate finale simulato;
- nessun output authorizer;
- nessun `FIRMA_READY`;
- nessuna chiusura M07.

### 6.3 Blocco 3 — Block propagation
File previsto:
- `tests/test_final_aba_block_propagation.py`

Controlli minimi:
- un blocco critico di B si propaga ad A;
- A non può ignorarlo;
- A non può produrre esito utile opponibile a valle del blocco;
- il blocco documentale non viene “sanato” da B.

### 6.4 Blocco 4 — M07 boundaries
File previsto:
- `tests/test_final_aba_m07_boundaries.py`

Controlli minimi:
- B può supportare documentalmente M07;
- B non può dichiarare M07 completo;
- solo A può considerare M07 superato nel proprio flusso.

### 6.5 Blocco 5 — End-to-end roundtrip
File previsto:
- `tests/test_final_aba_end_to_end_roundtrip.py`

Controlli minimi:
- scenario verde A→B→A;
- scenario con critical block;
- scenario con supporto documentale utile ma non opponibile;
- scenario con payload di ritorno non conforme.

---

## 7. Regole di blocco del roundtrip

1. Il Livello A non può inviare a B campi decisori o conclusivi.
2. Il Livello B non può restituire decisioni, validazioni o output opponibili.
3. Ogni critical block documentale di B deve propagarsi ad A.
4. Il Livello A non può ignorare un critical block documentale proveniente da B.
5. Il supporto documentale di B a M07 non equivale a chiusura di M07.
6. B non può produrre `GO` o `NO_GO`.
7. B non può produrre `FIRMA_READY`.
8. B non può autorizzare output opponibili.
9. Solo il Livello A può decidere l’esito finale del roundtrip.
10. Ogni scenario deve essere testato nel `ROOT/tests`.

---

## 8. Deliverable del cantiere

### 8.1 Documenti
- `docs/FINAL_ABA_ROUNDTRIP_VALIDATION_MATRIX_v1.md`

### 8.2 Test
- `tests/test_final_aba_request_contracts.py`
- `tests/test_final_aba_response_contracts.py`
- `tests/test_final_aba_block_propagation.py`
- `tests/test_final_aba_m07_boundaries.py`
- `tests/test_final_aba_end_to_end_roundtrip.py`

### 8.3 Runtime minimale, solo se strettamente necessario
- `runtime/final_aba_roundtrip_guard.py`

---

## 9. Clausola finale

La presente matrice:
- non altera il fondativo v2;
- non trasferisce funzioni decisorie al Livello B;
- non apre endpoint conclusivi nel Livello B;
- non sostituisce i gate del Livello A;
- serve esclusivamente a rendere verificabile e bloccabile il collegamento controllato A→B→A.