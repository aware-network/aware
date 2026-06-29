from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Api Ontology
from aware_api_ontology.api.api_package import ApiPackage
from aware_api_ontology.api.api_package_language_package import ApiPackageLanguagePackage

# Code
from aware_code.types import (
    JsonArray,
    JsonObject,
)

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Code Ontology
from aware_code_ontology.package.code_package import CodePackage
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)

# Api Ontology
from aware_api_ontology.api.api import Api
from aware_api_ontology.stable_ids import stable_api_package_id

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build(
    name: str,
    api_id: UUID,
    api_object_instance_graph_commit_id: UUID | None = None,
    source_code_package_id: UUID | None = None,
    fqn_prefix: str | None = None,
    version_number: int = 1,
    title: str | None = None,
    description: str | None = None,
    aware_api_version: int = 1,
    manifest_relative_path: str | None = None,
    package_root: str = ".",
    sources_root: str = "apis",
    include_paths: JsonArray = JsonArray(),
    exclude_paths: JsonArray = JsonArray(),
    force_fresh_scan: bool = True,
    compilation_mode: str = "raw_xor",
    dependencies: JsonArray = JsonArray(),
    targets: JsonObject = JsonObject(),
) -> ApiPackage:
    """
    Create the canonical API-owned package root over an existing `Api`.

    Contract:
    - Identity is keyed by API package `name`.
    - `ApiPackage` is the package/public root over an existing canonical `Api`.
    - `api_id` must point at the canonical Api stable id for this package root.
    - `api_object_instance_graph_commit_id` pins the historical ObjectInstanceGraphCommit for the
      semantic Api root so package consumers can replay the exact API truth without resolving branch
    head.
    - `source_code_package_id` is the explicit raw-source provenance link for this semantic leaf
    package.
    - Manifest/build/dependency/target attributes mirror `aware.api.toml` so committed package truth can
      drive Workspace, Service protocol, and runtime resolution without reopening authoring TOML.
    - Workspace will later mount `ApiPackage`, not raw `Api`.
    """

    # --- AWARE: LOGIC START build
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("ApiPackage.build requires non-empty name")
    normalized_fqn_prefix = (fqn_prefix or "").strip() or None
    normalized_title = (title or "").strip() or None
    normalized_description = (description or "").strip() or None
    normalized_manifest_relative_path = (manifest_relative_path or "").strip() or None
    normalized_package_root = (package_root or "").strip() or "."
    normalized_sources_root = (sources_root or "").strip() or "apis"
    normalized_compilation_mode = (compilation_mode or "").strip() or "raw_xor"
    include_paths_payload = JsonArray(include_paths or [])
    exclude_paths_payload = JsonArray(exclude_paths or [])
    dependencies_payload = JsonArray(dependencies or [])
    targets_payload = JsonObject(targets or {})

    package_id = stable_api_package_id(name=normalized_name)

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    resolved_api = session.imap_get(Api, api_id) if session is not None else None
    resolved_source_code_package = (
        session.imap_get(CodePackage, source_code_package_id)
        if session is not None and source_code_package_id is not None
        else None
    )
    resolved_api_object_instance_graph_commit = (
        session.imap_get(ObjectInstanceGraphCommit, api_object_instance_graph_commit_id)
        if session is not None and api_object_instance_graph_commit_id is not None
        else None
    )

    if session is not None:
        existing = session.imap_get(ApiPackage, package_id)
        if existing is not None:
            if (existing.name or "").strip() != normalized_name:
                raise RuntimeError(
                    "ApiPackage.build payload mismatch for existing package: " f"api_package_id={package_id}"
                )
            existing_api_id = existing.api_id
            if existing_api_id != api_id:
                raise RuntimeError(
                    "ApiPackage.build api_id mismatch for existing package: "
                    f"api_package_id={package_id} existing={existing_api_id} provided={api_id}"
                )

            existing_source_code_package_id = existing.source_code_package_id
            if source_code_package_id is not None:
                if existing_source_code_package_id is None:
                    existing.source_code_package_id = source_code_package_id
                    existing.source_code_package = resolved_source_code_package
                elif existing_source_code_package_id != source_code_package_id:
                    raise RuntimeError(
                        "ApiPackage.build source_code_package_id mismatch for existing package: "
                        f"api_package_id={package_id} "
                        f"existing={existing_source_code_package_id} provided={source_code_package_id}"
                    )
            if api_object_instance_graph_commit_id is not None:
                existing.api_object_instance_graph_commit_id = api_object_instance_graph_commit_id
                existing.api_object_instance_graph_commit = resolved_api_object_instance_graph_commit
            existing.fqn_prefix = normalized_fqn_prefix
            existing.version_number = version_number
            existing.title = normalized_title
            existing.description = normalized_description
            existing.aware_api_version = aware_api_version
            existing.manifest_relative_path = normalized_manifest_relative_path
            existing.package_root = normalized_package_root
            existing.sources_root = normalized_sources_root
            existing.include_paths = include_paths_payload
            existing.exclude_paths = exclude_paths_payload
            existing.force_fresh_scan = force_fresh_scan
            existing.compilation_mode = normalized_compilation_mode
            existing.dependencies = dependencies_payload
            existing.targets = targets_payload
            return existing

    return ApiPackage.model_construct(
        id=package_id,
        name=normalized_name,
        api=resolved_api,
        api_id=api_id,
        api_object_instance_graph_commit=resolved_api_object_instance_graph_commit,
        api_object_instance_graph_commit_id=api_object_instance_graph_commit_id,
        source_code_package=resolved_source_code_package,
        source_code_package_id=source_code_package_id,
        fqn_prefix=normalized_fqn_prefix,
        version_number=version_number,
        title=normalized_title,
        description=normalized_description,
        aware_api_version=aware_api_version,
        manifest_relative_path=normalized_manifest_relative_path,
        package_root=normalized_package_root,
        sources_root=normalized_sources_root,
        include_paths=include_paths_payload,
        exclude_paths=exclude_paths_payload,
        force_fresh_scan=force_fresh_scan,
        compilation_mode=normalized_compilation_mode,
        dependencies=dependencies_payload,
        targets=targets_payload,
    )
    # --- AWARE: LOGIC END build


