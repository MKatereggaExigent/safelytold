"""Build a deployable Keycloak realm without development users or origins."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'infrastructure' / 'keycloak' / 'safelytold-realm.json'


def build(public_origin: str) -> dict:
    origin = public_origin.rstrip('/')
    parsed = urlparse(origin)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.hostname in {'localhost', '127.0.0.1'}:
        raise ValueError('Production public origin must be a non-local HTTPS origin')
    realm = json.loads(SOURCE.read_text(encoding='utf-8'))
    realm['sslRequired'] = 'all'
    realm['users'] = []
    for client in realm['clients']:
        if client['clientId'] == 'safelytold-staff':
            client['redirectUris'] = [f'{origin}/staff/auth/callback']
            client['webOrigins'] = [origin]
            client.setdefault('attributes', {})['post.logout.redirect.uris'] = f'{origin}/staff/login'
        elif client['clientId'] == 'safelytold-reporter-confidential':
            client['redirectUris'] = [f'{origin}/*']
            client['webOrigins'] = [origin]
    return realm


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--public-origin', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(build(args.public_origin), indent=2) + '\n', encoding='utf-8')
    print(output)


if __name__ == '__main__':
    main()
