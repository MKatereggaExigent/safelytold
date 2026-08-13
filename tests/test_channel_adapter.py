import hashlib
import hmac

from services.integration_service.app.channels import valid_signature


def test_provider_signature_and_replay_window() -> None:
    raw = b'{"safe":"payload"}'
    timestamp = '1000'
    secret = 'test-secret-that-is-not-for-production'
    signature = hmac.new(secret.encode(), timestamp.encode() + b'.' + raw, hashlib.sha256).hexdigest()
    assert valid_signature(raw, timestamp, f'sha256={signature}', secret, now=1100)
    assert not valid_signature(raw, timestamp, signature, secret, now=1400)
    assert not valid_signature(raw + b'x', timestamp, signature, secret, now=1100)
