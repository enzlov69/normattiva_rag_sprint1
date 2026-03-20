# REAL CASES VALIDATION RELEASE NOTE v2

## 1. Oggetto

Il presente documento registra la chiusura della **versione estesa del primo ciclo di collaudo reale** del progetto **Normattiva RAG / Metodo Cerda – PPAV 2.2**.

La presente release note v2 aggiorna e integra la v1, dando atto che il primo ciclo di casistica reale:
- non è più limitato ai primi due casi;
- è stato esteso a un terzo caso reale;
- è stato consolidato in un **pack cumulativo v2**;
- costituisce una baseline estesa di collaudo reale del sistema.

---

## 2. Funzione del documento

La presente release note ha funzione di:
- attestare il perimetro aggiornato del primo ciclo di casi reali;
- registrare i casi inclusi nella versione estesa;
- riepilogare i test eseguiti e gli esiti conseguiti;
- fissare il tag stabile del pack esteso;
- formalizzare il passaggio da “primo ciclo avviato” a **primo ciclo esteso e consolidato**.

---

## 3. Stato di partenza

La presente release note interviene a valle della chiusura e stabilizzazione dei seguenti blocchi di progetto:

1. baseline fondativa v2;
2. Matrice Test Ufficiale **PPAV S0–S11**;
3. roundtrip controllato **Livello A → Livello B → Livello A**;
4. activation layer runtime A→B→A;
5. primo ciclo di casi reali in versione iniziale;
6. primo pack di casi reali `v1`.

La v2 non riapre tali blocchi, ma ne registra l’estensione sul piano della casistica reale.

---

## 4. Perimetro del primo ciclo esteso

Il primo ciclo esteso di collaudo reale ha riguardato la verifica, su casi concreti controllati, che:

- il **Livello A** apra correttamente il caso;
- il **Livello B** riceva solo request documentali controllate;
- il **Livello B** restituisca solo supporto documentale;
- warning, errors e blocks si propaghino correttamente;
- **M07-LPR** non venga chiuso dal Livello B;
- il governo finale del caso resti integralmente nel **Livello A**;
- il comportamento resti coerente non solo sui casi singoli, ma anche in una suite cumulativa.

---

## 5. Casi reali inclusi nella v2

### 5.1 Caso Reale n. 1
**Avvio del procedimento d’ufficio per possibile revoca parziale di contributo ad associazione per mancata rendicontazione**

Finalità del caso:
- testare il lato “avvio d’ufficio” del procedimento;
- verificare supporto documentale su comunicazione di avvio, contenuti minimi, fascicolo e tracciabilità;
- verificare scenario degradato;
- verificare blocco in presenza di `M07_DOCUMENTARY_INCOMPLETE`;
- verificare il rifiuto dell’overreach del Livello B.

File:
- `tests/test_real_case_avvio_procedimento_revoca_contributo.py`

---

### 5.2 Caso Reale n. 2
**Procedimento su istanza di parte per contributo economico straordinario con documentazione iniziale incompleta**

Finalità del caso:
- testare il lato “istanza di parte” del procedimento;
- verificare supporto documentale su avvio, integrazione documentale, profili del 10-bis, fascicolo e tracciabilità;
- verificare scenario degradato per coverage insufficiente;
- verificare blocco su M07 incompleto;
- verificare il rifiuto di campi decisori o conclusivi nel ritorno di B.

File:
- `tests/test_real_case_istanza_contributo_documentazione_incompleta.py`

---

### 5.3 Caso Reale n. 3
**Preavviso di rigetto ex art. 10-bis L. 241/1990 con osservazioni del privato**

Finalità del caso:
- testare una fase avanzata del procedimento;
- verificare il perimetro documentale del preavviso di rigetto;
- verificare il trattamento documentale delle osservazioni del privato;
- verificare che il Livello B non valuti il merito finale delle osservazioni;
- verificare il blocco dell’overreach di B sul merito e su M07.

File:
- `tests/test_real_case_preavviso_rigetto_osservazioni_privato.py`

---

## 6. Pack cumulativi

### 6.1 Pack v1
File:
- `tests/test_real_cases_pack_v1.py`

Funzione:
- consolidare i primi casi reali disponibili nella prima forma unificata di casistica.

### 6.2 Pack v2
File:
- `tests/test_real_cases_pack_v2.py`

Funzione:
- consolidare in un’unica suite il **primo pacchetto esteso di casi reali**;
- verificare la tenuta congiunta dei casi reali n. 1, n. 2 e n. 3;
- costituire la baseline estesa di collaudo reale.

---

## 7. Test eseguiti

### 7.1 Caso Reale n. 1
File:
- `tests/test_real_case_avvio_procedimento_revoca_contributo.py`

