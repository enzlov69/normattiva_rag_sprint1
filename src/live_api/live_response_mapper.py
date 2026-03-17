
from src.connectors.normattiva_errors import ensure_official_uri
from src.models.source_document import SourceDocument


class LiveResponseMapper:
    """Mapper per trasformare le risposte della API live Normattiva in SourceDocument."""

    def __init__(self, mapper=None):
        self.mapper = mapper

    def map_search_item_to_source_document(self, case_id: str, search_item: dict, trace_id: str):
        """
        Mappa un search_item Normattiva in SourceDocument.
        Supporta sia naming camelCase sia snake_case.
        """

        codice = (
            search_item.get("codiceRedazionale")
            or search_item.get("codice_redazionale")
        )

        data_gu = (
            search_item.get("dataGU")
            or search_item.get("data_gu")
            or ""
        )

        titolo = (
            search_item.get("titoloAtto")
            or search_item.get("titolo")
            or ""
        )

        uri = f"https://www.normattiva.it/atto/caricaDettaglioAtto?atto.codiceRedazionale={codice}"

        # Verifica URI ufficiale
        ensure_official_uri(uri)

        source_document = SourceDocument(
            case_id=case_id,
            source_system="normattiva_live",
            source_type="norm",
            codice_redazionale=codice,
            data_gu=data_gu,
            titolo=titolo,
            uri=uri,
            trace_id=trace_id,
        )

        return source_document
