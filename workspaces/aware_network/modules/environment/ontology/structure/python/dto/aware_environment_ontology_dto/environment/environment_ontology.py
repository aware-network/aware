from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_environment_ontology_dto.environment.environment import Environment
    from aware_ontology_ontology_dto.ontology.ontology import Ontology


class EnvironmentOntology(BaseModel):
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
    environment: Environment | None = Field(default=None, description="Reverse view for Environment.ontologies")

    # Attributes
    role: str = Field(default="runtime")
    status: str = Field(default="active")
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
