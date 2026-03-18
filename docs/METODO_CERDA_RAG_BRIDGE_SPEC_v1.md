# METODO\_CERDA\_RAG\_BRIDGE\_SPEC\_v1

## Titolo

Specifica del bridge architetturale tra “Metodo Cerda – PPAV” e “Normattiva RAG” per il governo della frontiera tra Livello A e Livello B

\---

## 1\. Scopo del documento

Il presente documento disciplina la frontiera tecnica, contrattuale e di controllo tra:

* **Livello A — Metodo Cerda / governo istruttorio**;
* **Livello B — Normattiva RAG / supporto documentale**.

Il documento definisce in modo espresso e non aggirabile:

* come il Livello A formula richieste documentali al Livello B;
* come il Livello B restituisce pacchetti documentali al Livello A;
* quali contenuti sono ammessi e vietati nei payload del bridge;
* come il supporto documentale a M07-LPR resta distinto dalla chiusura di M07;
* quali eventi di audit trail e SHADOW sono obbligatori sul confine A↔B;
* come i blocchi del Livello B rientrano sotto governo del Metodo Cerda;
* quali condizioni minime rendono il bridge conforme alla baseline del progetto.

Il presente documento non amplia in alcun modo i poteri del Livello B.

\---

## 2\. Natura e gerarchia del documento

Il presente documento ha natura di **specifica di raccordo** ed è subordinato a:

1. documento fondativo v2;
2. Documento Master v2;
3. architettura v2;
4. schema dati v2;
5. API v2;
6. piano test v2;
7. roadmap v2.

In caso di conflitto prevale sempre la baseline v2.

Il bridge spec può solo:

* dettagliare la frontiera A↔B;
* rafforzare il controllo del confine;
* rendere più stringenti rigetti, blocchi e condizioni di ritorno.

Il bridge spec non può:

* introdurre funzioni conclusive nel Livello B;
* attenuare blocchi già previsti;
* ridurre i presìdi su M07-LPR, PPAV, RAC o GO finale.

\---

## 3\. Principio architetturale del bridge

### 3.1 Formula fondativa

Metodo Cerda governa il ragionamento; il RAG governa il reperimento delle fonti.

### 3.2 Conseguenza specifica sul bridge

La traversata A↔B deve essere progettata in modo che:

* il Livello A resti sempre **livello chiamante sovraordinato**;
* il Livello B resti sempre **livello rispondente subordinato**;
* la risposta del Livello B sia sempre **documentale, tecnica, tracciabile, bloccabile e non autosufficiente**;
* nessun ritorno dal Livello B possa essere usato come esito finale senza riesame metodologico del Livello A;
* ogni divergenza o ambiguità generi degradazione o blocco, non espansione implicita dei poteri del RAG.

### 3.3 Regola di interpretazione restrittiva

In caso di dubbio su payload, stato, semantica, naming o contratto del bridge:

* prevale sempre la lettura più restrittiva;
* prevale sempre la tutela della subordinazione del RAG;
* prevale sempre la soluzione che impedisce al Livello B di assumere valore decisorio, validativo o certificativo.

\---

## 4\. Perimetro del bridge

Il bridge disciplina esclusivamente i seguenti passaggi:

1. **Bridge in entrata A→B**

   * traduzione della domanda metodologica in richiesta documentale;
   * attivazione del dominio documentale;
   * specificazione del perimetro documentale richiesto.
2. **Bridge in uscita B→A**

   * restituzione del pacchetto documentale;
   * restituzione di warning, errori e blocchi;
   * restituzione di coverage, vigenza, rinvii, allegati e supporto M07.
3. **Bridge di controllo trasversale**

   * validazione contrattuale dei payload;
   * intercettazione dei campi vietati;
   * audit trail e SHADOW della traversata;
   * gate di ritorno obbligatorio al Metodo Cerda.

Il bridge non disciplina:

* il ragionamento interno del Livello A;
* la logica interna dei singoli moduli del Livello B;
* la redazione dell’atto;
* la decisione metodologica finale.

\---

## 5\. Attori logici del bridge

### 5.1 Attori minimi lato Livello A

