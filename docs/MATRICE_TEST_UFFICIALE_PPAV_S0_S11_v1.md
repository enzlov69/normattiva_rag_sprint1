# MATRICE TEST UFFICIALE PPAV S0–S11 v1

## 1. Titolo e funzione del documento

Il presente documento formalizza la **Matrice Test Ufficiale S0–S11** del Metodo Cerda – PPAV 2.2.

La matrice ha funzione di:
- trasformare la sequenza metodologica da descrittiva a testabile;
- rendere ogni fase bloccabile, tracciabile e verificabile nel repo;
- vincolare l’ordine canonico del Metodo;
- collegare documentazione, registry, runtime minimale e test ROOT;
- impedire ogni uso improprio del Livello B come livello decisorio o validativo.

Il presente documento ha natura:
- metodologica;
- documentale;
- di test coverage;
- additiva e locale rispetto alla baseline attiva.

Non modifica:
- il fondativo v2;
- la separazione Livello A / Livello B;
- il runner federato;
- retrieval / router / ranking / corpus.

---

## 2. Baseline di riferimento del cantiere

Baseline operative richiamate:
- baseline A/B: `stable-final-ab-master-cycle-v1`
- baseline locale M07: `stable-m07-documentary-support-acceptance-pack-v1`
- baseline locale FIP-IND: `stable-fip-ind-gate-foundation-v1`

---

## 3. Principi vincolanti della matrice

### 3.1 Ordine canonico vincolante
L’ordine delle fasi da assumere come vincolante è il seguente:

1. S-PRE/D
2. S-PRE/F
3. S0 – FASE 0
4. S0-bis – FASE 0-bis
5. S0-ter – FASE 0-ter
6. S1 – FIP-IND
7. S2 – RAP-ATTI
8. S3 – M07-LPR
9. S4 – RAC
10. S5 – LAYER
11. S6 – MODULI PPAV
12. S7 – CS-PPAV
13. S8 – SCM-PRO
14. S9 – CRITIC v4
15. S10 – CF-ATTI
16. S11 – OUTPUT

### 3.2 Regola di sequenza
Se una fase non è valida o non è completata, la fase successiva **non può produrre un esito utile opponibile**.

### 3.3 Regola di blocco
Ogni blocco impeditivo deve:
- essere tracciato;
- essere propagato;
- impedire il passaggio utile alla fase successiva;
- impedire, ove rilevante, la produzione di FIRMA-READY.

### 3.4 Regola di non delega
Il Livello B:
- può supportare documentalmente;
- non può decidere;
- non può validare;
- non può emettere GO/NO-GO;
- non può chiudere M07;
- non può costruire da solo RAC opponibile;
- non può autorizzare output opponibili;
- non può sostituire i gate del Livello A.

### 3.5 Presìdi trasversali sempre attivi
Sono sempre attivi:
- `OP_ANTI_ALLUCINAZIONI_NORMATIVE`
- `OP_DOPPIA_LENTE_RATIO`
- `OP_COT++`

`OP_COT++` può riepilogare esiti e tracce, ma **non sostituisce alcun gate**.

### 3.6 Regola ROOT
Ogni fase e ogni transizione critica devono avere test nel `ROOT/tests` del sistema.

---

## 4. Classi ufficiali di test

Le classi ufficiali di test da usare nella coverage map e nei test ROOT sono:

- `UNIT` = test unitario di fase
- `TRN` = test di transizione tra fasi adiacenti
- `E2E` = test cumulativo end-to-end
- `BLK` = test di blocco/gate
- `ND` = test di non-delegabilità
- `LB` = test di subordinazione del Livello B
- `REP` = test di copertura documentale / schema / runtime / repo

---

## 5. Colonne ufficiali della matrice

Le colonne obbligatorie della Matrice Test Ufficiale sono:

- fase
- funzione
- precondizione
- input minimo
- azione attesa
- esito positivo
- esito negativo
- blocco atteso
- fase successiva ammessa o vietata
- tipo di test richiesto
- file/schema/runtime da presidiare
- priorità di implementazione

---

## 6. Matrice ufficiale S-PRE/D, S-PRE/F, S0–S11

