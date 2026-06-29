from __future__ import annotations

from dataclasses import dataclass

from tree_sitter import Node

from aware_code.language_service.features.navigation_capabilities.contracts import (
    ClassDefinitionTargetResolver,
    CursorInRangeMatcher,
    ExperienceNodeTargetResolver,
    FunctionDefinitionTargetResolver,
    NodeTextReader,
    SymbolTargetResolver,
)
from aware_code.language_service.position import ByteRange
from aware_code.language_service.programs import (
    find_program_call_target_at,
    intrinsic_signature,
    iter_program_body_statements,
    iter_program_defs,
    parse_tree,
    resolve_owner_to_class,
)
from aware_code.language_service.types import DefinitionTarget
from aware_workspace.compiler.workspace import WorkspaceSnapshot


@dataclass(frozen=True, slots=True)
class _PortNodeMapping:
    alias_node: Node


def collect_program_call_definition_targets(
    *,
    snapshot: WorkspaceSnapshot | None,
    uri: str,
    byte_offset: int,
    document_bytes: bytes,
    class_definition_target: ClassDefinitionTargetResolver,
    function_definition_target: FunctionDefinitionTargetResolver,
) -> list[DefinitionTarget]:
    if snapshot is None:
        return []
    if uri not in snapshot.codes_by_uri:
        return []
    if not document_bytes or b"program" not in document_bytes:
        return []

    try:
        root = parse_tree(document_bytes=document_bytes)
        call_at = find_program_call_target_at(root=root, byte_offset=byte_offset)
        if call_at is None and byte_offset > 0:
            call_at = find_program_call_target_at(root=root, byte_offset=byte_offset - 1)
    except Exception:
        return []

    if call_at is None:
        return []

    target = (call_at.target or "").strip()
    if not target:
        return []
    if intrinsic_signature(target) is not None:
        return []

    start = call_at.target_range.start
    end = call_at.target_range.end
    if end <= start:
        return []
    cursor = max(min(byte_offset, end), start)
    if cursor == end and cursor > start:
        cursor -= 1

    target_bytes = document_bytes[start:end]
    last_dot = target_bytes.rfind(b".")
    if last_dot <= 0:
        return []

    # Cursor on the owner portion navigates to the class; on the final segment navigates to the function.
    dot_abs = start + last_dot
    parts = [p for p in target.split(".") if p]
    if len(parts) < 2:
        return []
    owner = ".".join(parts[:-1])
    fn_name = parts[-1]

    res = resolve_owner_to_class(owner=owner, classes_by_fqn=snapshot.fqn_resolver.classes_by_fqn)
    if res.status != "ok" or res.class_cfg is None:
        return []

    if cursor <= dot_abs:
        class_target = class_definition_target(res.class_cfg)
        return [class_target] if class_target is not None else []

    cls = res.class_cfg.code_section_class
    if cls is None:
        return []
    for fn in cls.code_section_functions:
        if fn.name == fn_name:
            fn_target = function_definition_target(fn)
            return [fn_target] if fn_target is not None else []
    return []


