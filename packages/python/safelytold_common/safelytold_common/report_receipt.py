from typing import Any


CRYPTOGRAPHIC_ELIGIBILITY_CLASSES = frozenset({
    'cryptographically_verified', 'workforce_verified_unlinkable', 'verified_anonymous',
})


def build_privacy_receipt(*, organisation: str, organisation_slug: str,
                          reporter_type: str, eligibility_class: str,
                          mode: str, identity_provided: bool) -> dict[str, Any]:
    anonymous = mode in {'anonymous', 'verified_anonymous'}
    return {
        'organisation': organisation,
        'organisation_slug': organisation_slug,
        'reporter_type': reporter_type,
        'eligibility': 'cryptographically_verified' if eligibility_class in CRYPTOGRAPHIC_ELIGIBILITY_CLASSES else 'not_cryptographically_verified',
        'reporter_identity': 'unknown' if anonymous else ('provided' if identity_provided else 'not_provided'),
        'identity_stored': False if anonymous else identity_provided,
        'ip_stored': False,
        'device_id_stored': False,
        'corporate_sso_id_stored': False,
        'anonymous_mailbox': True,
    }
