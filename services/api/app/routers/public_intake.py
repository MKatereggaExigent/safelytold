"""Public intake endpoints for HELP ME submissions."""

import secrets
from datetime import datetime

from argon2 import PasswordHasher
from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from safelytold_common.ids import public_case_code, recovery_secret

from ..db import get_session
from ..models import Case, ReporterHandle, Tenant
from ..schemas import ReportReceipt, ReportSubmission


router = APIRouter(prefix="/public", tags=["public"])
password_hasher = PasswordHasher()


@router.post(
    "/tenants/{tenant_slug}/cases",
    response_model=ReportReceipt,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a HELP ME report",
)
async def create_case(
    submission: ReportSubmission,
    tenant_slug: str = Path(..., min_length=2, max_length=80),
    session: AsyncSession = Depends(get_session),
) -> ReportReceipt:
    tenant = await session.scalar(select(Tenant).where(Tenant.slug == tenant_slug))
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    case = Case(
        tenant_id=tenant.id,
        mode=submission.mode.value,
        jurisdiction_code=submission.jurisdiction_code.upper(),
        taxonomy_codes=[code.lower() for code in submission.taxonomy_codes],
        immediate_risk=submission.immediate_risk,
        questionnaire=submission.questionnaire.model_dump() if submission.questionnaire else None,
        sealed_narrative=submission.sealed_narrative,
        narrative_length=submission.narrative_length,
        created_at=datetime.utcnow(),
    )
    session.add(case)
    await session.flush()

    code = public_case_code()
    secret = recovery_secret()
    handle = ReporterHandle(
        tenant_id=tenant.id,
        case_id=case.id,
        public_code=code,
        secret_hash=password_hasher.hash(secret),
        mode=submission.mode.value,
    )
    session.add(handle)
    await session.commit()

    return ReportReceipt(case_id=str(case.id), public_code=code, recovery_secret=secret, mode=submission.mode)
