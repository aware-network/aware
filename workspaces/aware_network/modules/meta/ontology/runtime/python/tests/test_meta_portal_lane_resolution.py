from __future__ import annotations

from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from aware_meta.runtime import portal_lane_resolution as resolver_mod
from aware_meta.runtime.portal_lane_resolution import (
    attach_portal_target_branch_relationship_for_object,
    ensure_portal_target_lane_ref_for_object,
    resolve_portal_target_branch_ref_for_object,
    resolve_portal_target_lane_ref,
    resolve_portal_target_lane_refs,
    resolve_portal_target_lane_ref_for_object,
)
from aware_meta.graph.projection.branching import stable_portal_target_branch_id
from aware_meta_ontology.stable_ids import stable_object_instance_graph_branch_id


class _FakeCommitStore:
    def __init__(self, heads: dict[tuple[UUID, str], dict[str, object]]) -> None:
        self.heads = heads

    async def head(self, *, branch_id: UUID, projection_hash: str):
        return self.heads.get((branch_id, projection_hash))

    async def iter_lane_heads_by_projection(self, *, projection_hash: str):
        for (branch_id, head_projection_hash), head in self.heads.items():
            if head_projection_hash == projection_hash:
                yield branch_id, head


class _FakeSession:
    def __init__(self, instances: dict[UUID, object]) -> None:
        self.instances = instances

    def imap_get(self, _model_type: object, instance_id: UUID):
        return self.instances.get(instance_id)


def _fake_index() -> SimpleNamespace:
    return SimpleNamespace(
        ocg=SimpleNamespace(),
        opg_by_hash={"sha256:target": SimpleNamespace(projection_hash="sha256:target")},
        attribute_configs_by_id={},
        class_configs_by_id={},
    )


def _portal_fixture(
    *,
    relationship_count: int = 1,
    target_lane_count: int = 1,
    target_root_object_id: UUID | None = None,
    include_lane_head_commit_id: bool = True,
) -> dict[str, object]:
    source_branch_id = uuid4()
    source_projection_hash = "sha256:source"
    source_oig_id = uuid4()
    source_oigi_id = uuid4()
    source_oigi_projection_hash = "sha256:oigi"
    source_oigi_commit_id = uuid4()
    source_oigb_id = stable_object_instance_graph_branch_id(
        object_instance_graph_identity_id=source_oigi_id,
        branch_id=source_branch_id,
    )

    target_branch_id = uuid4()
    target_oigb_id = stable_object_instance_graph_branch_id(
        object_instance_graph_identity_id=source_oigi_id,
        branch_id=target_branch_id,
    )
    lane_entries = []
    heads: dict[tuple[UUID, str], dict[str, object]] = {
        (source_branch_id, source_projection_hash): {
            "commit_id": uuid4(),
            "object_instance_graph_id": source_oig_id,
            "graph_hash_post": "sha256:source-post",
        },
        (source_oig_id, source_oigi_projection_hash): {
            "commit_id": source_oigi_commit_id,
            "object_instance_graph_id": source_oigi_id,
            "graph_hash_post": "sha256:oigi-post",
        },
    }
    for index in range(target_lane_count):
        target_projection_hash = (
            "sha256:target" if index == 0 else f"sha256:target-{index}"
        )
        target_head_commit_id = uuid4()
        target_oig_id = uuid4()
        target_graph_hash_post = f"sha256:target-post-{index}"
        heads[(target_branch_id, target_projection_hash)] = {
            "commit_id": target_head_commit_id,
            "object_instance_graph_id": target_oig_id,
            "root_object_id": target_root_object_id or uuid4(),
            "graph_hash_post": target_graph_hash_post,
        }
        lane_kwargs: dict[str, object] = {
            "id": uuid4(),
            "branch_id": target_branch_id,
            "lane_hash": target_projection_hash,
        }
        if include_lane_head_commit_id:
            lane_kwargs["head_commit_id"] = target_head_commit_id
        lane = SimpleNamespace(**lane_kwargs)
        lane_entries.append(
            SimpleNamespace(
                id=uuid4(),
                lane_id=lane.id,
                lane=lane,
            )
        )

    target_oigb = SimpleNamespace(
        id=target_oigb_id,
        branch_id=target_branch_id,
        object_instance_graph_lanes=lane_entries,
    )
    relationships = [
        SimpleNamespace(
            id=uuid4(),
            object_instance_graph_branch_id=source_oigb_id,
            target_object_instance_graph_branch_id=target_oigb_id,
            target_object_instance_graph_branch=target_oigb,
        )
        for _ in range(relationship_count)
    ]
    source_oigb = SimpleNamespace(
        id=source_oigb_id,
        branch_id=source_branch_id,
        object_instance_graph_branch_relationships=relationships,
    )
    return {
        "heads": heads,
        "source_branch_id": source_branch_id,
        "source_projection_hash": source_projection_hash,
        "source_oig_id": source_oig_id,
        "source_oigi_id": source_oigi_id,
        "source_oigi_projection_hash": source_oigi_projection_hash,
        "source_oigi_commit_id": source_oigi_commit_id,
        "source_oigb_id": source_oigb_id,
        "target_branch_id": target_branch_id,
        "target_oigb_id": target_oigb_id,
        "target_oigb": target_oigb,
        "target_oigbs": {target_oigb_id: target_oigb},
        "relationships": relationships,
        "source_oigb": source_oigb,
    }


