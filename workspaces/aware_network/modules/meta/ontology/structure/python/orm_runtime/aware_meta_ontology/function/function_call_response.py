from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_meta_ontology.attribute.attribute import Attribute
    from aware_meta_ontology.class_.class_instance_identity import ClassInstanceIdentity
    from aware_meta_ontology.function.function_call_response_attribute import FunctionCallResponseAttribute
    from aware_meta_ontology.function.function_call_response_commit import FunctionCallResponseCommit
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


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

    @classmethod
    async def build_via_function_call(
        cls,
        function_call_id: UUID,
        success: bool = True,
        error_message: str | None = None,
        execution_time_ms: int = 0,
        graph_hash_post: str | None = None,
        root_class_instance_identity_id: UUID | None = None,
    ) -> FunctionCallResponse:
        """Build a deterministic response envelope under a FunctionCall scope."""

        payload = {
            "function_call_id": function_call_id,
            "success": success,
            "error_message": error_message,
            "execution_time_ms": execution_time_ms,
            "graph_hash_post": graph_hash_post,
            "root_class_instance_identity_id": root_class_instance_identity_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_function_call", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FunctionCallResponse):
            return value
        return FunctionCallResponse.validate_invocation_value(value)


class FunctionCallResponseBuildViaFunctionCallInput(BaseModel):
    function_call_id: UUID = Field(description="Foreign key for FunctionCall.function_call_response")
    success: bool = Field(default=True)
    error_message: str | None = Field(default=None)
    execution_time_ms: int = Field(default=0)
    graph_hash_post: str | None = Field(default=None)
    root_class_instance_identity_id: UUID | None = Field(default=None)


class FunctionCallResponseBuildViaFunctionCallOutput(BaseModel):
    value: FunctionCallResponse


FUNCTIONS = {
    "FunctionCallResponse": {
        "build_via_function_call": {
            "canonical": {
                "name": "build_via_function_call",
                "description": "Build a deterministic response envelope under a FunctionCall scope.",
                "is_constructor": True,
            },
            "input": FunctionCallResponseBuildViaFunctionCallInput,
            "output": FunctionCallResponseBuildViaFunctionCallOutput,
        },
    },
}

__all__ = [
    "FunctionCallResponse",
    "FunctionCallResponseBuildViaFunctionCallInput",
    "FunctionCallResponseBuildViaFunctionCallOutput",
    "FUNCTIONS",
]
