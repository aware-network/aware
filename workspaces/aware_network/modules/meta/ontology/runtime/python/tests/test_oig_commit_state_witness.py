from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from aware_history_ontology.change.change import Change
from aware_history_ontology.change.change_enums import ChangeType
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_instance_change import ClassInstanceChange
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change_enums import (
    ObjectInstanceGraphChangeType,
)
from aware_orm.session.autobind import disable_autobind

from aware_meta.graph.instance.commit.state_index import (
    CommitStateIndex,
    CommitStateRow,
)
from aware_meta.graph.instance.commit.state_witness import (
    COMMIT_STATE_WITNESS_SCHEMA,
    apply_commit_state_witness_changes,
    apply_commit_state_witness_row_changes,
    build_commit_state_witness_ref,
    build_commit_state_witness_cursor,
    build_commit_state_witness,
    compute_commit_state_witness_cursor_hash,
    compute_commit_state_witness_hash,
    replace_commit_state_witness_cursor_chunk_segments,
    replace_existing_commit_state_witness_cursor_segments,
    replace_existing_commit_state_witness_cursor_summary_chunks,
    replace_existing_commit_state_witness_ref_segments,
    validate_commit_state_witness_cursor,
    validate_commit_state_witness_cursor_summary,
    validate_commit_state_witness_ref,
)


CLASS_CONFIG_A = UUID("11111111-1111-4111-8111-111111111111")
CLASS_CONFIG_B = UUID("22222222-2222-4222-8222-222222222222")
CLASS_INSTANCE_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
CLASS_INSTANCE_B = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
ATTR_CONFIG_A = UUID("33333333-3333-4333-8333-333333333333")
ATTR_CONFIG_B = UUID("44444444-4444-4444-8444-444444444444")
REL_CONFIG = UUID("55555555-5555-4555-8555-555555555555")
OIG_ID = UUID("66666666-6666-4666-8666-666666666666")
OIGI_ID = UUID("77777777-7777-4777-8777-777777777777")


def test_commit_state_witness_preserves_current_state_hash_contract() -> None:
    state_index = _pre_state_index()

    witness = build_commit_state_witness(state_index)

    assert witness.schema == COMMIT_STATE_WITNESS_SCHEMA
    assert witness.state_hash == state_index.compute_hash()
    assert witness.state_index().compute_hash() == state_index.compute_hash()
    assert witness.witness_hash == compute_commit_state_witness_hash(witness.segments)
    assert [segment.kind for segment in witness.segments] == [
        "CLASS",
        "CLASS",
        "EDGE",
    ]
    assert [len(segment.rows) for segment in witness.segments] == [2, 2, 1]


def test_commit_state_witness_ref_preserves_compact_hash_contract() -> None:
    state_index = _pre_state_index()
    witness = build_commit_state_witness(state_index)

    witness_ref = build_commit_state_witness_ref(state_index)

    assert witness_ref.schema == COMMIT_STATE_WITNESS_SCHEMA
    assert witness_ref.state_hash == witness.state_hash
    assert witness_ref.witness_hash == witness.witness_hash
    assert witness_ref.row_count == witness.row_count
    assert witness_ref.segments == tuple(segment.ref() for segment in witness.segments)
    assert witness_ref.segment_digests_by_key() == witness.segment_digests_by_key()
    assert validate_commit_state_witness_ref(witness_ref)


def test_commit_state_witness_applies_delta_to_same_post_hash_as_full_index() -> None:
    pre_index = _pre_state_index()
    witness = build_commit_state_witness(pre_index)
    previous_segment_digests = witness.segment_digests_by_key()
    post_class_instance = ClassInstance(
        id=CLASS_INSTANCE_A,
        class_config_id=CLASS_CONFIG_A,
        object_instance_graph_id=OIG_ID,
        source_object_id=CLASS_INSTANCE_A,
        class_instance_attributes=[],
    )
    change = _oig_change(
        class_instance_id=CLASS_INSTANCE_A,
        change_type=ChangeType.update,
    )

    post_witness = apply_commit_state_witness_changes(
        pre_witness=witness,
        changes=(change,),
        post_class_instances_by_id={CLASS_INSTANCE_A: post_class_instance},
    )
    expected_post_index = CommitStateIndex(
        rows=(
            CommitStateRow(
                kind="NODE",
                key=str(CLASS_CONFIG_A),
                value=str(CLASS_INSTANCE_A),
            ),
            CommitStateRow(
                kind="NODE",
                key=str(CLASS_CONFIG_B),
                value=str(CLASS_INSTANCE_B),
            ),
            CommitStateRow(
                kind="ATTR",
                key=str(CLASS_INSTANCE_B),
                value=f"{ATTR_CONFIG_B}:beta",
            ),
            CommitStateRow(
                kind="EDGE",
                key=str(REL_CONFIG),
                value=f"{CLASS_INSTANCE_A}->{CLASS_INSTANCE_B}",
            ),
        )
    )

    assert post_witness.state_hash == expected_post_index.compute_hash()
    assert post_witness.state_hash != witness.state_hash
    assert post_witness.witness_hash != witness.witness_hash

    next_segment_digests = post_witness.segment_digests_by_key()
    assert next_segment_digests[f"class:{CLASS_INSTANCE_A}"] != (
        previous_segment_digests[f"class:{CLASS_INSTANCE_A}"]
    )
    assert next_segment_digests[f"class:{CLASS_INSTANCE_B}"] == (
        previous_segment_digests[f"class:{CLASS_INSTANCE_B}"]
    )
    assert (
        next_segment_digests[
            f"edge:{REL_CONFIG}:{CLASS_INSTANCE_A}->{CLASS_INSTANCE_B}"
        ]
        == previous_segment_digests[
            f"edge:{REL_CONFIG}:{CLASS_INSTANCE_A}->{CLASS_INSTANCE_B}"
        ]
    )


