from src.retrieval.dlgs33_runtime_integration import (
    apply_dlgs33_runtime_rerank,
    expand_retrieval_query_for_runtime,
    is_dlgs33_collection,
)


def test_is_dlgs33_collection_true():
    assert is_dlgs33_collection("normattiva_dlgs33_2013_vigente_articles") is True


def test_is_dlgs33_collection_false():
    assert is_dlgs33_collection("normattiva_tuel_267_2000") is False


def test_expand_retrieval_query_for_runtime_only_for_dlgs33():
    expanded = expand_retrieval_query_for_runtime(
        "amministrazione trasparente",
        "normattiva_dlgs33_2013_vigente_articles",
    )
    assert expanded == "amministrazione trasparente sezione amministrazione trasparente"

    unchanged = expand_retrieval_query_for_runtime(
        "fondo di riserva",
        "normattiva_tuel_267_2000",
    )
    assert unchanged == "fondo di riserva"


def test_runtime_rerank_promotes_art_9_for_amministrazione_trasparente():
    raw_results = [
        {
            "id": "a23",
            "articolo": "23",
            "rubrica": "Obblighi di pubblicazione concernenti i provvedimenti amministrativi",
            "text": "provvedimenti amministrativi",
            "atto_numero": "33",
            "atto_anno": "2013",
            "score_vector": 9.4,
            "score_lexical": 0.2,
        },
        {
            "id": "a48",
            "articolo": "48",
            "rubrica": "Norme sull'attuazione degli obblighi di pubblicità e trasparenza",
            "text": "pubblicità e trasparenza",
            "atto_numero": "33",
            "atto_anno": "2013",
            "score_vector": 9.2,
            "score_lexical": 0.1,
        },
        {
            "id": "a9",
            "articolo": "9",
            "rubrica": "Accesso alle informazioni pubblicate nei siti",
            "text": "La sezione denominata 'Amministrazione trasparente' è collocata nella home page dei siti istituzionali.",
            "atto_numero": "33",
            "atto_anno": "2013",
            "score_vector": 8.8,
            "score_lexical": 0.1,
        },
    ]

    reranked, shadow = apply_dlgs33_runtime_rerank(
        query_text="amministrazione trasparente",
        raw_results=raw_results,
        source_collection="normattiva_dlgs33_2013_vigente_articles",
        top_k=5,
    )

    assert shadow["patch_applicable"] is True
    assert shadow["mode"] == "reranked"
    assert shadow["retrieval_query"] == "amministrazione trasparente sezione amministrazione trasparente"
    assert reranked[0]["articolo"] == "9"


def test_runtime_rerank_promotes_art_43_for_responsabile_trasparenza():
    raw_results = [
        {
            "id": "a1",
            "articolo": "1",
            "rubrica": "Principio generale di trasparenza",
            "text": "La trasparenza è intesa come accessibilità totale.",
            "atto_numero": "33",
            "atto_anno": "2013",
            "score_vector": 9.6,
            "score_lexical": 0.1,
        },
        {
            "id": "a43",
            "articolo": "43",
            "rubrica": "Responsabile per la trasparenza",
            "text": "All'interno di ogni amministrazione il responsabile per la trasparenza...",
            "atto_numero": "33",
            "atto_anno": "2013",
            "score_vector": 8.0,
            "score_lexical": 0.2,
        },
    ]

    reranked, shadow = apply_dlgs33_runtime_rerank(
        query_text="responsabile per la trasparenza",
        raw_results=raw_results,
        source_collection="normattiva_dlgs33_2013_vigente_articles",
        top_k=5,
    )

    assert shadow["patch_applicable"] is True
    assert shadow["mode"] == "reranked"
    assert reranked[0]["articolo"] == "43"


def test_runtime_rerank_passthrough_for_non_dlgs33_collections():
    raw_results = [
        {
            "id": "x1",
            "articolo": "176",
            "rubrica": "Prelevamenti dal fondo di riserva",
            "text": "fondo di riserva",
            "atto_numero": "267",
            "atto_anno": "2000",
            "score_vector": 7.0,
            "score_lexical": 3.0,
        },
        {
            "id": "x2",
            "articolo": "193",
            "rubrica": "Salvaguardia degli equilibri di bilancio",
            "text": "equilibri di bilancio",
            "atto_numero": "267",
            "atto_anno": "2000",
            "score_vector": 9.0,
            "score_lexical": 1.0,
        },
    ]

    reranked, shadow = apply_dlgs33_runtime_rerank(
        query_text="fondo di riserva",
        raw_results=raw_results,
        source_collection="normattiva_tuel_267_2000",
        top_k=5,
    )

    assert shadow["patch_applicable"] is False
    assert shadow["mode"] == "passthrough"
    assert shadow["retrieval_query"] == "fondo di riserva"

    # Per corpus diversi dal D.Lgs. 33/2013 l'ordine deve restare invariato.
    assert reranked[0]["articolo"] == "176"
    assert reranked[1]["articolo"] == "193"
    assert reranked[0]["retrieval_reason"] == ["passthrough_non_dlgs33"]