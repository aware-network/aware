"""Physical review retention through accepted private FileSystem custody."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from aware_file_system import private_directory as physical
from aware_workspace_fs_adapter.architecture_setup_review import (
    _LIMITS,
    CHUNK_BYTES,
    FilesystemSetupReview,
)
from aware_workspace_sdk.architecture_setup_review_codec import SetupReviewValueError


@pytest.fixture
def storage(tmp_path):
    repository = tmp_path / "repository"
    repository.mkdir()
    evidence = tmp_path / "evidence"
    evidence.mkdir(mode=0o700)
    store = FilesystemSetupReview(
        repository_root=repository,
        evidence_root=evidence,
        authority_manifest_locator="aware.protocol.toml",
    )
    try:
        yield store
    finally:
        store.release()


def test_frozen_native_caps_are_not_replaced_with_larger_defaults():
    from dataclasses import asdict

    repository = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "aware.repo.toml").exists()
    )
    frozen = json.loads(
        (
            repository
            / "docs/reports/workspace-a1-reviewed-workflow-interface-inputs-20261016-r2.json"
        ).read_text()
    )
    assert asdict(_LIMITS) == frozen["native_sequence_limits"]


def test_four_original_chunks_roundtrip_with_full_cleanup(storage):
    raw = bytes(range(256)) * (4 * CHUNK_BYTES // 256)
    capture = storage.write_capture(raw, attempt="a" * 64, kind="command_v1")
    assert len(capture.chunks) == 4
    assert storage.read_capture(capture, attempt="a" * 64) == raw
    retention = storage.retention()
    assert len(retention.sequence_observations) == len(retention.sequence_cleanup) == 1
    assert retention.sequence_cleanup[0].sequence.release == "confirmed"
    assert all(row.original.cleanup.outcome == "closed" for row in storage.reads)


@pytest.mark.parametrize(
    "budget", ["metadata_bytes", "metadata_files", "logical", "raw_bytes", "raw_files"]
)
def test_budget_refusal_precedes_next_physical_effect(storage, budget):
    limits = {
        "metadata_bytes": 2 * CHUNK_BYTES,
        "metadata_files": 8,
        "logical": 64 * CHUNK_BYTES,
        "raw_bytes": 32 * CHUNK_BYTES,
        "raw_files": 32,
    }
    setattr(storage, budget, limits[budget])
    with pytest.raises(SetupReviewValueError):
        if budget.startswith("raw"):
            storage.write_capture(b"next", attempt="a" * 64, kind="command_v1")
        else:
            storage.write_metadata("a1-next.json", b"next")
    assert not list(storage.root.iterdir())


def test_publication_collision_keeps_original_bytes_and_full_refusal(storage):
    storage.write_metadata("a1-existing.json", b"original")
    with pytest.raises(physical.PrivateDirectoryRefusal):
        storage.write_metadata("a1-existing.json", b"replacement")
    assert (storage.root / "a1-existing.json").read_bytes() == b"original"
    assert storage.retention().physical_refusal is not None


def test_read_failure_retains_complete_original_owner_evidence(storage):
    with pytest.raises(physical.PrivateDirectoryRefusal):
        storage.read(
            "a1-absent.json",
            size=3,
            sha256="sha256:" + hashlib.sha256(b"abc").hexdigest(),
        )
    assert storage.retention().physical_refusal is not None
    assert not storage.retention().ledger_complete


def test_preparation_and_step_failures_release_child_once(storage, monkeypatch):
    execute = physical.execute_next_private_file_step
    calls = []

    def stopped(child, *, expected_ordinal):
        execute(child, expected_ordinal=expected_ordinal)
        calls.append(expected_ordinal)
        raise OSError("lost return after original step")

    monkeypatch.setattr(physical, "execute_next_private_file_step", stopped)
    with pytest.raises(OSError):
        storage.write_metadata("a1-lost.json", b"known prefix")
    assert calls == [0]
    retention = storage.retention()
    assert len(retention.sequence_cleanup) == 1
    assert retention.sequence_cleanup[0].sequence.release == "confirmed"
    assert not retention.ledger_complete
    assert (
        physical.observe_private_directory(storage.directory).active_sequence_ref
        is None
    )
