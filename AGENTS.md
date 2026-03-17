# AGENTS.md — Normattiva RAG Federated System

## CONTEXT
This project implements a federated RAG system over multiple legal corpora (Normattiva-based).
Each corpus is queried independently and results are merged into a global ranking.

The system is already STABLE and TESTED.
All modifications must preserve existing behavior.

## CORE RULES (MANDATORY)
1. DO NOT refactor the codebase.
2. DO NOT change architecture or data structures.
3. DO NOT introduce global ranking changes.
4. DO NOT modify embedding logic.
5. DO NOT normalize distances across collections.

## CHANGE POLICY
- Always start from the current stable file.
- Apply ONLY minimal, localized, reversible changes.
- One change at a time.
- If a change affects other queries -> REJECT IT.

## TESTING CONTRACT
The system is validated through:
tools/federated_tests/run_federated_active_corpora_tests.py

Requirements:
- query_fail must NOT increase
- no regression on existing passing queries
- runtime_fail must remain 0

## SPECIFIC FIX POLICY
When fixing a failing query:
- Prefer ultra-local fixes over general solutions
- If needed, implement query-specific logic
- Scope must be strictly limited (string match or equivalent)
- No global heuristics unless explicitly required

## DEBUG POLICY
- Debug logs must be temporary
- Debug must be query-scoped when possible
- Remove debug after validation

## OUTPUT REQUIREMENTS
When modifying code:
- Return full updated file
- Clearly indicate added/modified block
- Do NOT rewrite unrelated parts

## PROJECT PRIORITY
Correctness and stability > elegance and generalization

This is a controlled system, not a generic search engine.

## STABLE-BASE PATCH RULE

For any future modification on code or test runners:

1. Always start from the last validated stable file.
2. Never build a fix on top of an experimental or partially validated variant.
3. Apply only one minimal change at a time.
4. After each change, immediately rerun the relevant test.
5. Promote the change to stable baseline only if:
   - runtime failures do not increase
   - query_fail does not increase
   - no regression appears on previously passing cases
6. If regressions appear, rollback immediately to the stable base file.
7. Prefer ultra-local fixes over general heuristics.
8. For ranking issues, do not introduce global scoring changes unless explicitly required.
9. Keep temporary debug logs only during validation; remove them before consolidation.
10. When a fix is validated, create a stable backup copy before further edits.

## PROTOCOLLO OPERATIVO FISSO — BASE STABILE + PATCH MINIMA

1. Si parte sempre dall’ultimo file stabile validato.
2. Non si lavora mai su varianti sperimentali come nuova base.
3. Si applica una sola modifica per volta.
4. La modifica deve essere minima, localizzata e reversibile.
5. Dopo ogni modifica si esegue subito il test pertinente.
6. La patch si consolida solo se:
   - runtime failures non aumenta
   - query fail non aumenta
   - non compaiono regressioni sui casi già passati
7. Se compaiono regressioni, rollback immediato alla baseline stabile.
8. Si preferiscono fix ultra-locali a euristiche globali.
9. I debug temporanei si rimuovono prima del consolidamento finale.
10. Ogni patch validata diventa nuova baseline solo dopo backup o commit.
## TEST RUNNER GOVERNANCE RULE

When working inside `/tests`:

1. Always prefer the current active test runner as the base.
2. Never use historical runners (`*_old.py`, `*_v25_*`, numbered variants) as the default starting point if a current stable runner already exists.
3. Treat versioned runners as historical references, not as active baselines.
4. Use `*_STABLE.py` files only when they are explicitly confirmed as the current validated baseline.
5. Apply the same policy used for the federated runner:
   - stable base first
   - one minimal change at a time
   - immediate test rerun
   - reject regressions
6. Do not refactor historical test files unless explicitly requested.
7. If a fix is validated, promote only the active runner, not its historical variants.
