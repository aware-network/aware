from __future__ import annotations

from tree_sitter import Node

from aware_code.language_service.features.completion_capabilities.contracts import CompletionItemDict
from aware_code.language_service.programs import parse_tree
from aware_code.language_service.text import extract_identifier_prefix


def _cursor_in_range(*, byte_offset: int, start: int, end: int) -> bool:
    if end <= start:
        return False
    cursor = int(byte_offset)
    if cursor < start:
        return False
    if cursor > end:
        return False
    if cursor == end and cursor > start:
        cursor -= 1
    return start <= cursor < end


def _node_text(node: Node | None) -> str:
    if node is None or node.text is None:
        return ""
    return node.text.decode("utf-8", errors="replace")


def collect_environment_context_completion_items(
    *,
    byte_offset: int,
    document_bytes: bytes,
) -> list[CompletionItemDict] | None:
    if not document_bytes or b"environment" not in document_bytes:
        return None

    try:
        root = parse_tree(document_bytes=document_bytes)
    except Exception:
        return None

    event_names: set[str] = set()
    action_names: set[str] = set()
    queue: list[Node] = [root]
    while queue:
        node = queue.pop()
        queue.extend(node.named_children)
        if node.type == "event_def":
            name_node = node.child_by_field_name("name")
            name = _node_text(name_node).strip()
            if name:
                event_names.add(name)
        elif node.type == "action_def":
            name_node = node.child_by_field_name("name")
            name = _node_text(name_node).strip()
            if name:
                action_names.add(name)

    cursor = max(int(byte_offset), 0)
    queue = [root]
    while queue:
        node = queue.pop()
        queue.extend(node.named_children)
        if node.type != "environment_def":
            continue
        if not _cursor_in_range(
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
            if event_node is not None and _cursor_in_range(
                byte_offset=cursor,
                start=event_node.start_byte,
                end=event_node.end_byte,
            ):
                allowed = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_."
                prefix = extract_identifier_prefix(
                    document_bytes=document_bytes,
                    byte_offset=cursor,
                    segment_start=event_node.start_byte,
                    segment_end=max(event_node.end_byte, cursor),
                    allowed=allowed,
                ).strip()
                event_items: list[CompletionItemDict] = []
                for name in sorted(event_names):
                    if prefix and not name.startswith(prefix):
                        continue
                    event_items.append({"label": name, "kind": 14})
                return event_items

            for action_stmt in inner.named_children:
                if action_stmt.type != "environment_event_action_stmt":
                    continue
                action_node = action_stmt.child_by_field_name("action")
                if action_node is None or not _cursor_in_range(
                    byte_offset=cursor,
                    start=action_node.start_byte,
                    end=action_node.end_byte,
                ):
                    continue
                allowed = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_."
                prefix = extract_identifier_prefix(
                    document_bytes=document_bytes,
                    byte_offset=cursor,
                    segment_start=action_node.start_byte,
                    segment_end=max(action_node.end_byte, cursor),
                    allowed=allowed,
                ).strip()
                action_items: list[CompletionItemDict] = []
                for name in sorted(action_names):
                    if prefix and not name.startswith(prefix):
                        continue
                    action_items.append({"label": name, "kind": 14})
                return action_items

    return None
