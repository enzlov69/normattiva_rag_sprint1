# FINAL_AB_PRE_RUNTIME_ADAPTER_SPEC_v1

## 1. Scopo

Il presente documento definisce il primo adapter tecnico pre-runtime del collegamento finale tra **Livello A — Metodo Cerda / PPAV** e **Livello B — Normattiva RAG**, nel perimetro strettamente controllato del cantiere Fase 1.

L'adapter è progettato per:
- realizzare il primo flusso minimo **A→B→A** senza toccare il runner federato;
- imporre una validazione contrattuale rigorosa su request e response;
- impedire qualunque sconfinamento semantico o funzionale del Livello B;
- propagare in modo obbligatorio i blocchi documentali critici verso il Livello A;
- presidiare il confine tecnico del modulo **M07-LPR**;
- fornire una base testabile offline per il futuro cantiere runtime.

Il presente documento è subordinato al fondativo v2, al Master v2, ai file specialistici v2 e alla governance finale A/B già consolidata.

---

## 2. Soluzione raccomandata

La soluzione raccomandata è un **adapter contrattuale centrale, offline, sincrono e bloccante**, collocato tra il Livello A e il Livello B, con le seguenti caratteristiche:

- il **Livello A** resta l'unico soggetto che apre il caso, governa il flusso e consuma il pacchetto documentale;
- il **Livello B** risponde solo con output documentali, tecnici, tracciabili e bloccabili;
- l'adapter valida la request del Livello A prima di qualunque inoltro;
- l'adapter valida la response del Livello B prima di qualunque reingresso nel Livello A;
- l'adapter blocca i campi vietati, i tentativi di chiusura M07 e qualunque semantica conclusiva del Livello B;
- l'adapter normalizza e propaga i blocchi verso il Livello A;
- l'adapter restituisce al Livello A solo un **envelope tecnico di rientro**, mai un esito opponibile.

Questa soluzione è raccomandata perché:
- mantiene la separazione tecnica tra i due livelli;
- evita di usare il runner federato come primo punto di accoppiamento;
- rende verificabile il perimetro di non delega;
- consente test offline immediati;
- prepara il runtime futuro senza introdurre integrazioni premature.

Le alternative sono secondarie:
- **accoppiamento diretto A→runner federato**: non raccomandato, perché salta il layer di validazione contrattuale;
- **mock manuali senza adapter**: non raccomandato, perché non rendono stabile la disciplina dei blocchi e dei boundary M07.

---

## 3. Perimetro del cantiere

Il presente cantiere include esclusivamente:
- orchestrazione minima del Livello A a livello di envelope;
- adapter controllato A→B;
- adapter controllato B→A;
- validazione contrattuale della request;
- validazione contrattuale della response;
- propagazione dei blocchi B→A;
- presidio tecnico del confine M07;
- mini-suite pytest di integrazione logica.

Il presente cantiere **non** include:
- modifiche al runner federato;
- integrazione nel runtime reale;
- modifiche a retrieval, ranking, corpus o bridge già esistente;
- modifica del fondativo v2;
- modifica del system prompt del progetto;
- automazione del Final Compliance Gate;
- costruzione del RAC;
- autorizzazione di output opponibili.

---

## 4. Posizionamento architetturale dell'adapter

### 4.1 Collocazione

L'adapter è un componente di pre-runtime collocato tra:
- **A1 / Orchestratore PPAV** e moduli metodologici del Livello A;
- endpoint documentali del Livello B.

### 4.2 Natura del componente

L'adapter ha natura:
- **contrattuale**;
- **validante**;
- **bloccante**;
- **non decisoria**;
- **non interpretativa**;
- **non opponibile**.

### 4.3 Regola di subordinazione effettiva

L'adapter non trasforma il Livello B in sottosistema metodologico.
L'adapter serve solo a:
- verificare il rispetto del contratto;
- verificare l'assenza di campi vietati;
- proteggere il confine M07;
- propagare warning, errors e blocks;
- restituire al Livello A un rientro tecnico coerente.

---

## 5. Flusso minimo A→B→A

## 5.1 Sequenza canonica

