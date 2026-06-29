from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_history_ontology.commit.commit import Commit
from aware_history_ontology.commit.commit_enums import CommitStatus
from aware_meta.graph.instance.commit.fs_store import FSCommitStore
from aware_meta.graph.instance.commit.payload_refs import (
    export_oig_commit_payload_ref,
    import_oig_commit_payload_ref,
)
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta_ontology.stable_ids import stable_object_instance_graph_commit_id


@pytest.mark.asyncio
async def test_export_oig_commit_payload_ref_carries_verified_file_locator(
    tmp_path,
) -> None:
    store = FSCommitStore(root_dir=tmp_path)
    branch_id = uuid4()
    projection_hash = "CodePackage"
    commit = _make_commit(projection_hash=projection_hash)

    await store.put_commit_file(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit=commit,
    )

    ref = await export_oig_commit_payload_ref(
        root_dir=tmp_path,
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit.commit.id,
        workspace_revision_id=uuid4(),
        revision_code_package_id=uuid4(),
        code_package_id=commit.root_source_object_id,
    )
    metadata = ref.to_metadata()

    assert metadata["ref_schema"] == "aware.oig_commit_payload_ref.v1"
    assert metadata["payload_contract"] == "aware.oig_commit_payload.v1"
    assert metadata["branch_id"] == str(branch_id)
    assert metadata["projection_hash"] == projection_hash
    assert metadata["commit_id"] == str(commit.commit.id)
    assert metadata["domain_commit_id"] == str(commit.commit.id)
    assert metadata["object_instance_graph_commit_id"] == str(commit.id)
    assert metadata["object_instance_graph_identity_id"] == str(
        commit.object_instance_graph_identity_id
    )
    assert metadata["object_instance_graph_id"] == str(commit.object_instance_graph_id)
    assert metadata["graph_hash_post"] == commit.graph_hash_post
    assert (
        metadata["payload_url"]
        == store.commit_file_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit.commit.id,
        )
        .resolve()
        .as_uri()
    )
    assert isinstance(metadata["payload_size_bytes"], int)
    assert len(str(metadata["payload_sha256"])) == 64


@pytest.mark.asyncio
async def test_import_oig_commit_payload_ref_installs_verified_commit(
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

    receipt = await import_oig_commit_payload_ref(
        root_dir=target_root,
        ref=ref.to_metadata(),
    )

    assert receipt.status == "imported"
    assert receipt.wrote_commit is True
    installed = await target_store.get_commit(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit.commit.id,
    )
    assert installed is not None
    assert installed.id == commit.id


@pytest.mark.asyncio
async def test_import_oig_commit_payload_ref_rejects_sha_mismatch(tmp_path) -> None:
    store = FSCommitStore(root_dir=tmp_path)
    branch_id = uuid4()
    projection_hash = "CodePackage"
    commit = _make_commit(projection_hash=projection_hash)
    await store.put_commit_file(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit=commit,
    )
    ref = await export_oig_commit_payload_ref(
        root_dir=tmp_path,
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit.commit.id,
    )
    metadata = {**ref.to_metadata(), "payload_sha256": "0" * 64}

    with pytest.raises(RuntimeError, match="oig_commit_payload_sha256_mismatch"):
        await import_oig_commit_payload_ref(root_dir=tmp_path / "target", ref=metadata)


def _make_commit(
    *,
    projection_hash: str,
    commit_id: UUID | None = None,
) -> ObjectInstanceGraphCommit:
    commit_id = commit_id or uuid4()
    object_instance_graph_identity_id = uuid4()
    object_instance_graph_id = uuid4()
    root_source_object_id = uuid4()
    return ObjectInstanceGraphCommit.model_construct(
        id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            commit_id=commit_id,
        ),
        commit=Commit.model_construct(
            id=commit_id,
            author_id=uuid4(),
            key=str(commit_id),
            created_at=datetime.now(UTC),
            status=CommitStatus.local,
            lane_id=uuid4(),
            commit_parents=[],
        ),
        object_instance_graph_key="code-package",
        object_instance_graph_name="code-package",
        object_instance_graph_description=None,
        root_class_config_id=uuid4(),
        root_source_object_id=root_source_object_id,
        graph_hash_post=f"sha256:{uuid4().hex}",
        graph_hash_pre="",
        projection_hash=projection_hash,
        source_language=CodeLanguage.python,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
        commit_id=commit_id,
        object_instance_graph_changes=[],
    )
