from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel


class FocusScopeRequestResponse(ORMModel):
    # Attributes
    success: bool
    message: str | None = Field(default=None)

    # Foreign Keys
    focus_scope_request_id: UUID | None = Field(default=None, description="Foreign key for FocusScopeRequest.response")
