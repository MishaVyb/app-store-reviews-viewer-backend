import asyncio
import logging

import pytest
from pytest_mock import MockerFixture

from app.api.adapter import AppStoreReviewViewerAdapter
from app.api.app import FastAPIApplication
from app.services.queue import PollReviewsTask
from tests.conftest import TEST_APP_ID_INITIAL, TEST_APP_ID_UNKNOWN, TEST_REVIEWS_COUNT

logger = logging.getLogger("conftest")

pytestmark = [
    pytest.mark.usefixtures("mock_external_http_requests"),
]


async def test_get_apps(
    client: AppStoreReviewViewerAdapter, app: FastAPIApplication
) -> None:
    res = await client.get_apps()
    assert len(res.items) == len(app.state.settings.STORAGE_INITIAL_APP_IDS)


async def test_get_known_reviews(
    client: AppStoreReviewViewerAdapter, app: FastAPIApplication
) -> None:
    app_id = TEST_APP_ID_INITIAL
    res = await client.get_reviews(app_id)
    assert len(res.items) == 0

    task_id = PollReviewsTask(app_id).id
    assert task_id in app.state.queue._pending
    assert task_id not in app.state.queue._in_progress
    assert task_id not in app.state.queue._completed

    await app.state.queue._pending[task_id]
    assert task_id not in app.state.queue._in_progress
    assert task_id not in app.state.queue._pending
    assert task_id in app.state.queue._completed

    res = await client.get_reviews(app_id)
    assert len(res.items) == TEST_REVIEWS_COUNT


async def test_get_unknown_reviews(
    client: AppStoreReviewViewerAdapter, app: FastAPIApplication
) -> None:
    res = await client.get_reviews(TEST_APP_ID_UNKNOWN)
    assert len(res.items) == TEST_REVIEWS_COUNT


async def test_get_reviews_race_condition(
    client: AppStoreReviewViewerAdapter, app: FastAPIApplication, mocker: MockerFixture
) -> None:
    app_id = TEST_APP_ID_INITIAL
    spy = mocker.spy(app.state.external, "get_reviews")

    # in case of simultaneous requests for the same app, only one worker will poll reviews
    async with asyncio.TaskGroup() as tg:
        for _ in range(10):
            task = tg.create_task(client.get_reviews(app_id))

    res = task.result()
    assert len(res.items) == 0  # no reviews yet for this app
    assert spy.call_count == 1  # only one worker initially polled reviews for targe app

    # following requests for the same app should return reviews
    # - polling task has been scheduled on previous request
    # - polling task is expected to be completed at this point already
    async with asyncio.TaskGroup() as tg:
        for _ in range(10):
            task = tg.create_task(client.get_reviews(app_id))

    res = task.result()
    assert len(res.items) == TEST_REVIEWS_COUNT
    assert spy.call_count == 2  # only one worker actualized (re-fetched) reviews


async def test_get_unknown_reviews_race_condition(
    client: AppStoreReviewViewerAdapter, app: FastAPIApplication, mocker: MockerFixture
) -> None:
    spy = mocker.spy(app.state.external, "get_reviews")

    async with asyncio.TaskGroup() as tg:
        for _ in range(10):
            task = tg.create_task(client.get_reviews(TEST_APP_ID_UNKNOWN))

    res = task.result()
    assert len(res.items) == TEST_REVIEWS_COUNT
    assert spy.call_count == 1  # only one worker initially polled reviews for targe app
