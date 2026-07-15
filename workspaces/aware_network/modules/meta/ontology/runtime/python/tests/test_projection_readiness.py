from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from aware_meta.graph.instance.orm_projection_catchup import LaneProjectionCatchupResult
from aware_meta.graph.instance.projection_readiness import (
    ProjectionReadinessError,
    ProjectionReadinessModes,
    ProjectionReadinessRequirement,
    ensure_projection_readiness,
)


@pytest.mark.asyncio
async def test_projection_readiness_off_mode_skips_without_index(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_meta.graph.instance.projection_readiness as readiness_mod

    async def _fail_catchup(**_: object) -> object:
        raise AssertionError("off readiness must not replay commits")

    monkeypatch.setattr(
        readiness_mod, "ensure_lane_projection_caught_up", _fail_catchup
    )

    requirement = ProjectionReadinessRequirement(
        name="network_node.hosted_service_publication",
        branch_id=uuid4(),
        projection_hash="sha256:network-node",
        mode=ProjectionReadinessModes.OFF,
    )

    result = await ensure_projection_readiness(index=None, requirement=requirement)

    assert result.status == "skipped"
    assert result.skipped_reason == "mode:off"
    assert result.commits_applied == 0


@pytest.mark.asyncio
async def test_projection_readiness_required_db_skips_non_db_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_meta.graph.instance.projection_readiness as readiness_mod

    branch_id = uuid4()
    requirement = ProjectionReadinessRequirement(
        name="service.activation",
        branch_id=branch_id,
        projection_hash="sha256:service",
    )

    async def _fake_catchup(**kwargs: object) -> LaneProjectionCatchupResult:
        return LaneProjectionCatchupResult(
            branch_id=kwargs["branch_id"],  # type: ignore[arg-type]
            projection_hash=str(kwargs["projection_hash"]),
            head_commit_id=None,
            object_instance_graph_id=None,
            commits_applied=0,
            skipped_reason="backend:noop",
        )

    monkeypatch.setattr(
        readiness_mod, "ensure_lane_projection_caught_up", _fake_catchup
    )

    result = await ensure_projection_readiness(
        index=SimpleNamespace(),
        requirement=requirement,
    )

    assert result.status == "skipped"
    assert result.skipped_reason == "backend:noop"


@pytest.mark.asyncio
async def test_projection_readiness_required_db_fails_on_missing_head(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_meta.graph.instance.projection_readiness as readiness_mod

    branch_id = uuid4()
    requirement = ProjectionReadinessRequirement(
        name="service.activation",
        branch_id=branch_id,
        projection_hash="sha256:service",
        mode=ProjectionReadinessModes.REQUIRED_DB,
    )

    async def _fake_catchup(**kwargs: object) -> LaneProjectionCatchupResult:
        return LaneProjectionCatchupResult(
            branch_id=kwargs["branch_id"],  # type: ignore[arg-type]
            projection_hash=str(kwargs["projection_hash"]),
            head_commit_id=None,
            object_instance_graph_id=None,
            commits_applied=0,
            skipped_reason="missing_head",
        )

    monkeypatch.setattr(
        readiness_mod, "ensure_lane_projection_caught_up", _fake_catchup
    )

    with pytest.raises(ProjectionReadinessError, match="Required DB projection"):
        await ensure_projection_readiness(
            index=SimpleNamespace(),
            requirement=requirement,
        )


@pytest.mark.asyncio
async def test_projection_readiness_passes_committed_lane_coordinates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_meta.graph.instance.projection_readiness as readiness_mod

    branch_id = uuid4()
    head_commit_id = uuid4()
    object_instance_graph_id = uuid4()
    captured: dict[str, object] = {}

    async def _fake_catchup(**kwargs: object) -> LaneProjectionCatchupResult:
        captured.update(kwargs)
        return LaneProjectionCatchupResult(
            branch_id=branch_id,
            projection_hash="sha256:network-node",
            head_commit_id=head_commit_id,
            object_instance_graph_id=object_instance_graph_id,
            commits_applied=2,
            skipped_reason=None,
        )

    monkeypatch.setattr(
        readiness_mod, "ensure_lane_projection_caught_up", _fake_catchup
    )

    requirement = ProjectionReadinessRequirement(
        name="network_node.hosted_service_publication",
        branch_id=branch_id,
        projection_hash="sha256:network-node",
        head_commit_id=head_commit_id,
        object_instance_graph_id=object_instance_graph_id,
        mode=ProjectionReadinessModes.REQUIRED_DB,
        commit_every=7,
    )

    result = await ensure_projection_readiness(
        index=SimpleNamespace(),
        requirement=requirement,
    )

    assert result.status == "ready"
    assert result.commits_applied == 2
    assert captured["branch_id"] == branch_id
    assert captured["projection_hash"] == "sha256:network-node"
    assert captured["head_commit_id"] == head_commit_id
    assert captured["object_instance_graph_id"] == object_instance_graph_id
    assert captured["commit_every"] == 7
