from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_attention_ontology_dto.focus.focus_scope_request import FocusScopeRequest


class ActorFocusScopeRequest(BaseModel):
    # Relationships
    focus_scope_request: FocusScopeRequest | None = Field(default=None)