| Fase | Funzione | Precondizione | Input minimo | Azione attesa | Esito positivo | Esito negativo | Blocco atteso | Fase successiva ammessa o vietata | Tipo di test richiesto | File/schema/runtime da presidiare | Priorità |
|---|---|---|---|---|---|---|---|---|---|---|---|
| S-PRE/D | Apertura sessione e verifica integrità del sistema | Baseline attiva disponibile; registry leggibili; presìdi trasversali caricabili | `case_id` o contesto sessione; registry sequenza; registry gate | Verificare disponibilità catena, integrità registry, readiness iniziale | `READY` | `NOT_READY` | `SESSION_NOT_READY` | Ammessa solo S-PRE/F; vietate tutte le altre fasi | UNIT, BLK, REP | `docs/MATRICE_TEST_UFFICIALE_PPAV_S0_S11_v1.md`; `schemas/ppav_phase_sequence_registry_v1.json`; `schemas/ppav_phase_gate_registry_v1.json`; `tests/test_ppav_phase_order_matrix.py` | P0 |
| S-PRE/F | Verifica del singolo modulo/fase prima dell’esecuzione | S-PRE/D = READY | identificativo fase; metadati fase; prerequisiti locali | Verificare readiness della fase specifica | `PHASE_READY` | `PHASE_NOT_READY` | `PHASE_PRECHECK_FAILED` | Ammessa solo la fase richiesta se ready; vietato ogni esito utile della fase se non ready | UNIT, TRN, BLK, REP | `schemas/ppav_phase_gate_registry_v1.json`; `tests/test_ppav_phase_transition_matrix.py` | P0 |
| S0 – FASE 0 | Classificazione del tipo di output e dell’intensità applicativa | S-PRE/F su S0 = PHASE_READY | natura output; bisogno istruttorio/redazionale; materia preliminare; sensibilità iniziale | Classificare output e assegnare intensità | output classificato + intensità `ESSENZIALE/STANDARD/RAFFORZATA` | classificazione assente o incoerente | `CLASSIFICATION_REQUIRED` | Ammessa S0-bis; vietata ogni fase utile successiva senza classificazione | UNIT, TRN, E2E | runtime/classifier esistente; `tests/test_fase0_classifier.py`; coverage map | P0 |
| S0-bis – FASE 0-bis | Verifica presìdi trasversali di compliance | S0 valido | output S0; rischio iniziale; zone rosse; fast-track; presìdi trasversali | Attivare o attestare i presìdi rilevanti | `OK` oppure `NESSUNA_INCIDENZA` | presidio critico non assolto | `TRANSVERSAL_COMPLIANCE_BLOCK` | Ammessa S0-ter; vietata prosecuzione utile con presidio critico aperto | UNIT, TRN, BLK, E2E | runtime compliance gate esistente; `tests/test_fase0bis_compliance_gate.py`; registry gate | P0 |
| S0-ter – FASE 0-ter | Attivazione normativa settoriale e regolamenti comunali | S0-bis non bloccato | output S0/S0-bis; materia prevalente; regolamenti locali; procedure settoriali | Individuare normativa speciale, regolamenti e procedure obbligatorie | `OK` con attivazioni tracciate | normativa/regolamenti obbligatori non agganciati | `SECTORAL_NORMATIVE_BLOCK` | Ammessa S1; vietata prosecuzione utile senza attivazione normativa necessaria | UNIT, TRN, BLK, E2E | runtime normative gate esistente; `tests/test_fase0ter_normative_gate.py` | P0 |
| S1 – FIP-IND | Distinzione tra indirizzo politico e provvedimento gestionale | S0-ter valido | tipologia atto; effetti su terzi; contenuto dispositivo; allocazione competenze | Qualificare il regime di indirizzo/provvedimento | `INDIRIZZO_PURO`, `INDIRIZZO_CON_RISCHI`, `PROVVEDIMENTO_GESTIONALE` | `FALSO_INDIRIZZO` o incertezza bloccante | `FIP_IND_FALSE_INDIRIZZO_BLOCK` | Ammessa S2 solo se non `FALSO_INDIRIZZO`; vietata prosecuzione utile in caso di falso indirizzo | UNIT, TRN, BLK, ND | runtime FIP-IND esistente; `tests/test_fip_ind_gate.py` | P0 |
| S2 – RAP-ATTI | Integrità, tracciabilità e DB-LOCK dei dati essenziali | S1 non bloccato | dati essenziali atto; identificativi; stato bozza; campi bloccabili | Verificare completezza minima e attivare DB-LOCK | `DB_LOCK_OK` + stato `BOZZA` / `PRE_FIRMA` / `FIRMA_READY_TECHNICAL_ONLY` | dato essenziale mancante o lock assente | `RAP_ATTI_DB_LOCK_BLOCK` | Ammessa S3 solo con dati essenziali completi; vietata qualsiasi pretesa opponibile | UNIT, TRN, BLK, REP | `runtime/ppav_phase_chain.py` o `runtime/rap_atti_gate.py`; `tests/test_rap_atti_gate.py` | P0 |
| S3 – M07-LPR | Lettura rigo per rigo della fonte normativa | S2 valido; perimetro normativo disponibile | fonti; segmenti; rinvii; allegati; traccia lettura; ultimo comma | Verificare completamento governato della lettura integrale | `COMPLETO` | `INCOMPLETO` | `M07_INCOMPLETE_BLOCK` | Ammessa S4 solo se `COMPLETO`; vietata qualunque utilità opponibile se `INCOMPLETO` | UNIT, TRN, BLK, ND, LB | baseline M07 locale; registry gate; test M07 locali/ROOT | P0 |
| S4 – RAC | Traduzione della norma in Report Applicativo Comunale | S3 = `COMPLETO` | esiti M07; quadro fonti; competenza comunale; atti da adottare; adempimenti; prove | Costruire RAC governato dal Livello A | `OK` | `BLOCCO` | `RAC_BLOCK` | Ammessa S5 solo con RAC valido; vietata qualificazione opponibile senza RAC utile | UNIT, TRN, BLK, ND | `runtime/rac_gate.py`; `tests/test_rac_gate.py` | P0 |
| S5 – LAYER | Qualifica del regime dell’output e opponibilità | S4 = `OK` | esito RAC; prove documentali; DB-LOCK; blocchi aperti; eventuale `AAN_BLOCK_OPEN` | Decidere regime L-AR / L-PR / L-ML e opponibilità | `OPPONIBILE` oppure degradazione controllata | `NON_OPPONIBILE` | `OUTPUT_NOT_OPPONIBILE_BLOCK` | Ammessa S6 con regime definito; vietato S11 FIRMA-READY se `NON_OPPONIBILE` | UNIT, TRN, BLK, REP | `runtime/layer_gate.py`; `tests/test_ppav_layer_gate.py` | P0 |
| S6 – MODULI PPAV | Attivazione moduli M01–M06 + PM in base a materia e rischio | S5 definito | materia; intensità; rischio; zone rosse; esiti precedenti | Attivare i moduli pertinenti e i controlli obbligatori | `MODULES_OK` | input insufficienti o controlli obbligatori mancanti | `PPAV_MODULE_ACTIVATION_BLOCK` | Ammessa S7 solo con attivazioni minime coerenti; vietata prosecuzione stabile senza moduli necessari | UNIT, TRN, BLK | `runtime/ppav_module_activation.py`; `tests/test_ppav_module_activation.py` | P1 |
| S7 – CS-PPAV | Controllo di stabilità complessiva | S6 valido | esiti moduli; blocchi residui; stabilità normativa/istruttoria/contabile/motivazionale | Classificare stabilità complessiva | `VERDE` oppure `GIALLO` governato | `ROSSO` | `CS_PPAV_RED_BLOCK` | Ammessa S8 con `VERDE`; con `GIALLO` solo in traccia governata; vietata prosecuzione firma-ready con `ROSSO` | UNIT, TRN, BLK | `runtime/cs_ppav_gate.py`; `tests/test_cs_ppav_gate.py` | P1 |
| S8 – SCM-PRO | Controlli manuali obbligatori pre-firma | S7 non rosso | checklist controlli manuali; prove; verifiche umane | Registrare esito sintetico pre-firma | `GO` oppure `GO_CON_RISERVA` | `NO_GO` | `SCM_PRO_NO_GO_BLOCK` | Ammessa S9 con `GO` o riserva tracciata; vietata prosecuzione utile con `NO_GO` | UNIT, TRN, BLK | `runtime/scm_pro_gate.py`; `tests/test_scm_pro_gate.py` | P1 |
| S9 – CRITIC v4 | Stress test di legittimità e tenuta difensiva | S8 non `NO_GO` | atto; motivazione; criticità residue; profilo difensivo | Restituire esito di stress test | `OK` oppure `ATTENZIONE` governata | `CRITICO` | `CRITIC_V4_BLOCK` | Ammessa S10 solo se non `CRITICO`; vietato produrre GO utile se `CRITICO` | UNIT, TRN, BLK, ND | `runtime/critic_v4_gate.py`; `tests/test_critic_v4_gate.py` | P0 |
| S10 – CF-ATTI | Gate finale pre-firma | S9 non critico | esiti S0–S9; audit; shadow; blocchi aperti; opponibilità | Emettere il gate finale del Livello A | `GO` | `NO_GO` | `CF_ATTI_NO_GO_BLOCK` | Ammessa S11 solo con `GO`; vietata qualsiasi dichiarazione FIRMA-READY con `NO_GO` | UNIT, TRN, BLK | `runtime/cf_atti_gate.py`; `tests/test_cf_atti_gate.py` | P0 |
| S11 – OUTPUT | Produzione output finale a doppio layer | S10 = `GO` | atto; shadow; regime LAYER; audit completo | Produrre `LAYER_ATTO` + `LAYER_SHADOW` | output completo; `FIRMA_READY = true` solo se tutti i gate sono superati | output incompleto o firma-ready abusivo | `OUTPUT_FINAL_BLOCK` | Ammessa solo chiusura flusso; vietata emissione FIRMA-READY se un gate precedente è negativo o incompleto | E2E, BLK, ND, LB, REP | `runtime/output_gate.py`; `tests/test_ppav_end_to_end_official_flow.py`; `tests/test_ppav_output_firma_ready_rules.py` | P0 |

