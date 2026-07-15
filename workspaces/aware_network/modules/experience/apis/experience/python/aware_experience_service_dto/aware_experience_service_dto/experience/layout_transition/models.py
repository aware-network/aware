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
    from aware_experience_service_dto.experience.section_graph_binding.models import ExperienceSectionGraphBindingState


class ExperienceInterfaceWindowLayoutTarget(BaseModel):
    """
    Canonical DTOs for Experience-owned layout transitions.
    Ownership:
    - Attention owns layout, section, focus, and observable truth consumed by Interface.
    - Experience API owns which product layout target should be requested for one experience moment.
    - Interface owns the protected namespace/window/session mutation.
    """

    # Attributes
    interface_package_id: UUID | None = Field(default=None)
    interface_package_name: str | None = Field(default=None)
    window_key: str = Field(default="main")
    layout_config_id: UUID | None = Field(default=None)
    layout_key: str
    section_key: str | None = Field(default=None)
    observable_id: UUID | None = Field(default=None)
    representation_id: UUID | None = Field(default=None)


class ExperienceLayoutActorRoleGate(BaseModel):
    # Attributes
    access_scope: str = Field(default="personal")
    actor_id: UUID
    role_config_id: UUID | None = Field(default=None)
    role_config_name: str | None = Field(default=None)
    class_instance_identity_id: UUID
    role_assignment_binding_id: UUID | None = Field(default=None)


class ExperienceLayoutTransitionReceipt(BaseModel):
    # Attributes
    namespace: str
    actor_id: UUID
    identity_id: UUID | None = Field(default=None)
    experience_name: str
    intent_key: str
    target: ExperienceInterfaceWindowLayoutTarget
    role_gate: ExperienceLayoutActorRoleGate
    section_graph_binding_key: str | None = Field(default=None)
    attention_state: ExperienceSectionGraphBindingState | None = Field(default=None)
    interface_idempotency_key: str | None = Field(default=None)
    info: str | None = Field(default=None)
