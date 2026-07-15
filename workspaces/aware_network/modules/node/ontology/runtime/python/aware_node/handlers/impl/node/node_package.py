from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonArray

# Node Ontology
from aware_node_ontology.node.node_package import NodePackage
from aware_node_ontology.node.node_package_included_node_package import NodePackageIncludedNodePackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code_ontology.package.code_package import CodePackage
from aware_node_ontology.node.node_config import NodeConfig
from aware_node_ontology.stable_ids import (
    stable_node_package_id,
    stable_node_package_included_node_package_id,
)
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build(
    name: str,
    node_config_id: UUID,
    source_code_package_id: UUID | None = None,
    fqn_prefix: str | None = None,
    version_number: int = 1,
    title: str | None = None,
    description: str | None = None,
    aware_node_version: int = 1,
    manifest_relative_path: str | None = None,
    package_root: str = ".",
    sources_root: str = "nodes",
    include_paths: JsonArray = JsonArray(),
    exclude_paths: JsonArray = JsonArray(),
    force_fresh_scan: bool = True,
    compilation_mode: str = "raw_xor",
    dependencies: JsonArray = JsonArray(),
) -> NodePackage:
    """
    Create the canonical Node-owned package root over an existing `NodeConfig`.

    Contract:
    - Identity is keyed by Node package `name`.
    - `NodePackage` is the package/public root over an existing canonical `NodeConfig`.
    - `node_config_id` must point at the canonical NodeConfig stable id for this package root.
    - `source_code_package_id` is the explicit raw-source provenance link for this semantic
      leaf package.
    - Manifest/build/dependency attributes mirror `aware.node.toml` so committed package truth
      can drive Workspace and Node runtime resolution without reopening authoring TOML.
    - Workspace will later mount `NodePackage`, not raw `NodeConfig`.
    """

    # --- AWARE: LOGIC START build
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("NodePackage.build requires non-empty name")
    normalized_fqn_prefix = (fqn_prefix or "").strip() or None
    normalized_title = (title or "").strip() or None
    normalized_description = (description or "").strip() or None
    normalized_manifest_relative_path = (manifest_relative_path or "").strip() or None
    normalized_package_root = (package_root or "").strip() or "."
    normalized_sources_root = (sources_root or "").strip() or "nodes"
    normalized_compilation_mode = (compilation_mode or "").strip() or "raw_xor"
    include_paths_payload = JsonArray(include_paths or [])
    exclude_paths_payload = JsonArray(exclude_paths or [])
    dependencies_payload = JsonArray(dependencies or [])

    package_id = stable_node_package_id(name=normalized_name)

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    resolved_node_config = session.imap_get(NodeConfig, node_config_id) if session is not None else None
    resolved_source_code_package = (
        session.imap_get(CodePackage, source_code_package_id)
        if session is not None and source_code_package_id is not None
        else None
    )

    if session is not None:
        existing = session.imap_get(NodePackage, package_id)
        if existing is not None:
            if (existing.name or "").strip() != normalized_name:
                raise RuntimeError(
                    "NodePackage.build payload mismatch for existing package: " f"node_package_id={package_id}"
                )
            if existing.node_config_id != node_config_id:
                raise RuntimeError(
                    "NodePackage.build node_config_id mismatch for existing package: "
                    f"node_package_id={package_id} "
                    f"existing={existing.node_config_id} provided={node_config_id}"
                )

            existing_source_code_package_id = existing.source_code_package_id
            if source_code_package_id is not None:
                if existing_source_code_package_id is None:
                    existing.source_code_package_id = source_code_package_id
                    existing.source_code_package = resolved_source_code_package
                elif existing_source_code_package_id != source_code_package_id:
                    raise RuntimeError(
                        "NodePackage.build source_code_package_id mismatch for existing package: "
                        f"node_package_id={package_id} "
                        f"existing={existing_source_code_package_id} provided={source_code_package_id}"
                    )
            existing.fqn_prefix = normalized_fqn_prefix
            existing.version_number = version_number
            existing.title = normalized_title
            existing.description = normalized_description
            existing.aware_node_version = aware_node_version
            existing.manifest_relative_path = normalized_manifest_relative_path
            existing.package_root = normalized_package_root
            existing.sources_root = normalized_sources_root
            existing.include_paths = include_paths_payload
            existing.exclude_paths = exclude_paths_payload
            existing.force_fresh_scan = force_fresh_scan
            existing.compilation_mode = normalized_compilation_mode
            existing.dependencies = dependencies_payload
            return existing

    return NodePackage.model_construct(
        id=package_id,
        name=normalized_name,
        node_config=resolved_node_config,
        node_config_id=node_config_id,
        source_code_package=resolved_source_code_package,
        source_code_package_id=source_code_package_id,
        fqn_prefix=normalized_fqn_prefix,
        version_number=version_number,
        title=normalized_title,
        description=normalized_description,
        aware_node_version=aware_node_version,
        manifest_relative_path=normalized_manifest_relative_path,
        package_root=normalized_package_root,
        sources_root=normalized_sources_root,
        include_paths=include_paths_payload,
        exclude_paths=exclude_paths_payload,
        force_fresh_scan=force_fresh_scan,
        compilation_mode=normalized_compilation_mode,
        dependencies=dependencies_payload,
    )
    # --- AWARE: LOGIC END build


