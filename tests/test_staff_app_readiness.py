from scripts.check_staff_app_readiness import assess


def test_staff_application_has_no_demo_dependencies() -> None:
    assert assess() == []
