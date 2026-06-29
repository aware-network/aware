from __future__ import annotations

"""Compatibility stable-id helpers for the Reactivity module (Python runtime).

Canonical stable-id formulas are compiler-owned and generated from:
- `workspaces/aware_kernel/modules/reactivity/ontology/structure/stable_ids.toml`

Generated module:
- `aware_reactivity_ontology.stable_ids`
"""

from uuid import NAMESPACE_URL, UUID, uuid5

try:
    from aware_reactivity_ontology.stable_ids import (  # type: ignore[import-not-found]  # noqa: F401
        NS_REACTIVITY,
        stable_action_config_id,
        stable_action_execution_id,
        stable_action_feedback_id,
        stable_action_id,
        stable_action_intent_id,
        stable_condition_config_attribute_config_id,
        stable_condition_config_class_config_id,
        stable_condition_config_enum_config_id,
        stable_condition_config_enum_option_id,
        stable_condition_config_id,
        stable_condition_config_primitive_config_id,
        stable_condition_config_relationship_config_id,
        stable_condition_id,
        stable_event_condition_id,
        stable_event_config_action_config_id,
        stable_event_config_condition_config_id,
        stable_event_config_condition_config_scope_id,
        stable_event_config_condition_config_scope_event_id,
        stable_event_config_id,
        stable_event_id,
    )
except ModuleNotFoundError:
    NS_REACTIVITY = uuid5(NAMESPACE_URL, "aware://reactivity/v1")

    def stable_condition_config_id(*, name: str) -> UUID:
        normalized_name = name.casefold().strip()
        return uuid5(NS_REACTIVITY, f"condition_config:{normalized_name}")

    def stable_event_config_id(*, name: str) -> UUID:
        normalized_name = name.casefold().strip()
        return uuid5(NS_REACTIVITY, f"event_config:{normalized_name}")

    def stable_action_config_id(*, name: str) -> UUID:
        normalized_name = name.casefold().strip()
        return uuid5(NS_REACTIVITY, f"action_config:{normalized_name}")

    def stable_event_config_condition_config_id(*, event_config_id: UUID, condition_config_id: UUID) -> UUID:
        return uuid5(
            NS_REACTIVITY,
            f"event_config_condition_config:{event_config_id}:{condition_config_id}",
        )

    def stable_event_config_condition_config_scope_id(
        *,
        event_config_condition_config_id: UUID,
        object_instance_graph_identity_id: UUID,
        object_instance_graph_branch_key: str = "all",
    ) -> UUID:
        branch_key_norm = (object_instance_graph_branch_key or "").casefold().strip() or "all"
        return uuid5(
            NS_REACTIVITY,
            "event_config_condition_config_scope:"
            f"{event_config_condition_config_id}:{object_instance_graph_identity_id}:{branch_key_norm}",
        )

    def stable_event_config_condition_config_scope_event_id(
        *,
        event_config_condition_config_scope_id: UUID,
        event_id: UUID,
    ) -> UUID:
        return uuid5(
            NS_REACTIVITY,
            "event_config_condition_config_scope_event:" f"{event_config_condition_config_scope_id}:{event_id}",
        )

    def stable_event_config_action_config_id(*, event_config_id: UUID, action_config_id: UUID) -> UUID:
        return uuid5(
            NS_REACTIVITY,
            f"event_config_action_config:{event_config_id}:{action_config_id}",
        )

    def stable_condition_id(*, config_id: UUID, activation_id: UUID) -> UUID:
        return uuid5(NS_REACTIVITY, f"condition:{config_id}:{activation_id}")

    def stable_event_id(*, config_id: UUID, activation_id: UUID) -> UUID:
        return uuid5(NS_REACTIVITY, f"event:{config_id}:{activation_id}")

    def stable_event_condition_id(*, event_id: UUID, condition_id: UUID, config_id: UUID) -> UUID:
        return uuid5(
            NS_REACTIVITY,
            f"event_condition:{event_id}:{condition_id}:{config_id}",
        )

    def stable_action_id(*, event_id: UUID, config_id: UUID) -> UUID:
        return uuid5(NS_REACTIVITY, f"action:{event_id}:{config_id}")

    def stable_action_intent_id(*, event_id: UUID, config_id: UUID, intent_key: str) -> UUID:
        intent_key_norm = (intent_key or "").casefold().strip()
        return uuid5(NS_REACTIVITY, f"aware:action_intent:{event_id}:{config_id}:{intent_key_norm}")

    def stable_action_execution_id(*, action_intent_id: UUID, execution_key: str = "primary") -> UUID:
        execution_key_norm = (execution_key or "").casefold().strip() or "primary"
        return uuid5(NS_REACTIVITY, f"aware:action_execution:{action_intent_id}:{execution_key_norm}")

    def stable_action_feedback_id(*, action_execution_id: UUID, sequence: int) -> UUID:
        return uuid5(NS_REACTIVITY, f"aware:action_feedback:{action_execution_id}:{sequence}")

    def stable_condition_config_class_config_id(*, condition_config_id: UUID, class_config_id: UUID) -> UUID:
        return uuid5(
            NS_REACTIVITY,
            f"condition_config_class_config:{condition_config_id}:{class_config_id}",
        )

    def stable_condition_config_attribute_config_id(
        *,
        condition_config_class_config_id: UUID,
        attribute_config_id: UUID,
        operator: str,
        negate: bool,
    ) -> UUID:
        return uuid5(
            NS_REACTIVITY,
            "condition_config_attribute_config:"
            f"{condition_config_class_config_id}:{attribute_config_id}:{operator}:{int(negate)}",
        )

    def stable_condition_config_primitive_config_id(
        *, condition_config_attribute_config_id: UUID, primitive_config_id: UUID
    ) -> UUID:
        return uuid5(
            NS_REACTIVITY,
            "condition_config_primitive_config:" f"{condition_config_attribute_config_id}:{primitive_config_id}",
        )

    def stable_condition_config_enum_config_id(
        *, condition_config_attribute_config_id: UUID, enum_config_id: UUID
    ) -> UUID:
        return uuid5(
            NS_REACTIVITY,
            f"condition_config_enum_config:{condition_config_attribute_config_id}:{enum_config_id}",
        )

    def stable_condition_config_enum_option_id(*, condition_config_enum_config_id: UUID, enum_option_id: UUID) -> UUID:
        return uuid5(
            NS_REACTIVITY,
            f"condition_config_enum_option:{condition_config_enum_config_id}:{enum_option_id}",
        )

    def stable_condition_config_relationship_config_id(
        *,
        condition_config_attribute_config_id: UUID,
        class_config_relationship_id: UUID,
    ) -> UUID:
        return uuid5(
            NS_REACTIVITY,
            "condition_config_relationship_config:"
            f"{condition_config_attribute_config_id}:{class_config_relationship_id}",
        )


__all__ = [
    "stable_condition_config_id",
    "stable_condition_config_class_config_id",
    "stable_condition_config_attribute_config_id",
    "stable_condition_config_primitive_config_id",
    "stable_condition_config_enum_config_id",
    "stable_condition_config_enum_option_id",
    "stable_condition_config_relationship_config_id",
    "stable_event_config_id",
    "stable_action_config_id",
    "stable_action_id",
    "stable_action_intent_id",
    "stable_action_execution_id",
    "stable_action_feedback_id",
    "stable_condition_id",
    "stable_event_config_condition_config_id",
    "stable_event_config_condition_config_scope_id",
    "stable_event_config_condition_config_scope_event_id",
    "stable_event_config_action_config_id",
    "stable_event_condition_id",
    "stable_event_id",
]
