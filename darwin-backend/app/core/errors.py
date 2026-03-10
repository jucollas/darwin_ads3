from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("app")


def _validation_details(exc: RequestValidationError) -> list[dict[str, Any]]:
    out = []
    for e in exc.errors():
        out.append(
            {
                "loc": list(e.get("loc", [])),
                "msg": e.get("msg"),
                "type": e.get("type"),
            }
        )
    return out


def setup_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "type": "validation_error",
                    "message": "Invalid request payload",
                    "status_code": 422,
                    "details": _validation_details(exc),
                }
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": "http_error",
                    "message": exc.detail if isinstance(exc.detail, str) else "Request failed",
                    "status_code": exc.status_code,
                    "details": exc.detail if not isinstance(exc.detail, str) else None,
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "type": "internal_error",
                    "message": "Unexpected server error",
                    "status_code": 500,
                }
            },
        )