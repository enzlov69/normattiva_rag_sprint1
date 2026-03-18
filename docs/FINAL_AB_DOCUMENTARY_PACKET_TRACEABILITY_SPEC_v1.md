# FINAL AB Documentary Packet Traceability Spec v1

## Scopo
Rafforzare il controllo finale documentale nel solo `FinalABResponseEnvelopeGate`, verificando coerenza e tracciabilita' del `DocumentaryPacket` senza introdurre logica decisoria nel Livello B.

## Perimetro
- unico punto di controllo: post-mapper response-envelope gate
- nessuna modifica a handoff service, runner black-box, raw validator
- nessuna variazione di ordine pipeline

## Requisiti minimi di coerenza documentale
Il controllo finale verifica:
1. tracciabilita' minima delle `citations_valid`;
2. coerenza di copertura tra citations, `sources` e `norm_units`;
3. coerenza tra dichiarazioni di copertura documentale (`coverage_assessment`) e disponibilita' delle fonti;
4. coerenza `trace_id` tra envelope finale, audit e shadow (se presenti);
5. assenza di incoerenze materiali che rendano non opponibile il pacchetto documentale finale.

## Classificazione anomalie
### Bloccanti
- `CITATION_INCOMPLETE`: citation non tracciabile o priva di copertura minima.
- `CROSSREF_UNRESOLVED`: link citation->sources / citation->norm_units non tracciabile.
- `SOURCE_UNVERIFIED`: copertura dichiarata adeguata senza fonti documentali utili.
- `AUDIT_INCOMPLETE`: mismatch di tracciabilita' tra trace envelope e audit/shadow.

Queste anomalie non possono chiudere in `SUCCESS`.

### Warning / completezza debole
- `SOURCES_WEAK_TRACEABILITY`
- `NORM_UNITS_WEAK_TRACEABILITY`
- `DOCUMENTARY_COMPLETENESS_WARNING`

Queste anomalie non introducono decisione normativa: segnalano solo qualita' e completezza del tracciato documentale.

## Compatibilita' e limiti
- payload minimali non conclusivi restano ammessi se coerenti.
- nessuna interpretazione normativa o scelta applicativa.
- M07 resta fuori ambito decisionale: il gate controlla solo coerenza documentale/tracciabile.
- il Livello B resta subordinato al Metodo Cerda: recupera, struttura, traccia, segnala, blocca.

## Accettazione tecnica
I controlli sono verificati da:
- `tests/test_final_ab_documentary_packet_traceability.py`
- `tests/test_final_ab_documentary_packet_integrity_guards.py`

e dalla suite regressiva completa della Fase 6.
