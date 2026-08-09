from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID, uuid4

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, ForeignKey, LargeBinary, String, UniqueConstraint, select
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from safelytold_common.auth import ContextDep
from safelytold_common.db import Base, session
from safelytold_common.ids import public_case_code, recovery_secret
from safelytold_common.reporter_auth import create_reporter_token
from safelytold_common.service import create_app

from .crypto import decrypt_identity, encrypt_identity

router = APIRouter(prefix='/v1/reporter', tags=['reporter-identity'])
password_hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)

IDENTITY_REQUEST_ROLES = frozenset({'privacy_officer', 'legal_counsel', 'ombuds', 'platform_super_admin'})
IDENTITY_APPROVER_ROLES = frozenset({'privacy_officer', 'legal_counsel', 'ombuds'})
ACCESS_REQUEST_LIFETIME = timedelta(minutes=30)
REQUIRED_APPROVALS = 2


class Handle(Base):
    __tablename__ = 'reporter_handles'
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), unique=True)
    public_code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    secret_hash: Mapped[str] = mapped_column(String(300))
    tenant_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class VaultIdentity(Base):
    __tablename__ = 'vault_identities'
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), unique=True, index=True)
    encrypted_payload: Mapped[bytes] = mapped_column(LargeBinary)
    key_reference: Mapped[str] = mapped_column(String(200), default='local-development-envelope')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class VaultAccessRequest(Base):
    __tablename__ = 'vault_access_requests'
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    case_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    requester_subject_id: Mapped[str] = mapped_column(String(200), index=True)
    purpose: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(32), default='pending', index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revealed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class VaultAccessApproval(Base):
    __tablename__ = 'vault_access_approvals'
    __table_args__ = (
        UniqueConstraint('request_id', 'approver_subject_id', name='uq_vault_approval_request_approver'),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    request_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey('vault_access_requests.id', ondelete='CASCADE'),
        index=True,
    )
    approver_subject_id: Mapped[str] = mapped_column(String(200), index=True)
    approver_role: Mapped[str] = mapped_column(String(100))
    decision: Mapped[str] = mapped_column(String(16))
    rationale: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class CreateHandle(BaseModel):
    case_id: UUID


class CreatedHandle(BaseModel):
    case_id: UUID
    public_code: str
    recovery_secret: str = Field(description='Shown once')


class Login(BaseModel):
    public_code: str
    recovery_secret: str


class StoreIdentity(BaseModel):
    case_id: UUID
    identity: dict[str, Any]


class CreateAccessRequest(BaseModel):
    case_id: UUID
    purpose: str = Field(min_length=10, max_length=500)


class DecideAccessRequest(BaseModel):
    decision: Literal['approve', 'deny']
    rationale: str = Field(min_length=10, max_length=500)


def _require_any_role(context: ContextDep, allowed: frozenset[str]) -> str:
    matching = sorted(context.roles.intersection(allowed))
    if not matching:
        raise HTTPException(403, 'Role is not permitted to access the identity vault workflow')
    return matching[0]


def _expire_if_needed(request: VaultAccessRequest, now: datetime) -> None:
    if request.status in {'pending', 'approved'} and request.expires_at <= now:
        request.status = 'expired'


@router.post('/handles', response_model=CreatedHandle)
async def create_handle(body: CreateHandle, context: ContextDep, database: AsyncSession = Depends(session)) -> CreatedHandle:
    code = public_case_code()
    secret = recovery_secret()
    database.add(
        Handle(
            case_id=body.case_id,
            public_code=code,
            secret_hash=password_hasher.hash(secret),
            tenant_id=context.tenant_id,
        )
    )
    await database.commit()
    return CreatedHandle(case_id=body.case_id, public_code=code, recovery_secret=secret)


@router.post('/session')
async def login(body: Login, database: AsyncSession = Depends(session)) -> dict[str, Any]:
    handle = await database.scalar(select(Handle).where(Handle.public_code == body.public_code))
    if handle is None or handle.revoked_at is not None:
        raise HTTPException(401, 'Invalid credentials')
    try:
        password_hasher.verify(handle.secret_hash, body.recovery_secret)
    except VerifyMismatchError as exc:
        raise HTTPException(401, 'Invalid credentials') from exc
    token = create_reporter_token(
        case_id=handle.case_id,
        public_code=handle.public_code,
        handle_id=str(handle.id),
        tenant_id=handle.tenant_id,
    )
    return {
        'case_id': str(handle.case_id),
        'session': token,
        'expires_at': (datetime.now(UTC) + timedelta(minutes=30)).isoformat(),
    }


@router.post('/vault-identities', status_code=201)
async def store_identity(body: StoreIdentity, database: AsyncSession = Depends(session)) -> dict[str, str]:
    existing = await database.scalar(select(VaultIdentity).where(VaultIdentity.case_id == body.case_id))
    if existing is not None:
        raise HTTPException(409, 'Identity already stored for case')
    ciphertext = encrypt_identity(json.dumps(body.identity, separators=(',', ':')).encode())
    value = VaultIdentity(case_id=body.case_id, encrypted_payload=ciphertext)
    database.add(value)
    await database.commit()
    return {'identity_ref': str(value.id), 'case_id': str(body.case_id), 'status': 'vaulted'}


