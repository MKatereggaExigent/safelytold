from dataclasses import dataclass


@dataclass(frozen=True)
class GovernanceGate:
    capability: str
    raw_evidence_allowed: bool = False
    human_approval_required: bool = True
    retention_days: int = 30


ALLOWED_CAPABILITIES = {
    'reporter_writing',
    'anonymity_scan',
    'triage_copilot',
    'evidence_chronology',
    'policy_retrieval',
    'investigation_summary',
    'translation',
    'pattern_analytics',
    'sla_remediation',
}


def assert_governed(gate: GovernanceGate) -> None:
    if gate.capability not in ALLOWED_CAPABILITIES:
        raise ValueError('Capability is not approved')
    if gate.raw_evidence_allowed:
        raise ValueError('Raw evidence must be transformed in the evidence enclave first')
