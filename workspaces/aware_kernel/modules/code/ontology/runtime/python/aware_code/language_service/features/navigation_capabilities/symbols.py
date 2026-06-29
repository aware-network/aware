from __future__ import annotations

from aware_code.language_service.features.navigation_capabilities.contracts import (
    ClassDefinitionTargetResolver,
    EnumDefinitionTargetResolver,
)
from aware_code.language_service.types import DefinitionTarget, ResolvedSymbol
from aware_workspace.compiler.workspace import WorkspaceSnapshot


def collect_symbol_definition_targets(
    *,
    snapshot: WorkspaceSnapshot | None,
    uri: str,
    symbol: ResolvedSymbol | None,
    class_definition_target: ClassDefinitionTargetResolver,
    enum_definition_target: EnumDefinitionTargetResolver,
) -> list[DefinitionTarget]:
    if snapshot is None or symbol is None:
        return []

    code = snapshot.codes_by_uri.get(uri)
    if code is None:
        return []
    scope = snapshot.fqn_resolver.scope_for_code_id(code.id)

    if symbol.kind == "class":
        class_cfg = snapshot.fqn_resolver.classes_by_fqn.get(symbol.fqn)
        if class_cfg is None:
            resolved = scope.try_resolve_class_with_fqn(symbol.fqn)
            class_cfg = resolved[1] if resolved is not None else None
        if class_cfg is None:
            return []
        target = class_definition_target(class_cfg)
        return [target] if target is not None else []

    enum_cfg = snapshot.fqn_resolver.enums_by_fqn.get(symbol.fqn)
    if enum_cfg is None:
        resolved = scope.try_resolve_enum_with_fqn(symbol.fqn)
        enum_cfg = resolved[1] if resolved is not None else None
    if enum_cfg is None:
        return []
    target = enum_definition_target(enum_cfg)
    return [target] if target is not None else []
