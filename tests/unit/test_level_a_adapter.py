from src.adapters.level_a_adapter import LevelAAdapter
from src.interface.level_b_package_types import LevelBDeliveryPackage


def test_level_a_adapter_builds_valid_request_payload():
    package = LevelBDeliveryPackage(
        record_id='rec1',
        record_type='LevelBDeliveryPackage',
        package_id='pkg1',
        case_id='case1',
        report_id='rep1',
        support_only_flag=True,
        package_status='BLOCKED',
        block_ids=['b1'],
        block_codes=['CITATION_INCOMPLETE'],
        trace_id='trace1',
    )

    adapter = LevelAAdapter()
    payload = adapter.build_request_payload(package)

    assert payload['case_id'] == 'case1'
    assert payload['source_package_id'] == 'pkg1'
    assert payload['support_only_flag'] is True
    assert payload['technical_status'] == 'BLOCKED'
    assert payload['block_codes'] == ['CITATION_INCOMPLETE']
