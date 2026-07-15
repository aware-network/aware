from __future__ import annotations

import copy
from datetime import datetime, timezone
import os
from collections.abc import Iterable
from uuid import UUID

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_history_ontology.commit.commit_enums import CommitStatus
from aware_meta_ontology.graph.instance.object_instance_graph import (
    ObjectInstanceGraph,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_meta_ontology.attribute.attribute import Attribute
from aware_meta_ontology.attribute.attribute_value import AttributeValue
from aware_meta_ontology.attribute.attribute_value_link import AttributeValueLink
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_instance_attribute import ClassInstanceAttribute
from aware_meta.graph.config.lane.telemetry import (
    SeedTimings,
    maybe_metric,
)
from aware_orm.session.autobind import disable_autobind

SYSTEM_ACTOR_ID = UUID(int=0)
SEED_CREATED_AT = datetime(1970, 1, 1, tzinfo=timezone.utc)
OCG_DELTA_HINT_VERSION = 1
DEFAULT_OCG_SOURCE_LANGUAGE = CodeLanguage("aware")
DEFAULT_OCG_COMMIT_STATUS = CommitStatus("local")


def clone_object_instance_graph_for_validation(
    graph: ObjectInstanceGraph,
    *,
    changes: Iterable[ObjectInstanceGraphChange] | None = None,
    timings: SeedTimings | None = None,
    metric_prefix: str = "ocg_delta_validation",
) -> ObjectInstanceGraph:
    """Clone OIG for apply+hash validation with a selective copy-on-write rail."""
    prefix = (metric_prefix or "").strip() or "ocg_delta_validation"

    changed_class_instance_ids: set[UUID] = set()
    has_relationship_changes = False
    has_change_payload = False
    if changes is not None:
        for change_tree in changes:
            has_change_payload = True
            for ci_change in change_tree.class_instance_changes or []:
                changed_class_instance_ids.add(ci_change.class_instance_id)
            if change_tree.class_instance_relationship_changes:
                has_relationship_changes = True

    if has_change_payload:
        clone_all_class_instances = not (
            changed_class_instance_ids or has_relationship_changes
        )
        cloned = clone_object_instance_graph_model_for_validation(
            graph,
            changed_class_instance_ids=changed_class_instance_ids,
            clone_all_class_instances=clone_all_class_instances,
        )
        maybe_metric(timings, f"{prefix}_clone_mode", "selective")
        maybe_metric(
            timings,
            f"{prefix}_changed_class_instances",
            len(changed_class_instance_ids),
        )
        maybe_metric(
            timings,
            f"{prefix}_has_relationship_changes",
            has_relationship_changes,
        )
        maybe_metric(
            timings,
            f"{prefix}_clone_all_class_instances",
            clone_all_class_instances,
        )
        return cloned

    try:
        cloned = copy.deepcopy(graph)
        maybe_metric(timings, f"{prefix}_clone_mode", "deepcopy")
        return cloned
    except Exception:
        cloned = graph.model_copy(deep=True)
        maybe_metric(timings, f"{prefix}_clone_mode", "model_copy_deep")
        return cloned


def clone_object_instance_graph_model_for_validation(
    graph: ObjectInstanceGraph,
    *,
    changed_class_instance_ids: Iterable[UUID] | None = None,
    clone_all_class_instances: bool = False,
) -> ObjectInstanceGraph:
    """Clone an OIG through public model fields without copying ORM runtime state."""
    changed_ids = set(changed_class_instance_ids or ())
    with disable_autobind():
        cloned = graph.model_copy(deep=False)
    cloned.class_instances = [
        (
            _clone_class_instance_for_validation(ci)
            if clone_all_class_instances or ci.id in changed_ids
            else ci
        )
        for ci in graph.class_instances
    ]
    cloned.class_instance_relationships = list(graph.class_instance_relationships)
    for ci in cloned.class_instances:
        if ci.id == cloned.root_class_instance_id:
            cloned.root_class_instance = ci
            break
    return cloned


def _clone_class_instance_for_validation(
    class_instance: ClassInstance,
) -> ClassInstance:
    with disable_autobind():
        return ClassInstance.model_construct(
            id=class_instance.id,
            object_instance_graph_id=class_instance.object_instance_graph_id,
            class_config_id=class_instance.class_config_id,
            class_config=class_instance.class_config,
            source_object_id=class_instance.source_object_id,
            class_instance_attributes=[
                _clone_class_instance_attribute_for_validation(edge)
                for edge in (class_instance.class_instance_attributes or [])
            ],
            class_instance_changes=[],
        )


def _clone_class_instance_attribute_for_validation(
    edge: ClassInstanceAttribute,
) -> ClassInstanceAttribute:
    with disable_autobind():
        return ClassInstanceAttribute.model_construct(
            id=edge.id,
            class_instance_id=edge.class_instance_id,
            attribute_id=edge.attribute_id,
            attribute=(
                _clone_attribute_for_validation(edge.attribute)
                if edge.attribute is not None
                else None
            ),
        )


def _clone_attribute_for_validation(attribute: Attribute) -> Attribute:
    with disable_autobind():
        return Attribute.model_construct(
            id=attribute.id,
            owner_key=attribute.owner_key,
            attribute_config_id=attribute.attribute_config_id,
            attribute_config=attribute.attribute_config,
            attribute_changes=[],
            value_root_id=attribute.value_root_id,
            value_root=(
                _clone_attribute_value_for_validation(attribute.value_root)
                if attribute.value_root is not None
                else None
            ),
        )


def _clone_attribute_value_for_validation(value: AttributeValue) -> AttributeValue:
    with disable_autobind():
        return AttributeValue.model_construct(
            id=value.id,
            type_descriptor=value.type_descriptor,
            type_descriptor_id=value.type_descriptor_id,
            attribute_value_changes=[],
            child_links=[
                _clone_attribute_value_link_for_validation(link)
                for link in (value.child_links or [])
            ],
            enum_option=value.enum_option,
            enum_option_id=value.enum_option_id,
            class_instance=value.class_instance,
            class_instance_id=value.class_instance_id,
            inline_value_instance=value.inline_value_instance,
            inline_value_instance_id=value.inline_value_instance_id,
            primitive_value=value.primitive_value,
        )


def _clone_attribute_value_link_for_validation(
    link: AttributeValueLink,
) -> AttributeValueLink:
    with disable_autobind():
        return AttributeValueLink.model_construct(
            id=link.id,
            attribute_value_id=link.attribute_value_id,
            child_id=link.child_id,
            child=(
                _clone_attribute_value_for_validation(link.child)
                if link.child is not None
                else None
            ),
            role=link.role,
            position=link.position,
            identity_key=link.identity_key,
            attribute_value_link_changes=[],
        )


def count_object_instance_graph_change_operations(
    changes: Iterable[ObjectInstanceGraphChange],
) -> int:
    """Count nested change operations, not just root change envelopes."""
    count = 0
    for change_tree in changes:
        count += 1
        count += len(change_tree.class_instance_relationship_changes or [])
        for class_change in change_tree.class_instance_changes or []:
            count += 1
            count += len(class_change.attribute_changes or [])
            for attribute_change in class_change.attribute_changes or []:
                count += _count_attribute_value_change_operations(
                    attribute_change.value_root_change
                )
    return count


def _count_attribute_value_change_operations(change: object | None) -> int:
    if change is None:
        return 0
    count = 1
    link_changes = getattr(change, "attribute_value_link_changes", None) or []
    count += len(link_changes)
    for link_change in link_changes:
        count += _count_attribute_value_change_operations(
            getattr(link_change, "child_attribute_value_change", None)
        )
    return count


def bool_env_default_true(name: str) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    if raw in {"0", "false", "no", "off"}:
        return False
    return True
