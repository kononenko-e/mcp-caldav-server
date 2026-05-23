from __future__ import annotations

import importlib
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from types import ModuleType
from typing import Any, cast


@dataclass(frozen=True)
class CaldavBindings:
    davclient_module: ModuleType
    collection_module: ModuleType
    calendarobjectresource_module: ModuleType

    @property
    def dav_client_class(self) -> Any:
        return self.davclient_module.DAVClient


def load_caldav_bindings(http_backend: str, disable_http3: bool) -> CaldavBindings:
    if http_backend == "requests":
        return _load_requests_backend()
    return _load_niquests_backend(disable_http3=disable_http3)


def _load_requests_backend() -> CaldavBindings:
    with _blocked_import("niquests"):
        davclient_module = importlib.import_module("caldav.davclient")
        collection_module = importlib.import_module("caldav.collection")
        calendarobjectresource_module = importlib.import_module("caldav.calendarobjectresource")
    return CaldavBindings(
        davclient_module=davclient_module,
        collection_module=collection_module,
        calendarobjectresource_module=calendarobjectresource_module,
    )


def _load_niquests_backend(disable_http3: bool) -> CaldavBindings:
    davclient_module = importlib.import_module("caldav.davclient")
    collection_module = importlib.import_module("caldav.collection")
    calendarobjectresource_module = importlib.import_module("caldav.calendarobjectresource")

    if disable_http3 and getattr(davclient_module, "_USE_NIQUESTS", False):
        session_factory = davclient_module.requests.Session
        if not getattr(session_factory, "_mcp_caldav_http3_wrapped", False):

            def wrapped_session(*args: object, **kwargs: object) -> Any:
                kwargs.setdefault("disable_http3", True)
                return session_factory(*args, **kwargs)

            wrapped_session._mcp_caldav_http3_wrapped = True  # type: ignore[attr-defined]
            davclient_module.requests.Session = wrapped_session

    return CaldavBindings(
        davclient_module=davclient_module,
        collection_module=collection_module,
        calendarobjectresource_module=calendarobjectresource_module,
    )


@contextmanager
def _blocked_import(module_name: str) -> Iterator[None]:
    sentinel = object()
    previous = sys.modules.get(module_name, sentinel)
    sys.modules[module_name] = cast(ModuleType, None)
    try:
        yield
    finally:
        if previous is sentinel:
            sys.modules.pop(module_name, None)
        else:
            sys.modules[module_name] = cast(ModuleType, previous)
