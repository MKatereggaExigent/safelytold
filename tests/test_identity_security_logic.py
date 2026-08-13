import pytest
from fastapi import HTTPException
from services.identity_service.app.main import validate_role
from services.security_monitor_service.app.main import AlertIn
def test_unknown_identity_role_is_rejected():
 with pytest.raises(HTTPException):validate_role('super_duper_admin')
def test_security_context_model_accepts_privacy_safe_metadata():
 alert=AlertIn(alert_type='repeated_denial',severity='high',resource_ref='case/commitment',privacy_safe_context={'count':7})
 assert alert.privacy_safe_context=={'count':7}
