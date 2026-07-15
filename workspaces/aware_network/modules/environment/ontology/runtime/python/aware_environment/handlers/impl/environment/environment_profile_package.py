from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Environment Ontology
from aware_environment_ontology.environment.environment_profile_package import EnvironmentProfilePackage
from aware_environment_ontology.environment.environment_profile_package_dependency import (
    EnvironmentProfilePackageDependency,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code_ontology.package.code_package import CodePackage
from aware_meta.runtime.handler_context import current_handler_session
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_environment_ontology.environment.environment_profile_config import (
    EnvironmentProfileConfig,
)
from aware_environment_ontology.stable_ids import (
    stable_environment_profile_package_id,
)

# --- AWARE: USER_IMPORTS END


async def build(
    name: str,
    environment_profile_config_id: UUID,
    environment_profile_config_object_instance_graph_commit_id: UUID | None = None,
    environment_config_package_id: UUID | None = None,
    environment_config_package_object_instance_graph_commit_id: UUID | None = None,
    source_code_package_id: UUID | None = None,
    profile_key: str | None = None,
    environment_handle: str | None = None,
    version_number: int = 1,
    title: str | None = None,
    description: str | None = None,
    manifest_relative_path: str | None = None,
    package_root: str = ".",
    sources_root: str = "profiles",
) -> EnvironmentProfilePackage:
    """
    Create the canonical Environment package root over EnvironmentProfileConfig.

    Contract:
    - Identity is keyed by package `name`.
    - `environment_profile_config_id` points to reusable OS profile config
      truth, never a concrete EnvironmentProfile application.
    - OIG commit pins let WorkspaceRevision/Environment consumers replay
      exact profile config and dependency truth without reopening source
      profile manifests.
    - `environment_config_package_id` is optional package-level Environment
      composition provenance; EnvironmentConfig is Environment-owned.
    """

    # --- AWARE: LOGIC START build
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("EnvironmentProfilePackage.build requires non-empty name")

    normalized_profile_key = (profile_key or "").strip() or None
    normalized_environment_handle = (environment_handle or "").strip() or None
    normalized_title = (title or "").strip() or None
    normalized_description = (description or "").strip() or None
    normalized_manifest_relative_path = (manifest_relative_path or "").strip() or None
    normalized_package_root = (package_root or "").strip() or "."
    normalized_sources_root = (sources_root or "").strip() or "profiles"
    package_id = stable_environment_profile_package_id(name=normalized_name)

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    resolved_profile_config = (
        session.imap_get(EnvironmentProfileConfig, environment_profile_config_id) if session is not None else None
    )
    resolved_profile_config_oig_commit = (
        session.imap_get(
            ObjectInstanceGraphCommit,
            environment_profile_config_object_instance_graph_commit_id,
        )
        if session is not None and environment_profile_config_object_instance_graph_commit_id is not None
        else None
    )
    resolved_environment_config_package = None
    if session is not None and environment_config_package_id is not None:
        from aware_environment_ontology.environment.environment_config_package import (
            EnvironmentConfigPackage,
        )

        resolved_environment_config_package = session.imap_get(
            EnvironmentConfigPackage,
            environment_config_package_id,
        )
    resolved_environment_config_package_oig_commit = (
        session.imap_get(
            ObjectInstanceGraphCommit,
            environment_config_package_object_instance_graph_commit_id,
        )
        if session is not None and environment_config_package_object_instance_graph_commit_id is not None
        else None
    )
    resolved_source_code_package = (
        session.imap_get(CodePackage, source_code_package_id)
        if session is not None and source_code_package_id is not None
        else None
    )

    if session is not None:
        existing = session.imap_get(EnvironmentProfilePackage, package_id)
        if existing is not None:
            if (existing.name or "").strip() != normalized_name:
                raise RuntimeError(
                    "EnvironmentProfilePackage.build payload mismatch for existing package: "
                    f"environment_profile_package_id={package_id}"
                )
            if existing.environment_profile_config_id != environment_profile_config_id:
                raise RuntimeError(
                    "EnvironmentProfilePackage.build environment_profile_config_id mismatch "
                    "for existing package: "
                    f"environment_profile_package_id={package_id} "
                    f"existing={existing.environment_profile_config_id} "
                    f"provided={environment_profile_config_id}"
                )

            if environment_profile_config_object_instance_graph_commit_id is not None:
                existing_commit_id = existing.environment_profile_config_object_instance_graph_commit_id
                if existing_commit_id is None:
                    existing.environment_profile_config_object_instance_graph_commit_id = (
                        environment_profile_config_object_instance_graph_commit_id
                    )
                    existing.environment_profile_config_object_instance_graph_commit = (
                        resolved_profile_config_oig_commit
                    )
                elif existing_commit_id != environment_profile_config_object_instance_graph_commit_id:
                    raise RuntimeError(
                        "EnvironmentProfilePackage.build "
                        "environment_profile_config_object_instance_graph_commit_id mismatch "
                        "for existing package: "
                        f"environment_profile_package_id={package_id} "
                        f"existing={existing_commit_id} "
                        f"provided={environment_profile_config_object_instance_graph_commit_id}"
                    )

            if environment_config_package_id is not None:
                existing_environment_package_id = existing.environment_config_package_id
                if existing_environment_package_id is None:
                    existing.environment_config_package_id = environment_config_package_id
                    existing.environment_config_package = resolved_environment_config_package
                elif existing_environment_package_id != environment_config_package_id:
                    raise RuntimeError(
                        "EnvironmentProfilePackage.build environment_config_package_id mismatch "
                        "for existing package: "
                        f"environment_profile_package_id={package_id} "
                        f"existing={existing_environment_package_id} "
                        f"provided={environment_config_package_id}"
                    )
            if environment_config_package_object_instance_graph_commit_id is not None:
                existing_environment_commit_id = existing.environment_config_package_object_instance_graph_commit_id
                if existing_environment_commit_id is None:
                    existing.environment_config_package_object_instance_graph_commit_id = (
                        environment_config_package_object_instance_graph_commit_id
                    )
                    existing.environment_config_package_object_instance_graph_commit = (
                        resolved_environment_config_package_oig_commit
                    )
                elif existing_environment_commit_id != environment_config_package_object_instance_graph_commit_id:
                    raise RuntimeError(
                        "EnvironmentProfilePackage.build "
                        "environment_config_package_object_instance_graph_commit_id mismatch "
                        "for existing package: "
                        f"environment_profile_package_id={package_id} "
                        f"existing={existing_environment_commit_id} "
                        f"provided={environment_config_package_object_instance_graph_commit_id}"
                    )
            if source_code_package_id is not None:
                existing_source_code_package_id = existing.source_code_package_id
                if existing_source_code_package_id is None:
                    existing.source_code_package_id = source_code_package_id
                    existing.source_code_package = resolved_source_code_package
                elif existing_source_code_package_id != source_code_package_id:
                    raise RuntimeError(
                        "EnvironmentProfilePackage.build source_code_package_id mismatch "
                        "for existing package: "
                        f"environment_profile_package_id={package_id} "
                        f"existing={existing_source_code_package_id} "
                        f"provided={source_code_package_id}"
                    )
            existing.profile_key = normalized_profile_key
            existing.environment_handle = normalized_environment_handle
            existing.version_number = version_number
            existing.title = normalized_title
            existing.description = normalized_description
            existing.manifest_relative_path = normalized_manifest_relative_path
            existing.package_root = normalized_package_root
            existing.sources_root = normalized_sources_root
            return existing

    return EnvironmentProfilePackage.model_construct(
        id=package_id,
        source_code_package=resolved_source_code_package,
        source_code_package_id=source_code_package_id,
        environment_config_package=resolved_environment_config_package,
        environment_config_package_id=environment_config_package_id,
        environment_config_package_object_instance_graph_commit=(resolved_environment_config_package_oig_commit),
        environment_config_package_object_instance_graph_commit_id=(
            environment_config_package_object_instance_graph_commit_id
        ),
        environment_profile_config=resolved_profile_config,
        environment_profile_config_id=environment_profile_config_id,
        environment_profile_config_object_instance_graph_commit=(resolved_profile_config_oig_commit),
        environment_profile_config_object_instance_graph_commit_id=(
            environment_profile_config_object_instance_graph_commit_id
        ),
        dependencies=[],
        name=normalized_name,
        profile_key=normalized_profile_key,
        environment_handle=normalized_environment_handle,
        version_number=version_number,
        title=normalized_title,
        description=normalized_description,
        manifest_relative_path=normalized_manifest_relative_path,
        package_root=normalized_package_root,
        sources_root=normalized_sources_root,
    )
    # --- AWARE: LOGIC END build


async def attach_dependency(
    environment_profile_package: EnvironmentProfilePackage,
    target_environment_profile_package_id: UUID,
    target_package_name: str,
    target_environment_profile_package_object_instance_graph_commit_id: UUID | None = None,
    target_version_number: int | None = None,
    expected_hash_sha256: str | None = None,
    description: str | None = None,
) -> EnvironmentProfilePackageDependency:
    """
    Attach one EnvironmentProfilePackage dependency.

    Contract:
    - Parent `EnvironmentProfilePackage` scope is injected by propagation.
    - Dependencies are package-level profile dependencies, not applied
      EnvironmentProfile session links.
    - Optional OIG commit pin is exact replay truth for WorkspaceRevision
      and Hub consumers.
    """

    # --- AWARE: LOGIC START attach_dependency
    if environment_profile_package.id is None:
        raise RuntimeError("EnvironmentProfilePackage.attach_dependency requires EnvironmentProfilePackage.id")

    created = await EnvironmentProfilePackageDependency.build_via_environment_profile_package(
        environment_profile_package_id=environment_profile_package.id,
        target_environment_profile_package_id=target_environment_profile_package_id,
        target_package_name=target_package_name,
        target_environment_profile_package_object_instance_graph_commit_id=(
            target_environment_profile_package_object_instance_graph_commit_id
        ),
        target_version_number=target_version_number,
        expected_hash_sha256=expected_hash_sha256,
        description=description,
    )
    for existing in environment_profile_package.dependencies:
        if existing.id == created.id:
            return existing
    environment_profile_package.dependencies.append(created)
    return created
    # --- AWARE: LOGIC END attach_dependency
