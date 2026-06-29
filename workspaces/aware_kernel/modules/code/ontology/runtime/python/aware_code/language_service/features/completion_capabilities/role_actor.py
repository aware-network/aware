from __future__ import annotations

from tree_sitter import Node

from aware_code.language_service.features.completion_capabilities.contracts import CompletionItemDict
from aware_code.language_service.programs import parse_tree
from aware_code.language_service.text import extract_identifier_prefix
from aware_workspace.compiler.workspace import WorkspaceSnapshot


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


def collect_role_actor_context_completion_items(
    *,
    snapshot: WorkspaceSnapshot | None,
    uri: str,
    byte_offset: int,
    document_bytes: bytes,
) -> list[CompletionItemDict] | None:
    if snapshot is None:
        return None
    if not document_bytes or (b"role" not in document_bytes and b"actor" not in document_bytes):
        return None

    code = snapshot.codes_by_uri.get(uri)
    if code is None:
        return None
    scope = snapshot.fqn_resolver.scope_for_code_id(code.id)

    try:
        root = parse_tree(document_bytes=document_bytes)
    except Exception:
        return None

    role_names: set[str] = set()
    queue: list[Node] = [root]
    while queue:
        node = queue.pop()
        queue.extend(node.named_children)
        if node.type != "role_def":
            continue
        name_node = node.child_by_field_name("name")
        name = _node_text(name_node).strip()
        if name:
            role_names.add(name)

    cursor = max(int(byte_offset), 0)
    queue = [root]
    while queue:
        node = queue.pop()
        queue.extend(node.named_children)

        if node.type == "actor_def" and _cursor_in_range(
            byte_offset=cursor,
            start=node.start_byte,
            end=node.end_byte,
        ):
            for child in node.named_children:
                if child.type != "actor_role_stmt":
                    continue
                role_node = child.child_by_field_name("role")
                if role_node is None or not _cursor_in_range(
                    byte_offset=cursor,
                    start=role_node.start_byte,
                    end=role_node.end_byte,
                ):
                    continue
                allowed = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_."
                prefix = extract_identifier_prefix(
                    document_bytes=document_bytes,
                    byte_offset=cursor,
                    segment_start=role_node.start_byte,
                    segment_end=max(role_node.end_byte, cursor),
                    allowed=allowed,
                ).strip()
                role_items: list[CompletionItemDict] = []
                for name in sorted(role_names):
                    if prefix and not name.startswith(prefix):
                        continue
                    role_items.append({"label": name, "kind": 14})
                return role_items

        if node.type == "role_def" and _cursor_in_range(
            byte_offset=cursor,
            start=node.start_byte,
            end=node.end_byte,
        ):
            for child in node.named_children:
                if child.type != "role_capability_stmt":
                    continue
                target_node = child.child_by_field_name("target")
                if target_node is None or not _cursor_in_range(
                    byte_offset=cursor,
                    start=target_node.start_byte,
                    end=target_node.end_byte,
                ):
                    continue
                allowed = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_."
                prefix = extract_identifier_prefix(
                    document_bytes=document_bytes,
                    byte_offset=cursor,
                    segment_start=target_node.start_byte,
                    segment_end=max(target_node.end_byte, cursor),
                    allowed=allowed,
                ).strip()

                if "." in prefix:
                    owner_ref, fn_prefix = prefix.rsplit(".", 1)
                    owner_ref = owner_ref.strip()
                    fn_prefix = fn_prefix.strip()
                    resolved = scope.try_resolve_class_with_fqn(owner_ref)
                    if resolved is None:
                        return []
                    _fqn, class_cfg = resolved
                    cls = class_cfg.code_section_class
                    if cls is None:
                        return []
                    method_items: list[CompletionItemDict] = []
                    for fn in cls.code_section_functions:
                        fn_name = (fn.name or "").strip()
                        if not fn_name:
                            continue
                        if fn_prefix and not fn_name.startswith(fn_prefix):
                            continue
                        method_items.append(
                            {
                                "label": fn_name,
                                "kind": 2,
                                "detail": f"{owner_ref}.{fn_name}",
                            }
                        )
                    return method_items

                class_items: list[CompletionItemDict] = []
                class_seen: set[str] = set()
                for class_fqn in sorted(snapshot.fqn_resolver.classes_by_fqn):
                    class_ref = (class_fqn or "").strip()
                    if not class_ref:
                        continue
                    class_symbol = class_ref.rsplit(".", 1)[-1]
                    candidates = [class_symbol, class_ref]
                    for label in candidates:
                        if not label or label in class_seen:
                            continue
                        if prefix and not label.startswith(prefix):
                            continue
                        class_seen.add(label)
                        class_items.append({"label": label, "kind": 7})
                return class_items

    return None
