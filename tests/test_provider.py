from __future__ import annotations

from types import ModuleType

from mcp_caldav.config.models import AccountConfig, CalendarConfig
from mcp_caldav.providers.caldav import CaldavProvider
from mcp_caldav.providers.compat import CaldavBindings


class FakeRemoteCalendar:
    def __init__(self, name: str, url: str) -> None:
        self.name = name
        self.url = url


class FakePrincipal:
    def __init__(self, calendars: list[FakeRemoteCalendar]) -> None:
        self._calendars = calendars

    def calendars(self) -> list[FakeRemoteCalendar]:
        return self._calendars


class ProviderUnderTest(CaldavProvider):
    def __init__(self, account_id: str, account: AccountConfig, principal: FakePrincipal) -> None:
        bindings = CaldavBindings(
            davclient_module=ModuleType("davclient"),
            collection_module=ModuleType("collection"),
            calendarobjectresource_module=ModuleType("calendarobjectresource"),
        )
        super().__init__(account_id=account_id, account=account, bindings=bindings)
        self._fake_principal = principal

    def _principal_client(self):
        return self._fake_principal


def test_provider_uses_configured_calendar_id() -> None:
    provider = ProviderUnderTest(
        account_id="work",
        account=AccountConfig(
            url="https://caldav.example.com/",
            username="alice@example.com",
            password="secret",
            default_calendar_id="main",
            calendars=[CalendarConfig(calendar_id="main", name="Work")],
        ),
        principal=FakePrincipal([FakeRemoteCalendar(name="Work", url="https://caldav.example.com/work/")]),
    )

    calendars = provider.list_calendars()

    assert len(calendars) == 1
    assert calendars[0].calendar_id == "main"
    assert calendars[0].is_default is True


def test_provider_auto_discovers_unconfigured_calendars() -> None:
    provider = ProviderUnderTest(
        account_id="work",
        account=AccountConfig(
            url="https://caldav.example.com/",
            username="alice@example.com",
            password="secret",
        ),
        principal=FakePrincipal(
            [
                FakeRemoteCalendar(name="Work", url="https://caldav.example.com/work/"),
                FakeRemoteCalendar(name="Meetings", url="https://caldav.example.com/meetings/"),
            ]
        ),
    )

    calendars = provider.list_calendars()

    assert {calendar.calendar_id for calendar in calendars} == {"work", "meetings"}
