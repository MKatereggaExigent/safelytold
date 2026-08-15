# SafelyTold commercial product onboarding

Audience: sales, marketing, partnerships, bid teams and customer-success staff.

Purpose: enable a non-technical team member to explain the complete product, demonstrate it safely, answer normal questions and escalate anything that needs specialist authority.

## 1. The explanation to master

SafelyTold is a multi-tenant integrity-reporting and case-management SaaS platform. It gives people safe ways to raise concerns and gives authorised organisations controlled tools to receive, triage, investigate, protect, communicate, decide, report and audit those concerns.

It is designed around four promises:

1. A reporter can choose an appropriate reporting mode.
2. Case handlers see only what their tenant, role, assignment and purpose permit.
3. Important actions are recorded and evidence integrity can be verified.
4. Technology assists people but does not make credibility, disciplinary or identity-disclosure decisions.

Do not describe SafelyTold merely as a “whistleblowing form.” The product includes reporter engagement, case operations, protection, privacy, evidence, analytics, assurance and operational controls.

## 2. The four reporting modes

Always name all four modes correctly.

| Mode | Meaning | Identity treatment | Appropriate explanation |
| --- | --- | --- | --- |
| Anonymous | The reporter does not provide an identity. | No identity is collected for case handlers. | “You can report without telling the organisation who you are.” |
| Verified Anonymous | Eligibility is verified using an unlinkable credential while identity remains hidden. | The eligibility proof must not become a staff identity in the case. | “The system can verify that a person is eligible without revealing which eligible person reported.” |
| Confidential | Identity/contact information is supplied but segregated and tightly controlled. | Stored in the separate protected identity path; disclosure is not routine. | “Authorised handling can maintain contact while the reporter’s identity remains restricted.” |
| Identified | The reporter elects to have their identity associated with the report. | Identity is processed according to policy, lawful basis and access controls. | “The reporter chooses to proceed with their identity on record.” |

Verified Anonymous is not the same as Anonymous. It depends on an unlinkable eligibility-credential arrangement configured for the customer. Never claim that a normal staff login or ordinary access code is cryptographically unlinkable.

## 3. What the platform does

### Reporter experience

- Structured electronic reporting with jurisdiction, reporter type, reporting mode, categories, facts, dates, locations, witnesses, impact and preservation requests.
- A generated reference and recovery credential.
- A secure two-way mailbox.
- Case-status tracking without exposing internal privileged material.
- Retaliation concerns, conflict challenges and safe-contact preferences.
- Emergency guidance and support information.
- A private journal/control room for preparing information before submission.
- English, Afrikaans and isiZulu interfaces, with the translation framework used across reporter and staff applications.

### Organisation experience

- Tenant-isolated dashboard and case queue.
- Case status controls and reasoned transitions.
- Categorised allegations and conflict-cleared assignments.
- Investigation planning, findings, independent review and appeals.
- Evidence upload, scanning, hashing, integrity receipts and legal holds.
- Protected mailbox communication.
- Protection plans and retaliation check-ins.
- Consent-linked support referrals.
- Privacy requests and breach assessment.
- Cohort-thresholded analytics and management reporting.
- Awareness, training, QA, continuity, 24/7 coverage, hotline and reporting operational records.
- Security alert triage, audit records and integrity-ledger verification.
- Keycloak-backed MFA, tenant roles and scoped access grants.

### Platform-owner experience

- Organisation onboarding and regional/tenancy configuration.
- Restricted platform architecture and assurance views.
- Security and service-health oversight.
- No standing entitlement to read tenant case narratives simply because someone is a platform administrator.

## 4. Public URL directory

Production base: `https://safelytold.com`

Local demonstration base: `http://localhost:8100`

Replace the base only; the paths below remain the same.

### Public and reporter pages

