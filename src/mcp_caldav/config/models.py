from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CalendarConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    calendar_id: str
    name: str | None = None
    url: str | None = None
    calendar_uid: str | None = None


class AccountConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str
    username: str
    password: str | None = None
    password_env: str | None = None
    default_calendar_id: str | None = None
    calendars: list[CalendarConfig] | None = None
    auto_discover_calendars: bool = True
    connect_timeout_seconds: int = 30

    @model_validator(mode="after")
    def validate_password_source(self) -> AccountConfig:
        if bool(self.password) == bool(self.password_env):
            msg = "exactly one of 'password' or 'password_env' must be set"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def validate_default_calendar(self) -> AccountConfig:
        if self.default_calendar_id and self.calendars:
            calendar_ids = {calendar.calendar_id for calendar in self.calendars}
            if self.default_calendar_id not in calendar_ids:
                msg = "default_calendar_id must reference one of configured calendars"
                raise ValueError(msg)
        return self


class HttpConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    host: str = "127.0.0.1"
    port: int = 8000
    mount_path: str = "/"
    streamable_http_path: str = "/mcp"
    stateless_http: bool = False
    public_base_url: str | None = None


class AccessProfileConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_id: str
    token: str | None = None
    token_env: str | None = None
    description: str | None = None
    allowed_accounts: list[str] | None = None
    allowed_calendars: dict[str, list[str]] | None = None

    @model_validator(mode="after")
    def validate_token_source(self) -> AccessProfileConfig:
        if bool(self.token) == bool(self.token_env):
            msg = "exactly one of 'token' or 'token_env' must be set"
            raise ValueError(msg)
        return self


class AccessConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tokens: dict[str, AccessProfileConfig] = Field(default_factory=dict)


class ServerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accounts: dict[str, AccountConfig] = Field(min_length=1)
    http: HttpConfig = Field(default_factory=HttpConfig)
    access: AccessConfig | None = None
