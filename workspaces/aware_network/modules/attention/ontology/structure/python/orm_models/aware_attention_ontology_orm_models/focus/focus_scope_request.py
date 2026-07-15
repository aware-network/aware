from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Attention Ontology Orm Models
from aware_attention_ontology_orm_models.focus.focus_enums import FocusScopeRequestStatus

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.focus.focus import Focus
    from aware_attention_ontology_orm_models.focus.focus_scope_request_response import FocusScopeRequestResponse


class FocusScopeRequest(ORMModel):
    # Relationships
    focus: Focus | None = Field(default=None, exclude=True)
    response: FocusScopeRequestResponse | None = Field(default=None, exclude=True)

    # Attributes
    rationale: str | None = Field(default=None)
    state: FocusScopeRequestStatus = Field(default=FocusScopeRequestStatus.pending)
    response_rationale: str | None = Field(default=None, description="Response")

    # Foreign Keys
    focus_scope_id: UUID = Field(description="Foreign key for FocusScope.requests")
    focus_id: UUID = Field(description="Foreign key for FocusScopeRequest.focus")
