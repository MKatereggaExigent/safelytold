from safelytold_common.report_receipt import build_privacy_receipt


def test_verified_anonymous_receipt_never_claims_identity_storage() -> None:
    receipt = build_privacy_receipt(
        organisation='CTICC', organisation_slug='cticc', reporter_type='employee',
        eligibility_class='workforce_verified_unlinkable', mode='verified_anonymous',
        identity_provided=True,
    )
    assert receipt == {
        'organisation': 'CTICC',
        'organisation_slug': 'cticc',
        'reporter_type': 'employee',
        'eligibility': 'cryptographically_verified',
        'reporter_identity': 'unknown',
        'identity_stored': False,
        'ip_stored': False,
        'device_id_stored': False,
        'corporate_sso_id_stored': False,
        'anonymous_mailbox': True,
    }


def test_open_channel_does_not_claim_cryptographic_verification() -> None:
    receipt = build_privacy_receipt(
        organisation='CTICC', organisation_slug='cticc', reporter_type='employee',
        eligibility_class='open_unverified', mode='anonymous', identity_provided=False,
    )
    assert receipt['eligibility'] == 'not_cryptographically_verified'
