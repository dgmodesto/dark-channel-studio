from dcs_providers.adapters.elevenlabs_tts import ElevenLabsTTS
from dcs_providers.adapters.openai_chat import OpenAIChatModel
from dcs_providers.config import ProviderConfig
from dcs_providers.errors import ProviderConfigError
from dcs_providers.fakes import FakeChatModel, FakeTTS
from dcs_providers.protocols import TTS, ChatModel


def _resolve(cfg: ProviderConfig, role: str) -> tuple[str, str]:
    spec = cfg.roles.get(role)
    if spec is None:
        raise ProviderConfigError("provider.role_unmapped", f"role not mapped: {role}", role=role)
    provider, sep, model = spec.partition("/")
    if not sep or not provider or not model:
        raise ProviderConfigError(
            "provider.spec_invalid", f"invalid provider spec for role {role}", role=role
        )
    return provider, model


def _key(secret, var: str) -> str:
    if secret is None:
        raise ProviderConfigError("provider.key_missing", f"missing: {var}", variable=var)
    return secret.get_secret_value()


def build_chat(cfg: ProviderConfig, role: str) -> tuple[ChatModel, str, str]:
    """Return (adapter, provider, model) for the role."""
    provider, model = _resolve(cfg, role)
    if provider == "fake":
        return FakeChatModel(), provider, model
    if provider == "openai":
        return OpenAIChatModel(model, _key(cfg.openai_api_key, "OPENAI_API_KEY")), provider, model
    raise ProviderConfigError(
        "provider.unknown", f"unknown chat provider: {provider}", provider=provider
    )


def build_tts(cfg: ProviderConfig, role: str) -> tuple[TTS, str, str]:
    provider, model = _resolve(cfg, role)
    if provider == "fake":
        return FakeTTS(), provider, model
    if provider == "elevenlabs":
        key = _key(cfg.elevenlabs_api_key, "ELEVENLABS_API_KEY")
        return ElevenLabsTTS(model, key), provider, model
    raise ProviderConfigError(
        "provider.unknown", f"unknown TTS provider: {provider}", provider=provider
    )
