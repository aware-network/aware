"""Original Workspace local-policy enrollment and durable no-replace retention.

No Git writer, domain evaluator, Issue substitution, or caller-selected store.
The private metadata is trusted only under this explicitly limited same-local-UID
policy; it is not a signature or defense against an adversarial same-UID process.
Missing or damaged retention refuses. Preparation without completed enrollment
cannot be recovered by adopting an existing repository.
"""

from __future__ import annotations

import fcntl
import json
import os
import stat
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from aware_workspace_sdk.initial_authoring.values import (
    InitialAuthoringEnrollmentEvidence,
    _canonical,
    enrollment_evidence,
)

_DIRECTORY = "aware-initial-authoring-v1"
_RECORD = "enrollment.json"
_LIMIT = 16384
_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC


def require_configuration_source(plan):
    # This is the concrete selected-source integration, not a configurable
    # callback, another Protocol issuer, or a neutral-runtime FS dependency.
    import importlib

    original = importlib.import_module("aware_protocol_fs_adapter.project_bootstrap")
    return original.require_project_configuration(plan)


def _identity(value):
    return value.st_dev, value.st_ino


@contextmanager
def _root_and_metadata(port):
    descriptors = []
    try:
        fd = os.open("/", _DIR_FLAGS)
        descriptors.append(fd)
        opened = []
        path = type(port._root)("/")
        for part in port._root.parts[1:]:
            fd = os.open(part, _DIR_FLAGS, dir_fd=fd)
            descriptors.append(fd)
            path /= part
            opened.append((path, _identity(os.fstat(fd))))
        root_fd = fd
        if _identity(os.fstat(root_fd)) != port._identity:
            raise ValueError("initial_authoring_root_substituted")
        metadata_fd = os.open(".git", _DIR_FLAGS, dir_fd=root_fd)
        descriptors.append(metadata_fd)
        root = os.fstat(root_fd)
        metadata = os.fstat(metadata_fd)
        if root.st_uid != os.geteuid() or metadata.st_uid != os.geteuid():
            raise ValueError("initial_authoring_local_owner_required")
        if stat.S_IMODE(root.st_mode) & 0o022 or stat.S_IMODE(metadata.st_mode) & 0o022:
            raise ValueError("initial_authoring_owner_only_write_required")
        yield root_fd, metadata_fd, root, metadata
        for target, identity in opened:
            if (
                _identity(os.stat(target, follow_symlinks=False)) != identity
                or target.is_symlink()
            ):
                raise ValueError("initial_authoring_ancestor_substituted")
        if _identity(
            os.stat(".git", dir_fd=root_fd, follow_symlinks=False)
        ) != _identity(metadata):
            raise ValueError("initial_authoring_metadata_substituted")
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _empty_original(port, root_fd, *, enrolled):
    # Census is current selected-repository scope, not all-history/global origin.
    if os.listdir(root_fd) != [".git"]:
        raise ValueError("initial_authoring_fresh_worktree_required")
    # Check metadata before asking Git to interpret an index or config. No
    # arbitrary staged inventory is read to establish the absence of an index.
    with _root_and_metadata(port) as (_, metadata_fd, _, _):
        names = set(os.listdir(metadata_fd))
        if "index" in names or (not enrolled and _DIRECTORY in names):
            raise ValueError("initial_authoring_foreign_metadata_effect")
        for name, limit in (("HEAD", 4096), ("config", 16384)):
            value = os.stat(name, dir_fd=metadata_fd, follow_symlinks=False)
            if (
                not stat.S_ISREG(value.st_mode)
                or value.st_nlink != 1
                or value.st_size > limit
            ):
                raise ValueError("initial_authoring_bounded_git_metadata_required")
    if port._head() != ("refs/heads/main", None):
        raise ValueError("initial_authoring_unborn_main_required")
    if port._git("for-each-ref", "--count=1", "--format=%(refname)") or port._git(
        "ls-files", "--stage"
    ):
        raise ValueError("initial_authoring_empty_refs_and_index_required")
    if port._git("remote"):
        raise ValueError("initial_authoring_remote_adoption_refused")
    # Original preparation creates no index; an empty but foreign index is not
    # silently adopted. Enrollment's own retention is the only permitted addition.
    with _root_and_metadata(port) as (_, metadata_fd, _, _):
        names = set(os.listdir(metadata_fd))
        if "index" in names or (not enrolled and _DIRECTORY in names):
            raise ValueError("initial_authoring_foreign_metadata_effect")


