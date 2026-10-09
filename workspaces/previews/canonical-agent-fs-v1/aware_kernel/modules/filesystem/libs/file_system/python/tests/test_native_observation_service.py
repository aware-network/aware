from __future__ import annotations

import hashlib
import os
import threading
import time
from pathlib import Path

import pytest

from aware_file_system.native_observation_service import (
    NativeObservationService,
    NativeObservationServiceError,
    ObservationWatchMode,
    RustObservationServiceBuildConfig,
    prepare_rust_observation_service_binary,
)
from aware_file_system.native_snapshot import collect_python_workspace_snapshot


@pytest.fixture(scope="module")
def observation_service_binary(tmp_path_factory: pytest.TempPathFactory) -> Path:
    target_dir = tmp_path_factory.mktemp("observation-service-target")
    return prepare_rust_observation_service_binary(
        RustObservationServiceBuildConfig(target_dir=target_dir)
    )


def test_persistent_observation_service_lifecycle_and_restart(
    tmp_path: Path,
    observation_service_binary: Path,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "update.txt").write_text("before\n", encoding="utf-8")
    (root / "delete.txt").write_text("delete\n", encoding="utf-8")
    cache = tmp_path / "state" / "observation.cache"

    with NativeObservationService(
        binary_path=observation_service_binary,
        workspace_root=root,
        cache_path=cache,
    ) as service:
        first = service.observe("first")
        assert first["status"] == "exact"
        assert first["cache_start_state"] == "missing"
        assert first["cache_written"] is True
        assert first["added"] == ["delete.txt", "update.txt"]
        assert first["modified"] == []
        assert first["deleted"] == []
        first_generation = first["to_generation"]
        cache_mtime_ns = cache.stat().st_mtime_ns

        noop = service.observe("noop")
        assert noop["cache_written"] is False
        assert noop["from_generation"] == first_generation
        assert noop["to_generation"] == first_generation
        assert noop["added"] == noop["modified"] == noop["deleted"] == []
        assert cache.stat().st_mtime_ns == cache_mtime_ns

        (root / "update.txt").write_text("after-with-new-size\n", encoding="utf-8")
        (root / "delete.txt").unlink()
        (root / "created.txt").write_text("created\n", encoding="utf-8")
        changed = service.observe("changed")
        assert changed["cache_written"] is True
        assert changed["added"] == ["created.txt"]
        assert changed["modified"] == ["update.txt"]
        assert changed["deleted"] == ["delete.txt"]
        assert changed["to_generation"] == first_generation + 1
        assert len(changed["snapshot_digest"]) == 64
        assert len(changed["delta_digest"]) == 64

        snapshot = service.snapshot()
        assert [entry["path"] for entry in snapshot["entries"]] == [
            "created.txt",
            "update.txt",
        ]
        changed_digest = changed["snapshot_digest"]
        changed_generation = changed["to_generation"]

    with NativeObservationService(
        binary_path=observation_service_binary,
        workspace_root=root,
        cache_path=cache,
    ) as restarted:
        restart = restarted.observe("restart")
        assert restart["cache_start_state"] == "loaded"
        assert restart["cache_written"] is False
        assert restart["from_generation"] == changed_generation
        assert restart["to_generation"] == changed_generation
        assert restart["snapshot_digest"] == changed_digest


