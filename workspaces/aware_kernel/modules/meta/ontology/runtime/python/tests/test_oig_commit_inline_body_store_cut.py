from __future__ import annotations

from datetime import UTC, datetime
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
    object_instance_graph_changes_from_body,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.payload_refs import (
    export_oig_commit_payload_ref,
    import_oig_commit_payload_ref,
)
from aware_meta_ontology.class_.class_instance_change import ClassInstanceChange
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


@pytest.mark.asyncio
async def test_store_writes_envelope_plus_inline_body_without_legacy_commit_payload(
    tmp_path,
) -> None:
    store = FSCommitStore(root_dir=tmp_path)
    branch_id = uuid4()
    projection_hash = "WorkspaceRevision"
    commit = _make_commit(projection_hash=projection_hash)

    assert (
        await store.put_commit_file(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit=commit,
        )
        is True
    )

    envelope_path = store.commit_file_path(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit.commit.id,
    )
    body_path = store.commit_body_file_path(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit.commit.id,
    )
    envelope_payload = json.loads(envelope_path.read_text(encoding="utf-8"))
    body_payload = json.loads(body_path.read_text(encoding="utf-8"))

    assert "object_instance_graph_changes" not in envelope_payload
    assert envelope_payload["body_contract"] == OIG_COMMIT_BODY_CONTRACT
    assert envelope_payload["body_ref"] == body_path.name
    assert body_payload["c"] == OIG_COMMIT_BODY_CONTRACT
    assert "object_instance_graph_changes" not in body_payload

    body_text = body_path.read_text(encoding="utf-8")
    body_path.unlink()
    shallow_commit = await store.get_commit(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit.commit.id,
    )
    body_path.write_text(body_text, encoding="utf-8")
    assert shallow_commit is not None
    assert shallow_commit.commit.id == commit.commit.id
    assert shallow_commit.graph_hash_pre == commit.graph_hash_pre
    assert shallow_commit.graph_hash_post == commit.graph_hash_post
    assert shallow_commit.object_instance_graph_changes == []

    envelope = await store.get_commit_envelope(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit.commit.id,
    )
    body = await store.get_commit_body(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit.commit.id,
    )
    assert envelope is not None
    assert body is not None
    assert envelope.commit_id == commit.commit.id
    assert envelope.object_instance_graph_commit_id == commit.id
    assert body.commit_id == commit.commit.id
    changes = object_instance_graph_changes_from_body(body)
    assert len(changes) == 1
    assert changes[0].class_instance_changes[0].class_instance_id == (
        commit.object_instance_graph_changes[0]
        .class_instance_changes[0]
        .class_instance_id
    )

    lineage = [
        record
        async for record in store.iter_lineage_forward_records(
            branch_id=branch_id,
            projection_hash=projection_hash,
            head_commit_id=commit.commit.id,
            stop_at_commit_id=None,
        )
    ]
    assert [record.commit_id for record in lineage] == [commit.commit.id]


@pytest.mark.asyncio
async def test_payload_ref_import_export_uses_envelope_and_body_payloads(
    tmp_path,
) -> None:
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_store = FSCommitStore(root_dir=source_root)
    target_store = FSCommitStore(root_dir=target_root)
    branch_id = uuid4()
    projection_hash = "CodePackage"
    commit = _make_commit(projection_hash=projection_hash)
    await source_store.put_commit_file(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit=commit,
    )

    ref = await export_oig_commit_payload_ref(
        root_dir=source_root,
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit.commit.id,
    )
    metadata = ref.to_metadata()

    assert metadata["ref_schema"] == "aware.oig_commit_payload_ref.v2"
    assert metadata["payload_contract"] == "aware.oig_commit_envelope.v2"
    assert metadata["body_contract"] == OIG_COMMIT_BODY_CONTRACT
    assert str(metadata["payload_url"]).endswith(f"{commit.commit.id}.json")
    assert str(metadata["body_url"]).endswith(f"{commit.commit.id}.body.json")

    receipt = await import_oig_commit_payload_ref(
        root_dir=target_root,
        ref=metadata,
    )

    assert receipt.status == "imported"
    assert receipt.wrote_commit is True
    assert len(receipt.body_sha256) == 64
    installed_envelope = await target_store.get_commit_envelope(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit.commit.id,
    )
    installed_body = await target_store.get_commit_body(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit.commit.id,
    )
    assert installed_envelope is not None
    assert installed_envelope.object_instance_graph_commit_id == commit.id
    assert installed_body is not None
    assert installed_body.commit_id == commit.commit.id


def _make_commit(
    *,
    projection_hash: str,
    commit_id: UUID | None = None,
) -> ObjectInstanceGraphCommit:
    commit_id = commit_id or uuid4()
    object_instance_graph_identity_id = uuid4()
    object_instance_graph_id = uuid4()
    root_source_object_id = uuid4()
    root_class_config_id = uuid4()
    class_instance_id = uuid4()
    root_change = _change("root", ChangeType.update)
    class_change = _change(
        "class-instance",
        ChangeType.create,
        deltas=[
            _delta(
                change_id=uuid4(),
                position=0,
                property_name="source_object_id",
                payload={"value": root_source_object_id},
            ),
            _delta(
                change_id=uuid4(),
                position=1,
                property_name="class_config_id",
                payload={"value": root_class_config_id},
            ),
        ],
    )
    class_instance_change = ClassInstanceChange.model_construct(
        id=uuid4(),
        class_instance_id=class_instance_id,
        change=class_change,
        change_id=class_change.id,
        attribute_changes=[],
    )
    object_change = ObjectInstanceGraphChange.model_construct(
        id=uuid4(),
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
        type=ObjectInstanceGraphChangeType.object_instance,
        change=root_change,
        change_id=root_change.id,
        class_instance_changes=[class_instance_change],
        class_instance_relationship_changes=[],
    )
    return ObjectInstanceGraphCommit.model_construct(
        id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            commit_id=commit_id,
        ),
        commit=Commit.model_construct(
            id=commit_id,
            author_id=uuid4(),
            key=str(commit_id),
            created_at=datetime(2026, 7, 3, 10, 45, 0, tzinfo=UTC),
            status=CommitStatus.local,
            lane_id=uuid4(),
            commit_parents=[],
        ),
        object_instance_graph_key="workspace-revision",
        object_instance_graph_name="workspace-revision",
        object_instance_graph_description=None,
        root_class_config_id=root_class_config_id,
        root_source_object_id=root_source_object_id,
        graph_hash_post=f"sha256:{uuid4().hex}",
        graph_hash_pre="",
        projection_hash=projection_hash,
        source_language=CodeLanguage.python,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
        commit_id=commit_id,
        object_instance_graph_changes=[object_change],
    )


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
        created_at=datetime(2026, 7, 3, 10, 45, 0, tzinfo=UTC),
        type=change_type,
        change_deltas=[
            _rebind_delta(delta=delta, change_id=change_id) for delta in (deltas or [])
        ],
    )


def _delta(
    *,
    change_id: UUID,
    position: int,
    property_name: str,
    payload: object,
) -> ChangeDelta:
    return ChangeDelta.model_construct(
        id=uuid4(),
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
