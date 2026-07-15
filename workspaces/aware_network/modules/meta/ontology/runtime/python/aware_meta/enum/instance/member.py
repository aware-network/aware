from typing import Any, Mapping
from uuid import UUID

from aware_meta.graph.support.member import GraphMember

from aware_meta_ontology.enum.enum import Enum

from aware_meta.graph.instance.member_kind import ObjectInstanceGraphMemberKind


class EnumMember(GraphMember[ObjectInstanceGraphMemberKind]):
    enum: Enum

    def get_id(self) -> UUID | None:
        return self.enum.id

    def node_kind(self) -> ObjectInstanceGraphMemberKind:
        return ObjectInstanceGraphMemberKind.enum

    def get_path_key(self) -> str:
        enum_config_id = self.enum.enum_config_id
        return f"enum:{enum_config_id}" if enum_config_id is not None else "enum:unknown"

    def get_content_fields(self) -> Mapping[str, Any]:
        return {
            "enum_option_id": self.enum.enum_option_id,
        }
