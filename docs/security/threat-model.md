# STRIDE and LINDDUN starter threat model

| Threat | Example | Foundation control | Production validation |
|---|---|---|---|
| Spoofing | attacker opens staff case | OIDC boundary, role model | FIDO2 MFA, token binding, session controls |
| Tampering | investigator edits evidence | sealed originals, hashes, audit chain, Merkle roots | Object Lock, HSM signatures, independent verification |
| Repudiation | privileged user denies access | purpose-bound append-only audit | WORM audit store and external assurance |
| Information disclosure | identity leaks through logs/events | privacy validator and separate vault | DLP, egress policy, privacy chaos testing |
| Denial of service | campaign floods anonymous intake | gateway/rate-limit boundary | anti-bot controls that avoid reporter fingerprinting |
| Elevation | admin grants self case access | policy service, separation of duties | PAM/JIT, dual control, immutable entitlement audit |
| Linkability | timing links anonymous report to staff activity | separate realm | mixed/delayed batches, minimal telemetry, no shared cookies |
| Identifiability | rare title reveals reporter | anonymity assistant | trauma-informed warnings and human privacy review |
| Non-repudiation harm | permanent chain record identifies event | hash-only batching | correlation analysis and DPIA before activation |
| Detectability | network observer sees reporting | TLS boundary | private access options, CDN log minimisation, Tor policy review |
| Unawareness | reporter misunderstands confidentiality | mode-specific notices | user testing and jurisdiction-specific consent text |
| Non-compliance | retention conflicts with law | jurisdiction packs | legal sign-off, records schedule and deletion evidence |

Abuse cases include malicious false reporting, retaliatory identity requests, collusive investigators, platform-operator curiosity, evidence poisoning, prompt injection, analytics re-identification, insider export, corrupt validator governance and legal-process misuse.
