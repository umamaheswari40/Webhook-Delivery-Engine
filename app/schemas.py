from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class EventCreate(BaseModel):
    type: str = Field(min_length=1, max_length=255)
    payload: Dict[str, Any]
    webhook_url: HttpUrl


class AttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    attempted_at: datetime
    http_status: Optional[int] = None
    outcome: str


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str
    payload: Dict[str, Any]
    webhook_url: str
    status: str
    created_at: datetime
    attempts: List[AttemptResponse]


class RetryResponse(EventResponse):
    pass
