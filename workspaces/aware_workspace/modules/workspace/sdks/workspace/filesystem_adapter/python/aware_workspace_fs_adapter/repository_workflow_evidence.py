"""Bounded immutable workflow evidence; never publication or source authority."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import stat
import time
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from aware_workspace_sdk.repository_workflow_codec import (
    MAX_WORKFLOW_ATTEMPT_BYTES,
    MAX_WORKFLOW_RECORD_BYTES,
    MAX_WORKFLOW_RECORDS,
    WorkspaceWorkflowValueError,
    repository_workflow_value_from_payload,
    repository_workflow_value_to_payload,
)
from aware_workspace_sdk.repository_workflow_values import (
    WorkflowCleanup,
    WorkflowIntegrity,
    WorkflowPersistence,
    WorkflowRefusalCode,
    WorkspaceRepositoryWorkflowCleanupObservation,
    WorkspaceRepositoryWorkflowEvidenceAppendRequest,
    WorkspaceRepositoryWorkflowPlanObservation,
    WorkspaceRepositoryWorkflowRefusalEvidence,
    WorkspaceWorkflowEvidenceReference,
)

_CONTRACT = "aware.workspace.repository-workflow-evidence.v1"
_DIRECTORY = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
_FILE = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC


class WorkflowEvidenceError(ValueError):
    def __init__(
        self,
        code: WorkflowRefusalCode,
        *,
        persistence: WorkflowPersistence = "not_written",
        cleanup: WorkflowCleanup = "completed",
        evidence_refs: tuple[WorkspaceWorkflowEvidenceReference, ...] = (),
    ) -> None:
        super().__init__(code)
        self.code: WorkflowRefusalCode = code
        self.persistence: WorkflowPersistence = persistence
        self.cleanup: WorkflowCleanup = cleanup
        self.evidence_refs = evidence_refs


@dataclass(frozen=True, slots=True)
class WorkflowEvidenceSnapshot:
    plan: WorkspaceRepositoryWorkflowPlanObservation
    records: tuple[WorkspaceRepositoryWorkflowEvidenceAppendRequest, ...]
    cursor: int
    digest: str
    integrity: WorkflowIntegrity
    cleanup: WorkflowCleanup
    size_bytes: int
    evidence_refs: tuple[WorkspaceWorkflowEvidenceReference, ...] = ()


@dataclass(slots=True)
class _LockedEvidence:
    directory: int
    persistence: WorkflowPersistence = "not_written"
    evidence_refs: tuple[WorkspaceWorkflowEvidenceReference, ...] = ()
    binding_ref: str | None = None
    cleanup: WorkflowCleanup = "completed"

    def written(self, key: str, name: str, body: bytes) -> None:
        self.persistence = "persisted"
        self.evidence_refs = (
            WorkspaceWorkflowEvidenceReference(
                _CONTRACT, f"{key}/{name}", _digest(body), len(body)
            ),
        )

    def annotate_interruption(self, error: BaseException, *, uncertain: bool) -> None:
        if self.persistence == "persisted":
            vars(error)["workflow_evidence"] = (
                WorkspaceRepositoryWorkflowRefusalEvidence(
                    "source_unavailable",
                    "evidence_closeout",
                    self.evidence_refs,
                    self.persistence,
                    WorkspaceRepositoryWorkflowCleanupObservation(
                        self.binding_ref, "unknown" if uncertain else self.cleanup, ()
                    ),
                    ("journal_call_interrupted",),
                )
            )


def _digest(body: bytes) -> str:
    return "sha256:" + hashlib.sha256(body).hexdigest()


def _wire(value: object) -> bytes:
    body = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    if len(body) > MAX_WORKFLOW_RECORD_BYTES:
        raise WorkflowEvidenceError("malformed_binding")
    return body


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise WorkflowEvidenceError("evidence_corrupt")
        value[key] = item
    return value


def _number(value: str) -> None:
    raise WorkflowEvidenceError("evidence_corrupt")


def _payload(body: bytes) -> dict[str, Any]:
    try:
        value = json.loads(
            body, object_pairs_hook=_pairs, parse_float=_number, parse_constant=_number
        )
        if type(value) is not dict or _wire(cast(dict[str, Any], value)) != body:
            raise WorkflowEvidenceError("evidence_corrupt")
        return cast(dict[str, Any], value)
    except (ValueError, UnicodeError, RecursionError) as error:
        if type(error) is WorkflowEvidenceError:
            raise
        raise WorkflowEvidenceError("evidence_corrupt") from error


def _read(directory: int, name: str) -> bytes:
    descriptor = os.open(name, _FILE, dir_fd=directory)
    try:
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_size > MAX_WORKFLOW_RECORD_BYTES
        ):
            raise WorkflowEvidenceError("evidence_corrupt")
        body = bytearray()
        while chunk := os.read(
            descriptor, min(65536, MAX_WORKFLOW_RECORD_BYTES + 1 - len(body))
        ):
            body.extend(chunk)
            if len(body) > MAX_WORKFLOW_RECORD_BYTES:
                raise WorkflowEvidenceError("evidence_corrupt")
        return bytes(body)
    finally:
        os.close(descriptor)


def _write(
    directory: int, name: str, body: bytes
) -> tuple[WorkflowPersistence, WorkflowCleanup]:
    # Link publishes once without overwriting an existing immutable slot.
    pending = ".pending-" + str(uuid.uuid4())
    descriptor = None
    durable = False
    created = False
    try:
        descriptor = os.open(
            pending,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
            0o600,
            dir_fd=directory,
        )
        created = True
        position = 0
        while position < len(body):
            written = os.write(descriptor, body[position:])
            if written <= 0:
                raise OSError("evidence write made no progress")
            position += written
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        os.link(
            pending,
            name,
            src_dir_fd=directory,
            dst_dir_fd=directory,
            follow_symlinks=False,
        )
        os.fsync(directory)
        durable = True
        os.unlink(pending, dir_fd=directory)
        os.fsync(directory)
        return "persisted", "completed"
    except OSError as error:
        if durable:
            return "persisted", "incomplete"
        raise WorkflowEvidenceError(
            "evidence_persistence_unknown" if created else "source_unavailable",
            persistence="unknown" if created else "not_written",
            cleanup="incomplete" if created else "completed",
        ) from error
    finally:
        if descriptor is not None:
            os.close(descriptor)


class FilesystemWorkflowEvidence:
    """Explicit physical root; descriptor-scoped calls and process-local selection."""

    def __init__(self, root: Path) -> None:
        if (
            type(root) is not type(Path())
            or not root.is_absolute()
            or root.resolve() != root
        ):
            raise WorkflowEvidenceError("malformed_binding")
        self.root, self.pid = root, os.getpid()
        self._root_identity: tuple[int, int] | None = None

    def _live(self) -> None:
        if self.pid != os.getpid():
            raise WorkflowEvidenceError("foreign_or_retired_handle")

    @staticmethod
    def key(source: str, target: str, attempt_ref: str) -> str:
        return hashlib.sha256(_wire([source, target, attempt_ref])).hexdigest()

    @contextmanager
    def _locked(
        self, key: str, *, create: bool
    ) -> Generator[_LockedEvidence, None, None]:
        self._live()
        if len(key) != 64 or any(c not in "0123456789abcdef" for c in key):
            raise WorkflowEvidenceError("malformed_binding")
        parent = root = directory = lock = None
        scope: _LockedEvidence | None = None
        primary: BaseException | None = None
        try:
            parent = os.open(self.root.parent, _DIRECTORY)
            if create:
                try:
                    os.mkdir(self.root.name, 0o700, dir_fd=parent)
                    os.fsync(parent)
                except FileExistsError:
                    pass
            root = os.open(self.root.name, _DIRECTORY, dir_fd=parent)
            metadata = os.fstat(root)
            identity_root = metadata.st_dev, metadata.st_ino
            if self._root_identity is not None and identity_root != self._root_identity:
                raise WorkflowEvidenceError("evidence_conflict")
            self._root_identity = identity_root
            if create:
                try:
                    os.mkdir(key, 0o700, dir_fd=root)
                    os.fsync(root)
                except FileExistsError:
                    pass
            directory = os.open(key, _DIRECTORY, dir_fd=root)
            lock = os.open(
                "lock",
                (os.O_RDWR | os.O_CREAT if create else os.O_RDONLY)
                | os.O_NOFOLLOW
                | os.O_CLOEXEC
                | os.O_NONBLOCK,
                0o600,
                dir_fd=directory,
            )
            if not stat.S_ISREG(os.fstat(lock).st_mode):
                raise WorkflowEvidenceError("evidence_corrupt")
            deadline = time.monotonic() + 2
            while True:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise WorkflowEvidenceError("evidence_conflict") from None
                    time.sleep(0.005)
            identity = os.fstat(directory)
            live = os.stat(key, dir_fd=root, follow_symlinks=False)
            if (identity.st_dev, identity.st_ino) != (
                live.st_dev,
                live.st_ino,
            ) or not stat.S_ISDIR(live.st_mode):
                raise WorkflowEvidenceError("evidence_conflict")
            scope = _LockedEvidence(directory)
            yield scope
        except OSError as error:
            primary = WorkflowEvidenceError(
                "source_unavailable",
                persistence=scope.persistence if scope else "not_written",
                evidence_refs=scope.evidence_refs if scope else (),
            )
            raise primary from error
        except BaseException as error:
            primary = error
            if (
                type(error) is WorkflowEvidenceError
                and scope is not None
                and scope.persistence == "persisted"
            ):
                error.persistence = "persisted"
                error.evidence_refs = scope.evidence_refs
            raise
        finally:
            cleanup_error: BaseException | None = None
            for descriptor in (lock, directory, root, parent):
                if descriptor is not None:
                    try:
                        # Each owned descriptor gets one release attempt, even if a
                        # previous release failed or was interrupted. Never retry a
                        # close whose descriptor may already have been released.
                        os.close(descriptor)
                    except (OSError, KeyboardInterrupt, SystemExit) as error:
                        if cleanup_error is None:
                            cleanup_error = error
            if scope is not None and isinstance(
                primary, (KeyboardInterrupt, SystemExit)
            ):
                scope.annotate_interruption(
                    primary, uncertain=cleanup_error is not None
                )
            if cleanup_error is not None:
                if type(primary) is WorkflowEvidenceError:
                    primary.cleanup = "unknown"
                    primary.add_note(
                        "Descriptor cleanup failed: " + repr(cleanup_error)
                    )
                elif primary is not None:
                    primary.add_note("Workflow descriptor cleanup is unknown")
                elif isinstance(cleanup_error, (KeyboardInterrupt, SystemExit)):
                    if scope is not None:
                        scope.annotate_interruption(cleanup_error, uncertain=True)
                    cleanup_error.add_note(
                        "Workflow persistence="
                        + (scope.persistence if scope else "not_written")
                        + "; descriptor cleanup=unknown"
                    )
                    raise cleanup_error
                else:
                    raise WorkflowEvidenceError(
                        "source_unavailable",
                        persistence=scope.persistence if scope else "not_written",
                        cleanup="unknown",
                        evidence_refs=scope.evidence_refs if scope else (),
                    ) from cleanup_error

    def _snapshot(
        self, directory: int, *, key: str, expected_binding: str
    ) -> WorkflowEvidenceSnapshot:
        try:
            header = _read(directory, "header.json")
        except FileNotFoundError as error:
            raise WorkflowEvidenceError(
                "evidence_persistence_unknown", persistence="unknown"
            ) from error
        value = _payload(header)
        if (
            set(value) != {"contract", "attempt_ref", "plan"}
            or value["contract"] != _CONTRACT
            or type(value["attempt_ref"]) is not str
        ):
            raise WorkflowEvidenceError("evidence_corrupt")
        try:
            plan = repository_workflow_value_from_payload(
                WorkspaceRepositoryWorkflowPlanObservation, value["plan"]
            )
        except WorkspaceWorkflowValueError as error:
            raise WorkflowEvidenceError("evidence_corrupt") from error
        if (
            plan.binding_ref != expected_binding
            or self.key(
                plan.source_repository_binding_ref,
                plan.target_repository_binding_ref,
                value["attempt_ref"],
            )
            != key
        ):
            raise WorkflowEvidenceError("evidence_conflict")
        names = os.listdir(directory)
        slots = sorted(n for n in names if n.endswith(".json") and n != "header.json")
        if len(slots) > MAX_WORKFLOW_RECORDS or any(
            n not in {"header.json", "lock", *slots} and not n.startswith(".pending-")
            for n in names
        ):
            raise WorkflowEvidenceError("evidence_corrupt")
        records: list[WorkspaceRepositoryWorkflowEvidenceAppendRequest] = []
        digest = _digest(header)
        size_bytes = len(header)
        for ordinal, name in enumerate(slots, 1):
            if name != f"{ordinal:06d}.json":
                raise WorkflowEvidenceError("evidence_corrupt")
            body = _read(directory, name)
            size_bytes += len(body)
            if size_bytes > MAX_WORKFLOW_ATTEMPT_BYTES:
                raise WorkflowEvidenceError("evidence_corrupt")
            envelope = _payload(body)
            if (
                set(envelope) != {"previous_digest", "body"}
                or envelope["previous_digest"] != digest
            ):
                raise WorkflowEvidenceError("evidence_corrupt")
            try:
                record = repository_workflow_value_from_payload(
                    WorkspaceRepositoryWorkflowEvidenceAppendRequest, envelope["body"]
                )
            except WorkspaceWorkflowValueError as error:
                raise WorkflowEvidenceError("evidence_corrupt") from error
            if (
                record.attempt_binding_ref != plan.binding_ref
                or record.expected_cursor != ordinal - 1
                or record.expected_previous_digest != digest
                or record.evidence_grade != "caller_reported"
            ):
                raise WorkflowEvidenceError("evidence_corrupt")
            records.append(record)
            digest = _digest(body)
        pending = any(n.startswith(".pending-") for n in names)
        return WorkflowEvidenceSnapshot(
            plan,
            tuple(records),
            len(records),
            digest,
            "incomplete" if pending else "verified",
            "incomplete" if pending else "completed",
            size_bytes,
            (
                WorkspaceWorkflowEvidenceReference(
                    _CONTRACT, f"{key}/header.json", _digest(header), len(header)
                ),
            ),
        )

    def open(
        self, plan: WorkspaceRepositoryWorkflowPlanObservation, attempt_ref: str
    ) -> WorkflowEvidenceSnapshot:
        header = _wire(
            {
                "contract": _CONTRACT,
                "attempt_ref": attempt_ref,
                "plan": repository_workflow_value_to_payload(plan),
            }
        )
        key = self.key(
            plan.source_repository_binding_ref,
            plan.target_repository_binding_ref,
            attempt_ref,
        )
        with self._locked(key, create=True) as scope:
            directory = scope.directory
            scope.binding_ref = plan.binding_ref
            if "header.json" not in os.listdir(directory):
                names = set(os.listdir(directory))
                if any(n.startswith(".pending-") for n in names):
                    raise WorkflowEvidenceError(
                        "evidence_persistence_unknown", persistence="unknown"
                    )
                if names != {"lock"}:
                    raise WorkflowEvidenceError("evidence_corrupt")
                persistence, cleanup = _write(directory, "header.json", header)
                scope.cleanup = cleanup
                if persistence == "persisted":
                    scope.written(key, "header.json", header)
                if persistence != "persisted" or cleanup != "completed":
                    raise WorkflowEvidenceError(
                        "evidence_persistence_unknown",
                        persistence=persistence,
                        cleanup=cleanup,
                    )
            elif _read(directory, "header.json") != header:
                raise WorkflowEvidenceError("evidence_conflict")
            result = self._snapshot(
                directory, key=key, expected_binding=plan.binding_ref
            )
            if result.integrity != "verified":
                raise WorkflowEvidenceError(
                    "evidence_persistence_unknown",
                    persistence="unknown",
                    cleanup=result.cleanup,
                )
            scope.written(key, "header.json", header)
            return result

    def observe(
        self, source: str, target: str, attempt_ref: str, binding: str
    ) -> WorkflowEvidenceSnapshot:
        key = self.key(source, target, attempt_ref)
        with self._locked(key, create=False) as scope:
            directory = scope.directory
            scope.binding_ref = binding
            result = self._snapshot(directory, key=key, expected_binding=binding)
            if result.integrity == "verified":
                scope.persistence = "persisted"
                scope.evidence_refs = result.evidence_refs
            return result

    def append(
        self,
        source: str,
        target: str,
        attempt_ref: str,
        request: WorkspaceRepositoryWorkflowEvidenceAppendRequest,
    ) -> tuple[int, str, WorkflowPersistence, WorkflowCleanup]:
        payload = repository_workflow_value_to_payload(request)
        if request.evidence_grade != "caller_reported":
            raise WorkflowEvidenceError("supplier_unavailable")
        key = self.key(source, target, attempt_ref)
        with self._locked(key, create=False) as scope:
            directory = scope.directory
            scope.binding_ref = request.attempt_binding_ref
            snapshot = self._snapshot(
                directory, key=key, expected_binding=request.attempt_binding_ref
            )
            if snapshot.integrity != "verified":
                raise WorkflowEvidenceError(
                    "evidence_persistence_unknown",
                    persistence="unknown",
                    cleanup=snapshot.cleanup,
                )
            body = _wire(
                {"previous_digest": request.expected_previous_digest, "body": payload}
            )
            if request.expected_cursor < snapshot.cursor:
                existing = _read(directory, f"{request.expected_cursor + 1:06d}.json")
                if existing != body:
                    raise WorkflowEvidenceError("evidence_conflict")
                scope.written(key, f"{request.expected_cursor + 1:06d}.json", existing)
                return (
                    request.expected_cursor + 1,
                    _digest(existing),
                    "persisted",
                    "completed",
                )
            if (
                request.expected_cursor != snapshot.cursor
                or request.expected_previous_digest != snapshot.digest
                or snapshot.cursor >= MAX_WORKFLOW_RECORDS
            ):
                raise WorkflowEvidenceError("evidence_conflict")
            if snapshot.size_bytes + len(body) > MAX_WORKFLOW_ATTEMPT_BYTES:
                raise WorkflowEvidenceError("evidence_conflict")
            # Artifact bindings cannot silently replace a previously recorded artifact.
            known = {a.kind: a for r in snapshot.records for a in r.artifact_bindings}
            for artifact in request.artifact_bindings:
                if artifact.kind in known and repository_workflow_value_to_payload(
                    known[artifact.kind]
                ) != repository_workflow_value_to_payload(artifact):
                    raise WorkflowEvidenceError("evidence_conflict")
                known[artifact.kind] = artifact
            persistence, cleanup = _write(
                directory, f"{snapshot.cursor + 1:06d}.json", body
            )
            scope.cleanup = cleanup
            if persistence == "persisted":
                scope.written(key, f"{snapshot.cursor + 1:06d}.json", body)
            return snapshot.cursor + 1, _digest(body), persistence, cleanup
