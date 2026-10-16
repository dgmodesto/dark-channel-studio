from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProviderConfig(BaseSettings):
    """Maps roles to `provider/model` (or `provider/voice_id`). Keys come from env only."""

    model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)

    roles: dict[str, str] = {}
    openai_api_key: SecretStr | None = None
    elevenlabs_api_key: SecretStr | None = None
    run_budget_usd: float = 5.0
