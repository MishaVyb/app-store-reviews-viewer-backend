import asyncio
import logging

import pytest
from pytest_mock import MockerFixture

from app.api.adapter import AppStoreReviewViewerAdapter
from app.api.app import FastAPIApplication
from app.services.queue import PollReviewsTask
from tests.conftest import (
    TEST_APP_ID_INITIAL_1,
    TEST_APP_ID_NO_REVIEWS,
    TEST_APP_ID_UNKNOWN,
    TEST_REVIEWS_COUNT,
)

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

    # for the first time, there are no reviews for this app, because polling task is not yet completed
    app_id = TEST_APP_ID_INITIAL_1
    res = await client.get_reviews(app_id)
    assert len(res.items) == 0

    task_id = PollReviewsTask(app_id).id
    assert task_id in app.state.queue._pending
    assert task_id not in app.state.queue._in_progress
    assert task_id not in app.state.queue._completed

    # wait for the polling task to be completed
    await app.state.queue.wait_all_pending_and_progress()
    assert task_id not in app.state.queue._in_progress
    assert task_id not in app.state.queue._pending
    assert task_id in app.state.queue._completed

    # call one more time to get reviews after storage population
    res = await client.get_reviews(app_id)
    assert len(res.items) == TEST_REVIEWS_COUNT


async def test_get_unknown_reviews(
    client: AppStoreReviewViewerAdapter, app: FastAPIApplication
) -> None:
    # in that case get_reviews will return reviews for the unknown app at first(!) request
    # because it waits for the polling task to be completed (since the service got new app id to handle)
    res = await client.get_reviews(TEST_APP_ID_UNKNOWN)
    assert len(res.items) == TEST_REVIEWS_COUNT


async def test_get_reviews_pagination(
    client: AppStoreReviewViewerAdapter, app: FastAPIApplication, mocker: MockerFixture
) -> None:
    # check that worker calls external RSS server only once since since last comment was written long time ago
    # see settings.POLLING_REVIEWS_DEPTH
    spy = mocker.spy(app.state.external, "get_reviews")
    res = await client.get_reviews(TEST_APP_ID_NO_REVIEWS)
    assert not res.items
    assert spy.call_count == 1


async def test_get_reviews_race_condition(
    client: AppStoreReviewViewerAdapter, app: FastAPIApplication, mocker: MockerFixture
) -> None:
    app_id = TEST_APP_ID_INITIAL_1
    spy = mocker.spy(app.state.external, "get_reviews")

    # in case of simultaneous requests for the same app, only one worker will poll reviews
    async with asyncio.TaskGroup() as tg:
        for _ in range(10):
            task = tg.create_task(client.get_reviews(app_id))

    res = task.result()
    assert len(res.items) == 0  # no reviews yet for this app
    assert spy.call_count == 1  # only one worker initially polled reviews for targe app

    await app.state.queue.wait_all_pending_and_progress()

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
