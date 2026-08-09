# Secondary Evidence Corpus – Phase 1

This document aggregates publicly available research, regulator guidance and case law relevant to HELP ME. Each entry captures the source, stakeholder lens, findings and product implications. Primary interviews (Phase 1 R1–R5) will validate or adjust these hypotheses.

## 1. Workplace Reporting & Violence Benchmarks

| Source | Stakeholder | Key Findings | Product Implications |
| --- | --- | --- | --- |
| ILO & Gallup global study on violence and harassment (2022) | Employees | ~23% of workers reported experiencing workplace violence or harassment; prevalence spans all regions and genders. | Justifies global scope, multilingual support, and trauma-informed UX. Intake must accommodate multiple harm types (physical, psychological, sexual) and allow reporting beyond physical offices. |
| NAVEX 2026 benchmark (2.37M reports from 4,052 organisations, ~77M employees) | Ethics/compliance handlers | Median reporting rate rose to 1.65 reports per 100 employees; retaliation concerns remain a top reason for silence. | Configure KPIs (reports per 100 EE) and dashboards; emphasise retaliation protections and follow-up SLAs. |
| ACFE 2024 occupational fraud study | Investigations/compliance | 43% of detected fraud cases discovered via tips; 50%+ of tips came from employees. | Reinforces need for confidential channels, evidence handling, and analytics to detect fraud-related allegations. |
| Transparency International 2026 assessment | Advocacy / legal | 150+ countries have whistleblower laws but retaliation/confidentiality failures persist. | Strengthens requirement for separate identity vault, dual approvals for disclosure, and tenant governance audits. |

## 2. Handler & Compliance Evidence

| Source | Key Insight | Implication |
| --- | --- | --- |
| NAVEX & Protect (UK) case experience | Organisations with dedicated response teams and transparent SLAs achieve higher reporter trust. | Temporal workflows must encode configurable acknowledgement/feedback deadlines (e.g., 7 days + 3 months per EU directive). |
| SEC/OSHA/EEOC guidance | Independent escalation and anti-retaliation protocols are scrutinised in enforcement actions. | Align trust charter + contract rider; ensure logs/audit can prove compliance. |

## 3. Investigator & Regulator Standards

| Source | Insight | Implication |
| --- | --- | --- |
| South African Labour Court, Kunene v Akani Egoli (2026) | Disciplinary action immediately after a protected disclosure was deemed occupational detriment; court awarded eight months’ remuneration. | Retaliation engine should flag case-linked HR actions and enforce independent review. |
| Modika v Industrial Development Corporation | Whistleblower alleged bullying by line manager followed by detriment. | Case assignment must prevent implicated manager’s influence; conflict graph essential. |
| Pillay v Samancor Chrome | Protected disclosure followed by confidentiality charges/dismissal ruled retaliatory. | Document evidence of good-faith disclosures; ensure tenant policies prohibit using confidentiality clauses to silence reporters. |

## 4. Remote & Non-Traditional Work Contexts

| Source | Finding | Implication |
| --- | --- | --- |
| SA Harassment Code (2022) & Department of Employment and Labour guidance | Harassment protections apply to remote work, travel, communications, events, customer interactions. | Taxonomy must include channels like Teams/Slack/WhatsApp, business travel, client sites; intake allows specifying context. |

## 5. Psychological Safety & Negative Reporting Systems

| Source | Finding | Implication |
| --- | --- | --- |
| 2025 study on coworker-reporting systems in operating rooms | Poorly designed reporting tools caused perceived bullying, fear, reduced wellness among subjects. | Embed fairness controls: prevent revenge reporting, require structured fact capture, enforce human review, bar popularity metrics, narrow access to allegations. |

## 6. Anonymity & Retaliation Research

| Source | Finding | Implication |
| --- | --- | --- |
| Experimental study (citation pending) on anonymous vs identified reporting | Prior retaliation reduces willingness for identified reporting but not anonymous. | Validates anonymous identity realm, pseudonymous mailbox, separate identity vault, and dual-control disclosure. |
| Studies on expected retaliation cost | Higher perceived retaliation cost lowers intention to report wrongdoing. | Reinforces anti-retaliation UX messaging, optional safe-contact feature, and protection plans. |

## 7. Regulatory Requirements (Non-exhaustive)

| Source | Requirement | Product Action |
| --- | --- | --- |
| EU Whistleblower Directive | Secure internal channels, acknowledgement ≤7 days, feedback ≤3 months, impartial follow-up. | Temporal workflow templates with configurable timers; UI copy referencing deadlines. |
| POPIA + Information Regulator guidance | Mandatory PIIA/PIA, breach notification “as soon as reasonably possible”, defined operator/responsible parties. | DPIA template (`docs/privacy/dpia-mvp.md`), incident runbook, control-plane metadata. |
| Protected Disclosures Act 26 of 2000 | Protects workers making disclosures about unlawful/irregular conduct; occupational detriment prohibited. | Product must track disclosure categories, provide documentation of disclosures, and support evidence for PDA coverage. |

## 8. Taxonomy Enhancements

Based on the harassment Code, case law and studies, the intake taxonomy must cover:

- Physical, psychological, sexual harassment (remote/in-person)
- Bullying, discrimination, retaliation, fraud, safety hazards
- Channels: in-person, chat/IM, email, phone, video meetings, travel, events, customer interactions
- Perpetrator relationships: manager, peer, contractor, client, third party

## 9. Scenario Library

See `docs/research/case-scenarios.md` for anonymised flows derived from Kunene, Modika, Pillay and other cases to drive acceptance criteria.

## 10. Next Steps

1. Continue harvesting public sources (SAFLII, Transparency International, regulator reports) and tag entries with metadata.
2. Use this corpus to craft interview guides, personas and JTBD statements.
3. During primary interviews, validate each hypothesis: confirm, refine or reject; document variance.

_Citations:_ ILO/Gallup 2022 Workplace Violence and Harassment study; NAVEX 2026 Benchmark Report; ACFE 2024 Report to the Nations; Transparency International 2026 Whistleblower Protection Report; Kunene v Akani Egoli (LC); Modika v IDC; Pillay v Samancor Chrome; SA Harassment Code 2022; EU Directive 2019/1937; POPIA guidance; 2025 OR coworker-reporting study.
