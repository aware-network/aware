from __future__ import annotations

from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from aware_api_ontology.api.api import Api
from aware_api_runtime.ontology_graph.materialization import (
    APIOntologyMaterializationSpec,
    service as api_graph_service,
)
from aware_meta.materialization import MaterializationLaneContext


@pytest.mark.asyncio
async def test_api_graph_snapshot_commit_ensures_oigi_lane_before_direct_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    projection_hash = "sha256:api"
    opg_id = uuid4()
    opgi_id = uuid4()
    api_id = uuid4()
    lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash=projection_hash,
    )
    index = SimpleNamespace(
        opg_by_hash={projection_hash: SimpleNamespace(id=opg_id)},
        ocg=SimpleNamespace(),
        attribute_configs_by_id={},
        class_configs_by_id={},
        relationships_by_id={},
    )
    api = Api(id=api_id, name="environment")
    events: list[tuple[str, dict[str, object]]] = []

    async def _fake_build_api_plan_snapshot_objects(
        **_: object,
    ) -> tuple[Api, dict[UUID, Api]]:
        return api, {api_id: api}

    def _fake_build_rooted_object_instance_graph_base(
        **kwargs: object,
    ) -> SimpleNamespace:
        return SimpleNamespace(id=kwargs["oig_id"], hash="hash-pre")

    def _fake_resolve_meta_graph_ocgi_opgi(**_: object) -> tuple[None, SimpleNamespace]:
        return None, SimpleNamespace(id=opgi_id)

    def _fake_build_changes(**_: object) -> tuple[SimpleNamespace]:
        return (SimpleNamespace(change_id=uuid4()),)

    def _fake_materialize_meta_oig_post(**_: object) -> SimpleNamespace:
        return SimpleNamespace(hash="hash-post")

    async def _fake_ensure_object_instance_graph_identity_lane_head(
        **kwargs: object,
    ) -> None:
        assert not any(event_name == "commit" for event_name, _event in events)
        events.append(("ensure", dict(kwargs)))

    class _FakeCommitter:
        async def commit(self, **kwargs: object) -> SimpleNamespace:
            events.append(("commit", dict(kwargs)))
            return SimpleNamespace(
                commit=SimpleNamespace(id=kwargs["commit_id"]),
                object_instance_graph_identity_id=kwargs[
                    "object_instance_graph_identity_id"
                ],
            )

    monkeypatch.setattr(
        api_graph_service,
        "_build_api_plan_snapshot_objects",
        _fake_build_api_plan_snapshot_objects,
    )
    monkeypatch.setattr(
        api_graph_service,
        "build_rooted_object_instance_graph_base",
        _fake_build_rooted_object_instance_graph_base,
    )
    monkeypatch.setattr(
        api_graph_service,
        "resolve_meta_graph_ocgi_opgi",
        _fake_resolve_meta_graph_ocgi_opgi,
    )
    monkeypatch.setattr(
        api_graph_service,
        "build_object_instance_graph_changes_from_orm_change_set",
        _fake_build_changes,
    )
    monkeypatch.setattr(
        api_graph_service,
        "materialize_meta_oig_post",
        _fake_materialize_meta_oig_post,
    )
    monkeypatch.setattr(
        api_graph_service,
        "ensure_object_instance_graph_identity_lane_head",
        _fake_ensure_object_instance_graph_identity_lane_head,
    )
    monkeypatch.setattr(api_graph_service, "FSLaneCommitter", _FakeCommitter)

    result = await api_graph_service._commit_api_plan_snapshot(
        index=index,
        actor_id=None,
        lane=lane,
        spec=APIOntologyMaterializationSpec(
            api_name="environment",
            source_path="apis/environment.aware",
            plan=SimpleNamespace(),
        ),
        accessible_graphs=(),
    )

    assert result.object_count == 1
    assert [event_name for event_name, _event in events] == ["ensure", "commit"]
    ensure_event = events[0][1]
    commit_event = events[1][1]
    assert (
        ensure_event["object_instance_graph_id"]
        == commit_event["object_instance_graph_id"]
    )
    assert ensure_event["domain_projection_hash"] == projection_hash
    assert ensure_event["author_id"] == commit_event["author_id"]
