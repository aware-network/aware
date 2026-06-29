from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit
    from aware_sdk_ontology_orm_models.sdk.sdk_package import SdkPackage


class SdkPackageDependency(ORMModel):
    """
    SDK package to SDK package dependency bridge.
    The authored `aware.sdk.toml` dependency row is selector truth. The resolved
    OIG commit pin, when present, is exact reproducibility authority for Hub and
    WorkspaceRevision consumers.
    """

    # Relationships
    target_sdk_package: SdkPackage | None = Field(default=None)
    target_sdk_package_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Attributes
    target_package_name: str
    target_version_number: int | None = Field(default=None)
    expected_hash_sha256: str | None = Field(default=None)
    description: str | None = Field(default=None)

    # Foreign Keys
    sdk_package_id: UUID = Field(description="Foreign key for SdkPackage.sdk_package_dependencies")
    target_sdk_package_id: UUID = Field(description="Foreign key for SdkPackageDependency.target_sdk_package")
    target_sdk_package_object_instance_graph_commit_id: UUID | None = Field(
        default=None, description="Foreign key for SdkPackageDependency.target_sdk_package_object_instance_graph_commit"
    )
