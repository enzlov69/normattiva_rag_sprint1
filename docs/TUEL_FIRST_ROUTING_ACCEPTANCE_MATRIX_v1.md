# TUEL First Routing Acceptance Matrix v1

## Status

This document is a governance and validation artifact only.

It does not introduce production logic, does not modify query packs, does not alter the federated runner, and does not create executable tests.

Its purpose is to translate `TUEL_FIRST_ROUTING_SPEC_v1.md` into an operational acceptance matrix for future controlled validation.

## Acceptance Matrix

| # | Use case | Routing bucket | TUEL first role | Primary follow-up corpus | Optional secondary corpus | Expected answer shape | Pass/fail condition |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `Quando serve il parere ex art. 49 TUEL per una proposta di delibera?` | `governance/competence` | Identify municipal act context, internal control surface, and whether the matter is framed as a deliberative proposal requiring municipal pareri | None | `none` | Answer anchored in TUEL, stating when the municipal proposal requires the TUEL parere frame and who is involved in the local decision path | `PASS` only if TUEL remains the main corpus and the answer is not rerouted to a specialist corpus without necessity |
| 2 | `Per questa decisione è competente il consiglio o la giunta comunale?` | `governance/competence` | Identify the organo competente and the deliberative placement of the act inside municipal governance | None | `none` | Answer centered on TUEL allocation of competence, explicitly identifying which organ is competent and why in municipal terms | `PASS` only if the answer resolves the competence question through TUEL-first analysis and does not drift into unrelated specialist doctrine |
| 3 | `Annullamento d'ufficio di un provvedimento comunale: chi lo avvia e con quali limiti?` | `procedure` | Identify the municipal provvedimento context, the local authority frame, and the initiating office/organ side | `L. 241/1990` | `none` | Answer with TUEL municipal framing first, then L. 241/1990 for annullamento d'ufficio limits, conditions, and procedural constraints | `PASS` only if TUEL frames the municipal context and L. 241/1990 supplies the procedural rule; `FAIL` if TUEL is skipped or the case is treated as pure generic procedure |
| 4 | `Accesso agli atti di un procedimento amministrativo del comune` | `procedure` | Identify the municipal office/procedural context and whether the request concerns ordinary administrative access | `L. 241/1990` | `none` | Answer with TUEL framing of the local administrative context, then L. 241/1990 for access rights, limits, and procedural handling | `PASS` only if the answer distinguishes municipal context from general access doctrine and routes primarily to L. 241/1990 after TUEL orientation |
| 5 | `Il comune deve pubblicare questo atto o documento ai fini della trasparenza?` | `transparency` | Identify the municipal act, office, or publication context before assessing publication duties | `D.Lgs. 33/2013` | `none` | Answer with TUEL framing of the municipal act and D.Lgs. 33/2013 for the transparency/publication obligation | `PASS` only if TUEL identifies the municipal context and D.Lgs. 33/2013 is used as the primary transparency source |
| 6 | `Obblighi di pubblicazione per bandi di concorso del comune` | `transparency` | Identify that the issue concerns a municipal concorso and place it in the local authority publication context | `D.Lgs. 33/2013` | `D.Lgs. 165/2001` | Answer with TUEL municipal framing, D.Lgs. 33/2013 for publication duties, and D.Lgs. 165/2001 only if needed to qualify the personnel/concorsuale side | `PASS` only if D.Lgs. 33/2013 remains primary and D.Lgs. 165/2001 is added only when strictly needed |
| 7 | `Affidamento diretto sotto soglia da parte del comune` | `procurement` | Identify the municipal contracting frame, local act context, and public procurement setting inside the comune | `D.Lgs. 36/2023` | `none` | Answer with TUEL orientation of the municipal procurement context and D.Lgs. 36/2023 for the substantive procurement rule | `PASS` only if the case is routed TUEL-first and then primarily to D.Lgs. 36/2023; `FAIL` if procurement is answered without the municipal frame |
| 8 | `Accesso agli atti di gara del comune` | `procurement` | Identify the municipal procurement context and whether the request concerns access within a tender procedure | `D.Lgs. 36/2023` | `L. 241/1990` | Answer with TUEL first, D.Lgs. 36/2023 as the main procurement corpus, and L. 241/1990 only if needed to complete the procedural-access side | `PASS` only if D.Lgs. 36/2023 is primary and L. 241/1990 appears only as a secondary support when necessary |
| 9 | `Chi è competente per l'ufficio procedimenti disciplinari nel comune?` | `personnel/discipline` | Identify the local institutional frame and separate municipal governance context from management/disciplinary structure | `D.Lgs. 165/2001` | `none` | Answer with TUEL orientation of the municipal setting and D.Lgs. 165/2001 for UPD competence and disciplinary structure | `PASS` only if D.Lgs. 165/2001 is the primary follow-up corpus and TUEL is used to frame the municipal context first |
| 10 | `Rapporto tra indirizzo politico e gestione dei dirigenti nel comune` | `personnel/discipline` | Identify the local government frame and the boundary between political direction and management in the municipality | `D.Lgs. 165/2001` | `none` | Answer with TUEL framing of local institutional actors and D.Lgs. 165/2001 for the substantive rule on political-management separation | `PASS` only if the answer clearly distinguishes municipal institutional framing from the specialist personnel rule and routes primarily to D.Lgs. 165/2001 |
| 11 | `Debiti fuori bilancio del comune e necessità del parere del revisore` | `accounting/budget` | Identify the municipal accounting/governance context, organ path, and local control surface including revisore involvement | `D.Lgs. 118/2011` | `D.Lgs. 126/2014` | Answer with TUEL first for the municipal governance/control frame, D.Lgs. 118/2011 for the accounting rule, and D.Lgs. 126/2014 only if needed to complete the harmonization/reform support side | `PASS` only if D.Lgs. 118/2011 remains primary and D.Lgs. 126/2014 is used only where indispensable |
| 12 | `Riaccertamento ordinario dei residui e reimputazione nel bilancio comunale` | `accounting/budget` | Identify the municipal bilancio context and the local accounting/control frame before specialist treatment | `D.Lgs. 118/2011` | `D.Lgs. 126/2014` | Answer with TUEL framing of the municipal accounting context and D.Lgs. 118/2011 for riaccertamento/reimputazione doctrine, with D.Lgs. 126/2014 only if strictly needed | `PASS` only if the case is framed municipally through TUEL and then routed primarily to D.Lgs. 118/2011 without unnecessary multi-corpus spread |