def _private(value, mode):
    if (
        value.st_uid != os.geteuid()
        or stat.S_IMODE(value.st_mode) != mode
        or (mode == 0o600 and (not stat.S_ISREG(value.st_mode) or value.st_nlink != 1))
        or (mode == 0o700 and not stat.S_ISDIR(value.st_mode))
    ):
        raise ValueError("initial_authoring_private_retention_required")


def _directory_current(metadata_fd, directory):
    current = os.stat(_DIRECTORY, dir_fd=metadata_fd, follow_symlinks=False)
    _private(current, 0o700)
    if _identity(current) != _identity(os.fstat(directory)):
        raise ValueError("initial_authoring_retention_directory_changed")


def enroll(port, claim):
    from aware_workspace_sdk.initial_authoring.authority import _spend_enrollment_claim

    witness, execution_id, issuer_ref, issuer_generation = _spend_enrollment_claim(
        port, claim
    )
    if (
        witness.outcome != "created"
        or witness.request.dry_run
        or witness.repository_root != str(port._root)
        or witness.execution_id != execution_id
        or witness.cleanup_state != "completed"
        or not witness.ledger_complete
    ):
        raise ValueError("initial_authoring_original_creation_required")
    effects = [
        item for item in witness.effects if item.kind == "git_repository_initialization"
    ]
    if len(effects) != 1 or effects[0].state != "applied":
        raise ValueError("initial_authoring_original_git_effect_required")
    with _root_and_metadata(port) as (root_fd, metadata_fd, root, metadata):
        if (effects[0].path, effects[0].after_device, effects[0].after_inode) != (
            str(port._root / ".git"),
            metadata.st_dev,
            metadata.st_ino,
        ):
            raise ValueError("initial_authoring_creation_identity_mismatch")
        _empty_original(port, root_fd, enrolled=False)
        evidence = enrollment_evidence(
            enrollment_id=uuid4().hex,
            repository_root=str(port._root),
            root_device=root.st_dev,
            root_inode=root.st_ino,
            metadata_device=metadata.st_dev,
            metadata_inode=metadata.st_ino,
            local_uid=os.geteuid(),
            execution_id=execution_id,
            preparation_attempt_ref=witness.attempt_ref,
            selected_ref="refs/heads/main",
            issuer_ref=issuer_ref,
            issuer_generation=issuer_generation,
            assurance="local_fresh_repository_execution_correlation",
        )
        # No replacement or cleanup-on-error: a partial artifact remains visible
        # and blocks reenrollment. Never delete it and repeat the original effect.
        os.mkdir(_DIRECTORY, mode=0o700, dir_fd=metadata_fd)
        directory = os.open(_DIRECTORY, _DIR_FLAGS, dir_fd=metadata_fd)
        try:
            _private(os.fstat(directory), 0o700)
            os.fsync(metadata_fd)
            descriptor = os.open(
                _RECORD,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                0o600,
                dir_fd=directory,
            )
            try:
                _private(os.fstat(descriptor), 0o600)
                body = _canonical(evidence.to_wire()) + b"\n"
                offset = 0
                while offset < len(body):
                    count = os.write(descriptor, body[offset:])
                    if count <= 0:
                        raise OSError("initial_authoring_short_write")
                    offset += count
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            os.fsync(directory)
            os.fsync(metadata_fd)
            os.fsync(root_fd)
            _directory_current(metadata_fd, directory)
        finally:
            os.close(directory)
        # Reread independently before exposing any enrollment handle.
        if observe(port, confirm_durability=True) != evidence:
            raise ValueError("initial_authoring_retention_reread_mismatch")
        return evidence


