"""Canonical local git commit rail with strict ownership checks."""

from __future__ import annotations

import fcntl
import hashlib
import hmac
import json
import os
import re
import secrets
import shlex
import stat
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType
from typing import Any, Literal, Never, Protocol, Self, SupportsIndex, final, override

from aware_workspace_operator.models import (
    ResidentCommitAdmissionEvidence,
    WorkspaceAuthorizedCommitOptions,
    WorkspaceAuthorizedPathState,
    WorkspaceCommitIssueMetadata,
    WorkspaceCommitOptions,
    WorkspaceCommitOutcome,
    WorkspaceCommitReport,
    WorkspaceContentCommitOptions,
    WorkspaceSuppliedPathContent,
)

_OWNER_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*-.+$")
_HEADER_FIELD_PATTERN = re.compile(r"^\s*-\s*([^:]+):\s*(.*)$")
_OWNERSHIP_HEADER = "Ownership Scope"
_MAX_ERROR_TEXT_LEN = 500
_GIT_MUTATION_LOCK_PATH = Path("aware/locks/repository-publication.lock")
_DEFAULT_GIT_MUTATION_LOCK_TIMEOUT_SECONDS = 300.0
_DEFAULT_GIT_MUTATION_LOCK_POLL_SECONDS = 0.1
_MAX_IDEMPOTENCY_REF_LENGTH = 512
_MAX_IDEMPOTENCY_MATCHES = 2
_IDEMPOTENCY_REF_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")
_IDEMPOTENCY_REF_TRAILER = "Aware-Idempotency-Ref"
_REQUEST_FINGERPRINT_TRAILER = "Aware-Request-Fingerprint"
_ADMISSION_REF_NAMESPACE = "refs/aware/repository-admissions/v1"
_PUBLICATION_RECEIPT_PATTERN = re.compile(r"^git:([0-9a-fA-F]{40}|[0-9a-fA-F]{64})$")
_RESIDENT_PROVIDER_LOCK = threading.RLock()
_RESIDENT_PROVIDER_OWNERS: set[str] = set()
_RESIDENT_PROVIDER_TOKEN = object()


@dataclass(frozen=True)
class _IssueMetadata:
    issue_path: str
    issue_tag: str
    issue_owner: str
    issue_status: str
    ownership_scope: tuple[str, ...]


@dataclass(frozen=True)
class _GitCommandResult:
    returncode: int
    stdout: str
    stderr: str


