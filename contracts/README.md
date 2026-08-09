# Contracts

Contracts are versioned independently from service code. Events use a CloudEvents-compatible envelope and privacy-safe `data` objects.

Rules:

- Events contain opaque identifiers and operational metadata only.
- Raw allegations, evidence, interview notes, identity data, free text, email addresses, phone numbers, IP addresses and document content are prohibited.
- Breaking changes require a new event version.
- Consumers must be idempotent by event `id` and tolerate additive fields.
- JSON Schema validation runs in CI and at publisher boundaries.
