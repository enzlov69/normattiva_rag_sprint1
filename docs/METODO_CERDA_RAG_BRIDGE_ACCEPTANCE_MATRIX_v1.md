# METODO_CERDA_RAG_BRIDGE_ACCEPTANCE_MATRIX_v1

## 1. Scopo

Il presente documento definisce la matrice minima di accettazione del collegamento tra:

- **Livello A — Metodo Cerda / PPAV**
- **Livello B — Normattiva RAG / infrastruttura documentale**

La matrice ha funzione di verifica architetturale, contrattuale e di rilascio.
Non sostituisce il Bridge Spec, ma lo rende controllabile.

---

## 2. Regola fondativa di lettura

La matrice è conforme solo se rende verificabile, in modo testabile e non aggirabile, che:

- il **Metodo Cerda** governa ragionamento, qualificazione del fatto, interpretazione, motivazione, conclusione, validazione e autorizzazione dell’output opponibile;
- il **RAG** governa solo reperimento delle fonti, attivazione dei corpus, supporto documentale, tracciabilità, audit tecnico e blocchi;
- il **TUEL-first** resta una regola interna di instradamento documentale del Livello B;
- nessun modulo, payload, endpoint o flusso del Livello B può produrre esiti conclusivi o validativi.

---

## 3. Ambito di verifica

La presente matrice deve essere applicata almeno a:

- Bridge Spec Metodo ↔ RAG;
- contratti API A→B e B→A;
- schema dati del Livello B;
- guardrail di interfaccia;
- propagazione blocchi;
- M07 Support Layer;
- Audit Logger e SHADOW Tracer;
- release gate architetturale.

---

## 4. Regola di severità

Classificazione minima:

- **CRITICA**: difetto che compromette subordinazione del RAG, opponibilità, M07, gate finale, propagazione blocchi, audit o SHADOW essenziale.
- **ALTA**: difetto che compromette contratto API, tracciabilità, coerenza dei payload, gestione di vigenza/rinvii/citazioni.
- **MEDIA**: difetto che compromette completezza tecnica o leggibilità del controllo senza intaccare da solo i vincoli fondativi.
- **BASSA**: difetto redazionale o non bloccante.

---

## 5. Esiti ammessi

Ogni controllo della matrice deve produrre uno dei seguenti esiti:

- **PASS**
- **PASS_CON_RISERVA**
- **FAIL**
- **NOT_APPLICABLE**

Regola:

- un solo **FAIL** su controllo **CRITICO** impedisce l’idoneità della baseline;
- più **PASS_CON_RISERVA** su controlli ALTI o MEDI impediscono il congelamento finale finché non sono sanati;
- **NOT_APPLICABLE** è ammesso solo con motivazione espressa e auditabile.

---

## 6. Matrice di accettazione

