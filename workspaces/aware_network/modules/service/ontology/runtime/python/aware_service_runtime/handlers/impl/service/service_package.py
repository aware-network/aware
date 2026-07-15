from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonArray

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Service Ontology
from aware_service_ontology.service.service_package import ServicePackage
from aware_service_ontology.service.service_package_implementation_package import ServicePackageImplementationPackage
from aware_service_ontology.service.service_package_object_config_graph_package import (
    ServicePackageObjectConfigGraphPackage,
)
from aware_service_ontology.service.service_package_ontology_package import ServicePackageOntologyPackage
from aware_service_ontology.service.service_package_provided_api_package import ServicePackageProvidedApiPackage
from aware_service_ontology.service.service_package_required_api_package import ServicePackageRequiredApiPackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code_ontology.package.code_package import CodePackage
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_service_ontology.service.service_config import ServiceConfig
from aware_service_ontology.stable_ids import (
    stable_service_package_id,
    stable_service_package_implementation_package_id,
    stable_service_package_provided_api_package_id,
    stable_service_package_required_api_package_id,
)
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build(
    name: str,
    service_config_id: UUID,
    service_config_object_instance_graph_commit_id: UUID | None = None,
    source_code_package_id: UUID | None = None,
    fqn_prefix: str | None = None,
    version_number: int = 1,
    title: str | None = None,
    description: str | None = None,
    aware_service_version: int = 1,
    manifest_relative_path: str | None = None,
    package_root: str = ".",
    sources_root: str = "services",
    include_paths: JsonArray = JsonArray(),
    exclude_paths: JsonArray = JsonArray(),
    force_fresh_scan: bool = True,
    compilation_mode: str = "raw_xor",
    service_surface: str = "service",
    activation_mode: str = "materialize_and_load_committed",
    materialize_on_start: bool = True,
    dependencies: JsonArray = JsonArray(),
) -> ServicePackage:
    """
    Create the canonical Service-owned package root over an existing `ServiceConfig`.

    Contract:
    - Identity is keyed by Service package `name`.
    - `ServicePackage` is the package/public root over an existing canonical `ServiceConfig`.
    - `service_config_id` must point at the canonical ServiceConfig stable id for this package root.
    - `service_config_object_instance_graph_commit_id` pins the historical ObjectInstanceGraphCommit
      for the semantic ServiceConfig root so package consumers can replay exact service truth without
      resolving branch head.
    - `source_code_package_id` is the explicit raw-source provenance link for this semantic leaf
    package.
    - Manifest/build/host/dependency attributes mirror `aware.service.toml` so committed package truth
    can
      drive Workspace and Service runtime resolution without reopening authoring TOML.
    - Workspace will later mount `ServicePackage`, not raw `ServiceConfig`.
    """

    # --- AWARE: LOGIC START build
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("ServicePackage.build requires non-empty name")
    normalized_fqn_prefix = (fqn_prefix or "").strip() or None
    normalized_title = (title or "").strip() or None
    normalized_description = (description or "").strip() or None
    normalized_manifest_relative_path = (manifest_relative_path or "").strip() or None
    normalized_package_root = (package_root or "").strip() or "."
    normalized_sources_root = (sources_root or "").strip() or "services"
    normalized_compilation_mode = (compilation_mode or "").strip() or "raw_xor"
    normalized_service_surface = (service_surface or "").strip() or "service"
    normalized_activation_mode = (activation_mode or "").strip() or "materialize_and_load_committed"
    include_paths_payload = JsonArray(include_paths or [])
    exclude_paths_payload = JsonArray(exclude_paths or [])
    dependencies_payload = JsonArray(dependencies or [])

    package_id = stable_service_package_id(name=normalized_name)

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    resolved_service_config = session.imap_get(ServiceConfig, service_config_id) if session is not None else None
    resolved_source_code_package = (
        session.imap_get(CodePackage, source_code_package_id)
        if session is not None and source_code_package_id is not None
        else None
    )
    resolved_service_config_oig_commit = (
        session.imap_get(
            ObjectInstanceGraphCommit,
            service_config_object_instance_graph_commit_id,
        )
        if session is not None and service_config_object_instance_graph_commit_id is not None
        else None
    )

    if session is not None:
        existing = session.imap_get(ServicePackage, package_id)
        if existing is not None:
            if (existing.name or "").strip() != normalized_name:
                raise RuntimeError(
                    "ServicePackage.build payload mismatch for existing package: " f"service_package_id={package_id}"
                )
            if existing.service_config_id != service_config_id:
                raise RuntimeError(
                    "ServicePackage.build service_config_id mismatch for existing package: "
                    f"service_package_id={package_id} "
                    f"existing={existing.service_config_id} provided={service_config_id}"
                )

            existing_source_code_package_id = existing.source_code_package_id
            if source_code_package_id is not None:
                if existing_source_code_package_id is None:
                    existing.source_code_package_id = source_code_package_id
                    existing.source_code_package = resolved_source_code_package
                elif existing_source_code_package_id != source_code_package_id:
                    raise RuntimeError(
                        "ServicePackage.build source_code_package_id mismatch for existing package: "
                        f"service_package_id={package_id} "
                        f"existing={existing_source_code_package_id} provided={source_code_package_id}"
                    )
            existing.fqn_prefix = normalized_fqn_prefix
            existing_service_config_oig_commit_id = existing.service_config_object_instance_graph_commit_id
            if service_config_object_instance_graph_commit_id is not None:
                if existing_service_config_oig_commit_id is None:
                    existing.service_config_object_instance_graph_commit_id = (
                        service_config_object_instance_graph_commit_id
                    )
                    existing.service_config_object_instance_graph_commit = resolved_service_config_oig_commit
                elif existing_service_config_oig_commit_id != service_config_object_instance_graph_commit_id:
                    raise RuntimeError(
                        "ServicePackage.build service_config_object_instance_graph_commit_id "
                        "mismatch for existing package: "
                        f"service_package_id={package_id} "
                        f"existing={existing_service_config_oig_commit_id} "
                        f"provided={service_config_object_instance_graph_commit_id}"
                    )
            existing.version_number = version_number
            existing.title = normalized_title
            existing.description = normalized_description
            existing.aware_service_version = aware_service_version
            existing.manifest_relative_path = normalized_manifest_relative_path
            existing.package_root = normalized_package_root
            existing.sources_root = normalized_sources_root
            existing.include_paths = include_paths_payload
            existing.exclude_paths = exclude_paths_payload
            existing.force_fresh_scan = force_fresh_scan
            existing.compilation_mode = normalized_compilation_mode
            existing.service_surface = normalized_service_surface
            existing.activation_mode = normalized_activation_mode
            existing.materialize_on_start = materialize_on_start
            existing.dependencies = dependencies_payload
            return existing

    return ServicePackage.model_construct(
        id=package_id,
        name=normalized_name,
        service_config=resolved_service_config,
        service_config_id=service_config_id,
        service_config_object_instance_graph_commit=resolved_service_config_oig_commit,
        service_config_object_instance_graph_commit_id=(service_config_object_instance_graph_commit_id),
        source_code_package=resolved_source_code_package,
        source_code_package_id=source_code_package_id,
        implementation_packages=[],
        ontology_packages=[],
        object_config_graph_packages=[],
        provided_api_packages=[],
        required_api_packages=[],
        fqn_prefix=normalized_fqn_prefix,
        version_number=version_number,
        title=normalized_title,
        description=normalized_description,
        aware_service_version=aware_service_version,
        manifest_relative_path=normalized_manifest_relative_path,
        package_root=normalized_package_root,
        sources_root=normalized_sources_root,
        include_paths=include_paths_payload,
        exclude_paths=exclude_paths_payload,
        force_fresh_scan=force_fresh_scan,
        compilation_mode=normalized_compilation_mode,
        service_surface=normalized_service_surface,
        activation_mode=normalized_activation_mode,
        materialize_on_start=materialize_on_start,
        dependencies=dependencies_payload,
    )
    # --- AWARE: LOGIC END build


