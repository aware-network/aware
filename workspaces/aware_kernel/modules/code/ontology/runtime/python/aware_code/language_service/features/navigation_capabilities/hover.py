from __future__ import annotations

from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code.language_service.programs import (
    find_program_call_target_at,
    intrinsic_signature,
    parse_tree,
)
from aware_code.language_service.json_rpc import JsonObject
from aware_workspace.compiler.workspace import WorkspaceSnapshot


def collect_program_call_hover(*, byte_offset: int, document_bytes: bytes) -> JsonObject | None:
    if not document_bytes or b"program" not in document_bytes:
        return None
    try:
        root = parse_tree(document_bytes=document_bytes)
        call_at = find_program_call_target_at(root=root, byte_offset=byte_offset)
        if call_at is None and byte_offset > 0:
            call_at = find_program_call_target_at(root=root, byte_offset=byte_offset - 1)
    except Exception:
        return None
    if call_at is None:
        return None

    target = (call_at.target or "").strip()
    if not target:
        return None
    sig = intrinsic_signature(target)
    if sig is None:
        return None

    rendered = sig.render()
    return {
        "contents": {
            "kind": "markdown",
            "value": f"**intrinsic** `{sig.target}`\n\n```aware\n{rendered}\n```",
        }
    }


def collect_symbol_hover(
    *,
    snapshot: WorkspaceSnapshot | None,
    uri: str,
    token: str | None,
    workspace_language: CodeLanguage,
) -> JsonObject | None:
    if snapshot is None:
        return None
    normalized = (token or "").strip()
    if not normalized:
        return None

    code = snapshot.codes_by_uri.get(uri)
    if code is None:
        return None
    scope = snapshot.fqn_resolver.scope_for_code_id(code.id)

    resolved_class = scope.try_resolve_class_with_fqn(normalized)
    if resolved_class is not None:
        fqn, _ = resolved_class
        return {"contents": {"kind": "markdown", "value": f"**class** `{fqn}`"}}

    resolved_enum = scope.try_resolve_enum_with_fqn(normalized)
    if resolved_enum is not None:
        fqn, _ = resolved_enum
        return {"contents": {"kind": "markdown", "value": f"**enum** `{fqn}`"}}

    try:
        plugin = CodeLanguagePluginRegistry.get(workspace_language)
        prim = plugin.primitive_codec.parse(normalized)
        if prim is not None:
            rendered = plugin.primitive_codec.render(prim)
            return {
                "contents": {
                    "kind": "markdown",
                    "value": f"**primitive** `{rendered}`",
                }
            }
    except Exception:
        pass

    return None
