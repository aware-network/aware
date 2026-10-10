from __future__ import annotations

import difflib
import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from .change_evidence import (
    MAX_DIFF_LINE_CHARACTERS,
    RepositoryChangedEntryKind,
    RepositoryDiffBinaryPolicy,
    RepositoryDiffLineKind,
    RepositoryDiffPageState,
    RepositoryEvidencePosture,
    WorkspaceRepositoryChangeEvidence,
    WorkspaceRepositoryDiffFile,
    WorkspaceRepositoryDiffHunk,
    WorkspaceRepositoryDiffLine,
    WorkspaceRepositoryDiffPage,
    WorkspaceRepositoryDiffRequest,
    WorkspaceRepositoryMutationReceipt,
    repository_diff_continuation_ref,
    repository_diff_file_ref,
    repository_diff_hunk_ref,
    repository_diff_ref,
)

DEFAULT_OPERATIONAL_BODY_CAPACITY = 256
MAX_OPERATIONAL_BODY_CAPACITY = 4096
DEFAULT_OPERATIONAL_BODY_BYTES = 64 * 1024 * 1024
MAX_OPERATIONAL_BODY_BYTES = 512 * 1024 * 1024
DEFAULT_DIFF_CONTINUATION_CAPACITY = 4096
MAX_DIFF_CONTINUATION_CAPACITY = 16384


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryOperationalChange:
    receipt: WorkspaceRepositoryMutationReceipt
    evidence: WorkspaceRepositoryChangeEvidence
    before_content: bytes | None
    after_content: bytes | None

    def __post_init__(self) -> None:
        if self.receipt.outcome.value != "applied":
            raise ValueError("Operational bodies require an applied mutation")
        if self.evidence.posture is not RepositoryEvidencePosture.WORKSPACE_AUTHORIZED:
            raise ValueError("Operational bodies require authorized evidence")
        if self.receipt.mutation_receipt_ref not in self.evidence.mutation_receipt_refs:
            raise ValueError("Operational evidence does not retain its receipt")
        if self.evidence.before_coordinate != self.receipt.expected_coordinate:
            raise ValueError("Operational baseline differs from mutation expectation")
        if self.evidence.after_coordinate != self.receipt.result_coordinate:
            raise ValueError("Operational target differs from mutation result")

    @property
    def retained_bytes(self) -> int:
        return len(self.before_content or b"") + len(self.after_content or b"")


@dataclass(frozen=True, slots=True)
class _WorkspaceRepositoryRetainedExactChange:
    evidence: WorkspaceRepositoryChangeEvidence
    before_content: bytes | None
    after_content: bytes | None


_WorkspaceRepositoryResolvedChange = (
    WorkspaceRepositoryOperationalChange | _WorkspaceRepositoryRetainedExactChange
)


class _WorkspaceRepositoryDeltaDiffStore(Protocol):
    @property
    def repository_binding_ref(self) -> str: ...

    def retained_deltas(
        self,
    ) -> tuple[Any, ...]: ...

    def resolve_body(self, body_ref: str) -> bytes | None: ...


class _WorkspaceRepositoryDiffEvidenceIndex(Protocol):
    @property
    def repository_binding_ref(self) -> str: ...

    def retained_external_resolution(
        self, evidence_ref: str
    ) -> Any | None: ...


class WorkspaceRepositoryOperationalBodyStore:
    """Bounded volatile exact bodies for authorized operational mutations."""

    def __init__(
        self,
        *,
        capacity: int = DEFAULT_OPERATIONAL_BODY_CAPACITY,
        maximum_bytes: int = DEFAULT_OPERATIONAL_BODY_BYTES,
    ) -> None:
        if (
            isinstance(capacity, bool)
            or not 0 < capacity <= MAX_OPERATIONAL_BODY_CAPACITY
        ):
            raise ValueError("Operational body capacity is invalid")
        if (
            isinstance(maximum_bytes, bool)
            or not 0 < maximum_bytes <= MAX_OPERATIONAL_BODY_BYTES
        ):
            raise ValueError("Operational body byte capacity is invalid")
        self._capacity = capacity
        self._maximum_bytes = maximum_bytes
        self._values: dict[str, WorkspaceRepositoryOperationalChange] = {}
        self._retained_bytes = 0

    @property
    def retained_count(self) -> int:
        return len(self._values)

    @property
    def retained_bytes(self) -> int:
        return self._retained_bytes

    def can_retain(self, byte_count: int) -> bool:
        return (
            isinstance(byte_count, int)
            and not isinstance(byte_count, bool)
            and 0 <= byte_count <= self._maximum_bytes
        )

    def record(self, value: WorkspaceRepositoryOperationalChange) -> None:
        evidence_ref = value.evidence.evidence_ref
        existing = self._values.get(evidence_ref)
        if existing is not None:
            if existing != value:
                raise ValueError("Operational evidence ref cannot change bodies")
            return
        if value.retained_bytes > self._maximum_bytes:
            raise ValueError("Operational change exceeds body-store byte capacity")
        self._values[evidence_ref] = value
        self._retained_bytes += value.retained_bytes
        while (
            len(self._values) > self._capacity
            or self._retained_bytes > self._maximum_bytes
        ):
            old = self._values.pop(next(iter(self._values)))
            self._retained_bytes -= old.retained_bytes

    def resolve(self, evidence_ref: str) -> WorkspaceRepositoryOperationalChange | None:
        return self._values.get(evidence_ref)


