import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_event_contracts_have_no_free_text() -> None:
    forbidden = {'body','content','description','evidence','identity','message','narrative','statement','secret','token'}
    for path in (ROOT/'contracts'/'events').glob('*.json'):
        data = json.loads(path.read_text())['properties']['data']['properties']
        assert not (set(data) & forbidden), path.name
