import logging
import logging.config
import os
from contextlib import asynccontextmanager

import click
import uvicorn

from app.api.app import AppStoreReviewsViewer
from app.config import AppSettings

logger = logging.getLogger("app.main")


def setup_logging(settings: AppSettings) -> None:
    if settings.LOG_DIR_CREATE and not settings.LOG_DIR.exists():
        settings.LOG_DIR.mkdir()
    logging.config.dictConfig(settings.LOGGING)


def setup() -> AppStoreReviewsViewer:
    settings = AppSettings()
    setup_logging(settings)
    logger.info("Run app worker [%s]", click.style(os.getpid(), fg="cyan"))
    return AppStoreReviewsViewer.startup(settings, lifespan)


@asynccontextmanager
async def lifespan(app: AppStoreReviewsViewer):
    try:
        yield
    finally:
        pass


def main() -> None:
    settings = AppSettings()

    # NOTE: setup logging for main process;
    # later it will be initialized for each worker process as well;
    setup_logging(settings)
    logger.info("Run %s (%s)", settings.APP_NAME, settings.APP_VERSION)
    logger.info("Settings: %s", settings)

    uvicorn.run(
        "app.main:setup",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        workers=settings.APP_WORKERS,
        reload=settings.APP_RELOAD,
        factory=True,
    )


if __name__ == "__main__":
    main()
