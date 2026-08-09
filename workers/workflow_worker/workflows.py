from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from .activities import (
        anchor_case_milestone,
        create_protection_plan,
        record_audit_event,
        request_conflict_check,
        schedule_retaliation_check,
        send_privacy_safe_notification,
    )
    from .models import CaseState, CaseWorkflowInput


@workflow.defn
class CaseLifecycleWorkflow:
    """Authoritative, replay-safe lifecycle. AI output never changes this state directly."""

    def __init__(self) -> None:
        self.state = CaseState()
        self._assignment: str | None = None
        self._acknowledge = False
        self._finding = False
        self._approve = False
        self._close = False
        self._appeal = False

    @workflow.run
    async def run(self, data: CaseWorkflowInput) -> CaseState:
        self.state.history.append('reported')
        await workflow.execute_activity(
            record_audit_event,
            {'event_type': 'case.reported.v1', 'case_id': data.case_id, 'tenant_id': data.tenant_id},
            start_to_close_timeout=timedelta(seconds=30),
        )
        await workflow.execute_activity(
            send_privacy_safe_notification,
            {'template': 'case-received', 'case_id': data.case_id},
            start_to_close_timeout=timedelta(seconds=30),
        )
        if data.protection_required:
            await workflow.execute_activity(
                create_protection_plan,
                {'case_id': data.case_id, 'tenant_id': data.tenant_id},
                start_to_close_timeout=timedelta(seconds=30),
            )
            self.state.protection_plan_active = True
            await workflow.execute_activity(
                schedule_retaliation_check,
                {'case_id': data.case_id},
                start_to_close_timeout=timedelta(seconds=30),
            )

        while True:
            await workflow.wait_condition(lambda: self._assignment is not None)
            check = await workflow.execute_activity(
                request_conflict_check,
                {'case_id': data.case_id, 'candidate_id': self._assignment},
                start_to_close_timeout=timedelta(seconds=30),
            )
            if check['decision'] == 'allow':
                break
            self.state.status = 'assignment_blocked'
            self.state.history.append('assignment_blocked')
            self._assignment = None
        self.state.assigned_investigator = self._assignment
        self.state.status = 'triage'
        self.state.history.append('assigned')

        await workflow.wait_condition(lambda: self._acknowledge)
        self.state.acknowledged = True
        self.state.status = 'investigation'
        self.state.history.append('acknowledged')

        await workflow.wait_condition(lambda: self._finding)
        self.state.findings_submitted = True
        self.state.status = 'decision_review'
        self.state.history.append('finding_submitted')

        await workflow.wait_condition(lambda: self._approve)
        self.state.decision_approved = True
        self.state.status = 'remediation'
        self.state.history.append('decision_approved')

        await workflow.wait_condition(lambda: self._close)
        self.state.status = 'closed'
        self.state.history.append('closed')
        await workflow.execute_activity(
            anchor_case_milestone,
            {'batch_id': f'case-close:{data.case_id}', 'case_id': data.case_id},
            start_to_close_timeout=timedelta(seconds=30),
        )
        try:
            await workflow.wait_condition(lambda: self._appeal, timeout=timedelta(days=30))
        except TimeoutError:
            return self.state
        self.state.appeal_open = True
        self.state.status = 'appeal'
        self.state.history.append('appeal_opened')
        return self.state

    @workflow.signal
    async def assign(self, investigator_id: str) -> None:
        self._assignment = investigator_id

    @workflow.signal
    async def acknowledge(self) -> None:
        self._acknowledge = True

    @workflow.signal
    async def submit_findings(self) -> None:
        self._finding = True

    @workflow.signal
    async def approve_decision(self) -> None:
        self._approve = True

    @workflow.signal
    async def close(self) -> None:
        self._close = True

    @workflow.signal
    async def open_appeal(self) -> None:
        self._appeal = True

    @workflow.query
    def current_state(self) -> CaseState:
        return self.state
