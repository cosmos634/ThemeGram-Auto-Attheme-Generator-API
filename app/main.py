from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings, validate_startup_config
from app.routes import generate, health

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def create_app(validate_config: bool = True) -> FastAPI:
    if validate_config:
        validate_startup_config()
    application = FastAPI(
        title="ThemeGram Auto Attheme Generator API",
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.debug else None,
        debug=settings.debug,
    )
    application.include_router(health.router)
    application.include_router(generate.router)

    @application.api_route("/", methods=["GET", "HEAD"], include_in_schema=False, response_model=None)
    async def root(request: Request) -> dict[str, str] | Response:
        if request.method == "HEAD":
            return Response(status_code=200)
        return {"name": "ThemeGram Auto Attheme Generator API", "version": "1.0.0", "docs": "/docs" if settings.debug else "disabled"}

    @application.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, dict) else {"error": "http_error", "message": str(exc.detail)}
        return JSONResponse(status_code=exc.status_code, content=detail, headers=exc.headers)

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"error": "validation_error", "message": "Request validation failed."})

    @application.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logging.getLogger(__name__).exception("Unhandled API exception")
        return JSONResponse(status_code=500, content={"error": "internal_error", "message": "An internal server error occurred."})

    return application


app = create_app(validate_config=False)
