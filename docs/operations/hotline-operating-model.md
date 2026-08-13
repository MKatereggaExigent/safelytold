# Toll-free hotline operating model

Owner: Head of Operations. Review monthly and after every material incident.

Use a contracted, independently operated 24/7 toll-free service with South African language coverage,
call overflow and disaster recovery. The provider must support anonymous calls without caller-ID
retention, identified/confidential modes, a scripted consent notice, interpreter access and immediate
life-safety escalation. Calls enter the normal SafelyTold intake and produce the same taxonomy, case
reference, secure mailbox and SLA clock as web reports.

The call centre may capture structured facts. It must not email audio or narratives, keep local notes,
promise outcomes, investigate, or reveal a reporter's identity. Recording is off by default. Recording
requires explicit consent, a documented lawful basis, retention, encryption and evidence-vault ingestion.

## Provider acceptance gates

- Number is free from major South African mobile and fixed networks.
- Geographically separate failover queues work in and outside business hours.
- Two trained operators per shift; supervisor and SafelyTold duty-manager escalation are available.
- Contract covers uptime, answer time, privacy, breach notice, data residency, deletion and audit.
- Intake-only accounts use MFA and undergo quarterly access recertification.
- Synthetic calls prove reference delivery, categorisation, duplicate handling, emergency routing,
  mailbox access and audit entries.

## Call flow

1. Give the privacy/recording notice and ask whether it is safe to continue.
2. Offer anonymous, confidential or identified mode; never steer away from anonymity.
3. Check immediate danger and use the approved emergency route without removing the reporting option.
4. Capture category, roles, dates, location, narrative and safe-contact preference; minimise identity data.
5. Read back and submit once using provider call ID as the idempotency key.
6. Give case reference and recovery secret separately; never read a secret where unsafe.
7. State response expectations and secure-mailbox route; escalate high-risk categories immediately.

Monthly synthetic calls cover every shift and language group. Quarterly tests cover carrier, provider-site
and SafelyTold outages. During outage, use an encrypted, access-logged continuity queue; import within
four hours of recovery and destroy after reconciliation.

Launch evidence: contract/DPA, number ownership, DPIA update, roster, training, access list, scripts,
test-call results, failover drill and named escalation contacts.
