from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import pytest

from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as Kind,
    AttributeTypeDescriptorRole as Role,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_link import (
    AttributeTypeDescriptorLink,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_attribute import (
    ClassConfigRelationshipAttribute,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipType,
)
from aware_meta_ontology.class_.class_instance_relationship import (
    ClassInstanceRelationship,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_enums import (
    ObjectProjectionGraphNodeSelection,
)
from aware_meta_ontology.graph.projection.object_projection_graph_node import (
    ObjectProjectionGraphNode,
)
from aware_code_ontology.code.code_enums import CodeLanguage

from aware_meta.class_.instance.builder import build_class_instance
from aware_meta.graph.instance.builder import (
    build_rooted_object_instance_graph_base,
    build_object_instance_graph_from_class_instances,
)
from aware_meta.graph.instance.apply import apply_object_instance_graph_changes
from aware_meta.graph.instance.commit.builder import (
    build_object_instance_graph_commit,
    build_object_instance_graph_commit_from_changes,
)
from aware_meta.graph.instance.commit.hash_contract import compute_oig_lane_hash_state
from aware_meta.graph.instance.commit.fs_store import FSCommitStore, FSSnapshotStore
from aware_meta.graph.instance.commit.materializer import (
    MaterializerPostHashMismatchError,
    OIGMaterializer,
)
from aware_meta.graph.instance.diff import (
    build_object_instance_graph_seed_changes,
    diff_object_instance_graph_changes,
)
from aware_meta.graph.instance.hash import compute_hash
from aware_meta.graph.instance.index import build_index
from aware_meta.graph.config.lane.delta_support import (
    strip_volatile_source_reference_attrs_from_oig,
)
from aware_meta.test_support import (
    make_attribute_config,
    make_class_attribute_edge,
    make_class_config,
    make_rooted_object_instance_graph,
    test_class_fqn,
)


_USER_FQN = test_class_fqn("User")
_TEST_OIGI_ID = uuid4()


class _CountingSnapshotStore(FSSnapshotStore):
    def __init__(self) -> None:
        super().__init__()
        self.put_count = 0

    async def put(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        oig: ObjectInstanceGraph,
        indexes: dict[str, Any],
    ) -> None:
        self.put_count += 1
        await super().put(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            oig=oig,
            indexes=indexes,
        )


def _primitive_desc() -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(kind=Kind.primitive, child_links=[])


def _list_of_primitives_desc() -> AttributeTypeDescriptor:
    element = _primitive_desc()
    parent = AttributeTypeDescriptor(
        kind=Kind.collection,
        collection_kind=AttributeCollectionType.list,
        child_links=[],
    )
    parent.child_links.append(
        AttributeTypeDescriptorLink(
            attribute_type_descriptor_id=parent.id,
            child=element,
            child_id=element.id,
            role=Role.element,
        )
    )
    return parent


def _mapping_of_primitives_desc() -> AttributeTypeDescriptor:
    key = _primitive_desc()
    value = _primitive_desc()
    parent = AttributeTypeDescriptor(kind=Kind.mapping, child_links=[])
    parent.child_links.append(
        AttributeTypeDescriptorLink(
            attribute_type_descriptor_id=parent.id,
            child=key,
            child_id=key.id,
            role=Role.key,
        )
    )
    parent.child_links.append(
        AttributeTypeDescriptorLink(
            attribute_type_descriptor_id=parent.id,
            child=value,
            child_id=value.id,
            role=Role.value_,
        )
    )
    return parent


def _make_ocg_and_opg(
    *,
    name_cfg: AttributeConfig,
    extra_attribute_configs: list[AttributeConfig] | None = None,
) -> tuple[ObjectConfigGraph, ObjectProjectionGraph, ClassConfig]:
    user_cc = make_class_config(
        "User", class_fqn=_USER_FQN, class_config_attribute_configs=[]
    )
    attribute_configs = [name_cfg, *(extra_attribute_configs or [])]
    user_cc.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=user_cc.id,
            attribute_config=attribute_config,
            name=attribute_config.name,
            position=position,
        )
        for position, attribute_config in enumerate(attribute_configs)
    ]

    ocg = ObjectConfigGraph(
        name="test",
        description=None,
        hash="0",
        fqn_prefix="test",
        language=CodeLanguage.python,
        object_config_graph_nodes=[],
    )
    ocg.object_config_graph_nodes = [
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.class_,
            node_key=user_cc.class_fqn,
            class_config=user_cc,
            object_config_graph_id=ocg.id,
        ),
    ]

    opg = ObjectProjectionGraph(
        name="test-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash="lane",
        supports_virtual_build=True,
        object_config_graph_id=ocg.id,
        object_projection_graph_nodes=[],
        object_projection_graph_edges=[],
        object_projection_graph_relationships=[],
    )
    opg.object_projection_graph_nodes = [
        ObjectProjectionGraphNode(
            class_config_id=user_cc.id,
            object_projection_graph_id=opg.id,
            is_root=True,
            selection=ObjectProjectionGraphNodeSelection.one,
        ),
    ]

    return ocg, opg, user_cc


