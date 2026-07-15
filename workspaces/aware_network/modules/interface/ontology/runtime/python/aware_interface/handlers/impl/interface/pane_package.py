from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import (
    JsonArray,
    JsonObject,
)

# Interface Ontology
from aware_interface_ontology.interface.pane_package import PanePackage
from aware_interface_ontology.interface.pane_package_experience_package import PanePackageExperiencePackage
from aware_interface_ontology.interface.pane_package_render_component_package import PanePackageRenderComponentPackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Code Ontology
from aware_code_ontology.package.code_package import CodePackage
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)

# Interface Ontology
from aware_interface_ontology.interface.pane_package_experience_package import (
    PanePackageExperiencePackage,
)
from aware_interface_ontology.interface.pane_config import PaneConfig
from aware_interface_ontology.stable_ids import (
    stable_pane_package_experience_package_id,
    stable_pane_package_id,
)

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build(
    name: str,
    pane_config_id: UUID,
    pane_config_object_instance_graph_commit_id: UUID | None = None,
    source_code_package_id: UUID | None = None,
    fqn_prefix: str | None = None,
    pane_name: str | None = None,
    version_number: int = 1,
    title: str | None = None,
    description: str | None = None,
    aware_pane_version: int = 1,
    manifest_relative_path: str | None = None,
    package_root: str = ".",
    sources_root: str = ".",
    include_paths: JsonArray = JsonArray(),
    exclude_paths: JsonArray = JsonArray(),
    force_fresh_scan: bool = True,
    python: JsonObject = JsonObject(),
    dart: JsonObject = JsonObject(),
) -> PanePackage:
    """
    Create the canonical Pane-owned package root over an existing `PaneConfig`.

    Contract:
    - Identity is keyed by pane package `name`.
    - `PanePackage` is the package/public root over an existing canonical `PaneConfig`.
    - `pane_config_id` must point at the canonical standalone pane semantic id for this package root.
    - `pane_config_object_instance_graph_commit_id` pins the historical ObjectInstanceGraphCommit
      for the semantic PaneConfig root so package consumers can replay exact pane truth without
      resolving branch head or reopening authoring TOML.
    - `source_code_package_id` is the explicit raw-source provenance link for this semantic leaf
    package.
    - Manifest/build/python/dart attributes mirror `aware.pane.toml` so committed package truth
      can drive Interface and Workspace pane routing without reopening authoring TOML.
    - Interface packages and later Workspace mounts should depend on `PanePackage`, not raw
    `PaneConfig`.
    """

    # --- AWARE: LOGIC START build
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("PanePackage.build requires non-empty name")
    normalized_fqn_prefix = (fqn_prefix or "").strip() or None
    normalized_pane_name = (pane_name or "").strip() or None
    normalized_title = (title or "").strip() or None
    normalized_description = (description or "").strip() or None
    normalized_manifest_relative_path = (manifest_relative_path or "").strip() or None
    normalized_package_root = (package_root or "").strip() or "."
    normalized_sources_root = (sources_root or "").strip() or "."
    include_paths_payload = JsonArray(include_paths or [])
    exclude_paths_payload = JsonArray(exclude_paths or [])
    python_payload = JsonObject(python or {})
    dart_payload = JsonObject(dart or {})

    package_id = stable_pane_package_id(name=normalized_name)

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    resolved_pane_config = session.imap_get(PaneConfig, pane_config_id) if session is not None else None
    resolved_source_code_package = (
        session.imap_get(CodePackage, source_code_package_id)
        if session is not None and source_code_package_id is not None
        else None
    )
    resolved_pane_config_oig_commit = (
        session.imap_get(
            ObjectInstanceGraphCommit,
            pane_config_object_instance_graph_commit_id,
        )
        if session is not None and pane_config_object_instance_graph_commit_id is not None
        else None
    )

    if session is not None:
        existing = session.imap_get(PanePackage, package_id)
        if existing is not None:
            if (existing.name or "").strip() != normalized_name:
                raise RuntimeError(
                    "PanePackage.build payload mismatch for existing package: " f"pane_package_id={package_id}"
                )
            existing_pane_config_id = existing.pane_config_id
            if existing_pane_config_id != pane_config_id:
                raise RuntimeError(
                    "PanePackage.build pane_config_id mismatch for existing package: "
                    f"pane_package_id={package_id} "
                    f"existing={existing_pane_config_id} provided={pane_config_id}"
                )

            existing_source_code_package_id = existing.source_code_package_id
            if source_code_package_id is not None:
                if existing_source_code_package_id is None:
                    existing.source_code_package_id = source_code_package_id
                    existing.source_code_package = resolved_source_code_package
                elif existing_source_code_package_id != source_code_package_id:
                    raise RuntimeError(
                        "PanePackage.build source_code_package_id mismatch for existing package: "
                        f"pane_package_id={package_id} "
                        f"existing={existing_source_code_package_id} provided={source_code_package_id}"
                    )
            existing_pane_config_oig_commit_id = existing.pane_config_object_instance_graph_commit_id
            if pane_config_object_instance_graph_commit_id is not None:
                if existing_pane_config_oig_commit_id is None:
                    existing.pane_config_object_instance_graph_commit_id = pane_config_object_instance_graph_commit_id
                    existing.pane_config_object_instance_graph_commit = resolved_pane_config_oig_commit
                elif existing_pane_config_oig_commit_id != pane_config_object_instance_graph_commit_id:
                    raise RuntimeError(
                        "PanePackage.build pane_config_object_instance_graph_commit_id "
                        "mismatch for existing package: "
                        f"pane_package_id={package_id} "
                        f"existing={existing_pane_config_oig_commit_id} "
                        f"provided={pane_config_object_instance_graph_commit_id}"
                    )
            existing.fqn_prefix = normalized_fqn_prefix
            existing.pane_name = normalized_pane_name
            existing.version_number = version_number
            existing.title = normalized_title
            existing.description = normalized_description
            existing.aware_pane_version = aware_pane_version
            existing.manifest_relative_path = normalized_manifest_relative_path
            existing.package_root = normalized_package_root
            existing.sources_root = normalized_sources_root
            existing.include_paths = include_paths_payload
            existing.exclude_paths = exclude_paths_payload
            existing.force_fresh_scan = force_fresh_scan
            existing.python = python_payload
            existing.dart = dart_payload
            return existing

    return PanePackage.model_construct(
        id=package_id,
        name=normalized_name,
        experience_packages=[],
        render_component_packages=[],
        pane_config=resolved_pane_config,
        pane_config_id=pane_config_id,
        pane_config_object_instance_graph_commit=resolved_pane_config_oig_commit,
        pane_config_object_instance_graph_commit_id=pane_config_object_instance_graph_commit_id,
        source_code_package=resolved_source_code_package,
        source_code_package_id=source_code_package_id,
        fqn_prefix=normalized_fqn_prefix,
        pane_name=normalized_pane_name,
        version_number=version_number,
        title=normalized_title,
        description=normalized_description,
        aware_pane_version=aware_pane_version,
        manifest_relative_path=normalized_manifest_relative_path,
        package_root=normalized_package_root,
        sources_root=normalized_sources_root,
        include_paths=include_paths_payload,
        exclude_paths=exclude_paths_payload,
        force_fresh_scan=force_fresh_scan,
        python=python_payload,
        dart=dart_payload,
    )
    # --- AWARE: LOGIC END build