async def sync_manifest_truth(
    node_package: NodePackage,
    source_code_package_id: UUID | None = None,
    fqn_prefix: str | None = None,
    version_number: int = 1,
    title: str | None = None,
    description: str | None = None,
    aware_node_version: int = 1,
    manifest_relative_path: str | None = None,
    package_root: str = ".",
    sources_root: str = "nodes",
    include_paths: JsonArray = JsonArray(),
    exclude_paths: JsonArray = JsonArray(),
    force_fresh_scan: bool = True,
    compilation_mode: str = "raw_xor",
    dependencies: JsonArray = JsonArray(),
) -> NodePackage:
    """
    Sync mutable manifest/build/dependency truth onto an existing NodePackage root.

    This keeps `build` create-only for empty package lanes while allowing committed package
    truth to follow the latest parsed `aware.node.toml` snapshot.
    """

    # --- AWARE: LOGIC START sync_manifest_truth
    normalized_name = (node_package.name or "").strip()
    if not normalized_name:
        raise RuntimeError("NodePackage.sync_manifest_truth requires a named package")
    normalized_fqn_prefix = (fqn_prefix or "").strip() or None
    normalized_title = (title or "").strip() or None
    normalized_description = (description or "").strip() or None
    normalized_manifest_relative_path = (manifest_relative_path or "").strip() or None
    normalized_package_root = (package_root or "").strip() or "."
    normalized_sources_root = (sources_root or "").strip() or "nodes"
    normalized_compilation_mode = (compilation_mode or "").strip() or "raw_xor"
    include_paths_payload = JsonArray(include_paths or [])
    exclude_paths_payload = JsonArray(exclude_paths or [])
    dependencies_payload = JsonArray(dependencies or [])

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    if source_code_package_id is not None:
        resolved_source_code_package = (
            session.imap_get(CodePackage, source_code_package_id) if session is not None else None
        )
        existing_source_code_package_id = node_package.source_code_package_id
        if existing_source_code_package_id is None:
            node_package.source_code_package_id = source_code_package_id
            node_package.source_code_package = resolved_source_code_package
        elif existing_source_code_package_id != source_code_package_id:
            raise RuntimeError(
                "NodePackage.sync_manifest_truth source_code_package_id mismatch: "
                f"node_package_id={node_package.id} "
                f"existing={existing_source_code_package_id} provided={source_code_package_id}"
            )

    node_package.fqn_prefix = normalized_fqn_prefix
    node_package.version_number = version_number
    node_package.title = normalized_title
    node_package.description = normalized_description
    node_package.aware_node_version = aware_node_version
    node_package.manifest_relative_path = normalized_manifest_relative_path
    node_package.package_root = normalized_package_root
    node_package.sources_root = normalized_sources_root
    node_package.include_paths = include_paths_payload
    node_package.exclude_paths = exclude_paths_payload
    node_package.force_fresh_scan = force_fresh_scan
    node_package.compilation_mode = normalized_compilation_mode
    node_package.dependencies = dependencies_payload
    return node_package
    # --- AWARE: LOGIC END sync_manifest_truth


async def attach_included_node_package(
    node_package: NodePackage,
    included_package_name: str,
    include_key: str | None = None,
    description: str | None = None,
) -> NodePackageIncludedNodePackage:
    """
    Attach one package-level Node composition include.

    Contract:
    - Parent `NodePackage` scope is injected by propagation.
    - Identity is keyed by the included package's semantic package name.
    - The bridge resolves and stores the canonical included `NodePackage` relationship.
    - Includes select composition participants only; ServicePackage API bridge truth still
      drives route requirements.
    """

    # --- AWARE: LOGIC START attach_included_node_package
    if node_package.id is None:
        raise RuntimeError("NodePackage.attach_included_node_package requires NodePackage.id")
    normalized_included_package_name = (included_package_name or "").strip()
    if not normalized_included_package_name:
        raise RuntimeError("NodePackage.attach_included_node_package requires non-empty included_package_name")
    normalized_include_key = (include_key or "").strip() or normalized_included_package_name
    normalized_description = (description or "").strip() or None

    if node_package.name and node_package.name.strip() == normalized_included_package_name:
        raise RuntimeError(
            "NodePackage.attach_included_node_package cannot include the owning NodePackage: "
            f"node_package={node_package.name!r}"
        )

    include_id = stable_node_package_included_node_package_id(
        node_package_id=node_package.id,
        included_package_name=normalized_included_package_name,
    )
    for existing in node_package.included_node_packages:
        if existing.id == include_id or existing.included_package_name == normalized_included_package_name:
            return existing

    created = await NodePackageIncludedNodePackage.build_via_node_package(
        node_package_id=node_package.id,
        included_package_name=normalized_included_package_name,
        include_key=normalized_include_key,
        description=normalized_description,
    )
    node_package.included_node_packages.append(created)
    return created
    # --- AWARE: LOGIC END attach_included_node_package
