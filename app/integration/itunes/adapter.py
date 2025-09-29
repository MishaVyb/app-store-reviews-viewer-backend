from http import HTTPMethod
from pathlib import Path
from typing import Literal, Type, TypeVar

import httpx
from fhir.resources.observation import Observation
from fhir.resources.patient import Patient
from pydantic import BaseModel

from app.adapter.base import HTTPAdapterBase, QueryParamTypes

_T = TypeVar("_T")


class ItunesRSSAdapter(HTTPAdapterBase):
    """
    Adapter for the third party Itunes RSS server.
    https://itunes.apple.com/us/rss/customerreviews
    """

    _api_prefix = "/us/rss/customerreviews"

    async def get_reviews(
        self,
        app_id: str,
        page: int | None = None,
        sort_by: Literal["mostRecent"] | None = None,
    ) -> list[AppStoreReview]:
        """Get reviews for a given app ID and page."""
        response = await self._call_service(
            HTTPMethod.GET, url, response_schema=list[AppStoreReview]
        )
        return response

    def _use_url(
        self,
        app_id: str,
        page: int | None = None,
        sort_by: Literal["mostRecent"] | None = None,
    ) -> str:
        url = f"id={app_id}"
        if sort_by:
            url += f"/sortBy={sort_by}"
        if page:
            url += f"/page={page}"
        url += "/json"
        return super()._use_url(url)
