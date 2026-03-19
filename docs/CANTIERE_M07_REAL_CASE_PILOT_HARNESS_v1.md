
# CANTIERE M07 REAL CASE PILOT HARNESS v1

## 1. Scopo

Questo micro-cantiere introduce un harness locale e controllato per eseguire il modulo
`M07 Documentary Support Adapter` su un piccolo set di casi reali normalizzati,
senza innesto nel runner federato e senza produrre output opponibili.

## 2. Baseline di riferimento

- baseline A/B: `stable-final-ab-master-cycle-v1`
- baseline locale modulo: `stable-m07-documentary-support-acceptance-pack-v1`
- hardening resolver: `stable-m07-documentary-support-resolver-migration-v1`

## 3. Obiettivo operativo

Verificare che il mini-ciclo locale del modulo:
- riceva casi reali del Livello A;
- costruisca request corrette;
- produca documentary packet utile;
- propaghi warning e blocchi attesi;
- resti non decisorio e confinato.

## 4. File del cantiere

- `data/m07_real_case_pilot_cases_v1.json`
- `runtime/m07_real_case_pilot_harness.py`
- `tests/test_m07_real_case_pilot_harness.py`
- `tests/test_m07_real_case_pilot_regression.py`
- `docs/M07_REAL_CASE_PILOT_RESULTS_TEMPLATE_v1.md`

## 5. Guardrail

Il pilot harness:
- opera solo nel Livello A come orchestrazione locale;
- usa solo transport controllato/simulato;
- non tocca il runner federato;
- non chiude M07;
- non costruisce RAC;
- non emette GO/NO_GO;
- non autorizza output opponibili.

## 6. Casi pilota iniziali

1. Art. 107 TUEL - competenze gestionali del responsabile
2. Art. 107 TUEL - citazione incompleta su caso sensibile
3. Atto di indirizzo vs gestione - coverage parziale con warning

## 7. Criterio di accettazione

Il cantiere è accettabile solo se:
- tutti i test del pilot harness sono verdi;
- i blocchi attesi emergono correttamente;
- i casi ordinari producono supporto documentale utile;
- nessun caso abilita semantiche decisorie o autorizzative;
- il runner federato resta intatto.