def observe(port, *, confirm_durability=False, _attempt=False):
    with _root_and_metadata(port) as (root_fd, metadata_fd, root, metadata):
        if not _attempt:
            _empty_original(port, root_fd, enrolled=True)
        directory = os.open(_DIRECTORY, _DIR_FLAGS, dir_fd=metadata_fd)
        try:
            _private(os.fstat(directory), 0o700)
            allowed = {_RECORD, "configuration"} if _attempt else {_RECORD}
            if not set(os.listdir(directory)).issubset(
                allowed
            ) or _RECORD not in os.listdir(directory):
                raise ValueError("initial_authoring_retention_incomplete")
            descriptor = os.open(
                _RECORD,
                os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=directory,
            )
            try:
                before = os.fstat(descriptor)
                _private(before, 0o600)
                if before.st_size > _LIMIT:
                    raise ValueError("initial_authoring_retention_limit")
                body = os.read(descriptor, _LIMIT + 1)
                if len(body) > _LIMIT:
                    raise ValueError("initial_authoring_retention_limit")
                evidence = InitialAuthoringEnrollmentEvidence.from_wire(
                    json.loads(body)
                )
                if body != _canonical(evidence.to_wire()) + b"\n":
                    raise ValueError("initial_authoring_retention_noncanonical")
                current = os.stat(_RECORD, dir_fd=directory, follow_symlinks=False)
                if (
                    before.st_dev,
                    before.st_ino,
                    before.st_size,
                    before.st_mtime_ns,
                    before.st_ctime_ns,
                ) != (
                    current.st_dev,
                    current.st_ino,
                    current.st_size,
                    current.st_mtime_ns,
                    current.st_ctime_ns,
                ):
                    raise ValueError("initial_authoring_retention_changed")
                if confirm_durability:
                    os.fsync(descriptor)
                    os.fsync(directory)
                    os.fsync(metadata_fd)
                    os.fsync(root_fd)
            finally:
                os.close(descriptor)
            if (
                evidence.repository_root,
                evidence.root_device,
                evidence.root_inode,
                evidence.metadata_device,
                evidence.metadata_inode,
                evidence.local_uid,
            ) != (
                str(port._root),
                root.st_dev,
                root.st_ino,
                metadata.st_dev,
                metadata.st_ino,
                os.geteuid(),
            ):
                raise ValueError("initial_authoring_retention_repository_mismatch")
            if not _attempt:
                _empty_original(port, root_fd, enrolled=True)
            _directory_current(metadata_fd, directory)
            return evidence
        finally:
            os.close(directory)


def _write_record(directory, name, value):
    """Durable immutable attempt event; interruption cannot erase an event."""
    descriptor = os.open(
        name,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
        0o600,
        dir_fd=directory,
    )
    try:
        _private(os.fstat(descriptor), 0o600)
        body = _canonical(value) + b"\n"
        offset = 0
        while offset < len(body):
            count = os.write(descriptor, body[offset:])
            if count <= 0:
                raise OSError("initial_attempt_short_write")
            offset += count
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.fsync(directory)
    if _read_record(directory, name) != value:
        raise ValueError("initial_attempt_independent_reread_failed")


def _read_record(directory, name):
    descriptor = os.open(
        name,
        os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
        dir_fd=directory,
    )
    try:
        before = os.fstat(descriptor)
        _private(before, 0o600)
        if before.st_size > 262144:
            raise ValueError("initial_attempt_record_limit")
        body = os.read(descriptor, 262145)
        value = json.loads(body)
        if len(body) > 262144 or body != _canonical(value) + b"\n":
            raise ValueError("initial_attempt_record_noncanonical")
        after = os.stat(name, dir_fd=directory, follow_symlinks=False)
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise ValueError("initial_attempt_record_changed")
        return value
    finally:
        os.close(descriptor)


