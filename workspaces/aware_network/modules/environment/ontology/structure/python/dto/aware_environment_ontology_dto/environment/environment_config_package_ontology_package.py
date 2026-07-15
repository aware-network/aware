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


class EnvironmentConfigPackageOntologyPackage(BaseModel):
    # Relationships
    ontology_package: OntologyPackage | None = Field(default=None)
    ontology_package_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Attributes
    fqn_prefix: str
    name: str
