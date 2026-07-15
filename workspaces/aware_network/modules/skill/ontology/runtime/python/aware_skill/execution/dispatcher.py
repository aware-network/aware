from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol
from uuid import uuid4

from aware_api_runtime.package_ref_resolution import ApiRuntimePackageRef
from aware_meta.materialization import MaterializationLaneContext
from aware_meta.runtime import (
    find_meta_graph_projection_hash_by_name,
    MetaGraphRuntimeIndex,
)

from ..package_ref_resolution import SkillRuntimePackageRef
from .harness import materialize_skill_run_from_package_refs
from .models import (
    SkillInvocationContext,
    SkillRunHarnessRequest,
    SkillRunHarnessResult,
)


class _RuntimeProtocol(Protocol): ...


async def invoke_skill_package(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    context: SkillInvocationContext,
    skill_package_ref: SkillRuntimePackageRef,
    api_package_refs: Sequence[ApiRuntimePackageRef],
    request: SkillRunHarnessRequest,
    commit: bool = True,
    publish: bool = False,
) -> SkillRunHarnessResult:
    """Invoke one SkillPackage through the clean committed package-ref rail.

    The facade intentionally exposes execution context only. Skill/API source
    commits are derived from package OIG refs by the lower clean harness.
    """

    _validate_facade_skill_package_ref(skill_package_ref)
    api_refs = tuple(api_package_refs)
    for api_ref in api_refs:
        _validate_facade_api_package_ref(api_ref)

    return await materialize_skill_run_from_package_refs(
        runtime=runtime,
        index=index,
        actor_id=context.actor_id,
        skill_package_ref=skill_package_ref,
        api_package_refs=api_refs,
        api_call_lane=MaterializationLaneContext(
            branch_id=context.api_call_branch_id or uuid4(),
            projection_hash=find_meta_graph_projection_hash_by_name(
                index=index,
                projection_name="ApiCall",
            ),
        ),
        skill_run_lane=MaterializationLaneContext(
            branch_id=context.skill_run_branch_id or uuid4(),
            projection_hash=find_meta_graph_projection_hash_by_name(
                index=index,
                projection_name="SkillRun",
            ),
        ),
        request=request,
        commit=commit,
        publish=publish,
    )


def _validate_facade_skill_package_ref(package_ref: SkillRuntimePackageRef) -> None:
    if _clean(package_ref.manifest_path) is not None:
        raise RuntimeError(
            "Skill runtime facade rejects SkillRuntimePackageRef.manifest_path."
        )
    if _clean(package_ref.semantic_head_commit_id) is not None:
        raise RuntimeError(
            "Skill runtime facade rejects legacy SkillRuntimePackageRef.semantic_head_commit_id."
        )
    if _clean(package_ref.semantic_object_instance_graph_commit_id) is None:
        raise RuntimeError(
            "Skill runtime facade requires SkillRuntimePackageRef.semantic_object_instance_graph_commit_id."
        )


def _validate_facade_api_package_ref(package_ref: ApiRuntimePackageRef) -> None:
    if _clean(package_ref.manifest_path) is not None:
        raise RuntimeError(
            "Skill runtime facade rejects ApiRuntimePackageRef.manifest_path."
        )
    if _clean(package_ref.manifest_toml_path) is not None:
        raise RuntimeError(
            "Skill runtime facade rejects ApiRuntimePackageRef.manifest_toml_path."
        )
    if _clean(package_ref.semantic_head_commit_id) is not None:
        raise RuntimeError(
            "Skill runtime facade rejects legacy ApiRuntimePackageRef.semantic_head_commit_id."
        )
    if _clean(package_ref.semantic_object_instance_graph_commit_id) is None:
        raise RuntimeError(
            "Skill runtime facade requires every ApiRuntimePackageRef.semantic_object_instance_graph_commit_id."
        )


def _clean(value: object | None) -> str | None:
    if value is None:
        return None
    stripped = str(value).strip()
    return stripped or None


__all__ = ["invoke_skill_package"]
