
from pydantic import BaseModel, Field
from typing import List, Optional, Union
from datetime import datetime


class LabelField(BaseModel):
    """Base schema for fields that have a 'label' property"""
    label: str


class AttributesField(BaseModel):
    """Base schema for fields that have an 'attributes' property"""
    attributes: dict


class LinkAttributes(BaseModel):
    """Schema for link attributes"""
    rel: str
    href: str
    type: Optional[str] = None


class ContentAttributes(BaseModel):
    """Schema for content attributes"""
    type: str


class ContentTypeAttributes(BaseModel):
    """Schema for content type attributes"""
    term: str
    label: str


class Author(BaseModel):
    """Schema for review author"""
    uri: LabelField
    name: LabelField
    label: str = ""


class ReviewEntry(BaseModel):
    """Schema for individual review entry"""
    author: Author
    updated: LabelField
    im_rating: LabelField = Field(alias="im:rating")
    im_version: LabelField = Field(alias="im:version")
    id: LabelField
    title: LabelField
    content: LabelField
    link: AttributesField
    im_vote_sum: LabelField = Field(alias="im:voteSum")
    im_content_type: AttributesField = Field(alias="im:contentType")
    im_vote_count: LabelField = Field(alias="im:voteCount")

    class Config:
        allow_population_by_field_name = True


class FeedAuthor(BaseModel):
    """Schema for feed author"""
    name: LabelField
    uri: LabelField


class FeedLink(BaseModel):
    """Schema for feed links"""
    attributes: LinkAttributes


class Feed(BaseModel):
    """Schema for the main feed structure"""
    author: FeedAuthor
    entry: List[ReviewEntry]
    updated: LabelField
    rights: LabelField
    title: LabelField
    icon: LabelField
    link: List[FeedLink]
    id: LabelField


class ITunesReviewsResponse(BaseModel):
    """Root schema for iTunes App Store reviews response"""
    feed: Feed