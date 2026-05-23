from __future__ import annotations

import hashlib
import re


def slugify_id(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    if normalized:
        return normalized
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]
    return f"id-{digest}"


def stable_calendar_id(name: str | None, url: str) -> str:
    if name:
        candidate = slugify_id(name)
        if candidate:
            return candidate

    stripped = url.rstrip("/")
    tail = stripped.rsplit("/", maxsplit=1)[-1]
    candidate = slugify_id(tail)
    if candidate:
        return candidate

    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    return f"calendar-{digest}"
