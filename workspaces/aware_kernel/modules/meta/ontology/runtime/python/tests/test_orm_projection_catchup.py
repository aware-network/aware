from __future__ import annotations

from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from aware_meta.graph.instance.orm_projection_catchup import (
    ensure_lane_projection_caught_up,
)


class _FakeGraph:
    def __init__(self) -> None:
        self.hash = "root"
        self.applied: list[object] = []

    def model_copy(self, *, deep: bool = False) -> SimpleNamespace:
        _ = deep
        return SimpleNamespace(hash=self.hash, applied=tuple(self.applied))


class _FakeSession:
    def __init__(self, *, backend_name: str = "db") -> None:
        self.skip_db = False
        self._backend_name = backend_name
        self.commit_count = 0
        self.rollback_count = 0

    async def commit(self) -> None:
        self.commit_count += 1

    async def rollback(self) -> None:
        self.rollback_count += 1


class _FakeStore:
    def __init__(self, commits: tuple[object, ...]) -> None:
        self.commits = commits
        self.iterated = False

    async def head(self, **_: object) -> dict[str, str]:
        commit = self.commits[-1]
        return {
            "commit_id": str(commit.commit.id),
            "object_instance_graph_id": str(commit.object_instance_graph_id),
        }

    async def iter_lineage_forward(self, **_: object):
        self.iterated = True
        for commit in self.commits:
            yield commit


def _commit(
    *,
    object_instance_graph_id: UUID,
    changes: tuple[object, ...],
) -> object:
    return SimpleNamespace(
        commit=SimpleNamespace(id=uuid4()),
        object_instance_graph_id=object_instance_graph_id,
        object_instance_graph_key="aware_meta",
        object_instance_graph_name="aware_meta",
        object_instance_graph_description="",
        root_source_object_id=uuid4(),
        root_class_config_id=uuid4(),
        object_instance_graph_changes=list(changes),
        graph_hash_pre="",
        graph_hash_post="",
    )


@pytest.mark.asyncio
async def test_ensure_lane_projection_caught_up_replays_commits_through_orm_projector(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_meta.graph.instance.orm_projection_catchup as catchup_mod

    branch_id = uuid4()
    projection_hash = "service-projection"
    oig_id = uuid4()
    first_change = object()
    second_change = object()
    commits = (
        _commit(object_instance_graph_id=oig_id, changes=(first_change,)),
        _commit(object_instance_graph_id=oig_id, changes=(second_change,)),
    )
    store = _FakeStore(commits)
    session = _FakeSession()
    staged: list[dict[str, object]] = []

    def _fake_build_rooted_object_instance_graph_base(**_: object) -> _FakeGraph:
        return _FakeGraph()

    def _fake_apply_object_instance_graph_changes(
        *,
        graph: _FakeGraph,
        changes: list[object],
        **_: object,
    ) -> None:
        graph.applied.extend(changes)

    async def _fake_stage_domain_persistence(**kwargs: object) -> None:
        staged.append(dict(kwargs))

    monkeypatch.setattr(
        catchup_mod,
        "build_rooted_object_instance_graph_base",
        _fake_build_rooted_object_instance_graph_base,
    )
    monkeypatch.setattr(
        catchup_mod,
        "apply_object_instance_graph_changes",
        _fake_apply_object_instance_graph_changes,
    )
    monkeypatch.setattr(catchup_mod, "build_index", lambda _graph: object())
    monkeypatch.setattr(
        catchup_mod,
        "compute_hash",
        lambda graph, *, index: f"hash:{len(graph.applied)}",
    )
    monkeypatch.setattr(
        catchup_mod,
        "stage_domain_persistence",
        _fake_stage_domain_persistence,
    )

    result = await ensure_lane_projection_caught_up(
        index=SimpleNamespace(
            ocg=object(),
            opg_by_hash={projection_hash: object()},
            attribute_configs_by_id={},
            class_configs_by_id={},
        ),
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_store=store,  # type: ignore[arg-type]
        session=session,  # type: ignore[arg-type]
        commit_every=0,
    )

    assert result.commits_applied == 2
    assert result.skipped_reason is None
    assert store.iterated is True
    assert session.commit_count == 1
    assert session.rollback_count == 0
    assert [call["changes"] for call in staged] == [
        [first_change],
        [second_change],
    ]
    assert all(call["session"] is session for call in staged)
    assert all(call["branch_id"] == branch_id for call in staged)
    assert all(call["projection_hash"] == projection_hash for call in staged)


@pytest.mark.asyncio
async def test_ensure_lane_projection_caught_up_skips_non_db_sessions() -> None:
    class _ExplodingStore:
        async def head(self, **_: object) -> dict[str, str]:
            raise AssertionError("non-db catch-up must not inspect commit store")

    result = await ensure_lane_projection_caught_up(
        index=SimpleNamespace(
            ocg=object(),
            opg_by_hash={},
            attribute_configs_by_id={},
            class_configs_by_id={},
        ),
        branch_id=uuid4(),
        projection_hash="service-projection",
        commit_store=_ExplodingStore(),  # type: ignore[arg-type]
        session=_FakeSession(backend_name="noop"),  # type: ignore[arg-type]
    )

    assert result.commits_applied == 0
    assert result.skipped_reason == "backend:noop"
