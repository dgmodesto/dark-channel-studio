import shutil
import subprocess

import pytest

from dcs_worker.jobs.render import render_video_job
from dcs_worker.render.render import FfmpegTools
from dcs_worker.voice.store import LocalAudioStore

pytestmark = pytest.mark.skipif(
    not (shutil.which("ffmpeg") and shutil.which("ffprobe")), reason="ffmpeg not installed"
)


def sine_wav(path, freq, seconds):
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
         f"sine=frequency={freq}:duration={seconds}", "-ar", "44100", str(path)],
        check=True,
    )  # fmt: skip


async def test_real_render_is_byte_identical(tmp_path):
    store_dir = tmp_path / "store"
    (store_dir / "run-e").mkdir(parents=True)
    (store_dir / "music").mkdir()
    sine_wav(store_dir / "run-e" / "000-a.mp3", 440, 1)
    sine_wav(store_dir / "run-e" / "001-b.mp3", 550, 1)
    sine_wav(store_dir / "music" / "loop.mp3", 220, 2)
    store = LocalAudioStore(store_dir)
    manifest = {
        "run_id": "run-e",
        "entries": [
            {"index": 0, "section": "hook", "text": "Hello!", "audio_key": "run-e/000-a.mp3",
             "pause_after_seconds": 0.0, "cached": False},
            {"index": 1, "section": "dialogue", "text": "How are you?",
             "audio_key": "run-e/001-b.mp3", "pause_after_seconds": 1.0, "cached": False},
        ],
    }  # fmt: skip
    payload = {
        "run_id": "run-e",
        "template_id": "english-a1-a2-br",
        "manifest": manifest,
        "translations": ["Ola!", "Como vai?"],
        "background": {"kind": "color", "value": "101418"},
        "music": {"key": "music/loop.mp3"},
        "width": 320,
        "height": 180,
        "fps": 10,
    }
    ctx = {"audio_store": store, "media_tools": FfmpegTools()}
    first = await render_video_job(ctx, payload)
    first_bytes = await store.get(first["video_key"])
    assert len(first_bytes) > 1000

    await store.delete(first["video_key"])
    second = await render_video_job(ctx, payload)
    assert second["cached"] is False
    assert await store.get(second["video_key"]) == first_bytes
