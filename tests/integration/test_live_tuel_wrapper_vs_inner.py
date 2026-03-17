from src.live_api.live_detail_classifier import classify_detail_text, DetailKind

def test_wrapper_classification():

    text = "È approvato l'unito testo unico delle leggi sull'ordinamento degli enti locali."

    result = classify_detail_text(text)

    assert result.kind == DetailKind.WRAPPER_ARTICLE
