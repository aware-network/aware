from __future__ import annotations

from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import pytest

from _meta_proof_support import (
    build_interface_meta_proof_runtime,
    isolated_meta_aware_root,
    projection_by_name,
)
from aware_attention_ontology.stable_ids import stable_focus_id
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.runtime import resolve_meta_graph_ocgi_opgi
from _interface_runtime_test_paths import REPO_ROOT


@pytest.mark.asyncio
async def test_focus_created_before_os_exposes_oigb(tmp_path: Path) -> None:
    """
    Runtime invariant (v0):

    - Before the OS exposes an OIGB as a navigable branch, runtime should ensure
      a canonical Focus exists for that OIGB.

    The Meta runtime currently commits the FocusScope lane and OIGI history, but
    does not yet run an Attention-owned required reaction that creates the Focus
    lane. The missing Focus head is recorded as an xfail at the invariant point,
    not hidden by legacy harness setup.
    """

    repo_root = REPO_ROOT

    with isolated_meta_aware_root(tmp_path / "aware_root") as aware_root:
        runtime = build_interface_meta_proof_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )

        from aware_attention_ontology.focus.focus_scope import FocusScope

        context = runtime.context
        assert context is not None
        ids = _runtime_ids()
        focus_scope_id = uuid5(
            NAMESPACE_URL,
            "aware://tests/focus-first/focus_scope/meta/v1",
        )

        focus_scope_opg = projection_by_name(runtime, "FocusScope")
        focus_opg = projection_by_name(runtime, "Focus")
        assert focus_scope_opg is not None
        assert focus_opg is not None

        lane = runtime.bind(
            branch_id=focus_scope_id,
            projection="FocusScope",
            actor_id=ids["actor_id"],
        )
        with lane.activate(commit=True, publish=False):
            await FocusScope.build(
                title="Execution",
                description="Personal scope",
                expires_at=None,
                is_active=True,
                last_accessed=None,
            )

        _ocgi, target_opgi = resolve_meta_graph_ocgi_opgi(
            index=context.index,
            projection_hash=focus_scope_opg.projection_hash,
        )
        assert target_opgi is not None
        focus_id = stable_focus_id(
            object_projection_graph_identity_id=target_opgi.id,
            focus_scope_id=ids["thread_id"],
        )

        head = await FSCommitStore(root_dir=aware_root).head(
            branch_id=focus_id,
            projection_hash=focus_opg.projection_hash,
        )
        if not head or not head.get("commit_id"):
            pytest.xfail(
                "Meta runtime lacks the Attention required reaction that creates "
                "Focus before exposing a committed domain OIGB.",
            )
        assert head and head.get("commit_id"), head


def _runtime_ids() -> dict[str, UUID]:
    return {
        "environment_id": uuid4(),
        "process_id": uuid4(),
        "thread_id": uuid4(),
        "actor_id": uuid4(),
    }
