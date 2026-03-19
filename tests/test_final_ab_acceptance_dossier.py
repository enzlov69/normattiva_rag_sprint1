from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs' / 'FINAL_AB_ACCEPTANCE_DOSSIER_v1.md'


def test_acceptance_dossier_contains_baseline_tag_and_commit():
    text = DOC.read_text(encoding='utf-8')

    assert 'stable-final-ab-manual-review-gate-v1' in text
    assert 'bbabc4f' in text


def test_acceptance_dossier_summarizes_presidi_and_minimum_tests():
    text = DOC.read_text(encoding='utf-8').lower()

    assert 'presidi consolidati' in text
    assert 'test minimi eseguiti' in text
    assert 'validator runtime anomaly governance' in text


def test_acceptance_dossier_is_clear_on_level_b_subordination():
    text = DOC.read_text(encoding='utf-8').lower()

    assert 'il livello b non decide' in text
    assert 'il livello b non approva' in text
    assert 'il livello b non chiude m07' in text
    assert 'il livello b non autorizza output opponibili' in text
