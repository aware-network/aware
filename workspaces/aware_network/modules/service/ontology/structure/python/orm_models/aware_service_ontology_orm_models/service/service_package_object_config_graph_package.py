from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.graph.config.object_config_graph_package import ObjectConfigGraphPackage
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class ServicePackageObjectConfigGraphPackage(ORMModel):
    """
    Service package to owned ObjectConfigGraphPackage bridge.
    This records OCG/state packages declared by `aware.service.toml` as Service-owned
    package surfaces. These are not package dependencies; they are part of the
    ServicePackage truth and should travel with WorkspaceRevision/Hub receipts.
    """

    # Relationships
    object_config_graph_package: ObjectConfigGraphPackage | None = Field(default=None)
    object_config_graph_package_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Attributes
    role: str = Field(default="local_state")
    manifest_relative_path: str
    package_kind: str = Field(default="state")
    expected_hash_sha256: str | None = Field(default=None)
    description: str | None = Field(default=None)

    # Foreign Keys
    service_package_id: UUID = Field(description="Foreign key for ServicePackage.object_config_graph_packages")
    object_config_graph_package_id: UUID = Field(
        description="Foreign key for ServicePackageObjectConfigGraphPackage.object_config_graph_package"
    )
    object_config_graph_package_object_instance_graph_commit_id: UUID | None = Field(
        default=None,
        description="Foreign key for ServicePackageObjectConfigGraphPackage.object_config_graph_package_object_instance_graph_commit",
    )
