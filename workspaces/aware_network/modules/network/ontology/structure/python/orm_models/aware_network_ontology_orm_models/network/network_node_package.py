from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.package.code_package import CodePackage
    from aware_network_ontology_orm_models.network.network_node_config import NetworkNodeConfig


class NetworkNodePackage(ORMModel):
    # Relationships
    source_code_package: CodePackage | None = Field(default=None)
    network_node_config: NetworkNodeConfig | None = Field(default=None)

    # Attributes
    name: str

    # Foreign Keys
    source_code_package_id: UUID | None = Field(
        default=None, description="Foreign key for NetworkNodePackage.source_code_package"
    )
    network_node_config_id: UUID = Field(description="Foreign key for NetworkNodePackage.network_node_config")
