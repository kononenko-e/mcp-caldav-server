from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from icalendar import Calendar


def first_component(calendar: Calendar) -> Any:
    for component in calendar.subcomponents:
        if component.name == "VEVENT":
            return component
    msg = "VEVENT component was not found"
    raise ValueError(msg)


def serialize_recurrence(value: object | None) -> dict[str, list[str]] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return {
            str(key): [str(item) for item in _ensure_iterable(items)]
            for key, items in value.items()
        }
    return {"RRULE": [str(value)]}


def _ensure_iterable(value: object) -> Iterable[object]:
    if isinstance(value, (list, tuple, set)):
        return value
    return [value]
