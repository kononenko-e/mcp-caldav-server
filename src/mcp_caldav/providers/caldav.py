from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast
from uuid import uuid4

from icalendar import Alarm, Calendar, Event, vCalAddress, vCategory

from mcp_caldav.config.models import AccountConfig, CalendarConfig, ProviderConfig
from mcp_caldav.core.errors import (
    CalendarNotFoundError,
    EventNotFoundError,
    ProviderConnectionError,
)
from mcp_caldav.core.ids import stable_calendar_id
from mcp_caldav.providers.base import CalendarProvider
from mcp_caldav.providers.compat import CaldavBindings, load_caldav_bindings
from mcp_caldav.schemas.common import CalendarSummary, EventRecord
from mcp_caldav.schemas.tools import CreateEventInput, ReminderInput, UpdateEventInput
from mcp_caldav.utils.ical import first_component, serialize_recurrence
from mcp_caldav.utils.time import ensure_datetime, format_datetime


@dataclass(frozen=True)
class ResolvedCalendar:
    summary: CalendarSummary
    remote: Any


class CaldavProviderFactory:
    def __init__(self, provider_config: ProviderConfig) -> None:
        self._provider_config = provider_config
        self._bindings: CaldavBindings | None = None

    def __call__(self, account_id: str, account: AccountConfig) -> CaldavProvider:
        if self._bindings is None:
            self._bindings = load_caldav_bindings(
                http_backend=self._provider_config.http_backend,
                disable_http3=self._provider_config.disable_http3,
            )
        return CaldavProvider(account_id=account_id, account=account, bindings=self._bindings)


