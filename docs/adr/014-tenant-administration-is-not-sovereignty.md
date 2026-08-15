# ADR 014: Tenant administration is not sovereignty over case truth

## Decision

A subscribing organisation may administer its reporting programme, policies,
staff assignments and lawful retention configuration. Subscription or tenant
administration must not confer the ability to identify an anonymous reporter,
approve the administrator's own disclosure request, replace sealed evidence,
delete audit history, suppress a submitted report, or bypass purpose, conflict
and dual-control rules.

These are platform constitutional controls, not tenant-configurable features.
Application authorization, separate workload/database identities, immutable
object storage, append-only externally anchored audit proofs and independent
break-glass governance must enforce them at different layers.

## Current enforcement boundary

The application exposes no audit/evidence deletion route, sealed evidence uses
unique immutable references, and identity disclosure excludes ordinary tenant
administrators and requires two independent approvers. The shared local stack
does not yet protect against a privileged infrastructure/database operator.
Production certification therefore requires separate service credentials,
storage retention lock, externally witnessed audit anchors and tested operator
separation before claiming infrastructure-administrator resistance.
