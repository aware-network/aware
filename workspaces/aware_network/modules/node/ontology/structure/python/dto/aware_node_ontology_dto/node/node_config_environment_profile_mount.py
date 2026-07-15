from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_environment_ontology_dto.environment.environment_profile_package import EnvironmentProfilePackage


class NodeConfigEnvironmentProfileMount(BaseModel):
    # Relationships
    environment_profile_package: EnvironmentProfilePackage | None = Field(default=None)

    # Attributes
    package_name: str = Field(description="Stable EnvironmentProfilePackage package name selected for install.")
    profile_key: str = Field(description="Authored EnvironmentProfileConfig key under the selected package.")
    mount_key: str = Field(description="Stable mount key under the Environment target.")
    mode: str = Field(default="mounted", description="Installation mode (`mounted`, `system`, `extension`, etc.).")
    position: int | None = Field(default=None, description="Ordered install hint.")
