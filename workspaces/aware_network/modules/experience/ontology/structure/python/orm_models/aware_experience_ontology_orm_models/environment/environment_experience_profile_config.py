from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_environment_ontology_orm_models.environment.environment_profile_config import EnvironmentProfileConfig
    from aware_environment_ontology_orm_models.environment.environment_provider_grant import EnvironmentProviderGrant
    from aware_experience_ontology_orm_models.environment.environment_experience_actor import (
        EnvironmentExperienceActorConfig,
    )
    from aware_experience_ontology_orm_models.environment.environment_experience_event import EnvironmentExperienceEvent
    from aware_experience_ontology_orm_models.environment.environment_experience_process_config import (
        EnvironmentExperienceProcessConfig,
    )
    from aware_experience_ontology_orm_models.environment.environment_experience_projection import (
        EnvironmentExperienceProjection,
    )
    from aware_experience_ontology_orm_models.environment.environment_experience_view_event_transition import (
        EnvironmentExperienceViewEventTransition,
    )
    from aware_storage_ontology_orm_models.blob.storage_blob import StorageBlob


class EnvironmentExperienceProfileConfig(ORMModel):
    """
    Reusable Experience policy/config over one Environment EnvironmentProfileConfig.
    Purpose:
    - Bind Experience actor, projection, event, and policy semantics to stable
    Environment Environment topology config.
    - Keep EnvironmentProfileConfig/ProcessConfig/ThreadConfig construction in
    Environment while Experience config declares how it participates.
    Contract:
    - This object references Environment EnvironmentProfileConfig and optional
    EnvironmentProviderGrant truth.
    - It never constructs Environment topology config or applied EnvironmentProfile state.
    - Process/thread participation is represented by Experience config bridge
    objects keyed to Environment ProcessConfig/ThreadConfig.
    """

    # Relationships
    environment_profile_config: EnvironmentProfileConfig | None = Field(default=None, exclude=True)
    environment_provider_grant: EnvironmentProviderGrant | None = Field(default=None, exclude=True)
    actors: list[EnvironmentExperienceActorConfig] = Field(default_factory=list, exclude=True)
    experiences: list[EnvironmentExperienceProjection] = Field(default_factory=list, exclude=True)
    events: list[EnvironmentExperienceEvent] = Field(default_factory=list, exclude=True)
    view_event_transitions: list[EnvironmentExperienceViewEventTransition] = Field(
        default_factory=list,
        exclude=True,
        description="Experience-owned View -> Event -> View transition policies.\nContract:\n- The target is always a ProjectionExperienceSectionGraphBinding.\n- Attention focus is reached only through that binding, never directly here.",
    )
    process_configs: list[EnvironmentExperienceProcessConfig] = Field(default_factory=list, exclude=True)
    image: StorageBlob | None = Field(
        default=None,
        exclude=True,
        description="Optional experience-level image used as a default for territory surfaces.\nContract:\n- Image bytes are uploaded out-of-band (data-plane).\n- Commits reference StorageBlob metadata only.",
    )

    # Attributes
    description: str | None = Field(default=None)
    narrative: str | None = Field(
        default=None, description="Canonical experience-level narrative used by experience selection and AI context."
    )
    key: str = Field(description="Stable profile key (recommended: `control.default`, `coordination.default`, etc).")
    title: str | None = Field(default=None)

    # Foreign Keys
    environment_experience_id: UUID = Field(description="Foreign key for EnvironmentExperience.profile_configs")
    environment_profile_config_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceProfileConfig.environment_profile_config"
    )
    environment_provider_grant_id: UUID | None = Field(
        default=None, description="Foreign key for EnvironmentExperienceProfileConfig.environment_provider_grant"
    )
    image_id: UUID | None = Field(default=None, description="Foreign key for EnvironmentExperienceProfileConfig.image")