def test_oig_commit_roundtrip_materializer(tmp_path, monkeypatch) -> None:
    # Ensure FS commit/snapshot stores write under the temp root (not the repo).
    (tmp_path / ".aware").mkdir()
    monkeypatch.setenv("AWARE_ROOT", str(tmp_path))

    name_cfg = make_attribute_config(
        owner_key=_USER_FQN,
        name="name",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    ocg, opg, user_cc = _make_ocg_and_opg(name_cfg=name_cfg)

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        name: str

    author_id = uuid4()
    user_id: UUID = uuid4()
    graph_id: UUID = uuid4()

    # Base (empty) lane state
    g0 = make_rooted_object_instance_graph(
        object_config_graph=ocg,
        object_projection_graph=opg,
        root_source_object_id=user_id,
        root_class_config_id=user_cc.id,
        oig_id=graph_id,
        key="g",
        name="g",
        description="d",
    )

    # First state: CREATE user
    u1 = User(id=user_id, name="a")
    ci1 = build_class_instance(
        object_instance_graph_id=graph_id, class_config=user_cc, source=u1
    )
    g1 = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg.id,
        object_projection_graph_id=opg.id,
        root_class_instance=ci1,
        class_instances=[ci1],
        class_instance_relationships=[],
        oig_id=graph_id,
    )

    # Second state: UPDATE user.name
    u2 = User(id=user_id, name="b")
    ci2 = build_class_instance(
        object_instance_graph_id=graph_id, class_config=user_cc, source=u2
    )
    g2 = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg.id,
        object_projection_graph_id=opg.id,
        root_class_instance=ci2,
        class_instances=[ci2],
        class_instance_relationships=[],
        oig_id=graph_id,
    )

    # Build commits
    branch_id = uuid4()
    c1 = build_object_instance_graph_commit(
        old=g0,
        new=g1,
        branch_id=branch_id,
        object_projection_graph=opg,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        author_id=author_id,
    )
    assert c1 is not None
    c2 = build_object_instance_graph_commit(
        old=g1,
        new=g2,
        branch_id=branch_id,
        object_projection_graph=opg,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        author_id=author_id,
        parent_commit_id=c1.commit.id,
    )
    assert c2 is not None

    # Ensure the commit payload is fully delta-driven (no exclude=True holes).
    payload = c2.model_dump(mode="json", exclude_none=True)
    assert payload["object_instance_graph_changes"]
    assert (
        "change_deltas"
        in payload["object_instance_graph_changes"][0]["class_instance_changes"][0][
            "change"
        ]
    )

    # Persist and materialize
    store = FSCommitStore()
    mat = OIGMaterializer(commits=store)
    # Append in order (linear lane)
    import anyio

    async def _run() -> None:
        await store.append(
            branch_id=branch_id, projection_hash=opg.projection_hash, commit=c1
        )
        await store.append(
            branch_id=branch_id, projection_hash=opg.projection_hash, commit=c2
        )
        out, _ = await mat.get(
            branch_id=branch_id,
            ocg=ocg,
            opg=opg,
            commit_id=c2.commit.id,
            oig_id=graph_id,
        )
        assert out.hash == g2.hash

    anyio.run(_run)


