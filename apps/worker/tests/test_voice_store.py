import pytest

from dcs_worker.voice.models import VoiceError
from dcs_worker.voice.store import InMemoryAudioStore, LocalAudioStore


@pytest.mark.parametrize("make", [lambda p: LocalAudioStore(p), lambda p: InMemoryAudioStore()])
async def test_round_trip(tmp_path, make):
    store = make(tmp_path)
    assert not await store.exists("r/a.mp3")
    await store.put("r/a.mp3", b"abc")
    assert await store.exists("r/a.mp3")
    assert await store.get("r/a.mp3") == b"abc"
    await store.delete("r/a.mp3")
    assert not await store.exists("r/a.mp3")


async def test_local_store_writes_under_root(tmp_path):
    await LocalAudioStore(tmp_path).put("run/x.mp3", b"1")
    assert (tmp_path / "run" / "x.mp3").read_bytes() == b"1"


@pytest.mark.parametrize("key", ["../x.mp3", "/abs.mp3", "a/../../x", "C:\\x"])
async def test_local_store_rejects_escaping_keys(tmp_path, key):
    with pytest.raises(VoiceError) as exc:
        await LocalAudioStore(tmp_path).put(key, b"1")
    assert exc.value.code == "voice.invalid_key"
