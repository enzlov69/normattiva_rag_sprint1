# FINAL AB Runtime Anomaly Severity Propagation Spec v1

## Posizionamento
Questa specifica si colloca dopo:
- runtime hardening acceptance;
- documentary packet traceability/integrity guards.

Obiettivo: definire un canone tecnico unificato per anomalie, severita' e propagazione A<->B nel runtime finale, senza introdurre semantiche decisorie nel Livello B.

## Principio di ruolo
Il Livello B:
- recupera,
- struttura,
- traccia,
- segnala,
- blocca.

Il Livello B non:
- interpreta,
- motiva,
- conclude,
- valida.

La classificazione anomalie e' tecnica, non istruttoria.

## Modello canonico
Ogni anomalia e' descritta da:
- `anomaly_family`
- `severity`
- `signal_class`
- `runtime_effect`
- `envelope_status_effect`
- `propagate_to_level_a`
- `level_a_effect`
- `blocks_opponibility`

## Famiglie obbligatorie
- `CONTRACTUAL`
- `DOCUMENTARY`
- `TRACEABILITY`
- `BOUNDARY`
- `COMPLETENESS`

## Classi di segnale
- `INTERNAL`: segnale tecnico interno, non bloccante e non opponibile.
- `WARNING`: segnale visibile, richiede review ma non stop automatico.
- `ERROR`: degrada affidabilita', comporta almeno output degradato.
- `BLOCK`: incompatibile con opponibilita' piena; comporta blocco o rigetto.

## Canone di severita'
- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

Regole:
1. prevale sempre l'effetto piu' restrittivo;
2. `BOUNDARY` e non-delega prevalgono su eleganza semantica;
3. criticita' documentale essenziale non puo' essere ridotta a warning;
4. supporto documentale a M07 non equivale a chiusura M07.

## Runtime effects canonici
- `INTERNAL_SIGNAL`
- `PROPAGATE_WARNING`
- `PROPAGATE_ERROR`
- `DEGRADE_RESPONSE`
- `BLOCK_RESPONSE`
- `REJECT_RESPONSE`

## Envelope statuses ammessi
- `SUCCESS`
- `SUCCESS_WITH_WARNINGS`
- `DEGRADED`
- `BLOCKED`
- `REJECTED`
- `ERROR`

## Regole minime di consistenza
1. `LOW` non produce `BLOCK_RESPONSE`.
2. `CRITICAL` non puo' restare `INTERNAL`.
3. `BOUNDARY + CRITICAL` porta almeno a `BLOCKED` o `REJECTED`.
4. `DOCUMENTARY` essenziale con severita' `HIGH/CRITICAL` impedisce opponibilita' piena.
5. `TRACEABILITY` critica non puo' essere trattata come cosmetica.
6. `INTERNAL` non puo' avere `blocks_opponibility=true`.

## Propagazione verso Livello A
`level_a_effect` canonico:
- `NONE`
- `REVIEW_REQUIRED`
- `SUPPORT_ONLY`
- `STOP_FLOW`
- `HARD_STOP`

Regole:
- `INTERNAL + LOW` -> nessuna propagazione obbligatoria.
- `WARNING` -> almeno `REVIEW_REQUIRED`.
- `DEGRADE_RESPONSE` -> almeno `SUPPORT_ONLY`.
- `BLOCK_RESPONSE` -> almeno `STOP_FLOW`.
- `REJECT_RESPONSE` -> `HARD_STOP`.
- `RAG_SCOPE_VIOLATION` e `M07_BOUNDARY_VIOLATION` propagano sempre al Livello A.
- anomalie che colpiscono opponibilita' devono risultare tracciabili nell'envelope finale.

## Policy release
- se `default_envelope_status` e' `BLOCKED` o `REJECTED`, `release_allowed=false` salvo eccezione esplicita motivata nel registry.
- ogni eccezione deve avere `notes` non vuote e verificabili via test.
