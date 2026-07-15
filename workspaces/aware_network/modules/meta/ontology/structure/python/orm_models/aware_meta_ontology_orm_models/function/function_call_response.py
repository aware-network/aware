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
    from aware_meta_ontology_orm_models.function.function_call_response_attribute import FunctionCallResponseAttribute
    from aware_meta_ontology_orm_models.function.function_call_response_commit import FunctionCallResponseCommit
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class FunctionCallResponse(ORMModel):
    # Relationships
    root_class_instance_identity: ClassInstanceIdentity | None = Field(default=None)

    # Attributes
    graph_hash_post: str | None = Field(default=None)
    error_message: str | None = Field(default=None)
    execution_time_ms: int = Field(default=0)
    success: bool = Field(default=True)

    # Foreign Keys
    function_call_id: UUID = Field(description="Foreign key for FunctionCall.function_call_response")
    root_class_instance_identity_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionCallResponse.root_class_instance_identity"
    )

    # Edges
    function_call_response_attributes: list[FunctionCallResponseAttribute] = Field(
        default_factory=list, description="Edge association helper for attributes"
    )
    function_call_response_commits: list[FunctionCallResponseCommit] = Field(
        default_factory=list, description="Edge association helper for commits"
    )

    @property
    def attributes(self) -> list[Attribute]:
        return [edge.attribute for edge in self.function_call_response_attributes if edge.attribute is not None]

    @property
    def commits(self) -> list[ObjectInstanceGraphCommit]:
        return [
            edge.object_instance_graph_commit
            for edge in self.function_call_response_commits
            if edge.object_instance_graph_commit is not None
        ]
