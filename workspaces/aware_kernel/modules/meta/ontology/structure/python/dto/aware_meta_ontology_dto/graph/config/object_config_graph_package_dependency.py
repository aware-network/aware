from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_history_ontology_dto.version.version import Version
    from aware_meta_ontology_dto.graph.config.object_config_graph_package import ObjectConfigGraphPackage


class ObjectConfigGraphPackageDependency(BaseModel):
    """
    A direct dependency of an ObjectConfigGraphPackage.
    Dependencies are commit-pinned to make the dependency universe explicit and
    cross-OCG linking deterministic.
    """

    # Relationships
    target_object_config_graph_package: ObjectConfigGraphPackage | None = Field(
        default=None, description="Target package that is depended on (canonical DAG edge: package -> package)."
    )
    target_version: Version | None = Field(
        default=None,
        description="Optional version pin for the dependency package.\nThis is the canonical, human-facing pin. It may be null during local development\n(DAG is still determinable via target package identity). The lockfile will later\nmake this concrete.",
    )
    object_config_graph_package: ObjectConfigGraphPackage | None = Field(
        default=None, description="Reverse view for ObjectConfigGraphPackage.dependencies"
    )
