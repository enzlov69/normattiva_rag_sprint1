# FINAL_AB_RAW_VALIDATION_GATE_SPEC_v1

## 1. Scopo

Il presente documento definisce il **raw validation gate pre-mapper** del runtime controlled handoff della Fase 4.

Il gate è collocato **tra il runner invoker e il response mapper** e ha la sola funzione di:

- validare il payload raw restituito dal runner federato;
- intercettare campi vietati, alias e pattern sostanzialmente equivalenti;
- bloccare sconfinamenti del Livello B verso funzioni decisorie, conclusive o certificative;
- verificare la coerenza tecnica minima del pacchetto documentale;
- aprire warning, errori, degradazioni o blocchi tracciabili;
- consentire il passaggio al mapper solo per output raw conformi oppure conformi con warning/degradazione.

Il gate **non interpreta**, **non decide**, **non completa**, **non corregge** il contenuto del runner e **non modifica la logica interna del runner federato**.

---

## 2. Collocazione architetturale

Flusso canonico aggiornato:

`frontdoor runtime → handoff service → runner invoker → raw validation gate → response mapper → ABResponseEnvelope`

Regola:
il raw validation gate opera come **guardrail contrattuale e documentale del Livello B**.

Riferimenti di conformità:
- fondativo v2: divieto di funzioni conclusive del Livello B, blocchi minimi obbligatori, propagazione dei blocchi, divieto di chiusura M07 da parte del RAG;
- architettura v2: payload del Livello B privi di campi decisori, supporto M07 solo documentale, pacchetto documentale minimo, guardrail permanenti;
- schema dati v2: assenza di campi conclusivi nel Livello B, `DocumentaryPacket` minimo, blocchi su citazioni, vigenza, crossref, coverage, M07;
- API v2: response con `warnings`, `errors`, `blocks`, stati ammessi, divieto di `GO/NO_GO` e campi decisori;
- test v2: blocco di `RAG_SCOPE_VIOLATION`, boundary M07, propagazione blocchi, rigetto dei payload del Livello B con campi vietati.

---

## 3. Obiettivo tecnico

Il gate deve intercettare, prima del mapper:

1. struttura raw illeggibile o incompatibile col contratto;
2. nuclei minimi mancanti o tipizzati in modo errato;
3. campi vietati o alias decisori/conclusivi/validativi;
4. pseudo-chiusure M07 o pseudo-certificazioni della lettura;
5. citazioni incomplete su elementi essenziali;
6. vigenza incerta su punto essenziale;
7. rinvii essenziali irrisolti;
8. coverage insufficiente su punto essenziale;
9. assenza non giustificata di `warnings`/`errors`/`blocks` in presenza di criticità evidenti.

---

## 4. Perimetro funzionale

Il gate:

- riceve il raw output del runner;
- applica validazione di tipo, struttura minima e controlli di perimetro;
- usa registry e schema JSON esterni versionati;
- produce un esito tecnico tra:
  - `SUCCESS`
  - `SUCCESS_WITH_WARNINGS`
  - `DEGRADED`
  - `BLOCKED`
  - `REJECTED`
  - `ERROR`
- restituisce traccia tecnica riusabile dal service layer.

Il gate **non**:

- interpreta il significato giuridico delle fonti;
- decide l’applicabilità concreta;
- chiude M07;
- emette GO / NO-GO;
- arricchisce il raw con inferenze mancanti;
- sostituisce il response mapper.

---

## 5. Nuclei raw controllati

Il gate verifica i seguenti nuclei, ove presenti o dovuti:

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

Regola:
se un nucleo non è prodotto dal runner per disegno tecnico, il gate **non lo inventa**.
Lo classifica come:

- `missing`
- `unsupported`
- `omitted`

e applica l’esito previsto dal registry.

---

## 6. Campi vietati e alias semantici

Il gate deve bloccare almeno:

- `final_decision`
- `decision`
- `legal_outcome`
- `applicability_final`
- `applicable_yes_no`
- `compliance_go`
- `final_go`
- `authorization_status`
- `output_authorized`
- `ready_to_sign`
- `m07_closed`
- `m07_completed`
- `rac_final`
- `case_resolved`
- `definitive_result`

Sono inclusi:
- alias in `snake_case`, `camelCase`, `kebab-case`, con spazi o maiuscole;
- pattern testuali equivalenti;
- conclusive value phrases del tipo:
  - `output authorized`
  - `ready to sign`
  - `case resolved`
  - `final decision`
  - `m07 completed`
  - `m07 closed`
  - `compliance go`

La presenza di tali elementi comporta:
- `REJECTED`
- blocco `RAG_SCOPE_VIOLATION`

---

## 7. Boundary M07

Il supporto a M07 nel Livello B resta **solo documentale**.

Sono ammessi:
- ordinamento delle unità normative;
- segnalazione di allegati;
- segnalazione di omissioni;
- sequenze di lettura;
- supporto preparatorio.

Sono vietati:
- `m07_closed`
- `m07_completed`
- `m07_certified`
- `m07_completion_flag`
- qualunque chiave o valore che equivalga a:
  - chiusura del modulo;
  - certificazione della lettura integrale;
  - completion metodologico.

Esito atteso:
- `REJECTED`
- blocco `RAG_SCOPE_VIOLATION`

---

## 8. Regole di blocco minime

