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


class ServicePackageOntologyPackage(BaseModel):
    """
    Service package to required OntologyPackage bridge.
    This records ontology packages a ServicePackage must consume through a
    Service-owned replica. The bridge is package truth so WorkspaceRevision and
    Hub consumers can reproduce required ontology replica inputs without reading
    local authoring manifests.
    """

    # Relationships
    ontology_package: OntologyPackage | None = Field(default=None)
    ontology_package_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Attributes
    role: str = Field(default="replica")
    requirement_mode: str = Field(default="required")
    package_name: str
    fqn_prefix: str
    expected_hash_sha256: str | None = Field(default=None)
    description: str | None = Field(default=None)
