/* De-identified aggregate patterns compiled from published research on
 * workplace misconduct reporting. Figures are indicative ranges, not data
 * from this platform, and never relate to any individual report or case. */

export interface RankedInsight {
  rank: number;
  key: string;
  label: string;
  noteKey: string;
  share?: string;
  note: string;
}

export const COMMON_REPORT_TYPES: RankedInsight[] = [
  { rank: 1, key: 'wi_type_1', label: 'Bullying and psychological harassment', noteKey: 'wi_type_1_note', share: '≈ 30%', note: 'Consistently the most-reported category in global surveys.' },
  { rank: 2, key: 'wi_type_2', label: 'Discrimination and unequal treatment', noteKey: 'wi_type_2_note', share: '≈ 20%', note: 'Widely under-reported relative to the share who experience it.' },
  { rank: 3, key: 'wi_type_3', label: 'Abuse of power or unfair management', noteKey: 'wi_type_3_note', share: '≈ 15%', note: 'Often overlaps with other categories and retaliation claims.' },
  { rank: 4, key: 'wi_type_4', label: 'Fraud, corruption or conflict of interest', noteKey: 'wi_type_4_note', share: '≈ 10%', note: 'More likely to be raised in identified reports than anonymous ones.' },
  { rank: 5, key: 'wi_type_5', label: 'Retaliation for speaking up', noteKey: 'wi_type_5_note', share: '≈ 8%', note: 'Usually reported only after a first concern went unanswered.' },
  { rank: 6, key: 'wi_type_6', label: 'Health and safety risk', noteKey: 'wi_type_6_note', share: '≈ 7%', note: 'Tends to rise in sectors with physical or regulated environments.' },
  { rank: 7, key: 'wi_type_7', label: 'Other integrity concerns', noteKey: 'wi_type_7_note', share: '≈ 10%', note: 'Mixed and jurisdiction-specific.' },
];

export const ROOT_CAUSES: RankedInsight[] = [
  { rank: 1, key: 'wi_cause_1', label: 'Fear of retaliation', noteKey: 'wi_cause_1_note', note: 'The leading reason reporters stay silent across studies.' },
  { rank: 2, key: 'wi_cause_2', label: 'Unclear or invisible reporting channels', noteKey: 'wi_cause_2_note', note: 'People do not know where, how, or to whom they can report safely.' },
  { rank: 3, key: 'wi_cause_3', label: 'Normalisation of behaviour', noteKey: 'wi_cause_3_note', note: 'Persistent behaviour becomes treated as “the way things work”.' },
  { rank: 4, key: 'wi_cause_4', label: 'Power imbalance', noteKey: 'wi_cause_4_note', note: 'Reports often target people who control outcomes for the reporter.' },
  { rank: 5, key: 'wi_cause_5', label: 'Inconsistent enforcement', noteKey: 'wi_cause_5_note', note: 'Consequences for similar conduct vary, undermining trust in process.' },
  { rank: 6, key: 'wi_cause_6', label: 'Low psychological safety', noteKey: 'wi_cause_6_note', note: 'Teams where speaking up is punished, even subtly, report less.' },
];

export const COMMON_REMEDIES: RankedInsight[] = [
  { rank: 1, key: 'wi_rem_1', label: 'Independent, confidential channels', noteKey: 'wi_rem_1_note', note: 'Multiple entry points — anonymous, confidential and identified.' },
  { rank: 2, key: 'wi_rem_2', label: 'Clear anti-retaliation safeguards', noteKey: 'wi_rem_2_note', note: 'Protection plans and follow-up reduce fear and increase reporting.' },
  { rank: 3, key: 'wi_rem_3', label: 'Visible case timelines and feedback', noteKey: 'wi_rem_3_note', note: 'Reporters who hear back feel the process was fair.' },
  { rank: 4, key: 'wi_rem_4', label: 'Upstander and bystander training', noteKey: 'wi_rem_4_note', note: 'Builds a culture where peers challenge unacceptable conduct.' },
  { rank: 5, key: 'wi_rem_5', label: 'Leadership accountability', noteKey: 'wi_rem_5_note', note: 'Consequences applied consistently, including at senior levels.' },
  { rank: 6, key: 'wi_rem_6', label: 'Aggregate, de-identified outcome reporting', noteKey: 'wi_rem_6_note', note: 'Publishing anonymised trends builds confidence that reports matter.' },
];

export const OUTCOME_SIGNALS: { label: string; key: string; value: string; hint: string; hintKey: string }[] = [
  {
    key: 'wi_sig_fair',
    label: 'Fair process perception',
    value: '2×',
    hint: 'Reporters who receive updates and clear timelines are about twice as likely to rate the process as fair.',
    hintKey: 'wi_sig_fair_hint',
  },
  {
    key: 'wi_sig_confidential',
    label: 'Confidentiality preference',
    value: '≈ 7 in 10',
    hint: 'Most reporters choose confidential or anonymous channels when given the option.',
    hintKey: 'wi_sig_confidential_hint',
  },
  {
    key: 'wi_sig_retaliation',
    label: 'Retaliation risk',
    value: 'Higher',
    hint: 'Retaliation risk rises sharply when no protection plan or follow-up is in place.',
    hintKey: 'wi_sig_retaliation_hint',
  },
];