async def sync_manifest_truth(
    pane_package: PanePackage,
    pane_config_object_instance_graph_commit_id: UUID | None = None,
    source_code_package_id: UUID | None = None,
    fqn_prefix: str | None = None,
    pane_name: str | None = None,
    version_number: int = 1,
    title: str | None = None,
    description: str | None = None,
    aware_pane_version: int = 1,
    manifest_relative_path: str | None = None,
    package_root: str = ".",
    sources_root: str = ".",
    include_paths: JsonArray = JsonArray(),
    exclude_paths: JsonArray = JsonArray(),
    force_fresh_scan: bool = True,
    python: JsonObject = JsonObject(),
    dart: JsonObject = JsonObject(),
) -> PanePackage:
    """
    Sync mutable manifest/build/python/dart truth onto an existing PanePackage root.

    This keeps `build` create-only for empty package lanes while allowing committed package
    truth to follow the latest parsed `aware.pane.toml` snapshot and pinned semantic PaneConfig
    commit.
    """

    # --- AWARE: LOGIC START sync_manifest_truth
    normalized_name = (pane_package.name or "").strip()
    if not normalized_name:
        raise RuntimeError("PanePackage.sync_manifest_truth requires a named package")
    normalized_fqn_prefix = (fqn_prefix or "").strip() or None
    normalized_pane_name = (pane_name or "").strip() or None
    normalized_title = (title or "").strip() or None
    normalized_description = (description or "").strip() or None
    normalized_manifest_relative_path = (manifest_relative_path or "").strip() or None
    normalized_package_root = (package_root or "").strip() or "."
    normalized_sources_root = (sources_root or "").strip() or "."
    include_paths_payload = JsonArray(include_paths or [])
    exclude_paths_payload = JsonArray(exclude_paths or [])
    python_payload = JsonObject(python or {})
    dart_payload = JsonObject(dart or {})

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    if source_code_package_id is not None:
        resolved_source_code_package = (
            session.imap_get(CodePackage, source_code_package_id) if session is not None else None
        )
        existing_source_code_package_id = pane_package.source_code_package_id
        if existing_source_code_package_id is None:
            pane_package.source_code_package_id = source_code_package_id
            pane_package.source_code_package = resolved_source_code_package
        elif existing_source_code_package_id != source_code_package_id:
            raise RuntimeError(
                "PanePackage.sync_manifest_truth source_code_package_id mismatch: "
                f"pane_package_id={pane_package.id} "
                f"existing={existing_source_code_package_id} provided={source_code_package_id}"
            )

    if pane_config_object_instance_graph_commit_id is not None:
        resolved_pane_config_oig_commit = (
            session.imap_get(
                ObjectInstanceGraphCommit,
                pane_config_object_instance_graph_commit_id,
            )
            if session is not None
            else None
        )
        pane_package.pane_config_object_instance_graph_commit_id = pane_config_object_instance_graph_commit_id
        pane_package.pane_config_object_instance_graph_commit = resolved_pane_config_oig_commit

    pane_package.fqn_prefix = normalized_fqn_prefix
    pane_package.pane_name = normalized_pane_name
    pane_package.version_number = version_number
    pane_package.title = normalized_title
    pane_package.description = normalized_description
    pane_package.aware_pane_version = aware_pane_version
    pane_package.manifest_relative_path = normalized_manifest_relative_path
    pane_package.package_root = normalized_package_root
    pane_package.sources_root = normalized_sources_root
    pane_package.include_paths = include_paths_payload
    pane_package.exclude_paths = exclude_paths_payload
    pane_package.force_fresh_scan = force_fresh_scan
    pane_package.python = python_payload
    pane_package.dart = dart_payload
    return pane_package
    # --- AWARE: LOGIC END sync_manifest_truth


