from __future__ import annotations

from typing import Any, Mapping
from uuid import UUID

from aware_meta.graph.support.member import GraphMember

from aware_meta_ontology.class_.class_instance_relationship import (
    ClassInstanceRelationship,
)

from aware_meta.graph.instance.member_kind import ObjectInstanceGraphMemberKind


class ClassInstanceRelationshipMember(GraphMember[ObjectInstanceGraphMemberKind]):
    """
    GraphMember wrapper for ClassInstanceRelationship.

    Relationships are primarily structural edges between instances; identity is
    defined semantically by (source_class_instance_id, target_class_instance_id,
    class_config_relationship_id).
    """

    class_instance_relationship: ClassInstanceRelationship

    def get_id(self) -> UUID | None:
        return self.class_instance_relationship.id

    def node_kind(self) -> ObjectInstanceGraphMemberKind:
        return ObjectInstanceGraphMemberKind.relationship_instance

    def get_path_key(self) -> str:
        src = self.class_instance_relationship.source_class_instance_id
        tgt = self.class_instance_relationship.target_class_instance_id
        rel_id = self.class_instance_relationship.class_config_relationship_id
        return f"{src}->{tgt}:{rel_id}"

    def get_content_fields(self) -> Mapping[str, Any]:
        # Expose identity fields explicitly so diffs/commits never need to parse `path_key`.
        #
        # Relationships are structural; these fields are immutable for UPDATE (v0),
        # but CREATE/DELETE commits must still carry them.
        return {
            "class_config_relationship_id": self.class_instance_relationship.class_config_relationship_id,
            "source_class_instance_id": self.class_instance_relationship.source_class_instance_id,
            "target_class_instance_id": self.class_instance_relationship.target_class_instance_id,
        }
