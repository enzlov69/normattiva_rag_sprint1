from src.finalization.finalization_types import FinalGoAssessment
from src.finalization.output_authorizer import OutputAuthorizer


def build_assessment(go_possible: bool = True) -> FinalGoAssessment:
    return FinalGoAssessment(
        record_id='gorec_1',
        record_type='FinalGoAssessment',
        assessment_id='go_1',
        case_id='case_1',
        request_id='req_1',
        source_package_id='pkg_1',
        source_compliance_id='comp_1',
        support_only_flag=True,
        go_final_possible=go_possible,
        go_final_status='GO_FINAL_POSSIBLE' if go_possible else 'GO_FINAL_NOT_POSSIBLE',
        source_layer='A',
    )


def test_output_authorization_allowed_only_for_supported_output_types() -> None:
    authorizer = OutputAuthorizer()
    decision = authorizer.authorize(build_assessment(True), requested_output_type='RAC_DRAFT')
    assert decision.authorization_allowed is True
    assert decision.authorization_status == 'OUTPUT_AUTHORIZATION_ALLOWED'
    assert decision.authorized_output_ref is not None



def test_output_authorization_denied_when_go_not_possible_or_type_invalid() -> None:
    authorizer = OutputAuthorizer()
    decision = authorizer.authorize(build_assessment(False), requested_output_type='FINAL_ACT')
    assert decision.authorization_allowed is False
    assert decision.authorization_status == 'OUTPUT_AUTHORIZATION_DENIED'
    assert 'go_final_not_possible' in decision.denied_reasons
    assert 'output_type_not_allowed' in decision.denied_reasons
