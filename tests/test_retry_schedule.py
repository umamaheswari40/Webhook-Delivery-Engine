from datetime import datetime, timezone

from app.config import RETRY_DELAYS_SECONDS
from app.worker import calculate_next_retry


def test_retry_delays_are_exact():
    assert RETRY_DELAYS_SECONDS == (30, 300, 1800)


def test_retry_schedule():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    assert (calculate_next_retry(now, 1) - now).total_seconds() == 30
    assert (calculate_next_retry(now, 2) - now).total_seconds() == 300
    assert (calculate_next_retry(now, 3) - now).total_seconds() == 1800
