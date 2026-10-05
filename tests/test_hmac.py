import hashlib
import hmac

from app.hmac_utils import generate_signature, verify_signature


def test_hmac_signature_matches_standard_hmac():
    body = b'{"hello":"world"}'
    secret = "test-secret"

    expected = "sha256=" + hmac.new(
        secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    assert generate_signature(body, secret) == expected
    assert verify_signature(body, expected, secret)


def test_hmac_rejects_modified_body():
    body = b'{"hello":"world"}'
    secret = "test-secret"
    signature = generate_signature(body, secret)

    assert not verify_signature(b'{"hello":"changed"}', signature, secret)