### 8.1 Scope violation
- campo decisorio o conclusivo → `REJECTED` + `RAG_SCOPE_VIOLATION`
- chiusura o certificazione M07 → `REJECTED` + `RAG_SCOPE_VIOLATION`

### 8.2 Citazioni
- citazione essenziale incompleta → `BLOCKED` + `CITATION_INCOMPLETE`

Elementi essenziali minimi:
- `atto_tipo`
- `atto_numero`
- `atto_anno`
- `articolo`
- `uri_ufficiale`
- `stato_vigenza`

### 8.3 Vigenza
- vigenza incerta su punto essenziale → `BLOCKED` + `VIGENZA_UNCERTAIN`

### 8.4 Cross-reference
- rinvio essenziale irrisolto → `BLOCKED` + `CROSSREF_UNRESOLVED`

### 8.5 Coverage
- coverage insufficiente su punto essenziale → `BLOCKED` + `COVERAGE_INADEQUATE`

### 8.6 Struttura
- raw non leggibile / non object → `ERROR`
- schema incompatibile col contratto → `REJECTED` o `ERROR` secondo registry
- nuclei non critici mancanti → `DEGRADED`

### 8.7 Segnali di controllo incoerenti
- criticità evidenti senza `warnings`/`errors`/`blocks` → `BLOCKED` o `DEGRADED` secondo registry

---

## 9. Registry e schema

Il gate usa tre artefatti esterni:

1. `schemas/final_ab_runner_raw_minimum_schema_v1.json`
   - struttura minima ammessa del raw output;
   - tipi attesi dei nuclei.

2. `schemas/final_ab_runner_raw_forbidden_fields_v1.json`
   - campi vietati;
   - alias;
   - pattern su chiavi;
   - pattern su valori.

3. `schemas/final_ab_runner_raw_block_rules_v1.json`
   - regole di mapping tra anomalia e stato;
   - codici blocco;
   - severità;
   - messaggi standard.

Regola:
il validator è **registry-driven** per quanto riguarda severità, codici e pattern vietati.
Non introduce logica inferenziale oltre ai controlli meccanici di struttura, completezza minima e confini semantici vietati.

---

## 10. Contratto del validator

### Input
- `raw_output: Any`
- `request_context: Optional[dict]`

### Output
Oggetto di validazione contenente almeno:
- `status`
- `validated_raw_payload`
- `warnings`
- `errors`
- `blocks`
- `findings`
- `registry_version`
- `schema_version`
- `trace`

### Regola di passaggio al mapper
Il mapper può essere invocato solo se lo stato del validator è:
- `SUCCESS`
- `SUCCESS_WITH_WARNINGS`
- `DEGRADED`

Il mapper **non** può essere invocato se lo stato è:
- `BLOCKED`
- `REJECTED`
- `ERROR`

---

## 11. Integrazione nel service layer

L’integrazione corretta avviene nel `handoff service`:

1. ricezione request A→B;
2. invocazione del runner black-box;
3. validazione raw pre-mapper;
4. eventuale stop / degradazione / blocco;
5. mapping solo per raw ammissibili;
6. costruzione `ABResponseEnvelope`;
7. propagazione dei blocchi al Livello A.

Regole:
- nessuna modifica al retrieval;
- nessuna modifica al router;
- nessuna modifica al ranking;
- nessuna modifica ai corpus;
- nessuna modifica alla logica interna del runner.

---

## 12. Tracciabilità

Il gate deve alimentare una traccia tecnica minima con:
- `validator_module`
- `schema_version`
- `registry_version`
- `detected_anomalies`
- `detected_forbidden_paths`
- `detected_m07_scope_paths`
- `effective_status`

Questa traccia è tecnica e non opponibile.

---

## 13. Errori da prevenire

Devono essere prevenuti almeno i seguenti errori:

- far passare al mapper payload raw con campi decisori;
- degradare invece di rigettare una chiusura M07;
- trattare la coverage come giudizio finale;
- trasformare l’assenza di nuclei critici in correzione automatica;
- aggiungere campi mancanti nel payload del runner;
- usare il validator per “ripulire” semanticamente il runner.

---

## 14. Test minimi

Il pacchetto minimo di test deve coprire:

1. contratti del validator;
2. campi vietati espliciti;
3. alias e pattern equivalenti;
4. citazioni incomplete;
5. vigenza incerta essenziale;
6. crossref essenziale irrisolto;
7. coverage essenziale inadeguata;
8. assenza incoerente di warnings/blocks;
9. boundary M07;
10. end-to-end con gate inserito prima del mapper.

---

## 15. Decisione raccomandata

La soluzione raccomandata è:

- **validator dedicato pre-mapper**;
- **registry esterni** per campi vietati e severità;
- **integrazione nel service layer**;
- **runner invariato**;
- **propagazione dei blocchi al Livello A**;
- **mapper invocato solo su raw ammesso**.

È la soluzione corretta perché:
- mantiene intatto il runner black-box;
- rende effettivo il confine tra Livello A e Livello B;
- blocca sconfinamenti prima della trasformazione in `DocumentaryPacket`;
- evita che il mapper normalizzi contenuti vietati;
- preserva M07 come presidio esclusivo del Livello A.

---

## 16. Clausola finale

Il raw validation gate recupera, controlla, blocca, degrada e traccia.

Non interpreta.
Non conclude.
Non valida.
Non chiude M07.
Non autorizza output opponibili.

Il gate è conforme solo se rafforza la subordinazione del Livello B senza alterare la logica interna del runner federato.