1. Il Livello A prepara una **adapter request** completa di `request_id`, `case_id`, `trace_id`, `api_version`, `caller_module`, `target_module`, `target_endpoint`, `level_a_phase`, `m07_context`, `block_policy`, `payload`, `timestamp`.
2. L'adapter valida la request.
3. Se la request è invalida, l'adapter restituisce `REJECTED` o `ERROR` senza inoltro.
4. Se la request è valida, l'adapter inoltra la richiesta al provider documentale offline del Livello B.
5. Il Livello B restituisce una **adapter response** con `documentary_packet`, `warnings`, `errors`, `blocks`, `shadow_fragment`.
6. L'adapter valida la response.
7. L'adapter verifica:
   - campi minimi;
   - campi vietati del Livello B;
   - confini M07;
   - coerenza tra request e response;
   - struttura minima del pacchetto documentale;
   - propagabilità dei blocchi.
8. L'adapter produce il rientro verso il Livello A con:
   - status tecnico finale;
   - blocchi propagati;
   - flag `support_only_flag = true`;
   - flag `opponibile_output_flag = false`;
   - `m07_boundary_state`;
   - `level_a_action_required = true`;
   - frammento SHADOW di collegamento.
9. Il Livello A, fuori dall'adapter, governa M07, RAC, gate finale e output authorizer.

### 5.2 Esiti ammessi dell'adapter

Gli stati finali ammessi dell'adapter sono:
- `SUCCESS`
- `SUCCESS_WITH_WARNINGS`
- `DEGRADED`
- `BLOCKED`
- `REJECTED`
- `ERROR`

L'adapter **non** può restituire:
- `GO`
- `NO_GO`
- `AUTHORIZED`
- `APPROVED`
- `M07_CLOSED`

---

## 6. Input e output dell'adapter

## 6.1 Input obbligatorio lato A

L'adapter riceve una request con i seguenti campi minimi:
- `request_id`
- `case_id`
- `trace_id`
- `flow_id`
- `api_version`
- `caller_module`
- `target_module`
- `target_endpoint`
- `level_a_phase`
- `m07_context`
- `block_policy`
- `payload`
- `timestamp`

### 6.2 Output minimo di rientro verso A

L'adapter restituisce una response con i seguenti campi minimi:
- `request_id`
- `case_id`
- `trace_id`
- `flow_id`
- `api_version`
- `responder_module`
- `status`
- `documentary_packet`
- `warnings`
- `errors`
- `blocks`
- `propagated_blocks`
- `m07_boundary_state`
- `support_only_flag`
- `opponibile_output_flag`
- `level_a_action_required`
- `shadow_fragment`
- `timestamp`

---

## 7. Regole tecniche obbligatorie

## 7.1 Regole sulla request

L'adapter deve rigettare la request se manca anche uno solo dei seguenti elementi essenziali:
- `request_id`
- `case_id`
- `trace_id`
- `api_version`
- `caller_module`
- `target_module`
- `target_endpoint`
- `payload`
- `timestamp`

L'adapter deve inoltre verificare che:
- `caller_module` appartenga al registry del Livello A;
- `target_endpoint` appartenga al perimetro documentale ammesso del Livello B;
- `level_a_phase` sia coerente con il flusso minimo;
- `m07_context` esista sempre come oggetto tecnico, anche se `required = false`.

## 7.2 Regole sulla response

L'adapter deve rigettare o bloccare la response se:
- manca `documentary_packet`;
- manca `blocks`;
- manca `warnings` in presenza di criticità note;
- `request_id`, `case_id` o `trace_id` non corrispondono alla request originaria;
- il Livello B produce campi vietati;
- il Livello B tenta di chiudere M07;
- il Livello B restituisce esiti finali o autorizzativi.

## 7.3 Regole sul pacchetto documentale

Il `documentary_packet` minimo deve contenere almeno:
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

Se uno di questi elementi manca, l'adapter deve almeno degradare l'output e, sui casi essenziali, bloccarlo.

---

## 8. Regole di blocco e propagazione

### 8.1 Principio