def verify_repository_commit_receipt(
    *,
    repo_root: str | Path,
    publication_receipt_ref: str,
    expected_issue_ref: str | None = None,
) -> str:
    """Verify that a Git receipt names a commit reachable from current HEAD."""

    resolved_root = Path(repo_root).expanduser().resolve()
    _validate_repo_root(repo_root=resolved_root)
    if type(publication_receipt_ref) is not str:
        raise TypeError("publication_receipt_ref must be str")
    match = _PUBLICATION_RECEIPT_PATTERN.fullmatch(publication_receipt_ref)
    if match is None:
        raise ValueError("publication_receipt_malformed")
    commit_hash = match.group(1).lower()
    exists = subprocess.run(
        ("git", "cat-file", "-e", f"{commit_hash}^{{commit}}"),
        cwd=resolved_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if exists.returncode != 0:
        raise ValueError("publication_receipt_commit_absent")
    reachable = subprocess.run(
        ("git", "merge-base", "--is-ancestor", commit_hash, "HEAD"),
        cwd=resolved_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if reachable.returncode != 0:
        raise ValueError("publication_receipt_not_reachable")
    if expected_issue_ref is not None:
        if type(expected_issue_ref) is not str or not expected_issue_ref.strip():
            raise ValueError("expected_issue_ref_invalid")
        message = subprocess.run(
            ("git", "show", "-s", "--format=%B", commit_hash),
            cwd=resolved_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if message.returncode != 0:
            raise ValueError("publication_receipt_message_unavailable")
        expected_trailer = f"Issue-Tag: {expected_issue_ref.strip()}"
        if expected_trailer not in message.stdout.splitlines():
            raise ValueError("publication_receipt_issue_mismatch")
    return f"git:{commit_hash}"


@dataclass(frozen=True)
class _IdempotentCommit:
    commit_hash: str
    changed_paths: tuple[str, ...]


class _GitCommandError(RuntimeError):
    def __init__(
        self,
        *,
        args: tuple[str, ...],
        cwd: Path,
        result: _GitCommandResult,
        command_log: tuple[tuple[str, ...], ...],
    ) -> None:
        self.command_args = args
        self.cwd = cwd
        self.result = result
        self.command_log = command_log
        super().__init__(
            _format_git_command_failure(
                args=args,
                cwd=cwd,
                result=result,
            )
        )


class _GitMutationLockTimeoutError(RuntimeError):
    pass


class _RepositoryWritePreflightError(RuntimeError):
    pass


class _RepositoryIndexRestoreError(RuntimeError):
    pass


def _refuse_resident_admission_movement() -> Never:
    raise TypeError("resident_commit_admission_is_process_local")


@final
class _ResidentCommitAdmissionGrant:
    __slots__ = ()

    def __new__(cls) -> _ResidentCommitAdmissionGrant:
        raise TypeError("resident_commit_admission_constructor_private")

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("resident_commit_admission_is_final")

    def __copy__(self) -> object:
        _refuse_resident_admission_movement()

    def __deepcopy__(self, memo: dict[int, object]) -> object:
        del memo
        _refuse_resident_admission_movement()

    @override
    def __reduce__(self) -> Never:
        _refuse_resident_admission_movement()

    @override
    def __reduce_ex__(self, protocol: SupportsIndex) -> Never:
        del protocol
        _refuse_resident_admission_movement()


@dataclass(slots=True)
class _ResidentGrantRecord:
    issuance_digest: str
    provider_owner: object
    authority_digest: str
    consumed: bool = False


@final
class _ResidentRepositoryCommitProvider:
    __slots__ = (
        "_generation_owner_ref",
        "_grants",
        "_issuer_key",
        "_journal_root",
        "_owner",
    )

    def __new__(
        cls, token: object, generation_owner_ref: str, journal_root: Path
    ) -> _ResidentRepositoryCommitProvider:
        del generation_owner_ref, journal_root
        if token is not _RESIDENT_PROVIDER_TOKEN:
            raise TypeError("resident_commit_provider_constructor_private")
        return super().__new__(cls)

    def __init__(
        self, token: object, generation_owner_ref: str, journal_root: Path
    ) -> None:
        if token is not _RESIDENT_PROVIDER_TOKEN:
            raise TypeError("resident_commit_provider_constructor_private")
        if (
            not generation_owner_ref
            or generation_owner_ref != generation_owner_ref.strip()
            or not journal_root.is_absolute()
        ):
            raise ValueError("resident_commit_generation_owner_invalid")
        self._generation_owner_ref = generation_owner_ref
        self._journal_root = journal_root
        if self._journal_root.exists():
            metadata = self._journal_root.lstat()
            if (
                not stat.S_ISDIR(metadata.st_mode)
                or metadata.st_uid != os.geteuid()
                or stat.S_IMODE(metadata.st_mode) != 0o700
            ):
                raise ValueError("resident_commit_journal_root_invalid")
        else:
            self._journal_root.mkdir(mode=0o700, parents=True)
        if self._journal_root.is_symlink():
            raise ValueError("resident_commit_journal_root_invalid")
        self._issuer_key = self._load_or_create_issuer_key()
        self._owner = object()
        self._grants: dict[_ResidentCommitAdmissionGrant, _ResidentGrantRecord] = {}

    def authenticate_admission_evidence(
        self, evidence: dict[str, object]
    ) -> dict[str, object]:
        self._require_transaction_caller()
        if "issuer_authentication_code" in evidence:
            raise ValueError("resident_commit_admission_already_authenticated")
        code = hmac.new(
            self._issuer_key, _canonical_bytes(evidence), hashlib.sha256
        ).hexdigest()
        return {**evidence, "issuer_authentication_code": f"hmac-sha256:{code}"}

    def verify_admission_evidence(self, evidence: dict[str, object]) -> None:
        supplied = evidence.get("issuer_authentication_code")
        if not isinstance(supplied, str) or not supplied.startswith("hmac-sha256:"):
            raise RuntimeError("resident_commit_admission_authentication_missing")
        unsigned = dict(evidence)
        del unsigned["issuer_authentication_code"]
        expected = (
            "hmac-sha256:"
            + hmac.new(
                self._issuer_key, _canonical_bytes(unsigned), hashlib.sha256
            ).hexdigest()
        )
        if not hmac.compare_digest(supplied, expected):
            raise RuntimeError("resident_commit_admission_authentication_invalid")

    def _load_or_create_issuer_key(self) -> bytes:
        path = self._journal_root / "issuer.key"
        if not path.exists():
            try:
                _write_no_replace(path, secrets.token_bytes(32))
            except RuntimeError:
                if not path.exists():
                    raise
        metadata = path.lstat()
        value = path.read_bytes()
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != os.geteuid()
            or metadata.st_nlink != 1
            or stat.S_IMODE(metadata.st_mode) != 0o600
            or len(value) != 32
        ):
            raise ValueError("resident_commit_admission_issuer_key_invalid")
        return value

    def __call__(
        self, *, options: WorkspaceAuthorizedCommitOptions
    ) -> WorkspaceCommitOutcome:
        evidence = options.resident_admission_evidence
        if (
            evidence is None
            or evidence.generation_owner_ref != self._generation_owner_ref
        ):
            return run_workspace_authorized_commit(options=options)
        return run_workspace_authorized_commit(options=options, _resident_provider=self)

    def _issue(self, authority: dict[str, object]) -> _ResidentCommitAdmissionGrant:
        caller = sys._getframe(1)
        if caller.f_code is not type(self).prepare_transaction.__code__:
            raise RuntimeError("resident_commit_admission_issuer_unavailable")
        authority_digest = _canonical_digest(authority)
        issuance_digest = _canonical_digest(
            {
                "authority_digest": authority_digest,
                "generation_owner_ref": self._generation_owner_ref,
                "schema": "aware.repository.commit-admission-issuance.v1",
            }
        )
        grant = object.__new__(_ResidentCommitAdmissionGrant)
        with _RESIDENT_PROVIDER_LOCK:
            self._grants[grant] = _ResidentGrantRecord(
                issuance_digest=issuance_digest,
                provider_owner=self._owner,
                authority_digest=authority_digest,
            )
        return grant

    def _consume(
        self,
        grant: object,
        *,
        authority: dict[str, object],
        journal_issuance_digest: str,
    ) -> None:
        caller = sys._getframe(1)
        if caller.f_code is not type(self).prepare_transaction.__code__:
            raise RuntimeError("resident_commit_admission_issuer_unavailable")
        if type(grant) is not _ResidentCommitAdmissionGrant:
            raise TypeError("resident_commit_admission_grant_invalid")
        with _RESIDENT_PROVIDER_LOCK:
            record = self._grants.get(grant)
            if (
                record is None
                or record.provider_owner is not self._owner
                or record.consumed
                or record.authority_digest != _canonical_digest(authority)
                or record.issuance_digest != journal_issuance_digest
            ):
                raise RuntimeError("resident_commit_admission_not_live")
            record.consumed = True

    def prepare_transaction(
        self,
        *,
        authority: dict[str, object],
        journal_name: str,
        journal_body: dict[str, object],
    ) -> None:
        self._require_transaction_caller()
        if (
            not journal_name.endswith(".json")
            or "/" in journal_name
            or journal_name in {".", ".."}
        ):
            raise ValueError("resident_commit_admission_journal_name_invalid")
        path = self._journal_root / journal_name
        retained = _read_resident_journal(path)
        if retained is not None:
            comparable = dict(retained)
            issuance = comparable.pop("grant_issuance_digest", None)
            if comparable != journal_body or not _is_sha256_digest(issuance):
                raise RuntimeError("resident_commit_admission_journal_collision")
            return
        grant = self._issue(authority)
        record = self._grants.get(grant)
        if record is None:
            raise RuntimeError("resident_commit_admission_not_live")
        journal = {**journal_body, "grant_issuance_digest": record.issuance_digest}
        _write_no_replace(path, _canonical_bytes(journal))
        if _read_resident_journal(path) != journal:
            raise RuntimeError("resident_commit_admission_journal_reread_mismatch")
        self._consume(
            grant,
            authority=authority,
            journal_issuance_digest=record.issuance_digest,
        )

    def terminalize_transaction(
        self,
        *,
        journal_name: str,
        terminal_body: dict[str, object],
    ) -> None:
        self._require_transaction_caller()
        journal_path = self._journal_root / journal_name
        journal = _read_resident_journal(journal_path)
        if journal is None:
            raise RuntimeError("resident_commit_admission_journal_missing")
        completed = {
            **terminal_body,
            "journal_digest": "sha256:"
            + hashlib.sha256(journal_path.read_bytes()).hexdigest(),
        }
        _write_no_replace(
            journal_path.with_suffix(".complete"),
            _canonical_bytes(completed),
            allow_identical=True,
        )

    @staticmethod
    def _require_transaction_caller() -> None:
        caller = sys._getframe(2)
        if (
            caller.f_globals is not globals()
            or caller.f_code is not _publish_resident_admitted_transaction.__code__
        ):
            raise RuntimeError("resident_commit_admission_issuer_unavailable")

    def close(self) -> None:
        with _RESIDENT_PROVIDER_LOCK:
            self._grants.clear()
            _RESIDENT_PROVIDER_OWNERS.discard(self._generation_owner_ref)


def _take_resident_repository_commit_provider(
    *, generation_owner_ref: str, journal_root: Path
) -> _ResidentRepositoryCommitProvider:
    """Consume the resident issuer only from the real generation bootstrap."""

    caller = sys._getframe(1)
    bootstrap = sys.modules.get(
        "aware_local_dev_service.process_generation_composition"
    )
    function = getattr(bootstrap, "build_development_local_service_generation", None)
    if (
        bootstrap is None
        or caller.f_globals is not vars(bootstrap)
        or getattr(function, "__code__", None) is not caller.f_code
        or generation_owner_ref in _RESIDENT_PROVIDER_OWNERS
    ):
        raise RuntimeError("resident_commit_admission_issuer_unavailable")
    _RESIDENT_PROVIDER_OWNERS.add(generation_owner_ref)
    return _ResidentRepositoryCommitProvider(
        _RESIDENT_PROVIDER_TOKEN, generation_owner_ref, journal_root
    )


@dataclass(frozen=True)
class _RepositoryGitPaths:
    git_dir: Path
    common_dir: Path
    index_path: Path


@dataclass
class _RepositoryIndexTransaction:
    repo_root: Path
    git_dir: Path
    common_dir: Path
    index_path: Path
    enabled: bool
    staged_paths: tuple[str, ...] = ()
    restored: bool | None = None
    transaction_index_path: Path | None = None
    shared_index_unchanged: bool | None = None
    projection_applied: bool = False
    projection_error: str | None = None
    expected_head: str | None = None
    candidate_commit: str | None = None
    updated_reference: str | None = None
    reference_update: Literal["not_run", "cas_applied", "cas_failed"] = "not_run"
    journal_path: Path | None = None
    repository_admission_ref: str | None = None
    repository_admission_evidence_digest: str | None = None
    _existed: bool = False
    _contents: bytes | None = None
    _mode: int | None = None

    def __enter__(self) -> Self:
        if not self.enabled:
            return self
        self._existed = self.index_path.exists()
        if self._existed:
            details = self.index_path.lstat()
            if self.index_path.is_symlink() or not self.index_path.is_file():
                raise _RepositoryWritePreflightError(
                    f"repository_index_invalid:{self.index_path}"
                )
            self._contents = self.index_path.read_bytes()
            self._mode = details.st_mode & 0o7777
        transaction_root = self.git_dir / "aware-transactions"
        transaction_root.mkdir(parents=True, exist_ok=True)
        _recover_interrupted_reference_transactions(
            repo_root=self.repo_root,
            git_dir=self.git_dir,
            common_dir=self.common_dir,
        )
        for stale_path in transaction_root.glob("repository-index-*.tmp"):
            if stale_path.is_symlink() or not stale_path.is_file():
                raise _RepositoryWritePreflightError(
                    f"repository_transaction_index_invalid:{stale_path}"
                )
            stale_path.unlink()
        descriptor, raw_path = tempfile.mkstemp(
            prefix="repository-index-", suffix=".tmp", dir=transaction_root
        )
        os.close(descriptor)
        self.transaction_index_path = Path(raw_path)
        self.transaction_index_path.unlink()
        return self

    def record_staged_paths(self, paths: tuple[str, ...]) -> None:
        self.staged_paths = paths

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        if not self.enabled:
            return False
        try:
            if self.transaction_index_path is not None:
                self.transaction_index_path.unlink(missing_ok=True)
            if self.journal_path is not None:
                self.journal_path.unlink(missing_ok=True)
            if self.projection_applied:
                self.shared_index_unchanged = False
            elif self._existed:
                assert self._contents is not None
                self.shared_index_unchanged = (
                    self.index_path.exists()
                    and self.index_path.read_bytes() == self._contents
                )
            else:
                self.shared_index_unchanged = not self.index_path.exists()
            self.restored = (
                self.shared_index_unchanged if exc_type is not None else None
            )
        except OSError as cleanup_error:
            self.restored = False
            raise _RepositoryIndexRestoreError(
                f"repository_transaction_cleanup_failed:{cleanup_error}"
            ) from exc
        if exc_type is not None and self.shared_index_unchanged is not True:
            raise _RepositoryIndexRestoreError(
                f"repository_shared_index_changed_before_reference_cas:{self.index_path}"
            ) from exc
        return False

    def git_environment(self) -> dict[str, str] | None:
        if not self.enabled:
            return None
        assert self.transaction_index_path is not None
        return {"GIT_INDEX_FILE": self.transaction_index_path.as_posix()}

    def record_reference_cas_journal(self) -> None:
        assert self.updated_reference is not None
        assert self.candidate_commit is not None
        journal_root = self.common_dir / "aware/transactions"
        journal_root.mkdir(parents=True, exist_ok=True)
        token = f"{os.getpid()}-{time.monotonic_ns()}"
        self.journal_path = journal_root / f"repository-reference-{token}.json"
        reference_lock = _reference_lock_path(
            git_dir=self.git_dir,
            common_dir=self.common_dir,
            reference=self.updated_reference,
        )
        payload = {
            "candidate_commit": self.candidate_commit,
            "expected_head": self.expected_head,
            "index_path": (
                self.transaction_index_path.as_posix()
                if self.transaction_index_path is not None
                else None
            ),
            "pid": os.getpid(),
            "reference": self.updated_reference,
            "reference_lock_path": reference_lock.as_posix(),
            "symbolic_head_lock_path": (
                (self.git_dir / "HEAD.lock").as_posix()
                if self.updated_reference != "HEAD"
                else None
            ),
            "schema_version": "aware.repository-reference-transaction.v1",
        }
        with self.journal_path.open("x", encoding="utf-8") as journal_file:
            journal_file.write(json.dumps(payload, sort_keys=True) + "\n")
            journal_file.flush()
            os.fsync(journal_file.fileno())

    def clear_reference_cas_journal(self) -> None:
        if self.journal_path is not None:
            self.journal_path.unlink(missing_ok=True)
            self.journal_path = None


class _GitRunnerProtocol(Protocol):
    def run(self, *, args: tuple[str, ...], cwd: Path) -> _GitCommandResult: ...


class _SubprocessGitRunner:
    def run(self, *, args: tuple[str, ...], cwd: Path) -> _GitCommandResult:
        completed = subprocess.run(
            list(args),
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        return _GitCommandResult(
            returncode=int(completed.returncode),
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
        )

    def run_with_environment(
        self,
        *,
        args: tuple[str, ...],
        cwd: Path,
        environment: dict[str, str],
    ) -> _GitCommandResult:
        completed = subprocess.run(
            list(args),
            cwd=cwd,
            env={**os.environ, **environment},
            capture_output=True,
            text=True,
            check=False,
        )
        return _GitCommandResult(
            returncode=int(completed.returncode),
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
        )


def run_workspace_commit(
    *,
    options: WorkspaceCommitOptions,
    git_runner: _GitRunnerProtocol | None = None,
) -> WorkspaceCommitOutcome:
    """Run local git commit flow with deterministic issue/ownership guardrails."""

    repo_root = Path(options.repo_root).expanduser().resolve()
    report = WorkspaceCommitReport(
        repo_root=repo_root.as_posix(),
        issue_path=str(options.issue_path),
        owner_id=str(options.owner_id) if options.owner_id else None,
        dry_run=bool(options.dry_run),
        status="failed",
    )

    transaction: _RepositoryIndexTransaction | None = None
    try:
        _validate_repo_root(repo_root=repo_root)
        owner_id = _resolve_owner_id(raw_owner_id=options.owner_id)
        issue_path = _resolve_issue_path(
            repo_root=repo_root, raw_issue_path=options.issue_path
        )
        if options.expected_issue_source_sha256 is not None:
            expected_issue_source_sha256 = _normalize_source_digest(
                options.expected_issue_source_sha256,
                field="expected_issue_source_sha256",
            )
            observed_issue_source_sha256 = (
                "sha256:" + hashlib.sha256(issue_path.read_bytes()).hexdigest()
            )
            if observed_issue_source_sha256 != expected_issue_source_sha256:
                raise ValueError(
                    "issue_source_digest_stale:"
                    f"expected={expected_issue_source_sha256}:"
                    f"actual={observed_issue_source_sha256}"
                )
        if options.issue_metadata is None:
            issue = _parse_issue_metadata(issue_path=issue_path, repo_root=repo_root)
        else:
            issue = _issue_metadata_from_override(
                issue_path=issue_path,
                repo_root=repo_root,
                override=options.issue_metadata,
            )
        requested_paths = _resolve_requested_paths(
            repo_root=repo_root,
            raw_paths=tuple(options.target_paths),
        )
        _validate_issue_and_paths(
            issue=issue,
            owner_id=owner_id,
            requested_paths=requested_paths,
        )

        report.owner_id = owner_id
        report.issue_path = issue.issue_path
        report.issue_tag = issue.issue_tag
        report.issue_owner = issue.issue_owner
        report.issue_status = issue.issue_status
        report.ownership_scope = list(issue.ownership_scope)
        report.requested_paths = list(requested_paths)

        runner: _GitRunnerProtocol = git_runner or _SubprocessGitRunner()
        if options.reconcile_commit is not None:
            return _run_issue_index_reconciliation(
                repo_root=repo_root, runner=runner, report=report, issue=issue,
                requested_paths=requested_paths, owner_id=owner_id,
                publication_commit=options.reconcile_commit, dry_run=options.dry_run,
            )
        with _git_mutation_lock(
            repo_root=repo_root,
            owner_id=owner_id,
            issue_tag=issue.issue_tag,
            command_summary=(
                "aware-cli commit --dry-run" if options.dry_run else "aware-cli commit"
            ),
        ):
            if not options.dry_run:
                transaction = _prepare_repository_index_transaction(
                    repo_root=repo_root,
                    runner=runner,
                    report=report,
                )
            active_transaction = transaction or _RepositoryIndexTransaction(
                repo_root=repo_root,
                git_dir=repo_root / ".git",
                common_dir=repo_root / ".git",
                index_path=repo_root / ".git/index",
                enabled=False,
            )
            staged_paths: tuple[str, ...] = ()
            command_log: list[tuple[str, ...]] = []
            with active_transaction:
                staged_paths, command_log = _run_commit_flow(
                    runner=runner,
                    repo_root=repo_root,
                    issue=issue,
                    requested_paths=requested_paths,
                    message=str(options.message),
                    owner_id=owner_id,
                    dry_run=bool(options.dry_run),
                    allow_empty=bool(options.allow_empty),
                    transaction=active_transaction,
                )
            report.command_log = [list(entry) for entry in command_log]
            report.staged_paths = list(staged_paths)
            if options.dry_run:
                report.status = "planned"
                report.commit_message = _compose_commit_message(
                    message=str(options.message),
                    issue=issue,
                    owner_id=owner_id,
                    requested_paths=requested_paths,
                )
            else:
                report.status = "ok"
                report.commit_hash = active_transaction.candidate_commit or _extract_head_commit_hash(
                    runner=runner, repo_root=repo_root, command_log=command_log,
                )
                report.commit_message = _compose_commit_message(
                    message=str(options.message),
                    issue=issue,
                    owner_id=owner_id,
                    requested_paths=requested_paths,
                )
    except _GitCommandError as exc:
        report.status = "failed"
        report.error = str(exc)
        report.command_log = [list(entry) for entry in exc.command_log]
    except _GitMutationLockTimeoutError as exc:
        report.status = "failed"
        report.error = str(exc)
    except Exception as exc:  # noqa: BLE001 - command boundary returns typed failure
        report.status = "failed"
        report.error = _compact_error(str(exc))

    _apply_index_transaction_report(report=report, transaction=transaction)

    return WorkspaceCommitOutcome(
        report=report,
        exit_code=0 if report.status in {"ok", "planned"} else 2,
    )


def _run_issue_index_reconciliation(
    *, repo_root: Path, runner: _GitRunnerProtocol, report: WorkspaceCommitReport,
    issue: _IssueMetadata, requested_paths: tuple[str, ...], owner_id: str,
    publication_commit: str, dry_run: bool,
) -> WorkspaceCommitOutcome:
    """Recover a published projection, not a new commit or worktree mutation."""
    command_log: list[tuple[str, ...]] = []
    transaction: _RepositoryIndexTransaction | None = None
    try:
        publication = _normalize_git_object_id(publication_commit, field="publication_commit")
        with _git_mutation_lock(
            repo_root=repo_root, owner_id=owner_id, issue_tag=issue.issue_tag,
            command_summary="aware-cli commit --reconcile-index",
        ):
            _require_git_repo(runner=runner, repo_root=repo_root, command_log=command_log)
            head = _repository_head(runner=runner, repo_root=repo_root, command_log=command_log)
            _run_git(
                runner=runner, repo_root=repo_root,
                args=("git", "merge-base", "--is-ancestor", publication, head),
                command_log=command_log,
            )
            body = _run_git(
                runner=runner, repo_root=repo_root,
                args=("git", "show", "-s", "--format=%B", publication),
                command_log=command_log,
            ).stdout
            if (
                _commit_trailer_values(body=body, trailer_name="Issue-Tag") != (issue.issue_tag,)
                or _commit_trailer_values(body=body, trailer_name="Issue-Path") != (issue.issue_path,)
            ):
                raise ValueError("index_reconciliation_publication_issue_mismatch")
            owned = _commit_trailer_values(body=body, trailer_name="Owned-Paths")
            if len(owned) != 1 or not set(requested_paths).issubset(owned[0].split(",")):
                raise ValueError("index_reconciliation_publication_scope_mismatch")
            git_paths = _resolve_repository_git_paths(repo_root=repo_root)
            reference = _run_git_optional(
                runner=runner, repo_root=repo_root,
                args=("git", "symbolic-ref", "-q", "HEAD"), command_log=command_log,
            )
            check = _RepositoryIndexTransaction(
                repo_root=repo_root, git_dir=git_paths.git_dir,
                common_dir=git_paths.common_dir, index_path=git_paths.index_path,
                enabled=False, expected_head=head,
                updated_reference=reference.stdout.strip() if reference.returncode == 0 else "HEAD",
            )
            for path in requested_paths:
                if _head_path_entry(
                    runner=runner, repo_root=repo_root, head=publication,
                    path=path, command_log=command_log,
                ) != _head_path_entry(
                    runner=runner, repo_root=repo_root, head=head,
                    path=path, command_log=command_log,
                ):
                    raise ValueError(f"index_reconciliation_published_path_advanced:{path}")
                if not _shared_index_matches_expected_paths(
                    runner=runner, repo_root=repo_root, expected_head=head,
                    requested_paths=(path,), command_log=command_log,
                ) and _projection_debt_preimage(
                    runner=runner, repo_root=repo_root, transaction=check,
                    path=path, command_log=command_log,
                ) is None:
                    raise ValueError(f"index_reconciliation_foreign_staging:{path}")
            report.commit_hash = publication
            if dry_run:
                report.status = "planned"
            else:
                transaction = _recover_replayed_index_projection(
                    runner=runner, repo_root=repo_root, report=report,
                    requested_paths=requested_paths, command_log=command_log,
                    expected_head=head,
                )
                transaction.candidate_commit = publication
                _apply_index_transaction_report(report=report, transaction=transaction)
                report.status = "ok" if transaction.projection_applied else "failed"
                report.error = transaction.projection_error
    except Exception as exc:  # noqa: BLE001 - governed recovery fails closed
        report.status = "failed"
        report.error = _compact_error(str(exc))
    report.command_log = [list(entry) for entry in command_log]
    return WorkspaceCommitOutcome(
        report=report, exit_code=0 if report.status in {"ok", "planned"} else 2,
    )


def run_workspace_authorized_commit(
    *,
    options: WorkspaceAuthorizedCommitOptions,
    git_runner: _GitRunnerProtocol | None = None,
    _resident_provider: _ResidentRepositoryCommitProvider | None = None,
) -> WorkspaceCommitOutcome:
    """Run local git commit flow for already-authorized explicit paths."""

    repo_root = Path(options.repo_root).expanduser().resolve()
    report = WorkspaceCommitReport(
        repo_root=repo_root.as_posix(),
        owner_id=str(options.owner_id) if options.owner_id else None,
        dry_run=bool(options.dry_run),
        status="failed",
    )

    transaction: _RepositoryIndexTransaction | None = None
    try:
        _validate_repo_root(repo_root=repo_root)
        owner_id = _resolve_owner_id(raw_owner_id=options.owner_id)
        requested_paths = _resolve_requested_paths(
            repo_root=repo_root,
            raw_paths=tuple(options.target_paths),
        )
        normalized_message = _normalize_commit_message(str(options.message))
        idempotency_ref = _normalize_idempotency_ref(options.idempotency_ref)
        authorized_path_states = _normalize_authorized_path_states(
            repo_root=repo_root,
            requested_paths=requested_paths,
            authorized_path_states=options.authorized_path_states,
        )
        request_fingerprint = (
            _authorized_commit_request_fingerprint(
                repo_root=repo_root,
                owner_id=owner_id,
                requested_paths=requested_paths,
                message=normalized_message,
                allow_empty=bool(options.allow_empty),
                authorized_path_states=authorized_path_states,
            )
            if idempotency_ref is not None
            else None
        )
        commit_message = _compose_authorized_commit_message(
            message=normalized_message,
            idempotency_ref=idempotency_ref,
            request_fingerprint=request_fingerprint,
        )

        report.owner_id = owner_id
        report.requested_paths = list(requested_paths)
        report.idempotency_ref = idempotency_ref
        report.request_fingerprint = request_fingerprint

        runner: _GitRunnerProtocol = git_runner or _SubprocessGitRunner()
        with _git_mutation_lock(
            repo_root=repo_root,
            owner_id=owner_id,
            issue_tag=None,
            command_summary=(
                "aware-cli authorized commit --dry-run"
                if options.dry_run
                else "aware-cli authorized commit"
            ),
        ):
            replay: _IdempotentCommit | None = None
            initial_command_log: list[tuple[str, ...]] | None = None
            if idempotency_ref is not None and not options.dry_run:
                initial_command_log = []
                _require_git_repo(
                    runner=runner,
                    repo_root=repo_root,
                    command_log=initial_command_log,
                )
                try:
                    replay = _resolve_idempotent_authorized_commit(
                        runner=runner,
                        repo_root=repo_root,
                        idempotency_ref=idempotency_ref,
                        request_fingerprint=str(request_fingerprint),
                        requested_paths=requested_paths,
                        command_log=initial_command_log,
                    )
                finally:
                    report.command_log = [list(entry) for entry in initial_command_log]
            staged_paths: tuple[str, ...] = ()
            command_log: list[tuple[str, ...]] = initial_command_log or []
            if replay is None:
                _validate_authorized_path_states(
                    repo_root=repo_root,
                    requested_paths=requested_paths,
                    authorized_path_states=authorized_path_states,
                )
                if not options.dry_run:
                    transaction = _prepare_repository_index_transaction(
                        repo_root=repo_root,
                        runner=runner,
                        report=report,
                    )
                active_transaction = transaction or _RepositoryIndexTransaction(
                    repo_root=repo_root,
                    git_dir=repo_root / ".git",
                    common_dir=repo_root / ".git",
                    index_path=repo_root / ".git/index",
                    enabled=False,
                )
                with active_transaction:
                    staged_paths, command_log = _run_authorized_commit_flow(
                        runner=runner,
                        repo_root=repo_root,
                        requested_paths=requested_paths,
                        commit_message=commit_message,
                        dry_run=bool(options.dry_run),
                        allow_empty=bool(options.allow_empty),
                        command_log=initial_command_log,
                        repository_validated=initial_command_log is not None,
                        transaction=active_transaction,
                        resident_provider=_resident_provider,
                        resident_evidence=options.resident_admission_evidence,
                    )
            else:
                staged_paths = replay.changed_paths
                command_log = initial_command_log or []
                transaction = _recover_replayed_index_projection(
                    runner=runner, repo_root=repo_root, report=report,
                    requested_paths=requested_paths, command_log=command_log,
                )
            report.command_log = [list(entry) for entry in command_log]
            report.staged_paths = list(staged_paths)
            report.commit_message = commit_message
            if options.dry_run:
                report.status = "planned"
            elif replay is not None:
                report.status = "ok"
                report.commit_hash = replay.commit_hash
                report.idempotent_replay = True
            else:
                report.status = "ok"
                report.commit_hash = _extract_head_commit_hash(
                    runner=runner,
                    repo_root=repo_root,
                    command_log=command_log,
                )
    except _GitCommandError as exc:
        report.status = "failed"
        report.error = str(exc)
        report.command_log = [list(entry) for entry in exc.command_log]
    except _GitMutationLockTimeoutError as exc:
        report.status = "failed"
        report.error = str(exc)
    except Exception as exc:  # noqa: BLE001 - command boundary returns typed failure
        report.status = "failed"
        report.error = _compact_error(str(exc))

    _apply_index_transaction_report(report=report, transaction=transaction)

    return WorkspaceCommitOutcome(
        report=report,
        exit_code=0 if report.status in {"ok", "planned"} else 2,
    )


def run_workspace_content_commit(
    *,
    options: WorkspaceContentCommitOptions,
    git_runner: _GitRunnerProtocol | None = None,
) -> WorkspaceCommitOutcome:
    """Publish supplied exact path postimages without reading worktree bytes."""

    repo_root = Path(options.repo_root).expanduser().resolve()
    report = WorkspaceCommitReport(
        repo_root=repo_root.as_posix(),
        issue_path=str(options.issue_path),
        owner_id=str(options.owner_id) if options.owner_id else None,
        dry_run=bool(options.dry_run),
        status="failed",
    )
    transaction: _RepositoryIndexTransaction | None = None
    try:
        _validate_repo_root(repo_root=repo_root)
        owner_id = _resolve_owner_id(raw_owner_id=options.owner_id)
        issue_relpath = _resolve_requested_paths(
            repo_root=repo_root,
            raw_paths=(options.issue_path,),
        )[0]
        path_contents = _normalize_supplied_path_contents(
            repo_root=repo_root,
            path_contents=options.path_contents,
        )
        requested_paths = tuple(item.path for item in path_contents)
        expected_head = _normalize_git_object_id(
            options.expected_head,
            field="expected_head",
        )
        expected_issue_blob_oid = (
            _normalize_git_object_id(
                options.expected_issue_blob_oid,
                field="expected_issue_blob_oid",
            )
            if options.expected_issue_blob_oid is not None
            else None
        )
        semantic_intent_digest = _normalize_semantic_intent_digest(
            options.semantic_intent_digest
        )
        idempotency_ref = _normalize_idempotency_ref(options.idempotency_ref)
        assert idempotency_ref is not None
        normalized_message = _normalize_commit_message(options.message)
        expected_repository_ref = _normalize_repository_ref(
            options.expected_repository_ref
        )
        request_fingerprint = _content_commit_request_fingerprint(
            repo_root=repo_root,
            issue_relpath=issue_relpath,
            owner_id=owner_id,
            requested_paths=requested_paths,
            message=normalized_message,
            semantic_intent_digest=semantic_intent_digest,
            repository_ref=expected_repository_ref,
        )

        report.owner_id = owner_id
        report.requested_paths = list(requested_paths)
        report.idempotency_ref = idempotency_ref
        report.request_fingerprint = request_fingerprint
        report.expected_head = expected_head
        report.updated_reference = expected_repository_ref
        runner: _GitRunnerProtocol = git_runner or _SubprocessGitRunner()
        command_log: list[tuple[str, ...]] = []
        replay: _IdempotentCommit | None = None
        with _git_mutation_lock(
            repo_root=repo_root,
            owner_id=owner_id,
            issue_tag=None,
            command_summary="aware content-supplied repository commit",
        ):
            _require_git_repo(
                runner=runner,
                repo_root=repo_root,
                command_log=command_log,
            )
            observed_repository_ref = _repository_symbolic_ref(
                runner=runner,
                repo_root=repo_root,
                command_log=command_log,
            )
            if observed_repository_ref != expected_repository_ref:
                raise ValueError(
                    "repository_ref_stale:"
                    f"expected={expected_repository_ref}:"
                    f"actual={observed_repository_ref}"
                )
            observed_head = _repository_head(
                runner=runner,
                repo_root=repo_root,
                command_log=command_log,
            )
            if not options.dry_run:
                replay = _resolve_idempotent_authorized_commit(
                    runner=runner,
                    repo_root=repo_root,
                    idempotency_ref=idempotency_ref,
                    request_fingerprint=request_fingerprint,
                    requested_paths=requested_paths,
                    command_log=command_log,
                )
                if replay is not None and not _repository_is_ancestor(
                    runner=runner,
                    repo_root=repo_root,
                    ancestor=replay.commit_hash,
                    descendant=observed_head,
                    command_log=command_log,
                ):
                    raise ValueError(
                        "idempotent_commit_not_reachable_from_repository_ref:"
                        f"commit={replay.commit_hash}:ref={expected_repository_ref}"
                    )
            issue_entry = _head_path_entry(
                runner=runner,
                repo_root=repo_root,
                head=expected_head,
                path=issue_relpath,
                command_log=command_log,
            )
            if issue_entry is None:
                raise ValueError(f"committed_issue_missing:path={issue_relpath}")
            committed_issue_blob_oid = issue_entry[1]
            report.committed_issue_blob_oid = committed_issue_blob_oid
            if (
                expected_issue_blob_oid is not None
                and committed_issue_blob_oid != expected_issue_blob_oid
            ):
                raise ValueError(
                    "committed_issue_revision_stale:"
                    f"expected={expected_issue_blob_oid}:"
                    f"actual={committed_issue_blob_oid}"
                )
            issue_text = _head_path_text(
                runner=runner,
                repo_root=repo_root,
                head=expected_head,
                path=issue_relpath,
                command_log=command_log,
            )
            issue = _parse_issue_metadata_text(
                text=issue_text,
                issue_relpath=issue_relpath,
            )
            _validate_issue_and_paths(
                issue=issue,
                owner_id=owner_id,
                requested_paths=requested_paths,
            )
            report.issue_path = issue.issue_path
            report.issue_tag = issue.issue_tag
            report.issue_owner = issue.issue_owner
            report.issue_status = issue.issue_status
            report.ownership_scope = list(issue.ownership_scope)
            commit_message = _compose_authorized_commit_message(
                message=_compose_commit_message(
                    message=normalized_message,
                    issue=issue,
                    owner_id=owner_id,
                    requested_paths=requested_paths,
                ),
                idempotency_ref=idempotency_ref,
                request_fingerprint=request_fingerprint,
            )
            report.commit_message = commit_message
            if replay is None:
                if observed_head != expected_head:
                    raise ValueError(
                        "repository_head_stale:"
                        f"expected={expected_head}:actual={observed_head}"
                    )
                _validate_supplied_head_preimages(
                    runner=runner,
                    repo_root=repo_root,
                    head=expected_head,
                    path_contents=path_contents,
                    command_log=command_log,
                )
                if options.dry_run:
                    report.status = "planned"
                    report.staged_paths = list(requested_paths)
                else:
                    transaction = _prepare_repository_index_transaction(
                        repo_root=repo_root,
                        runner=runner,
                        report=report,
                    )
                    with transaction:
                        _initialize_isolated_index(
                            runner=runner,
                            repo_root=repo_root,
                            transaction=transaction,
                            command_log=command_log,
                        )
                        if transaction.expected_head != expected_head:
                            raise ValueError("repository_head_changed_before_stage")
                        if transaction.updated_reference != expected_repository_ref:
                            raise ValueError("repository_ref_changed_before_stage")
                        staged_paths = _stage_supplied_path_contents(
                            runner=runner,
                            repo_root=repo_root,
                            path_contents=path_contents,
                            transaction=transaction,
                            command_log=command_log,
                        )
                        transaction.record_staged_paths(staged_paths)
                        _publish_staged_transaction(
                            runner=runner,
                            repo_root=repo_root,
                            requested_paths=requested_paths,
                            commit_message=commit_message,
                            allow_empty=False,
                            transaction=transaction,
                            command_log=command_log,
                        )
                    report.status = "ok"
                    report.staged_paths = list(staged_paths)
                    report.commit_hash = transaction.candidate_commit
            else:
                report.status = "ok"
                report.commit_hash = replay.commit_hash
                report.candidate_commit = replay.commit_hash
                report.reference_update = "cas_applied"
                report.staged_paths = list(replay.changed_paths)
                report.idempotent_replay = True
                transaction = _recover_replayed_index_projection(
                    runner=runner, repo_root=repo_root, report=report,
                    requested_paths=requested_paths, command_log=command_log,
                )
        report.command_log = [list(entry) for entry in command_log]
    except _GitCommandError as exc:
        report.error = str(exc)
        report.command_log = [list(entry) for entry in exc.command_log]
    except Exception as exc:  # noqa: BLE001 - command boundary returns typed failure
        report.error = _compact_error(str(exc))

    _apply_index_transaction_report(report=report, transaction=transaction)
    return WorkspaceCommitOutcome(
        report=report,
        exit_code=0 if report.status in {"ok", "planned"} else 2,
    )


def print_workspace_commit_report(*, report: WorkspaceCommitReport) -> None:
    print(f"Workspace commit: {report.status.upper()}")
    print(f"Repo root: {report.repo_root}")
    if report.issue_path:
        print(f"Issue: {report.issue_path}")
    if report.issue_tag:
        print(f"Issue tag: {report.issue_tag}")
    if report.owner_id:
        print(f"Owner: {report.owner_id}")
    if report.requested_paths:
        print("Requested paths:")
        for path in report.requested_paths:
            print(f"- {path}")
    if report.staged_paths:
        print("Staged paths:")
        for path in report.staged_paths:
            print(f"- {path}")
    if report.commit_hash:
        print(f"Commit hash: {report.commit_hash}")
    if report.error:
        print("Error:")
        print(report.error)
    if report.index_reconciliation_pending:
        print(f"Shared index: PENDING ({report.shared_index_projection_error})")


def print_workspace_commit_result(*, payload: dict[str, object]) -> None:
    report = WorkspaceCommitReport.model_validate(payload)
    print_workspace_commit_report(report=report)


def _validate_repo_root(*, repo_root: Path) -> None:
    if not repo_root.exists():
        raise FileNotFoundError(f"Repo root does not exist: {repo_root}")
    if not repo_root.is_dir():
        raise NotADirectoryError(f"Repo root must be a directory: {repo_root}")


def _prepare_repository_index_transaction(
    *,
    repo_root: Path,
    runner: _GitRunnerProtocol,
    report: WorkspaceCommitReport,
) -> _RepositoryIndexTransaction:
    enabled = isinstance(runner, _SubprocessGitRunner)
    git_paths = _RepositoryGitPaths(
        git_dir=repo_root / ".git",
        common_dir=repo_root / ".git",
        index_path=repo_root / ".git/index",
    )
    if enabled:
        try:
            git_paths = _resolve_repository_git_paths(repo_root=repo_root)
            _preflight_repository_write_access(
                repo_root=repo_root,
                git_paths=git_paths,
            )
        except (OSError, _RepositoryWritePreflightError):
            report.repository_write_preflight = "failed"
            raise
        report.repository_write_preflight = "passed"
        report.transaction_mode = "isolated_index_atomic_ref_v1"
    else:
        report.transaction_mode = "shared_index_snapshot_v0"
    return _RepositoryIndexTransaction(
        repo_root=repo_root,
        git_dir=git_paths.git_dir,
        common_dir=git_paths.common_dir,
        index_path=git_paths.index_path,
        enabled=enabled,
    )


def _apply_index_transaction_report(
    *,
    report: WorkspaceCommitReport,
    transaction: _RepositoryIndexTransaction | None,
) -> None:
    if transaction is None:
        return
    if report.status == "failed" and transaction.staged_paths:
        report.staged_paths = list(transaction.staged_paths)
    report.index_restored = transaction.restored
    if not report.idempotent_replay:
        report.expected_head = transaction.expected_head
        report.candidate_commit = transaction.candidate_commit
        report.updated_reference = transaction.updated_reference
        report.reference_update = transaction.reference_update
    report.shared_index_unchanged = transaction.shared_index_unchanged
    pending = transaction.projection_error is not None or (
        transaction.reference_update == "cas_applied" and not transaction.projection_applied
    )
    report.shared_index_projection = (
        "applied"
        if transaction.projection_applied
        else "failed"
        if pending
        else "not_run"
    )
    report.shared_index_projection_error = transaction.projection_error or (
        "post_publication_projection_interrupted" if pending else None
    )
    report.index_reconciliation_pending = pending
    if transaction.reference_update == "cas_applied" and report.commit_hash is None:
        report.commit_hash = transaction.candidate_commit
    if not report.idempotent_replay:
        report.repository_admission_ref = transaction.repository_admission_ref
        report.repository_admission_evidence_digest = (
            transaction.repository_admission_evidence_digest
        )


def _resolve_repository_git_paths(*, repo_root: Path) -> _RepositoryGitPaths:
    def resolve(*arguments: str) -> Path:
        completed = subprocess.run(
            ("git", "rev-parse", *arguments),
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0 or not completed.stdout.strip():
            raise _RepositoryWritePreflightError(
                "repository_git_path_unavailable:"
                f"{' '.join(arguments)}:{completed.stderr.strip()}"
            )
        candidate = Path(completed.stdout.strip())
        return (
            candidate if candidate.is_absolute() else repo_root / candidate
        ).resolve()

    return _RepositoryGitPaths(
        git_dir=resolve("--absolute-git-dir"),
        common_dir=resolve("--git-common-dir"),
        index_path=resolve("--git-path", "index"),
    )


def _preflight_repository_write_access(
    *, repo_root: Path, git_paths: _RepositoryGitPaths
) -> None:
    git_root = git_paths.git_dir
    common_root = git_paths.common_dir
    if git_root.is_symlink() or not git_root.is_dir():
        raise _RepositoryWritePreflightError(
            f"repository_git_directory_invalid:{git_root}"
        )
    if common_root.is_symlink() or not common_root.is_dir():
        raise _RepositoryWritePreflightError(
            f"repository_git_common_directory_invalid:{common_root}"
        )

    head_path = git_root / "HEAD"
    try:
        head_value = head_path.read_text(encoding="utf-8").strip()
    except OSError as error:
        raise _RepositoryWritePreflightError(
            f"repository_head_unreadable:{head_path}:{error}"
        ) from error
    head_log = git_root / "logs/HEAD"
    index_path = git_paths.index_path
    objects_root = common_root / "objects"

    reference_path: Path | None
    reference_log: Path | None
    if head_value.startswith("ref: refs/"):
        reference_relative = Path(head_value.removeprefix("ref: "))
        if reference_relative.is_absolute() or ".." in reference_relative.parts:
            raise _RepositoryWritePreflightError(
                f"repository_head_reference_invalid:{head_value}"
            )
        reference_path = common_root / reference_relative
        reference_log = common_root / "logs" / reference_relative
    elif re.fullmatch(r"[0-9a-fA-F]{40,64}", head_value):
        reference_path = head_path
        reference_log = None
    else:
        raise _RepositoryWritePreflightError(
            f"repository_head_value_invalid:{head_value}"
        )

    required_directories = {
        git_root,
        common_root,
        objects_root,
        _nearest_existing_directory(head_log.parent),
        index_path.parent,
    }
    required_directories.add(_nearest_existing_directory(reference_path.parent))
    if reference_log is not None:
        required_directories.add(_nearest_existing_directory(reference_log.parent))
    if objects_root.is_dir():
        required_directories.update(
            path
            for path in objects_root.iterdir()
            if path.is_dir() and not path.is_symlink()
        )
    required_files = {
        path
        for path in (index_path, reference_path, head_log, reference_log)
        if path is not None and path.exists()
    }

    failures: list[str] = []
    for path in sorted(required_directories, key=lambda item: item.as_posix()):
        if path.is_symlink() or not path.is_dir():
            failures.append(f"directory_invalid:{path}")
            continue
        if not os.access(path, os.W_OK | os.X_OK, effective_ids=True):
            failures.append(f"directory_not_writable:{path}")
    for path in sorted(required_files, key=lambda item: item.as_posix()):
        if path.is_symlink() or not path.is_file():
            failures.append(f"file_invalid:{path}")
            continue
        if not os.access(path, os.W_OK, effective_ids=True):
            failures.append(f"file_not_writable:{path}")
    if failures:
        raise _RepositoryWritePreflightError(
            f"repository_metadata_not_writable:uid={os.geteuid()}:" + ";".join(failures)
        )


def _nearest_existing_directory(path: Path) -> Path:
    candidate = path
    while not candidate.exists() and candidate != candidate.parent:
        candidate = candidate.parent
    return candidate


def _reference_lock_path(*, git_dir: Path, common_dir: Path, reference: str) -> Path:
    if reference == "HEAD":
        return git_dir / "HEAD.lock"
    relative = Path(reference)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or not reference.startswith("refs/heads/")
    ):
        raise _RepositoryWritePreflightError(
            f"repository_reference_lock_path_invalid:{reference}"
        )
    return common_dir / f"{reference}.lock"


def _recover_interrupted_reference_transactions(
    *, repo_root: Path, git_dir: Path, common_dir: Path
) -> None:
    journal_root = common_dir / "aware/transactions"
    if not journal_root.exists():
        return
    if journal_root.is_symlink() or not journal_root.is_dir():
        raise _RepositoryWritePreflightError(
            f"repository_transaction_journal_root_invalid:{journal_root}"
        )
    for journal_path in sorted(journal_root.glob("repository-reference-*.json")):
        if journal_path.is_symlink() or not journal_path.is_file():
            raise _RepositoryWritePreflightError(
                f"repository_transaction_journal_invalid:{journal_path}"
            )
        try:
            payload = json.loads(journal_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise _RepositoryWritePreflightError(
                f"repository_transaction_journal_unreadable:{journal_path}:{error}"
            ) from error
        if not isinstance(payload, dict) or payload.get("schema_version") != (
            "aware.repository-reference-transaction.v1"
        ):
            raise _RepositoryWritePreflightError(
                f"repository_transaction_journal_schema_invalid:{journal_path}"
            )
        pid = payload.get("pid")
        reference = payload.get("reference")
        expected_head = payload.get("expected_head")
        candidate_commit = payload.get("candidate_commit")
        lock_value = payload.get("reference_lock_path")
        symbolic_head_lock_value = payload.get("symbolic_head_lock_path")
        if (
            not isinstance(pid, int)
            or pid <= 0
            or not isinstance(reference, str)
            or (expected_head is not None and not isinstance(expected_head, str))
            or not isinstance(candidate_commit, str)
            or not re.fullmatch(r"[0-9a-f]{40,64}", candidate_commit)
            or not isinstance(lock_value, str)
            or (
                symbolic_head_lock_value is not None
                and not isinstance(symbolic_head_lock_value, str)
            )
        ):
            raise _RepositoryWritePreflightError(
                f"repository_transaction_journal_fields_invalid:{journal_path}"
            )
        if _process_exists(pid):
            raise _RepositoryWritePreflightError(
                f"repository_transaction_owner_still_live:{journal_path}:pid={pid}"
            )
        expected_lock = _reference_lock_path(
            git_dir=git_dir,
            common_dir=common_dir,
            reference=reference,
        ).resolve()
        observed_lock = Path(lock_value).resolve()
        if observed_lock != expected_lock:
            raise _RepositoryWritePreflightError(
                f"repository_transaction_lock_binding_invalid:{journal_path}"
            )
        current = subprocess.run(
            ("git", "rev-parse", "--verify", reference),
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        current_head = current.stdout.strip() if current.returncode == 0 else None
        if current_head != expected_head:
            raise _RepositoryWritePreflightError(
                f"repository_transaction_reference_moved:{reference}:"
                f"expected={expected_head}:actual={current_head}"
            )
        if expected_lock.exists():
            if expected_lock.is_symlink() or not expected_lock.is_file():
                raise _RepositoryWritePreflightError(
                    f"repository_transaction_lock_invalid:{expected_lock}"
                )
            if expected_lock.read_text(encoding="ascii").strip() != candidate_commit:
                raise _RepositoryWritePreflightError(
                    f"repository_transaction_lock_content_conflict:{expected_lock}"
                )
            expected_lock.unlink()
        if symbolic_head_lock_value is not None:
            expected_head_lock = (git_dir / "HEAD.lock").resolve()
            observed_head_lock = Path(symbolic_head_lock_value).resolve()
            if observed_head_lock != expected_head_lock:
                raise _RepositoryWritePreflightError(
                    f"repository_transaction_head_lock_binding_invalid:{journal_path}"
                )
            if expected_head_lock.exists():
                if (
                    expected_head_lock.is_symlink()
                    or not expected_head_lock.is_file()
                    or expected_head_lock.stat().st_size != 0
                ):
                    raise _RepositoryWritePreflightError(
                        f"repository_transaction_head_lock_content_conflict:"
                        f"{expected_head_lock}"
                    )
                expected_head_lock.unlink()
        index_value = payload.get("index_path")
        if isinstance(index_value, str) and index_value:
            stale_index = Path(index_value).resolve()
            transaction_root = (git_dir / "aware-transactions").resolve()
            if stale_index.parent != transaction_root:
                raise _RepositoryWritePreflightError(
                    f"repository_transaction_index_binding_invalid:{stale_index}"
                )
            stale_index.unlink(missing_ok=True)
        journal_path.unlink()


def _process_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _normalize_provider_key(raw_value: str | None) -> str | None:
    candidate = re.sub(r"[^a-z0-9]+", "_", str(raw_value or "").strip().lower()).strip(
        "_"
    )
    return candidate or None


def _default_owner_id_from_environment() -> str | None:
    provider = _normalize_provider_key(os.environ.get("AWARE_INTERFACE_PROVIDER"))
    if provider is None and (os.environ.get("CODEX_THREAD_ID") or "").strip():
        provider = "codex"
    if provider is None:
        return None

    provider_session_id = (
        os.environ.get("AWARE_INTERFACE_PROVIDER_SESSION_ID") or ""
    ).strip()
    if not provider_session_id and provider == "codex":
        provider_session_id = (os.environ.get("CODEX_THREAD_ID") or "").strip()
    if not provider_session_id:
        return None
    return f"{provider}-{provider_session_id}"


def _resolve_owner_id(*, raw_owner_id: str | None) -> str:
    if raw_owner_id:
        candidate = str(raw_owner_id).strip()
    else:
        candidate = _default_owner_id_from_environment() or ""
        if not candidate:
            raise ValueError(
                "Missing owner identity: set "
                "`AWARE_INTERFACE_PROVIDER` + `AWARE_INTERFACE_PROVIDER_SESSION_ID`, "
                "or rely on `CODEX_THREAD_ID` for Codex, "
                "or pass `--owner-id <provider>-<provider_session_id>`."
            )
    if not _OWNER_ID_PATTERN.match(candidate):
        raise ValueError(
            f"Invalid owner identity format: {candidate!r}; "
            "expected `<provider>-<provider_session_id>`."
        )
    return candidate


def _resolve_issue_path(*, repo_root: Path, raw_issue_path: str) -> Path:
    value = str(raw_issue_path).strip()
    if not value:
        raise ValueError("--issue is required.")
    candidate = Path(value).expanduser()
    resolved = (
        candidate.resolve()
        if candidate.is_absolute()
        else (repo_root / candidate).resolve()
    )
    try:
        resolved.relative_to(repo_root)
    except Exception as exc:
        raise ValueError(f"Issue path escapes repo root: {resolved}") from exc
    if not resolved.exists():
        raise FileNotFoundError(f"Issue file not found: {resolved}")
    if not resolved.is_file():
        raise ValueError(f"Issue path must be a file: {resolved}")
    return resolved


def _parse_issue_metadata(*, issue_path: Path, repo_root: Path) -> _IssueMetadata:
    text = issue_path.read_text(encoding="utf-8")
    return _parse_issue_metadata_text(
        text=text,
        issue_relpath=issue_path.relative_to(repo_root).as_posix(),
    )


def _parse_issue_metadata_text(*, text: str, issue_relpath: str) -> _IssueMetadata:
    owner = ""
    status = ""
    tag = ""
    inline_scope: tuple[str, ...] = ()
    lines = text.splitlines()

    for line in lines:
        match = _HEADER_FIELD_PATTERN.match(line)
        if not match:
            continue
        key = match.group(1).strip()
        value = match.group(2).strip()
        normalized_key = key.lower()
        if normalized_key == "owner":
            owner = _normalize_header_value(value)
        elif normalized_key == "status":
            status = _normalize_header_value(value)
        elif normalized_key == "tag":
            tag = _normalize_header_value(value)
        elif normalized_key == _OWNERSHIP_HEADER.lower():
            inline_scope = _parse_scope_tokens(value)

    section_scope = _parse_scope_section(lines=tuple(lines))
    merged_scope = tuple(dict.fromkeys([*inline_scope, *section_scope]))
    normalized_scope = _normalize_scope_tokens(tokens=merged_scope)
    if not owner:
        raise ValueError(f"Issue missing Owner header: {issue_relpath}")
    if not status:
        raise ValueError(f"Issue missing Status header: {issue_relpath}")
    if not tag:
        raise ValueError(f"Issue missing Tag header: {issue_relpath}")
    if not normalized_scope:
        raise ValueError(
            "Issue missing ownership scope. Add `- Ownership Scope: ` with explicit repo-relative paths."
        )

    return _IssueMetadata(
        issue_path=issue_relpath,
        issue_tag=tag,
        issue_owner=owner,
        issue_status=status,
        ownership_scope=normalized_scope,
    )


def _issue_metadata_from_override(
    *,
    issue_path: Path,
    repo_root: Path,
    override: WorkspaceCommitIssueMetadata,
) -> _IssueMetadata:
    tag = _normalize_header_value(override.issue_tag)
    owner = _normalize_header_value(override.issue_owner)
    status = _normalize_header_value(override.issue_status)
    normalized_scope = _normalize_scope_tokens(tokens=tuple(override.ownership_scope))

    if not owner:
        raise ValueError("Canonical issue metadata missing issue_owner.")
    if not status:
        raise ValueError("Canonical issue metadata missing issue_status.")
    if not tag:
        raise ValueError("Canonical issue metadata missing issue_tag.")
    if not normalized_scope:
        raise ValueError("Canonical issue metadata missing ownership_scope.")

    return _IssueMetadata(
        issue_path=issue_path.relative_to(repo_root).as_posix(),
        issue_tag=tag,
        issue_owner=owner,
        issue_status=status,
        ownership_scope=normalized_scope,
    )


def _parse_scope_section(*, lines: tuple[str, ...]) -> tuple[str, ...]:
    in_scope = False
    collected: list[str] = []
    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()
        if stripped.startswith("## "):
            heading = stripped[3:].strip().lower()
            in_scope = heading == _OWNERSHIP_HEADER.lower()
            continue
        if not in_scope:
            continue
        if not stripped:
            continue
        if stripped.startswith("- "):
            value = stripped[2:].strip()
            normalized = _normalize_header_value(value)
            if normalized:
                collected.append(normalized)
            continue
        if stripped.startswith("## "):
            break
    return tuple(collected)


def _parse_scope_tokens(value: str) -> tuple[str, ...]:
    raw = _normalize_header_value(value)
    if not raw:
        return ()
    parts = [part.strip() for part in raw.split(",")]
    return tuple(part for part in parts if part)


def _normalize_scope_tokens(*, tokens: tuple[str, ...]) -> tuple[str, ...]:
    normalized: list[str] = []
    for token in tokens:
        raw = _normalize_header_value(token)
        if not raw:
            continue
        if raw.startswith("/"):
            raise ValueError(
                f"Ownership scope must be repo-relative, got absolute path: {raw}"
            )
        if "*" in raw or "?" in raw:
            raise ValueError(f"Ownership scope must not use wildcard patterns: {raw}")
        candidate = Path(raw)
        if any(part in {"..", "."} for part in candidate.parts):
            raise ValueError(f"Ownership scope must not contain '.' or '..': {raw}")
        cleaned = candidate.as_posix().strip("/")
        if not cleaned:
            raise ValueError("Ownership scope cannot target repo root.")
        normalized.append(cleaned)
    return tuple(dict.fromkeys(normalized))


def _normalize_header_value(value: str) -> str:
    trimmed = value.strip()
    if len(trimmed) >= 2 and trimmed[0] == "`" and trimmed[-1] == "`":
        trimmed = trimmed[1:-1].strip()
    if len(trimmed) >= 2 and trimmed[0] == '"' and trimmed[-1] == '"':
        trimmed = trimmed[1:-1].strip()
    return trimmed


def _resolve_requested_paths(
    *, repo_root: Path, raw_paths: tuple[str, ...]
) -> tuple[str, ...]:
    if not raw_paths:
        raise ValueError("At least one --path is required.")
    resolved: list[str] = []
    for raw_path in raw_paths:
        value = str(raw_path).strip()
        if not value:
            continue
        candidate = Path(value).expanduser()
        absolute = (
            candidate.resolve(strict=False)
            if candidate.is_absolute()
            else (repo_root / candidate).resolve(strict=False)
        )
        try:
            relative = absolute.relative_to(repo_root).as_posix()
        except Exception as exc:
            raise ValueError(f"Path escapes repo root: {absolute}") from exc
        cleaned = relative.strip("/")
        if not cleaned or cleaned == ".":
            raise ValueError(f"Invalid commit path: {value!r}")
        resolved.append(cleaned)
    if not resolved:
        raise ValueError("At least one non-empty --path is required.")
    return tuple(dict.fromkeys(resolved))


def _validate_issue_and_paths(
    *,
    issue: _IssueMetadata,
    owner_id: str,
    requested_paths: tuple[str, ...],
) -> None:
    if issue.issue_owner != owner_id:
        raise ValueError(
            f"Issue owner mismatch: issue owner is {issue.issue_owner!r}, command owner is {owner_id!r}."
        )
    normalized_status = " ".join(
        issue.issue_status.strip().lower().replace("_", " ").replace("-", " ").split()
    )
    if normalized_status != "in progress":
        raise ValueError(
            f"Issue status must be In Progress for commit rail, found: {issue.issue_status!r}."
        )
    for path in requested_paths:
        if not _is_within_any_scope(path=path, scope_paths=issue.ownership_scope):
            raise ValueError(
                f"Requested path is outside ownership scope: {path} (scope={list(issue.ownership_scope)})"
            )


def _is_within_any_scope(*, path: str, scope_paths: tuple[str, ...]) -> bool:
    for scope in scope_paths:
        if path == scope:
            return True
        prefix = f"{scope}/"
        if path.startswith(prefix):
            return True
    return False


def _run_commit_flow(
    *,
    runner: _GitRunnerProtocol,
    repo_root: Path,
    issue: _IssueMetadata,
    requested_paths: tuple[str, ...],
    message: str,
    owner_id: str,
    dry_run: bool,
    allow_empty: bool,
    transaction: _RepositoryIndexTransaction,
) -> tuple[tuple[str, ...], list[tuple[str, ...]]]:
    command_log: list[tuple[str, ...]] = []
    _require_git_repo(runner=runner, repo_root=repo_root, command_log=command_log)

    pre_staged = (
        ()
        if transaction.enabled
        else _git_name_list(
            runner=runner,
            repo_root=repo_root,
            args=("git", "diff", "--cached", "--name-only"),
            command_log=command_log,
        )
    )
    if not dry_run:
        _ensure_scoped_paths(
            paths=pre_staged,
            requested_paths=requested_paths,
            ownership_scope=issue.ownership_scope,
            context="pre-staged",
        )

    if dry_run:
        changed_paths = _git_status_paths(
            runner=runner,
            repo_root=repo_root,
            requested_paths=requested_paths,
            command_log=command_log,
        )
        if not changed_paths and not allow_empty:
            raise ValueError(
                "No changes detected in requested paths. Use --allow-empty to permit empty commit plans."
            )
        _ensure_scoped_paths(
            paths=changed_paths,
            requested_paths=requested_paths,
            ownership_scope=issue.ownership_scope,
            context="planned",
        )
        return changed_paths, command_log

    if transaction.enabled:
        _initialize_isolated_index(
            runner=runner,
            repo_root=repo_root,
            transaction=transaction,
            command_log=command_log,
        )

    # Use `-A` so deletions/renames inside scoped paths are staged without requiring raw git.
    # Missing paths are only added when Git still tracks them. This preserves
    # deleted-file staging while avoiding stale move/source pathspec failures.
    tracked_paths = _tracked_missing_requested_paths(
        runner=runner,
        repo_root=repo_root,
        requested_paths=requested_paths,
        pre_staged=pre_staged,
        command_log=command_log,
        environment=transaction.git_environment(),
    )
    add_paths = _requested_paths_for_git_add(
        repo_root=repo_root,
        requested_paths=requested_paths,
        pre_staged=pre_staged,
        tracked_paths=tracked_paths,
    )
    if add_paths:
        _run_git(
            runner=runner,
            repo_root=repo_root,
            args=("git", "add", "-A", "--", *add_paths),
            command_log=command_log,
            environment=transaction.git_environment(),
        )

    staged_paths = _git_name_list(
        runner=runner,
        repo_root=repo_root,
        args=("git", "diff", "--cached", "--name-only"),
        command_log=command_log,
        environment=transaction.git_environment(),
    )
    if not staged_paths and not allow_empty:
        raise ValueError(
            "No staged files after `git add`. Use --allow-empty to permit empty commits."
        )
    _ensure_scoped_paths(
        paths=staged_paths,
        requested_paths=requested_paths,
        ownership_scope=issue.ownership_scope,
        context="staged",
    )
    transaction.record_staged_paths(staged_paths)

    commit_message = _compose_commit_message(
        message=message,
        issue=issue,
        owner_id=owner_id,
        requested_paths=requested_paths,
    )
    _publish_staged_transaction(
        runner=runner,
        repo_root=repo_root,
        requested_paths=requested_paths,
        commit_message=commit_message,
        allow_empty=allow_empty,
        transaction=transaction,
        command_log=command_log,
    )
    return staged_paths, command_log


def _run_authorized_commit_flow(
    *,
    runner: _GitRunnerProtocol,
    repo_root: Path,
    requested_paths: tuple[str, ...],
    commit_message: str,
    dry_run: bool,
    allow_empty: bool,
    transaction: _RepositoryIndexTransaction,
    command_log: list[tuple[str, ...]] | None = None,
    repository_validated: bool = False,
    resident_provider: _ResidentRepositoryCommitProvider | None = None,
    resident_evidence: ResidentCommitAdmissionEvidence | None = None,
) -> tuple[tuple[str, ...], list[tuple[str, ...]]]:
    command_log = command_log if command_log is not None else []
    if not repository_validated:
        _require_git_repo(runner=runner, repo_root=repo_root, command_log=command_log)

    pre_staged = (
        ()
        if transaction.enabled
        else _git_name_list(
            runner=runner,
            repo_root=repo_root,
            args=("git", "diff", "--cached", "--name-only"),
            command_log=command_log,
        )
    )
    if not dry_run:
        _ensure_paths_within_requested(
            paths=pre_staged,
            requested_paths=requested_paths,
            context="pre-staged",
        )

    if dry_run:
        changed_paths = _git_status_paths(
            runner=runner,
            repo_root=repo_root,
            requested_paths=requested_paths,
            command_log=command_log,
        )
        if not changed_paths and not allow_empty:
            raise ValueError(
                "No changes detected in requested paths. Use --allow-empty to permit empty commit plans."
            )
        _ensure_paths_within_requested(
            paths=changed_paths,
            requested_paths=requested_paths,
            context="planned",
        )
        return changed_paths, command_log

    if transaction.enabled:
        _initialize_isolated_index(
            runner=runner,
            repo_root=repo_root,
            transaction=transaction,
            command_log=command_log,
        )

    tracked_paths = _tracked_missing_requested_paths(
        runner=runner,
        repo_root=repo_root,
        requested_paths=requested_paths,
        pre_staged=pre_staged,
        command_log=command_log,
        environment=transaction.git_environment(),
    )
    add_paths = _requested_paths_for_git_add(
        repo_root=repo_root,
        requested_paths=requested_paths,
        pre_staged=pre_staged,
        tracked_paths=tracked_paths,
    )
    if add_paths:
        _run_git(
            runner=runner,
            repo_root=repo_root,
            args=("git", "add", "-A", "--", *add_paths),
            command_log=command_log,
            environment=transaction.git_environment(),
        )

    staged_paths = _git_name_list(
        runner=runner,
        repo_root=repo_root,
        args=("git", "diff", "--cached", "--name-only"),
        command_log=command_log,
        environment=transaction.git_environment(),
    )
    if not staged_paths and not allow_empty:
        raise ValueError(
            "No staged files after `git add`. Use --allow-empty to permit empty commits."
        )
    _ensure_paths_within_requested(
        paths=staged_paths,
        requested_paths=requested_paths,
        context="staged",
    )
    transaction.record_staged_paths(staged_paths)

    _publish_staged_transaction(
        runner=runner,
        repo_root=repo_root,
        requested_paths=requested_paths,
        commit_message=_normalize_commit_message(commit_message),
        allow_empty=allow_empty,
        transaction=transaction,
        command_log=command_log,
        resident_provider=resident_provider,
        resident_evidence=resident_evidence,
    )
    return staged_paths, command_log


def _initialize_isolated_index(
    *,
    runner: _GitRunnerProtocol,
    repo_root: Path,
    transaction: _RepositoryIndexTransaction,
    command_log: list[tuple[str, ...]],
) -> None:
    if not transaction.enabled:
        return
    reference_result = _run_git_optional(
        runner=runner,
        repo_root=repo_root,
        args=("git", "symbolic-ref", "-q", "HEAD"),
        command_log=command_log,
    )
    reference = (
        reference_result.stdout.strip() if reference_result.returncode == 0 else "HEAD"
    )
    if reference != "HEAD" and not reference.startswith("refs/heads/"):
        raise ValueError(f"repository_head_reference_unsupported:{reference}")
    head_result = _run_git_optional(
        runner=runner,
        repo_root=repo_root,
        args=("git", "rev-parse", "--verify", "HEAD^{commit}"),
        command_log=command_log,
    )
    expected_head = head_result.stdout.strip() if head_result.returncode == 0 else None
    transaction.expected_head = expected_head
    transaction.updated_reference = reference
    read_tree_args = (
        ("git", "read-tree", expected_head)
        if expected_head is not None
        else ("git", "read-tree", "--empty")
    )
    _run_git(
        runner=runner,
        repo_root=repo_root,
        args=read_tree_args,
        command_log=command_log,
        environment=transaction.git_environment(),
    )


def _publish_staged_transaction(
    *,
    runner: _GitRunnerProtocol,
    repo_root: Path,
    requested_paths: tuple[str, ...],
    commit_message: str,
    allow_empty: bool,
    transaction: _RepositoryIndexTransaction,
    command_log: list[tuple[str, ...]],
    resident_provider: _ResidentRepositoryCommitProvider | None = None,
    resident_evidence: ResidentCommitAdmissionEvidence | None = None,
) -> None:
    if not transaction.enabled:
        commit_args: tuple[str, ...] = ("git", "commit")
        if allow_empty:
            commit_args = (*commit_args, "--allow-empty")
        _run_git(
            runner=runner,
            repo_root=repo_root,
            args=(*commit_args, "-m", commit_message),
            command_log=command_log,
        )
        return

    tree_result = _run_git(
        runner=runner,
        repo_root=repo_root,
        args=("git", "write-tree"),
        command_log=command_log,
        environment=transaction.git_environment(),
    )
    tree_hash = tree_result.stdout.strip()
    if not tree_hash:
        raise ValueError("repository_transaction_tree_missing")
    commit_args: tuple[str, ...] = ("git", "commit-tree", tree_hash)
    if transaction.expected_head is not None:
        commit_args = (*commit_args, "-p", transaction.expected_head)
    candidate_result = _run_git(
        runner=runner,
        repo_root=repo_root,
        args=(*commit_args, "-m", commit_message),
        command_log=command_log,
    )
    candidate_commit = candidate_result.stdout.strip()
    if not candidate_commit:
        raise ValueError("repository_transaction_candidate_commit_missing")
    transaction.candidate_commit = candidate_commit
    assert transaction.updated_reference is not None
    _record_index_projection_debt(
        runner=runner,
        repo_root=repo_root,
        transaction=transaction,
        requested_paths=requested_paths,
        command_log=command_log,
    )
    expected_value = transaction.expected_head or ("0" * 40)
    if resident_provider is not None:
        if resident_evidence is None:
            raise ValueError("resident_commit_admission_evidence_missing")
        _publish_resident_admitted_transaction(
            runner=runner,
            repo_root=repo_root,
            requested_paths=requested_paths,
            commit_message=commit_message,
            tree_hash=tree_hash,
            candidate_commit=candidate_commit,
            expected_value=expected_value,
            transaction=transaction,
            command_log=command_log,
            provider=resident_provider,
            evidence=resident_evidence,
        )
    else:
        transaction.record_reference_cas_journal()
        try:
            _run_git(
                runner=runner,
                repo_root=repo_root,
                args=(
                    "git",
                    "update-ref",
                    "-m",
                    "aware repository publication",
                    transaction.updated_reference,
                    candidate_commit,
                    expected_value,
                ),
                command_log=command_log,
            )
        except _GitCommandError:
            transaction.reference_update = "cas_failed"
            raise
        transaction.reference_update = "cas_applied"
        transaction.clear_reference_cas_journal()
    # This observation is advisory only: the locked projection revalidates the
    # latest per-path entries, including durable debt from an earlier publication.
    _shared_index_matches_expected_paths(
        runner=runner,
        repo_root=repo_root,
        expected_head=transaction.expected_head,
        requested_paths=requested_paths,
        command_log=command_log,
    )
    # Native Git writers do not take our provider lock. Retry short contention,
    # never steal their index lock or overwrite a changed staged postimage.
    projection_error: str | None = None
    for attempt in range(3):
        projection_error = _project_shared_index_atomically(
            runner=runner, repo_root=repo_root, candidate_commit=candidate_commit,
            requested_paths=requested_paths, transaction=transaction,
            command_log=command_log,
        )
        if projection_error != "shared_index_lock_busy" or attempt == 2:
            break
        time.sleep(0.05)
    if projection_error is None:
        transaction.projection_applied = True
    else:
        transaction.projection_error = projection_error


def _recover_replayed_index_projection(
    *,
    runner: _GitRunnerProtocol,
    repo_root: Path,
    report: WorkspaceCommitReport,
    requested_paths: tuple[str, ...],
    command_log: list[tuple[str, ...]],
    expected_head: str | None = None,
) -> _RepositoryIndexTransaction:
    transaction = _prepare_repository_index_transaction(
        repo_root=repo_root, runner=runner, report=report
    )
    with transaction:
        if not transaction.enabled:
            return transaction
        transaction.expected_head = _repository_head(
            runner=runner, repo_root=repo_root, command_log=command_log
        )
        if expected_head is not None and transaction.expected_head != expected_head:
            raise ValueError("index_reconciliation_head_advanced")
        reference = _run_git_optional(
            runner=runner,
            repo_root=repo_root,
            args=("git", "symbolic-ref", "-q", "HEAD"),
            command_log=command_log,
        )
        transaction.updated_reference = (
            reference.stdout.strip() if reference.returncode == 0 else "HEAD"
        )
        transaction.projection_error = _project_shared_index_atomically(
            runner=runner, repo_root=repo_root,
            candidate_commit=transaction.expected_head,
            requested_paths=requested_paths, transaction=transaction,
            command_log=command_log,
        )
        transaction.projection_applied = transaction.projection_error is None
    return transaction


def _record_index_projection_debt(
    *,
    runner: _GitRunnerProtocol,
    repo_root: Path,
    transaction: _RepositoryIndexTransaction,
    requested_paths: tuple[str, ...],
    command_log: list[tuple[str, ...]],
) -> None:
    """Persist eligible original preimages before the reference CAS, not after it."""
    if transaction._contents is None:
        return
    root = transaction.git_dir / "aware-transactions"
    descriptor, raw_path = tempfile.mkstemp(prefix="projection-preimage-", dir=root)
    snapshot = Path(raw_path)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(transaction._contents)
        preimage_heads: dict[str, str] = {}
        environment = {"GIT_INDEX_FILE": snapshot.as_posix()}
        for path in requested_paths:
            if _shared_index_matches_expected_paths(
                runner=runner,
                repo_root=repo_root,
                expected_head=transaction.expected_head,
                requested_paths=(path,),
                command_log=command_log,
                environment=environment,
            ):
                assert transaction.expected_head is not None
                preimage_heads[path] = transaction.expected_head
            else:
                inherited = _projection_debt_preimage(
                    runner=runner, repo_root=repo_root, transaction=transaction,
                    path=path, command_log=command_log, environment=environment,
                )
                if inherited is not None:
                    preimage_heads[path] = inherited
    finally:
        snapshot.unlink(missing_ok=True)
    if not preimage_heads:
        return
    assert transaction.candidate_commit is not None
    payload = {
        "schema_version": "aware.repository-index-projection.v2",
        "candidate_commit": transaction.candidate_commit,
        "expected_head": transaction.expected_head,
        "reference": transaction.updated_reference,
        "paths": list(preimage_heads),
        "preimage_heads": preimage_heads,
    }
    debt_path = root / f"index-projection-{transaction.candidate_commit}.json"
    descriptor, raw_path = tempfile.mkstemp(prefix="projection-debt-", dir=root)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(raw_path, debt_path)
    finally:
        Path(raw_path).unlink(missing_ok=True)
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def _projection_debt_preimage(
    *,
    runner: _GitRunnerProtocol,
    repo_root: Path,
    transaction: _RepositoryIndexTransaction,
    path: str,
    command_log: list[tuple[str, ...]],
    environment: dict[str, str] | None = None,
) -> str | None:
    """Only reachable published debt with an unchanged postimage grants recovery."""
    if transaction.expected_head is None:
        return None
    root = transaction.git_dir / "aware-transactions"
    for debt_path in root.glob("index-projection-*.json"):
        payload = _read_projection_debt(debt_path)
        if payload is None:
            continue
        if (
            payload.get("schema_version") != "aware.repository-index-projection.v2"
            or payload.get("reference") != transaction.updated_reference
            or path not in payload.get("paths", [])
        ):
            continue
        candidate = payload["candidate_commit"]
        parent = payload["expected_head"]
        if _run_git_optional(
            runner=runner,
            repo_root=repo_root,
            args=("git", "merge-base", "--is-ancestor", candidate, transaction.expected_head),
            command_log=command_log,
        ).returncode != 0:
            continue
        parents = _run_git_optional(
            runner=runner,
            repo_root=repo_root,
            args=("git", "rev-list", "--parents", "-n", "1", candidate),
            command_log=command_log,
        )
        if parents.stdout.strip().split() != [candidate, parent]:
            continue
        published = _head_path_entry(
            runner=runner, repo_root=repo_root, head=candidate,
            path=path, command_log=command_log,
        )
        current = _head_path_entry(
            runner=runner, repo_root=repo_root, head=transaction.expected_head,
            path=path, command_log=command_log,
        )
        if published != current:
            continue
        preimage = payload["preimage_heads"][path]
        if _run_git_optional(
            runner=runner, repo_root=repo_root,
            args=("git", "merge-base", "--is-ancestor", preimage, parent),
            command_log=command_log,
        ).returncode != 0:
            continue
        if _shared_index_matches_expected_paths(
            runner=runner, repo_root=repo_root, expected_head=preimage,
            requested_paths=(path,), command_log=command_log, environment=environment,
        ):
            return preimage
    return None


def _read_projection_debt(path: Path) -> dict[str, Any] | None:
    try:
        if path.is_symlink() or not path.is_file():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        if (
            not isinstance(payload, dict)
            or set(payload) != {
                "schema_version", "candidate_commit", "expected_head", "reference", "paths", "preimage_heads"
            }
            or payload["schema_version"] != "aware.repository-index-projection.v2"
            or not isinstance(payload["candidate_commit"], str)
            or not isinstance(payload["expected_head"], str)
            or not re.fullmatch(r"[0-9a-f]{40}", payload["candidate_commit"])
            or not re.fullmatch(r"[0-9a-f]{40}", payload["expected_head"])
            or not isinstance(payload["reference"], str)
            or not isinstance(payload["paths"], list)
            or not all(isinstance(item, str) for item in payload["paths"])
            or not isinstance(payload["preimage_heads"], dict)
            or set(payload["preimage_heads"]) != set(payload["paths"])
            or not all(
                isinstance(item, str) and re.fullmatch(r"[0-9a-f]{40}", item)
                for item in payload["preimage_heads"].values()
            )
        ):
            return None
        return payload
    except (OSError, ValueError):
        return None


def _project_shared_index_atomically(
    *,
    runner: _GitRunnerProtocol,
    repo_root: Path,
    candidate_commit: str,
    requested_paths: tuple[str, ...],
    transaction: _RepositoryIndexTransaction,
    command_log: list[tuple[str, ...]],
) -> str | None:
    """Project exact owned paths into the latest index under its native lock."""

    if transaction._contents is None or transaction._mode is None:
        return "shared_index_snapshot_missing"
    transaction_root = transaction.git_dir / "aware-transactions"
    lock_path = Path(f"{transaction.index_path}.lock")
    try:
        lock_descriptor = os.open(
            lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, transaction._mode
        )
    except FileExistsError:
        return "shared_index_lock_busy"
    lock_owned = True
    projection_path: Path | None = None
    try:
        if not transaction.index_path.exists():
            return "shared_index_advanced"
        latest_contents = transaction.index_path.read_bytes()
        for path in requested_paths:
            if _shared_index_matches_expected_paths(
                runner=runner, repo_root=repo_root,
                expected_head=transaction.expected_head,
                requested_paths=(path,), command_log=command_log,
            ) or _projection_debt_preimage(
                runner=runner, repo_root=repo_root, transaction=transaction,
                path=path, command_log=command_log,
            ) is not None:
                continue
            return (
                "shared_index_advanced"
                if latest_contents != transaction._contents
                else "foreign_staged_content_preserved"
            )
        descriptor, raw_path = tempfile.mkstemp(
            prefix="repository-projection-", suffix=".tmp", dir=transaction_root
        )
        projection_path = Path(raw_path)
        with os.fdopen(descriptor, "wb") as projection_file:
            projection_file.write(latest_contents)
        projection_result = _run_git_optional(
            runner=runner,
            repo_root=repo_root,
            args=("git", "reset", "--mixed", candidate_commit, "--", *requested_paths),
            command_log=command_log,
            environment={"GIT_INDEX_FILE": projection_path.as_posix()},
        )
        if projection_result.returncode != 0:
            return "shared_index_projection_prepare_failed"
        projected_contents = projection_path.read_bytes()
        if (
            not transaction.index_path.exists()
            or transaction.index_path.read_bytes() != latest_contents
        ):
            return "shared_index_advanced"
        reference_result = _run_git_optional(
            runner=runner,
            repo_root=repo_root,
            args=("git", "symbolic-ref", "-q", "HEAD"),
            command_log=command_log,
        )
        reference = (
            reference_result.stdout.strip()
            if reference_result.returncode == 0
            else "HEAD"
        )
        if reference != transaction.updated_reference:
            return "repository_ref_changed_before_index_projection"
        reference_head = _repository_head(
            runner=runner,
            repo_root=repo_root,
            command_log=command_log,
        )
        if reference_head != candidate_commit:
            return "repository_ref_advanced_before_index_projection"
        with os.fdopen(lock_descriptor, "wb") as lock_file:
            lock_descriptor = -1
            lock_file.write(projected_contents)
            lock_file.flush()
            os.fsync(lock_file.fileno())
        # Spend recovery authority durably before the index effect, while our
        # native lock still excludes other index writers. A crash in between
        # fails closed: it may need explicit repair, but cannot resurrect debt
        # after a successful projection and overwrite a later staged preimage.
        _clear_satisfied_projection_debt(
            transaction=transaction, requested_paths=requested_paths
        )
        os.replace(lock_path, transaction.index_path)
        lock_owned = False  # replacement consumes our lock; a new one is foreign
        return None
    finally:
        if lock_descriptor >= 0:
            os.close(lock_descriptor)
        if lock_owned:
            lock_path.unlink(missing_ok=True)
        if projection_path is not None:
            projection_path.unlink(missing_ok=True)


def _clear_satisfied_projection_debt(
    *, transaction: _RepositoryIndexTransaction, requested_paths: tuple[str, ...]
) -> None:
    for debt_path in (transaction.git_dir / "aware-transactions").glob(
        "index-projection-*.json"
    ):
        payload = _read_projection_debt(debt_path)
        if payload is None:
            continue
        if payload.get("reference") != transaction.updated_reference:
            continue
        remaining = [path for path in payload["paths"] if path not in requested_paths]
        if remaining == payload["paths"]:
            continue
        if not remaining:
            debt_path.unlink()
        else:
            payload["paths"] = remaining
            payload["preimage_heads"] = {
                path: payload["preimage_heads"][path] for path in remaining
            }
            descriptor, raw_path = tempfile.mkstemp(
                prefix="projection-debt-", dir=debt_path.parent
            )
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                    stream.write(json.dumps(payload, sort_keys=True) + "\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(raw_path, debt_path)
            finally:
                Path(raw_path).unlink(missing_ok=True)
    directory = os.open(transaction.git_dir / "aware-transactions", os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def _shared_index_matches_expected_paths(
    *,
    runner: _GitRunnerProtocol,
    repo_root: Path,
    expected_head: str | None,
    requested_paths: tuple[str, ...],
    command_log: list[tuple[str, ...]],
    environment: dict[str, str] | None = None,
) -> bool:
    if expected_head is None:
        return False
    for path in requested_paths:
        index = _run_git_optional(
            runner=runner,
            repo_root=repo_root,
            args=("git", "ls-files", "--stage", "-z", "--", path),
            command_log=command_log,
            environment=environment,
        )
        tree = _run_git_optional(
            runner=runner,
            repo_root=repo_root,
            args=("git", "ls-tree", "-z", expected_head, "--", path),
            command_log=command_log,
        )
        if index.returncode != 0 or tree.returncode != 0:
            return False
        index_text = index.stdout
        tree_text = tree.stdout
        if not index_text and not tree_text:
            continue
        if not index_text or not tree_text:
            return False
        index_records = index_text.rstrip("\0").split("\0")
        tree_records = tree_text.rstrip("\0").split("\0")
        if len(index_records) != 1 or len(tree_records) != 1:
            return False
        index_metadata, index_path = index_records[0].split("\t", 1)
        tree_metadata, tree_path = tree_records[0].split("\t", 1)
        index_fields = index_metadata.split()
        tree_fields = tree_metadata.split()
        if (
            len(index_fields) != 3 or len(tree_fields) != 3
            or index_fields[2] != "0" or index_path != path or tree_path != path
        ):
            return False
        if index_fields[0] != tree_fields[0] or index_fields[1] != tree_fields[2]:
            return False
    return True


def _publish_resident_admitted_transaction(
    *,
    runner: _GitRunnerProtocol,
    repo_root: Path,
    requested_paths: tuple[str, ...],
    commit_message: str,
    tree_hash: str,
    candidate_commit: str,
    expected_value: str,
    transaction: _RepositoryIndexTransaction,
    command_log: list[tuple[str, ...]],
    provider: _ResidentRepositoryCommitProvider,
    evidence: ResidentCommitAdmissionEvidence,
) -> None:
    if evidence.agent_ref is not None and evidence.human_sponsor_ref is None:
        raise ValueError("resident_commit_human_sponsor_missing")
    main_ref = transaction.updated_reference
    if main_ref is None:
        raise RuntimeError("resident_commit_main_ref_missing")
    fingerprints = _commit_trailer_values(
        body=commit_message, trailer_name=_REQUEST_FINGERPRINT_TRAILER
    )
    if len(fingerprints) != 1:
        raise ValueError("resident_commit_request_fingerprint_missing")
    path_entries = _tree_path_entries(
        runner=runner,
        repo_root=repo_root,
        tree_hash=tree_hash,
        requested_paths=requested_paths,
        command_log=command_log,
    )
    unsigned_authority: dict[str, object] = {
        "actor_ref": evidence.actor_ref,
        "agent_ref": evidence.agent_ref,
        "candidate_commit": candidate_commit,
        "dev_session_ref": evidence.dev_session_ref,
        "generation_owner_ref": evidence.generation_owner_ref,
        "human_sponsor_ref": evidence.human_sponsor_ref,
        "issue_revision_ref": evidence.issue_revision_ref,
        "message_digest": "sha256:"
        + hashlib.sha256(commit_message.encode()).hexdigest(),
        "predecessor_commit": expected_value,
        "provider_source_admission_digests": list(
            evidence.provider_source_admission_digests
        ),
        "repository_operation_ref": evidence.repository_operation_ref,
        "request_fingerprint": fingerprints[0],
        "schema": "aware.repository.commit-admission-evidence.v1",
        "selected_path_entries": path_entries,
        "source_effect_policy": evidence.source_effect_policy,
        "tree": tree_hash,
        "work_context_ref": evidence.work_context_ref,
        "workspace_mutation_receipt_digests": list(
            evidence.workspace_mutation_receipt_digests
        ),
        "workspace_session_ref": evidence.workspace_session_ref,
    }
    authority = provider.authenticate_admission_evidence(unsigned_authority)
    evidence_bytes = _canonical_bytes(authority)
    evidence_digest = "sha256:" + hashlib.sha256(evidence_bytes).hexdigest()
    object_id = _hash_git_blob(
        repo_root=repo_root,
        payload=evidence_bytes,
        command_log=command_log,
        write=False,
    )
    admission_ref = (
        f"{_ADMISSION_REF_NAMESPACE}/{candidate_commit}/"
        f"{evidence_digest.removeprefix('sha256:')}"
    )
    journal_body: dict[str, object] = {
        "admission_ref": admission_ref,
        "candidate_commit": candidate_commit,
        "evidence_digest": evidence_digest,
        "evidence_object_id": object_id,
        "generation_owner_ref": evidence.generation_owner_ref,
        "main_ref": main_ref,
        "predecessor_commit": expected_value,
        "request_fingerprint": fingerprints[0],
        "schema": "aware.repository.commit-admission-transaction-journal.v1",
        "tree": tree_hash,
    }
    journal_name = f"{candidate_commit}-{evidence_digest[7:]}.json"
    provider.prepare_transaction(
        authority=authority,
        journal_name=journal_name,
        journal_body=journal_body,
    )
    written_object_id = _hash_git_blob(
        repo_root=repo_root,
        payload=evidence_bytes,
        command_log=command_log,
        write=True,
    )
    if written_object_id != object_id:
        raise RuntimeError("resident_commit_admission_object_mismatch")
    main_now = _read_ref(
        runner=runner,
        repo_root=repo_root,
        reference=main_ref,
        command_log=command_log,
    )
    admission_now = _read_ref(
        runner=runner,
        repo_root=repo_root,
        reference=admission_ref,
        command_log=command_log,
    )
    if main_now == candidate_commit and admission_now == object_id:
        pass
    elif main_now == expected_value and admission_now is None:
        _atomic_update_admission_refs(
            repo_root=repo_root,
            main_ref=main_ref,
            expected_main=expected_value,
            candidate_commit=candidate_commit,
            admission_ref=admission_ref,
            evidence_object_id=object_id,
            command_log=command_log,
        )
    else:
        raise RuntimeError("resident_commit_admission_ref_state_conflict")
    if (
        _read_ref(
            runner=runner,
            repo_root=repo_root,
            reference=main_ref,
            command_log=command_log,
        )
        != candidate_commit
        or _read_ref(
            runner=runner,
            repo_root=repo_root,
            reference=admission_ref,
            command_log=command_log,
        )
        != object_id
    ):
        raise RuntimeError("resident_commit_admission_reread_mismatch")
    provider.terminalize_transaction(
        journal_name=journal_name,
        terminal_body={
            "admission_ref": admission_ref,
            "candidate_commit": candidate_commit,
            "evidence_digest": evidence_digest,
            "evidence_object_id": object_id,
            "schema": "aware.repository.commit-admission-transaction-complete.v1",
        },
    )
    transaction.reference_update = "cas_applied"
    transaction.repository_admission_ref = admission_ref
    transaction.repository_admission_evidence_digest = evidence_digest


def _tree_path_entries(
    *,
    runner: _GitRunnerProtocol,
    repo_root: Path,
    tree_hash: str,
    requested_paths: tuple[str, ...],
    command_log: list[tuple[str, ...]],
) -> list[dict[str, str]]:
    result = _run_git(
        runner=runner,
        repo_root=repo_root,
        args=("git", "ls-tree", "-r", tree_hash, "--", *requested_paths),
        command_log=command_log,
    )
    entries: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        metadata, separator, path = line.partition("\t")
        values = metadata.split()
        if not separator or len(values) != 3:
            raise RuntimeError("resident_commit_tree_entry_invalid")
        mode, kind, object_id = values
        entries.append(
            {"kind": kind, "mode": mode, "object_id": object_id, "path": path}
        )
    if [item["path"] for item in entries] != sorted(item["path"] for item in entries):
        raise RuntimeError("resident_commit_tree_entries_not_ordered")
    return entries


def _hash_git_blob(
    *,
    repo_root: Path,
    payload: bytes,
    command_log: list[tuple[str, ...]],
    write: bool,
) -> str:
    command = ("git", "hash-object", *(("-w",) if write else ()), "--stdin")
    command_log.append(command)
    completed = subprocess.run(
        list(command),
        cwd=repo_root,
        input=payload,
        capture_output=True,
        check=False,
    )
    object_id = completed.stdout.decode("ascii", "strict").strip()
    if completed.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40,64}", object_id):
        raise RuntimeError("resident_commit_admission_object_write_failed")
    return object_id


def _atomic_update_admission_refs(
    *,
    repo_root: Path,
    main_ref: str,
    expected_main: str,
    candidate_commit: str,
    admission_ref: str,
    evidence_object_id: str,
    command_log: list[tuple[str, ...]],
) -> None:
    command = ("git", "update-ref", "--stdin")
    command_log.append(command)
    transaction = (
        "start\n"
        f"update {main_ref} {candidate_commit} {expected_main}\n"
        f"create {admission_ref} {evidence_object_id}\n"
        "prepare\n"
        "commit\n"
    )
    completed = subprocess.run(
        list(command),
        cwd=repo_root,
        input=transaction,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("resident_commit_admission_ref_transaction_failed")


def _read_ref(
    *,
    runner: _GitRunnerProtocol,
    repo_root: Path,
    reference: str,
    command_log: list[tuple[str, ...]],
) -> str | None:
    result = _run_git_optional(
        runner=runner,
        repo_root=repo_root,
        args=("git", "rev-parse", "--verify", reference),
        command_log=command_log,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _read_resident_journal(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    try:
        value: object = json.loads(path.read_bytes())
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("resident_commit_admission_journal_invalid") from exc
    if not isinstance(value, dict) or _canonical_bytes(value) != path.read_bytes():
        raise RuntimeError("resident_commit_admission_journal_invalid")
    return dict(value)


def _write_no_replace(
    path: Path, payload: bytes, *, allow_identical: bool = False
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        if allow_identical and path.read_bytes() == payload:
            return
        raise RuntimeError("resident_commit_admission_journal_collision") from None
    try:
        written = 0
        while written < len(payload):
            count = os.write(descriptor, payload[written:])
            if count <= 0:
                raise RuntimeError("resident_commit_admission_journal_short_write")
            written += count
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(parent)
    finally:
        os.close(parent)


def _canonical_bytes(value: dict[str, object]) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode()


def _canonical_digest(value: dict[str, object]) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _is_sha256_digest(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 71
        and value.startswith("sha256:")
        and all(character in "0123456789abcdef" for character in value[7:])
    )


def _require_git_repo(
    *,
    runner: _GitRunnerProtocol,
    repo_root: Path,
    command_log: list[tuple[str, ...]],
) -> None:
    result = _run_git(
        runner=runner,
        repo_root=repo_root,
        args=("git", "rev-parse", "--is-inside-work-tree"),
        command_log=command_log,
    )
    if result.stdout.strip().lower() != "true":
        raise ValueError(f"Not a git work tree: {repo_root}")


def _extract_head_commit_hash(
    *,
    runner: _GitRunnerProtocol,
    repo_root: Path,
    command_log: list[tuple[str, ...]],
) -> str:
    result = _run_git(
        runner=runner,
        repo_root=repo_root,
        args=("git", "rev-parse", "HEAD"),
        command_log=command_log,
    )
    commit_hash = result.stdout.strip()
    if not commit_hash:
        raise ValueError("Unable to resolve HEAD commit hash after commit.")
    return commit_hash


def _git_name_list(
    *,
    runner: _GitRunnerProtocol,
    repo_root: Path,
    args: tuple[str, ...],
    command_log: list[tuple[str, ...]],
    environment: dict[str, str] | None = None,
) -> tuple[str, ...]:
    result = _run_git(
        runner=runner,
        repo_root=repo_root,
        args=args,
        command_log=command_log,
        environment=environment,
    )
    names = tuple(line.strip() for line in result.stdout.splitlines() if line.strip())
    return tuple(dict.fromkeys(names))


def _git_status_paths(
    *,
    runner: _GitRunnerProtocol,
    repo_root: Path,
    requested_paths: tuple[str, ...],
    command_log: list[tuple[str, ...]],
) -> tuple[str, ...]:
    result = _run_git(
        runner=runner,
        repo_root=repo_root,
        args=("git", "status", "--porcelain", "--", *requested_paths),
        command_log=command_log,
    )
    collected: list[str] = []
    for line in result.stdout.splitlines():
        # Porcelain format reserves first 3 chars for XY + space.
        if not line.strip():
            continue
        if len(line) < 4:
            continue
        path = line[3:].strip()
        if " -> " in path:
            _, path = path.split(" -> ", 1)
            path = path.strip()
        if path:
            collected.append(path)
    return tuple(dict.fromkeys(collected))


def _ensure_scoped_paths(
    *,
    paths: tuple[str, ...],
    requested_paths: tuple[str, ...],
    ownership_scope: tuple[str, ...],
    context: str,
) -> None:
    for path in paths:
        if not _is_within_any_scope(path=path, scope_paths=ownership_scope):
            raise ValueError(
                f"{context} path is outside issue ownership scope: {path} (scope={list(ownership_scope)})"
            )
        if not _is_within_any_scope(path=path, scope_paths=requested_paths):
            raise ValueError(
                f"{context} path is outside requested --path scope: {path} (requested={list(requested_paths)})"
            )


def _ensure_paths_within_requested(
    *,
    paths: tuple[str, ...],
    requested_paths: tuple[str, ...],
    context: str,
) -> None:
    _ensure_scoped_paths(
        paths=paths,
        requested_paths=requested_paths,
        ownership_scope=requested_paths,
        context=context,
    )


def _requested_paths_for_git_add(
    *,
    repo_root: Path,
    requested_paths: tuple[str, ...],
    pre_staged: tuple[str, ...],
    tracked_paths: tuple[str, ...] = (),
) -> tuple[str, ...]:
    add_paths: list[str] = []
    for path in requested_paths:
        absolute = repo_root / path
        if absolute.exists():
            add_paths.append(path)
            continue
        if _path_or_descendant_in_paths(path=path, paths=pre_staged):
            continue
        if _path_or_descendant_in_paths(path=path, paths=tracked_paths):
            add_paths.append(path)
            continue
    return tuple(add_paths)


def _tracked_missing_requested_paths(
    *,
    runner: _GitRunnerProtocol,
    repo_root: Path,
    requested_paths: tuple[str, ...],
    pre_staged: tuple[str, ...],
    command_log: list[tuple[str, ...]],
    environment: dict[str, str] | None = None,
) -> tuple[str, ...]:
    missing_unstaged = tuple(
        path
        for path in requested_paths
        if not (repo_root / path).exists()
        and not _path_or_descendant_in_paths(path=path, paths=pre_staged)
    )
    if not missing_unstaged:
        return ()
    return _git_name_list(
        runner=runner,
        repo_root=repo_root,
        args=("git", "ls-files", "--", *missing_unstaged),
        command_log=command_log,
        environment=environment,
    )


def _path_or_descendant_in_paths(*, path: str, paths: tuple[str, ...]) -> bool:
    prefix = f"{path}/"
    return any(candidate == path or candidate.startswith(prefix) for candidate in paths)


def _normalize_commit_message(message: str) -> str:
    summary = str(message).strip()
    if not summary:
        raise ValueError("Commit message must not be empty.")
    return summary


def _normalize_idempotency_ref(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None
    value = str(raw_value).strip()
    if not value:
        raise ValueError("Idempotency ref must not be empty when supplied.")
    if len(value) > _MAX_IDEMPOTENCY_REF_LENGTH:
        raise ValueError(
            f"Idempotency ref exceeds {_MAX_IDEMPOTENCY_REF_LENGTH} characters."
        )
    if not _IDEMPOTENCY_REF_PATTERN.fullmatch(value):
        raise ValueError(
            "Idempotency ref must start with an ASCII letter or digit and contain "
            "only ASCII letters, digits, `.`, `_`, `:`, `/`, or `-`."
        )
    return value


def _authorized_commit_request_fingerprint(
    *,
    repo_root: Path,
    owner_id: str,
    requested_paths: tuple[str, ...],
    message: str,
    allow_empty: bool,
    authorized_path_states: tuple[WorkspaceAuthorizedPathState, ...] = (),
) -> str:
    canonical = json.dumps(
        {
            "allow_empty": allow_empty,
            "message": message,
            "owner_id": owner_id,
            "repo_root": repo_root.as_posix(),
            "requested_paths": sorted(requested_paths),
            "authorized_path_states": sorted(
                (
                    {
                        "path": state.path,
                        "expected_exists": state.expected_exists,
                        "expected_content_digest": state.expected_content_digest,
                    }
                    for state in authorized_path_states
                ),
                key=lambda state: str(state["path"]),
            ),
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def _content_commit_request_fingerprint(
    *,
    repo_root: Path,
    issue_relpath: str,
    owner_id: str,
    requested_paths: tuple[str, ...],
    message: str,
    semantic_intent_digest: str,
    repository_ref: str,
) -> str:
    """Hash stable semantic intent, deliberately excluding HEAD/postimages."""

    canonical = json.dumps(
        {
            "issue_path": issue_relpath,
            "message": message,
            "owner_id": owner_id,
            "repo_root": repo_root.as_posix(),
            "requested_paths": sorted(requested_paths),
            "repository_ref": repository_ref,
            "semantic_intent_digest": semantic_intent_digest,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def _normalize_repository_ref(value: str) -> str:
    normalized = value.strip()
    if not re.fullmatch(r"refs/heads/[A-Za-z0-9._/-]+", normalized):
        raise ValueError("expected_repository_ref must name one refs/heads/* ref.")
    if ".." in normalized or normalized.endswith(("/", ".")):
        raise ValueError("expected_repository_ref is not canonical.")
    return normalized


def _repository_symbolic_ref(
    *,
    runner: _GitRunnerProtocol,
    repo_root: Path,
    command_log: list[tuple[str, ...]],
) -> str:
    result = _run_git(
        runner=runner,
        repo_root=repo_root,
        args=("git", "symbolic-ref", "-q", "HEAD"),
        command_log=command_log,
    )
    return _normalize_repository_ref(result.stdout.strip())


def _repository_is_ancestor(
    *,
    runner: _GitRunnerProtocol,
    repo_root: Path,
    ancestor: str,
    descendant: str,
    command_log: list[tuple[str, ...]],
) -> bool:
    result = _run_git_optional(
        runner=runner,
        repo_root=repo_root,
        args=("git", "merge-base", "--is-ancestor", ancestor, descendant),
        command_log=command_log,
    )
    if result.returncode not in {0, 1}:
        raise _GitCommandError(
            args=("git", "merge-base", "--is-ancestor", ancestor, descendant),
            cwd=repo_root,
            result=result,
            command_log=tuple(command_log),
        )
    return result.returncode == 0


def _normalize_semantic_intent_digest(value: str) -> str:
    normalized = value.strip().casefold()
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", normalized):
        raise ValueError("semantic_intent_digest must be 'sha256:' plus 64 hex.")
    return normalized


def _normalize_source_digest(value: str, *, field: str) -> str:
    normalized = str(value).strip().lower()
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", normalized):
        raise ValueError(f"{field} must be 'sha256:' plus 64 hex.")
    return normalized


def _normalize_git_object_id(value: str, *, field: str) -> str:
    normalized = value.strip().casefold()
    if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", normalized):
        raise ValueError(f"{field} must be one full Git object id.")
    return normalized


def _normalize_supplied_path_contents(
    *,
    repo_root: Path,
    path_contents: tuple[WorkspaceSuppliedPathContent, ...],
) -> tuple[WorkspaceSuppliedPathContent, ...]:
    if not path_contents:
        raise ValueError("At least one supplied path postimage is required.")
    normalized: dict[str, WorkspaceSuppliedPathContent] = {}
    for item in path_contents:
        path = _resolve_requested_paths(
            repo_root=repo_root,
            raw_paths=(item.path,),
        )[0]
        if path in normalized:
            raise ValueError(f"Duplicate supplied path postimage: {path}")
        expected_oid = (
            _normalize_git_object_id(
                item.expected_head_blob_oid,
                field=f"expected_head_blob_oid:{path}",
            )
            if item.expected_head_blob_oid is not None
            else None
        )
        normalized[path] = item.model_copy(
            update={"path": path, "expected_head_blob_oid": expected_oid}
        )
    return tuple(normalized[path] for path in sorted(normalized))


def _repository_head(
    *,
    runner: _GitRunnerProtocol,
    repo_root: Path,
    command_log: list[tuple[str, ...]],
) -> str:
    result = _run_git(
        runner=runner,
        repo_root=repo_root,
        args=("git", "rev-parse", "--verify", "HEAD^{commit}"),
        command_log=command_log,
    )
    return _normalize_git_object_id(result.stdout.strip(), field="repository_head")


def _head_path_entry(
    *,
    runner: _GitRunnerProtocol,
    repo_root: Path,
    head: str,
    path: str,
    command_log: list[tuple[str, ...]],
) -> tuple[str, str] | None:
    result = _run_git(
        runner=runner,
        repo_root=repo_root,
        args=("git", "ls-tree", head, "--", path),
        command_log=command_log,
    )
    line = result.stdout.rstrip("\n")
    if not line:
        return None
    metadata, separator, observed_path = line.partition("\t")
    fields = metadata.split()
    if separator != "\t" or observed_path != path or len(fields) != 3:
        raise ValueError(f"repository_tree_entry_invalid:{path}")
    mode, kind, oid = fields
    if kind != "blob" or mode not in {"100644", "100755"}:
        raise ValueError(f"repository_tree_entry_unsupported:{path}")
    return mode, _normalize_git_object_id(oid, field=f"head_blob_oid:{path}")


def _head_path_text(
    *,
    runner: _GitRunnerProtocol,
    repo_root: Path,
    head: str,
    path: str,
    command_log: list[tuple[str, ...]],
) -> str:
    if (
        _head_path_entry(
            runner=runner,
            repo_root=repo_root,
            head=head,
            path=path,
            command_log=command_log,
        )
        is None
    ):
        raise ValueError(f"repository_head_path_missing:{path}")
    return _run_git(
        runner=runner,
        repo_root=repo_root,
        args=("git", "show", f"{head}:{path}"),
        command_log=command_log,
    ).stdout


def _validate_supplied_head_preimages(
    *,
    runner: _GitRunnerProtocol,
    repo_root: Path,
    head: str,
    path_contents: tuple[WorkspaceSuppliedPathContent, ...],
    command_log: list[tuple[str, ...]],
) -> None:
    for item in path_contents:
        entry = _head_path_entry(
            runner=runner,
            repo_root=repo_root,
            head=head,
            path=item.path,
            command_log=command_log,
        )
        observed_oid = entry[1] if entry is not None else None
        if observed_oid != item.expected_head_blob_oid:
            raise ValueError(
                "repository_head_path_stale:"
                f"path={item.path}:expected={item.expected_head_blob_oid}:"
                f"actual={observed_oid}"
            )


def _stage_supplied_path_contents(
    *,
    runner: _GitRunnerProtocol,
    repo_root: Path,
    path_contents: tuple[WorkspaceSuppliedPathContent, ...],
    transaction: _RepositoryIndexTransaction,
    command_log: list[tuple[str, ...]],
) -> tuple[str, ...]:
    if not transaction.enabled:
        raise ValueError("supplied content requires an isolated index transaction.")
    for item in path_contents:
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as handle:
            handle.write(item.content_text.encode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
            content_path = Path(handle.name)
        try:
            blob = _run_git(
                runner=runner,
                repo_root=repo_root,
                args=("git", "hash-object", "-w", content_path.as_posix()),
                command_log=command_log,
            ).stdout.strip()
        finally:
            content_path.unlink(missing_ok=True)
        blob_oid = _normalize_git_object_id(blob, field=f"postimage_blob:{item.path}")
        _run_git(
            runner=runner,
            repo_root=repo_root,
            args=(
                "git",
                "update-index",
                "--add",
                "--cacheinfo",
                f"{item.file_mode},{blob_oid},{item.path}",
            ),
            command_log=command_log,
            environment=transaction.git_environment(),
        )
    staged_paths = _git_name_list(
        runner=runner,
        repo_root=repo_root,
        args=("git", "diff", "--cached", "--name-only"),
        command_log=command_log,
        environment=transaction.git_environment(),
    )
    requested_paths = tuple(item.path for item in path_contents)
    if not staged_paths:
        raise ValueError("supplied content produced no repository change.")
    _ensure_paths_within_requested(
        paths=staged_paths,
        requested_paths=requested_paths,
        context="supplied-content-staged",
    )
    if set(staged_paths) != set(requested_paths):
        raise ValueError("supplied content must change every requested path.")
    return staged_paths


def _validate_authorized_path_states(
    *,
    repo_root: Path,
    requested_paths: tuple[str, ...],
    authorized_path_states: tuple[WorkspaceAuthorizedPathState, ...],
) -> None:
    """Validate exact expected bytes immediately before the Git stage boundary."""

    normalized_states = _normalize_authorized_path_states(
        repo_root=repo_root,
        requested_paths=requested_paths,
        authorized_path_states=authorized_path_states,
    )
    if not normalized_states:
        return
    states_by_path = {state.path: state for state in normalized_states}

    for path in requested_paths:
        state = states_by_path[path]
        expected_digest = state.expected_content_digest
        if state.expected_exists:
            if expected_digest is None or not re.fullmatch(
                r"sha256:[0-9a-f]{64}", expected_digest
            ):
                raise ValueError(
                    f"Authorized existing path requires a SHA-256 digest: {path}"
                )
            candidate = repo_root / path
            try:
                candidate.lstat()
            except FileNotFoundError as error:
                raise ValueError(
                    f"Authorized repository path no longer exists: {path}"
                ) from error
            if candidate.is_symlink() or not candidate.is_file():
                raise ValueError(
                    f"Authorized repository path is not a regular file: {path}"
                )
            digest_builder = hashlib.sha256()
            with candidate.open("rb") as stream:
                while chunk := stream.read(1024 * 1024):
                    digest_builder.update(chunk)
            digest = "sha256:" + digest_builder.hexdigest()
            if digest != expected_digest:
                raise ValueError(f"Authorized repository path state is stale: {path}")
        else:
            if expected_digest is not None:
                raise ValueError(
                    f"Authorized absent path cannot carry a content digest: {path}"
                )
            if (repo_root / path).exists() or (repo_root / path).is_symlink():
                raise ValueError(
                    f"Authorized repository deletion state is stale: {path}"
                )


def _normalize_authorized_path_states(
    *,
    repo_root: Path,
    requested_paths: tuple[str, ...],
    authorized_path_states: tuple[WorkspaceAuthorizedPathState, ...],
) -> tuple[WorkspaceAuthorizedPathState, ...]:
    if not authorized_path_states:
        return ()
    states_by_path: dict[str, WorkspaceAuthorizedPathState] = {}
    for state in authorized_path_states:
        resolved = _resolve_requested_paths(
            repo_root=repo_root,
            raw_paths=(state.path,),
        )[0]
        if resolved in states_by_path:
            raise ValueError(f"Duplicate authorized path state: {resolved}")
        states_by_path[resolved] = state.model_copy(update={"path": resolved})
    if set(states_by_path) != set(requested_paths):
        raise ValueError(
            "Authorized path states must exactly match requested repository paths."
        )
    return tuple(states_by_path[path] for path in sorted(states_by_path))


def _compose_authorized_commit_message(
    *,
    message: str,
    idempotency_ref: str | None,
    request_fingerprint: str | None,
) -> str:
    normalized = _normalize_commit_message(message)
    if idempotency_ref is None:
        return normalized
    reserved_prefixes = (
        f"{_IDEMPOTENCY_REF_TRAILER}:",
        f"{_REQUEST_FINGERPRINT_TRAILER}:",
    )
    if any(
        line.strip().startswith(reserved_prefixes) for line in normalized.splitlines()
    ):
        raise ValueError(
            "Commit message must not supply reserved Aware idempotency trailers."
        )
    if request_fingerprint is None:
        raise ValueError("Idempotent commit requires a request fingerprint.")
    return (
        f"{normalized}\n\n"
        f"{_IDEMPOTENCY_REF_TRAILER}: {idempotency_ref}\n"
        f"{_REQUEST_FINGERPRINT_TRAILER}: {request_fingerprint}"
    )


def _resolve_idempotent_authorized_commit(
    *,
    runner: _GitRunnerProtocol,
    repo_root: Path,
    idempotency_ref: str,
    request_fingerprint: str,
    requested_paths: tuple[str, ...],
    command_log: list[tuple[str, ...]],
) -> _IdempotentCommit | None:
    escaped_ref = idempotency_ref.replace(".", r"\.")
    grep_arg = f"--grep=^{_IDEMPOTENCY_REF_TRAILER}: {escaped_ref}$"
    result = _run_git(
        runner=runner,
        repo_root=repo_root,
        args=(
            "git",
            "log",
            "--all",
            "--basic-regexp",
            grep_arg,
            f"--max-count={_MAX_IDEMPOTENCY_MATCHES}",
            "--format=%H%x00%B%x00",
        ),
        command_log=command_log,
    )
    fields = [field.strip() for field in result.stdout.split("\x00")]
    commits: list[tuple[str, str]] = []
    for index in range(0, len(fields) - 1, 2):
        commit_hash = fields[index]
        body = fields[index + 1]
        if commit_hash:
            commits.append((commit_hash, body))

    expected_ref_line = f"{_IDEMPOTENCY_REF_TRAILER}: {idempotency_ref}"
    matches = [
        (commit_hash, body)
        for commit_hash, body in commits
        if expected_ref_line in {line.strip() for line in body.splitlines()}
    ]
    if not matches:
        return None
    if len(matches) != 1:
        raise ValueError(
            "Idempotency ref resolves to multiple commits in Git metadata: "
            f"{idempotency_ref!r}."
        )

    commit_hash, body = matches[0]
    fingerprint_values = _commit_trailer_values(
        body=body,
        trailer_name=_REQUEST_FINGERPRINT_TRAILER,
    )
    if fingerprint_values != (request_fingerprint,):
        raise ValueError(
            "Idempotency ref is already bound to a different authorized "
            f"commit request: {idempotency_ref!r}."
        )
    changed_paths = _git_name_list(
        runner=runner,
        repo_root=repo_root,
        args=(
            "git",
            "diff-tree",
            "--root",
            "--no-commit-id",
            "--name-only",
            "-r",
            commit_hash,
        ),
        command_log=command_log,
    )
    _ensure_paths_within_requested(
        paths=changed_paths,
        requested_paths=requested_paths,
        context="idempotent replay",
    )
    return _IdempotentCommit(
        commit_hash=commit_hash,
        changed_paths=changed_paths,
    )


def _commit_trailer_values(*, body: str, trailer_name: str) -> tuple[str, ...]:
    prefix = f"{trailer_name}:"
    return tuple(
        line.strip()[len(prefix) :].strip()
        for line in body.splitlines()
        if line.strip().startswith(prefix)
    )


def _compose_commit_message(
    *,
    message: str,
    issue: _IssueMetadata,
    owner_id: str,
    requested_paths: tuple[str, ...],
) -> str:
    summary = _normalize_commit_message(message)
    paths_csv = ",".join(requested_paths)
    return (
        f"{summary}\n\n"
        f"Issue-Tag: {issue.issue_tag}\n"
        f"Issue-Path: {issue.issue_path}\n"
        f"Owner: {owner_id}\n"
        f"Owned-Paths: {paths_csv}"
    )


def _run_git(
    *,
    runner: _GitRunnerProtocol,
    repo_root: Path,
    args: tuple[str, ...],
    command_log: list[tuple[str, ...]],
    environment: dict[str, str] | None = None,
) -> _GitCommandResult:
    command_log.append(args)
    if environment and isinstance(runner, _SubprocessGitRunner):
        result = runner.run_with_environment(
            args=args,
            cwd=repo_root,
            environment=environment,
        )
    else:
        result = runner.run(args=args, cwd=repo_root)
    if result.returncode != 0:
        raise _GitCommandError(
            args=args,
            cwd=repo_root,
            result=result,
            command_log=tuple(command_log),
        )
    return result


def _run_git_optional(
    *,
    runner: _GitRunnerProtocol,
    repo_root: Path,
    args: tuple[str, ...],
    command_log: list[tuple[str, ...]],
    environment: dict[str, str] | None = None,
) -> _GitCommandResult:
    command_log.append(args)
    if environment and isinstance(runner, _SubprocessGitRunner):
        return runner.run_with_environment(
            args=args,
            cwd=repo_root,
            environment=environment,
        )
    return runner.run(args=args, cwd=repo_root)


@contextmanager
def _git_mutation_lock(
    *,
    repo_root: Path,
    owner_id: str,
    issue_tag: str | None,
    command_summary: str,
) -> Iterator[None]:
    lock_path = _repository_mutation_lock_path(repo_root=repo_root)
    metadata_path = _git_mutation_lock_metadata_path(lock_path=lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    token = f"{os.getpid()}:{time.monotonic_ns()}"
    timeout_seconds = _git_mutation_lock_timeout_seconds()
    poll_seconds = _git_mutation_lock_poll_seconds()
    wait_started_at = time.monotonic()

    with lock_path.open("a+", encoding="utf-8") as lock_file:
        while True:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError as exc:
                elapsed_seconds = time.monotonic() - wait_started_at
                if elapsed_seconds >= timeout_seconds:
                    raise _GitMutationLockTimeoutError(
                        _format_git_mutation_lock_timeout(
                            lock_path=lock_path,
                            metadata_path=metadata_path,
                            timeout_seconds=timeout_seconds,
                            waited_seconds=elapsed_seconds,
                        )
                    ) from exc
                time.sleep(poll_seconds)

        metadata = {
            "command_summary": command_summary,
            "issue_tag": issue_tag,
            "owner_id": owner_id,
            "pid": os.getpid(),
            "started_at_utc": datetime.now(UTC).isoformat(),
            "token": token,
        }
        metadata_path.write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        try:
            yield
        finally:
            _remove_git_mutation_lock_metadata(metadata_path=metadata_path, token=token)
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _repository_mutation_lock_path(*, repo_root: Path) -> Path:
    try:
        common_dir = _resolve_repository_git_paths(repo_root=repo_root).common_dir
    except _RepositoryWritePreflightError:
        return repo_root / ".aware/locks/git-mutation.lock"
    return common_dir / _GIT_MUTATION_LOCK_PATH


def _git_mutation_lock_timeout_seconds() -> float:
    return _read_positive_float_env(
        name="AWARE_GIT_MUTATION_LOCK_TIMEOUT_SECONDS",
        default=_DEFAULT_GIT_MUTATION_LOCK_TIMEOUT_SECONDS,
    )


def _git_mutation_lock_poll_seconds() -> float:
    return _read_positive_float_env(
        name="AWARE_GIT_MUTATION_LOCK_POLL_SECONDS",
        default=_DEFAULT_GIT_MUTATION_LOCK_POLL_SECONDS,
    )


def _read_positive_float_env(*, name: str, default: float) -> float:
    raw_value = os.environ.get(name)
    if raw_value is None or not raw_value.strip():
        return default
    try:
        value = float(raw_value)
    except ValueError:
        return default
    if value <= 0:
        return default
    return value


def _git_mutation_lock_metadata_path(*, lock_path: Path) -> Path:
    return lock_path.with_suffix(f"{lock_path.suffix}.json")


def _remove_git_mutation_lock_metadata(*, metadata_path: Path, token: str) -> None:
    try:
        metadata = _read_git_mutation_lock_metadata(metadata_path=metadata_path)
        if metadata and metadata.get("token") != token:
            return
        metadata_path.unlink(missing_ok=True)
    except OSError:
        return


def _read_git_mutation_lock_metadata(
    *, metadata_path: Path
) -> dict[str, object] | None:
    try:
        raw_text = metadata_path.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        value = json.loads(raw_text)
    except json.JSONDecodeError:
        return {"raw": raw_text}
    if isinstance(value, dict):
        return value
    return {"raw": value}


def _format_git_mutation_lock_timeout(
    *,
    lock_path: Path,
    metadata_path: Path,
    timeout_seconds: float,
    waited_seconds: float,
) -> str:
    metadata = _read_git_mutation_lock_metadata(metadata_path=metadata_path)
    holder = (
        json.dumps(metadata, indent=2, sort_keys=True) if metadata else "<unavailable>"
    )
    return "\n".join(
        [
            f"Timed out after {waited_seconds:.3f}s waiting for Aware Git mutation lock.",
            f"configured_timeout_seconds: {timeout_seconds:.3f}",
            f"lock_path: {lock_path}",
            f"metadata_path: {metadata_path}",
            "holder:",
            holder,
        ]
    )


def _format_git_command_failure(
    *,
    args: tuple[str, ...],
    cwd: Path,
    result: _GitCommandResult,
) -> str:
    stderr = result.stderr.strip()
    stdout = result.stdout.strip()
    rendered_command = " ".join(shlex.quote(arg) for arg in args)
    sections = [
        f"Git command failed with exit code {result.returncode}.",
        f"cwd: {cwd}",
        "stderr:",
        stderr or "<empty>",
    ]
    if stdout:
        sections.extend(["stdout:", stdout])
    sections.extend(["command:", rendered_command])
    return "\n".join(sections)


def _compact_error(text: str) -> str:
    value = str(text).strip()
    if len(value) <= _MAX_ERROR_TEXT_LEN:
        return value
    overflow = len(value) - _MAX_ERROR_TEXT_LEN
    return f"{value[:_MAX_ERROR_TEXT_LEN]}...[truncated {overflow} chars]"


__all__ = [
    "print_workspace_commit_report",
    "print_workspace_commit_result",
    "run_workspace_authorized_commit",
    "run_workspace_commit",
]