def test_oig_materializer_reuses_exact_snapshot_without_rewriting(
    tmp_path, monkeypatch
) -> None:
    (tmp_path / ".aware").mkdir()
    monkeypatch.setenv("AWARE_ROOT", str(tmp_path))

    name_cfg = make_attribute_config(
        owner_key=_USER_FQN,
        name="name",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    ocg, opg, user_cc = _make_ocg_and_opg(name_cfg=name_cfg)

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        name: str

    author_id = uuid4()
    user_id: UUID = uuid4()
    graph_id: UUID = uuid4()
    branch_id = uuid4()

    g0 = make_rooted_object_instance_graph(
        object_config_graph=ocg,
        object_projection_graph=opg,
        root_source_object_id=user_id,
        root_class_config_id=user_cc.id,
        oig_id=graph_id,
        key="g",
        name="g",
        description="d",
    )
    ci = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, name="a"),
    )
    g1 = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg.id,
        object_projection_graph_id=opg.id,
        root_class_instance=ci,
        class_instances=[ci],
        class_instance_relationships=[],
        oig_id=graph_id,
    )
    commit = build_object_instance_graph_commit(
        old=g0,
        new=g1,
        branch_id=branch_id,
        object_projection_graph=opg,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        author_id=author_id,
    )
    assert commit is not None

    store = FSCommitStore()
    initial_materializer = OIGMaterializer(commits=store, snaps=FSSnapshotStore())
    counting_snaps = _CountingSnapshotStore()
    cached_materializer = OIGMaterializer(commits=store, snaps=counting_snaps)

    import anyio

    async def _run() -> None:
        await store.append(
            branch_id=branch_id, projection_hash=opg.projection_hash, commit=commit
        )
        materialized, _ = await initial_materializer.get(
            branch_id=branch_id,
            ocg=ocg,
            opg=opg,
            commit_id=commit.commit.id,
            oig_id=graph_id,
        )
        assert materialized.hash == g1.hash

        cached, indexes = await cached_materializer.get(
            branch_id=branch_id,
            ocg=ocg,
            opg=opg,
            commit_id=commit.commit.id,
            oig_id=graph_id,
        )

        assert cached.hash == g1.hash
        assert "instance_map" in indexes
        assert counting_snaps.put_count == 0

    anyio.run(_run)


def test_oig_seed_create_changes_apply_descriptor_value_tree() -> None:
    name_cfg = make_attribute_config(
        owner_key=_USER_FQN,
        name="name",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    payload_cfg = make_attribute_config(
        owner_key=_USER_FQN,
        name="payload",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    ocg, opg, user_cc = _make_ocg_and_opg(
        name_cfg=name_cfg,
        extra_attribute_configs=[payload_cfg],
    )

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        name: str
        payload: dict[str, object]

    user_id: UUID = uuid4()
    graph_id: UUID = uuid4()
    g0 = make_rooted_object_instance_graph(
        object_config_graph=ocg,
        object_projection_graph=opg,
        root_source_object_id=user_id,
        root_class_config_id=user_cc.id,
        oig_id=graph_id,
        key="g",
        name="g",
        description="d",
    )
    ci = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(
            id=user_id,
            name="literal",
            payload={
                "kind": "FunctionImplValueSourceLiteralPrimitive",
                "value": [1, "two"],
            },
        ),
    )
    g1 = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg.id,
        object_projection_graph_id=opg.id,
        root_class_instance=ci,
        class_instances=[ci],
        class_instance_relationships=[],
        oig_id=graph_id,
    )

    changes = build_object_instance_graph_seed_changes(
        before=g0,
        new=g1,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
    )
    candidate = g0.model_copy(deep=True)
    _ = apply_object_instance_graph_changes(
        graph=candidate,
        changes=changes,
        attribute_configs_by_id={
            name_cfg.id: name_cfg,
            payload_cfg.id: payload_cfg,
        },
        class_configs_by_id={user_cc.id: user_cc},
    )

    assert compute_hash(candidate, index=build_index(candidate)) == compute_hash(
        g1,
        index=build_index(g1),
    )