---

## 7. Regole minime di blocco da considerare vincolanti

1. Nessun salto di fase.
   Regola secca: nessun salto di fase è consentito.

2. nessuna produzione `FIRMA_READY` prima di `S10 = GO`.

3. Nessuna fase successiva utile se la precedente è bloccata.

4. `S3 = INCOMPLETO` impedisce a `S4` di produrre RAC valido.

5. `S5 = NON_OPPONIBILE` impedisce a `S11` di produrre `LAYER_ATTO` FIRMA-READY.

6. `S9 = CRITICO` impedisce a `S10` di produrre `GO`.

7. `S10 = NO_GO` impedisce a `S11` di produrre testo FIRMA-READY.

8. Il Livello B non può svolgere funzioni decisorie o validative.

9. Tutte le regole devono essere testate nel `ROOT/tests`.

10. Ogni divergenza tra documento, schema, runtime e test equivale a cantiere non chiuso.

---

## 8. Deliverable tecnici minimi collegati alla matrice

### Documenti
- `docs/MATRICE_TEST_UFFICIALE_PPAV_S0_S11_v1.md`
- `docs/PPAV_TEST_COVERAGE_MAP_v1.md`

### Schemi
- `schemas/ppav_phase_sequence_registry_v1.json`
- `schemas/ppav_phase_gate_registry_v1.json`

### Runtime minimale, solo se necessario
- `runtime/ppav_phase_chain.py`

### Test ROOT minimi
- `tests/test_ppav_phase_order_matrix.py`
- `tests/test_ppav_phase_transition_matrix.py`
- `tests/test_ppav_gate_block_propagation.py`
- `tests/test_ppav_non_delegability_matrix.py`
- `tests/test_ppav_level_b_subordination.py`
- `tests/test_ppav_end_to_end_official_flow.py`
- `tests/test_ppav_repo_coverage_integrity.py`
- `tests/test_ppav_output_firma_ready_rules.py`

---

## 9. Clausola finale di uso

La presente matrice serve a trasformare il Metodo Cerda – PPAV 2.2 da sequenza descrittiva a sequenza:
- verificabile;
- bloccabile;
- certificabile;
- coerente tra metodo, documenti, runtime e test.

La matrice:
- non altera il fondativo v2;
- non riapre il Livello B;
- non riapre retrieval/router/ranking/corpus;
- non tocca il runner federato salvo necessità eccezionale non richiesta in questo cantiere.