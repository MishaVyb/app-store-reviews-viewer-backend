from http import HTTPMethod
from typing import Literal

import httpx

from app.common.base_adapter import HTTPAdapterBase
from app.integration.itunes import schemas


class ItunesRSSAdapter(HTTPAdapterBase):
    """HTTP Adapter for the third party Itunes RSS server."""

    _api_prefix = "/us/rss/customerreviews"

    async def get_reviews(
        self,
        app_id: str,
        page: int | None = None,
        sort_by: Literal["mostRecent"] | None = "mostRecent",
    ) -> schemas.ITunesReviewsResponse:
        """Get reviews for a given app ID and page."""
        path = self._build_path(app_id, page, sort_by)
        response = await self._call_service(
            HTTPMethod.GET, path, response_schema=schemas.ITunesReviewsResponse
        )
        return response

    # TODO 48 hours or more if there is no reviews
    # async def get_reviews_with_pagination(
    #     self,
    #     app_id: str,
    #     page: int | None = None,  # start page number
    #     sort_by: Literal["mostRecent"] | None = "mostRecent",
    #     date_update_min: datetime | None = None,
    # ) -> schemas.ITunesReviewsResponse:
    #     """Get reviews for a given app ID and page."""

    def _build_path(
        self,
        app_id: str,
        page: int | None,
        sort_by: Literal["mostRecent"] | None,
    ) -> httpx.URL:
        url = f"/id={app_id}"
        if sort_by:
            url += f"/sortBy={sort_by}"
        if page:
            if page > 10:
                raise ValueError(
                    "Page number must be less than 10. External server limitation."
                )
            url += f"/page={page}"

        url += "/json"
        return super()._use_url(url)
