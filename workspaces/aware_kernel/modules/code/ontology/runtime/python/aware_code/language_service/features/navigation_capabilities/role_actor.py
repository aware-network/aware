from __future__ import annotations

from tree_sitter import Node

from aware_code.language_service.features.navigation_capabilities.contracts import (
    ClassDefinitionTargetResolver,
    CursorInRangeMatcher,
    FunctionDefinitionTargetResolver,
    NodeTextReader,
)
from aware_code.language_service.position import ByteRange
from aware_code.language_service.programs import parse_tree
from aware_code.language_service.types import DefinitionTarget
from aware_workspace.compiler.workspace import WorkspaceSnapshot


def collect_role_actor_definition_targets(
    *,
    snapshot: WorkspaceSnapshot | None,
    uri: str,
    byte_offset: int,
    document_bytes: bytes,
    cursor_in_range: CursorInRangeMatcher,
    node_text: NodeTextReader,
    class_definition_target: ClassDefinitionTargetResolver,
    function_definition_target: FunctionDefinitionTargetResolver,
) -> list[DefinitionTarget]:
    if snapshot is None:
        return []
    if not document_bytes or (b"role" not in document_bytes and b"actor" not in document_bytes):
        return []

    code = snapshot.codes_by_uri.get(uri)
    if code is None:
        return []
    scope = snapshot.fqn_resolver.scope_for_code_id(code.id)

    try:
        root = parse_tree(document_bytes=document_bytes)
    except Exception:
        return []

    def _local_role_targets_for(symbol: str) -> list[DefinitionTarget]:
        token = (symbol or "").strip()
        if not token:
            return []
        key = token.rsplit(".", 1)[-1]
        targets: list[DefinitionTarget] = []
        queue_local: list[Node] = [root]
        while queue_local:
            node = queue_local.pop()
            queue_local.extend(node.named_children)
            if node.type != "role_def":
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

    def _role_capability_targets_for(target_ref: str) -> list[DefinitionTarget]:
        token = (target_ref or "").strip()
        if not token or "." not in token:
            return []
        owner_ref, fn_name = token.rsplit(".", 1)
        owner_ref = owner_ref.strip()
        fn_name = fn_name.strip()
        if not owner_ref:
            return []
        resolved = scope.try_resolve_class_with_fqn(owner_ref)
        if resolved is None:
            return []
        _fqn, class_cfg = resolved
        cls = class_cfg.code_section_class
        if cls is None:
            return []
        if fn_name:
            fn = next(
                (candidate for candidate in cls.code_section_functions if candidate.name == fn_name),
                None,
            )
            if fn is not None:
                target = function_definition_target(fn)
                return [target] if target is not None else []
        class_target = class_definition_target(class_cfg)
        return [class_target] if class_target is not None else []

    cursor = max(int(byte_offset), 0)
    queue: list[Node] = [root]
    while queue:
        node = queue.pop()
        queue.extend(node.named_children)
        if node.type == "role_def" and cursor_in_range(
            byte_offset=cursor,
            start=node.start_byte,
            end=node.end_byte,
        ):
            for child in node.named_children:
                if child.type != "role_capability_stmt":
                    continue
                target_node = child.child_by_field_name("target")
                if target_node is None or not cursor_in_range(
                    byte_offset=cursor,
                    start=target_node.start_byte,
                    end=target_node.end_byte,
                ):
                    continue
                target_ref = node_text(target_node).strip()
                return _role_capability_targets_for(target_ref)

        if node.type == "actor_def" and cursor_in_range(
            byte_offset=cursor,
            start=node.start_byte,
            end=node.end_byte,
        ):
            for child in node.named_children:
                if child.type != "actor_role_stmt":
                    continue
                role_node = child.child_by_field_name("role")
                if role_node is None or not cursor_in_range(
                    byte_offset=cursor,
                    start=role_node.start_byte,
                    end=role_node.end_byte,
                ):
                    continue
                role_ref = node_text(role_node).strip()
                return _local_role_targets_for(role_ref)

    return []
