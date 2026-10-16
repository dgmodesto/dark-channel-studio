"""Static USD price table. Update when vendors change prices; unknown models are unpriced."""

from decimal import Decimal

_M = Decimal(1_000_000)

# (input USD per 1M tokens, output USD per 1M tokens)
CHAT_PRICES: dict[tuple[str, str], tuple[Decimal, Decimal]] = {
    ("openai", "gpt-4o-mini"): (Decimal("0.15"), Decimal("0.60")),
    ("openai", "gpt-4o"): (Decimal("2.50"), Decimal("10.00")),
}

# USD per 1K characters; "*" matches any voice
TTS_PRICES_PER_1K_CHARS: dict[tuple[str, str], Decimal] = {
    ("elevenlabs", "*"): Decimal("0.18"),
}


def chat_cost(
    provider: str, model: str, *, input_tokens: int, output_tokens: int
) -> tuple[Decimal, bool]:
    if provider == "fake":
        return Decimal(0), True
    prices = CHAT_PRICES.get((provider, model))
    if prices is None:
        return Decimal(0), False
    return (prices[0] * input_tokens + prices[1] * output_tokens) / _M, True


def tts_cost(provider: str, model: str, *, characters: int) -> tuple[Decimal, bool]:
    if provider == "fake":
        return Decimal(0), True
    price = TTS_PRICES_PER_1K_CHARS.get((provider, model)) or TTS_PRICES_PER_1K_CHARS.get(
        (provider, "*")
    )
    if price is None:
        return Decimal(0), False
    return price * characters / 1000, True
