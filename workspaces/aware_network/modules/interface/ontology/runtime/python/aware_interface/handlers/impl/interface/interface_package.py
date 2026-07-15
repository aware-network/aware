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
from aware_interface_ontology.interface.interface_package import InterfacePackage
from aware_interface_ontology.interface.interface_package_experience_package import InterfacePackageExperiencePackage
from aware_interface_ontology.interface.interface_package_pane_package import InterfacePackagePanePackage
from aware_interface_ontology.interface.interface_package_render_component_package import (
    InterfacePackageRenderComponentPackage,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Code Ontology
from aware_code_ontology.package.code_package import CodePackage
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)

# Interface Ontology
from aware_interface_ontology.interface.interface_config import InterfaceConfig
from aware_interface_ontology.stable_ids import (
    stable_interface_package_experience_package_id,
    stable_interface_package_pane_package_id,
    stable_interface_package_id,
)

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build(
    name: str,
    interface_config_id: UUID,
    interface_config_object_instance_graph_commit_id: UUID | None = None,
    source_code_package_id: UUID | None = None,
    fqn_prefix: str | None = None,
    version_number: int = 1,
    title: str | None = None,
    description: str | None = None,
    aware_interface_version: int = 1,
    manifest_relative_path: str | None = None,
    package_root: str = ".",
    sources_root: str = ".",
    config_bundle_path: str | None = None,
    include_paths: JsonArray = JsonArray(),
    exclude_paths: JsonArray = JsonArray(),
    force_fresh_scan: bool = True,
    compilation_mode: str = "raw_xor",
    dependencies: JsonArray = JsonArray(),
    dart: JsonObject = JsonObject(),
) -> InterfacePackage:
    """
    Create the canonical Interface-owned package root over an existing `InterfaceConfig`.

    Contract:
    - Identity is keyed by Interface package `name`.
    - `InterfacePackage` is the package/public root over an existing canonical `InterfaceConfig`.
    - `interface_config_id` must point at the canonical InterfaceConfig stable id for this package root.
    - `interface_config_object_instance_graph_commit_id` pins the historical ObjectInstanceGraphCommit
      for the semantic InterfaceConfig root so package consumers can replay exact interface truth
      without resolving branch head or reopening authoring TOML.
    - `source_code_package_id` is the explicit raw-source provenance link for this semantic leaf
    package.
    - Manifest/build/dependency/dart attributes mirror `aware.interface.toml` so committed package
      truth can drive Workspace and UI runtime routing without reopening authoring TOML.
    - Workspace will later mount `InterfacePackage`, not raw `InterfaceConfig`.
    """

    # --- AWARE: LOGIC START build
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("InterfacePackage.build requires non-empty name")
    normalized_fqn_prefix = (fqn_prefix or "").strip() or None
    normalized_title = (title or "").strip() or None
    normalized_description = (description or "").strip() or None
    normalized_manifest_relative_path = (manifest_relative_path or "").strip() or None
    normalized_package_root = (package_root or "").strip() or "."
    normalized_sources_root = (sources_root or "").strip() or "."
    normalized_config_bundle_path = (config_bundle_path or "").strip() or None
    normalized_compilation_mode = (compilation_mode or "").strip() or "raw_xor"
    include_paths_payload = JsonArray(include_paths or [])
    exclude_paths_payload = JsonArray(exclude_paths or [])
    dependencies_payload = JsonArray(dependencies or [])
    dart_payload = JsonObject(dart or {})

    package_id = stable_interface_package_id(name=normalized_name)

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    resolved_interface_config = session.imap_get(InterfaceConfig, interface_config_id) if session is not None else None
    resolved_source_code_package = (
        session.imap_get(CodePackage, source_code_package_id)
        if session is not None and source_code_package_id is not None
        else None
    )
    resolved_interface_config_oig_commit = (
        session.imap_get(
            ObjectInstanceGraphCommit,
            interface_config_object_instance_graph_commit_id,
        )
        if session is not None and interface_config_object_instance_graph_commit_id is not None
        else None
    )

    if session is not None:
        existing = session.imap_get(InterfacePackage, package_id)
        if existing is not None:
            if (existing.name or "").strip() != normalized_name:
                raise RuntimeError(
                    "InterfacePackage.build payload mismatch for existing package: "
                    f"interface_package_id={package_id}"
                )
            existing_interface_config_id = existing.interface_config_id
            if existing_interface_config_id != interface_config_id:
                raise RuntimeError(
                    "InterfacePackage.build interface_config_id mismatch for existing package: "
                    f"interface_package_id={package_id} "
                    f"existing={existing_interface_config_id} provided={interface_config_id}"
                )

            existing_source_code_package_id = existing.source_code_package_id
            if source_code_package_id is not None:
                if existing_source_code_package_id is None:
                    existing.source_code_package_id = source_code_package_id
                    existing.source_code_package = resolved_source_code_package
                elif existing_source_code_package_id != source_code_package_id:
                    raise RuntimeError(
                        "InterfacePackage.build source_code_package_id mismatch for existing package: "
                        f"interface_package_id={package_id} "
                        f"existing={existing_source_code_package_id} provided={source_code_package_id}"
                    )
            existing_interface_config_oig_commit_id = existing.interface_config_object_instance_graph_commit_id
            if interface_config_object_instance_graph_commit_id is not None:
                if existing_interface_config_oig_commit_id is None:
                    existing.interface_config_object_instance_graph_commit_id = (
                        interface_config_object_instance_graph_commit_id
                    )
                    existing.interface_config_object_instance_graph_commit = resolved_interface_config_oig_commit
                elif existing_interface_config_oig_commit_id != interface_config_object_instance_graph_commit_id:
                    raise RuntimeError(
                        "InterfacePackage.build interface_config_object_instance_graph_commit_id "
                        "mismatch for existing package: "
                        f"interface_package_id={package_id} "
                        f"existing={existing_interface_config_oig_commit_id} "
                        f"provided={interface_config_object_instance_graph_commit_id}"
                    )
            existing.fqn_prefix = normalized_fqn_prefix
            existing.version_number = version_number
            existing.title = normalized_title
            existing.description = normalized_description
            existing.aware_interface_version = aware_interface_version
            existing.manifest_relative_path = normalized_manifest_relative_path
            existing.package_root = normalized_package_root
            existing.sources_root = normalized_sources_root
            existing.config_bundle_path = normalized_config_bundle_path
            existing.include_paths = include_paths_payload
            existing.exclude_paths = exclude_paths_payload
            existing.force_fresh_scan = force_fresh_scan
            existing.compilation_mode = normalized_compilation_mode
            existing.dependencies = dependencies_payload
            existing.dart = dart_payload
            return existing

    return InterfacePackage.model_construct(
        id=package_id,
        name=normalized_name,
        interface_config=resolved_interface_config,
        interface_config_id=interface_config_id,
        interface_config_object_instance_graph_commit=resolved_interface_config_oig_commit,
        interface_config_object_instance_graph_commit_id=(interface_config_object_instance_graph_commit_id),
        source_code_package=resolved_source_code_package,
        source_code_package_id=source_code_package_id,
        fqn_prefix=normalized_fqn_prefix,
        version_number=version_number,
        title=normalized_title,
        description=normalized_description,
        aware_interface_version=aware_interface_version,
        manifest_relative_path=normalized_manifest_relative_path,
        package_root=normalized_package_root,
        sources_root=normalized_sources_root,
        config_bundle_path=normalized_config_bundle_path,
        include_paths=include_paths_payload,
        exclude_paths=exclude_paths_payload,
        force_fresh_scan=force_fresh_scan,
        compilation_mode=normalized_compilation_mode,
        dependencies=dependencies_payload,
        dart=dart_payload,
    )
    # --- AWARE: LOGIC END build


