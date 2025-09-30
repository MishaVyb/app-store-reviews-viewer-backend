from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        validate_default=True,
        json_schema_serialization_defaults_required=True,
    )


class Label(BaseSchema):
    label: str


class Attributes(BaseSchema):
    attributes: dict


class LinkAttributes(BaseSchema):
    rel: str
    href: str
    type: Optional[str] = None


class ContentAttributes(BaseSchema):
    type: str


class ContentTypeAttributes(BaseSchema):
    term: str
    label: str


class Author(BaseSchema):
    uri: Label
    name: Label
    label: str = ""


class ReviewEntry(BaseSchema):
    """Schema for individual review entry."""

    id: Label
    author: Author
    updated: Label
    im_rating: Label = Field(alias="im:rating")
    im_version: Label = Field(alias="im:version")
    title: Label
    content: Label
    link: Attributes
    im_vote_sum: Label = Field(alias="im:voteSum")
    im_content_type: Attributes = Field(alias="im:contentType")
    im_vote_count: Label = Field(alias="im:voteCount")


class FeedAuthor(BaseSchema):
    name: Label
    uri: Label


class FeedLink(BaseSchema):
    attributes: LinkAttributes


class Feed(BaseSchema):
    id: Label
    entry: List[ReviewEntry] = []
    author: FeedAuthor
    updated: Label
    rights: Label
    title: Label
    icon: Label
    link: List[FeedLink]


class ITunesReviewsResponse(BaseSchema):
    """Root schema for iTunes App Store reviews response."""

    feed: Feed
