from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from aware_history_ontology.change.change_enums import ChangeType
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.attribute.instance.value.stable_ids import stable_attribute_value_id
from aware_meta.graph.config.stable_ids import stable_attribute_id
from aware_history.stable_ids import stable_lane_id
from aware_history_ontology.commit.commit import Commit
from aware_history_ontology.commit.commit_parent import CommitParent
from aware_history_ontology.commit.commit_enums import CommitStatus
from aware_history_ontology.lane.lane import Lane
from aware_history_ontology.stable_ids import (
    stable_commit_id,
    stable_commit_parent_id,
)
import aware_meta.runtime.commit.identity_history as identity_history_mod
from aware_meta.graph.instance.commit.fs_commit_store import (
    OigCommitRecordUnavailableError,
)
from aware_meta.graph.instance.commit.state_index import build_commit_state_index
from aware_meta.runtime.commit.identity_history import (
    _canonicalize_domain_commit_identity_for_history,
    _materialize_oigi_history_head_with_recovery,
    _oigi_history_head_state_hash_mismatch,
    _oigi_primitive_leaf_value_fingerprint,
    _project_oigi_history_direct,
    _try_build_oigi_history_primitive_leaf_attribute_change,
    _try_build_oigi_primitive_leaf_attribute,
    _try_emit_oigi_model_free_primitive_leaf_source_row,
)
from aware_meta.test_support import make_attribute_config, test_class_fqn
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.class_.class_instance_change import ClassInstanceChange
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta_ontology.graph.instance.object_instance_graph_identity import (
    ObjectInstanceGraphIdentity,
)
from aware_meta_ontology.stable_ids import stable_object_instance_graph_commit_id
from aware_orm.session.session import Session


def _primitive_attribute_config(name: str = "label"):
    descriptor = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive,
        child_links=[],
    )
    return make_attribute_config(
        owner_key=test_class_fqn("OigiRowBackedPrimitive"),
        name=name,
        type_descriptor=descriptor,
        type_descriptor_id=descriptor.id,
    )


def _minimal_oig(*, graph_hash: str) -> ObjectInstanceGraph:
    graph_id = uuid4()
    class_instance_id = uuid4()
    class_instance = ClassInstance(
        id=class_instance_id,
        class_config_id=uuid4(),
        source_object_id=class_instance_id,
        object_instance_graph_id=graph_id,
        attributes=[],
        class_instance_relationships=[],
    )
    return ObjectInstanceGraph(
        id=graph_id,
        key="oigi",
        name="OIGI",
        description=None,
        object_projection_graph_id=uuid4(),
        root_class_instance_id=class_instance.id,
        root_class_instance=class_instance,
        class_instances=[class_instance],
        class_instance_relationships=[],
        hash=graph_hash,
    )


def test_oigi_history_head_state_hash_mismatch_detects_invalid_head() -> None:
    graph = _minimal_oig(graph_hash="invalid")

    mismatch = _oigi_history_head_state_hash_mismatch(before_oig=graph)

    assert mismatch is not None
    state_index_hash, graph_hash = mismatch
    assert graph_hash == "invalid"
    assert state_index_hash != graph_hash


