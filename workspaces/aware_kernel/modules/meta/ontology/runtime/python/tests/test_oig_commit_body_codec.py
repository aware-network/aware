from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from uuid import UUID, uuid4

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_history_ontology.change.change import Change
from aware_history_ontology.change.change_delta import ChangeDelta
from aware_history_ontology.change.change_enums import ChangeDeltaKind, ChangeType
from aware_history_ontology.commit.commit import Commit
from aware_history_ontology.commit.commit_enums import CommitStatus
from aware_meta.graph.instance.commit.body_codec import (
    OIG_COMMIT_BODY_CONTRACT,
    OIG_CHANGE_SET_CONTRACT,
    OigCommitBodyDraft,
    OigCommitBodyRootChangeDraft,
    OigCommitBodyCodecError,
    build_oig_commit_body,
    build_oig_commit_body_from_draft,
    canonical_oig_change_set_bytes,
    decode_oig_commit_body,
    object_instance_graph_changes_from_body,
    oig_commit_body_change_ref_draft_from_change,
    oig_commit_body_class_instance_change_draft_from_change,
    oig_commit_body_relationship_change_draft_from_change,
    oig_commit_body_sha256,
    oig_change_set_sha256,
)
from aware_meta_ontology.attribute.attribute_change import AttributeChange
from aware_meta_ontology.attribute.attribute_value_change import AttributeValueChange
from aware_meta_ontology.attribute.attribute_value_link_change import (
    AttributeValueLinkChange,
)
from aware_meta_ontology.class_.class_instance_change import ClassInstanceChange
from aware_meta_ontology.class_.class_instance_relationship_change import (
    ClassInstanceRelationshipChange,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change_enums import (
    ObjectInstanceGraphChangeType,
)
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta_ontology.stable_ids import stable_object_instance_graph_commit_id


_CREATED_AT = datetime(2026, 7, 3, 7, 1, 26, tzinfo=UTC)


def test_oig_commit_body_codec_emits_canonical_inline_payload() -> None:
    commit, delta_id = _make_commit_with_changes()

    body = build_oig_commit_body(commit)
    decoded = decode_oig_commit_body(body.canonical_bytes)
    parsed = json.loads(body.canonical_bytes.decode("utf-8"))

    assert body.payload == decoded.payload
    assert body.sha256 == hashlib.sha256(body.canonical_bytes).hexdigest()
    assert body.sha256 == oig_commit_body_sha256(body.payload)
    assert body.commit_id == commit.commit.id
    assert body.object_instance_graph_commit_id == commit.id
    assert (
        body.object_instance_graph_identity_id
        == commit.object_instance_graph_identity_id
    )
    assert body.object_instance_graph_id == commit.object_instance_graph_id
    assert parsed["c"] == OIG_COMMIT_BODY_CONTRACT
    assert parsed["v"] == 1
    assert parsed["r"][0]["ci"][0]["f"][0] == {
        "op": "scalar_set",
        "p": "source_object_id",
        "pos": 0,
        "x": {"value": str(commit.root_source_object_id)},
    }
    assert body.canonical_bytes == json.dumps(
        parsed,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    assert b"object_instance_graph_changes" not in body.canonical_bytes
    assert str(delta_id).encode("utf-8") not in body.canonical_bytes

    changes = object_instance_graph_changes_from_body(decoded)
    assert len(changes) == 1
    assert changes[0].id == commit.object_instance_graph_changes[0].id
    assert (
        changes[0].object_instance_graph_identity_id
        == commit.object_instance_graph_identity_id
    )
    assert changes[0].object_instance_graph_id == commit.object_instance_graph_id
    assert changes[0].class_instance_changes[0].class_instance_id == (
        commit.object_instance_graph_changes[0]
        .class_instance_changes[0]
        .class_instance_id
    )
    assert (
        changes[0].class_instance_changes[0].change.change_deltas[0].property
        == "source_object_id"
    )
    assert changes[0].class_instance_changes[0].change.change_deltas[0].id != delta_id


def test_oig_change_set_digest_matches_canonical_commit_body_roots() -> None:
    commit, _ = _make_commit_with_changes()
    changes = tuple(commit.object_instance_graph_changes)
    copied_changes = tuple(change.model_copy(deep=True) for change in changes)

    payload = json.loads(canonical_oig_change_set_bytes(changes).decode("utf-8"))
    body = build_oig_commit_body(commit)

    assert payload == {
        "c": OIG_CHANGE_SET_CONTRACT,
        "v": 1,
        "r": body.payload["r"],
    }
    assert oig_change_set_sha256(copied_changes) == oig_change_set_sha256(changes)

    copied_changes[0].class_instance_changes[0].change.change_deltas[0].payload = {
        "value": str(uuid4())
    }
    assert oig_change_set_sha256(copied_changes) != oig_change_set_sha256(changes)


def test_oig_commit_body_codec_rejects_legacy_commit_payload() -> None:
    legacy_payload = {
        "commit": {"id": str(uuid4())},
        "object_instance_graph_changes": [],
    }

    with pytest.raises(OigCommitBodyCodecError, match="legacy_oig_commit_payload"):
        decode_oig_commit_body(json.dumps(legacy_payload).encode("utf-8"))


def test_oig_commit_body_codec_rejects_unknown_keys() -> None:
    commit, _ = _make_commit_with_changes()
    body = build_oig_commit_body(commit)
    payload = {**body.payload, "legacy": True}

    with pytest.raises(OigCommitBodyCodecError, match="unknown_oig_commit_body_keys"):
        oig_commit_body_sha256(payload)


def test_oig_commit_body_draft_matches_change_tree_payload() -> None:
    commit, _ = _make_commit_with_changes()
    change = commit.object_instance_graph_changes[0]
    expected = build_oig_commit_body(commit)
    draft = OigCommitBodyDraft(
        roots=(
            OigCommitBodyRootChangeDraft(
                id=change.id,
                type=change.type,
                change=oig_commit_body_change_ref_draft_from_change(change.change),
                class_instance_changes=tuple(
                    oig_commit_body_class_instance_change_draft_from_change(item)
                    for item in change.class_instance_changes
                ),
                class_instance_relationship_changes=tuple(
                    oig_commit_body_relationship_change_draft_from_change(item)
                    for item in change.class_instance_relationship_changes
                ),
            ),
        )
    )

    actual = build_oig_commit_body_from_draft(
        commit_id=commit.commit.id,
        object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
        object_instance_graph_id=commit.object_instance_graph_id,
        draft=draft,
    )

    assert actual.payload == expected.payload
    assert actual.canonical_bytes == expected.canonical_bytes
    assert actual.sha256 == expected.sha256


def _make_commit_with_changes() -> tuple[ObjectInstanceGraphCommit, UUID]:
    commit_id = uuid4()
    object_instance_graph_identity_id = uuid4()
    object_instance_graph_id = uuid4()
    root_source_object_id = uuid4()
    root_class_config_id = uuid4()
    class_instance_id = uuid4()
    attribute_id = uuid4()
    attribute_value_id = uuid4()
    attribute_value_link_id = uuid4()
    relationship_id = uuid4()
    target_class_instance_id = uuid4()
    delta_id = uuid4()
    root_change = _change("root", ChangeType.update)
    class_change = _change(
        "class-instance",
        ChangeType.create,
        deltas=[
            _delta(
                delta_id=delta_id,
                change_id=uuid4(),
                position=0,
                property_name="source_object_id",
                payload={"value": root_source_object_id},
            ),
            _delta(
                delta_id=uuid4(),
                change_id=uuid4(),
                position=1,
                property_name="class_config_id",
                payload={"value": root_class_config_id},
            ),
        ],
    )
    value_change = AttributeValueChange.model_construct(
        id=uuid4(),
        attribute_value_id=attribute_value_id,
        change=_change("attribute-value", ChangeType.create),
        change_id=uuid4(),
        attribute_value_link_changes=[
            AttributeValueLinkChange.model_construct(
                id=uuid4(),
                attribute_value_link_id=attribute_value_link_id,
                attribute_value_change_id=attribute_value_id,
                change=_change("attribute-value-link", ChangeType.create),
                change_id=uuid4(),
                child_attribute_value_change=None,
                child_attribute_value_change_id=None,
            )
        ],
    )
    attribute_change = AttributeChange.model_construct(
        id=uuid4(),
        class_instance_change_id=class_instance_id,
        attribute_id=attribute_id,
        change=_change("attribute", ChangeType.create),
        change_id=uuid4(),
        value_root_change=value_change,
        value_root_change_id=value_change.id,
    )
    class_instance_change = ClassInstanceChange.model_construct(
        id=uuid4(),
        class_instance_id=class_instance_id,
        change=class_change,
        change_id=class_change.id,
        attribute_changes=[attribute_change],
    )
    relationship_change = ClassInstanceRelationshipChange.model_construct(
        id=uuid4(),
        class_config_relationship_id=relationship_id,
        source_class_instance_id=class_instance_id,
        target_class_instance_id=target_class_instance_id,
        change=_change("relationship", ChangeType.create),
        change_id=uuid4(),
    )
    object_change = ObjectInstanceGraphChange.model_construct(
        id=uuid4(),
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
        type=ObjectInstanceGraphChangeType.object_instance,
        change=root_change,
        change_id=root_change.id,
        class_instance_changes=[class_instance_change],
        class_instance_relationship_changes=[relationship_change],
    )
    commit = ObjectInstanceGraphCommit.model_construct(
        id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            commit_id=commit_id,
        ),
        commit=Commit.model_construct(
            id=commit_id,
            author_id=uuid4(),
            key=str(commit_id),
            created_at=_CREATED_AT,
            status=CommitStatus.local,
            lane_id=uuid4(),
            commit_parents=[],
        ),
        object_instance_graph_key="workspace-revision",
        object_instance_graph_name="workspace-revision",
        object_instance_graph_description=None,
        root_class_config_id=root_class_config_id,
        root_source_object_id=root_source_object_id,
        graph_hash_post="sha256:post",
        graph_hash_pre="sha256:pre",
        projection_hash="WorkspaceRevision",
        source_language=CodeLanguage.python,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
        commit_id=commit_id,
        object_instance_graph_changes=[object_change],
    )
    return commit, delta_id


def _change(
    suffix: str,
    change_type: ChangeType,
    *,
    deltas: list[ChangeDelta] | None = None,
) -> Change:
    change_id = uuid4()
    return Change.model_construct(
        id=change_id,
        key=f"workspace-revision:{suffix}",
        created_at=_CREATED_AT,
        type=change_type,
        change_deltas=[
            _rebind_delta(delta=delta, change_id=change_id) for delta in (deltas or [])
        ],
    )


def _delta(
    *,
    delta_id: UUID,
    change_id: UUID,
    position: int,
    property_name: str,
    payload: object,
) -> ChangeDelta:
    return ChangeDelta.model_construct(
        id=delta_id,
        change_id=change_id,
        position=position,
        property=property_name,
        kind=ChangeDeltaKind.scalar_set,
        payload=payload,
    )


def _rebind_delta(*, delta: ChangeDelta, change_id: UUID) -> ChangeDelta:
    return ChangeDelta.model_construct(
        id=delta.id,
        change_id=change_id,
        position=delta.position,
        property=delta.property,
        kind=delta.kind,
        payload=delta.payload,
    )
