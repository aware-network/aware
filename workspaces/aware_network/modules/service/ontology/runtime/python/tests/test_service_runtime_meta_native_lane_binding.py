from __future__ import annotations

from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from aware_service_runtime.materialization import service as service_materialization
from aware_service_runtime.ontology.materialization import _lane_hydration


class _FakeMetaLane:
    def __init__(self, *, projection: str, branch_id: object) -> None:
        self.binding = SimpleNamespace(projection_hash=projection)
        self.branch_id = branch_id
        self.last_commit_id = None
        self.last_head_commit_id = None
        self.activate_calls: list[dict[str, object]] = []

    def activate(self, **kwargs: object) -> object:
        self.activate_calls.append(dict(kwargs))
        return nullcontext("active")


class _FakeMetaRuntime:
    def __init__(self) -> None:
        self.bind_calls: list[dict[str, object]] = []

    def bind(self, **kwargs: object) -> _FakeMetaLane:
        self.bind_calls.append(dict(kwargs))
        return _FakeMetaLane(
            projection=str(kwargs["projection"]),
            branch_id=kwargs["branch_id"],
        )


def _lane_kwargs(runtime: object) -> dict[str, object]:
    return {
        "runtime": runtime,
        "index": object(),
        "branch_id": uuid4(),
        "projection": "service-test-projection-hash",
        "actor_id": uuid4(),
    }


def test_service_runtime_lane_binding_uses_meta_runtime_bind() -> None:
    runtime = _FakeMetaRuntime()

    runtime_lane = _lane_hydration.bind_service_runtime_lane(**_lane_kwargs(runtime))

    assert runtime.bind_calls
    assert runtime_lane.binding.projection_hash == "service-test-projection-hash"
    with runtime_lane.activate(
        commit=True,
        publish=False,
        hydrate_portal_targets=False,
    ) as activated:
        assert activated == "active"


def test_service_materialization_lane_binding_uses_same_meta_native_helper() -> None:
    runtime = _FakeMetaRuntime()

    runtime_lane = service_materialization._bind_runtime_lane(**_lane_kwargs(runtime))

    assert runtime.bind_calls
    assert runtime_lane.binding.projection_hash == "service-test-projection-hash"


def test_service_runtime_lane_binding_rejects_missing_meta_bind() -> None:
    with pytest.raises(RuntimeError, match=r"runtime\.bind"):
        _lane_hydration.bind_service_runtime_lane(**_lane_kwargs(object()))


def test_service_runtime_lane_binding_has_no_aware_runtime_harness_fallback() -> None:
    lane_hydration_source = Path(_lane_hydration.__file__).read_text()
    service_source = Path(service_materialization.__file__).read_text()

    assert "aware_runtime.harness" not in lane_hydration_source
    assert "aware_runtime.harness" not in service_source
