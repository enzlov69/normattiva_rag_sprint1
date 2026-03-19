from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_master_cycle_docs_exist():
    for path in (
        'docs/MASTER_FINAL_AB_CYCLE_10_15_v1.md',
        'docs/FINAL_AB_PHASES_10_15_INDEX_v1.md',
        'docs/FINAL_AB_BASELINE_TAG_REGISTRY_v1.md',
        'docs/FINAL_AB_DOCUMENT_TO_RUNTIME_TRACE_MATRIX_v1.md',
    ):
        assert (ROOT / path).exists(), path


def test_phase_index_contains_phases_10_to_15():
    text = _read('docs/FINAL_AB_PHASES_10_15_INDEX_v1.md').lower()

    for phase in ('fase 10', 'fase 11', 'fase 12', 'fase 13', 'fase 14', 'fase 15'):
        assert phase in text


def test_baseline_tag_registry_contains_minimum_tags():
    text = _read('docs/FINAL_AB_BASELINE_TAG_REGISTRY_v1.md')

    for tag in (
        'stable-final-ab-controlled-handoff-v1',
        'stable-final-ab-runtime-controlled-handoff-v2',
        'stable-final-ab-level-a-intake-gate-v1',
        'stable-final-ab-consumption-audit-v1',
        'stable-final-ab-manual-review-gate-v1',
        'stable-final-ab-release-certification-v1',
    ):
        assert tag in text


def test_trace_matrix_contains_minimum_document_schema_runtime_test_links():
    text = _read('docs/FINAL_AB_DOCUMENT_TO_RUNTIME_TRACE_MATRIX_v1.md').lower()

    for term in (
        'final_ab_pre_runtime_controlled_handoff_spec_v1.md',
        'final_ab_runtime_controlled_handoff_spec_v1.md',
        'final_ab_level_a_intake_gate_spec_v1.md',
        'final_ab_level_a_consumption_audit_spec_v1.md',
        'final_ab_level_a_manual_review_gate_spec_v1.md',
        'final_ab_release_certification_pack_v1.md',
        'src/adapters/level_a_response_guard.py',
        'runtime/final_ab_runtime_handoff_service.py',
        'tools/final_ab_runtime_baseline_verifier.py',
        'tests/test_final_ab_manual_review_gate.py',
    ):
        assert term in text


def test_master_final_clarifies_level_b_subordination_and_non_delegability():
    text = _read('docs/MASTER_FINAL_AB_CYCLE_10_15_v1.md').lower()

    assert 'il livello b non decide' in text
    assert 'il livello b non approva' in text
    assert 'il livello b non chiude m07' in text
    assert 'il livello b non autorizza output opponibili' in text
    assert 'restano rigorosamente nel livello a' in text
    assert 'certificazione tecnica non sostituisce la responsabilita\' umana finale' in text
