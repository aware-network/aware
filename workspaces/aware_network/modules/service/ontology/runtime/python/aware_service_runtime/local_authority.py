from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
import fcntl
import json
import os
from pathlib import Path
from typing import Literal, Mapping
from uuid import NAMESPACE_URL, uuid4, uuid5


SERVICE_HOST_LIFECYCLE_CONTRACT_VERSION = (
    "aware.service.local-service-host.lifecycle.v1"
)
SERVICE_HOST_STARTUP_FAILURE_CONTRACT_VERSION = (
    "aware.service.local-service-host.startup-failure.v1"
)
SERVICE_HOST_ATTACHMENT_CONTRACT_VERSION = (
    "aware.service.local-service-host.attachment.v1"
)
SERVICE_HOST_LIFECYCLE_UPDATE_CONTRACT_VERSION = (
    "aware.service.local-service-host.lifecycle-update.v1"
)
SERVICE_HOST_LIFECYCLE_UPDATE_JOURNAL_CONTRACT_VERSION = (
    "aware.service.local-service-host.lifecycle-update-journal.v1"
)
DEFAULT_SERVICE_HOST_LIFECYCLE_UPDATE_RETENTION = 512
DEFAULT_SERVICE_HOST_ATTACHMENT_LEASE_SECONDS = 60 * 60
SERVICE_HOST_AUTHORITY_ID_ENV = "AWARE_SERVICE_HOST_AUTHORITY_ID"
SERVICE_HOST_GENERATION_ID_ENV = "AWARE_SERVICE_HOST_GENERATION_ID"
SERVICE_HOST_PACKAGE_ENV = "AWARE_SERVICE_HOST_PACKAGE"
SERVICE_HOST_STARTUP_FAILURE_PATH_ENV = "AWARE_SERVICE_HOST_STARTUP_FAILURE_PATH"


class ServiceHostHealthStatus(StrEnum):
    running_healthy = "running_healthy"
    running_degraded = "running_degraded"
    stale = "stale"
    stopped = "stopped"


class ServiceHostStartupPhase(StrEnum):
    bootstrap_config = "bootstrap_config"
    app_construction = "app_construction"
    activation = "activation"
    readiness = "readiness"
    process_exit = "process_exit"


class ServiceHostLifecycleTransition(StrEnum):
    generation_ready = "generation_ready"
    generation_degraded = "generation_degraded"
    generation_failed = "generation_failed"
    generation_stopped = "generation_stopped"
    attachment_added = "attachment_added"
    attachment_removed = "attachment_removed"
    drain_started = "drain_started"


