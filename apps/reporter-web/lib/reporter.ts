export const JURISDICTIONS = [
  { value: 'ZA', key: 'jur_ZA', label: 'South Africa (ZA)' },
  { value: 'GB', key: 'jur_GB', label: 'United Kingdom (GB)' },
  { value: 'EU', key: 'jur_EU', label: 'European Union (EU)' },
  { value: 'US', key: 'jur_US', label: 'United States (US)' },
  { value: 'GLOBAL', key: 'jur_GLOBAL', label: 'Global / other' },
];

export const TAXONOMY_GROUPS = [
  { value: 'fraud_financial_crime', label: 'Fraud and financial crime', items: [
    ['fraud', 'Fraud'], ['theft', 'Theft'], ['bribery', 'Bribery'], ['procurement_irregularity', 'Procurement irregularity'], ['money_laundering', 'Money laundering'], ['expense_fraud', 'Expense fraud'],
  ] },
  { value: 'people_workplace_conduct', label: 'People and workplace conduct', items: [
    ['bullying', 'Bullying'], ['harassment', 'Harassment'], ['sexual_harassment', 'Sexual harassment'], ['discrimination', 'Discrimination'], ['racism', 'Racism'], ['favouritism', 'Favouritism'], ['nepotism', 'Nepotism'], ['intimidation', 'Intimidation'],
  ] },
  { value: 'workplace_fairness', label: 'Workplace fairness', items: [
    ['unfair_disciplinary_action', 'Unfair disciplinary action'], ['unfair_labour_practice', 'Unfair labour practice'], ['promotion_irregularity', 'Promotion irregularity'], ['performance_management_abuse', 'Performance-management abuse'], ['retaliation', 'Retaliation'], ['victimisation', 'Victimisation'], ['hr_matters', 'Human resources matters'],
  ] },
  { value: 'governance', label: 'Governance', items: [
    ['conflict_of_interest', 'Conflict of interest'], ['policy_breach', 'Policy breach'], ['abuse_of_authority', 'Abuse of authority'], ['inappropriate_conduct', 'Inappropriate conduct'], ['unethical_business_practice', 'Unethical business practice'], ['misconduct', 'Misconduct'],
  ] },
  { value: 'safety', label: 'Safety', items: [
    ['health_and_safety', 'Health and safety'], ['violence', 'Violence'], ['unsafe_working_conditions', 'Unsafe working conditions'], ['working_conditions', 'Working conditions'],
  ] },
  { value: 'public_interest', label: 'Public interest', items: [
    ['corruption', 'Corruption'], ['service_delivery', 'Service delivery'], ['environment', 'Environment'], ['public_infrastructure', 'Public infrastructure'],
  ] },
] as const;

export const TAXONOMY = [
  ...TAXONOMY_GROUPS.flatMap((group) => group.items.map(([value, label]) => ({ value, key: `tax_${value}`, label, domain: group.value }))),
  // Legacy categories stay readable for reports created before the ontology.
  { value: 'bullying_harassment', key: 'tax_bullying', label: 'Bullying or harassment' },
  { value: 'fraud_abuse', key: 'tax_fraud', label: 'Fraud or abuse of authority' },
  { value: 'safety', key: 'tax_safety', label: 'Health or safety risk' },
  { value: 'integrity', key: 'tax_integrity', label: 'Other integrity concern' },
];

export const REPORTER_TYPES = [
  { value: 'employee', label: 'Employee' },
  { value: 'contractor', label: 'Contractor' },
  { value: 'former_employee', label: 'Former employee' },
  { value: 'supplier', label: 'Supplier' },
  { value: 'customer', label: 'Customer' },
  { value: 'anonymous_witness', label: 'Anonymous witness' },
  { value: 'other', label: 'Other relationship' },
] as const;

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
    value: 'verified_anonymous',
    key: 'mode_verified_anonymous',
    badgeKey: 'mode_verified_anon_badge',
    descKey: 'mode_verified_anon_desc',
    title: 'Verified anonymous',
    badge: 'Eligibility proven, identity not retained',
    description: 'Available on restricted organisation channels after an unlinkable eligibility credential is redeemed.',
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
