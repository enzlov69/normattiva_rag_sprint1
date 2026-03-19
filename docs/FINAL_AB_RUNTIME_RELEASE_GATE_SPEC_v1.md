# FINAL_AB_RUNTIME_RELEASE_GATE_SPEC_v1

## 1. Posizionamento

Questa specifica definisce una milestone trasversale di rilascio e presidio qualita' del progetto Normattiva RAG / Metodo Cerda - PPAV.

Non sostituisce la Fase 10 della roadmap v2 e non la rinomina.

La sua collocazione corretta e':

- post-Fase 10, come release gate tecnico-documentale;
- oppure in parallelo alla chiusura della Fase 10, ma solo come supporto tecnico-documentale non interferente.

Questa specifica non equivale a chiusura di M07 e non modifica il perimetro del collegamento finale A/B gia' definito dalla roadmap.

## 2. Natura del presidio

Il release gate e' un presidio tecnico di stabilita', auditabilita' e readiness.

Non e':

- un motore decisorio;
- un validatore dell'istruttoria;
- un sostituto del Final Compliance Gate del Livello A;
- un sostituto del Metodo Cerda;
- un meccanismo di chiusura di M07.

Formula di governo vincolante:

**Metodo Cerda governa. RAG recupera. AI assiste. L'uomo decide e firma.**

Conseguenze operative:

- AI assiste nel Livello A ma non decide;
- l'approvazione umana finale obbligatoria resta requisito strutturale;
- il Livello B resta un sottosistema tecnico-documentale e non acquisisce funzioni conclusive;
- il naming tecnico prevalente del Livello B, nei documenti di rilascio e controllo, e' `RAG Normativo Governato e Federato`.

## 3. Scopo

Il release gate trasforma i presidi offline consolidati nelle Fasi 8 e 9 in un controllo automatico e auditabile su GitHub.

Lo scopo e':

- eseguire controlli minimi su push e pull request;
- bloccare regressioni sugli artefatti di anomaly governance;
- verificare la rilasciabilita' minima della baseline tecnica;
- produrre un report leggibile per uso umano;
- confermare i presidi documentali su orchestrazione AI-assistita del Livello A, approvazione umana finale e naming tecnico del Livello B;
- mantenere il Livello B confinato come `RAG Normativo Governato e Federato`, senza funzioni decisorie.

## 4. Perimetro

### 4.1 In scope

- workflow GitHub di verifica;
- esecuzione dei test e validator offline gia' consolidati;
- baseline verifier additivo;
- checklist di rilascio manuale;
- report di readiness tecnico-documentale.

### 4.2 Out of scope

- modifiche a retrieval, router, ranking, corpus;
- modifiche al fondativo v2;
- modifiche al system prompt;
- modifiche distruttive del runner;
- spostamento del boundary M07;
- attribuzione al Livello B di funzioni decisorie, validative o conclusive.

## 5. Input del release gate

Gli input minimi del gate sono:

- `schemas/final_ab_runtime_anomaly_registry_v1.json`
- `schemas/final_ab_runtime_severity_canon_v1.json`
- `schemas/final_ab_runtime_propagation_matrix_v1.json`
- `data/final_ab_runtime_golden_cases_v1.json`
- `tools/final_ab_runtime_anomaly_validator.py`
- `tools/final_ab_runtime_baseline_verifier.py`
- i documenti essenziali Fase 8-9 gia' consolidati;
- la checklist di rilascio;
- i test minimi richiamati dal workflow GitHub.

## 6. Trigger

Il workflow di release gate si attiva almeno su:

- `push` verso `master`;
- `pull_request` verso `master`.

Il gate puo' anche essere eseguito manualmente in locale come controllo di pre-release.

## 7. Controlli minimi

I controlli minimi del release gate sono:

1. coerenza di `anomaly registry`, `severity canon`, `propagation matrix` e `golden cases`;
2. esecuzione verde del validator offline;
3. esecuzione verde del baseline verifier;
4. presenza degli artefatti e delle specifiche essenziali Fase 8-9;
5. conferma che il supporto documentale a M07 non equivale a chiusura M07;
6. conferma che AI assiste nel Livello A ma non decide;
7. conferma che l'approvazione umana finale obbligatoria resta espressa nei documenti pertinenti;
8. conferma che il naming tecnico rilevante del Livello B e' `RAG Normativo Governato e Federato`;
9. conferma che il release gate non introduce logica runtime nuova.

## 8. Output

Il baseline verifier produce un report tecnico, leggibile e deterministico con almeno:

- `summary`
- `passed_checks`
- `failed_checks`
- `warnings`
- `release_readiness`
- `exit_status`

L'esito e' usato come presidio tecnico di readiness e non come giudizio conclusivo del caso.

## 9. Failure policy

Una baseline e' non rilasciabile se almeno uno dei seguenti controlli fallisce:

- validator offline fallito;
- golden cases incoerenti;
- registry, canon e matrix incoerenti;
- baseline verifier fallito;
- file chiave mancanti;
- specifiche o documenti essenziali mancanti;
- assenza del presidio documentale di orchestrazione AI-assistita nel Livello A;
- assenza del requisito di approvazione umana finale obbligatoria;
- naming tecnico del Livello B incoerente nei punti in cui il release gate lo richiede.

Il gate fallisce con `exit_status != 0` in tutti i casi di non rilasciabilita'.

## 10. Esiti di rilascio

### 10.1 Non rilasciabile

Condizione:

- almeno un controllo obbligatorio fallito.

Esito:

- `release_readiness = NOT_RELEASABLE`

### 10.2 Rilasciabile con warning tecnici

Condizione:

- tutti i controlli obbligatori verdi;
- presenza di warning tecnici non bloccanti.

Esito:

- `release_readiness = RELEASABLE_WITH_WARNINGS`

### 10.3 Rilasciabile pienamente

Condizione:

- nessun controllo obbligatorio fallito;
- nessun warning tecnico residuo rilevante nel report.

Esito:

- `release_readiness = FULLY_RELEASABLE`

## 11. Regole di non sostituzione

Il release gate:

- non conclude l'istruttoria;
- non motiva;
- non valida la decisione finale;
- non sostituisce il Final Compliance Gate;
- non sostituisce la firma umana finale;
- non trasforma il Livello B in livello decisorio.

Supporto documentale a M07 non equivale a chiusura M07.

## 12. Regole sul Livello B

Nel contesto di questo gate il Livello B deve essere trattato come `RAG Normativo Governato e Federato`.

Il Livello B puo':

- recuperare fonti;
- strutturare output documentali;
- tracciare, segnalare e bloccare anomalie tecniche;
- restituire supporto documentale non opponibile.

Il Livello B non puo':

- validare l'istruttoria;
- concludere il caso;
- chiudere M07;
- sostituire l'uomo;
- sostituire il governo metodologico del Livello A.

## 13. Decisione implementativa raccomandata

La soluzione raccomandata e' additiva e conservativa:

- nessuna modifica runtime;
- nessuna modifica a handoff service, raw validator, response-envelope gate o runner salvo necessita' meccanica dimostrata da test;
- riuso del validator offline e dei test consolidati come source of truth esecutiva;
- introduzione di workflow GitHub, baseline verifier e release checklist;
- nessuna duplicazione semantica delle regole Fase 8-9.

