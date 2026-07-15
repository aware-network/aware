from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_interface_ontology_orm_models.interface.interface_package import InterfacePackage
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class AppPackageInterfacePackage(ORMModel):
    # Relationships
    interface_package: InterfacePackage | None = Field(default=None)
    interface_package_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)
    role: str = Field(default="interface")

    # Foreign Keys
    app_package_id: UUID = Field(description="Foreign key for AppPackage.interface_packages")
    interface_package_id: UUID = Field(description="Foreign key for AppPackageInterfacePackage.interface_package")
    interface_package_object_instance_graph_commit_id: UUID | None = Field(
        default=None,
        description="Foreign key for AppPackageInterfacePackage.interface_package_object_instance_graph_commit",
    )
