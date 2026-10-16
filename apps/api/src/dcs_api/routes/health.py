import asyncio

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

REQUIRED = ("database", "redis")


@router.get("/health")
async def health(request: Request) -> JSONResponse:
    probes = request.app.state.probes
    db, redis, worker = await asyncio.gather(probes.database(), probes.redis_(), probes.worker_())
    components = {
        "api": {"status": "healthy"},
        "database": db.public(),
        "redis": redis.public(),
        "worker": worker.public(),
    }
    healthy = all(components[name]["status"] == "healthy" for name in REQUIRED)
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={"status": "healthy" if healthy else "unhealthy", "components": components},
    )
