from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.focus.focus_scope_request import FocusScopeRequest


class ActorFocusScopeRequest(ORMModel):
    # Relationships
    focus_scope_request: FocusScopeRequest | None = Field(default=None, exclude=True)

    # Foreign Keys
    actor_focus_scope_id: UUID = Field(description="Foreign key for ActorFocusScope.requests")
    focus_scope_request_id: UUID = Field(description="Foreign key for ActorFocusScopeRequest.focus_scope_request")
