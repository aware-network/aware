from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_node_ontology_orm_models.node.node_config_service_code_package import NodeConfigServiceCodePackage
    from aware_service_ontology_orm_models.service.service_config import ServiceConfig


class NodeConfigServiceTarget(ORMModel):
    # Relationships
    service_config: ServiceConfig | None = Field(default=None)
    code_packages: list[NodeConfigServiceCodePackage] = Field(default_factory=list)

    # Attributes
    service_name: str

    # Foreign Keys
    node_config_id: UUID = Field(description="Foreign key for NodeConfig.service_targets")
    service_config_id: UUID | None = Field(
        default=None, description="Foreign key for NodeConfigServiceTarget.service_config"
    )