* A1 Orchestratore PPAV
* A2 Case Classifier / FASE 0
* A4 M07 Governor
* A5 Final Compliance Gate
* A6 Output Authorizer

### 5.2 Attori minimi lato Livello B

* B1 Domain Classifier
* B10 Hybrid Retriever
* B12 Coverage Estimator
* B13 Vigenza Checker
* B14 Cross-Reference Resolver
* B15 Citation Builder
* B16 M07 Support Layer
* B17 Guardrail Engine
* B18 Block Manager
* B19 Audit Logger
* B20 SHADOW Tracer

### 5.3 Attori trasversali obbligatori del bridge

* Bridge Contract Validator
* Bridge Payload Sanitizer
* Bridge Return Gate
* Bridge Anti-Scope Validator

Tali funzioni possono essere distribuite su moduli esistenti, ma devono risultare espresse, testabili e auditabili.

\---

## 6\. Regola di chiamata A→B

Il Livello A può interrogare il Livello B solo attraverso una richiesta documentale formalizzata.

Ogni richiesta A→B deve indicare almeno:

* `request\_id`;
* `case\_id`;
* `trace\_id`;
* modulo chiamante del Livello A;
* obiettivo documentale della richiesta;
* dominio principale richiesto;
* eventuali domini secondari;
* perimetro documentale richiesto;
* natura della richiesta;
* essenzialità del punto richiesto;
* eventuale regime FAST-TRACK, attivabile solo dal Livello A.

### 6.1 Nature ammesse della richiesta

* retrieval documentale;
* supporto citazionale;
* verifica vigenza;
* risoluzione rinvii;
* verifica allegati essenziali;
* coverage;
* supporto documentale a M07-LPR.

### 6.2 Nature vietate della richiesta

Il Livello A non può delegare al Livello B richieste equivalenti a:

* “decidi se si applica”;
* “dimmi la conclusione finale”;
* “chiudi M07”;
* “valida il caso”;
* “autorizza l’output”;
* “scegli in via finale la norma prevalente”.

Se la request contiene delega metodologica impropria:

* il bridge deve rigettarla o degradarla;
* deve aprire o supportare `RAG\_SCOPE\_VIOLATION`;
* l’evento deve essere auditato.

\---

## 7\. Regola di risposta B→A

Il Livello B deve restituire esclusivamente un **pacchetto documentale di supporto**.

Sul piano di interfaccia il Livello B non deve esporre endpoint conclusivi né endpoint semanticamente equivalenti a funzioni decisionali, validative o autorizzative.

### 7.1 Contenuto minimo del pacchetto documentale

Il pacchetto deve contenere almeno:

* fonti recuperate;
* unità normative recuperate;
* riferimenti a corpus e versioni usate;
* citazioni valide;
* citazioni bloccate;
* stato di vigenza;
* stato dei rinvii;
* stato degli allegati essenziali, se rilevanti;
* coverage tecnica;
* warning;
* errori;
* blocchi;
* riferimenti di audit;
* SHADOW tecnico;
* stato di supporto M07, se richiesto.

Quando rilevanti rispetto al caso o all'esito della traversata, la response del Livello B deve includere in modo espresso warning, errori, blocchi e trace tecnico.

### 7.2 Natura giuridica del pacchetto

Il pacchetto B→A:

* non equivale a RAC;
* non equivale a parere;
* non equivale a motivazione;
* non equivale a giudizio finale di applicabilità;
* non equivale a GO/NO\_GO;
* non equivale a chiusura di M07;
* non equivale ad autorizzazione dell’output opponibile.

Il pacchetto B→A non può inoltre contenere payload con campi decisionali o validativi, né chiavi o strutture semanticamente equivalenti.

\---

## 8\. Stati ammessi del bridge di ritorno

Il bridge B→A può restituire solo stati coerenti con la natura documentale del Livello B.

### 8.1 Stati ammessi

* `DOCUMENT\_PACKAGE\_READY`
* `DOCUMENT\_PACKAGE\_READY\_WITH\_WARNINGS`
* `DOCUMENT\_PACKAGE\_DEGRADED`
* `DOCUMENT\_PACKAGE\_BLOCKED`
* `DOCUMENT\_PACKAGE\_REJECTED`
* `DOCUMENT\_PACKAGE\_ERROR`

