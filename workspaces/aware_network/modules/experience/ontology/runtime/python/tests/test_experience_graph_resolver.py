from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from aware_experience.graph import resolver


def test_graph_resolver_source_is_clean() -> None:
    source = Path(resolver.__file__).read_text(encoding="utf-8")

    assert "aware_runtime" not in source
    assert "hydrate_orm_graph_from_oig" not in source


@pytest.mark.asyncio
async def test_materialize_lane_instance_ids_reads_meta_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch_id = uuid4()
    commit_id = uuid4()
    oig_id = uuid4()
    source_object_id = uuid4()
    opg = SimpleNamespace(projection_hash="hash:ProjectionExperience")

    class _Store:
        async def head(
            self, *, branch_id: UUID, projection_hash: str
        ) -> dict[str, str]:
            _ = branch_id, projection_hash
            return {
                "commit_id": str(commit_id),
                "object_instance_graph_id": str(oig_id),
            }

    class _Materializer:
        async def get(self, **kwargs: object) -> tuple[object, object]:
            assert kwargs["branch_id"] == branch_id
            assert kwargs["commit_id"] == commit_id
            assert kwargs["oig_id"] == oig_id
            assert kwargs["opg"] is opg
            return (
                SimpleNamespace(
                    class_instances=(
                        SimpleNamespace(source_object_id=source_object_id),
                    )
                ),
                object(),
            )

    monkeypatch.setattr(resolver, "FSCommitStore", _Store)
    monkeypatch.setattr(resolver, "CachedLaneMaterializer", _Materializer)

    index = SimpleNamespace(
        ocg=SimpleNamespace(),
        opg_by_hash={opg.projection_hash: opg},
    )

    assert await resolver._materialize_lane_instance_ids(
        index=cast(Any, index),
        branch_id=branch_id,
        projection_hash=opg.projection_hash,
    ) == {source_object_id}


@pytest.mark.asyncio
async def test_hydrate_projection_experience_graph_identity_uses_meta_reifier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch_id = uuid4()
    commit_id = uuid4()
    oig_id = uuid4()
    identity_id = uuid4()
    opg = SimpleNamespace(
        name="ProjectionExperienceGraph",
        projection_hash="hash:ProjectionExperienceGraph",
    )
    oig = object()
    hydrated = SimpleNamespace(id=identity_id)
    captured: dict[str, object] = {}

    class _Session:
        def __init__(self) -> None:
            self._objects: dict[UUID, object] = {}

        def imap_get(self, _model_type: object, object_id: UUID) -> object | None:
            return self._objects.get(object_id)

        def merge(self, obj: object) -> None:
            self._objects[getattr(obj, "id")] = obj

    class _Scratch:
        def imap_get(self, _model_type: object, object_id: UUID) -> object | None:
            if object_id == identity_id:
                return hydrated
            return None

    class _Store:
        async def head(
            self, *, branch_id: UUID, projection_hash: str
        ) -> dict[str, str]:
            _ = branch_id, projection_hash
            return {
                "commit_id": str(commit_id),
                "object_instance_graph_id": str(oig_id),
            }

    class _Materializer:
        async def get(self, **kwargs: object) -> tuple[object, object]:
            captured["materializer_kwargs"] = kwargs
            return oig, object()

    def _fake_reify_oig_session(**kwargs: object) -> _Scratch:
        captured["reifier_kwargs"] = kwargs
        return _Scratch()

    active_session = _Session()
    index = SimpleNamespace(
        ocg=SimpleNamespace(object_projection_graphs=(opg,)),
        opg_by_hash={opg.projection_hash: opg},
        attribute_configs_by_id={},
        class_configs_by_id={},
    )

    monkeypatch.setattr(resolver, "current_handler_session", lambda: active_session)
    monkeypatch.setattr(resolver, "current_handler_index", lambda: index)
    monkeypatch.setattr(
        resolver,
        "current_handler_context",
        lambda: SimpleNamespace(branch_id=branch_id),
    )
    monkeypatch.setattr(resolver, "FSCommitStore", _Store)
    monkeypatch.setattr(resolver, "CachedLaneMaterializer", _Materializer)
    monkeypatch.setattr(resolver, "reify_oig_session", _fake_reify_oig_session)

    result = (
        await resolver.hydrate_projection_experience_graph_identity_into_active_session(
            projection_experience_graph_identity_id=identity_id,
        )
    )

    assert result is hydrated
    materializer_kwargs = cast(dict[str, object], captured["materializer_kwargs"])
    assert materializer_kwargs["branch_id"] == branch_id
    assert materializer_kwargs["opg"] is opg
    assert materializer_kwargs["commit_id"] == commit_id
    assert materializer_kwargs["oig_id"] == oig_id
    reifier_kwargs = cast(dict[str, object], captured["reifier_kwargs"])
    assert reifier_kwargs["index"] is index
    assert reifier_kwargs["opg"] is opg
    assert reifier_kwargs["oig"] is oig
    assert reifier_kwargs["branch_id"] == branch_id