def collect_program_topology_definition_targets(
    *,
    snapshot: WorkspaceSnapshot | None,
    uri: str,
    byte_offset: int,
    document_bytes: bytes,
    cursor_in_range: CursorInRangeMatcher,
    node_text: NodeTextReader,
    experience_targets_by_symbol: SymbolTargetResolver,
    experience_view_targets_by_symbol: SymbolTargetResolver,
    experience_node_targets_by_symbol: ExperienceNodeTargetResolver,
    projection_targets_by_symbol: SymbolTargetResolver,
    projection_view_targets_by_symbol: SymbolTargetResolver,
) -> list[DefinitionTarget]:
    if snapshot is None:
        return []
    if not document_bytes or b"program" not in document_bytes:
        return []

    try:
        root = parse_tree(document_bytes=document_bytes)
    except Exception:
        return []

    cursor = max(int(byte_offset), 0)
    program_defs = list(iter_program_defs(root=root))
    programs_by_name: dict[str, Node] = {}
    program_name_nodes: dict[str, Node] = {}
    for program_def in program_defs:
        name_node = program_def.child_by_field_name("name")
        name = node_text(name_node).strip()
        if name_node is None or not name:
            continue
        programs_by_name[name] = program_def
        program_name_nodes[name] = name_node

    for program_def in program_defs:
        if not cursor_in_range(
            byte_offset=cursor,
            start=program_def.start_byte,
            end=program_def.end_byte,
        ):
            continue

        impl_node = program_def.child_by_field_name("impl")
        impl_ref = node_text(impl_node).strip() if impl_node is not None else ""
        if (
            impl_node is not None
            and impl_ref
            and cursor_in_range(
                byte_offset=cursor,
                start=impl_node.start_byte,
                end=impl_node.end_byte,
            )
        ):
            decl_node = program_name_nodes.get(impl_ref)
            if decl_node is None:
                return []
            return [
                DefinitionTarget(
                    uri=uri,
                    range=ByteRange(start=decl_node.start_byte, end=decl_node.end_byte),
                )
            ]

        port_source_def = programs_by_name.get(impl_ref) if impl_ref else None
        if port_source_def is None:
            port_source_def = program_def

        ports_by_name: dict[str, Node] = {}
        port_node_by_alias: dict[str, _PortNodeMapping] = {}
        port_source_statements = list(iter_program_body_statements(program_def=port_source_def))
        for stmt in port_source_statements:
            if stmt.type != "port_decl_stmt":
                continue
            name_node = stmt.child_by_field_name("name")
            name = node_text(name_node).strip()
            if name_node is None or not name:
                continue
            ports_by_name[name] = name_node

            ref_node = stmt.child_by_field_name("ref")
            experience_ref = node_text(ref_node).strip() if ref_node is not None else ""
            body_node = stmt.child_by_field_name("body")
            if body_node is None or not experience_ref:
                continue
            for child in body_node.named_children:
                if child.type != "port_decl_node_stmt":
                    continue
                node_name_node = child.child_by_field_name("name")
                node_ref_node = child.child_by_field_name("ref")
                node_name = node_text(node_name_node).strip() if node_name_node is not None else ""
                node_ref = node_text(node_ref_node).strip() if node_ref_node is not None else ""
                if (
                    node_name_node is None
                    or node_ref_node is None
                    or not node_name
                    or not node_ref
                ):
                    continue
                port_node_by_alias[node_name] = _PortNodeMapping(
                    alias_node=node_name_node,
                )

        for stmt in port_source_statements:
            if stmt.type != "port_decl_stmt":
                continue
            ref_node = stmt.child_by_field_name("ref")
            experience_ref = node_text(ref_node).strip() if ref_node is not None else ""
            if ref_node is not None and cursor_in_range(
                byte_offset=cursor,
                start=ref_node.start_byte,
                end=ref_node.end_byte,
            ):
                if not experience_ref:
                    return []
                ref_parts = [part for part in experience_ref.split(".") if part]
                if not ref_parts:
                    return []
                experience_name = ref_parts[0].strip()
                if not experience_name:
                    return []
                exp_targets = experience_targets_by_symbol(
                    uri=uri,
                    symbol=experience_name,
                )
                if exp_targets:
                    return exp_targets
                return projection_targets_by_symbol(
                    uri=uri,
                    symbol=experience_name,
                )

            body_node = stmt.child_by_field_name("body")
            if body_node is None or not experience_ref:
                continue
            for child in body_node.named_children:
                if child.type != "port_decl_node_stmt":
                    continue
                node_ref_node = child.child_by_field_name("ref")
                if node_ref_node is None:
                    continue
                if not cursor_in_range(
                    byte_offset=cursor,
                    start=node_ref_node.start_byte,
                    end=node_ref_node.end_byte,
                ):
                    continue
                node_ref = node_text(node_ref_node).strip()
                if not node_ref:
                    return []
                return experience_node_targets_by_symbol(
                    uri=uri,
                    experience_symbol=experience_ref,
                    node_symbol=node_ref,
                )

        current_statements = list(iter_program_body_statements(program_def=program_def))
        for stmt in current_statements:
            if stmt.type == "bind_stmt":
                port_node = stmt.child_by_field_name("port")
                if port_node is not None and cursor_in_range(
                    byte_offset=cursor,
                    start=port_node.start_byte,
                    end=port_node.end_byte,
                ):
                    port_name = node_text(port_node).strip()
                    if not port_name:
                        return []
                    decl = ports_by_name.get(port_name)
                    if decl is None:
                        return []
                    return [
                        DefinitionTarget(
                            uri=uri,
                            range=ByteRange(start=decl.start_byte, end=decl.end_byte),
                        )
                    ]

                view_node = stmt.child_by_field_name("view")
                if view_node is not None and cursor_in_range(
                    byte_offset=cursor,
                    start=view_node.start_byte,
                    end=view_node.end_byte,
                ):
                    view_ref = node_text(view_node).strip()
                    if not view_ref:
                        return []
                    exp_view_targets = experience_view_targets_by_symbol(
                        uri=uri,
                        symbol=view_ref,
                    )
                    if exp_view_targets:
                        return exp_view_targets
                    view_targets = projection_view_targets_by_symbol(
                        uri=uri,
                        symbol=view_ref,
                    )
                    if view_targets:
                        return view_targets
                    projection_ref = view_ref.split(".", 1)[0].strip()
                    if not projection_ref:
                        return []
                    return projection_targets_by_symbol(
                        uri=uri,
                        symbol=projection_ref,
                    )
                continue

            if stmt.type != "call_stmt":
                continue
            object_node = stmt.child_by_field_name("object")
            if object_node is None:
                continue
            if not cursor_in_range(
                byte_offset=cursor,
                start=object_node.start_byte,
                end=object_node.end_byte,
            ):
                continue
            object_ref = node_text(object_node).strip()
            if not object_ref:
                return []
            port_node = port_node_by_alias.get(object_ref)
            if port_node is None:
                return []
            return [
                DefinitionTarget(
                    uri=uri,
                    range=ByteRange(
                        start=port_node.alias_node.start_byte,
                        end=port_node.alias_node.end_byte,
                    ),
                )
            ]

    return []
