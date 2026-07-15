from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Attention Ontology Dto
from aware_attention_ontology_dto.focus.focus_enums import FocusScopeRequestStatus

if TYPE_CHECKING:
    from aware_attention_ontology_dto.focus.focus import Focus
    from aware_attention_ontology_dto.focus.focus_scope_request_response import FocusScopeRequestResponse


class FocusScopeRequest(BaseModel):
    # Relationships
    focus: Focus | None = Field(default=None)
    response: FocusScopeRequestResponse | None = Field(default=None)

    # Attributes
    rationale: str | None = Field(default=None)
    state: FocusScopeRequestStatus = Field(default=FocusScopeRequestStatus.pending)
    response_rationale: str | None = Field(default=None, description="Response")
