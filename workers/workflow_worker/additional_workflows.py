from __future__ import annotations

from datetime import timedelta
from typing import Any

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from .activities import anchor_case_milestone, record_audit_event, send_privacy_safe_notification


@workflow.defn
class RetaliationProtectionWorkflow:
    def __init__(self) -> None:
        self._concern: dict[str, Any] | None = None
        self._closed = False

    @workflow.run
    async def run(self, case_id: str) -> dict[str, Any]:
        checks_completed = 0
        for delay_days in (7, 30, 90):
            try:
                await workflow.wait_condition(lambda: self._concern is not None or self._closed, timeout=timedelta(days=delay_days))
            except TimeoutError:
                await workflow.execute_activity(
                    send_privacy_safe_notification,
                    {'template': 'retaliation-check-in', 'case_id': case_id},
                    start_to_close_timeout=timedelta(seconds=30),
                )
                checks_completed += 1
            if self._concern is not None:
                await workflow.execute_activity(
                    record_audit_event,
                    {'event_type': 'retaliation.concern_reported.v1', 'case_id': case_id, 'risk_band': self._concern.get('risk_band')},
                    start_to_close_timeout=timedelta(seconds=30),
                )
                return {'status': 'escalated', 'checks_completed': checks_completed}
            if self._closed:
                break
        return {'status': 'completed', 'checks_completed': checks_completed}

    @workflow.signal
    async def report_concern(self, concern: dict[str, Any]) -> None:
        self._concern = concern

    @workflow.signal
    async def close_protection(self) -> None:
        self._closed = True


@workflow.defn
class DisclosurePackageWorkflow:
    def __init__(self) -> None:
        self._approved_by: set[str] = set()
        self._cancelled = False

    @workflow.run
    async def run(self, package_id: str) -> dict[str, Any]:
        await workflow.wait_condition(lambda: len(self._approved_by) >= 2 or self._cancelled)
        if self._cancelled:
            return {'status': 'cancelled'}
        await workflow.execute_activity(
            anchor_case_milestone,
            {'batch_id': f'disclosure:{package_id}', 'package_id': package_id},
            start_to_close_timeout=timedelta(seconds=30),
        )
        await workflow.execute_activity(
            record_audit_event,
            {'event_type': 'disclosure.package.approved.v1', 'package_id': package_id},
            start_to_close_timeout=timedelta(seconds=30),
        )
        return {'status': 'approved', 'approver_count': len(self._approved_by)}

    @workflow.signal
    async def approve(self, approver_id: str) -> None:
        self._approved_by.add(approver_id)

    @workflow.signal
    async def cancel(self) -> None:
        self._cancelled = True


@workflow.defn
class RetentionReviewWorkflow:
    def __init__(self) -> None:
        self._legal_hold = False
        self._approved = False

    @workflow.run
    async def run(self, record_scope: str) -> dict[str, Any]:
        await workflow.wait_condition(lambda: self._approved)
        if self._legal_hold:
            return {'status': 'retained', 'reason': 'legal_hold'}
        await workflow.execute_activity(
            record_audit_event,
            {'event_type': 'retention.deletion_approved.v1', 'record_scope': record_scope},
            start_to_close_timeout=timedelta(seconds=30),
        )
        return {'status': 'approved_for_crypto_erasure'}

    @workflow.signal
    async def set_legal_hold(self, active: bool) -> None:
        self._legal_hold = active

    @workflow.signal
    async def approve_review(self) -> None:
        self._approved = True
