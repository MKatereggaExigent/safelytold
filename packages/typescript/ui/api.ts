/* Gateway client for safelytold.
 *
 * Every backend service is reached through the API gateway at
 * /gateway/{service}/... so the browser only ever talks to one origin
 * (NEXT_PUBLIC_API_BASE_URL, default http://localhost:8101).
 *
 * Auth: in development (DEV_AUTH_BYPASS=true) services accept x-dev-*
 * headers; in production a verified OIDC access token is sent instead.
 */

export const GATEWAY_BASE = (
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  'http://localhost:8101'
).replace(/\/$/, '');

export const DEV_AUTH = (process.env.NEXT_PUBLIC_DEV_AUTH ?? 'false') === 'true';
export const DEV_TENANT_ID =
  process.env.NEXT_PUBLIC_DEV_TENANT_ID ?? '00000000-0000-0000-0000-000000000001';
export const DEMO_TENANT_ID = 'd3a00000-0000-4000-8000-000000000001';

export type ServiceSlug =
  | 'tenancy'
  | 'identity'
  | 'reporter-identity'
  | 'policy'
  | 'intake'
  | 'mailbox'
  | 'case'
  | 'investigation'
  | 'evidence'
  | 'protection'
  | 'support'
  | 'analytics'
  | 'integration'
  | 'notification'
  | 'privacy'
  | 'audit'
  | 'security'
  | 'ai'
  | 'ledger';

export interface Session {
  tenantId: string;
  subject: string;
  roles: string[];
  purpose: string;
  accessToken?: string;
  refreshToken?: string;
  idToken?: string;
  expiresAt?: number;
  displayName?: string;
  email?: string;
  /** Marks the development bypass session created by the "Continue in
   * development mode" action. Never set on real OIDC sessions. */
  isDev?: boolean;
}

export const DEFAULT_SESSION: Session = {
  tenantId: DEV_TENANT_ID,
  subject: 'development-user',
  roles: ['platform_developer'],
  purpose: 'development',
};

/** Dev-bypass session that AuthGate accepts when NEXT_PUBLIC_DEV_AUTH=true. */
export const DEV_SESSION: Session = {
  ...DEFAULT_SESSION,
  isDev: true,
};

export interface ApiOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE' | 'HEAD' | 'OPTIONS';
  body?: unknown;
  formData?: FormData;
  headers?: Record<string, string>;
  signal?: AbortSignal;
  /** Null omits every auth header (public/pseudonymous endpoints). */
  session?: Session | null;
  /** Disable the auto-generated idempotency key for mutating calls. */
  noIdempotency?: boolean;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: unknown,
    message?: string,
  ) {
    super(message ?? (typeof detail === 'string' ? detail : `Request failed with status ${status}`));
    this.name = 'ApiError';
  }
}

export function buildHeaders(session: Session | null, opts: ApiOptions): Record<string, string> {
  const headers: Record<string, string> = {
    accept: 'application/json',
    ...(opts.headers ?? {}),
  };
  if (opts.formData) {
    // Let the browser set multipart boundary.
    headers['content-type'] = '';
  } else if (opts.body !== undefined) {
    headers['content-type'] = 'application/json';
  }
  if (session) {
    headers['x-tenant-id'] = session.tenantId;
    headers['x-purpose'] = session.purpose;
    if (session.accessToken) {
      headers['authorization'] = `Bearer ${session.accessToken}`;
    }
    if (DEV_AUTH) {
      // Dev bypass: services accept x-dev-* headers. Derive them from the
      // authenticated identity so the real user/roles propagate end-to-end.
      headers['x-dev-subject'] = session.subject;
      headers['x-dev-roles'] = session.roles.join(',');
      if (session.email) headers['x-dev-email'] = session.email;
    }
  }
  if (
    session &&
    opts.method !== 'GET' &&
    opts.method !== 'HEAD' &&
    opts.method !== 'OPTIONS' &&
    !opts.noIdempotency
  ) {
    headers['x-idempotency-key'] = crypto.randomUUID();
  }
  return headers;
}

function responseError(response: Response, detail: unknown): ApiError {
  return new ApiError(response.status, detail);
}

