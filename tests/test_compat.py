from __future__ import annotations

from mcp_caldav.providers.compat import load_caldav_bindings


def test_requests_backend_is_used_by_default_compat_path() -> None:
    bindings = load_caldav_bindings(http_backend="requests", disable_http3=True)
    module = bindings.davclient_module

    assert getattr(module, "_USE_NIQUESTS", False) is False
    assert getattr(module, "_USE_REQUESTS", False) is True
    assert module.requests.__name__ == "requests"
