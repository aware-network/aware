from __future__ import annotations

from typing import Any, Mapping
from uuid import UUID

from aware_meta.graph.support.member import GraphMember

from aware_meta_ontology.class_.class_instance import ClassInstance

from aware_meta.graph.instance.member_kind import ObjectInstanceGraphMemberKind


class ClassInstanceMember(GraphMember[ObjectInstanceGraphMemberKind]):
    """
    GraphMember wrapper for ClassInstance (canonical instance node).
    """

    class_instance: ClassInstance

    def get_id(self) -> UUID | None:
        return self.class_instance.id

    def node_kind(self) -> ObjectInstanceGraphMemberKind:
        return ObjectInstanceGraphMemberKind.class_instance

    def get_path_key(self) -> str:
        """
        Semantic identity for an object instance.

        Canonical: stable identity is (class_config_id, class_instance.id).
        """
        # Canonical: stable identity is (class_config_id, class_instance.id) (no ObjectConfig/ObjectInstance).
        class_config_id = self.class_instance.class_config_id
        entity_id = self.class_instance.id
        return f"{class_config_id}:{entity_id}" if entity_id is not None else f"{class_config_id}:unknown"

    def get_content_fields(self) -> Mapping[str, Any]:
        # Mutable fields that define content at the object instance level.
        # Values are read from the underlying ClassInstance.
        return {
            "class_config_id": self.class_instance.class_config_id,
        }
