from __future__ import annotations

import threading

from mcp_caldav.config.models import AccountConfig, ServerConfig
from mcp_caldav.core.registry import AccountRegistry
from mcp_caldav.core.session import SessionManager
from mcp_caldav.providers.base import CalendarProvider


class DummyProvider(CalendarProvider):
    def __init__(self, account_id: str) -> None:
        self.account_id = account_id

    def list_calendars(self):
        return []

    def get_calendar(self, calendar_id: str):
        raise NotImplementedError

    def list_events(self, calendar_id: str, start: str, end: str):
        return []

    def create_event(self, payload):
        raise NotImplementedError

    def update_event(self, payload):
        raise NotImplementedError

    def delete_event(self, calendar_id: str, event_uid: str) -> None:
        raise NotImplementedError

    def search_events(
        self,
        calendar_id: str,
        query: str,
        start: str | None = None,
        end: str | None = None,
    ):
        return []


def build_sessions(counter: dict[str, int]) -> SessionManager:
    registry = AccountRegistry(
        ServerConfig(
            accounts={
                "work": AccountConfig(
                    url="https://caldav.example.com/",
                    username="alice@example.com",
                    password="secret",
                )
            }
        )
    )

    def factory(account_id: str, account: AccountConfig) -> CalendarProvider:
        del account
        counter["created"] += 1
        return DummyProvider(account_id)

    return SessionManager(registry=registry, factory=factory)


def test_session_manager_creates_provider_lazily() -> None:
    counter = {"created": 0}
    sessions = build_sessions(counter)

    assert counter["created"] == 0

    provider = sessions.get_provider("work")

    assert counter["created"] == 1
    assert isinstance(provider, DummyProvider)


def test_session_manager_caches_provider() -> None:
    counter = {"created": 0}
    sessions = build_sessions(counter)

    first = sessions.get_provider("work")
    second = sessions.get_provider("work")

    assert first is second
    assert counter["created"] == 1


def test_session_manager_thread_safe_get_provider() -> None:
    counter = {"created": 0}
    sessions = build_sessions(counter)
    results: list[CalendarProvider] = []
    lock = threading.Lock()

    def worker() -> None:
        p = sessions.get_provider("work")
        with lock:
            results.append(p)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert counter["created"] == 1
    assert all(p is results[0] for p in results)