@pytest.mark.asyncio
async def test_oigi_history_materialized_head_hash_mismatch_resets_lane(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    invalid_graph = _minimal_oig(graph_hash="invalid")
    valid_graph_base = _minimal_oig(graph_hash="")
    valid_graph = valid_graph_base.model_copy(
        update={"hash": build_commit_state_index(valid_graph_base).compute_hash()}
    )
    original_head_commit_id = uuid4()
    original_head_oig_id = invalid_graph.id
    reseeded_head_commit_id = uuid4()
    reseeded_head_oig_id = valid_graph.id
    reset_calls: list[dict[str, object]] = []
    ensure_calls: list[dict[str, object]] = []

    class _Materializer:
        def __init__(self) -> None:
            self.calls = 0

        async def get(self, **_: object):
            self.calls += 1
            if self.calls == 1:
                return invalid_graph, {}
            return valid_graph, {}

    class _Store:
        aware_root = tmp_path

        async def head(self, **_: object):
            return {
                "commit_id": str(reseeded_head_commit_id),
                "object_instance_graph_id": str(reseeded_head_oig_id),
            }

    class _Index:
        ocg = object()
        attribute_configs_by_id: dict[object, object] = {}
        class_configs_by_id: dict[object, object] = {}

    def _reset(**kwargs: object) -> None:
        reset_calls.append(kwargs)

    async def _ensure(**kwargs: object) -> None:
        ensure_calls.append(kwargs)

    monkeypatch.setattr(
        identity_history_mod,
        "reset_invalid_object_instance_graph_identity_lane",
        _reset,
    )
    monkeypatch.setattr(
        identity_history_mod,
        "ensure_object_instance_graph_identity_lane_head",
        _ensure,
    )
    perf_ms: dict[str, int] = {}

    materialized = await _materialize_oigi_history_head_with_recovery(
        materializer=_Materializer(),  # type: ignore[arg-type]
        lane_materializer=None,
        store=_Store(),  # type: ignore[arg-type]
        index=_Index(),  # type: ignore[arg-type]
        oigi_opg=object(),  # type: ignore[arg-type]
        domain_oig_id=uuid4(),
        domain_projection_hash="domain-hash",
        oigi_projection_hash="oigi-hash",
        head_commit_id=original_head_commit_id,
        head_oig_id=original_head_oig_id,
        author_id=uuid4(),
        perf_ms=perf_ms,
        perf_metric_prefix="test",
    )

    assert materialized.before_oig is valid_graph
    assert materialized.head_commit_id == reseeded_head_commit_id
    assert materialized.head_oig_id == reseeded_head_oig_id
    assert len(reset_calls) == 1
    assert len(ensure_calls) == 1
    assert perf_ms["test_invalid_oigi_head_reset_count"] == 1
    assert perf_ms["test_invalid_oigi_head_state_hash_reset_count"] == 1


@pytest.mark.asyncio
async def test_oigi_history_unavailable_record_resets_and_reseeds_lane(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    domain_oig_id = uuid4()
    original_head_commit_id = uuid4()
    valid_graph_base = _minimal_oig(graph_hash="")
    valid_graph = valid_graph_base.model_copy(
        update={"hash": build_commit_state_index(valid_graph_base).compute_hash()}
    )
    reseeded_head_commit_id = uuid4()
    reset_calls: list[dict[str, object]] = []
    ensure_calls: list[dict[str, object]] = []

    class _Materializer:
        def __init__(self) -> None:
            self.calls = 0

        async def get(self, **_: object):
            self.calls += 1
            if self.calls == 1:
                raise OigCommitRecordUnavailableError(
                    branch_id=domain_oig_id,
                    projection_hash="oigi-hash",
                    commit_id=original_head_commit_id,
                    lookup_commit_id=original_head_commit_id,
                )
            return valid_graph, {}

    class _Store:
        aware_root = tmp_path

        async def head(self, **_: object):
            return {
                "commit_id": str(reseeded_head_commit_id),
                "object_instance_graph_id": str(valid_graph.id),
            }

    class _Index:
        ocg = object()
        attribute_configs_by_id: dict[object, object] = {}
        class_configs_by_id: dict[object, object] = {}

    monkeypatch.setattr(
        identity_history_mod,
        "reset_invalid_object_instance_graph_identity_lane",
        lambda **kwargs: reset_calls.append(kwargs),
    )

    async def _ensure(**kwargs: object) -> None:
        ensure_calls.append(kwargs)

    monkeypatch.setattr(
        identity_history_mod,
        "ensure_object_instance_graph_identity_lane_head",
        _ensure,
    )
    perf_ms: dict[str, int] = {}

    materialized = await _materialize_oigi_history_head_with_recovery(  # pyright: ignore[reportArgumentType]
        materializer=_Materializer(),  # type: ignore[arg-type]
        lane_materializer=None,
        store=_Store(),  # type: ignore[arg-type]
        index=_Index(),  # type: ignore[arg-type]
        oigi_opg=object(),  # type: ignore[arg-type]
        domain_oig_id=domain_oig_id,
        domain_projection_hash="domain-hash",
        oigi_projection_hash="oigi-hash",
        head_commit_id=original_head_commit_id,
        head_oig_id=uuid4(),
        author_id=uuid4(),
        perf_ms=perf_ms,
        perf_metric_prefix="test",
    )

    assert materialized.before_oig is valid_graph
    assert materialized.head_commit_id == reseeded_head_commit_id
    assert len(reset_calls) == 1
    assert len(ensure_calls) == 1
    assert perf_ms["test_invalid_oigi_head_reset_count"] == 1
    assert perf_ms["test_invalid_oigi_head_record_unavailable_reset_count"] == 1


@pytest.mark.asyncio
async def test_oigi_history_unavailable_record_with_explicit_lane_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    domain_oig_id = uuid4()
    commit_id = uuid4()

    class _Materializer:
        async def get(self, **_: object):
            raise OigCommitRecordUnavailableError(
                branch_id=domain_oig_id,
                projection_hash="oigi-hash",
                commit_id=commit_id,
                lookup_commit_id=commit_id,
            )

    class _Store:
        aware_root = tmp_path

    class _Index:
        ocg = object()
        attribute_configs_by_id: dict[object, object] = {}
        class_configs_by_id: dict[object, object] = {}

    def _unexpected_reset(**_: object) -> None:
        raise AssertionError("explicit lane materialization must not reset state")

    monkeypatch.setattr(
        identity_history_mod,
        "reset_invalid_object_instance_graph_identity_lane",
        _unexpected_reset,
    )
    materializer = _Materializer()

    with pytest.raises(OigCommitRecordUnavailableError):
        await _materialize_oigi_history_head_with_recovery(  # pyright: ignore[reportArgumentType]
            materializer=materializer,  # type: ignore[arg-type]
            lane_materializer=materializer,  # type: ignore[arg-type]
            store=_Store(),  # type: ignore[arg-type]
            index=_Index(),  # type: ignore[arg-type]
            oigi_opg=object(),  # type: ignore[arg-type]
            domain_oig_id=domain_oig_id,
            domain_projection_hash="domain-hash",
            oigi_projection_hash="oigi-hash",
            head_commit_id=commit_id,
            head_oig_id=uuid4(),
            author_id=uuid4(),
            perf_ms={},
            perf_metric_prefix="test",
        )


def test_oigi_primitive_row_backed_prestate_reuses_existing_attribute() -> None:
    owner_key = uuid4()
    attribute_config = _primitive_attribute_config()
    before_fingerprint = _oigi_primitive_leaf_value_fingerprint(
        type_descriptor=attribute_config.type_descriptor,
        primitive_value={"value": "same"},
    )
    assert before_fingerprint is not None

    emission = _try_emit_oigi_model_free_primitive_leaf_source_row(
        owner_key=owner_key,
        attribute_config=attribute_config,
        value="same",
        before_attributes_by_id={},
        before_attribute_fingerprints_by_config_id={
            attribute_config.id: before_fingerprint,
        },
        created_at=datetime.now(UTC),
    )

    expected_attribute_id = stable_attribute_id(
        owner_key=owner_key,
        attribute_config_id=attribute_config.id,
    )
    assert emission.attribute_id == expected_attribute_id
    assert emission.attribute_change_body_draft is None
    assert emission.reused_before_fingerprint is True
    assert emission.row_backed_before_attribute is True


def test_oigi_primitive_row_backed_prestate_emits_update_not_create() -> None:
    owner_key = uuid4()
    attribute_config = _primitive_attribute_config()
    before_fingerprint = _oigi_primitive_leaf_value_fingerprint(
        type_descriptor=attribute_config.type_descriptor,
        primitive_value={"value": "before"},
    )
    assert before_fingerprint is not None

    emission = _try_emit_oigi_model_free_primitive_leaf_source_row(
        owner_key=owner_key,
        attribute_config=attribute_config,
        value="after",
        before_attributes_by_id={},
        before_attribute_fingerprints_by_config_id={
            attribute_config.id: before_fingerprint,
        },
        created_at=datetime.now(UTC),
    )

    expected_attribute_id = stable_attribute_id(
        owner_key=owner_key,
        attribute_config_id=attribute_config.id,
    )
    assert emission.attribute_id == expected_attribute_id
    assert emission.attribute_change_body_draft is not None
    assert emission.attribute_change_body_draft.change.type == ChangeType.update
    assert emission.attribute_change_body_draft.value_root_change is not None
    assert (
        emission.attribute_change_body_draft.value_root_change.change.type
        == ChangeType.update
    )
    assert (
        emission.attribute_change_body_draft.value_root_change.attribute_value_id
        == (
            stable_attribute_value_id(
                parent_value_id=expected_attribute_id,
                role="member",
                position=0,
                identity_key="root",
            )
        )
    )
    assert emission.row_backed_before_attribute is True


def test_oigi_required_primitive_without_prestate_emits_create() -> None:
    owner_key = uuid4()
    attribute_config = _primitive_attribute_config()
    attribute_config.is_required = True

    emission = _try_emit_oigi_model_free_primitive_leaf_source_row(
        owner_key=owner_key,
        attribute_config=attribute_config,
        value="after",
        before_attributes_by_id={},
        before_attribute_fingerprints_by_config_id={},
        created_at=datetime.now(UTC),
    )

    expected_attribute_id = stable_attribute_id(
        owner_key=owner_key,
        attribute_config_id=attribute_config.id,
    )
    assert emission.attribute_id == expected_attribute_id
    assert emission.attribute_change_body_draft is not None
    assert emission.attribute_change_body_draft.change.type == ChangeType.create
    assert emission.attribute_change_body_draft.value_root_change is not None
    assert (
        emission.attribute_change_body_draft.value_root_change.change.type
        == ChangeType.create
    )
    assert (
        emission.attribute_change_body_draft.value_root_change.attribute_value_id
        == (
            stable_attribute_value_id(
                parent_value_id=expected_attribute_id,
                role="member",
                position=0,
                identity_key="root",
            )
        )
    )
    assert emission.row_backed_before_attribute is False


def test_oigi_optional_primitive_without_prestate_emits_create() -> None:
    owner_key = uuid4()
    attribute_config = _primitive_attribute_config()

    emission = _try_emit_oigi_model_free_primitive_leaf_source_row(
        owner_key=owner_key,
        attribute_config=attribute_config,
        value="after",
        before_attributes_by_id={},
        before_attribute_fingerprints_by_config_id={},
        created_at=datetime.now(UTC),
    )

    assert emission.attribute_change_body_draft is not None
    assert emission.attribute_change_body_draft.change.type == ChangeType.create
    assert emission.attribute_change_body_draft.value_root_change is not None
    assert (
        emission.attribute_change_body_draft.value_root_change.change.type
        == ChangeType.create
    )
    assert emission.row_backed_before_attribute is False


def test_oigi_primitive_generic_row_backed_prestate_emits_update_not_create() -> None:
    owner_key = uuid4()
    attribute_config = _primitive_attribute_config()
    before_fingerprint = _oigi_primitive_leaf_value_fingerprint(
        type_descriptor=attribute_config.type_descriptor,
        primitive_value={"value": "before"},
    )
    assert before_fingerprint is not None
    attribute = _try_build_oigi_primitive_leaf_attribute(
        owner_key=owner_key,
        attribute_config=attribute_config,
        value="after",
    )
    assert attribute is not None
    value_fingerprint = _oigi_primitive_leaf_value_fingerprint(
        type_descriptor=attribute_config.type_descriptor,
        primitive_value={"value": "after"},
    )
    parent = ClassInstanceChange.model_construct(id=uuid4())

    change = _try_build_oigi_history_primitive_leaf_attribute_change(
        before_attribute=None,
        before_value_fingerprint=before_fingerprint,
        attribute=attribute,
        value_fingerprint=value_fingerprint,
        parent=parent,
        created_at=datetime.now(UTC),
        row_backed_before_attribute=True,
    )

    expected_attribute_id = stable_attribute_id(
        owner_key=owner_key,
        attribute_config_id=attribute_config.id,
    )
    assert change is not None
    assert change.attribute_id == expected_attribute_id
    assert change.change.type == ChangeType.update
    assert change.value_root_change.change.type == ChangeType.update
    assert change.value_root_change.attribute_value_id == stable_attribute_value_id(
        parent_value_id=expected_attribute_id,
        role="member",
        position=0,
        identity_key="root",
    )


def test_oigi_primitive_generic_without_prestate_emits_create() -> None:
    owner_key = uuid4()
    attribute_config = _primitive_attribute_config()
    attribute = _try_build_oigi_primitive_leaf_attribute(
        owner_key=owner_key,
        attribute_config=attribute_config,
        value="after",
    )
    assert attribute is not None
    value_fingerprint = _oigi_primitive_leaf_value_fingerprint(
        type_descriptor=attribute_config.type_descriptor,
        primitive_value={"value": "after"},
    )
    parent = ClassInstanceChange.model_construct(id=uuid4())

    change = _try_build_oigi_history_primitive_leaf_attribute_change(
        before_attribute=None,
        before_value_fingerprint=None,
        attribute=attribute,
        value_fingerprint=value_fingerprint,
        parent=parent,
        created_at=datetime.now(UTC),
    )

    expected_attribute_id = stable_attribute_id(
        owner_key=owner_key,
        attribute_config_id=attribute_config.id,
    )
    assert change is not None
    assert change.attribute_id == expected_attribute_id
    assert change.change.type == ChangeType.create
    assert change.value_root_change.change.type == ChangeType.create
    assert change.value_root_change.attribute_value_id == stable_attribute_value_id(
        parent_value_id=expected_attribute_id,
        role="member",
        position=0,
        identity_key="root",
    )


def test_oigi_primitive_generic_row_backed_prestate_returns_no_change() -> None:
    owner_key = uuid4()
    attribute_config = _primitive_attribute_config()
    before_fingerprint = _oigi_primitive_leaf_value_fingerprint(
        type_descriptor=attribute_config.type_descriptor,
        primitive_value={"value": "same"},
    )
    assert before_fingerprint is not None
    attribute = _try_build_oigi_primitive_leaf_attribute(
        owner_key=owner_key,
        attribute_config=attribute_config,
        value="same",
    )
    assert attribute is not None
    parent = ClassInstanceChange.model_construct(id=uuid4())

    change = _try_build_oigi_history_primitive_leaf_attribute_change(
        before_attribute=None,
        before_value_fingerprint=before_fingerprint,
        attribute=attribute,
        value_fingerprint=before_fingerprint,
        parent=parent,
        created_at=datetime.now(UTC),
        row_backed_before_attribute=True,
    )

    assert change is None


@pytest.mark.asyncio
async def test_oigi_history_canonicalizes_stale_domain_commit_identity() -> None:
    domain_branch_id = uuid4()
    domain_projection_hash = "sha256:test:domain"
    domain_oig_id = uuid4()
    expected_oigi_id = uuid4()
    stale_oigi_id = uuid4()
    domain_commit_id = uuid4()
    persisted: list[ObjectInstanceGraphCommit] = []
    object_instance_graph_identity = ObjectInstanceGraphIdentity(
        id=expected_oigi_id,
        object_projection_graph_identity_id=uuid4(),
        object_instance_graph_id=domain_oig_id,
    )
    domain_commit = ObjectInstanceGraphCommit(
        id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=stale_oigi_id,
            commit_id=domain_commit_id,
        ),
        object_instance_graph_identity_id=stale_oigi_id,
        object_instance_graph_id=domain_oig_id,
        commit=Commit(
            id=domain_commit_id,
            lane_id=uuid4(),
            key=str(domain_commit_id),
            author_id=uuid4(),
            created_at=datetime.now(UTC),
            status=CommitStatus.local,
        ),
        commit_id=domain_commit_id,
        object_instance_graph_key="domain",
        object_instance_graph_name="Domain",
        object_instance_graph_description=None,
        root_class_config_id=uuid4(),
        root_source_object_id=uuid4(),
        graph_hash_pre="sha256:test:pre",
        graph_hash_post="sha256:test:post",
        projection_hash=domain_projection_hash,
        source_language=CodeLanguage.aware,
        object_instance_graph_changes=[],
    )

    class _Store:
        async def put_commit_file(
            self,
            *,
            branch_id: object,
            projection_hash: object,
            commit: ObjectInstanceGraphCommit,
        ) -> bool:
            assert branch_id == domain_branch_id
            assert projection_hash == domain_projection_hash
            persisted.append(commit)
            return True

    canonical_commit = await _canonicalize_domain_commit_identity_for_history(
        store=_Store(),  # type: ignore[arg-type]
        domain_branch_id=domain_branch_id,
        domain_projection_hash=domain_projection_hash,
        object_instance_graph_identity=object_instance_graph_identity,
        domain_commit=domain_commit,
    )

    assert canonical_commit.object_instance_graph_id == domain_oig_id
    assert canonical_commit.object_instance_graph_identity_id == expected_oigi_id
    assert canonical_commit.id == stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=expected_oigi_id,
        commit_id=domain_commit_id,
    )
    assert persisted == [canonical_commit]


