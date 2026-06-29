from __future__ import annotations

from aware_code_ontology.attribute.code_section_attribute import CodeSectionAttribute
from aware_code_ontology.class_.code_section_class import CodeSectionClass
from aware_code_ontology.function.code_section_function import CodeSectionFunction
from aware_code.language_service.features.navigation_capabilities.contracts import (
    AttributeDefinitionTargetResolver,
    ClassDefinitionTargetResolver,
    EnumValueDefinitionTargetResolver,
    FunctionDefinitionTargetResolver,
    UriDocumentTextReader,
)
from aware_code.language_service.position import ByteRange
from aware_code.language_service.text import split_double_colon_parts
from aware_code.language_service.types import DefinitionTarget
from aware_code.language_service.json_rpc import JsonObject
from aware_workspace.compiler.workspace import WorkspaceSnapshot


def collect_annotation_path_hover(
    *,
    snapshot: WorkspaceSnapshot | None,
    uri: str,
    byte_offset: int,
    document_bytes: bytes,
    path_range: ByteRange,
    get_document_text: UriDocumentTextReader,
) -> JsonObject | None:
    if snapshot is None:
        return None
    code = snapshot.codes_by_uri.get(uri)
    if code is None:
        return None

    cursor = byte_offset
    if cursor == path_range.end and cursor > path_range.start:
        cursor -= 1
    if not (path_range.start <= cursor < path_range.end):
        return None
    if document_bytes[cursor:cursor + 1] == b":":
        return None

    token_bytes = document_bytes[path_range.start:path_range.end]
    parts = split_double_colon_parts(token_bytes=token_bytes, token_range=path_range)
    if not parts:
        return None

    part_idx: int | None = None
    for idx, part in enumerate(parts):
        part_cursor = cursor
        if part_cursor == part.range.end and part_cursor > part.range.start:
            part_cursor -= 1
        if part.range.start <= part_cursor < part.range.end:
            part_idx = idx
            break
    if part_idx is None:
        return None

    type_ref = parts[0].text
    members = [part.text for part in parts[1:]]
    member_idx = part_idx - 1
    scope = snapshot.fqn_resolver.scope_for_code_id(code.id)

    resolved_class = scope.try_resolve_class_with_fqn(type_ref)
    if resolved_class is not None:
        fqn, class_cfg = resolved_class
        cls = class_cfg.code_section_class
        if cls is None:
            return {"contents": {"kind": "markdown", "value": f"**class** `{fqn}`"}}

        if part_idx == 0:
            return {"contents": {"kind": "markdown", "value": f"**class** `{fqn}`"}}

        if member_idx == 0:
            name = members[0] if members else ""
            attr = _find_attr(owner=cls, name=name)
            if attr is not None:
                type_text = attr.type_text
                edge_name = attr.edge_spec_name
                lines = [f"**attribute** `{fqn}::{name}`"]
                if isinstance(type_text, str) and type_text:
                    lines.append(f"- type: `{type_text}`")
                if isinstance(edge_name, str) and edge_name:
                    lines.append(f"- edge: `{edge_name}`")
                return {"contents": {"kind": "markdown", "value": "\n".join(lines)}}

            fn = _find_fn(owner=cls, name=name)
            if fn is not None:
                signature = None
                sig_seg = fn.signature_segment
                fn_code_id = fn.code_section.code_id
                fn_uri = snapshot.uri_by_code_id.get(fn_code_id)
                if fn_uri and sig_seg and sig_seg.byte_start is not None and sig_seg.byte_end is not None:
                    try:
                        fn_text = get_document_text(fn_uri)
                        document_buffer = fn_text.encode("utf-8")
                        signature = (
                            document_buffer[sig_seg.byte_start:sig_seg.byte_end]
                            .decode("utf-8", errors="replace")
                            .strip()
                        )
                    except Exception:
                        signature = None
                value = f"**function** `{fqn}::{name}`"
                if signature:
                    value = value + f"\n\n```aware\n{signature}\n```"
                return {"contents": {"kind": "markdown", "value": value}}

            return {
                "contents": {
                    "kind": "markdown",
                    "value": f"`{name}` (unresolved member on `{fqn}`)",
                }
            }

        if member_idx == 1:
            head = members[0]
            name = members[1] if len(members) >= 2 else ""
            fn = _find_fn(owner=cls, name=head)
            if fn is not None:
                attr = _find_attr(owner=fn, name=name)
                if attr is not None:
                    type_text = attr.type_text
                    lines = [f"**attribute** `{fqn}::{head}::{name}`"]
                    if isinstance(type_text, str) and type_text:
                        lines.append(f"- type: `{type_text}`")
                    return {"contents": {"kind": "markdown", "value": "\n".join(lines)}}
                return {
                    "contents": {
                        "kind": "markdown",
                        "value": f"`{name}` (unresolved member on `{fqn}::{head}`)",
                    }
                }

            resolved_edge = scope.try_resolve_class_with_fqn(name)
            if resolved_edge is not None:
                edge_fqn, _ = resolved_edge
                return {
                    "contents": {
                        "kind": "markdown",
                        "value": f"**class** `{edge_fqn}`",
                    }
                }
            return None

        if len(members) < 2:
            return None

        edge_type_ref = members[1]
        resolved_edge = scope.try_resolve_class_with_fqn(edge_type_ref)
        if resolved_edge is None:
            return None
        edge_fqn, edge_cfg = resolved_edge
        edge_cls = edge_cfg.code_section_class
        if edge_cls is None:
            return {"contents": {"kind": "markdown", "value": f"**class** `{edge_fqn}`"}}

        name = members[member_idx] if member_idx < len(members) else ""
        if member_idx == 2:
            attr = _find_attr(owner=edge_cls, name=name)
            if attr is not None:
                type_text = attr.type_text
                lines = [f"**attribute** `{edge_fqn}::{name}`"]
                if isinstance(type_text, str) and type_text:
                    lines.append(f"- type: `{type_text}`")
                return {"contents": {"kind": "markdown", "value": "\n".join(lines)}}
            fn = _find_fn(owner=edge_cls, name=name)
            if fn is not None:
                return {
                    "contents": {
                        "kind": "markdown",
                        "value": f"**function** `{edge_fqn}::{name}`",
                    }
                }
            return None

        if member_idx == 3:
            edge_fn_name = members[2]
            edge_fn = _find_fn(owner=edge_cls, name=edge_fn_name)
            if edge_fn is None:
                return None
            attr = _find_attr(owner=edge_fn, name=name)
            if attr is not None:
                type_text = attr.type_text
                lines = [f"**attribute** `{edge_fqn}::{edge_fn_name}::{name}`"]
                if isinstance(type_text, str) and type_text:
                    lines.append(f"- type: `{type_text}`")
                return {"contents": {"kind": "markdown", "value": "\n".join(lines)}}
            return None

        return None

    resolved_enum = scope.try_resolve_enum_with_fqn(type_ref)
    if resolved_enum is not None:
        fqn, _ = resolved_enum
        if part_idx == 0:
            return {"contents": {"kind": "markdown", "value": f"**enum** `{fqn}`"}}
        if member_idx == 0 and members:
            option = members[0]
            return {
                "contents": {
                    "kind": "markdown",
                    "value": f"**enum option** `{fqn}::{option}`",
                }
            }
        return {"contents": {"kind": "markdown", "value": f"**enum** `{fqn}`"}}

    return None


