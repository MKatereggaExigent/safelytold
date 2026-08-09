import asyncio
import os

from temporalio.client import Client
from temporalio.worker import Worker

from .activities import (
    anchor_case_milestone,
    create_protection_plan,
    record_audit_event,
    request_conflict_check,
    schedule_retaliation_check,
    send_privacy_safe_notification,
)
from .additional_workflows import DisclosurePackageWorkflow, RetaliationProtectionWorkflow, RetentionReviewWorkflow
from .workflows import CaseLifecycleWorkflow


async def main() -> None:
    client = await Client.connect(
        os.getenv('TEMPORAL_ADDRESS', 'temporal:7233'),
        namespace=os.getenv('TEMPORAL_NAMESPACE', 'default'),
    )
    worker = Worker(
        client,
        task_queue=os.getenv('TEMPORAL_TASK_QUEUE', 'safelytold-case-lifecycle'),
        workflows=[CaseLifecycleWorkflow, RetaliationProtectionWorkflow, DisclosurePackageWorkflow, RetentionReviewWorkflow],
        activities=[
            record_audit_event,
            request_conflict_check,
            send_privacy_safe_notification,
            create_protection_plan,
            schedule_retaliation_check,
            anchor_case_milestone,
        ],
    )
    await worker.run()


if __name__ == '__main__':
    asyncio.run(main())
