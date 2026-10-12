"""Original profile planning and bounded evidence; no source/publication authority."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import threading
import uuid
import weakref
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Literal, cast

from aware_workspace_sdk.repository_workflow import (
    WorkspaceRepositoryWorkflowAttempt,
    WorkspaceRepositoryWorkflowPlan,
    WorkspaceRepositoryWorkflowRefusal,
)
from aware_workspace_sdk.repository_workflow_codec import (
    WorkspaceWorkflowValueError,
    repository_workflow_value_from_payload,
    repository_workflow_value_to_payload,
)
from aware_workspace_sdk.repository_workflow_values import (
    WorkflowStage,
    WorkspaceRepositoryWorkflowAttemptObservation,
    WorkspaceRepositoryWorkflowAttemptObserveRequest,
    WorkspaceRepositoryWorkflowCleanupObservation,
    WorkspaceRepositoryWorkflowEvidenceAppendRequest,
    WorkspaceRepositoryWorkflowEvidenceWriteObservation,
    WorkspaceRepositoryWorkflowPlanObservation,
    WorkspaceRepositoryWorkflowRequest,
    WorkspaceRepositoryWorkflowStageObservation,
)
from packaging.markers import default_environment

from .package_checkout import PackageSourceCheckout

_CHECKOUT_CLASS = PackageSourceCheckout
_CHECKOUT_METHODS: tuple[tuple[str, Callable[..., Any]], ...] = tuple(
    (name, vars(_CHECKOUT_CLASS)[name])
    for name in (
        "__init__",
        "resolve",
        "revalidate",
        "close",
    )
)
_STAGES: tuple[WorkflowStage, ...] = (
    "source_capture",
    "qualification",
    "envelope",
    "tree_projection",
    "local_publication",
    "selection_freeze",
    "remote_delivery",
    "acquisition",
    "evidence_closeout",
)


def _digest(body: bytes) -> str:
    return "sha256:" + hashlib.sha256(body).hexdigest()


def _wire(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode()


def _execution() -> str:
    values = [
        (provider, (os.environ.get(key) or "").strip())
        for provider, key in (
            ("codex", "CODEX_THREAD_ID"),
            ("claude_code", "CLAUDE_CODE_SESSION_ID"),
        )
    ]
    values = [(provider, value) for provider, value in values if value]
    if len(values) != 1 or any(c.isspace() for c in values[0][1]):
        raise WorkspaceRepositoryWorkflowRefusal("malformed_binding")
    return values[0][0] + "-" + values[0][1]


def _root(value: Path, *, existing: bool) -> Path:
    if type(value) is not type(Path()) or not value.is_absolute():
        raise WorkspaceRepositoryWorkflowRefusal("malformed_binding")
    if value.resolve() != value or (existing and not value.is_dir()):
        raise WorkspaceRepositoryWorkflowRefusal("malformed_binding")
    return value


def _identity(root: Path) -> tuple[int, int]:
    value = root.stat()
    return value.st_dev, value.st_ino


def _git(root: Path, *arguments: str) -> bytes:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *arguments],
            capture_output=True,
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GIT_LITERAL_PATHSPECS": "1"},
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as error:
        # Ordinary read failures remain typed; interruptions propagate unchanged.
        diagnostic = (
            "git_read_timeout"
            if isinstance(error, subprocess.TimeoutExpired)
            else "git_read_os_error"
            if isinstance(error, OSError)
            else "git_read_subprocess_error"
        )
        raise WorkspaceRepositoryWorkflowRefusal(
            "source_unavailable", diagnostics=(diagnostic,)
        ) from error
    if result.returncode:
        raise WorkspaceRepositoryWorkflowRefusal("source_unavailable")
    return result.stdout


def _head(root: Path, reference: str) -> str | None:
    if _git(root, "symbolic-ref", "HEAD").decode().strip() != reference:
        raise WorkspaceRepositoryWorkflowRefusal("stale_target")
    refs = _git(root, "for-each-ref", "--format=%(refname) %(objectname)", reference)
    matches = [
        line.split()[1]
        for line in refs.decode().splitlines()
        if line.split()[0] == reference
    ]
    return matches[0] if matches else None


@dataclass(slots=True)
class _PlanRecord:
    request: WorkspaceRepositoryWorkflowRequest | None
    observation: WorkspaceRepositoryWorkflowPlanObservation | None
    retired: bool = False


@dataclass(slots=True)
class _AttemptRecord:
    plan: WorkspaceRepositoryWorkflowPlanObservation | None
    attempt_ref: str
    status: Literal["active", "held", "released"] = "active"


class WorkspaceRepositoryWorkflowRuntime:
    def __init__(
        self,
        *,
        source_repository_root: Path,
        target_repository_root: Path,
        state_root: Path,
        execution_id: str,
    ) -> None:
        self.source = _root(source_repository_root, existing=True)
        self.target = _root(target_repository_root, existing=True)
        self.state_root = _root(state_root, existing=False)
        if any(
            self.state_root.is_relative_to(root) for root in (self.source, self.target)
        ):
            raise WorkspaceRepositoryWorkflowRefusal("malformed_binding")
        if type(execution_id) is not str or execution_id != _execution():
            raise WorkspaceRepositoryWorkflowRefusal("malformed_binding")
        self.execution_id = execution_id
        self.pid, self.thread = os.getpid(), threading.get_ident()
        self.source_identity, self.target_identity = (
            _identity(self.source),
            _identity(self.target),
        )
        for root in (self.source, self.target):
            if _git(root, "rev-parse", "--show-toplevel").decode().strip() != str(root):
                raise WorkspaceRepositoryWorkflowRefusal("malformed_binding")
        self.generation = str(uuid.uuid4())
        self._plans: list[
            tuple[weakref.ReferenceType[WorkspaceRepositoryWorkflowPlan], _PlanRecord]
        ] = []
        self._attempts: list[
            tuple[
                weakref.ReferenceType[WorkspaceRepositoryWorkflowAttempt],
                _AttemptRecord,
            ]
        ] = []
        self._journal: Any = None
        self._journal_class: Any = None
        self._journal_entries: dict[str, Callable[..., Any]] = {}
        self._retired = False

    def retire(self) -> None:
        self._retired = True
        for _, record in self._plans:
            record.request = record.observation = None
            record.retired = True

        for _, attempt in self._attempts:
            attempt.plan = None
            attempt.status = "released"

    def check_current(self) -> None:
        # Inherited process/thread custody refuses before any IO or lock.
        if self.pid != os.getpid() or self.thread != threading.get_ident():
            raise WorkspaceRepositoryWorkflowRefusal("foreign_or_retired_handle")
        try:
            if self._retired or self.execution_id != _execution():
                raise WorkspaceRepositoryWorkflowRefusal("foreign_or_retired_handle")
            for root, identity in (
                (self.source, self.source_identity),
                (self.target, self.target_identity),
            ):
                if root.is_symlink() or _identity(root) != identity:
                    raise WorkspaceRepositoryWorkflowRefusal(
                        "foreign_or_retired_handle"
                    )
        except (OSError, WorkspaceRepositoryWorkflowRefusal):
            self.retire()
            raise WorkspaceRepositoryWorkflowRefusal(
                "foreign_or_retired_handle"
            ) from None
        except BaseException:
            self.retire()
            raise

    def _request(
        self, request: WorkspaceRepositoryWorkflowRequest
    ) -> WorkspaceRepositoryWorkflowRequest:
        try:
            value = repository_workflow_value_from_payload(
                WorkspaceRepositoryWorkflowRequest,
                repository_workflow_value_to_payload(request),
            )
            if not all(
                x and x.strip() == x
                for x in (
                    value.workflow_ref,
                    value.attempt_ref,
                    value.profile_key,
                )
            ):
                raise ValueError
            if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", value.source_commit):
                raise ValueError
            if value.expected_target_head is not None and not re.fullmatch(
                r"(?:[0-9a-f]{40}|[0-9a-f]{64})",
                value.expected_target_head,
            ):
                raise ValueError
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", value.profile_digest):
                raise ValueError
            keys = tuple(x.key for x in value.marker_environment)
            if keys != tuple(sorted(default_environment())):
                raise ValueError
            if not value.target_reference.startswith("refs/heads/"):
                raise ValueError
            _git(self.target, "check-ref-format", value.target_reference)
            return value
        except WorkspaceRepositoryWorkflowRefusal as error:
            if error.__cause__ is not None:
                raise
            # Keep invalid-reference nonzero exits as malformed request evidence.
            raise WorkspaceRepositoryWorkflowRefusal("malformed_binding") from error
        except (ValueError, WorkspaceWorkflowValueError):
            raise WorkspaceRepositoryWorkflowRefusal("malformed_binding") from None

    def _capture(self, request: WorkspaceRepositoryWorkflowRequest) -> str:
        from . import package_checkout

        if package_checkout.PackageSourceCheckout is not _CHECKOUT_CLASS or any(
            vars(_CHECKOUT_CLASS).get(name) is not method
            for name, method in _CHECKOUT_METHODS
        ):
            raise WorkspaceRepositoryWorkflowRefusal("source_unavailable")
        reader = None
        bodies = ()
        try:
            reader = _CHECKOUT_CLASS(self.source)
            inventory = _CHECKOUT_METHODS[1][1](
                reader,
                profiles=(request.profile_key,),
                marker_environment={x.key: x.value for x in request.marker_environment},
            )
            if inventory["revision_basis"] != request.source_commit:
                raise WorkspaceRepositoryWorkflowRefusal("stale_source")
            bodies = reader._bodies  # pyright: ignore[reportPrivateUsage] -- original captured selector bytes; never reread a substitute inventory
            manifest = next(body for path, body in bodies if path == "aware.repo.toml")
            if _digest(manifest) != request.profile_digest:
                raise WorkspaceRepositoryWorkflowRefusal("stale_source")
            # This consumes the original selector's captured paths; no caller inventory.
            for start in range(0, len(bodies), 512):
                batch = bodies[start : start + 512]
                rows = _git(
                    self.source,
                    "ls-tree",
                    "-rz",
                    request.source_commit,
                    "--",
                    *(path for path, _ in batch),
                )
                committed: dict[str, tuple[str, str, str]] = {}
                for row in rows.split(b"\0"):
                    if row:
                        metadata, path = row.split(b"\t", 1)
                        mode, kind, oid = metadata.decode().split()
                        committed[path.decode()] = (mode, kind, oid)
                for path, body in batch:
                    item = committed.get(path)
                    if (
                        item is None
                        or item[0] not in {"100644", "100755"}
                        or item[1] != "blob"
                    ):
                        raise WorkspaceRepositoryWorkflowRefusal("stale_source")
                    git_body = b"blob " + str(len(body)).encode() + b"\0" + body
                    digest = (
                        hashlib.sha1(git_body).hexdigest()
                        if len(item[2]) == 40
                        else hashlib.sha256(git_body).hexdigest()
                    )
                    mode = (self.source / path).lstat().st_mode
                    if (
                        digest != item[2]
                        or not stat.S_ISREG(mode)
                        or bool(mode & 0o111) != (item[0] == "100755")
                    ):
                        raise WorkspaceRepositoryWorkflowRefusal("stale_source")
            _CHECKOUT_METHODS[2][1](reader)
            if any(
                vars(_CHECKOUT_CLASS).get(name) is not method
                for name, method in _CHECKOUT_METHODS
            ):
                raise WorkspaceRepositoryWorkflowRefusal("source_unavailable")
            return cast(str, inventory["inventory_digest"])
        except WorkspaceRepositoryWorkflowRefusal:
            raise
        except (OSError, subprocess.SubprocessError) as error:
            raise WorkspaceRepositoryWorkflowRefusal(
                "source_unavailable", diagnostics=("source_capture_read_failed",)
            ) from error
        except (ValueError, StopIteration):
            raise WorkspaceRepositoryWorkflowRefusal("source_unavailable") from None
        finally:
            if reader is not None:
                _CHECKOUT_METHODS[3][1](reader)
            reader = bodies = batch = manifest = body = git_body = inventory = None

    def plan(
        self, request: WorkspaceRepositoryWorkflowRequest
    ) -> WorkspaceRepositoryWorkflowPlan:
        self.check_current()
        value = self._request(request)
        if _head(self.target, value.target_reference) != value.expected_target_head:
            raise WorkspaceRepositoryWorkflowRefusal("stale_target")
        selection = self._capture(value)
        self.check_current()
        if _head(self.target, value.target_reference) != value.expected_target_head:
            raise WorkspaceRepositoryWorkflowRefusal("stale_target")
        source_binding = _digest(_wire((str(self.source), self.source_identity)))
        target_binding = _digest(_wire((str(self.target), self.target_identity)))
        binding = _digest(
            _wire(
                (
                    source_binding,
                    target_binding,
                    self.generation,
                    self.execution_id,
                    selection,
                    repository_workflow_value_to_payload(value),
                )
            )
        )
        journal_available = False
        try:
            self._evidence_backend()
            journal_available = True
        except WorkspaceRepositoryWorkflowRefusal as error:
            if error.code != "supplier_unavailable":
                raise
        observed = WorkspaceRepositoryWorkflowPlanObservation(
            binding,
            source_binding,
            target_binding,
            value.source_commit,
            value.profile_key,
            value.profile_digest,
            selection,
            value.target_reference,
            value.expected_target_head,
            tuple(
                WorkspaceRepositoryWorkflowStageObservation(
                    stage,
                    "available"
                    if stage == "source_capture"
                    or (stage == "evidence_closeout" and journal_available)
                    else "supplier_unavailable",
                    ()
                    if stage == "source_capture"
                    or (stage == "evidence_closeout" and journal_available)
                    else ("original_stage_supplier_not_joined",),
                )
                for stage in _STAGES
            ),
            (),
        )
        self._plans = [
            (handle, record) for handle, record in self._plans if handle() is not None
        ]
        if len(self._plans) >= 256:
            raise WorkspaceRepositoryWorkflowRefusal("malformed_binding")
        handle = object.__new__(WorkspaceRepositoryWorkflowPlan)
        self._plans.append((weakref.ref(handle), _PlanRecord(value, observed)))
        return handle

    def _record(self, handle: object) -> _PlanRecord:
        # Identity lookup first retires known restamped families, without foreign dispatch.
        for reference, record in self._plans:
            if reference() is handle:
                if (
                    type(handle) is not WorkspaceRepositoryWorkflowPlan
                    or record.retired
                ):
                    record.request = record.observation = None
                    record.retired = True
                    raise WorkspaceRepositoryWorkflowRefusal(
                        "foreign_or_retired_handle"
                    )
                return record
        raise WorkspaceRepositoryWorkflowRefusal("foreign_or_retired_handle")

    def observe_plan(
        self, handle: WorkspaceRepositoryWorkflowPlan
    ) -> WorkspaceRepositoryWorkflowPlanObservation:
        self.check_current()
        record = self._record(handle)
        try:
            if record.request is None or record.observation is None:
                raise WorkspaceRepositoryWorkflowRefusal("foreign_or_retired_handle")
            if self._capture(record.request) != record.observation.selection_digest:
                raise WorkspaceRepositoryWorkflowRefusal("stale_source")
            if (
                _head(self.target, record.observation.target_reference)
                != record.observation.expected_target_head
            ):
                raise WorkspaceRepositoryWorkflowRefusal("stale_target")
            self.check_current()
            return repository_workflow_value_from_payload(
                WorkspaceRepositoryWorkflowPlanObservation,
                repository_workflow_value_to_payload(record.observation),
            )
        except BaseException:
            record.retired = True
            record.request = record.observation = None
            raise

    def _evidence_backend(self) -> tuple[Any, dict[str, Callable[..., Any]]]:
        if self._journal is None:
            try:
                from aware_workspace_fs_adapter.repository_workflow_evidence import (
                    FilesystemWorkflowEvidence,
                )
            except ImportError as error:
                raise WorkspaceRepositoryWorkflowRefusal(
                    "supplier_unavailable", stage="evidence_closeout"
                ) from error
            self._journal = FilesystemWorkflowEvidence(self.state_root)
            self._journal_class = FilesystemWorkflowEvidence
            self._journal_entries = {
                name: vars(FilesystemWorkflowEvidence)[name]
                for name in ("open", "observe", "append")
            }
        if type(self._journal) is not self._journal_class or any(
            cast(dict[str, object], vars(self._journal_class)).get(name) is not method
            for name, method in self._journal_entries.items()
        ):
            self.retire()
            raise WorkspaceRepositoryWorkflowRefusal(
                "foreign_or_retired_handle", stage="evidence_closeout"
            )
        return self._journal, self._journal_entries

    def _attempt_record(self, handle: object) -> _AttemptRecord:
        for reference, record in self._attempts:
            if reference() is handle:
                if type(handle) is not WorkspaceRepositoryWorkflowAttempt:
                    record.plan = None
                    record.status = "released"
                    raise WorkspaceRepositoryWorkflowRefusal(
                        "foreign_or_retired_handle", stage="evidence_closeout"
                    )
                return record
        raise WorkspaceRepositoryWorkflowRefusal(
            "foreign_or_retired_handle", stage="evidence_closeout"
        )

    def open_attempt(
        self, plan: WorkspaceRepositoryWorkflowPlan
    ) -> WorkspaceRepositoryWorkflowAttempt:
        from aware_workspace_fs_adapter.repository_workflow_evidence import (
            WorkflowEvidenceError,
        )

        observed = self.observe_plan(plan)
        record = self._record(plan)
        assert record.request is not None
        attempt_ref = record.request.attempt_ref
        self._attempts = [
            (reference, value)
            for reference, value in self._attempts
            if reference() is not None
        ]
        if len(self._attempts) >= 256:
            raise WorkspaceRepositoryWorkflowRefusal(
                "malformed_binding", stage="evidence_closeout"
            )
        # One original plan opens at most one operational attempt, including failure.
        record.retired = True
        record.request = record.observation = None
        opening = None
        try:
            backend, entries = self._evidence_backend()
            opening = entries["open"](backend, observed, attempt_ref)
            self.check_current()
        except WorkflowEvidenceError as error:
            raise WorkspaceRepositoryWorkflowRefusal(
                error.code,
                stage="evidence_closeout",
                persistence=error.persistence,
                cleanup=error.cleanup,
                attempt_binding_ref=observed.binding_ref,
                original_evidence_refs=error.evidence_refs,
            ) from error
        except WorkspaceRepositoryWorkflowRefusal as error:
            if opening is None:
                raise
            raise WorkspaceRepositoryWorkflowRefusal(
                error.code,
                stage="evidence_closeout",
                persistence="persisted",
                cleanup=opening.cleanup,
                attempt_binding_ref=observed.binding_ref,
                original_evidence_refs=opening.evidence_refs,
                diagnostics=("journal_opened_command_retired",),
            ) from error
        except (KeyboardInterrupt, SystemExit) as error:
            if opening is not None:
                # Preserve interruption identity and its original cause. This is
                # descriptive write evidence, never an active attempt or retry.
                evidence = WorkspaceRepositoryWorkflowRefusal(
                    "foreign_or_retired_handle",
                    stage="evidence_closeout",
                    persistence="persisted",
                    cleanup=opening.cleanup,
                    attempt_binding_ref=observed.binding_ref,
                    original_evidence_refs=opening.evidence_refs,
                ).evidence
                vars(error)["workflow_evidence"] = evidence
            raise
        handle = object.__new__(WorkspaceRepositoryWorkflowAttempt)
        self._attempts.append(
            (weakref.ref(handle), _AttemptRecord(observed, attempt_ref))
        )
        return handle

    def append_evidence(
        self,
        attempt: WorkspaceRepositoryWorkflowAttempt,
        request: WorkspaceRepositoryWorkflowEvidenceAppendRequest,
    ) -> WorkspaceRepositoryWorkflowEvidenceWriteObservation:
        from aware_workspace_fs_adapter.repository_workflow_evidence import (
            WorkflowEvidenceError,
        )

        self.check_current()
        record = self._attempt_record(attempt)
        if record.status != "active" or record.plan is None:
            raise WorkspaceRepositoryWorkflowRefusal(
                "foreign_or_retired_handle", stage="evidence_closeout"
            )
        value = None
        try:
            value = repository_workflow_value_from_payload(
                WorkspaceRepositoryWorkflowEvidenceAppendRequest,
                repository_workflow_value_to_payload(request),
            )
            if value.attempt_binding_ref != record.plan.binding_ref:
                raise WorkspaceRepositoryWorkflowRefusal(
                    "malformed_binding", stage=value.stage
                )
            if value.evidence_grade != "caller_reported":
                raise WorkspaceRepositoryWorkflowRefusal(
                    "supplier_unavailable", stage=value.stage
                )
            backend, entries = self._evidence_backend()
            cursor, digest, persistence, cleanup = entries["append"](
                backend,
                record.plan.source_repository_binding_ref,
                record.plan.target_repository_binding_ref,
                record.attempt_ref,
                value,
            )
            if cleanup != "completed":
                record.status = "held"
            result = WorkspaceRepositoryWorkflowEvidenceWriteObservation(
                value.attempt_binding_ref,
                value.expected_cursor,
                cursor,
                value.expected_previous_digest,
                digest,
                persistence,
                (),
                value.effect_state,
                cleanup,
                () if cleanup == "completed" else ("journal_cleanup_incomplete",),
            )
            try:
                self.check_current()
                self._evidence_backend()
            except WorkspaceRepositoryWorkflowRefusal:
                record.status = "held"
                return replace(
                    result,
                    diagnostics=result.diagnostics
                    + ("journal_written_command_retired",),
                )
            return result
        except WorkspaceWorkflowValueError as error:
            record.status = "held"
            raise WorkspaceRepositoryWorkflowRefusal(
                "malformed_binding", stage="evidence_closeout"
            ) from error
        except WorkflowEvidenceError as error:
            record.status = "held"
            if error.persistence == "unknown" and value is not None:
                return WorkspaceRepositoryWorkflowEvidenceWriteObservation(
                    value.attempt_binding_ref,
                    value.expected_cursor,
                    None,
                    value.expected_previous_digest,
                    None,
                    "unknown",
                    (),
                    value.effect_state,
                    error.cleanup,
                    (error.code,),
                )
            raise WorkspaceRepositoryWorkflowRefusal(
                error.code,
                stage=value.stage if value else "evidence_closeout",
                persistence=error.persistence,
                cleanup=error.cleanup,
                attempt_binding_ref=value.attempt_binding_ref if value else None,
                original_evidence_refs=error.evidence_refs,
            ) from error
        except BaseException:
            record.status = "held"
            raise

    def observe_attempt(
        self, request: WorkspaceRepositoryWorkflowAttemptObserveRequest
    ) -> WorkspaceRepositoryWorkflowAttemptObservation:
        from aware_workspace_fs_adapter.repository_workflow_evidence import (
            WorkflowEvidenceError,
        )

        self.check_current()
        try:
            value = repository_workflow_value_from_payload(
                WorkspaceRepositoryWorkflowAttemptObserveRequest,
                repository_workflow_value_to_payload(request),
            )
            source = _digest(_wire((str(self.source), self.source_identity)))
            target = _digest(_wire((str(self.target), self.target_identity)))
            if (
                value.source_repository_binding_ref != source
                or value.target_repository_binding_ref != target
            ):
                raise WorkspaceRepositoryWorkflowRefusal(
                    "malformed_binding", stage="evidence_closeout"
                )
            backend, entries = self._evidence_backend()
            snapshot = entries["observe"](
                backend,
                source,
                target,
                value.attempt_ref,
                value.expected_binding_digest,
            )
            return WorkspaceRepositoryWorkflowAttemptObservation(
                snapshot.plan,
                snapshot.records,
                snapshot.cursor,
                snapshot.digest,
                "persisted" if snapshot.integrity == "verified" else "unknown",
                snapshot.integrity,
                snapshot.cleanup,
                "descriptive_only",
                (),
            )
        except WorkspaceWorkflowValueError as error:
            raise WorkspaceRepositoryWorkflowRefusal(
                "malformed_binding", stage="evidence_closeout"
            ) from error
        except WorkflowEvidenceError as error:
            raise WorkspaceRepositoryWorkflowRefusal(
                error.code,
                stage="evidence_closeout",
                persistence=error.persistence,
                cleanup=error.cleanup,
            ) from error

    def release_attempt(
        self, attempt: WorkspaceRepositoryWorkflowAttempt
    ) -> WorkspaceRepositoryWorkflowCleanupObservation:
        self.check_current()
        record = self._attempt_record(attempt)
        binding = record.plan.binding_ref if record.plan else None
        record.plan = None
        record.status = "released"
        # Physical calls own their descriptors; release never deletes durable evidence.
        return WorkspaceRepositoryWorkflowCleanupObservation(binding, "completed", ())
