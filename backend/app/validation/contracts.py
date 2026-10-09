"""Strict, versioned request and model-output boundaries for TANAW-03."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

CardId = Annotated[str, StringConstraints(min_length=1, max_length=32)]
CardIds = Annotated[list[CardId], Field(min_length=1, max_length=12)]


class ExpandRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    request_id: UUID
    revision: Annotated[int, Field(ge=0)]
    vocabulary_version: Annotated[str, StringConstraints(min_length=1, max_length=64)]
    locale: Literal["en"]
    selected_card_ids: CardIds


class ModelCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    source_card_ids: CardIds
    text: Annotated[str, StringConstraints(min_length=1, max_length=256)]