| ID | Area | Controllo | Criterio di accettazione | Evidenza minima richiesta | Severità se fallisce |
|---|---|---|---|---|---|
| BR-ACC-01 | Governance | Separazione A/B espressa | Il documento distingue in modo netto funzioni esclusive del Livello A e funzioni documentali del Livello B | Sezioni dedicate + clausola finale di subordinazione | CRITICA |
| BR-ACC-02 | Governance | Monopolio metodologico del Livello A | Il Livello A è l’unico livello autorizzato a qualificare, interpretare, motivare, concludere e validare | Elenco funzioni esclusive del Livello A | CRITICA |
| BR-ACC-03 | Governance | Subordinazione del Livello B | Il Livello B è descritto solo come layer documentale, tecnico e di blocco | Elenco funzioni consentite del Livello B | CRITICA |
| BR-ACC-04 | Payload | Assenza di campi conclusivi | I payload del Livello B non contengono campi decisori o validativi | Regola esplicita + esempi di campi vietati | CRITICA |
| BR-ACC-05 | Payload | Equivalenza semantica dei campi vietati | Il divieto si applica anche a campi equivalenti a final_decision, approval, applicability_final, case_closed, m07_closed, authorized_output | Lista esemplificativa non tassativa | CRITICA |
| BR-ACC-06 | API | Nessun endpoint conclusivo nel Livello B | Il catalogo API del Livello B non espone funzioni che autorizzano, validano o concludono | Catalogo endpoint documentali e interni | CRITICA |
| BR-ACC-07 | API | Regola di risposta del Livello B | Il Livello B restituisce solo pacchetti documentali, tecnici e di blocco | Clausola contrattuale B→A | CRITICA |
| BR-ACC-08 | API | Contract-first sul bridge | Ogni request/response del bridge ha identificativi minimi, status, warning, errori, blocchi e trace | Schema minimo request/response | ALTA |
| BR-ACC-09 | API | Rigetto payload vietati | La presenza di un campo vietato nel payload B produce rigetto e apertura del blocco corretto | Regola `REJECTED` + codice blocco | CRITICA |
| BR-ACC-10 | Blocchi | Propagazione B→A | Un blocco critico aperto nel Livello B è visibile al Livello A e non può essere degradato a warning | Regola di propagazione + test dedicato | CRITICA |
| BR-ACC-11 | Blocchi | Impossibilità di override improprio | Il Livello A non può trattare un blocco critico del Livello B come non rilevante per output opponibile | Clausola di non aggiramento | CRITICA |
| BR-ACC-12 | M07 | Supporto documentale senza chiusura | Il supporto documentale a M07-LPR non equivale in nessun caso a chiusura o completamento di M07 | Clausola esplicita su non-equivalenza | CRITICA |
| BR-ACC-13 | M07 | M07 Support Layer senza poteri certificativi | `/doc/m07/support` può predisporre evidenze, ma non certificare lettura integrale né chiudere M07 | Regola del modulo + regola API | CRITICA |
| BR-ACC-14 | M07 | Ritorno al Metodo obbligatorio | Dopo il pacchetto documentale M07, la valutazione torna necessariamente al M07 Governor del Livello A | Bridge Return Gate o clausola equivalente | CRITICA |
| BR-ACC-15 | Audit | Audit trail minimo sul confine | Ogni attraversamento A→B e B→A genera audit minimo collegato a `case_id` e `trace_id` | Eventi audit sui nodi critici | CRITICA |
| BR-ACC-16 | SHADOW | SHADOW del percorso documentale | Query, filtri, moduli attivati, risultati, warning, errori, blocchi e versioni sono tracciati | Campo/oggetto SHADOW o trace tecnica | CRITICA |
| BR-ACC-17 | Audit/SHADOW | Non sostitutività | Audit e SHADOW supportano ricostruibilità ma non sostituiscono il controllo metodologico | Clausola espressa | CRITICA |
| BR-ACC-18 | Citazioni | Citazioni opponibili ricostruibili | Nessuna citazione incompleta può transitare come idonea | Regole minime di citazione + blocco dedicato | ALTA |
| BR-ACC-19 | Vigenza | Vigenza essenziale governata | Una vigenza incerta su punto essenziale impedisce piena opponibilità | Stato vigenza + blocco o degradazione | ALTA |
| BR-ACC-20 | Rinvii | Rinvii essenziali governati | Un rinvio essenziale non ricostruito blocca o degrada | Stato crossref + blocco dedicato | ALTA |
| BR-ACC-21 | Coverage | Coverage non decisoria | La coverage è qualificata come stima tecnica e non come giudizio di sufficienza giuridica | Clausola espressa | ALTA |
| BR-ACC-22 | Output | GO finale riservato al Livello A | Nessun output opponibile nasce senza gate metodologico e autorizzazione finale del Livello A | Clausola GO / NO-GO + Output Authorizer | CRITICA |
| BR-ACC-23 | Fallback | Degradazione corretta | In caso di criticità il bridge può degradare a supporto istruttorio non opponibile, non a pseudo-esito finale | Regola di fallback | ALTA |
| BR-ACC-24 | Fast-track | Nessuna elusione dei presìdi | Il FAST-TRACK comprime il tempo ma non elimina M07, blocchi, audit, vigenza, rinvii e gate finale | Clausola dedicata | CRITICA |
| BR-ACC-25 | Release | Stop al rilascio su violazioni fondative | Se il Livello B conclude, valida, chiude M07, nasconde blocchi o manca audit critico, il rilascio è sospeso | Elenco condizioni di sospensione | CRITICA |
| BR-ACC-26 | Test | Test anti-sconfinamento previsti | Esistono test contrattuali e di regressione sui payload vietati, su M07 e sui blocchi | Piano test o matrice test collegata | CRITICA |
| BR-ACC-27 | Dati | Nessun oggetto B con esito finale opponibile | Gli oggetti del Livello B non modellano esiti finali di decisione o autorizzazione | Verifica schema dati | CRITICA |
| BR-ACC-28 | Contratto | Pacchetto minimo di ritorno B→A | Ogni risposta documentale contiene almeno fonti, unità, stato citazioni, vigenza, rinvii, coverage, warning, errori, blocchi, trace | Elenco oggetto minimo di risposta | ALTA |
| BR-ACC-29 | Guardrail | Guardrail di ruolo, dato e interfaccia presenti | Il bridge è protetto da guardrail che impediscono esiti metodologici, record impropri e payload conclusivi | Sezione guardrail completa | CRITICA |
| BR-ACC-30 | Idoneità finale | Baseline architetturale non aggirabile | Il sistema è idoneo solo se la subordinazione del RAG è verificabile, non solo dichiarata | Clausola finale di idoneità | CRITICA |

