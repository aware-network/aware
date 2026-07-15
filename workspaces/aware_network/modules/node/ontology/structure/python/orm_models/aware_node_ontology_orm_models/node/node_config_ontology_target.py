from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_ontology_ontology_orm_models.ontology.ontology_package import OntologyPackage


class NodeConfigOntologyTarget(ORMModel):
    # Relationships
    ontology_package: OntologyPackage | None = Field(default=None)

    # Attributes
    package_name: str

    # Foreign Keys
    node_config_id: UUID = Field(description="Foreign key for NodeConfig.ontology_targets")
    ontology_package_id: UUID | None = Field(
        default=None, description="Foreign key for NodeConfigOntologyTarget.ontology_package"
    )