async def sync_manifest_truth(
    service_package: ServicePackage,
    service_config_object_instance_graph_commit_id: UUID | None = None,
    source_code_package_id: UUID | None = None,
    fqn_prefix: str | None = None,
    version_number: int = 1,
    title: str | None = None,
    description: str | None = None,
    aware_service_version: int = 1,
    manifest_relative_path: str | None = None,
    package_root: str = ".",
    sources_root: str = "services",
    include_paths: JsonArray = JsonArray(),
    exclude_paths: JsonArray = JsonArray(),
    force_fresh_scan: bool = True,
    compilation_mode: str = "raw_xor",
    service_surface: str = "service",
    activation_mode: str = "materialize_and_load_committed",
    materialize_on_start: bool = True,
    dependencies: JsonArray = JsonArray(),
) -> ServicePackage:
    """
    Sync mutable manifest/build/host/dependency truth onto an existing ServicePackage root.

    This keeps `build` create-only for empty package lanes while allowing committed package truth to
    follow the latest parsed `aware.service.toml` snapshot and pinned semantic ServiceConfig commit.
    """

    # --- AWARE: LOGIC START sync_manifest_truth
    normalized_name = (service_package.name or "").strip()
    if not normalized_name:
        raise RuntimeError("ServicePackage.sync_manifest_truth requires a named package")
    normalized_fqn_prefix = (fqn_prefix or "").strip() or None
    normalized_title = (title or "").strip() or None
    normalized_description = (description or "").strip() or None
    normalized_manifest_relative_path = (manifest_relative_path or "").strip() or None
    normalized_package_root = (package_root or "").strip() or "."
    normalized_sources_root = (sources_root or "").strip() or "services"
    normalized_compilation_mode = (compilation_mode or "").strip() or "raw_xor"
    normalized_service_surface = (service_surface or "").strip() or "service"
    normalized_activation_mode = (activation_mode or "").strip() or "materialize_and_load_committed"
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
        existing_source_code_package_id = service_package.source_code_package_id
        if existing_source_code_package_id is None:
            service_package.source_code_package_id = source_code_package_id
            service_package.source_code_package = resolved_source_code_package
        elif existing_source_code_package_id != source_code_package_id:
            raise RuntimeError(
                "ServicePackage.sync_manifest_truth source_code_package_id mismatch: "
                f"service_package_id={service_package.id} "
                f"existing={existing_source_code_package_id} provided={source_code_package_id}"
            )

    if service_config_object_instance_graph_commit_id is not None:
        resolved_service_config_oig_commit = (
            session.imap_get(
                ObjectInstanceGraphCommit,
                service_config_object_instance_graph_commit_id,
            )
            if session is not None
            else None
        )
        service_package.service_config_object_instance_graph_commit_id = service_config_object_instance_graph_commit_id
        service_package.service_config_object_instance_graph_commit = resolved_service_config_oig_commit

    service_package.fqn_prefix = normalized_fqn_prefix
    service_package.version_number = version_number
    service_package.title = normalized_title
    service_package.description = normalized_description
    service_package.aware_service_version = aware_service_version
    service_package.manifest_relative_path = normalized_manifest_relative_path
    service_package.package_root = normalized_package_root
    service_package.sources_root = normalized_sources_root
    service_package.include_paths = include_paths_payload
    service_package.exclude_paths = exclude_paths_payload
    service_package.force_fresh_scan = force_fresh_scan
    service_package.compilation_mode = normalized_compilation_mode
    service_package.service_surface = normalized_service_surface
    service_package.activation_mode = normalized_activation_mode
    service_package.materialize_on_start = materialize_on_start
    service_package.dependencies = dependencies_payload
    return service_package
    # --- AWARE: LOGIC END sync_manifest_truth


