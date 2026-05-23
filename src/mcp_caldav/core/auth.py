from __future__ import annotations

from mcp.server.auth.provider import AccessToken

from mcp_caldav.config.models import AccessConfig, AccessProfileConfig


class StaticTokenVerifier:
    def __init__(self, access: AccessConfig) -> None:
        self._tokens: dict[str, AccessProfileConfig] = {}
        for profile in access.tokens.values():
            if profile.token is None:
                continue
            self._tokens[profile.token] = profile

    async def verify_token(self, token: str) -> AccessToken | None:
        profile = self._tokens.get(token)
        if profile is None:
            return None
        return AccessToken(
            token=token,
            client_id=profile.client_id,
            scopes=["caldav"],
        )
