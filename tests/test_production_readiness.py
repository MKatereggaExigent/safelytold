from scripts.check_production_readiness import assess

def test_readiness_manifest_has_valid_evidence() -> None:
    errors, blockers = assess()
    assert errors == []
    assert blockers, "Production must not be declared ready without operational sign-off"
