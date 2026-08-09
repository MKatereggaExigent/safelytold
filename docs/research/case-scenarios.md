# Case Scenario Library (Derived from Public Judgments)

These scenarios convert South African case law into product/user stories. Use them when defining onboarding flows, retaliation detection, and conflict rules.

## Scenario K-01 – Protected Disclosure Followed by Disciplinary Action
- **Source:** Kunene v Akani Egoli (Labour Court, 27 Feb 2026)
- **Summary:** Employee made a protected disclosure about irregularities; within days, the employer initiated disciplinary action leading to dismissal. Court ruled actions constituted occupational detriment.
- **Product Hooks:**
  - Temporal workflow logs disclosure timestamp.
  - HRIS integration detects new disciplinary notices linked to reporter → triggers retaliation alert.
  - Case handler cannot be reporting-line subordinate of implicated manager.
  - Protection plan prompts check-ins and legal reminders to tenant.

## Scenario M-01 – Bullying Allegations Against Line Manager
- **Source:** Modika v Industrial Development Corporation
- **Summary:** Whistleblower alleged systemic bullying/harassment by line manager; claimed subsequent detriment for disclosure.
- **Product Hooks:**
  - Intake taxonomy includes bullying + manager relationship.
  - Conflict graph excludes implicated manager’s hierarchy from case access.
  - Ombuds escalation route automatically offered.

## Scenario P-01 – Confidentiality Charges Post Disclosure
- **Source:** Pillay v Samancor Chrome
- **Summary:** After the employee raised concerns, employer charged them with confidentiality breaches and dismissed them; court deemed retaliatory.
- **Product Hooks:**
  - Platform stores evidence that disclosure was protected; generates documentation for labour litigation.
  - Retaliation detection tracks new confidentiality charges against reporter.
  - Tenant policy reminder: confidentiality clauses cannot nullify whistleblower rights.

Use these scenarios to test policy engine, retaliation detection, and reporting flows.
