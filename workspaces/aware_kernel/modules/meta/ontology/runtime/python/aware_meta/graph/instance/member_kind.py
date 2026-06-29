"""ObjectInstanceGraph-specific node types."""

from __future__ import annotations

from enum import Enum


class ObjectInstanceGraphMemberKind(Enum):
    """Enumeration of node kinds in an ObjectInstanceGraph."""

    object_instance_graph = "object_instance_graph"
    object_instance = "object_instance"
    relationship_instance = "relationship_instance"
    class_instance = "class_instance"
    attribute = "attribute"
    attribute_value = "attribute_value"
    attribute_value_link = "attribute_value_link"
    primitive = "primitive"
    enum = "enum"


# Mapping from class names to node kinds for fingerprinting
CLASS_TO_KIND: dict[str, ObjectInstanceGraphMemberKind] = {
    "objectinstance": ObjectInstanceGraphMemberKind.object_instance,
    "objectinstancerelationship": ObjectInstanceGraphMemberKind.relationship_instance,
    "classinstance": ObjectInstanceGraphMemberKind.class_instance,
    "attribute": ObjectInstanceGraphMemberKind.attribute,
    "attributevalue": ObjectInstanceGraphMemberKind.attribute_value,
    "attributevaluelink": ObjectInstanceGraphMemberKind.attribute_value_link,
    "primitive": ObjectInstanceGraphMemberKind.primitive,
    "enum": ObjectInstanceGraphMemberKind.enum,
}