export async function apiFetch<T>(serviceOrPath: string, pathOrOpts?: string | ApiOptions, maybeOpts?: ApiOptions): Promise<T> {
  let service = '';
  let path: string;
  let opts: ApiOptions;
  if (typeof pathOrOpts === 'string') {
    service = serviceOrPath;
    path = pathOrOpts;
    opts = maybeOpts ?? {};
  } else {
    path = serviceOrPath;
    opts = pathOrOpts ?? {};
  }
  const session = opts.session === undefined ? null : opts.session;
  const url = service
    ? `${GATEWAY_BASE}/v1/gateway/${service}${path}`
    : `${GATEWAY_BASE}${path}`;

  const headers = buildHeaders(session, opts);
  if (headers['content-type'] === '') delete headers['content-type'];

  const body = opts.formData
    ? opts.formData
    : opts.body !== undefined
      ? JSON.stringify(opts.body)
      : undefined;

  let response: Response;
  try {
    response = await fetch(url, { method: opts.method ?? 'GET', headers, body, signal: opts.signal });
  } catch (err) {
    throw new ApiError(0, null, err instanceof Error ? err.message : 'Network error');
  }

  if (!response.ok) {
    let detail: unknown = null;
    try {
      detail = await response.json();
    } catch {
      detail = await response.text().catch(() => null);
    }
    throw responseError(response, detail);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

/* ------------------------------------------------------------------ */
/* Generic domain-record API (used by most bounded contexts)           */
/* ------------------------------------------------------------------ */

export interface RecordView {
  id: string;
  tenant_id: string;
  kind: string;
  status: string;
  payload: Record<string, unknown>;
}

export interface RecordQuery {
  /** Filter by the record kind (e.g. `case`, `mailbox_message`). */
  kind?: string;
  /** Filter by the exact record `status` column. */
  status?: string;
  /** Filter by `payload.case_id` on the server. */
  caseId?: string;
  /** Max rows to return. Defaults to 100 on the server, up to 1000. */
  limit?: number;
  /** Skip `offset` rows for pagination. */
  offset?: number;
}

export function listRecords(
  service: ServiceSlug,
  session: Session | null,
  query?: RecordQuery,
  signal?: AbortSignal,
): Promise<RecordView[]> {
  const qs = new URLSearchParams();
  if (query?.kind) qs.set('kind', query.kind);
  if (query?.status) qs.set('status', query.status);
  if (query?.caseId) qs.set('case_id', query.caseId);
  if (typeof query?.limit === 'number') qs.set('limit', String(query.limit));
  if (typeof query?.offset === 'number') qs.set('offset', String(query.offset));
  const suffix = qs.size > 0 ? `?${qs.toString()}` : '';
  return apiFetch(service, `/v1/records${suffix}`, { session, signal });
}

/** Server-side count with the same `kind` / `status` / `caseId` filters. */
export async function countRecords(
  service: ServiceSlug,
  session: Session | null,
  query?: Pick<RecordQuery, 'kind' | 'status' | 'caseId'>,
): Promise<number> {
  const qs = new URLSearchParams();
  if (query?.kind) qs.set('kind', query.kind);
  if (query?.status) qs.set('status', query.status);
  if (query?.caseId) qs.set('case_id', query.caseId);
  const suffix = qs.size > 0 ? `?${qs.toString()}` : '';
  const result = await apiFetch<{ total: number }>(service, `/v1/records/count${suffix}`, { session });
  return result.total;
}

export function getRecord(
  service: ServiceSlug,
  id: string,
  session: Session | null,
): Promise<RecordView> {
  return apiFetch(service, `/v1/records/${id}`, { session });
}

export function createRecord(
  service: ServiceSlug,
  kind: string,
  payload: Record<string, unknown>,
  session: Session | null,
): Promise<RecordView> {
  return apiFetch(service, '/v1/records', {
    method: 'POST',
    body: { kind, payload },
    session,
  });
}

/* Explicit staff domain APIs. Generic records are retained only for legacy
 * public bounded contexts and must not be used by the production staff app. */
export interface CaseView { id:string; tenant_id:string; public_reference:string; status:string; jurisdiction_code:string; severity_band:string; workflow_id:string; policy_version_id:string; created_at:string; updated_at:string }
export const listCases=(session:Session,status?:string)=>apiFetch<CaseView[]>('case',`/v1/cases${status?`?status=${encodeURIComponent(status)}`:''}`,{session});
export const getCase=(id:string,session:Session)=>apiFetch<CaseView>('case',`/v1/cases/${id}`,{session});
export const transitionCase=(id:string,status:string,reason:string,session:Session)=>apiFetch<CaseView>('case',`/v1/cases/${id}/transitions`,{method:'POST',body:{status,reason},session});
export const addAllegation=(id:string,taxonomy_code:string,session:Session)=>apiFetch('case',`/v1/cases/${id}/allegations`,{method:'POST',body:{taxonomy_code},session});
export const createConflictCheck=(id:string,body:{candidate_subject_id:string;conflicts:string[];decision:'clear'|'conflicted'},session:Session)=>apiFetch<{id:string}>('case',`/v1/cases/${id}/conflict-checks`,{method:'POST',body,session});
export const createCaseAssignment=(id:string,body:{subject_id:string;role:string;purpose:string;valid_until:string;conflict_check_id:string},session:Session)=>apiFetch('case',`/v1/cases/${id}/assignments`,{method:'POST',body,session});

export interface InvestigationView {id:string;tenant_id:string;case_id:string;status:string;scope:string;issue_ids:string[];evidence_sources:string[];milestones:Record<string,unknown>[];created_at:string}
export const listInvestigations=(caseId:string,session:Session)=>apiFetch<InvestigationView[]>('investigation',`/v1/investigations/case/${caseId}`,{session});
export const createInvestigation=(body:{case_id:string;issue_ids:string[];scope:string;evidence_sources:string[];milestones:Record<string,unknown>[]},session:Session)=>apiFetch<InvestigationView>('investigation','/v1/investigations',{method:'POST',body,session});
export const createFinding=(id:string,body:Record<string,unknown>,session:Session)=>apiFetch('investigation',`/v1/investigations/${id}/findings`,{method:'POST',body,session});
export const reviewFinding=(investigationId:string,findingId:string,reviewerApprovalId:string,session:Session)=>apiFetch('investigation',`/v1/investigations/${investigationId}/findings/${findingId}/review`,{method:'POST',body:{reviewer_approval_id:reviewerApprovalId},session});
export const createAppeal=(id:string,body:Record<string,unknown>,session:Session)=>apiFetch('investigation',`/v1/investigations/${id}/appeals`,{method:'POST',body,session});

export interface ProtectionPlanView {id:string;tenant_id:string;case_id:string;status:string;requested_measures:string[];approved_measures:string[];owner_ref:string;next_review_at:string;created_at:string}
export const listProtectionPlans=(caseId:string,session:Session)=>apiFetch<ProtectionPlanView[]>('protection',`/v1/protection/case/${caseId}`,{session});
export const createProtectionPlan=(body:Record<string,unknown>,session:Session)=>apiFetch<ProtectionPlanView>('protection','/v1/protection/plans',{method:'POST',body,session});
export const scheduleProtectionCheckIn=(planId:string,due_at:string,session:Session)=>apiFetch('protection',`/v1/protection/plans/${planId}/check-ins`,{method:'POST',body:{due_at},session});
export const listProtectionCheckIns=(session:Session,caseId?:string)=>apiFetch<any[]>('protection',`/v1/protection/check-ins${caseId?`?case_id=${caseId}`:''}`,{session});
export const completeProtectionCheckIn=(id:string,body:Record<string,unknown>,session:Session)=>apiFetch('protection',`/v1/protection/check-ins/${id}/complete`,{method:'POST',body,session});

export const listSupportDirectory=(session:Session)=>apiFetch<any[]>('support','/v1/support/directory',{session});
export const createSupportDirectoryEntry=(body:Record<string,unknown>,session:Session)=>apiFetch('support','/v1/support/directory',{method:'POST',body,session});
export const listSupportReferrals=(session:Session,caseId?:string)=>apiFetch<any[]>('support',`/v1/support/referrals${caseId?`?case_id=${caseId}`:''}`,{session});
export const createSupportReferral=(body:Record<string,unknown>,session:Session)=>apiFetch('support','/v1/support/referrals',{method:'POST',body,session});

export const listPrivacyRequests=(session:Session)=>apiFetch<any[]>('privacy','/v1/privacy/requests',{session});
export const createPrivacyRequest=(body:Record<string,unknown>,session:Session)=>apiFetch('privacy','/v1/privacy/requests',{method:'POST',body,session});
export const decidePrivacyRequest=(id:string,body:Record<string,unknown>,session:Session)=>apiFetch('privacy',`/v1/privacy/requests/${id}/decision`,{method:'POST',body,session});
export const listPrivacyBreaches=(session:Session)=>apiFetch<any[]>('privacy','/v1/privacy/breaches',{session});
export const createPrivacyBreach=(body:Record<string,unknown>,session:Session)=>apiFetch('privacy','/v1/privacy/breaches',{method:'POST',body,session});

export const listStaffIdentities=(session:Session)=>apiFetch<any[]>('identity','/v1/identity/staff',{session});
export const createStaffIdentity=(body:Record<string,unknown>,session:Session)=>apiFetch('identity','/v1/identity/staff',{method:'POST',body,session});
export const listAccessGrants=(session:Session)=>apiFetch<any[]>('identity','/v1/identity/grants',{session});
export const createAccessGrant=(body:Record<string,unknown>,session:Session)=>apiFetch('identity','/v1/identity/grants',{method:'POST',body,session});
export const revokeAccessGrant=(id:string,session:Session)=>apiFetch('identity',`/v1/identity/grants/${id}`,{method:'DELETE',session});
export const listSecurityAlerts=(session:Session,status?:string)=>apiFetch<any[]>('security',`/v1/security/alerts${status?`?status=${status}`:''}`,{session});
export const createSecurityAlert=(body:Record<string,unknown>,session:Session)=>apiFetch('security','/v1/security/alerts',{method:'POST',body,session});
export const triageSecurityAlert=(id:string,body:Record<string,unknown>,session:Session)=>apiFetch('security',`/v1/security/alerts/${id}/triage`,{method:'POST',body,session});
export const listAuditEntries=(session:Session)=>apiFetch<any[]>('audit','/v1/audit/entries',{session});
export const listLedgerAnchors=(session:Session)=>apiFetch<any[]>('ledger','/v1/ledger/anchors',{session});
export const listEvidence=(session:Session,caseId?:string)=>apiFetch<any[]>('evidence',`/v1/evidence${caseId?`?case_id=${caseId}`:''}`,{session});
export const getAnalyticsTrends=(metric:string,start:string,end:string,session:Session)=>apiFetch<any>('analytics',`/v1/analytics/trends?metric=${encodeURIComponent(metric)}&start=${start}&end=${end}`,{session});
export const getManagementReport=(start:string,end:string,session:Session)=>apiFetch<any>('analytics',`/v1/analytics/management-report?start=${start}&end=${end}`,{session});

export type OperationsArea = 'awareness' | 'training' | 'qa' | 'continuity' | 'coverage' | 'hotline' | 'reporting';

export interface OperationalRecordView {
  id: string;
  area: OperationsArea;
  status: string;
  payload: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export function listOperationalRecords(session: Session, area?: OperationsArea): Promise<OperationalRecordView[]> {
  const suffix = area ? `?area=${encodeURIComponent(area)}` : '';
  return apiFetch('integration', `/v1/operations${suffix}`, { session });
}

export function createOperationalRecord(session: Session, area: OperationsArea, payload: Record<string, unknown>): Promise<OperationalRecordView> {
  return apiFetch('integration', '/v1/operations', { method: 'POST', body: { area, payload }, session });
}

export function transitionOperationalRecord(session: Session, id: string, status: string, evidence: Record<string, unknown>): Promise<OperationalRecordView> {
  return apiFetch('integration', `/v1/operations/${id}/transition`, { method: 'POST', body: { status, evidence }, session });
}

export function getCoverageStatus(session: Session): Promise<{ covered: boolean; active_shifts: number; launch_ready: boolean }> {
  return apiFetch('integration', '/v1/operations/coverage/status', { session });
}

/* ------------------------------------------------------------------ */
/* Reporter identity (public + vault)                                  */
/* ------------------------------------------------------------------ */

export interface CreatedHandle {
  case_id: string;
  public_code: string;
  recovery_secret: string;
}

export function createReporterHandle(caseId: string): Promise<CreatedHandle> {
  return apiFetch('reporter-identity', '/v1/reporter/handles', {
    method: 'POST',
    body: { case_id: caseId },
    session: null,
  });
}

export interface ReportingContext {
  organisation: { slug: string; display_name: string };
  channel: string;
  eligibility_class: string;
  allowed_modes: string[];
  reporting_session: string;
  expires_at: string;
}

export interface SalesPlan {
  code: string;
  name: string;
  employee_min: number | null;
  employee_max: number | null;
  monthly_equivalent: number;
  monthly_max?: number;
  annual_price: number | null;
  setup_fee: number;
  price_from: boolean;
  custom_annual?: boolean;
  required_isolation?: string;
  currency: 'ZAR';
  vat_included: false;
  billing_term: 'annual';
  core_privacy_controls: string[];
  enterprise_capabilities: string[];
}

export interface SalesCatalogue {
  plans: SalesPlan[];
  sales_contact: { email: string; phone: string };
}

export function getSalesCatalogue(): Promise<SalesCatalogue> {
  return apiFetch('tenancy', '/v1/sales/plans', { session: null });
}

export function resolveReportingContext(organisation: string, channel = 'open'): Promise<ReportingContext> {
  return apiFetch('tenancy', '/v1/reporting/resolve', {
    method: 'POST', body: { organisation, channel }, session: null,
  });
}

export function createTenantReport(payload: Record<string, unknown>, reportingSession: string): Promise<RecordView> {
  return apiFetch('intake', '/v1/reports', {
    method: 'POST', body: { kind: 'report', payload }, session: null,
    headers: { authorization: `Bearer ${reportingSession}` },
  });
}

export function createTenantReporterHandle(caseId: string, reportingSession: string): Promise<CreatedHandle> {
  return apiFetch('reporter-identity', '/v1/reporter/handles', {
    method: 'POST', body: { case_id: caseId }, session: null,
    headers: { authorization: `Bearer ${reportingSession}` },
  });
}

export function reporterSession(
  publicCode: string,
  recoverySecret: string,
): Promise<{ case_id: string; session: string; expires_at: string }> {
  return apiFetch('reporter-identity', '/v1/reporter/session', {
    method: 'POST',
    body: { public_code: publicCode, recovery_secret: recoverySecret },
    session: null,
  });
}

export function storeVaultIdentity(caseId: string, identity: Record<string, unknown>, reportingSession?: string): Promise<{ identity_ref: string; case_id: string; status: string }> {
  return apiFetch('reporter-identity', '/v1/reporter/vault-identities', {
    method: 'POST',
    body: { case_id: caseId, identity },
    session: null,
    headers: reportingSession ? { authorization: `Bearer ${reportingSession}` } : {},
  });
}

export function createVaultAccessRequest(
  caseId: string,
  purpose: string,
  session: Session,
): Promise<{ request_id: string; case_id: string; status: string; purpose: string; expires_at: string; required_approvals: number }> {
  return apiFetch('reporter-identity', '/v1/reporter/vault-access-requests', {
    method: 'POST',
    body: { case_id: caseId, purpose },
    session,
  });
}

export function decideVaultAccessRequest(
  requestId: string,
  decision: 'approve' | 'deny',
  rationale: string,
  session: Session,
): Promise<{ request_id: string; decision: string; status: string; approver_role: string }> {
  return apiFetch('reporter-identity', `/v1/reporter/vault-access-requests/${requestId}/approvals`, {
    method: 'POST',
    body: { decision, rationale },
    session,
  });
}

export function revealVaultIdentity(
  requestId: string,
  session: Session,
): Promise<{ identity_ref: string; request_id: string; purpose: string; revealed_at: string; identity: Record<string, unknown> }> {
  return apiFetch('reporter-identity', `/v1/reporter/vault-access-requests/${requestId}/reveal`, {
    method: 'POST',
    body: {},
    session,
  });
}

/* ------------------------------------------------------------------ */
/* Mailbox (encrypted pseudonymous threads)                            */
/* ------------------------------------------------------------------ */

export interface MailboxMessage {
  id: string;
  case_id: string;
  sender: 'reporter' | 'platform';
  body: string;
  attachment_ids: string[];
  created_at: string;
  read_at: string | null;
}

export interface SafeContactPreferences {
  allowed_channels: string[];
  prohibited_times: string[];
  neutral_message_only: boolean;
}

function reporterAuth(token: string): Record<string, string> {
  return { authorization: `Bearer ${token}` };
}

export function listMailboxMessages(caseId: string, token: string): Promise<MailboxMessage[]> {
  return apiFetch('mailbox', `/v1/mailbox/cases/${caseId}/messages`, { session: null, headers: reporterAuth(token) });
}

export function sendMailboxMessage(caseId: string, body: string, token: string): Promise<MailboxMessage> {
  return apiFetch('mailbox', `/v1/mailbox/cases/${caseId}/messages`, {
    method: 'POST',
    body: { body, attachment_ids: [] },
    session: null,
    headers: reporterAuth(token),
  });
}

export function submitConflictChallenge(
  caseId: string,
  challenge: { challenged_assignment_id?: string | null; reason_category: string; details: string },
  token: string,
): Promise<{ id: string; case_id: string; status: string }> {
  return apiFetch('mailbox', `/v1/mailbox/cases/${caseId}/conflict-challenges`, {
    method: 'POST',
    body: challenge,
    session: null,
    headers: reporterAuth(token),
  });
}

export function submitRetaliationConcern(
  caseId: string,
  concern: { risk_band: string; details: string },
  token: string,
): Promise<{ id: string; case_id: string; risk_band: string; status: string }> {
  return apiFetch('mailbox', `/v1/mailbox/cases/${caseId}/retaliation-concerns`, {
    method: 'POST',
    body: concern,
    session: null,
    headers: reporterAuth(token),
  });
}

export function getSafeContact(caseId: string, token: string): Promise<SafeContactPreferences> {
  return apiFetch('mailbox', `/v1/mailbox/cases/${caseId}/safe-contact`, { session: null, headers: reporterAuth(token) });
}

export function updateSafeContact(caseId: string, prefs: SafeContactPreferences, token: string): Promise<SafeContactPreferences> {
  return apiFetch('mailbox', `/v1/mailbox/cases/${caseId}/safe-contact`, {
    method: 'PUT',
    body: prefs,
    session: null,
    headers: reporterAuth(token),
  });
}

export function listMailboxThread(caseId: string, session: Session): Promise<MailboxMessage[]> {
  return apiFetch('mailbox', `/v1/mailbox/threads/${caseId}/messages`, { session });
}

export function replyMailboxMessage(caseId: string, body: string, session: Session): Promise<MailboxMessage> {
  return apiFetch('mailbox', `/v1/mailbox/threads/${caseId}/messages`, {
    method: 'POST',
    body: { body, attachment_ids: [] },
    session,
  });
}

export interface RetaliationConcernView {
  id: string;
  case_id: string;
  risk_band: string;
  details: string;
  status: string;
  created_at: string;
}

export function listAllMailboxConcerns(session: Session | null): Promise<RetaliationConcernView[]> {
  return apiFetch('mailbox', '/v1/mailbox/concerns', { session });
}

export function listMailboxConcerns(
  caseId: string,
  session: Session,
): Promise<RetaliationConcernView[]> {
  return apiFetch('mailbox', `/v1/mailbox/threads/${caseId}/concerns`, { session });
}

export function listMailboxChallenges(
  caseId: string,
  session: Session,
): Promise<{ id: string; case_id: string; reason_category: string; details: string; status: string; created_at: string }[]> {
  return apiFetch('mailbox', `/v1/mailbox/threads/${caseId}/challenges`, { session });
}

/* ------------------------------------------------------------------ */
/* Policy engine (stateless authorisation decisions)                   */
/* ------------------------------------------------------------------ */

export interface PolicyInput {
  tenant_id?: string;
  subject_id?: string;
  roles?: string[];
  action: string;
  resource_type: string;
  resource_id?: string;
  purpose?: string;
  assigned_case_ids?: string[];
  implicated_subject_ids?: string[];
  requested_identity_access?: boolean;
  dual_approval_count?: number;
}

export interface PolicyOutput {
  decision: 'allow' | 'deny' | 'require_approval' | 'recuse';
  reasons: string[];
  obligations: string[];
}

export function policyDecide(input: PolicyInput, session: Session): Promise<PolicyOutput> {
  return apiFetch('policy', '/v1/policy/decide', { method: 'POST', body: input, session });
}

/* ------------------------------------------------------------------ */
/* Evidence (sealed upload + legal hold)                               */
/* ------------------------------------------------------------------ */

export interface EvidenceReceipt {
  evidence_id: string;
  sha256: string;
  size_bytes: number;
  copy_kind: string;
  object_key: string;
  scan_status: string;
}

export function uploadEvidence(
  caseId: string,
  file: File,
  session: Session,
): Promise<EvidenceReceipt> {
  const form = new FormData();
  form.append('file', file);
  return apiFetch('evidence', `/v1/evidence/${caseId}/upload`, {
    method: 'POST',
    formData: form,
    session,
  });
}

export function applyLegalHold(evidenceId: string, session: Session): Promise<{ evidence_id: string; legal_hold: string }> {
  return apiFetch('evidence', `/v1/evidence/${evidenceId}/legal-hold`, {
    method: 'POST',
    body: {},
    session,
  });
}

/* ------------------------------------------------------------------ */
/* Audit (append-only hash chain)                                      */
/* ------------------------------------------------------------------ */

export interface AuditEntry {
  id: string;
  sequence: number;
  entry_hash: string;
  previous_hash: string;
  signature: string;
}

export function appendAuditEntry(
  body: { event_type: string; subject_ref: string; purpose: string; metadata?: Record<string, unknown> },
  session: Session,
): Promise<AuditEntry> {
  return apiFetch('audit', '/v1/audit/entries', { method: 'POST', body, session });
}

export function verifyAuditChain(
  tenantId: string,
  session: Session,
): Promise<{ valid: boolean; entries?: number; head?: string; failed_sequence?: number }> {
  return apiFetch('audit', `/v1/audit/verify/${tenantId}`, { session });
}

/* ------------------------------------------------------------------ */
/* Blockchain integrity ledger                                         */
/* ------------------------------------------------------------------ */

export interface AnchorRequest {
  tenant_hash: string;
  batch_id?: string;
  kind: 'audit_batch' | 'evidence_manifest' | 'disclosure_package' | 'policy_version';
  leaf_hashes: string[];
  metadata?: Record<string, unknown>;
}

export interface AnchorResult {
  anchor_id: string;
  merkle_root: string;
  leaf_count: number;
  mode: string;
  transaction_hash: string | null;
  chain_id: string | null;
}

export function createAnchor(body: AnchorRequest, session: Session): Promise<AnchorResult> {
  return apiFetch('ledger', '/v1/ledger/anchors', { method: 'POST', body, session });
}

export interface MerkleProofStep {
  index: number;
  sibling: string;
}

export function verifyLedgerProof(
  leafHash: string,
  root: string,
  proof: MerkleProofStep[],
): Promise<{ valid: boolean }> {
  return apiFetch('ledger', '/v1/ledger/proofs/verify', {
    method: 'POST',
    body: { leaf_hash: leafHash, root, proof },
    session: null,
  });
}

/* ------------------------------------------------------------------ */
/* AI gateway (advisory, human-reviewed)                               */
/* ------------------------------------------------------------------ */

export type AiCapability =
  | 'reporter_writing'
  | 'anonymity_scan'
  | 'triage_copilot'
  | 'evidence_chronology'
  | 'policy_retrieval'
  | 'investigation_summary'
  | 'translation'
  | 'pattern_analytics'
  | 'sla_remediation';

export interface AiRunRequest {
  tenant_id?: string;
  case_id?: string;
  capability: AiCapability;
  purpose: string;
  redacted_input: string;
  source_refs?: string[];
}

export interface AiRunResult {
  run_id: string;
  capability: AiCapability;
  status: string;
  output: string;
  source_refs: string[];
  uncertainty: string;
  requires_human_approval: boolean;
}

export function runAi(body: AiRunRequest, session: Session | null): Promise<AiRunResult> {
  return apiFetch('ai', '/v1/ai/runs', { method: 'POST', body, session });
}

export type AiRunStatus = 'awaiting_human_review' | 'approved' | 'rejected';

export interface AiRunView {
  id: string;
  tenant_id: string;
  case_id: string | null;
  capability: AiCapability;
  purpose: string;
  input_hash: string;
  input_length: number;
  source_refs: string[];
  output: string;
  uncertainty: string;
  status: AiRunStatus;
  requires_human_approval: boolean;
  provider: string;
  model: string;
  requested_by: string | null;
  requested_at: string;
  reviewed_by: string | null;
  decision_note: string | null;
  decided_at: string | null;
}

export interface AiRunQuery {
  tenant_id?: string;
  capability?: AiCapability;
  status?: AiRunStatus;
  limit?: number;
  offset?: number;
}

/** List recorded AI runs for audit and human review (superuser). */
export function listAiRuns(session: Session | null, query?: AiRunQuery): Promise<{ runs: AiRunView[]; count: number }> {
  const qs = new URLSearchParams();
  if (query?.tenant_id) qs.set('tenant_id', query.tenant_id);
  if (query?.capability) qs.set('capability', query.capability);
  if (query?.status) qs.set('status', query.status);
  if (typeof query?.limit === 'number') qs.set('limit', String(query.limit));
  if (typeof query?.offset === 'number') qs.set('offset', String(query.offset));
  const suffix = qs.size > 0 ? `?${qs.toString()}` : '';
  return apiFetch('ai', `/v1/ai/runs${suffix}`, { session });
}

export function getAiRun(id: string, session: Session | null): Promise<AiRunView> {
  return apiFetch('ai', `/v1/ai/runs/${id}`, { session });
}

export interface ReviewAiRunBody {
  approved: boolean;
  note?: string;
}

/** Approve or reject an AI draft. Advisory output is never applied until a human decides. */
export function reviewAiRun(id: string, body: ReviewAiRunBody, session: Session | null): Promise<AiRunView> {
  return apiFetch('ai', `/v1/ai/runs/${id}/review`, { method: 'POST', body, session });
}

export interface AiGovernance {
  capabilities: { name: string; description?: string }[];
  prohibited_purposes: string[];
  raw_evidence_allowed: boolean;
  human_approval_default: boolean;
  provider: string;
}

export function getAiGovernance(): Promise<AiGovernance> {
  return apiFetch('ai', '/v1/ai/governance', { session: null });
}

export interface TranslateResult {
  target_locale: string;
  source_locale: string;
  values: Record<string, string>;
}

/** Translate a UI dictionary into any language via the AI gateway (Azure Translator). */
export function translateMessages(
  targetLocale: string,
  source: Record<string, string>,
  sourceLocale = 'en',
): Promise<TranslateResult> {
  return apiFetch('ai', '/v1/ai/translate', {
    method: 'POST',
    body: { target_locale: targetLocale, source_locale: sourceLocale, source },
    session: null,
  });
}

export interface SupportedLanguage {
  code: string;
  name: string;
}

/** List every language the translation backend supports (100+ via Azure). */
export function getSupportedLanguages(): Promise<{ languages: SupportedLanguage[]; provider?: string }> {
  return apiFetch('ai', '/v1/ai/languages', { session: null });
}

const I18N_CACHE_KEY = 'wpc:i18n:translate-cache:v2';

interface TranslationCacheEntry {
  hashes: Record<string, number>;
  values: Record<string, string>;
}

function fnv1a(text: string): number {
  let hash = 0x811c9dc5;
  for (let i = 0; i < text.length; i++) {
    hash ^= text.charCodeAt(i);
    hash = Math.imul(hash, 0x01000193);
  }
  return hash >>> 0;
}

function loadTranslationCache(): Record<string, TranslationCacheEntry> {
  try {
    const raw = localStorage.getItem(I18N_CACHE_KEY);
    const parsed = raw ? (JSON.parse(raw) as Record<string, TranslationCacheEntry>) : {};
    const clean: Record<string, TranslationCacheEntry> = {};
    for (const [locale, entry] of Object.entries(parsed)) {
      if (
        entry &&
        typeof entry === 'object' &&
        typeof entry.hashes === 'object' &&
        entry.hashes !== null &&
        typeof entry.values === 'object' &&
        entry.values !== null
      ) {
        clean[locale] = entry;
      }
    }
    return clean;
  } catch {
    return {};
  }
}

function saveTranslationCache(cache: Record<string, TranslationCacheEntry>): void {
  try {
    localStorage.setItem(I18N_CACHE_KEY, JSON.stringify(cache));
  } catch {
    /* storage full or unavailable - translation still works, just uncached */
  }
}

/**
 * Translate a UI dictionary with an incremental local cache.
 *
 * The source strings are content-hashed per key; when a target locale is
 * requested again, only keys whose English text changed are sent to the
 * gateway - everything else is served from the local cache. If nothing
 * changed, no network call happens at all.
 */
export async function translateMessagesCached(
  targetLocale: string,
  source: Record<string, string>,
  sourceLocale = 'en',
): Promise<Record<string, string>> {
  const cache = loadTranslationCache();
  const entry = cache[targetLocale];

  const changed: Record<string, string> = {};
  for (const key of Object.keys(source)) {
    if (!entry?.hashes || entry.hashes[key] !== fnv1a(source[key])) {
      changed[key] = source[key];
    }
  }

  if (Object.keys(changed).length === 0 && entry) {
    return entry.values;
  }

  const values: Record<string, string> = {};
  if (entry) {
    for (const key of Object.keys(source)) {
      if (entry.hashes[key] === fnv1a(source[key])) values[key] = entry.values[key];
    }
  }

  const result = await translateMessages(targetLocale, changed, sourceLocale);
  for (const key of Object.keys(result.values)) {
    values[key] = result.values[key];
  }
  for (const key of Object.keys(changed)) {
    if (!(key in values)) values[key] = source[key];
  }

  // Only lock in values that actually differ from the English source. A value
  // identical to the source is almost always an untranslated fallback, so it is
  // left unlocked and re-requested on the next load (self-healing once a real
  // translation becomes available), instead of being cached as English forever.
  const hashes: Record<string, number> = {};
  for (const key of Object.keys(source)) {
    if (values[key] !== source[key]) hashes[key] = fnv1a(source[key]);
  }
  cache[targetLocale] = { hashes, values };
  saveTranslationCache(cache);
  return values;
}

/* ------------------------------------------------------------------ */
/* Gateway-native endpoints                                            */
/* ------------------------------------------------------------------ */

export function gatewayServices(): Promise<Record<string, string>> {
  return apiFetch('/v1/services', { session: null });
}

export async function gatewayHealth(): Promise<Record<string, { status: string }>> {
  const result = await apiFetch<{ services: Record<string, { status: string }> }>('/v1/health/aggregate', {
    session: null,
  });
  return result.services;
}