def test_oig_materializer_accepts_lane_hash_normalization_for_delta_commits(
    tmp_path,
    monkeypatch,
) -> None:
    (tmp_path / ".aware").mkdir()
    monkeypatch.setenv("AWARE_ROOT", str(tmp_path))

    name_cfg = make_attribute_config(
        owner_key=_USER_FQN,
        name="name",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    volatile_cfg = make_attribute_config(
        owner_key=_USER_FQN,
        name="code_section_annotation_id",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    schema_attribute_configs_by_id = {
        name_cfg.id: name_cfg,
        volatile_cfg.id: volatile_cfg,
    }
    ocg, opg, user_cc = _make_ocg_and_opg(
        name_cfg=name_cfg,
        extra_attribute_configs=[volatile_cfg],
    )

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        name: str
        code_section_annotation_id: str

    author_id = uuid4()
    user_id: UUID = uuid4()
    graph_id: UUID = uuid4()
    branch_id = uuid4()

    g_empty = make_rooted_object_instance_graph(
        object_config_graph=ocg,
        object_projection_graph=opg,
        root_source_object_id=user_id,
        root_class_config_id=user_cc.id,
        oig_id=graph_id,
        key="g",
        name="g",
        description="d",
    )

    ci1 = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, name="a", code_section_annotation_id="ann-1"),
    )
    g1 = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg.id,
        object_projection_graph_id=opg.id,
        root_class_instance=ci1,
        class_instances=[ci1],
        class_instance_relationships=[],
        oig_id=graph_id,
    )

    ci2 = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, name="b", code_section_annotation_id="ann-2"),
    )
    g2 = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg.id,
        object_projection_graph_id=opg.id,
        root_class_instance=ci2,
        class_instances=[ci2],
        class_instance_relationships=[],
        oig_id=graph_id,
    )

    seed_commit = build_object_instance_graph_commit(
        old=g_empty,
        new=g1,
        branch_id=branch_id,
        object_projection_graph=opg,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        author_id=author_id,
    )
    assert seed_commit is not None

    g1_lane = g1.model_copy(deep=True)
    g2_lane = g2.model_copy(deep=True)
    _ = strip_volatile_source_reference_attrs_from_oig(
        graph=g1_lane,
        schema_attribute_configs_by_id=schema_attribute_configs_by_id,
    )
    _ = strip_volatile_source_reference_attrs_from_oig(
        graph=g2_lane,
        schema_attribute_configs_by_id=schema_attribute_configs_by_id,
    )
    delta_changes = diff_object_instance_graph_changes(
        old=g1_lane,
        new=g2_lane,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
    )
    lane_hash_post = compute_oig_lane_hash_state(
        graph=g2,
        schema_attribute_configs_by_id=schema_attribute_configs_by_id,
    ).lane_hash
    delta_commit = build_object_instance_graph_commit_from_changes(
        before_oig=g1,
        changes=delta_changes,
        branch_id=branch_id,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        object_instance_graph_id=graph_id,
        projection_hash=opg.projection_hash,
        graph_hash_pre=seed_commit.graph_hash_post,
        graph_hash_post=lane_hash_post,
        author_id=author_id,
        parent_commit_id=seed_commit.commit.id,
    )

    store = FSCommitStore()
    mat = OIGMaterializer(commits=store)

    import anyio

    async def _run() -> None:
        await store.append(
            branch_id=branch_id, projection_hash=opg.projection_hash, commit=seed_commit
        )
        await store.append(
            branch_id=branch_id,
            projection_hash=opg.projection_hash,
            commit=delta_commit,
        )
        graph, _ = await mat.get(
            branch_id=branch_id,
            ocg=ocg,
            opg=opg,
            commit_id=delta_commit.commit.id,
            oig_id=graph_id,
            attribute_configs_by_id=schema_attribute_configs_by_id,
            class_configs_by_id={user_cc.id: user_cc},
        )
        hash_state = compute_oig_lane_hash_state(
            graph=graph,
            schema_attribute_configs_by_id=schema_attribute_configs_by_id,
        )
        assert hash_state.raw_hash != delta_commit.graph_hash_post
        assert hash_state.lane_hash == delta_commit.graph_hash_post
        assert graph.hash == delta_commit.graph_hash_post

    anyio.run(_run)