---

## 7. Elenco minimo dei campi vietati del Livello B

L’elenco seguente è **minimo** e **non tassativo**.
La presenza nel Livello B di uno di questi campi, o di un loro equivalente semantico, comporta rigetto contrattuale e apertura di blocco `RAG_SCOPE_VIOLATION`.

### 7.1 Campi espressamente vietati

- `final_decision`
- `decision_outcome`
- `case_resolved`
- `case_closed`
- `final_validation`
- `validated`
- `approval_status`
- `approved_for_output`
- `authorize_output`
- `output_authorized`
- `legal_applicability_final`
- `norma_prevalente_final`
- `motivazione_finale`
- `rac_final`
- `go_final`
- `no_go_final`
- `m07_closed`
- `m07_completed`
- `reading_certified`
- `provvedimento_autorizzato`

### 7.2 Regola di equivalenza semantica

Sono ugualmente vietati campi che, pur con nome diverso, producono uno di questi effetti:

- chiusura del caso;
- validazione finale;
- autorizzazione dell’output opponibile;
- certificazione di lettura integrale;
- scelta finale della norma prevalente;
- dichiarazione finale di applicabilità concreta;
- conclusione istruttoria;
- formazione autonoma del GO.

---

## 8. Auto-fail immediato della baseline

La baseline del bridge è da considerarsi **non idonea** in presenza anche di una sola delle seguenti condizioni:

1. il Livello B espone un endpoint conclusivo;
2. il payload del Livello B contiene campi decisori o validativi;
3. il supporto documentale a M07 è trattato come chiusura/completamento di M07;
4. un blocco critico del Livello B non si propaga al Livello A;
5. l’output opponibile può nascere senza GO finale del Livello A;
6. audit trail o SHADOW mancano su un nodo critico del bridge;
7. coverage, retrieval o ranking sono trattati come giudizio istruttorio;
8. un report tecnico del Livello B è utilizzabile da solo come parere conclusivo;
9. il FAST-TRACK viene usato per eludere un presidio fondativo;
10. il Bridge Return Gate verso il Metodo non esiste o è aggirabile.

---

## 9. Uso raccomandato

La sequenza raccomandata è:

1. congelare il Bridge Spec;
2. verificare il Bridge Spec con la presente matrice;
3. allineare schema dati e API ai controlli critici;
4. derivare i test contrattuali e di regressione dalla matrice;
5. dichiarare la baseline idonea solo dopo esito verde dei controlli critici.

---

## 10. Clausola finale

La presente Acceptance Matrix è conforme solo se rende **effettiva** la seguente separazione:

- il **Livello B** recupera, struttura, traccia, segnala e blocca;
- il **Livello A** governa, interpreta, motiva, conclude e valida.

Ogni soluzione che permetta al RAG di oltrepassare questo confine è non conforme alla baseline architetturale del progetto.
