from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.graph.config.object_config_graph_enums import ObjectConfigGraphNodeType

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_meta_ontology.class_.class_config import ClassConfig
    from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
    from aware_meta_ontology.enum.enum_config import EnumConfig
    from aware_meta_ontology.graph.config.object_config_graph_node_layout import ObjectConfigGraphNodeLayout


class ObjectConfigGraphNode(ORMModel):
    # Relationships
    enum_config: EnumConfig | None = Field(default=None)
    class_config: ClassConfig | None = Field(default=None)
    class_config_relationship: ClassConfigRelationship | None = Field(default=None)
    layouts: list[ObjectConfigGraphNodeLayout] = Field(default_factory=list)

    # Attributes
    type: ObjectConfigGraphNodeType
    node_key: str = Field(
        description="Canonical semantic identity for this node lane.\nExamples:\n- class node: class FQN\n- enum node: enum FQN\n- relationship node: canonical relationship fingerprint"
    )

    # Foreign Keys
    object_config_graph_id: UUID = Field(description="Foreign key for ObjectConfigGraph.object_config_graph_nodes")
    class_config_relationship_id: UUID | None = Field(
        default=None, description="Foreign key for ObjectConfigGraphNode.class_config_relationship"
    )

    async def create_class(
        self,
        class_fqn: str,
        name: str,
        is_base: bool = True,
        is_edge: bool = False,
        description: str | None = None,
        value_mode: ClassValueMode = ClassValueMode.graph_ref,
    ) -> ClassConfig:
        """Materialize ClassConfig under this node."""

        payload = {
            "class_fqn": class_fqn,
            "name": name,
            "is_base": is_base,
            "is_edge": is_edge,
            "description": description,
            "value_mode": value_mode,
        }
        result = await invoke_instance(orm_model=self, function_name="create_class", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.class_.class_config import ClassConfig

        if isinstance(value, ClassConfig):
            return value
        return ClassConfig.validate_invocation_value(value)

    async def create_enum(
        self, enum_fqn: str, name: str, description: str | None = None, values: list[str] = []
    ) -> EnumConfig:
        """Materialize EnumConfig under this node."""

        payload = {"enum_fqn": enum_fqn, "name": name, "description": description, "values": values}
        result = await invoke_instance(orm_model=self, function_name="create_enum", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.enum.enum_config import EnumConfig

        if isinstance(value, EnumConfig):
            return value
        return EnumConfig.validate_invocation_value(value)

    @classmethod
    async def create_via_object_config_graph(
        cls, object_config_graph_id: UUID, type: ObjectConfigGraphNodeType, node_key: str
    ) -> ObjectConfigGraphNode:
        """
        Create deterministic node shell under an ObjectConfigGraph.

        Contract:
        - Parent `ObjectConfigGraph` scope is propagated by traversal lowering.
        - Canonical stable identity derives from parent scope + `(type, node_key)`.
        - Contained entities derive under this node instead of being the node identity source.
        """

        payload = {"object_config_graph_id": object_config_graph_id, "type": type, "node_key": node_key}
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_object_config_graph", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ObjectConfigGraphNode):
            return value
        return ObjectConfigGraphNode.validate_invocation_value(value)


class ObjectConfigGraphNodeCreateClassInput(BaseModel):
    class_fqn: str
    name: str
    is_base: bool = Field(default=True)
    is_edge: bool = Field(default=False)
    description: str | None = Field(default=None)
    value_mode: ClassValueMode = Field(default=ClassValueMode.graph_ref)


class ObjectConfigGraphNodeCreateClassOutput(BaseModel):
    value: ClassConfig


class ObjectConfigGraphNodeCreateEnumInput(BaseModel):
    enum_fqn: str
    name: str
    description: str | None = Field(default=None)
    values: list[str] = Field(default_factory=list)


class ObjectConfigGraphNodeCreateEnumOutput(BaseModel):
    value: EnumConfig


class ObjectConfigGraphNodeCreateViaObjectConfigGraphInput(BaseModel):
    object_config_graph_id: UUID = Field(description="Foreign key for ObjectConfigGraph.object_config_graph_nodes")
    type: ObjectConfigGraphNodeType
    node_key: str


class ObjectConfigGraphNodeCreateViaObjectConfigGraphOutput(BaseModel):
    value: ObjectConfigGraphNode


FUNCTIONS = {
    "ObjectConfigGraphNode": {
        "create_class": {
            "canonical": {
                "name": "create_class",
                "description": "Materialize ClassConfig under this node.",
                "is_constructor": False,
            },
            "input": ObjectConfigGraphNodeCreateClassInput,
            "output": ObjectConfigGraphNodeCreateClassOutput,
        },
        "create_enum": {
            "canonical": {
                "name": "create_enum",
                "description": "Materialize EnumConfig under this node.",
                "is_constructor": False,
            },
            "input": ObjectConfigGraphNodeCreateEnumInput,
            "output": ObjectConfigGraphNodeCreateEnumOutput,
        },
        "create_via_object_config_graph": {
            "canonical": {
                "name": "create_via_object_config_graph",
                "description": "Create deterministic node shell under an ObjectConfigGraph.\n\nContract:\n- Parent `ObjectConfigGraph` scope is propagated by traversal lowering.\n- Canonical stable identity derives from parent scope + `(type, node_key)`.\n- Contained entities derive under this node instead of being the node identity source.",
                "is_constructor": True,
            },
            "input": ObjectConfigGraphNodeCreateViaObjectConfigGraphInput,
            "output": ObjectConfigGraphNodeCreateViaObjectConfigGraphOutput,
        },
    },
}

__all__ = [
    "ObjectConfigGraphNode",
    "ObjectConfigGraphNodeCreateClassInput",
    "ObjectConfigGraphNodeCreateClassOutput",
    "ObjectConfigGraphNodeCreateEnumInput",
    "ObjectConfigGraphNodeCreateEnumOutput",
    "ObjectConfigGraphNodeCreateViaObjectConfigGraphInput",
    "ObjectConfigGraphNodeCreateViaObjectConfigGraphOutput",
    "FUNCTIONS",
]
