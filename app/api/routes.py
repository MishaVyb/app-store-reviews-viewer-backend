import logging
from datetime import datetime
from typing import TYPE_CHECKING

from fastapi import APIRouter

from app.common import base_schemas as schemas
from app.common.base_schemas import AppID

if TYPE_CHECKING:
    from app.api.app import Request
else:
    from fastapi import Request

reviews = APIRouter(prefix="/reviews", tags=["App Store Reviews"])
apps = APIRouter(prefix="/apps", tags=["App Store Apps"])
monitoring = APIRouter(prefix="", tags=["Monitoring"])

logger = logging.getLogger(__name__)


@apps.get("")
async def get_apps(request: Request) -> schemas.GetAppsResponse:
    """Get current apps from the storage."""

    adapter = request.app.state.storage
    res = schemas.GetAppsResponse(items=await adapter.get_app_list())
    logger.debug(f"Got {len(res.items)} apps")
    return res


@reviews.get("/{app_id}")
async def get_reviews(
    app_id: AppID,
    request: Request,
    *,
    updated_min: datetime | None = None,
) -> schemas.GetReviewsResponse:
    """Get reviews for a given App ID."""

    logger.info("Handle HTTP Request: %s %s", request.method, request.url)

    storage = request.app.state.storage
    queue = request.app.state.queue

    if app := await storage.get_app(app_id):
        logger.debug("Existing app is requested: %s. ", app)
        logger.debug("Scheduled task to actualize reviews for next requests")
        task = queue.push(app_id)

    else:
        logger.debug("Unknown app is requested: %s. ", app_id)
        logger.debug("Waiting for reviews being fetched for unknown app: %s", app_id)
        task = queue.push(app_id)
        await task

    reviews = await storage.get_review_list(app_id, updated_min=updated_min)
    return schemas.GetReviewsResponse(items=reviews)


@monitoring.get("/health")
async def health() -> None:
    return None
