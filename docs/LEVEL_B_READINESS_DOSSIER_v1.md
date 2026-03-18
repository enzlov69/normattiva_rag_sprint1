# LEVEL B READINESS DOSSIER v1

## 1. Scopo

Il presente dossier definisce lo stato di **readiness offline** del Livello B del progetto
**Normattiva RAG / Metodo Cerda – PPAV**, con funzione di fascicolo sintetico di governo.

Il dossier:

- consolida in un unico punto la maturità del blocco **Level B offline**;
- distingue chiaramente ciò che è **pronto**, ciò che è **non pronto** e ciò che è
  **escluso per scelta architetturale**;
- non introduce logica runtime;
- non modifica runner federato, retrieval, router, corpus o bridge applicativo;
- non attribuisce al Livello B funzioni decisorie, interpretative o validative.

## 2. Ambito

Il dossier copre esclusivamente il perimetro **offline** del Livello B, includendo:

1. Validation Kit
2. Golden Baseline + Release Gate
3. Runbook Offline
4. Change Control Pack
5. Traceability Bundle
6. Baseline Index Master

## 3. Stato di readiness dichiarato

Lo stato di readiness può assumere solo i seguenti valori:

- `COMPLETE`  
  Il blocco Level B offline risulta completo rispetto ai checkpoint attesi, con
  file chiave presenti, eventuali tag attesi riscontrati e working tree pulito.

- `HOLD`  
  Il blocco non è ancora consolidato o manca almeno una precondizione strutturale.

- `ERROR`  
  Il dossier/registry è invalido o non interpretabile.

## 4. Cosa è pronto

Il blocco Level B offline è considerato **pronto** quando:

- tutti i checkpoint attesi risultano presenti nel registry;
- per ogni checkpoint sono presenti i file chiave minimi;
- il repository è pulito;
- la sequenza dei tag attesi è riscontrabile o comunque dichiarata nel report;
- il perimetro resta confinato all’offline governance stack.

## 5. Cosa non è pronto

Il blocco **non è pronto** quando:

- manca uno dei checkpoint fondativi;
- manca il file chiave di almeno uno dei checkpoint;
- il working tree non è pulito;
- il registry è incoerente o incompleto.

## 6. Cosa resta fuori per scelta architetturale

Restano fuori dal perimetro del presente dossier:

- runner federato;
- runtime applicativo;
- retrieval e routing operativo;
- bridge applicativo verso Layer/Metodo superiore;
- chiusura M07-LPR;
- funzioni decisorie, conclusive o opponibili.

## 7. Precondizioni minime per futuri cantieri pre-runtime

Ogni futuro cantiere pre-runtime deve partire almeno da:

- baseline offline Level B consolidata;
- golden baseline ancora integra;
- release gate e runbook coerenti;
- change control attivo;
- traceability bundle e baseline index aggiornati;
- working tree pulito prima di valutazioni di readiness.

## 8. Regola di non sconfinamento

Il dossier ha sola funzione di:

- ricognizione;
- sintesi;
- tracciabilità;
- readiness assessment offline.

Il dossier non può:

- autorizzare da solo l’ingresso nel runtime;
- sostituire il Metodo Cerda;
- qualificare fatti o norme;
- validare esiti opponibili;
- fondare conclusioni istruttorie.

## 9. Ordine canonico di lettura

1. Validation Kit
2. Golden Baseline + Release Gate
3. Runbook Offline
4. Change Control Pack
5. Traceability Bundle
6. Baseline Index Master
7. Presente Readiness Dossier

## 10. Output atteso

Il runner produce un report con:

- decisione finale (`COMPLETE`, `HOLD`, `ERROR`);
- elenco checkpoint;
- stato file chiave;
- stato tag attesi;
- stato working tree;
- componenti esclusi;
- precondizioni per il passo successivo.
