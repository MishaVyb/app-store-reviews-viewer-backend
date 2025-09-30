from http import HTTPMethod

from app.common.base_adapter import HTTPAdapterBase
from app.common.base_schemas import AppID
from app.services import schemas


class AppStoreReviewViewerAdapter(HTTPAdapterBase):
    """
    Adapter for the App Store Review Viewer API.
    For testing purposes or future integrations in other services.
    """

    _api_prefix = "/api"

    async def get_apps(self) -> schemas.GetAppsResponse:
        return await self._call_service(
            HTTPMethod.GET,
            "/apps",
            response_schema=schemas.GetAppsResponse,
        )

    async def get_reviews(self, app_id: AppID) -> schemas.GetReviewsResponse:
        return await self._call_service(
            HTTPMethod.GET,
            f"/reviews/{app_id}",
            response_schema=schemas.GetReviewsResponse,
        )
