from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from aware_api_runtime.workspace_provider.provider import resolve_currentness_replay
from aware_code.semantic_currentness import (
    SemanticMaterializationCurrentnessReplayRequest,
)
from aware_code.semantic_materialization import SemanticPackageMaterializationBundle


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("semantic_package_kind", "workspace_manifest_kind", "has_semantic_head"),
    (
        ("api_dto_package", "api_dto", False),
        ("api_package", "api", True),
    ),
)
async def test_api_currentness_replays_exact_live_output_heads(
    tmp_path: Path,
    semantic_package_kind: str,
    workspace_manifest_kind: str,
    has_semantic_head: bool,
) -> None:
    runtime_branch_id = uuid4()
    runtime_oig_commit_id = uuid4()
    semantic_branch_id = uuid4() if has_semantic_head else None
    semantic_oig_commit_id = uuid4() if has_semantic_head else None
    artifact_path = tmp_path / "generated/runtime.manifest.json"
    artifact_path.parent.mkdir(parents=True)
    artifact_path.write_text('{"schema":"runtime"}\n', encoding="utf-8")
    artifact_digest = sha256(artifact_path.read_bytes()).hexdigest()
    runtime_ref = {
        "source_code_package_id": str(uuid4()),
        "branch_id": str(runtime_branch_id),
        "projection_hash": "code-package-projection",
        "object_instance_graph_commit_id": str(runtime_oig_commit_id),
        "runtime_artifact_refs": [
            {
                "manifest_path": "generated/runtime.manifest.json",
                "digest": artifact_digest,
                "digest_algorithm": "sha256",
            }
        ],
    }
    bundle = SemanticPackageMaterializationBundle(
        package_key="demo-service-api",
        manifest_toml_path=Path("modules/demo/apis/demo/aware.api.toml"),
        semantic_package_id=uuid4(),
        semantic_root_id=uuid4(),
        semantic_branch_id=semantic_branch_id,
        semantic_object_instance_graph_commit_id=semantic_oig_commit_id,
        semantic_projection_hash=(
            "api-package-projection" if has_semantic_head else None
        ),
        runtime_code_package_refs=(runtime_ref,),
    )

    async def _read_head(
        *,
        branch_id: UUID,
        projection_hash: str,
    ) -> dict[str, object] | None:
        if (
            branch_id == runtime_branch_id
            and projection_hash == "code-package-projection"
        ):
            return {"object_instance_graph_commit_id": str(runtime_oig_commit_id)}
        if (
            semantic_branch_id is not None
            and branch_id == semantic_branch_id
            and projection_hash == "api-package-projection"
        ):
            return {"object_instance_graph_commit_id": str(semantic_oig_commit_id)}
        return None

    result = await resolve_currentness_replay(
        SemanticMaterializationCurrentnessReplayRequest(
            provider_key="aware_api",
            semantic_owner="aware_api.provider",
            workspace_root=tmp_path,
            workspace_manifest_kind=workspace_manifest_kind,
            semantic_package_family="api",
            semantic_package_kind=semantic_package_kind,
            input_proof={"kind": "declared_source_tree", "complete": True},
            bundles=(bundle,),
            read_head=_read_head,
            replay_output_details={
                "artifact_ownership_receipts": ({"status": "available"},)
            },
        )
    )

    assert result.status == "reused"
    assert result.reason == "api_output_heads_and_artifacts_current"
    assert result.replay_kind == "previous_api_output_bundles"


@pytest.mark.asyncio
async def test_api_currentness_rejects_runtime_code_package_head_mismatch(
    tmp_path: Path,
) -> None:
    artifact_path = tmp_path / "generated/runtime.manifest.json"
    artifact_path.parent.mkdir(parents=True)
    artifact_path.write_text('{"schema":"runtime"}\n', encoding="utf-8")
    bundle = SemanticPackageMaterializationBundle(
        package_key="demo-service-dto",
        manifest_toml_path=Path("modules/demo/apis/demo/dto/aware.toml"),
        semantic_package_id=uuid4(),
        semantic_root_id=uuid4(),
        runtime_code_package_refs=(
            {
                "source_code_package_id": str(uuid4()),
                "branch_id": str(uuid4()),
                "projection_hash": "code-package-projection",
                "object_instance_graph_commit_id": str(uuid4()),
                "runtime_artifact_refs": [
                    {
                        "manifest_path": "generated/runtime.manifest.json",
                        "digest": sha256(artifact_path.read_bytes()).hexdigest(),
                        "digest_algorithm": "sha256",
                    }
                ],
            },
        ),
    )

    async def _read_other_head(
        *,
        branch_id: UUID,
        projection_hash: str,
    ) -> dict[str, object]:
        del branch_id, projection_hash
        return {"object_instance_graph_commit_id": str(uuid4())}

    result = await resolve_currentness_replay(
        SemanticMaterializationCurrentnessReplayRequest(
            provider_key="aware_api",
            semantic_owner="aware_api.provider",
            workspace_root=tmp_path,
            workspace_manifest_kind="api_dto",
            semantic_package_family="api",
            semantic_package_kind="api_dto_package",
            input_proof={"kind": "declared_source_tree", "complete": True},
            bundles=(bundle,),
            read_head=_read_other_head,
        )
    )

    assert result.status == "must_execute"
    assert result.reason == "api_runtime_code_package_live_head_mismatch"
