from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Network Ontology
from aware_network_ontology.network.network_stream_enums import NetworkStreamControl

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology.function.function_call import FunctionCall
    from aware_network_ontology.network.network_stream import NetworkStream


class NetworkStreamFrame(ORMModel):
    # Relationships
    network_stream: NetworkStream | None = Field(default=None, exclude=True)
    function_call: FunctionCall | None = Field(default=None, exclude=True)

    # Attributes
    ack_seq: int | None = Field(default=None)
    control: NetworkStreamControl = Field(default=NetworkStreamControl.data)
    seq: int

    # Foreign Keys
    network_stream_id: UUID = Field(description="Foreign key for NetworkStreamFrame.network_stream")
    function_call_id: UUID | None = Field(default=None, description="Foreign key for NetworkStreamFrame.function_call")


FUNCTIONS = {
    "NetworkStreamFrame": {},
}

__all__ = [
    "NetworkStreamFrame",
    "FUNCTIONS",
]
