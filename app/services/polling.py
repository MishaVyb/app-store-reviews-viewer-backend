import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Never

from app.common import base_schemas as schemas
from app.integration.itunes.adapter import ItunesRSSAdapter
from app.services.queue import DataPollingQueue, PollReviewsTask
from app.services.storage import StorageService

logger = logging.getLogger(__name__)


class DataPollingWorker:
    """
    Service to poll data from external sources.
    Thy system may run many workers at one time to poll data from external sources concurrently.
    """

    def __init__(
        self,
        storage: StorageService,
        queue: DataPollingQueue,
        adapter: ItunesRSSAdapter,
        *,
        id: str,
        polling_depth: timedelta,
    ) -> None:
        self._storage = storage
        self._queue = queue
        self._adapter = adapter
        self._id = id
        self._polling_depth = polling_depth
        self._is_available = asyncio.Event()

    @property
    def is_available(self) -> bool:
        return self._is_available.is_set()

    async def wait_for_availability(self) -> None:
        await self._is_available.wait()

    async def run(self) -> Never:
        logger.info("Start worker in the background: %s", self)
        while True:
            self._is_available.set()

            # wait for the next task, if there is no task, the worker is blocked
            task = await self._queue.pop()

            try:
                await self.process(task)
            except Exception as e:
                logger.exception(f"Error reviews polling for app {task.app_id}: {e}")
            finally:
                # NOTE
                # No matter are there errors or not, the task is marked as complete.
                # This is important to avoid blocking the queue.
                # In case of error, user gets no response for this App.
                self._queue.mark_complete(task)
                self._is_available.clear()

    async def process(self, task: PollReviewsTask) -> None:
        """
        Process task to poll reviews for a given App.

        It calls external adapter to get reviews, build compatible with StorageService
        models and then create these entities in the storage.
        """
        logger.debug("%s; Processing task: %s", self, task)

        reviews: list[schemas.Review] = []
        for page in range(1, self._adapter.MAX_PAGES + 1):
            response = await self._adapter.get_reviews(task.app_id, page)
            if not response.feed.entry:
                break

            for entry in response.feed.entry:
                review = schemas.Review(
                    # NOTE:
                    # review id might be not unique among all apps, so build composed review id
                    id=f"{task.app_id}_{entry.id.label}",
                    app_id=task.app_id,
                    title=entry.title.label,
                    content=entry.content.label,
                    author=entry.author.name.label,
                    score=entry.im_rating.label,  # type: ignore
                    updated=entry.updated.label,  # type: ignore
                )
                reviews.append(review)

            now = datetime.now(timezone.utc)
            if reviews[-1].updated < now - self._polling_depth:
                break

        await self._storage.create_reviews(reviews)

        # create app in case it does not exist
        if not await self._storage.get_app(task.app_id):
            app = schemas.App(id=task.app_id)
            await self._storage.create_app(app)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._id})"