@dataclass(frozen=True, slots=True)
class _Continuation:
    evidence_ref: str
    group_index: int
    line_offset: int


class WorkspaceRepositoryOperationalDiffProvider:
    """Lazy exact diff projection over retained authorized bodies."""

    def __init__(
        self,
        *,
        body_store: WorkspaceRepositoryOperationalBodyStore,
        is_cancelled: Callable[[str], bool] | None = None,
        continuation_capacity: int = DEFAULT_DIFF_CONTINUATION_CAPACITY,
    ) -> None:
        if (
            isinstance(continuation_capacity, bool)
            or not 0 < continuation_capacity <= MAX_DIFF_CONTINUATION_CAPACITY
        ):
            raise ValueError("Diff continuation capacity is invalid")
        self._body_store = body_store
        self._is_cancelled = is_cancelled or (lambda _ref: False)
        self._continuation_capacity = continuation_capacity
        self._continuations: dict[str, _Continuation] = {}

    def diff(
        self, request: WorkspaceRepositoryDiffRequest
    ) -> WorkspaceRepositoryDiffPage:
        diff_ref = repository_diff_ref(
            repository_binding_ref=request.repository_binding_ref,
            evidence_ref=request.evidence_ref,
            baseline=request.baseline,
            target=request.target,
        )
        change = self._resolve_change(request)
        if change is None:
            return _unavailable_page(
                request, diff_ref, self._missing_change_reason
            )
        if request.cancellation_ref is not None and self._is_cancelled(
            request.cancellation_ref
        ):
            return _unavailable_page(request, diff_ref, "diff request cancelled")
        evidence = change.evidence
        if (
            evidence.repository_binding_ref != request.repository_binding_ref
            or evidence.before_coordinate != request.baseline
            or evidence.after_coordinate != request.target
        ):
            return _unavailable_page(
                request,
                diff_ref,
                "diff coordinates are stale for retained evidence",
                state=RepositoryDiffPageState.STALE,
            )
        entry = evidence.changed_entries[0]
        if (
            request.changed_entry_ref is not None
            and request.changed_entry_ref != entry.changed_entry_ref
        ):
            return _unavailable_page(request, diff_ref, "changed entry is not retained")
        old_body = (
            b""
            if entry.kind is RepositoryChangedEntryKind.CREATE
            else change.before_content
        )
        new_body = (
            b""
            if entry.kind is RepositoryChangedEntryKind.DELETE
            else change.after_content
        )
        if old_body is None or new_body is None:
            return _unavailable_page(
                request, diff_ref, "exact baseline or target body unavailable"
            )
        binary = _is_binary(old_body) or _is_binary(new_body)
        file_ref = repository_diff_file_ref(
            diff_ref=diff_ref,
            kind=entry.kind,
            old_path=entry.old_path,
            new_path=entry.new_path,
        )
        if binary:
            if request.binary_policy is RepositoryDiffBinaryPolicy.REJECT:
                return _unavailable_page(
                    request, diff_ref, "binary diff rejected by policy"
                )
            file = WorkspaceRepositoryDiffFile(
                file_ref=file_ref,
                kind=entry.kind,
                old_path=entry.old_path,
                new_path=entry.new_path,
                old_content_digest=entry.old_content_digest,
                new_content_digest=entry.new_content_digest,
                binary=True,
                changed_entry_ref=entry.changed_entry_ref,
            )
            return _available_page(
                request=request,
                diff_ref=diff_ref,
                state=RepositoryDiffPageState.BINARY,
                file=file,
                complete=True,
                posture=evidence.posture,
            )
        try:
            groups = _line_groups(
                old_body.decode("utf-8"),
                new_body.decode("utf-8"),
                context_lines=request.context_lines,
            )
        except (UnicodeDecodeError, ValueError):
            if request.binary_policy is RepositoryDiffBinaryPolicy.REJECT:
                return _unavailable_page(
                    request, diff_ref, "content is not a bounded text diff"
                )
            file = WorkspaceRepositoryDiffFile(
                file_ref=file_ref,
                kind=entry.kind,
                old_path=entry.old_path,
                new_path=entry.new_path,
                old_content_digest=entry.old_content_digest,
                new_content_digest=entry.new_content_digest,
                binary=True,
                changed_entry_ref=entry.changed_entry_ref,
            )
            return _available_page(
                request=request,
                diff_ref=diff_ref,
                state=RepositoryDiffPageState.BINARY,
                file=file,
                complete=True,
                posture=evidence.posture,
            )
        position = _Continuation(request.evidence_ref, 0, 0)
        if request.continuation_ref is not None:
            resolved = self._continuations.get(request.continuation_ref)
            if resolved is None or resolved.evidence_ref != request.evidence_ref:
                return _unavailable_page(
                    request, diff_ref, "diff continuation is unavailable"
                )
            position = resolved
        selection, next_position = _select_lines(
            groups,
            group_index=position.group_index,
            line_offset=position.line_offset,
            maximum_lines=min(request.maximum_lines, 4096),
            maximum_bytes=request.maximum_bytes,
        )
        if selection is None:
            return _unavailable_page(
                request, diff_ref, "diff line exceeds requested byte budget"
            )
        selected_group, selected_lines = selection
        continuation_ref: str | None = None
        if next_position is not None:
            continuation_index = _continuation_index(request, next_position)
            continuation_ref = repository_diff_continuation_ref(
                diff_ref=diff_ref,
                last_file_ref=file_ref,
                page_index=continuation_index,
            )
            candidate = _Continuation(
                evidence_ref=request.evidence_ref,
                group_index=next_position[0],
                line_offset=next_position[1],
            )
            existing = self._continuations.get(continuation_ref)
            if existing is not None and existing != candidate:
                return _unavailable_page(
                    request, diff_ref, "diff continuation identity collision"
                )
            self._continuations[continuation_ref] = candidate
            while len(self._continuations) > self._continuation_capacity:
                self._continuations.pop(next(iter(self._continuations)))
        hunks: tuple[WorkspaceRepositoryDiffHunk, ...] = ()
        if selected_lines:
            old_numbers = [
                line.old_line_number for line in selected_lines if line.old_line_number
            ]
            new_numbers = [
                line.new_line_number for line in selected_lines if line.new_line_number
            ]
            old_start = min(old_numbers, default=selected_group.old_start)
            new_start = min(new_numbers, default=selected_group.new_start)
            old_count = sum(
                line.kind is not RepositoryDiffLineKind.ADDITION
                for line in selected_lines
            )
            new_count = sum(
                line.kind is not RepositoryDiffLineKind.DELETION
                for line in selected_lines
            )
            hunk = WorkspaceRepositoryDiffHunk(
                hunk_ref=repository_diff_hunk_ref(
                    file_ref=file_ref,
                    hunk_index=0,
                    old_start=old_start,
                    old_count=old_count,
                    new_start=new_start,
                    new_count=new_count,
                ),
                hunk_index=0,
                old_start=old_start,
                old_count=old_count,
                new_start=new_start,
                new_count=new_count,
                lines=selected_lines,
            )
            hunks = (hunk,)
        complete = continuation_ref is None
        file = WorkspaceRepositoryDiffFile(
            file_ref=file_ref,
            kind=entry.kind,
            old_path=entry.old_path,
            new_path=entry.new_path,
            old_content_digest=entry.old_content_digest,
            new_content_digest=entry.new_content_digest,
            binary=False,
            hunks=hunks,
            changed_entry_ref=entry.changed_entry_ref,
            complete=complete,
            truncated=not complete,
            next_continuation_ref=continuation_ref,
        )
        return _available_page(
            request=request,
            diff_ref=diff_ref,
            state=(
                RepositoryDiffPageState.AVAILABLE
                if complete
                else RepositoryDiffPageState.PARTIAL
            ),
            file=file,
            complete=complete,
            continuation_ref=continuation_ref,
            posture=evidence.posture,
        )

    @property
    def _missing_change_reason(self) -> str:
        return "exact operational bodies unavailable"

    def _resolve_change(
        self, request: WorkspaceRepositoryDiffRequest
    ) -> _WorkspaceRepositoryResolvedChange | None:
        return self._body_store.resolve(request.evidence_ref)


