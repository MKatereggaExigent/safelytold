import type { Session } from '@safelytold/ui/api';

export const STAFF_ROLES = [
  { value: 'triage_officer', label: 'Triage officer' },
  { value: 'case_manager', label: 'Case manager' },
  { value: 'investigator', label: 'Investigator' },
  { value: 'legal_counsel', label: 'Legal counsel' },
  { value: 'dpo', label: 'DPO / privacy officer' },
  { value: 'ethics_administrator', label: 'Ethics administrator' },
  { value: 'board_delegate', label: 'Ombuds / board delegate' },
] as const;

export const STAFF_ROLE_LABEL: Record<string, string> = Object.fromEntries(
  STAFF_ROLES.map((r) => [r.value, r.label]),
);

export const PURPOSES = [
  'development',
  'triage',
  'investigation',
  'case-management',
  'privacy-review',
  'evidence-preservation',
  'oversight',
  'legal-review',
] as const;

export function staffSession(role: string, purpose: string, displayName: string): Session {
  return {
    tenantId: '00000000-0000-0000-0000-000000000001',
    subject: `staff-${role}-${displayName.toLowerCase().replace(/[^a-z0-9]+/g, '') || 'user'}`,
    roles: [role],
    purpose,
    displayName: displayName || (STAFF_ROLE_LABEL[role] ?? role),
  };
}

export const CASE_STATUSES = ['unverified', 'triage', 'reviewing', 'await_information', 'under_investigation', 'substantiated', 'unsubstantiated', 'inconclusive', 'referred', 'resolved', 'closed'] as const;

export const CASE_STATUS_LABELS: Record<string, string> = {
  unverified: 'Unverified',
  triage: 'In triage',
  reviewing: 'Under review',
  await_information: 'Awaiting information',
  under_investigation: 'Under investigation',
  substantiated: 'Substantiated',
  unsubstantiated: 'Unsubstantiated',
  inconclusive: 'Inconclusive',
  referred: 'Referred',
  resolved: 'Resolved',
  closed: 'Closed',
};

export const TAXONOMY_LABELS: Record<string, string> = {
  bullying_harassment: 'Bullying and psychological harassment',
  discrimination: 'Discrimination and unequal treatment',
  retaliation: 'Retaliation for speaking up',
  abuse_of_power: 'Abuse of power',
  fraud_corruption: 'Fraud, corruption and conflict of interest',
  safety_health: 'Safety and health risk',
  process_fairness: 'Unfair process',
  integrity: 'Integrity and ethical conduct',
};

export interface CaseSummary {
  id: string;
  status: string;
  mode: string;
  jurisdiction_code?: string;
  taxonomy_codes?: string[];
  immediate_risk?: boolean;
  created_at?: string;
  updated_at?: string;
}

export function summarizeCase(record: { id: string; status: string; payload: Record<string, unknown> }): CaseSummary {
  const p = record.payload as Record<string, unknown>;
  return {
    id: record.id,
    status: record.status,
    mode: (p.mode as string) ?? 'unknown',
    jurisdiction_code: p.jurisdiction_code as string,
    taxonomy_codes: Array.isArray(p.taxonomy_codes) ? (p.taxonomy_codes as string[]) : [],
    immediate_risk: Boolean(p.immediate_risk),
    created_at: (p.created_at as string) ?? record.id,
  };
}

export function latestCaseRecords<T extends { id: string; payload: Record<string, unknown> }>(records: T[]): T[] {
  const byCase = new Map<string, T>();
  for (const r of records) {
    const caseId = (r.payload.case_id as string) ?? r.id;
    const stamp = (r.payload.created_at as string) ?? r.id;
    const existing = byCase.get(caseId);
    if (!existing || stamp > ((existing.payload.created_at as string) ?? existing.id)) byCase.set(caseId, r);
  }
  return [...byCase.values()];
}
