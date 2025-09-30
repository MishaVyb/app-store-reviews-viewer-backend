import asyncio
import logging
from datetime import timedelta

from app.services import schemas
from app.services.polling import DataPollingWorker
from app.services.queue import DataPollingQueue
from app.services.storage import StorageService

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service to schedule background tasks to workers."""

    def __init__(
        self,
        queue: DataPollingQueue,
        storage: StorageService,
        workers: list[DataPollingWorker],
        delay: float = 10.0,  # seconds
    ) -> None:
        self._queue = queue
        self._storage = storage
        self._workers = workers
        self._delay = delay

    async def run(self) -> None:
        while True:
            await self.process()
            await asyncio.sleep(self._delay)

    async def wait_available_worker(self) -> None:
        await asyncio.wait(
            [
                asyncio.create_task(worker.wait_for_availability())
                for worker in self._workers
            ],
            return_when=asyncio.FIRST_COMPLETED,
        )

    async def process(self) -> None:
        """Schedule review polling for all apps."""
        logger.debug("%s. Scheduling reviews polling for all apps", self)
        apps = await self._storage.get_app_list()

        for app in apps:
            logger.debug("%s. Actualizing reviews for app: %s", self, app.id)
            await self.wait_available_worker()
            self._queue.push(app.id)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
