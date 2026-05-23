from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta


def ensure_datetime(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        normalized = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def format_datetime(value: datetime | date | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        dt = datetime.combine(value, time.min, tzinfo=UTC)
        return dt.isoformat()
    return ensure_datetime(value).isoformat()


def today_window(now: datetime | None = None) -> tuple[str, str]:
    current = now or datetime.now(tz=UTC)
    start = current.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start.isoformat(), end.isoformat()


def week_window(now: datetime | None = None) -> tuple[str, str]:
    current = now or datetime.now(tz=UTC)
    start = current.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=7)
    return start.isoformat(), end.isoformat()
