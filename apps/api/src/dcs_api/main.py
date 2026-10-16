from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from dcs_api.errors import ApiError
from dcs_api.routes import channels, health, templates
from dcs_common.logging import configure_logging
from dcs_common.settings import load_settings

_HTTP_CODES = {404: "http.not_found", 405: "http.method_not_allowed", 422: "http.invalid_request"}


def create_app(probes=None, engine=None) -> FastAPI:
    """Build the app. Tests inject `probes` and `engine`; production wires real ones at startup."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if probes is not None:
            yield
            return

        from redis.asyncio import Redis
        from sqlalchemy.ext.asyncio import create_async_engine

        from dcs_api.db import LiveProbes

        settings = load_settings()
        configure_logging(settings.log_level)
        live_engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        redis = Redis.from_url(settings.redis_url)
        app.state.engine = live_engine
        app.state.probes = LiveProbes(live_engine, redis)
        structlog.get_logger().info("api.started")
        try:
            yield
        finally:
            await redis.aclose()
            await live_engine.dispose()

    app = FastAPI(title="Dark Channel Studio API", lifespan=lifespan)
    if probes is not None:
        app.state.probes = probes
    if engine is not None:
        app.state.engine = engine
    app.include_router(health.router)
    app.include_router(templates.router)
    app.include_router(channels.router)

    @app.exception_handler(ApiError)
    async def api_error(_: Request, exc: ApiError):
        return JSONResponse(
            status_code=exc.status_code, content={"code": exc.code, "params": exc.params}
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError):
        fields = sorted({str(e["loc"][-1]) for e in exc.errors() if e["loc"]})
        return JSONResponse(
            status_code=422, content={"code": "http.invalid_request", "params": {"fields": fields}}
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, exc: StarletteHTTPException):
        code = _HTTP_CODES.get(exc.status_code, f"http.{exc.status_code}")
        return JSONResponse(status_code=exc.status_code, content={"code": code, "params": {}})

    return app


def app_factory() -> FastAPI:
    return create_app()
