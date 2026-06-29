from __future__ import annotations

from collections.abc import Sequence

from tree_sitter import Node

from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_code.language_service.features.completion_capabilities.contracts import CompletionItemDict
from aware_code.language_service.programs import parse_tree
from aware_code.language_service.text import extract_identifier_prefix
from aware_workspace.compiler.workspace import WorkspaceSnapshot


_ProjectionRecord = tuple[str, str | None, str, str, set[str], dict[str, set[str]]]


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


def _match_projection(
    *,
    symbol: str,
    projection_records: Sequence[_ProjectionRecord],
    known_packages: set[str],
    local_pkg: str | None,
) -> list[_ProjectionRecord]:
    token = (symbol or "").strip()
    if not token:
        return []
    qualifier_pkg: str | None = None
    symbol_ref = token
    if "." in token:
        prefix, last = token.rsplit(".", 1)
        prefix = (prefix or "").strip()
        last = (last or "").strip()
        if prefix in known_packages:
            qualifier_pkg = prefix
        symbol_ref = last

    symbol_ref = (symbol_ref or "").strip()

    hits: list[_ProjectionRecord] = []
    for rec in projection_records:
        _uri, pkg, symbol_name, projection_name, _obs, _views = rec
        if qualifier_pkg is not None and pkg != qualifier_pkg:
            continue
        if symbol_ref and symbol_name == symbol_ref:
            hits.append(rec)
            continue
        if token and projection_name == token:
            hits.append(rec)
            continue
        if projection_name and projection_name == symbol_ref:
            hits.append(rec)

    if qualifier_pkg is None and local_pkg is not None:
        preferred = [rec for rec in hits if rec[1] == local_pkg]
        if preferred:
            return preferred
    return hits


def collect_experience_context_completion_items(
    *,
    snapshot: WorkspaceSnapshot | None,
    uri: str,
    byte_offset: int,
    document_bytes: bytes,
) -> list[CompletionItemDict] | None:
    if snapshot is None:
        return None
    if not document_bytes or b"experience" not in document_bytes:
        return None

    code = snapshot.codes_by_uri.get(uri)
    if code is None:
        return None

    try:
        root = parse_tree(document_bytes=document_bytes)
    except Exception:
        return None

    ns_local = snapshot.namespace_by_code_id.get(code.id)
    local_pkg = ns_local.package if ns_local is not None else None

    projection_records: list[_ProjectionRecord] = []
    known_packages: set[str] = set()
    for other_uri, other_code in snapshot.codes_by_uri.items():
        ns_other = snapshot.namespace_by_code_id.get(other_code.id)
        other_pkg = ns_other.package if ns_other is not None else None
        if other_pkg:
            known_packages.add(other_pkg)
        for section in other_code.code_sections:
            if section.type != CodeSectionType.projection:
                continue
            proj = section.code_section_projection
            if proj is None:
                continue
            symbol_name = (proj.name or "").strip()
            projection_name = (proj.projection_name or "").strip()
            if not symbol_name and not projection_name:
                continue
            observable_keys: set[str] = set()
            observable_view_keys: dict[str, set[str]] = {}
            for view in proj.projection_views or []:
                full_key = (view.key or "").strip()
                if not full_key:
                    continue
                parts = [part for part in full_key.split(".") if part]
                if len(parts) < 2:
                    continue
                observable_name = ".".join(parts[:-1])
                view_name = parts[-1]
                observable_keys.add(observable_name)
                observable_view_keys.setdefault(observable_name, set()).add(view_name)
            projection_records.append(
                (
                    other_uri,
                    other_pkg,
                    symbol_name,
                    projection_name,
                    observable_keys,
                    observable_view_keys,
                )
            )

    cursor = max(int(byte_offset), 0)
    queue: list[Node] = [root]
    while queue:
        node = queue.pop()
        queue.extend(node.named_children)
        if node.type != "experience_def":
            continue
        if not _cursor_in_range(
            byte_offset=cursor,
            start=node.start_byte,
            end=node.end_byte,
        ):
            continue

        exp_projection_node = node.child_by_field_name("projection")
        exp_projection_ref = _node_text(exp_projection_node).strip()
        if exp_projection_node is not None and _cursor_in_range(
            byte_offset=cursor,
            start=exp_projection_node.start_byte,
            end=exp_projection_node.end_byte,
        ):
            allowed = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_."
            prefix = extract_identifier_prefix(
                document_bytes=document_bytes,
                byte_offset=cursor,
                segment_start=exp_projection_node.start_byte,
                segment_end=max(exp_projection_node.end_byte, cursor),
                allowed=allowed,
            ).strip()
            projection_items: list[CompletionItemDict] = []
            projection_seen: set[str] = set()
            for _u, pkg, symbol_name, projection_name, _obs, _views in projection_records:
                candidates = [symbol_name, projection_name]
                if pkg and symbol_name:
                    candidates.append(f"{pkg}.{symbol_name}")
                for label in candidates:
                    if not label or label in projection_seen:
                        continue
                    if prefix and not label.startswith(prefix):
                        continue
                    projection_seen.add(label)
                    projection_items.append({"label": label, "kind": 9})
            return projection_items

        matches = _match_projection(
            symbol=exp_projection_ref,
            projection_records=projection_records,
            known_packages=known_packages,
            local_pkg=local_pkg,
        )
        for exp_item in node.named_children:
            if exp_item.type != "experience_item":
                continue
            members = list(exp_item.named_children)
            if not members:
                continue
            item = members[0]
            if item.type != "experience_observable_group":
                continue

            observable_node = item.child_by_field_name("observable")
            observable_name = _node_text(observable_node).strip()
            if observable_node is not None and _cursor_in_range(
                byte_offset=cursor,
                start=observable_node.start_byte,
                end=observable_node.end_byte,
            ):
                allowed = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-"
                prefix = extract_identifier_prefix(
                    document_bytes=document_bytes,
                    byte_offset=cursor,
                    segment_start=observable_node.start_byte,
                    segment_end=max(observable_node.end_byte, cursor),
                    allowed=allowed,
                ).strip()
                observable_items: list[CompletionItemDict] = []
                observable_seen: set[str] = set()
                for _u, _pkg, _sym, _pname, observable_keys, _views in matches:
                    for label in sorted(observable_keys):
                        if not label or label in observable_seen:
                            continue
                        if prefix and not label.startswith(prefix):
                            continue
                        observable_seen.add(label)
                        observable_items.append({"label": label, "kind": 5})
                return observable_items

            for view_node in item.named_children:
                if view_node.type != "experience_view_def":
                    continue
                view_key_node = view_node.child_by_field_name("view_key")
                if view_key_node is None or not _cursor_in_range(
                    byte_offset=cursor,
                    start=view_key_node.start_byte,
                    end=view_key_node.end_byte,
                ):
                    continue
                allowed = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-"
                prefix = extract_identifier_prefix(
                    document_bytes=document_bytes,
                    byte_offset=cursor,
                    segment_start=view_key_node.start_byte,
                    segment_end=max(view_key_node.end_byte, cursor),
                    allowed=allowed,
                ).strip()
                view_items: list[CompletionItemDict] = []
                view_seen: set[str] = set()
                for _u, _pkg, _sym, _pname, _obs, observable_view_keys in matches:
                    for label in sorted(observable_view_keys.get(observable_name, set())):
                        if not label or label in view_seen:
                            continue
                        if prefix and not label.startswith(prefix):
                            continue
                        view_seen.add(label)
                        view_items.append({"label": label, "kind": 12})
                return view_items

    return None
