from pathlib import Path

from aware_service_runtime.local_authority import (
    ServiceHostHealthStatus,
    ServiceHostLifecycleTransition,
    ServiceHostStartupPhase,
    authorize_service_host_attachment,
    authorize_service_host_control,
    append_service_host_lifecycle_update,
    classify_service_host_lifecycle,
    new_service_host_generation_id,
    observe_service_host_lifecycle_updates,
    partition_service_host_attachments_by_lease,
    renew_service_host_attachment,
    read_service_host_startup_failure,
    service_host_authority_id,
    service_host_attachment,
    service_host_attachment_from_payload,
    service_host_startup_failure_from_exception,
    write_service_host_startup_failure,
)


def _authority(tmp_path: Path) -> str:
    return service_host_authority_id(
        service_package="aware-demo-service",
        socket_path=tmp_path / "service.sock",
        state_root=tmp_path / "state",
    )


def test_service_host_authority_and_generation_are_distinct(tmp_path: Path) -> None:
    authority_id = _authority(tmp_path)

    assert authority_id == _authority(tmp_path)
    assert new_service_host_generation_id(authority_id=authority_id) != (
        new_service_host_generation_id(authority_id=authority_id)
    )


def test_service_host_lifecycle_requires_handshake_for_health(tmp_path: Path) -> None:
    lifecycle = classify_service_host_lifecycle(
        authority_id=_authority(tmp_path),
        generation_id="generation-1",
        service_package="aware-demo-service",
        pid=42,
        process_alive=True,
        process_matches=True,
        socket_exists=True,
        handshake_ready=False,
        artifacts_exist=True,
    )

    assert lifecycle.health_status is ServiceHostHealthStatus.running_degraded
    assert lifecycle.healthy is False
    assert lifecycle.running is True


def test_service_host_lifecycle_classifies_stale_authority(tmp_path: Path) -> None:
    lifecycle = classify_service_host_lifecycle(
        authority_id=_authority(tmp_path),
        generation_id="generation-1",
        service_package="aware-demo-service",
        pid=42,
        process_alive=False,
        process_matches=False,
        socket_exists=True,
        handshake_ready=False,
        artifacts_exist=True,
    )

    assert lifecycle.health_status is ServiceHostHealthStatus.stale


def test_running_service_host_control_requires_matching_generation(
    tmp_path: Path,
) -> None:
    lifecycle = classify_service_host_lifecycle(
        authority_id=_authority(tmp_path),
        generation_id="generation-1",
        service_package="aware-demo-service",
        pid=42,
        process_alive=True,
        process_matches=True,
        socket_exists=True,
        handshake_ready=True,
        artifacts_exist=True,
    )

    missing = authorize_service_host_control(
        operation="stop",
        lifecycle=lifecycle,
        expected_generation_id=None,
    )
    mismatch = authorize_service_host_control(
        operation="restart",
        lifecycle=lifecycle,
        expected_generation_id="generation-2",
    )
    matched = authorize_service_host_control(
        operation="restart",
        lifecycle=lifecycle,
        expected_generation_id="generation-1",
    )

    assert missing.allowed is False
    assert missing.reason == "expected_service_host_generation_required"
    assert mismatch.allowed is False
    assert mismatch.reason == "service_host_generation_mismatch"
    assert matched.allowed is True


def test_startup_failure_receipt_preserves_ordered_exception_chain(
    tmp_path: Path,
) -> None:
    try:
        try:
            raise ValueError("generated SQL missing")
        except ValueError as cause:
            raise RuntimeError("service activation failed") from cause
    except RuntimeError as error:
        evidence = service_host_startup_failure_from_exception(
            authority_id="authority-1",
            generation_id="generation-1",
            service_package="aware-workspace-service",
            phase=ServiceHostStartupPhase.activation,
            error=error,
            pid=1234,
        )

    path = tmp_path / "startup-failure.json"
    write_service_host_startup_failure(path=path, evidence=evidence)
    loaded = read_service_host_startup_failure(path)

    assert loaded == evidence
    assert loaded is not None
    assert loaded.reason == "service_host_activation_failed"
    assert [item.exception_type for item in loaded.causes] == [
        "RuntimeError",
        "ValueError",
    ]
    assert loaded.root_cause is not None
    assert loaded.root_cause.message == "generated SQL missing"


