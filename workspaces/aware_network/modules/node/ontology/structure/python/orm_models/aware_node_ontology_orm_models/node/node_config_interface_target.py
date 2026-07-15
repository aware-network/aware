from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_interface_ontology_orm_models.interface.interface_config import InterfaceConfig


class NodeConfigInterfaceTarget(ORMModel):
    # Relationships
    interface_config: InterfaceConfig | None = Field(default=None)

    # Attributes
    interface_name: str

    # Foreign Keys
    node_config_id: UUID = Field(description="Foreign key for NodeConfig.interface_targets")
    interface_config_id: UUID | None = Field(
        default=None, description="Foreign key for NodeConfigInterfaceTarget.interface_config"
    )
