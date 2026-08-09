# KPI Measurement Plan (Phase 1 Output)

## Metric Catalogue (from §18.2)

| Metric | Definition | Data Source | Owner |
| --- | --- | --- | --- |
| Report completion rate | % of started HELP ME flows that reach submission | Frontend analytics (de-identified) | Product Analytics |
| Mailbox re-engagement | % of reporters sending/receiving follow-up messages | Mailbox service metrics | CX |
| Time to acknowledgement | Mean time from submission to triage acknowledgement | Temporal workflow logs | Case Ops |
| Conflict recusal rate | % of case assignments blocked by conflict rules | Policy service | Integrity |
| Retaliation concerns logged | Count + severity per case | Protection module | Protection Lead |
| Evidence completeness | Cases with hashed/sealed evidence per policy | Evidence service | Investigations |
| Access-policy violations | Unauthorized access attempts caught | Security monitoring | Security |
| Privacy/Security incidents | Number/impact per quarter | IR tracker | Security |
| Tenant renewal/expansion | Annual net revenue retention | GTM |

## Instrumentation Roadmap
- Implement privacy-preserving analytics on HELP ME funnel (no PII).
- Build Temporal metrics exporter.
- Add conflict-policy decision logs with aggregation, respecting ADR-009.
- Define protection-retaliation schema for consistent reporting.

## Reporting
- Monthly internal dashboard.
- Quarterly summary for advisory board (aggregated, anonymised).
