import pytest

from dcs_common.retry import retry_async


async def test_succeeds_after_transient_failures():
    calls = {"n": 0}

    async def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionError("not ready")
        return "ok"

    assert await retry_async(flaky, attempts=5, base_delay=0) == "ok"
    assert calls["n"] == 3


async def test_gives_up_after_limit():
    calls = {"n": 0}

    async def always_fail():
        calls["n"] += 1
        raise ConnectionError("down")

    with pytest.raises(ConnectionError):
        await retry_async(always_fail, attempts=3, base_delay=0)
    assert calls["n"] == 3
