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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_meta_ontology.attribute.attribute import Attribute
    from aware_meta_ontology.class_.class_instance_identity import ClassInstanceIdentity
    from aware_meta_ontology.function.function_call_argument import FunctionCallArgument
    from aware_meta_ontology.function.function_call_response import FunctionCallResponse
    from aware_meta_ontology.function.function_config import FunctionConfig
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


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

    async def create_response(
        self,
        success: bool = True,
        error_message: str | None = None,
        execution_time_ms: int = 0,
        graph_hash_post: str | None = None,
        root_class_instance_identity_id: UUID | None = None,
    ) -> FunctionCallResponse:
        payload = {
            "success": success,
            "error_message": error_message,
            "execution_time_ms": execution_time_ms,
            "graph_hash_post": graph_hash_post,
            "root_class_instance_identity_id": root_class_instance_identity_id,
        }
        result = await invoke_instance(orm_model=self, function_name="create_response", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.function.function_call_response import FunctionCallResponse

        if isinstance(value, FunctionCallResponse):
            return value
        return FunctionCallResponse.validate_invocation_value(value)

    @classmethod
    async def build_via_object_instance_graph_lane(
        cls,
        object_instance_graph_lane_id: UUID,
        call_key: UUID,
        function_config_id: UUID,
        target_class_instance_identity_id: UUID | None = None,
        base_commit_id: UUID | None = None,
        graph_hash_pre: str | None = None,
    ) -> FunctionCall:
        """
        Build one durable FunctionCall envelope under an ObjectInstanceGraphLane.

        Contract:
        - Parent ObjectInstanceGraphLane ownership is propagated by traversal lowering.
        - `call_key` is the per-invocation identity and is required.
        - `function_config` is execution contract truth.
        - `target_class_instance_identity` is null for constructor calls until
          response materialization identifies the created root identity.
        """

        payload = {
            "object_instance_graph_lane_id": object_instance_graph_lane_id,
            "call_key": call_key,
            "function_config_id": function_config_id,
            "target_class_instance_identity_id": target_class_instance_identity_id,
            "base_commit_id": base_commit_id,
            "graph_hash_pre": graph_hash_pre,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_object_instance_graph_lane", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FunctionCall):
            return value
        return FunctionCall.validate_invocation_value(value)


class FunctionCallCreateResponseInput(BaseModel):
    success: bool = Field(default=True)
    error_message: str | None = Field(default=None)
    execution_time_ms: int = Field(default=0)
    graph_hash_post: str | None = Field(default=None)
    root_class_instance_identity_id: UUID | None = Field(default=None)


class FunctionCallCreateResponseOutput(BaseModel):
    value: FunctionCallResponse


class FunctionCallBuildViaObjectInstanceGraphLaneInput(BaseModel):
    object_instance_graph_lane_id: UUID = Field(description="Foreign key for ObjectInstanceGraphLane.function_calls")
    call_key: UUID
    function_config_id: UUID
    target_class_instance_identity_id: UUID | None = Field(default=None)
    base_commit_id: UUID | None = Field(default=None)
    graph_hash_pre: str | None = Field(default=None)


class FunctionCallBuildViaObjectInstanceGraphLaneOutput(BaseModel):
    value: FunctionCall


FUNCTIONS = {
    "FunctionCall": {
        "create_response": {
            "canonical": {"name": "create_response", "description": None, "is_constructor": False},
            "input": FunctionCallCreateResponseInput,
            "output": FunctionCallCreateResponseOutput,
        },
        "build_via_object_instance_graph_lane": {
            "canonical": {
                "name": "build_via_object_instance_graph_lane",
                "description": "Build one durable FunctionCall envelope under an ObjectInstanceGraphLane.\n\nContract:\n- Parent ObjectInstanceGraphLane ownership is propagated by traversal lowering.\n- `call_key` is the per-invocation identity and is required.\n- `function_config` is execution contract truth.\n- `target_class_instance_identity` is null for constructor calls until\n  response materialization identifies the created root identity.",
                "is_constructor": True,
            },
            "input": FunctionCallBuildViaObjectInstanceGraphLaneInput,
            "output": FunctionCallBuildViaObjectInstanceGraphLaneOutput,
        },
    },
}

__all__ = [
    "FunctionCall",
    "FunctionCallCreateResponseInput",
    "FunctionCallCreateResponseOutput",
    "FunctionCallBuildViaObjectInstanceGraphLaneInput",
    "FunctionCallBuildViaObjectInstanceGraphLaneOutput",
    "FUNCTIONS",
]