I blocchi nati nel Livello B devono essere trattati come blocchi documentali tecnici obbligatoriamente propagabili al Livello A.

### 8.2 Regola operativa

L'adapter deve:
- acquisire i blocchi del Livello B;
- filtrarli sul registry di propagazione;
- preservare codice, severità, origine, oggetto colpito, ragione, stato;
- popolare `propagated_blocks`;
- impostare `level_a_action_required = true` in presenza di qualunque blocco propagabile;
- impostare `status = BLOCKED` in presenza di blocco critico aperto.

### 8.3 Divieto di attenuazione

L'adapter non può:
- trasformare un blocco critico in warning;
- sopprimere un blocco critico documentale;
- restituire `SUCCESS` in presenza di blocco critico aperto.

---

## 9. Confine tecnico M07-LPR

### 9.1 Principio

Il Livello B può solo preparare supporto documentale a M07.
Non può certificare, concludere o chiudere M07.

### 9.2 Regole specifiche

Sono ammessi solo campi di supporto quali:
- sequenza ordinata di lettura;
- elenco unità normative;
- allegati richiamati;
- rinvii richiamati;
- omissioni documentali;
- `human_completion_required = true`.

Sono vietati campi o semantiche equivalenti a:
- `m07_closed`
- `m07_completed`
- `m07_certified`
- `integral_reading_certified`
- `reading_completed`
- `last_comma_verified_as_final`
- qualunque dicitura che equivalga a chiusura metodologica.

### 9.3 Esito boundary

L'adapter deve valorizzare `m07_boundary_state` con uno dei seguenti valori:
- `NOT_REQUESTED`
- `PREPARATORY_ONLY`
- `BOUNDARY_VIOLATION`

Se emerge una violazione, l'adapter deve:
- aprire o supportare `RAG_SCOPE_VIOLATION`;
- impostare `status = REJECTED` o `BLOCKED` secondo la gravità;
- impedire il rientro come supporto documentale valido.

---

## 10. Audit e SHADOW del collegamento

Nel perimetro pre-runtime l'adapter deve produrre almeno un frammento tecnico coerente con audit e SHADOW.

Il frammento minimo deve includere:
- `adapter_version`
- `flow_id`
- `request_contract_valid`
- `response_contract_valid`
- `forbidden_fields_detected`
- `propagated_block_codes`
- `m07_boundary_state`
- `support_only_flag`
- `timestamp`

L'adapter non sostituisce il logging di progetto, ma fornisce un tracciato minimo verificabile per i test.

---

## 11. Errori da prevenire

Devono essere considerati errori critici del cantiere:
- usare il runner federato come primo accoppiamento;
- accettare payload del Livello B con campi decisori;
- accettare semantiche di chiusura M07 dal Livello B;
- non propagare un blocco critico;
- consentire rientro verso A senza `support_only_flag = true`;
- consentire `opponibile_output_flag = true` nel rientro dell'adapter;
- produrre esiti `GO` o `NO_GO` nell'adapter.

---

## 12. Test di accettazione del cantiere

Il cantiere può considerarsi correttamente montato solo se la suite minima verifica almeno:
- validazione contrattuale della request;
- validazione contrattuale della response;
- blocco su campo vietato del Livello B;
- propagazione di blocco critico B→A;
- boundary M07 con `human_completion_required = true`;
- rigetto di tentata chiusura M07;
- flusso end-to-end A→B→A con `support_only_flag = true` e `opponibile_output_flag = false`.

---

## 13. Decisione finale raccomandata

Per il presente cantiere la decisione raccomandata è:

1. montare **subito** un adapter offline minimo e testabile;
2. vincolarlo ai registry e agli schemi del cantiere;
3. usare il modulo Python solo come helper tecnico pre-runtime, senza integrazione nel runner;
4. congelare il comportamento con la mini-suite pytest;
5. rinviare ogni aggancio runtime reale alla fase successiva, solo dopo esito verde dei test.

Questa è la traiettoria più rigorosa perché produce un collegamento tecnico reale ma ancora controllato, non distruttivo e pienamente coerente con la subordinazione del Livello B.
