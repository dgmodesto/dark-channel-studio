import httpx

from dcs_providers.errors import ProviderCallError
from dcs_providers.protocols import ChatMessage, ChatResult, Usage


class OpenAIChatModel:
    def __init__(
        self,
        model: str,
        api_key: str,
        *,
        base_url: str = "https://api.openai.com/v1",
        client: httpx.AsyncClient | None = None,
    ):
        self._model, self._api_key, self._base_url = model, api_key, base_url
        self._client = client or httpx.AsyncClient(timeout=60)

    def __repr__(self) -> str:
        return f"OpenAIChatModel(model={self._model!r})"

    async def complete(self, messages: list[ChatMessage]) -> ChatResult:
        try:
            response = await self._client.post(
                f"{self._base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "messages": [{"role": m.role, "content": m.content} for m in messages],
                },
            )
        except httpx.HTTPError as e:
            raise ProviderCallError(provider="openai", reason=type(e).__name__) from None
        if response.status_code >= 400:
            raise ProviderCallError(provider="openai", status=response.status_code)
        data = response.json()
        usage = data.get("usage", {})
        return ChatResult(
            text=data["choices"][0]["message"]["content"] or "",
            usage=Usage(
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
            ),
        )
