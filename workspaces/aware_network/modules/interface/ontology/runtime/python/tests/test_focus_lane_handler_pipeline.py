from __future__ import annotations

from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import pytest

from _meta_proof_support import (
    build_interface_meta_proof_runtime,
    isolated_meta_aware_root,
    projection_by_name,
    rehydrate_lane_root_from_head,
)
from aware_attention_ontology.stable_ids import stable_focus_id
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.runtime import resolve_meta_graph_ocgi_opgi
from aware_meta_ontology.stable_ids import (
    stable_object_instance_graph_branch_id,
    stable_object_instance_graph_identity_id,
)
from _interface_runtime_test_paths import REPO_ROOT


@pytest.mark.asyncio
async def test_focus_lane_commit_matches_focus_build_handler(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    with isolated_meta_aware_root(tmp_path / "aware_root") as aware_root:
        runtime = build_interface_meta_proof_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )

        from aware_attention_ontology.focus.focus import Focus
        from aware_attention_ontology.focus.focus_scope import FocusScope

        context = runtime.context
        assert context is not None
        ids = _runtime_ids()
        ns = uuid5(NAMESPACE_URL, "aware://tests/runtime/focus_lane/meta/v1")
        focus_scope_id = uuid5(ns, "focus-scope")

        focus_scope_lane = runtime.bind(
            branch_id=focus_scope_id,
            projection="FocusScope",
            actor_id=ids["actor_id"],
        )
        with focus_scope_lane.activate(commit=True, publish=False):
            await FocusScope.build(
                title="Execution",
                description="Personal scope",
                expires_at=None,
                is_active=True,
                last_accessed=None,
            )

        focus_scope_opg = projection_by_name(runtime, "FocusScope")
        assert focus_scope_opg is not None
        focus_scope_head = await FSCommitStore(root_dir=aware_root).head(
            branch_id=focus_scope_id,
            projection_hash=focus_scope_opg.projection_hash,
        )
        assert focus_scope_head and focus_scope_head.get("object_instance_graph_id")
        focus_scope_oig_id = UUID(str(focus_scope_head["object_instance_graph_id"]))

        _ocgi, target_opgi = resolve_meta_graph_ocgi_opgi(
            index=context.index,
            projection_hash=focus_scope_opg.projection_hash,
        )
        assert target_opgi is not None
        target_opgi_id = target_opgi.id
        focus_scope_oigi_id = stable_object_instance_graph_identity_id(
            object_projection_graph_identity_id=target_opgi_id,
            object_instance_graph_id=focus_scope_oig_id,
        )
        focus_scope_oigb_id = stable_object_instance_graph_branch_id(
            object_instance_graph_identity_id=focus_scope_oigi_id,
            branch_id=focus_scope_id,
        )

        focus_id = stable_focus_id(
            object_projection_graph_identity_id=target_opgi_id,
            focus_scope_id=focus_scope_id,
        )
        focus_lane = runtime.bind(
            branch_id=focus_id,
            projection="Focus",
            actor_id=ids["actor_id"],
        )
        with focus_lane.activate(commit=True, publish=False):
            await Focus.build(
                focus_scope_id=focus_scope_id,
                object_projection_graph_identity_id=target_opgi_id,
                projection_hash=focus_scope_opg.projection_hash,
                object_instance_graph_branch_id=focus_scope_oigb_id,
                target_type="oigb",
                target_id=focus_scope_oigb_id,
                description="Focus lane handler proof",
                expires_at=None,
                is_active=True,
                last_accessed=None,
            )

        committed_focus = await rehydrate_lane_root_from_head(
            runtime=runtime,
            aware_root=aware_root,
            branch_id=focus_id,
            projection_name="Focus",
            root_id=focus_id,
            root_type=Focus,
        )

        assert committed_focus.id == focus_id
        assert committed_focus.focus_scope_id == focus_scope_id
        assert committed_focus.projection_hash == focus_scope_opg.projection_hash
        assert committed_focus.object_projection_graph_identity_id == target_opgi_id
        assert committed_focus.object_instance_graph_branch_id == focus_scope_oigb_id
        assert committed_focus.target_type == "oigb"
        assert committed_focus.target_id == focus_scope_oigb_id
        assert committed_focus.description == "Focus lane handler proof"
        assert committed_focus.is_active is True


def _runtime_ids() -> dict[str, object]:
    return {
        "environment_id": uuid4(),
        "process_id": uuid4(),
        "thread_id": uuid4(),
        "actor_id": uuid4(),
    }
