# Web applications

Three independently deployable Next.js applications reduce accidental data crossover:

- **reporter-web**: anonymous/confidential/identified intake and two-way mailbox.
- **staff-web**: authorised triage, investigation, protection, privacy and audit workbench.
- **trust-center-web**: public transparency, policies, aggregate metrics and support resources.

Do not share browser storage, authentication cookies or telemetry identifiers between reporter and staff applications. In production they should use separate hostnames, Content Security Policies, identity clients and analytics configurations.
