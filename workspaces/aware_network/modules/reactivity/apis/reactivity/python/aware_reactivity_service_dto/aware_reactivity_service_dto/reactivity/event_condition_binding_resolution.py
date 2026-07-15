from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_reactivity_service_dto.reactivity.event_action_binding import EventActionBinding


class EventConditionBindingResolution(BaseModel):
    """
    Canonical DTO for condition-binding resolution used by receipt evaluators.
    Ownership:
    - Reactivity API owns cross-module binding contracts.
    - Runtime and node rails consume this DTO as the typed boundary.
    """

    # Attributes
    id: UUID
    event_config_id: UUID
    condition_config_id: UUID
    is_enabled: bool
    continue_on_fail: bool
    is_required: bool
    scoped_class_instance_identity_ids: list[UUID] = Field(
        default_factory=list,
        description="Optional instance-scope filters loaded from EventConfigConditionConfigScope.\nContract:\n- Empty means the binding keeps existing lane-level behavior.\n- Non-empty means the condition evaluator intersects commit trigger\ncandidate ids with this set before evaluating class/attribute policy.\n- Values are Meta ClassInstanceIdentity ids. This DTO never references\nExperience graph-binding objects.",
    )
    action_bindings: list[EventActionBinding] = Field(default_factory=list)
