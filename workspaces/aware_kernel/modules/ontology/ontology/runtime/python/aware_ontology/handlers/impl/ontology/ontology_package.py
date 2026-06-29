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
from aware_ontology_ontology.ontology.ontology_package import OntologyPackage
from aware_ontology_ontology.ontology.ontology_package_dependency import OntologyPackageDependency
from aware_ontology_ontology.ontology.ontology_package_runtime_code_package import OntologyPackageRuntimeCodePackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Code Ontology
from aware_code_ontology.package.code_package import CodePackage

# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph_package import (
    ObjectConfigGraphPackage,
)
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)

# Ontology Ontology
from aware_ontology_ontology.ontology.ontology_config import OntologyConfig
from aware_ontology_ontology.stable_ids import stable_ontology_package_id

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build(
    name: str,
    fqn_prefix: str,
    ontology_config_id: UUID | None = None,
    ontology_config_object_instance_graph_commit_id: UUID | None = None,
    source_code_package_id: UUID | None = None,
    object_config_graph_package_id: UUID | None = None,
    object_config_graph_package_object_instance_graph_commit_id: UUID | None = None,
    object_config_graph_object_instance_graph_commit_id: UUID | None = None,
    version_number: int = 1,
    title: str | None = None,
    description: str | None = None,
    manifest_relative_path: str | None = None,
    package_root: str = ".",
    sources_root: str = "modules",
) -> OntologyPackage:
    """
    Create the canonical ontology-owned semantic package root.

    Contract:
    - Identity is keyed by ontology package `name` and `fqn_prefix`.
    - `ontology_config_id` points to Ontology-owned config/schema truth.
    - `source_code_package_id` points to Code-owned source package truth.
    - `object_config_graph_package_id` points to Meta-owned raw OCG package
      representation truth.
    - OIG commit pins let WorkspaceRevision/Environment consumers replay
      exact ontology package and graph truth without reopening source TOMLs.
    - Environment composition should select `OntologyPackage`; raw
      `ObjectConfigGraphPackage` membership is representation detail and
      compatibility fallback only.
    """

    # --- AWARE: LOGIC START build
    normalized_name = (name or "").strip()
    normalized_fqn_prefix = (fqn_prefix or "").strip()
    if not normalized_name:
        raise RuntimeError("OntologyPackage.build requires non-empty name")
    if not normalized_fqn_prefix:
        raise RuntimeError("OntologyPackage.build requires non-empty fqn_prefix")

    package_id = stable_ontology_package_id(
        name=normalized_name,
        fqn_prefix=normalized_fqn_prefix,
    )
    normalized_title = (title or "").strip() or None
    normalized_description = (description or "").strip() or None
    normalized_manifest_path = (manifest_relative_path or "").strip() or None
    normalized_package_root = (package_root or "").strip() or "."
    normalized_sources_root = (sources_root or "").strip() or "modules"

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    resolved_source_code_package = (
        session.imap_get(CodePackage, source_code_package_id)
        if session is not None and source_code_package_id is not None
        else None
    )
    resolved_ontology_config = (
        session.imap_get(OntologyConfig, ontology_config_id)
        if session is not None and ontology_config_id is not None
        else None
    )
    resolved_ontology_config_commit = (
        session.imap_get(
            ObjectInstanceGraphCommit,
            ontology_config_object_instance_graph_commit_id,
        )
        if session is not None and ontology_config_object_instance_graph_commit_id is not None
        else None
    )
    resolved_ocg_package = (
        session.imap_get(ObjectConfigGraphPackage, object_config_graph_package_id)
        if session is not None and object_config_graph_package_id is not None
        else None
    )
    resolved_ocg_package_commit = (
        session.imap_get(
            ObjectInstanceGraphCommit,
            object_config_graph_package_object_instance_graph_commit_id,
        )
        if session is not None and object_config_graph_package_object_instance_graph_commit_id is not None
        else None
    )
    resolved_ocg_commit = (
        session.imap_get(
            ObjectInstanceGraphCommit,
            object_config_graph_object_instance_graph_commit_id,
        )
        if session is not None and object_config_graph_object_instance_graph_commit_id is not None
        else None
    )

    if session is not None:
        existing = session.imap_get(OntologyPackage, package_id)
        if existing is not None:
            if (existing.name or "").strip() != normalized_name or (
                existing.fqn_prefix or ""
            ).strip() != normalized_fqn_prefix:
                raise RuntimeError(
                    "OntologyPackage.build payload mismatch for existing package: " f"ontology_package_id={package_id}"
                )
            if source_code_package_id is not None and existing.source_code_package_id not in {
                None,
                source_code_package_id,
            }:
                raise RuntimeError(
                    "OntologyPackage.build source_code_package_id mismatch for " f"ontology_package_id={package_id}"
                )
            if ontology_config_id is not None and existing.ontology_config_id not in {
                None,
                ontology_config_id,
            }:
                raise RuntimeError(
                    "OntologyPackage.build ontology_config_id mismatch for " f"ontology_package_id={package_id}"
                )
            if (
                ontology_config_object_instance_graph_commit_id is not None
                and existing.ontology_config_object_instance_graph_commit_id
                not in {
                    None,
                    ontology_config_object_instance_graph_commit_id,
                }
            ):
                raise RuntimeError(
                    "OntologyPackage.build ontology_config commit mismatch for " f"ontology_package_id={package_id}"
                )
            if object_config_graph_package_id is not None and existing.object_config_graph_package_id not in {
                None,
                object_config_graph_package_id,
            }:
                raise RuntimeError(
                    "OntologyPackage.build object_config_graph_package_id mismatch for "
                    f"ontology_package_id={package_id}"
                )
            if (
                object_config_graph_package_object_instance_graph_commit_id is not None
                and existing.object_config_graph_package_object_instance_graph_commit_id
                not in {
                    None,
                    object_config_graph_package_object_instance_graph_commit_id,
                }
            ):
                raise RuntimeError(
                    "OntologyPackage.build object_config_graph_package commit mismatch "
                    f"for ontology_package_id={package_id}"
                )
            if (
                object_config_graph_object_instance_graph_commit_id is not None
                and existing.object_config_graph_object_instance_graph_commit_id
                not in {None, object_config_graph_object_instance_graph_commit_id}
            ):
                raise RuntimeError(
                    "OntologyPackage.build object_config_graph commit mismatch for " f"ontology_package_id={package_id}"
                )

            if source_code_package_id is not None:
                existing.source_code_package_id = source_code_package_id
                existing.source_code_package = resolved_source_code_package
            if ontology_config_id is not None:
                existing.ontology_config_id = ontology_config_id
                existing.ontology_config = resolved_ontology_config
            if ontology_config_object_instance_graph_commit_id is not None:
                existing.ontology_config_object_instance_graph_commit_id = (
                    ontology_config_object_instance_graph_commit_id
                )
                existing.ontology_config_object_instance_graph_commit = resolved_ontology_config_commit
            if object_config_graph_package_id is not None:
                existing.object_config_graph_package_id = object_config_graph_package_id
                existing.object_config_graph_package = resolved_ocg_package
            if object_config_graph_package_object_instance_graph_commit_id is not None:
                existing.object_config_graph_package_object_instance_graph_commit_id = (
                    object_config_graph_package_object_instance_graph_commit_id
                )
                existing.object_config_graph_package_object_instance_graph_commit = resolved_ocg_package_commit
            if object_config_graph_object_instance_graph_commit_id is not None:
                existing.object_config_graph_object_instance_graph_commit_id = (
                    object_config_graph_object_instance_graph_commit_id
                )
                existing.object_config_graph_object_instance_graph_commit = resolved_ocg_commit
            existing.version_number = version_number
            existing.title = normalized_title
            existing.description = normalized_description
            existing.manifest_relative_path = normalized_manifest_path
            existing.package_root = normalized_package_root
            existing.sources_root = normalized_sources_root
            return existing

    return OntologyPackage.model_construct(
        id=package_id,
        name=normalized_name,
        fqn_prefix=normalized_fqn_prefix,
        ontology_config=resolved_ontology_config,
        ontology_config_id=ontology_config_id,
        ontology_config_object_instance_graph_commit=(resolved_ontology_config_commit),
        ontology_config_object_instance_graph_commit_id=(ontology_config_object_instance_graph_commit_id),
        source_code_package=resolved_source_code_package,
        source_code_package_id=source_code_package_id,
        object_config_graph_package=resolved_ocg_package,
        object_config_graph_package_id=object_config_graph_package_id,
        object_config_graph_package_object_instance_graph_commit=(resolved_ocg_package_commit),
        object_config_graph_package_object_instance_graph_commit_id=(
            object_config_graph_package_object_instance_graph_commit_id
        ),
        object_config_graph_object_instance_graph_commit=resolved_ocg_commit,
        object_config_graph_object_instance_graph_commit_id=(object_config_graph_object_instance_graph_commit_id),
        version_number=version_number,
        title=normalized_title,
        description=normalized_description,
        manifest_relative_path=normalized_manifest_path,
        package_root=normalized_package_root,
        sources_root=normalized_sources_root,
    )
    # --- AWARE: LOGIC END build


