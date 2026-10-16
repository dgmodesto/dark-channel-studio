import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool

from dcs_api.channels import metadata
from dcs_api.main import create_app


@pytest.fixture
async def client():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    app = create_app(probes=object(), engine=engine)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    await engine.dispose()


async def _create(client, name="English with Ana", **extra):
    return await client.post(
        "/channels", json={"name": name, "template_id": "english-a1-a2-br", **extra}
    )


async def test_templates_listed(client):
    r = await client.get("/templates")
    assert r.status_code == 200
    assert any(t["id"] == "english-a1-a2-br" for t in r.json())


async def test_create_pins_latest_version_and_language(client):
    r = await _create(client)
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "English with Ana"
    assert (body["template_id"], body["template_version"], body["content_language"]) == (
        "english-a1-a2-br",
        1,
        "en",
    )
    assert (await client.get(f"/channels/{body['id']}")).json() == body


async def test_unknown_template_is_422_with_code(client):
    r = await client.post("/channels", json={"name": "x", "template_id": "nope"})
    assert r.status_code == 422
    assert r.json() == {"code": "channel.template_unknown", "params": {"template_id": "nope"}}


async def test_unknown_template_version_is_422(client):
    r = await _create(client, template_version=99)
    assert r.status_code == 422 and r.json()["code"] == "channel.template_unknown"


async def test_blank_name_is_invalid(client):
    r = await _create(client, name="")
    assert r.status_code == 422 and r.json()["code"] == "http.invalid_request"


async def test_list_newest_first(client):
    await _create(client, "first")
    await _create(client, "second")
    names = [c["name"] for c in (await client.get("/channels")).json()]
    assert names == ["second", "first"]


async def test_update_name(client):
    cid = (await _create(client)).json()["id"]
    r = await client.patch(f"/channels/{cid}", json={"name": "Renamed"})
    assert r.status_code == 200 and r.json()["name"] == "Renamed"
    assert r.json()["updated_at"] >= r.json()["created_at"]


async def test_update_unknown_template_rejected(client):
    cid = (await _create(client)).json()["id"]
    r = await client.patch(f"/channels/{cid}", json={"template_id": "nope"})
    assert r.status_code == 422 and r.json()["code"] == "channel.template_unknown"


async def test_delete_then_gone(client):
    cid = (await _create(client)).json()["id"]
    assert (await client.delete(f"/channels/{cid}")).status_code == 204
    assert (await client.get("/channels")).json() == []
    r = await client.get(f"/channels/{cid}")
    assert r.status_code == 404 and r.json() == {"code": "channel.not_found", "params": {}}


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
async def test_unknown_channel_is_404(client, method):
    missing = "00000000-0000-0000-0000-000000000000"
    kwargs = {"json": {"name": "x"}} if method == "patch" else {}
    r = await getattr(client, method)(f"/channels/{missing}", **kwargs)
    assert r.status_code == 404 and r.json()["code"] == "channel.not_found"
