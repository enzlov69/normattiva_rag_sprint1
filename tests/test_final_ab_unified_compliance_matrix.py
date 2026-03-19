from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs' / 'FINAL_AB_UNIFIED_COMPLIANCE_MATRIX_v1.md'


def test_unified_compliance_matrix_contains_minimum_control_areas():
    text = DOC.read_text(encoding='utf-8').lower()

    for term in (
        'forbidden fields',
        'documentary packet minimum',
        'm07 boundary',
        'block propagation',
        'intake gate',
        'consumption rules',
        'quarantine',
        'decision isolation',
        'manual review gate',
        'final human approval trace',
    ):
        assert term in text


def test_unified_compliance_matrix_covers_phases_10_to_14():
    text = DOC.read_text(encoding='utf-8').lower()

    for phase in ('fase 10', 'fase 11', 'fase 12', 'fase 13', 'fase 14'):
        assert phase in text


def test_unified_compliance_matrix_keeps_presidio_and_layer_coherent():
    text = DOC.read_text(encoding='utf-8')

    assert 'Livello A' in text
    assert 'Livello B' in text
    assert 'Runtime' in text
