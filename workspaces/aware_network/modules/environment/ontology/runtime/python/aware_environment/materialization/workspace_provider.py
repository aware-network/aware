from __future__ import annotations

from uuid import UUID

from aware_code.semantic_materialization import (
    SemanticPackageMaterializationBundle,
    SemanticPackageMaterializationRequest,
    SemanticPackageMaterializationResult,
)
from aware_environment.manifest.loader import load_aware_environment_profile_toml_spec
from aware_environment.materialization.environment_workspace_provider import (
    materialize as materialize_environment_config_package,
)
from aware_environment_ontology.stable_ids import (
    stable_environment_profile_package_id,
)


_ENVIRONMENT_TOML_NAME = "aware.environment.toml"
_ENVIRONMENT_PROFILE_TOML_NAME = "aware.environment.profile.toml"
_PROFILE_FULL_REBUILD_FALLBACK_REASON = (
    "Environment provider has not implemented EnvironmentProfilePackage "
    "delta materialization yet; registered the package root from the profile "
    "manifest."
)


async def materialize(
    request: SemanticPackageMaterializationRequest,
) -> SemanticPackageMaterializationResult:
    manifest_name = request.manifest_path.name
    if manifest_name == _ENVIRONMENT_TOML_NAME:
        return await materialize_environment_config_package(request)
    if manifest_name == _ENVIRONMENT_PROFILE_TOML_NAME:
        return await _materialize_environment_profile_package(request)
    raise RuntimeError(
        "Environment materialization provider received unsupported manifest "
        f"{request.manifest_path.as_posix()!r}; expected {_ENVIRONMENT_TOML_NAME!r} "
        f"or {_ENVIRONMENT_PROFILE_TOML_NAME!r}."
    )


async def _materialize_environment_profile_package(
    request: SemanticPackageMaterializationRequest,
) -> SemanticPackageMaterializationResult:
    spec = load_aware_environment_profile_toml_spec(toml_path=request.manifest_path)
    profile = spec.environment_profile
    package_id = stable_environment_profile_package_id(name=profile.package_name)
    source_code_package_id = _uuid_or_none(
        request.context.get("source_code_package_id")
    )
    package_key = str(
        request.context.get("semantic_package_name") or profile.package_name
    ).strip()

    return SemanticPackageMaterializationResult(
        details={
            "environment_profile_toml_path": request.manifest_path.as_posix(),
            "environment_profile_package_name": profile.package_name,
            "environment_profile_package_id": str(package_id),
            "environment_handle": profile.environment_handle,
            "profile_key": profile.profile_key,
            "version_number": profile.version_number,
            "source_code_package_id": (
                str(source_code_package_id)
                if source_code_package_id is not None
                else None
            ),
            "dependency_package_names": [
                dependency.package_name for dependency in spec.dependencies
            ],
        },
        bundle_packages=(
            SemanticPackageMaterializationBundle(
                package_key=package_key or profile.package_name,
                manifest_toml_path=request.manifest_path,
                semantic_package_id=package_id,
                semantic_root_id=package_id,
                semantic_branch_id=package_id,
                semantic_root_kind="environment_profile_package",
                semantic_projection_name="EnvironmentProfilePackage",
                source_code_package_id=source_code_package_id,
                profiles=(
                    {
                        "package_name": profile.package_name,
                        "profile_key": profile.profile_key,
                        "environment_handle": profile.environment_handle,
                        "version_number": profile.version_number,
                    },
                ),
            ),
        ),
        mode="full_rebuild",
        affected_semantic_keys=(package_key or profile.package_name,),
        applied_semantic_keys=(package_key or profile.package_name,),
        skipped_semantic_keys=(),
        stale_semantic_keys=(),
        fallback_reason=_PROFILE_FULL_REBUILD_FALLBACK_REASON,
    )


def _uuid_or_none(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str) and value.strip():
        return UUID(value.strip())
    return None


__all__ = ["materialize"]
