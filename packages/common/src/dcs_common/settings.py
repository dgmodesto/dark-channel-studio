from typing import Literal

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)

    database_url: str
    redis_url: str
    log_level: LogLevel = "INFO"


class ConfigError(Exception):
    """Startup configuration problem. Names variables only, never their values."""

    code = "config.missing"

    def __init__(self, missing: list[str], invalid: list[str]):
        self.missing = missing
        self.invalid = invalid
        if not missing:
            self.code = "config.invalid"
        parts = []
        if missing:
            parts.append("missing: " + ", ".join(missing))
        if invalid:
            parts.append("invalid: " + ", ".join(invalid))
        super().__init__("configuration error (" + "; ".join(parts) + ")")


def load_settings() -> Settings:
    try:
        return Settings()  # type: ignore[call-arg]
    except ValidationError as e:
        missing, invalid = [], []
        for err in e.errors():
            name = str(err["loc"][0]).upper() if err["loc"] else "UNKNOWN"
            (missing if err["type"] == "missing" else invalid).append(name)
        raise ConfigError(missing, invalid) from None
