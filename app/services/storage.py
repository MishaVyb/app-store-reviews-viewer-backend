import asyncio
import logging
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

from app.common import base_schemas as schemas
from app.common.base_schemas import AppID, ReviewId

logger = logging.getLogger(__name__)


class Storage(BaseModel):
    apps: dict[AppID, schemas.App] = {}
    reviews: dict[ReviewId, schemas.Review] = {}


class StorageService:
    """Simple file based persistence service."""

    def __init__(self, path: Path) -> None:
        self._storage = Storage()
        self._path = path

    async def create_app(self, app: schemas.App):
        logger.debug("Creating app: %s", app)
        self._storage.apps[app.id] = app
        await self.write()

    async def get_app(self, app_id: AppID) -> schemas.App | None:
        logger.debug("Getting app: %s", app_id)
        return self._storage.apps.get(app_id)

    async def get_app_list(self) -> list[schemas.App]:
        logger.debug("Getting apps")
        return list(self._storage.apps.values())

    async def create_reviews(self, reviews: list[schemas.Review]):
        logger.debug("Creating reviews: %s", len(reviews))
        for review in reviews:
            self._storage.reviews[review.id] = review
        await self.write()

    async def get_review(self, review_id: ReviewId) -> schemas.Review | None:
        logger.debug("Getting review: %s", review_id)
        return self._storage.reviews.get(review_id)

    async def get_review_list(
        self, app_id: AppID, *, updated_min: datetime | None = None
    ) -> list[schemas.Review]:
        logger.debug("Getting reviews for app: %s", app_id)
        filtered = [
            review
            for review in self._storage.reviews.values()
            if review.app_id == app_id
            and (updated_min is None or review.updated >= updated_min)
        ]
        return list(reversed(sorted(filtered, key=lambda x: x.updated)))

    async def load(self) -> bool:
        if not self._path.exists() or self._path.read_text() == "":
            return False
        self._storage = Storage.model_validate_json(self._path.read_text())
        return True

    async def write(self) -> None:
        await asyncio.to_thread(self._path.write_text, self._storage.model_dump_json())
