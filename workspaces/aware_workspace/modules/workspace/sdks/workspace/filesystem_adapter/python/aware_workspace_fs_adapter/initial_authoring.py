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
from typing import Any
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


def _projection_stat(value):
    return [
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    ]


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
            allowed = (
                {_RECORD, "configuration", "project", "goal", "membership"}
                if _attempt
                else {_RECORD}
            )
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


def _projection_effect(effect):
    return {
        "path": effect.path,
        "kind": effect.kind,
        "state": effect.state.value,
        "durability_confirmed": effect.durability_confirmed,
        "mode": effect.mode,
        "before_digest": effect.before_digest,
        "after_digest": effect.after_digest,
        "after_identity": list(effect.after_identity)
        if effect.after_identity is not None
        else None,
    }


def reserve_configuration(
    port, claim, *, _project=False, _goal=False, _membership=False
):
    from aware_workspace_sdk.initial_authoring.authority import (
        _spend_configuration_reservation,
    )
    from aware_workspace_sdk.initial_authoring.values import initial_reference
    from aware_workspace_sdk.repository_publication.codec import (
        repository_publication_value_to_payload,
    )

    if sum((_goal, _project, _membership)) > 1:
        raise ValueError("initial_authoring_profiles_conflict")
    from aware_workspace_sdk.initial_authoring.goal_publication import (
        InitialGoalPublicationRequest,
        _spend_goal_reservation,
    )
    from aware_workspace_sdk.initial_authoring.membership import (
        InitialMembershipRequest,
        _spend_membership_reservation,
    )

    request, binding = (
        _spend_membership_reservation(port, claim)
        if _membership
        else _spend_goal_reservation(port, claim)
        if _goal
        else _spend_configuration_reservation(port, claim)
    )
    from aware_workspace_sdk.initial_authoring.values import (
        InitialConfigurationRequest,
        InitialProjectRequest,
    )

    if type(request) is not (
        InitialMembershipRequest
        if _membership
        else InitialGoalPublicationRequest
        if _goal
        else InitialProjectRequest
        if _project
        else InitialConfigurationRequest
    ):
        raise ValueError("initial_authoring_request_profile_mismatch")
    enrollment = observe(
        port, confirm_durability=True, _attempt=_project or _goal or _membership
    )
    if (
        enrollment.enrollment_ref != request.enrollment_ref
        or enrollment.execution_id != request.execution_id
    ):
        raise ValueError("initial_configuration_enrollment_mismatch")
    project_source = (
        request.source
        if isinstance(
            request,
            (
                InitialProjectRequest,
                InitialGoalPublicationRequest,
                InitialMembershipRequest,
            ),
        )
        else None
    )
    target = (
        project_source["target_path"]
        if project_source is not None
        else "aware.protocol.toml"
    )
    expected_head = (
        project_source["expected_head"] if project_source is not None else None
    )
    if project_source is not None:
        if _membership:
            port.verify_initial_membership_origin(request, current=True)
        elif _goal:
            port.verify_initial_goal_origin(request)
        else:
            _verify_project_origin(port, request)
        if (
            not _membership
            and project_preimage(port, target) != project_source["parent_preimages"]
        ):
            raise ValueError("initial_project_parents_changed")
    expected_preimage = {"path": target, "state": "absent"}
    if _membership:
        expected_preimage = port.initial_membership_preimage(project_source)
    if (
        port._head() != (binding.publication_reference, binding.expected_head)
        or binding.expected_head != expected_head
        or port._postimage(target) != expected_preimage
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
    if _membership and len(_canonical(record)) + 1 > 262144:
        raise ValueError("initial_membership_admission_retention_limit")
    with _root_and_metadata(port) as (_, metadata_fd, _, _):
        directory = os.open(_DIRECTORY, _DIR_FLAGS, dir_fd=metadata_fd)
        try:
            _private(os.fstat(directory), 0o700)
            name = (
                "membership"
                if _membership
                else "goal"
                if _goal
                else "project"
                if _project
                else "configuration"
            )
            os.mkdir(name, mode=0o700, dir_fd=directory)
            attempt = os.open(name, _DIR_FLAGS, dir_fd=directory)
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
                if (
                    port._head()
                    != (
                        binding.publication_reference,
                        binding.expected_head,
                    )
                    or port._postimage(target) != expected_preimage
                ):
                    raise ValueError("initial_configuration_admission_source_advanced")
                if _membership:
                    port.verify_initial_membership_origin(request, current=True)
            finally:
                os.close(attempt)
        finally:
            os.close(directory)
    return record


@contextmanager
def configuration_attempt(
    port, request, *, _project=False, _goal=False, _membership=False
):
    """One original-provider attempt lock spans dispatch through result retention.

    No process-local mutex is relabeled durable. Missing events remain unknown;
    this entrance never calls a writer or retries an interrupted attempt.
    """
    from aware_workspace_sdk.initial_authoring.goal_publication import (
        InitialGoalPublicationRequest,
    )
    from aware_workspace_sdk.initial_authoring.membership import (
        InitialMembershipRequest,
    )
    from aware_workspace_sdk.initial_authoring.values import (
        InitialConfigurationRequest,
        InitialProjectRequest,
        initial_reference,
    )
    from aware_workspace_sdk.repository_publication.codec import (
        repository_publication_value_from_payload,
    )
    from aware_workspace_sdk.repository_publication.values import (
        WorkspaceRepositoryPublicationBinding,
    )

    if sum((_goal, _project, _membership)) > 1:
        raise ValueError("initial_authoring_profiles_conflict")
    kind = (
        InitialMembershipRequest
        if _membership
        else InitialGoalPublicationRequest
        if _goal
        else InitialProjectRequest
        if _project
        else InitialConfigurationRequest
    )
    if type(request) is not kind:
        raise ValueError("initial_authoring_request_profile_mismatch")
    request.to_wire()
    if _project:
        _verify_project_origin(port, request)
    if _goal:
        port.verify_initial_goal_origin(request)
    if _membership:
        port.verify_initial_membership_origin(request)
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
            name = (
                "membership"
                if _membership
                else "goal"
                if _goal
                else "project"
                if _project
                else "configuration"
            )
            attempt = os.open(name, _DIR_FLAGS, dir_fd=directory)
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
            original = kind.from_wire(record["request"])
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
            config = (
                request.source
                if isinstance(
                    request,
                    (
                        InitialProjectRequest,
                        InitialGoalPublicationRequest,
                        InitialMembershipRequest,
                    ),
                )
                else request.to_wire()["configuration"]
            )
            if type(config) is not dict:
                raise ValueError("initial_authoring_source_shape_invalid")
            if (
                binding.repository_ref != config["repository_root"]
                or binding.expected_head
                != (
                    config["expected_head"]
                    if _project or _goal or _membership
                    else None
                )
                or binding.publication_reference != evidence.selected_ref
                or binding.target_paths
                != (
                    config["target_path"]
                    if _project or _goal or _membership
                    else "aware.protocol.toml",
                )
                or binding.execution_id != evidence.execution_id
                or binding.attempt_ref != request.request_ref
            ):
                raise ValueError("initial_admission_binding_invalid")
            names = set(os.listdir(attempt))
            if not names.issubset(
                {
                    "lock",
                    "admission.json",
                    "dispatch.json",
                    "result.json",
                    "projection-start.json",
                    "projection-result.json",
                }
                | ({"goal-intent.json"} if _project else set())
            ):
                raise ValueError("initial_attempt_unknown_event")
            if _membership:
                manager = port.initial_membership_attempt_manager(
                    attempt, record, directory
                )
            elif _goal:
                manager = port.initial_goal_attempt_manager(attempt, record, directory)
            else:
                manager = (ProjectAttempt if _project else ConfigurationAttempt)(
                    port, attempt, record, directory
                )
            yield manager
            if _identity(
                os.stat(name, dir_fd=directory, follow_symlinks=False)
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

    def _publication_source(self) -> tuple[str, bytes, str | None, str]:
        return (
            "aware.protocol.toml",
            self.record["request"]["configuration"]["content_utf8"].encode("utf-8"),
            None,
            "Initialize Project-capable Protocol configuration",
        )

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

    def _projection_source(self, result):
        """Exact present source; immutable publication is not currentness."""
        if (
            result.publication_state != "published"
            or not result.ledger_complete
            or result.admission_completion != "completed"
            or result.index_projection != "applied"
            or result.commit_hash is None
            or self.port._head() != ("refs/heads/main", result.commit_hash)
        ):
            raise ValueError("initial_projection_publication_not_current")
        content = self.record["request"]["configuration"]["content_utf8"].encode(
            "utf-8"
        )
        blob = self.port._git("hash-object", "--stdin", input=content)
        with _root_and_metadata(self.port) as (_, metadata_fd, _, _):
            before = os.stat("index", dir_fd=metadata_fd, follow_symlinks=False)
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                raise ValueError("initial_projection_regular_index_required")
            if self.port._git("ls-files", "--stage", "--", "aware.protocol.toml") != (
                f"100644 {blob} 0\taware.protocol.toml"
            ):
                raise ValueError("initial_projection_index_mismatch")
            after = os.stat("index", dir_fd=metadata_fd, follow_symlinks=False)
            if _projection_stat(before) != _projection_stat(after):
                raise ValueError("initial_projection_index_changed")
        if self.port._head() != ("refs/heads/main", result.commit_hash):
            raise ValueError("initial_projection_source_advanced")
        return content

    def _projection_file(self, content):
        """No-follow bounded reread, preserving original file identity."""
        import hashlib

        with _root_and_metadata(self.port) as (root_fd, _, _, _):
            descriptor = os.open(
                "aware.protocol.toml",
                os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=root_fd,
            )
            try:
                before = os.fstat(descriptor)
                if (
                    not stat.S_ISREG(before.st_mode)
                    or before.st_nlink != 1
                    or stat.S_IMODE(before.st_mode) != 0o644
                    or before.st_size != len(content)
                    or os.read(descriptor, len(content) + 1) != content
                ):
                    raise ValueError("initial_projection_file_mismatch")
                os.fsync(descriptor)
                os.fsync(root_fd)
                after = os.stat(
                    "aware.protocol.toml", dir_fd=root_fd, follow_symlinks=False
                )

                if _projection_stat(before) != _projection_stat(after):
                    raise ValueError("initial_projection_file_changed")
                return {
                    "stat": _projection_stat(after),
                    "sha256": "sha256:" + hashlib.sha256(content).hexdigest(),
                }
            finally:
                os.close(descriptor)

    def project_configuration(self, *, read_only=False):
        """Single original absent-file effect, never a second repository writer.

        The attempt lock serializes callers; the original FileSystem primitive
        provides cooperative descriptor-walk/no-replace semantics, not continuous
        hostile-writer exclusion. Durable intent precedes physical creation.
        An interrupted intent cannot mint another physical attempt after restart.
        """
        from aware_file_system.retained_bootstrap import (
            BootstrapFileCreation,
            retain_confined_bootstrap_creation,
        )
        from aware_workspace_sdk.initial_authoring.values import initial_reference
        from aware_workspace_sdk.repository_publication.values import (
            WorkspaceRepositoryCommitResult,
        )

        recovered = self.recover()
        if recovered["disposition"] != "recorded":
            raise ValueError("initial_projection_original_result_required")
        result = recovered["original_result"]
        publication = recovered.get("publication")
        if (
            type(result) is not WorkspaceRepositoryCommitResult
            or type(publication) is not dict
        ):
            raise ValueError("initial_projection_original_result_required")
        content = self._projection_source(result)
        intent = {
            "schema_id": "aware.workspace.initial-configuration-projection-intent.v1",
            "publication_ref": publication["publication_ref"],
            "request_ref": self.record["request"]["request_ref"],
            "commit": result.commit_hash,
            "target_path": "aware.protocol.toml",
            "preimage": "absent",
            "physical_profile": "descriptor_walk_v1",
        }
        names = set(os.listdir(self.directory))
        if "projection-start.json" in names:
            if _canonical(
                _read_record(self.directory, "projection-start.json")
            ) != _canonical(intent):
                raise ValueError("initial_projection_intent_mismatch")
            if "projection-result.json" not in names:
                return {
                    "projection_state": "uncertain",
                    "projection": None,
                    "diagnostics": (),
                }
            record = _read_record(self.directory, "projection-result.json")
            self._verify_projection(record, intent, content)
            # Confirm durability independently after a complete-looking interrupted
            # record. Reread again before reporting the retained original effect.
            for name in ("projection-start.json", "projection-result.json"):
                fd = os.open(
                    name,
                    os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
                    dir_fd=self.directory,
                )
                try:
                    _private(os.fstat(fd), 0o600)
                    os.fsync(fd)
                finally:
                    os.close(fd)
            os.fsync(self.directory)
            if _canonical(
                _read_record(self.directory, "projection-result.json")
            ) != _canonical(record):
                raise ValueError("initial_projection_record_changed")
            self._projection_source(result)
            return {
                "projection_state": "installed",
                "projection": record,
                "diagnostics": (),
            }
        if "projection-result.json" in names:
            raise ValueError("initial_projection_result_without_intent")
        if read_only:
            return {
                "projection_state": "not_started",
                "projection": None,
                "diagnostics": (),
            }
        with _root_and_metadata(self.port) as (root_fd, _, _, _):
            try:
                os.stat("aware.protocol.toml", dir_fd=root_fd, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                raise ValueError("initial_projection_foreign_target")
        handle = retain_confined_bootstrap_creation(
            root=self.port._root,
            files=(BootstrapFileCreation("aware.protocol.toml", content),),
            directory_paths=(),
        )
        try:
            # Recheck the original root after the physical owner pins its own
            # descriptors, before any worktree effect or durable projection intent.
            with _root_and_metadata(self.port):
                handle.validate_current()
                self._projection_source(result)
                _write_record(self.directory, "projection-start.json", intent)
                handle.create_next_file()
                effects = handle.finish()
                if len(effects) != 1:
                    raise ValueError("initial_projection_effect_inventory_invalid")
                effect = effects[0]
                file = self._projection_file(content)
                body = {
                    "schema_id": "aware.workspace.initial-configuration-projection.v1",
                    "intent": intent,
                    "file": file,
                    "effect": _projection_effect(effect),
                }
                record = {
                    **body,
                    "projection_ref": initial_reference(
                        "workspace-initial-configuration-projection", body
                    ),
                }
                self._verify_projection(record, intent, content)
                self._projection_source(result)
                _write_record(self.directory, "projection-result.json", record)
                self._verify_projection(
                    _read_record(self.directory, "projection-result.json"),
                    intent,
                    content,
                )
                self._projection_source(result)
            return {
                "projection_state": "installed",
                "projection": record,
                "diagnostics": (),
            }
        except (ValueError, OSError, RuntimeError) as error:
            # Keep the original physical owner's known partial effects. No final
            # record is inferred from an applied link or matching bytes; restart
            # sees the durable start and remains uncertain without retry.
            return {
                "projection_state": "uncertain",
                "projection": None,
                "projection_effects": tuple(
                    _projection_effect(effect) for effect in handle.observe_effects()
                ),
                "residual_scratch_paths": tuple(
                    getattr(error, "residual_scratch_paths", ())
                ),
                "diagnostics": (str(error),),
            }
        finally:
            handle.release()

    def _verify_projection(self, record, intent, content):
        self._verify_projection_history(record, intent, content)
        if _canonical(record["file"]) != _canonical(self._projection_file(content)):
            raise ValueError("initial_projection_record_mismatch")

    def _verify_projection_history(self, record, intent, content):
        """Original retained physical evidence, without claiming current source."""
        import hashlib

        from aware_workspace_sdk.initial_authoring.values import initial_reference

        if type(record) is not dict or set(record) != {
            "schema_id",
            "intent",
            "file",
            "effect",
            "projection_ref",
        }:
            raise ValueError("initial_projection_record_invalid")
        file = record["file"]
        if type(file) is not dict or set(file) != {"stat", "sha256"}:
            raise ValueError("initial_projection_record_invalid")
        values = file["stat"]
        if (
            type(values) is not list
            or len(values) != 7
            or any(type(value) is not int or value < 0 for value in values)
            or values[2] != stat.S_IFREG | 0o644
            or values[3] != 1
            or values[4] != len(content)
            or file["sha256"] != "sha256:" + hashlib.sha256(content).hexdigest()
        ):
            raise ValueError("initial_projection_record_invalid")
        expected_effect = {
            "path": "aware.protocol.toml",
            "kind": "file",
            "state": "applied",
            "durability_confirmed": True,
            "mode": 0o644,
            "before_digest": None,
            "after_digest": file["sha256"],
            "after_identity": file["stat"][:2],
        }
        body = {key: value for key, value in record.items() if key != "projection_ref"}
        if (
            record["schema_id"] != "aware.workspace.initial-configuration-projection.v1"
            or _canonical(record["intent"]) != _canonical(intent)
            or _canonical(record["effect"]) != _canonical(expected_effect)
            or record["projection_ref"]
            != initial_reference("workspace-initial-configuration-projection", body)
        ):
            raise ValueError("initial_projection_record_mismatch")

    def recover(self) -> dict[str, Any]:
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
        _, _, expected_head, _ = self._publication_source()
        if (
            result.binding_ref != binding["binding_ref"]
            or result.attempt_ref != binding["attempt_ref"]
            or result.work_admission_receipt_ref != self.receipt_ref
            or result.expected_head != expected_head
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
        target, content, expected_head, message = self._publication_source()
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
            or writer.requested_paths != [target]
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
                or effect.before_ref != expected_head
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
        if self.port._git("show", "-s", "--format=%P", commit) != (expected_head or ""):
            raise ValueError("initial_publication_parent_not_unborn")
        blob = self.port._git("hash-object", "--stdin", input=content)
        tree = (
            self.port._git("ls-tree", "-r", commit)
            if expected_head is None
            else self.port._git(
                "diff-tree", "--no-commit-id", "--name-only", "-z", "-r", commit
            )
        )
        if (expected_head is None and tree != f"100644 blob {blob}\t{target}") or (
            expected_head is not None
            and (
                tree != target + "\0"
                or self.port._git("ls-tree", "-z", commit, "--", target)
                != f"100644 blob {blob}\t{target}\0"
            )
        ):
            raise ValueError("initial_publication_tree_mismatch")
        expected_message = (
            message
            + "\n\n"
            + "Aware-Initial-Authoring: "
            + self.receipt_ref
            + "\n"
            + "Aware-Initial-Request: "
            + self.record["request"]["request_ref"]
            + "\n"
            + "Owner: "
            + binding["execution_id"]
            + "\n"
            + "Owned-Paths: "
            + target
        )
        if (
            self.port._git("show", "-s", "--format=%B", commit) != expected_message
            or writer.commit_message != expected_message
        ):
            raise ValueError("initial_publication_commit_binding_mismatch")
        if (
            binding["message_digest"]
            != "sha256:" + hashlib.sha256(message.encode("utf-8")).hexdigest()
        ):
            raise ValueError("initial_publication_message_binding_mismatch")


def reserve_project(port, claim):
    return reserve_configuration(port, claim, _project=True)


def project_attempt(port, request):
    return configuration_attempt(port, request, _project=True)


def project_preimage(port, target):
    """Complete no-follow parent census; no directories or files are created."""
    parts = target.split("/")
    if len(parts) > 65 or any(part in {"", ".", "..", ".git"} for part in parts):
        raise ValueError("initial_project_target_invalid")
    with _root_and_metadata(port) as (root_fd, _, _, _):
        opened = []
        directory = root_fd
        result = []
        try:
            for index, part in enumerate(parts[:-1]):
                path = "/".join(parts[: index + 1])
                try:
                    fd = os.open(part, _DIR_FLAGS, dir_fd=directory)
                except FileNotFoundError:
                    result.extend(
                        {"path": "/".join(parts[:i]), "state": "absent"}
                        for i in range(index + 1, len(parts))
                    )
                    return result
                opened.append(fd)
                value = os.fstat(fd)
                result.append(
                    {
                        "path": path,
                        "state": "directory",
                        "identity": list(_identity(value)),
                        "mode": stat.S_IMODE(value.st_mode),
                    }
                )
                directory = fd
            try:
                os.stat(parts[-1], dir_fd=directory, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                raise ValueError("initial_project_target_not_absent")
            return result
        finally:
            for descriptor in reversed(opened):
                os.close(descriptor)


def _verify_project_origin(port, request):
    """Original configuration permission at its own epoch, not a new grant."""
    from aware_workspace_sdk.initial_authoring.values import InitialConfigurationRequest

    source = request.source
    _project_location(source)
    config_request = InitialConfigurationRequest.from_wire(
        source["configuration_request"]
    )
    config = config_request.to_wire()["configuration"]
    if type(config) is not dict:
        raise ValueError("initial_project_configuration_invalid")
    if (
        source["repository_root"] != str(port._root)
        or source["manifest_sha256"] != config["source_sha256"]
    ):
        raise ValueError("initial_project_foreign_source")
    with configuration_attempt(port, config_request) as attempt:
        recovered = attempt.recover()
        if recovered["disposition"] != "recorded":
            raise ValueError("initial_project_configuration_unavailable")
        result = recovered["original_result"]
        if (
            result.publication_state != "published"
            or not result.ledger_complete
            or result.commit_hash != source["expected_head"]
            or recovered["publication"]["publication_ref"]
            != source["configuration_publication_ref"]
        ):
            raise ValueError("initial_project_configuration_binding_mismatch")
        intent = {
            "schema_id": "aware.workspace.initial-configuration-projection-intent.v1",
            "publication_ref": source["configuration_publication_ref"],
            "request_ref": config_request.request_ref,
            "commit": source["expected_head"],
            "target_path": "aware.protocol.toml",
            "preimage": "absent",
            "physical_profile": "descriptor_walk_v1",
        }
        if _canonical(
            _read_record(attempt.directory, "projection-start.json")
        ) != _canonical(intent):
            raise ValueError("initial_project_configuration_projection_mismatch")
        projection = _read_record(attempt.directory, "projection-result.json")
        # Historical permission is not current manifest/file authority. Live
        # construction/show separately require fresh Protocol/source intake.
        attempt._verify_projection_history(
            projection, intent, config["content_utf8"].encode("utf-8")
        )
        if projection["projection_ref"] != source["configuration_projection_ref"]:
            raise ValueError("initial_project_configuration_projection_mismatch")
        for name, expected in (
            ("projection-start.json", intent),
            ("projection-result.json", projection),
        ):
            fd = os.open(
                name,
                os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=attempt.directory,
            )
            try:
                _private(os.fstat(fd), 0o600)
                os.fsync(fd)
            finally:
                os.close(fd)
            if _canonical(_read_record(attempt.directory, name)) != _canonical(
                expected
            ):
                raise ValueError("initial_project_configuration_projection_changed")
        os.fsync(attempt.directory)
    return recovered


def _project_location(source):
    from aware_protocol_fs_adapter.project_templates import match_project_path
    from aware_workspace_sdk.initial_authoring.values import InitialConfigurationRequest

    config = InitialConfigurationRequest.from_wire(
        source["configuration_request"]
    ).to_wire()["configuration"]
    if type(config) is not dict:
        raise ValueError("initial_project_configuration_invalid")
    prefix = config["project_root"] + "/"
    if (
        not source["target_path"].startswith(prefix)
        or match_project_path(
            "project-<slug>.toml", source["target_path"][len(prefix) :]
        )
        is None
    ):
        raise ValueError("initial_project_target_outside_binding")


def qualify_project_source(port, source, capability, *, current=False):
    """Concrete scope only. No Project meaning or caller verdict is imported."""
    from aware_protocol_fs_adapter import require_project_resolver

    selected = require_project_resolver(capability)
    # The shared writer currently reports non-ASCII staged names in Git-quoted
    # form. Refuse before admission; do not install another writer or narrow
    # Protocol's broader read-location grammar.
    if not source["target_path"].isascii():
        raise ValueError("initial_project_writer_path_profile_unavailable")
    _project_location(source)
    if (
        selected.repository_root != port._root
        or str(port._root) != source["repository_root"]
        or selected.manifest_sha256 != source["manifest_sha256"]
    ):
        raise ValueError("initial_project_source_owner_mismatch")
    selected.resolve_project_path(source["target_path"])
    if (
        current
        and project_preimage(port, source["target_path"]) != source["parent_preimages"]
    ):
        raise ValueError("initial_project_parents_changed")
    selected.resolve_project_path(source["target_path"])
    if current and port._head() != ("refs/heads/main", source["expected_head"]):
        raise ValueError("initial_project_source_advanced")


class _InitialCreationProjection(ConfigurationAttempt):
    """One cooperative FileSystem creation projector, not another publisher.

    Concrete original attempts supply source bytes and a fixed receipt domain.
    No caller-selected projector or replacement policy is accepted.
    """

    _projection_kind = "project"

    def _publication_source(self) -> tuple[str, bytes, str | None, str]:
        raise NotImplementedError("original initial-creation source required")

    def _project_current(self, result):
        target, content, _, _ = self._publication_source()
        if (
            result.publication_state != "published"
            or not result.ledger_complete
            or result.admission_completion != "completed"
            or result.index_projection != "applied"
            or self.port._head() != ("refs/heads/main", result.commit_hash)
        ):
            raise ValueError("initial_project_projection_source_not_current")
        blob = self.port._git("hash-object", "--stdin", input=content)
        with _root_and_metadata(self.port) as (_, metadata_fd, _, _):
            before = os.stat("index", dir_fd=metadata_fd, follow_symlinks=False)
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                raise ValueError("initial_project_regular_index_required")
            if (
                self.port._git("ls-files", "--stage", "-z", "--", target)
                != f"100644 {blob} 0\t{target}\0"
            ):
                raise ValueError("initial_project_projection_index_mismatch")
            if _projection_stat(before) != _projection_stat(
                os.stat("index", dir_fd=metadata_fd, follow_symlinks=False)
            ):
                raise ValueError("initial_project_projection_index_changed")
        if self.port._head() != ("refs/heads/main", result.commit_hash):
            raise ValueError("initial_project_projection_head_advanced")
        return target, content

    def _project_target(self, content=None) -> dict[str, Any]:
        """Exact no-follow chain and file; missing directory census creates nothing."""
        import hashlib

        target = self._publication_source()[0]
        parts = target.split("/")
        with _root_and_metadata(self.port) as (root_fd, _, _, _):
            opened = []
            directory = root_fd
            parents = []
            try:
                for index, part in enumerate(parts[:-1]):
                    try:
                        fd = os.open(part, _DIR_FLAGS, dir_fd=directory)
                    except FileNotFoundError:
                        if content is not None:
                            raise
                        return {
                            "missing": [
                                "/".join(parts[:i])
                                for i in range(index + 1, len(parts))
                            ],
                            "file": None,
                        }
                    opened.append(fd)
                    observed = os.fstat(fd)
                    parents.append(
                        {
                            "path": "/".join(parts[: index + 1]),
                            "identity": list(_identity(observed)),
                            "mode": stat.S_IMODE(observed.st_mode),
                        }
                    )
                    directory = fd
                if content is None:
                    try:
                        os.stat(parts[-1], dir_fd=directory, follow_symlinks=False)
                    except FileNotFoundError:
                        return {"missing": [], "file": None}
                    raise ValueError("initial_project_foreign_projection_target")
                fd = os.open(
                    parts[-1],
                    os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                    dir_fd=directory,
                )
                opened.append(fd)
                observed = os.fstat(fd)
                if (
                    not stat.S_ISREG(observed.st_mode)
                    or observed.st_nlink != 1
                    or stat.S_IMODE(observed.st_mode) != 0o644
                    or observed.st_size != len(content)
                    or os.read(fd, len(content) + 1) != content
                ):
                    raise ValueError("initial_project_projection_file_mismatch")
                os.fsync(fd)
                for parent in opened[:-1]:
                    os.fsync(parent)
                os.fsync(root_fd)
                if _projection_stat(observed) != _projection_stat(
                    os.stat(parts[-1], dir_fd=directory, follow_symlinks=False)
                ):
                    raise ValueError("initial_project_projection_file_changed")
                # Check every opened directory is still the named child, not a
                # detached retained descriptor after an ancestor substitution.
                parent_fd = root_fd
                for part, retained in zip(parts[:-1], opened[:-1], strict=True):
                    if _identity(
                        os.stat(part, dir_fd=parent_fd, follow_symlinks=False)
                    ) != _identity(os.fstat(retained)):
                        raise ValueError("initial_project_projection_parent_changed")
                    parent_fd = retained
                return {
                    "parents": parents,
                    "file": {
                        "stat": _projection_stat(observed),
                        "sha256": "sha256:" + hashlib.sha256(content).hexdigest(),
                    },
                }
            finally:
                for descriptor in reversed(opened):
                    os.close(descriptor)

    def _verify_project_projection(self, record, intent, content):
        from aware_workspace_sdk.initial_authoring.values import initial_reference

        if type(record) is not dict or set(record) != {
            "schema_id",
            "intent",
            "target",
            "effects",
            "projection_ref",
        }:
            raise ValueError("initial_project_projection_record_invalid")
        observed = self._project_target(content)
        for before in self.record["request"]["source"]["parent_preimages"]:
            if before["state"] == "directory":
                current = next(
                    parent
                    for parent in observed["parents"]
                    if parent["path"] == before["path"]
                )
                if (
                    current["identity"] != before["identity"]
                    or current["mode"] != before["mode"]
                ):
                    raise ValueError("initial_project_projection_parent_substituted")
        body = {key: value for key, value in record.items() if key != "projection_ref"}
        # Creation effects retain the original 0700 mode. Check the physical
        # parent as well: a handoff mutation must not be adopted into `target`
        # while its unchanged creation effect still claims the original mode.
        # The canonical effect comparison below also binds each observed identity
        # to that original effect, both before retention and during recovery.
        for path in intent["directory_paths"]:
            current = next(
                parent for parent in observed["parents"] if parent["path"] == path
            )
            if current["mode"] != 0o700:
                raise ValueError("initial_project_projection_created_parent_mode_changed")
        expected_effects = [
            {
                "path": path,
                "kind": "directory",
                "state": "applied",
                "durability_confirmed": True,
                "mode": 0o700,
                "before_digest": None,
                "after_digest": None,
                "after_identity": next(
                    parent["identity"]
                    for parent in observed["parents"]
                    if parent["path"] == path
                ),
            }
            for path in intent["directory_paths"]
        ]
        expected_effects.append(
            {
                "path": intent["target_path"],
                "kind": "file",
                "state": "applied",
                "durability_confirmed": True,
                "mode": 0o644,
                "before_digest": None,
                "after_digest": observed["file"]["sha256"],
                "after_identity": observed["file"]["stat"][:2],
            }
        )
        if (
            record["schema_id"]
            != f"aware.workspace.initial-{self._projection_kind}-projection.v1"
            or _canonical(record["intent"]) != _canonical(intent)
            or _canonical(record["target"]) != _canonical(observed)
            or _canonical(record["effects"]) != _canonical(expected_effects)
            or record["projection_ref"]
            != initial_reference(
                f"workspace-initial-{self._projection_kind}-projection", body
            )
        ):
            raise ValueError("initial_project_projection_record_mismatch")

    def _project_creation(self, *, read_only=False):
        from aware_file_system.retained_bootstrap import (
            BootstrapFileCreation,
            retain_confined_bootstrap_creation,
        )
        from aware_workspace_sdk.initial_authoring.values import initial_reference

        recovered = self.recover()
        if recovered["disposition"] != "recorded":
            raise ValueError("initial_project_original_result_required")
        result = recovered["original_result"]
        target, content = self._project_current(result)
        names = set(os.listdir(self.directory))
        fixed = {
            "schema_id": f"aware.workspace.initial-{self._projection_kind}-projection-intent.v1",
            "publication_ref": recovered["publication"]["publication_ref"],
            "request_ref": self.record["request"]["request_ref"],
            "commit": result.commit_hash,
            "target_path": target,
            "preimage": "absent",
            "physical_profile": "descriptor_walk_v1",
        }
        if "projection-start.json" in names:
            intent = _read_record(self.directory, "projection-start.json")
            if (
                type(intent) is not dict
                or set(intent) != {*fixed, "directory_paths"}
                or _canonical(
                    {k: v for k, v in intent.items() if k != "directory_paths"}
                )
                != _canonical(fixed)
                or type(intent["directory_paths"]) is not list
                or any(type(path) is not str for path in intent["directory_paths"])
                or len(intent["directory_paths"]) > 64
            ):
                raise ValueError("initial_project_projection_intent_mismatch")
            expected_directories = [
                item["path"]
                for item in self.record["request"]["source"]["parent_preimages"]
                if item["state"] == "absent"
            ]
            if intent["directory_paths"] != expected_directories:
                raise ValueError(
                    "initial_project_projection_directory_inventory_invalid"
                )
            if "projection-result.json" not in names:
                return {
                    "projection_state": "uncertain",
                    "projection": None,
                    "diagnostics": (),
                }
            record = _read_record(self.directory, "projection-result.json")
            self._verify_project_projection(record, intent, content)
            for name in ("projection-start.json", "projection-result.json"):
                fd = os.open(
                    name,
                    os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
                    dir_fd=self.directory,
                )
                try:
                    _private(os.fstat(fd), 0o600)
                    os.fsync(fd)
                finally:
                    os.close(fd)
            os.fsync(self.directory)
            if _canonical(
                _read_record(self.directory, "projection-result.json")
            ) != _canonical(record):
                raise ValueError("initial_project_projection_record_changed")
            self._project_current(result)
            # A terminal source qualification must not hide a target/parent
            # change. Compare again against the ORIGINAL retained effects.
            self._verify_project_projection(record, intent, content)
            if _canonical(
                _read_record(self.directory, "projection-result.json")
            ) != _canonical(record) or _canonical(
                _read_record(self.directory, "projection-start.json")
            ) != _canonical(intent):
                raise ValueError("initial_project_projection_record_changed")
            return {
                "projection_state": "installed",
                "projection": record,
                "diagnostics": (),
            }
        if "projection-result.json" in names:
            raise ValueError("initial_project_projection_result_without_intent")
        if read_only:
            return {
                "projection_state": "not_started",
                "projection": None,
                "diagnostics": (),
            }
        if (
            project_preimage(self.port, target)
            != self.record["request"]["source"]["parent_preimages"]
        ):
            raise ValueError("initial_project_parents_changed")
        missing = self._project_target()["missing"]
        intent = {**fixed, "directory_paths": missing}
        handle = retain_confined_bootstrap_creation(
            root=self.port._root,
            files=(BootstrapFileCreation(target, content),),
            directory_paths=tuple(missing),
        )
        try:
            with _root_and_metadata(self.port):
                self._project_current(result)
                handle.validate_current()
                if (
                    project_preimage(self.port, target)
                    != self.record["request"]["source"]["parent_preimages"]
                ):
                    raise ValueError("initial_project_parents_changed")
                _write_record(self.directory, "projection-start.json", intent)
                for _ in missing:
                    handle.prepare_next_directory()
                handle.create_next_file()
                effects = handle.finish()
                body = {
                    "schema_id": f"aware.workspace.initial-{self._projection_kind}-projection.v1",
                    "intent": intent,
                    "target": self._project_target(content),
                    "effects": [_projection_effect(effect) for effect in effects],
                }
                record = {
                    **body,
                    "projection_ref": initial_reference(
                        f"workspace-initial-{self._projection_kind}-projection", body
                    ),
                }
                self._verify_project_projection(record, intent, content)
                self._project_current(result)
                self._verify_project_projection(record, intent, content)
                _write_record(self.directory, "projection-result.json", record)
                self._verify_project_projection(
                    _read_record(self.directory, "projection-result.json"),
                    intent,
                    content,
                )
                self._project_current(result)
                self._verify_project_projection(record, intent, content)
                if _canonical(
                    _read_record(self.directory, "projection-result.json")
                ) != _canonical(record) or _canonical(
                    _read_record(self.directory, "projection-start.json")
                ) != _canonical(intent):
                    raise ValueError("initial_project_projection_record_changed")
            return {
                "projection_state": "installed",
                "projection": record,
                "diagnostics": (),
            }
        except (ValueError, OSError, RuntimeError) as error:
            return {
                "projection_state": "uncertain",
                "projection": None,
                "projection_effects": tuple(
                    _projection_effect(effect) for effect in handle.observe_effects()
                ),
                "residual_scratch_paths": tuple(
                    getattr(error, "residual_scratch_paths", ())
                ),
                "diagnostics": (str(error),),
            }
        finally:
            handle.release()


class ProjectAttempt(_InitialCreationProjection):
    """Original Project profile; its receipt identities and bytes are unchanged."""

    def _publication_source(self):
        source = self.record["request"]["source"]
        return (
            source["target_path"],
            source["project_plan"]["content_utf8"].encode("utf-8"),
            source["expected_head"],
            "Create initial Project context",
        )

    def project_project(self, *, read_only=False):
        return self._project_creation(read_only=read_only)
