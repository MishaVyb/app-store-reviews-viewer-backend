import asyncio
import logging

from app.common.base_schemas import AppID

logger = logging.getLogger(__name__)


# TODO statuses: pending, working, completed, failed
class PollReviewsTask:

    def __init__(self, app_id: AppID):
        self._app_id = app_id
        self._is_completed = asyncio.Event()

    @property
    def app_id(self) -> AppID:
        return self._app_id

    @property
    def id(self) -> str:
        return f"task_{self._app_id}"

    def mark_complete(self) -> None:
        self._is_completed.set()

    def __await__(self):
        return self._is_completed.wait().__await__()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.id})"


class DataPollingQueue:
    """
    Queue for data polling tasks.

    Implements both FIFO (First In, First Out) and LIFO (Last In, First Out) principles
    depending on the urgency of the task.
    """

    def __init__(self) -> None:
        self._queue: list[PollReviewsTask] = []
        self._is_queue_filled = asyncio.Event()

        self._pending: dict[str, PollReviewsTask] = {}
        self._in_progress: dict[str, PollReviewsTask] = {}
        self._completed: dict[str, PollReviewsTask] = {}

    def push(self, app_id: AppID, *, urgent: bool = False) -> PollReviewsTask:
        task = PollReviewsTask(app_id)

        if pending_task := self._pending.get(task.id):
            logger.warning("Task is pending already: %s", task)
            return pending_task
        if pending_task := self._in_progress.get(task.id):
            logger.warning("Task in progress already: %s", task)
            return pending_task

        self._pending[task.id] = task
        if urgent:
            self._queue.insert(0, task)
        else:
            self._queue.append(task)

        self._is_queue_filled.set()
        return task

    async def pop(self) -> PollReviewsTask:
        if not self._queue:
            logger.debug("No task in queue, waiting for a task...")
            await self._is_queue_filled.wait()

        task = self._queue.pop(0)
        if not self._queue:
            self._is_queue_filled.clear()

        self._pending.pop(task.id)
        self._in_progress[task.id] = task
        return task

    async def wait_all_pending_and_progress(self) -> None:
        tasks = [*self._pending.values(), *self._in_progress.values()]
        await asyncio.gather(*[asyncio.ensure_future(task) for task in tasks])

    def mark_complete(self, task: PollReviewsTask) -> None:
        self._in_progress.pop(task.id)
        self._completed[task.id] = task
        task.mark_complete()
