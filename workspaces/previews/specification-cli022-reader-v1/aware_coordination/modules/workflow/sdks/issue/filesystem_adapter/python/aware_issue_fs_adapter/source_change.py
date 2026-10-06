"""Genuine filesystem Issue issuance and fixed physical consumption.

No callback guard, actor-string request, decoded permit or reverse Protocol
dependency. This is a cooperative filesystem/harness grade, not authentication.
"""

from __future__ import annotations

import hashlib
import os
import stat
import threading
from dataclasses import dataclass, field, replace
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, NoReturn
from weakref import WeakKeyDictionary, finalize

from aware_file_system.retained_mutation import (
    RetainedPhysicalEffect,
    RetainedPhysicalMutation,
    retain_confined_manifest_replacement,
)
from aware_issue_operational_runtime import evaluate_issue_source_scope
from aware_issue_sdk.source_change import (
    ISSUE_SOURCE_CHANGE_OPERATION_REF,
    IssueSourceChangeEffect,
    IssueSourceChangeReceipt,
    IssueSourceChangeRefusal,
    IssueSourceChangeRequest,
)

if TYPE_CHECKING:
    from .provider import FilesystemIssueOperationProvider


@dataclass
class _State:
    provider: FilesystemIssueOperationProvider
    provider_root: Path
    provider_manifest: str
    root: Path
    issue_path: str
    issue_identity: tuple
    parent_identities: tuple
    execution: str
    request: IssueSourceChangeRequest
    manifest: str
    physical: RetainedPhysicalMutation
    pid: int = field(default_factory=os.getpid)
    phase: str = "issued"
    lock: threading.RLock = field(default_factory=threading.RLock)


_ADMISSIONS: WeakKeyDictionary = WeakKeyDictionary()


