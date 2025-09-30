from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from app.common.base_schemas import AppID


class AppSettings(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_default=True,
        validate_return=True,
        frozen=True,
    )

    ROOT_DIR: Path = Path(__file__).resolve().parent.parent

    APP_ENVIRONMENT: Literal["dev", "staging", "production"] = "dev"
    APP_NAME: str = "App Store Reviews Viewer"
    APP_DESCRIPTION: str = "App Store Reviews Viewer API"
    APP_VERSION: str = "1.0.0.0"

    API_PORT: int = 8000
    API_HOST: str = "0.0.0.0"
    API_WORKERS: int | None = None
    API_RELOAD: bool = False

    API_CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    API_PREFIX: str = "/api"

    POOLING_WORKERS_NUM: int = 10
    STORAGE_INITIAL_APP_IDS: list[AppID] = [
        415458524,  # SkyScanner
        595068606,  # Tab
        640437525,  # Qantas
    ]

    HTTP_EXTERNAL_RSS_HOST: str = "https://itunes.apple.com/us/rss/customerreviews"
    HTTP_EXTERNAL_RSS_TIMEOUT: float = 59.0

    LOG_LEVEL: str = "DEBUG"
    LOG_LEVEL_CONFTEST: str = "DEBUG"
    LOG_LEVEL_HTTPX: str = "DEBUG"
    LOG_HANDLERS: list[str] = ["console", "file"]

    LOG_FILE: str = "app_store_reviews_viewer.log"
    LOG_JSON_FILE: str = "app_store_reviews_viewer.json"
    LOG_DIR_CREATE: bool = True
    LOG_MAX_BYTE_WHEN_ROTATION: int = 100 * 1024 * 1024
    LOG_BACKUP_COUNT: int = 10

    @property
    def API_OPENAPI_URL(self) -> str:
        return f"{self.API_PREFIX}/openapi.json"

    @property
    def API_DOCS_URL(self) -> str:
        return f"{self.API_PREFIX}/docs"

    @property
    def LOG_DIR(self) -> Path:
        return self.ROOT_DIR / "log"

    @property
    def LOGGING(self) -> dict[str, Any]:
        default_handlers = {
            "console": {
                "level": self.LOG_LEVEL,
                "class": "logging.StreamHandler",
                "formatter": "console",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "level": self.LOG_LEVEL,
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "file",
                "filename": self.LOG_DIR / self.LOG_FILE,
                "maxBytes": self.LOG_MAX_BYTE_WHEN_ROTATION,
                "backupCount": self.LOG_BACKUP_COUNT,
            },
        }
        handlers = {k: v for k, v in default_handlers.items() if k in self.LOG_HANDLERS}
        config = {
            "version": 1,
            "formatters": {
                "file": {
                    "()": "uvicorn.logging.ColourizedFormatter",
                    "format": "[-] %(asctime)s [%(levelname)s] - %(message)s",
                },
                "console": {
                    "()": "uvicorn.logging.DefaultFormatter",
                    "fmt": "%(levelprefix)s %(message)s",
                    "use_colors": None,
                },
            },
            "handlers": handlers,
            "loggers": {
                "app": {
                    "level": self.LOG_LEVEL,
                    "handlers": self.LOG_HANDLERS,
                },
                "uvicorn": {
                    "handlers": self.LOG_HANDLERS,
                    "level": self.LOG_LEVEL,
                },
                "conftest": {
                    "level": self.LOG_LEVEL_CONFTEST,
                    "handlers": self.LOG_HANDLERS,
                },
                "httpx": {
                    "level": self.LOG_LEVEL_HTTPX,
                    "handlers": self.LOG_HANDLERS,
                },
            },
        }
        return config

    def __repr_args__(self):
        # represent only the fields that are set
        for k, v in super().__repr_args__():
            if (
                k in self.model_fields_set
                and k in self.model_fields
                and self.model_fields[k].repr
            ):
                yield (k, v)

    def __str__(self) -> str:
        return repr(self)