@pytest.mark.asyncio
async def test_oigi_history_leaves_unrelated_domain_oig_mismatch_to_validator() -> None:
    expected_oigi_id = uuid4()
    object_instance_graph_identity = ObjectInstanceGraphIdentity(
        id=expected_oigi_id,
        object_projection_graph_identity_id=uuid4(),
        object_instance_graph_id=uuid4(),
    )
    domain_commit_id = uuid4()
    domain_commit = ObjectInstanceGraphCommit(
        id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=uuid4(),
            commit_id=domain_commit_id,
        ),
        object_instance_graph_identity_id=uuid4(),
        object_instance_graph_id=uuid4(),
        commit=Commit(
            id=domain_commit_id,
            lane_id=uuid4(),
            key=str(domain_commit_id),
            author_id=uuid4(),
            created_at=datetime.now(UTC),
            status=CommitStatus.local,
        ),
        commit_id=domain_commit_id,
        object_instance_graph_key="domain",
        object_instance_graph_name="Domain",
        object_instance_graph_description=None,
        root_class_config_id=uuid4(),
        root_source_object_id=uuid4(),
        graph_hash_pre="sha256:test:pre",
        graph_hash_post="sha256:test:post",
        projection_hash="sha256:test:domain",
        source_language=CodeLanguage.aware,
        object_instance_graph_changes=[],
    )

    class _Store:
        async def put_commit_file(self, **_: object) -> bool:
            raise AssertionError("unrelated domain OIG mismatch must not be rewritten")

    unchanged_commit = await _canonicalize_domain_commit_identity_for_history(
        store=_Store(),  # type: ignore[arg-type]
        domain_branch_id=uuid4(),
        domain_projection_hash="sha256:test:domain",
        object_instance_graph_identity=object_instance_graph_identity,
        domain_commit=domain_commit,
    )

    assert unchanged_commit is domain_commit


