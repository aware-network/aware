from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_identity import ObjectInstanceGraphIdentity
    from aware_ontology_ontology_orm_models.ontology.ontology_config import OntologyConfig


class Ontology(ORMModel):
    """
    Concrete ontology authority/worldline.
    `Ontology` is the instance/runtime layer materialized under
    `OntologyConfig.ontologies`; it indexes the ObjectInstanceGraphIdentity
    worldlines that exist under this ontology authority.
    """

    # Relationships
    object_instance_graph_identities: list[ObjectInstanceGraphIdentity] = Field(default_factory=list)
    ontology_config: OntologyConfig | None = Field(
        default=None, exclude=True, description="Reverse view for OntologyConfig.ontologies"
    )

    # Attributes
    description: str | None = Field(default=None)
    key: str
    status: str = Field(default="active")
    title: str | None = Field(default=None)

    # Foreign Keys
    ontology_config_id: UUID = Field(description="Foreign key for OntologyConfig.ontologies")
