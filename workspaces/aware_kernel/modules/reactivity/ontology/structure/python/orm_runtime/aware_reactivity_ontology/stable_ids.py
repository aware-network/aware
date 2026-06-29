# GENERATED CODE - DO NOT MODIFY BY HAND
# Canonical stable-id derivations (UUIDv5).
from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

NS_REACTIVITY = uuid5(NAMESPACE_URL, "aware://reactivity/v1")


def stable_action_id(*, event_id: UUID, config_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: event_id, config_id"""

    return uuid5(NS_REACTIVITY, f"aware:action:{event_id}:{config_id}")


def stable_action_config_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_REACTIVITY, f"aware:action_config:{name_norm}")


def stable_action_execution_id(*, action_intent_id: UUID, execution_key: str = "primary") -> UUID:
    """Compiler-generated from class-attribute identity keys: action_intent_id, execution_key"""

    execution_key_norm = (execution_key or "").casefold().strip() or "primary"
    return uuid5(NS_REACTIVITY, f"aware:action_execution:{action_intent_id}:{execution_key_norm}")


def stable_action_feedback_id(*, action_execution_id: UUID, sequence: int) -> UUID:
    """Compiler-generated from class-attribute identity keys: action_execution_id, sequence"""

    return uuid5(NS_REACTIVITY, f"aware:action_feedback:{action_execution_id}:{sequence}")


def stable_action_intent_id(*, event_id: UUID, config_id: UUID, intent_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: event_id, config_id, intent_key"""

    intent_key_norm = (intent_key or "").casefold().strip()
    return uuid5(NS_REACTIVITY, f"aware:action_intent:{event_id}:{config_id}:{intent_key_norm}")


def stable_condition_id(*, config_id: UUID, activation_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: config_id, activation_id"""

    return uuid5(NS_REACTIVITY, f"aware:condition:{config_id}:{activation_id}")


def stable_condition_config_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_REACTIVITY, f"aware:condition_config:{name_norm}")


def stable_condition_config_attribute_config_id(
    *, condition_config_class_config_id: UUID, attribute_config_id: UUID, operator: str, negate: bool = False
) -> UUID:
    """Compiler-generated from class-attribute identity keys: condition_config_class_config_id, attribute_config_id, operator, negate"""

    operator_norm = (operator or "").casefold().strip()
    negate_int = int(negate)
    return uuid5(
        NS_REACTIVITY,
        f"aware:condition_config_attribute_config:{condition_config_class_config_id}:{attribute_config_id}:{operator_norm}:{negate_int}",
    )


def stable_condition_config_class_config_id(*, condition_config_id: UUID, class_config_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: condition_config_id, class_config_id"""

    return uuid5(NS_REACTIVITY, f"aware:condition_config_class_config:{condition_config_id}:{class_config_id}")


def stable_condition_config_enum_config_id(*, condition_config_attribute_config_id: UUID, enum_config_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: condition_config_attribute_config_id, enum_config_id"""

    return uuid5(
        NS_REACTIVITY, f"aware:condition_config_enum_config:{condition_config_attribute_config_id}:{enum_config_id}"
    )


def stable_condition_config_enum_option_id(*, condition_config_enum_config_id: UUID, enum_option_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: condition_config_enum_config_id, enum_option_id"""

    return uuid5(
        NS_REACTIVITY, f"aware:condition_config_enum_option:{condition_config_enum_config_id}:{enum_option_id}"
    )


def stable_condition_config_primitive_config_id(
    *, condition_config_attribute_config_id: UUID, primitive_config_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: condition_config_attribute_config_id, primitive_config_id"""

    return uuid5(
        NS_REACTIVITY,
        f"aware:condition_config_primitive_config:{condition_config_attribute_config_id}:{primitive_config_id}",
    )


def stable_condition_config_relationship_config_id(
    *, condition_config_attribute_config_id: UUID, class_config_relationship_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: condition_config_attribute_config_id, class_config_relationship_id"""

    return uuid5(
        NS_REACTIVITY,
        f"aware:condition_config_relationship_config:{condition_config_attribute_config_id}:{class_config_relationship_id}",
    )


def stable_event_id(*, config_id: UUID, activation_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: config_id, activation_id"""

    return uuid5(NS_REACTIVITY, f"aware:event:{config_id}:{activation_id}")


def stable_event_condition_id(*, event_id: UUID, condition_id: UUID, config_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: event_id, condition_id, config_id"""

    return uuid5(NS_REACTIVITY, f"aware:event_condition:{event_id}:{condition_id}:{config_id}")


def stable_event_config_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_REACTIVITY, f"aware:event_config:{name_norm}")


def stable_event_config_action_config_id(*, event_config_id: UUID, action_config_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: event_config_id, action_config_id"""

    return uuid5(NS_REACTIVITY, f"aware:event_config_action_config:{event_config_id}:{action_config_id}")


def stable_event_config_condition_config_id(*, event_config_id: UUID, condition_config_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: event_config_id, condition_config_id"""

    return uuid5(NS_REACTIVITY, f"aware:event_config_condition_config:{event_config_id}:{condition_config_id}")


def stable_event_config_condition_config_scope_id(
    *, event_config_condition_config_id: UUID, object_instance_graph_identity_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: event_config_condition_config_id, object_instance_graph_identity_id"""

    return uuid5(
        NS_REACTIVITY,
        f"aware:event_config_condition_config_scope:{event_config_condition_config_id}:{object_instance_graph_identity_id}",
    )


def stable_event_config_condition_config_scope_event_id(
    *, event_config_condition_config_scope_id: UUID, event_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: event_config_condition_config_scope_id, event_id"""

    return uuid5(
        NS_REACTIVITY,
        f"aware:event_config_condition_config_scope_event:{event_config_condition_config_scope_id}:{event_id}",
    )


def stable_event_schedule_id(*, event_config_id: UUID, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: event_config_id, key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_REACTIVITY, f"aware:event_schedule:{event_config_id}:{key_norm}")


CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID: dict[str, tuple[str, tuple[str, ...]]] = {
    "0faf2317-32da-5417-b7b2-4803be6280db": ("stable_action_intent_id", ("event_id", "config_id", "intent_key")),
    "17951659-8fcd-5925-9655-326b91b68e75": ("stable_action_feedback_id", ("action_execution_id", "sequence")),
    "2080e6e6-492b-5cc8-9e48-1adb875e4930": (
        "stable_event_config_action_config_id",
        ("event_config_id", "action_config_id"),
    ),
    "3b5e95e6-71ec-5c22-a155-d58387b016c6": (
        "stable_event_config_condition_config_id",
        ("event_config_id", "condition_config_id"),
    ),
    "3fcc925b-0fec-5bb6-a730-7f69d3ea35c6": ("stable_action_id", ("event_id", "config_id")),
    "46116ca2-dc07-5464-9489-f19ad4368939": (
        "stable_event_config_condition_config_scope_id",
        ("event_config_condition_config_id", "object_instance_graph_identity_id"),
    ),
    "4ee96aab-24ad-5bec-be0f-46ef4e7ee8a5": ("stable_condition_config_id", ("name",)),
    "50bd4b3a-42b7-5914-afbb-9fb5cca5f192": (
        "stable_condition_config_relationship_config_id",
        ("condition_config_attribute_config_id", "class_config_relationship_id"),
    ),
    "5c2601fc-d9e5-5790-a289-6d0502e8eb4d": (
        "stable_condition_config_class_config_id",
        ("condition_config_id", "class_config_id"),
    ),
    "5c9eb8d9-0406-52af-bbd0-95fbb3c0bc98": ("stable_action_execution_id", ("action_intent_id", "execution_key")),
    "5d257356-b469-51eb-bbf3-9b21d86d8227": ("stable_event_id", ("config_id", "activation_id")),
    "745afee4-c250-5f5b-b9bf-d0c37f8a90a9": (
        "stable_condition_config_enum_option_id",
        ("condition_config_enum_config_id", "enum_option_id"),
    ),
    "83f84aaa-53fe-5982-940b-2ea82c41d6c8": ("stable_condition_id", ("config_id", "activation_id")),
    "8f9f10c8-f162-5ba9-b5f3-e2138970dea6": (
        "stable_event_config_condition_config_scope_event_id",
        ("event_config_condition_config_scope_id", "event_id"),
    ),
    "91fbd6a2-1659-5716-b7a0-65fcd2a5cdbf": ("stable_event_config_id", ("name",)),
    "ab2007f3-c925-5120-b72b-a746eb05a59b": ("stable_event_condition_id", ("event_id", "condition_id", "config_id")),
    "b84c4b54-fb17-5668-ba7e-172a58d19d41": (
        "stable_condition_config_attribute_config_id",
        ("condition_config_class_config_id", "attribute_config_id", "operator", "negate"),
    ),
    "dc27b639-66c8-5bca-9136-c00bc988ecdf": (
        "stable_condition_config_enum_config_id",
        ("condition_config_attribute_config_id", "enum_config_id"),
    ),
    "ee737ee5-7ddd-5c57-add0-85ffaff346ae": ("stable_action_config_id", ("name",)),
    "f9430ace-376f-5409-bc22-b6608d20ed27": (
        "stable_condition_config_primitive_config_id",
        ("condition_config_attribute_config_id", "primitive_config_id"),
    ),
}

__all__ = [
    "stable_action_id",
    "stable_action_config_id",
    "stable_action_execution_id",
    "stable_action_feedback_id",
    "stable_action_intent_id",
    "stable_condition_id",
    "stable_condition_config_id",
    "stable_condition_config_attribute_config_id",
    "stable_condition_config_class_config_id",
    "stable_condition_config_enum_config_id",
    "stable_condition_config_enum_option_id",
    "stable_condition_config_primitive_config_id",
    "stable_condition_config_relationship_config_id",
    "stable_event_id",
    "stable_event_condition_id",
    "stable_event_config_id",
    "stable_event_config_action_config_id",
    "stable_event_config_condition_config_id",
    "stable_event_config_condition_config_scope_id",
    "stable_event_config_condition_config_scope_event_id",
    "stable_event_schedule_id",
    "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID",
]
