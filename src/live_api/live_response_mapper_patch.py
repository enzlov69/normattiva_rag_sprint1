# Patch da applicare in src/live_api/live_response_mapper.py

def build_detail_request_payload_from_search_item(self, search_item, data_vigenza=None):
    codice = (
        search_item.get("codiceRedazionale")
        or search_item.get("codice_redazionale")
        or ""
    )

    data_gu_value = (
        search_item.get("dataGU")
        or search_item.get("data_gu")
        or ""
    )

    return {
        "codiceRedazionale": codice,
        "dataGU": data_vigenza or data_gu_value,
        "idArticolo": 1,
        "sottoArticolo": 1,
        "sottoArticolo1": 0,
        "idGruppo": 1,
        "progressivo": 0,
        "versione": 0,
    }