| Page | Production URL | What to use it for |
| --- | --- | --- |
| Home | https://safelytold.com/ | Product introduction and entry point. |
| Submit a report | https://safelytold.com/report | Start the structured reporting journey and select one of four modes. |
| Track a case | https://safelytold.com/case | Enter recovery details and access case status. |
| Secure mailbox | https://safelytold.com/mailbox | Reporter communication surface. |
| Private journal | https://safelytold.com/journal | Prepare and organise a concern before reporting. |
| Reporter control room | https://safelytold.com/control-room | Reporter-owned workspace overview. |
| Control-room mailbox | https://safelytold.com/control-room/mailbox | Reporter mailbox within the control room. |
| Control-room case | https://safelytold.com/control-room/case | Reporter case tracking within the control room. |
| Control-room support | https://safelytold.com/control-room/support | Support resources and referrals. |
| Support | https://safelytold.com/support | Public support information. |
| Emergency guidance | https://safelytold.com/emergency | Immediate-risk guidance; it is not an emergency-response service. |
| Pricing | https://safelytold.com/pricing | Published packaging overview; confirm contractual pricing with Commercial. |

### Public trust pages

| Page | Production URL | What it explains |
| --- | --- | --- |
| Trust overview | https://safelytold.com/trust | Trust model and assurance themes. |
| Governance | https://safelytold.com/trust/governance | Fair process, least privilege and human accountability. |
| Integrity | https://safelytold.com/trust/integrity | Evidence and record-integrity approach. |
| Privacy | https://safelytold.com/trust/privacy | Identity separation, purpose limitation and retention principles. |
| AI | https://safelytold.com/trust/ai | Permitted assistance and prohibited automated authority. |
| Reports | https://safelytold.com/trust/reports | Transparency and aggregate reporting approach. |
| Verify | https://safelytold.com/trust/verify | Integrity-proof verification. |

The detailed architecture page is intentionally not public. It is restricted to authorised platform owners at `/staff/architecture`.

### Authenticated staff pages

| Page | Production URL | Primary user |
| --- | --- | --- |
| Sign in | https://safelytold.com/staff/login | All authorised staff. |
| Dashboard | https://safelytold.com/staff/dashboard | Operational overview. |
| Demo tour | https://safelytold.com/staff/demo | Demo-tenant users only. |
| Cases | https://safelytold.com/staff/cases | Triage and case teams. |
| Case workspace | `https://safelytold.com/staff/cases/{case-id}` | Assigned case team. |
| Mailbox | https://safelytold.com/staff/mailbox | Authorised case communicators. |
| Evidence | https://safelytold.com/staff/evidence | Investigators/evidence handlers. |
| Protection | https://safelytold.com/staff/protection | Case managers/protection officers. |
| Support circle | https://safelytold.com/staff/support | Support coordinators/case managers. |
| Analytics | https://safelytold.com/staff/analytics | Management and reporting users. |
| Operations | https://safelytold.com/staff/operations | Training, QA, continuity, coverage, hotline and reporting operations. |
| Organisation administration | https://safelytold.com/staff/admin | Allowlisted platform super-administrator. |
| Identity and access | https://safelytold.com/staff/identity | Tenant administrator. |
| Security monitoring | https://safelytold.com/staff/security | Security analyst. |
| Privacy room | https://safelytold.com/staff/privacy | Privacy officer. |
| AI copilot | https://safelytold.com/staff/ai | Authorised assisted workflows. |
| Integrity ledger | https://safelytold.com/staff/ledger | Integrity verification and anchors. |
| Audit log | https://safelytold.com/staff/audit | Audit/assurance roles. |
| Platform architecture | https://safelytold.com/staff/architecture | Allowlisted platform super-administrator only. |
| Assurance register | https://safelytold.com/staff/admin/assurance | Allowlisted platform super-administrator only. |

Do not send staff URLs as if they are public brochures. Access depends on the tenant and Keycloak roles, and a user may correctly receive “access denied.”

## 5. How to run a safe demonstration

### Before the call

