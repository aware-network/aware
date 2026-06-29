from __future__ import annotations

import json
from collections.abc import Iterable

from aware_meta.graph.instance.change.descriptor import CommitChangeDescriptor


def narrate_change_descriptors(
    descriptors: Iterable[CommitChangeDescriptor],
) -> list[str]:
    """Default deterministic narrator for commit delta descriptors."""
    lines: list[str] = []
    for d in descriptors:
        if d.kind == "class_instance":
            cls = d.class_name or (str(d.class_config_id) if d.class_config_id else "<class>")
            inst = str(d.class_instance_id) if d.class_instance_id else "<instance>"
            if d.op == "create":
                lines.append(f"Created {cls} ({inst})")
            elif d.op == "delete":
                lines.append(f"Deleted {cls} ({inst})")
            else:
                lines.append(f"Updated {cls} ({inst})")
            continue

        if d.kind == "attribute_value":
            cls = d.class_name or (str(d.class_config_id) if d.class_config_id else "<class>")
            attr = d.attribute_name or (str(d.attribute_config_id) if d.attribute_config_id else "<attribute>")
            path = d.path or attr

            if d.value_kind is None:
                lines.append(f"{cls}.{path} updated")
                continue

            if d.value_kind == "complex":
                lines.append(f"{cls}.{path} updated")
                continue

            value = _format_value(d.value)
            if d.op == "create":
                lines.append(f"{cls}.{path} = {value} (created)")
            elif d.op == "delete":
                lines.append(f"{cls}.{path} deleted")
            else:
                lines.append(f"{cls}.{path} = {value}")
            continue

        if d.kind == "relationship":
            count = d.details.get("relationship_change_count")
            lines.append(f"Relationship changes: {count}")
            continue

        lines.append(f"Change: {d.kind} {d.op}")

    return lines


def _format_value(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, (str, int, float, bool)):
        return json.dumps(value, ensure_ascii=False)
    return json.dumps(value, default=str, ensure_ascii=False)
