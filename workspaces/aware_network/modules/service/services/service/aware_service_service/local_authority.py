from __future__ import annotations

import asyncio
from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Iterator, Literal, cast
from uuid import UUID, uuid4

import fcntl

from aware_service_runtime.local_authority import (
    SERVICE_HOST_AUTHORITY_ID_ENV,
    SERVICE_HOST_GENERATION_ID_ENV,
    SERVICE_HOST_PACKAGE_ENV,
    SERVICE_HOST_STARTUP_FAILURE_PATH_ENV,
    ServiceHostAttachmentEvidence,
    ServiceHostLifecycleTransition,
    ServiceHostLifecycleUpdateBatch,
    ServiceHostLifecycleEvidence,
    ServiceHostStartupFailureEvidence,
    append_service_host_lifecycle_update,
    authorize_service_host_attachment,
    authorize_service_host_control,
    classify_service_host_lifecycle,
    new_service_host_generation_id,
    observe_service_host_lifecycle_updates,
    partition_service_host_attachments_by_lease,
    read_service_host_startup_failure,
    renew_service_host_attachment,
    service_host_authority_id,
    service_host_attachment,
    service_host_attachment_from_payload,
    service_host_startup_failure_for_process_exit,
    service_host_startup_failure_with_process_exit,
    write_service_host_startup_failure,
)

from aware_service_service.ontology.replica.state import (
    ServiceOntologyOcgMigrationApplyResult,
    ServiceOntologyReplicaStateStore,
)
from aware_service_service.workspace_revision_bootstrap import (
    ServiceHostWorkspaceRevisionBootstrapPlan,
    write_service_host_workspace_revision_bootstrap_config,
)

_AWARE_ROOT_ENV = "AWARE_ROOT"
_DATABASE_URL_ENV = "DATABASE_URL"
_META_EVENT_STORE_ROOT_ENV = "AWARE_META_SERVICE_EVENT_STORE_ROOT"
_META_EVENT_STORE_ROOT_RELATIVE_PATH = Path(".aware/meta/commit-events")
_PERSISTENCE_BACKEND_ENV = "AWARE_PERSISTENCE_BACKEND"


@dataclass(frozen=True, slots=True)
class ServiceHostLocalAuthorityResult:
    status: str
    reason: str | None
    state_path: Path
    socket_path: Path | None = None
    pid: int | None = None
    payload: dict[str, object] | None = None

    @property
    def ready(self) -> bool:
        return self.status in {"running", "started"}

    def to_payload(self) -> dict[str, object]:
        return {
            **(dict(self.payload or {})),
            "status": self.status,
            "reason": self.reason,
            "state_path": self.state_path.as_posix(),
            "socket_path": (
                self.socket_path.as_posix() if self.socket_path is not None else None
            ),
            "pid": self.pid,
        }


@dataclass(frozen=True, slots=True)
class ServiceHostAuthorityCandidate:
    state_path: Path
    status: str
    current: bool
    authority_id: str | None
    generation_id: str | None
    socket_path: Path | None
    lifecycle: dict[str, object]
    status_payload: dict[str, object]

    def to_payload(self) -> dict[str, object]:
        return {
            "state_path": self.state_path.as_posix(),
            "status": self.status,
            "current": self.current,
            "authority_id": self.authority_id,
            "generation_id": self.generation_id,
            "socket_path": (
                self.socket_path.as_posix() if self.socket_path is not None else None
            ),
            "lifecycle": dict(self.lifecycle),
            "status_payload": dict(self.status_payload),
        }


@dataclass(frozen=True, slots=True)
class ServiceHostAuthorityDiscoveryResult:
    status: Literal["current", "missing", "ambiguous"]
    reason: str
    service_package: str
    selected: ServiceHostAuthorityCandidate | None
    candidates: tuple[ServiceHostAuthorityCandidate, ...]
    scanned_candidate_count: int

    @property
    def ready(self) -> bool:
        return self.status == "current" and self.selected is not None

    def to_payload(self) -> dict[str, object]:
        return {
            "status": self.status,
            "reason": self.reason,
            "ready": self.ready,
            "service_package": self.service_package,
            "selected": self.selected.to_payload() if self.selected else None,
            "candidates": [item.to_payload() for item in self.candidates],
            "scanned_candidate_count": self.scanned_candidate_count,
        }


class ServiceHostProcessExitedBeforeReady(RuntimeError):
    def __init__(self, *, exit_code: int) -> None:
        self.exit_code = exit_code
        super().__init__(f"ServiceHost process exited before ready: {exit_code}")


