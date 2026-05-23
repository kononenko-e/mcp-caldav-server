from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AccountSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str
    url: str
    username: str
    default_calendar_id: str | None = None
    configured_calendar_count: int
    auto_discover_calendars: bool


class CalendarSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str
    calendar_id: str
    calendar_uid: str
    name: str
    url: str
    is_default: bool = False
    index: int = Field(ge=0)


class EventRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str
    calendar_id: str
    calendar_name: str
    calendar_url: str
    event_uid: str
    summary: str
    dtstart: str | None = None
    dtend: str | None = None
    location: str | None = None
    description: str | None = None
    categories: list[str] = Field(default_factory=list)
    attendees: list[str] = Field(default_factory=list)
    recurrence: dict[str, list[str]] | None = None
    source_url: str | None = None
    last_modified: str | None = None
