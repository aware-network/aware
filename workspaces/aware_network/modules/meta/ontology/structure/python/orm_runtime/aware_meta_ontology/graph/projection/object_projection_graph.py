from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Meta Ontology
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipSideLoadingStrategy,
)
from aware_meta_ontology.graph.projection.object_projection_graph_enums import (
    ObjectProjectionGraphAttributeRole,
    ObjectProjectionGraphEdgeInclude,
    ObjectProjectionGraphEdgeMultiplicity,
    ObjectProjectionGraphNodeSelection,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
    from aware_meta_ontology.graph.projection.object_projection_graph_constructor import (
        ObjectProjectionGraphConstructor,
    )
    from aware_meta_ontology.graph.projection.object_projection_graph_edge import ObjectProjectionGraphEdge
    from aware_meta_ontology.graph.projection.object_projection_graph_node import ObjectProjectionGraphNode
    from aware_meta_ontology.graph.projection.object_projection_graph_relationship import (
        ObjectProjectionGraphRelationship,
    )


class ObjectProjectionGraph(ORMModel):
    # Relationships
    object_projection_graph_edges: list[ObjectProjectionGraphEdge] = Field(
        default_factory=list, description="Canonical membership edges declared under this projection graph."
    )
    object_projection_graph_nodes: list[ObjectProjectionGraphNode] = Field(default_factory=list)
    object_projection_graph_constructors: list[ObjectProjectionGraphConstructor] = Field(default_factory=list)
    object_projection_graph_relationships: list[ObjectProjectionGraphRelationship] = Field(default_factory=list)
    object_instance_graphs: list[ObjectInstanceGraph] = Field(default_factory=list, exclude=True)

    # Attributes
    description: str | None = Field(default=None)
    language: CodeLanguage
    name: str
    projection_hash: str
    supports_virtual_build: bool = Field(default=True)

    # Foreign Keys
    object_config_graph_id: UUID = Field(description="Foreign key for ObjectConfigGraph.object_projection_graphs")

    async def create_node(
        self,
        class_config_id: UUID,
        is_root: bool = False,
        required_for_validity: bool = False,
        selection: ObjectProjectionGraphNodeSelection = ObjectProjectionGraphNodeSelection.all,
        top_n: int | None = None,
        selector_condition_id: UUID | None = None,
        policy_refs: list[str] = [],
    ) -> ObjectProjectionGraphNode:
        """Create deterministic ObjectProjectionGraphNode under this ObjectProjectionGraph."""

        payload = {
            "class_config_id": class_config_id,
            "is_root": is_root,
            "required_for_validity": required_for_validity,
            "selection": selection,
            "top_n": top_n,
            "selector_condition_id": selector_condition_id,
            "policy_refs": policy_refs,
        }
        result = await invoke_instance(orm_model=self, function_name="create_node", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.graph.projection.object_projection_graph_node import ObjectProjectionGraphNode

        if isinstance(value, ObjectProjectionGraphNode):
            return value
        return ObjectProjectionGraphNode.validate_invocation_value(value)

    async def create_edge(
        self,
        class_config_relationship_id: UUID,
        include: ObjectProjectionGraphEdgeInclude = ObjectProjectionGraphEdgeInclude.required,
        multiplicity: ObjectProjectionGraphEdgeMultiplicity = ObjectProjectionGraphEdgeMultiplicity.many,
        traversal_direction: ClassConfigRelationshipDirection = ClassConfigRelationshipDirection.forward,
        depth_limit: int | None = None,
        attribute_role: ObjectProjectionGraphAttributeRole = ObjectProjectionGraphAttributeRole.reference,
        loading_override: ClassConfigRelationshipSideLoadingStrategy | None = None,
    ) -> ObjectProjectionGraphEdge:
        """Create deterministic ObjectProjectionGraphEdge under this ObjectProjectionGraph."""

        payload = {
            "class_config_relationship_id": class_config_relationship_id,
            "include": include,
            "multiplicity": multiplicity,
            "traversal_direction": traversal_direction,
            "depth_limit": depth_limit,
            "attribute_role": attribute_role,
            "loading_override": loading_override,
        }
        result = await invoke_instance(orm_model=self, function_name="create_edge", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.graph.projection.object_projection_graph_edge import ObjectProjectionGraphEdge

        if isinstance(value, ObjectProjectionGraphEdge):
            return value
        return ObjectProjectionGraphEdge.validate_invocation_value(value)

    async def create_constructor(
        self, root_node_id: UUID, function_constructor_id: UUID
    ) -> ObjectProjectionGraphConstructor:
        """Create deterministic ObjectProjectionGraphConstructor under this ObjectProjectionGraph."""

        payload = {"root_node_id": root_node_id, "function_constructor_id": function_constructor_id}
        result = await invoke_instance(orm_model=self, function_name="create_constructor", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.graph.projection.object_projection_graph_constructor import (
            ObjectProjectionGraphConstructor,
        )

        if isinstance(value, ObjectProjectionGraphConstructor):
            return value
        return ObjectProjectionGraphConstructor.validate_invocation_value(value)

    async def create_relationship(
        self,
        target_object_projection_graph_id: UUID,
        class_config_relationship_id: UUID,
        source_object_projection_graph_node_id: UUID,
        target_object_projection_graph_node_id: UUID,
    ) -> ObjectProjectionGraphRelationship:
        """Create deterministic ObjectProjectionGraphRelationship under this ObjectProjectionGraph."""

        payload = {
            "target_object_projection_graph_id": target_object_projection_graph_id,
            "class_config_relationship_id": class_config_relationship_id,
            "source_object_projection_graph_node_id": source_object_projection_graph_node_id,
            "target_object_projection_graph_node_id": target_object_projection_graph_node_id,
        }
        result = await invoke_instance(orm_model=self, function_name="create_relationship", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.graph.projection.object_projection_graph_relationship import (
            ObjectProjectionGraphRelationship,
        )

        if isinstance(value, ObjectProjectionGraphRelationship):
            return value
        return ObjectProjectionGraphRelationship.validate_invocation_value(value)

    async def create_object_instance_graph(
        self,
        key: str,
        root_class_config_id: UUID,
        root_source_object_id: UUID,
        name: str,
        description: str | None = None,
        hash: str = "",
    ) -> ObjectInstanceGraph:
        """
        Create deterministic ObjectInstanceGraph under this ObjectProjectionGraph.

        Contract:
        - Parent `object_projection_graph_id` is propagated by constructor lowering.
        - Child identity resolves from `(object_projection_graph_id via path, key)`.
        - Root ClassInstance is created eagerly at construction time; empty OIGs are not allowed.
        - `name` is mutable payload metadata; `hash` is snapshot metadata only.
        """

        payload = {
            "key": key,
            "root_class_config_id": root_class_config_id,
            "root_source_object_id": root_source_object_id,
            "name": name,
            "description": description,
            "hash": hash,
        }
        result = await invoke_instance(orm_model=self, function_name="create_object_instance_graph", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph

        if isinstance(value, ObjectInstanceGraph):
            return value
        return ObjectInstanceGraph.validate_invocation_value(value)

    @classmethod
    async def build_via_object_config_graph(
        cls,
        object_config_graph_id: UUID,
        name: str,
        projection_hash: str,
        language: CodeLanguage = CodeLanguage.aware,
        description: str | None = None,
        supports_virtual_build: bool = True,
    ) -> ObjectProjectionGraph:
        """
        Create deterministic ObjectProjectionGraph root for runtime proof composition.

        Contract:
        - Parent `object_config_graph_id` is propagated by constructor lowering.
        - Identity resolves from `(object_config_graph_id via path, name)`.
        - `projection_hash` is snapshot metadata and must not participate in stable identity.
        """

        payload = {
            "object_config_graph_id": object_config_graph_id,
            "name": name,
            "projection_hash": projection_hash,
            "language": language,
            "description": description,
            "supports_virtual_build": supports_virtual_build,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_object_config_graph", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ObjectProjectionGraph):
            return value
        return ObjectProjectionGraph.validate_invocation_value(value)


class ObjectProjectionGraphCreateNodeInput(BaseModel):
    class_config_id: UUID
    is_root: bool = Field(default=False)
    required_for_validity: bool = Field(default=False)
    selection: ObjectProjectionGraphNodeSelection = Field(default=ObjectProjectionGraphNodeSelection.all)
    top_n: int | None = Field(default=None)
    selector_condition_id: UUID | None = Field(default=None)
    policy_refs: list[str] = Field(default_factory=list)


class ObjectProjectionGraphCreateNodeOutput(BaseModel):
    value: ObjectProjectionGraphNode


class ObjectProjectionGraphCreateEdgeInput(BaseModel):
    class_config_relationship_id: UUID
    include: ObjectProjectionGraphEdgeInclude = Field(default=ObjectProjectionGraphEdgeInclude.required)
    multiplicity: ObjectProjectionGraphEdgeMultiplicity = Field(default=ObjectProjectionGraphEdgeMultiplicity.many)
    traversal_direction: ClassConfigRelationshipDirection = Field(default=ClassConfigRelationshipDirection.forward)
    depth_limit: int | None = Field(default=None)
    attribute_role: ObjectProjectionGraphAttributeRole = Field(default=ObjectProjectionGraphAttributeRole.reference)
    loading_override: ClassConfigRelationshipSideLoadingStrategy | None = Field(default=None)


class ObjectProjectionGraphCreateEdgeOutput(BaseModel):
    value: ObjectProjectionGraphEdge


class ObjectProjectionGraphCreateConstructorInput(BaseModel):
    root_node_id: UUID
    function_constructor_id: UUID


class ObjectProjectionGraphCreateConstructorOutput(BaseModel):
    value: ObjectProjectionGraphConstructor


class ObjectProjectionGraphCreateRelationshipInput(BaseModel):
    target_object_projection_graph_id: UUID
    class_config_relationship_id: UUID
    source_object_projection_graph_node_id: UUID
    target_object_projection_graph_node_id: UUID


class ObjectProjectionGraphCreateRelationshipOutput(BaseModel):
    value: ObjectProjectionGraphRelationship


class ObjectProjectionGraphCreateObjectInstanceGraphInput(BaseModel):
    key: str
    root_class_config_id: UUID
    root_source_object_id: UUID
    name: str
    description: str | None = Field(default=None)
    hash: str = Field(default="")


class ObjectProjectionGraphCreateObjectInstanceGraphOutput(BaseModel):
    value: ObjectInstanceGraph


class ObjectProjectionGraphBuildViaObjectConfigGraphInput(BaseModel):
    object_config_graph_id: UUID = Field(description="Foreign key for ObjectConfigGraph.object_projection_graphs")
    name: str
    projection_hash: str
    language: CodeLanguage = Field(default=CodeLanguage.aware)
    description: str | None = Field(default=None)
    supports_virtual_build: bool = Field(default=True)


class ObjectProjectionGraphBuildViaObjectConfigGraphOutput(BaseModel):
    value: ObjectProjectionGraph


FUNCTIONS = {
    "ObjectProjectionGraph": {
        "create_node": {
            "canonical": {
                "name": "create_node",
                "description": "Create deterministic ObjectProjectionGraphNode under this ObjectProjectionGraph.",
                "is_constructor": False,
            },
            "input": ObjectProjectionGraphCreateNodeInput,
            "output": ObjectProjectionGraphCreateNodeOutput,
        },
        "create_edge": {
            "canonical": {
                "name": "create_edge",
                "description": "Create deterministic ObjectProjectionGraphEdge under this ObjectProjectionGraph.",
                "is_constructor": False,
            },
            "input": ObjectProjectionGraphCreateEdgeInput,
            "output": ObjectProjectionGraphCreateEdgeOutput,
        },
        "create_constructor": {
            "canonical": {
                "name": "create_constructor",
                "description": "Create deterministic ObjectProjectionGraphConstructor under this ObjectProjectionGraph.",
                "is_constructor": False,
            },
            "input": ObjectProjectionGraphCreateConstructorInput,
            "output": ObjectProjectionGraphCreateConstructorOutput,
        },
        "create_relationship": {
            "canonical": {
                "name": "create_relationship",
                "description": "Create deterministic ObjectProjectionGraphRelationship under this ObjectProjectionGraph.",
                "is_constructor": False,
            },
            "input": ObjectProjectionGraphCreateRelationshipInput,
            "output": ObjectProjectionGraphCreateRelationshipOutput,
        },
        "create_object_instance_graph": {
            "canonical": {
                "name": "create_object_instance_graph",
                "description": "Create deterministic ObjectInstanceGraph under this ObjectProjectionGraph.\n\nContract:\n- Parent `object_projection_graph_id` is propagated by constructor lowering.\n- Child identity resolves from `(object_projection_graph_id via path, key)`.\n- Root ClassInstance is created eagerly at construction time; empty OIGs are not allowed.\n- `name` is mutable payload metadata; `hash` is snapshot metadata only.",
                "is_constructor": False,
            },
            "input": ObjectProjectionGraphCreateObjectInstanceGraphInput,
            "output": ObjectProjectionGraphCreateObjectInstanceGraphOutput,
        },
        "build_via_object_config_graph": {
            "canonical": {
                "name": "build_via_object_config_graph",
                "description": "Create deterministic ObjectProjectionGraph root for runtime proof composition.\n\nContract:\n- Parent `object_config_graph_id` is propagated by constructor lowering.\n- Identity resolves from `(object_config_graph_id via path, name)`.\n- `projection_hash` is snapshot metadata and must not participate in stable identity.",
                "is_constructor": True,
            },
            "input": ObjectProjectionGraphBuildViaObjectConfigGraphInput,
            "output": ObjectProjectionGraphBuildViaObjectConfigGraphOutput,
        },
    },
}

__all__ = [
    "ObjectProjectionGraph",
    "ObjectProjectionGraphCreateNodeInput",
    "ObjectProjectionGraphCreateNodeOutput",
    "ObjectProjectionGraphCreateEdgeInput",
    "ObjectProjectionGraphCreateEdgeOutput",
    "ObjectProjectionGraphCreateConstructorInput",
    "ObjectProjectionGraphCreateConstructorOutput",
    "ObjectProjectionGraphCreateRelationshipInput",
    "ObjectProjectionGraphCreateRelationshipOutput",
    "ObjectProjectionGraphCreateObjectInstanceGraphInput",
    "ObjectProjectionGraphCreateObjectInstanceGraphOutput",
    "ObjectProjectionGraphBuildViaObjectConfigGraphInput",
    "ObjectProjectionGraphBuildViaObjectConfigGraphOutput",
    "FUNCTIONS",
]
