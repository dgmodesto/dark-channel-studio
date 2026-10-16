import httpx

from dcs_providers.errors import ProviderCallError
from dcs_providers.protocols import TTSResult, Usage


class ElevenLabsTTS:
    def __init__(
        self,
        voice_id: str,
        api_key: str,
        *,
        base_url: str = "https://api.elevenlabs.io/v1",
        client: httpx.AsyncClient | None = None,
    ):
        self._voice_id, self._api_key, self._base_url = voice_id, api_key, base_url
        self._client = client or httpx.AsyncClient(timeout=120)

    def __repr__(self) -> str:
        return f"ElevenLabsTTS(voice_id={self._voice_id!r})"

    async def synthesize(self, text: str, *, voice: str | None = None) -> TTSResult:
        try:
            response = await self._client.post(
                f"{self._base_url}/text-to-speech/{voice or self._voice_id}",
                headers={"xi-api-key": self._api_key, "Accept": "audio/mpeg"},
                json={"text": text},
            )
        except httpx.HTTPError as e:
            raise ProviderCallError(provider="elevenlabs", reason=type(e).__name__) from None
        if response.status_code >= 400:
            raise ProviderCallError(provider="elevenlabs", status=response.status_code)
        return TTSResult(audio=response.content, usage=Usage(characters=len(text)))