async def attach_provided_api_package(
    service_package: ServicePackage,
    api_package_id: UUID,
    service_protocol_package_id: UUID,
    service_protocol_plan_hash_sha256: str,
    api_package_object_instance_graph_commit_id: UUID,
    description: str | None = None,
) -> ServicePackageProvidedApiPackage:
    """
    Attach one API package this ServicePackage provides.

    Contract:
    - This is the package-level provider rail for Node/service dependency resolution.
    - It declares which API packages this ServicePackage can fulfill through ServiceHost.
    - Provider truth must stay compatible with config-level `ServiceConfig -> ServiceConfigApi`
      fulfillment; it does not describe outgoing invocation.
    """

    # --- AWARE: LOGIC START attach_provided_api_package
    if service_package.id is None:
        raise RuntimeError("ServicePackage.attach_provided_api_package requires ServicePackage.id")

    service_package_api_package_id = stable_service_package_provided_api_package_id(
        service_package_id=service_package.id,
        api_package_id=api_package_id,
    )

    created = await ServicePackageProvidedApiPackage.build_via_service_package(
        service_package_id=service_package.id,
        api_package_id=api_package_id,
        service_protocol_package_id=service_protocol_package_id,
        service_protocol_plan_hash_sha256=service_protocol_plan_hash_sha256,
        api_package_object_instance_graph_commit_id=(api_package_object_instance_graph_commit_id),
        description=description,
    )
    if all(existing.id != service_package_api_package_id for existing in service_package.provided_api_packages):
        service_package.provided_api_packages.append(created)
    return created
    # --- AWARE: LOGIC END attach_provided_api_package


