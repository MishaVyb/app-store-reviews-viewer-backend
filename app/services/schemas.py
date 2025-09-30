from __future__ import annotations

import warnings
from typing import Generic, TypeVar

from pydantic import AwareDatetime, BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.common.base_schemas import AppID, ReviewId

# enable pydantic warning as error to not miss type mismatch
warnings.filterwarnings("error", r"Pydantic serializer warnings")


# TODO move to base_schemas ???
class BaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=to_camel,
        use_attribute_docstrings=True,
        json_schema_serialization_defaults_required=True,
    )

    def __repr_args__(self):
        # represent only the fields that are set
        for k, v in super().__repr_args__():
            if k in self.model_fields_set and self.model_fields[k].repr:
                yield (k, v)


class App(BaseSchema):
    id: AppID


class Review(BaseSchema):
    id: ReviewId
    app_id: AppID

    title: str
    content: str
    author: str
    score: int
    updated: AwareDatetime


_T = TypeVar("_T")


class BasePaginatedResponse(BaseModel, Generic[_T]):
    items: list[_T]


class GetAppsResponse(BasePaginatedResponse[App]):
    pass


class GetReviewsResponse(BasePaginatedResponse[Review]):
    pass