class WorkspaceRepositoryExactDiffProvider(
    WorkspaceRepositoryOperationalDiffProvider
):
    """Lazy diff projection over direct mutations and resident exact deltas."""

    def __init__(
        self,
        *,
        body_store: WorkspaceRepositoryOperationalBodyStore,
        delta_store: _WorkspaceRepositoryDeltaDiffStore,
        evidence_resolver: _WorkspaceRepositoryDiffEvidenceIndex,
        is_cancelled: Callable[[str], bool] | None = None,
        continuation_capacity: int = DEFAULT_DIFF_CONTINUATION_CAPACITY,
    ) -> None:
        if (
            delta_store.repository_binding_ref
            != evidence_resolver.repository_binding_ref
        ):
            raise ValueError("Resident diff authorities use different repositories")
        super().__init__(
            body_store=body_store,
            is_cancelled=is_cancelled,
            continuation_capacity=continuation_capacity,
        )
        self._delta_store = delta_store
        self._evidence_resolver = evidence_resolver

    @property
    def _missing_change_reason(self) -> str:
        return "exact Workspace bodies unavailable"

    def _resolve_change(
        self, request: WorkspaceRepositoryDiffRequest
    ) -> _WorkspaceRepositoryResolvedChange | None:
        operational = super()._resolve_change(request)
        if operational is not None:
            return operational
        retained = self._evidence_resolver.retained_external_resolution(
            request.evidence_ref
        )
        if retained is None:
            return None
        evidence = retained.evidence
        if (
            evidence.before_coordinate is None
            or evidence.after_coordinate is None
            or evidence.before_coordinate.observation is None
            or evidence.after_coordinate.observation is None
        ):
            return None
        entries = tuple(
            entry
            for entry in evidence.changed_entries
            if request.changed_entry_ref is None
            or entry.changed_entry_ref == request.changed_entry_ref
        )
        if len(entries) != 1:
            return None
        entry = entries[0]
        candidates = tuple(
            delta
            for delta in self._delta_store.retained_deltas()
            if str(delta.state) in {"available", "binary"}
            and delta.before_coordinate == evidence.before_coordinate.observation
            and delta.after_coordinate == evidence.after_coordinate.observation
            and delta.kind is entry.kind
            and delta.old_path == entry.old_path
            and delta.new_path == entry.new_path
            and (
                entry.old_content_digest is None
                or delta.old_content_digest == entry.old_content_digest
            )
            and (
                entry.new_content_digest is None
                or delta.new_content_digest == entry.new_content_digest
            )
            and (
                entry.old_size_bytes is None
                or delta.old_size_bytes == entry.old_size_bytes
            )
            and (
                entry.new_size_bytes is None
                or delta.new_size_bytes == entry.new_size_bytes
            )
        )
        signatures = {
            (delta.old_body_ref, delta.new_body_ref) for delta in candidates
        }
        if len(signatures) != 1:
            return None
        old_body_ref, new_body_ref = next(iter(signatures))
        before_content = (
            None
            if old_body_ref is None
            else self._delta_store.resolve_body(old_body_ref)
        )
        after_content = (
            None
            if new_body_ref is None
            else self._delta_store.resolve_body(new_body_ref)
        )
        if (old_body_ref is not None and before_content is None) or (
            new_body_ref is not None and after_content is None
        ):
            return None
        return _WorkspaceRepositoryRetainedExactChange(
            evidence=evidence,
            before_content=before_content,
            after_content=after_content,
        )


