"""Canonical concern categories accepted by SafelyTold intake.

Codes are stable storage/API values. Labels belong in the client translation
catalogues. Legacy codes remain accepted so existing reports stay readable.
"""

MISCONDUCT_ONTOLOGY = {
    'fraud_financial_crime': {
        'fraud', 'theft', 'bribery', 'procurement_irregularity',
        'money_laundering', 'expense_fraud',
    },
    'people_workplace_conduct': {
        'bullying', 'harassment', 'sexual_harassment', 'discrimination',
        'racism', 'favouritism', 'nepotism', 'intimidation',
    },
    'workplace_fairness': {
        'unfair_disciplinary_action', 'unfair_labour_practice',
        'promotion_irregularity', 'performance_management_abuse',
        'retaliation', 'victimisation', 'hr_matters',
    },
    'governance': {
        'conflict_of_interest', 'policy_breach', 'abuse_of_authority',
        'inappropriate_conduct', 'unethical_business_practice', 'misconduct',
    },
    'safety': {
        'health_and_safety', 'violence', 'unsafe_working_conditions',
        'working_conditions',
    },
    'public_interest': {
        'corruption', 'service_delivery', 'environment', 'public_infrastructure',
    },
}

CATEGORY_PARENT = {
    category: parent
    for parent, categories in MISCONDUCT_ONTOLOGY.items()
    for category in categories
}

CONCERN_CATEGORY_CODES = frozenset(CATEGORY_PARENT) | frozenset({
    'harassment',
    'discrimination',
    'racism',
    'intimidation',
    'nepotism',
    'victimisation',
    'unfair_disciplinary_action',
    'unfair_labour_practice',
    'working_conditions',
    'hr_matters',
    'conflict_of_interest',
    'inappropriate_conduct',
    'unethical_business_practice',
    # Existing SafelyTold codes retained for backward compatibility.
    'bullying_harassment',
    'retaliation',
    'fraud_abuse',
    'safety',
    'integrity',
})


def validate_concern_categories(values: list[str]) -> list[str]:
    """Return unique canonical codes or raise a client-safe validation error."""
    cleaned = list(dict.fromkeys(value.strip().lower() for value in values if value.strip()))
    if not cleaned:
        raise ValueError('Choose at least one concern category')
    unknown = sorted(set(cleaned) - CONCERN_CATEGORY_CODES)
    if unknown:
        raise ValueError(f'Unsupported concern category: {", ".join(unknown)}')
    return cleaned
