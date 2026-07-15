from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_environment_ontology_orm_models.environment.environment_config import EnvironmentConfig
    from aware_environment_ontology_orm_models.environment.environment_profile_actor_config import (
        EnvironmentProfileActorConfig,
    )
    from aware_environment_ontology_orm_models.environment.environment_provider import EnvironmentProvider
    from aware_environment_ontology_orm_models.process.process_config import ProcessConfig
    from aware_storage_ontology_orm_models.blob.storage_blob import StorageBlob


class EnvironmentProfileConfig(ORMModel):
    """
    Reusable Environment OS topology profile config.
    Contract:
    - Parent constructor is EnvironmentConfig.
    - Stable Environment topology config lives here, not in Experience and not
    under a concrete Environment instance.
    - ProcessConfig and ThreadConfig are reusable config parents.
    - EnvironmentProfile applies this config under a concrete Environment and
    owns concrete Process/Thread provenance.
    - EnvironmentSessionConfig lives at EnvironmentConfig scope; profile config
    can be referenced from session config defaults but never owns sessions.
    - Experiences attach later as approved providers through provider grants.
    """

    # Relationships
    process_configs: list[ProcessConfig] = Field(default_factory=list)
    providers: list[EnvironmentProvider] = Field(default_factory=list)
    actor_configs: list[EnvironmentProfileActorConfig] = Field(default_factory=list)
    image: StorageBlob | None = Field(
        default=None,
        exclude=True,
        description="Optional profile image used as the default for territory surfaces.\nContract:\n- Image bytes are uploaded out-of-band (data-plane).\n- Commits reference StorageBlob metadata only.",
    )
    environment_config: EnvironmentConfig | None = Field(
        default=None, exclude=True, description="Reverse view for EnvironmentConfig.profile_configs"
    )

    # Attributes
    description: str | None = Field(default=None)
    narrative: str | None = Field(
        default=None, description="Canonical environment-level narrative used by Environment selection and AI context."
    )
    key: str = Field(description="Stable profile key (recommended: `os.default`, `desktop.story`, etc).")
    title: str | None = Field(default=None)

    # Foreign Keys
    environment_config_id: UUID = Field(description="Foreign key for EnvironmentConfig.profile_configs")
    image_id: UUID | None = Field(default=None, description="Foreign key for EnvironmentProfileConfig.image")