def collect_annotation_member_definition_target(
    *,
    snapshot: WorkspaceSnapshot | None,
    uri: str,
    byte_offset: int,
    document_bytes: bytes,
    annotation_path_range: ByteRange,
    class_definition_target: ClassDefinitionTargetResolver,
    attribute_definition_target: AttributeDefinitionTargetResolver,
    function_definition_target: FunctionDefinitionTargetResolver,
    enum_value_definition_target: EnumValueDefinitionTargetResolver,
) -> DefinitionTarget | None:
    if snapshot is None:
        return None
    code = snapshot.codes_by_uri.get(uri)
    if code is None:
        return None

    cursor = byte_offset
    if cursor == annotation_path_range.end and cursor > annotation_path_range.start:
        cursor -= 1
    if not (annotation_path_range.start <= cursor < annotation_path_range.end):
        return None
    if document_bytes[cursor:cursor + 1] == b":":
        return None

    before = document_bytes[annotation_path_range.start:cursor]
    segment_index = before.count(b"::")
    if segment_index <= 0:
        return None

    path = document_bytes[annotation_path_range.start:annotation_path_range.end].decode("utf-8", errors="replace")
    parts = [part for part in path.split("::")]
    if not parts:
        return None

    type_ref = (parts[0] or "").strip()
    members = [(part or "").strip() for part in parts[1:]]
    member_idx = segment_index - 1
    if not type_ref or member_idx < 0 or member_idx >= len(members):
        return None

    scope = snapshot.fqn_resolver.scope_for_code_id(code.id)

    resolved_enum = scope.try_resolve_enum_with_fqn(type_ref)
    if resolved_enum is not None:
        _, enum_cfg = resolved_enum
        enum = enum_cfg.code_section_enum
        if enum is None or member_idx != 0:
            return None
        option = members[0]
        for val in enum.code_section_enum_values:
            if val.value != option:
                continue
            return enum_value_definition_target(val)
        return None

    resolved_class = scope.try_resolve_class_with_fqn(type_ref)
    if resolved_class is None:
        return None
    _, class_cfg = resolved_class
    cls = class_cfg.code_section_class
    if cls is None:
        return None

    name = members[member_idx]
    if member_idx == 0:
        attr = _find_attr(owner=cls, name=name)
        if attr is not None:
            return attribute_definition_target(attr)
        fn = _find_fn(owner=cls, name=name)
        if fn is not None:
            return function_definition_target(fn)
        return None

    if member_idx == 1:
        head = members[0]
        fn = _find_fn(owner=cls, name=head)
        if fn is not None:
            attr = _find_attr(owner=fn, name=name)
            if attr is not None:
                return attribute_definition_target(attr)
            return None

        resolved_edge = scope.try_resolve_class_with_fqn(name)
        if resolved_edge is None:
            return None
        _, edge_cfg = resolved_edge
        return class_definition_target(edge_cfg)

    if len(members) < 2:
        return None

    edge_type_ref = members[1]
    resolved_edge = scope.try_resolve_class_with_fqn(edge_type_ref)
    if resolved_edge is None:
        return None
    _, edge_cfg = resolved_edge
    edge_cls = edge_cfg.code_section_class
    if edge_cls is None:
        return None

    if member_idx == 2:
        attr = _find_attr(owner=edge_cls, name=name)
        if attr is not None:
            return attribute_definition_target(attr)
        fn = _find_fn(owner=edge_cls, name=name)
        if fn is not None:
            return function_definition_target(fn)
        return None

    if member_idx == 3:
        edge_fn_name = members[2]
        edge_fn = _find_fn(owner=edge_cls, name=edge_fn_name)
        if edge_fn is None:
            return None
        attr = _find_attr(owner=edge_fn, name=name)
        if attr is not None:
            return attribute_definition_target(attr)
        return None

    return None


def _find_attr(owner: CodeSectionFunction | CodeSectionClass, name: str) -> CodeSectionAttribute | None:
    for attr in owner.code_section_attributes:
        if attr.name == name:
            return attr
    return None


def _find_fn(owner: CodeSectionClass, name: str) -> CodeSectionFunction | None:
    for fn in owner.code_section_functions:
        if fn.name == name:
            return fn
    return None
