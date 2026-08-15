import pytest

from safelytold_common.taxonomy import CONCERN_CATEGORY_CODES, validate_concern_categories


REQUIRED_PRODUCTION_CATEGORIES = {
    'harassment', 'discrimination', 'racism', 'intimidation', 'nepotism',
    'victimisation', 'unfair_disciplinary_action', 'unfair_labour_practice',
    'working_conditions', 'hr_matters', 'conflict_of_interest',
    'inappropriate_conduct', 'unethical_business_practice',
}


def test_required_production_categories_are_supported() -> None:
    assert REQUIRED_PRODUCTION_CATEGORIES <= CONCERN_CATEGORY_CODES


def test_category_validation_normalises_and_deduplicates() -> None:
    assert validate_concern_categories([' Racism ', 'racism', 'harassment']) == ['racism', 'harassment']


def test_category_validation_rejects_unknown_codes() -> None:
    with pytest.raises(ValueError, match='Unsupported concern category'):
        validate_concern_categories(['internal_engineering_code'])