@router.post('/vault-access-requests', status_code=201)
async def create_access_request(
    body: CreateAccessRequest,
    context: ContextDep,
    database: AsyncSession = Depends(session),
) -> dict[str, Any]:
    _require_any_role(context, IDENTITY_REQUEST_ROLES)
    identity = await database.scalar(select(VaultIdentity.id).where(VaultIdentity.case_id == body.case_id))
    if identity is None:
        raise HTTPException(404, 'Vault identity not found')

    now = datetime.now(UTC)
    value = VaultAccessRequest(
        tenant_id=context.tenant_id,
        case_id=body.case_id,
        requester_subject_id=context.subject_id,
        purpose=body.purpose,
        expires_at=now + ACCESS_REQUEST_LIFETIME,
    )
    database.add(value)
    await database.commit()
    await database.refresh(value)
    return {
        'request_id': str(value.id),
        'case_id': str(value.case_id),
        'status': value.status,
        'purpose': value.purpose,
        'expires_at': value.expires_at,
        'required_approvals': REQUIRED_APPROVALS,
    }


@router.post('/vault-access-requests/{request_id}/approvals', status_code=201)
async def decide_access_request(
    request_id: UUID,
    body: DecideAccessRequest,
    context: ContextDep,
    database: AsyncSession = Depends(session),
) -> dict[str, Any]:
    approver_role = _require_any_role(context, IDENTITY_APPROVER_ROLES)
    request = await database.scalar(
        select(VaultAccessRequest).where(
            VaultAccessRequest.id == request_id,
            VaultAccessRequest.tenant_id == context.tenant_id,
        ).with_for_update()
    )
    if request is None:
        raise HTTPException(404, 'Vault access request not found')

    now = datetime.now(UTC)
    _expire_if_needed(request, now)
    if request.status == 'expired':
        await database.commit()
        raise HTTPException(410, 'Vault access request expired')
    if request.status not in {'pending', 'approved'}:
        raise HTTPException(409, f'Vault access request is {request.status}')
    if request.requester_subject_id == context.subject_id:
        raise HTTPException(403, 'Requester cannot approve their own identity access request')

    existing = await database.scalar(
        select(VaultAccessApproval.id).where(
            VaultAccessApproval.request_id == request.id,
            VaultAccessApproval.approver_subject_id == context.subject_id,
        )
    )
    if existing is not None:
        raise HTTPException(409, 'Approver has already decided this request')

    approval = VaultAccessApproval(
        request_id=request.id,
        approver_subject_id=context.subject_id,
        approver_role=approver_role,
        decision=body.decision,
        rationale=body.rationale,
    )
    database.add(approval)
    if body.decision == 'deny':
        request.status = 'denied'
    else:
        approved_subjects = set(
            (
                await database.scalars(
                    select(VaultAccessApproval.approver_subject_id).where(
                        VaultAccessApproval.request_id == request.id,
                        VaultAccessApproval.decision == 'approve',
                    )
                )
            ).all()
        )
        approved_subjects.add(context.subject_id)
        if len(approved_subjects) >= REQUIRED_APPROVALS:
            request.status = 'approved'

    await database.commit()
    return {
        'request_id': str(request.id),
        'decision': body.decision,
        'status': request.status,
        'approver_role': approver_role,
    }


@router.post('/vault-access-requests/{request_id}/reveal')
async def reveal_identity(
    request_id: UUID,
    response: Response,
    context: ContextDep,
    database: AsyncSession = Depends(session),
) -> dict[str, Any]:
    _require_any_role(context, IDENTITY_REQUEST_ROLES)
    request = await database.scalar(
        select(VaultAccessRequest).where(
            VaultAccessRequest.id == request_id,
            VaultAccessRequest.tenant_id == context.tenant_id,
        ).with_for_update()
    )
    if request is None:
        raise HTTPException(404, 'Vault access request not found')

    now = datetime.now(UTC)
    _expire_if_needed(request, now)
    if request.status == 'expired':
        await database.commit()
        raise HTTPException(410, 'Vault access request expired')
    if request.requester_subject_id != context.subject_id:
        raise HTTPException(403, 'Only the original requester may use the approved reveal')
    if request.status != 'approved':
        raise HTTPException(403, 'Two independent approvals are required before reveal')

    approved_subjects = set(
        (
            await database.scalars(
                select(VaultAccessApproval.approver_subject_id).where(
                    VaultAccessApproval.request_id == request.id,
                    VaultAccessApproval.decision == 'approve',
                )
            )
        ).all()
    )
    if len(approved_subjects) < REQUIRED_APPROVALS:
        raise HTTPException(403, 'Two independent approvals are required before reveal')

    value = await database.scalar(select(VaultIdentity).where(VaultIdentity.case_id == request.case_id))
    if value is None:
        raise HTTPException(404, 'Vault identity not found')

    request.status = 'revealed'
    request.revealed_at = now
    await database.commit()

    # Prevent intermediaries and browsers from caching the decrypted identity response.
    response.headers['Cache-Control'] = 'no-store, private, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['X-Content-Type-Options'] = 'nosniff'

    # Production deployment must emit a purpose-bound audit event without the decrypted payload.
    identity = json.loads(decrypt_identity(value.encrypted_payload))
    return {
        'identity_ref': str(value.id),
        'request_id': str(request.id),
        'purpose': request.purpose,
        'revealed_at': request.revealed_at,
        'identity': identity,
    }


app = create_app(
    'Reporter Identity Service',
    'Separate pseudonymous realm and isolated optional identity vault with dual-control reveal.',
    [router],
)