async def attach_runtime_code_package(
    ontology_package: OntologyPackage,
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
    Attach one runtime/implementation CodePackage to this OntologyPackage.

    Contract:
    - Parent `OntologyPackage` scope is injected by propagation.
    - The attached `CodePackage` is implementation/runtime truth, not the
      ontology package source package unless it also appears in
      `source_code_package`.
    - Consumers must use this explicit package contract instead of inferring
      runtime import roots from repository layout.
    """

    # --- AWARE: LOGIC START attach_runtime_code_package
    edge = await OntologyPackageRuntimeCodePackage.build_via_ontology_package(
        ontology_package_id=ontology_package.id,
        code_package_id=code_package_id,
        package_name=package_name,
        language=language,
        import_root=import_root,
        manifest_relative_path=manifest_relative_path,
        package_root=package_root,
        role=role,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
        include_paths=JsonArray(include_paths or []),
        exclude_paths=JsonArray(exclude_paths or []),
    )
    if all(existing.id != edge.id for existing in ontology_package.runtime_code_packages):
        ontology_package.runtime_code_packages.append(edge)
    return edge
    # --- AWARE: LOGIC END attach_runtime_code_package


async def attach_dependency(
    ontology_package: OntologyPackage,
    target_ontology_package_id: UUID,
    target_package_name: str,
    target_ontology_package_object_instance_graph_commit_id: UUID | None = None,
    target_version_number: int | None = None,
    expected_hash_sha256: str | None = None,
    description: str | None = None,
) -> OntologyPackageDependency:
    """
    Attach one ontology package dependency.

    Contract:
    - Parent `OntologyPackage` scope is injected by propagation.
    - Dependencies are ontology package dependencies, not raw OCG dependency
      shortcuts. Raw graph dependency closure is resolved through the target
      `OntologyPackage -> ObjectConfigGraphPackage` bridge.
    """

    # --- AWARE: LOGIC START attach_dependency
    edge = await OntologyPackageDependency.build_via_ontology_package(
        ontology_package_id=ontology_package.id,
        target_ontology_package_id=target_ontology_package_id,
        target_package_name=target_package_name,
        target_ontology_package_object_instance_graph_commit_id=(
            target_ontology_package_object_instance_graph_commit_id
        ),
        target_version_number=target_version_number,
        expected_hash_sha256=expected_hash_sha256,
        description=description,
    )
    if all(existing.id != edge.id for existing in ontology_package.dependencies):
        ontology_package.dependencies.append(edge)
    return edge
    # --- AWARE: LOGIC END attach_dependency