def reserve_configuration(port, claim):
    from aware_workspace_sdk.initial_authoring.authority import (
        _spend_configuration_reservation,
    )
    from aware_workspace_sdk.initial_authoring.values import initial_reference
    from aware_workspace_sdk.repository_publication.codec import (
        repository_publication_value_to_payload,
    )

    request, binding = _spend_configuration_reservation(port, claim)
    enrollment = observe(port, confirm_durability=True)
    if (
        enrollment.enrollment_ref != request.enrollment_ref
        or enrollment.execution_id != request.execution_id
    ):
        raise ValueError("initial_configuration_enrollment_mismatch")
    if (
        port._head() != (binding.publication_reference, binding.expected_head)
        or binding.expected_head is not None
        or port._postimage("aware.protocol.toml")
        != {"path": "aware.protocol.toml", "state": "absent"}
    ):
        raise ValueError("initial_configuration_admission_source_stale")
    body = {
        "schema_id": "aware.workspace.initial-authoring-admission.v1",
        "request": request.to_wire(),
        "binding": repository_publication_value_to_payload(binding),
    }
    issued = datetime.now(UTC)
    body["issued_at"] = issued.isoformat(timespec="microseconds")
    body["expires_at"] = (issued + timedelta(seconds=300)).isoformat(
        timespec="microseconds"
    )
    record = {
        **body,
        "admission_ref": initial_reference("workspace-initial-admission", body),
    }
    with _root_and_metadata(port) as (_, metadata_fd, _, _):
        directory = os.open(_DIRECTORY, _DIR_FLAGS, dir_fd=metadata_fd)
        try:
            _private(os.fstat(directory), 0o700)
            os.mkdir("configuration", mode=0o700, dir_fd=directory)
            attempt = os.open("configuration", _DIR_FLAGS, dir_fd=directory)
            try:
                _private(os.fstat(attempt), 0o700)
                lock = os.open(
                    "lock",
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                    0o600,
                    dir_fd=attempt,
                )
                try:
                    os.fsync(lock)
                finally:
                    os.close(lock)
                _write_record(attempt, "admission.json", record)
                os.fsync(directory)
                os.fsync(metadata_fd)
                _directory_current(metadata_fd, directory)
                if port._head() != (
                    binding.publication_reference,
                    binding.expected_head,
                ) or port._postimage("aware.protocol.toml") != {
                    "path": "aware.protocol.toml",
                    "state": "absent",
                }:
                    raise ValueError("initial_configuration_admission_source_advanced")
            finally:
                os.close(attempt)
        finally:
            os.close(directory)
    return record


