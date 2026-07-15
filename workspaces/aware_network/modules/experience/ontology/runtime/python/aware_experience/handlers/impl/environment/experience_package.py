from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonArray

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Experience Ontology
from aware_experience_ontology.environment.experience_package import ExperiencePackage
from aware_experience_ontology.environment.experience_package_api_package import ExperiencePackageApiPackage
from aware_experience_ontology.environment.experience_package_attention_package import ExperiencePackageAttentionPackage
from aware_experience_ontology.environment.experience_package_dependency import ExperiencePackageDependency
from aware_experience_ontology.environment.experience_package_language_package import ExperiencePackageLanguagePackage
from aware_experience_ontology.environment.experience_package_sdk_package import ExperiencePackageSdkPackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Code Ontology
from aware_code_ontology.package.code_package import CodePackage

# Experience Ontology
from aware_experience.stable_ids import stable_experience_package_id
from aware_experience_ontology.environment.environment_experience import (
    EnvironmentExperience,
)

# Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build(
    name: str, environment_experience_id: UUID, source_code_package_id: UUID | None = None
) -> ExperiencePackage:
    """
    Create the canonical Experience-owned package root over an existing `EnvironmentExperience`.

    Contract:
    - Identity is keyed by Experience package `name`.
    - `ExperiencePackage` is the package/public root over an existing canonical
      `EnvironmentExperience`.
    - `environment_experience_id` must point at the canonical EnvironmentExperience stable id
      for this package root.
    - `source_code_package_id` is the explicit raw-source provenance link for this semantic
      leaf package.
    - Workspace will later mount `ExperiencePackage`, not raw `EnvironmentExperience`.
    """

    # --- AWARE: LOGIC START build
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("ExperiencePackage.build requires non-empty name")

    package_id = stable_experience_package_id(name=normalized_name)

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    resolved_environment_experience = (
        session.imap_get(EnvironmentExperience, environment_experience_id) if session is not None else None
    )
    resolved_source_code_package = (
        session.imap_get(CodePackage, source_code_package_id)
        if session is not None and source_code_package_id is not None
        else None
    )

    if session is not None:
        existing = session.imap_get(ExperiencePackage, package_id)
        if existing is not None:
            if (existing.name or "").strip() != normalized_name:
                raise RuntimeError(
                    "ExperiencePackage.build payload mismatch for existing package: "
                    f"experience_package_id={package_id}"
                )
            existing_environment_experience_id = existing.environment_experience_id
            if existing_environment_experience_id != environment_experience_id:
                raise RuntimeError(
                    "ExperiencePackage.build environment_experience_id mismatch for existing package: "
                    f"experience_package_id={package_id} "
                    f"existing={existing_environment_experience_id} provided={environment_experience_id}"
                )

            existing_source_code_package_id = existing.source_code_package_id
            if source_code_package_id is not None:
                if existing_source_code_package_id is None:
                    existing.source_code_package_id = source_code_package_id
                    existing.source_code_package = resolved_source_code_package
                elif existing_source_code_package_id != source_code_package_id:
                    raise RuntimeError(
                        "ExperiencePackage.build source_code_package_id mismatch for existing package: "
                        f"experience_package_id={package_id} "
                        f"existing={existing_source_code_package_id} provided={source_code_package_id}"
                    )
            return existing

    return ExperiencePackage.model_construct(
        id=package_id,
        name=normalized_name,
        environment_experience=resolved_environment_experience,
        environment_experience_id=environment_experience_id,
        source_code_package=resolved_source_code_package,
        source_code_package_id=source_code_package_id,
    )
    # --- AWARE: LOGIC END build


async def attach_attention_package(
    experience_package: ExperiencePackage, attention_package_id: UUID, description: str | None = None
) -> ExperiencePackageAttentionPackage:
    """
    Attach one Attention package dependency to this ExperiencePackage.

    Contract:
    - This is package-level dependency truth for Experience-authored layout/section bindings.
    - ProjectionExperienceSectionGraphBinding may target Attention layout sections only through
      committed package dependency truth, not through runtime guesses.
    - The dependency is relational truth; runtime mutation still goes through Attention services.
    """

    # --- AWARE: LOGIC START attach_attention_package
    experience_package_id = experience_package.id
    if experience_package_id is None:
        raise RuntimeError("ExperiencePackage.attach_attention_package requires id")

    created = await ExperiencePackageAttentionPackage.build_via_experience_package(
        experience_package_id=experience_package_id,
        attention_package_id=attention_package_id,
        description=description,
    )
    for existing in experience_package.attention_packages:
        if existing.id == created.id:
            return existing
    experience_package.attention_packages.append(created)
    return created
    # --- AWARE: LOGIC END attach_attention_package


async def attach_api_package(
    experience_package: ExperiencePackage, api_package_id: UUID, description: str | None = None
) -> ExperiencePackageApiPackage:
    """
    Attach one API package dependency to this ExperiencePackage.

    Contract:
    - Experience owns ProjectionExperienceView action capability truth.
    - API package dependencies declare which API packages those view actions may target.
    - Pane/interface packages must not become the product owner of API capability truth.
    """

    # --- AWARE: LOGIC START attach_api_package
    experience_package_id = experience_package.id
    if experience_package_id is None:
        raise RuntimeError("ExperiencePackage.attach_api_package requires id")

    created = await ExperiencePackageApiPackage.build_via_experience_package(
        experience_package_id=experience_package_id,
        api_package_id=api_package_id,
        description=description,
    )
    for existing in experience_package.api_packages:
        if existing.id == created.id:
            return existing
    experience_package.api_packages.append(created)
    return created
    # --- AWARE: LOGIC END attach_api_package


