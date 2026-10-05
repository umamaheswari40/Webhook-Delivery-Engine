# Webhook Delivery Engine

A FastAPI service that accepts webhook events, delivers them in the background, records delivery attempts, and retries failed deliveries on a fixed schedule.

## Features

- Create and inspect webhook events through a REST API.
- Deliver due events asynchronously with HTTPX.
- Retry failed deliveries after 30 seconds, 5 minutes, and 30 minutes (four total attempts).
- Persist events and retry state in SQLite so pending retries survive a restart.
- Sign each outgoing request with HMAC-SHA256 in the `X-Webhook-Signature` header.
- Manually re-queue events that reach the `dead` state.

## Requirements

- Python 3.9 or later
- pip

## Setup and run

Create and activate a virtual environment from this directory:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set a strong `WEBHOOK_SECRET` before using the service outside local development. The application uses a development secret if the variable is not set; do not use that default in production.

Start the API and background worker:

```bash
python run.py
```

The service listens on `http://localhost:8000`.

- Interactive API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

The worker starts with the API process.

## API

### Create an event

`POST /events`

```json
{
  "type": "payment.failed",
  "payload": {
    "user_id": 123,
    "amount": 500
  },
  "webhook_url": "https://example.com/webhook"
}
```

The request returns the new event, including its ID, status, and attempt history.

### List events

`GET /events`

### Get an event and its attempt history

`GET /events/{event_id}`

### Manually retry a dead event

`POST /events/{event_id}/retry`

This endpoint accepts only events in the `dead` state.

### Health check

`GET /health`

Returns `{"status":"ok"}` when the service is running.

## Delivery and retries

The initial delivery is attempted as soon as the event is due. A non-2xx response, timeout, or network error is recorded as a failed attempt. After a failure, the next attempt is scheduled for 30 seconds, 5 minutes, or 30 minutes later. After the fourth failed attempt, the event is marked `dead`.

The event status, retry count, and next attempt time are stored in SQLite. If the service restarts while an event is waiting, it resumes from the persisted schedule. Events whose retry time passed while the service was offline are delivered after startup.

## Request signing

Outgoing requests include:

```text
X-Webhook-Signature: sha256=<hex digest>
```

The digest is calculated as `HMAC-SHA256(WEBHOOK_SECRET, raw_request_body)`. Receivers should verify the exact raw request bytes before parsing the JSON body.

## Configuration

The following environment variables are supported:

| Variable | Default | Description |
| --- | --- | --- |
| `WEBHOOK_SECRET` | Development-only value | Secret used to sign outgoing requests. Set a strong value outside local development. |
| `DATABASE_URL` | `sqlite:///./webhook_engine.db` | SQLAlchemy database URL. |
| `WORKER_POLL_INTERVAL_SECONDS` | `0.5` | Interval at which the worker checks for due events. |
| `HTTP_TIMEOUT_SECONDS` | `10` | Timeout for outgoing webhook requests. |

## Tests

Run the test suite from this directory:

```bash
pytest -q
```

Tests cover API event operations, HMAC signing, and retry scheduling.
