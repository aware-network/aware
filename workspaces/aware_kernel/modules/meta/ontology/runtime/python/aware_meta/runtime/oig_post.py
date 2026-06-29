"""Meta-owned OIG post-state materialization."""

from __future__ import annotations

import copy
from collections.abc import Iterable, Mapping
from uuid import UUID

from aware_history_ontology.change.change_enums import ChangeType
from aware_meta.graph.instance.apply import apply_object_instance_graph_changes
from aware_meta.graph.instance.hash import compute_hash
from aware_meta.graph.instance.index import build_index
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.instance.object_instance_graph import (
    ObjectInstanceGraph,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)


def materialize_meta_oig_post(
    *,
    before_oig: ObjectInstanceGraph,
    changes: Iterable[ObjectInstanceGraphChange],
    attribute_configs_by_id: Mapping[UUID, AttributeConfig],
    class_configs_by_id: Mapping[UUID, ClassConfig] | None = None,
) -> ObjectInstanceGraph:
    """Build OIG(post) by applying deltas to a selective copy of OIG(pre)."""

    change_tuple = tuple(changes)
    after_oig = before_oig.model_copy(deep=False)
    after_oig.class_instances = list(before_oig.class_instances)
    after_oig.class_instance_relationships = list(
        before_oig.class_instance_relationships,
    )

    update_ids: set[UUID] = set()
    for root_change in change_tuple:
        for class_instance_change in root_change.class_instance_changes:
            if class_instance_change.change.type == ChangeType.update:
                update_ids.add(class_instance_change.class_instance_id)

    if update_ids:
        positions = {
            class_instance.id: position
            for position, class_instance in enumerate(after_oig.class_instances)
        }
        for instance_id in sorted(update_ids, key=str):
            position = positions.get(instance_id)
            if position is None:
                continue
            after_oig.class_instances[position] = copy.deepcopy(
                after_oig.class_instances[position],
            )

    apply_object_instance_graph_changes(
        graph=after_oig,
        changes=change_tuple,
        attribute_configs_by_id=attribute_configs_by_id,
        class_configs_by_id=class_configs_by_id,
    )
    after_index = build_index(after_oig)
    after_oig.hash = compute_hash(after_oig, index=after_index)
    return after_oig


__all__ = ["materialize_meta_oig_post"]
