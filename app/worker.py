import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from .config import MAX_RETRIES, RETRY_DELAYS_SECONDS, WORKER_POLL_INTERVAL_SECONDS
from .database import SessionLocal
from .models import Attempt, Event
from .webhook import deliver_event


def utcnow():
    return datetime.now(timezone.utc)


def calculate_next_retry(now: datetime, retry_number: int) -> datetime:
    """
    retry_number is 1, 2, or 3.
    1 -> +30 seconds
    2 -> +5 minutes
    3 -> +30 minutes
    """
    if not 1 <= retry_number <= MAX_RETRIES:
        raise ValueError("retry_number must be between 1 and 3")

    return now + timedelta(seconds=RETRY_DELAYS_SECONDS[retry_number - 1])


def get_due_event(session):
    now = utcnow()

    statement = (
        select(Event)
        .where(
            Event.status.in_(("pending", "failed")),
            Event.next_attempt_at <= now,
        )
        .order_by(Event.next_attempt_at.asc())
        .limit(1)
    )

    return session.execute(statement).scalars().first()


async def process_event(event_id: str):
    # Use one DB session to load the event, perform the HTTP request,
    # then persist the attempt and status transition.
    session = SessionLocal()
    try:
        event = session.get(Event, event_id)
        if not event:
            return

        if event.status not in ("pending", "failed"):
            return

        # Deliver outside the database transaction.
        success, http_status = await deliver_event(event)
        attempted_at = utcnow()

        attempt = Attempt(
            event_id=event.id,
            attempted_at=attempted_at,
            http_status=http_status,
            outcome="success" if success else "failed",
        )
        session.add(attempt)

        if success:
            event.status = "delivered"
            event.next_attempt_at = attempted_at

        else:
            # retry_count represents how many retries have already
            # been scheduled after the initial attempt.
            if event.retry_count < MAX_RETRIES:
                event.retry_count += 1
                event.status = "failed"
                event.next_attempt_at = calculate_next_retry(
                    attempted_at,
                    event.retry_count,
                )
            else:
                # Four total attempts: initial + 3 retries.
                event.status = "dead"
                event.next_attempt_at = attempted_at

        session.commit()

    except Exception:
        session.rollback()
        # Keep the worker alive if one event unexpectedly causes an exception.
        # The event will remain persisted and can be inspected/retried.
    finally:
        session.close()


async def worker_loop(stop_event: asyncio.Event):
    while not stop_event.is_set():
        session = SessionLocal()
        try:
            event = get_due_event(session)
            event_id = event.id if event else None
        finally:
            session.close()

        if event_id:
            await process_event(event_id)
            continue

        try:
            await asyncio.wait_for(
                stop_event.wait(),
                timeout=WORKER_POLL_INTERVAL_SECONDS,
            )
        except asyncio.TimeoutError:
            pass
