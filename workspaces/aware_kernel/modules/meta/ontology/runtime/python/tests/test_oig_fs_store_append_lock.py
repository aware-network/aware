from __future__ import annotations

import threading
from queue import Queue
from uuid import UUID, uuid4

from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as Kind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
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
    build_object_instance_graph_from_class_instances,
)
from aware_meta.graph.instance.commit.builder import build_object_instance_graph_commit
from aware_meta.graph.instance.commit.fs_store import FSCommitStore
from aware_meta.test_support import (
    make_attribute_config,
    make_class_attribute_edge,
    make_class_config,
    make_rooted_object_instance_graph,
    test_class_fqn,
)


_USER_FQN = test_class_fqn("User")
_TEST_OIGI_ID = uuid4()


def _primitive_desc() -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(kind=Kind.primitive, child_links=[])


def _make_ocg_and_opg(
    *, name_cfg: AttributeConfig
) -> tuple[ObjectConfigGraph, ObjectProjectionGraph, ClassConfig]:
    user_cc = make_class_config(
        "User", class_fqn=_USER_FQN, class_config_attribute_configs=[]
    )
    user_cc.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=user_cc.id,
            attribute_config=name_cfg,
            name=name_cfg.name,
            position=0,
        ),
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
            class_config_id=user_cc.id,
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


def test_fs_store_append_is_atomic_under_concurrent_writers(
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

    branch_id = uuid4()
    graph_id: UUID = uuid4()
    user_id = uuid4()

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

    ci1 = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, name="a"),
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
        source=User(id=user_id, name="b"),
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

    ci3 = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, name="c"),
    )
    g3 = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg.id,
        object_projection_graph_id=opg.id,
        root_class_instance=ci3,
        class_instances=[ci3],
        class_instance_relationships=[],
        oig_id=graph_id,
    )

    c0 = build_object_instance_graph_commit(
        old=g0,
        new=g1,
        object_projection_graph=opg,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        branch_id=branch_id,
        author_id=uuid4(),
        commit_id=uuid4(),
    )
    assert c0 is not None
    c1 = build_object_instance_graph_commit(
        old=g1,
        new=g2,
        object_projection_graph=opg,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        branch_id=branch_id,
        author_id=uuid4(),
        parent_commit_id=c0.commit.id,
        commit_id=uuid4(),
    )
    assert c1 is not None
    c2 = build_object_instance_graph_commit(
        old=g1,
        new=g3,
        object_projection_graph=opg,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        branch_id=branch_id,
        author_id=uuid4(),
        parent_commit_id=c0.commit.id,
        commit_id=uuid4(),
    )
    assert c2 is not None

    store = FSCommitStore()

    import anyio

    async def _append(commit) -> None:
        await store.append(
            branch_id=branch_id, projection_hash=opg.projection_hash, commit=commit
        )

    anyio.run(_append, c0)

    barrier = threading.Barrier(3)
    results: "Queue[tuple[str, UUID, str | None]]" = Queue()

    def _worker(commit) -> None:
        try:
            barrier.wait()
            anyio.run(_append, commit)
            results.put(("ok", commit.commit.id, None))
        except Exception as e:
            results.put(("err", commit.commit.id, str(e)))

    t1 = threading.Thread(target=_worker, args=(c1,), daemon=True)
    t2 = threading.Thread(target=_worker, args=(c2,), daemon=True)
    t1.start()
    t2.start()
    barrier.wait()
    t1.join(timeout=5)
    t2.join(timeout=5)

    out = [results.get_nowait() for _ in range(2)]
    oks = [x for x in out if x[0] == "ok"]
    errs = [x for x in out if x[0] == "err"]
    assert len(oks) == 1
    assert len(errs) == 1

    winner = oks[0][1]
    loser = errs[0][1]

    lane_dir = tmp_path / ".aware" / "oig" / str(branch_id) / opg.projection_hash
    commits_dir = lane_dir / "commits"
    assert (commits_dir / f"{winner}.json").exists()
    assert not (commits_dir / f"{loser}.json").exists()

    head = (lane_dir / "HEAD.json").read_text()
    assert str(winner) in head