@dataclass(frozen=True, slots=True)
class _LineGroup:
    old_start: int
    new_start: int
    lines: tuple[WorkspaceRepositoryDiffLine, ...]


def _line_groups(
    old_text: str, new_text: str, *, context_lines: int
) -> tuple[_LineGroup, ...]:
    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False)
    groups: list[_LineGroup] = []
    for opcodes in matcher.get_grouped_opcodes(context_lines):
        lines: list[WorkspaceRepositoryDiffLine] = []
        for tag, old_start, old_end, new_start, new_end in opcodes:
            if tag in {"equal", "delete", "replace"}:
                kind = (
                    RepositoryDiffLineKind.CONTEXT
                    if tag == "equal"
                    else RepositoryDiffLineKind.DELETION
                )
                for index in range(old_start, old_end):
                    lines.append(
                        _diff_line(
                            kind=kind,
                            raw=old_lines[index],
                            old_number=index + 1,
                            new_number=(
                                new_start + (index - old_start) + 1
                                if tag == "equal"
                                else None
                            ),
                        )
                    )
            if tag in {"insert", "replace"}:
                for index in range(new_start, new_end):
                    lines.append(
                        _diff_line(
                            kind=RepositoryDiffLineKind.ADDITION,
                            raw=new_lines[index],
                            old_number=None,
                            new_number=index + 1,
                        )
                    )
        if lines:
            groups.append(
                _LineGroup(
                    old_start=opcodes[0][1] + 1,
                    new_start=opcodes[0][3] + 1,
                    lines=tuple(lines),
                )
            )
    return tuple(groups)


