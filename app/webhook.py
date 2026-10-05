import json
from datetime import datetime, timezone
from typing import Any, Optional, Tuple

import httpx

from .config import HTTP_TIMEOUT_SECONDS, WEBHOOK_SECRET
from .hmac_utils import generate_signature


def _json_default(value: Any):
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def build_webhook_body(event) -> bytes:
    # The assessment does not prescribe an outgoing body shape.
    # We send a useful event envelope and sign these exact bytes.
    body = {
        "id": event.id,
        "type": event.type,
        "payload": event.payload,
        "created_at": event.created_at,
    }
    return json.dumps(
        body,
        separators=(",", ":"),
        sort_keys=True,
        default=_json_default,
    ).encode("utf-8")


async def deliver_event(event) -> Tuple[bool, Optional[int]]:
    body = build_webhook_body(event)
    signature = generate_signature(body, WEBHOOK_SECRET)

    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature,
        "X-Webhook-Event-ID": event.id,
    }

    try:
        async with httpx.AsyncClient(
            timeout=HTTP_TIMEOUT_SECONDS,
            follow_redirects=False,
        ) as client:
            response = await client.post(
                event.webhook_url,
                content=body,
                headers=headers,
            )

        return 200 <= response.status_code < 300, response.status_code

    except (httpx.TimeoutException, httpx.RequestError):
        return False, None
