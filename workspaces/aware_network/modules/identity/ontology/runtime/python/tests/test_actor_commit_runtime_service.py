from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

import pytest


class _FakeLane:
    def __init__(self) -> None:
        self.activations: list[tuple[bool, bool]] = []

    def activate(self, *, commit: bool, publish: bool) -> object:
        self.activations.append((commit, publish))
        return self

    def __enter__(self) -> "_FakeLane":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        _ = (exc_type, exc, tb)


class _FakeContext:
    def __init__(self) -> None:
        self.bound_lanes: list[tuple[str, UUID, _FakeLane]] = []

    def bind_lane(self, *, projection: str, branch_id: UUID) -> _FakeLane:
        lane = _FakeLane()
        self.bound_lanes.append((projection, branch_id, lane))
        return lane


def test_actor_commit_uses_meta_runtime_readback_boundary() -> None:
    import aware_identity.actor.commit as commit_mod

    source = Path(commit_mod.__file__).read_text(encoding="utf-8")

    assert "from aware_runtime.index" not in source
    assert "AwareRuntimeIndex" not in source
    assert "hydrate_orm_graph_from_oig" not in source
    assert (
        "from aware_runtime.materialization import MaterializationRuntimeContext"
        not in source
    )


@pytest.mark.asyncio
async def test_actor_commit_runtime_ensure_creates_actor_commit_lane(
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    import aware_identity.actor.commit as commit_mod
    from aware_identity_service_dto.actor.commit import ActorCommitEnsureRequest
    from aware_identity_ontology.actor.actor_commit import ActorCommit
    from aware_identity_ontology.stable_ids import stable_actor_commit_id

    actor_id = uuid4()
    domain_branch_id = uuid4()
    domain_commit_id = uuid4()
    object_instance_graph_commit_id = uuid4()
    expected_actor_commit_id = stable_actor_commit_id(
        actor_id=actor_id,
        domain_branch_id=domain_branch_id,
        domain_projection_hash="identity.projection.hash",
        domain_commit_id=domain_commit_id,
    )
    context = _FakeContext()
    ensure_calls: list[tuple[ActorCommitEnsureRequest, str]] = []
    materialize_calls = 0

    async def _resolve_actor_commit_by_id(
        *,
        context: object,
        actor_commit_id: UUID,
    ) -> ActorCommit | None:
        nonlocal materialize_calls
        assert context is context_fake
        assert actor_commit_id == expected_actor_commit_id
        materialize_calls += 1
        if materialize_calls == 1:
            return None
        return ActorCommit(
            id=expected_actor_commit_id,
            actor_id=actor_id,
            domain_branch_id=domain_branch_id,
            domain_projection_hash="identity.projection.hash",
            domain_commit_id=domain_commit_id,
            object_instance_graph_commit_id=object_instance_graph_commit_id,
            operation_label="Identity.signup",
            call_target="function_call",
            head_version=1,
        )

    async def _ensure_actor_commit_on_identity_lane(
        *,
        context: object,
        request: ActorCommitEnsureRequest,
        projection_hash: str,
    ) -> None:
        assert context is context_fake
        ensure_calls.append((request, projection_hash))

    context_fake = context
    monkeypatch.setattr(
        commit_mod,
        "_resolve_actor_commit_by_id",
        _resolve_actor_commit_by_id,
    )
    monkeypatch.setattr(
        commit_mod,
        "_ensure_actor_commit_on_identity_lane",
        _ensure_actor_commit_on_identity_lane,
    )

    receipt = await commit_mod.ensure_actor_commit(
        request=ActorCommitEnsureRequest(
            actor_id=actor_id,
            domain_branch_id=domain_branch_id,
            domain_projection_hash="identity.projection.hash",
            domain_commit_id=domain_commit_id,
            object_instance_graph_commit_id=object_instance_graph_commit_id,
            operation_label="Identity.signup",
            call_target="function_call",
            head_version=1,
            request_id=uuid4(),
        ),
        context=cast(Any, context),
    )

    assert receipt.actor_commit_created is True
    assert receipt.actor_commit.actor_commit_id == expected_actor_commit_id
    assert receipt.actor_commit.actor_id == actor_id
    assert receipt.actor_commit.object_instance_graph_commit_id == (
        object_instance_graph_commit_id
    )
    assert receipt.actor_commit.operation_label == "Identity.signup"
    assert receipt.info == "identity actor-commit ensured"
    assert len(ensure_calls) == 1
    ensure_request, ensure_projection_hash = ensure_calls[0]
    assert ensure_request.actor_id == actor_id
    assert ensure_request.domain_branch_id == domain_branch_id
    assert ensure_projection_hash == "identity.projection.hash"
    assert ensure_request.domain_commit_id == domain_commit_id


@pytest.mark.asyncio
async def test_actor_commit_runtime_resolve_filters_and_sorts_actor_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    import aware_identity.actor.commit as commit_mod
    from aware_identity_service_dto.actor.commit import ActorCommitResolveRequest
    from aware_identity_ontology.actor.actor_commit import ActorCommit

    actor_id = uuid4()
    other_actor_id = uuid4()
    function_id = uuid4()
    newer_oig_commit_id = uuid4()
    context = _FakeContext()

    async def _list_actor_commits(*, context: object) -> list[ActorCommit]:
        assert context is context_fake
        return [
            ActorCommit(
                id=uuid4(),
                actor_id=actor_id,
                domain_branch_id=uuid4(),
                domain_projection_hash="identity.projection.hash",
                domain_commit_id=uuid4(),
                object_instance_graph_commit_id=newer_oig_commit_id,
                function_id=function_id,
                created_at_unix_ms=200,
                operation_label="newer",
            ),
            ActorCommit(
                id=uuid4(),
                actor_id=actor_id,
                domain_branch_id=uuid4(),
                domain_projection_hash="identity.projection.hash",
                domain_commit_id=uuid4(),
                object_instance_graph_commit_id=uuid4(),
                function_id=function_id,
                created_at_unix_ms=100,
                operation_label="older",
            ),
            ActorCommit(
                id=uuid4(),
                actor_id=other_actor_id,
                domain_branch_id=uuid4(),
                domain_projection_hash="identity.projection.hash",
                domain_commit_id=uuid4(),
                object_instance_graph_commit_id=uuid4(),
                function_id=function_id,
                created_at_unix_ms=300,
                operation_label="other",
            ),
        ]

    context_fake = context
    monkeypatch.setattr(commit_mod, "_list_actor_commits", _list_actor_commits)

    result = await commit_mod.resolve_actor_commits(
        request=ActorCommitResolveRequest(
            actor_id=actor_id,
            domain_projection_hash="identity.projection.hash",
            function_id=function_id,
            limit=1,
        ),
        context=cast(Any, context),
    )

    assert [record.operation_label for record in result.actor_commits] == ["newer"]
    assert (
        result.actor_commits[0].object_instance_graph_commit_id == newer_oig_commit_id
    )
    assert result.info == "identity actor-commits resolved"
