"""FastAPI service wrapper for network apps."""

from __future__ import annotations

import os
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, StrictStr

from aware_comms.duplex.collection import DuplexCollection
from aware_comms.http import endpoint as http_endpoint
from aware_comms.http.client import HTTPClient
from aware_comms.http.endpoint import HttpRouteKey
from aware_comms.http.registry import http_registry
from aware_comms.http.server import HttpServer

logger = logging.getLogger(__name__)


async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    if isinstance(exc, RequestValidationError):
        error_details = exc.errors()
    else:
        error_details = [str(exc)]
    logger.error("Validation error at %s: %s", request.url, error_details)
    return JSONResponse(
        status_code=422,
        content=http_endpoint.HttpErrorMessage(
            type=http_endpoint.HttpErrorType.VALIDATION_ERROR,
            message=str(error_details),
        ).model_dump(),
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, HTTPException):
        status_code = exc.status_code
        detail = exc.detail
    else:
        status_code = 500
        detail = str(exc)
    logger.error("HTTP error %s at %s: %s", status_code, request.url, detail)
    return JSONResponse(
        status_code=status_code,
        content=http_endpoint.HttpErrorMessage(
            type=http_endpoint.HttpErrorType.HTTP_ERROR, message=str(detail)
        ).model_dump(),
    )


class App(BaseModel):
    """A service app packaged as a FastAPI server instance."""

    app_type: StrictStr
    title: str
    description: str
    http_server: HttpServer
    duplex_collection: DuplexCollection

    @asynccontextmanager
    async def lifespan(self, _app: FastAPI):
        logger.info("Starting %s...", self.title)
        yield
        logger.info("Shutting down %s...", self.title)

    def create_app(self) -> FastAPI:
        logger.info("Creating %s...", self.title)
        app = FastAPI(
            title=self.title, description=self.description, lifespan=self.lifespan
        )

        app.add_exception_handler(HTTPException, http_exception_handler)
        app.add_exception_handler(RequestValidationError, validation_exception_handler)

        async def health_check() -> dict[str, str]:
            return {"status": "healthy"}

        app.add_api_route("/health", health_check, methods=["GET"])

        logger.info("Registering %s HTTP Server...", self.app_type)
        http_routers = self.register_http_server()
        for router in http_routers:
            app.include_router(router)

        if not os.environ.get("AWARE_SKIP_DUPLEX"):
            logger.info("Registering %s Duplex Server...", self.app_type)
            ws_routers = self.register_duplex_collection()
            for router in ws_routers:
                app.include_router(router)

        async def root() -> dict[str, str]:
            return {
                "message": f"Welcome to {self.title}. App description: {self.description}"
            }

        app.add_api_route("/", root, methods=["GET"])

        return app

    def get_http_client(self, route_type: HttpRouteKey) -> HTTPClient:
        return HTTPClient(app_type=self.app_type, route_type=route_type)

    def get_duplex_client(self, server_app_type: str):
        client = self.duplex_collection.get_client(server_app_type)
        if client:
            return client
        raise ValueError(
            f"App type {self.app_type} does not support WebSocket client connections to {server_app_type}"
        )

    def get_duplex_server(self, client_app_type: str):
        server = self.duplex_collection.get_server(client_app_type)
        if server:
            return server
        raise ValueError(
            f"App type {self.app_type} does not support WebSocket server connections from {client_app_type}"
        )

    def register_duplex_collection(self) -> list[APIRouter]:
        return self.duplex_collection.register(self.app_type)

    def register_http_server(self) -> list[APIRouter]:
        http_registry.register_server(self.http_server)
        return self.http_server.register()

    async def run_dev(
        self, port: int, host: str, ssl_keyfile: str | None, ssl_certfile: str | None
    ):
        app = self.create_app()
        config = uvicorn.Config(
            app=app,
            host=host,
            port=port,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile,
        )
        await self.run_uvicorn(config)

    async def run_prod(self, host: str, port: int):
        app = self.create_app()
        config = uvicorn.Config(
            app=app,
            host=host,
            port=port,
        )
        await self.run_uvicorn(config)

    async def run_uvicorn(self, config: uvicorn.Config):
        server = uvicorn.Server(config)
        await server.serve()


__all__ = ["App"]
