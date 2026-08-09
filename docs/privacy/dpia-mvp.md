# Data Protection Impact Assessment – MVP (Draft)

## 1. Overview
- Processing activity: HELP ME anonymous/confidential reporting, case management, evidence vault.
- Stakeholders: DPO, Legal, Security, Product, Independent Advisory.

## 2. Description of Processing
- Categories of data (reporter narratives, optional identity, evidence files, case metadata).
- Data subjects (employees, contractors, witnesses, subjects).
- Systems + vendors involved (Next.js, FastAPI, Postgres, object storage, Temporal, email/SMS providers).

## 3. Legal Basis & Purpose
- Legitimate interest / legal obligation (whistleblowing, OHSA, PDA).
- Contractual commitments with tenants.

## 4. Risk Assessment
- Use LINDDUN + STRIDE outputs (link to `docs/security/threat-model-phase1.md`).
- Evaluate impact × likelihood for privacy risks (deanonymisation, retaliation, unauthorised access).

## 5. Safeguards
- Technical: encryption, RLS, separation of identity realms, immutable audit.
- Organisational: trust charter, anti-retaliation rider, advisory oversight.

## 6. Residual Risk & Actions
- Document remaining high risks + mitigation roadmap.

## 7. Consultation
- Note consultations with employee reps, advisory board, regulators if required.

## 8. Approval
- DPO signature, date, next review.
