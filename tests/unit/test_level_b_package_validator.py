from src.interface.level_b_package_types import LevelBDeliveryPackage
from src.interface.level_b_package_validator import LevelBPackageValidator


def test_level_b_package_validator_accepts_valid_package() -> None:
    package = LevelBDeliveryPackage(
        record_id='packrec_1',
        record_type='LevelBDeliveryPackage',
        package_id='pack_1',
        case_id='case_001',
        report_id='report_1',
        support_only_flag=True,
        source_ids=['source_1'],
        warnings=[],
        errors=[],
        block_ids=[],
        block_codes=[],
        package_status='READY',
    )

    result = LevelBPackageValidator().validate(package)

    assert result.valid is True
    assert result.missing_fields == []
    assert result.forbidden_fields == []


def test_level_b_package_validator_rejects_forbidden_and_conclusive_fields() -> None:
    payload = {
        'package_id': 'pack_2',
        'case_id': 'case_002',
        'report_id': 'report_2',
        'support_only_flag': False,
        'source_ids': ['source_2'],
        'warnings': [],
        'errors': [],
        'block_ids': [],
        'block_codes': [],
        'package_status': 'GO',
        'final_decision': 'APPROVED',
    }

    result = LevelBPackageValidator().validate(payload)

    assert result.valid is False
    assert 'final_decision' in result.forbidden_fields
    assert result.errors