async def sync_manifest_truth(
    interface_package: InterfacePackage,
    interface_config_object_instance_graph_commit_id: UUID | None = None,
    source_code_package_id: UUID | None = None,
    fqn_prefix: str | None = None,
    version_number: int = 1,
    title: str | None = None,
    description: str | None = None,
    aware_interface_version: int = 1,
    manifest_relative_path: str | None = None,
    package_root: str = ".",
    sources_root: str = ".",
    config_bundle_path: str | None = None,
    include_paths: JsonArray = JsonArray(),
    exclude_paths: JsonArray = JsonArray(),
    force_fresh_scan: bool = True,
    compilation_mode: str = "raw_xor",
    dependencies: JsonArray = JsonArray(),
    dart: JsonObject = JsonObject(),
) -> InterfacePackage:
    """
    Sync mutable manifest/build/dependency/dart truth onto an existing InterfacePackage root.

    This keeps `build` create-only for empty package lanes while allowing committed package
    truth to follow the latest parsed `aware.interface.toml` snapshot and pinned semantic
    InterfaceConfig commit.
    """

    # --- AWARE: LOGIC START sync_manifest_truth
    normalized_name = (interface_package.name or "").strip()
    if not normalized_name:
        raise RuntimeError("InterfacePackage.sync_manifest_truth requires a named package")
    normalized_fqn_prefix = (fqn_prefix or "").strip() or None
    normalized_title = (title or "").strip() or None
    normalized_description = (description or "").strip() or None
    normalized_manifest_relative_path = (manifest_relative_path or "").strip() or None
    normalized_package_root = (package_root or "").strip() or "."
    normalized_sources_root = (sources_root or "").strip() or "."
    normalized_config_bundle_path = (config_bundle_path or "").strip() or None
    normalized_compilation_mode = (compilation_mode or "").strip() or "raw_xor"
    include_paths_payload = JsonArray(include_paths or [])
    exclude_paths_payload = JsonArray(exclude_paths or [])
    dependencies_payload = JsonArray(dependencies or [])
    dart_payload = JsonObject(dart or {})

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    if source_code_package_id is not None:
        resolved_source_code_package = (
            session.imap_get(CodePackage, source_code_package_id) if session is not None else None
        )
        existing_source_code_package_id = interface_package.source_code_package_id
        if existing_source_code_package_id is None:
            interface_package.source_code_package_id = source_code_package_id
            interface_package.source_code_package = resolved_source_code_package
        elif existing_source_code_package_id != source_code_package_id:
            raise RuntimeError(
                "InterfacePackage.sync_manifest_truth source_code_package_id mismatch: "
                f"interface_package_id={interface_package.id} "
                f"existing={existing_source_code_package_id} provided={source_code_package_id}"
            )

    if interface_config_object_instance_graph_commit_id is not None:
        resolved_interface_config_oig_commit = (
            session.imap_get(
                ObjectInstanceGraphCommit,
                interface_config_object_instance_graph_commit_id,
            )
            if session is not None
            else None
        )
        interface_package.interface_config_object_instance_graph_commit_id = (
            interface_config_object_instance_graph_commit_id
        )
        interface_package.interface_config_object_instance_graph_commit = resolved_interface_config_oig_commit

    interface_package.fqn_prefix = normalized_fqn_prefix
    interface_package.version_number = version_number
    interface_package.title = normalized_title
    interface_package.description = normalized_description
    interface_package.aware_interface_version = aware_interface_version
    interface_package.manifest_relative_path = normalized_manifest_relative_path
    interface_package.package_root = normalized_package_root
    interface_package.sources_root = normalized_sources_root
    interface_package.config_bundle_path = normalized_config_bundle_path
    interface_package.include_paths = include_paths_payload
    interface_package.exclude_paths = exclude_paths_payload
    interface_package.force_fresh_scan = force_fresh_scan
    interface_package.compilation_mode = normalized_compilation_mode
    interface_package.dependencies = dependencies_payload
    interface_package.dart = dart_payload
    return interface_package
    # --- AWARE: LOGIC END sync_manifest_truth