def test_commit_state_witness_row_apply_does_not_require_class_instances() -> None:
    pre_index = _pre_state_index()
    witness = build_commit_state_witness(pre_index)
    change = _oig_change(
        class_instance_id=CLASS_INSTANCE_A,
        change_type=ChangeType.update,
    )
    post_rows = (
        CommitStateRow(
            kind="NODE",
            key=str(CLASS_CONFIG_A),
            value=str(CLASS_INSTANCE_A),
        ),
    )

    post_witness = apply_commit_state_witness_row_changes(
        pre_witness=witness,
        changes=(change,),
        post_class_state_rows_by_id={CLASS_INSTANCE_A: post_rows},
    )

    assert (
        post_witness.state_hash
        == CommitStateIndex(
            rows=(
                CommitStateRow(
                    kind="NODE",
                    key=str(CLASS_CONFIG_A),
                    value=str(CLASS_INSTANCE_A),
                ),
                CommitStateRow(
                    kind="NODE",
                    key=str(CLASS_CONFIG_B),
                    value=str(CLASS_INSTANCE_B),
                ),
                CommitStateRow(
                    kind="ATTR",
                    key=str(CLASS_INSTANCE_B),
                    value=f"{ATTR_CONFIG_B}:beta",
                ),
                CommitStateRow(
                    kind="EDGE",
                    key=str(REL_CONFIG),
                    value=f"{CLASS_INSTANCE_A}->{CLASS_INSTANCE_B}",
                ),
            )
        ).compute_hash()
    )


def test_commit_state_witness_ref_replaces_existing_segments_without_rows() -> None:
    pre_index = _pre_state_index()
    pre_witness_ref = build_commit_state_witness_ref(pre_index)
    post_class_rows = (
        CommitStateRow(
            kind="NODE",
            key=str(CLASS_CONFIG_A),
            value=str(CLASS_INSTANCE_A),
        ),
    )
    expected_post_index = CommitStateIndex(
        rows=(
            *post_class_rows,
            CommitStateRow(
                kind="NODE",
                key=str(CLASS_CONFIG_B),
                value=str(CLASS_INSTANCE_B),
            ),
            CommitStateRow(
                kind="ATTR",
                key=str(CLASS_INSTANCE_B),
                value=f"{ATTR_CONFIG_B}:beta",
            ),
            CommitStateRow(
                kind="EDGE",
                key=str(REL_CONFIG),
                value=f"{CLASS_INSTANCE_A}->{CLASS_INSTANCE_B}",
            ),
        )
    )
    replacement_ref = (
        build_commit_state_witness(CommitStateIndex(rows=post_class_rows))
        .segments[0]
        .ref()
    )

    post_ref = replace_existing_commit_state_witness_ref_segments(
        pre_witness_ref=pre_witness_ref,
        replacement_segments_by_key={f"class:{CLASS_INSTANCE_A}": replacement_ref},
        post_state_hash=expected_post_index.compute_hash(),
    )
    expected_post_ref = build_commit_state_witness_ref(expected_post_index)

    assert validate_commit_state_witness_ref(post_ref)
    assert post_ref == expected_post_ref
    assert post_ref.witness_hash != pre_witness_ref.witness_hash
    assert post_ref.segment_digests_by_key()[f"class:{CLASS_INSTANCE_B}"] == (
        pre_witness_ref.segment_digests_by_key()[f"class:{CLASS_INSTANCE_B}"]
    )

    post_ref_without_state_hash = replace_existing_commit_state_witness_ref_segments(
        pre_witness_ref=pre_witness_ref,
        replacement_segments_by_key={f"class:{CLASS_INSTANCE_A}": replacement_ref},
    )

    assert validate_commit_state_witness_ref(post_ref_without_state_hash)
    assert post_ref_without_state_hash.state_hash is None
    assert post_ref_without_state_hash.witness_hash == expected_post_ref.witness_hash
    assert post_ref_without_state_hash.row_count == expected_post_ref.row_count


