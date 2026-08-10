from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta


@dataclass(frozen=True, slots=True)
class NudgeDecision:
    due: bool
    reason: str
    next_check: datetime | None = None


def parse_window(value: str) -> tuple[time, time]:
    """Parse 'HH:MM-HH:MM' into (start, end). End may wrap past midnight."""
    start_text, end_text = value.split('-', 1)
    start = datetime.strptime(start_text.strip(), '%H:%M').time()
    end = datetime.strptime(end_text.strip(), '%H:%M').time()
    return start, end


def in_prohibited_window(now: datetime, windows: list[str] | None) -> bool:
    if not windows:
        return False
    current = now.astimezone(UTC).time()
    for raw in windows:
        start, end = parse_window(raw)
        if start <= end:
            if start <= current < end:
                return True
        else:
            if current >= start or current < end:
                return True
    return False


def next_attempt_at(
    attempts: int,
    now: datetime,
    *,
    first_delay_hours: float = 24.0,
    escalation_hours: list[float] | None = None,
) -> datetime:
    """Pull-only escalating cadence.

    attempts is the count already sent. The first nudge fires first_delay_hours
    after the triggering event; each later nudge waits longer (escalation_hours).
    """
    steps = escalation_hours or [72.0, 168.0]
    if attempts <= 0:
        delay = first_delay_hours
    else:
        index = min(attempts - 1, len(steps) - 1)
        delay = steps[index]
    return now.astimezone(UTC) + timedelta(hours=delay)


def decide_send(
    *,
    now: datetime,
    last_attempt_at: datetime | None,
    attempts: int,
    max_nudges: int = 3,
    allowed_channels: list[str] | None = None,
    prohibited_times: list[str] | None = None,
    neutral_message_only: bool = True,
    email_allowed: bool = True,
) -> NudgeDecision:
    """Decide whether a neutral email nudge may go out right now.

    Pull-only: nudges stop once attempts reach max_nudges. Honours
    SafeContactPreference channels and prohibited windows. A neutral_message_only
    preference is always satisfied because templates carry zero case content.
    """
    now = now.astimezone(UTC)
    channels = set(allowed_channels or [])
    if email_allowed and 'email' not in channels:
        return NudgeDecision(False, 'email channel not permitted by safe contact preferences')
    if attempts >= max_nudges:
        return NudgeDecision(False, f'maximum {max_nudges} nudges already sent')
    if in_prohibited_window(now, prohibited_times):
        return NudgeDecision(False, 'inside prohibited contact window')
    if neutral_message_only is False:
        # Safe default: only neutral-only contact is implemented. Require it.
        return NudgeDecision(False, 'only neutral_message_only preferences are supported')
    if last_attempt_at is None:
        return NudgeDecision(True, 'first nudge due')
    return NudgeDecision(True, 'escalation nudge due')


def post_send_next_check(
    now: datetime,
    attempts_after_send: int,
    *,
    max_nudges: int = 3,
    first_delay_hours: float = 24.0,
    escalation_hours: list[float] | None = None,
) -> datetime | None:
    if attempts_after_send >= max_nudges:
        return None
    return next_attempt_at(attempts_after_send, now, first_delay_hours=first_delay_hours, escalation_hours=escalation_hours)
