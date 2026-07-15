from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_interface_ontology_dto.interface.interface_config import InterfaceConfig


class NodeConfigInterfaceTarget(BaseModel):
    # Relationships
    interface_config: InterfaceConfig | None = Field(default=None)

    # Attributes
    interface_name: str
