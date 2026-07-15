from __future__ import annotations

from typing import cast
from uuid import UUID

from aware_code.semantic_materialization import (
    SemanticPackageMaterializationBundle,
    SemanticPackageMaterializationRequest,
    SemanticPackageMaterializationResult,
)
from aware_skill.materialization.service import materialize_skill_package_from_manifest


async def materialize(
    request: SemanticPackageMaterializationRequest,
) -> SemanticPackageMaterializationResult:
    result = await materialize_skill_package_from_manifest(
        runtime=request.runtime,
        index=request.index,
        actor_id=request.actor_id,
        environment_id=request.environment_id,
        process_id=request.process_id,
        thread_id=request.thread_id,
        branch_id=request.branch_id,
        workspace_root=request.workspace_root,
        skill_toml_path=request.manifest_path,
        api_reference_branch_ids_by_api_name=_uuid_mapping(
            request.context.get("api_reference_branch_ids_by_api_name")
        ),
    )
    return SemanticPackageMaterializationResult(
        details={
            "skill_toml_path": result.skill_toml_path.as_posix(),
            "skill_name": result.skill_package.name,
            "skill_config_id": str(result.skill_config_id),
            "skill_package_name": result.skill_package.name,
            "skill_package_id": str(result.skill_package.id),
            "semantic_branch_id": str(request.branch_id),
            "source_code_package_id": (
                str(result.source_code_package_id)
                if result.source_code_package_id is not None
                else None
            ),
            "skill_source_path": result.skill_source_path,
            "source_files": list(result.source_files),
            "skill_config_object_instance_graph_commit_id": (
                str(result.skill_config_object_instance_graph_commit_id)
                if result.skill_config_object_instance_graph_commit_id is not None
                else None
            ),
            "skill_package_commit_id": (
                str(result.package_commit_id)
                if result.package_commit_id is not None
                else None
            ),
            "skill_package_head_commit_id": (
                str(result.package_head_commit_id)
                if result.package_head_commit_id is not None
                else None
            ),
            "skill_package_api_package_ids": tuple(
                str(edge.api_package_id)
                for edge in result.skill_package_api_packages
            ),
        },
        bundle_packages=(
            SemanticPackageMaterializationBundle(
                package_key=result.skill_package.name,
                manifest_toml_path=result.skill_toml_path,
                semantic_package_id=result.skill_package.id,
                semantic_root_id=result.skill_config_id,
                semantic_branch_id=request.branch_id,
                semantic_head_commit_id=result.package_head_commit_id,
                semantic_root_object_instance_graph_commit_id=(
                    result.skill_config_object_instance_graph_commit_id
                ),
                semantic_root_kind="skill_config",
                source_code_package_id=result.source_code_package_id,
            ),
        ),
        commit_id=result.package_commit_id,
        head_commit_id=result.package_head_commit_id,
        affected_semantic_keys=_semantic_keys_from_request(request),
        applied_semantic_keys=_semantic_keys_from_request(request),
    )


def _semantic_keys_from_request(
    request: SemanticPackageMaterializationRequest,
) -> tuple[str, ...]:
    raw_keys = request.change_preview.get("affected_semantic_keys")
    if not isinstance(raw_keys, (list, tuple, set)):
        return ()
    return tuple(sorted({str(key).strip() for key in raw_keys if str(key).strip()}))


def _uuid_mapping(value: object) -> dict[str, UUID]:
    if not isinstance(value, dict):
        return {}
    return {
        str(key): cast(UUID, item)
        for key, item in value.items()
        if isinstance(key, str) and isinstance(item, UUID)
    }


__all__ = ["materialize"]