def test_commit_state_witness_ref_rejects_unknown_segment_keys() -> None:
    pre_witness_ref = build_commit_state_witness_ref(_pre_state_index())
    replacement_ref = (
        build_commit_state_witness(
            CommitStateIndex(
                rows=(
                    CommitStateRow(
                        kind="NODE",
                        key=str(CLASS_CONFIG_A),
                        value=str(CLASS_INSTANCE_A),
                    ),
                )
            )
        )
        .segments[0]
        .ref()
    )

    with pytest.raises(ValueError, match="unknown keys"):
        replace_existing_commit_state_witness_ref_segments(
            pre_witness_ref=pre_witness_ref,
            replacement_segments_by_key={"class:not-present": replacement_ref},
            post_state_hash=pre_witness_ref.state_hash,
        )


def test_commit_state_witness_cursor_chunks_existing_ref() -> None:
    witness_ref = build_commit_state_witness_ref(_pre_state_index())

    cursor = build_commit_state_witness_cursor(witness_ref, chunk_size=2)

    assert validate_commit_state_witness_cursor(cursor)
    assert cursor.state_hash == witness_ref.state_hash
    assert cursor.legacy_witness_hash == witness_ref.witness_hash
    assert cursor.row_count == witness_ref.row_count
    assert cursor.segment_count == len(witness_ref.segments)
    assert [chunk.segment_keys for chunk in cursor.chunks] == [
        tuple(segment.key for segment in witness_ref.segments[:2]),
        tuple(segment.key for segment in witness_ref.segments[2:]),
    ]
    assert cursor.cursor_hash == compute_commit_state_witness_cursor_hash(
        cursor.chunks,
    )
    assert cursor.cursor_hash != cursor.legacy_witness_hash
    assert validate_commit_state_witness_cursor_summary(cursor.summary())
    assert cursor.summary().cursor_hash == cursor.cursor_hash
    assert cursor.summary().chunks[0].first_segment_key == (witness_ref.segments[0].key)


def test_commit_state_witness_cursor_replaces_existing_chunk_segment() -> None:
    pre_witness_ref = build_commit_state_witness_ref(_pre_state_index())
    cursor = build_commit_state_witness_cursor(pre_witness_ref, chunk_size=2)
    post_class_rows = (
        CommitStateRow(
            kind="NODE",
            key=str(CLASS_CONFIG_A),
            value=str(CLASS_INSTANCE_A),
        ),
    )
    replacement_ref = (
        build_commit_state_witness(CommitStateIndex(rows=post_class_rows))
        .segments[0]
        .ref()
    )
    expected_post_index = CommitStateIndex(
        rows=(
            *post_class_rows,
            CommitStateRow(
                kind="NODE",
                key=str(CLASS_CONFIG_B),
                value=str(CLASS_INSTANCE_B),
            ),
            CommitStateRow(
                kind="ATTR",
                key=str(CLASS_INSTANCE_B),
                value=f"{ATTR_CONFIG_B}:beta",
            ),
            CommitStateRow(
                kind="EDGE",
                key=str(REL_CONFIG),
                value=f"{CLASS_INSTANCE_A}->{CLASS_INSTANCE_B}",
            ),
        )
    )
    expected_post_ref = build_commit_state_witness_ref(expected_post_index)

    post_cursor = replace_existing_commit_state_witness_cursor_segments(
        cursor=cursor,
        replacement_segments_by_key={f"class:{CLASS_INSTANCE_A}": replacement_ref},
        post_state_hash=expected_post_index.compute_hash(),
    )

    assert validate_commit_state_witness_cursor(post_cursor)
    assert post_cursor.state_hash == expected_post_ref.state_hash
    assert post_cursor.legacy_witness_hash == expected_post_ref.witness_hash
    assert post_cursor.cursor_hash != cursor.cursor_hash
    assert post_cursor.chunks[0].digest != cursor.chunks[0].digest
    assert post_cursor.chunks[1].digest == cursor.chunks[1].digest
    assert post_cursor.segment_digests_by_key()[f"class:{CLASS_INSTANCE_B}"] == (
        cursor.segment_digests_by_key()[f"class:{CLASS_INSTANCE_B}"]
    )