async def attach_object_config_graph_package(
    service_package: ServicePackage,
    object_config_graph_package_id: UUID,
    manifest_relative_path: str,
    role: str = "local_state",
    package_kind: str = "state",
    object_config_graph_package_object_instance_graph_commit_id: UUID | None = None,
    expected_hash_sha256: str | None = None,
    description: str | None = None,
) -> ServicePackageObjectConfigGraphPackage:
    """
    Attach one Service-owned ObjectConfigGraphPackage to this ServicePackage.

    Contract:
    - This is service ownership truth, not a service dependency.
    - The child package is declared by `aware.service.toml` and materialized through the
      canonical ObjectConfigGraphPackage rail.
    - ServiceHost and WorkspaceRevision consumers can use the optional OIG commit pin to replay
      exact service-local DB/schema truth without reopening local manifests.
    """

    # --- AWARE: LOGIC START attach_object_config_graph_package
    ocg_package = await ServicePackageObjectConfigGraphPackage.build_via_service_package(
        service_package_id=service_package.id,
        object_config_graph_package_id=object_config_graph_package_id,
        manifest_relative_path=manifest_relative_path,
        role=role,
        package_kind=package_kind,
        object_config_graph_package_object_instance_graph_commit_id=(
            object_config_graph_package_object_instance_graph_commit_id
        ),
        expected_hash_sha256=expected_hash_sha256,
        description=description,
    )
    if all(existing.id != ocg_package.id for existing in service_package.object_config_graph_packages):
        service_package.object_config_graph_packages.append(ocg_package)
    return ocg_package
    # --- AWARE: LOGIC END attach_object_config_graph_package


async def attach_ontology_package(
    service_package: ServicePackage,
    ontology_package_id: UUID,
    package_name: str,
    fqn_prefix: str,
    role: str = "replica",
    requirement_mode: str = "required",
    ontology_package_object_instance_graph_commit_id: UUID | None = None,
    expected_hash_sha256: str | None = None,
    description: str | None = None,
) -> ServicePackageOntologyPackage:
    """
    Attach one ontology package this ServicePackage requires as a replica.

    Contract:
    - This is package-level ontology replica requirement truth.
    - It declares which OntologyPackage must be available to ServiceHost as a
      read-only Service-owned ontology replica before required handler dispatch.
    - Required ontology truth must not imply this ServicePackage owns or mutates
      the ontology package. Ontology remains the write/DB authority.
    """

    # --- AWARE: LOGIC START attach_ontology_package
    if service_package.id is None:
        raise RuntimeError("ServicePackage.attach_ontology_package requires ServicePackage.id")

    created = await ServicePackageOntologyPackage.build_via_service_package(
        service_package_id=service_package.id,
        ontology_package_id=ontology_package_id,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        role=role,
        requirement_mode=requirement_mode,
        ontology_package_object_instance_graph_commit_id=(ontology_package_object_instance_graph_commit_id),
        expected_hash_sha256=expected_hash_sha256,
        description=description,
    )
    for index, existing in enumerate(service_package.ontology_packages):
        if existing.id == created.id or existing.ontology_package_id == ontology_package_id:
            service_package.ontology_packages[index] = created
            return created

    service_package.ontology_packages.append(created)
    return created
    # --- AWARE: LOGIC END attach_ontology_package


