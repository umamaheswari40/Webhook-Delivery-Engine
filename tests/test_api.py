import os
import tempfile

# Set an isolated SQLite database before importing the application.
tmp_db = os.path.join(tempfile.gettempdir(), "nestack_test_webhook.db")
os.environ["DATABASE_URL"] = "sqlite:///" + tmp_db
os.environ["WEBHOOK_SECRET"] = "test-secret"

from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


def test_create_and_get_event():
    with TestClient(app) as client:
        response = client.post(
            "/events",
            json={
                "type": "user.signup",
                "payload": {"user_id": 123},
                "webhook_url": "https://example.com/webhook",
            },
        )

        assert response.status_code == 201

        event = response.json()
        assert event["type"] == "user.signup"
        assert event["status"] == "pending"
        assert event["attempts"] == []

        event_id = event["id"]

        response = client.get(f"/events/{event_id}")
        assert response.status_code == 200
        assert response.json()["id"] == event_id


def test_retry_non_dead_returns_400():
    with TestClient(app) as client:
        response = client.post(
            "/events",
            json={
                "type": "payment.failed",
                "payload": {"amount": 100},
                "webhook_url": "https://example.com/webhook",
            },
        )

        event_id = response.json()["id"]

        retry_response = client.post(f"/events/{event_id}/retry")
        assert retry_response.status_code == 400
