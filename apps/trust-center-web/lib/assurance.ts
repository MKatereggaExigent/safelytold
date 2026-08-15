export const LIFECYCLE = [
  { stage: 'Before wrongdoing', capabilities: ['Policy awareness', 'Culture signals', 'Safe reporting channels'] },
  { stage: 'Report', capabilities: ['Anonymous', 'Verified anonymous', 'Confidential', 'Identified'] },
  { stage: 'Triage', capabilities: ['Conflict detection', 'Severity assessment', 'Jurisdiction', 'Safeguarding'] },
  { stage: 'Case management', capabilities: ['Evidence', 'Investigators', 'Deadlines', 'Escalation', 'Procedural fairness'] },
  { stage: 'Reporter protection', capabilities: ['Anonymous follow-up', 'Retaliation monitoring', 'Protection measures'] },
  { stage: 'Resolution', capabilities: ['Outcome', 'Remediation', 'Appeal and review', 'Audit trail'] },
  { stage: 'Organisation intelligence', capabilities: ['Recurring units and roles', 'Systemic patterns', 'Unresolved risks', 'Case-handling performance', 'Board governance'] },
] as const;
