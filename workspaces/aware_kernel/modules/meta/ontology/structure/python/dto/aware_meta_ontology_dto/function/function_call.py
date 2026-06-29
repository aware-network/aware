from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.attribute.attribute import Attribute
    from aware_meta_ontology_dto.class_.class_instance_identity import ClassInstanceIdentity
    from aware_meta_ontology_dto.function.function_call_argument import FunctionCallArgument
    from aware_meta_ontology_dto.function.function_call_response import FunctionCallResponse
    from aware_meta_ontology_dto.function.function_config import FunctionConfig
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class FunctionCall(BaseModel):
    # Relationships
    function_config: FunctionConfig | None = Field(default=None)
    target_class_instance_identity: ClassInstanceIdentity | None = Field(default=None)
    base_commit: ObjectInstanceGraphCommit | None = Field(default=None)
    function_call_response: FunctionCallResponse | None = Field(default=None)

    # Attributes
    call_key: UUID
    graph_hash_pre: str | None = Field(default=None)