@pytest.mark.asyncio
async def test_oigi_history_direct_stops_at_already_projected_parent() -> None:
    oigi_id = uuid4()
    domain_oig_id = uuid4()
    domain_branch_id = uuid4()
    domain_projection_hash = "sha256:test:domain"
    lane_id = stable_lane_id(
        branch_id=domain_branch_id,
        lane_hash=domain_projection_hash,
    )
    author_id = uuid4()
    parent_domain_commit_id = uuid4()
    head_domain_commit_id = uuid4()
    parent_history_commit_id = stable_commit_id(
        lane_id=lane_id,
        key=str(parent_domain_commit_id),
    )
    head_history_commit_id = stable_commit_id(
        lane_id=lane_id,
        key=str(head_domain_commit_id),
    )
    parent_history_commit = Commit(
        id=parent_history_commit_id,
        lane_id=lane_id,
        key=str(parent_domain_commit_id),
        author_id=author_id,
        created_at=datetime.now(UTC),
        status=CommitStatus.local,
    )
    parent_wrapper = ObjectInstanceGraphCommit(
        id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=oigi_id,
            commit_id=parent_domain_commit_id,
        ),
        object_instance_graph_identity_id=oigi_id,
        object_instance_graph_id=domain_oig_id,
        commit=parent_history_commit,
        commit_id=parent_history_commit_id,
        object_instance_graph_key="domain",
        object_instance_graph_name="Domain",
        object_instance_graph_description=None,
        root_class_config_id=uuid4(),
        root_source_object_id=uuid4(),
        graph_hash_pre="sha256:test:parent-pre",
        graph_hash_post="sha256:test:parent-post",
        projection_hash=domain_projection_hash,
        source_language=CodeLanguage.aware,
        object_instance_graph_changes=[],
    )
    object_instance_graph_identity = ObjectInstanceGraphIdentity(
        id=oigi_id,
        object_projection_graph_identity_id=uuid4(),
        object_instance_graph_id=domain_oig_id,
        object_instance_graph_commits=[parent_wrapper],
    )
    session = Session(branch_id=domain_branch_id, skip_db=True)
    session.imap_add(object_instance_graph_identity)
    session.imap_add(parent_history_commit)
    session.imap_add(parent_wrapper)

    domain_head_commit = Commit(
        id=head_domain_commit_id,
        lane_id=uuid4(),
        key=str(head_domain_commit_id),
        author_id=author_id,
        created_at=datetime.now(UTC),
        status=CommitStatus.local,
        commit_parents=[
            CommitParent(
                id=stable_commit_parent_id(
                    commit_id=head_domain_commit_id,
                    parent_commit_id=parent_domain_commit_id,
                ),
                commit_id=head_domain_commit_id,
                parent_commit_id=parent_domain_commit_id,
            )
        ],
    )
    domain_commit = ObjectInstanceGraphCommit(
        id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=oigi_id,
            commit_id=head_domain_commit_id,
        ),
        object_instance_graph_identity_id=oigi_id,
        object_instance_graph_id=domain_oig_id,
        commit=domain_head_commit,
        commit_id=head_domain_commit_id,
        object_instance_graph_key="domain",
        object_instance_graph_name="Domain",
        object_instance_graph_description=None,
        root_class_config_id=uuid4(),
        root_source_object_id=uuid4(),
        graph_hash_pre="sha256:test:head-pre",
        graph_hash_post="sha256:test:head-post",
        projection_hash=domain_projection_hash,
        source_language=CodeLanguage.aware,
        object_instance_graph_changes=[],
    )

    class _Store:
        calls: list[object] = []

        async def get_commit(
            self,
            *,
            branch_id: object,
            projection_hash: object,
            commit_id: object,
        ) -> ObjectInstanceGraphCommit | None:
            self.calls.append(commit_id)
            raise AssertionError(
                "already projected parent commits must not be replayed"
            )

        async def get_commit_identity_sidecar(self, **_: object) -> None:
            return None

        async def put_commit_file(self, **_: object) -> bool:
            return True

    store = _Store()

    await _project_oigi_history_direct(
        session=session,
        object_instance_graph_identity=object_instance_graph_identity,
        domain_branch_id=domain_branch_id,
        domain_projection_hash=domain_projection_hash,
        lane_id=lane_id,
        head_commit_id=head_domain_commit_id,
        domain_commit=domain_commit,
        store=store,  # type: ignore[arg-type]
    )

    projected_domain_commit_ids = {
        wrapper.commit.key
        for wrapper in object_instance_graph_identity.object_instance_graph_commits
    }
    assert projected_domain_commit_ids == {
        str(parent_domain_commit_id),
        str(head_domain_commit_id),
    }
    assert store.calls == []
    lane = session.imap_get(Lane, lane_id)
    assert lane is not None
    assert lane.head_commit_id == head_history_commit_id
