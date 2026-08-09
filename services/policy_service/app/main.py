from enum import StrEnum
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, Field

from safelytold_common.service import create_app

router = APIRouter(prefix='/v1/policy', tags=['policy'])


class Decision(StrEnum):
    ALLOW = 'allow'
    DENY = 'deny'
    REQUIRE_APPROVAL = 'require_approval'
    RECUSE = 'recuse'


class Input(BaseModel):
    tenant_id: UUID
    subject_id: str
    roles: set[str] = Field(default_factory=set)
    action: str
    resource_type: str
    resource_id: UUID
    purpose: str
    assigned_case_ids: set[UUID] = Field(default_factory=set)
    implicated_subject_ids: set[str] = Field(default_factory=set)
    requested_identity_access: bool = False
    dual_approval_count: int = 0


class Output(BaseModel):
    decision: Decision
    reasons: list[str]
    obligations: list[str] = Field(default_factory=list)


@router.post('/decide', response_model=Output)
async def decide(body: Input) -> Output:
    obligations = ['audit_access_reason', 'bind_to_declared_purpose']
    if body.subject_id in body.implicated_subject_ids:
        return Output(decision=Decision.RECUSE, reasons=['subject_is_implicated'])
    if not body.purpose or body.purpose == 'unspecified':
        return Output(decision=Decision.DENY, reasons=['purpose_required'])
    if body.requested_identity_access and body.dual_approval_count < 2:
        return Output(
            decision=Decision.REQUIRE_APPROVAL,
            reasons=['identity_vault_requires_dual_control'],
            obligations=obligations + ['notify_privacy_officer'],
        )
    if body.action.startswith('case:') and (
        body.resource_type != 'case' or body.resource_id not in body.assigned_case_ids
    ):
        return Output(decision=Decision.DENY, reasons=['case_assignment_required'])
    return Output(decision=Decision.ALLOW, reasons=['policy_conditions_satisfied'], obligations=obligations)


app = create_app('Policy and Authorisation Service', 'RBAC + ABAC + relationships/conflicts + purpose.', [router])
