from decimal import Decimal

from dcs_providers.pricing import chat_cost, tts_cost


def test_chat_cost_from_tokens():
    cost, priced = chat_cost(
        "openai", "gpt-4o-mini", input_tokens=1_000_000, output_tokens=1_000_000
    )
    assert priced
    assert cost == Decimal("0.75")


def test_tts_cost_from_characters():
    cost, priced = tts_cost("elevenlabs", "voice-x", characters=1000)
    assert priced
    assert cost == Decimal("0.18")


def test_unknown_model_is_unpriced_zero():
    assert chat_cost("openai", "nope", input_tokens=10, output_tokens=10) == (Decimal(0), False)


def test_fake_provider_is_free_but_priced():
    assert chat_cost("fake", "x", input_tokens=10, output_tokens=10) == (Decimal(0), True)
    assert tts_cost("fake", "x", characters=10) == (Decimal(0), True)