async def sync_manifest_truth(
    api_package: ApiPackage,
    api_object_instance_graph_commit_id: UUID | None = None,
    source_code_package_id: UUID | None = None,
    fqn_prefix: str | None = None,
    version_number: int = 1,
    title: str | None = None,
    description: str | None = None,
    aware_api_version: int = 1,
    manifest_relative_path: str | None = None,
    package_root: str = ".",
    sources_root: str = "apis",
    include_paths: JsonArray = JsonArray(),
    exclude_paths: JsonArray = JsonArray(),
    force_fresh_scan: bool = True,
    compilation_mode: str = "raw_xor",
    dependencies: JsonArray = JsonArray(),
    targets: JsonObject = JsonObject(),
) -> ApiPackage:
    """
    Sync mutable manifest/build/dependency/target truth onto an existing ApiPackage root.

    This keeps `build` create-only for empty package lanes while allowing committed package truth to
    follow the latest parsed `aware.api.toml` snapshot and pinned semantic Api commit.
    """

    # --- AWARE: LOGIC START sync_manifest_truth
    normalized_name = (api_package.name or "").strip()
    if not normalized_name:
        raise RuntimeError("ApiPackage.sync_manifest_truth requires a named package")
    normalized_fqn_prefix = (fqn_prefix or "").strip() or None
    normalized_title = (title or "").strip() or None
    normalized_description = (description or "").strip() or None
    normalized_manifest_relative_path = (manifest_relative_path or "").strip() or None
    normalized_package_root = (package_root or "").strip() or "."
    normalized_sources_root = (sources_root or "").strip() or "apis"
    normalized_compilation_mode = (compilation_mode or "").strip() or "raw_xor"
    include_paths_payload = JsonArray(include_paths or [])
    exclude_paths_payload = JsonArray(exclude_paths or [])
    dependencies_payload = JsonArray(dependencies or [])
    targets_payload = JsonObject(targets or {})

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    if source_code_package_id is not None:
        resolved_source_code_package = (
            session.imap_get(CodePackage, source_code_package_id) if session is not None else None
        )
        existing_source_code_package_id = api_package.source_code_package_id
        if existing_source_code_package_id is None:
            api_package.source_code_package_id = source_code_package_id
            api_package.source_code_package = resolved_source_code_package
        elif existing_source_code_package_id != source_code_package_id:
            raise RuntimeError(
                "ApiPackage.sync_manifest_truth source_code_package_id mismatch: "
                f"api_package_id={api_package.id} "
                f"existing={existing_source_code_package_id} provided={source_code_package_id}"
            )

    if api_object_instance_graph_commit_id is not None:
        api_package.api_object_instance_graph_commit_id = api_object_instance_graph_commit_id
        api_package.api_object_instance_graph_commit = (
            session.imap_get(ObjectInstanceGraphCommit, api_object_instance_graph_commit_id)
            if session is not None
            else None
        )

    api_package.fqn_prefix = normalized_fqn_prefix
    api_package.version_number = version_number
    api_package.title = normalized_title
    api_package.description = normalized_description
    api_package.aware_api_version = aware_api_version
    api_package.manifest_relative_path = normalized_manifest_relative_path
    api_package.package_root = normalized_package_root
    api_package.sources_root = normalized_sources_root
    api_package.include_paths = include_paths_payload
    api_package.exclude_paths = exclude_paths_payload
    api_package.force_fresh_scan = force_fresh_scan
    api_package.compilation_mode = normalized_compilation_mode
    api_package.dependencies = dependencies_payload
    api_package.targets = targets_payload
    return api_package
    # --- AWARE: LOGIC END sync_manifest_truth


async def attach_language_package(
    api_package: ApiPackage,
    code_package_id: UUID,
    package_name: str,
    language: CodeLanguage,
    import_root: str,
    manifest_relative_path: str,
    package_root: str = ".",
    role: str = "public_package",
    output_key: str = "python.public_package",
    include_paths: JsonArray = JsonArray(),
    exclude_paths: JsonArray = JsonArray(),
) -> ApiPackageLanguagePackage:
    """
    Attach one generated language package owned by this ApiPackage.

    Contract:
    - API generated clients and service protocols are explicit package truth.
    - WorkspaceRevision checkout and SDK/service consumers must resolve API
      generated language roots from this bridge, not from target-table or
      filesystem inference.
    - `code_package_id` points at the canonical CodePackage for the generated
      package root.
    - `role` distinguishes API client and service protocol package outputs.
    """

    # --- AWARE: LOGIC START attach_language_package
    return await ApiPackageLanguagePackage.build_via_api_package(
        api_package_id=api_package.id,
        code_package_id=code_package_id,
        package_name=package_name,
        language=language,
        import_root=import_root,
        manifest_relative_path=manifest_relative_path,
        package_root=package_root,
        role=role,
        output_key=output_key,
        include_paths=JsonArray(include_paths or []),
        exclude_paths=JsonArray(exclude_paths or []),
    )
    # --- AWARE: LOGIC END attach_language_package
