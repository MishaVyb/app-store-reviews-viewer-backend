import asyncio
import json
import logging
import re
from typing import AsyncGenerator, Literal

import httpx
import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from pytest_httpx import HTTPXMock

from app.api.adapter import AppStoreReviewViewerAdapter
from app.api.app import FastAPIApplication
from app.config import AppSettings
from app.main import setup

logger = logging.getLogger("conftest")


TEST_APP_IDS_INITIAL = AppSettings.model_fields["STORAGE_INITIAL_APP_IDS"].default
TEST_APP_ID_INITIAL_1 = TEST_APP_IDS_INITIAL[0]
TEST_APP_ID_UNKNOWN = 389801252  # not in initial app ids list
TEST_REVIEWS_COUNT = 50


@pytest.fixture
def anyio_backend() -> Literal["asyncio"]:
    return "asyncio"


@pytest.fixture
def settings_overrides() -> AppSettings | None:
    return AppSettings(SCHEDULER_ENABLED=False)


@pytest.fixture
async def app(
    settings_overrides: AppSettings | None,
) -> AsyncGenerator[FastAPIApplication, None]:
    app = setup(settings_overrides)
    async with LifespanManager(app):
        yield app


@pytest.fixture
async def client(
    app: FastAPIApplication,
) -> AsyncGenerator[AppStoreReviewViewerAdapter, None]:
    async with AsyncClient(
        transport=ASGITransport(app), base_url="http://testserver"
    ) as session:
        yield AppStoreReviewViewerAdapter(session)


@pytest.fixture
async def mock_external_http_requests(
    app: FastAPIApplication, httpx_mock: HTTPXMock
) -> None:
    async def callback(request: httpx.Request) -> httpx.Response:
        await asyncio.sleep(0)  # switch event loop task

        match = re.match(r".*/id=(\d+)/.*", request.url.path)
        assert match
        app_id = match.group(1)

        path = app.state.settings.ROOT_DIR / "data" / "examples" / f"{app_id}.json"
        return httpx.Response(200, json=json.loads(path.read_text()))

    httpx_mock.add_callback(
        callback,
        url=re.compile(f"{app.state.settings.HTTP_EXTERNAL_RSS_HOST}.*"),
        is_reusable=True,
        is_optional=True,
    )