def test_oig_materializer_post_hash_mismatch_reports_lane_diagnostics(
    tmp_path, monkeypatch
) -> None:
    (tmp_path / ".aware").mkdir()
    monkeypatch.setenv("AWARE_ROOT", str(tmp_path))

    name_cfg = make_attribute_config(
        owner_key=_USER_FQN,
        name="name",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    ocg, opg, user_cc = _make_ocg_and_opg(name_cfg=name_cfg)

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        name: str

    author_id = uuid4()
    user_id: UUID = uuid4()
    graph_id: UUID = uuid4()

    g0 = make_rooted_object_instance_graph(
        object_config_graph=ocg,
        object_projection_graph=opg,
        root_source_object_id=user_id,
        root_class_config_id=user_cc.id,
        oig_id=graph_id,
        key="g",
        name="g",
        description="d",
    )

    u1 = User(id=user_id, name="a")
    ci1 = build_class_instance(
        object_instance_graph_id=graph_id, class_config=user_cc, source=u1
    )
    g1 = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg.id,
        object_projection_graph_id=opg.id,
        root_class_instance=ci1,
        class_instances=[ci1],
        class_instance_relationships=[],
        oig_id=graph_id,
    )

    branch_id = uuid4()
    c1 = build_object_instance_graph_commit(
        old=g0,
        new=g1,
        branch_id=branch_id,
        object_projection_graph=opg,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        author_id=author_id,
    )
    assert c1 is not None
    broken = c1.model_copy(update={"graph_hash_post": "0" * 64})

    store = FSCommitStore()
    mat = OIGMaterializer(commits=store)

    import anyio

    async def _run() -> None:
        await store.append(
            branch_id=branch_id, projection_hash=opg.projection_hash, commit=broken
        )
        with pytest.raises(
            MaterializerPostHashMismatchError, match="Materializer post-hash mismatch"
        ) as exc:
            await mat.get(
                branch_id=branch_id,
                ocg=ocg,
                opg=opg,
                commit_id=broken.commit.id,
                oig_id=graph_id,
            )
        error = exc.value
        details = error.details
        message = str(error)
        assert details.branch_id == branch_id
        assert details.projection_hash == opg.projection_hash
        assert details.commit_id == broken.commit.id
        assert details.change_tree.oig_changes >= 1
        assert details.change_tree.class_instance_changes >= 1
        assert details.change_tree.attribute_changes >= 1
        assert details.change_tree.change_deltas >= 1
        descriptor_count = details.semantics.get("descriptor_count")
        assert isinstance(descriptor_count, int)
        assert descriptor_count >= 1
        assert f"branch_id={branch_id}" in message
        assert f"projection_hash={opg.projection_hash}" in message
        assert f"commit={broken.commit.id}" in message
        assert "oig_changes=" in message
        assert "class_instance_changes=" in message
        assert "attribute_changes=" in message
        assert "change_deltas=" in message
        assert "descriptor_count=" in message
        assert (
            "hint=lane_commit_not_replayable_under_current_materializer_contract"
            in message
        )

    anyio.run(_run)


