from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field, field_validator

from safelytold_common.taxonomy import validate_concern_categories


class PrivateJournalEntry(BaseModel):
    id: UUID
    owner_handle: str
    encrypted_payload: str
    created_at: datetime
    converted_to_report_at: datetime | None = None

class ReportMode(str):
    pass

class Report(BaseModel):
    id: UUID
    tenant_id: UUID
    reporter_handle_id: UUID
    mode: str = Field(pattern='^(anonymous|verified_anonymous|confidential|identified|external_referral)$')
    jurisdiction_code: str
    taxonomy_codes: list[str] = Field(min_length=1, max_length=10)
    immediate_risk: bool = False
    encrypted_narrative_ref: str
    status: str = 'unverified'

    @field_validator('taxonomy_codes')
    @classmethod
    def validate_taxonomy_codes(cls, values: list[str]) -> list[str]:
        return validate_concern_categories(values)

class ReportQuestionnaire(BaseModel):
    observable_conduct: list[str]
    approximate_dates: list[str]
    locations: list[str]
    witness_refs: list[str]
    impact_categories: list[str]
    preservation_requests: list[str]
