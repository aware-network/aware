from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import pytest

from aware_code.materialization.workspace_provider import resolve_currentness_replay
from aware_code.semantic_contract import CODE_MATERIALIZATION_CAPABILITY_METADATA
from aware_code.semantic_currentness import (
    SemanticMaterializationCurrentnessReplayContextRequirement,
    SemanticMaterializationCurrentnessReplayRequest,
    resolve_semantic_materialization_currentness_replay_adapter,
)
from aware_code.semantic_materialization import SemanticPackageMaterializationBundle


@pytest.mark.asyncio
async def test_code_currentness_adapter_requires_exact_live_head() -> None:
    branch_id = uuid4()
    oig_commit_id = uuid4()
    bundle = SemanticPackageMaterializationBundle(
        package_key="aware-code",
        manifest_toml_path=Path("pyproject.toml"),
        semantic_package_id=uuid4(),
        semantic_root_id=uuid4(),
        semantic_branch_id=branch_id,
        semantic_head_commit_id=oig_commit_id,
        semantic_object_instance_graph_commit_id=oig_commit_id,
        semantic_root_object_instance_graph_commit_id=oig_commit_id,
        semantic_projection_hash="code-package-projection",
    )

    async def _read_head(
        *,
        branch_id: UUID,
        projection_hash: str,
    ) -> dict[str, object]:
        assert branch_id == bundle.semantic_branch_id
        assert projection_hash == bundle.semantic_projection_hash
        return {"object_instance_graph_commit_id": str(oig_commit_id)}

    adapter = resolve_semantic_materialization_currentness_replay_adapter(
        capability_metadata=CODE_MATERIALIZATION_CAPABILITY_METADATA,
    )
    assert adapter is resolve_currentness_replay
    request = SemanticMaterializationCurrentnessReplayRequest(
        provider_key="aware_code",
        semantic_owner="aware_code.provider",
        workspace_root=Path.cwd(),
        workspace_manifest_kind="code",
        semantic_package_family="code",
        semantic_package_kind="code_package",
        input_proof={"kind": "declared_source_tree", "complete": True},
        bundles=(bundle,),
        read_head=_read_head,
    )

    current = await resolve_currentness_replay(request)
    assert current.reused is True
    assert current.replay_kind == "previous_code_package_bundles"
    assert current.context_requirement == (
        SemanticMaterializationCurrentnessReplayContextRequirement()
    )

    async def _read_stale_head(**_kwargs: object) -> dict[str, object]:
        return {"object_instance_graph_commit_id": str(uuid4())}

    stale = await resolve_currentness_replay(
        SemanticMaterializationCurrentnessReplayRequest(
            provider_key=request.provider_key,
            semantic_owner=request.semantic_owner,
            workspace_root=request.workspace_root,
            workspace_manifest_kind=request.workspace_manifest_kind,
            semantic_package_family=request.semantic_package_family,
            semantic_package_kind=request.semantic_package_kind,
            input_proof=request.input_proof,
            bundles=request.bundles,
            read_head=_read_stale_head,
        )
    )
    assert stale.reused is False
    assert stale.reason == "code_package_live_head_mismatch"
