from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from aware_meta_ontology.attribute.attribute_value_change import AttributeValueChange
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)

from aware_meta.graph.instance.change.descriptor import describe_oig_changes
from aware_meta.graph.instance.change.narrator import narrate_change_descriptors
from aware_meta.graph.instance.change.ocg_descriptor_spec import OcgDescriptorSpec


@dataclass(frozen=True, slots=True)
class CommitChangeTreeSummary:
    oig_changes: int
    class_instance_changes: int
    attribute_changes: int
    value_root_changes: int
    value_link_changes: int
    relationship_changes: int
    change_deltas: int

    def to_dict(self) -> dict[str, int]:
        return {
            "oig_changes": self.oig_changes,
            "class_instance_changes": self.class_instance_changes,
            "attribute_changes": self.attribute_changes,
            "value_root_changes": self.value_root_changes,
            "value_link_changes": self.value_link_changes,
            "relationship_changes": self.relationship_changes,
            "change_deltas": self.change_deltas,
        }


def summarize_oig_change_tree(*, changes: Iterable[ObjectInstanceGraphChange]) -> CommitChangeTreeSummary:
    """Return compact typed counts for an OIG change payload."""
    changes_list = list(changes)
    class_instance_changes = 0
    attribute_changes = 0
    value_root_changes = 0
    value_link_changes = 0
    relationship_changes = 0
    change_deltas = 0

    for oig_change in changes_list:
        change_deltas += len(oig_change.change.change_deltas or [])

        rel_changes = list(oig_change.class_instance_relationship_changes or [])
        relationship_changes += len(rel_changes)
        for rel_change in rel_changes:
            change_deltas += len(rel_change.change.change_deltas or [])

        ci_changes = list(oig_change.class_instance_changes or [])
        class_instance_changes += len(ci_changes)
        for ci_change in ci_changes:
            change_deltas += len(ci_change.change.change_deltas or [])

            attr_changes = list(ci_change.attribute_changes or [])
            attribute_changes += len(attr_changes)
            for attr_change in attr_changes:
                change_deltas += len(attr_change.change.change_deltas or [])
                value_root_change = attr_change.value_root_change
                if value_root_change is None:
                    continue

                value_root_changes += 1
                links_count, deltas_count = _count_value_change_tree(value_change=value_root_change)
                value_link_changes += links_count
                change_deltas += deltas_count

    return CommitChangeTreeSummary(
        oig_changes=len(changes_list),
        class_instance_changes=class_instance_changes,
        attribute_changes=attribute_changes,
        value_root_changes=value_root_changes,
        value_link_changes=value_link_changes,
        relationship_changes=relationship_changes,
        change_deltas=change_deltas,
    )


def summarize_commit_change_tree(*, commit: ObjectInstanceGraphCommit) -> CommitChangeTreeSummary:
    """Return compact typed counts for an OIG commit payload."""
    return summarize_oig_change_tree(changes=list(commit.object_instance_graph_changes or []))


def _count_value_change_tree(*, value_change: AttributeValueChange) -> tuple[int, int]:
    """Return (link_count, delta_count) recursively for a value-change tree."""
    link_count = 0
    delta_count = len(value_change.change.change_deltas or [])
    for link_change in value_change.attribute_value_link_changes:
        link_count += 1
        delta_count += len(link_change.change.change_deltas or [])
        child_change = link_change.child_attribute_value_change
        if child_change is not None:
            child_links, child_deltas = _count_value_change_tree(value_change=child_change)
            link_count += child_links
            delta_count += child_deltas
    return link_count, delta_count


def build_change_semantics_payload(
    *,
    changes: Iterable[ObjectInstanceGraphChange],
    ocg_descriptor_spec: OcgDescriptorSpec | None = None,
    include_descriptors: bool,
    max_narration_lines: int = 200,
    max_descriptors: int = 200,
) -> dict[str, object]:
    """Build canonical semantic summary payload for arbitrary OIG change trees."""
    changes_list = list(changes)
    changes_payload = [change.model_dump(mode="json", exclude_none=True) for change in changes_list]
    descriptors = describe_oig_changes(
        changes_payload=changes_payload,
        ocg_descriptor_spec=ocg_descriptor_spec,
    )
    narration = narrate_change_descriptors(descriptors)

    kind_counts = Counter(descriptor.kind for descriptor in descriptors)
    op_counts = Counter(descriptor.op for descriptor in descriptors)

    out: dict[str, object] = {
        "descriptor_count": len(descriptors),
        "descriptor_kind_counts": {k: int(v) for k, v in sorted(kind_counts.items())},
        "descriptor_op_counts": {k: int(v) for k, v in sorted(op_counts.items())},
        "narration_lines": narration[:max_narration_lines],
    }
    if len(narration) > max_narration_lines:
        out["narration_truncated_lines"] = len(narration) - max_narration_lines

    if include_descriptors:
        descriptor_items = [descriptor.to_dict() for descriptor in descriptors]
        out["descriptors"] = descriptor_items[:max_descriptors]
        if len(descriptor_items) > max_descriptors:
            out["descriptors_truncated_items"] = len(descriptor_items) - max_descriptors

    return out


def build_commit_semantics_payload(
    *,
    commit: ObjectInstanceGraphCommit,
    ocg_descriptor_spec: OcgDescriptorSpec | None = None,
    include_descriptors: bool,
    max_narration_lines: int = 200,
    max_descriptors: int = 200,
) -> dict[str, object]:
    """Build canonical semantic summary payload for a single OIG commit."""
    return build_change_semantics_payload(
        changes=commit.object_instance_graph_changes,
        ocg_descriptor_spec=ocg_descriptor_spec,
        include_descriptors=include_descriptors,
        max_narration_lines=max_narration_lines,
        max_descriptors=max_descriptors,
    )


__all__ = [
    "CommitChangeTreeSummary",
    "build_change_semantics_payload",
    "build_commit_semantics_payload",
    "summarize_oig_change_tree",
    "summarize_commit_change_tree",
]