def _diff_line(
    *,
    kind: RepositoryDiffLineKind,
    raw: str,
    old_number: int | None,
    new_number: int | None,
) -> WorkspaceRepositoryDiffLine:
    text = raw.removesuffix("\n")
    text = text.removesuffix("\r")
    if len(text) > MAX_DIFF_LINE_CHARACTERS:
        raise ValueError("Diff line exceeds contract character bound")
    return WorkspaceRepositoryDiffLine(
        kind=kind,
        text=text,
        old_line_number=old_number,
        new_line_number=new_number,
        no_newline=not raw.endswith("\n"),
    )


def _select_lines(
    groups: tuple[_LineGroup, ...],
    *,
    group_index: int,
    line_offset: int,
    maximum_lines: int,
    maximum_bytes: int,
) -> tuple[
    tuple[_LineGroup, tuple[WorkspaceRepositoryDiffLine, ...]] | None,
    tuple[int, int] | None,
]:
    if not groups:
        return (_LineGroup(0, 0, ()), ()), None
    if group_index >= len(groups):
        return None, None
    group = groups[group_index]
    selected: list[WorkspaceRepositoryDiffLine] = []
    consumed_bytes = 0
    for line in group.lines[line_offset:]:
        line_bytes = len(line.text.encode("utf-8"))
        if selected and (
            len(selected) >= maximum_lines
            or consumed_bytes + line_bytes > maximum_bytes
        ):
            break
        if not selected and line_bytes > maximum_bytes:
            return None, None
        selected.append(line)
        consumed_bytes += line_bytes
        if len(selected) >= maximum_lines:
            break
    next_offset = line_offset + len(selected)
    if next_offset < len(group.lines):
        next_position = (group_index, next_offset)
    elif group_index + 1 < len(groups):
        next_position = (group_index + 1, 0)
    else:
        next_position = None
    return (group, tuple(selected)), next_position


def _is_binary(content: bytes) -> bool:
    return b"\x00" in content[:8192]


def _continuation_index(
    request: WorkspaceRepositoryDiffRequest, position: tuple[int, int]
) -> int:
    token = f"{request.request_ref}\n{position[0]}\n{position[1]}"
    return int(hashlib.sha256(token.encode("utf-8")).hexdigest()[:16], 16)


def _unavailable_page(
    request: WorkspaceRepositoryDiffRequest,
    diff_ref: str,
    reason: str,
    *,
    state: RepositoryDiffPageState = RepositoryDiffPageState.UNAVAILABLE,
) -> WorkspaceRepositoryDiffPage:
    return WorkspaceRepositoryDiffPage(
        diff_ref=diff_ref,
        evidence_ref=request.evidence_ref,
        repository_binding_ref=request.repository_binding_ref,
        posture=RepositoryEvidencePosture.WORKSPACE_AUTHORIZED,
        state=state,
        baseline=request.baseline,
        target=request.target,
        files=(),
        returned_file_count=0,
        total_file_count=None,
        complete=False,
        reason=reason,
    )


def _available_page(
    *,
    request: WorkspaceRepositoryDiffRequest,
    diff_ref: str,
    state: RepositoryDiffPageState,
    file: WorkspaceRepositoryDiffFile,
    complete: bool,
    posture: RepositoryEvidencePosture,
    continuation_ref: str | None = None,
) -> WorkspaceRepositoryDiffPage:
    return WorkspaceRepositoryDiffPage(
        diff_ref=diff_ref,
        evidence_ref=request.evidence_ref,
        repository_binding_ref=request.repository_binding_ref,
        posture=posture,
        state=state,
        baseline=request.baseline,
        target=request.target,
        files=(file,),
        returned_file_count=1,
        total_file_count=1,
        complete=complete,
        truncated=not complete,
        continuation_ref=continuation_ref,
    )