@dataclass(frozen=True, slots=True)
class ServiceHostStartupFailureCause:
    exception_type: str
    exception_module: str
    message: str

    def to_payload(self) -> dict[str, object]:
        return {
            "exception_type": self.exception_type,
            "exception_module": self.exception_module,
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class ServiceHostStartupFailureEvidence:
    authority_id: str
    generation_id: str
    service_package: str
    phase: ServiceHostStartupPhase
    reason: str
    observed_at_utc: str
    pid: int | None
    exit_code: int | None
    causes: tuple[ServiceHostStartupFailureCause, ...]

    @property
    def root_cause(self) -> ServiceHostStartupFailureCause | None:
        return self.causes[-1] if self.causes else None

    def to_payload(self) -> dict[str, object]:
        root_cause = self.root_cause
        return {
            "contract_version": SERVICE_HOST_STARTUP_FAILURE_CONTRACT_VERSION,
            "authority_id": self.authority_id,
            "generation_id": self.generation_id,
            "service_package": self.service_package,
            "phase": self.phase.value,
            "reason": self.reason,
            "observed_at_utc": self.observed_at_utc,
            "pid": self.pid,
            "exit_code": self.exit_code,
            "causes": [item.to_payload() for item in self.causes],
            "root_cause": root_cause.to_payload() if root_cause is not None else None,
        }


@dataclass(frozen=True, slots=True)
class ServiceHostAttachmentEvidence:
    attachment_id: str
    authority_id: str
    generation_id: str
    consumer_id: str
    session_key: str
    attached_at_utc: str
    lease_renewed_at_utc: str
    lease_expires_at_utc: str

    def to_payload(self) -> dict[str, object]:
        return {
            "contract_version": SERVICE_HOST_ATTACHMENT_CONTRACT_VERSION,
            "attachment_id": self.attachment_id,
            "authority_id": self.authority_id,
            "generation_id": self.generation_id,
            "consumer_id": self.consumer_id,
            "session_key": self.session_key,
            "attached_at_utc": self.attached_at_utc,
            "lease_renewed_at_utc": self.lease_renewed_at_utc,
            "lease_expires_at_utc": self.lease_expires_at_utc,
        }


@dataclass(frozen=True, slots=True)
class ServiceHostLifecycleUpdate:
    update_id: str
    sequence_number: int
    transition: ServiceHostLifecycleTransition
    authority_id: str
    generation_id: str | None
    service_package: str
    reason: str
    observed_at_utc: str
    lifecycle: "ServiceHostLifecycleEvidence"
    attachment: ServiceHostAttachmentEvidence | None = None
    startup_failure: ServiceHostStartupFailureEvidence | None = None
    controller_id: str | None = None

    def to_payload(self) -> dict[str, object]:
        return {
            "contract_version": SERVICE_HOST_LIFECYCLE_UPDATE_CONTRACT_VERSION,
            "update_id": self.update_id,
            "sequence_number": self.sequence_number,
            "transition": self.transition.value,
            "authority_id": self.authority_id,
            "generation_id": self.generation_id,
            "service_package": self.service_package,
            "reason": self.reason,
            "observed_at_utc": self.observed_at_utc,
            "lifecycle": self.lifecycle.to_payload(),
            "attachment": (
                self.attachment.to_payload() if self.attachment is not None else None
            ),
            "startup_failure": (
                self.startup_failure.to_payload()
                if self.startup_failure is not None
                else None
            ),
            "controller_id": self.controller_id,
        }


@dataclass(frozen=True, slots=True)
class ServiceHostLifecycleUpdateBatch:
    journal_available: bool
    authority_id: str | None
    service_package: str | None
    after_sequence_number: int
    first_available_sequence_number: int | None
    latest_sequence_number: int
    next_cursor_sequence_number: int
    cursor_expired: bool
    updates: tuple[ServiceHostLifecycleUpdate, ...]

    @property
    def ready(self) -> bool:
        return self.journal_available and not self.cursor_expired

    def to_payload(self) -> dict[str, object]:
        return {
            "contract_version": (
                SERVICE_HOST_LIFECYCLE_UPDATE_JOURNAL_CONTRACT_VERSION
            ),
            "status": (
                "missing"
                if not self.journal_available
                else ("cursor_expired" if self.cursor_expired else "ready")
            ),
            "ready": self.ready,
            "journal_available": self.journal_available,
            "authority_id": self.authority_id,
            "service_package": self.service_package,
            "after_sequence_number": self.after_sequence_number,
            "first_available_sequence_number": self.first_available_sequence_number,
            "latest_sequence_number": self.latest_sequence_number,
            "next_cursor_sequence_number": self.next_cursor_sequence_number,
            "update_count": len(self.updates),
            "updates": [item.to_payload() for item in self.updates],
        }


@dataclass(frozen=True, slots=True)
class ServiceHostLifecycleEvidence:
    authority_id: str
    generation_id: str | None
    service_package: str
    health_status: ServiceHostHealthStatus
    pid: int | None
    process_alive: bool
    process_matches: bool
    socket_exists: bool
    handshake_ready: bool
    observed_at_utc: str
    reason: str

    @property
    def healthy(self) -> bool:
        return self.health_status is ServiceHostHealthStatus.running_healthy

    @property
    def running(self) -> bool:
        return self.health_status in {
            ServiceHostHealthStatus.running_healthy,
            ServiceHostHealthStatus.running_degraded,
        }

    def to_payload(self) -> dict[str, object]:
        return {
            "contract_version": SERVICE_HOST_LIFECYCLE_CONTRACT_VERSION,
            "authority_id": self.authority_id,
            "generation_id": self.generation_id,
            "service_package": self.service_package,
            "health_status": self.health_status.value,
            "pid": self.pid,
            "process_alive": self.process_alive,
            "process_matches": self.process_matches,
            "socket_exists": self.socket_exists,
            "handshake_ready": self.handshake_ready,
            "observed_at_utc": self.observed_at_utc,
            "reason": self.reason,
            "healthy": self.healthy,
            "running": self.running,
        }


@dataclass(frozen=True, slots=True)
class ServiceHostControlDecision:
    operation: Literal["stop", "restart"]
    allowed: bool
    reason: str
    authority_id: str
    current_generation_id: str | None
    expected_generation_id: str | None
    active_attachment_count: int = 0
    draining: bool = False

    def to_payload(self) -> dict[str, object]:
        return {
            "contract_version": SERVICE_HOST_LIFECYCLE_CONTRACT_VERSION,
            "operation": self.operation,
            "allowed": self.allowed,
            "reason": self.reason,
            "authority_id": self.authority_id,
            "current_generation_id": self.current_generation_id,
            "expected_generation_id": self.expected_generation_id,
            "active_attachment_count": self.active_attachment_count,
            "draining": self.draining,
        }


@dataclass(frozen=True, slots=True)
class ServiceHostAttachmentDecision:
    operation: Literal["attach", "detach", "drain"]
    allowed: bool
    reason: str
    authority_id: str
    current_generation_id: str | None
    expected_generation_id: str | None
    active_attachment_count: int
    draining: bool

    def to_payload(self) -> dict[str, object]:
        return {
            "contract_version": SERVICE_HOST_ATTACHMENT_CONTRACT_VERSION,
            "operation": self.operation,
            "allowed": self.allowed,
            "reason": self.reason,
            "authority_id": self.authority_id,
            "current_generation_id": self.current_generation_id,
            "expected_generation_id": self.expected_generation_id,
            "active_attachment_count": self.active_attachment_count,
            "draining": self.draining,
        }


def service_host_authority_id(
    *,
    service_package: str,
    socket_path: Path,
    state_root: Path,
) -> str:
    identity = "|".join(
        (
            service_package.strip(),
            socket_path.expanduser().resolve().as_posix(),
            state_root.expanduser().resolve().as_posix(),
        )
    )
    return str(uuid5(NAMESPACE_URL, f"aware.service.local-authority:{identity}"))


def new_service_host_generation_id(*, authority_id: str) -> str:
    return str(
        uuid5(
            NAMESPACE_URL,
            f"aware.service.local-authority.generation:{authority_id}:{uuid4()}",
        )
    )


def service_host_attachment(
    *,
    authority_id: str,
    generation_id: str,
    consumer_id: str,
    session_key: str,
    attached_at_utc: str | None = None,
    lease_renewed_at_utc: str | None = None,
    lease_duration_seconds: int = DEFAULT_SERVICE_HOST_ATTACHMENT_LEASE_SECONDS,
) -> ServiceHostAttachmentEvidence:
    identity = "|".join(
        (
            authority_id.strip(),
            generation_id.strip(),
            consumer_id.strip(),
            session_key.strip(),
        )
    )
    attached_at = attached_at_utc or _utc_now()
    renewed_at = lease_renewed_at_utc or attached_at
    lease_expires_at = _service_host_attachment_lease_expiry(
        renewed_at_utc=renewed_at,
        lease_duration_seconds=lease_duration_seconds,
    )
    if lease_expires_at is None:
        raise ValueError("ServiceHost attachment lease timestamp must be ISO-8601 UTC")
    return ServiceHostAttachmentEvidence(
        attachment_id=str(
            uuid5(NAMESPACE_URL, f"aware.service.local-authority.attachment:{identity}")
        ),
        authority_id=authority_id,
        generation_id=generation_id,
        consumer_id=consumer_id,
        session_key=session_key,
        attached_at_utc=attached_at,
        lease_renewed_at_utc=renewed_at,
        lease_expires_at_utc=lease_expires_at,
    )


def renew_service_host_attachment(
    attachment: ServiceHostAttachmentEvidence,
    *,
    renewed_at_utc: str | None = None,
    lease_duration_seconds: int = DEFAULT_SERVICE_HOST_ATTACHMENT_LEASE_SECONDS,
) -> ServiceHostAttachmentEvidence:
    return service_host_attachment(
        authority_id=attachment.authority_id,
        generation_id=attachment.generation_id,
        consumer_id=attachment.consumer_id,
        session_key=attachment.session_key,
        attached_at_utc=attachment.attached_at_utc,
        lease_renewed_at_utc=renewed_at_utc or _utc_now(),
        lease_duration_seconds=lease_duration_seconds,
    )


def partition_service_host_attachments_by_lease(
    attachments: tuple[ServiceHostAttachmentEvidence, ...],
    *,
    observed_at_utc: str | None = None,
) -> tuple[
    tuple[ServiceHostAttachmentEvidence, ...],
    tuple[ServiceHostAttachmentEvidence, ...],
]:
    observed_at = _parse_utc_datetime(observed_at_utc or _utc_now())
    if observed_at is None:
        return attachments, ()
    active: list[ServiceHostAttachmentEvidence] = []
    expired: list[ServiceHostAttachmentEvidence] = []
    for attachment in attachments:
        expires_at = _parse_utc_datetime(attachment.lease_expires_at_utc)
        if expires_at is not None and expires_at <= observed_at:
            expired.append(attachment)
        else:
            active.append(attachment)
    return tuple(active), tuple(expired)


def service_host_attachment_from_payload(
    payload: Mapping[str, object],
) -> ServiceHostAttachmentEvidence | None:
    if payload.get("contract_version") != SERVICE_HOST_ATTACHMENT_CONTRACT_VERSION:
        return None
    attachment_id = _required_text(payload.get("attachment_id"))
    authority_id = _required_text(payload.get("authority_id"))
    generation_id = _required_text(payload.get("generation_id"))
    consumer_id = _required_text(payload.get("consumer_id"))
    session_key = _required_text(payload.get("session_key"))
    attached_at_utc = _required_text(payload.get("attached_at_utc"))
    if None in {
        attachment_id,
        authority_id,
        generation_id,
        consumer_id,
        session_key,
        attached_at_utc,
    }:
        return None
    lease_renewed_at_utc = (
        _required_text(payload.get("lease_renewed_at_utc")) or attached_at_utc
    )
    lease_expires_at_utc = _required_text(payload.get("lease_expires_at_utc"))
    if lease_expires_at_utc is None:
        lease_expires_at_utc = _service_host_attachment_lease_expiry(
            renewed_at_utc=lease_renewed_at_utc,
            lease_duration_seconds=DEFAULT_SERVICE_HOST_ATTACHMENT_LEASE_SECONDS,
        )
    if lease_expires_at_utc is None:
        # Invalid legacy timestamps remain active rather than being pruned unsafely.
        lease_expires_at_utc = attached_at_utc
    return ServiceHostAttachmentEvidence(
        attachment_id=attachment_id,
        authority_id=authority_id,
        generation_id=generation_id,
        consumer_id=consumer_id,
        session_key=session_key,
        attached_at_utc=attached_at_utc,
        lease_renewed_at_utc=lease_renewed_at_utc,
        lease_expires_at_utc=lease_expires_at_utc,
    )


def service_host_lifecycle_from_payload(
    payload: Mapping[str, object],
) -> ServiceHostLifecycleEvidence | None:
    if payload.get("contract_version") != SERVICE_HOST_LIFECYCLE_CONTRACT_VERSION:
        return None
    authority_id = _required_text(payload.get("authority_id"))
    service_package = _required_text(payload.get("service_package"))
    observed_at_utc = _required_text(payload.get("observed_at_utc"))
    reason = _required_text(payload.get("reason"))
    try:
        health_status = ServiceHostHealthStatus(str(payload.get("health_status")))
    except ValueError:
        return None
    if None in {authority_id, service_package, observed_at_utc, reason}:
        return None
    return ServiceHostLifecycleEvidence(
        authority_id=authority_id,
        generation_id=_required_text(payload.get("generation_id")),
        service_package=service_package,
        health_status=health_status,
        pid=_optional_int(payload.get("pid")),
        process_alive=payload.get("process_alive") is True,
        process_matches=payload.get("process_matches") is True,
        socket_exists=payload.get("socket_exists") is True,
        handshake_ready=payload.get("handshake_ready") is True,
        observed_at_utc=observed_at_utc,
        reason=reason,
    )


def service_host_lifecycle_update_from_payload(
    payload: Mapping[str, object],
) -> ServiceHostLifecycleUpdate | None:
    if (
        payload.get("contract_version")
        != SERVICE_HOST_LIFECYCLE_UPDATE_CONTRACT_VERSION
    ):
        return None
    update_id = _required_text(payload.get("update_id"))
    sequence_number = _optional_int(payload.get("sequence_number"))
    authority_id = _required_text(payload.get("authority_id"))
    service_package = _required_text(payload.get("service_package"))
    reason = _required_text(payload.get("reason"))
    observed_at_utc = _required_text(payload.get("observed_at_utc"))
    lifecycle_payload = payload.get("lifecycle")
    lifecycle = (
        service_host_lifecycle_from_payload(lifecycle_payload)
        if isinstance(lifecycle_payload, Mapping)
        else None
    )
    attachment_payload = payload.get("attachment")
    attachment = (
        service_host_attachment_from_payload(attachment_payload)
        if isinstance(attachment_payload, Mapping)
        else None
    )
    startup_failure_payload = payload.get("startup_failure")
    startup_failure = (
        service_host_startup_failure_from_payload(startup_failure_payload)
        if isinstance(startup_failure_payload, Mapping)
        else None
    )
    try:
        transition = ServiceHostLifecycleTransition(str(payload.get("transition")))
    except ValueError:
        return None
    if None in {
        update_id,
        sequence_number,
        authority_id,
        service_package,
        reason,
        observed_at_utc,
        lifecycle,
    }:
        return None
    if (
        lifecycle.authority_id != authority_id
        or lifecycle.generation_id != _required_text(payload.get("generation_id"))
        or lifecycle.service_package != service_package
    ):
        return None
    identity = "|".join(
        (
            authority_id,
            str(sequence_number),
            transition.value,
            lifecycle.generation_id or "none",
        )
    )
    expected_update_id = str(
        uuid5(
            NAMESPACE_URL,
            f"aware.service.local-authority.lifecycle-update:{identity}",
        )
    )
    if update_id != expected_update_id:
        return None
    if (
        transition
        in {
            ServiceHostLifecycleTransition.attachment_added,
            ServiceHostLifecycleTransition.attachment_removed,
        }
        and attachment is None
    ):
        return None
    if attachment is not None and (
        attachment.authority_id != authority_id
        or attachment.generation_id != lifecycle.generation_id
    ):
        return None
    controller_id = _required_text(payload.get("controller_id"))
    if (
        transition is ServiceHostLifecycleTransition.drain_started
        and controller_id is None
    ):
        return None
    if (
        transition is ServiceHostLifecycleTransition.generation_failed
        and startup_failure is None
    ):
        return None
    if startup_failure is not None and (
        startup_failure.authority_id != authority_id
        or startup_failure.generation_id != lifecycle.generation_id
        or startup_failure.service_package != service_package
    ):
        return None
    return ServiceHostLifecycleUpdate(
        update_id=update_id,
        sequence_number=sequence_number,
        transition=transition,
        authority_id=authority_id,
        generation_id=_required_text(payload.get("generation_id")),
        service_package=service_package,
        reason=reason,
        observed_at_utc=observed_at_utc,
        lifecycle=lifecycle,
        attachment=attachment,
        startup_failure=startup_failure,
        controller_id=controller_id,
    )


def append_service_host_lifecycle_update(
    *,
    path: Path,
    transition: ServiceHostLifecycleTransition,
    lifecycle: ServiceHostLifecycleEvidence,
    reason: str,
    attachment: ServiceHostAttachmentEvidence | None = None,
    startup_failure: ServiceHostStartupFailureEvidence | None = None,
    controller_id: str | None = None,
    observed_at_utc: str | None = None,
    retention: int = DEFAULT_SERVICE_HOST_LIFECYCLE_UPDATE_RETENTION,
) -> ServiceHostLifecycleUpdate:
    if retention < 1:
        raise ValueError("ServiceHost lifecycle update retention must be positive")
    if (
        transition
        in {
            ServiceHostLifecycleTransition.attachment_added,
            ServiceHostLifecycleTransition.attachment_removed,
        }
        and attachment is None
    ):
        raise ValueError("Attachment lifecycle updates require attachment evidence")
    if transition is ServiceHostLifecycleTransition.drain_started and not controller_id:
        raise ValueError("Drain lifecycle updates require controller_id")
    if (
        transition is ServiceHostLifecycleTransition.generation_failed
        and startup_failure is None
    ):
        raise ValueError("Failed-generation updates require startup failure evidence")
    if attachment is not None and (
        attachment.authority_id != lifecycle.authority_id
        or attachment.generation_id != lifecycle.generation_id
    ):
        raise ValueError("Attachment lifecycle update coordinates do not match")
    if startup_failure is not None and (
        startup_failure.authority_id != lifecycle.authority_id
        or startup_failure.generation_id != lifecycle.generation_id
        or startup_failure.service_package != lifecycle.service_package
    ):
        raise ValueError("Startup failure lifecycle update coordinates do not match")
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(path.suffix + ".lock")
    with lock_path.open("a+b") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            journal = _read_service_host_lifecycle_update_journal(path)
            existing_authority_id = _required_text(journal.get("authority_id"))
            if (
                existing_authority_id is not None
                and existing_authority_id != lifecycle.authority_id
            ):
                raise ValueError("ServiceHost lifecycle journal authority mismatch")
            sequence_number = max(
                _optional_int(journal.get("next_sequence_number"), positive_only=False)
                or 1,
                1,
            )
            timestamp = observed_at_utc or _utc_now()
            identity = "|".join(
                (
                    lifecycle.authority_id,
                    str(sequence_number),
                    transition.value,
                    lifecycle.generation_id or "none",
                )
            )
            update = ServiceHostLifecycleUpdate(
                update_id=str(
                    uuid5(
                        NAMESPACE_URL,
                        f"aware.service.local-authority.lifecycle-update:{identity}",
                    )
                ),
                sequence_number=sequence_number,
                transition=transition,
                authority_id=lifecycle.authority_id,
                generation_id=lifecycle.generation_id,
                service_package=lifecycle.service_package,
                reason=reason,
                observed_at_utc=timestamp,
                lifecycle=lifecycle,
                attachment=attachment,
                startup_failure=startup_failure,
                controller_id=controller_id,
            )
            existing_updates = _service_host_lifecycle_updates_from_journal(journal)
            retained = (*existing_updates, update)[-retention:]
            payload = {
                "contract_version": (
                    SERVICE_HOST_LIFECYCLE_UPDATE_JOURNAL_CONTRACT_VERSION
                ),
                "authority_id": lifecycle.authority_id,
                "service_package": lifecycle.service_package,
                "first_available_sequence_number": retained[0].sequence_number,
                "latest_sequence_number": retained[-1].sequence_number,
                "next_sequence_number": sequence_number + 1,
                "retention": retention,
                "updates": [item.to_payload() for item in retained],
            }
            _write_json_atomic(path=path, payload=payload)
            return update
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def observe_service_host_lifecycle_updates(
    *,
    path: Path,
    after_sequence_number: int = 0,
    limit: int = 100,
) -> ServiceHostLifecycleUpdateBatch:
    if after_sequence_number < 0:
        raise ValueError("after_sequence_number must be non-negative")
    if limit < 1:
        raise ValueError("limit must be positive")
    journal = _read_service_host_lifecycle_update_journal(path)
    journal_available = bool(journal)
    updates = _service_host_lifecycle_updates_from_journal(journal)
    first_available = updates[0].sequence_number if updates else None
    latest = updates[-1].sequence_number if updates else 0
    cursor_expired = bool(
        first_available is not None
        and after_sequence_number > 0
        and after_sequence_number < first_available - 1
    )
    selected = (
        ()
        if cursor_expired
        else tuple(
            item for item in updates if item.sequence_number > after_sequence_number
        )[:limit]
    )
    next_sequence = selected[-1].sequence_number if selected else after_sequence_number
    return ServiceHostLifecycleUpdateBatch(
        journal_available=journal_available,
        authority_id=_required_text(journal.get("authority_id")),
        service_package=_required_text(journal.get("service_package")),
        after_sequence_number=after_sequence_number,
        first_available_sequence_number=first_available,
        latest_sequence_number=latest,
        next_cursor_sequence_number=next_sequence,
        cursor_expired=cursor_expired,
        updates=selected,
    )


def authorize_service_host_attachment(
    *,
    operation: Literal["attach", "detach", "drain"],
    lifecycle: ServiceHostLifecycleEvidence,
    expected_generation_id: str | None,
    active_attachment_count: int,
    draining: bool,
) -> ServiceHostAttachmentDecision:
    current_generation_id = lifecycle.generation_id
    if current_generation_id is None:
        allowed = False
        reason = "running_service_host_generation_missing"
    elif expected_generation_id is None:
        allowed = False
        reason = "expected_service_host_generation_required"
    elif expected_generation_id != current_generation_id:
        allowed = False
        reason = "service_host_generation_mismatch"
    elif operation != "detach" and not lifecycle.running:
        allowed = False
        reason = "service_host_not_running"
    elif operation == "attach" and draining:
        allowed = False
        reason = "service_host_generation_draining"
    else:
        allowed = True
        reason = {
            "attach": "service_host_attachment_allowed",
            "detach": "service_host_detachment_allowed",
            "drain": "service_host_drain_allowed",
        }[operation]
    return ServiceHostAttachmentDecision(
        operation=operation,
        allowed=allowed,
        reason=reason,
        authority_id=lifecycle.authority_id,
        current_generation_id=current_generation_id,
        expected_generation_id=expected_generation_id,
        active_attachment_count=max(active_attachment_count, 0),
        draining=draining,
    )


def service_host_startup_failure_from_exception(
    *,
    authority_id: str,
    generation_id: str,
    service_package: str,
    phase: ServiceHostStartupPhase,
    error: BaseException,
    pid: int | None = None,
    exit_code: int | None = None,
    observed_at_utc: str | None = None,
) -> ServiceHostStartupFailureEvidence:
    return ServiceHostStartupFailureEvidence(
        authority_id=authority_id,
        generation_id=generation_id,
        service_package=service_package,
        phase=phase,
        reason=f"service_host_{phase.value}_failed",
        observed_at_utc=observed_at_utc or _utc_now(),
        pid=pid,
        exit_code=exit_code,
        causes=_exception_causes(error),
    )


def service_host_startup_failure_for_process_exit(
    *,
    authority_id: str,
    generation_id: str,
    service_package: str,
    pid: int | None,
    exit_code: int,
    observed_at_utc: str | None = None,
) -> ServiceHostStartupFailureEvidence:
    return ServiceHostStartupFailureEvidence(
        authority_id=authority_id,
        generation_id=generation_id,
        service_package=service_package,
        phase=ServiceHostStartupPhase.process_exit,
        reason="service_host_process_exited_before_ready",
        observed_at_utc=observed_at_utc or _utc_now(),
        pid=pid,
        exit_code=exit_code,
        causes=(),
    )


def service_host_startup_failure_with_process_exit(
    evidence: ServiceHostStartupFailureEvidence,
    *,
    pid: int | None,
    exit_code: int,
) -> ServiceHostStartupFailureEvidence:
    return ServiceHostStartupFailureEvidence(
        authority_id=evidence.authority_id,
        generation_id=evidence.generation_id,
        service_package=evidence.service_package,
        phase=evidence.phase,
        reason=evidence.reason,
        observed_at_utc=evidence.observed_at_utc,
        pid=pid if pid is not None else evidence.pid,
        exit_code=exit_code,
        causes=evidence.causes,
    )


def service_host_startup_failure_from_payload(
    payload: Mapping[str, object],
) -> ServiceHostStartupFailureEvidence | None:
    if payload.get("contract_version") != SERVICE_HOST_STARTUP_FAILURE_CONTRACT_VERSION:
        return None
    authority_id = _required_text(payload.get("authority_id"))
    generation_id = _required_text(payload.get("generation_id"))
    service_package = _required_text(payload.get("service_package"))
    reason = _required_text(payload.get("reason"))
    observed_at_utc = _required_text(payload.get("observed_at_utc"))
    try:
        phase = ServiceHostStartupPhase(str(payload.get("phase")))
    except ValueError:
        return None
    if None in {
        authority_id,
        generation_id,
        service_package,
        reason,
        observed_at_utc,
    }:
        return None
    raw_causes = payload.get("causes")
    if not isinstance(raw_causes, list):
        return None
    causes: list[ServiceHostStartupFailureCause] = []
    for raw_cause in raw_causes:
        if not isinstance(raw_cause, dict):
            return None
        exception_type = _required_text(raw_cause.get("exception_type"))
        exception_module = _required_text(raw_cause.get("exception_module"))
        message = _required_text(raw_cause.get("message"), allow_empty=True)
        if exception_type is None or exception_module is None or message is None:
            return None
        causes.append(
            ServiceHostStartupFailureCause(
                exception_type=exception_type,
                exception_module=exception_module,
                message=message,
            )
        )
    return ServiceHostStartupFailureEvidence(
        authority_id=authority_id,
        generation_id=generation_id,
        service_package=service_package,
        phase=phase,
        reason=reason,
        observed_at_utc=observed_at_utc,
        pid=_optional_int(payload.get("pid")),
        exit_code=_optional_int(payload.get("exit_code"), positive_only=False),
        causes=tuple(causes),
    )


def write_service_host_startup_failure(
    *, path: Path, evidence: ServiceHostStartupFailureEvidence
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.{uuid4()}.tmp")
    temporary_path.write_text(
        json.dumps(evidence.to_payload(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(path)


def read_service_host_startup_failure(
    path: Path,
) -> ServiceHostStartupFailureEvidence | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError, UnicodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return service_host_startup_failure_from_payload(payload)


def write_service_host_startup_failure_from_environment(
    *, phase: ServiceHostStartupPhase, error: BaseException
) -> ServiceHostStartupFailureEvidence | None:
    authority_id = _required_text(os.getenv(SERVICE_HOST_AUTHORITY_ID_ENV))
    generation_id = _required_text(os.getenv(SERVICE_HOST_GENERATION_ID_ENV))
    service_package = _required_text(os.getenv(SERVICE_HOST_PACKAGE_ENV))
    path_text = _required_text(os.getenv(SERVICE_HOST_STARTUP_FAILURE_PATH_ENV))
    if None in {authority_id, generation_id, service_package, path_text}:
        return None
    evidence = service_host_startup_failure_from_exception(
        authority_id=authority_id,
        generation_id=generation_id,
        service_package=service_package,
        phase=phase,
        error=error,
        pid=os.getpid(),
    )
    write_service_host_startup_failure(path=Path(path_text), evidence=evidence)
    return evidence


def classify_service_host_lifecycle(
    *,
    authority_id: str,
    generation_id: str | None,
    service_package: str,
    pid: int | None,
    process_alive: bool,
    process_matches: bool,
    socket_exists: bool,
    handshake_ready: bool,
    artifacts_exist: bool,
    observed_at_utc: str | None = None,
) -> ServiceHostLifecycleEvidence:
    if process_alive and process_matches and socket_exists and handshake_ready:
        health_status = ServiceHostHealthStatus.running_healthy
        reason = "service_host_handshake_ready"
    elif process_alive and process_matches:
        health_status = ServiceHostHealthStatus.running_degraded
        reason = "service_host_process_alive_handshake_unavailable"
    elif artifacts_exist:
        health_status = ServiceHostHealthStatus.stale
        reason = "service_host_authority_artifacts_stale"
    else:
        health_status = ServiceHostHealthStatus.stopped
        reason = "service_host_not_running"
    return ServiceHostLifecycleEvidence(
        authority_id=authority_id,
        generation_id=generation_id,
        service_package=service_package,
        health_status=health_status,
        pid=pid,
        process_alive=process_alive,
        process_matches=process_matches,
        socket_exists=socket_exists,
        handshake_ready=handshake_ready,
        observed_at_utc=observed_at_utc or _utc_now(),
        reason=reason,
    )


def authorize_service_host_control(
    *,
    operation: Literal["stop", "restart"],
    lifecycle: ServiceHostLifecycleEvidence,
    expected_generation_id: str | None,
    active_attachment_count: int = 0,
    draining: bool = False,
) -> ServiceHostControlDecision:
    current_generation_id = lifecycle.generation_id
    if lifecycle.running and current_generation_id is None:
        allowed = False
        reason = "running_service_host_generation_missing"
    elif lifecycle.running and expected_generation_id is None:
        allowed = False
        reason = "expected_service_host_generation_required"
    elif (
        lifecycle.running
        and current_generation_id is not None
        and expected_generation_id != current_generation_id
    ):
        allowed = False
        reason = "service_host_generation_mismatch"
    elif lifecycle.running and active_attachment_count > 0:
        allowed = False
        reason = "active_service_host_attachments_present"
    else:
        allowed = True
        reason = (
            "service_host_generation_matched"
            if lifecycle.running
            else "service_host_not_running_control_allowed"
        )
    return ServiceHostControlDecision(
        operation=operation,
        allowed=allowed,
        reason=reason,
        authority_id=lifecycle.authority_id,
        current_generation_id=current_generation_id,
        expected_generation_id=expected_generation_id,
        active_attachment_count=max(active_attachment_count, 0),
        draining=draining,
    )


def _utc_now() -> str:
    return datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")


def _service_host_attachment_lease_expiry(
    *,
    renewed_at_utc: str,
    lease_duration_seconds: int,
) -> str | None:
    if lease_duration_seconds <= 0:
        raise ValueError("ServiceHost attachment lease duration must be positive")
    renewed_at = _parse_utc_datetime(renewed_at_utc)
    if renewed_at is None:
        return None
    return (
        (renewed_at + timedelta(seconds=lease_duration_seconds))
        .isoformat()
        .replace("+00:00", "Z")
    )


def _parse_utc_datetime(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(UTC)


def _exception_causes(
    error: BaseException,
) -> tuple[ServiceHostStartupFailureCause, ...]:
    causes: list[ServiceHostStartupFailureCause] = []
    seen: set[int] = set()
    current: BaseException | None = error
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        causes.append(
            ServiceHostStartupFailureCause(
                exception_type=current.__class__.__name__,
                exception_module=current.__class__.__module__,
                message=str(current),
            )
        )
        current = current.__cause__ or current.__context__
    return tuple(causes)


def _required_text(value: object, *, allow_empty: bool = False) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if text or allow_empty:
        return text
    return None


def _optional_int(value: object, *, positive_only: bool = True) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        result = int(str(value))
    except (TypeError, ValueError):
        return None
    if positive_only and result <= 0:
        return None
    return result


def _read_service_host_lifecycle_update_journal(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.expanduser().resolve().read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"ServiceHost lifecycle update journal is invalid: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise ValueError("ServiceHost lifecycle update journal must be a JSON object")
    contract_version = payload.get("contract_version")
    if contract_version != SERVICE_HOST_LIFECYCLE_UPDATE_JOURNAL_CONTRACT_VERSION:
        raise ValueError(
            "ServiceHost lifecycle update journal contract version is unsupported"
        )
    return payload


def _service_host_lifecycle_updates_from_journal(
    journal: Mapping[str, object],
) -> tuple[ServiceHostLifecycleUpdate, ...]:
    raw_updates = journal.get("updates")
    if raw_updates is None:
        return ()
    if not isinstance(raw_updates, list):
        raise ValueError("ServiceHost lifecycle update journal updates must be a list")
    updates: list[ServiceHostLifecycleUpdate] = []
    for payload in raw_updates:
        if not isinstance(payload, Mapping):
            raise ValueError("ServiceHost lifecycle update payload must be an object")
        update = service_host_lifecycle_update_from_payload(payload)
        if update is None:
            raise ValueError("ServiceHost lifecycle update payload is invalid")
        updates.append(update)
    if any(
        current.sequence_number >= following.sequence_number
        for current, following in zip(updates, updates[1:], strict=False)
    ):
        raise ValueError("ServiceHost lifecycle updates must be strictly ordered")
    return tuple(updates)


def _write_json_atomic(*, path: Path, payload: Mapping[str, object]) -> None:
    temporary_path = path.with_name(f".{path.name}.{uuid4()}.tmp")
    temporary_path.write_text(
        json.dumps(dict(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(path)


__all__ = [
    "SERVICE_HOST_ATTACHMENT_CONTRACT_VERSION",
    "SERVICE_HOST_LIFECYCLE_UPDATE_CONTRACT_VERSION",
    "SERVICE_HOST_LIFECYCLE_UPDATE_JOURNAL_CONTRACT_VERSION",
    "SERVICE_HOST_LIFECYCLE_CONTRACT_VERSION",
    "SERVICE_HOST_STARTUP_FAILURE_CONTRACT_VERSION",
    "SERVICE_HOST_AUTHORITY_ID_ENV",
    "SERVICE_HOST_GENERATION_ID_ENV",
    "SERVICE_HOST_PACKAGE_ENV",
    "SERVICE_HOST_STARTUP_FAILURE_PATH_ENV",
    "ServiceHostControlDecision",
    "ServiceHostAttachmentDecision",
    "ServiceHostAttachmentEvidence",
    "ServiceHostHealthStatus",
    "ServiceHostLifecycleEvidence",
    "ServiceHostLifecycleTransition",
    "ServiceHostLifecycleUpdate",
    "ServiceHostLifecycleUpdateBatch",
    "ServiceHostStartupFailureCause",
    "ServiceHostStartupFailureEvidence",
    "ServiceHostStartupPhase",
    "authorize_service_host_control",
    "authorize_service_host_attachment",
    "append_service_host_lifecycle_update",
    "classify_service_host_lifecycle",
    "new_service_host_generation_id",
    "read_service_host_startup_failure",
    "observe_service_host_lifecycle_updates",
    "service_host_authority_id",
    "service_host_attachment",
    "service_host_attachment_from_payload",
    "service_host_lifecycle_from_payload",
    "service_host_lifecycle_update_from_payload",
    "service_host_startup_failure_for_process_exit",
    "service_host_startup_failure_from_exception",
    "service_host_startup_failure_from_payload",
    "service_host_startup_failure_with_process_exit",
    "write_service_host_startup_failure",
    "write_service_host_startup_failure_from_environment",
]
