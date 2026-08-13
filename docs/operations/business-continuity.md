# Business continuity and disaster recovery

Owner: Service Continuity Manager. Invocation authority: incident commander.

Critical journeys are report submission, reference recovery, reporter mailbox, staff triage and hotline
intake. Target service availability is 24/7. Proposed objectives are RTO 4 hours and RPO 15 minutes until
the production risk assessment approves tighter targets.

- Multi-zone replicas, database HA, encrypted point-in-time backups, versioned object storage and
  redundant messaging/workflow workers.
- External monitoring; primary and secondary on-call; severity-based paging.
- Daily backups, monthly restore verification and quarterly full recovery exercises.
- Hotline continuity queue defined in the hotline operating model.
- Current suppliers and escalation contacts live in the controlled incident system, not this repository.

Recovery order: identity/secrets, database, intake/mailbox, workflow workers, evidence, analytics, then
non-critical services. Reconcile outbox events, hotline entries, evidence hashes and audit roots before
normal operation. Record actual RTO/RPO, data loss, decisions and follow-ups. Two consecutive successful
restore exercises are required before production sign-off.
