"""API middleware — error handling, CORS, request logging."""

from __future__ import annotations

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

import structlog

logger = structlog.get_logger("agentkit.api")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Add a unique request ID to every request."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:12])
        request.state.request_id = request_id

        start_time = time.time()
        response = await call_next(request)
        elapsed_ms = (time.time() - start_time) * 1000

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = str(round(elapsed_ms, 2))

        logger.info(
            "api_request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            latency_ms=round(elapsed_ms, 2),
        )

        return response


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global error handler for consistent error responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        from fastapi.responses import JSONResponse

        try:
            return await call_next(request)
        except Exception as e:
            logger.error(
                "api_unhandled_error",
                request_id=getattr(request.state, "request_id", "unknown"),
                path=request.url.path,
                error=str(e),
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "detail": str(e),
                    "status_code": 500,
                    "request_id": getattr(request.state, "request_id", "unknown"),
                },
            )


def add_middleware(app) -> None:
    """Add all middleware to the FastAPI app."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(ErrorHandlerMiddleware)
