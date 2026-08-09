"""Pydantic schemas for public intake endpoints."""

from enum import Enum
from typing import List, Literal

from pydantic import BaseModel, Field, constr


class ReportMode(str, Enum):
    ANONYMOUS = "anonymous"
    CONFIDENTIAL = "confidential"
    IDENTIFIED = "identified"


class Questionnaire(BaseModel):
    dates: str | None = Field(None, description="Approximate dates or ranges")
    locations: str | None = Field(None, description="Locations where the events occurred")
    witnesses: List[constr(strip_whitespace=True)] = Field(default_factory=list)
    impacts: List[str] = Field(default_factory=list)
    preservation_requests: List[str] = Field(default_factory=list)


class ReportSubmission(BaseModel):
    mode: ReportMode
    jurisdiction_code: constr(strip_whitespace=True, min_length=2, max_length=16)
    taxonomy_codes: List[constr(strip_whitespace=True, min_length=2, max_length=64)]
    immediate_risk: bool = False
    questionnaire: Questionnaire | None = None
    sealed_narrative: str = Field(..., description="Client-side encrypted narrative payload")
    narrative_length: int = Field(..., ge=0)


class ReportReceipt(BaseModel):
    case_id: str
    public_code: str
    recovery_secret: str
    mode: ReportMode
    message: str = "Keep this info safe – it is the only way to access your HELP ME mailbox."
