from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CaseWorkflowInput:
    tenant_id: str
    case_id: str
    severity: str
    jurisdiction: str
    acknowledgement_due_at: datetime
    target_resolution_at: datetime
    protection_required: bool = False


@dataclass
class CaseState:
    status: str = 'reported'
    assigned_investigator: str | None = None
    acknowledged: bool = False
    protection_plan_active: bool = False
    findings_submitted: bool = False
    decision_approved: bool = False
    appeal_open: bool = False
    history: list[str] = field(default_factory=list)
