"""Canonical public reporting modes used across every bounded context."""

REPORTING_MODES = frozenset({
    'anonymous',
    'verified_anonymous',
    'confidential',
    'identified',
})

ANONYMOUS_REPORTING_MODES = frozenset({'anonymous', 'verified_anonymous'})
IDENTITY_BEARING_REPORTING_MODES = frozenset({'confidential', 'identified'})
