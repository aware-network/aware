from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_history_ontology.version.version import Version
    from aware_meta_ontology.graph.config.object_config_graph_package import ObjectConfigGraphPackage


class ObjectConfigGraphPackageDependency(ORMModel):
    """
    A direct dependency of an ObjectConfigGraphPackage.
    Dependencies are commit-pinned to make the dependency universe explicit and
    cross-OCG linking deterministic.
    """

    # Relationships
    target_object_config_graph_package: ObjectConfigGraphPackage | None = Field(
        default=None,
        exclude=True,
        description="Target package that is depended on (canonical DAG edge: package -> package).",
    )
    target_version: Version | None = Field(
        default=None,
        description="Optional version pin for the dependency package.\nThis is the canonical, human-facing pin. It may be null during local development\n(DAG is still determinable via target package identity). The lockfile will later\nmake this concrete.",
    )
    object_config_graph_package: ObjectConfigGraphPackage | None = Field(
        default=None, exclude=True, description="Reverse view for ObjectConfigGraphPackage.dependencies"
    )

    # Foreign Keys
    object_config_graph_package_id: UUID = Field(description="Foreign key for ObjectConfigGraphPackage.dependencies")
    target_object_config_graph_package_id: UUID = Field(
        description="Foreign key for ObjectConfigGraphPackageDependency.target_object_config_graph_package"
    )
    target_version_id: UUID | None = Field(
        default=None, description="Foreign key for ObjectConfigGraphPackageDependency.target_version"
    )


FUNCTIONS = {
    "ObjectConfigGraphPackageDependency": {},
}

__all__ = [
    "ObjectConfigGraphPackageDependency",
    "FUNCTIONS",
]