### 8.2 Stati vietati

Sono vietati stati o semantiche equivalenti a:

* `GO`
* `GO\_WITH\_SUPPORT`
* `NO\_GO`
* `CASE\_RESOLVED`
* `FINAL\_DECISION\_READY`
* `M07\_COMPLETED`
* `OUTPUT\_AUTHORIZED`
* `PPAV\_COMPLETED`

Tali stati appartengono al solo governo del Livello A o comunque sono incompatibili con la natura del Livello B.

\---

## 9\. Payload vietati del Livello B

### 9.1 Regola generale

Nel bridge B→A sono vietati campi espressi o semanticamente equivalenti che attribuiscano al Livello B funzione:

* decisoria;
* interpretativa conclusiva;
* motivazionale;
* validativa;
* autorizzativa;
* certificativa di M07;
* conclusiva di PPAV.

### 9.2 Elenco minimo dei campi vietati

Sono vietati almeno i seguenti campi, chiavi, attributi o equivalenti semantici:

* `final\_decision`
* `decision`
* `final\_applicability`
* `applicability\_final`
* `legal\_conclusion`
* `conclusione\_giuridica`
* `motivazione\_finale`
* `motivational\_frame`
* `output\_authorized`
* `final\_authorization`
* `go\_finale`
* `go`
* `no\_go`
* `m07\_closed`
* `m07\_completed`
* `ppav\_closed`
* `rac\_generated`
* `case\_resolved`
* `norma\_prevalente\_finale`
* `atto\_firmabile`
* `provvedimento\_autorizzabile`
* `validazione\_finale`

### 9.3 Regola di equivalenza semantica

Il divieto non riguarda solo i nomi esatti dei campi ma anche:

* sinonimi;
* abbreviazioni;
* campi derivati;
* flag booleani equivalenti;
* stati o label che, nel contesto, producano il medesimo effetto conclusivo.

### 9.4 Conseguenze della violazione

La presenza di un campo vietato nel payload del Livello B produce:

* invalidazione della response o del record;
* apertura o supporto a `RAG\_SCOPE\_VIOLATION`;
* stato `DOCUMENT\_PACKAGE\_REJECTED` o `DOCUMENT\_PACKAGE\_BLOCKED`;
* audit obbligatorio dell’evento;
* impossibilità di trattare la response come semplice warning.

\---

## 10\. Regola speciale su TUEL-first

TUEL-first è una regola interna di instradamento documentale del Livello B per il contesto comunale.

Essa:

* è ammessa come criterio di routing documentale;
* può orientare l’ordine di interrogazione dei corpus;
* non costituisce interpretazione normativa;
* non costituisce presunzione applicativa;
* non produce prevalenza giuridica automatica;
* non può comparire nel bridge come esito conclusivo verso il Livello A.

Il bridge deve trattare TUEL-first come **metadato di instradamento documentale**, non come argomento decisorio.

\---

## 11\. Regola speciale su M07-LPR

### 11.1 Principio

Il supporto documentale del RAG a M07-LPR non equivale mai a chiusura, completamento o certificazione di M07.

### 11.2 Cosa può fare il Livello B in relazione a M07

Il Livello B può soltanto:

* ordinare le unità normative da leggere;
* evidenziare allegati, rinvii e ultimo comma;
* segnalare omissioni o lacune del perimetro documentale;
* predisporre il `M07EvidencePack`;
* marcare `human\_completion\_required = true`.

### 11.3 Cosa non può fare il Livello B

Il Livello B non può:

* certificare lettura integrale;
* dichiarare M07 completato;
* rilasciare esiti equivalenti a “lettura sufficiente”;
* sostituire il presidio umano;
* sostituire il presidio metodologico del Livello A.

### 11.4 Stati ammessi sul supporto M07 lato Livello B

Sono ammessi solo stati come:

* `M07\_SUPPORT\_PREPARED`
* `M07\_SUPPORT\_PARTIAL`
* `M07\_SUPPORT\_DEGRADED`
* `M07\_SUPPORT\_BLOCKED`

Sono vietati stati come:

