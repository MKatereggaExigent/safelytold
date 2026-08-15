from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from safelytold_common.auth import SuperuserDep

router = APIRouter(prefix='/v1/admin/assurance', tags=['platform-assurance'])


class AssuranceControl(BaseModel):
    id: str
    name: str
    status: Literal['enforced', 'partially_enforced', 'not_deployed']
    claim: str
    verification: str
    evidence: list[str]


CONTROLS = [
    AssuranceControl(id='tenant-non-omnipotence', name='Tenant administration is not control over case truth', status='partially_enforced', claim='Tenant administrators cannot use application features to identify anonymous reporters, delete audit history, replace sealed evidence or self-approve identity disclosure. Resistance to privileged infrastructure operators is not yet claimed.', verification='Test tenant-admin permissions, self-approval, evidence replacement and audit deletion; then separately test database, object-store and infrastructure administrator paths.', evidence=['docs/adr/014-tenant-administration-is-not-sovereignty.md', 'services/reporter_identity_service/app/main.py', 'services/evidence_service/app/main.py', 'services/audit_service/app/main.py']),
    AssuranceControl(id='tor-onion-ingress', name='Tor/onion reporting', status='not_deployed', claim='No production onion service is currently operated, so SafelyTold does not claim Tor protection.', verification='An auditor must resolve the published onion address, inspect its signed ownership statement and submit a synthetic report through it.', evidence=['docs/adr/013-tenant-bound-reporter-plane.md']),
    AssuranceControl(id='blinded-eligibility', name='Privacy Pass and blinded eligibility credentials', status='not_deployed', claim='Policy types exist, but issuance and single-use redemption are intentionally blocked until an unlinkable credential service is deployed.', verification='Test that issuance identity cannot be correlated with redemption and that a redeemed token cannot be spent twice.', evidence=['services/tenancy_service/app/reporting.py']),
    AssuranceControl(id='unlinkable-workforce-verification', name='Cryptographically unlinkable workforce verification', status='not_deployed', claim='Verified-anonymous reporting is modelled but is unavailable without the blinded credential control.', verification='Run issuer/verifier collusion tests and demonstrate that staff SSO subject identifiers never enter reporter or case records.', evidence=['packages/python/safelytold_common/safelytold_common/reporter_access.py']),
    AssuranceControl(id='ohttp-relay', name='OHTTP-style privacy relays', status='not_deployed', claim='Direct browser-to-gateway transport is currently used; no relay anonymity claim is made.', verification='Confirm relay and gateway are independently operated and neither party can observe both reporter network identity and request content.', evidence=['docs/security/threat-model.md']),
    AssuranceControl(id='identity-vault', name='Separate identity-vault architecture', status='enforced', claim='Optional reporter identity is encrypted in a separate service and database with purpose-bound, time-limited, dual approval disclosure.', verification='Inspect database connectivity, request identity disclosure and confirm two independent approvals are required and the requester cannot self-approve.', evidence=['services/reporter_identity_service/app/main.py', 'docs/adr/005-separate-identity-vault.md']),
    AssuranceControl(id='reporter-case-non-linkability', name='Reporter and case database non-linkability', status='partially_enforced', claim='Identity and case records are separated, but the reporter-handle service retains the case mapping required for mailbox recovery.', verification='Inspect schemas and demonstrate that the case database alone contains no reporter identity; separately assess handle-to-case linkage risk.', evidence=['services/reporter_identity_service/app/main.py', 'services/case_service/app/main.py']),
    AssuranceControl(id='ip-non-retention', name='IP non-retention design', status='partially_enforced', claim='Frontend proxy and application access logs are disabled, but production infrastructure and third-party emergency routes still require an independent telemetry audit.', verification='Submit synthetic traffic and search proxy, application, tracing, WAF and provider logs for the source IP and forwarded-address headers.', evidence=['docs/security/logging-standards.md', 'infrastructure/nginx/nginx.conf']),
    AssuranceControl(id='sanitised-evidence', name='Metadata-sanitised evidence copies', status='not_deployed', claim='Sealed originals are scanned and hashed, but the sandboxed sanitisation provider is not configured; derivative-only investigator access is not yet claimed.', verification='Upload files containing EXIF, author, revision and active-content metadata; verify investigators receive only inert derivatives while sealed hashes remain unchanged.', evidence=['services/evidence_service/app/sanitizer.py', 'services/evidence_service/app/main.py']),
    AssuranceControl(id='trust-zone-separation', name='Independent reporter and investigator trust zones', status='partially_enforced', claim='Reporter, staff and identity services use separate authentication paths and stores; production network-level isolation and independently operated ingress remain outstanding.', verification='Review network policies, workload identities and database grants, then attempt reporter-to-staff and staff-to-vault boundary crossings.', evidence=['docs/adr/013-tenant-bound-reporter-plane.md', 'infrastructure/keycloak/safelytold-realm.json']),
]


@router.get('/controls', response_model=list[AssuranceControl])
async def list_assurance_controls(_: SuperuserDep) -> list[AssuranceControl]:
    """Internal assurance evidence; never expose through a public application."""
    return CONTROLS
