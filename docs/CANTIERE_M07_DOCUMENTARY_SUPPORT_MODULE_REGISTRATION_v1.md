# CANTIERE M07 DOCUMENTARY SUPPORT MODULE REGISTRATION v1

## 1. Scopo

Questo pacchetto introduce la registrazione controllata del modulo
`M07 Documentary Support Adapter` nel solo Livello A, sopra la baseline congelata:

- baseline A/B: `stable-final-ab-master-cycle-v1`
- fondazione cantiere: `stable-m07-documentary-support-foundation-v1`
- runtime adapter: `stable-m07-documentary-support-runtime-adapter-v1`

La registrazione è locale, additiva e non distruttiva.

## 2. Obiettivo

Consentire al Livello A di:
- riconoscere formalmente il modulo;
- risolvere il modulo in modo controllato;
- conservarne metadati, perimetro e guardrail;
- impedirne l’uso come decisore o validatore.

## 3. Perimetro

### Incluso
- registry locale del modulo
- schema del registry
- funzioni di lookup e dispatch controllato
- test di conformità e policy

### Escluso
- nessun aggancio al runner federato
- nessuna modifica del core A/B
- nessuna modifica di retrieval/router/ranking
- nessuna autorizzazione automatica dell’output
- nessuna chiusura M07

## 4. Regole di governo

Il modulo registrato:
- resta nel Livello A
- ha `dispatch_mode = MANUAL_LEVEL_A_ONLY`
- punta al target `B16_M07SupportLayer`
- è support-only
- richiede completamento umano
- non può chiudere M07
- non può costruire RAC
- non può emettere GO/NO_GO
- non può autorizzare output opponibili
- non può modificare il runner federato

## 5. Guardrail obbligatori

- `NO_DECISION`
- `NO_GO_NO_GO`
- `NO_M07_CLOSE`
- `NO_OUTPUT_AUTH`
- `NO_RAC_BUILD`
- `BOUNDARY_ENFORCED`
- `BLOCK_PROPAGATION_REQUIRED`

## 6. Criterio di accettazione

Il pacchetto è accettabile solo se:
- il registry è conforme allo schema;
- il modulo è risolvibile solo da caller autorizzati;
- il dispatch non abilita semantiche conclusive;
- il runner federato resta non toccato.