1. Confirm that the demonstration tenant is available and clearly marked synthetic.
2. Use a named demo persona appropriate to the audience.
3. Test login, MFA, gateway health and the pages you intend to show.
4. Close unrelated browser tabs and disable personal notifications.
5. Never use a production customer tenant or real report.
6. Agree whether the audience wants a reporter journey, operations journey, security review or all three.

### Recommended 30-minute journey

1. Open the public home and Trust Centre.
2. Explain the four reporting modes on the reporting page.
3. Show reference/recovery and the reporter mailbox concept.
4. Sign in as `demo.case-manager` and open the demo tour.
5. Show the dashboard, case queue and one synthetic case.
6. Explain conflict-cleared assignment and separation of roles.
7. Show evidence integrity, protection and mailbox.
8. Show privacy-thresholded analytics and operational readiness records.
9. End with audit, security and the Trust Centre.

### Demo personas

| Username | Demonstrates |
| --- | --- |
| `demo.owner` | Tenant ownership and identity/access administration. |
| `demo.case-manager` | Triage, case lifecycle, assignment and communication. |
| `demo.investigator` | Investigation and findings. |
| `demo.reviewer` | Independent review, decision and appeal. |
| `demo.privacy` | Consent, data-subject requests and breach handling. |
| `demo.protection` | Protection plans and retaliation monitoring. |
| `demo.support` | Support directory and consent-linked referrals. |
| `demo.security` | Security alerts and containment. |
| `demo.auditor` | Audit and assurance review. |

Credentials must be supplied through an approved secure channel. Do not put passwords in proposals, slide decks, CRM notes or email campaigns. Demo accounts are temporary, MFA-enforced and bound to the fixed demo tenant.

### First login to the local demo

1. Open `http://localhost:8100/staff/login`.
2. Select **Sign in**. The browser redirects to the SafelyTold Keycloak realm at `http://localhost:8080`.
3. Enter one demo username and the temporary password supplied through the approved secure channel.
4. Replace the temporary password when prompted. This changes the password for that persona only.
5. Scan the Keycloak QR code with an authenticator application.
6. Enter the current six-digit time-based code to complete MFA enrolment.
7. After redirection, open `http://localhost:8100/staff/demo`.
8. Use **Sign out** before changing to a different persona.

If an old development session previously allowed access without login, clear the site data for `localhost:8100` or remove the `wpc:session` local-storage entry and reload. With development authentication disabled, the application also rejects that stored development session and redirects protected paths to `/staff/login`.

Never disable MFA or re-enable development authentication to make a customer demonstration easier.

## 6. User guides

### Reporter guide

1. Start at `/report` and confirm the intended organisation/channel.
2. Read the privacy and safety information before selecting a mode.
3. Choose Anonymous, Verified Anonymous, Confidential or Identified deliberately.
4. Provide observable facts rather than conclusions where possible.
5. Avoid uploading unnecessary third-party personal information.
6. Save the case reference and recovery secret separately and securely.
7. Use `/case` or `/mailbox` to return; do not create repeated reports merely to request an update.
8. Use `/emergency` for guidance when immediate harm may exist, but contact the appropriate emergency service directly.

Do not promise that anonymity prevents identification through facts the reporter chooses to disclose. The platform can minimise technical identity collection; a narrative, attachment or workplace context can still identify someone indirectly.

### Case-handler guide

1. Sign in through `/staff/login` and complete MFA.
2. Confirm the visible tenant and declared purpose.
3. Work from the case queue; do not copy case information to private notes or personal email.
4. Record a reason for every status transition.
5. Complete conflict checking before assignment.
6. Use the protected mailbox for reporter communication.
7. Store evidence in the evidence vault, not in chat or ordinary shared drives.
8. Start a protection plan where retaliation or safety risk exists.
9. Keep findings evidence-balanced and route them for independent review.
10. Use approved closure and appeal paths; do not silently remove or overwrite records.

### Tenant-administrator guide

