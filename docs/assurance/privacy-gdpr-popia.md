# Privacy control mapping: GDPR and POPIA

This is a product-control mapping, not a jurisdictional legal opinion. For each tenant, the contract and
privacy schedule must identify responsible party/controller, operator/processor, lawful basis, purposes,
retention, data locations, subprocessors, transfer mechanism and data-subject contact route.

## Principles and controls

| GDPR / POPIA principle | SafelyTold control | Status / evidence required |
|---|---|---|
| Lawfulness, fairness, transparency | Mode-specific notices, trust centre, consent receipts, policy versions, neutral allegation language | Implemented foundation; local legal approval required |
| Purpose specification/limitation | Purpose claim required for staff auth; policy decisions and audit record purpose | Implemented; production access sampling required |
| Data minimisation | Optional identity, separate vault, structured intake, metadata-only events/logs | Implemented; periodic field inventory required |
| Accuracy/data quality | Reporter mailbox, correction/DSAR workflows, source-linked evidence and findings | Partial; production DSAR exercise required |
| Storage limitation | Configurable retention, legal hold and crypto-erasure design | Partial; approved records schedule and deletion proof required |
| Integrity/confidentiality/security safeguards | MFA, tenant scoping/RLS, encryption architecture, evidence integrity, malware scanning, audit | Implemented foundation; pen test/key/restore evidence required |
| Accountability | DPIA, audit chain, approvals, policy/version provenance, evidence register | Partial until DPO approval and operational records exist |
| Data-subject participation/rights | Access, correction, restriction, deletion review and export service surfaces | Partial; legal exceptions and SLA tests required |
| Security compromise/personal-data breach | Privacy incident event and runbook; regulator/data-subject workflow | Implemented foundation; tabletop exercise required |
| Cross-border transfers | Region-aware design and tenant deployment tier | Contractual/production configuration required |
| Processor/operator governance | Supplier DPA, subprocessor inventory, confidentiality, incident, deletion and audit terms | External procurement evidence required |

## GDPR-specific considerations

- Article 5 principles are reflected in minimisation, purpose binding, retention and accountability.
- Articles 12–22 rights require tenant-specific identity verification, exceptions and response workflow.
- Article 25 privacy by design/default is supported by optional identity and separated vault.
- Article 28 processor requirements belong in the DPA and supplier contracts.
- Article 30 records of processing must be maintained outside source code by SafelyTold and each controller.
- Articles 32–34 security and breach duties require production risk assessment and tested notification.
- Article 35 DPIA is required for high-risk processing; the current MVP DPIA is a draft pending approval.
- Chapter V transfer mechanisms must be chosen for actual hosting/subprocessors; architecture alone is
  not a transfer mechanism.

Special-category/criminal-allegation processing requires additional lawful-condition and access analysis.
SafelyTold does not infer health status or make automated adverse employment decisions.

## POPIA-specific considerations

- Accountability, processing limitation, purpose specification, further-processing limitation,
  information quality, openness, security safeguards and data-subject participation are mapped above.
- The tenant and SafelyTold must document Responsible Party/Operator roles and Information Officer duties.
- Operator contracts must require confidentiality, authorised processing and prompt security-compromise
  notice.
- Security safeguards require reasonable technical and organisational measures proportionate to risk;
  production pen testing, access review and restore evidence are necessary.
- Security-compromise handling must follow current Information Regulator requirements and counsel-approved
  notification decisions.
- Cross-border processing requires a documented section 72 basis where applicable.

## Privacy-safe analytics and AI

- Analytics suppress cohorts below a minimum threshold and prohibit individual complaint rankings.
- AI inputs must be redacted by default; raw evidence is disabled by configuration.
- AI cannot score credibility, guilt, loyalty, discipline, dismissal or mental health.
- AI output is advisory, source linked, recorded and subject to human review.
- Allegation content must not train general-purpose provider models without explicit lawful approval.

## Required tenant privacy schedule

Before go-live record: purposes; lawful bases/conditions; categories and subjects; notices; recipients;
subprocessors; regions/transfers; retention by record type; legal holds; DSAR identity checks and SLAs;
breach contacts; DPIA outcome; children's/vulnerable-person rules if applicable; union/collective agreement
requirements; and local whistleblowing/employment-law channels.