## Validation Rules For Future Testing

The following rules apply to any future manual or automated validation built from this matrix.

1. Each use case must be classified into exactly one of the seven routing buckets.
2. TUEL must be the first routing and orientation layer in every municipal use case listed here.
3. Each use case must identify exactly one primary follow-up corpus, except pure `governance/competence` cases where TUEL may remain sufficient.
4. A secondary corpus is allowed only when this matrix explicitly permits it and only when the answer would otherwise be materially incomplete.
5. Future tests must verify answer shape, not just retrieval presence:
   - municipal framing from TUEL
   - specialist rule from the designated primary corpus
   - limited and justified use of any secondary corpus
6. A case fails if routing jumps directly to a specialist corpus without TUEL orientation.
7. A case fails if more than one specialist corpus is treated as primary.
8. A case fails if a secondary corpus is used where this matrix says `none`.
9. A case fails if the response does not identify the municipal frame:
   - organo competente
   - act or control context
   - local-government setting
10. This matrix is a governance acceptance baseline for future TUEL-first validation work and must not be treated as implemented production routing.

## Coverage Note

This v1 matrix validates 6 of the 7 routing buckets through concrete use cases.

The `mixed municipal case` bucket is intentionally not yet represented by a dedicated acceptance case.

A future v1.1 matrix should introduce at least one explicit composite municipal case for that bucket.
