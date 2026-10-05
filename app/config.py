import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./webhook_engine.db")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "dev-secret-change-me")
WORKER_POLL_INTERVAL_SECONDS = float(os.getenv("WORKER_POLL_INTERVAL_SECONDS", "0.5"))
HTTP_TIMEOUT_SECONDS = float(os.getenv("HTTP_TIMEOUT_SECONDS", "10"))

# Fixed by the assessment: 30 seconds -> 5 minutes -> 30 minutes.
RETRY_DELAYS_SECONDS = (30, 300, 1800)
MAX_RETRIES = len(RETRY_DELAYS_SECONDS)
