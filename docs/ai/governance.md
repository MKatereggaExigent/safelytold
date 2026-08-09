# AI governance

## Allowed bounded capabilities

Reporter writing assistance, anonymity-risk hints, triage suggestions, chronology extraction from sanitised derivatives, policy retrieval, investigator summary drafts, translation, thresholded pattern analysis and SLA/remediation recommendations.

## Mandatory controls

- Provider-agnostic AI gateway; no direct model calls from domain services.
- Redaction and data classification before inference.
- Customer/provider training disabled contractually and technically.
- Region and model allowlists, version pinning and egress controls.
- Source references, uncertainty and human approval recorded.
- Prompt, retrieval and tool permissions scoped by case assignment and purpose.
- Prompt-injection scanning and untrusted-document isolation.
- Evaluation sets for factuality, bias, privacy leakage, overreach and refusal.
- No automated writes to findings, decisions, remedies or identity disclosures.

## Agent design

Use small purpose-specific agents with explicit tools and budgets. Events may start an AI workflow, but AI cannot consume raw event-bus content or become the system of record. Prefect coordinates sanitisation, inference, evaluation and approval; Temporal resumes the case only after a signed human decision.
