from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit
    from aware_ontology_ontology_dto.ontology.ontology_package import OntologyPackage


class OntologyPackageDependency(BaseModel):
    """Direct ontology package dependency bridge."""

    # Relationships
    target_ontology_package: OntologyPackage | None = Field(default=None)
    target_ontology_package_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)
    ontology_package: OntologyPackage | None = Field(
        default=None, description="Reverse view for OntologyPackage.dependencies"
    )

    # Attributes
    description: str | None = Field(default=None)
    expected_hash_sha256: str | None = Field(default=None)
    target_package_name: str
    target_version_number: int | None = Field(default=None)
