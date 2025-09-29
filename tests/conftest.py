import logging
from typing import AsyncGenerator, Literal

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app.api.adapter import AppStoreReviewViewerAdapter
from app.api.app import AppStoreReviewsViewer
from app.main import setup

logger = logging.getLogger("conftest")


@pytest.fixture(scope="session")
def anyio_backend() -> Literal["asyncio"]:
    return "asyncio"


@pytest.fixture
async def app() -> AsyncGenerator[AppStoreReviewsViewer, None]:
    app = setup()
    async with LifespanManager(app):
        yield app


@pytest.fixture
async def client(
    app: AppStoreReviewsViewer, setup_tables: None
) -> AsyncGenerator[AppStoreReviewViewerAdapter, None]:
    async with AsyncClient(
        transport=ASGITransport(app), base_url="http://testserver"
    ) as session:
        yield AppStoreReviewViewerAdapter(session)
