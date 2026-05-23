from __future__ import annotations

from abc import ABC, abstractmethod

from mcp_caldav.schemas.common import CalendarSummary, EventRecord
from mcp_caldav.schemas.tools import CreateEventInput, UpdateEventInput


class CalendarProvider(ABC):
    @abstractmethod
    def list_calendars(self) -> list[CalendarSummary]:
        raise NotImplementedError

    @abstractmethod
    def get_calendar(self, calendar_id: str) -> CalendarSummary:
        raise NotImplementedError

    @abstractmethod
    def list_events(self, calendar_id: str, start: str, end: str) -> list[EventRecord]:
        raise NotImplementedError

    @abstractmethod
    def create_event(self, payload: CreateEventInput) -> EventRecord:
        raise NotImplementedError

    @abstractmethod
    def update_event(self, payload: UpdateEventInput) -> EventRecord:
        raise NotImplementedError

    @abstractmethod
    def delete_event(self, calendar_id: str, event_uid: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def search_events(
        self,
        calendar_id: str,
        query: str,
        start: str | None = None,
        end: str | None = None,
    ) -> list[EventRecord]:
        raise NotImplementedError
