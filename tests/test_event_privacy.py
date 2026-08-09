import pytest
from safelytold_common.privacy import assert_event_safe, redact_mapping, redact_text


def test_event_rejects_sensitive_keys() -> None:
    with pytest.raises(ValueError):
        assert_event_safe({'case_id': 'x', 'allegation_text': 'forbidden'})


def test_redaction() -> None:
    text = redact_text('mail me at person@example.com or +27 82 555 1234')
    assert 'person@example.com' not in text
    assert '+27 82 555 1234' not in text


def test_nested_mapping_is_redacted() -> None:
    assert redact_mapping({'safe': {'message': 'secret'}})['safe']['message'] == '[REDACTED]'


def test_event_rejects_nested_sensitive_key() -> None:
    with pytest.raises(ValueError):
        assert_event_safe({'case_id': 'x', 'metadata': {'reporter_email': 'redacted elsewhere'}})


def test_event_rejects_pii_inside_safe_key() -> None:
    with pytest.raises(ValueError):
        assert_event_safe({'case_id': 'x', 'reference': 'contact person@example.com'})
