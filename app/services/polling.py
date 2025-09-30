import logging
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
    ):
        self._storage = storage
        self._queue = queue
        self._adapter = adapter
        self._id = id

    async def run(self) -> Never:
        logger.info("Start worker: %s", self)
        while True:
            task = await self._queue.pop()
            try:
                await self.process(task)
            except Exception as e:
                logger.exception(f"Error reviews polling for app {task.app_id}: {e}")
                # task.failed()
                # raise NotImplementedError

            else:
                self._queue.complete(task)

    async def process(self, task: PollReviewsTask) -> None:
        logger.debug("%s; Processing task: %s", self, task)

        response = await self._adapter.get_reviews(task.app_id)
        reviews = []
        for entry in response.feed.entry:
            review = schemas.Review(
                id=entry.id.label,
                app_id=task.app_id,
                title=entry.title.label,
                content=entry.content.label,
                author=entry.author.label,
                score=entry.im_rating.label,
                updated=entry.updated.label,
            )
            reviews.append(review)

        await self._storage.create_reviews(reviews)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._id})"
