from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_environment_ontology_orm_models.environment.environment import Environment
    from aware_ontology_ontology_orm_models.ontology.ontology import Ontology


class EnvironmentOntology(ORMModel):
    """
    Runtime Environment to Ontology authority bridge.
    Contract:
    - Environment records which Ontology authorities are available in this
    runtime territory.
    - Ontology owns ObjectInstanceGraphIdentity inventory discovery.
    - This bridge must not duplicate OIG/OIGI membership.
    """

    # Relationships
    ontology: Ontology | None = Field(default=None)
    environment: Environment | None = Field(
        default=None, exclude=True, description="Reverse view for Environment.ontologies"
    )

    # Attributes
    role: str = Field(default="runtime")
    status: str = Field(default="active")
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)

    # Foreign Keys
    environment_id: UUID = Field(description="Foreign key for Environment.ontologies")
    ontology_id: UUID = Field(description="Foreign key for EnvironmentOntology.ontology")
