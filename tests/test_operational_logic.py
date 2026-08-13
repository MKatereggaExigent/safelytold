import pytest

from services.integration_service.app.operations import transition_allowed, validate_payload


def test_hotline_metadata_rejects_reporter_data() -> None:
    with pytest.raises(ValueError, match='reporter data'):
        validate_payload('hotline', 'received', {'provider_call_id': 'c1', 'reporting_mode': 'anonymous', 'language': 'en', 'started_at': 'now', 'phone_number': 'secret'})


def test_hotline_submission_requires_normal_intake_case() -> None:
    with pytest.raises(ValueError, match='case_id'):
        validate_payload('hotline', 'submitted', {'provider_call_id': 'c1', 'reporting_mode': 'anonymous', 'language': 'en', 'started_at': 'now'})


def test_training_pass_rules() -> None:
    with pytest.raises(ValueError): validate_payload('training', 'passed', {'score': 79, 'critical_questions_passed': True})
    validate_payload('training', 'passed', {'score': 80, 'critical_questions_passed': True})


def test_continuity_pass_requires_objectives_and_restore() -> None:
    with pytest.raises(ValueError): validate_payload('continuity', 'passed', {'restore_verified': False})
    validate_payload('continuity', 'passed', {'restore_verified': True, 'actual_rto_minutes': 30, 'target_rto_minutes': 60, 'actual_rpo_minutes': 5, 'target_rpo_minutes': 15})


def test_qa_and_coverage_controls() -> None:
    with pytest.raises(ValueError): validate_payload('qa', 'approved', {'critical_defects': 1})
    with pytest.raises(ValueError): validate_payload('coverage', 'active', {'primary_subject': 'a', 'secondary_subject': 'a'})
    assert transition_allowed('awareness', 'approved', 'published')
    assert not transition_allowed('awareness', 'draft', 'published')
