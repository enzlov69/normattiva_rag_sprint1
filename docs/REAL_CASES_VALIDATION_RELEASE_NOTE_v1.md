# REAL CASES VALIDATION RELEASE NOTE v1

## 1. Oggetto

Il presente documento registra la chiusura del **primo ciclo di collaudo reale** del progetto **Normattiva RAG / Metodo Cerda – PPAV 2.2**.

La release note ha funzione di:
- attestare il perimetro del primo ciclo di casi reali;
- identificare i test eseguiti e i relativi esiti;
- registrare il significato metodologico del collaudo;
- fissare il tag stabile di riferimento del primo pack di casistica reale;
- formalizzare il passaggio da validazione strutturale a validazione su casi concreti.

---

## 2. Perimetro del primo ciclo

Il primo ciclo di collaudo reale ha riguardato casi concreti costruiti per verificare, nel runtime controllato **Livello A → Livello B → Livello A**, che:

- il **Livello A** apra correttamente il caso;
- il **Livello B** restituisca solo supporto documentale;
- warning, errors e blocks si propaghino correttamente;
- **M07-LPR** non venga chiuso dal Livello B;
- il governo finale del caso resti integralmente in capo al **Livello A**.

Il primo ciclo non ha finalità di produzione piena, ma di:
- collaudo reale controllato;
- validazione casistica minima;
- conferma pratica della subordinazione del Livello B.

---

## 3. Stato di partenza del progetto

Il primo ciclo è stato avviato dopo la chiusura e stabilizzazione dei seguenti blocchi:

1. matrice ufficiale **PPAV S0–S11**;
2. roundtrip controllato **Livello A → Livello B → Livello A**;
3. activation layer runtime A→B→A;
4. boundary test su M07-LPR;
5. test di non-delegabilità e block propagation.

Il primo ciclo di casi reali si colloca quindi **a valle** della validazione metodologica e runtime già chiusa.

---

## 4. Casi reali inclusi nel primo ciclo

### 4.1 Caso Reale n. 1
**Avvio del procedimento d’ufficio per possibile revoca parziale di contributo ad associazione per mancata rendicontazione**

Finalità del caso:
- testare l’avvio del procedimento;
- testare il ritorno documentale su comunicazione di avvio, contenuti minimi, fascicolo e tracciabilità;
- verificare la gestione di scenario degradato;
- verificare il blocco di M07 incompleto;
- verificare il blocco dell’overreach del Livello B.

File collegato:
- `tests/test_real_case_avvio_procedimento_revoca_contributo.py`

### 4.2 Caso Reale n. 2
**Procedimento su istanza di parte per contributo economico straordinario con documentazione iniziale incompleta**

Finalità del caso:
- testare il lato “istanza di parte” del procedimento;
- testare request di supporto documentale su avvio, integrazione documentale, 10-bis, fascicolo e tracciabilità;
- verificare scenario degradato per coverage insufficiente;
- verificare blocco M07 incompleto;
- verificare rifiuto di campi decisori o di completamento M07 nella response di B.

File collegato:
- `tests/test_real_case_istanza_contributo_documentazione_incompleta.py`

### 4.3 Pack cumulativo del primo ciclo
File collegato:
- `tests/test_real_cases_pack_v1.py`

Funzione:
- richiamare in forma unificata i casi reali già stabilizzati;
- verificare che il primo pack di casistica reale regga come suite coerente;
- preparare il terreno alla futura espansione dei casi reali successivi.

---

## 5. Test eseguiti

### 5.1 Caso Reale n. 1
File:
- `tests/test_real_case_avvio_procedimento_revoca_contributo.py`

Esito:
- `4 passed`

### 5.2 Caso Reale n. 2
File:
- `tests/test_real_case_istanza_contributo_documentazione_incompleta.py`

Esito:
- `5 passed`

### 5.3 Pack cumulativo del primo ciclo
File:
- `tests/test_real_cases_pack_v1.py`

Esito:
- `6 passed`

### 5.4 Suite cumulativa del primo ciclo
File eseguiti insieme:
- `tests/test_real_case_avvio_procedimento_revoca_contributo.py`
- `tests/test_real_case_istanza_contributo_documentazione_incompleta.py`
- `tests/test_real_cases_pack_v1.py`

Esito complessivo:
- `15 passed`

---

## 6. Esiti metodologici del primo ciclo

Il primo ciclo conferma, su casistica reale controllata, che:

1. il **Metodo Cerda** governa effettivamente l’apertura e il ritorno del caso;
2. il **Livello B** opera come sottosistema documentale subordinato;
3. il runtime A→B→A intercetta e blocca gli sconfinamenti;
4. warning, errors e blocks documentali si propagano correttamente;
5. il Livello B non può:
   - chiudere M07-LPR;
   - emettere GO/NO_GO;
   - produrre FIRMA_READY;
   - autorizzare output opponibili;
   - decidere l’esito finale del caso;
6. i casi reali possono essere lavorati in modo degradato o bloccato senza perdere il governo metodologico del Livello A.

---

## 7. Regole confermate dal primo ciclo

Il primo ciclo conferma in modo pratico e testato le seguenti regole:

1. ogni caso si apre nel **Livello A**;
2. il **Livello A** invia a **B** solo request documentali controllate;
3. il **Livello B** restituisce solo supporto documentale;
4. i blocchi di **B** si propagano correttamente ad **A**;
5. **M07-LPR** non può essere chiuso da **B**;
6. il ritorno da **B** non equivale mai a decisione finale;
7. nessun caso del primo ciclo genera automaticamente GO/NO_GO o FIRMA_READY;
8. il governo finale del caso resta sempre nel **Livello A**.

---

## 8. Tag stabile del primo ciclo

Tag di riferimento del primo ciclo di casi reali:

- `stable-real-cases-pack-v1`

Tale tag costituisce il riferimento stabile del primo pacchetto di casistica reale validata.

---

## 9. Significato operativo del primo ciclo

Il primo ciclo consente di affermare che il progetto non è più soltanto:
- metodologicamente corretto;
- contrattualmente corretto;
- runtime-validato;

ma è anche:
- **casisticamente avviato**;
- **realmente collaudato su scenari concreti**;
- pronto per una progressiva espansione della casistica.

Questo non equivale ancora a produzione massiva, ma equivale a:

**uso controllato e collaudato del RAG sotto governo del Metodo Cerda su una prima base di casi reali.**

---

## 10. Stato risultante

Il progetto, a valle del primo ciclo, dispone ora di:

1. baseline fondativa e metodologica stabile;
2. matrice PPAV S0–S11 stabile;
3. roundtrip A→B→A stabile;
4. runtime activation layer stabile;
5. primo pack di casi reali validato e versionato.

Il presente stato può essere qualificato come:

**primo ciclo di collaudo reale chiuso con esito positivo**

---

## 11. Passi successivi raccomandati

I passi successivi raccomandati sono:

1. apertura del **Caso Reale n. 3**;
2. progressiva estensione del pack dei casi reali;
3. mantenimento della regola per cui ogni nuovo caso reale entra nel repo solo con:
   - test dedicato;
   - eventuale test cumulativo;
   - tracciabilità Git;
4. eventuale predisposizione di una dashboard o checklist di collaudo casi reali.

---

## 12. Clausola finale

La presente release note:
- non modifica il fondativo v2;
- non altera la separazione Livello A / Livello B;
- non amplia i poteri del Livello B;
- registra esclusivamente la chiusura del **primo ciclo di collaudo reale** del progetto, con esito positivo e tracciabilità completa nel repo.