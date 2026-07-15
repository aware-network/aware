from enum import Enum


class ObjectConfigGraphMemberKind(Enum):
    """Enumeration of member kinds in an ObjectConfigGraph."""

    ROOT = "root"

    # Object
    OBJECT = "object"
    OBJECT_CLASS_LINK = "object_class_link"

    # Relationship
    RELATIONSHIP = "relationship"

    # Class
    CLASS = "class"
    CLASS_FUNCTION_LINK = "class_function_link"
    CLASS_ATTRIBUTE_LINK = "class_attribute_link"

    # Function
    FUNCTION = "function"

    # Attribute
    ATTRIBUTE = "attribute"
    ATTRIBUTE_PRIMITIVE_LINK = "attribute_primitive_link"
    ATTRIBUTE_ENUM_LINK = "attribute_enum_link"
    ATTRIBUTE_CLASS_LINK = "attribute_class_link"

    # Enum
    ENUM = "enum"
    ENUM_OPTION = "enum_option"

    # Primitive
    PRIMITIVE = "primitive"


# Mapping from class names to node kinds for fingerprinting
CLASS_TO_KIND: dict[str, ObjectConfigGraphMemberKind] = {
    "objectconfiggraph": ObjectConfigGraphMemberKind.ROOT,
    "objectconfig": ObjectConfigGraphMemberKind.OBJECT,
    "classconfig": ObjectConfigGraphMemberKind.CLASS,
    "functionconfig": ObjectConfigGraphMemberKind.FUNCTION,
    "attributeconfig": ObjectConfigGraphMemberKind.ATTRIBUTE,
    "enumconfig": ObjectConfigGraphMemberKind.ENUM,
    "enumoption": ObjectConfigGraphMemberKind.ENUM_OPTION,
    "primitiveconfig": ObjectConfigGraphMemberKind.PRIMITIVE,
    "objectconfigrelationship": ObjectConfigGraphMemberKind.RELATIONSHIP,
}