class FilesystemIssueSourceChangeAdmission:
    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("Use the original Issue provider's admit_source_change")

    def __copy__(self):
        raise TypeError("Issue source admission cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("Issue source admission cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("Issue source admission cannot be serialized")

    @property
    def phase(self) -> str:
        return _issued(self).phase

    @property
    def effects(self) -> tuple[IssueSourceChangeEffect, ...]:
        return _effects(_issued(self))

    def validate_current(self) -> None:
        state = _issued(self)
        with state.lock:
            _check_or_retire(state)

    def prepare_next_directory(self) -> IssueSourceChangeEffect:
        state = _issued(self)
        with state.lock:
            _check_or_retire(state)
            try:
                effect = state.physical.prepare_next_directory()
                state.phase = "preparing"
                _check_or_retire(state)
                return _effect(effect)
            except BaseException as error:  # noqa: BLE001 - interruption retires with effects
                _retire(
                    state, getattr(error, "code", "source_preparation_failed"), error
                )

    def replace_manifest(self) -> IssueSourceChangeEffect:
        state = _issued(self)
        with state.lock:
            _check_or_retire(state)
            try:
                effect = state.physical.replace_manifest()
                state.phase = "replaced"
                _check_or_retire(state)
                return _effect(effect)
            except BaseException as error:  # noqa: BLE001 - actual effects must survive refusal
                _retire(
                    state, getattr(error, "code", "source_replacement_failed"), error
                )

    def finish(self) -> IssueSourceChangeReceipt:
        state = _issued(self)
        with state.lock:
            _check_or_retire(state)
            try:
                state.physical.finish()
                # Revalidate Issue at return after physical consumption; no
                # resurrection or invented rollback if this last read refuses.
                _check_issue(state)
                state.physical.validate_consumed_current()
                state.phase = "consumed"
                return IssueSourceChangeReceipt(
                    issue_ref=state.request.issue_ref,
                    execution_ref=state.execution,
                    client_intent_id=state.request.client_intent_id,
                    issue_sha256=state.request.expected_issue_sha256,
                    manifest_preimage_sha256=state.request.expected_manifest_sha256,
                    manifest_postimage_sha256=state.request.candidate_sha256,
                    ordered_effect_paths=(
                        *state.request.directory_paths,
                        state.manifest,
                    ),
                    effects=_effects(state),
                )
            except BaseException as error:  # noqa: BLE001 - post-effect refusal is terminal
                _retire(
                    state, getattr(error, "code", "source_completion_failed"), error
                )

    def release(self) -> None:
        state = _issued(self)
        with state.lock:
            _abandon(state)


def _admit(
    provider: FilesystemIssueOperationProvider, request: IssueSourceChangeRequest
) -> FilesystemIssueSourceChangeAdmission:
    from .provider import FilesystemIssueOperationProvider

    if type(provider) is not FilesystemIssueOperationProvider:
        raise IssueSourceChangeRefusal("original_issue_provider_required")
    if type(request) is not IssueSourceChangeRequest:
        raise TypeError("Source change requires exact neutral request")
    # Copy the frozen structural intent; the caller's DTO is never the permit.
    request = replace(request)
    physical = None
    try:
        execution = _execution()
        root = provider._repository_root.expanduser().resolve()
        source = _relative_manifest(root, provider._protocol_source_ref)
        if _relative_manifest(root, request.manifest_locator) != source:
            raise IssueSourceChangeRefusal("manifest_locator_mismatch")
        issue_path = _target(provider, request.issue_ref)
        body, identity, parents = _read_issue(root, issue_path)
        _policy(provider, request, execution, source, issue_path, body)
        physical = retain_confined_manifest_replacement(
            root=root,
            target_path=source,
            expected_content_digest=request.expected_manifest_sha256,
            content=request.candidate,
            directory_paths=request.directory_paths,
        )
        state = _State(
            provider,
            provider._repository_root,
            provider._protocol_source_ref,
            root,
            issue_path,
            identity,
            parents,
            execution,
            request,
            source,
            physical,
        )
        _check_or_retire(state)
        handle = object.__new__(FilesystemIssueSourceChangeAdmission)
        _ADMISSIONS[handle] = state
        finalize(handle, _abandon, state)
        return handle
    except BaseException as error:
        if physical is not None:
            physical.release()
        if isinstance(error, IssueSourceChangeRefusal):
            raise
        raise IssueSourceChangeRefusal(
            getattr(error, "code", "source_admission_failed")
        ) from error


def _execution() -> str:
    identities = [
        (provider, (os.environ.get(key) or "").strip())
        for provider, key in (
            ("codex", "CODEX_THREAD_ID"),
            ("claude_code", "CLAUDE_CODE_SESSION_ID"),
        )
    ]
    identities = [(provider, value) for provider, value in identities if value]
    if len(identities) != 1 or any(
        c.isspace() for _, value in identities for c in value
    ):
        raise IssueSourceChangeRefusal("provider_execution_identity_unavailable")
    provider, value = identities[0]
    return f"{provider}-{value}"


def _validate_bound(provider, admission) -> None:
    state = _issued(admission)
    with state.lock:
        if state.provider is not provider:
            _retire(state, "foreign_issue_provider")
        _check_or_retire(state)


def _relative_manifest(root: Path, locator: str) -> str:
    path = Path(locator)
    try:
        relative = str(path.relative_to(root)) if path.is_absolute() else locator
    except ValueError as error:
        raise IssueSourceChangeRefusal("manifest_locator_outside_repository") from error
    parsed = PurePosixPath(relative)
    if (
        not relative
        or "\\" in relative
        or parsed.is_absolute()
        or ".." in parsed.parts
        or str(parsed) != relative
        or relative == "."
    ):
        raise IssueSourceChangeRefusal("manifest_locator_noncanonical")
    return relative


def _target(provider, issue_ref: str) -> str:
    from aware_issue_sdk import IssueMutationResult

    target = provider._mutation_target(
        operation_ref=ISSUE_SOURCE_CHANGE_OPERATION_REF, issue_ref=issue_ref
    )
    if isinstance(target, IssueMutationResult):
        raise IssueSourceChangeRefusal(
            target.diagnostics[0]
            if target.diagnostics
            else "issue_authority_unavailable"
        )
    return target[1]


def _read_issue(root: Path, path: str) -> tuple[bytes, tuple, tuple]:
    descriptors = []
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        directory = os.open(root, flags)
        descriptors.append(directory)
        parents = []
        for part in PurePosixPath(path).parts[:-1]:
            directory = os.open(part, flags, dir_fd=directory)
            descriptors.append(directory)
            value = os.fstat(directory)
            parents.append((value.st_dev, value.st_ino, value.st_mode))
        leaf = PurePosixPath(path).name
        prior = os.stat(leaf, dir_fd=directory, follow_symlinks=False)
        if not stat.S_ISREG(prior.st_mode):
            raise IssueSourceChangeRefusal("issue_regular_bounded_authority_required")
        # A pre-open type check alone is racy. NONBLOCK ensures a substituted
        # FIFO cannot suspend admission before descriptor-based validation.
        descriptor = os.open(
            leaf, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory
        )
        descriptors.append(descriptor)
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or before.st_size > 4 * 1024 * 1024
        ):
            raise IssueSourceChangeRefusal("issue_regular_bounded_authority_required")
        if (prior.st_dev, prior.st_ino) != (before.st_dev, before.st_ino):
            raise IssueSourceChangeRefusal("issue_changed_during_open")
        chunks = []
        remaining = 4 * 1024 * 1024 + 1
        while remaining:
            chunk = os.read(descriptor, min(remaining, 64 * 1024))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        body = b"".join(chunks)
        after = os.fstat(descriptor)
        identity = lambda value: (
            value.st_dev,
            value.st_ino,
            value.st_mode,
            value.st_size,
            value.st_mtime_ns,
            value.st_ctime_ns,
            value.st_nlink,
        )
        if len(body) > 4 * 1024 * 1024 or identity(before) != identity(after):
            raise IssueSourceChangeRefusal("issue_changed_during_read")
        return body, identity(after), tuple(parents)
    finally:
        cleanup_error = None
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except BaseException as error:  # noqa: BLE001 - attempt every cleanup even when one is interrupted
                if cleanup_error is None:
                    cleanup_error = error
        if cleanup_error is not None:
            raise IssueSourceChangeRefusal(
                "issue_read_descriptor_cleanup_failed"
            ) from cleanup_error


