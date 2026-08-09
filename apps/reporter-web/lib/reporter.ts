export const JURISDICTIONS = [
  { value: 'ZA', key: 'jur_ZA', label: 'South Africa (ZA)' },
  { value: 'GB', key: 'jur_GB', label: 'United Kingdom (GB)' },
  { value: 'EU', key: 'jur_EU', label: 'European Union (EU)' },
  { value: 'US', key: 'jur_US', label: 'United States (US)' },
  { value: 'GLOBAL', key: 'jur_GLOBAL', label: 'Global / other' },
];

export const TAXONOMY = [
  { value: 'bullying_harassment', key: 'tax_bullying', label: 'Bullying or harassment' },
  { value: 'discrimination', key: 'tax_discrimination', label: 'Discrimination' },
  { value: 'retaliation', key: 'tax_retaliation', label: 'Retaliation for raising a concern' },
  { value: 'fraud_abuse', key: 'tax_fraud', label: 'Fraud or abuse of authority' },
  { value: 'safety', key: 'tax_safety', label: 'Health or safety risk' },
  { value: 'integrity', key: 'tax_integrity', label: 'Other integrity concern' },
];

export const IMPACT_CATEGORIES = [
  { value: 'physical_safety', key: 'imp_physical', label: 'Physical safety at risk' },
  { value: 'mental_health', key: 'imp_mental', label: 'Impact on wellbeing or mental health' },
  { value: 'career', key: 'imp_career', label: 'Impact on role, pay or career' },
  { value: 'personal', key: 'imp_personal', label: 'Personal or family impact' },
  { value: 'other', key: 'imp_other', label: 'Other impact' },
];

export const SUPPORT_TYPES = [
  { value: 'family', key: 'sup_family', label: 'Family member' },
  { value: 'union', key: 'sup_union', label: 'Union representative' },
  { value: 'attorney', key: 'sup_attorney', label: 'Attorney or advocate' },
  { value: 'colleague', key: 'sup_colleague', label: 'Trusted colleague' },
];

export const SUPPORT_PERMISSIONS = [
  { value: 'status_updates', key: 'sup_perm_status', label: 'View selected status updates' },
  { value: 'draft_messages', key: 'sup_perm_draft', label: 'Help draft messages' },
  { value: 'attend_interviews', key: 'sup_perm_interviews', label: 'Attend selected interviews' },
];

export const REPORT_MODES = [
  {
    value: 'anonymous',
    key: 'mode_anonymous',
    badgeKey: 'mode_anon_badge',
    descKey: 'mode_anon_desc',
    title: 'Anonymous',
    badge: 'No identity required',
    description: 'Receive a random case code and a separate secret. The platform cannot link the report back to you.',
  },
  {
    value: 'confidential',
    key: 'mode_confidential',
    badgeKey: 'mode_conf_badge',
    descKey: 'mode_conf_desc',
    title: 'Confidential',
    badge: 'Identity vaulted',
    description: 'Your identity is encrypted in a separate realm. Exceptional disclosure needs independent dual approval.',
  },
  {
    value: 'identified',
    key: 'mode_identified',
    badgeKey: 'mode_iden_badge',
    descKey: 'mode_iden_desc',
    title: 'Identified',
    badge: 'Direct follow-up',
    description: 'Share your contact details for direct follow-up while keeping case-level access controls in place.',
  },
];

export const CASE_STATUS_LABELS: Record<string, { key: string; label: string }> = {
  unverified: { key: 'cstatus_unverified', label: 'Received, not yet verified' },
  triage: { key: 'cstatus_triage', label: 'In triage' },
  investigating: { key: 'cstatus_investigating', label: 'Investigation in progress' },
  review: { key: 'cstatus_review', label: 'Under review' },
  decided: { key: 'cstatus_decided', label: 'Decision recorded' },
  remediated: { key: 'cstatus_remediated', label: 'Remediation in progress' },
  closed: { key: 'cstatus_closed', label: 'Closed' },
  referred: { key: 'cstatus_referred', label: 'Referred to a specialist' },
};

const STORAGE_KEY = 'wpc:reporter:case';

export interface ReporterCase {
  caseId: string;
  publicCode: string;
  /** Short-lived reporter JWT. Absent until the mailbox has been opened at least once. */
  token?: string;
  /** ISO timestamp for token expiry; used to prompt a fresh unlock. */
  expiresAt?: string;
}

export function storeReporterCase(c: ReporterCase): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(c));
}

export function loadReporterCase(): ReporterCase | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as ReporterCase;
    if (!parsed.caseId || !parsed.publicCode) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function clearReporterCase(): void {
  localStorage.removeItem(STORAGE_KEY);
}
