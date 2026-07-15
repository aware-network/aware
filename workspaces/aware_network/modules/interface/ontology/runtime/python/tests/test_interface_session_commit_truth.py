from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from _interface_runtime_test_paths import REPO_ROOT
from _meta_proof_support import (
    build_interface_meta_proof_runtime,
    isolated_meta_aware_root,
    projection_hash_by_name,
    rehydrate_lane_root_from_head,
)
from aware_interface_ontology.stable_ids import stable_interface_session_id
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore


@pytest.mark.asyncio
async def test_interface_session_handler_rejects_non_uuid_parent_keys() -> None:
    from aware_interface.handlers.impl.interface.interface_session import (
        build_via_interface,
    )

    with pytest.raises(TypeError, match="requires interface_id"):
        await build_via_interface(  # type: ignore[arg-type]
            interface_id="not-a-uuid",
            identity_session_id=uuid4(),
            name="shared-home",
        )

    with pytest.raises(TypeError, match="requires identity_session_id"):
        await build_via_interface(  # type: ignore[arg-type]
            interface_id=uuid4(),
            identity_session_id="not-a-uuid",
            name="shared-home",
        )


@pytest.mark.asyncio
async def test_interface_session_constructor_commits_and_rehydrates_truth(
    tmp_path: Path,
) -> None:
    with isolated_meta_aware_root(tmp_path / "aware_root") as aware_root:
        runtime = build_interface_meta_proof_runtime(
            repo_root=REPO_ROOT,
            aware_root=aware_root,
        )

        from aware_interface_ontology.interface.interface_enums import (
            InterfaceSessionState,
        )
        from aware_interface_ontology.interface.interface_session import (
            InterfaceSession,
        )

        interface_id = uuid4()
        identity_session_id = uuid4()
        actor_id = uuid4()
        name = "shared-home"
        interface_session_id = stable_interface_session_id(
            interface_id=interface_id,
            identity_session_id=identity_session_id,
            name=name,
        )

        lane = runtime.bind(
            branch_id=interface_session_id,
            projection="InterfaceSession",
            actor_id=actor_id,
        )
        with lane.activate(commit=True, publish=False):
            created = await InterfaceSession.build_via_interface(
                interface_id=interface_id,
                identity_session_id=identity_session_id,
                name=f"  {name}  ",
                state=InterfaceSessionState.active,
            )
            repeated = await InterfaceSession.build_via_interface(
                interface_id=interface_id,
                identity_session_id=identity_session_id,
                name=name,
                state=InterfaceSessionState.active,
            )

        # Generated invocation payload validation may return a fresh Python
        # model instance; idempotency is the same canonical graph root.
        assert repeated.id == created.id
        assert created.id == interface_session_id

        projection_hash = projection_hash_by_name(runtime, "InterfaceSession")
        head = await FSCommitStore(root_dir=aware_root).head(
            branch_id=interface_session_id,
            projection_hash=projection_hash,
        )
        assert head is not None
        assert head["commit_id"]

        committed = await rehydrate_lane_root_from_head(
            runtime=runtime,
            aware_root=aware_root,
            branch_id=interface_session_id,
            projection_name="InterfaceSession",
            root_id=interface_session_id,
            root_type=InterfaceSession,
        )

        assert committed.id == interface_session_id
        assert committed.interface_id == interface_id
        assert committed.identity_session_id == identity_session_id
        assert committed.identity_session is None
        assert committed.name == name
        assert committed.state == InterfaceSessionState.active
        assert "interface_session_network_binding_id" not in committed.model_dump()


@pytest.mark.asyncio
async def test_interface_session_constructor_rejects_blank_name_before_commit(
    tmp_path: Path,
) -> None:
    with isolated_meta_aware_root(tmp_path / "aware_root") as aware_root:
        runtime = build_interface_meta_proof_runtime(
            repo_root=REPO_ROOT,
            aware_root=aware_root,
        )

        from aware_interface_ontology.interface.interface_session import (
            InterfaceSession,
        )

        interface_id = uuid4()
        identity_session_id = uuid4()
        actor_id = uuid4()
        branch_id = uuid4()
        lane = runtime.bind(
            branch_id=branch_id,
            projection="InterfaceSession",
            actor_id=actor_id,
        )

        with pytest.raises(ValueError, match="requires non-empty name"):
            with lane.activate(commit=True, publish=False):
                await InterfaceSession.build_via_interface(
                    interface_id=interface_id,
                    identity_session_id=identity_session_id,
                    name="   ",
                )

        projection_hash = projection_hash_by_name(runtime, "InterfaceSession")
        head = await FSCommitStore(root_dir=aware_root).head(
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
        assert head is None
