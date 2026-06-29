from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

import pytest
from _pytest.monkeypatch import MonkeyPatch

from aware_history_ontology.lane.lane import Lane
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as Kind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
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
from aware_meta.graph.config.lane.delta_support import (
    strip_volatile_source_reference_attrs_from_oig,
)
from aware_meta.graph.instance.builder import (
    build_object_instance_graph_from_class_instances,
)
from aware_meta.graph.instance.commit.committer import (
    FSLaneCommitter,
    LaneBeforeOigHashMismatchError,
    LaneCommitError,
    LaneHeadPreHashMismatchError,
)
from aware_meta.graph.instance.commit.hash_contract import compute_oig_lane_hash_state
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.graph.instance.diff import diff_object_instance_graph_changes
from aware_meta_ontology.stable_ids import stable_object_instance_graph_commit_id
from aware_meta.test_support import (
    make_attribute_config,
    make_class_attribute_edge,
    make_class_config,
    make_rooted_object_instance_graph,
    test_class_fqn,
)


_USER_FQN = test_class_fqn("User")
_TEST_OIGI_ID = uuid4()


def _set_aware_root(*, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    (tmp_path / ".aware").mkdir()
    monkeypatch.setenv("AWARE_ROOT", str(tmp_path))


def _read_json_object(path: Path) -> dict[str, object]:
    payload = cast(object, json.loads(path.read_text(encoding="utf-8")))
    if not isinstance(payload, dict):
        raise AssertionError(f"Expected JSON object in {path}")
    payload_mapping = cast(Mapping[object, object], payload)
    typed_payload: dict[str, object] = {}
    for key, value in payload_mapping.items():
        if isinstance(key, str):
            typed_payload[key] = value
    return typed_payload


def _primitive_desc() -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(kind=Kind.primitive, child_links=[])


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


@pytest.mark.asyncio
async def test_lane_committer_appends_and_materializes(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    _set_aware_root(tmp_path=tmp_path, monkeypatch=monkeypatch)

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
    branch_id = uuid4()
    graph_id: UUID = uuid4()
    user_id: UUID = uuid4()

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

    changes1 = diff_object_instance_graph_changes(
        old=g0,
        new=g1,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
    )
    changes2 = diff_object_instance_graph_changes(
        old=g1,
        new=g2,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
    )

    committer = FSLaneCommitter()
    c1_id = uuid4()
    c2_id = uuid4()

    lane = Lane(branch_id=branch_id, lane_hash=opg.projection_hash)

    c1 = await committer.commit(
        branch_id=branch_id,
        projection_hash=opg.projection_hash,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        object_instance_graph_id=graph_id,
        before_oig=g0,
        changes=changes1,
        graph_hash_pre=g0.hash,
        graph_hash_post=g1.hash,
        author_id=author_id,
        commit_id=c1_id,
        source_language=ocg.language,
    )
    assert c1 is not None
    assert c1.commit.id == c1_id
    assert c1.commit.commit_parents == []
    c1_perf = committer.last_commit_perf_profile_snapshot()
    assert c1_perf.get("total_ms", -1) >= 0
    assert c1_perf.get("head_resolve_ms", -1) >= 0
    assert c1_perf.get("build_commit_payload_ms", -1) >= 0
    assert c1_perf.get("validate_commit_payload_ms", -1) >= 0
    assert c1_perf.get("append_ms", -1) >= 0
    assert c1_perf.get("append_total_ms", -1) >= 0
    assert c1_perf.get("append_lock_wait_ms", -1) >= 0
    assert c1_perf.get("append_lock_hold_ms", -1) >= 0
    assert c1_perf.get("append_head_read_ms", -1) >= 0
    assert c1_perf.get("append_validation_ms", -1) >= 0
    assert c1_perf.get("append_write_commit_file_ms", -1) >= 0
    assert c1_perf.get("append_write_meta_file_ms", -1) >= 0
    assert c1_perf.get("append_write_head_ms", -1) >= 0
    assert c1_perf.get("append_dispatch_watcher_ms", -1) >= 0

    # Lane-first API is canonical for DB-backed heads later.
    c2 = await committer.commit_to_lane(
        lane=lane,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        object_instance_graph_id=graph_id,
        before_oig=g1,
        changes=changes2,
        graph_hash_pre=g1.hash,
        graph_hash_post=g2.hash,
        author_id=author_id,
        commit_id=c2_id,
        source_language=ocg.language,
    )
    assert c2 is not None
    assert c2.commit.id == c2_id
    assert len(c2.commit.commit_parents) == 1
    assert c2.commit.commit_parents[0].parent_commit_id == c1_id

    # Idempotency: re-issuing the same commit_id when it's already HEAD is a no-op.
    c2_retry = await committer.commit(
        branch_id=branch_id,
        projection_hash=opg.projection_hash,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        object_instance_graph_id=graph_id,
        before_oig=g1,
        changes=changes2,
        graph_hash_pre=g1.hash,
        graph_hash_post=g2.hash,
        author_id=author_id,
        commit_id=c2_id,
        source_language=ocg.language,
    )
    assert c2_retry is not None
    assert c2_retry.commit.id == c2_id
    c2_retry_perf = committer.last_commit_perf_profile_snapshot()
    assert c2_retry_perf.get("idempotent_head_hit", 0) == 1

    headf = (
        tmp_path / ".aware" / "oig" / str(branch_id) / opg.projection_hash / "HEAD.json"
    )
    commitf = (
        tmp_path
        / ".aware"
        / "oig"
        / str(branch_id)
        / opg.projection_hash
        / "commits"
        / f"{c2_id}.json"
    )
    stale_oigi_id = uuid4()
    stale_oig_commit_id = stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=stale_oigi_id,
        commit_id=c2_id,
    )
    stale_commit_payload = _read_json_object(commitf)
    stale_commit_payload["id"] = str(stale_oig_commit_id)
    stale_commit_payload["object_instance_graph_identity_id"] = str(stale_oigi_id)
    commitf.write_text(
        json.dumps(stale_commit_payload, separators=(",", ":"), sort_keys=True),
        encoding="utf-8",
    )
    stale_head_payload = _read_json_object(headf)
    stale_head_payload["object_instance_graph_commit_id"] = str(stale_oig_commit_id)
    headf.write_text(
        json.dumps(stale_head_payload, separators=(",", ":"), sort_keys=True),
        encoding="utf-8",
    )

    c2_repaired_retry = await committer.commit(
        branch_id=branch_id,
        projection_hash=opg.projection_hash,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        object_instance_graph_id=graph_id,
        before_oig=g1,
        changes=changes2,
        graph_hash_pre=g1.hash,
        graph_hash_post=g2.hash,
        author_id=author_id,
        commit_id=c2_id,
        source_language=ocg.language,
    )
    assert c2_repaired_retry is not None
    expected_oig_commit_id = stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        commit_id=c2_id,
    )
    assert c2_repaired_retry.id == expected_oig_commit_id
    assert c2_repaired_retry.object_instance_graph_identity_id == _TEST_OIGI_ID
    c2_repair_perf = committer.last_commit_perf_profile_snapshot()
    assert c2_repair_perf.get("idempotent_head_hit", 0) == 1
    assert c2_repair_perf.get("idempotent_repaired_commit_identity_metadata", 0) == 1

    repaired_commit_payload = _read_json_object(commitf)
    assert repaired_commit_payload["id"] == str(expected_oig_commit_id)
    assert repaired_commit_payload["object_instance_graph_identity_id"] == str(
        _TEST_OIGI_ID
    )

    # HEAD is lane-scoped and records the OIG id for fast consistency checks.
    head = _read_json_object(headf)
    assert head["commit_id"] == str(c2_id)
    assert head["object_instance_graph_id"] == str(graph_id)
    assert head["object_instance_graph_commit_id"] == str(expected_oig_commit_id)

    mat = OIGMaterializer()
    out, _ = await mat.get(
        branch_id=branch_id,
        ocg=ocg,
        opg=opg,
        commit_id=c2_id,
        oig_id=graph_id,
    )
    assert out.hash == g2.hash


