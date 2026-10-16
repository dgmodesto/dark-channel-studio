import pytest

from dcs_providers.adapters.elevenlabs_tts import ElevenLabsTTS
from dcs_providers.adapters.openai_chat import OpenAIChatModel
from dcs_providers.config import ProviderConfig
from dcs_providers.errors import ProviderConfigError
from dcs_providers.fakes import FakeChatModel, FakeTTS
from dcs_providers.registry import build_chat, build_tts

CFG = ProviderConfig(
    roles={
        "script_writer": "openai/gpt-4o-mini",
        "narrator": "elevenlabs/voice-1",
        "fake_chat": "fake/x",
        "fake_voice": "fake/x",
        "bad": "acme/thing",
        "malformed": "nodash",
    },
    openai_api_key="sk-test",
    elevenlabs_api_key="el-test",
)


def test_openai_chat_selected_by_role():
    model, provider, name = build_chat(CFG, "script_writer")
    assert isinstance(model, OpenAIChatModel) and (provider, name) == ("openai", "gpt-4o-mini")


def test_elevenlabs_selected_by_role():
    model, provider, name = build_tts(CFG, "narrator")
    assert isinstance(model, ElevenLabsTTS) and (provider, name) == ("elevenlabs", "voice-1")


def test_fakes_selected_by_role():
    assert isinstance(build_chat(CFG, "fake_chat")[0], FakeChatModel)
    assert isinstance(build_tts(CFG, "fake_voice")[0], FakeTTS)


@pytest.mark.parametrize("role", ["missing", "bad", "malformed"])
def test_unknown_role_or_provider_errors(role):
    with pytest.raises(ProviderConfigError) as exc:
        build_chat(CFG, role)
    assert exc.value.code.startswith("provider.")


def test_missing_key_names_variable_not_value():
    cfg = ProviderConfig(roles={"r": "openai/gpt-4o-mini"})
    with pytest.raises(ProviderConfigError) as exc:
        build_chat(cfg, "r")
    assert exc.value.code == "provider.key_missing"
    assert "OPENAI_API_KEY" in str(exc.value)


def test_secret_not_in_repr():
    assert "sk-test" not in repr(CFG)