def test_observation_service_recovery_states(
    tmp_path: Path,
    observation_service_binary: Path,
) -> None:
    root = tmp_path / "root-one"
    root.mkdir()
    (root / "source.txt").write_text("source\n", encoding="utf-8")
    cache = tmp_path / "observation.cache"

    with NativeObservationService(
        binary_path=observation_service_binary,
        workspace_root=root,
        cache_path=cache,
    ) as service:
        service.observe("seed")

    stale_temp = cache.with_name(f".{cache.name}.999999.123456.tmp")
    stale_temp.write_bytes(b"interrupted cache replacement")

    other_root = tmp_path / "root-two"
    other_root.mkdir()
    (other_root / "other.txt").write_text("other\n", encoding="utf-8")
    with NativeObservationService(
        binary_path=observation_service_binary,
        workspace_root=other_root,
        cache_path=cache,
    ) as root_mismatch:
        report = root_mismatch.observe("root-mismatch")
        assert report["cache_start_state"] == "root_mismatch"
        assert report["cache_written"] is True
        assert report["stale_cache_temp_files_removed"] == 1
        assert not stale_temp.exists()

    cache.write_bytes(b"corrupt")
    with NativeObservationService(
        binary_path=observation_service_binary,
        workspace_root=root,
        cache_path=cache,
    ) as corrupt:
        report = corrupt.observe("corrupt")
        assert report["cache_start_state"] == "corrupt"
        assert report["cache_written"] is True

    raw = cache.read_bytes()
    payload = bytearray(raw[:-32])
    payload[:16] = b"INCOMPATIBLE!!!\0"
    cache.write_bytes(payload + hashlib.sha256(payload).digest())
    with NativeObservationService(
        binary_path=observation_service_binary,
        workspace_root=root,
        cache_path=cache,
    ) as incompatible:
        report = incompatible.observe("incompatible")
        assert report["cache_start_state"] == "incompatible"
        assert report["cache_written"] is True


