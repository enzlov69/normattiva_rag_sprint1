from typing import Any, Dict, Iterable, List, Optional

from src.blocks import codes
from src.blocks.manager import BlockManager
from src.connectors.normattiva_errors import (
    NormattivaInvalidPayloadError,
    NormattivaMetadataError,
    NormattivaSourceUnverifiedError,
    ensure_official_uri,
)
from src.models.norm_unit import NormUnit
from src.models.source_document import SourceDocument
from src.parsing.parser import Parser
from src.utils.hashing import sha256_text
from src.utils.ids import build_id


class NormattivaMapper:
    SEARCH_ITEM_URI_KEYS = (
        "uri_ufficiale",
        "uri",
        "urn",
        "url",
        "linkTesto",
        "dettaglioAttoUrl",
    )

    def __init__(self, block_manager: Optional[BlockManager] = None) -> None:
        self.block_manager = block_manager or BlockManager()
        self.parser = Parser(self.block_manager)

    def map_search_item_to_source_document(
        self,
        *,
        case_id: str,
        item: Dict[str, Any],
        trace_id: str = "",
    ) -> SourceDocument:
        uri = self._pick_first(item, self.SEARCH_ITEM_URI_KEYS)
        atto_tipo = self._pick_first(item, ("denominazioneAtto", "tipoAtto", "atto_tipo")) or self._derive_atto_tipo(item)
        atto_numero = self._pick_first(item, ("numeroProvvedimento", "atto_numero", "numero", "numeroAtto"))
        atto_anno = self._pick_first(item, ("annoProvvedimento", "atto_anno", "anno", "annoDataGU"))
        titolo = self._pick_first(item, ("descrizioneAtto", "titolo", "title"))

        try:
            if not atto_tipo or not atto_numero or not atto_anno or not titolo:
                raise NormattivaMetadataError(
                    "Metadati Normattiva insufficienti: atto_tipo/atto_numero/atto_anno/titolo"
                )
            ensure_official_uri(uri)
        except (NormattivaMetadataError, NormattivaSourceUnverifiedError) as exc:
            self._open_mapping_block(
                case_id=case_id,
                trace_id=trace_id,
                affected_object_id=item.get("id") or "normattiva-search-item",
                reason=str(exc),
            )
            raise

        source_id = self._pick_first(item, ("codiceRedazionale", "id", "source_id")) or build_id("source")
        publication = self._pick_first(item, ("pubblicazione", "fontePubblicazione", "source")) or "Normattiva"
        publication_date = self._pick_first(item, ("dataPubblicazione", "dataEmanazione", "dataGUStr")) or ""
        issuer = self._pick_first(item, ("descrizione_emettitore", "ente_emittente", "emettitore")) or "Stato"
        stato_vigenza = self._pick_first(item, ("stato_vigenza", "vigore_status")) or "VIGENZA_INCERTA"

        return SourceDocument(
            record_id=build_id("srcdocrec"),
            record_type="SourceDocument",
            source_id=str(source_id),
            atto_tipo=str(atto_tipo),
            atto_numero=str(atto_numero),
            atto_anno=str(atto_anno),
            titolo=str(titolo),
            ente_emittente=str(issuer),
            pubblicazione=str(publication),
            data_pubblicazione=str(publication_date),
            uri_ufficiale=str(uri),
            stato_verifica_fonte="VERIFIED",
            stato_vigenza=str(stato_vigenza),
            versione_documento="v1",
            hash_contenuto=sha256_text(str(item)),
            authoritative_flag=True,
            document_status="VERIFIED",
            parse_ready_flag=True,
            trace_id=trace_id,
        )

    def map_detail_payload_to_norm_units(
        self,
        *,
        case_id: str,
        source_document: SourceDocument,
        detail_payload: Any,
        trace_id: str = "",
    ) -> List[NormUnit]:
        if isinstance(detail_payload, str):
            return self.parser.parse(
                case_id=case_id,
                source_document=source_document,
                text=detail_payload,
                trace_id=trace_id,
            )

        if not isinstance(detail_payload, dict):
            raise NormattivaInvalidPayloadError("Il payload di dettaglio deve essere un dict o una stringa")

        for text_key in ("testo", "contenuto", "testoCoordinato", "body"):
            text_value = detail_payload.get(text_key)
            if isinstance(text_value, str) and text_value.strip():
                return self.parser.parse(
                    case_id=case_id,
                    source_document=source_document,
                    text=text_value,
                    trace_id=trace_id,
                )

        article_items = self._pick_first(detail_payload, ("articoli", "articles", "articolo"))
        if isinstance(article_items, dict):
            article_items = [article_items]
        if not isinstance(article_items, list) or not article_items:
            raise NormattivaInvalidPayloadError(
                "Payload di dettaglio privo di testo grezzo e di lista articoli utilizzabile"
            )

        units: List[NormUnit] = []
        for art_idx, article in enumerate(article_items, start=1):
            articolo = self._pick_first(article, ("articolo", "numeroArticolo", "numero", "idArticolo"))
            rubrica = self._pick_first(article, ("rubrica", "titolo", "heading")) or ""
            article_text = self._pick_first(article, ("testo", "contenuto", "body")) or ""
            commi = self._pick_first(article, ("commi", "paragraphs", "comma"))

            if not articolo:
                raise NormattivaMetadataError("Articolo privo di identificativo")

            if isinstance(commi, dict):
                commi = [commi]
            if isinstance(commi, list) and commi:
                for comma_idx, comma_payload in enumerate(commi, start=1):
                    comma_num = self._pick_first(comma_payload, ("comma", "numeroComma", "numero", "idComma")) or str(comma_idx)
                    comma_text = self._pick_first(comma_payload, ("testo", "contenuto", "body")) or ""
                    units.append(
                        self._build_unit(
                            source_document=source_document,
                            articolo=str(articolo),
                            comma=str(comma_num),
                            rubrica=str(rubrica),
                            testo_unita=str(comma_text),
                            unit_type="COMMA",
                            position_index=art_idx * 100 + comma_idx,
                            hierarchy_path=f"articolo:{articolo}/comma:{comma_num}",
                            trace_id=trace_id,
                        )
                    )
                continue

            units.append(
                self._build_unit(
                    source_document=source_document,
                    articolo=str(articolo),
                    comma=None,
                    rubrica=str(rubrica),
                    testo_unita=str(article_text),
                    unit_type="ARTICOLO",
                    position_index=art_idx,
                    hierarchy_path=f"articolo:{articolo}",
                    trace_id=trace_id,
                )
            )

        if not units:
            raise NormattivaInvalidPayloadError("Nessuna NormUnit generata dal payload di dettaglio")
        return units

    def _build_unit(
        self,
        *,
        source_document: SourceDocument,
        articolo: str,
        comma: Optional[str],
        rubrica: str,
        testo_unita: str,
        unit_type: str,
        position_index: int,
        hierarchy_path: str,
        trace_id: str,
    ) -> NormUnit:
        return NormUnit(
            record_id=build_id("normunitrec"),
            record_type="NormUnit",
            norm_unit_id=build_id("normunit"),
            source_id=source_document.source_id,
            unit_type=unit_type,
            articolo=articolo,
            comma=comma,
            rubrica=rubrica,
            testo_unita=testo_unita,
            position_index=position_index,
            hierarchy_path=hierarchy_path,
            trace_id=trace_id,
        )

    @staticmethod
    def _pick_first(payload: Dict[str, Any], keys: Iterable[str]) -> Any:
        for key in keys:
            value = payload.get(key)
            if value not in (None, "", []):
                return value
        return None

    @staticmethod
    def _derive_atto_tipo(item: Dict[str, Any]) -> str:
        descrizione = str(item.get("descrizioneAtto") or item.get("titolo") or "").strip()
        if not descrizione:
            return ""
        stop_markers = [", n.", " n.", ",", " del "]
        upper_descr = descrizione.upper()
        for marker in stop_markers:
            idx = upper_descr.find(marker.upper())
            if idx > 0:
                return descrizione[:idx].strip()
        return descrizione.split()[0].strip()

    def _open_mapping_block(self, *, case_id: str, trace_id: str, affected_object_id: str, reason: str) -> None:
        self.block_manager.open_block(
            case_id=case_id,
            block_code=codes.METADATA_INSUFFICIENT,
            block_category="metadata",
            block_severity="CRITICAL",
            origin_module="NormattivaMapper",
            affected_object_type="NormattivaPayload",
            affected_object_id=str(affected_object_id),
            block_reason=reason,
            trace_id=trace_id,
        )
