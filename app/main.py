import asyncio
import logging
import logging.config
import os
from contextlib import asynccontextmanager

import click
import httpx
import uvicorn

from app.api.app import FastAPIApplication
from app.config import AppSettings
from app.integration.itunes.adapter import ItunesRSSAdapter
from app.services import schemas
from app.services.polling import DataPollingWorker
from app.services.queue import DataPollingQueue
from app.services.scheduller import SchedulerService
from app.services.storage import StorageService

logger = logging.getLogger("app.main")


def setup_logging(settings: AppSettings) -> None:
    if settings.LOG_DIR_CREATE and not settings.LOG_DIR.exists():
        settings.LOG_DIR.mkdir()
    logging.config.dictConfig(settings.LOGGING)


def setup(settings: AppSettings | None = None) -> FastAPIApplication:
    settings = settings or AppSettings()
    setup_logging(settings)
    logger.info("Run app worker [%s]", click.style(os.getpid(), fg="cyan"))
    return FastAPIApplication.startup(settings, lifespan)


@asynccontextmanager
async def lifespan(app: FastAPIApplication):

    app.state.event_loop_tasks = []
    app.state.workers = []
    app.state.queue = DataPollingQueue()

    try:
        app.state.storage = await setup_storage(app)

        async with httpx.AsyncClient(
            base_url=app.state.settings.HTTP_EXTERNAL_RSS_HOST,
            timeout=app.state.settings.HTTP_EXTERNAL_RSS_TIMEOUT,
        ) as client:
            app.state.external = ItunesRSSAdapter(client)
            setup_workers(app)
            if app.state.settings.SCHEDULER_ENABLED:
                setup_scheduler(app)

            yield
    finally:
        for task in app.state.event_loop_tasks:
            task.cancel()


async def setup_storage(app: FastAPIApplication) -> StorageService:
    storage = StorageService(app.state.settings.STORAGE_PATH)
    await storage.load()
    for app_id in app.state.settings.STORAGE_INITIAL_APP_IDS:
        await storage.create_app(schemas.App(id=app_id))
    return storage


def setup_scheduler(app: FastAPIApplication) -> None:
    scheduler = SchedulerService(
        app.state.queue,
        app.state.storage,
        app.state.workers,
    )
    app.state.event_loop_tasks.append(asyncio.create_task(scheduler.run()))


def setup_workers(app: FastAPIApplication):
    for idx in range(app.state.settings.POOLING_WORKERS_NUM):
        worker = DataPollingWorker(
            app.state.storage,
            app.state.queue,
            app.state.external,
            id=f"worker_{idx}",
        )
        app.state.event_loop_tasks.append(asyncio.create_task(worker.run()))
        app.state.workers.append(worker)


def main() -> None:
    settings = AppSettings()

    # NOTE: setup logging for main process;
    # later it will be initialized for each worker process as well;
    setup_logging(settings)
    logger.info("Run %s (%s)", settings.APP_NAME, settings.APP_VERSION)
    logger.info("Settings: %s", settings)

    if settings.API_WORKERS:
        raise NotImplementedError(
            "Horizontal scaling by running multiple instances is not supported "
            "due to unsafe file storage sharing between instances. "
        )

    uvicorn.run(
        "app.main:setup",
        host=settings.API_HOST,
        port=settings.API_PORT,
        workers=settings.API_WORKERS,
        reload=settings.API_RELOAD,
        factory=True,
    )


if __name__ == "__main__":
    main()
