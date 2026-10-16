import asyncio
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Protocol

from dcs_worker.voice.models import VoiceError


class AudioStore(Protocol):
    async def exists(self, key: str) -> bool: ...

    async def put(self, key: str, data: bytes) -> None: ...

    async def get(self, key: str) -> bytes: ...

    async def delete(self, key: str) -> None: ...


class InMemoryAudioStore:
    def __init__(self) -> None:
        self._data: dict[str, bytes] = {}

    def keys(self) -> list[str]:
        return list(self._data)

    async def exists(self, key: str) -> bool:
        return key in self._data

    async def put(self, key: str, data: bytes) -> None:
        self._data[key] = data

    async def get(self, key: str) -> bytes:
        return self._data[key]

    async def delete(self, key: str) -> None:
        self._data.pop(key, None)


class LocalAudioStore:
    """Filesystem store; keys are relative POSIX paths confined to the root."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root).resolve()

    def _path(self, key: str) -> Path:
        posix, win = PurePosixPath(key), PureWindowsPath(key)
        if not key or "\\" in key or posix.is_absolute() or win.drive or ".." in posix.parts:
            raise VoiceError("voice.invalid_key")
        path = (self._root / posix).resolve()
        if not path.is_relative_to(self._root):
            raise VoiceError("voice.invalid_key")
        return path

    async def exists(self, key: str) -> bool:
        return await asyncio.to_thread(self._path(key).is_file)

    async def put(self, key: str, data: bytes) -> None:
        path = self._path(key)

        def write() -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_name(path.name + ".tmp")
            tmp.write_bytes(data)
            tmp.replace(path)  # atomic: a crash never leaves a partial clip counted as done

        await asyncio.to_thread(write)

    async def get(self, key: str) -> bytes:
        return await asyncio.to_thread(self._path(key).read_bytes)

    async def delete(self, key: str) -> None:
        await asyncio.to_thread(self._path(key).unlink, missing_ok=True)