class ServiceHostReadinessTimeout(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class _ServiceHostSocketProcess:
    pid: int
    environment: Mapping[str, str]


def ensure_service_host_from_workspace_revision_plan(
    *,
    plan: ServiceHostWorkspaceRevisionBootstrapPlan,
    replace: bool = False,
    timeout_s: float = 30.0,
    expected_generation_id: str | None = None,
    consumer_id: str | None = None,
    session_key: str | None = None,
) -> ServiceHostLocalAuthorityResult:
    if not plan.boot_ready:
        return ServiceHostLocalAuthorityResult(
            status="blocked",
            reason=plan.reason,
            state_path=_state_path_for_plan(plan=plan),
            socket_path=plan.socket_path,
            payload={
                "plan": plan.to_payload(),
                "missing_requirements": list(plan.missing_requirements),
            },
        )

    state_path = _state_path_for_plan(plan=plan)
    with _service_host_control_lock(state_path=state_path):
        existing_state = read_service_host_state(state_path)
        existing_pid = _state_pid(existing_state)
        if existing_pid is not None and service_host_pid_alive(existing_pid):
            status_payload = _service_host_status_payload(
                state_path=state_path,
                state=existing_state,
            )
            lifecycle = _lifecycle_from_status_payload(status_payload)
            if not replace:
                if consumer_id is not None and session_key is not None:
                    attachment_result = _attach_to_service_host_state(
                        state=existing_state,
                        lifecycle=lifecycle,
                        consumer_id=consumer_id,
                        session_key=session_key,
                    )
                    if attachment_result["allowed"] is not True:
                        return ServiceHostLocalAuthorityResult(
                            status="blocked",
                            reason=str(attachment_result["reason"]),
                            state_path=state_path,
                            socket_path=(
                                _state_socket_path(existing_state) or plan.socket_path
                            ),
                            pid=existing_pid,
                            payload={
                                **status_payload,
                                "attachment_decision": attachment_result,
                            },
                        )
                    write_service_host_state(path=state_path, payload=existing_state)
                    attachment_payload = attachment_result.get("attachment")
                    attachment = (
                        service_host_attachment_from_payload(attachment_payload)
                        if isinstance(attachment_payload, Mapping)
                        else None
                    )
                    if (
                        lifecycle is not None
                        and attachment is not None
                        and attachment_result.get("changed") is True
                    ):
                        _append_service_host_update(
                            state_path=state_path,
                            transition=ServiceHostLifecycleTransition.attachment_added,
                            lifecycle=lifecycle,
                            reason="service_host_attachment_active",
                            attachment=attachment,
                        )
                    status_payload = _service_host_status_payload(
                        state_path=state_path,
                        state=existing_state,
                    )
                healthy = lifecycle is not None and lifecycle.healthy
                return ServiceHostLocalAuthorityResult(
                    status="running" if healthy else "degraded",
                    reason=(
                        "service_host_already_running"
                        if healthy
                        else "service_host_running_handshake_unavailable"
                    ),
                    state_path=state_path,
                    socket_path=(
                        _state_socket_path(existing_state) or plan.socket_path
                    ),
                    pid=existing_pid,
                    payload=status_payload,
                )
            if lifecycle is not None:
                if lifecycle.process_alive and not lifecycle.process_matches:
                    return ServiceHostLocalAuthorityResult(
                        status="blocked",
                        reason="service_host_process_identity_mismatch",
                        state_path=state_path,
                        socket_path=(
                            _state_socket_path(existing_state) or plan.socket_path
                        ),
                        pid=existing_pid,
                        payload=status_payload,
                    )
                decision = authorize_service_host_control(
                    operation="restart",
                    lifecycle=lifecycle,
                    expected_generation_id=expected_generation_id,
                    active_attachment_count=len(
                        _service_host_attachments(existing_state)
                    ),
                    draining=bool(existing_state.get("draining")),
                )
                if not decision.allowed:
                    return ServiceHostLocalAuthorityResult(
                        status="blocked",
                        reason=decision.reason,
                        state_path=state_path,
                        socket_path=(
                            _state_socket_path(existing_state) or plan.socket_path
                        ),
                        pid=existing_pid,
                        payload={
                            **status_payload,
                            "control_decision": decision.to_payload(),
                        },
                    )
            terminate_service_host_pid(pid=existing_pid, timeout_s=timeout_s)
            if lifecycle is not None:
                _append_service_host_update(
                    state_path=state_path,
                    transition=ServiceHostLifecycleTransition.generation_stopped,
                    lifecycle=_stopped_service_host_lifecycle(lifecycle),
                    reason="service_host_restarted_generation_terminated",
                )

        interrupted_start = _recover_interrupted_service_host_start(
            plan=plan,
            state_path=state_path,
            consumer_id=consumer_id,
            session_key=session_key,
        )
        if interrupted_start is not None:
            return interrupted_start

        ocg_migration_apply = _apply_service_local_state_ocg_migrations(plan=plan)
        if ocg_migration_apply.status == "blocked":
            return ServiceHostLocalAuthorityResult(
                status="blocked",
                reason="service_local_state_ocg_migration_blocked",
                state_path=state_path,
                socket_path=plan.socket_path,
                payload={
                    "plan": plan.to_payload(),
                    "ocg_migration_apply": dict(ocg_migration_apply.evidence or {}),
                },
            )

        config_path = write_service_host_workspace_revision_bootstrap_config(plan=plan)
        service_package = plan.service_package_name or "unknown-service"
        state_root = _service_host_runtime_state_root(config_path=config_path)
        authority_id = service_host_authority_id(
            service_package=service_package,
            socket_path=plan.socket_path,
            state_root=state_root,
        )
        generation_id = new_service_host_generation_id(authority_id=authority_id)
        startup_failure_path = service_host_startup_failure_path(state_path=state_path)
        startup_failure_path.unlink(missing_ok=True)
        process = start_service_host_process(
            plan=plan,
            config_path=config_path,
            authority_id=authority_id,
            generation_id=generation_id,
            startup_failure_path=startup_failure_path,
        )
        starting_state = _run_state(
            plan=plan,
            config_path=config_path,
            process=process,
            authority_id=authority_id,
            generation_id=generation_id,
            startup_failure_path=startup_failure_path,
            ocg_migration_apply=ocg_migration_apply,
        )
        starting_state.update(
            {
                "status": "starting",
                "reason": "service_host_process_started_readiness_pending",
            }
        )
        write_service_host_state(path=state_path, payload=starting_state)
        try:
            wait_for_service_ready(
                process=process,
                socket_path=plan.socket_path,
                timeout_s=timeout_s,
            )
        except ServiceHostProcessExitedBeforeReady as exc:
            failure = read_service_host_startup_failure(startup_failure_path)
            if failure is None:
                failure = service_host_startup_failure_for_process_exit(
                    authority_id=authority_id,
                    generation_id=generation_id,
                    service_package=service_package,
                    pid=process.pid,
                    exit_code=exc.exit_code,
                )
            else:
                failure = service_host_startup_failure_with_process_exit(
                    failure,
                    pid=process.pid,
                    exit_code=exc.exit_code,
                )
            write_service_host_startup_failure(
                path=startup_failure_path,
                evidence=failure,
            )
            state = _run_state(
                plan=plan,
                config_path=config_path,
                process=process,
                authority_id=authority_id,
                generation_id=generation_id,
                startup_failure_path=startup_failure_path,
                ocg_migration_apply=ocg_migration_apply,
            )
            state.update(
                {
                    "status": "failed",
                    "reason": failure.reason,
                    "exit_code": exc.exit_code,
                    "startup_failure": failure.to_payload(),
                }
            )
            write_service_host_state(path=state_path, payload=state)
            failed_lifecycle = _service_host_lifecycle(
                state=state,
                handshake_ready=False,
            )
            _append_service_host_update(
                state_path=state_path,
                transition=ServiceHostLifecycleTransition.generation_failed,
                lifecycle=failed_lifecycle,
                reason=failure.reason,
                startup_failure=failure,
            )
            return ServiceHostLocalAuthorityResult(
                status="failed",
                reason=failure.reason,
                state_path=state_path,
                socket_path=plan.socket_path,
                pid=process.pid,
                payload={
                    **state,
                    "lifecycle": _service_host_lifecycle(
                        state=state,
                        handshake_ready=False,
                    ).to_payload(),
                },
            )
        except ServiceHostReadinessTimeout as exc:
            state = _run_state(
                plan=plan,
                config_path=config_path,
                process=process,
                authority_id=authority_id,
                generation_id=generation_id,
                startup_failure_path=startup_failure_path,
                ocg_migration_apply=ocg_migration_apply,
            )
            state.update(
                {
                    "status": "starting",
                    "reason": "service_host_readiness_timeout_process_preserved",
                    "readiness_error": str(exc),
                }
            )
            write_service_host_state(path=state_path, payload=state)
            degraded_lifecycle = _service_host_lifecycle(
                state=state,
                handshake_ready=False,
            )
            _append_service_host_update(
                state_path=state_path,
                transition=ServiceHostLifecycleTransition.generation_degraded,
                lifecycle=degraded_lifecycle,
                reason="service_host_readiness_timeout_process_preserved",
            )
            return ServiceHostLocalAuthorityResult(
                status="degraded",
                reason="service_host_readiness_timeout_process_preserved",
                state_path=state_path,
                socket_path=plan.socket_path,
                pid=process.pid,
                payload={
                    **state,
                    "lifecycle": _service_host_lifecycle(
                        state=state,
                        handshake_ready=False,
                    ).to_payload(),
                },
            )
        state = _run_state(
            plan=plan,
            config_path=config_path,
            process=process,
            authority_id=authority_id,
            generation_id=generation_id,
            startup_failure_path=startup_failure_path,
            ocg_migration_apply=ocg_migration_apply,
        )
        attachment = None
        if consumer_id is not None and session_key is not None:
            attachment = service_host_attachment(
                authority_id=authority_id,
                generation_id=generation_id,
                consumer_id=consumer_id,
                session_key=session_key,
            )
            state["attachments"] = [attachment.to_payload()]
        write_service_host_state(path=state_path, payload=state)
        ready_lifecycle = _service_host_lifecycle(
            state=state,
            handshake_ready=True,
        )
        _append_service_host_update(
            state_path=state_path,
            transition=ServiceHostLifecycleTransition.generation_ready,
            lifecycle=ready_lifecycle,
            reason="service_host_started",
            attachment=attachment,
        )
        return ServiceHostLocalAuthorityResult(
            status="started",
            reason="service_host_started",
            state_path=state_path,
            socket_path=plan.socket_path,
            pid=process.pid,
            payload={
                **state,
                "lifecycle": _service_host_lifecycle(
                    state=state,
                    handshake_ready=True,
                ).to_payload(),
            },
        )


def service_host_status_payload(
    *,
    workspace_root: Path,
    service_package: str,
    run_root: Path | None = None,
) -> dict[str, object]:
    state_path = service_host_state_path(
        workspace_root=workspace_root,
        service_package=service_package,
        run_root=run_root,
    )
    return service_host_status_payload_from_state_path(state_path=state_path)


def observe_service_host_updates(
    *,
    workspace_root: Path,
    service_package: str,
    run_root: Path | None = None,
    after_sequence_number: int = 0,
    limit: int = 100,
) -> ServiceHostLifecycleUpdateBatch:
    state_path = service_host_state_path(
        workspace_root=workspace_root,
        service_package=service_package,
        run_root=run_root,
    )
    return observe_service_host_lifecycle_updates(
        path=service_host_update_journal_path(state_path=state_path),
        after_sequence_number=after_sequence_number,
        limit=limit,
    )


def service_host_update_journal_path(*, state_path: Path) -> Path:
    return state_path.with_name("service-host-updates.json")


def service_host_status_payload_from_state_path(
    *, state_path: Path
) -> dict[str, object]:
    state = read_service_host_state(state_path)
    return _service_host_status_payload(state_path=state_path, state=state)


def discover_service_host_authority(
    *,
    workspace_root: Path,
    service_package: str,
    explicit_state_paths: tuple[Path, ...] = (),
    candidate_limit: int = 256,
) -> ServiceHostAuthorityDiscoveryResult:
    if candidate_limit < 1:
        raise ValueError("ServiceHost authority candidate_limit must be positive")
    workspace_root = workspace_root.expanduser().resolve()
    default_state_path = service_host_state_path(
        workspace_root=workspace_root,
        service_package=service_package,
        run_root=None,
    )
    runs_root = workspace_root / ".aware" / "service-host" / "runs"
    discovered_paths = (
        sorted(runs_root.glob("*/service-host-state.json"))
        if runs_root.is_dir()
        else []
    )
    scan_truncated = len(discovered_paths) > candidate_limit
    paths = {
        default_state_path,
        *(path.expanduser().resolve() for path in explicit_state_paths),
        *(path.expanduser().resolve() for path in discovered_paths[:candidate_limit]),
    }
    candidates: list[ServiceHostAuthorityCandidate] = []
    for state_path in sorted(paths):
        state = read_service_host_state(state_path)
        if not state:
            if state_path in {
                default_state_path,
                *(path.expanduser().resolve() for path in explicit_state_paths),
            }:
                candidates.append(
                    ServiceHostAuthorityCandidate(
                        state_path=state_path,
                        status="missing",
                        current=False,
                        authority_id=None,
                        generation_id=None,
                        socket_path=None,
                        lifecycle={},
                        status_payload={},
                    )
                )
            continue
        if _optional_text(state.get("service")) != service_package:
            continue
        status_payload = _service_host_status_payload(
            state_path=state_path,
            state=state,
        )
        lifecycle_payload = status_payload.get("lifecycle")
        lifecycle = (
            dict(lifecycle_payload) if isinstance(lifecycle_payload, Mapping) else {}
        )
        generation_id = _optional_text(lifecycle.get("generation_id"))
        authority_id = _optional_text(lifecycle.get("authority_id"))
        current = bool(
            lifecycle.get("running") is True
            and lifecycle.get("process_matches") is True
            and generation_id is not None
            and authority_id is not None
        )
        candidates.append(
            ServiceHostAuthorityCandidate(
                state_path=state_path,
                status="current" if current else "stale",
                current=current,
                authority_id=authority_id,
                generation_id=generation_id,
                socket_path=_state_socket_path(state),
                lifecycle=lifecycle,
                status_payload=status_payload,
            )
        )
    current_candidates = tuple(item for item in candidates if item.current)
    if scan_truncated:
        status: Literal["current", "missing", "ambiguous"] = "ambiguous"
        reason = "service_host_authority_candidate_limit_exceeded"
        selected = None
    elif len(current_candidates) > 1:
        status = "ambiguous"
        reason = "multiple_current_service_host_authorities"
        selected = None
    elif len(current_candidates) == 1:
        status = "current"
        reason = "current_service_host_authority_resolved"
        selected = current_candidates[0]
    else:
        status = "missing"
        reason = "current_service_host_authority_missing"
        selected = None
    return ServiceHostAuthorityDiscoveryResult(
        status=status,
        reason=reason,
        service_package=service_package,
        selected=selected,
        candidates=tuple(candidates),
        scanned_candidate_count=len(paths),
    )


def stop_service_host(
    *,
    workspace_root: Path,
    service_package: str,
    run_root: Path | None = None,
    timeout_s: float = 10.0,
    expected_generation_id: str | None = None,
    require_generation: bool = False,
) -> ServiceHostLocalAuthorityResult:
    state_path = service_host_state_path(
        workspace_root=workspace_root,
        service_package=service_package,
        run_root=run_root,
    )
    with _service_host_control_lock(state_path=state_path):
        state = read_service_host_state(state_path)
        pid = _state_pid(state)
        if pid is None or not service_host_pid_alive(pid):
            return ServiceHostLocalAuthorityResult(
                status="stopped",
                reason="service_host_not_running",
                state_path=state_path,
                socket_path=_state_socket_path(state),
                pid=pid,
                payload=_service_host_status_payload(
                    state_path=state_path,
                    state=state,
                ),
            )
        lifecycle = _service_host_lifecycle(
            state=state,
            handshake_ready=_probe_service_host_handshake(
                socket_path=_state_socket_path(state),
            ),
        )
        if lifecycle.process_alive and not lifecycle.process_matches:
            return ServiceHostLocalAuthorityResult(
                status="blocked",
                reason="service_host_process_identity_mismatch",
                state_path=state_path,
                socket_path=_state_socket_path(state),
                pid=pid,
                payload={
                    **state,
                    "lifecycle": lifecycle.to_payload(),
                },
            )
        attachments, expired_attachments = _prune_expired_service_host_attachments(
            state_path=state_path,
            state=state,
            lifecycle=lifecycle,
        )
        if require_generation or attachments:
            decision = authorize_service_host_control(
                operation="stop",
                lifecycle=lifecycle,
                expected_generation_id=(
                    expected_generation_id
                    if require_generation
                    else lifecycle.generation_id
                ),
                active_attachment_count=len(attachments),
                draining=bool(state.get("draining")),
            )
            if not decision.allowed:
                return ServiceHostLocalAuthorityResult(
                    status="blocked",
                    reason=decision.reason,
                    state_path=state_path,
                    socket_path=_state_socket_path(state),
                    pid=pid,
                    payload={
                        **state,
                        "lifecycle": lifecycle.to_payload(),
                        "control_decision": decision.to_payload(),
                        "expired_attachment_count": len(expired_attachments),
                    },
                )
        terminate_service_host_pid(pid=pid, timeout_s=timeout_s)
        payload = {
            **state,
            "status": "stopped",
            "reason": "service_host_terminated",
            "pid": pid,
        }
        write_service_host_state(path=state_path, payload=payload)
        _append_service_host_update(
            state_path=state_path,
            transition=ServiceHostLifecycleTransition.generation_stopped,
            lifecycle=_stopped_service_host_lifecycle(lifecycle),
            reason="service_host_terminated",
        )
        return ServiceHostLocalAuthorityResult(
            status="stopped",
            reason="service_host_terminated",
            state_path=state_path,
            socket_path=_state_socket_path(state),
            pid=pid,
            payload={
                **payload,
                "lifecycle": _service_host_lifecycle(
                    state=payload,
                    handshake_ready=False,
                ).to_payload(),
            },
        )


def attach_service_host(
    *,
    workspace_root: Path,
    service_package: str,
    consumer_id: str,
    session_key: str,
    expected_generation_id: str,
    run_root: Path | None = None,
) -> ServiceHostLocalAuthorityResult:
    return _mutate_service_host_attachment(
        operation="attach",
        workspace_root=workspace_root,
        service_package=service_package,
        consumer_id=consumer_id,
        session_key=session_key,
        expected_generation_id=expected_generation_id,
        run_root=run_root,
    )


def detach_service_host(
    *,
    workspace_root: Path,
    service_package: str,
    consumer_id: str,
    session_key: str,
    expected_generation_id: str,
    run_root: Path | None = None,
) -> ServiceHostLocalAuthorityResult:
    return _mutate_service_host_attachment(
        operation="detach",
        workspace_root=workspace_root,
        service_package=service_package,
        consumer_id=consumer_id,
        session_key=session_key,
        expected_generation_id=expected_generation_id,
        run_root=run_root,
    )


def drain_service_host(
    *,
    workspace_root: Path,
    service_package: str,
    controller_id: str,
    expected_generation_id: str,
    run_root: Path | None = None,
) -> ServiceHostLocalAuthorityResult:
    state_path = service_host_state_path(
        workspace_root=workspace_root,
        service_package=service_package,
        run_root=run_root,
    )
    with _service_host_control_lock(state_path=state_path):
        state = read_service_host_state(state_path)
        lifecycle = _service_host_lifecycle(
            state=state,
            handshake_ready=_probe_service_host_handshake(
                socket_path=_state_socket_path(state)
            ),
        )
        attachments, expired_attachments = _prune_expired_service_host_attachments(
            state_path=state_path,
            state=state,
            lifecycle=lifecycle,
        )
        decision = authorize_service_host_attachment(
            operation="drain",
            lifecycle=lifecycle,
            expected_generation_id=expected_generation_id,
            active_attachment_count=len(attachments),
            draining=bool(state.get("draining")),
        )
        if not decision.allowed:
            return ServiceHostLocalAuthorityResult(
                status="blocked",
                reason=decision.reason,
                state_path=state_path,
                socket_path=_state_socket_path(state),
                pid=_state_pid(state),
                payload={
                    **_service_host_status_payload(
                        state_path=state_path,
                        state=state,
                    ),
                    "attachment_decision": decision.to_payload(),
                    "expired_attachment_count": len(expired_attachments),
                },
            )
        if not bool(state.get("draining")):
            state.update(
                {
                    "draining": True,
                    "drain_requested_by": controller_id,
                    "drain_requested_at_utc": datetime.now(tz=UTC)
                    .isoformat()
                    .replace("+00:00", "Z"),
                }
            )
            write_service_host_state(path=state_path, payload=state)
            _append_service_host_update(
                state_path=state_path,
                transition=ServiceHostLifecycleTransition.drain_started,
                lifecycle=lifecycle,
                reason="service_host_generation_draining",
                controller_id=controller_id,
            )
        return ServiceHostLocalAuthorityResult(
            status="draining",
            reason="service_host_generation_draining",
            state_path=state_path,
            socket_path=_state_socket_path(state),
            pid=_state_pid(state),
            payload=_service_host_status_payload(
                state_path=state_path,
                state=state,
            ),
        )


def start_service_host_process(
    *,
    plan: ServiceHostWorkspaceRevisionBootstrapPlan,
    config_path: Path,
    authority_id: str,
    generation_id: str,
    startup_failure_path: Path,
) -> subprocess.Popen[bytes]:
    run_root = config_path.parent
    run_root.mkdir(parents=True, exist_ok=True)
    _service_host_meta_event_store_root(config_path=config_path).mkdir(
        parents=True,
        exist_ok=True,
    )
    stdout = (run_root / "service.stdout.log").open("ab")
    stderr = (run_root / "service.stderr.log").open("ab")
    env = service_host_process_env(
        plan=plan,
        config_path=config_path,
        authority_id=authority_id,
        generation_id=generation_id,
        startup_failure_path=startup_failure_path,
    )
    return subprocess.Popen(
        [sys.executable, "-m", "aware_service_service"],
        cwd=str(plan.workspace_root),
        env=env,
        stdout=stdout,
        stderr=stderr,
        start_new_session=True,
    )


def service_host_process_env(
    *,
    plan: ServiceHostWorkspaceRevisionBootstrapPlan,
    config_path: Path,
    authority_id: str | None = None,
    generation_id: str | None = None,
    startup_failure_path: Path | None = None,
) -> dict[str, str]:
    env = os.environ.copy()
    env[_AWARE_ROOT_ENV] = _service_host_runtime_state_root(
        config_path=config_path
    ).as_posix()
    env[_PERSISTENCE_BACKEND_ENV] = "fs"
    env.pop(_DATABASE_URL_ENV, None)
    env["AWARE_SERVICE_HOST_CONFIG_PATH"] = config_path.as_posix()
    env[_META_EVENT_STORE_ROOT_ENV] = _service_host_meta_event_store_root(
        config_path=config_path
    ).as_posix()
    if authority_id is not None:
        env[SERVICE_HOST_AUTHORITY_ID_ENV] = authority_id
    if generation_id is not None:
        env[SERVICE_HOST_GENERATION_ID_ENV] = generation_id
    if plan.service_package_name is not None:
        env[SERVICE_HOST_PACKAGE_ENV] = plan.service_package_name
    if startup_failure_path is not None:
        env[SERVICE_HOST_STARTUP_FAILURE_PATH_ENV] = (
            startup_failure_path.expanduser().resolve().as_posix()
        )
    pythonpath = [
        *(
            path.as_posix()
            for path in getattr(plan, "python_import_roots", ())
            if path.exists()
        ),
        *(env.get("PYTHONPATH", "").split(os.pathsep) if env.get("PYTHONPATH") else []),
    ]
    env["PYTHONPATH"] = os.pathsep.join(
        item for item in _dedupe_tokens(pythonpath) if item
    )
    return env


def _service_host_runtime_state_root(*, config_path: Path) -> Path:
    return config_path.parent.expanduser().resolve()


def _service_host_meta_event_store_root(*, config_path: Path) -> Path:
    return (
        (
            _service_host_runtime_state_root(config_path=config_path)
            / _META_EVENT_STORE_ROOT_RELATIVE_PATH
        )
        .expanduser()
        .resolve()
    )


def wait_for_service_ready(
    *,
    process: subprocess.Popen[bytes],
    socket_path: Path,
    timeout_s: float,
) -> None:
    from aware_comms import DuplexIpcEndpoint
    from aware_service_runtime.contracts import (
        SERVICE_HOST_PROTOCOL_VERSION,
        ServiceHostBootstrapStatus,
        ServiceHostHandshakeRequest,
    )
    from aware_service_runtime.duplex_client import ServiceHostDuplexClient

    deadline = time.time() + max(timeout_s, 0.1)
    last_error = "service host did not create IPC socket"
    while time.time() < deadline:
        return_code = process.poll()
        if return_code is not None:
            raise ServiceHostProcessExitedBeforeReady(
                exit_code=return_code,
            )
        if socket_path.exists():
            try:
                client = ServiceHostDuplexClient(
                    endpoint=DuplexIpcEndpoint.unix_socket(
                        socket_path=socket_path.as_posix()
                    )
                )
                response = asyncio.run(
                    client.send_handshake(
                        request=ServiceHostHandshakeRequest(
                            supported_protocol_versions=(SERVICE_HOST_PROTOCOL_VERSION,)
                        ),
                        timeout_s=2.0,
                    )
                )
                if response.readiness.status is ServiceHostBootstrapStatus.ready:
                    return
                last_error = response.readiness.reason or str(response.readiness.status)
            except Exception as exc:
                last_error = str(exc)
        time.sleep(0.2)
    raise ServiceHostReadinessTimeout(f"ServiceHost readiness timed out: {last_error}")


def service_host_state_path(
    *,
    workspace_root: Path,
    service_package: str,
    run_root: Path | None,
) -> Path:
    root = run_root or (
        workspace_root
        / ".aware"
        / "service-host"
        / "runs"
        / _safe_path_key(service_package)
    )
    return root.expanduser().resolve() / "service-host-state.json"


def service_host_startup_failure_path(*, state_path: Path) -> Path:
    return state_path.with_name("service-host-startup-failure.json")


def read_service_host_state(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {}
    return {str(key): value for key, value in payload.items()}


def write_service_host_state(*, path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.{uuid4()}.tmp")
    temporary_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    temporary_path.replace(path)


def service_host_pid_alive(pid: int) -> bool:
    if _process_state(pid) == "Z":
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def terminate_service_host_pid(*, pid: int, timeout_s: float) -> None:
    if not service_host_pid_alive(pid):
        return
    os.kill(pid, signal.SIGTERM)
    deadline = time.time() + max(timeout_s, 0.1)
    while time.time() < deadline:
        if not service_host_pid_alive(pid):
            return
        time.sleep(0.1)
    raise RuntimeError(f"ServiceHost process did not stop after SIGTERM: pid={pid}")


def _run_state(
    *,
    plan: ServiceHostWorkspaceRevisionBootstrapPlan,
    config_path: Path,
    process: subprocess.Popen[bytes],
    authority_id: str,
    generation_id: str,
    startup_failure_path: Path,
    ocg_migration_apply: ServiceOntologyOcgMigrationApplyResult | None = None,
) -> dict[str, object]:
    return _run_state_for_pid(
        plan=plan,
        config_path=config_path,
        pid=process.pid,
        authority_id=authority_id,
        generation_id=generation_id,
        startup_failure_path=startup_failure_path,
        ocg_migration_apply=ocg_migration_apply,
    )


def _run_state_for_pid(
    *,
    plan: ServiceHostWorkspaceRevisionBootstrapPlan,
    config_path: Path,
    pid: int,
    authority_id: str,
    generation_id: str,
    startup_failure_path: Path,
    ocg_migration_apply: ServiceOntologyOcgMigrationApplyResult | None = None,
) -> dict[str, object]:
    state_path = _state_path_for_plan(plan=plan)
    payload = {
        "pid": pid,
        "authority_id": authority_id,
        "generation_id": generation_id,
        "process_start_token": _process_start_token(pid),
        "service": plan.service_package_name,
        "workspace_root": plan.workspace_root.as_posix(),
        "workspace_revision_id": plan.workspace_revision_id,
        "workspace_materialization_id": plan.workspace_materialization_id,
        "socket_path": plan.socket_path.as_posix(),
        "config_path": config_path.as_posix(),
        "state_path": state_path.as_posix(),
        "startup_failure_path": startup_failure_path.as_posix(),
        "runtime_state_root": _service_host_runtime_state_root(
            config_path=config_path
        ).as_posix(),
        "meta_event_store_root": _service_host_meta_event_store_root(
            config_path=config_path
        ).as_posix(),
        "started_at_utc": datetime.now(tz=UTC).isoformat().replace("+00:00", "Z"),
        "attachments": [],
        "draining": False,
        "service_package_refs": [
            item.to_payload() for item in plan.service_package_refs
        ],
        "experience_package_refs": [
            item.to_payload() for item in plan.experience_package_refs
        ],
    }
    if ocg_migration_apply is not None:
        payload["ocg_migration_apply"] = dict(ocg_migration_apply.evidence or {})
    return payload


def _recover_interrupted_service_host_start(
    *,
    plan: ServiceHostWorkspaceRevisionBootstrapPlan,
    state_path: Path,
    consumer_id: str | None,
    session_key: str | None,
) -> ServiceHostLocalAuthorityResult | None:
    socket_path = plan.socket_path.expanduser().resolve()
    if not socket_path.exists():
        return None

    candidates = _service_host_socket_processes(socket_path=socket_path)
    if not candidates:
        return None
    if not _probe_service_host_handshake(socket_path=socket_path):
        return ServiceHostLocalAuthorityResult(
            status="blocked",
            reason="service_host_interrupted_start_handshake_unavailable",
            state_path=state_path,
            socket_path=socket_path,
            payload={"candidate_process_count": len(candidates)},
        )
    authority_id = service_host_authority_id(
        service_package=plan.service_package_name or "unknown-service",
        socket_path=socket_path,
        state_root=_service_host_runtime_state_root(config_path=plan.config_path),
    )
    matching = tuple(
        candidate
        for candidate in candidates
        if _service_host_process_matches_plan(
            candidate=candidate,
            plan=plan,
            authority_id=authority_id,
        )
    )
    if len(matching) != 1:
        return ServiceHostLocalAuthorityResult(
            status="blocked",
            reason=(
                "service_host_interrupted_start_owner_ambiguous"
                if len(matching) > 1
                else "service_host_interrupted_start_owner_mismatch"
            ),
            state_path=state_path,
            socket_path=socket_path,
            payload={
                "candidate_process_count": len(candidates),
                "matching_process_count": len(matching),
            },
        )

    candidate = matching[0]
    generation_id = candidate.environment[SERVICE_HOST_GENERATION_ID_ENV]
    startup_failure_path = service_host_startup_failure_path(state_path=state_path)
    state = _run_state_for_pid(
        plan=plan,
        config_path=plan.config_path,
        pid=candidate.pid,
        authority_id=authority_id,
        generation_id=generation_id,
        startup_failure_path=startup_failure_path,
    )
    state.update(
        {
            "status": "running",
            "reason": "service_host_interrupted_start_recovered",
        }
    )
    attachment = None
    if consumer_id is not None and session_key is not None:
        attachment = service_host_attachment(
            authority_id=authority_id,
            generation_id=generation_id,
            consumer_id=consumer_id,
            session_key=session_key,
        )
        state["attachments"] = [attachment.to_payload()]
    write_service_host_state(path=state_path, payload=state)
    lifecycle = _service_host_lifecycle(state=state, handshake_ready=True)
    _append_service_host_update(
        state_path=state_path,
        transition=ServiceHostLifecycleTransition.generation_ready,
        lifecycle=lifecycle,
        reason="service_host_interrupted_start_recovered",
        attachment=attachment,
    )
    return ServiceHostLocalAuthorityResult(
        status="running",
        reason="service_host_interrupted_start_recovered",
        state_path=state_path,
        socket_path=socket_path,
        pid=candidate.pid,
        payload={
            **_service_host_status_payload(state_path=state_path, state=state),
            "recovery": {
                "source": "service_host_socket_process_environment",
                "candidate_process_count": len(candidates),
                "matching_process_count": 1,
            },
        },
    )


def _service_host_process_matches_plan(
    *,
    candidate: _ServiceHostSocketProcess,
    plan: ServiceHostWorkspaceRevisionBootstrapPlan,
    authority_id: str,
) -> bool:
    environment = candidate.environment
    expected = {
        SERVICE_HOST_AUTHORITY_ID_ENV: authority_id,
        SERVICE_HOST_PACKAGE_ENV: plan.service_package_name or "unknown-service",
        "AWARE_SERVICE_HOST_CONFIG_PATH": plan.config_path.expanduser()
        .resolve()
        .as_posix(),
        _AWARE_ROOT_ENV: _service_host_runtime_state_root(
            config_path=plan.config_path
        ).as_posix(),
    }
    generation_id = str(environment.get(SERVICE_HOST_GENERATION_ID_ENV) or "").strip()
    process_start_token = _process_start_token(candidate.pid)
    return bool(
        generation_id
        and process_start_token
        and service_host_pid_alive(candidate.pid)
        and all(environment.get(key) == value for key, value in expected.items())
    )


def _service_host_socket_processes(
    *, socket_path: Path, proc_root: Path = Path("/proc")
) -> tuple[_ServiceHostSocketProcess, ...]:
    inode = _unix_socket_inode(socket_path=socket_path, proc_root=proc_root)
    if inode is None:
        return ()
    socket_target = f"socket:[{inode}]"
    result: list[_ServiceHostSocketProcess] = []
    for proc_dir in proc_root.iterdir():
        if not proc_dir.name.isdigit():
            continue
        fd_dir = proc_dir / "fd"
        try:
            owns_socket = any(
                os.readlink(fd_path) == socket_target for fd_path in fd_dir.iterdir()
            )
        except OSError:
            continue
        if not owns_socket:
            continue
        environment = _process_environment(proc_dir=proc_dir)
        if environment is None:
            continue
        result.append(
            _ServiceHostSocketProcess(
                pid=int(proc_dir.name),
                environment=environment,
            )
        )
    return tuple(sorted(result, key=lambda item: item.pid))


def _unix_socket_inode(*, socket_path: Path, proc_root: Path) -> str | None:
    try:
        lines = (proc_root / "net" / "unix").read_text(encoding="utf-8").splitlines()
    except (FileNotFoundError, OSError, UnicodeError):
        return None
    expected_path = socket_path.expanduser().resolve().as_posix()
    for line in lines[1:]:
        fields = line.split(maxsplit=7)
        if len(fields) == 8 and fields[7] == expected_path:
            return fields[6]
    return None


def _process_environment(*, proc_dir: Path) -> dict[str, str] | None:
    try:
        payload = (proc_dir / "environ").read_bytes()
    except (FileNotFoundError, OSError):
        return None
    environment: dict[str, str] = {}
    for item in payload.split(b"\0"):
        if b"=" not in item:
            continue
        key, value = item.split(b"=", 1)
        try:
            environment[key.decode("utf-8")] = value.decode("utf-8")
        except UnicodeDecodeError:
            continue
    return environment


def _apply_service_local_state_ocg_migrations(
    *,
    plan: ServiceHostWorkspaceRevisionBootstrapPlan,
) -> ServiceOntologyOcgMigrationApplyResult:
    artifact_refs = plan.code_package_artifact_refs
    if not artifact_refs:
        return ServiceOntologyOcgMigrationApplyResult(
            status="skipped",
            evidence={
                "status": "skipped",
                "reason": "no_code_package_artifact_refs",
                "artifact_count": 0,
            },
        )
    if plan.service_local_state_db_path is None:
        return ServiceOntologyOcgMigrationApplyResult(
            status="skipped",
            evidence={
                "status": "skipped",
                "reason": "service_local_state_db_path_unavailable",
                "artifact_count": len(artifact_refs),
            },
        )
    if plan.service_package_name is None:
        return ServiceOntologyOcgMigrationApplyResult(
            status="blocked",
            evidence={
                "status": "blocked",
                "reason": "service_package_name_unavailable",
                "artifact_count": len(artifact_refs),
            },
        )
    if plan.environment_id is None:
        return ServiceOntologyOcgMigrationApplyResult(
            status="blocked",
            evidence={
                "status": "blocked",
                "reason": "service_local_state_environment_id_unavailable",
                "artifact_count": len(artifact_refs),
            },
        )
    try:
        environment_id = UUID(plan.environment_id)
    except ValueError:
        return ServiceOntologyOcgMigrationApplyResult(
            status="blocked",
            evidence={
                "status": "blocked",
                "reason": "service_local_state_environment_id_invalid",
                "artifact_count": len(artifact_refs),
            },
        )

    store = asyncio.run(
        ServiceOntologyReplicaStateStore.open(
            db_path=plan.service_local_state_db_path,
            environment_id=environment_id,
        )
    )
    try:
        return store.apply_ocg_migration_artifacts(
            service_package_name=plan.service_package_name,
            workspace_root=plan.workspace_root,
            artifacts=(item.to_payload() for item in artifact_refs),
        )
    finally:
        store.close()


def _mutate_service_host_attachment(
    *,
    operation: str,
    workspace_root: Path,
    service_package: str,
    consumer_id: str,
    session_key: str,
    expected_generation_id: str,
    run_root: Path | None,
) -> ServiceHostLocalAuthorityResult:
    state_path = service_host_state_path(
        workspace_root=workspace_root,
        service_package=service_package,
        run_root=run_root,
    )
    with _service_host_control_lock(state_path=state_path):
        state = read_service_host_state(state_path)
        lifecycle = _service_host_lifecycle(
            state=state,
            handshake_ready=_probe_service_host_handshake(
                socket_path=_state_socket_path(state)
            ),
        )
        attachments, expired_attachments = _prune_expired_service_host_attachments(
            state_path=state_path,
            state=state,
            lifecycle=lifecycle,
        )
        decision = authorize_service_host_attachment(
            operation=cast(Literal["attach", "detach"], operation),
            lifecycle=lifecycle,
            expected_generation_id=expected_generation_id,
            active_attachment_count=len(attachments),
            draining=bool(state.get("draining")),
        )
        if not decision.allowed:
            return ServiceHostLocalAuthorityResult(
                status="blocked",
                reason=decision.reason,
                state_path=state_path,
                socket_path=_state_socket_path(state),
                pid=_state_pid(state),
                payload={
                    **_service_host_status_payload(
                        state_path=state_path,
                        state=state,
                    ),
                    "attachment_decision": decision.to_payload(),
                    "expired_attachment_count": len(expired_attachments),
                },
            )
        attachment = service_host_attachment(
            authority_id=lifecycle.authority_id,
            generation_id=expected_generation_id,
            consumer_id=consumer_id,
            session_key=session_key,
        )
        by_id = {item.attachment_id: item for item in attachments}
        if operation == "attach":
            existing_attachment = by_id.get(attachment.attachment_id)
            changed = existing_attachment is None
            if existing_attachment is not None:
                attachment = renew_service_host_attachment(existing_attachment)
            by_id[attachment.attachment_id] = attachment
            reason = "service_host_attachment_active"
            status = "attached"
        else:
            changed = attachment.attachment_id in by_id
            by_id.pop(attachment.attachment_id, None)
            reason = "service_host_attachment_detached"
            status = "detached"
        state["attachments"] = [
            item.to_payload()
            for item in sorted(by_id.values(), key=lambda row: row.attachment_id)
        ]
        write_service_host_state(path=state_path, payload=state)
        if changed:
            _append_service_host_update(
                state_path=state_path,
                transition=(
                    ServiceHostLifecycleTransition.attachment_added
                    if operation == "attach"
                    else ServiceHostLifecycleTransition.attachment_removed
                ),
                lifecycle=lifecycle,
                reason=reason,
                attachment=attachment,
            )
        return ServiceHostLocalAuthorityResult(
            status=status,
            reason=reason,
            state_path=state_path,
            socket_path=_state_socket_path(state),
            pid=_state_pid(state),
            payload={
                **_service_host_status_payload(
                    state_path=state_path,
                    state=state,
                ),
                "attachment": attachment.to_payload(),
                "attachment_changed": changed,
                "attachment_lease_renewed": operation == "attach" and not changed,
                "expired_attachment_count": len(expired_attachments),
                "attachment_decision": decision.to_payload(),
            },
        )


def _attach_to_service_host_state(
    *,
    state: dict[str, object],
    lifecycle: ServiceHostLifecycleEvidence | None,
    consumer_id: str,
    session_key: str,
) -> dict[str, object]:
    if lifecycle is None:
        return {
            "allowed": False,
            "reason": "service_host_lifecycle_unavailable",
        }
    generation_id = _optional_text(lifecycle.generation_id)
    attachments = _service_host_attachments(state)
    decision = authorize_service_host_attachment(
        operation="attach",
        lifecycle=lifecycle,
        expected_generation_id=generation_id,
        active_attachment_count=len(attachments),
        draining=bool(state.get("draining")),
    )
    result = decision.to_payload()
    if not decision.allowed or generation_id is None:
        return result
    attachment = service_host_attachment(
        authority_id=lifecycle.authority_id,
        generation_id=generation_id,
        consumer_id=consumer_id,
        session_key=session_key,
    )
    by_id = {item.attachment_id: item for item in attachments}
    existing_attachment = by_id.get(attachment.attachment_id)
    changed = existing_attachment is None
    if existing_attachment is not None:
        attachment = renew_service_host_attachment(existing_attachment)
    by_id[attachment.attachment_id] = attachment
    state["attachments"] = [
        item.to_payload()
        for item in sorted(by_id.values(), key=lambda row: row.attachment_id)
    ]
    return {
        **result,
        "attachment": attachment.to_payload(),
        "changed": changed,
        "lease_renewed": not changed,
    }


def _prune_expired_service_host_attachments(
    *,
    state_path: Path,
    state: dict[str, object],
    lifecycle: ServiceHostLifecycleEvidence,
) -> tuple[
    tuple[ServiceHostAttachmentEvidence, ...],
    tuple[ServiceHostAttachmentEvidence, ...],
]:
    active, expired = partition_service_host_attachments_by_lease(
        _service_host_attachments(state)
    )
    if not expired:
        return active, expired
    state["attachments"] = [
        item.to_payload() for item in sorted(active, key=lambda row: row.attachment_id)
    ]
    write_service_host_state(path=state_path, payload=state)
    for attachment in sorted(expired, key=lambda row: row.attachment_id):
        _append_service_host_update(
            state_path=state_path,
            transition=ServiceHostLifecycleTransition.attachment_removed,
            lifecycle=lifecycle,
            reason="service_host_attachment_lease_expired",
            attachment=attachment,
        )
    return active, expired


def _service_host_attachments(state: Mapping[str, object]):
    raw = state.get("attachments")
    if not isinstance(raw, list):
        return ()
    result = []
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        attachment = service_host_attachment_from_payload(item)
        if attachment is not None:
            result.append(attachment)
    return tuple(result)


def _state_path_for_plan(*, plan: ServiceHostWorkspaceRevisionBootstrapPlan) -> Path:
    return plan.config_path.parent / "service-host-state.json"


def _state_pid(payload: dict[str, object]) -> int | None:
    raw = payload.get("pid")
    if isinstance(raw, bool) or raw is None:
        return None
    try:
        pid = int(str(raw))
    except (TypeError, ValueError):
        return None
    return pid if pid > 0 else None


def _state_socket_path(payload: dict[str, object]) -> Path | None:
    raw = payload.get("socket_path")
    if raw is None or not str(raw).strip():
        return None
    return Path(str(raw)).expanduser().resolve()


def _service_host_status_payload(
    *,
    state_path: Path,
    state: dict[str, object],
) -> dict[str, object]:
    socket_path = _state_socket_path(state)
    lifecycle = _service_host_lifecycle(
        state=state,
        handshake_ready=_probe_service_host_handshake(socket_path=socket_path),
    )
    attachments = _service_host_attachments(state)
    return {
        **state,
        "status": "running" if lifecycle.running else "stopped",
        "health_status": lifecycle.health_status.value,
        "healthy": lifecycle.healthy,
        "state_path": state_path.as_posix(),
        "pid": lifecycle.pid,
        "lifecycle": lifecycle.to_payload(),
        "attachments": [item.to_payload() for item in attachments],
        "attachment_count": len(attachments),
        "draining": bool(state.get("draining")),
    }


def _service_host_lifecycle(
    *,
    state: dict[str, object],
    handshake_ready: bool,
):
    pid = _state_pid(state)
    process_alive = pid is not None and service_host_pid_alive(pid)
    expected_start_token = _optional_text(state.get("process_start_token"))
    process_matches = bool(
        process_alive
        and (
            expected_start_token is None
            or _process_start_token(cast(int, pid)) == expected_start_token
        )
    )
    socket_path = _state_socket_path(state)
    service_package = _optional_text(state.get("service")) or "unknown-service"
    state_path_text = _optional_text(state.get("state_path"))
    state_root = (
        Path(state_path_text).expanduser().resolve().parent
        if state_path_text is not None
        else (socket_path.parent if socket_path is not None else Path.cwd())
    )
    authority_id = _optional_text(state.get("authority_id")) or (
        service_host_authority_id(
            service_package=service_package,
            socket_path=socket_path or state_root / "service.sock",
            state_root=state_root,
        )
    )
    return classify_service_host_lifecycle(
        authority_id=authority_id,
        generation_id=_optional_text(state.get("generation_id")),
        service_package=service_package,
        pid=pid,
        process_alive=process_alive,
        process_matches=process_matches,
        socket_exists=bool(socket_path and socket_path.exists()),
        handshake_ready=handshake_ready,
        artifacts_exist=bool(state),
    )


def _stopped_service_host_lifecycle(
    lifecycle: ServiceHostLifecycleEvidence,
) -> ServiceHostLifecycleEvidence:
    return classify_service_host_lifecycle(
        authority_id=lifecycle.authority_id,
        generation_id=lifecycle.generation_id,
        service_package=lifecycle.service_package,
        pid=lifecycle.pid,
        process_alive=False,
        process_matches=False,
        socket_exists=False,
        handshake_ready=False,
        artifacts_exist=False,
    )


def _append_service_host_update(
    *,
    state_path: Path,
    transition: ServiceHostLifecycleTransition,
    lifecycle: ServiceHostLifecycleEvidence,
    reason: str,
    attachment: ServiceHostAttachmentEvidence | None = None,
    startup_failure: ServiceHostStartupFailureEvidence | None = None,
    controller_id: str | None = None,
) -> None:
    append_service_host_lifecycle_update(
        path=service_host_update_journal_path(state_path=state_path),
        transition=transition,
        lifecycle=lifecycle,
        reason=reason,
        attachment=attachment,
        startup_failure=startup_failure,
        controller_id=controller_id,
    )


def _lifecycle_from_status_payload(payload: dict[str, object]):
    lifecycle_payload = payload.get("lifecycle")
    if not isinstance(lifecycle_payload, dict):
        return None
    return _service_host_lifecycle(
        state=payload,
        handshake_ready=bool(lifecycle_payload.get("handshake_ready")),
    )


def _probe_service_host_handshake(*, socket_path: Path | None) -> bool:
    if socket_path is None or not socket_path.exists():
        return False
    from aware_comms import DuplexIpcEndpoint
    from aware_service_runtime.contracts import (
        SERVICE_HOST_PROTOCOL_VERSION,
        ServiceHostHandshakeRequest,
    )
    from aware_service_runtime.duplex_client import ServiceHostDuplexClient

    try:
        response = asyncio.run(
            ServiceHostDuplexClient(
                endpoint=DuplexIpcEndpoint.unix_socket(
                    socket_path=socket_path.as_posix()
                )
            ).send_handshake(
                request=ServiceHostHandshakeRequest(
                    supported_protocol_versions=(SERVICE_HOST_PROTOCOL_VERSION,)
                ),
                timeout_s=2.0,
            )
        )
    except Exception:
        return False
    return bool(response.readiness.is_ready)


def _process_start_token(pid: int) -> str | None:
    try:
        stat_payload = (Path("/proc") / str(pid) / "stat").read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    command_end = stat_payload.rfind(")")
    if command_end < 0:
        return None
    state_and_fields = stat_payload[command_end + 1 :].split()
    return state_and_fields[19] if len(state_and_fields) > 19 else None


def _process_state(pid: int) -> str | None:
    try:
        fields = (Path("/proc") / str(pid) / "stat").read_text(encoding="utf-8").split()
    except (OSError, UnicodeError):
        return None
    return fields[2] if len(fields) > 2 else None


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


@contextmanager
def _service_host_control_lock(*, state_path: Path) -> Iterator[None]:
    lock_path = state_path.with_name("service-host-control.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _safe_path_key(value: str) -> str:
    cleaned = "".join(
        char if char.isalnum() or char in {"-", "_", "."} else "-"
        for char in value.strip()
    ).strip("-._")
    return cleaned or "service"


def _dedupe_tokens(values: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        token = value.strip()
        if not token or token in seen:
            continue
        seen.add(token)
        result.append(token)
    return tuple(result)


__all__ = [
    "ServiceHostAuthorityCandidate",
    "ServiceHostAuthorityDiscoveryResult",
    "ServiceHostLocalAuthorityResult",
    "attach_service_host",
    "detach_service_host",
    "drain_service_host",
    "discover_service_host_authority",
    "ensure_service_host_from_workspace_revision_plan",
    "observe_service_host_updates",
    "read_service_host_state",
    "service_host_pid_alive",
    "service_host_process_env",
    "service_host_state_path",
    "service_host_startup_failure_path",
    "service_host_status_payload",
    "service_host_status_payload_from_state_path",
    "service_host_update_journal_path",
    "start_service_host_process",
    "stop_service_host",
    "terminate_service_host_pid",
    "wait_for_service_ready",
    "write_service_host_state",
]
