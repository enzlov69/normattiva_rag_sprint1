from src.adapters.level_a_request_mapper import LevelARequestMapper
from src.interface.level_b_package_types import LevelBDeliveryPackage


def test_request_mapper_creates_support_only_envelope():
    package = LevelBDeliveryPackage(
        record_id='rec1',
        record_type='LevelBDeliveryPackage',
        package_id='pkg1',
        case_id='case1',
        report_id='rep1',
        support_only_flag=True,
        package_status='READY_WITH_WARNINGS',
        source_ids=['src1'],
        valid_citation_ids=['cit1'],
        warnings=['warning-1'],
        trace_id='trace1',
    )

    mapper = LevelARequestMapper()
    envelope = mapper.map_from_package(package)

    assert envelope.case_id == 'case1'
    assert envelope.source_package_id == 'pkg1'
    assert envelope.support_only_flag is True
    assert envelope.technical_status == 'READY_WITH_WARNINGS'
    assert 'Pacchetto tecnico-documentale di supporto, non conclusivo.' in envelope.adapter_notes
    assert envelope.source_layer == 'A'
