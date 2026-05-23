from __future__ import annotations

from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mcp_caldav.core.errors import ValidationError
from mcp_caldav.schemas.common import AccountSummary, CalendarSummary, EventRecord
from mcp_caldav.utils.time import ensure_datetime


class ListAccountsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accounts: list[AccountSummary]


class ListCalendarsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str


class GetCalendarInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str
    calendar_id: str


class GetCalendarResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str
    calendar: CalendarSummary


class ListCalendarsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str
    calendars: list[CalendarSummary]


class ListEventsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str
    calendar_id: str
    start: str
    end: str

    @model_validator(mode="after")
    def validate_range(self) -> ListEventsInput:
        if ensure_datetime(self.end) <= ensure_datetime(self.start):
            raise ValidationError("'end' must be later than 'start'")
        return self


class GetTodayEventsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str
    calendar_id: str


class GetWeekEventsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str
    calendar_id: str


class ReminderInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    minutes_before: int = Field(gt=0)
    description: str | None = None

    def to_trigger(self) -> timedelta:
        return timedelta(minutes=-self.minutes_before)


class CreateEventInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str
    calendar_id: str
    title: str
    start_time: str
    end_time: str | None = None
    duration_hours: float | None = Field(default=None, gt=0)
    description: str | None = None
    location: str | None = None
    categories: list[str] | None = None
    priority: int | None = Field(default=None, ge=0, le=9)
    reminders: list[ReminderInput] | None = None
    attendees: list[str] | None = None
    recurrence: dict[str, list[str]] | None = None
    event_uid: str | None = None

    @model_validator(mode="after")
    def validate_end_strategy(self) -> CreateEventInput:
        if self.end_time is None and self.duration_hours is None:
            raise ValidationError("either 'end_time' or 'duration_hours' must be provided")
        if self.end_time is not None and self.duration_hours is not None:
            raise ValidationError("provide only one of 'end_time' or 'duration_hours'")
        start = ensure_datetime(self.start_time)
        end = self.compute_end_datetime()
        if end <= start:
            raise ValidationError("event end must be later than start_time")
        return self

    def compute_end_datetime(self) -> datetime:
        start = ensure_datetime(self.start_time)
        if self.end_time:
            return ensure_datetime(self.end_time)
        if self.duration_hours is None:
            raise ValidationError("duration_hours is required when end_time is missing")
        return start + timedelta(hours=self.duration_hours)

    def created_timestamp(self) -> datetime:
        return datetime.now(tz=UTC)


class UpdateEventInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str
    calendar_id: str
    event_uid: str
    title: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    duration_hours: float | None = Field(default=None, gt=0)
    description: str | None = None
    location: str | None = None
    categories: list[str] | None = None
    priority: int | None = Field(default=None, ge=0, le=9)
    reminders: list[ReminderInput] | None = None
    attendees: list[str] | None = None
    recurrence: dict[str, list[str]] | None = None

    @model_validator(mode="after")
    def validate_update_shape(self) -> UpdateEventInput:
        changed_fields = [
            self.title,
            self.start_time,
            self.end_time,
            self.duration_hours,
            self.description,
            self.location,
            self.categories,
            self.priority,
            self.reminders,
            self.attendees,
            self.recurrence,
        ]
        if all(item is None for item in changed_fields):
            raise ValidationError("at least one mutable field must be provided for update")
        if self.duration_hours is not None and self.start_time is None and self.end_time is None:
            raise ValidationError("duration_hours update requires start_time or end_time context")
        if self.start_time and self.end_time:
            if ensure_datetime(self.end_time) <= ensure_datetime(self.start_time):
                raise ValidationError("event end must be later than start_time")
        return self

    def compute_end_datetime(self) -> datetime:
        if self.start_time is None or self.duration_hours is None:
            raise ValidationError("start_time and duration_hours are required to compute event end")
        return ensure_datetime(self.start_time) + timedelta(hours=self.duration_hours)


class DeleteEventInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str
    calendar_id: str
    event_uid: str


class SearchEventsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str
    calendar_id: str
    query: str
    start: str | None = None
    end: str | None = None

    @model_validator(mode="after")
    def validate_range(self) -> SearchEventsInput:
        if self.start and self.end and ensure_datetime(self.end) <= ensure_datetime(self.start):
            raise ValidationError("'end' must be later than 'start'")
        return self


class ListEventsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str
    calendar_id: str
    events: list[EventRecord]


class CreateEventResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str
    calendar_id: str
    event: EventRecord


class UpdateEventResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str
    calendar_id: str
    event_uid: str
    event: EventRecord


class DeleteEventResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str
    calendar_id: str
    event_uid: str
    deleted: bool


class SearchEventsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str
    calendar_id: str
    query: str
    events: list[EventRecord]
