from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class EventActionBinding(BaseModel):
    """
    Canonical DTO for one action binding resolved from EventConfig.
    Ownership:
    - Reactivity API owns cross-module binding contracts.
    - Runtime implementations must import this DTO instead of local dataclasses.
    """

    # Attributes
    id: UUID
    action_config_id: UUID
    action_type: str | None = Field(default=None)
    execution_order: int
    priority: int
    is_enabled: bool
    is_required: bool
    continue_on_fail: bool
