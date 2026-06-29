from __future__ import annotations

from typing import Any, Mapping
from uuid import UUID

from aware_meta.graph.support.member import GraphMember

from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as DescKind,
)
from aware_meta_ontology.attribute.attribute_value import AttributeValue
from aware_meta_ontology.attribute.attribute_value_link import AttributeValueLink

from aware_meta.graph.instance.member_kind import ObjectInstanceGraphMemberKind


class AttributeValueMember(GraphMember[ObjectInstanceGraphMemberKind]):
    """
    GraphMember wrapper for an AttributeValue node.

    Identity within a value tree is expressed by the parent link slot key
    (role+position/identity_key). Therefore the node path key can be a stable
    literal; the link defines the semantic position of the node.
    """

    attribute_value: AttributeValue

    def get_id(self) -> UUID | None:
        return self.attribute_value.id

    def node_kind(self) -> ObjectInstanceGraphMemberKind:
        return ObjectInstanceGraphMemberKind.attribute_value

    def get_path_key(self) -> str:
        return "value"

    def get_content_fields(self) -> Mapping[str, Any]:
        desc = self.attribute_value.type_descriptor
        if desc is None:
            return {}

        if desc.kind == DescKind.primitive:
            raw = self.attribute_value.primitive_value
            if isinstance(raw, dict) and set(raw.keys()) == {"value"}:
                return {"primitive_value": raw.get("value")}
            return {"primitive_value": raw}

        if desc.kind == DescKind.enum:
            return {"enum_option_id": self.attribute_value.enum_option_id}

        if desc.kind == DescKind.class_:
            # CLASS leaves can be:
            # - GRAPH_REF: class_instance_id is the payload
            # - INLINE_VALUE: inline_value_instance_id is the payload
            inline_value_instance_id = self.attribute_value.inline_value_instance_id
            if inline_value_instance_id is None and self.attribute_value.inline_value_instance is not None:
                inline_value_instance_id = self.attribute_value.inline_value_instance.id
            if inline_value_instance_id is not None:
                return {"inline_value_instance_id": inline_value_instance_id}
            return {"class_instance_id": self.attribute_value.class_instance_id}

        # Container nodes have no leaf payload; changes are expressed structurally by children.
        return {}


class AttributeValueLinkMember(GraphMember[ObjectInstanceGraphMemberKind]):
    """
    GraphMember wrapper for an AttributeValueLink (edge in the value tree).

    Canonical identity is expressed by the slot key:
    - LIST/TUPLE/UNION: (role, position)
    - SET/MAPPING: (role, identity_key)
    """

    attribute_value_link: AttributeValueLink

    def get_id(self) -> UUID | None:
        return self.attribute_value_link.id

    def node_kind(self) -> ObjectInstanceGraphMemberKind:
        return ObjectInstanceGraphMemberKind.attribute_value_link

    def get_path_key(self) -> str:
        role = self.attribute_value_link.role.value
        pos = self.attribute_value_link.position
        ident = self.attribute_value_link.identity_key
        if ident is not None:
            return f"link:{role}:{ident}"
        if pos is not None:
            return f"link:{role}:{pos}"
        return f"link:{role}"

    def get_content_fields(self) -> Mapping[str, Any]:
        # Expose identity fields explicitly so diffs/commits never need to parse `path_key`.
        #
        # NOTE: These fields are immutable at runtime; link updates should not
        # change them (v0), but CREATE commits must carry them.
        return {
            "role": self.attribute_value_link.role.value,
            "position": self.attribute_value_link.position,
            "identity_key": self.attribute_value_link.identity_key,
        }


__all__ = [
    "AttributeValueLinkMember",
    "AttributeValueMember",
]
