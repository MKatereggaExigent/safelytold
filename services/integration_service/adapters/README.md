# Integration adapter contracts

Implement each adapter behind outbound ports; never call vendors directly from domain services.

- `identity`: OIDC/SAML metadata and SCIM lifecycle
- `hris`: organisational relationships, employment events and consented retaliation checks
- `messaging`: neutral SMS/email/push notifications without case content
- `voice`: consent-aware recordings, restricted audio access and privacy-reviewed transcription
- `eap`: consent-controlled referral only; no case disclosure by default
- `investigator`: scoped invitations and secure package exchange
- `regulator`: human-approved jurisdiction-specific exports; never autonomous
- `siem`: security events stripped of case content
- `webhook`: signed, allowlisted, retried metadata-only events

Each connector requires regional routing, credential reference, data-processing terms, deletion/exit capability, health monitoring and circuit breaking.
