from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_experience_service_dto.experience.environment_profile.models import ExperienceEnvironmentProfileSpec
    from aware_experience_service_dto.experience.environment_profile.models import (
        ExperienceEnvironmentProfileTopologySeedSpec,
    )


class ExperienceThreadLayoutEnvironmentTarget(BaseModel):
    """
    Config-level Experience resolution DTOs for semantic Thread-Layout intent.
    Ownership:
    - Experience owns semantic intent, config targets, access requirements, view mappings, and evidence.
    - Environment owns runtime process/thread/layout activation from this receipt.
    - Attention owns focus/window application after runtime activation.
    """

    # Attributes
    environment_id: UUID | None = Field(default=None)
    environment_handle: str | None = Field(default=None)
    environment_selector: str | None = Field(default=None)


class ExperienceThreadLayoutConfigTarget(BaseModel):
    # Attributes
    process_key: str | None = Field(default=None)
    process_config_id: UUID | None = Field(default=None)
    thread_key: str | None = Field(default=None)
    thread_config_id: UUID | None = Field(default=None)
    layout_key: str | None = Field(default=None)
    layout_config_id: UUID | None = Field(default=None)
    interface_package_id: UUID | None = Field(default=None)
    interface_package_name: str | None = Field(default=None)
    window_key: str = Field(default="main")


class ExperienceThreadLayoutSectionViewMapping(BaseModel):
    # Attributes
    section_key: str
    layout_section_config_id: UUID | None = Field(default=None)
    projection_experience_name: str | None = Field(default=None)
    view_key: str | None = Field(default=None)
    view_ref: str | None = Field(default=None)
    section_graph_binding_key: str | None = Field(default=None)
    observable_id: UUID | None = Field(default=None)
    representation_id: UUID | None = Field(default=None)
    is_default: bool = Field(default=False)
    intent: str | None = Field(default=None)


class ExperienceThreadLayoutAccessRequirement(BaseModel):
    # Attributes
    access_scope: str = Field(default="shared")
    role_config_id: UUID | None = Field(default=None)
    role_config_name: str | None = Field(default=None)
    class_instance_identity_required: bool = Field(default=False)
    role_assignment_binding_required: bool = Field(default=False)


class ExperienceThreadLayoutEnvironmentActivation(BaseModel):
    # Attributes
    profile: ExperienceEnvironmentProfileSpec = Field(
        description="Declarative EnvironmentExperience profile the Environment runtime should upsert before provisioning."
    )
    topology_seeds: list[ExperienceEnvironmentProfileTopologySeedSpec] = Field(
        default_factory=list, description="Runtime topology seeds owned by the resolved Experience profile."
    )
    topology_seed_key: str | None = Field(
        default=None, description="Seed selected for the immediate Thread/Layout provision step."
    )


class ExperienceThreadLayoutIntentResolution(BaseModel):
    # Attributes
    experience_name: str
    profile_key: str | None = Field(default=None)
    intent_key: str
    environment: ExperienceThreadLayoutEnvironmentTarget | None = Field(default=None)
    target: ExperienceThreadLayoutConfigTarget
    sections: list[ExperienceThreadLayoutSectionViewMapping] = Field(default_factory=list)
    default_section_key: str | None = Field(default=None)
    default_focus_key: str | None = Field(default=None)
    access_requirement: ExperienceThreadLayoutAccessRequirement | None = Field(default=None)
    environment_activation: ExperienceThreadLayoutEnvironmentActivation | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)
