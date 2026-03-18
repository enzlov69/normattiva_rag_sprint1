# FINAL AB Runtime Anomaly Governance Lock Spec v1

## Posizionamento
Questa specifica e' un'estensione additiva della Fase 8 (registry + severity canon + propagation matrix).

## Scopo
Definire un presidio offline, deterministico e auditabile che verifichi la coerenza tra:
- anomaly registry;
- severity canon;
- propagation matrix;
- golden cases.

Il validator offline:
- non modifica runtime,
- non modifica envelope,
- non decide esiti amministrativi,
- non interpreta norme.

## Fonte di verita'
I file autoritativi sono:
- `schemas/final_ab_runtime_anomaly_registry_v1.json`
- `schemas/final_ab_runtime_severity_canon_v1.json`
- `schemas/final_ab_runtime_propagation_matrix_v1.json`
- `data/final_ab_runtime_golden_cases_v1.json`

## Tipi di non conformita'
- validation error strutturale (file/campi mancanti, JSON non valido)
- semantic inconsistency (valori non canonici, regole violate)
- uncovered mapping (trajectory registry->matrix irrisolvibile)
- forbidden downgrade (boundary/documentary/traceability critical attenuati)
- missing mandatory anomaly coverage (codici obbligatori assenti)

## Regole di lock
Il validator deve fallire almeno in presenza di:
1. duplicate `anomaly_code`;
2. codice obbligatorio mancante;
3. severity/signal/runtime/status non definiti nel canon;
4. combinazione `family+severity+signal_class` non coperta dalla matrix;
5. `blocks_opponibility=true` con `signal_class=INTERNAL`;
6. `BOUNDARY + CRITICAL` non bloccante/reject;
7. `DOCUMENTARY` o `TRACEABILITY` critical trattata come warning cosmetico;
8. mismatch tra golden cases e registry/canon/matrix.

## Output validator
Output tecnico deterministico con:
- `summary`
- `passed_checks`
- `failed_checks`
- `warnings`
- `coverage_stats`
- `exit_status`

Entry point stabile:
- `python tools/final_ab_runtime_anomaly_validator.py`

## M07 e non-delega
Il lock conferma solo coerenza tecnica, opponibilita' tecnica e propagazione.
Supporto documentale a M07 non equivale a chiusura M07.
Il Livello B resta non decisorio e subordinato al Metodo Cerda.
