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

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Sdk Ontology
from aware_sdk_ontology.sdk.sdk_package import SdkPackage
from aware_sdk_ontology.sdk.sdk_package_api_package import SdkPackageApiPackage
from aware_sdk_ontology.sdk.sdk_package_dependency import SdkPackageDependency
from aware_sdk_ontology.sdk.sdk_package_implementation_package import SdkPackageImplementationPackage
from aware_sdk_ontology.sdk.sdk_package_object_config_graph_package import SdkPackageObjectConfigGraphPackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_sdk_ontology.stable_ids import stable_sdk_package_id

# --- AWARE: USER_IMPORTS END


async def build(
    name: str,
    sdk_config_id: UUID,
    sdk_config_object_instance_graph_commit_id: UUID | None = None,
    source_code_package_id: UUID | None = None,
    fqn_prefix: str | None = None,
    version_number: int = 1,
    title: str | None = None,
    description: str | None = None,
    aware_sdk_version: int = 1,
    manifest_relative_path: str | None = None,
    package_root: str = ".",
    sources_root: str = "sdks",
    include_paths: JsonArray = JsonArray(),
    exclude_paths: JsonArray = JsonArray(),
    force_fresh_scan: bool = True,
    compilation_mode: str = "raw_xor",
    dependencies: JsonArray = JsonArray(),
    targets: JsonObject = JsonObject(),
) -> SdkPackage:
    """
    Create the canonical SDK-owned package root over an existing `SdkConfig`.

    Contract:
    - Identity is keyed by SDK package `name`.
    - `SdkPackage` is the package/public root over an existing canonical `SdkConfig`.
    - `sdk_config_id` must point at the canonical SdkConfig stable id for this package root.
    - `sdk_config_object_instance_graph_commit_id` pins the historical ObjectInstanceGraphCommit
      for the semantic SdkConfig root so package consumers can replay exact SDK truth without
      resolving branch head or reopening authoring TOML.
    - `source_code_package_id` is explicit raw-source provenance for this semantic leaf package.
    - `SdkPackageApiPackage` declares which API packages are available to generated/runtime SDKs.
    - `SdkPackageImplementationPackage` declares concrete Python/Dart package roots owned by
      the SDK package for public install/runtime consumption.
    - `SdkPackageObjectConfigGraphPackage` declares SDK-owned OCG/state packages that travel
      with this SDK package rather than acting as external dependencies.
    - `SdkPackageDependency` declares package-level SDK dependencies; operation composition may only
      target SDK operations from this declared dependency closure.
    """

    # --- AWARE: LOGIC START build
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("SdkPackage.build requires non-empty name")
    return SdkPackage(
        id=stable_sdk_package_id(name=normalized_name),
        name=normalized_name,
        sdk_config_id=sdk_config_id,
        sdk_config_object_instance_graph_commit_id=sdk_config_object_instance_graph_commit_id,
        source_code_package_id=source_code_package_id,
        fqn_prefix=(fqn_prefix or "").strip() or None,
        version_number=version_number,
        title=(title or "").strip() or None,
        description=(description or "").strip() or None,
        aware_sdk_version=aware_sdk_version,
        manifest_relative_path=(manifest_relative_path or "").strip() or None,
        package_root=(package_root or "").strip() or ".",
        sources_root=(sources_root or "").strip() or "sdks",
        include_paths=JsonArray(include_paths or []),
        exclude_paths=JsonArray(exclude_paths or []),
        force_fresh_scan=force_fresh_scan,
        compilation_mode=(compilation_mode or "").strip() or "raw_xor",
        dependencies=JsonArray(dependencies or []),
        targets=JsonObject(targets or {}),
    )
    # --- AWARE: LOGIC END build


async def sync_manifest_truth(
    sdk_package: SdkPackage,
    sdk_config_object_instance_graph_commit_id: UUID | None = None,
    source_code_package_id: UUID | None = None,
    fqn_prefix: str | None = None,
    version_number: int = 1,
    title: str | None = None,
    description: str | None = None,
    aware_sdk_version: int = 1,
    manifest_relative_path: str | None = None,
    package_root: str = ".",
    sources_root: str = "sdks",
    include_paths: JsonArray = JsonArray(),
    exclude_paths: JsonArray = JsonArray(),
    force_fresh_scan: bool = True,
    compilation_mode: str = "raw_xor",
    dependencies: JsonArray = JsonArray(),
    targets: JsonObject = JsonObject(),
) -> SdkPackage:
    """
    Sync mutable manifest/build/dependency/target truth onto an existing SdkPackage root.
    """

    # --- AWARE: LOGIC START sync_manifest_truth
    sdk_package.sdk_config_object_instance_graph_commit_id = sdk_config_object_instance_graph_commit_id
    sdk_package.source_code_package_id = source_code_package_id
    sdk_package.fqn_prefix = (fqn_prefix or "").strip() or None
    sdk_package.version_number = version_number
    sdk_package.title = (title or "").strip() or None
    sdk_package.description = (description or "").strip() or None
    sdk_package.aware_sdk_version = aware_sdk_version
    sdk_package.manifest_relative_path = (manifest_relative_path or "").strip() or None
    sdk_package.package_root = (package_root or "").strip() or "."
    sdk_package.sources_root = (sources_root or "").strip() or "sdks"
    sdk_package.include_paths = JsonArray(include_paths or [])
    sdk_package.exclude_paths = JsonArray(exclude_paths or [])
    sdk_package.force_fresh_scan = force_fresh_scan
    sdk_package.compilation_mode = (compilation_mode or "").strip() or "raw_xor"
    sdk_package.dependencies = JsonArray(dependencies or [])
    sdk_package.targets = JsonObject(targets or {})
    return sdk_package
    # --- AWARE: LOGIC END sync_manifest_truth


