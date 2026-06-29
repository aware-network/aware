from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonArray

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Ontology Ontology
from aware_ontology_ontology.ontology.ontology_package_runtime_code_package import OntologyPackageRuntimeCodePackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Code Ontology
from aware_code_ontology.package.code_package import CodePackage

# Meta Ontology
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)

# Ontology Ontology
from aware_ontology_ontology.stable_ids import (
    stable_ontology_package_runtime_code_package_id,
)

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_ontology_package(
    ontology_package_id: UUID,
    code_package_id: UUID,
    package_name: str,
    language: CodeLanguage,
    import_root: str,
    manifest_relative_path: str,
    package_root: str = ".",
    role: str = "runtime",
    object_instance_graph_commit_id: UUID | None = None,
    include_paths: JsonArray = JsonArray(),
    exclude_paths: JsonArray = JsonArray(),
) -> OntologyPackageRuntimeCodePackage:
    """
    Attach one Code-owned implementation/runtime package.

    Contract:
    - Parent `OntologyPackage` scope is injected by propagation.
    - Identity is keyed by the attached `CodePackage`.
    - `object_instance_graph_commit_id`, when present, is the exact
      WorkspaceRevision/Hub replay pin for that CodePackage.
    """

    # --- AWARE: LOGIC START build_via_ontology_package
    normalized_package_name = (package_name or "").strip()
    normalized_import_root = (import_root or "").strip()
    normalized_manifest_path = (manifest_relative_path or "").strip()
    if not normalized_package_name:
        raise RuntimeError(
            "OntologyPackageRuntimeCodePackage.build_via_ontology_package " "requires non-empty package_name"
        )
    if not normalized_import_root:
        raise RuntimeError(
            "OntologyPackageRuntimeCodePackage.build_via_ontology_package " "requires non-empty import_root"
        )
    if not normalized_manifest_path:
        raise RuntimeError(
            "OntologyPackageRuntimeCodePackage.build_via_ontology_package " "requires non-empty manifest_relative_path"
        )

    runtime_package_id = stable_ontology_package_runtime_code_package_id(
        ontology_package_id=ontology_package_id,
        code_package_id=code_package_id,
    )

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    resolved_code_package = session.imap_get(CodePackage, code_package_id) if session is not None else None
    resolved_commit = (
        session.imap_get(ObjectInstanceGraphCommit, object_instance_graph_commit_id)
        if session is not None and object_instance_graph_commit_id is not None
        else None
    )

    if session is not None:
        existing = session.imap_get(
            OntologyPackageRuntimeCodePackage,
            runtime_package_id,
        )
        if existing is not None:
            if existing.ontology_package_id != ontology_package_id or existing.code_package_id != code_package_id:
                raise RuntimeError(
                    "OntologyPackageRuntimeCodePackage.build_via_ontology_package "
                    f"payload mismatch for runtime_code_package_id={runtime_package_id}"
                )
            if object_instance_graph_commit_id is not None and existing.object_instance_graph_commit_id not in {
                None,
                object_instance_graph_commit_id,
            }:
                raise RuntimeError(
                    "OntologyPackageRuntimeCodePackage.build_via_ontology_package "
                    "commit mismatch for "
                    f"runtime_code_package_id={runtime_package_id}"
                )
            if existing.code_package is None:
                existing.code_package = resolved_code_package
            if object_instance_graph_commit_id is not None:
                existing.object_instance_graph_commit_id = object_instance_graph_commit_id
                existing.object_instance_graph_commit = resolved_commit
            existing.package_name = normalized_package_name
            existing.language = language
            existing.import_root = normalized_import_root
            existing.manifest_relative_path = normalized_manifest_path
            existing.package_root = (package_root or "").strip() or "."
            existing.role = (role or "").strip() or "runtime"
            existing.include_paths = JsonArray(include_paths or [])
            existing.exclude_paths = JsonArray(exclude_paths or [])
            return existing

    return OntologyPackageRuntimeCodePackage.model_construct(
        id=runtime_package_id,
        ontology_package_id=ontology_package_id,
        code_package=resolved_code_package,
        code_package_id=code_package_id,
        object_instance_graph_commit=resolved_commit,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
        package_name=normalized_package_name,
        language=language,
        import_root=normalized_import_root,
        manifest_relative_path=normalized_manifest_path,
        package_root=(package_root or "").strip() or ".",
        role=(role or "").strip() or "runtime",
        include_paths=JsonArray(include_paths or []),
        exclude_paths=JsonArray(exclude_paths or []),
    )
    # --- AWARE: LOGIC END build_via_ontology_package
