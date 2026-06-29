from __future__ import annotations

from tree_sitter import Node

from aware_code.language_service.features.navigation_capabilities.contracts import (
    CursorInRangeMatcher,
    NodeTextReader,
)
from aware_code.language_service.position import ByteRange
from aware_code.language_service.programs import parse_tree
from aware_code.language_service.types import DefinitionTarget


def collect_environment_definition_targets(
    *,
    uri: str,
    byte_offset: int,
    document_bytes: bytes,
    cursor_in_range: CursorInRangeMatcher,
    node_text: NodeTextReader,
) -> list[DefinitionTarget]:
    if not document_bytes or b"environment" not in document_bytes:
        return []

    try:
        root = parse_tree(document_bytes=document_bytes)
    except Exception:
        return []

    def _local_def_targets_for(node_type: str, symbol: str) -> list[DefinitionTarget]:
        token = (symbol or "").strip()
        if not token:
            return []
        key = token.rsplit(".", 1)[-1]
        targets: list[DefinitionTarget] = []
        queue_local: list[Node] = [root]
        while queue_local:
            node = queue_local.pop()
            queue_local.extend(node.named_children)
            if node.type != node_type:
                continue
            name_node = node.child_by_field_name("name")
            if name_node is None or name_node.end_byte <= name_node.start_byte:
                continue
            name = node_text(name_node).strip()
            if name not in {token, key}:
                continue
            targets.append(
                DefinitionTarget(
                    uri=uri,
                    range=ByteRange(
                        start=name_node.start_byte,
                        end=name_node.end_byte,
                    ),
                )
            )
        return targets

    cursor = max(int(byte_offset), 0)
    queue: list[Node] = [root]
    while queue:
        node = queue.pop()
        queue.extend(node.named_children)
        if node.type != "environment_def":
            continue
        if not cursor_in_range(
            byte_offset=cursor,
            start=node.start_byte,
            end=node.end_byte,
        ):
            continue

        for env_item in node.named_children:
            if env_item.type != "environment_item":
                continue
            members = list(env_item.named_children)
            if not members:
                continue
            inner = members[0]
            if inner.type != "environment_event_stmt":
                continue

            event_node = inner.child_by_field_name("event")
            if event_node is not None and cursor_in_range(
                byte_offset=cursor,
                start=event_node.start_byte,
                end=event_node.end_byte,
            ):
                event_ref = node_text(event_node).strip()
                return _local_def_targets_for("event_def", event_ref)

            for action_stmt in inner.named_children:
                if action_stmt.type != "environment_event_action_stmt":
                    continue
                action_node = action_stmt.child_by_field_name("action")
                if action_node is None or not cursor_in_range(
                    byte_offset=cursor,
                    start=action_node.start_byte,
                    end=action_node.end_byte,
                ):
                    continue
                action_ref = node_text(action_node).strip()
                return _local_def_targets_for("action_def", action_ref)

    return []