@pytest.mark.asyncio
async def test_lane_committer_accepts_normalized_lane_hash_precondition(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    _set_aware_root(tmp_path=tmp_path, monkeypatch=monkeypatch)

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
    branch_id = uuid4()
    graph_id: UUID = uuid4()
    user_id: UUID = uuid4()

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

    g0_lane = g0.model_copy(deep=True)
    g1_lane = g1.model_copy(deep=True)
    _ = strip_volatile_source_reference_attrs_from_oig(
        graph=g0_lane,
        schema_attribute_configs_by_id=schema_attribute_configs_by_id,
    )
    _ = strip_volatile_source_reference_attrs_from_oig(
        graph=g1_lane,
        schema_attribute_configs_by_id=schema_attribute_configs_by_id,
    )
    changes = diff_object_instance_graph_changes(
        old=g0_lane,
        new=g1_lane,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
    )
    graph_hash_pre = compute_oig_lane_hash_state(
        graph=g0,
        schema_attribute_configs_by_id=schema_attribute_configs_by_id,
    ).lane_hash
    graph_hash_post = compute_oig_lane_hash_state(
        graph=g1,
        schema_attribute_configs_by_id=schema_attribute_configs_by_id,
    ).lane_hash

    committer = FSLaneCommitter()
    commit = await committer.commit(
        branch_id=branch_id,
        projection_hash=opg.projection_hash,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        object_instance_graph_id=graph_id,
        before_oig=g0,
        changes=changes,
        graph_hash_pre=graph_hash_pre,
        graph_hash_post=graph_hash_post,
        author_id=author_id,
        schema_attribute_configs_by_id=schema_attribute_configs_by_id,
    )

    assert commit is not None
    assert commit.graph_hash_pre == graph_hash_pre
    assert commit.graph_hash_post == graph_hash_post

    # HEAD is lane-scoped and records the OIG id for fast consistency checks.
    headf = (
        tmp_path / ".aware" / "oig" / str(branch_id) / opg.projection_hash / "HEAD.json"
    )
    head = _read_json_object(headf)
    assert head["commit_id"] == str(commit.commit.id)
    assert head["object_instance_graph_id"] == str(graph_id)

    mat = OIGMaterializer()
    out, _ = await mat.get(
        branch_id=branch_id,
        ocg=ocg,
        opg=opg,
        commit_id=commit.commit.id,
        oig_id=graph_id,
        attribute_configs_by_id=schema_attribute_configs_by_id,
        class_configs_by_id={user_cc.id: user_cc},
    )
    assert out.hash == graph_hash_post


@pytest.mark.asyncio
async def test_lane_committer_rejects_prehash_mismatch(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    _set_aware_root(tmp_path=tmp_path, monkeypatch=monkeypatch)

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
    branch_id = uuid4()
    graph_id: UUID = uuid4()
    user_id: UUID = uuid4()

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
    changes1 = diff_object_instance_graph_changes(
        old=g0,
        new=g1,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
    )

    committer = FSLaneCommitter()
    _ = await committer.commit(
        branch_id=branch_id,
        projection_hash=opg.projection_hash,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        object_instance_graph_id=graph_id,
        before_oig=g0,
        changes=changes1,
        graph_hash_pre=g0.hash,
        graph_hash_post=g1.hash,
        author_id=author_id,
        commit_id=uuid4(),
        source_language=ocg.language,
    )

    # Second commit with mismatched pre-hash should fail before touching the store.
    with pytest.raises(LaneBeforeOigHashMismatchError) as exc:
        _ = await committer.commit(
            branch_id=branch_id,
            projection_hash=opg.projection_hash,
            object_instance_graph_identity_id=_TEST_OIGI_ID,
            object_instance_graph_id=graph_id,
            before_oig=g0,
            changes=changes1,
            graph_hash_pre="wrong",
            graph_hash_post=g1.hash,
            author_id=author_id,
            commit_id=uuid4(),
            source_language=ocg.language,
        )
    assert exc.value.details.branch_id == branch_id
    assert exc.value.details.projection_hash == opg.projection_hash


@pytest.mark.asyncio
async def test_lane_committer_rejects_head_prehash_mismatch(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    _set_aware_root(tmp_path=tmp_path, monkeypatch=monkeypatch)

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
    branch_id = uuid4()
    graph_id: UUID = uuid4()
    user_id: UUID = uuid4()

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
    changes1 = diff_object_instance_graph_changes(
        old=g0,
        new=g1,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
    )

    committer = FSLaneCommitter()
    _ = await committer.commit(
        branch_id=branch_id,
        projection_hash=opg.projection_hash,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        object_instance_graph_id=graph_id,
        before_oig=g0,
        changes=changes1,
        graph_hash_pre=g0.hash,
        graph_hash_post=g1.hash,
        author_id=author_id,
        commit_id=uuid4(),
        source_language=ocg.language,
    )

    with pytest.raises(LaneHeadPreHashMismatchError) as exc:
        _ = await committer.commit(
            branch_id=branch_id,
            projection_hash=opg.projection_hash,
            object_instance_graph_identity_id=_TEST_OIGI_ID,
            object_instance_graph_id=graph_id,
            before_oig=g0,
            changes=changes1,
            graph_hash_pre=g0.hash,
            graph_hash_post=g1.hash,
            author_id=author_id,
            commit_id=uuid4(),
            source_language=ocg.language,
        )
    assert exc.value.details.head_graph_hash_post == g1.hash
    assert exc.value.details.graph_hash_pre == g0.hash


@pytest.mark.asyncio
async def test_lane_committer_rejects_malformed_head_payload(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    _set_aware_root(tmp_path=tmp_path, monkeypatch=monkeypatch)

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
    branch_id = uuid4()
    graph_id: UUID = uuid4()
    user_id: UUID = uuid4()

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
    changes1 = diff_object_instance_graph_changes(
        old=g0,
        new=g1,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
    )

    headf = (
        tmp_path / ".aware" / "oig" / str(branch_id) / opg.projection_hash / "HEAD.json"
    )
    headf.parent.mkdir(parents=True, exist_ok=True)
    _ = headf.write_text(
        json.dumps({"commit_id": 7, "graph_hash_post": g0.hash}),
        encoding="utf-8",
    )

    committer = FSLaneCommitter()
    with pytest.raises(
        LaneCommitError,
        match="Lane HEAD commit_id must be a non-empty UUID string",
    ):
        _ = await committer.commit(
            branch_id=branch_id,
            projection_hash=opg.projection_hash,
            object_instance_graph_identity_id=_TEST_OIGI_ID,
            object_instance_graph_id=graph_id,
            before_oig=g0,
            changes=changes1,
            graph_hash_pre=g0.hash,
            graph_hash_post=g1.hash,
            author_id=author_id,
            commit_id=uuid4(),
            source_language=ocg.language,
        )
