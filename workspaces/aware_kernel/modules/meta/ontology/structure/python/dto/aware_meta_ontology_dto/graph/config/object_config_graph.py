from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology Dto
from aware_code_ontology_dto.code.code_enums import CodeLanguage

if TYPE_CHECKING:
    from aware_meta_ontology_dto.graph.config.object_config_graph_annotation import ObjectConfigGraphAnnotation
    from aware_meta_ontology_dto.graph.config.object_config_graph_binding import ObjectConfigGraphBinding
    from aware_meta_ontology_dto.graph.config.object_config_graph_identity import ObjectConfigGraphIdentity
    from aware_meta_ontology_dto.graph.config.object_config_graph_mirror import ObjectConfigGraphMirror
    from aware_meta_ontology_dto.graph.config.object_config_graph_node import ObjectConfigGraphNode
    from aware_meta_ontology_dto.graph.config.object_config_graph_overlay import ObjectConfigGraphOverlay
    from aware_meta_ontology_dto.graph.config.object_config_graph_relationship import ObjectConfigGraphRelationship
    from aware_meta_ontology_dto.graph.projection.object_projection_graph import ObjectProjectionGraph
    from aware_meta_ontology_dto.graph.projection.object_projection_graph_declaration import (
        ObjectProjectionGraphDeclaration,
    )


class ObjectConfigGraph(BaseModel):
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
