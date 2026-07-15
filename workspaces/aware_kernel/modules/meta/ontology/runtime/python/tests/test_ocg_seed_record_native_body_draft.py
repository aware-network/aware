from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from aware_meta.graph.config.lane import seed_commit as seed_commit_module
from aware_meta.graph.config.lane.plan import OCGSeedPlan
from aware_meta.graph.instance.commit.body_codec import OigCommitBodyDraft
from aware_meta.graph.instance.diff import build_object_instance_graph_create_body_draft
from aware_meta.graph.config.lane.errors import OcgSeedError
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph


def test_ocg_seed_reuses_canonical_builder_hashes() -> None:
    graph = ObjectInstanceGraph.model_construct(hash="canonical-hash")

    assert (
        seed_commit_module._require_built_graph_hash(
            graph=graph,
            graph_role="post",
        )
        == "canonical-hash"
    )


def test_ocg_seed_rejects_missing_canonical_builder_hash() -> None:
    graph = ObjectInstanceGraph.model_construct(hash="")

    with pytest.raises(OcgSeedError, match="graph_hash_post"):
        seed_commit_module._require_built_graph_hash(
            graph=graph,
            graph_role="post",
        )


@pytest.mark.asyncio
async def test_ocg_seed_append_uses_body_draft_without_compat_changes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    graph_id = uuid4()
    class_instance = ClassInstance.model_construct(
        id=uuid4(),
        object_instance_graph_id=graph_id,
        class_config_id=uuid4(),
        source_object_id=uuid4(),
        attributes=[],
        class_instance_attributes=[],
    )
    body_draft = build_object_instance_graph_create_body_draft(
        class_instances=(class_instance,),
        created_at=seed_commit_module.SEED_CREATED_AT,
    )
    before_oig = ObjectInstanceGraph.model_construct(
        id=graph_id,
        class_instances=[],
        class_instance_relationships=[],
    )
    after_oig = ObjectInstanceGraph.model_construct(
        id=graph_id,
        class_instances=[class_instance],
        class_instance_relationships=[],
    )
    branch_id = uuid4()
    oigi_id = uuid4()
    plan = OCGSeedPlan(
        seeded=False,
        branch_id=branch_id,
        projection_hash="projection",
        object_instance_graph_id=graph_id,
        root_object_id=graph_id,
        graph_hash_pre="pre",
        graph_hash_post="post",
        commit_id=uuid4(),
        changes=[],
        before_oig=before_oig,
        after_oig=after_oig,
        objects_by_id={},
        body_draft=body_draft,
        object_instance_graph_identity_id=oigi_id,
    )
    captured: dict[str, object] = {}

    class FakeStore:
        aware_root = tmp_path

        async def head(self, **_: object) -> dict[str, object]:
            return {}

        async def get_commit_envelope(self, **_: object) -> None:
            return None

    class FakeCommitter:
        def __init__(self, **_: object) -> None:
            pass

        async def commit_record_shallow(self, **kwargs: object) -> object:
            captured.update(kwargs)
            return object()

        def last_commit_perf_profile_snapshot(self) -> dict[str, int]:
            return {}

    monkeypatch.setattr(
        seed_commit_module,
        "_build_ocg_seed_plan_and_commit",
        lambda **_: (plan, None),
    )
    monkeypatch.setattr(
        seed_commit_module,
        "build_commit_state_index",
        lambda _: SimpleNamespace(),
    )
    monkeypatch.setattr(
        seed_commit_module,
        "extract_object_instance_graph_commit_root_metadata",
        lambda **_: SimpleNamespace(root_source_object_id=graph_id),
    )
    monkeypatch.setattr(
        "aware_meta.graph.instance.commit.committer.FSLaneCommitter",
        FakeCommitter,
    )

    result = await seed_commit_module.ensure_ocg_seeded_lane(
        ocg=ObjectConfigGraph.model_construct(id=graph_id),
        branch_id=branch_id,
        ocg_hash="ocg-hash",
        store=FakeStore(),
    )

    assert result.seeded is True
    assert captured["changes"] == []
    assert captured["body_draft"] is body_draft
    assert captured["object_instance_graph_identity_id"] == oigi_id
    assert seed_commit_module._body_draft_operation_count(body_draft) > 0
    assert isinstance(captured["body_draft"], OigCommitBodyDraft)