@contextmanager
def configuration_attempt(port, request):
    """One original-provider attempt lock spans dispatch through result retention.

    No process-local mutex is relabeled durable. Missing events remain unknown;
    this entrance never calls a writer or retries an interrupted attempt.
    """
    from aware_workspace_sdk.initial_authoring.values import (
        InitialConfigurationRequest,
        initial_reference,
    )
    from aware_workspace_sdk.repository_publication.codec import (
        repository_publication_value_from_payload,
    )
    from aware_workspace_sdk.repository_publication.values import (
        WorkspaceRepositoryPublicationBinding,
    )

    evidence = observe(port, _attempt=True)
    if (
        evidence.enrollment_ref != request.enrollment_ref
        or evidence.execution_id != request.execution_id
    ):
        raise ValueError("initial_attempt_enrollment_mismatch")
    with _root_and_metadata(port) as (_, metadata_fd, _, _):
        directory = os.open(_DIRECTORY, _DIR_FLAGS, dir_fd=metadata_fd)
        attempt = lock = None
        try:
            _private(os.fstat(directory), 0o700)
            attempt = os.open("configuration", _DIR_FLAGS, dir_fd=directory)
            _private(os.fstat(attempt), 0o700)
            lock = os.open(
                "lock",
                os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                dir_fd=attempt,
            )
            _private(os.fstat(lock), 0o600)
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise ValueError("initial_configuration_attempt_busy") from error
            record = _read_record(attempt, "admission.json")
            if type(record) is not dict or set(record) != {
                "schema_id",
                "request",
                "binding",
                "admission_ref",
                "issued_at",
                "expires_at",
            }:
                raise ValueError("initial_admission_record_invalid")
            if (
                type(record["issued_at"]) is not str
                or type(record["expires_at"]) is not str
            ):
                raise ValueError("initial_admission_times_invalid")
            issued = datetime.fromisoformat(record["issued_at"])
            expires = datetime.fromisoformat(record["expires_at"])
            if (
                issued.utcoffset() != timedelta(0)
                or expires.utcoffset() != timedelta(0)
                or expires - issued != timedelta(seconds=300)
                or issued.isoformat(timespec="microseconds") != record["issued_at"]
                or expires.isoformat(timespec="microseconds") != record["expires_at"]
            ):
                raise ValueError("initial_admission_times_invalid")
            original = InitialConfigurationRequest.from_wire(record["request"])
            body = {
                key: value for key, value in record.items() if key != "admission_ref"
            }
            if (
                record["schema_id"] != "aware.workspace.initial-authoring-admission.v1"
                or original != request
                or record["admission_ref"]
                != initial_reference("workspace-initial-admission", body)
            ):
                raise ValueError("initial_admission_record_mismatch")
            binding = repository_publication_value_from_payload(
                WorkspaceRepositoryPublicationBinding, record["binding"]
            )
            config = request.to_wire()["configuration"]
            if (
                binding.repository_ref != config["repository_root"]
                or binding.expected_head is not None
                or binding.publication_reference != evidence.selected_ref
                or binding.target_paths != ("aware.protocol.toml",)
                or binding.execution_id != evidence.execution_id
                or binding.attempt_ref != request.request_ref
            ):
                raise ValueError("initial_admission_binding_invalid")
            names = set(os.listdir(attempt))
            if not names.issubset(
                {"lock", "admission.json", "dispatch.json", "result.json"}
            ):
                raise ValueError("initial_attempt_unknown_event")
            manager = ConfigurationAttempt(port, attempt, record, directory)
            yield manager
            if _identity(
                os.stat("configuration", dir_fd=directory, follow_symlinks=False)
            ) != _identity(os.fstat(attempt)):
                raise ValueError("initial_attempt_directory_substituted")
            if _identity(
                os.stat("lock", dir_fd=attempt, follow_symlinks=False)
            ) != _identity(os.fstat(lock)):
                raise ValueError("initial_attempt_lock_substituted")
            _directory_current(metadata_fd, directory)
        finally:
            if lock is not None:
                os.close(lock)
            if attempt is not None:
                os.close(attempt)
            os.close(directory)


