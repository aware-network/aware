from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.environment.experience_package import ExperiencePackage
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class ExperiencePackageDependency(BaseModel):
    """
    Experience package to Experience package dependency bridge.
    The authored `aware.experience.toml` dependency row is selector truth. The
    resolved OIG commit pin, when present, is exact reproducibility authority for
    WorkspaceRevision/Hub consumers and cross-Experience transition linking.
    """

    # Relationships
    target_experience_package: ExperiencePackage | None = Field(default=None)
    target_experience_package_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Attributes
    target_package_name: str
    target_version_number: int | None = Field(default=None)
    expected_hash_sha256: str | None = Field(default=None)
    description: str | None = Field(default=None)