def test_startup_failure_reader_rejects_unknown_contract(tmp_path: Path) -> None:
    path = tmp_path / "startup-failure.json"
    path.write_text('{"contract_version":"unknown"}\n', encoding="utf-8")

    assert read_service_host_startup_failure(path) is None


def test_service_host_attachment_identity_is_idempotent(tmp_path: Path) -> None:
    attachment = service_host_attachment(
        authority_id=_authority(tmp_path),
        generation_id="generation-1",
        consumer_id="codex-thread-1",
        session_key="workspace-session:shared",
        attached_at_utc="2026-07-11T00:00:00Z",
    )
    repeated = service_host_attachment(
        authority_id=_authority(tmp_path),
        generation_id="generation-1",
        consumer_id="codex-thread-1",
        session_key="workspace-session:shared",
        attached_at_utc="2026-07-11T01:00:00Z",
    )

    assert attachment.attachment_id == repeated.attachment_id
    assert attachment.to_payload()["contract_version"] == (
        "aware.service.local-service-host.attachment.v1"
    )
    assert attachment.lease_expires_at_utc == "2026-07-11T01:00:00Z"


def test_service_host_attachment_lease_renews_and_partitions_expired(
    tmp_path: Path,
) -> None:
    expired = service_host_attachment(
        authority_id=_authority(tmp_path),
        generation_id="generation-1",
        consumer_id="codex-thread-old",
        session_key="workspace-session:shared",
        attached_at_utc="2026-07-11T00:00:00Z",
    )
    current = service_host_attachment(
        authority_id=_authority(tmp_path),
        generation_id="generation-1",
        consumer_id="codex-thread-current",
        session_key="workspace-session:shared",
        attached_at_utc="2026-07-11T01:30:00Z",
    )
    renewed = renew_service_host_attachment(
        expired,
        renewed_at_utc="2026-07-11T01:45:00Z",
    )

    active, stale = partition_service_host_attachments_by_lease(
        (expired, current),
        observed_at_utc="2026-07-11T01:15:00Z",
    )

    assert renewed.attachment_id == expired.attachment_id
    assert renewed.attached_at_utc == expired.attached_at_utc
    assert renewed.lease_renewed_at_utc == "2026-07-11T01:45:00Z"
    assert renewed.lease_expires_at_utc == "2026-07-11T02:45:00Z"
    assert active == (current,)
    assert stale == (expired,)


def test_legacy_service_host_attachment_derives_lease_without_identity_change(
    tmp_path: Path,
) -> None:
    attachment = service_host_attachment(
        authority_id=_authority(tmp_path),
        generation_id="generation-1",
        consumer_id="codex-thread-legacy",
        session_key="workspace-session:shared",
        attached_at_utc="2026-07-11T00:00:00Z",
    )
    legacy_payload = attachment.to_payload()
    legacy_payload.pop("lease_renewed_at_utc")
    legacy_payload.pop("lease_expires_at_utc")

    parsed = service_host_attachment_from_payload(legacy_payload)

    assert parsed is not None
    assert parsed.attachment_id == attachment.attachment_id
    assert parsed.lease_renewed_at_utc == "2026-07-11T00:00:00Z"
    assert parsed.lease_expires_at_utc == "2026-07-11T01:00:00Z"