def test_oig_commit_roundtrip_materializer_list_append(tmp_path, monkeypatch) -> None:
    (tmp_path / ".aware").mkdir()
    monkeypatch.setenv("AWARE_ROOT", str(tmp_path))

    items_cfg = make_attribute_config(
        owner_key=_USER_FQN,
        name="items",
        is_required=True,
        type_descriptor=_list_of_primitives_desc(),
    )
    ocg, opg, user_cc = _make_ocg_and_opg(name_cfg=items_cfg)

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        items: list[int]

    author_id = uuid4()
    user_id: UUID = uuid4()
    graph_id: UUID = uuid4()

    g0 = make_rooted_object_instance_graph(
        object_config_graph=ocg,
        object_projection_graph=opg,
        root_source_object_id=user_id,
        root_class_config_id=user_cc.id,
        oig_id=graph_id,
        key="g",
        name="g",
        description="d",
    )

    u1 = User(id=user_id, items=[1])
    ci1 = build_class_instance(
        object_instance_graph_id=graph_id, class_config=user_cc, source=u1
    )
    g1 = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg.id,
        object_projection_graph_id=opg.id,
        root_class_instance=ci1,
        class_instances=[ci1],
        class_instance_relationships=[],
        oig_id=graph_id,
    )

    u2 = User(id=user_id, items=[1, 2])
    ci2 = build_class_instance(
        object_instance_graph_id=graph_id, class_config=user_cc, source=u2
    )
    g2 = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg.id,
        object_projection_graph_id=opg.id,
        root_class_instance=ci2,
        class_instances=[ci2],
        class_instance_relationships=[],
        oig_id=graph_id,
    )

    branch_id = uuid4()
    c1 = build_object_instance_graph_commit(
        old=g0,
        new=g1,
        branch_id=branch_id,
        object_projection_graph=opg,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        author_id=author_id,
    )
    assert c1 is not None
    c2 = build_object_instance_graph_commit(
        old=g1,
        new=g2,
        branch_id=branch_id,
        object_projection_graph=opg,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        author_id=author_id,
        parent_commit_id=c1.commit.id,
    )
    assert c2 is not None

    # Ensure the payload includes a value-tree link change (list append).
    payload = c2.model_dump(mode="json", exclude_none=True)
    link_changes = payload["object_instance_graph_changes"][0][
        "class_instance_changes"
    ][0]["attribute_changes"][0]["value_root_change"]["attribute_value_link_changes"]
    assert link_changes

    branch_id = uuid4()
    store = FSCommitStore()
    mat = OIGMaterializer(commits=store)

    import anyio

    async def _run() -> None:
        await store.append(
            branch_id=branch_id, projection_hash=opg.projection_hash, commit=c1
        )
        await store.append(
            branch_id=branch_id, projection_hash=opg.projection_hash, commit=c2
        )
        out, _ = await mat.get(
            branch_id=branch_id,
            ocg=ocg,
            opg=opg,
            commit_id=c2.commit.id,
            oig_id=graph_id,
        )
        assert out.hash == g2.hash

    anyio.run(_run)


