from services.analytics_service.app.main import thresholded


def test_thresholded_aggregates_and_suppresses_small_cohorts() -> None:
    result = thresholded([({'category': 'fraud'}, 2), ({'category': 'fraud'}, 4), ({'category': 'safety'}, 3)], 5)
    assert result == [
        {'dimensions': {'category': 'fraud'}, 'value': 6, 'suppressed': False},
        {'dimensions': {'category': 'safety'}, 'value': None, 'suppressed': True},
    ]
