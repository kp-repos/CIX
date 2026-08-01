from typing import Literal
from pydantic import BaseModel, Field

class Segment(BaseModel):
    speaker: str | None = None
    ts: str | None = None
    text: str

class InteractionUnit(BaseModel):
    id: str
    source_type: Literal["transcript", "email", "note"]
    participants: list[str] = Field(default_factory=list)
    date: str | None = None
    account_id: str | None = None
    thread_id: str | None = None
    segments: list[Segment] = Field(min_length=1)
