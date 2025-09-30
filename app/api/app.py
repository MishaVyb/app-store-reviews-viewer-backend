from __future__ import annotations

import asyncio
import logging
from typing import Type

import fastapi.datastructures
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.types import Lifespan

from app.api import routes
from app.config import AppSettings
from app.integration.itunes.adapter import ItunesRSSAdapter
from app.services.polling import DataPollingWorker
from app.services.queue import DataPollingQueue
from app.services.storage import StorageService

logger = logging.getLogger(__name__)


class Request(fastapi.Request):
    app: FastAPIApplication


class FastAPIApplication(FastAPI):
    class State(fastapi.datastructures.State):
        settings: AppSettings
        event_loop_tasks: list[asyncio.Task]

        # Services:
        storage: StorageService
        queue: DataPollingQueue
        workers: list[DataPollingWorker]
        external: ItunesRSSAdapter

    state: State

    @classmethod
    def startup(
        cls: Type[FastAPIApplication],
        settings: AppSettings,
        lifespan: Lifespan[FastAPIApplication],
    ) -> FastAPIApplication:
        app = cls(
            title=settings.APP_NAME,
            description=settings.APP_DESCRIPTION,
            version=settings.APP_VERSION,
            openapi_url=str(settings.API_OPENAPI_URL),
            docs_url=str(settings.API_DOCS_URL),
            generate_unique_id_function=lambda route: route.name,
            lifespan=lifespan,
            redirect_slashes=False,
        )
        app.state.settings = settings

        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.API_CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        app.include_router(routes.apps, prefix=settings.API_PREFIX)
        app.include_router(routes.reviews, prefix=settings.API_PREFIX)
        app.include_router(routes.monitoring, prefix=settings.API_PREFIX)

        return app