class CaldavProvider(CalendarProvider):
    def __init__(
        self,
        account_id: str,
        account: AccountConfig,
        bindings: CaldavBindings,
    ) -> None:
        self._account_id = account_id
        self._account = account
        self._bindings = bindings
        self._client: Any = None
        self._principal: Any = None
        self._calendar_cache: dict[str, ResolvedCalendar] | None = None

    def list_calendars(self) -> list[CalendarSummary]:
        return [resolved.summary for resolved in self._load_calendars().values()]

    def get_calendar(self, calendar_id: str) -> CalendarSummary:
        return self._resolve_calendar(calendar_id).summary

    def list_events(self, calendar_id: str, start: str, end: str) -> list[EventRecord]:
        remote_calendar = self._resolve_calendar(calendar_id)
        results = cast(
            list[Any],
            remote_calendar.remote.date_search(
                start=ensure_datetime(start),
                end=ensure_datetime(end),
                expand=True,
            ),
        )
        return [self._event_to_record(remote_calendar.summary, event) for event in results]

    def create_event(self, payload: CreateEventInput) -> EventRecord:
        remote_calendar = self._resolve_calendar(payload.calendar_id)
        cal = Calendar()
        event = Event()
        uid = payload.event_uid or str(uuid4())
        start = ensure_datetime(payload.start_time)
        end = (
            ensure_datetime(payload.end_time)
            if payload.end_time
            else payload.compute_end_datetime()
        )

        event.add("uid", uid)
        event.add("summary", payload.title)
        event.add("dtstart", start)
        event.add("dtend", end)
        event.add("dtstamp", payload.created_timestamp())

        if payload.description:
            event.add("description", payload.description)
        if payload.location:
            event.add("location", payload.location)
        if payload.categories:
            event.add("categories", [vCategory(category) for category in payload.categories])
        if payload.priority is not None:
            event.add("priority", payload.priority)
        if payload.attendees:
            for attendee in payload.attendees:
                address = vCalAddress(f"MAILTO:{attendee}")
                event.add("attendee", address, encode=False)
        if payload.recurrence:
            event.add("rrule", payload.recurrence)

        cal.add_component(event)

        for reminder in payload.reminders or []:
            cal_alarm = self._build_alarm(reminder)
            event.add_component(cal_alarm)

        remote_event = cast(Any, remote_calendar.remote.save_event(cal.to_ical()))
        return self._event_to_record(remote_calendar.summary, remote_event)

    def update_event(self, payload: UpdateEventInput) -> EventRecord:
        remote_calendar = self._resolve_calendar(payload.calendar_id)
        event = self._get_event(remote_calendar.remote, payload.event_uid)
        with event.edit_icalendar_instance() as calendar:
            component = first_component(calendar)
            if payload.title is not None:
                component["SUMMARY"] = payload.title
            if payload.start_time is not None:
                component["DTSTART"] = ensure_datetime(payload.start_time)
            if payload.end_time is not None:
                component["DTEND"] = ensure_datetime(payload.end_time)
            elif payload.duration_hours is not None and payload.start_time is not None:
                component["DTEND"] = payload.compute_end_datetime()
            if payload.description is not None:
                _replace_property(component, "DESCRIPTION", payload.description)
            if payload.location is not None:
                _replace_property(component, "LOCATION", payload.location)
            if payload.categories is not None:
                _replace_property(
                    component,
                    "CATEGORIES",
                    [vCategory(cat) for cat in payload.categories],
                )
            if payload.priority is not None:
                _replace_property(component, "PRIORITY", payload.priority)
            if payload.attendees is not None:
                if "ATTENDEE" in component:
                    del component["ATTENDEE"]
                for attendee in payload.attendees:
                    address = vCalAddress(f"MAILTO:{attendee}")
                    component.add("attendee", address, encode=False)
            if payload.recurrence is not None:
                _replace_property(component, "RRULE", payload.recurrence)
            if payload.reminders is not None:
                component.subcomponents = [
                    sub for sub in component.subcomponents if sub.name != "VALARM"
                ]
                for reminder in payload.reminders:
                    component.add_component(self._build_alarm(reminder))

        event.save()
        return self._event_to_record(remote_calendar.summary, event)

    def delete_event(self, calendar_id: str, event_uid: str) -> None:
        remote_calendar = self._resolve_calendar(calendar_id)
        # Build the direct URL to the event .ics file
        # iCloud CalDAV URL: <calendar_url>/<event_uid>.ics
        url = remote_calendar.summary.url.rstrip("/") + f"/{event_uid}.ics"
        client = self._client_instance()
        response = client.request(url, "DELETE")
        if response.status not in (200, 204, 404):
            raise ProviderConnectionError(
                f"failed to delete event '{event_uid}' from calendar '{calendar_id}': "
                f"{response.status} {response.reason}"
            )

    def search_events(
        self,
        calendar_id: str,
        query: str,
        start: str | None = None,
        end: str | None = None,
    ) -> list[EventRecord]:
        remote_calendar = self._resolve_calendar(calendar_id)
        search_start = ensure_datetime(start) if start else None
        search_end = ensure_datetime(end) if end else None

        if search_start is not None:
            results = cast(
                list[Any],
                remote_calendar.remote.date_search(
                    start=search_start,
                    end=search_end,
                    expand=True,
                ),
            )
        else:
            results = cast(list[Any], remote_calendar.remote.events())

        matched: list[EventRecord] = []
        lowered = query.casefold()
        for event in results:
            record = self._event_to_record(remote_calendar.summary, event)
            haystack = " ".join(
                [
                    record.summary or "",
                    record.description or "",
                    record.location or "",
                    " ".join(record.categories),
                ]
            ).casefold()
            if lowered in haystack:
                matched.append(record)
        return matched

    def _build_alarm(self, reminder: ReminderInput) -> Alarm:
        alarm = Alarm()
        alarm.add("action", "DISPLAY")
        alarm.add("description", reminder.description or "Reminder")
        alarm.add("trigger", reminder.to_trigger())
        return alarm

    def _resolve_calendar(self, calendar_id: str) -> ResolvedCalendar:
        calendars = self._load_calendars()
        try:
            return calendars[calendar_id]
        except KeyError as exc:
            raise CalendarNotFoundError(
                f"calendar_id '{calendar_id}' was not found in account '{self._account_id}'"
            ) from exc

    def _load_calendars(self) -> dict[str, ResolvedCalendar]:
        if self._calendar_cache is not None:
            return self._calendar_cache

        remote_calendars = cast(list[Any], self._principal_client().calendars())
        configured = self._account.calendars or []

        resolved: dict[str, ResolvedCalendar] = {}
        used_remote_urls: set[str] = set()

        for index, configured_calendar in enumerate(configured):
            remote = self._match_remote_calendar(configured_calendar, remote_calendars)
            if remote is None:
                continue
            used_remote_urls.add(str(remote.url))
            summary = CalendarSummary(
                account_id=self._account_id,
                calendar_id=configured_calendar.calendar_id,
                calendar_uid=(
                    configured_calendar.calendar_uid
                    or stable_calendar_id(remote.name, str(remote.url))
                ),
                name=remote.name or configured_calendar.name or configured_calendar.calendar_id,
                url=str(remote.url),
                is_default=configured_calendar.calendar_id == self._account.default_calendar_id,
                index=index,
            )
            resolved[summary.calendar_id] = ResolvedCalendar(summary=summary, remote=remote)

        if not configured or self._account.auto_discover_calendars:
            next_index = len(resolved)
            for remote in remote_calendars:
                remote_url = str(remote.url)
                if remote_url in used_remote_urls:
                    continue
                calendar_id = self._unique_calendar_id(
                    stable_calendar_id(remote.name, remote_url),
                    resolved,
                )
                summary = CalendarSummary(
                    account_id=self._account_id,
                    calendar_id=calendar_id,
                    calendar_uid=stable_calendar_id(remote.name, remote_url),
                    name=remote.name or calendar_id,
                    url=remote_url,
                    is_default=calendar_id == self._account.default_calendar_id,
                    index=next_index,
                )
                resolved[calendar_id] = ResolvedCalendar(summary=summary, remote=remote)
                next_index += 1

        self._calendar_cache = resolved
        return resolved

    def _match_remote_calendar(
        self,
        configured_calendar: CalendarConfig,
        remote_calendars: list[Any],
    ) -> Any | None:
        for remote in remote_calendars:
            remote_url = str(remote.url)
            if (
                configured_calendar.url
                and configured_calendar.url.rstrip("/") == remote_url.rstrip("/")
            ):
                return remote
            if configured_calendar.name and remote.name == configured_calendar.name:
                return remote
        return None

    def _unique_calendar_id(
        self,
        preferred: str,
        resolved: dict[str, ResolvedCalendar],
    ) -> str:
        if preferred not in resolved:
            return preferred
        suffix = 2
        while f"{preferred}-{suffix}" in resolved:
            suffix += 1
        return f"{preferred}-{suffix}"

    def _principal_client(self) -> Any:
        if self._principal is not None:
            return self._principal
        try:
            client = self._client_instance()
            self._principal = client.principal()
            return self._principal
        except Exception as exc:  # pragma: no cover - library-specific failure paths
            raise ProviderConnectionError(
                f"failed to connect account '{self._account_id}' to CalDAV server: {exc}"
            ) from exc

    def _client_instance(self) -> Any:
        if self._client is None:
            self._client = self._bindings.dav_client_class(
                url=self._account.url,
                username=self._account.username,
                password=self._account.password,
                timeout=self._account.connect_timeout_seconds,
            )
        return self._client

    def _get_event(self, calendar: Any, event_uid: str) -> Any:
        event = cast(Any, calendar).event_by_uid(event_uid)
        if event is None:
            raise EventNotFoundError(
                f"event_uid '{event_uid}' was not found in calendar '{calendar.name}'"
            )
        return cast(Any, event)

    def _event_to_record(self, calendar: CalendarSummary, event: Any) -> EventRecord:
        component = event.get_icalendar_component()
        start = component.get("DTSTART")
        end = component.get("DTEND")
        categories = component.get("CATEGORIES")
        attendees = component.get("ATTENDEE")

        category_values: list[str] = []
        if categories is not None:
            if isinstance(categories, list):
                category_values = [str(item) for item in categories]
            else:
                category_values = [str(item) for item in getattr(categories, "cats", [categories])]

        attendee_values: list[str] = []
        if attendees is not None:
            raw_attendees = attendees if isinstance(attendees, list) else [attendees]
            attendee_values = [str(item).removeprefix("MAILTO:") for item in raw_attendees]

        return EventRecord(
            account_id=self._account_id,
            calendar_id=calendar.calendar_id,
            calendar_name=calendar.name,
            calendar_url=calendar.url,
            event_uid=str(component.get("UID")),
            summary=str(component.get("SUMMARY", "")),
            dtstart=format_datetime(start.dt if start else None),
            dtend=format_datetime(end.dt if end else None),
            location=_optional_str(component.get("LOCATION")),
            description=_optional_str(component.get("DESCRIPTION")),
            categories=category_values,
            attendees=attendee_values,
            recurrence=serialize_recurrence(component.get("RRULE")),
            source_url=str(getattr(event, "url", "")),
            last_modified=format_datetime(getattr(component.get("LAST-MODIFIED"), "dt", None)),
        )


def _replace_property(component: Event, key: str, value: object | None) -> None:
    if key in component:
        del component[key]
    if value is not None:
        component.add(key.lower(), value)


def _optional_str(value: object | None) -> str | None:
    if value is None:
        return None
    return str(value)
