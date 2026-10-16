import asyncio
import dataclasses
import hashlib
import tempfile
from pathlib import Path
from typing import Protocol

from dcs_worker.render.models import RenderError, RenderRequest, RenderResult
from dcs_worker.render.plan import build_plan, validate_request
from dcs_worker.voice.models import VoiceError
from dcs_worker.voice.store import AudioStore


class MediaTools(Protocol):
    async def probe_duration(self, path: Path) -> float: ...

    async def run(self, args: list[str], cwd: Path) -> None: ...


class FfmpegTools:
    def __init__(self, timeout_seconds: float = 1800.0) -> None:
        self._timeout = timeout_seconds

    async def _exec(
        self, args: list[str], cwd: Path | None, capture_out: bool
    ) -> tuple[int, bytes, bytes]:
        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE if capture_out else asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError as e:
            raise RenderError("render.ffmpeg_missing", binary=args[0]) from e
        try:
            out, err = await asyncio.wait_for(proc.communicate(), self._timeout)
        except BaseException as e:
            proc.kill()
            await proc.wait()
            if isinstance(e, TimeoutError):
                raise RenderError("render.ffmpeg_timeout") from e
            raise
        return proc.returncode or 0, out or b"", err or b""

    async def probe_duration(self, path: Path) -> float:
        args = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0"]
        code, out, _ = await self._exec([*args, str(path)], None, True)
        try:
            if code != 0:
                raise ValueError
            return round(float(out.decode().strip()), 3)
        except ValueError as e:
            raise RenderError("render.probe_failed", file=path.name) from e

    async def run(self, args: list[str], cwd: Path) -> None:
        code, _, err = await self._exec(args, cwd, False)
        if code != 0:
            raise RenderError("render.ffmpeg_failed", detail=err.decode(errors="replace")[-500:])


async def _read(store: AudioStore, key: str) -> bytes:
    try:
        return await store.get(key)
    except (KeyError, FileNotFoundError, VoiceError) as e:
        raise RenderError("render.input_missing", key=key) from e


async def render_video(
    request: RenderRequest, store: AudioStore, tools: MediaTools
) -> RenderResult:
    """Render the video, or return the stored one when the same inputs were rendered before."""
    validate_request(request)
    with tempfile.TemporaryDirectory(prefix="dcs-render-") as tmp:
        work = Path(tmp)
        clips = []
        for i, clip in enumerate(request.clips):
            data = await _read(store, clip.audio_key)
            path = work / f"probe{i:03d}{Path(clip.audio_key).suffix}"
            path.write_bytes(data)
            duration = await tools.probe_duration(path)
            clips.append(
                dataclasses.replace(
                    clip, audio_sha256=hashlib.sha256(data).hexdigest(), duration_seconds=duration
                )
            )
        request = dataclasses.replace(request, clips=clips)
        if request.music:
            data = await _read(store, request.music.key)
            request = dataclasses.replace(
                request,
                music=dataclasses.replace(request.music, sha256=hashlib.sha256(data).hexdigest()),
            )
        if request.background.kind == "image":
            data = await _read(store, request.background.value)
            request = dataclasses.replace(
                request,
                background=dataclasses.replace(
                    request.background, sha256=hashlib.sha256(data).hexdigest()
                ),
            )
        plan = build_plan(request)
        if await store.exists(plan.output_key):
            return RenderResult(
                request.run_id, plan.output_key, plan.input_hash, plan.duration_seconds, True
            )
        for name, key in plan.inputs:
            (work / name).write_bytes(await _read(store, key))
        (work / "subs.ass").write_text(plan.ass, encoding="utf-8")
        await tools.run(plan.args, work)
        output = work / plan.args[-1]
        if not output.is_file():
            raise RenderError("render.ffmpeg_failed")
        await store.put(plan.output_key, output.read_bytes())
    return RenderResult(
        request.run_id, plan.output_key, plan.input_hash, plan.duration_seconds, False
    )
