# CANTIERE M07 DOCUMENTARY SUPPORT ACCEPTANCE PACK v1

## 1. Scopo

Questo pacchetto introduce la suite di accettazione cumulativa del mini-ciclo locale
del modulo "M07 Documentary Support Adapter", sopra i checkpoint già fissati:

- baseline A/B: `stable-final-ab-master-cycle-v1`
- foundation: `stable-m07-documentary-support-foundation-v1`
- runtime adapter: `stable-m07-documentary-support-runtime-adapter-v1`
- module registry: `stable-m07-documentary-support-module-registry-v1`
- orchestrator: `stable-m07-documentary-support-orchestrator-v1`

## 2. Obiettivo

Provare insieme, in una sola suite locale:
- registry del modulo;
- orchestrazione A→B→A;
- propagazione blocchi;
- presidio M07Required;
- non-delegabilità;
- assenza di impatto sul runner federato.

## 3. Perimetro

### Incluso
- test di successo del mini-ciclo completo
- test di propagazione blocchi
- test di blocco per assenza M07EvidencePack
- test di non-delegabilità
- test di caller non autorizzato
- test di blocco di semantiche conclusive

### Escluso
- nessun innesto nel runner federato
- nessuna modifica del core A/B
- nessuna decisione finale
- nessuna chiusura M07
- nessuna costruzione RAC
- nessuna autorizzazione output opponibile

## 4. Criterio di accettazione

Il pacchetto è accettabile solo se:
- tutti i test della suite sono verdi;
- il runner federato resta non toccato;
- i flag di non-delegabilità restano sempre negativi;
- i blocchi del Livello B si propagano correttamente;
- il modulo resta confinato nel solo Livello A come orchestrazione locale.