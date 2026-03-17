from src.live_api.live_detail_classifier import classify_detail_text, DetailKind

def test_unresolved_case():

    text = "Testo non riconosciuto."

    result = classify_detail_text(text)

    assert result.kind == DetailKind.UNRESOLVED
