from uuid import uuid4
from services.policy_service.app.main import Decision, Input, decide


async def test_identity_access_needs_dual_control() -> None:
    result = await decide(Input(tenant_id=uuid4(),subject_id='a',action='identity:read',resource_type='identity',resource_id=uuid4(),purpose='privacy-incident',requested_identity_access=True,dual_approval_count=1))
    assert result.decision == Decision.REQUIRE_APPROVAL


async def test_implicated_subject_is_recused() -> None:
    result = await decide(Input(tenant_id=uuid4(),subject_id='a',action='case:read',resource_type='case',resource_id=uuid4(),purpose='investigation',implicated_subject_ids={'a'}))
    assert result.decision == Decision.RECUSE
