from src.live_api.live_detail_classifier import classify_detail_text, DetailKind

def test_inner_text_classification():

    text = "Il presente testo unico contiene i principi e le disposizioni in materia di ordinamento degli enti locali."

    result = classify_detail_text(text)

    assert result.kind == DetailKind.INNER_TEXT_ARTICLE
