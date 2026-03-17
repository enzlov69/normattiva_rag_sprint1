from pathlib import Path

from src.runtime.tuel_real_validation_runner import TuelRealValidationRunner


FIXTURE_DIR = Path(__file__).resolve().parents[1] / 'fixtures' / 'normattiva'


def test_tuel_real_payload_authorized_technical_output() -> None:
    runner = TuelRealValidationRunner()
    artifacts = runner.run(
        case_id='case_tuel_real_success',
        search_item_path=FIXTURE_DIR / 'tuel_search_item_real.json',
        detail_payload_path=FIXTURE_DIR / 'tuel_detail_payload_real.json',
        trace_id='trace_tuel_real_success',
    )

    assert artifacts.ingest_result.source_document is not None
    assert artifacts.ingest_result.source_document.atto_numero == '267'
    assert len(artifacts.ingest_result.norm_units) == 4
    assert artifacts.retrieval_results
    assert artifacts.technical_report.report_status == 'READY'
    assert artifacts.package_validation.valid is True
    assert artifacts.package.package_status == 'READY'
    assert artifacts.runtime_result.authorization_status == 'OUTPUT_AUTHORIZATION_ALLOWED'
    assert artifacts.runtime_result.final_runtime_status == 'AUTHORIZED_TECHNICAL_OUTPUT'


def test_tuel_real_payload_blocks_when_required_target_is_removed() -> None:
    runner = TuelRealValidationRunner()
    artifacts = runner.run(
        case_id='case_tuel_real_blocked',
        search_item_path=FIXTURE_DIR / 'tuel_search_item_real.json',
        detail_payload_path=FIXTURE_DIR / 'tuel_detail_payload_real.json',
        trace_id='trace_tuel_real_blocked',
        query_text='articolo 50 consiglio'
    )

    # Corruzione controllata: simuliamo un perimetro documentale che perde il target del rinvio.
    targetless_units = [unit for unit in artifacts.ingest_result.norm_units if unit.articolo != '50']
    crossref_records = []
    for unit in targetless_units:
        crossref_records.extend(
            runner.crossref_resolver.resolve(
                case_id='case_tuel_real_blocked_mutated',
                source_document=artifacts.ingest_result.source_document,
                norm_unit=unit,
                known_norm_units=targetless_units,
                essential_ref_default=True,
                trace_id='trace_tuel_real_blocked_mutated',
            )
        )

    assert any(record.resolution_status == 'UNRESOLVED' for record in crossref_records)