def test_oig_commit_roundtrip_materializer_mapping_value_update(
    tmp_path, monkeypatch
) -> None:
    (tmp_path / ".aware").mkdir()
    monkeypatch.setenv("AWARE_ROOT", str(tmp_path))

    props_cfg = make_attribute_config(
        owner_key=_USER_FQN,
        name="props",
        is_required=True,
        type_descriptor=_mapping_of_primitives_desc(),
    )
    ocg, opg, user_cc = _make_ocg_and_opg(name_cfg=props_cfg)

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        props: dict[str, str]

    author_id = uuid4()
    user_id: UUID = uuid4()
    graph_id: UUID = uuid4()

    g0 = make_rooted_object_instance_graph(
        object_config_graph=ocg,
        object_projection_graph=opg,
        root_source_object_id=user_id,
        root_class_config_id=user_cc.id,
        oig_id=graph_id,
        key="g",
        name="g",
        description="d",
    )

    u1 = User(id=user_id, props={"k": "v1"})
    ci1 = build_class_instance(
        object_instance_graph_id=graph_id, class_config=user_cc, source=u1
    )
    g1 = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg.id,
        object_projection_graph_id=opg.id,
        root_class_instance=ci1,
        class_instances=[ci1],
        class_instance_relationships=[],
        oig_id=graph_id,
    )

    u2 = User(id=user_id, props={"k": "v2"})
    ci2 = build_class_instance(
        object_instance_graph_id=graph_id, class_config=user_cc, source=u2
    )
    g2 = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg.id,
        object_projection_graph_id=opg.id,
        root_class_instance=ci2,
        class_instances=[ci2],
        class_instance_relationships=[],
        oig_id=graph_id,
    )

    branch_id = uuid4()
    c1 = build_object_instance_graph_commit(
        old=g0,
        new=g1,
        branch_id=branch_id,
        object_projection_graph=opg,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        author_id=author_id,
    )
    assert c1 is not None
    c2 = build_object_instance_graph_commit(
        old=g1,
        new=g2,
        branch_id=branch_id,
        object_projection_graph=opg,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        author_id=author_id,
        parent_commit_id=c1.commit.id,
    )
    assert c2 is not None

    store = FSCommitStore()
    mat = OIGMaterializer(commits=store)

    import anyio

    async def _run() -> None:
        await store.append(
            branch_id=branch_id, projection_hash=opg.projection_hash, commit=c1
        )
        await store.append(
            branch_id=branch_id, projection_hash=opg.projection_hash, commit=c2
        )
        out, _ = await mat.get(
            branch_id=branch_id,
            ocg=ocg,
            opg=opg,
            commit_id=c2.commit.id,
            oig_id=graph_id,
        )
        assert out.hash == g2.hash

    anyio.run(_run)