def _install_fake_runtime(
    monkeypatch: pytest.MonkeyPatch,
    *,
    fixture: dict[str, object],
) -> list[dict[str, object]]:
    store = _FakeCommitStore(fixture["heads"])  # type: ignore[arg-type]
    materializer_calls: list[dict[str, object]] = []

    class _FakeMaterializer:
        def __init__(self, *, commits: object) -> None:
            assert commits is store

        async def get(self, **kwargs: object):
            materializer_calls.append(dict(kwargs))
            return (SimpleNamespace(id=fixture["source_oigi_id"]), {})

    session = _FakeSession(
        {
            fixture["source_oigb_id"]: fixture["source_oigb"],
            **fixture["target_oigbs"],  # type: ignore[arg-type]
        }
    )
    monkeypatch.setattr(resolver_mod, "FSCommitStore", lambda: store)
    monkeypatch.setattr(resolver_mod, "OIGMaterializer", _FakeMaterializer)
    monkeypatch.setattr(
        resolver_mod,
        "resolve_object_instance_graph_identity_lane_context",
        lambda *, index: SimpleNamespace(
            projection_hash=fixture["source_oigi_projection_hash"],
            opg=SimpleNamespace(
                projection_hash=fixture["source_oigi_projection_hash"],
            ),
        ),
    )
    monkeypatch.setattr(
        resolver_mod,
        "reify_oig_session",
        lambda **_kwargs: session,
    )
    return materializer_calls


