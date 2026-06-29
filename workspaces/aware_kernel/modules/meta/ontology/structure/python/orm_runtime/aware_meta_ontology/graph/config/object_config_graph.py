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
from aware_meta_ontology.graph.config.object_config_graph_enums import ObjectConfigGraphNodeType

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_meta_ontology.graph.config.object_config_graph_annotation import ObjectConfigGraphAnnotation
    from aware_meta_ontology.graph.config.object_config_graph_binding import ObjectConfigGraphBinding
    from aware_meta_ontology.graph.config.object_config_graph_identity import ObjectConfigGraphIdentity
    from aware_meta_ontology.graph.config.object_config_graph_mirror import ObjectConfigGraphMirror
    from aware_meta_ontology.graph.config.object_config_graph_node import ObjectConfigGraphNode
    from aware_meta_ontology.graph.config.object_config_graph_overlay import ObjectConfigGraphOverlay
    from aware_meta_ontology.graph.config.object_config_graph_relationship import ObjectConfigGraphRelationship
    from aware_meta_ontology.graph.projection.object_projection_graph import ObjectProjectionGraph
    from aware_meta_ontology.graph.projection.object_projection_graph_declaration import (
        ObjectProjectionGraphDeclaration,
    )


class ObjectConfigGraph(ORMModel):
    # Relationships
    object_config_graph_identity: ObjectConfigGraphIdentity | None = Field(
        default=None, description="Stable identity for this config graph family (compiler-owned)."
    )
    object_config_graph_annotations: list[ObjectConfigGraphAnnotation] = Field(default_factory=list)
    object_config_graph_mirrors: list[ObjectConfigGraphMirror] = Field(default_factory=list)
    object_config_graph_nodes: list[ObjectConfigGraphNode] = Field(default_factory=list)
    object_config_graph_overlays: list[ObjectConfigGraphOverlay] = Field(default_factory=list)
    object_config_graph_bindings: list[ObjectConfigGraphBinding] = Field(
        default_factory=list,
        description="Cross-layer binding rails (source scope is this OCG; target scope is the child binding key).",
    )
    object_config_graph_relationships: list[ObjectConfigGraphRelationship] = Field(default_factory=list)
    object_projection_graph_declarations: list[ObjectProjectionGraphDeclaration] = Field(
        default_factory=list,
        description="Compiler-owned projection declarations (hashable SSOT for OPG membership/portals).",
    )
    object_projection_graphs: list[ObjectProjectionGraph] = Field(default_factory=list)

    # Attributes
    name: str
    description: str | None = Field(default=None)
    hash: str
    layout_hash: str | None = Field(
        default=None,
        description="Stable hash that includes layout metadata (relative paths + ordering).\nUsed to invalidate materialization caches when files move without semantic changes.",
    )
    fqn_prefix: str = Field(
        description="Stable FQN prefix used as the root namespace for all FQNs in this graph.\nNOTE: `package_name` (installable package identity) is modeled on\nObjectConfigGraphPackage. This field is purely for deterministic FQN\nconstruction and cross-OCG linking."
    )
    language: CodeLanguage

    # Foreign Keys
    object_config_graph_identity_id: UUID | None = Field(
        default=None, description="Foreign key for ObjectConfigGraph.object_config_graph_identity"
    )

    @classmethod
    async def build(
        cls,
        name: str,
        hash: str,
        fqn_prefix: str,
        language: CodeLanguage = CodeLanguage.aware,
        object_config_graph_id: UUID | None = None,
        object_config_graph_identity_id: UUID | None = None,
        description: str | None = None,
        layout_hash: str | None = None,
    ) -> ObjectConfigGraph:
        """
        Create deterministic ObjectConfigGraph root for runtime proof composition.

        Contract:
        - Identity contract is keyed by `(fqn_prefix, language)`.
        - `object_config_graph_id` is optional compatibility input; when provided it must match
          compiler/runtime deterministic derivation for `(fqn_prefix, language)`.
        """

        payload = {
            "name": name,
            "hash": hash,
            "fqn_prefix": fqn_prefix,
            "language": language,
            "object_config_graph_id": object_config_graph_id,
            "object_config_graph_identity_id": object_config_graph_identity_id,
            "description": description,
            "layout_hash": layout_hash,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ObjectConfigGraph):
            return value
        return ObjectConfigGraph.validate_invocation_value(value)

    async def create_node(self, type: ObjectConfigGraphNodeType, node_key: str) -> ObjectConfigGraphNode:
        """Create one node under this ObjectConfigGraph."""

        payload = {"type": type, "node_key": node_key}
        result = await invoke_instance(orm_model=self, function_name="create_node", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.graph.config.object_config_graph_node import ObjectConfigGraphNode

        if isinstance(value, ObjectConfigGraphNode):
            return value
        return ObjectConfigGraphNode.validate_invocation_value(value)

    async def delete_node(
        self, type: ObjectConfigGraphNodeType, node_key: str, object_config_graph_node_id: UUID | None = None
    ) -> None:
        """
        Remove one node from this ObjectConfigGraph.

        Contract:
        - The target node identity must match `(type, node_key)` inside this graph.
        - `object_config_graph_node_id` is optional identity evidence for delete deltas.
        - Delete mutates only this graph's `object_config_graph_nodes` membership.
        """

        payload = {"type": type, "node_key": node_key, "object_config_graph_node_id": object_config_graph_node_id}
        await invoke_instance(orm_model=self, function_name="delete_node", payload=payload)
        return None

    async def create_object_projection_graph(
        self,
        name: str,
        projection_hash: str,
        language: CodeLanguage = CodeLanguage.aware,
        description: str | None = None,
        supports_virtual_build: bool = True,
    ) -> ObjectProjectionGraph:
        """
        Create deterministic ObjectProjectionGraph under this ObjectConfigGraph.

        Contract:
        - Parent `object_config_graph_id` is propagated by constructor lowering.
        - Child identity resolves from `(object_config_graph_id via path, name)`.
        - `projection_hash` is snapshot metadata and must not participate in stable identity.
        """

        payload = {
            "name": name,
            "projection_hash": projection_hash,
            "language": language,
            "description": description,
            "supports_virtual_build": supports_virtual_build,
        }
        result = await invoke_instance(orm_model=self, function_name="create_object_projection_graph", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.graph.projection.object_projection_graph import ObjectProjectionGraph

        if isinstance(value, ObjectProjectionGraph):
            return value
        return ObjectProjectionGraph.validate_invocation_value(value)

    async def get_topology_description(self) -> str:
        """Returns a description of the ObjectConfigGraph topology."""

        payload = {}
        result = await invoke_instance(orm_model=self, function_name="get_topology_description", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        return value

    async def create_object_config_graph_relationship(
        self, target_object_config_graph_id: UUID
    ) -> ObjectConfigGraphRelationship:
        """Create deterministic ObjectConfigGraphRelationship under this ObjectConfigGraph."""

        payload = {"target_object_config_graph_id": target_object_config_graph_id}
        result = await invoke_instance(
            orm_model=self, function_name="create_object_config_graph_relationship", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.graph.config.object_config_graph_relationship import ObjectConfigGraphRelationship

        if isinstance(value, ObjectConfigGraphRelationship):
            return value
        return ObjectConfigGraphRelationship.validate_invocation_value(value)

    async def create_object_config_graph_binding(self, target_object_config_graph_id: UUID) -> ObjectConfigGraphBinding:
        """
        Create deterministic ObjectConfigGraphBinding under this ObjectConfigGraph.

        Contract:
        - Source OCG scope is propagated through parent containment.
        - Child identity resolves from `(object_config_graph_id via path, target_object_config_graph_id)`.
        """

        payload = {"target_object_config_graph_id": target_object_config_graph_id}
        result = await invoke_instance(
            orm_model=self, function_name="create_object_config_graph_binding", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.graph.config.object_config_graph_binding import ObjectConfigGraphBinding

        if isinstance(value, ObjectConfigGraphBinding):
            return value
        return ObjectConfigGraphBinding.validate_invocation_value(value)


class ObjectConfigGraphBuildInput(BaseModel):
    name: str
    hash: str
    fqn_prefix: str
    language: CodeLanguage = Field(default=CodeLanguage.aware)
    object_config_graph_id: UUID | None = Field(default=None)
    object_config_graph_identity_id: UUID | None = Field(default=None)
    description: str | None = Field(default=None)
    layout_hash: str | None = Field(default=None)


class ObjectConfigGraphBuildOutput(BaseModel):
    value: ObjectConfigGraph


class ObjectConfigGraphCreateNodeInput(BaseModel):
    type: ObjectConfigGraphNodeType
    node_key: str


class ObjectConfigGraphCreateNodeOutput(BaseModel):
    value: ObjectConfigGraphNode


class ObjectConfigGraphDeleteNodeInput(BaseModel):
    type: ObjectConfigGraphNodeType
    node_key: str
    object_config_graph_node_id: UUID | None = Field(default=None)


class ObjectConfigGraphDeleteNodeOutput(BaseModel):
    pass


class ObjectConfigGraphCreateObjectProjectionGraphInput(BaseModel):
    name: str
    projection_hash: str
    language: CodeLanguage = Field(default=CodeLanguage.aware)
    description: str | None = Field(default=None)
    supports_virtual_build: bool = Field(default=True)


class ObjectConfigGraphCreateObjectProjectionGraphOutput(BaseModel):
    value: ObjectProjectionGraph


class ObjectConfigGraphGetTopologyDescriptionInput(BaseModel):
    pass


class ObjectConfigGraphGetTopologyDescriptionOutput(BaseModel):
    value: str


class ObjectConfigGraphCreateObjectConfigGraphRelationshipInput(BaseModel):
    target_object_config_graph_id: UUID


class ObjectConfigGraphCreateObjectConfigGraphRelationshipOutput(BaseModel):
    value: ObjectConfigGraphRelationship


class ObjectConfigGraphCreateObjectConfigGraphBindingInput(BaseModel):
    target_object_config_graph_id: UUID


class ObjectConfigGraphCreateObjectConfigGraphBindingOutput(BaseModel):
    value: ObjectConfigGraphBinding


FUNCTIONS = {
    "ObjectConfigGraph": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create deterministic ObjectConfigGraph root for runtime proof composition.\n\nContract:\n- Identity contract is keyed by `(fqn_prefix, language)`.\n- `object_config_graph_id` is optional compatibility input; when provided it must match\n  compiler/runtime deterministic derivation for `(fqn_prefix, language)`.",
                "is_constructor": True,
            },
            "input": ObjectConfigGraphBuildInput,
            "output": ObjectConfigGraphBuildOutput,
        },
        "create_node": {
            "canonical": {
                "name": "create_node",
                "description": "Create one node under this ObjectConfigGraph.",
                "is_constructor": False,
            },
            "input": ObjectConfigGraphCreateNodeInput,
            "output": ObjectConfigGraphCreateNodeOutput,
        },
        "delete_node": {
            "canonical": {
                "name": "delete_node",
                "description": "Remove one node from this ObjectConfigGraph.\n\nContract:\n- The target node identity must match `(type, node_key)` inside this graph.\n- `object_config_graph_node_id` is optional identity evidence for delete deltas.\n- Delete mutates only this graph's `object_config_graph_nodes` membership.",
                "is_constructor": False,
            },
            "input": ObjectConfigGraphDeleteNodeInput,
            "output": ObjectConfigGraphDeleteNodeOutput,
        },
        "create_object_projection_graph": {
            "canonical": {
                "name": "create_object_projection_graph",
                "description": "Create deterministic ObjectProjectionGraph under this ObjectConfigGraph.\n\nContract:\n- Parent `object_config_graph_id` is propagated by constructor lowering.\n- Child identity resolves from `(object_config_graph_id via path, name)`.\n- `projection_hash` is snapshot metadata and must not participate in stable identity.",
                "is_constructor": False,
            },
            "input": ObjectConfigGraphCreateObjectProjectionGraphInput,
            "output": ObjectConfigGraphCreateObjectProjectionGraphOutput,
        },
        "get_topology_description": {
            "canonical": {
                "name": "get_topology_description",
                "description": "Returns a description of the ObjectConfigGraph topology.",
                "is_constructor": False,
            },
            "input": ObjectConfigGraphGetTopologyDescriptionInput,
            "output": ObjectConfigGraphGetTopologyDescriptionOutput,
        },
        "create_object_config_graph_relationship": {
            "canonical": {
                "name": "create_object_config_graph_relationship",
                "description": "Create deterministic ObjectConfigGraphRelationship under this ObjectConfigGraph.",
                "is_constructor": False,
            },
            "input": ObjectConfigGraphCreateObjectConfigGraphRelationshipInput,
            "output": ObjectConfigGraphCreateObjectConfigGraphRelationshipOutput,
        },
        "create_object_config_graph_binding": {
            "canonical": {
                "name": "create_object_config_graph_binding",
                "description": "Create deterministic ObjectConfigGraphBinding under this ObjectConfigGraph.\n\nContract:\n- Source OCG scope is propagated through parent containment.\n- Child identity resolves from `(object_config_graph_id via path, target_object_config_graph_id)`.",
                "is_constructor": False,
            },
            "input": ObjectConfigGraphCreateObjectConfigGraphBindingInput,
            "output": ObjectConfigGraphCreateObjectConfigGraphBindingOutput,
        },
    },
}

__all__ = [
    "ObjectConfigGraph",
    "ObjectConfigGraphBuildInput",
    "ObjectConfigGraphBuildOutput",
    "ObjectConfigGraphCreateNodeInput",
    "ObjectConfigGraphCreateNodeOutput",
    "ObjectConfigGraphDeleteNodeInput",
    "ObjectConfigGraphDeleteNodeOutput",
    "ObjectConfigGraphCreateObjectProjectionGraphInput",
    "ObjectConfigGraphCreateObjectProjectionGraphOutput",
    "ObjectConfigGraphGetTopologyDescriptionInput",
    "ObjectConfigGraphGetTopologyDescriptionOutput",
    "ObjectConfigGraphCreateObjectConfigGraphRelationshipInput",
    "ObjectConfigGraphCreateObjectConfigGraphRelationshipOutput",
    "ObjectConfigGraphCreateObjectConfigGraphBindingInput",
    "ObjectConfigGraphCreateObjectConfigGraphBindingOutput",
    "FUNCTIONS",
]
