from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs' / 'FINAL_AB_RELEASE_CERTIFICATION_PACK_v1.md'


def test_release_certification_pack_contains_minimum_sections():
    text = DOC.read_text(encoding='utf-8').lower()

    for term in (
        'presidi attivi riepilogati',
        'criteri di certificabilita',
        'controlli contrattuali a/b',
        'controlli runtime',
        'controlli intake e consumption',
        'controlli isolation, manual review e final human approval',
    ):
        assert term in text


def test_release_certification_pack_distinguishes_technical_certification_from_admin_decision():
    text = DOC.read_text(encoding='utf-8').lower()

    assert 'certificazione qui definita e\' tecnica e di perimetro' in text
    assert 'non equivale a:' in text
    assert 'decisione amministrativa' in text


def test_release_certification_pack_is_clear_on_non_delegability():
    text = DOC.read_text(encoding='utf-8').lower()

    assert 'il livello b non decide, non approva, non chiude m07 e non autorizza output opponibili' in text
