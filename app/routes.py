from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from .database import get_db
from .models import Event, utcnow
from .schemas import EventCreate, EventResponse

router = APIRouter()


@router.post(
    "/events",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_event(request: EventCreate, db: Session = Depends(get_db)):
    event = Event(
        type=request.type,
        payload=request.payload,
        webhook_url=str(request.webhook_url),
        status="pending",
        created_at=utcnow(),
        next_attempt_at=utcnow(),
        retry_count=0,
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event


@router.get("/events", response_model=list[EventResponse])
def list_events(db: Session = Depends(get_db)):
    events = db.execute(
        select(Event).order_by(Event.created_at.desc())
    ).scalars().all()

    return events


@router.get("/events/{event_id}", response_model=EventResponse)
def get_event(event_id: str, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    return event


@router.post("/events/{event_id}/retry", response_model=EventResponse)
def retry_dead_event(event_id: str, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    if event.status != "dead":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only dead events can be manually retried",
        )

    event.status = "pending"
    event.retry_count = 0
    event.next_attempt_at = utcnow()

    db.commit()
    db.refresh(event)

    return event