def _policy(provider, request, execution, manifest, issue_path, body):
    from aware_issue_runtime import IssueReadProjection

    if "sha256:" + hashlib.sha256(body).hexdigest() != request.expected_issue_sha256:
        raise IssueSourceChangeRefusal("issue_source_sha256_mismatch")
    projection = provider._parse_projection(
        operation_ref=ISSUE_SOURCE_CHANGE_OPERATION_REF,
        issue_ref=request.issue_ref,
        relative_path=issue_path,
        source=body,
    )
    if not isinstance(projection, IssueReadProjection):
        raise IssueSourceChangeRefusal("issue_projection_unavailable")
    decision = evaluate_issue_source_scope(
        issue_owner=projection.owner_ref or "",
        issue_status=projection.status,
        scope_paths=projection.ownership_scope,
        actor_ref=execution,
        effect_paths=(*request.directory_paths, manifest),
    )
    if not decision.allowed:
        assert decision.refusal is not None
        raise IssueSourceChangeRefusal(decision.refusal.value)


def _check_issue(state: _State) -> None:
    if _execution() != state.execution:
        raise IssueSourceChangeRefusal("provider_execution_changed")
    if (
        state.provider._repository_root != state.provider_root
        or state.provider._protocol_source_ref != state.provider_manifest
    ):
        raise IssueSourceChangeRefusal("original_issue_provider_changed")
    if (
        state.provider._repository_root.expanduser().resolve() != state.root
        or _target(state.provider, state.request.issue_ref) != state.issue_path
    ):
        raise IssueSourceChangeRefusal("issue_authority_binding_changed")
    body, identity, parents = _read_issue(state.root, state.issue_path)
    if identity != state.issue_identity or parents != state.parent_identities:
        raise IssueSourceChangeRefusal("issue_authority_identity_changed")
    _policy(
        state.provider,
        state.request,
        state.execution,
        state.manifest,
        state.issue_path,
        body,
    )


def _check_or_retire(state: _State) -> None:
    if state.phase in {"retired", "consumed"}:
        raise IssueSourceChangeRefusal("issue_admission_terminal", _effects(state))
    try:
        state.physical.validate_current()
        _check_issue(state)
        state.physical.validate_current()
    except BaseException as error:  # noqa: BLE001 - freshness interruption is terminal
        _retire(state, getattr(error, "code", "source_currentness_failed"), error)


def _issued(handle) -> _State:
    state = (
        _ADMISSIONS.get(handle)
        if type(handle) is FilesystemIssueSourceChangeAdmission
        else None
    )
    if state is None:
        raise IssueSourceChangeRefusal("issue_admission_not_issued")
    if state.pid != os.getpid():
        _retire(state, "issue_admission_foreign_process")
    return state


def _effect(value: RetainedPhysicalEffect) -> IssueSourceChangeEffect:
    return IssueSourceChangeEffect(
        value.path,
        value.kind,
        value.state.value,
        value.durability_confirmed,
        value.mode,
        value.before_digest,
        value.after_digest,
        value.after_identity,
    )


def _effects(state: _State) -> tuple[IssueSourceChangeEffect, ...]:
    try:
        effects = state.physical.effects
    except BaseException as error:  # noqa: BLE001 - foreign-process refusal still carries read-only evidence
        effects = getattr(error, "effects", ())
    return tuple(_effect(value) for value in effects)


def _abandon(state: _State) -> None:
    if state.phase not in {"retired", "consumed"}:
        state.phase = "retired"
        state.physical.release()


def _retire(state: _State, code: str, cause: BaseException | None = None) -> NoReturn:
    state.phase = "retired"
    try:
        state.physical.release()
    except BaseException as error:  # noqa: BLE001 - retirement cannot discard physical failure evidence
        if cause is None:
            cause = error
    raise IssueSourceChangeRefusal(
        code, _effects(state), getattr(cause, "residual_scratch_paths", ())
    ) from cause
