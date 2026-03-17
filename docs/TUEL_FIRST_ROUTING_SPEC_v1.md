# TUEL First Routing Spec v1

## Status

This document is a governance and design artifact only.

It does not introduce production logic, does not modify the federated runner, does not change any query pack, and does not alter retrieval behavior.

## Purpose

The TUEL-first routing layer defines how municipal legal requests should enter the system.

Operational principle:

1. TUEL is the first routing and orientation layer for municipal use cases.
2. TUEL identifies the local-government frame of the question:
   - organo competente
   - funzione amministrativa coinvolta
   - tipo di atto o controllo
   - bisogno di instradamento specialistico
3. After TUEL orientation, the request may be routed to one stabilized specialist corpus.
4. A secondary corpus is used only when strictly necessary for a real composite municipal case.

The objective is not to replace specialist corpora with TUEL.

The objective is to make TUEL the municipal entry surface that determines where the question belongs before specialist retrieval is applied.

## Routing Buckets

Only the following seven routing buckets are allowed in v1:

1. `governance/competence`
2. `procedure`
3. `transparency`
4. `procurement`
5. `personnel/discipline`
6. `accounting/budget`
7. `mixed municipal case`

## Routing Matrix

All buckets start from TUEL first.

| Bucket | TUEL first role | Primary follow-up corpus | Optional secondary corpus |
| --- | --- | --- | --- |
| `governance/competence` | Identify municipal organ, act type, deliberative path, internal control surface | None in standard cases | `D.Lgs. 118/2011` only if the competence issue is inseparable from accounting governance |
| `procedure` | Place the administrative issue in the municipal frame and identify the office/organ/procedural context | `L. 241/1990` | `D.Lgs. 36/2023` only when the procedure is specifically a procurement procedure |
| `transparency` | Identify the municipal act, office, or publication context | `D.Lgs. 33/2013` | `D.Lgs. 165/2001` only when the transparency issue directly concerns personnel or concorsi |
| `procurement` | Identify the municipal contracting frame and the local act/organ context | `D.Lgs. 36/2023` | `L. 241/1990` only when access or procedural guarantees must be answered together with procurement rules |
| `personnel/discipline` | Distinguish local political/governance surface from management and disciplinary structure | `D.Lgs. 165/2001` | `D.Lgs. 33/2013` only when personnel issues also require publication or transparency duties |
| `accounting/budget` | Identify the municipal budgeting/control frame and the local authority step | `D.Lgs. 118/2011` | `D.Lgs. 126/2014` only when reform/support rules are strictly needed to complete the answer |
| `mixed municipal case` | Identify the dominant municipal frame first and determine whether the case is truly cross-corpus | One dominant primary corpus chosen among `L. 241/1990`, `D.Lgs. 33/2013`, `D.Lgs. 36/2023`, `D.Lgs. 165/2001`, `D.Lgs. 118/2011` | One secondary corpus only if the answer is incomplete without it |

## Bucket Guidance

### `governance/competence`

Use when the user is primarily asking:

- who is competent
- whether the matter belongs to consiglio, giunta, sindaco, dirigente, segretario
- whether a municipal parere or internal control is required

Expected outcome:

- TUEL should often be sufficient as the primary legal anchor.

### `procedure`

Use when the user is primarily asking:

- how a municipal administrative procedure must be handled
- access to acts outside procurement
- responsabile del procedimento
- annullamento d'ufficio or other procedural guarantees applied to municipal action

Expected outcome:

- TUEL frames the municipal context
- `L. 241/1990` provides the procedural rule

### `transparency`

Use when the user is primarily asking:

- publication obligations
- transparency duties
- administrative transparency for municipal acts, documents, offices, or procedures

Expected outcome:

- TUEL frames the municipal act and organ
- `D.Lgs. 33/2013` provides the transparency rule

### `procurement`

Use when the user is primarily asking:

- affidamenti
- procedure di gara
- RUP
- sotto soglia
- access to tender documents

Expected outcome:

- TUEL frames the municipal contracting context
- `D.Lgs. 36/2023` provides the procurement rule

### `personnel/discipline`

Use when the user is primarily asking:

- political-management separation in the municipality
- dirigente competence
- UPD
- disciplinary office or management responsibility

Expected outcome:

- TUEL frames the local-government institutional setting
- `D.Lgs. 165/2001` provides the personnel/discipline rule

### `accounting/budget`

Use when the user is primarily asking:

- bilancio
- equilibri
- debiti fuori bilancio
- residui
- FPV
- armonizzazione contabile

Expected outcome:

- TUEL frames the municipal decision/control context
- `D.Lgs. 118/2011` provides the accounting rule
- `D.Lgs. 126/2014` is used only when strictly needed

### `mixed municipal case`

Use only when:

- the case is genuinely cross-corpus
- one specialist corpus is not sufficient
- the answer would be materially incomplete without a secondary corpus

Expected outcome:

- TUEL identifies the dominant municipal frame first
- exactly one primary follow-up corpus is chosen
- a secondary corpus is added only if indispensable

## Real Municipal Use Cases

The following use cases are the initial validation set for the TUEL-first entry layer.

1. `Quando serve il parere ex art. 49 TUEL per una proposta di delibera?`
2. `Per questa decisione è competente il consiglio o la giunta comunale?`
3. `Annullamento d'ufficio di un provvedimento comunale: chi lo avvia e con quali limiti?`
4. `Accesso agli atti di un procedimento amministrativo del comune`
5. `Il comune deve pubblicare questo atto o documento ai fini della trasparenza?`
6. `Obblighi di pubblicazione per bandi di concorso del comune`
7. `Affidamento diretto sotto soglia da parte del comune`
8. `Accesso agli atti di gara del comune`
9. `Chi è competente per l'ufficio procedimenti disciplinari nel comune?`
10. `Rapporto tra indirizzo politico e gestione dei dirigenti nel comune`
11. `Debiti fuori bilancio del comune e necessità del parere del revisore`
12. `Riaccertamento ordinario dei residui e reimputazione nel bilancio comunale`

## Success Criteria

The TUEL-first entry layer is considered valid only if all of the following hold:

1. The municipal question is first classified into one of the seven routing buckets without ambiguity in ordinary cases.
2. TUEL is always the first orientation layer for municipal use cases.
3. The chosen primary follow-up corpus is coherent with the actual legal center of gravity of the question.
4. A secondary corpus is invoked only when the case is materially incomplete without it.
5. TUEL remains responsible for identifying:
   - organo competente
   - municipal context
   - local act/control frame
6. Specialist corpora remain responsible for the substantive specialist rule.
7. Mixed cases do not degenerate into undirected multi-corpus retrieval.
8. The routing design remains compatible with the stabilized federated corpora already in use:
   - TUEL
   - `L. 241/1990`
   - `D.Lgs. 33/2013`
   - `D.Lgs. 36/2023`
   - `D.Lgs. 165/2001`
   - `D.Lgs. 118/2011`
   - `D.Lgs. 126/2014`
9. The design can be tested with real municipal questions before any production routing logic is introduced.

## Operational Notes

- This specification governs routing design, not ranking behavior.
- This specification does not authorize any change to embeddings, federated merge logic, or query packs.
- This specification should be used as the baseline document for any future TUEL-first routing prototype or query-pack design.

## Non-Production Statement

This file is a governance/design artifact, not production logic.

It must not be interpreted as an implemented router, an approved ranking strategy, or an authorization to modify the active federated system without separate controlled validation.
