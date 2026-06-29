from __future__ import annotations

from pathlib import Path
from typing import cast
from uuid import UUID

from aware_code.semantic_materialization import (
    SemanticPackageMaterializationBundle,
    SemanticPackageMaterializationEmittedPackageOutput,
    SemanticPackageMaterializationRequest,
    SemanticPackageMaterializationResult,
)
from aware_meta.runtime import MetaGraphRuntimeIndex
from ..semantic_contract import (
    SDK_OWNED_OCG_PACKAGE_OUTPUT_KEY,
    SDK_OWNED_OCG_PACKAGE_PRODUCER_KEY,
    SDK_OWNED_OCG_PACKAGE_RUNTIME_CONTRACT_VERSION,
    SDK_OWNED_OCG_PACKAGE_TARGET_INPUT_KEY,
    SDK_PROVIDER_PACKAGE_ROLE,
)
from .service import (
    SdkPackageMaterializationResult,
    materialize_sdk_package_from_manifest,
)

_FULL_REBUILD_FALLBACK_REASON = (
    "SDK provider has not implemented delta materialization yet; "
    "replayed the full SDK package manifest."
)


async def materialize(
    request: SemanticPackageMaterializationRequest,
) -> SemanticPackageMaterializationResult:
    result = await materialize_sdk_package_from_manifest(
        index=cast(MetaGraphRuntimeIndex, request.index),
        actor_id=request.actor_id,
        branch_id=request.branch_id,
        workspace_root=request.workspace_root,
        sdk_toml_path=request.manifest_path,
    )
    semantic_keys = _semantic_keys_from_request(request)
    return SemanticPackageMaterializationResult(
        details={
            "sdk_toml_path": result.sdk_toml_path.as_posix(),
            "sdk_config_name": result.sdk_config.name,
            "sdk_config_id": str(result.sdk_config.id),
            "sdk_package_name": result.sdk_package.name,
            "sdk_package_id": str(result.sdk_package.id),
            "semantic_branch_id": str(request.branch_id),
            "source_code_package_id": (
                str(result.source_code_package_id)
                if result.source_code_package_id is not None
                else None
            ),
            "sdk_source_path": result.sdk_source_path,
            "source_files": list(result.source_files),
            "sdk_phase_timings_s": dict(sorted(result.phase_timings_s.items())),
            "sdk_config_commit_id": (
                str(result.sdk_config_commit_id)
                if result.sdk_config_commit_id is not None
                else None
            ),
            "sdk_config_object_instance_graph_commit_id": (
                str(result.sdk_config_object_instance_graph_commit_id)
                if result.sdk_config_object_instance_graph_commit_id is not None
                else None
            ),
            "sdk_package_commit_id": (
                str(result.package_commit_id)
                if result.package_commit_id is not None
                else None
            ),
            "sdk_package_head_commit_id": (
                str(result.package_head_commit_id)
                if result.package_head_commit_id is not None
                else None
            ),
            "api_package_ids": [
                str(api_package_id) for api_package_id in result.api_package_ids
            ],
            "implementation_code_package_ids": [
                str(item) for item in result.implementation_code_package_ids
            ],
            "implementation_code_packages": [
                {
                    key: str(value) if _is_uuid(value) else value
                    for key, value in item.items()
                }
                for item in result.implementation_code_package_refs
            ],
            "object_config_graph_packages": [
                {
                    "manifest_path": package.manifest_path.as_posix(),
                    "manifest_relative_path": package.manifest_relative_path,
                    "role": package.role,
                    "package_name": package.package_name,
                    "package_fqn_prefix": package.package_fqn_prefix,
                    "package_kind": package.package_kind,
                    "code_package_surface": "structure",
                    "object_config_graph_package_id": str(
                        package.object_config_graph_package_id
                    ),
                    "object_config_graph_id": str(package.object_config_graph_id),
                    "package_branch_id": (
                        str(package.package_branch_id)
                        if package.package_branch_id is not None
                        else None
                    ),
                    "source_code_package_id": (
                        str(package.source_code_package_id)
                        if package.source_code_package_id is not None
                        else None
                    ),
                    "object_config_graph_package_head_commit_id": (
                        str(package.object_config_graph_package_head_commit_id)
                        if package.object_config_graph_package_head_commit_id
                        is not None
                        else None
                    ),
                    "object_config_graph_package_object_instance_graph_commit_id": (
                        str(
                            package.object_config_graph_package_object_instance_graph_commit_id
                        )
                        if package.object_config_graph_package_object_instance_graph_commit_id
                        is not None
                        else None
                    ),
                    "object_config_graph_object_instance_graph_commit_id": (
                        str(package.object_config_graph_object_instance_graph_commit_id)
                        if package.object_config_graph_object_instance_graph_commit_id
                        is not None
                        else None
                    ),
                    **_language_materialization_targets_details(package),
                }
                for package in getattr(result, "object_config_graph_packages", ())
            ],
            "emitted_owned_object_config_graph_package_count": len(
                getattr(result, "object_config_graph_packages", ())
            ),
            "sdk_package_dependency_ids": [
                str(dependency_id)
                for dependency_id in result.sdk_package_dependency_ids
            ],
        },
        bundle_packages=(
            SemanticPackageMaterializationBundle(
                package_key=result.sdk_package.name,
                manifest_toml_path=result.sdk_toml_path,
                semantic_package_id=result.sdk_package.id,
                semantic_root_id=result.sdk_config.id,
                semantic_branch_id=request.branch_id,
                semantic_head_commit_id=result.package_head_commit_id,
                semantic_object_instance_graph_commit_id=(
                    result.package_head_commit_id
                ),
                semantic_root_object_instance_graph_commit_id=(
                    result.sdk_config_object_instance_graph_commit_id
                ),
                semantic_root_kind="sdk_config",
                source_code_package_id=result.source_code_package_id,
                runtime_code_package_refs=_runtime_code_package_refs(
                    result.implementation_code_package_refs
                ),
                implementation_code_packages=result.implementation_code_package_refs,
            ),
        ),
        mode="full_rebuild",
        affected_semantic_keys=semantic_keys,
        applied_semantic_keys=semantic_keys,
        emitted_package_outputs=_owned_object_config_graph_package_outputs(
            result=result
        ),
        fallback_reason=_FULL_REBUILD_FALLBACK_REASON,
        commit_id=result.package_commit_id,
        head_commit_id=result.package_head_commit_id,
    )


