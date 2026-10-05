import hashlib
import hmac


def generate_signature(body: bytes, secret: str) -> str:
    digest = hmac.new(
        secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
    return f"sha256={digest}"


def verify_signature(body: bytes, signature: str, secret: str) -> bool:
    expected = generate_signature(body, secret)
    return hmac.compare_digest(expected, signature)