Esito:
- `4 passed`

### 7.2 Caso Reale n. 2
File:
- `tests/test_real_case_istanza_contributo_documentazione_incompleta.py`

Esito:
- `5 passed`

### 7.3 Caso Reale n. 3
File:
- `tests/test_real_case_preavviso_rigetto_osservazioni_privato.py`

Esito:
- `6 passed`

### 7.4 Pack cumulativo v2
File:
- `tests/test_real_cases_pack_v2.py`

Esito:
- `9 passed`

### 7.5 Suite cumulativa estesa del primo ciclo
File eseguiti insieme:
- `tests/test_real_case_avvio_procedimento_revoca_contributo.py`
- `tests/test_real_case_istanza_contributo_documentazione_incompleta.py`
- `tests/test_real_case_preavviso_rigetto_osservazioni_privato.py`
- `tests/test_real_cases_pack_v2.py`

Esito complessivo:
- `24 passed`

---

## 8. Esiti metodologici della v2

La versione estesa del primo ciclo conferma, in modo testato, che:

1. il **Metodo Cerda** governa effettivamente il ciclo di lavoro sui casi reali;
2. il **Livello B** opera come sottosistema documentale subordinato;
3. il runtime A→B→A intercetta e blocca gli sconfinamenti;
4. warning, errors e blocks documentali si propagano correttamente ad A;
5. il **Livello B** non può:
   - chiudere M07-LPR;
   - emettere GO/NO-GO;
   - produrre FIRMA_READY;
   - autorizzare output opponibili;
   - decidere l’esito finale del caso;
   - valutare il merito finale delle osservazioni del privato;
6. il sistema regge non solo su casi singoli, ma anche su una suite cumulativa di casi reali differenti.

---

## 9. Regole confermate dalla v2

La presente versione estesa conferma in modo pratico e testato le seguenti regole:

1. ogni caso si apre nel **Livello A**;
2. il **Livello A** invia a **B** solo request documentali controllate;
3. il **Livello B** restituisce solo supporto documentale;
4. i blocchi documentali di **B** si propagano correttamente ad **A**;
5. **M07-LPR** non può essere chiuso da **B**;
6. il ritorno da **B** non equivale mai a decisione finale;
7. nessun caso del primo ciclo esteso genera automaticamente:
   - `GO`
   - `NO_GO`
   - `FIRMA_READY`
   - autorizzazione di output;
8. il merito finale del caso resta sempre nel **Livello A**;
9. anche nei casi più avanzati, come il 10-bis, il Livello B può supportare documentalmente ma non può concludere.

---

## 10. Significato operativo della v2

La v2 consente di affermare che il progetto non è più soltanto:
- fondativamente corretto;
- metodologicamente corretto;
- contrattualmente corretto;
- runtime-validato;

ma è anche:
- **casisticamente esteso**;
- **collaudato su famiglie procedimentali differenti**;
- **consolidato in un pack cumulativo di casi reali**.

In particolare, la v2 dimostra la tenuta del sistema su tre famiglie diverse:
- procedimento d’ufficio;
- procedimento su istanza di parte;
- fase avanzata di contraddittorio procedimentale.

---

## 11. Tag stabile della v2

Tag di riferimento della versione estesa del pack casi reali:

- `stable-real-cases-pack-v2`

Tale tag costituisce il riferimento stabile della presente release note.

---

## 12. Stato risultante

A valle della v2, il progetto dispone ora di:

1. baseline fondativa e metodologica stabile;
2. matrice PPAV S0–S11 stabile;
3. roundtrip A→B→A stabile;
4. activation layer runtime stabile;
5. tre casi reali distinti validati;
6. pack cumulativo esteso dei casi reali validato e versionato.

Il presente stato può essere qualificato come:

**primo pacchetto esteso di collaudo reale chiuso con esito positivo**

---

## 13. Passi successivi raccomandati

I passi successivi raccomandati sono:

1. apertura del **Caso Reale n. 4**;
2. progressiva espansione controllata della casistica reale;
3. mantenimento della regola per cui ogni nuovo caso reale entra nel repo solo con:
   - test dedicato;
   - eventuale aggiornamento del pack cumulativo;
   - tracciabilità Git;
4. eventuale predisposizione di strumenti di lettura sintetica della copertura reale del sistema;
5. governo della crescita del progetto tramite cicli di rilascio, non tramite ampliamenti disordinati.

---

## 14. Clausola finale

La presente release note:
- non modifica il fondativo v2;
- non altera la separazione Livello A / Livello B;
- non amplia i poteri del Livello B;
- registra esclusivamente la chiusura della **versione estesa del primo ciclo di collaudo reale**, con esito positivo e tracciabilità completa nel repo.