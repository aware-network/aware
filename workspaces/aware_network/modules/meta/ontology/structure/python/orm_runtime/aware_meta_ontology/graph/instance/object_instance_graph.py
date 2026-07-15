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
    from aware_meta_ontology.class_.class_instance import ClassInstance
    from aware_meta_ontology.class_.class_instance_relationship import ClassInstanceRelationship


class ObjectInstanceGraph(ORMModel):
    # Relationships
    root_class_instance: ClassInstance
    class_instances: list[ClassInstance] = Field(default_factory=list)
    class_instance_relationships: list[ClassInstanceRelationship] = Field(default_factory=list)

    # Attributes
    key: str
    name: str
    description: str | None = Field(default=None)
    hash: str

    # Foreign Keys
    object_projection_graph_id: UUID = Field(description="Foreign key for ObjectProjectionGraph.object_instance_graphs")
    root_class_instance_id: UUID | None = Field(
        default=None, description="Foreign key for ObjectInstanceGraph.root_class_instance"
    )

    async def create_class_instance(self, class_config_id: UUID, source_object_id: UUID) -> ClassInstance:
        """
        Create deterministic ClassInstance under this ObjectInstanceGraph.

        Contract:
        - Parent ObjectInstanceGraph identity is propagated by constructor lowering.
        - The child ClassInstance stable id must resolve from
          `(object_instance_graph_id via path, class_config_id, source_object_id)`.
        """

        payload = {"class_config_id": class_config_id, "source_object_id": source_object_id}
        result = await invoke_instance(orm_model=self, function_name="create_class_instance", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.class_.class_instance import ClassInstance

        if isinstance(value, ClassInstance):
            return value
        return ClassInstance.validate_invocation_value(value)

    @classmethod
    async def build_via_object_projection_graph(
        cls,
        object_projection_graph_id: UUID,
        key: str,
        root_class_config_id: UUID,
        root_source_object_id: UUID,
        name: str,
        description: str | None = None,
        hash: str = "",
    ) -> ObjectInstanceGraph:
        """
        Create deterministic ObjectInstanceGraph under one ObjectProjectionGraph.

        Contract:
        - Parent `object_projection_graph_id` is propagated by constructor lowering.
        - Identity resolves from `(object_projection_graph_id via path, key)`.
        - Root ClassInstance is created eagerly from `(root_class_config_id, root_source_object_id)`.
        - Empty OIGs are not allowed.
        - `name` is mutable payload metadata and must not participate in stable identity.
        - `hash` is snapshot metadata and must not participate in stable identity.
        """

        payload = {
            "object_projection_graph_id": object_projection_graph_id,
            "key": key,
            "root_class_config_id": root_class_config_id,
            "root_source_object_id": root_source_object_id,
            "name": name,
            "description": description,
            "hash": hash,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_object_projection_graph", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ObjectInstanceGraph):
            return value
        return ObjectInstanceGraph.validate_invocation_value(value)


class ObjectInstanceGraphCreateClassInstanceInput(BaseModel):
    class_config_id: UUID
    source_object_id: UUID


class ObjectInstanceGraphCreateClassInstanceOutput(BaseModel):
    value: ClassInstance


class ObjectInstanceGraphBuildViaObjectProjectionGraphInput(BaseModel):
    object_projection_graph_id: UUID = Field(description="Foreign key for ObjectProjectionGraph.object_instance_graphs")
    key: str
    root_class_config_id: UUID
    root_source_object_id: UUID
    name: str
    description: str | None = Field(default=None)
    hash: str = Field(default="")


class ObjectInstanceGraphBuildViaObjectProjectionGraphOutput(BaseModel):
    value: ObjectInstanceGraph


FUNCTIONS = {
    "ObjectInstanceGraph": {
        "create_class_instance": {
            "canonical": {
                "name": "create_class_instance",
                "description": "Create deterministic ClassInstance under this ObjectInstanceGraph.\n\nContract:\n- Parent ObjectInstanceGraph identity is propagated by constructor lowering.\n- The child ClassInstance stable id must resolve from\n  `(object_instance_graph_id via path, class_config_id, source_object_id)`.",
                "is_constructor": False,
            },
            "input": ObjectInstanceGraphCreateClassInstanceInput,
            "output": ObjectInstanceGraphCreateClassInstanceOutput,
        },
        "build_via_object_projection_graph": {
            "canonical": {
                "name": "build_via_object_projection_graph",
                "description": "Create deterministic ObjectInstanceGraph under one ObjectProjectionGraph.\n\nContract:\n- Parent `object_projection_graph_id` is propagated by constructor lowering.\n- Identity resolves from `(object_projection_graph_id via path, key)`.\n- Root ClassInstance is created eagerly from `(root_class_config_id, root_source_object_id)`.\n- Empty OIGs are not allowed.\n- `name` is mutable payload metadata and must not participate in stable identity.\n- `hash` is snapshot metadata and must not participate in stable identity.",
                "is_constructor": True,
            },
            "input": ObjectInstanceGraphBuildViaObjectProjectionGraphInput,
            "output": ObjectInstanceGraphBuildViaObjectProjectionGraphOutput,
        },
    },
}

__all__ = [
    "ObjectInstanceGraph",
    "ObjectInstanceGraphCreateClassInstanceInput",
    "ObjectInstanceGraphCreateClassInstanceOutput",
    "ObjectInstanceGraphBuildViaObjectProjectionGraphInput",
    "ObjectInstanceGraphBuildViaObjectProjectionGraphOutput",
    "FUNCTIONS",
]
