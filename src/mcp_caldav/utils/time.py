from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, available_timezones


# Preferred timezone names for common fixed UTC offsets
_OFFSET_TO_ZONE: list[tuple[timedelta, str]] = [
    (timedelta(hours=12), "Asia/Kamchatka"),
    (timedelta(hours=11), "Asia/Magadan"),
    (timedelta(hours=10), "Asia/Vladivostok"),
    (timedelta(hours=9), "Asia/Yakutsk"),
    (timedelta(hours=8), "Asia/Irkutsk"),
    (timedelta(hours=7), "Asia/Krasnoyarsk"),
    (timedelta(hours=6), "Asia/Omsk"),
    (timedelta(hours=5), "Asia/Yekaterinburg"),
    (timedelta(hours=4), "Europe/Samara"),
    (timedelta(hours=3), "Europe/Moscow"),
    (timedelta(hours=2), "Europe/Kaliningrad"),
    (timedelta(hours=1), "Europe/Paris"),
    (timedelta(hours=0), "UTC"),
    (timedelta(hours=-1), "Atlantic/Azores"),
    (timedelta(hours=-2), "America/Noronha"),
    (timedelta(hours=-3), "America/Sao_Paulo"),
    (timedelta(hours=-4), "America/Halifax"),
    (timedelta(hours=-5), "America/New_York"),
    (timedelta(hours=-6), "America/Chicago"),
    (timedelta(hours=-7), "America/Denver"),
    (timedelta(hours=-8), "America/Los_Angeles"),
    (timedelta(hours=-9), "America/Anchorage"),
    (timedelta(hours=-10), "Pacific/Honolulu"),
    (timedelta(hours=-11), "Pacific/Pago_Pago"),
    (timedelta(hours=-12), "Pacific/Kwajalein"),
]


def _fixed_offset_to_zoneinfo(dt: timedelta) -> ZoneInfo | None:
    """Convert a fixed UTC offset to a named ZoneInfo, preferring well-known zones."""
    if isinstance(dt, timedelta):
        total = dt.total_seconds()
        for offset, name in _OFFSET_TO_ZONE:
            if abs(offset.total_seconds() - total) < 1800:  # within 30 min
                return ZoneInfo(name)
    return None


def ensure_datetime(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        normalized = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    # Convert fixed offsets (datetime.timezone) to named ZoneInfo
    if isinstance(dt.tzinfo, timezone) and dt.tzinfo != UTC:
        zone = _fixed_offset_to_zoneinfo(dt.utcoffset())
        if zone is not None:
            dt = dt.replace(tzinfo=zone)
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
