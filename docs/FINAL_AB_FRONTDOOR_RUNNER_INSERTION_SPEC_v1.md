# FINAL_AB_FRONTDOOR_RUNNER_INSERTION_SPEC_v1

## 1. Scopo

La presente specifica disciplina il primo innesto tecnico controllato davanti al runner federato,
senza modificare la logica interna del runner, senza alterare retrieval/router/ranking/corpus
e senza spostare funzioni metodologiche dal Livello A al Livello B.

## 2. Decisione raccomandata

La soluzione raccomandata è introdurre un **front door contrattuale** davanti al pacchetto
pre-runtime già validato.

Catena canonica:

**Livello A → Front Door → Adapter pre-runtime A→B→A → Runner federato → Adapter → Front Door → Livello A**

Questa soluzione è raccomandata perché:
- mantiene il runner come componente sottostante e non decisorio;
- riusa il pacchetto `adapters/final_ab_pre_runtime_adapter.py` come base obbligatoria;
- concentra i controlli di contratto e di perimetro in un unico punto reversibile;
- evita modifiche semantiche al runner;
- rende l’innesto testabile, bloccabile e facilmente disattivabile.

## 3. Perimetro e non-obiettivi

### 3.1 Perimetro
Il front door può solo:
- validare la request del Livello A;
- validare la response documentale del Livello B;
- bloccare payload o semantiche vietate nel Livello B;
- propagare blocchi critici dal Livello B al Livello A;
- verificare il boundary M07;
- invocare l’adapter pre-runtime e, tramite esso, il runner federato.

### 3.2 Non-obiettivi
Il front door non può:
- riscrivere query documentali;
- cambiare retrieval;
- cambiare ranking;
- cambiare router;
- cambiare i corpus attivi;
- generare GO / NO-GO finale;
- costruire RAC;
- chiudere M07-LPR;
- autorizzare output opponibili.

## 4. Punto di innesto

Il punto di innesto è **prima** del runner federato e **dopo** il Livello A.

Conseguenza:
- il runner non diventa il primo punto di accoppiamento A/B;
- il primo punto di accoppiamento resta un layer contrattuale versionato;
- il runner resta sottostante e invisibile al Livello A.

## 5. Responsabilità del front door

Il front door deve svolgere almeno i seguenti controlli:

1. validazione dei campi minimi di request:
   - `request_id`
   - `case_id`
   - `trace_id`
   - `api_version`
   - `caller_module`
   - `target_module`
   - `timestamp`
   - `payload`

2. invocazione del pacchetto pre-runtime già validato tramite callable bridge;

3. validazione dei campi minimi di response:
   - `request_id`
   - `case_id`
   - `trace_id`
   - `api_version`
   - `responder_module`
   - `status`
   - `payload`
   - `warnings`
   - `errors`
   - `blocks`
   - `timestamp`

4. intercettazione di campi vietati o semantiche conclusive nel Livello B;

5. rigetto di ogni tentativo di chiusura o certificazione M07 lato Livello B;

6. propagazione dei blocchi critici al Livello A senza downgrade;

7. mantenimento del runner in regime di mero esecutore documentale sottostante.

## 6. Invarianti non derogabili

Devono restare sempre veri i seguenti invarianti:

- il Livello A governa il flusso;
- il Livello B resta documentale;
- il runner non riceve poteri metodologici;
- il front door non altera la semantica della richiesta documentale;
- il front door non riscrive gli output del runner se non per:
  - rigetto contrattuale;
  - apertura di `RAG_SCOPE_VIOLATION`;
  - escalation di blocchi critici già presenti;
- nessun campo conclusivo del Livello B supera il front door;
- nessun supporto documentale del Livello B vale come chiusura M07.

## 7. Flusso canonico

1. Il Livello A costruisce una request conforme.
2. Il front door valida il contratto minimo.
3. Il front door chiama l’adapter pre-runtime già validato.
4. L’adapter invoca il runner federato come dipendenza sottostante.
5. Il runner restituisce esito documentale all’adapter.
6. L’adapter ricompone la response A→B→A.
7. Il front door valida la response.
8. Il front door:
   - rigetta campi vietati;
   - rigetta chiusure M07;
   - propaga blocchi critici;
   - restituisce solo esito documentale conforme.
9. Il Livello A governa M07, RAC, PPAV e gate finale.

## 8. Regole sui blocchi

### 8.1 Propagazione
Se la response del Livello B contiene un blocco critico, il front door deve restituire almeno:
- il blocco originario;
- uno stato coerente con il blocco (`BLOCKED`, `REJECTED` o `ERROR`).

### 8.2 Divieto di downgrade
Il front door non può trasformare un blocco critico in warning.

### 8.3 Codici minimi trattati come critici
- `CORPUS_MISSING`
- `SOURCE_UNVERIFIED`
- `CITATION_INCOMPLETE`
- `VIGENZA_UNCERTAIN`
- `CROSSREF_UNRESOLVED`
- `M07_REQUIRED`
- `RAG_SCOPE_VIOLATION`
- `AUDIT_INCOMPLETE`
- `OUTPUT_NOT_OPPONIBLE`
- `COVERAGE_INADEQUATE`

## 9. Regole sul boundary M07

Il front door deve rigettare qualunque response del Livello B che contenga campi o semantiche equivalenti a:
- `m07_closed`
- `m07_completed`
- `m07_certified`
- `m07_completion_certified`
- `reading_completed`
- `integral_reading_certified`

Esito atteso:
- `REJECTED`
- apertura o conferma di `RAG_SCOPE_VIOLATION`

## 10. Reversibilità

L’innesto è conforme solo se reversibile.

Reversibilità minima:
- un solo file entrypoint;
- nessuna modifica alla logica interna del runner;
- rimozione del front door senza refactoring del runner;
- test dedicati che dimostrino il passaggio controllato.

## 11. File minimi raccomandati del cantiere

- `docs/FINAL_AB_FRONTDOOR_RUNNER_INSERTION_SPEC_v1.md`
- `runtime/final_ab_runner_frontdoor.py`
- `schemas/final_ab_frontdoor_runtime_registry_v1.json`
- `tests/test_final_ab_frontdoor_runtime_bridge.py`

## 12. Test di accettazione minimi

Devono risultare verdi almeno i seguenti casi:

1. request contrattuale valida;
2. request contrattuale incompleta;
3. response del Livello B con campo vietato;
4. response del Livello B con tentativo di chiusura M07;
5. propagazione di blocco critico dal Livello B;
6. passthrough al runner senza alterazione semantica della richiesta sottostante.

## 13. Criterio di accettazione del cantiere

Il cantiere può considerarsi correttamente impostato solo se:
- il runner non è stato modificato;
- l’adapter pre-runtime resta la base obbligatoria;
- il front door non introduce campi decisori;
- il Livello B non conclude;
- M07 resta nel Livello A;
- i test del bridge risultano verdi.

## 14. Decisione finale

**Soluzione raccomandata:** front door contrattuale minimale, davanti all’adapter pre-runtime e al runner federato, con guardrail di perimetro, propagazione blocchi e boundary M07, senza toccare retrieval/router/ranking/corpus.