1. Tenant administration manages identities, roles and configuration; it does not create ownership over case truth.
2. Grant the least role needed and use scoped/time-bound grants for exceptional access.
3. Never grant `platform_super_admin` to ordinary tenant staff.
4. Review dormant users, assignments and grants regularly.
5. Keep role approval evidence outside the hands of the person requesting access.
6. Escalate identity-vault disclosure rather than attempting to work around it.

### Management-reporting guide

1. Use aggregate analytics rather than raw case narratives for management reporting.
2. Small cohorts are suppressed below the privacy threshold.
3. Explain a suppressed value as a privacy control, not missing data.
4. Do not combine exported aggregates with other data to re-identify reporters.
5. Record the reporting period, approval and distribution through Operations.

## 7. Standard questions and approved answers

### “Can anyone create a staff account?”

No. Public staff registration is disabled. Staff identities are provisioned by authorised administrators, tied to a tenant and roles, and protected by MFA.

### “Can SafelyTold identify an anonymous reporter?”

Ordinary case handlers do not receive an anonymous identity. Confidential identity data follows a separate protected path. Do not promise absolute anonymity where a reporter’s own facts, files, device or surrounding circumstances may identify them.

### “Is Verified Anonymous already available to every customer?”

The product models and validates Verified Anonymous as a distinct mode. Its use requires an approved unlinkable eligibility-credential configuration for that customer. Escalate solution design before committing it contractually.

### “Is it POPIA/GDPR compliant?”

Say: “SafelyTold includes controls designed to support POPIA and GDPR obligations, including minimisation, purpose-bound access, privacy workflows and tenant isolation. Compliance depends on the customer’s purposes, configuration, contracts and operations, so Legal/Privacy confirms the final position.”

Never say that software alone “makes a customer compliant.”

### “Is SafelyTold SOC 2 certified?”

Do not claim certification unless Commercial has the current signed report or certificate approved for distribution. The platform has a SOC 2 readiness and evidence programme; readiness is not certification.

### “Is the blockchain storing reports?”

No. The ledger stores integrity anchors such as hashes and Merkle roots, not report narratives or reporter identities. It supports tamper evidence; it does not replace access control, evidence handling or audit review.

### “Do you provide a 24/7 hotline?”

SafelyTold includes hotline intake records, escalation and coverage controls. A real 24/7 telephone service depends on the contracted hotline operator, number provisioning, languages, scripts, service levels and integration testing. Confirm the customer-specific arrangement with Operations before making a commitment.

### “Does AI decide whether someone is telling the truth?”

No. AI may help with writing, translation, structured review or aggregate patterns. It must not determine credibility, guilt, discipline, identity disclosure or final case outcomes.

### “Can data be hosted in our region or environment?”

The tenancy model supports shared database, dedicated database, dedicated data plane and customer-environment patterns. Region, keys, recovery objectives, integrations and cost require a technical solution design.

### “Can platform administrators read every case?”

No standing access is implied by platform administration. Tenant, purpose, role, assignment and exceptional approval controls remain relevant. Infrastructure privilege and break-glass risk must be covered in the customer security design.

## 8. Bid and procurement response procedure

1. Record the exact question and mandatory wording.
2. Mark whether the answer concerns current capability, configuration, roadmap, certification or contractual service.
3. Use evidence from the Trust Centre and approved repository documents.
4. Do not convert “supports,” “designed for,” “readiness” or “available with configuration” into “certified,” “guaranteed” or “deployed.”
5. Route security questionnaires to Security, privacy questions to Privacy/Legal, and architecture/integration questions to the technical team.
6. Require approval before stating recovery objectives, uptime, retention periods, geographic residency, hotline SLAs, penetration-test outcomes or certifications.
7. Store the approved final response with its date, product version and approving owner.

## 9. Escalation rules

Escalate immediately when the caller asks about:

