from src.retrieval.reranker_dlgs33_patch import RetrievalCandidate, RerankerDLGS33Patch

def _candidates_amministrazione_trasparente():
    return [
        RetrievalCandidate(
            retrieval_result_id="art_001",
            atto_tipo="Decreto legislativo",
            atto_numero="33",
            atto_anno="2013",
            articolo="1",
            rubrica="Principio generale di trasparenza",
            testo_unita=(
                "La trasparenza è intesa come accessibilità totale dei dati e documenti detenuti "
                "dalle pubbliche amministrazioni..."
            ),
            source_collection="normattiva_dlgs33_2013_vigente_articles",
            score_lexical=65.0,
            score_vector=70.0,
        ),
        RetrievalCandidate(
            retrieval_result_id="art_009",
            atto_tipo="Decreto legislativo",
            atto_numero="33",
            atto_anno="2013",
            articolo="9",
            rubrica="Accesso alle informazioni pubblicate nei siti",
            testo_unita=(
                "Ai fini della piena accessibilità delle informazioni pubblicate, nella home page "
                "dei siti istituzionali è collocata un'apposita sezione denominata 'Amministrazione trasparente'..."
            ),
            source_collection="normattiva_dlgs33_2013_vigente_articles",
            score_lexical=58.0,
            score_vector=66.0,
        ),
    ]


def _candidates_responsabile_trasparenza():
    return [
        RetrievalCandidate(
            retrieval_result_id="art_001",
            atto_tipo="Decreto legislativo",
            atto_numero="33",
            atto_anno="2013",
            articolo="1",
            rubrica="Principio generale di trasparenza",
            testo_unita=(
                "La trasparenza è intesa come accessibilità totale dei dati e documenti detenuti "
                "dalle pubbliche amministrazioni..."
            ),
            source_collection="normattiva_dlgs33_2013_vigente_articles",
            score_lexical=63.0,
            score_vector=69.0,
        ),
        RetrievalCandidate(
            retrieval_result_id="art_043",
            atto_tipo="Decreto legislativo",
            atto_numero="33",
            atto_anno="2013",
            articolo="43",
            rubrica="Responsabile per la trasparenza",
            testo_unita=(
                "All'interno di ogni amministrazione il responsabile per la prevenzione della corruzione "
                "svolge, di norma, le funzioni di Responsabile per la trasparenza..."
            ),
            source_collection="normattiva_dlgs33_2013_vigente_articles",
            score_lexical=59.0,
            score_vector=65.0,
        ),
    ]


def test_amministrazione_trasparente_goes_top1():
    reranker = RerankerDLGS33Patch()
    results = reranker.rerank("amministrazione trasparente", _candidates_amministrazione_trasparente())
    assert results[0].articolo == "9", [
        (r.articolo, r.score_reranked, r.retrieval_reason) for r in results
    ]


def test_responsabile_per_la_trasparenza_goes_top1():
    reranker = RerankerDLGS33Patch()
    results = reranker.rerank("responsabile per la trasparenza", _candidates_responsabile_trasparenza())
    assert results[0].articolo == "43", [
        (r.articolo, r.score_reranked, r.retrieval_reason) for r in results
    ]


def test_non_dlgs33_corpus_is_untouched():
    reranker = RerankerDLGS33Patch()
    candidates = [
        RetrievalCandidate(
            retrieval_result_id="tuel_art_1",
            atto_tipo="Decreto legislativo",
            atto_numero="267",
            atto_anno="2000",
            articolo="1",
            rubrica="Oggetto",
            testo_unita="Il presente testo unico contiene i principi...",
            source_collection="normattiva_tuel_267_2000_articles",
            score_lexical=10.0,
            score_vector=5.0,
        )
    ]
    results = reranker.rerank("amministrazione trasparente", candidates)
    assert results[0].score_reranked == 15.0
