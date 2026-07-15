from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_attention_ontology_dto.session.attention_session_layout import AttentionSessionLayout
    from aware_identity_ontology_dto.session.session import Session


class AttentionSession(BaseModel):
    """
    Identity-backed Attention session over graph/layout focus state.
    Contract:
    - AttentionSession is the lowest shared Attention primitive over Graph OS.
    - It bridges to Identity Session for actor participation.
    - It owns layout/section/focus transition state without importing higher
    application layers, DTO/API, service, or SDK surfaces.
    """

    # Relationships
    identity_session: Session | None = Field(default=None)
    layouts: list[AttentionSessionLayout] = Field(default_factory=list)
    active_layout: AttentionSessionLayout | None = Field(default=None)

    # Attributes
    key: str | None = Field(default=None)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    purpose: str | None = Field(default=None)
    status: str = Field(default="active")
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)
