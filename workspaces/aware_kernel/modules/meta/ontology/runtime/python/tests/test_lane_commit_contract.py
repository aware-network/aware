from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_history_ontology.commit.commit import Commit
from aware_history_ontology.commit.commit_enums import CommitStatus
from aware_meta.graph.instance.commit import fs_store as fs_store_module
from aware_meta.graph.instance.commit.committer import FSLaneCommitter
from aware_meta.graph.instance.commit.contract import (
    CommitEnvelopeReader,
    LaneCommitBackend,
    LaneCommitStore,
    LaneCommitter,
    ObjectInstanceGraphCommitEnvelope,
    ObjectInstanceGraphCommitIdentitySidecar,
)
from aware_meta.graph.instance.commit.fs_store import (
    FSCommitStore,
    ObjectInstanceGraphCommitEnvelope as LegacyCommitEnvelope,
    ObjectInstanceGraphCommitIdentitySidecar as LegacyCommitIdentitySidecar,
)
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta_ontology.stable_ids import stable_object_instance_graph_commit_id


def test_filesystem_store_satisfies_neutral_commit_protocols(tmp_path: Path) -> None:
    store = FSCommitStore(root_dir=tmp_path)
    committer = FSLaneCommitter(store=store)

    assert isinstance(store, CommitEnvelopeReader)
    assert isinstance(store, LaneCommitStore)
    assert isinstance(store, LaneCommitBackend)
    assert isinstance(committer, LaneCommitter)


def test_legacy_fs_store_contract_types_are_neutral_reexports() -> None:
    assert LegacyCommitEnvelope is ObjectInstanceGraphCommitEnvelope
    assert LegacyCommitIdentitySidecar is ObjectInstanceGraphCommitIdentitySidecar


@pytest.mark.asyncio
async def test_neutral_envelope_reader_uses_envelope_index_without_body_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
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
    commit_path = store.commit_file_path(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit.commit.id,
    )
    _fail_on_commit_body_read(monkeypatch=monkeypatch, commit_path=commit_path)

    reader: CommitEnvelopeReader = store
    envelope = await reader.get_commit_envelope(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit.commit.id,
    )
    sidecar = await reader.get_commit_identity_sidecar(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit.commit.id,
    )

    assert envelope is not None
    assert envelope.commit_id == commit.commit.id
    assert envelope.graph_hash_post == commit.graph_hash_post
    assert sidecar is not None
    assert sidecar.commit_id == commit.commit.id
    metrics = reader.commit_envelope_read_metrics_snapshot()
    assert metrics["commit_envelope_index_hit_count"] == 1
    assert metrics["commit_envelope_full_body_fallback_count"] == 0
    assert metrics["commit_identity_sidecar_index_hit_count"] == 1
    assert metrics["commit_identity_sidecar_full_body_fallback_count"] == 0


@pytest.mark.asyncio
async def test_neutral_envelope_reader_metrics_count_full_body_fallback(
    tmp_path: Path,
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
    lane_dir = tmp_path / ".aware" / "oig" / str(branch_id) / projection_hash
    (lane_dir / "indexes" / "commit_envelopes" / f"{commit.commit.id}.json").unlink()
    (
        lane_dir / "indexes" / "commit_identity_sidecars" / f"{commit.commit.id}.json"
    ).unlink()

    reader: CommitEnvelopeReader = store
    envelope = await reader.get_commit_envelope(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit.commit.id,
    )
    sidecar = await reader.get_commit_identity_sidecar(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit.commit.id,
    )

    assert envelope is not None
    assert sidecar is not None
    metrics = reader.commit_envelope_read_metrics_snapshot()
    assert metrics["commit_envelope_index_hit_count"] == 0
    assert metrics["commit_envelope_full_body_fallback_count"] == 1
    assert metrics["commit_identity_sidecar_index_hit_count"] == 0
    assert metrics["commit_identity_sidecar_full_body_fallback_count"] == 1
    assert metrics["commit_envelope_fallback_failure_count"] == 0
    assert metrics["commit_identity_sidecar_fallback_failure_count"] == 0


def _fail_on_commit_body_read(
    *,
    monkeypatch: pytest.MonkeyPatch,
    commit_path: Path,
) -> None:
    original_reader = fs_store_module._SESSION_JSON_FILE_CACHE.try_read_json_object

    def _guarded_try_read_json_object(
        path: Path,
        *,
        log_prefix: str,
    ) -> fs_store_module.JsonObject | None:
        if path == commit_path:
            raise AssertionError("envelope reader must not read commit body")
        return original_reader(path, log_prefix=log_prefix)

    monkeypatch.setattr(
        fs_store_module._SESSION_JSON_FILE_CACHE,
        "try_read_json_object",
        _guarded_try_read_json_object,
    )


def _make_commit(
    *,
    projection_hash: str,
    commit_id: UUID | None = None,
    object_instance_graph_identity_id: UUID | None = None,
    object_instance_graph_id: UUID | None = None,
    graph_hash_post: str | None = None,
) -> ObjectInstanceGraphCommit:
    commit_id = commit_id or uuid4()
    object_instance_graph_identity_id = object_instance_graph_identity_id or uuid4()
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
        root_source_object_id=uuid4(),
        graph_hash_post=graph_hash_post or f"sha256:{uuid4().hex}",
        graph_hash_pre="",
        projection_hash=projection_hash,
        source_language=CodeLanguage.python,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id or uuid4(),
        commit_id=commit_id,
        object_instance_graph_changes=[],
    )