class ConfigurationAttempt:
    def __init__(self, port, directory, record, parent_directory):
        self.port, self.directory, self.record = port, directory, record
        self.parent_directory = parent_directory
        self.receipt_ref = record["admission_ref"]

    def consume(self):
        record = {
            "schema_id": "aware.workspace.initial-authoring-dispatch.v1",
            "admission_ref": self.receipt_ref,
            "request_ref": self.record["request"]["request_ref"],
        }
        _write_record(self.directory, "dispatch.json", record)
        return self

    def finish(self, result):
        from dataclasses import replace

        from aware_workspace_sdk.initial_authoring.values import initial_reference
        from aware_workspace_sdk.repository_publication.codec import (
            repository_publication_value_to_payload,
        )

        result = replace(
            result,
            admission_completion="completed" if result.ledger_complete else "unknown",
        )
        body = {
            "schema_id": "aware.workspace.initial-authoring-publication.v1",
            "admission_ref": self.receipt_ref,
            "request_ref": self.record["request"]["request_ref"],
            "original_result": repository_publication_value_to_payload(result),
        }
        _write_record(
            self.directory,
            "result.json",
            {
                **body,
                "publication_ref": initial_reference(
                    "workspace-initial-publication", body
                ),
            },
        )
        return result

    def recover(self):
        from aware_workspace_sdk.initial_authoring.values import initial_reference
        from aware_workspace_sdk.repository_publication.codec import (
            repository_publication_value_from_payload,
        )
        from aware_workspace_sdk.repository_publication.values import (
            WorkspaceRepositoryCommitResult,
        )

        names = set(os.listdir(self.directory))
        dispatch = None
        if "dispatch.json" in names:
            dispatch = _read_record(self.directory, "dispatch.json")
            if dispatch != {
                "schema_id": "aware.workspace.initial-authoring-dispatch.v1",
                "admission_ref": self.receipt_ref,
                "request_ref": self.record["request"]["request_ref"],
            }:
                raise ValueError("initial_dispatch_record_invalid")
        if "result.json" not in names:
            # Absence does not prove no CAS or terminal prevention. In particular
            # a Git child may outlive the parent. Never redispatch from this view.
            return {
                "disposition": "uncertain" if "dispatch.json" in names else "pending",
                "admission_ref": self.receipt_ref,
                "original_result": None,
                "authorizes_redispatch": False,
            }
        if dispatch is None:
            raise ValueError("initial_result_without_dispatch")
        record = _read_record(self.directory, "result.json")
        if type(record) is not dict or set(record) != {
            "schema_id",
            "admission_ref",
            "request_ref",
            "original_result",
            "publication_ref",
        }:
            raise ValueError("initial_publication_record_invalid")
        body = {key: value for key, value in record.items() if key != "publication_ref"}
        if (
            record["schema_id"] != "aware.workspace.initial-authoring-publication.v1"
            or record["admission_ref"] != self.receipt_ref
            or record["request_ref"] != self.record["request"]["request_ref"]
            or record["publication_ref"]
            != initial_reference("workspace-initial-publication", body)
        ):
            raise ValueError("initial_publication_record_mismatch")
        result = repository_publication_value_from_payload(
            WorkspaceRepositoryCommitResult, record["original_result"]
        )
        binding = self.record["binding"]
        if (
            result.binding_ref != binding["binding_ref"]
            or result.attempt_ref != binding["attempt_ref"]
            or result.work_admission_receipt_ref != self.receipt_ref
            or result.expected_head is not None
        ):
            raise ValueError("initial_publication_result_binding_invalid")
        self._verify_original_result(result)
        # A complete event may survive a crash before its fsync returned. The
        # original recovery owner must confirm durability independently before
        # reporting a recorded result; complete-looking bytes are not a barrier.
        for name, expected in (
            ("admission.json", self.record),
            ("dispatch.json", dispatch),
            ("result.json", record),
        ):
            descriptor = os.open(
                name,
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                dir_fd=self.directory,
            )
            try:
                _private(os.fstat(descriptor), 0o600)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            if _canonical(_read_record(self.directory, name)) != _canonical(expected):
                raise ValueError("initial_recovery_terminal_reread_failed")
        os.fsync(self.directory)
        os.fsync(self.parent_directory)
        return {
            "disposition": "recorded",
            "publication": record,
            "original_result": result,
            "authorizes_redispatch": False,
        }

    def _verify_original_result(self, result):
        """Historical original receipt verification, not new currentness issuance."""
        import hashlib

        writer = result.original_writer_report
        binding = self.record["binding"]
        lock = result.lock_release
        if lock is None or (
            lock.binding_ref,
            lock.attempt_ref,
            lock.provider_ref,
            lock.provider_generation,
        ) != (
            binding["binding_ref"],
            binding["attempt_ref"],
            binding["provider_ref"],
            binding["provider_generation"],
        ):
            raise ValueError("initial_publication_lock_binding_mismatch")
        if result.admission_completion != (
            "completed" if result.ledger_complete else "unknown"
        ) or (
            result.ledger_complete
            and (
                result.cleanup_state != "completed"
                or lock.repository_lock_release != "confirmed_released"
            )
        ):
            raise ValueError("initial_publication_completion_inconsistent")
        if writer is not None and (
            writer.repository_admission_ref != self.receipt_ref
            or writer.requested_paths != ["aware.protocol.toml"]
            or writer.owner_id != binding["execution_id"]
            or writer.issue_tag is not None
            or writer.commit_hash != result.commit_hash
            or writer.candidate_commit != result.candidate_commit
            or writer.reference_update != result.reference_update
            or writer.shared_index_projection != result.index_projection
            or writer.expected_head != result.expected_head
            or writer.updated_reference != result.updated_reference
            or writer.transaction_mode != result.transaction_mode
            or writer.repo_root != binding["repository_ref"]
        ):
            raise ValueError("initial_original_writer_result_mismatch")
        if (writer is not None and writer.reference_update == "cas_applied") != (
            result.publication_state == "published"
        ):
            raise ValueError("initial_publication_state_inconsistent")
        kinds = [effect.kind for effect in result.effects]
        if len(kinds) != len(set(kinds)) or any(
            kind not in {"repository_reference_update", "shared_index_projection"}
            for kind in kinds
        ):
            raise ValueError("initial_publication_effect_inventory_invalid")
        for effect in result.effects:
            if effect.kind == "repository_reference_update" and (
                effect.subject_ref != binding["publication_reference"]
                or effect.before_ref is not None
                or effect.after_ref
                != (
                    result.commit_hash
                    if result.publication_state == "published"
                    else None
                )
            ):
                raise ValueError("initial_publication_reference_effect_mismatch")
            if effect.kind == "shared_index_projection" and (
                effect.subject_ref != binding["repository_ref"]
                or effect.state != result.index_projection
            ):
                raise ValueError("initial_publication_index_effect_mismatch")
        if result.publication_state != "published":
            return
        if (
            "repository_reference_update" not in kinds
            or next(
                effect
                for effect in result.effects
                if effect.kind == "repository_reference_update"
            ).state
            != "applied"
        ):
            raise ValueError("initial_publication_reference_effect_missing")
        commit = result.commit_hash
        if (
            writer is None
            or commit is None
            or result.reference_update != "cas_applied"
            or result.candidate_commit != commit
            or result.updated_reference != "refs/heads/main"
        ):
            raise ValueError("initial_publication_result_contradiction")
        config = self.record["request"]["configuration"]
        content = config["content_utf8"].encode("utf-8")
        if self.port._git("show", "-s", "--format=%P", commit) != "":
            raise ValueError("initial_publication_parent_not_unborn")
        blob = self.port._git("hash-object", "--stdin", input=content)
        tree = self.port._git("ls-tree", "-r", commit)
        if tree != f"100644 blob {blob}\taware.protocol.toml":
            raise ValueError("initial_publication_tree_mismatch")
        expected_message = (
            "Initialize Project-capable Protocol configuration\n\n"
            + "Aware-Initial-Authoring: "
            + self.receipt_ref
            + "\n"
            + "Aware-Initial-Request: "
            + self.record["request"]["request_ref"]
            + "\n"
            + "Owner: "
            + binding["execution_id"]
            + "\n"
            + "Owned-Paths: aware.protocol.toml"
        )
        if (
            self.port._git("show", "-s", "--format=%B", commit) != expected_message
            or writer.commit_message != expected_message
        ):
            raise ValueError("initial_publication_commit_binding_mismatch")
        if (
            binding["message_digest"]
            != "sha256:"
            + hashlib.sha256(
                b"Initialize Project-capable Protocol configuration"
            ).hexdigest()
        ):
            raise ValueError("initial_publication_message_binding_mismatch")
