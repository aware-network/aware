from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Network Ontology Dto
from aware_network_ontology_dto.network.network_stream_enums import NetworkStreamControl

if TYPE_CHECKING:
    from aware_meta_ontology_dto.function.function_call import FunctionCall
    from aware_network_ontology_dto.network.network_stream import NetworkStream


class NetworkStreamFrame(BaseModel):
    # Relationships
    network_stream: NetworkStream | None = Field(default=None)
    function_call: FunctionCall | None = Field(default=None)

    # Attributes
    ack_seq: int | None = Field(default=None)
    control: NetworkStreamControl = Field(default=NetworkStreamControl.data)
    seq: int
