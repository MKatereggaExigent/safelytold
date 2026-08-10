from datetime import UTC, datetime, timedelta

import pytest

from services.notification_service.app.nudge import (
    decide_send,
    in_prohibited_window,
    next_attempt_at,
    post_send_next_check,
)


NOW = datetime(2026, 8, 9, 12, 0, tzinfo=UTC)


def test_first_nudge_fires_after_first_delay() -> None:
    at = next_attempt_at(0, NOW, first_delay_hours=24.0, escalation_hours=[72.0, 168.0])
    assert at == NOW + timedelta(hours=24)


def test_escalation_waits_longer_each_time() -> None:
    first = next_attempt_at(0, NOW, first_delay_hours=24.0, escalation_hours=[72.0, 168.0])
    second = next_attempt_at(1, NOW, first_delay_hours=24.0, escalation_hours=[72.0, 168.0])
    third = next_attempt_at(2, NOW, first_delay_hours=24.0, escalation_hours=[72.0, 168.0])
    assert (second - first) == timedelta(hours=48)
    assert (third - second) == timedelta(hours=96)


def test_escalation_caps_at_last_step() -> None:
    last = next_attempt_at(5, NOW, first_delay_hours=24.0, escalation_hours=[72.0, 168.0])
    assert last == NOW + timedelta(hours=168)


def test_decision_respects_max_nudges() -> None:
    decision = decide_send(now=NOW, last_attempt_at=NOW, attempts=3, max_nudges=3, allowed_channels=['email'])
    assert decision.due is False
    assert 'maximum' in decision.reason


def test_decision_requires_email_channel() -> None:
    decision = decide_send(now=NOW, last_attempt_at=None, attempts=0, allowed_channels=['sms'])
    assert decision.due is False
    assert 'email channel not permitted' in decision.reason


def test_decision_honours_prohibited_window() -> None:
    decision = decide_send(
        now=NOW,
        last_attempt_at=None,
        attempts=0,
        allowed_channels=['email'],
        prohibited_times=['10:00-14:00'],
    )
    assert decision.due is False
    assert 'prohibited contact window' in decision.reason


def test_decision_rejects_non_neutral_preference() -> None:
    decision = decide_send(
        now=NOW,
        last_attempt_at=None,
        attempts=0,
        allowed_channels=['email'],
        neutral_message_only=False,
    )
    assert decision.due is False


def test_decision_allows_neutral_email_outside_window() -> None:
    decision = decide_send(
        now=NOW,
        last_attempt_at=None,
        attempts=0,
        allowed_channels=['email'],
        prohibited_times=['02:00-06:00'],
    )
    assert decision.due is True


def test_in_prohibited_window_wraps_midnight() -> None:
    assert in_prohibited_window(NOW.replace(hour=23), ['22:00-04:00'])
    assert not in_prohibited_window(NOW.replace(hour=12), ['22:00-04:00'])


def test_post_send_next_check_returns_none_at_max() -> None:
    result = post_send_next_check(NOW, 3, max_nudges=3, first_delay_hours=24.0, escalation_hours=[72.0, 168.0])
    assert result is None


def test_post_send_next_check_escalates_below_max() -> None:
    result = post_send_next_check(NOW, 1, max_nudges=3, first_delay_hours=24.0, escalation_hours=[72.0, 168.0])
    assert result == NOW + timedelta(hours=72)


def test_prohibited_window_rejects_malformed_input() -> None:
    with pytest.raises(ValueError):
        in_prohibited_window(NOW, ['not-a-window'])
