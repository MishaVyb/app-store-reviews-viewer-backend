import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Never

from app.integration.itunes.adapter import ItunesRSSAdapter
from app.services import schemas
from app.services.queue import DataPollingQueue, PollReviewsTask
from app.services.storage import StorageService

logger = logging.getLogger(__name__)


class DataPollingWorker:
    """Service to poll data from external sources."""

    def __init__(
        self,
        storage: StorageService,
        queue: DataPollingQueue,
        adapter: ItunesRSSAdapter,
        *,
        id: str,
        polling_depth: timedelta,
    ):
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
        logger.info("Start worker: %s", self)
        while True:
            self._is_available.set()
            task = await self._queue.pop()
            try:
                await self.process(task)
            except Exception as e:
                logger.exception(f"Error reviews polling for app {task.app_id}: {e}")
            finally:
                self._queue.mark_complete(task)
                self._is_available.clear()

    async def process(self, task: PollReviewsTask) -> None:
        logger.debug("%s; Processing task: %s", self, task)

        reviews = []
        for page in range(1, self._adapter.MAX_PAGES + 1):
            response = await self._adapter.get_reviews(task.app_id, page)
            if not response.feed.entry:
                break

            for entry in response.feed.entry:
                review = schemas.Review(
                    # review id might be not unique among all apps, so build composed review id
                    id=f"{task.app_id}_{entry.id.label}",
                    app_id=task.app_id,
                    title=entry.title.label,
                    content=entry.content.label,
                    author=entry.author.name.label,
                    score=entry.im_rating.label,
                    updated=entry.updated.label,
                )
                reviews.append(review)

            now = datetime.now(timezone.utc)
            if reviews[-1].updated < now - self._polling_depth:
                break

        await self._storage.create_reviews(reviews)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._id})"