def test_service_host_drain_seals_attachment_and_stop_waits_for_detach(
    tmp_path: Path,
) -> None:
    lifecycle = classify_service_host_lifecycle(
        authority_id=_authority(tmp_path),
        generation_id="generation-1",
        service_package="aware-demo-service",
        pid=42,
        process_alive=True,
        process_matches=True,
        socket_exists=True,
        handshake_ready=True,
        artifacts_exist=True,
    )

    attach = authorize_service_host_attachment(
        operation="attach",
        lifecycle=lifecycle,
        expected_generation_id="generation-1",
        active_attachment_count=1,
        draining=True,
    )
    stop = authorize_service_host_control(
        operation="stop",
        lifecycle=lifecycle,
        expected_generation_id="generation-1",
        active_attachment_count=1,
        draining=True,
    )
    stop_after_detach = authorize_service_host_control(
        operation="stop",
        lifecycle=lifecycle,
        expected_generation_id="generation-1",
        active_attachment_count=0,
        draining=True,
    )

    assert attach.allowed is False
    assert attach.reason == "service_host_generation_draining"
    assert stop.allowed is False
    assert stop.reason == "active_service_host_attachments_present"
    assert stop_after_detach.allowed is True


def test_service_host_lifecycle_updates_are_ordered_for_independent_consumers(
    tmp_path: Path,
) -> None:
    path = tmp_path / "service-host-updates.json"
    lifecycle = classify_service_host_lifecycle(
        authority_id=_authority(tmp_path),
        generation_id="generation-1",
        service_package="aware-demo-service",
        pid=42,
        process_alive=True,
        process_matches=True,
        socket_exists=True,
        handshake_ready=True,
        artifacts_exist=True,
    )

    first = append_service_host_lifecycle_update(
        path=path,
        transition=ServiceHostLifecycleTransition.generation_ready,
        lifecycle=lifecycle,
        reason="service_host_started",
    )
    second = append_service_host_lifecycle_update(
        path=path,
        transition=ServiceHostLifecycleTransition.drain_started,
        lifecycle=lifecycle,
        reason="service_host_generation_draining",
        controller_id="codex-thread-1",
    )
    consumer_one = observe_service_host_lifecycle_updates(path=path)
    consumer_two = observe_service_host_lifecycle_updates(path=path)

    assert first.sequence_number == 1
    assert second.sequence_number == 2
    assert first.update_id != second.update_id
    assert consumer_one == consumer_two
    assert [item.transition for item in consumer_one.updates] == [
        ServiceHostLifecycleTransition.generation_ready,
        ServiceHostLifecycleTransition.drain_started,
    ]
    assert consumer_one.next_cursor_sequence_number == 2


def test_service_host_lifecycle_update_retention_reports_expired_cursor(
    tmp_path: Path,
) -> None:
    path = tmp_path / "service-host-updates.json"
    lifecycle = classify_service_host_lifecycle(
        authority_id=_authority(tmp_path),
        generation_id="generation-1",
        service_package="aware-demo-service",
        pid=42,
        process_alive=True,
        process_matches=True,
        socket_exists=True,
        handshake_ready=True,
        artifacts_exist=True,
    )
    for _ in range(4):
        append_service_host_lifecycle_update(
            path=path,
            transition=ServiceHostLifecycleTransition.generation_ready,
            lifecycle=lifecycle,
            reason="service_host_started",
            retention=2,
        )

    bootstrap = observe_service_host_lifecycle_updates(
        path=path,
        after_sequence_number=0,
    )
    current = observe_service_host_lifecycle_updates(
        path=path,
        after_sequence_number=2,
    )

    assert bootstrap.cursor_expired is False
    assert [item.sequence_number for item in bootstrap.updates] == [3, 4]
    assert current.cursor_expired is False
    assert [item.sequence_number for item in current.updates] == [3, 4]

    too_old = observe_service_host_lifecycle_updates(
        path=path,
        after_sequence_number=1,
    )
    assert too_old.cursor_expired is True
    assert too_old.updates == ()


def test_service_host_lifecycle_observation_reports_missing_journal(
    tmp_path: Path,
) -> None:
    batch = observe_service_host_lifecycle_updates(
        path=tmp_path / "missing-updates.json",
    )

    assert batch.ready is False
    assert batch.journal_available is False
    assert batch.to_payload()["status"] == "missing"
