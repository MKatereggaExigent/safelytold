from prefect import serve

from .capability_flows import (
    anonymity_scan,
    evidence_chronology,
    investigation_summary,
    pattern_analytics,
    policy_retrieval,
    reporter_writing,
    sla_remediation,
    translation,
    triage_copilot,
)
from .flows import retention_scan


if __name__ == '__main__':
    serve(
        reporter_writing.to_deployment(name='reporter-writing-assistant', tags=['reporter', 'privacy-gated']),
        anonymity_scan.to_deployment(name='anonymity-risk-scan', tags=['reporter', 'privacy-gated']),
        triage_copilot.to_deployment(name='triage-copilot', tags=['staff', 'human-review']),
        evidence_chronology.to_deployment(name='evidence-chronology-agent', tags=['evidence', 'human-review']),
        policy_retrieval.to_deployment(name='policy-retrieval-agent', tags=['policy', 'human-review']),
        investigation_summary.to_deployment(name='investigation-summary-agent', tags=['investigation', 'human-review']),
        translation.to_deployment(name='translation-agent', tags=['language', 'human-review']),
        pattern_analytics.to_deployment(name='privacy-safe-pattern-agent', tags=['analytics', 'thresholded']),
        sla_remediation.to_deployment(name='sla-remediation-agent', tags=['workflow', 'human-review']),
        retention_scan.to_deployment(name='retention-scan', tags=['privacy', 'records-management']),
    )
