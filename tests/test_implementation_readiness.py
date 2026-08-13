from scripts.check_implementation_readiness import assess


def test_implementation_gate_detects_remaining_scaffolds() -> None:
    blockers = assess()
    assert blockers == [], '\n'.join(blockers)
