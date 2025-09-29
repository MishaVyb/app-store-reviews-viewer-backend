import logging
from pathlib import Path

from app.integration.itunes.schemas import ITunesReviewsResponse

logger = logging.getLogger("conftest")


async def test_itunes_integration_schema() -> None:
    res = ITunesReviewsResponse.model_validate_json(
        Path("data/examples/sky-scanner.json").read_text()
    )