def test_observation_service_tracks_gitignore_semantic_changes(
    tmp_path: Path,
    observation_service_binary: Path,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    ignore_file = root / ".gitignore"
    ignored_source = root / "admitted-later.txt"
    ignore_file.write_text("admitted-later.txt\n", encoding="utf-8")
    ignored_source.write_text("source\n", encoding="utf-8")
    cache = tmp_path / "state.cache"

    with NativeObservationService(
        binary_path=observation_service_binary,
        workspace_root=root,
        cache_path=cache,
    ) as service:
        first = service.observe("ignored")
        assert first["added"] == [".gitignore"]

        ignore_file.write_text("", encoding="utf-8")
        admitted = service.observe("admitted")
        assert admitted["added"] == ["admitted-later.txt"]
        assert admitted["modified"] == [".gitignore"]
        assert admitted["deleted"] == []
        assert admitted["to_generation"] == first["to_generation"] + 1


def test_snapshot_requires_observation_when_cache_is_missing(
    tmp_path: Path,
    observation_service_binary: Path,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    service = NativeObservationService(
        binary_path=observation_service_binary,
        workspace_root=root,
        cache_path=tmp_path / "missing.cache",
    )
    try:
        service.ping()
        with pytest.raises(NativeObservationServiceError, match="not ready"):
            service.snapshot()
    finally:
        service.close()


def test_observation_request_id_rejects_line_breaks(
    tmp_path: Path,
    observation_service_binary: Path,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    with NativeObservationService(
        binary_path=observation_service_binary,
        workspace_root=root,
        cache_path=tmp_path / "state.cache",
    ) as service:
        with pytest.raises(ValueError, match="line breaks"):
            service.observe("bad\nrequest")


def test_event_hint_poll_suppresses_idle_scan_and_reconciles_changes(
    tmp_path: Path,
    observation_service_binary: Path,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "source.txt").write_text("before\n", encoding="utf-8")
    with NativeObservationService(
        binary_path=observation_service_binary,
        workspace_root=root,
        cache_path=tmp_path / "state.cache",
        reconciliation_interval_s=10.0,
    ) as service:
        startup = service.poll("startup")
        assert startup["status"] == "exact"
        assert startup["observation_mode"] == "full_reconciliation"
        assert startup["reconciliation_cause"] == "startup"
        watcher_ready = service.wait_for_watcher_ready()
        assert watcher_ready["reconciliation_cause"] == "watcher_ready"
        assert service.health()["watcher"]["state"] == "active"

        idle = service.poll("idle")
        assert idle["status"] == "maintained"
        assert idle["observation_mode"] == "maintained_no_hint"
        assert idle["scan_ns"] == 0
        assert idle["cache_written"] is False

        (root / "source.txt").write_text("after-with-new-size\n", encoding="utf-8")
        changed = _poll_until_event_reconciliation(service, "changed")
        assert changed["status"] == "exact"
        assert changed["modified"] == ["source.txt"]
        assert changed["hint_event_count"] > 0
        assert changed["scan_ns"] > 0
        assert changed["observation_mode"] == "dirty_path_reconciliation"
        assert changed["reconciled_scope_count"] == 1
        assert changed["directories_scanned"] == 0
        assert changed["files_seen"] == 1
        assert changed["persistence_mode"] == "journal_append"
        assert changed["checkpoint_written"] is False
        assert changed["journal_frame_count"] == 1
        assert changed["digest_backend_kind"] == "rustcrypto_sha2_asm_optimized"
        assert changed["snapshot_digest"] == collect_python_workspace_snapshot(
            root
        ).inventory_digest


def test_event_hint_journal_replays_exact_changes_across_service_restart(
    tmp_path: Path,
    observation_service_binary: Path,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    modified_path = root / "modified.txt"
    deleted_path = root / "deleted.txt"
    modified_path.write_text("before\n", encoding="utf-8")
    deleted_path.write_text("delete\n", encoding="utf-8")
    cache = tmp_path / "state.cache"

    with NativeObservationService(
        binary_path=observation_service_binary,
        workspace_root=root,
        cache_path=cache,
        reconciliation_interval_s=3600.0,
    ) as service:
        startup = service.initialize_observation("startup")
        service.wait_for_watcher_ready()
        base_cache_mtime_ns = cache.stat().st_mtime_ns

        created_path = root / "created.txt"
        created_path.write_text("created\n", encoding="utf-8")
        created = _poll_until_event_reconciliation(service, "created")
        assert created["added"] == ["created.txt"]
        assert created["persistence_mode"] == "journal_append"

        modified_path.write_text("after-with-new-size\n", encoding="utf-8")
        modified = _poll_until_event_reconciliation(service, "modified")
        assert modified["modified"] == ["modified.txt"]
        assert modified["persistence_mode"] == "journal_append"

        deleted_path.unlink()
        deleted = _poll_until_event_reconciliation(service, "deleted")
        assert deleted["deleted"] == ["deleted.txt"]
        assert deleted["persistence_mode"] == "journal_append"
        assert deleted["journal_frame_count"] == 3
        assert cache.stat().st_mtime_ns == base_cache_mtime_ns
        expected_generation = deleted["to_generation"]
        expected_digest = deleted["snapshot_digest"]
        assert expected_generation == startup["to_generation"] + 3

    with NativeObservationService(
        binary_path=observation_service_binary,
        workspace_root=root,
        cache_path=cache,
    ) as restarted:
        replayed = restarted.observe("restart")
        assert replayed["cache_start_state"] == "loaded"
        assert replayed["cache_written"] is False
        assert replayed["from_generation"] == expected_generation
        assert replayed["to_generation"] == expected_generation
        assert replayed["journal_frame_count"] == 3
        assert replayed["snapshot_digest"] == expected_digest
        assert replayed["snapshot_digest"] == collect_python_workspace_snapshot(
            root
        ).inventory_digest


def test_event_hint_journal_truncates_torn_tail_to_last_complete_generation(
    tmp_path: Path,
    observation_service_binary: Path,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    source = root / "source.txt"
    source.write_text("base\n", encoding="utf-8")
    cache = tmp_path / "state.cache"
    journal = Path(f"{cache}.journal")

    with NativeObservationService(
        binary_path=observation_service_binary,
        workspace_root=root,
        cache_path=cache,
        reconciliation_interval_s=3600.0,
    ) as service:
        service.initialize_observation("startup")
        service.wait_for_watcher_ready()

        source.write_text("first-acknowledged-state\n", encoding="utf-8")
        first = _poll_until_event_reconciliation(service, "first")
        first_stat = source.stat()
        first_journal_size = journal.stat().st_size
        first_generation = first["to_generation"]
        first_digest = first["snapshot_digest"]

        source.write_text("second-acknowledged-state-with-new-size\n", encoding="utf-8")
        second = _poll_until_event_reconciliation(service, "second")
        assert second["journal_frame_count"] == 2
        complete_journal_size = journal.stat().st_size
        assert complete_journal_size > first_journal_size

    torn_journal_size = complete_journal_size - 7
    with journal.open("r+b") as stream:
        stream.truncate(torn_journal_size)
    source.write_text("first-acknowledged-state\n", encoding="utf-8")
    os.utime(source, ns=(first_stat.st_atime_ns, first_stat.st_mtime_ns))

    with NativeObservationService(
        binary_path=observation_service_binary,
        workspace_root=root,
        cache_path=cache,
    ) as restarted:
        recovered = restarted.observe("recover-torn-tail")
        assert recovered["cache_start_state"] == "loaded"
        assert recovered["cache_written"] is False
        assert recovered["from_generation"] == first_generation
        assert recovered["to_generation"] == first_generation
        assert recovered["journal_frame_count"] == 1
        assert recovered["journal_tail_bytes_removed"] == (
            torn_journal_size - first_journal_size
        )
        assert journal.stat().st_size == first_journal_size
        assert recovered["snapshot_digest"] == first_digest
        assert recovered["snapshot_digest"] == collect_python_workspace_snapshot(
            root
        ).inventory_digest


def test_dirty_path_create_delete_and_periodic_audit_identity(
    tmp_path: Path,
    observation_service_binary: Path,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    anchor = root / "anchor.txt"
    anchor.write_text("anchor\n", encoding="utf-8")
    with NativeObservationService(
        binary_path=observation_service_binary,
        workspace_root=root,
        cache_path=tmp_path / "state.cache",
        reconciliation_interval_s=0.1,
    ) as service:
        service.initialize_observation("startup")
        service.wait_for_watcher_ready()

        created_path = root / "created.txt"
        created_path.write_text("created\n", encoding="utf-8")
        created = _poll_until_event_reconciliation(service, "created")
        assert created["observation_mode"] == "dirty_path_reconciliation"
        assert created["added"] == ["created.txt"]
        assert created["snapshot_digest"] == collect_python_workspace_snapshot(
            root
        ).inventory_digest

        created_path.unlink()
        deleted = _poll_until_event_reconciliation(service, "deleted")
        assert deleted["observation_mode"] == "dirty_path_reconciliation"
        assert deleted["deleted"] == ["created.txt"]
        assert deleted["snapshot_digest"] == collect_python_workspace_snapshot(
            root
        ).inventory_digest

        time.sleep(0.11)
        periodic = service.poll("periodic-after-dirty")
        assert periodic["observation_mode"] == "full_reconciliation"
        assert periodic["reconciliation_cause"] == "periodic"
        assert periodic["snapshot_digest"] == deleted["snapshot_digest"]


def test_event_hint_poll_forces_periodic_exact_reconciliation(
    tmp_path: Path,
    observation_service_binary: Path,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "source.txt").write_text("source\n", encoding="utf-8")
    with NativeObservationService(
        binary_path=observation_service_binary,
        workspace_root=root,
        cache_path=tmp_path / "state.cache",
        reconciliation_interval_s=0.02,
    ) as service:
        service.poll("startup")
        service.wait_for_watcher_ready()
        assert service.poll("idle")["observation_mode"] == "maintained_no_hint"
        time.sleep(0.03)
        periodic = service.poll("periodic")
        assert periodic["status"] == "exact"
        assert periodic["reconciliation_cause"] == "periodic"


def test_reconciliation_only_mode_never_claims_maintained_no_hint(
    tmp_path: Path,
    observation_service_binary: Path,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    source = root / "source.txt"
    source.write_text("before\n", encoding="utf-8")
    with NativeObservationService(
        binary_path=observation_service_binary,
        workspace_root=root,
        cache_path=tmp_path / "state.cache",
        reconciliation_interval_s=3600.0,
        watch_mode=ObservationWatchMode.RECONCILIATION_ONLY,
    ) as service:
        startup = service.initialize_observation("startup")
        assert startup["status"] == "exact"
        health = service.health()["watcher"]
        assert health["state"] == "reconciliation_only"
        assert health["backend"] == "none_exact_reconciliation"
        assert health["watched_directory_count"] == 0
        assert health["total_error_count"] == 0

        unchanged = service.wait_for_watcher_ready(request_id="exact-noop")
        assert unchanged["status"] == "exact"
        assert unchanged["observation_mode"] == "full_reconciliation"
        assert unchanged["reconciliation_cause"] == "watch_unavailable"
        assert unchanged["scan_ns"] > 0

        source.write_text("after-with-new-size\n", encoding="utf-8")
        changed = service.poll("changed")
        assert changed["status"] == "exact"
        assert changed["reconciliation_cause"] == "watch_unavailable"
        assert changed["modified"] == ["source.txt"]


def test_observation_watch_mode_is_explicit(
    tmp_path: Path,
    observation_service_binary: Path,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    with pytest.raises(ValueError, match="watch_mode must be one of"):
        NativeObservationService(
            binary_path=observation_service_binary,
            workspace_root=root,
            cache_path=tmp_path / "state.cache",
            watch_mode="auto",
        )


def test_event_hint_poll_converges_nested_directory_rename_delete_and_ignore(
    tmp_path: Path,
    observation_service_binary: Path,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    ignore_file = root / ".gitignore"
    ignore_file.write_text("admitted.txt\n", encoding="utf-8")
    (root / "admitted.txt").write_text("hidden\n", encoding="utf-8")
    with NativeObservationService(
        binary_path=observation_service_binary,
        workspace_root=root,
        cache_path=tmp_path / "state.cache",
        reconciliation_interval_s=10.0,
    ) as service:
        service.initialize_observation("startup")
        service.wait_for_watcher_ready()

        nested = root / "nested"
        nested.mkdir()
        source = nested / "source.txt"
        source.write_text("created\n", encoding="utf-8")
        created = _poll_until_event_reconciliation(service, "nested-create")
        assert created["added"] == ["nested/source.txt"]
        assert created["observation_mode"] == "full_reconciliation"

        registration_ready = dict(service.poll("nested-watch-registration-ready"))
        assert registration_ready["reconciliation_cause"] == "watcher_ready"
        assert registration_ready["observation_mode"] == "full_reconciliation"
        assert registration_ready["added"] == []
        assert registration_ready["modified"] == []
        assert registration_ready["deleted"] == []

        source.write_text("updated-with-new-size\n", encoding="utf-8")
        updated = _poll_until_event_reconciliation(service, "nested-update")
        assert updated["modified"] == ["nested/source.txt"]
        assert updated["observation_mode"] == "dirty_path_reconciliation"

        renamed = nested / "renamed.txt"
        source.rename(renamed)
        moved = _poll_until_event_reconciliation(service, "nested-rename")
        assert moved["added"] == ["nested/renamed.txt"]
        assert moved["deleted"] == ["nested/source.txt"]
        assert moved["observation_mode"] == "full_reconciliation"

        renamed.unlink()
        deleted = _poll_until_event_reconciliation(service, "nested-delete")
        assert deleted["deleted"] == ["nested/renamed.txt"]
        assert deleted["observation_mode"] == "dirty_path_reconciliation"

        ignore_file.write_text("", encoding="utf-8")
        admitted = _poll_until_event_reconciliation(service, "ignore-change")
        assert admitted["added"] == ["admitted.txt"]
        assert admitted["modified"] == [".gitignore"]
        assert admitted["observation_mode"] == "full_reconciliation"


def test_event_hint_poll_converges_atomic_save_and_bounded_burst_churn(
    tmp_path: Path,
    observation_service_binary: Path,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    source = root / "source.txt"
    source.write_text("before\n", encoding="utf-8")
    with NativeObservationService(
        binary_path=observation_service_binary,
        workspace_root=root,
        cache_path=tmp_path / "state.cache",
        reconciliation_interval_s=10.0,
    ) as service:
        service.initialize_observation("startup")
        service.wait_for_watcher_ready()

        replacement = root / ".source.txt.atomic"
        replacement.write_text("after-with-new-size\n", encoding="utf-8")
        replacement.replace(source)
        for index in range(256):
            (root / f"burst-{index:03d}.txt").write_text(
                f"burst-{index}\n",
                encoding="utf-8",
            )

        changed = _poll_until_event_reconciliation(service, "atomic-burst")
        assert changed["modified"] == ["source.txt"]
        assert changed["added"] == [f"burst-{index:03d}.txt" for index in range(256)]
        assert changed["hint_event_count"] > 0
        assert len(changed["hint_paths"]) <= 64
        assert changed["hint_paths_truncated"] is True

        for index in range(256):
            (root / f"burst-{index:03d}.txt").unlink()
        deleted = _poll_until_event_reconciliation(service, "burst-delete")
        assert deleted["deleted"] == [f"burst-{index:03d}.txt" for index in range(256)]
        assert len(deleted["hint_paths"]) <= 64


@pytest.mark.skipif(os.name == "nt", reason="uses a POSIX executable fixture")
def test_observation_request_timeout_terminates_unresponsive_process(
    tmp_path: Path,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    unresponsive = tmp_path / "unresponsive-observer"
    unresponsive.write_text(
        "#!/usr/bin/env python3\nimport time\ntime.sleep(60)\n",
        encoding="utf-8",
    )
    unresponsive.chmod(0o755)
    service = NativeObservationService(
        binary_path=unresponsive,
        workspace_root=root,
        cache_path=tmp_path / "state.cache",
        request_timeout_s=0.05,
    )
    try:
        with pytest.raises(NativeObservationServiceError, match="timed out"):
            service.ping()
        assert service._process.poll() is not None
    finally:
        service.close()


def test_observation_process_forced_termination_is_visible_and_close_is_idempotent(
    tmp_path: Path,
    observation_service_binary: Path,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    service = NativeObservationService(
        binary_path=observation_service_binary,
        workspace_root=root,
        cache_path=tmp_path / "state.cache",
    )
    service.ping()
    service.terminate_immediately()
    deadline = time.monotonic() + 3.0
    while True:
        try:
            service.health()
        except NativeObservationServiceError as error:
            assert "ended" in str(error) or "terminated" in str(error)
            break
        if time.monotonic() >= deadline:
            pytest.fail("killed observation process remained requestable")
        time.sleep(0.01)
    service.close()
    service.close()


def test_active_periodic_audit_crash_restarts_from_exact_maintained_cache(
    tmp_path: Path,
    observation_service_binary: Path,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    for index in range(8_000):
        (root / f"source-{index:05d}.aware").write_text(
            f"source-{index}\n",
            encoding="utf-8",
        )
    cache = tmp_path / "state.cache"
    baseline_threads = {
        thread.name
        for thread in threading.enumerate()
        if thread.name.startswith("aware-fs-observation-")
    }
    service = NativeObservationService(
        binary_path=observation_service_binary,
        workspace_root=root,
        cache_path=cache,
        reconciliation_interval_s=0.2,
    )
    try:
        startup = service.initialize_observation("periodic-crash-startup")
        service.wait_for_watcher_ready(request_id="periodic-crash-watcher-ready")
        expected_digest = str(startup["snapshot_digest"])
        expected_generation = int(startup["to_generation"])
        deadline = time.monotonic() + 3.0
        attempt = 0
        while True:
            running = dict(service.poll(f"periodic-crash-running-{attempt}"))
            if running["observation_mode"] == "periodic_audit_running":
                break
            assert running["observation_mode"] == "maintained_no_hint"
            assert time.monotonic() < deadline
            attempt += 1
            time.sleep(0.002)
        process = service._process
        service.terminate_immediately()
        service.close()
        assert process.poll() is not None
    finally:
        service.close()

    with NativeObservationService(
        binary_path=observation_service_binary,
        workspace_root=root,
        cache_path=cache,
        reconciliation_interval_s=3600.0,
    ) as restarted:
        recovered = restarted.initialize_observation("periodic-crash-restart")
        assert recovered["cache_start_state"] == "loaded"
        assert recovered["cache_written"] is False
        assert recovered["to_generation"] == expected_generation
        assert recovered["snapshot_digest"] == expected_digest
        assert recovered["snapshot_digest"] == collect_python_workspace_snapshot(
            root
        ).inventory_digest

    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        current_threads = {
            thread.name
            for thread in threading.enumerate()
            if thread.name.startswith("aware-fs-observation-")
        }
        if current_threads == baseline_threads:
            break
        time.sleep(0.01)
    assert current_threads == baseline_threads


def _poll_until_event_reconciliation(
    service: NativeObservationService,
    request_id: str,
) -> dict[str, object]:
    deadline = time.monotonic() + 3.0
    attempt = 0
    while True:
        report = dict(service.poll(f"{request_id}-{attempt}"))
        if str(report["reconciliation_cause"]).startswith("event_hints"):
            return report
        assert report["observation_mode"] == "maintained_no_hint"
        if time.monotonic() >= deadline:
            pytest.fail("native watcher did not invalidate before deadline")
        attempt += 1
        time.sleep(0.01)