async def attach_implementation_package(
    service_package: ServicePackage,
    code_package_id: UUID,
    package_name: str,
    language: CodeLanguage,
    import_root: str,
    manifest_relative_path: str,
    package_root: str = ".",
    entrypoint: str | None = None,
    role: str = "service_bindings",
    include_paths: JsonArray = JsonArray(),
    exclude_paths: JsonArray = JsonArray(),
) -> ServicePackageImplementationPackage:
    """
    Attach one concrete implementation package owned by this ServicePackage.

    Contract:
    - The ServicePackage owns explicit language implementation packages as semantic package truth.
    - ServiceHost must resolve importable implementation code from this bridge, never from
      `fqn_prefix` guesses or workspace layout heuristics.
    - `code_package_id` points at the canonical CodePackage for the implementation package.
    - `package_root` and `manifest_relative_path` are workspace-revision relative contract payload.
    """

    # --- AWARE: LOGIC START attach_implementation_package
    if service_package.id is None:
        raise RuntimeError("ServicePackage.attach_implementation_package requires ServicePackage.id")

    normalized_package_name = (package_name or "").strip()
    if not normalized_package_name:
        raise RuntimeError("ServicePackage.attach_implementation_package requires non-empty package_name")
    normalized_import_root = (import_root or "").strip()
    if not normalized_import_root:
        raise RuntimeError("ServicePackage.attach_implementation_package requires non-empty import_root")
    normalized_manifest_relative_path = (manifest_relative_path or "").strip()
    if not normalized_manifest_relative_path:
        raise RuntimeError("ServicePackage.attach_implementation_package requires non-empty manifest_relative_path")
    normalized_package_root = (package_root or "").strip() or "."
    normalized_role = (role or "").strip() or "service_bindings"
    normalized_entrypoint = (entrypoint or "").strip() or None
    include_paths_payload = JsonArray(include_paths or [])
    exclude_paths_payload = JsonArray(exclude_paths or [])

    implementation_package_id = stable_service_package_implementation_package_id(
        service_package_id=service_package.id,
        code_package_id=code_package_id,
    )

    for existing in service_package.implementation_packages:
        if existing.id == implementation_package_id or existing.code_package_id == code_package_id:
            return await ServicePackageImplementationPackage.build_via_service_package(
                service_package_id=service_package.id,
                code_package_id=code_package_id,
                package_name=normalized_package_name,
                language=language,
                import_root=normalized_import_root,
                manifest_relative_path=normalized_manifest_relative_path,
                package_root=normalized_package_root,
                entrypoint=normalized_entrypoint,
                role=normalized_role,
                include_paths=include_paths_payload,
                exclude_paths=exclude_paths_payload,
            )

    created = await ServicePackageImplementationPackage.build_via_service_package(
        service_package_id=service_package.id,
        code_package_id=code_package_id,
        package_name=normalized_package_name,
        language=language,
        import_root=normalized_import_root,
        manifest_relative_path=normalized_manifest_relative_path,
        package_root=normalized_package_root,
        entrypoint=normalized_entrypoint,
        role=normalized_role,
        include_paths=include_paths_payload,
        exclude_paths=exclude_paths_payload,
    )
    service_package.implementation_packages.append(created)
    return created
    # --- AWARE: LOGIC END attach_implementation_package


async def attach_required_api_package(
    service_package: ServicePackage, api_package_id: UUID, description: str | None = None
) -> ServicePackageRequiredApiPackage:
    """
    Attach one API package this ServicePackage requires for outgoing invocation.

    Contract:
    - This is the package-level consumer rail for generated SDK/API clients.
    - It declares which API packages this ServicePackage may invoke through Node service routing.
    - Required API truth must not imply this ServicePackage hosts or fulfills the API.
    """

    # --- AWARE: LOGIC START attach_required_api_package
    if service_package.id is None:
        raise RuntimeError("ServicePackage.attach_required_api_package requires ServicePackage.id")

    service_package_api_package_id = stable_service_package_required_api_package_id(
        service_package_id=service_package.id,
        api_package_id=api_package_id,
    )

    for existing in service_package.required_api_packages:
        if existing.id == service_package_api_package_id or existing.api_package_id == api_package_id:
            return existing

    created = await ServicePackageRequiredApiPackage.build_via_service_package(
        service_package_id=service_package.id,
        api_package_id=api_package_id,
        description=description,
    )
    service_package.required_api_packages.append(created)
    return created
    # --- AWARE: LOGIC END attach_required_api_package