async def attach_experience_package(
    interface_package: InterfacePackage, experience_package_id: UUID, description: str | None = None
) -> InterfacePackageExperiencePackage:
    """
    Attach one Experience package to this InterfacePackage.

    Contract:
    - This is the package/import rail for authored Interface view ownership.
    - It declares which Experience packages supply canonical observable/view contracts to this
      Interface package.
    - Runtime pane resolution remains a later `observable -> experience view -> pane` seam.
    """

    # --- AWARE: LOGIC START attach_experience_package
    if interface_package.id is None:
        raise RuntimeError("InterfacePackage.attach_experience_package requires InterfacePackage.id")

    interface_package_experience_package_id = stable_interface_package_experience_package_id(
        interface_package_id=interface_package.id,
        experience_package_id=experience_package_id,
    )

    for existing in interface_package.experience_packages:
        if (
            existing.id == interface_package_experience_package_id
            or existing.experience_package_id == experience_package_id
        ):
            return existing

    created = InterfacePackageExperiencePackage.model_construct(
        id=interface_package_experience_package_id,
        interface_package_id=interface_package.id,
        experience_package=None,
        experience_package_id=experience_package_id,
        description=description,
    )
    interface_package.experience_packages.append(created)
    return created
    # --- AWARE: LOGIC END attach_experience_package


async def attach_pane_package(
    interface_package: InterfacePackage, pane_package_id: UUID, description: str | None = None
) -> InterfacePackagePanePackage:
    """
    Attach one pane package to this InterfacePackage.

    Contract:
    - This is the package/import rail for canonical pane implementation ownership.
    - It lets Interface packages compose pane packages explicitly instead of guessing pane runtime
    packages.
    - Runtime registrar loading remains a later seam; this cut only establishes package dependency
    truth.
    """

    # --- AWARE: LOGIC START attach_pane_package
    if interface_package.id is None:
        raise RuntimeError("InterfacePackage.attach_pane_package requires InterfacePackage.id")

    interface_package_pane_package_id = stable_interface_package_pane_package_id(
        interface_package_id=interface_package.id,
        pane_package_id=pane_package_id,
    )

    for existing in interface_package.pane_packages:
        if existing.id == interface_package_pane_package_id or existing.pane_package_id == pane_package_id:
            return existing

    created = InterfacePackagePanePackage.model_construct(
        id=interface_package_pane_package_id,
        interface_package_id=interface_package.id,
        pane_package=None,
        pane_package_id=pane_package_id,
        description=description,
    )
    interface_package.pane_packages.append(created)
    return created
    # --- AWARE: LOGIC END attach_pane_package


async def attach_render_component_package(
    interface_package: InterfacePackage, render_component_package_id: UUID, description: str | None = None
) -> InterfacePackageRenderComponentPackage:
    """
    Attach one render component package to this InterfacePackage.

    Contract:
    - This is the package/import rail for reusable rich renderer component contracts.
    - Interface packages declare component availability explicitly so renderers do not guess
      native capability registries from pane implementation details.
    - Pane packages still decide which components their PaneRenderSpec may reference.
    """

    # --- AWARE: LOGIC START attach_render_component_package
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END attach_render_component_package
