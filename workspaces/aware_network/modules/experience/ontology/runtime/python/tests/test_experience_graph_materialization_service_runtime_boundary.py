from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from aware_experience.graph.materialization import (
    service as graph_materialization_service,
)


def test_experience_graph_materialization_service_source_is_clean() -> None:
    source = Path(graph_materialization_service.__file__).read_text(encoding="utf-8")

    assert "aware_" + "runtime" not in source
    assert "hydrate_orm_graph_" + "from_oig" not in source


def test_find_projection_hash_by_name_reads_meta_index() -> None:
    index = SimpleNamespace(
        ocg=SimpleNamespace(
            object_projection_graphs=(
                SimpleNamespace(name="Other", projection_hash="hash:other"),
                SimpleNamespace(
                    name="ProjectionExperienceGraph",
                    projection_hash="hash:projection-experience-graph",
                ),
            )
        )
    )

    assert (
        graph_materialization_service._find_projection_hash_by_name(
            index=cast(Any, index),
            projection_name="ProjectionExperienceGraph",
        )
        == "hash:projection-experience-graph"
    )


@pytest.mark.asyncio
async def test_hydrate_lane_session_uses_meta_reifier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch_id = uuid4()
    commit_id = uuid4()
    projection_hash = "hash:ProjectionExperience"
    opg = SimpleNamespace(name="ProjectionExperience", projection_hash=projection_hash)
    oig = object()
    scratch_session = object()
    captured: dict[str, object] = {}

    class _Store:
        async def head(
            self, *, branch_id: UUID, projection_hash: str
        ) -> dict[str, str]:
            captured["head"] = {
                "branch_id": branch_id,
                "projection_hash": projection_hash,
            }
            return {"commit_id": str(commit_id)}

    class _Materializer:
        async def get(self, **kwargs: object) -> tuple[object, object]:
            captured["materializer_kwargs"] = kwargs
            return oig, object()

    def _fake_reify_oig_session(**kwargs: object) -> object:
        captured["reifier_kwargs"] = kwargs
        return scratch_session

    monkeypatch.setattr(graph_materialization_service, "FSCommitStore", _Store)
    monkeypatch.setattr(graph_materialization_service, "OIGMaterializer", _Materializer)
    monkeypatch.setattr(
        graph_materialization_service,
        "reify_oig_session",
        _fake_reify_oig_session,
    )
    index = SimpleNamespace(
        ocg=SimpleNamespace(),
        opg_by_hash={projection_hash: opg},
        attribute_configs_by_id={},
        class_configs_by_id={},
    )

    result = await graph_materialization_service._hydrate_lane_session(
        index=cast(Any, index),
        branch_id=branch_id,
        projection_hash=projection_hash,
        error_context="test",
    )

    assert result is scratch_session
    assert captured["head"] == {
        "branch_id": branch_id,
        "projection_hash": projection_hash,
    }
    materializer_kwargs = cast(dict[str, object], captured["materializer_kwargs"])
    assert materializer_kwargs["branch_id"] == branch_id
    assert materializer_kwargs["opg"] is opg
    assert materializer_kwargs["commit_id"] is None
    assert materializer_kwargs["attribute_configs_by_id"] == {}
    assert materializer_kwargs["class_configs_by_id"] == {}
    reifier_kwargs = cast(dict[str, object], captured["reifier_kwargs"])
    assert reifier_kwargs["index"] is index
    assert reifier_kwargs["opg"] is opg
    assert reifier_kwargs["oig"] is oig
    assert reifier_kwargs["branch_id"] == branch_id
