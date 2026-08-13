from datetime import UTC,datetime,timedelta
import pytest
from pydantic import ValidationError
from services.protection_service.app.main import Complete,PlanIn
def test_high_risk_completion_shape_is_validated():
 assert Complete(risk_band='critical',escalation_id=None).risk_band=='critical'
def test_protection_plan_requires_measure():
 with pytest.raises(ValidationError):PlanIn(case_id='00000000-0000-0000-0000-000000000001',requested_measures=[],approved_measures=[],owner_ref='x',next_review_at=datetime.now(UTC)+timedelta(days=1))