- breach or security incidents;
- suspected reporter identification or retaliation;
- subpoenas, law-enforcement demands, litigation holds or regulator contact;
- exact POPIA/GDPR roles, lawful basis or cross-border transfers;
- certifications, penetration tests or vulnerability details;
- custom SSO, SCIM, identity federation or privileged access;
- dedicated infrastructure, data residency, customer-managed keys or disaster recovery;
- integrations, API limits, bulk migration or custom workflow;
- hotline numbers, country coverage, recording, consent or 24/7 SLA;
- contractual uptime, RTO/RPO, indemnity, insurance or liability;
- blockchain network, gas/cost, custody or legal admissibility;
- Verified Anonymous credential design;
- any request for architecture diagrams not approved for public distribution.

### Escalation ownership

| Question | Primary escalation | Secondary |
| --- | --- | --- |
| Product fit/workflow | Product | Solution architecture |
| Security questionnaire | Security | Technical lead |
| Privacy/legal/regulatory | Privacy/legal | Security |
| SSO, APIs, integrations, migration | Solution architecture | Engineering |
| Availability, recovery, support | Operations/SRE | Technical lead |
| Hotline/24-hour service | Operations | Privacy/legal |
| Pricing, SLA, contract | Commercial | Legal/Operations |
| AI governance | AI governance owner | Privacy/Security |

### Information to capture

- organisation, country and industry;
- contact name, role and approved contact route;
- question verbatim;
- affected tenant/environment, if any;
- bid deadline or business urgency;
- data types, user volumes and expected report volume;
- required countries, languages and reporting channels;
- requested integrations and identity provider;
- certifications or contract terms requested;
- whether the matter is a sales enquiry, active incident or legal demand.

Never put report narratives, reporter identities, recovery secrets, passwords or evidence in CRM notes or escalation email.

## 10. Commercial do and do not list

### Do

- Use the four reporting-mode names consistently.
- Say which capability is standard, configurable or externally contracted.
- Demonstrate only synthetic records.
- Explain tenant isolation and least privilege in plain language.
- Describe blockchain as integrity anchoring only.
- Explain analytics suppression as a deliberate privacy control.
- Ask about jurisdiction, languages, channels, SSO and operating model early.
- State when an answer needs specialist confirmation.

### Do not

- Promise absolute anonymity, zero breach risk or guaranteed legal compliance.
- claim SOC 2, ISO 27001 or another certification without current approved evidence.
- imply that a signed hotline provider contract or toll-free number exists for every country.
- show restricted architecture pages to an unauthorised audience.
- use live customer information in a demonstration.
- share demo passwords in public collateral.
- call database-mode ledger records public-chain transactions.
- say AI makes decisions about credibility, discipline or disclosure.
- invent roadmap dates, uptime, recovery objectives or retention periods.
- advise a reporter to confront an alleged wrongdoer or delay emergency assistance.

## 11. Call opening and closing scripts

Opening:

> “SafelyTold is a secure integrity-reporting and case-management platform. Before I recommend a configuration, may I understand your countries, reporting channels, expected users, independence requirements and current case process?”

Technical boundary:

> “I can explain the product behavior and standard controls. That question affects architecture/security/legal commitments, so I will record it precisely and obtain a validated response from the responsible specialist.”

Closing:

> “I will send the agreed public material and list each item needing specialist confirmation. Nothing described as configurable or subject to assessment should be treated as a contractual commitment until it appears in the approved proposal.”

## 12. Competency check

Before representing SafelyTold independently, a team member must be able to:

- explain all four reporting modes without conflating them;
- describe the reporter-to-closure lifecycle;
- distinguish tenant administration from case access;
- run the synthetic demo without exposing secrets;
- explain the hotline dependency accurately;
- describe the ledger without saying reports are stored on-chain;
- respond safely to compliance and certification questions;
- identify every mandatory escalation category;
- locate all public, staff and Trust Centre URLs;
- complete a mock procurement call and escalation record.

The commercial lead should record completion and repeat assessment after material product changes.