async def attach_experience_package_dependency(
    experience_package: ExperiencePackage,
    target_experience_package_id: UUID,
    target_package_name: str,
    target_experience_package_object_instance_graph_commit_id: UUID | None = None,
    target_version_number: int | None = None,
    expected_hash_sha256: str | None = None,
    description: str | None = None,
) -> ExperiencePackageDependency:
    """
    Attach one Experience package dependency to this ExperiencePackage.

    Contract:
    - This is package-level dependency truth for cross-Experience profile composition.
    - View/event transitions may reference source views or target bindings from another
      Experience package only when backed by this dependency closure.
    - `target_version_number` is selector/compatibility metadata.
    - `target_experience_package_object_instance_graph_commit_id`, when present, pins
      exact semantic package truth resolved through WorkspaceRevision/Hub evidence.
    """

    # --- AWARE: LOGIC START attach_experience_package_dependency
    experience_package_id = experience_package.id
    if experience_package_id is None:
        raise RuntimeError("ExperiencePackage.attach_experience_package_dependency requires id")

    created = await ExperiencePackageDependency.build_via_experience_package(
        experience_package_id=experience_package_id,
        target_experience_package_id=target_experience_package_id,
        target_package_name=target_package_name,
        target_experience_package_object_instance_graph_commit_id=(
            target_experience_package_object_instance_graph_commit_id
        ),
        target_version_number=target_version_number,
        expected_hash_sha256=expected_hash_sha256,
        description=description,
    )
    for existing in experience_package.experience_package_dependencies:
        if existing.id == created.id:
            return existing
    experience_package.experience_package_dependencies.append(created)
    return created
    # --- AWARE: LOGIC END attach_experience_package_dependency


async def attach_language_package(
    experience_package: ExperiencePackage,
    code_package_id: UUID,
    package_name: str,
    language: CodeLanguage,
    import_root: str,
    manifest_relative_path: str,
    package_root: str = ".",
    sources_root: str | None = None,
    role: str = "view_model_package",
    output_key: str = "experience.language_contract.generated_code_packages",
    include_paths: JsonArray = JsonArray(),
    exclude_paths: JsonArray = JsonArray(),
) -> ExperiencePackageLanguagePackage:
    """
    Attach one Experience-owned generated language package.

    Contract:
    - Experience packages own their generated view-model/runtime language package truth.
    - Identity is keyed by the attached generated CodePackage.
    - Consumers must not infer Experience language packages from local targets or filesystem
      layout; they must read this package relationship.
    - The CodePackage remains the code-content owner. This edge is semantic package
      ownership/provenance, not a parallel artifact rail.
    """

    # --- AWARE: LOGIC START attach_language_package
    experience_package_id = experience_package.id
    if experience_package_id is None:
        raise RuntimeError("ExperiencePackage.attach_language_package requires id")

    normalized_package_name = (package_name or "").strip()
    if not normalized_package_name:
        raise RuntimeError("ExperiencePackage.attach_language_package requires non-empty package_name")
    normalized_import_root = (import_root or "").strip()
    if not normalized_import_root:
        raise RuntimeError("ExperiencePackage.attach_language_package requires non-empty import_root")
    normalized_manifest_relative_path = (manifest_relative_path or "").strip()
    if not normalized_manifest_relative_path:
        raise RuntimeError("ExperiencePackage.attach_language_package requires non-empty manifest_relative_path")

    created = await ExperiencePackageLanguagePackage.build_via_experience_package(
        experience_package_id=experience_package_id,
        code_package_id=code_package_id,
        package_name=normalized_package_name,
        language=language,
        import_root=normalized_import_root,
        manifest_relative_path=normalized_manifest_relative_path,
        package_root=(package_root or "").strip() or ".",
        sources_root=(sources_root or "").strip() or None,
        role=(role or "").strip() or "view_model_package",
        output_key=((output_key or "").strip() or "experience.language_contract.generated_code_packages"),
        include_paths=JsonArray(include_paths or []),
        exclude_paths=JsonArray(exclude_paths or []),
    )
    for existing in experience_package.language_packages:
        if existing.id == created.id:
            return existing
    experience_package.language_packages.append(created)
    return created
    # --- AWARE: LOGIC END attach_language_package


async def attach_sdk_package(
    experience_package: ExperiencePackage, sdk_package_id: UUID, description: str | None = None
) -> ExperiencePackageSdkPackage:
    """
    Attach one SDK package dependency to this ExperiencePackage.

    Contract:
    - Experience owns ProjectionExperienceView action capability truth.
    - SDK package dependencies declare which SDK packages those view actions may target.
    - SDK invocation remains a boundary adapter, not pane-owned product semantics.
    """

    # --- AWARE: LOGIC START attach_sdk_package
    experience_package_id = experience_package.id
    if experience_package_id is None:
        raise RuntimeError("ExperiencePackage.attach_sdk_package requires id")

    created = await ExperiencePackageSdkPackage.build_via_experience_package(
        experience_package_id=experience_package_id,
        sdk_package_id=sdk_package_id,
        description=description,
    )
    for existing in experience_package.sdk_packages:
        if existing.id == created.id:
            return existing
    experience_package.sdk_packages.append(created)
    return created
    # --- AWARE: LOGIC END attach_sdk_package