def test_oig_commit_roundtrip_materializer_relationship_create(
    tmp_path, monkeypatch
) -> None:
    (tmp_path / ".aware").mkdir()
    monkeypatch.setenv("AWARE_ROOT", str(tmp_path))

    # A --b--> B relationship.
    b_fqn = test_class_fqn("B")
    a_fqn = test_class_fqn("A")
    b_name_cfg = make_attribute_config(
        owner_key=b_fqn,
        name="name",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    b_cc = make_class_config("B", class_fqn=b_fqn, class_config_attribute_configs=[])
    b_cc.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=b_cc.id,
            attribute_config=b_name_cfg,
            name=b_name_cfg.name,
            position=0,
        ),
    ]

    a_name_cfg = make_attribute_config(
        owner_key=a_fqn,
        name="name",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    b_desc = AttributeTypeDescriptor(
        kind=Kind.class_, class_config_id=b_cc.id, child_links=[]
    )
    a_b_cfg = make_attribute_config(
        owner_key=a_fqn, name="b", is_required=False, type_descriptor=b_desc
    )
    a_cc = make_class_config(
        "A",
        class_fqn=a_fqn,
        class_config_attribute_configs=[],
        class_config_relationships=[],
    )
    a_cc.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=a_cc.id,
            attribute_config=a_name_cfg,
            name=a_name_cfg.name,
            position=0,
        ),
        make_class_attribute_edge(
            class_config_id=a_cc.id,
            attribute_config=a_b_cfg,
            name=a_b_cfg.name,
            position=1,
        ),
    ]

    rel = ClassConfigRelationship(
        relationship_key="a_b",
        relationship_type=ClassConfigRelationshipType.many_to_one,
        forward_required=False,
        forward_loading_strategy=None,
        reverse_loading_strategy=None,
        class_config_id=a_cc.id,
        target_class_config_id=b_cc.id,
        class_config_relationship_attributes=[],
    )
    rel.class_config_relationship_attributes.append(
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=rel.id,
            attribute_config_id=a_b_cfg.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        )
    )
    a_cc.class_config_relationships = [rel]

    ocg = ObjectConfigGraph(
        name="test",
        description=None,
        hash="0",
        fqn_prefix="test",
        language=CodeLanguage.python,
        object_config_graph_nodes=[],
    )
    ocg.object_config_graph_nodes = [
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.class_,
            node_key=a_cc.class_fqn,
            class_config=a_cc,
            object_config_graph_id=ocg.id,
        ),
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.class_,
            node_key=b_cc.class_fqn,
            class_config=b_cc,
            object_config_graph_id=ocg.id,
        ),
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.relationship,
            node_key=rel.relationship_key,
            class_config_relationship=rel,
            class_config_relationship_id=rel.id,
            object_config_graph_id=ocg.id,
        ),
    ]

    opg = ObjectProjectionGraph(
        name="test-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash="lane",
        supports_virtual_build=True,
        object_config_graph_id=ocg.id,
        object_projection_graph_nodes=[],
        object_projection_graph_edges=[],
        object_projection_graph_relationships=[],
    )
    opg.object_projection_graph_nodes = [
        ObjectProjectionGraphNode(
            class_config_id=a_cc.id,
            object_projection_graph_id=opg.id,
            is_root=True,
            selection=ObjectProjectionGraphNodeSelection.one,
        ),
    ]

    from aware_orm.models.base_model import BaseORMModel

    class B(BaseORMModel):
        name: str

    class A(BaseORMModel):
        name: str

    author_id = uuid4()
    a_id: UUID = uuid4()
    b_id: UUID = uuid4()
    graph_id: UUID = uuid4()

    g0 = build_rooted_object_instance_graph_base(
        key="g",
        name="g",
        description="d",
        object_config_graph_id=ocg.id,
        object_projection_graph=opg,
        root_source_object_id=a_id,
        root_class_config_id=a_cc.id,
        oig_id=graph_id,
    )

    # Base: both instances present, no relationship edge.
    ci_a1 = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=a_cc,
        source=A(id=a_id, name="a"),
    )
    ci_b1 = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=b_cc,
        source=B(id=b_id, name="b"),
    )
    g1 = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg.id,
        object_projection_graph_id=opg.id,
        root_class_instance=ci_a1,
        class_instances=[ci_a1, ci_b1],
        class_instance_relationships=[],
        oig_id=graph_id,
    )

    # Next: relationship edge appears.
    ci_a2 = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=a_cc,
        source=A(id=a_id, name="a"),
    )
    ci_b2 = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=b_cc,
        source=B(id=b_id, name="b"),
    )
    g2 = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg.id,
        object_projection_graph_id=opg.id,
        root_class_instance=ci_a2,
        class_instances=[ci_a2, ci_b2],
        class_instance_relationships=[
            ClassInstanceRelationship(
                object_instance_graph_id=graph_id,
                class_config_relationship_id=rel.id,
                source_class_instance_id=ci_a2.id,
                target_class_instance_id=ci_b2.id,
            )
        ],
        oig_id=graph_id,
    )

    branch_id = uuid4()
    c1 = build_object_instance_graph_commit(
        old=g0,
        new=g1,
        branch_id=branch_id,
        object_projection_graph=opg,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        author_id=author_id,
    )
    assert c1 is not None
    c2 = build_object_instance_graph_commit(
        old=g1,
        new=g2,
        branch_id=branch_id,
        object_projection_graph=opg,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        author_id=author_id,
        parent_commit_id=c1.commit.id,
    )
    assert c2 is not None

    store = FSCommitStore()
    mat = OIGMaterializer(commits=store)

    import anyio

    async def _run() -> None:
        await store.append(
            branch_id=branch_id, projection_hash=opg.projection_hash, commit=c1
        )
        await store.append(
            branch_id=branch_id, projection_hash=opg.projection_hash, commit=c2
        )
        out, _ = await mat.get(
            branch_id=branch_id,
            ocg=ocg,
            opg=opg,
            commit_id=c2.commit.id,
            oig_id=graph_id,
        )
        assert out.hash == g2.hash
        assert len(out.class_instance_relationships) == 1
        r = out.class_instance_relationships[0]
        assert r.class_config_relationship_id == rel.id
        assert r.source_class_instance_id == ci_a2.id
        assert r.target_class_instance_id == ci_b2.id

    anyio.run(_run)
