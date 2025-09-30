import asyncio
import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter

from app.common.base_schemas import AppID
from app.services import schemas

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
    adapter = request.app.state.storage
    res = schemas.GetAppsResponse(items=await adapter.get_app_list())
    logger.debug(f"Got {len(res.items)} apps")
    return res


@reviews.get("/{app_id}")
async def get_reviews(app_id: AppID, request: Request) -> schemas.GetReviewsResponse:
    logger.info("Handle HTTP Request: %s %s", request.method, request.url)

    storage = request.app.state.storage
    queue = request.app.state.queue

    if app := await storage.get_app(app_id):
        logger.debug("Existing app is requested: %s. ", app_id)
        logger.debug("Scheduled task to actualize reviews for next requests")
        task = queue.push(app_id)

    else:
        logger.debug("Unknown app is requested: %s. ", app_id)
        logger.debug("Waiting for reviews being fetched for unknown app: %s", app_id)
        task = queue.push(app_id)
        await task

        # NOTE: create app only after polling is completed
        app = schemas.App(id=app_id)
        await storage.create_app(app)

    reviews = await storage.get_review_list(app_id)
    return schemas.GetReviewsResponse(items=reviews)


@monitoring.get("/health")
async def health() -> None:
    return None