* `M07\_DONE`
* `M07\_COMPLETED`
* `M07\_CLOSED`
* `M07\_CERTIFIED`

### 11.5 Regola dell’ultimo comma

Se il perimetro documentale evidenzia la presenza di ultimo comma rilevante, allegati essenziali o rinvii non governati, il pacchetto M07 del Livello B deve segnalarlo espressamente e non può essere trattato dal Livello A come completamento implicito della lettura.

\---

## 12\. Audit trail e SHADOW sul bridge

### 12.1 Regola generale

Ogni attraversamento della frontiera A↔B deve generare audit trail e SHADOW minimi obbligatori.

### 12.2 Eventi audit minimi sul bridge

Devono essere auditati almeno:

1. apertura della richiesta A→B;
2. traduzione della domanda metodologica in obiettivo documentale;
3. attivazione del dominio documentale;
4. esito del corpus check;
5. produzione della response B→A;
6. eventuali warning, errori e blocchi;
7. intercettazione di payload vietati;
8. preparazione di supporto M07;
9. ritorno del pacchetto documentale al Livello A;
10. eventuale rigetto o degradazione del pacchetto di ritorno.

### 12.3 Contenuto minimo dello SHADOW del bridge

Lo SHADOW del bridge deve registrare almeno:

* moduli attivati;
* query e filtri applicati;
* corpus e versioni interrogate;
* documenti e unità normative viste;
* citazioni prodotte o bloccate;
* vigenza, rinvii e allegati valutati;
* warning;
* errori;
* blocchi;
* stato di supporto M07;
* esito del Bridge Return Gate.

### 12.4 Regola di non sostituzione

Audit trail e SHADOW:

* sono obbligatori;
* sono supporto di ricostruibilità tecnica;
* non sostituiscono RAC;
* non sostituiscono M07;
* non sostituiscono il controllo metodologico del Livello A.

### 12.5 Blocco per audit insufficiente

Mancanza di audit o SHADOW su un nodo critico del bridge comporta almeno:

* `AUDIT\_INCOMPLETE`;
* degradazione o blocco del pacchetto documentale;
* impossibilità di usarlo come base piena nel percorso opponibile.

\---

## 13\. Gate di ritorno al Metodo Cerda

### 13.1 Principio

Ogni risposta del Livello B deve attraversare un **Bridge Return Gate** prima di essere assunta dal Livello A.

### 13.2 Funzioni minime del Bridge Return Gate

Il Bridge Return Gate deve verificare almeno:

* coerenza contrattuale della response;
* assenza di campi vietati;
* presenza di warning, errori e blocchi coerenti;
* integrità del pacchetto documentale;
* presenza di audit e SHADOW minimi;
* corretta marcatura del supporto M07;
* assenza di semantica conclusiva implicita.

### 13.3 Esiti ammessi del Bridge Return Gate

Il Bridge Return Gate può soltanto:

* accettare il pacchetto come supporto documentale;
* accettarlo con degradazione;
* rigettarlo;
* propagarne i blocchi al Livello A.

Non può:

* trasformarlo in GO;
* trasformarlo in esito finale opponibile;
* sanare implicitamente criticità fondative del Livello B.

### 13.4 Propagazione dei blocchi

Un blocco critico originato nel Livello B:

* deve essere visibile nel pacchetto di ritorno;
* deve propagarsi al Livello A;
* non può essere declassato dal Livello A a semplice warning senza specifica gestione metodologica tracciata.

\---

## 14\. Regime di blocco del bridge

Scatta blocco o degradazione del bridge almeno nei seguenti casi:

* campo vietato nel payload del Livello B;
* stato conclusivo improprio nella response del Livello B;
* supporto M07 trattato come chiusura implicita;
* audit trail incompleto;
* SHADOW incompleto;
* vigenza incerta su punto essenziale non segnalata;
* rinvio essenziale irrisolto non propagato;
* allegato essenziale mancante non propagato;
* coverage inadeguata su punto essenziale non dichiarata;
* request A→B con delega metodologica impropria.

### 14.1 Codici di blocco minimi rilevanti per il bridge

