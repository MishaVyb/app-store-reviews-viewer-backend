import logging

from pydantic import BaseModel

from app.common.base_schemas import AppID, ReviewId
from app.services import schemas

logger = logging.getLogger(__name__)


class Storage(BaseModel):
    apps: dict[AppID, schemas.App] = {}
    reviews: dict[ReviewId, schemas.Review] = {}


class StorageService:
    """Persistence service."""

    def __init__(self):
        self._storage = Storage()

    async def create_app(self, app: schemas.App):
        logger.debug("Creating app: %s", app)
        self._storage.apps[app.id] = app

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

    async def get_review(self, review_id: ReviewId) -> schemas.Review | None:
        logger.debug("Getting review: %s", review_id)
        return self._storage.reviews.get(review_id)

    async def get_review_list(self, app_id: AppID) -> list[schemas.Review]:
        logger.debug("Getting reviews for app: %s", app_id)
        return [
            review
            for review in self._storage.reviews.values()
            if review.app_id == app_id
        ]
