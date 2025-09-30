import asyncio
import logging

import pytest
from asgi_lifespan import LifespanManager

from app.api.app import FastAPIApplication
from app.config import AppSettings
from app.main import setup
from tests.conftest import TEST_APP_IDS_INITIAL

logger = logging.getLogger("conftest")

pytestmark = [
    pytest.mark.usefixtures("mock_external_http_requests"),
]


@pytest.fixture
def settings_overrides(settings_overrides) -> AppSettings | None:
    return AppSettings(
        **dict(
            settings_overrides.model_dump(exclude_unset=True),
            SCHEDULER_ENABLED=True,
        )
    )


async def test_scheduler_enabled(
    app: FastAPIApplication, settings_overrides: AppSettings
) -> None:
    app = setup(settings_overrides)
    async with LifespanManager(app):
        await asyncio.sleep(0.1)
        assert await app.state.storage.get_review_list(TEST_APP_IDS_INITIAL[0])
        assert await app.state.storage.get_review_list(TEST_APP_IDS_INITIAL[1])
        assert await app.state.storage.get_review_list(TEST_APP_IDS_INITIAL[2])


async def test_file_persistence(
    app: FastAPIApplication, settings_overrides: AppSettings
) -> None:
    app = setup(settings_overrides)
    async with LifespanManager(app):
        await asyncio.sleep(0.1)
        assert await app.state.storage.get_review_list(TEST_APP_IDS_INITIAL[0])

    settings = AppSettings(
        **dict(
            settings_overrides.model_dump(exclude_unset=True),
            SCHEDULER_ENABLED=False,
        )
    )
    app = setup(settings)
    async with LifespanManager(app):
        await asyncio.sleep(0.1)
        assert await app.state.storage.get_review_list(TEST_APP_IDS_INITIAL[0])