async def attach_api_package(
    sdk_package: SdkPackage, api_package_id: UUID, description: str | None = None
) -> SdkPackageApiPackage:
    """
    Attach one API package to this SdkPackage.

    Contract:
    - This is the package/import rail for authored/generated SDK source.
    - Operation-level endpoint bindings remain separate `SdkOperation -> ApiCapabilityEndpoint` truth.
    """

    # --- AWARE: LOGIC START attach_api_package
    api_package = await SdkPackageApiPackage.build_via_sdk_package(
        sdk_package_id=sdk_package.id,
        api_package_id=api_package_id,
        description=description,
    )
    if all(existing.id != api_package.id for existing in sdk_package.api_packages):
        sdk_package.api_packages.append(api_package)
    return api_package
    # --- AWARE: LOGIC END attach_api_package


async def attach_implementation_package(
    sdk_package: SdkPackage,
    code_package_id: UUID,
    package_name: str,
    language: CodeLanguage,
    import_root: str,
    manifest_relative_path: str,
    package_root: str = ".",
    entrypoint: str | None = None,
    role: str = "public_package",
    include_paths: JsonArray = JsonArray(),
    exclude_paths: JsonArray = JsonArray(),
) -> SdkPackageImplementationPackage:
    """
    Attach one concrete language implementation package owned by this SdkPackage.

    Contract:
    - The SDK package owns explicit language implementation packages as semantic package truth.
    - WorkspaceRevision checkout and SDK installers must resolve public package roots from this
      bridge, never from target JSON or workspace layout heuristics.
    - `code_package_id` points at the canonical CodePackage for the implementation package.
    - `package_root` and `manifest_relative_path` are workspace-revision relative contract payload.
    """

    # --- AWARE: LOGIC START attach_implementation_package
    implementation_package = await SdkPackageImplementationPackage.build_via_sdk_package(
        sdk_package_id=sdk_package.id,
        code_package_id=code_package_id,
        package_name=package_name,
        language=language,
        import_root=import_root,
        manifest_relative_path=manifest_relative_path,
        package_root=package_root,
        entrypoint=entrypoint,
        role=role,
        include_paths=JsonArray(include_paths or []),
        exclude_paths=JsonArray(exclude_paths or []),
    )
    if all(existing.id != implementation_package.id for existing in sdk_package.implementation_packages):
        sdk_package.implementation_packages.append(implementation_package)
    return implementation_package
    # --- AWARE: LOGIC END attach_implementation_package


async def attach_object_config_graph_package(
    sdk_package: SdkPackage,
    object_config_graph_package_id: UUID,
    manifest_relative_path: str,
    role: str = "local_state",
    package_kind: str = "state",
    object_config_graph_package_object_instance_graph_commit_id: UUID | None = None,
    expected_hash_sha256: str | None = None,
    description: str | None = None,
) -> SdkPackageObjectConfigGraphPackage:
    """
    Attach one SDK-owned ObjectConfigGraphPackage to this SdkPackage.

    Contract:
    - This is SDK ownership truth, not SDK dependency truth.
    - The child package is declared by `aware.sdk.toml` and materialized through the
      canonical ObjectConfigGraphPackage rail.
    - WorkspaceRevision/Hub consumers can use the optional OIG commit pin to replay
      exact SDK-owned DB/schema truth without reopening local manifests.
    """

    # --- AWARE: LOGIC START attach_object_config_graph_package
    ocg_package = await SdkPackageObjectConfigGraphPackage.build_via_sdk_package(
        sdk_package_id=sdk_package.id,
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
    if all(existing.id != ocg_package.id for existing in sdk_package.object_config_graph_packages):
        sdk_package.object_config_graph_packages.append(ocg_package)
    return ocg_package
    # --- AWARE: LOGIC END attach_object_config_graph_package


async def attach_sdk_package_dependency(
    sdk_package: SdkPackage,
    target_sdk_package_id: UUID,
    target_package_name: str,
    target_sdk_package_object_instance_graph_commit_id: UUID | None = None,
    target_version_number: int | None = None,
    expected_hash_sha256: str | None = None,
    description: str | None = None,
) -> SdkPackageDependency:
    """
    Attach one SDK package dependency to this SdkPackage.

    Contract:
    - This is package dependency truth, not operation invocation truth.
    - `target_version_number` is selector/compatibility metadata.
    - `target_sdk_package_object_instance_graph_commit_id` is the exact reproducibility authority
      when the dependency is locked or resolved through WorkspaceRevision/Hub evidence.
    - SDK operation composition must only target operations from the declared dependency closure.
    """

    # --- AWARE: LOGIC START attach_sdk_package_dependency
    dependency = await SdkPackageDependency.build_via_sdk_package(
        sdk_package_id=sdk_package.id,
        target_sdk_package_id=target_sdk_package_id,
        target_package_name=target_package_name,
        target_sdk_package_object_instance_graph_commit_id=(target_sdk_package_object_instance_graph_commit_id),
        target_version_number=target_version_number,
        expected_hash_sha256=expected_hash_sha256,
        description=description,
    )
    if all(existing.id != dependency.id for existing in sdk_package.sdk_package_dependencies):
        sdk_package.sdk_package_dependencies.append(dependency)
    return dependency
    # --- AWARE: LOGIC END attach_sdk_package_dependency
