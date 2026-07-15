from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.attribute.attribute import Attribute
    from aware_meta_ontology_dto.class_.class_instance_identity import ClassInstanceIdentity
    from aware_meta_ontology_dto.function.function_call_response_attribute import FunctionCallResponseAttribute
    from aware_meta_ontology_dto.function.function_call_response_commit import FunctionCallResponseCommit
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class FunctionCallResponse(BaseModel):
    # Relationships
    root_class_instance_identity: ClassInstanceIdentity | None = Field(default=None)

    # Attributes
    graph_hash_post: str | None = Field(default=None)
    error_message: str | None = Field(default=None)
    execution_time_ms: int = Field(default=0)
    success: bool = Field(default=True)
