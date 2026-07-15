from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_ontology_ontology_dto.ontology.ontology_package import OntologyPackage


class NodeConfigOntologyTarget(BaseModel):
    # Relationships
    ontology_package: OntologyPackage | None = Field(default=None)

    # Attributes
    package_name: str
