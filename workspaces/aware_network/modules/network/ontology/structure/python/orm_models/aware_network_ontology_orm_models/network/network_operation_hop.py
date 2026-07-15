from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Network Ontology Orm Models
from aware_network_ontology_orm_models.network.network_enums import NetworkAppType

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_environment_ontology_orm_models.environment.environment import Environment
    from aware_network_ontology_orm_models.network.network_node import NetworkNode


class NetworkOperationHop(ORMModel):
    # Relationships
    source_environment: Environment | None = Field(default=None, exclude=True)
    source_node: NetworkNode | None = Field(default=None, exclude=True)
    target_environment: Environment | None = Field(default=None, exclude=True)
    target_node: NetworkNode | None = Field(default=None, exclude=True)

    # Attributes
    source_interface_id: UUID | None = Field(default=None)
    target_interface_id: UUID | None = Field(default=None)
    hop_index: int
    source_app_type: NetworkAppType
    target_app_type: NetworkAppType

    # Foreign Keys
    network_operation_id: UUID = Field(description="Foreign key for NetworkOperation.network_operation_hops")
    source_environment_id: UUID | None = Field(
        default=None, description="Foreign key for NetworkOperationHop.source_environment"
    )
    source_node_id: UUID | None = Field(default=None, description="Foreign key for NetworkOperationHop.source_node")
    target_environment_id: UUID | None = Field(
        default=None, description="Foreign key for NetworkOperationHop.target_environment"
    )
    target_node_id: UUID | None = Field(default=None, description="Foreign key for NetworkOperationHop.target_node")
