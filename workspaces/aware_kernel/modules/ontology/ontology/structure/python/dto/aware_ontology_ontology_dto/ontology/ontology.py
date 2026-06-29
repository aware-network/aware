from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_identity import ObjectInstanceGraphIdentity
    from aware_ontology_ontology_dto.ontology.ontology_config import OntologyConfig


class Ontology(BaseModel):
    """
    Concrete ontology authority/worldline.
    `Ontology` is the instance/runtime layer materialized under
    `OntologyConfig.ontologies`; it indexes the ObjectInstanceGraphIdentity
    worldlines that exist under this ontology authority.
    """

    # Relationships
    object_instance_graph_identities: list[ObjectInstanceGraphIdentity] = Field(default_factory=list)
    ontology_config: OntologyConfig | None = Field(
        default=None, description="Reverse view for OntologyConfig.ontologies"
    )

    # Attributes
    description: str | None = Field(default=None)
    key: str
    status: str = Field(default="active")
    title: str | None = Field(default=None)
