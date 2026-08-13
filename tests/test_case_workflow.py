import pytest
from fastapi import HTTPException

from services.case_service.app.main import ensure_transition


def test_case_lifecycle_allows_controlled_progression():
    ensure_transition('unverified', 'triage')
    ensure_transition('triage', 'open')
    ensure_transition('open', 'investigating')


def test_case_lifecycle_rejects_skipping_controls():
    with pytest.raises(HTTPException) as error:
        ensure_transition('unverified', 'closed')
    assert error.value.status_code == 409
