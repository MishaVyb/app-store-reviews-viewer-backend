from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Callable, Type

import fastapi.datastructures
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.types import Lifespan

from app.api import routes
from app.config import AppSettings

logger = logging.getLogger(__name__)


class AppStoreReviewsViewer(FastAPI):
    class State(fastapi.datastructures.State):
        settings: AppSettings

    state: State

    @classmethod
    def startup(
        cls: Type[AppStoreReviewsViewer],
        settings: AppSettings,
        lifespan: Lifespan[AppStoreReviewsViewer],
    ) -> AppStoreReviewsViewer:
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
            allow_origins=settings.APP_CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        app.include_router(routes.patients, prefix=settings.API_PREFIX)
        app.include_router(routes.observations, prefix=settings.API_PREFIX)
        app.include_router(routes.concepts, prefix=settings.API_PREFIX)
        app.include_router(routes.score, prefix=settings.API_PREFIX)
        app.include_router(routes.monitoring, prefix=settings.API_PREFIX)

        return app