@pytest.mark.asyncio
async def test_resolve_portal_target_lane_ref_reads_committed_oigb_relationship(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _portal_fixture()
    materializer_calls = _install_fake_runtime(monkeypatch, fixture=fixture)

    result = await resolve_portal_target_lane_ref(
        index=_fake_index(),  # type: ignore[arg-type]
        source_domain_branch_id=fixture["source_branch_id"],  # type: ignore[arg-type]
        source_projection_hash=fixture["source_projection_hash"],  # type: ignore[arg-type]
        target_projection_hash="sha256:target",
    )

    target_head = fixture["heads"][
        (fixture["target_branch_id"], "sha256:target")
    ]  # type: ignore[index]
    assert result.source_object_instance_graph_id == fixture["source_oig_id"]
    assert result.source_object_instance_graph_identity_id == fixture["source_oigi_id"]
    assert result.source_object_instance_graph_branch_id == fixture["source_oigb_id"]
    assert result.relationship_id == fixture["relationships"][0].id  # type: ignore[index,union-attr]
    assert result.target_object_instance_graph_branch_id == fixture["target_oigb_id"]
    assert result.target_branch_id == fixture["target_branch_id"]
    assert result.target_projection_hash == "sha256:target"
    assert result.target_head_commit_id == target_head["commit_id"]
    assert (
        result.target_object_instance_graph_id
        == target_head["object_instance_graph_id"]
    )
    assert result.target_root_object_id == target_head["root_object_id"]
    assert result.target_graph_hash_post == target_head["graph_hash_post"]
    assert materializer_calls[0]["branch_id"] == fixture["source_oig_id"]
    assert materializer_calls[0]["commit_id"] == fixture["source_oigi_commit_id"]
    assert materializer_calls[0]["oig_id"] == fixture["source_oigi_id"]


@pytest.mark.asyncio
async def test_resolve_portal_target_lane_ref_uses_explicit_cross_store_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _portal_fixture()
    source_head_keys = {
        (
            fixture["source_branch_id"],
            fixture["source_projection_hash"],
        ),
        (
            fixture["source_oig_id"],
            fixture["source_oigi_projection_hash"],
        ),
    }
    source_store = _FakeCommitStore(
        {
            key: head
            for key, head in fixture["heads"].items()  # type: ignore[union-attr]
            if key in source_head_keys
        }
    )
    target_store = _FakeCommitStore(
        {
            key: head
            for key, head in fixture["heads"].items()  # type: ignore[union-attr]
            if key not in source_head_keys
        }
    )

    class _FakeMaterializer:
        def __init__(self, *, commits: object) -> None:
            assert commits is source_store

        async def get(self, **_kwargs: object):
            return (SimpleNamespace(id=fixture["source_oigi_id"]), {})

    session = _FakeSession(
        {
            fixture["source_oigb_id"]: fixture["source_oigb"],
            **fixture["target_oigbs"],  # type: ignore[arg-type]
        }
    )
    monkeypatch.setattr(resolver_mod, "OIGMaterializer", _FakeMaterializer)
    monkeypatch.setattr(
        resolver_mod,
        "resolve_object_instance_graph_identity_lane_context",
        lambda *, index: SimpleNamespace(
            projection_hash=fixture["source_oigi_projection_hash"],
            opg=SimpleNamespace(
                projection_hash=fixture["source_oigi_projection_hash"],
            ),
        ),
    )
    monkeypatch.setattr(
        resolver_mod,
        "reify_oig_session",
        lambda **_kwargs: session,
    )

    result = await resolve_portal_target_lane_ref(
        index=_fake_index(),  # type: ignore[arg-type]
        source_domain_branch_id=fixture["source_branch_id"],  # type: ignore[arg-type]
        source_projection_hash=fixture["source_projection_hash"],  # type: ignore[arg-type]
        target_projection_hash="sha256:target",
        source_store=source_store,  # type: ignore[arg-type]
        target_store=target_store,  # type: ignore[arg-type]
    )

    assert result.source_object_instance_graph_id == fixture["source_oig_id"]
    assert result.target_branch_id == fixture["target_branch_id"]
    assert (
        result.target_head_commit_id
        == fixture["heads"][  # type: ignore[index]
            (fixture["target_branch_id"], "sha256:target")
        ]["commit_id"]
    )


@pytest.mark.asyncio
async def test_resolve_portal_target_lane_refs_returns_committed_catalog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _portal_fixture()
    second_branch_id = uuid4()
    second_oigb_id = stable_object_instance_graph_branch_id(
        object_instance_graph_identity_id=fixture["source_oigi_id"],  # type: ignore[arg-type]
        branch_id=second_branch_id,
    )
    second_head_commit_id = uuid4()
    second_lane = SimpleNamespace(
        id=uuid4(),
        branch_id=second_branch_id,
        lane_hash="sha256:target",
        head_commit_id=second_head_commit_id,
    )
    second_oigb = SimpleNamespace(
        id=second_oigb_id,
        branch_id=second_branch_id,
        object_instance_graph_lanes=[
            SimpleNamespace(id=uuid4(), lane_id=second_lane.id, lane=second_lane)
        ],
    )
    second_relationship = SimpleNamespace(
        id=uuid4(),
        object_instance_graph_branch_id=fixture["source_oigb_id"],
        target_object_instance_graph_branch_id=second_oigb_id,
        target_object_instance_graph_branch=second_oigb,
    )
    fixture["source_oigb"].object_instance_graph_branch_relationships.append(  # type: ignore[union-attr]
        second_relationship
    )
    fixture["target_oigbs"][second_oigb_id] = second_oigb  # type: ignore[index]
    fixture["heads"][(second_branch_id, "sha256:target")] = {  # type: ignore[index]
        "commit_id": second_head_commit_id,
        "object_instance_graph_id": uuid4(),
        "root_object_id": uuid4(),
        "graph_hash_post": "sha256:second-target-post",
    }
    _install_fake_runtime(monkeypatch, fixture=fixture)

    results = await resolve_portal_target_lane_refs(
        index=_fake_index(),  # type: ignore[arg-type]
        source_domain_branch_id=fixture["source_branch_id"],  # type: ignore[arg-type]
        source_projection_hash=fixture["source_projection_hash"],  # type: ignore[arg-type]
        target_projection_hash="sha256:target",
    )

    assert len(results) == 2
    assert {result.target_branch_id for result in results} == {
        fixture["target_branch_id"],
        second_branch_id,
    }
    assert [
        (result.target_projection_hash, str(result.target_branch_id))
        for result in results
    ] == sorted(
        (result.target_projection_hash, str(result.target_branch_id))
        for result in results
    )
    second_result = next(
        result for result in results if result.target_branch_id == second_branch_id
    )
    assert second_result.relationship_id == second_relationship.id
    assert second_result.target_head_commit_id == second_head_commit_id


@pytest.mark.asyncio
async def test_resolve_portal_target_lane_ref_still_rejects_catalog_ambiguity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _portal_fixture(relationship_count=2)
    _install_fake_runtime(monkeypatch, fixture=fixture)

    with pytest.raises(
        RuntimeError,
        match="Ambiguous committed portal target lane relationships",
    ):
        await resolve_portal_target_lane_ref(
            index=_fake_index(),  # type: ignore[arg-type]
            source_domain_branch_id=fixture["source_branch_id"],  # type: ignore[arg-type]
            source_projection_hash=fixture["source_projection_hash"],  # type: ignore[arg-type]
            target_projection_hash="sha256:target",
        )


@pytest.mark.asyncio
async def test_resolve_portal_target_lane_ref_for_object_selects_matching_relationship(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target_object_id = uuid4()
    target_class_config_id = uuid4()
    fixture = _portal_fixture(target_root_object_id=uuid4())

    second_branch_id = uuid4()
    second_oigb_id = stable_object_instance_graph_branch_id(
        object_instance_graph_identity_id=fixture["source_oigi_id"],  # type: ignore[arg-type]
        branch_id=second_branch_id,
    )
    second_lane = SimpleNamespace(
        id=uuid4(),
        branch_id=second_branch_id,
        lane_hash="sha256:target",
        head_commit_id=uuid4(),
    )
    second_oigb = SimpleNamespace(
        id=second_oigb_id,
        branch_id=second_branch_id,
        object_instance_graph_lanes=[
            SimpleNamespace(id=uuid4(), lane_id=second_lane.id, lane=second_lane)
        ],
    )
    second_relationship = SimpleNamespace(
        id=uuid4(),
        object_instance_graph_branch_id=fixture["source_oigb_id"],
        target_object_instance_graph_branch_id=second_oigb_id,
        target_object_instance_graph_branch=second_oigb,
    )
    fixture["source_oigb"].object_instance_graph_branch_relationships.append(  # type: ignore[union-attr]
        second_relationship
    )
    fixture["target_oigbs"][second_oigb_id] = second_oigb  # type: ignore[index]
    fixture["heads"][(second_branch_id, "sha256:target")] = {  # type: ignore[index]
        "commit_id": second_lane.head_commit_id,
        "object_instance_graph_id": uuid4(),
        "root_object_id": target_object_id,
        "graph_hash_post": "sha256:second-target-post",
    }
    _install_fake_runtime(monkeypatch, fixture=fixture)

    result = await resolve_portal_target_lane_ref_for_object(
        index=_fake_index(),  # type: ignore[arg-type]
        source_domain_branch_id=fixture["source_branch_id"],  # type: ignore[arg-type]
        source_projection_hash=fixture["source_projection_hash"],  # type: ignore[arg-type]
        target_projection_hash="sha256:target",
        target_class_config_id=target_class_config_id,
        target_object_id=target_object_id,
    )

    assert result.relationship_id == second_relationship.id
    assert result.target_branch_id == second_branch_id
    assert result.target_root_object_id == target_object_id


@pytest.mark.asyncio
async def test_ensure_portal_target_lane_ref_for_object_attaches_in_meta(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target_object_id = uuid4()
    target_class_config_id = uuid4()
    fixture = _portal_fixture(
        relationship_count=0,
        target_root_object_id=target_object_id,
    )
    _install_fake_runtime(monkeypatch, fixture=fixture)
    attach_calls: list[dict[str, object]] = []

    async def _fake_attach_oigb_relationship(**kwargs: object) -> None:
        attach_calls.append(dict(kwargs))
        fixture["source_oigb"].object_instance_graph_branch_relationships.append(  # type: ignore[union-attr]
            SimpleNamespace(
                id=uuid4(),
                object_instance_graph_branch_id=fixture["source_oigb_id"],
                target_object_instance_graph_branch_id=fixture["target_oigb_id"],
                target_object_instance_graph_branch=fixture["target_oigb"],
            )
        )

    monkeypatch.setattr(
        resolver_mod,
        "attach_oigb_relationship",
        _fake_attach_oigb_relationship,
    )

    result = await ensure_portal_target_lane_ref_for_object(
        index=_fake_index(),  # type: ignore[arg-type]
        author_id=uuid4(),
        source_domain_branch_id=fixture["source_branch_id"],  # type: ignore[arg-type]
        source_projection_hash=fixture["source_projection_hash"],  # type: ignore[arg-type]
        target_projection_hash="sha256:target",
        target_class_config_id=target_class_config_id,
        target_object_id=target_object_id,
    )

    assert result.target_branch_id == fixture["target_branch_id"]
    assert result.target_projection_hash == "sha256:target"
    assert result.target_root_object_id == target_object_id
    assert len(attach_calls) == 1
    assert attach_calls[0]["source_domain_branch_id"] == fixture["source_branch_id"]
    assert (
        attach_calls[0]["source_projection_hash"] == fixture["source_projection_hash"]
    )
    assert attach_calls[0]["target_domain_branch_id"] == fixture["target_branch_id"]
    assert attach_calls[0]["target_projection_hash"] == "sha256:target"


@pytest.mark.asyncio
async def test_resolve_portal_target_branch_ref_for_object_derives_target_branch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_branch_id = uuid4()
    source_projection_hash = "sha256:source"
    source_oig_id = uuid4()
    target_projection_hash = "sha256:target"
    target_opgi_id = uuid4()
    target_object_id = uuid4()
    store = _FakeCommitStore(
        {
            (source_branch_id, source_projection_hash): {
                "object_instance_graph_id": source_oig_id,
            }
        }
    )
    monkeypatch.setattr(resolver_mod, "FSCommitStore", lambda: store)
    monkeypatch.setattr(
        resolver_mod,
        "resolve_meta_graph_ocgi_opgi",
        lambda *, index, projection_hash: (
            None,
            SimpleNamespace(id=target_opgi_id),
        ),
    )

    result = await resolve_portal_target_branch_ref_for_object(
        index=_fake_index(),  # type: ignore[arg-type]
        source_domain_branch_id=source_branch_id,
        source_projection_hash=source_projection_hash,
        target_projection_hash=target_projection_hash,
        target_object_id=target_object_id,
    )

    assert result.source_object_instance_graph_id == source_oig_id
    assert result.target_object_projection_graph_identity_id == target_opgi_id
    assert result.target_object_id == target_object_id
    assert result.target_projection_hash == target_projection_hash
    assert result.target_branch_id == stable_portal_target_branch_id(
        object_instance_graph_id=source_oig_id,
        object_projection_graph_identity_id=target_opgi_id,
        target_object_id=target_object_id,
    )


@pytest.mark.asyncio
async def test_attach_portal_target_branch_relationship_for_object_attaches_in_meta(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_branch_id = uuid4()
    source_projection_hash = "sha256:source"
    source_oig_id = uuid4()
    target_projection_hash = "sha256:target"
    target_opgi_id = uuid4()
    target_object_id = uuid4()
    source_store = _FakeCommitStore({})
    target_store = _FakeCommitStore({})
    expected_branch_id = stable_portal_target_branch_id(
        object_instance_graph_id=source_oig_id,
        object_projection_graph_identity_id=target_opgi_id,
        target_object_id=target_object_id,
    )
    attach_calls: list[dict[str, object]] = []

    monkeypatch.setattr(
        resolver_mod,
        "resolve_meta_graph_ocgi_opgi",
        lambda *, index, projection_hash: (
            None,
            SimpleNamespace(id=target_opgi_id),
        ),
    )

    async def _fake_attach_oigb_relationship(**kwargs: object) -> None:
        attach_calls.append(dict(kwargs))

    monkeypatch.setattr(
        resolver_mod,
        "attach_oigb_relationship",
        _fake_attach_oigb_relationship,
    )

    result = await attach_portal_target_branch_relationship_for_object(
        index=_fake_index(),  # type: ignore[arg-type]
        author_id=uuid4(),
        source_domain_branch_id=source_branch_id,
        source_projection_hash=source_projection_hash,
        source_object_instance_graph_id=source_oig_id,
        target_projection_hash=target_projection_hash,
        target_object_id=target_object_id,
        target_domain_branch_id=expected_branch_id,
        source_store=source_store,  # type: ignore[arg-type]
        target_store=target_store,  # type: ignore[arg-type]
    )

    assert result.target_branch_id == expected_branch_id
    assert len(attach_calls) == 1
    assert attach_calls[0]["source_domain_branch_id"] == source_branch_id
    assert attach_calls[0]["source_projection_hash"] == source_projection_hash
    assert attach_calls[0]["target_domain_branch_id"] == expected_branch_id
    assert attach_calls[0]["target_projection_hash"] == target_projection_hash
    assert attach_calls[0]["source_store"] is source_store
    assert attach_calls[0]["target_store"] is target_store


@pytest.mark.asyncio
async def test_attach_portal_target_branch_relationship_for_object_fails_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_oig_id = uuid4()
    target_opgi_id = uuid4()
    monkeypatch.setattr(
        resolver_mod,
        "resolve_meta_graph_ocgi_opgi",
        lambda *, index, projection_hash: (
            None,
            SimpleNamespace(id=target_opgi_id),
        ),
    )

    with pytest.raises(RuntimeError, match="Portal target branch mismatch"):
        await attach_portal_target_branch_relationship_for_object(
            index=_fake_index(),  # type: ignore[arg-type]
            author_id=uuid4(),
            source_domain_branch_id=uuid4(),
            source_projection_hash="sha256:source",
            source_object_instance_graph_id=source_oig_id,
            target_projection_hash="sha256:target",
            target_object_id=uuid4(),
            target_domain_branch_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_resolve_portal_target_lane_ref_fails_without_relationship(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _portal_fixture(relationship_count=0)
    _install_fake_runtime(monkeypatch, fixture=fixture)

    with pytest.raises(RuntimeError, match="No committed portal target lane"):
        await resolve_portal_target_lane_ref(
            index=_fake_index(),  # type: ignore[arg-type]
            source_domain_branch_id=fixture["source_branch_id"],  # type: ignore[arg-type]
            source_projection_hash=fixture["source_projection_hash"],  # type: ignore[arg-type]
        )


@pytest.mark.asyncio
async def test_resolve_portal_target_lane_ref_accepts_shallow_lane_head(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _portal_fixture(include_lane_head_commit_id=False)
    _install_fake_runtime(monkeypatch, fixture=fixture)

    result = await resolve_portal_target_lane_ref(
        index=_fake_index(),  # type: ignore[arg-type]
        source_domain_branch_id=fixture["source_branch_id"],  # type: ignore[arg-type]
        source_projection_hash=fixture["source_projection_hash"],  # type: ignore[arg-type]
        target_projection_hash="sha256:target",
    )

    target_head = fixture["heads"][
        (fixture["target_branch_id"], "sha256:target")
    ]  # type: ignore[index]
    assert result.target_head_commit_id == target_head["commit_id"]


@pytest.mark.asyncio
async def test_resolve_portal_target_lane_ref_fails_on_ambiguous_target_lanes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _portal_fixture(target_lane_count=2)
    _install_fake_runtime(monkeypatch, fixture=fixture)

    with pytest.raises(RuntimeError, match="Ambiguous committed portal target"):
        await resolve_portal_target_lane_ref(
            index=_fake_index(),  # type: ignore[arg-type]
            source_domain_branch_id=fixture["source_branch_id"],  # type: ignore[arg-type]
            source_projection_hash=fixture["source_projection_hash"],  # type: ignore[arg-type]
        )
