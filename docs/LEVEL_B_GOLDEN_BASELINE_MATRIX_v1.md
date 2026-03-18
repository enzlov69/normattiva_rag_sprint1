# LEVEL_B_GOLDEN_BASELINE_MATRIX_v1

## 1. Scopo

Il presente documento definisce il Golden Baseline Pack del Livello B come benchmark regressivo permanente, offline e non negoziabile, da eseguire prima di qualunque futuro innesto pre-runtime.

Il pack non modifica runner, runtime, retrieval, router, corpus o bridge applicativo.

## 2. Decisione raccomandata

La soluzione raccomandata è trattare il Golden Baseline Pack come **presidio separato** rispetto ai test ordinari già esistenti.

È la soluzione corretta perché:
- congela i vincoli fondativi del Livello B;
- evita che refactor locali degradino silenziosamente la non delega;
- consente regressione stabile offline prima di ogni pre-runtime;
- mantiene netta la separazione tra governance documentale, validator offline e futuri innesti applicativi.

## 3. Architettura del pack

Il pack è composto da quattro strati:

1. **Registry congelato**  
   Elenca i golden case, le famiglie fixture, gli invarianti non negoziabili, i criteri di congelamento e gli esiti attesi.

2. **Fixture golden**  
   Payload completi, deterministici e offline-only, separati in famiglie `pass`, `degrade`, `reject`.

3. **Suite pytest dedicata**  
   Legge il registry, carica le fixture, applica controlli invarianti e confronta esiti attesi.

4. **Supporto tecnico opzionale**  
   Helper offline di sola utilità testuale per evitare duplicazioni sporche nei test. Nessuna logica runtime. Nessuna logica decisoria.

## 4. Regola strutturale del pack

Il Golden Baseline Pack:
- resta nel solo perimetro offline del Livello B;
- non integra il runner federato;
- non introduce API nuove;
- non introduce semantica conclusiva;
- non chiude M07-LPR;
- non sostituisce i validator già esistenti, ma li presidia con casi congelati.

## 5. Convenzione tra famiglie fixture e status

La distinzione è la seguente:

- `pass/` = famiglia positiva, con esito atteso `SUCCESS`
- `degrade/` = famiglia support-only, con esito atteso `DEGRADED`
- `reject/` = famiglia negativa non accettante, che può contenere sia `BLOCKED` sia `REJECTED`

Questa convenzione è raccomandata perché evita di moltiplicare directory senza perdere la distinzione semantica fra gli status: la directory rappresenta la **famiglia di benchmark**, mentre lo `expected_status` resta espresso in modo puntuale nel registry.

## 6. Criteri di congelamento della baseline

Un caso entra nel Golden Baseline Pack solo se soddisfa cumulativamente i seguenti criteri:

1. tutela un vincolo fondativo già espresso nella baseline v2;
2. è valutabile offline in modo deterministico;
3. non dipende dal runner, da retrieval live o da servizi runtime;
4. intercetta una regressione ad alto rischio metodologico;
5. espone un esito atteso univoco e verificabile;
6. resta stabile anche in presenza di refactor interni non sostanziali.

## 7. Convenzione di distinzione: golden vs test ordinari

### 7.1 Test ordinari esistenti
I test ordinari restano:
- granulari;
- mirati a schema, semantica, blocchi o contratti specifici;
- più liberi di evolvere con il codice.

### 7.2 Golden case fondativi
I golden case sono invece:
- pochi;
- trasversali;
- interi payload congelati;
- non negoziabili;
- pensati come benchmark regressivo permanente.

### 7.3 Convenzione consigliata
- prefisso case id: `GB-...`
- filename fixture: `gb_<family>_<nnn>_<slug>.json`
- nessun riuso ambiguo di fixture dei test ordinari
- ogni golden case deve essere registrato nel registry prima di entrare in suite

## 8. Matrice dei casi congelati

| Case ID | Famiglia | Status atteso | Invariante fondativo protetto | Fixture |
|---|---|---:|---|---|
| GB-PASS-001 | pass | SUCCESS | payload documentale pulito, audit+shadow presenti, nessuna semantica conclusiva | `pass/gb_pass_001_clean_documentary_support.json` |
| GB-DEGRADE-001 | degrade | DEGRADED | M07 support-only, human completion obbligatoria, nessuna chiusura M07 | `degrade/gb_degrade_001_m07_support_human_completion.json` |
| GB-DEGRADE-002 | degrade | DEGRADED | gap documentale non critico degrada ma non blocca | `degrade/gb_degrade_002_non_critical_coverage_gap.json` |
| GB-BLOCK-001 | reject | BLOCKED | vigenza incerta su punto essenziale blocca | `reject/gb_reject_001_blocked_vigenza_uncertain_essential.json` |
| GB-BLOCK-002 | reject | BLOCKED | audit trail mancante blocca | `reject/gb_reject_002_blocked_audit_missing.json` |
| GB-BLOCK-003 | reject | BLOCKED | SHADOW mancante blocca | `reject/gb_reject_003_blocked_shadow_missing.json` |
| GB-REJECT-001 | reject | REJECTED | divieto assoluto di campo decisorio `final_decision` | `reject/gb_reject_004_forbidden_final_decision.json` |
| GB-REJECT-002 | reject | REJECTED | divieto assoluto di chiusura M07-LPR dal Livello B | `reject/gb_reject_005_forbidden_m07_closed.json` |
| GB-REJECT-003 | reject | REJECTED | divieto di citazione `VALID` senza URI ufficiale | `reject/gb_reject_006_valid_citation_without_uri.json` |
| GB-REJECT-004 | reject | REJECTED | divieto di semantiche conclusive testuali | `reject/gb_reject_007_conclusive_text_semantics.json` |
| GB-REJECT-005 | reject | REJECTED | coerenza obbligatoria tra status, errors e blocks | `reject/gb_reject_008_incoherent_block_propagation.json` |

## 9. Ordine di esecuzione raccomandato

1. validazione strutturale del registry;
2. esistenza e caricamento delle fixture;
3. controlli invarianti raw sulle fixture;
4. esecuzione del validator offline esistente;
5. confronto con gli esiti congelati;
6. fail immediato su ogni difformità fondativa.

## 10. Regole di manutenzione

### 10.1 Regola generale
I golden case non si modificano per inseguire il codice.

### 10.2 Quando è ammesso cambiare la baseline
Solo se cambia la baseline fondativa o contrattuale del progetto e si effettua:
- incremento di versione del registry;
- aggiornamento esplicito della matrice;
- riesame formale dei casi congelati.

### 10.3 Quando non è ammesso
Non è ammesso cambiare un golden case per “far tornare verde” una regressione che segnala uno sconfinamento reale del Livello B.

## 11. Esito operativo

Il Golden Baseline Pack deve essere considerato il **cancello regressivo minimo** del Livello B offline.

Se uno dei golden case fallisce:
- il cantiere non è stabile;
- la baseline offline non è difendibile;
- ogni futuro innesto pre-runtime deve considerarsi sospeso fino a riallineamento.