def test_commit_state_witness_cursor_summary_replaces_changed_chunk_only() -> None:
    pre_witness_ref = build_commit_state_witness_ref(_pre_state_index())
    cursor = build_commit_state_witness_cursor(pre_witness_ref, chunk_size=2)
    post_class_rows = (
        CommitStateRow(
            kind="NODE",
            key=str(CLASS_CONFIG_A),
            value=str(CLASS_INSTANCE_A),
        ),
    )
    replacement_ref = (
        build_commit_state_witness(CommitStateIndex(rows=post_class_rows))
        .segments[0]
        .ref()
    )

    post_chunk = replace_commit_state_witness_cursor_chunk_segments(
        chunk=cursor.chunks[0],
        replacement_segments_by_key={replacement_ref.key: replacement_ref},
    )
    post_summary = replace_existing_commit_state_witness_cursor_summary_chunks(
        summary=cursor.summary(),
        replacement_chunks_by_index={post_chunk.index: post_chunk},
    )

    assert validate_commit_state_witness_cursor_summary(post_summary)
    assert post_summary.cursor_hash != cursor.cursor_hash
    assert post_summary.legacy_witness_hash is None
    assert post_summary.chunks[0].digest == post_chunk.digest
    assert post_summary.chunks[1].digest == cursor.summary().chunks[1].digest


def test_commit_state_witness_cursor_rejects_corrupted_chunk() -> None:
    cursor = build_commit_state_witness_cursor(
        build_commit_state_witness_ref(_pre_state_index()),
        chunk_size=2,
    )
    corrupted_cursor = replace(
        cursor,
        chunks=(
            replace(cursor.chunks[0], digest="not-the-real-digest"),
            *cursor.chunks[1:],
        ),
    )

    assert not validate_commit_state_witness_cursor(corrupted_cursor)
    with pytest.raises(ValueError, match="cursor is invalid"):
        replace_existing_commit_state_witness_cursor_segments(
            cursor=corrupted_cursor,
            replacement_segments_by_key={},
        )


def test_commit_state_witness_cursor_rejects_unknown_segment_keys() -> None:
    cursor = build_commit_state_witness_cursor(
        build_commit_state_witness_ref(_pre_state_index()),
        chunk_size=2,
    )
    replacement_ref = (
        build_commit_state_witness(
            CommitStateIndex(
                rows=(
                    CommitStateRow(
                        kind="NODE",
                        key=str(CLASS_CONFIG_A),
                        value=str(CLASS_INSTANCE_A),
                    ),
                )
            )
        )
        .segments[0]
        .ref()
    )

    with pytest.raises(ValueError, match="unknown keys"):
        replace_existing_commit_state_witness_cursor_segments(
            cursor=cursor,
            replacement_segments_by_key={"class:not-present": replacement_ref},
        )


def _pre_state_index() -> CommitStateIndex:
    return CommitStateIndex(
        rows=(
            CommitStateRow(
                kind="NODE",
                key=str(CLASS_CONFIG_A),
                value=str(CLASS_INSTANCE_A),
            ),
            CommitStateRow(
                kind="ATTR",
                key=str(CLASS_INSTANCE_A),
                value=f"{ATTR_CONFIG_A}:alpha",
            ),
            CommitStateRow(
                kind="NODE",
                key=str(CLASS_CONFIG_B),
                value=str(CLASS_INSTANCE_B),
            ),
            CommitStateRow(
                kind="ATTR",
                key=str(CLASS_INSTANCE_B),
                value=f"{ATTR_CONFIG_B}:beta",
            ),
            CommitStateRow(
                kind="EDGE",
                key=str(REL_CONFIG),
                value=f"{CLASS_INSTANCE_A}->{CLASS_INSTANCE_B}",
            ),
        )
    )


def _oig_change(
    *,
    class_instance_id: UUID,
    change_type: ChangeType,
) -> ObjectInstanceGraphChange:
    with disable_autobind():
        change = Change(
            id=uuid4(),
            key=f"class:{class_instance_id}:{change_type.value}",
            change_deltas=[],
            type=change_type,
            created_at=datetime.now(timezone.utc),
        )
        class_change = ClassInstanceChange(
            id=uuid4(),
            change=change,
            change_id=change.id,
            class_instance_id=class_instance_id,
        )
        return ObjectInstanceGraphChange(
            id=uuid4(),
            change=change,
            change_id=change.id,
            type=ObjectInstanceGraphChangeType.object_instance,
            object_instance_graph_identity_id=OIGI_ID,
            object_instance_graph_id=OIG_ID,
            class_instance_changes=[class_change],
            class_instance_relationship_changes=[],
        )
