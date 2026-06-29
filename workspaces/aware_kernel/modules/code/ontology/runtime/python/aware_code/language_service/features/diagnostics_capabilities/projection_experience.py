from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from tree_sitter import Node

from aware_code_ontology.code.code import Code

from aware_meta.fqn_resolver import FqnScope

from aware_workspace.compiler.workspace import WorkspaceSnapshot

from .environment import collect_environment_diagnostics
from .experience import collect_experience_diagnostics
from .projection import (
    ProjectionAddDiagnostic,
    ProjectionSuggestFn,
    build_projection_lookup,
    collect_projection_diagnostics,
)
from .role_actor import collect_role_actor_diagnostics


def collect_projection_experience_role_environment_diagnostics(
    *,
    snapshot: WorkspaceSnapshot,
    code: Code,
    scope: FqnScope,
    document_bytes: bytes,
    projection_root: Node | None,
    class_candidates: list[str],
    add: ProjectionAddDiagnostic,
    suggest: ProjectionSuggestFn,
    uri: str | None = None,
    uri_to_path: Callable[[str], Path] | None = None,
) -> None:
    lookup = build_projection_lookup(snapshot=snapshot, code=code)

    collect_projection_diagnostics(
        code=code,
        scope=scope,
        document_bytes=document_bytes,
        projection_root=projection_root,
        class_candidates=class_candidates,
        lookup=lookup,
        add=add,
        suggest=suggest,
    )

    collect_experience_diagnostics(
        projection_root=projection_root,
        document_bytes=document_bytes,
        lookup=lookup,
        add=add,
        suggest=suggest,
        uri=uri,
        uri_to_path=uri_to_path,
    )

    collect_role_actor_diagnostics(
        projection_root=projection_root,
        document_bytes=document_bytes,
        scope=scope,
        class_candidates=class_candidates,
        add=add,
        suggest=suggest,
    )

    collect_environment_diagnostics(
        projection_root=projection_root,
        document_bytes=document_bytes,
        add=add,
        suggest=suggest,
    )
