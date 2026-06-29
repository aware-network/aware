from __future__ import annotations

from difflib import get_close_matches
from re import Pattern

from aware_code_ontology.code.code import Code

from aware_meta.fqn_resolver import FqnScope

from aware_code.language_service.position import Utf16PositionMapper

from aware_workspace.compiler.workspace import WorkspaceSnapshot

from ..contracts import AwareDiagnostic
from .attribute_types import collect_attribute_type_diagnostics
from .augment_bases import collect_augment_base_diagnostics
from .candidates import build_quickfix_candidates
from .contracts import TypeMirrorPluginContract
from .mirror_targets import collect_mirror_target_diagnostics


def collect_type_mirror_augment_diagnostics(
    *,
    snapshot: WorkspaceSnapshot | None,
    code: Code,
    mapper: Utf16PositionMapper,
    plugin: TypeMirrorPluginContract,
    scope: FqnScope,
    common_primitive_tokens: tuple[str, ...],
    class_not_found_rx: Pattern[str],
    optional_list_rx: Pattern[str],
) -> list[AwareDiagnostic]:
    quickfix_candidates = build_quickfix_candidates(
        snapshot=snapshot,
        common_primitive_tokens=common_primitive_tokens,
    )

    def suggest(value: str, options: list[str]) -> list[str]:
        normalized = (value or "").strip()
        if not normalized:
            return []
        return list(get_close_matches(normalized, options, n=3, cutoff=0.6))

    diagnostics: list[AwareDiagnostic] = []
    diagnostics.extend(
        collect_attribute_type_diagnostics(
            code=code,
            mapper=mapper,
            plugin=plugin,
            scope=scope,
            class_not_found_rx=class_not_found_rx,
            optional_list_rx=optional_list_rx,
            quickfix_candidates=quickfix_candidates,
            suggest=suggest,
        )
    )
    diagnostics.extend(
        collect_mirror_target_diagnostics(
            code=code,
            mapper=mapper,
            scope=scope,
            quickfix_candidates=quickfix_candidates,
            suggest=suggest,
        )
    )
    diagnostics.extend(
        collect_augment_base_diagnostics(
            code=code,
            mapper=mapper,
            scope=scope,
        )
    )

    return diagnostics
