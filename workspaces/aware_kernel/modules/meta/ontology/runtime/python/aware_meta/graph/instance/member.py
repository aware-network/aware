from __future__ import annotations

from typing import Any, Mapping
from uuid import UUID

from aware_meta.graph.support.member import GraphMember

from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta.graph.instance.member_kind import ObjectInstanceGraphMemberKind


class ObjectInstanceGraphMember(GraphMember[ObjectInstanceGraphMemberKind]):
    """
    Graph representation of object instances and their relationships.

    This model captures the state of object instances at a point in time,
    including their values and relationships to other instances.
    """

    object_instance_graph: ObjectInstanceGraph

    def get_id(self) -> UUID | None:
        return self.object_instance_graph.id

    def node_kind(self) -> ObjectInstanceGraphMemberKind:
        return ObjectInstanceGraphMemberKind.object_instance_graph

    def get_path_key(self) -> str:
        # Canonical reconciliation identity MUST NOT depend on derived metadata
        # like `name`/`description`. Use the stable graph id.
        graph_id = self.object_instance_graph.id
        if graph_id is None:
            raise ValueError("ObjectInstanceGraph has no id")
        return f"graph:{graph_id}"

    def get_content_fields(self) -> Mapping[str, Any]:
        # Mapping from logical field name to value, sourced from the underlying
        # ObjectInstanceGraph entity.
        return {
            "name": self.object_instance_graph.name,
            "description": self.object_instance_graph.description,
        }
