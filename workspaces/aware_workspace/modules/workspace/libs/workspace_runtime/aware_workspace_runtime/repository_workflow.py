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
from dataclasses import dataclass, field, replace
from pathlib import Path
from types import FunctionType
from typing import Any, Literal, cast

from aware_workspace_sdk.repository_workflow import (
    WorkspaceRepositoryWorkflowAttempt,
    WorkspaceRepositoryWorkflowPlan,
    WorkspaceRepositoryWorkflowRefusal,
    WorkspaceRepositoryWorkflowSource,
)
from aware_workspace_sdk.repository_workflow_codec import (
    WorkspaceWorkflowValueError,
    repository_workflow_value_from_payload,
    repository_workflow_value_to_payload,
)
from aware_workspace_sdk.repository_workflow_source_codec import (
    repository_workflow_source_value_clone,
    repository_workflow_source_value_to_payload,
)
from aware_workspace_sdk.repository_workflow_source_values import (
    MAX_WORKFLOW_SOURCE_BYTES,
    MAX_WORKFLOW_SOURCE_FILES,
    WorkspaceWorkflowSourceBinding,
    WorkspaceWorkflowSourceBody,
    WorkspaceWorkflowSourceFile,
    WorkspaceWorkflowSourceObservation,
    WorkspaceWorkflowSourceRead,
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

from . import composition, package_checkout, source_observation_io
from .package_checkout import PackageSourceCheckout

_CHECKOUT_CLASS = PackageSourceCheckout
_CHECKOUT_METHODS: tuple[tuple[str, Callable[..., Any]], ...] = tuple(
    (name, vars(_CHECKOUT_CLASS)[name])
    for name in (
        "__init__",
        "resolve",
        "revalidate",
        "close",
        "revalidate_paths",
    )
)
# All owner helper entries dispatched by the retained reader, including IO primitives.
_READER_CLASS_PINS = tuple(
    (name, value) for name, value in vars(_CHECKOUT_CLASS).items() if callable(value)
)
_READER_CLASS_SHAPE = tuple(vars(_CHECKOUT_CLASS).items())
_READER_CLASS_CODE_PINS = tuple(
    (method, method.__code__)
    for _, method in _READER_CLASS_PINS
    if hasattr(method, "__code__")
)
_READER_MODULE_PINS = tuple(
    (name, vars(package_checkout)[name])
    for name in (
        "PackageSourceCheckout",
        "_bind_retained_reader",
        "_check_retained_reader",
        "_read_git",
        "_retain_composition_readers",
        "_COMPOSITION_READER_ENTRIES",
        "_TRACKED_STAT",
        "os",
        "subprocess",
        "_RETAINED_READER_GUARDS",
        "_git",
        "_GIT_RUN",
        "capture_exact_paths",
        "validate_relative_path",
        "parse_checkout_profiles",
        "expand_checkout_profiles",
        "checkout_repository_files",
        "LocalCheckoutWorkspaceCompositionProvider",
        "_LIMITS",
    )
)
_READER_IO_PINS = tuple(
    (name, vars(source_observation_io)[name])
    for name in (
        "capture_exact_paths",
        "validate_relative_path",
        "_stamp",
        "_EXACT_PATH_IO",
        "_EXACT_VALIDATE_PATH",
        "_EXACT_STAMP",
        "os",
    )
)
_READER_OS_PINS = tuple(
    (name, vars(os)[name]) for name in ("dup", "open", "close", "fstat", "stat", "read")
)
_COMPOSITION_CLASS = package_checkout.LocalCheckoutWorkspaceCompositionProvider
_COMPOSITION_CLASS_PINS = tuple(vars(_COMPOSITION_CLASS).items())
_COMPOSITION_MODULE_PINS = tuple(
    (name, value) for name, value in vars(composition).items() if callable(value)
)
# Function/code identity does not cover mutable default selection. Retain both
# the default containers and a detached snapshot of keyword-default entries,
# including nested guard/IO helpers reached by the original reader.
_READER_DEFAULT_PINS = tuple(
    (
        method,
        method.__defaults__,
        method.__kwdefaults__,
        tuple(method.__kwdefaults__.items())
        if method.__kwdefaults__ is not None
        else (),
    )
    for _, method in (
        *_READER_CLASS_PINS,
        *_READER_MODULE_PINS,
        *_READER_IO_PINS,
        *_COMPOSITION_CLASS_PINS,
        *_COMPOSITION_MODULE_PINS,
    )
    if type(method) is FunctionType
)
_PATH_METHOD_PINS = tuple(
    (name, getattr(Path, name))
    for name in (
        "stat",
        "lstat",
        "resolve",
        "is_symlink",
        "is_file",
        "is_dir",
        "read_bytes",
        "open",
        "__str__",
    )
)
_READER_RUN = subprocess.run
_READER_LSTAT = os.lstat
_READER_CHECK_CLASS = _CHECKOUT_CLASS
_READER_CLOSE = vars(_CHECKOUT_CLASS)["close"]


def _reader_entries_current() -> None:
    for method, defaults, keyword_defaults, entries in _READER_DEFAULT_PINS:
        current = method.__kwdefaults__
        if (
            method.__defaults__ is not defaults
            or current is not keyword_defaults
            or (
                current is not None
                and (
                    type(current) is not dict
                    or len(current) != len(entries)
                    or any(
                        type(name) is not str
                        or name != original_name
                        or value is not original_value
                        for (name, value), (original_name, original_value) in zip(
                            current.items(), entries, strict=True
                        )
                    )
                )
            )
        ):
            # A held refusal must not retain a substituted defaults container.
            del current
            raise WorkspaceRepositoryWorkflowRefusal(
                "source_unavailable", diagnostics=("retained_reader_substituted",)
            )
    if (
        len(vars(_READER_CHECK_CLASS)) != len(_READER_CLASS_SHAPE)
        or any(method.__code__ is not code for method, code in _READER_CLASS_CODE_PINS)
        or any(
            vars(_READER_CHECK_CLASS).get(name) is not original
            for name, original in _READER_CLASS_SHAPE
        )
        or any(
            vars(_READER_CHECK_CLASS).get(name) is not original
            for name, original in _READER_CLASS_PINS
        )
        or any(
            vars(package_checkout).get(name) is not original
            for name, original in _READER_MODULE_PINS
        )
        or any(
            vars(source_observation_io).get(name) is not original
            for name, original in _READER_IO_PINS
        )
        or any(vars(os).get(name) is not original for name, original in _READER_OS_PINS)
        or len(vars(_COMPOSITION_CLASS)) != len(_COMPOSITION_CLASS_PINS)
        or any(
            vars(_COMPOSITION_CLASS).get(name) is not original
            for name, original in _COMPOSITION_CLASS_PINS
        )
        or any(
            vars(composition).get(name) is not original
            for name, original in _COMPOSITION_MODULE_PINS
        )
        or any(
            getattr(Path, name) is not original for name, original in _PATH_METHOD_PINS
        )
        or subprocess.run is not _READER_RUN
    ):
        raise WorkspaceRepositoryWorkflowRefusal(
            "source_unavailable", diagnostics=("retained_reader_substituted",)
        )


@dataclass(slots=True)
class _SourceRecord:
    parent: _AttemptRecord
    reader: PackageSourceCheckout | None
    observation: WorkspaceWorkflowSourceObservation
    guard: Callable[[], None]
    state: tuple[tuple[str, object], ...]
    reader_data: dict[str, Any]
    descriptor: int
    status: Literal["retained", "released", "terminal"] = "retained"
    cleanup: Literal["completed", "unknown"] = "completed"


def _close_source(
    record: _SourceRecord,
    pid: int,
    *,
    terminal: bool = False,
    _close: Callable[[int], None] = os.close,
) -> None:
    if os.getpid() != pid:
        return
    record.reader = None
    descriptor, record.descriptor = record.descriptor, -1
    record.state = ()
    record.status = "terminal" if terminal else "released"
    if terminal:
        record.parent.status = "held"
    # Only the dictionary captured by the original owner is cleared. A changed
    # reader class/descriptor/dictionary cannot redirect cleanup to borrowed state.
    data = record.reader_data
    data["_fd"] = -1
    data["_bodies"] = ()
    data["_inventory"] = None
    data["_reader_guard"] = None
    record.reader_data = {}
    try:
        if descriptor >= 0:
            _close(descriptor)
    except BaseException:  # noqa: BLE001 -- once-spent physical cleanup retains uncertainty
        record.cleanup = "unknown"
    finally:
        data = None


def _source_acquisition_cleanup(
    error: BaseException,
) -> Literal["completed", "unknown"]:
    """Carry original partial-acquisition cleanup through typed refusal causes."""
    current: BaseException | None = error
    try:
        for _ in range(8):
            if current is None:
                break
            if vars(current).get("workspace_source_acquisition_cleanup") == "unknown":
                return "unknown"
            current = vars(BaseException)["__cause__"].__get__(current, BaseException)
        return "completed"
    finally:
        del error, current


def _release_parent_sources(record: _AttemptRecord, pid: int) -> None:
    if os.getpid() == pid:
        record.status = "released"
        record.request = None
        for source in record.sources:
            _close_source(source, pid)


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
    request: WorkspaceRepositoryWorkflowRequest | None = None
    opening_refs: tuple[Any, ...] = ()
    sources: list[_SourceRecord] = field(default_factory=list)


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
        self._sources: list[
            tuple[
                weakref.ReferenceType[WorkspaceRepositoryWorkflowSource], _SourceRecord
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
            _release_parent_sources(attempt, self.pid)
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

    def _capture(
        self, request: WorkspaceRepositoryWorkflowRequest, *, retain: bool = False
    ) -> str | PackageSourceCheckout:
        from . import package_checkout

        if package_checkout.PackageSourceCheckout is not _CHECKOUT_CLASS or any(
            vars(_CHECKOUT_CLASS).get(name) is not method
            for name, method in _CHECKOUT_METHODS
        ):
            raise WorkspaceRepositoryWorkflowRefusal("source_unavailable")
        reader = None
        retained = False
        bodies = ()
        batches: list[list[tuple[str, bytes]]] = []
        if retain:
            _reader_entries_current()
        try:
            reader = (
                _CHECKOUT_CLASS(self.source, _workflow_guard=_reader_entries_current)
                if retain
                else _CHECKOUT_CLASS(self.source)
            )
            if retain:
                _reader_entries_current()
                package_checkout._bind_retained_reader(reader, _reader_entries_current)  # pyright: ignore[reportPrivateUsage] -- original reader owner binding
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
            # Retained delivery batches remain below a conservative argv byte bound.
            batches = [[]]
            argument_bytes = 0
            for path, body in bodies:
                if batches[-1] and (
                    len(batches[-1]) >= (2048 if retain else 512)
                    or argument_bytes + len(path.encode()) + 1
                    > (98304 if retain else 65536)
                ):
                    batches.append([])
                    argument_bytes = 0
                batches[-1].append((path, body))
                argument_bytes += len(path.encode()) + 1
            for batch in batches:
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
                    if retain:
                        if os.lstat is not _READER_LSTAT:
                            raise WorkspaceRepositoryWorkflowRefusal(
                                "source_unavailable"
                            )
                        mode = _READER_LSTAT(str(self.source) + "/" + path).st_mode
                    else:
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
            if retain:
                _reader_entries_current()
                retained = True
                return reader
            return cast(str, inventory["inventory_digest"])
        except WorkspaceRepositoryWorkflowRefusal:
            raise
        except (OSError, subprocess.SubprocessError) as error:
            raise WorkspaceRepositoryWorkflowRefusal(
                "source_unavailable", diagnostics=("source_capture_read_failed",)
            ) from error
        except (
            ValueError,
            StopIteration,
            source_observation_io.SourceObservationUnavailable,
        ) as error:
            if "workspace_source_acquisition_cleanup" in vars(error):
                raise WorkspaceRepositoryWorkflowRefusal(
                    "source_unavailable", cleanup=_source_acquisition_cleanup(error)
                ) from error
            raise WorkspaceRepositoryWorkflowRefusal("source_unavailable") from None
        finally:
            batches.clear()
            if reader is not None and not retained:
                _CHECKOUT_METHODS[3][1](reader)
            reader = bodies = batch = manifest = body = git_body = inventory = None

    def plan(
        self, request: WorkspaceRepositoryWorkflowRequest
    ) -> WorkspaceRepositoryWorkflowPlan:
        self.check_current()
        value = self._request(request)
        if _head(self.target, value.target_reference) != value.expected_target_head:
            raise WorkspaceRepositoryWorkflowRefusal("stale_target")
        selection = cast(str, self._capture(value))
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
                    _release_parent_sources(record, self.pid)
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
        original_request = record.request
        attempt_ref = original_request.attempt_ref
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
        attempt_record = _AttemptRecord(
            observed,
            attempt_ref,
            request=original_request,
            opening_refs=opening.evidence_refs,
        )
        self._attempts.append((weakref.ref(handle), attempt_record))
        weakref.finalize(handle, _release_parent_sources, attempt_record, self.pid)
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
        _release_parent_sources(record, self.pid)
        record.plan = None
        record.status = "released"
        # Physical calls own their descriptors; release never deletes durable evidence.
        return WorkspaceRepositoryWorkflowCleanupObservation(
            binding,
            "unknown"
            if any(source.cleanup == "unknown" for source in record.sources)
            else "completed",
            (),
        )

    def retain_source(
        self, attempt: WorkspaceRepositoryWorkflowAttempt
    ) -> WorkspaceRepositoryWorkflowSource:
        parent = reader = record = handle = inventory = bodies = files = state = None
        try:
            self.check_current()
            parent = self._attempt_record(attempt)
            if (
                parent.status != "active"
                or parent.request is None
                or parent.plan is None
                or parent.sources
            ):
                raise WorkspaceRepositoryWorkflowRefusal("foreign_or_retired_handle")
            reader = cast(
                PackageSourceCheckout, self._capture(parent.request, retain=True)
            )
            inventory = reader._inventory  # pyright: ignore[reportPrivateUsage] -- original owner captures the retained reader state
            if (
                inventory is None
                or inventory["inventory_digest"] != parent.plan.selection_digest
            ):
                raise WorkspaceRepositoryWorkflowRefusal("stale_source")
            bodies = dict(reader._bodies)  # pyright: ignore[reportPrivateUsage] -- original owner captures the retained reader state
            files = tuple(
                WorkspaceWorkflowSourceFile(
                    source,
                    output,
                    _digest(bodies[source]),
                    len(bodies[source]),
                    mode,
                    cast(Any, 493 if mode == "100755" else 420),
                )
                for mode, output, source in object.__getattribute__(
                    reader, "_output_rows"
                )
            )  # pyright: ignore[reportPrivateUsage] -- original owner captures the retained reader state
            layout = _digest(
                _wire(
                    [
                        [
                            f.source_path,
                            f.output_path,
                            f.content_digest,
                            f.size_bytes,
                            f.git_mode,
                            f.projected_mode,
                        ]
                        for f in files
                    ]
                )
            )
            binding = WorkspaceWorkflowSourceBinding(
                _digest(_wire((self.generation, parent.plan.binding_ref, "source:v1"))),
                parent.request.workflow_ref,
                parent.attempt_ref,
                parent.plan.binding_ref,
                self.generation,
                self.execution_id,
                self.pid,
                self.thread,
                parent.plan.source_repository_binding_ref,
                parent.plan.target_repository_binding_ref,
                str(self.source),
                str(self.target),
                self.source_identity,
                self.target_identity,
                parent.request.source_commit,
                parent.request.profile_key,
                parent.request.profile_digest,
                parent.request.marker_environment,
                parent.plan.selection_digest,
                inventory["contract"],
                layout,
                len(bodies),
                len(files),
                sum(len(body) for body in bodies.values()),
                MAX_WORKFLOW_SOURCE_FILES,
                MAX_WORKFLOW_SOURCE_BYTES,
                parent.request.target_reference,
                parent.request.expected_target_head,
            )
            observation = WorkspaceWorkflowSourceObservation(
                binding, files, "retained", "not_attempted"
            )
            repository_workflow_source_value_to_payload(observation)
            state = tuple(
                (name, object.__getattribute__(reader, name))
                for name in (
                    "root",
                    "_fd",
                    "_identity",
                    "_revision",
                    "_bodies",
                    "_source_rows",
                    "_package_roots",
                    "_repository_rows",
                    "_output_rows",
                    "_inventory",
                    "_reader_guard",
                )
            )
            record = _SourceRecord(
                parent,
                reader,
                observation,
                _reader_entries_current,
                state,
                vars(reader),
                reader._fd,  # pyright: ignore[reportPrivateUsage] -- original owned descriptor custody
            )
            self.check_current()
            _CHECKOUT_METHODS[2][1](reader)
            handle = object.__new__(WorkspaceRepositoryWorkflowSource)
            parent.sources.append(record)
            self._sources.append((weakref.ref(handle), record))
            weakref.finalize(handle, _close_source, record, self.pid)
            reader = None
            return handle
        except (
            ValueError,
            OSError,
            source_observation_io.SourceObservationUnavailable,
        ) as error:
            if parent is not None:
                parent.status = "held"
            if record is not None:
                _close_source(record, self.pid, terminal=True)
            if parent is not None and parent.plan is not None:
                raise WorkspaceRepositoryWorkflowRefusal(
                    error.code
                    if type(error) is WorkspaceRepositoryWorkflowRefusal
                    else "source_unavailable",
                    persistence="persisted",
                    attempt_binding_ref=parent.plan.binding_ref,
                    original_evidence_refs=parent.opening_refs,
                    cleanup=record.cleanup
                    if record is not None
                    else _source_acquisition_cleanup(error),
                ) from error
            raise
        except BaseException as error:
            if parent is not None:
                parent.status = "held"
            if record is not None:
                _close_source(record, self.pid, terminal=True)
            if (
                parent is not None
                and parent.plan is not None
                and (type(error) is KeyboardInterrupt or type(error) is SystemExit)
            ):
                vars(error)["workflow_evidence"] = WorkspaceRepositoryWorkflowRefusal(
                    "source_unavailable",
                    persistence="persisted",
                    attempt_binding_ref=parent.plan.binding_ref,
                    original_evidence_refs=parent.opening_refs,
                    cleanup=record.cleanup
                    if record is not None
                    else _source_acquisition_cleanup(error),
                ).evidence
            raise
        finally:
            if reader is not None:
                _READER_CLOSE(reader)
            del (
                self,
                attempt,
                parent,
                reader,
                record,
                handle,
                inventory,
                bodies,
                files,
                state,
            )

    def _source_record(self, source: object) -> _SourceRecord:
        reference = record = None
        try:
            if self.pid != os.getpid() or self.thread != threading.get_ident():
                raise WorkspaceRepositoryWorkflowRefusal("foreign_or_retired_handle")
            for reference, record in self._sources:
                if reference() is source:
                    if type(source) is not WorkspaceRepositoryWorkflowSource:
                        _close_source(record, self.pid, terminal=True)
                        raise WorkspaceRepositoryWorkflowRefusal(
                            "foreign_or_retired_handle"
                        )
                    return record
            raise WorkspaceRepositoryWorkflowRefusal("foreign_or_retired_handle")
        finally:
            del self, source, reference, record

    def _validate_source(
        self, record: _SourceRecord, *, output_paths: tuple[str, ...] | None = None
    ) -> None:
        if (
            record.status != "retained"
            or record.reader is None
            or record.parent.status != "active"
        ):
            raise WorkspaceRepositoryWorkflowRefusal("foreign_or_retired_handle")
        self.check_current()
        reader = record.reader
        try:
            _reader_entries_current()
            if (
                type(reader) is not _READER_CHECK_CLASS
                or vars(reader) is not record.reader_data
                or any(
                    object.__getattribute__(reader, name) is not value
                    for name, value in record.state
                )
            ):
                raise WorkspaceRepositoryWorkflowRefusal("source_unavailable")
            if output_paths is None:
                _CHECKOUT_METHODS[2][1](reader)
            else:
                _CHECKOUT_METHODS[4][1](reader, output_paths)
            _reader_entries_current()
            self.check_current()
        finally:
            del self, record, reader

    def _source_operation(
        self,
        source: object,
        expected: object = None,
        paths: object = None,
        *,
        verify_paths: bool = False,
    ) -> Any:
        record = selected = result = bodies = expected_payload = selected_paths = None
        try:
            record = self._source_record(source)
            if verify_paths and (
                type(expected) is not WorkspaceWorkflowSourceBinding
                or type(paths) is not tuple
                or any(
                    type(path) is not str for path in cast(tuple[object, ...], paths)
                )
            ):
                raise WorkspaceRepositoryWorkflowRefusal("malformed_binding")
            selected_paths = cast(tuple[str, ...], paths) if verify_paths else None
            self._validate_source(record, output_paths=selected_paths)
            if expected is not None:
                if type(expected) is not WorkspaceWorkflowSourceBinding:
                    raise WorkspaceRepositoryWorkflowRefusal("malformed_binding")
                expected_payload = repository_workflow_source_value_to_payload(expected)
                if _wire(expected_payload) != _wire(
                    repository_workflow_source_value_to_payload(
                        record.observation.binding
                    )
                ):
                    raise WorkspaceRepositoryWorkflowRefusal("malformed_binding")
            if verify_paths or (paths is None and expected is not None):
                result = (
                    None  # Verification does not allocate another complete observation.
                )
            elif paths is None:
                result = repository_workflow_source_value_clone(record.observation)
            else:
                if type(paths) is not tuple:
                    raise WorkspaceRepositoryWorkflowRefusal("malformed_binding")
                paths = cast(tuple[str, ...], paths)
                if (
                    not paths
                    or len(paths) > MAX_WORKFLOW_SOURCE_FILES
                    or any(type(path) is not str for path in paths)
                ):
                    raise WorkspaceRepositoryWorkflowRefusal("malformed_binding")
                if tuple(sorted(set(paths))) != paths:
                    raise WorkspaceRepositoryWorkflowRefusal("malformed_binding")
                selected = {f.output_path: f for f in record.observation.files}
                if any(path not in selected for path in paths):
                    raise WorkspaceRepositoryWorkflowRefusal("malformed_binding")
                assert record.reader is not None
                bodies = dict(record.reader._bodies)  # pyright: ignore[reportPrivateUsage] -- original owner captures the retained reader state
                result = WorkspaceWorkflowSourceRead(
                    record.observation.binding,
                    tuple(
                        WorkspaceWorkflowSourceBody(
                            selected[path], bodies[selected[path].source_path]
                        )
                        for path in paths
                    ),
                )
            self._validate_source(record, output_paths=selected_paths)
            return result
        except (
            ValueError,
            OSError,
            source_observation_io.SourceObservationUnavailable,
        ) as error:
            if record is not None:
                _close_source(record, self.pid, terminal=True)
                raise WorkspaceRepositoryWorkflowRefusal(
                    error.code
                    if type(error) is WorkspaceRepositoryWorkflowRefusal
                    else "source_unavailable",
                    persistence="persisted",
                    attempt_binding_ref=record.observation.binding.binding_ref,
                    original_evidence_refs=record.parent.opening_refs,
                    cleanup=record.cleanup,
                ) from error
            raise
        except BaseException as error:
            if record is not None:
                _close_source(record, self.pid, terminal=True)
                if type(error) is KeyboardInterrupt or type(error) is SystemExit:
                    vars(error)["workflow_evidence"] = (
                        WorkspaceRepositoryWorkflowRefusal(
                            "source_unavailable",
                            persistence="persisted",
                            attempt_binding_ref=record.observation.binding.binding_ref,
                            original_evidence_refs=record.parent.opening_refs,
                            cleanup=record.cleanup,
                        ).evidence
                    )
            raise
        finally:
            del (
                self,
                source,
                expected,
                paths,
                record,
                selected,
                result,
                bodies,
                expected_payload,
                selected_paths,
            )

    def observe_source(
        self, source: WorkspaceRepositoryWorkflowSource
    ) -> WorkspaceWorkflowSourceObservation:
        try:
            return cast(
                WorkspaceWorkflowSourceObservation, self._source_operation(source)
            )
        finally:
            del self, source

    def verify_source(
        self,
        source: WorkspaceRepositoryWorkflowSource,
        expected_binding: WorkspaceWorkflowSourceBinding,
    ) -> None:
        try:
            self._source_operation(source, expected_binding)
        finally:
            del self, source, expected_binding

    def read_source(
        self,
        source: WorkspaceRepositoryWorkflowSource,
        expected_binding: WorkspaceWorkflowSourceBinding,
        output_paths: tuple[str, ...],
    ) -> WorkspaceWorkflowSourceRead:
        try:
            return cast(
                WorkspaceWorkflowSourceRead,
                self._source_operation(source, expected_binding, output_paths),
            )
        finally:
            del self, source, expected_binding, output_paths

    def verify_source_paths(
        self,
        source: WorkspaceRepositoryWorkflowSource,
        expected_binding: WorkspaceWorkflowSourceBinding,
        output_paths: tuple[str, ...],
    ) -> None:
        try:
            self._source_operation(
                source, expected_binding, output_paths, verify_paths=True
            )
        finally:
            del self, source, expected_binding, output_paths

    def release_source(
        self, source: WorkspaceRepositoryWorkflowSource
    ) -> WorkspaceRepositoryWorkflowCleanupObservation:
        record = None
        try:
            record = self._source_record(source)
            _close_source(record, self.pid)
            return WorkspaceRepositoryWorkflowCleanupObservation(
                record.observation.binding.binding_ref, record.cleanup, ()
            )
        finally:
            del self, source, record
