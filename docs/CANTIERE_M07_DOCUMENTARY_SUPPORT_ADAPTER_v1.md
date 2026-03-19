\# CANTIERE M07 DOCUMENTARY SUPPORT ADAPTER v1



\## 1. Scopo



Questo cantiere realizza il primo innesto applicativo reale sopra la baseline congelata:



\- tag: `stable-final-ab-master-cycle-v1`

\- commit: `e0ea436`



Il cantiere implementa un adapter controllato A→B→A per il supporto documentale al modulo M07-LPR, senza riaprire il core A/B già chiuso e senza alterare la separazione tra Livello A e Livello B.



\## 2. Natura del cantiere



\### Classificazione

\- tipo: adapter controllato A→B→A

\- natura: additiva

\- perimetro: locale e reversibile

\- livello prevalente: Livello A con supporto documentale confinato del Livello B



\### Soluzione raccomandata

La soluzione raccomandata è sviluppare il solo tratto:



1\. bisogno istruttorio nel Livello A

2\. orchestrazione AI-assistita nel Livello A

3\. request documentale strutturata verso il Livello B

4\. response documentale M07-ready dal Livello B

5\. riassorbimento nel Livello A per governo M07, RAC e gate finali



\## 3. Fondamento architetturale



Il cantiere è conforme solo se:



\- il Livello A governa integralmente il flusso;

\- il Livello B restituisce esclusivamente pacchetti documentali, tecnici e di blocco;

\- nessun payload del Livello B contiene campi decisori o autorizzativi;

\- `M07EvidencePack` supporta la lettura integrale ma non chiude M07;

\- RAC, Final Compliance Gate e Output Authorizer restano nel Livello A;

\- audit trail e SHADOW restano obbligatori;

\- i blocchi critici del Livello B si propagano al Livello A.



\## 4. Use case reale



\### Input funzionale

\- quesito istruttorio;

\- bozza di atto;

\- richiesta di ricognizione normativa;

\- esigenza di apertura M07 su testo lungo o rischio interpretativo.



\### Flusso

1\. il Livello A registra il caso;

2\. genera `case\_id`, `trace\_id`, `request\_id`;

3\. apre audit e SHADOW;

4\. attiva orchestrazione AI-assistita;

5\. formula una request documentale verso `/doc/m07/support`;

6\. il Livello B esegue retrieval/coverage/vigenza/rinvii/citazioni/supporto M07;

7\. il Livello B restituisce documentary packet + `M07EvidencePack` + warning/error/block;

8\. il Livello A usa il pacchetto per governare M07 e proseguire verso RAC.



\### Output

Supporto istruttorio non opponibile, tracciabile, bloccabile e riutilizzabile dal Livello A.



\## 5. Perimetro dati del modulo



\## 5.1 Request A→B

Campi minimi:

\- `request\_id`

\- `case\_id`

\- `trace\_id`

\- `api\_version`

\- `caller\_module`

\- `target\_module`

\- `timestamp`

\- `payload`



\## 5.2 Response B→A

Campi minimi:

\- `request\_id`

\- `case\_id`

\- `trace\_id`

\- `api\_version`

\- `responder\_module`

\- `status`

\- `payload`

\- `warnings`

\- `errors`

\- `blocks`

\- `timestamp`



\## 5.3 Oggetto `M07EvidencePack`

Campi minimi:

\- `record\_id`

\- `record\_type`

\- `m07\_pack\_id`

\- `case\_id`

\- `source\_ids`

\- `norm\_unit\_ids`

\- `ordered\_reading\_sequence`

\- `annex\_refs`

\- `crossref\_refs`

\- `coverage\_ref\_id`

\- `missing\_elements`

\- `m07\_support\_status`

\- `human\_completion\_required`

\- `created\_at`

\- `updated\_at`

\- `schema\_version`

\- `record\_version`

\- `source\_layer`

\- `trace\_id`

\- `active\_flag`



\## 6. Regole di blocco e non delega



\## 6.1 Vietato nel Livello B

Sono vietati campi o semantiche equivalenti a:

\- `final\_decision`

\- `final\_applicability`

\- `legal\_conclusion`

\- `motivazione\_finale`

\- `output\_authorized`

\- `m07\_closed`

\- `ppav\_closed`

\- `go\_finale`



\## 6.2 Blocchi minimi da preservare

\- `CITATION\_INCOMPLETE`

\- `VIGENZA\_UNCERTAIN`

\- `CROSSREF\_UNRESOLVED`

\- `M07\_REQUIRED`

\- `RAG\_SCOPE\_VIOLATION`

\- `AUDIT\_INCOMPLETE`

\- `OUTPUT\_NOT\_OPPONIBLE`

\- `COVERAGE\_INADEQUATE`



\## 6.3 Regola M07

`M07EvidencePack`:

\- può ordinare le unità normative;

\- può segnalare allegati, rinvii, omissioni e gap;

\- non può certificare lettura integrale;

\- non può dichiarare chiuso M07;

\- deve imporre `human\_completion\_required = true`.



\## 7. File toccabili



\### Da creare

\- presente spec

\- request schema

\- response schema

\- schema `M07EvidencePack`

\- suite test contrattuale

\- suite test anti-sconfinamento

\- suite test end-to-end



\### Da non toccare

\- fondativo v2

\- core A/B già chiuso

\- runner federato come baseline

\- qualunque elemento che sposti M07 o RAC nel Livello B



\## 8. Test minimi obbligatori



\### Contrattuali

\- validazione campi minimi request/response

\- stabilità enum `status`

\- validazione `source\_layer = "B"` per `M07EvidencePack`



\### Boundary

\- rigetto di payload conclusivi

\- rigetto di `m07\_closed`

\- apertura/supporto a `RAG\_SCOPE\_VIOLATION`



\### End-to-end

\- caso ordinario M07-ready

\- caso con citazione incompleta

\- caso con vigenza incerta

\- caso con rinvio essenziale irrisolto

\- caso con audit mancante



\## 9. Criteri di accettazione



Il pacchetto è accettabile solo se:

\- il contratto request/response è stabile;

\- `M07EvidencePack` è formalizzato e non certificativo;

\- il Livello B non contiene campi conclusivi;

\- i blocchi critici si propagano;

\- il pacchetto resta supporto istruttorio non opponibile;

\- il Livello A conserva apertura caso, M07, RAC, gate finale e autorizzazione umana.



\## 10. Criteri di stop



Stop immediato se:

\- il Livello B può chiudere M07;

\- il Livello B può produrre RAC;

\- il Livello B può produrre GO/NO\_GO;

\- un campo vietato non viene intercettato;

\- un blocco critico non si propaga;

\- manca audit su uno snodo critico.

