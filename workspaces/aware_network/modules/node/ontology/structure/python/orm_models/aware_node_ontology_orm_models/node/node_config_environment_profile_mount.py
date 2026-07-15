from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_environment_ontology_orm_models.environment.environment_profile_package import EnvironmentProfilePackage


class NodeConfigEnvironmentProfileMount(ORMModel):
    # Relationships
    environment_profile_package: EnvironmentProfilePackage | None = Field(default=None)

    # Attributes
    package_name: str = Field(description="Stable EnvironmentProfilePackage package name selected for install.")
    profile_key: str = Field(description="Authored EnvironmentProfileConfig key under the selected package.")
    mount_key: str = Field(description="Stable mount key under the Environment target.")
    mode: str = Field(default="mounted", description="Installation mode (`mounted`, `system`, `extension`, etc.).")
    position: int | None = Field(default=None, description="Ordered install hint.")

    # Foreign Keys
    node_config_environment_target_id: UUID = Field(
        description="Foreign key for NodeConfigEnvironmentTarget.profile_mounts"
    )
    environment_profile_package_id: UUID | None = Field(
        default=None, description="Foreign key for NodeConfigEnvironmentProfileMount.environment_profile_package"
    )
