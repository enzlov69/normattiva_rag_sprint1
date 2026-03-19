# FINAL_AB_BASELINE_TAG_REGISTRY_v1

| Fase o milestone | Tag | Commit | Significato della baseline | Note |
| --- | --- | --- | --- | --- |
| Fase 10 consolidata | `stable-final-ab-controlled-handoff-v1` | `6222752` | Chiusura del perimetro contrattuale A/B pre-runtime con boundary M07, forbidden fields e documentary packet minimo | Baseline contrattuale prima del runtime controlled handoff |
| Fase 11 consolidata | `stable-final-ab-runtime-controlled-handoff-v2` | `10cba22` | Primo runtime controlled handoff A->B->runner->B->A con registri runtime e collaudo end-to-end | Runner resta black-box e non decisorio |
| Fase 12 consolidata | `stable-final-ab-level-a-intake-gate-v1` | `7efaf58` | Intake gate lato Livello A con response consumption policy, quarantine e sensitive module protection | Supporto documentale classificato e non decisorio |
| Fase 13 consolidata | `stable-final-ab-consumption-audit-v1` | `b42ad63` | Consumption audit trail e decision isolation log del Livello A | Tracciabilita' ex post del consumo e isolamento dei moduli sensibili |
| Fase 14 consolidata | `stable-final-ab-manual-review-gate-v1` | `bbabc4f` | Manual review gate e final human approval trace | Approvazione umana finale resta distinta dal supporto documentale |
| Fase 15 consolidata | `stable-final-ab-release-certification-v1` | `ed0a8af` | Release certification pack, acceptance dossier, unified compliance matrix, readiness e non-delegability finali | Chiusura tecnica/documentale del ciclo A/B senza estensione funzionale |

## Regola interpretativa

Questo registry elenca baseline di congelamento tecnico-documentale del percorso A/B.

I tag elencati sopra sono le baseline finali realmente utili e raccomandate del ciclo 10-15.
Eventuali tag precedenti non presenti in questa tabella devono essere trattati come storici o intermedi e non come baseline finali raccomandate.

Non attribuisce approvazione amministrativa.
Non sostituisce Final Compliance Gate, Output Authorizer o approvazione umana finale.