* `RAG\_SCOPE\_VIOLATION`
* `M07\_REQUIRED`
* `AUDIT\_INCOMPLETE`
* `CITATION\_INCOMPLETE`
* `VIGENZA\_UNCERTAIN`
* `CROSSREF\_UNRESOLVED`
* `COVERAGE\_INADEQUATE`
* `OUTPUT\_NOT\_OPPONIBLE`

### 14.2 Regola di non rilascio automatico

Nessun blocco aperto sul bridge può essere rilasciato automaticamente dal Livello B se incide su:

* opponibilità;
* non delega;
* M07;
* audit minimo;
* vigenza essenziale;
* rinvii essenziali.

\---

## 15\. Flusso logico del bridge

1. Il Livello A apre il caso e governa FASE 0.
2. Il Livello A formula la richiesta documentale A→B.
3. Il Bridge Contract Validator verifica la request.
4. Il Livello B attiva il dominio documentale e interroga i corpus.
5. Il Livello B produce il pacchetto documentale.
6. Il Bridge Anti-Scope Validator intercetta semantiche vietate.
7. Il Bridge Return Gate valuta la conformità della response.
8. Il pacchetto rientra nel Livello A solo come supporto documentale.
9. Il Livello A governa M07, RAC, PPAV e Final Compliance Gate.
10. Solo il Livello A può produrre GO/NO\_GO e autorizzare o negare l’output opponibile.

\---

## 16\. Errori architetturali specifici del bridge da prevenire

Sono errori architetturali gravi del bridge:

* usare il bridge come scorciatoia per trasferire conclusioni dal Livello B al Livello A;
* far passare come “supporto” un payload semanticamente decisorio;
* far intendere che il pacchetto M07 equivalga a lettura completata;
* consentire stati di ritorno equivalenti a GO/NO\_GO nel Livello B;
* nascondere blocchi del Livello B nella response al Livello A;
* trattare audit o SHADOW come sostituti del controllo metodologico;
* usare TUEL-first come presunzione interpretativa o applicativa;
* consentire al Livello B di generare RAC o esiti equivalenti.

\---

## 17\. Criteri minimi di accettazione del bridge

Il bridge è accettabile solo se risulta verificato che:

* il Livello B non espone payload con campi conclusivi o validativi;
* il Livello B non restituisce stati equivalenti a GO/NO\_GO o chiusura M07;
* il supporto documentale a M07 resta distinto dalla chiusura di M07;
* audit trail e SHADOW sono obbligatori sul confine A↔B;
* i blocchi critici del Livello B si propagano al Livello A;
* TUEL-first resta confinato a routing documentale;
* il Bridge Return Gate esiste e opera realmente;
* nessun output opponibile può nascere dal solo bridge;
* il ritorno al Metodo Cerda è sempre espresso, tracciato e non aggirabile.

\---

## 18\. Decisione raccomandata

La soluzione raccomandata è la seguente:

* trattare il bridge come **disciplinare della frontiera** e non come mero riepilogo architetturale;
* introdurre un **Bridge Return Gate** espresso;
* rendere esplicito l’elenco dei payload vietati del Livello B;
* disciplinare M07 con stati solo documentali lato B;
* rendere audit trail e SHADOW obbligatori su ogni attraversamento critico;
* mantenere TUEL-first confinato al routing del RAG e non alla decisione.

Questa soluzione è raccomandata perché:

* chiude il punto più delicato del progetto, cioè il passaggio dal supporto documentale al ragionamento metodologico;
* impedisce scorciatoie implicite;
* rende più forte la separazione fra i livelli;
* rende testabile il rispetto della non delega.

\---

## 19\. Clausola finale di chiusura

Il bridge è conforme solo se funziona come frontiera controllata e non come zona grigia.

Il Livello B può restituire solo evidenze documentali, stati tecnici, warning, errori, blocchi e trace.
Il Livello A resta l’unico titolare del governo metodologico, della chiusura di M07, della costruzione del RAC, del GO/NO\_GO finale e dell’autorizzazione dell’output opponibile.

Qualsiasi soluzione che renda il bridge idoneo a trasferire conclusioni, validazioni o chiusure implicite dal Livello B al Livello A è non conforme alla baseline del progetto.
