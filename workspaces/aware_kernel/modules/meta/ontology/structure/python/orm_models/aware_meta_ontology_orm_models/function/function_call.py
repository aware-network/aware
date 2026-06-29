from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.attribute.attribute import Attribute
    from aware_meta_ontology_orm_models.class_.class_instance_identity import ClassInstanceIdentity
    from aware_meta_ontology_orm_models.function.function_call_argument import FunctionCallArgument
    from aware_meta_ontology_orm_models.function.function_call_response import FunctionCallResponse
    from aware_meta_ontology_orm_models.function.function_config import FunctionConfig
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class FunctionCall(ORMModel):
    # Relationships
    function_config: FunctionConfig | None = Field(default=None)
    target_class_instance_identity: ClassInstanceIdentity | None = Field(default=None)
    base_commit: ObjectInstanceGraphCommit | None = Field(default=None)
    function_call_response: FunctionCallResponse | None = Field(default=None)

    # Attributes
    call_key: UUID
    graph_hash_pre: str | None = Field(default=None)

    # Foreign Keys
    object_instance_graph_lane_id: UUID = Field(description="Foreign key for ObjectInstanceGraphLane.function_calls")
    function_config_id: UUID = Field(description="Foreign key for FunctionCall.function_config")
    target_class_instance_identity_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionCall.target_class_instance_identity"
    )
    base_commit_id: UUID | None = Field(default=None, description="Foreign key for FunctionCall.base_commit")

    # Edges
    function_call_arguments: list[FunctionCallArgument] = Field(
        default_factory=list, description="Edge association helper for attributes"
    )

    @property
    def attributes(self) -> list[Attribute]:
        return [edge.attribute for edge in self.function_call_arguments if edge.attribute is not None]