async def attach_experience_package(
    pane_package: PanePackage, experience_package_id: UUID, description: str | None = None
) -> PanePackageExperiencePackage:
    """
    Attach one Experience package to this PanePackage.

    Contract:
    - This is the pane-local package/import rail for the one Experience view
      a PaneConfig adapts.
    - Pane packages resolve ProjectionExperienceView through this declared
      dependency before any Interface package consumes the pane.
    - Interface packages must not use their own Experience package
      dependencies to rescue unresolved pane view refs.
    """

    # --- AWARE: LOGIC START attach_experience_package
    if pane_package.id is None:
        raise RuntimeError("PanePackage.attach_experience_package requires PanePackage.id")

    edge_id = stable_pane_package_experience_package_id(
        pane_package_id=pane_package.id,
        experience_package_id=experience_package_id,
    )

    for existing in pane_package.experience_packages:
        if existing.id == edge_id or existing.experience_package_id == experience_package_id:
            return existing

    created = PanePackageExperiencePackage.model_construct(
        id=edge_id,
        pane_package_id=pane_package.id,
        experience_package=None,
        experience_package_id=experience_package_id,
        description=description,
    )
    pane_package.experience_packages.append(created)
    return created
    # --- AWARE: LOGIC END attach_experience_package


async def attach_render_component_package(
    pane_package: PanePackage, render_component_package_id: UUID, description: str | None = None
) -> PanePackageRenderComponentPackage:
    """
    Attach one render component package to this PanePackage.

    Contract:
    - This is the pane-local package/import rail for rich renderer component contracts.
    - It declares which reusable components authored PaneRenderSpec nodes may reference.
    - Components provide ports and renderer capability requirements; they do not own pane state
      or bypass canonical ActionBinding/API execution.
    """

    # --- AWARE: LOGIC START attach_render_component_package
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END attach_render_component_package
