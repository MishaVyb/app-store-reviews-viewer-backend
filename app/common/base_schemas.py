from typing import Annotated

from fastapi import Path
from pydantic import Field

AppID = Annotated[int, Field(description="AppStore Application ID")]
AppIDPath = Annotated[int, Path(description="AppStore Application ID")]
ReviewId = Annotated[str, Field(description="AppStore Review ID")]