def _semantic_keys_from_request(
    request: SemanticPackageMaterializationRequest,
) -> tuple[str, ...]:
    raw_keys = cast(object, request.change_preview.get("affected_semantic_keys"))
    if not isinstance(raw_keys, (list, tuple, set)):
        return ()
    iterable_keys = cast("list[object] | tuple[object, ...] | set[object]", raw_keys)
    semantic_keys: set[str] = set()
    for key in iterable_keys:
        clean_key = str(key).strip()
        if clean_key:
            semantic_keys.add(clean_key)
    return tuple(sorted(semantic_keys))


def _owned_object_config_graph_package_outputs(
    *,
    result: SdkPackageMaterializationResult,
) -> tuple[SemanticPackageMaterializationEmittedPackageOutput, ...]:
    source_manifest_path = _relative_or_posix(
        path=result.sdk_toml_path,
        root=result.workspace_root,
    )
    outputs: list[SemanticPackageMaterializationEmittedPackageOutput] = []
    for package in getattr(result, "object_config_graph_packages", ()):
        package_root = _package_root_from_manifest_relative_path(
            package.manifest_relative_path
        )
        payload: dict[str, object] = {
            "aware_toml_path": package.manifest_path.as_posix(),
            "fqn_prefix": package.package_fqn_prefix,
            "manifest_kind": "aware_toml",
            "manifest_relative_path": package.manifest_relative_path,
            "package_kind": package.package_kind,
            "code_package_surface": "structure",
            "package_name": package.package_name,
            "package_root": package_root,
            "role": package.role,
        }
        language_targets = _language_materialization_targets(package)
        if language_targets:
            payload["language_materialization_targets"] = [
                dict(target) for target in language_targets
            ]
        if (
            package.object_config_graph_package_object_instance_graph_commit_id
            is not None
        ):
            payload["object_instance_graph_commit_id"] = str(
                package.object_config_graph_package_object_instance_graph_commit_id
            )
        outputs.append(
            SemanticPackageMaterializationEmittedPackageOutput(
                producer_provider_key="aware_sdk",
                producer_semantic_owner=SDK_PROVIDER_PACKAGE_ROLE,
                producer_key=SDK_OWNED_OCG_PACKAGE_PRODUCER_KEY,
                output_key=SDK_OWNED_OCG_PACKAGE_OUTPUT_KEY,
                target_provider_key="aware_meta",
                target_semantic_owner="aware_meta.object_config_graph",
                target_input_key=SDK_OWNED_OCG_PACKAGE_TARGET_INPUT_KEY,
                target_package_family="meta",
                target_semantic_kind="object_config_graph_package",
                package_key=package.package_name,
                input_artifact_family="aware_toml_manifest",
                input_artifact_path=package.manifest_path,
                input_artifact_payload=payload,
                runtime_contract_version=(
                    SDK_OWNED_OCG_PACKAGE_RUNTIME_CONTRACT_VERSION
                ),
                source_package_key=result.sdk_package.name,
                source_manifest_path=source_manifest_path,
                provider_payload={
                    "schema_version": 1,
                    "source": "sdk.object_config_graph_packages",
                    "role": package.role,
                },
            )
        )
    return tuple(outputs)


def _language_materialization_targets(package: object) -> tuple[dict[str, object], ...]:
    raw_targets = getattr(package, "language_materialization_targets", ()) or ()
    return tuple(dict(target) for target in raw_targets)


def _language_materialization_targets_details(
    package: object,
) -> dict[str, object]:
    targets = _language_materialization_targets(package)
    if not targets:
        return {}
    return {"language_materialization_targets": [dict(target) for target in targets]}


def _runtime_code_package_refs(
    implementation_code_package_refs: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    refs: list[dict[str, object]] = []
    for implementation_ref in implementation_code_package_refs:
        source_code_package_id = implementation_ref.get("source_code_package_id")
        if source_code_package_id is None:
            source_code_package_id = implementation_ref.get("code_package_id")
        if source_code_package_id is None:
            continue
        refs.append(
            {
                "role": "sdk_implementation_package",
                "source_code_package_id": source_code_package_id,
                "source_object_instance_graph_commit_id": (
                    implementation_ref.get("object_instance_graph_commit_id")
                ),
                "package_name": implementation_ref.get("package_name"),
                "manifest_relative_path": implementation_ref.get(
                    "manifest_relative_path"
                ),
                "package_root": implementation_ref.get("package_root"),
                "sources_root": implementation_ref.get("sources_root"),
                "language": implementation_ref.get("language"),
            }
        )
    return tuple(refs)


def _package_root_from_manifest_relative_path(manifest_relative_path: str) -> str:
    package_root = Path(manifest_relative_path).parent.as_posix()
    return "." if package_root == "." else package_root


def _relative_or_posix(*, path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _is_uuid(value: object) -> bool:
    return isinstance(value, UUID)


__all__ = ["materialize"]
