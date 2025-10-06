import hmac
import hashlib

from services.ingest_services import _sign_serial, _verify_token
from config.settings import settings


def test_sign_serial_matches_python_hmac():
    secret = "ABLE-SECRET"
    serial = "AI-ABCDE1"
    expected = hmac.new(secret.encode(), serial.encode(), hashlib.sha256).hexdigest()
    assert _sign_serial(secret, serial) == expected


def test_verify_token_true_and_false(monkeypatch):
    # Force the provision secret to a known value
    monkeypatch.setattr(settings, "provision_secret", "ABLE-SECRET", raising=False)
    serial = "AI-ABCDE1"
    token = _sign_serial(settings.provision_secret, serial)

    assert _verify_token(serial, token) is True
    assert _verify_token(serial, "bad-token") is False


