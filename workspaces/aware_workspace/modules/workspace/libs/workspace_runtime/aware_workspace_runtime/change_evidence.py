from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import PurePosixPath

from .repository_access import RepositoryObservationCoordinate

WORKSPACE_REPOSITORY_CHANGE_EVIDENCE_CONTRACT_REF = (
    "aware.workspace.repository-change-evidence.v1"
)
WORKSPACE_REPOSITORY_CHANGE_EVIDENCE_CONTRACT_VERSION = "1"
WORKSPACE_REPOSITORY_EVIDENCE_GAP_OBSERVER_BASELINE_UNAVAILABLE = (
    "observer_baseline_unavailable"
)
WORKSPACE_REPOSITORY_EVIDENCE_GAP_EXACT_TRANSITION_UNAVAILABLE = (
    "observer_exact_transition_unavailable"
)

MAX_EXTERNAL_CHANGES = 256
MAX_CONTEXT_REFS = 64
MAX_CHANGED_ENTRIES = 4096
MAX_DIFF_FILES_PER_PAGE = 256
MAX_DIFF_HUNKS_PER_FILE = 2048
MAX_DIFF_LINES_PER_HUNK = 4096
MAX_DIFF_LINE_CHARACTERS = 32768
MAX_DIFF_FILE_BUDGET = 4096
MAX_DIFF_LINE_BUDGET = 200000
MAX_DIFF_BYTE_BUDGET = 16 * 1024 * 1024


class RepositoryEvidenceCoordinateKind(StrEnum):
    OBSERVATION = "observation"
    COMMITTED_REVISION = "committed_revision"


class RepositoryEvidencePosture(StrEnum):
    PROVIDER_REPORTED = "provider_reported"
    WORKSPACE_OBSERVED = "workspace_observed"
    PROVIDER_CORRELATED = "provider_correlated"
    WORKSPACE_AUTHORIZED = "workspace_authorized"
    COMMITTED_REVISION = "committed_revision"
    AMBIGUOUS = "ambiguous"
    GAP = "gap"


class RepositoryEvidenceResolutionState(StrEnum):
    REPORTED = "reported"
    RESOLVED = "resolved"
    AMBIGUOUS = "ambiguous"
    GAP = "gap"


class RepositoryReportedChangeKind(StrEnum):
    UNKNOWN = "unknown"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    RENAME = "rename"
    BINARY = "binary"


class RepositoryChangedEntryKind(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    RENAME = "rename"
    BINARY = "binary"


class RepositoryBodyAvailability(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    BINARY = "binary"
    TOO_LARGE = "too_large"
    MISSING_PREIMAGE = "missing_preimage"


class RepositoryMutationKind(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class RepositoryMutationOutcome(StrEnum):
    APPLIED = "applied"
    CONFLICT = "conflict"
    STALE = "stale"
    DENIED = "denied"
    FAILED = "failed"


class RepositoryDiffLineKind(StrEnum):
    CONTEXT = "context"
    ADDITION = "addition"
    DELETION = "deletion"


class RepositoryDiffPageState(StrEnum):
    AVAILABLE = "available"
    PARTIAL = "partial"
    BINARY = "binary"
    STALE = "stale"
    UNAVAILABLE = "unavailable"
    GAP = "gap"


class RepositoryDiffBinaryPolicy(StrEnum):
    METADATA_ONLY = "metadata_only"
    REJECT = "reject"


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryEvidenceCoordinate:
    kind: RepositoryEvidenceCoordinateKind
    repository_binding_ref: str
    state_digest: str
    observation: RepositoryObservationCoordinate | None = None
    revision_ref: str | None = None

    def __post_init__(self) -> None:
        binding_ref = _required(self.repository_binding_ref, "repository_binding_ref")
        state_digest = _required(self.state_digest, "state_digest")
        if self.kind is RepositoryEvidenceCoordinateKind.OBSERVATION:
            observation = self.observation
            if observation is None or self.revision_ref is not None:
                raise ValueError(
                    "Observation evidence coordinate requires only observation"
                )
            _validate_observation_coordinate(observation)
            if observation.repository_binding_ref != binding_ref:
                raise ValueError("Observation coordinate repository binding differs")
            if observation.snapshot_digest != state_digest:
                raise ValueError("Observation coordinate state digest differs")
        else:
            if self.observation is not None:
                raise ValueError("Revision coordinate cannot carry observation")
            object.__setattr__(
                self, "revision_ref", _required(self.revision_ref, "revision_ref")
            )
        object.__setattr__(self, "repository_binding_ref", binding_ref)
        object.__setattr__(self, "state_digest", state_digest)


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryReportedChange:
    path: str
    kind: RepositoryReportedChangeKind = RepositoryReportedChangeKind.UNKNOWN
    new_path: str | None = None

    def __post_init__(self) -> None:
        path = _relative_path(self.path)
        new_path = _optional_path(self.new_path)
        if self.kind is RepositoryReportedChangeKind.RENAME:
            if new_path is None or new_path == path:
                raise ValueError("Reported rename requires a distinct new path")
        elif new_path is not None:
            raise ValueError("Only reported rename may carry new_path")
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "new_path", new_path)


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryExternalEvidenceRef:
    evidence_ref: str
    source_namespace: str
    source_contract_version: str
    observed_at: datetime
    changes: tuple[WorkspaceRepositoryReportedChange, ...] = ()
    context_refs: tuple[str, ...] = ()
    body_evidence_ref: str | None = None
    complete: bool = True
    truncated: bool = False
    correlation_started_at: datetime | None = None
    correlation_ended_at: datetime | None = None
    posture: RepositoryEvidencePosture = RepositoryEvidencePosture.PROVIDER_REPORTED

    def __post_init__(self) -> None:
        if self.posture is not RepositoryEvidencePosture.PROVIDER_REPORTED:
            raise ValueError("External evidence posture must remain provider_reported")
        changes = tuple(self.changes)
        context_refs = _unique_refs(self.context_refs, "context_refs", MAX_CONTEXT_REFS)
        if len(changes) > MAX_EXTERNAL_CHANGES:
            raise ValueError("External evidence change count exceeds bound")
        if len({(item.path, item.new_path) for item in changes}) != len(changes):
            raise ValueError("External evidence changes must be unique")
        body_ref = _optional(self.body_evidence_ref, "body_evidence_ref")
        if not changes and body_ref is None:
            raise ValueError("External evidence requires changes or body evidence")
        if self.complete and self.truncated:
            raise ValueError("Complete external evidence cannot be truncated")
        started = _optional_utc(self.correlation_started_at)
        ended = _optional_utc(self.correlation_ended_at)
        if (started is None) != (ended is None):
            raise ValueError("Correlation interval requires both endpoints")
        if started is not None and ended is not None and ended < started:
            raise ValueError("Correlation interval end precedes start")
        object.__setattr__(
            self, "evidence_ref", _required(self.evidence_ref, "evidence_ref")
        )
        object.__setattr__(
            self,
            "source_namespace",
            _required(self.source_namespace, "source_namespace"),
        )
        object.__setattr__(
            self,
            "source_contract_version",
            _required(self.source_contract_version, "source_contract_version"),
        )
        object.__setattr__(self, "observed_at", _utc(self.observed_at))
        object.__setattr__(self, "changes", changes)
        object.__setattr__(self, "context_refs", context_refs)
        object.__setattr__(self, "body_evidence_ref", body_ref)
        object.__setattr__(self, "correlation_started_at", started)
        object.__setattr__(self, "correlation_ended_at", ended)


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryChangedEntry:
    changed_entry_ref: str
    kind: RepositoryChangedEntryKind
    posture: RepositoryEvidencePosture
    before_coordinate: WorkspaceRepositoryEvidenceCoordinate
    after_coordinate: WorkspaceRepositoryEvidenceCoordinate
    old_path: str | None = None
    new_path: str | None = None
    old_entry_ref: str | None = None
    new_entry_ref: str | None = None
    old_content_digest: str | None = None
    new_content_digest: str | None = None
    old_size_bytes: int | None = None
    new_size_bytes: int | None = None
    old_body_availability: RepositoryBodyAvailability = (
        RepositoryBodyAvailability.UNAVAILABLE
    )
    new_body_availability: RepositoryBodyAvailability = (
        RepositoryBodyAvailability.UNAVAILABLE
    )
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.posture in {
            RepositoryEvidencePosture.PROVIDER_REPORTED,
            RepositoryEvidencePosture.GAP,
        }:
            raise ValueError("Changed entry requires Workspace state evidence")
        _same_binding(self.before_coordinate, self.after_coordinate)
        old_path = _optional_path(self.old_path)
        new_path = _optional_path(self.new_path)
        old_entry_ref = _optional(self.old_entry_ref, "old_entry_ref")
        new_entry_ref = _optional(self.new_entry_ref, "new_entry_ref")
        old_digest = _optional(self.old_content_digest, "old_content_digest")
        new_digest = _optional(self.new_content_digest, "new_content_digest")
        _optional_non_negative(self.old_size_bytes, "old_size_bytes")
        _optional_non_negative(self.new_size_bytes, "new_size_bytes")
        reason = _optional(self.reason, "reason")
        if self.posture is RepositoryEvidencePosture.AMBIGUOUS:
            if reason is None:
                raise ValueError("Ambiguous changed entry requires reason")
        elif reason is not None:
            raise ValueError("Resolved changed entry cannot carry ambiguity reason")
        if self.kind is RepositoryChangedEntryKind.CREATE:
            if (
                any(
                    value is not None
                    for value in (
                        old_path,
                        old_entry_ref,
                        old_digest,
                        self.old_size_bytes,
                    )
                )
                or new_path is None
            ):
                raise ValueError("Create change requires only target path/state")
        elif self.kind is RepositoryChangedEntryKind.DELETE:
            if old_path is None or any(
                value is not None
                for value in (new_path, new_entry_ref, new_digest, self.new_size_bytes)
            ):
                raise ValueError("Delete change requires only prior path/state")
        elif self.kind is RepositoryChangedEntryKind.RENAME:
            if old_path is None or new_path is None or old_path == new_path:
                raise ValueError("Rename change requires distinct old/new paths")
        else:
            if old_path is None or new_path is None or old_path != new_path:
                raise ValueError("Update/binary change requires one stable path")
        expected_ref = repository_changed_entry_ref(
            repository_binding_ref=self.before_coordinate.repository_binding_ref,
            before_coordinate=self.before_coordinate,
            after_coordinate=self.after_coordinate,
            kind=self.kind,
            old_path=old_path,
            new_path=new_path,
        )
        if self.changed_entry_ref != expected_ref:
            raise ValueError("Changed entry ref is not deterministic")
        object.__setattr__(self, "old_path", old_path)
        object.__setattr__(self, "new_path", new_path)
        object.__setattr__(self, "old_entry_ref", old_entry_ref)
        object.__setattr__(self, "new_entry_ref", new_entry_ref)
        object.__setattr__(self, "old_content_digest", old_digest)
        object.__setattr__(self, "new_content_digest", new_digest)
        object.__setattr__(self, "reason", reason)


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryPhysicalEffect:
    """Physical writer evidence, never a converged authorization receipt."""

    state: str
    durability_confirmed: bool
    before_exists: bool
    before_content_digest: str | None
    before_size_bytes: int | None
    after_exists: bool
    after_content_digest: str | None
    after_size_bytes: int | None

    def __post_init__(self) -> None:
        if self.state not in {"none", "applied", "unknown"}:
            raise ValueError("Unsupported physical effect state")
        for flag in (self.durability_confirmed, self.before_exists, self.after_exists):
            if type(flag) is not bool:
                raise TypeError("Physical effect flags must be exact bools")
        if self.durability_confirmed and self.state != "applied":
            raise ValueError("Only known applied effects can confirm durability")
        for exists, digest, size in (
            (self.before_exists, self.before_content_digest, self.before_size_bytes),
            (self.after_exists, self.after_content_digest, self.after_size_bytes),
        ):
            _optional_non_negative(size, "physical_size_bytes")
            if exists != (digest is not None and size is not None):
                raise ValueError("Physical existence and content evidence disagree")
            if not exists and (digest is not None or size is not None):
                raise ValueError("Physical absence cannot carry content evidence")
            if digest is not None and (
                not digest.startswith("sha256:") or len(digest) != 71
                or any(c not in "0123456789abcdef" for c in digest[7:])
            ):
                raise ValueError("Physical content digest must be exact sha256")


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryMutationReceipt:
    mutation_receipt_ref: str
    repository_binding_ref: str
    operation_ref: str
    idempotency_key: str
    mutation_kind: RepositoryMutationKind
    expected_coordinate: WorkspaceRepositoryEvidenceCoordinate
    target_path: str
    expected_exists: bool
    expected_content_digest: str | None
    outcome: RepositoryMutationOutcome
    context_refs: tuple[str, ...] = ()
    result_coordinate: WorkspaceRepositoryEvidenceCoordinate | None = None
    result_entry_ref: str | None = None
    result_content_digest: str | None = None
    result_size_bytes: int | None = None
    request_body_evidence_ref: str | None = None
    result_body_evidence_ref: str | None = None
    delta_evidence_ref: str | None = None
    error_code: str | None = None
    physical_effect: WorkspaceRepositoryPhysicalEffect | None = None

    def __post_init__(self) -> None:
        if self.physical_effect is not None and type(self.physical_effect) is not WorkspaceRepositoryPhysicalEffect:
            raise TypeError("Physical effect must be the neutral evidence contract")
        binding_ref = _required(self.repository_binding_ref, "repository_binding_ref")
        operation_ref = _required(self.operation_ref, "operation_ref")
        idempotency_key = _required(self.idempotency_key, "idempotency_key")
        if self.expected_coordinate.repository_binding_ref != binding_ref:
            raise ValueError("Mutation expected coordinate binding differs")
        if (
            self.expected_coordinate.kind
            is not RepositoryEvidenceCoordinateKind.OBSERVATION
        ):
            raise ValueError("Mutation expected coordinate must be an observation")
        target_path = _relative_path(self.target_path)
        expected_digest = _optional(
            self.expected_content_digest, "expected_content_digest"
        )
        if self.mutation_kind is RepositoryMutationKind.CREATE:
            if self.expected_exists or expected_digest is not None:
                raise ValueError("Create mutation requires absent target baseline")
        elif not self.expected_exists or expected_digest is None:
            raise ValueError("Update/delete mutation requires exact prior digest")
        context_refs = _unique_refs(self.context_refs, "context_refs", MAX_CONTEXT_REFS)
        result_entry_ref = _optional(self.result_entry_ref, "result_entry_ref")
        result_digest = _optional(self.result_content_digest, "result_content_digest")
        request_body_ref = _optional(
            self.request_body_evidence_ref, "request_body_evidence_ref"
        )
        result_body_ref = _optional(
            self.result_body_evidence_ref, "result_body_evidence_ref"
        )
        delta_ref = _optional(self.delta_evidence_ref, "delta_evidence_ref")
        error_code = _optional(self.error_code, "error_code")
        _optional_non_negative(self.result_size_bytes, "result_size_bytes")
        if self.outcome is RepositoryMutationOutcome.APPLIED:
            result_coordinate = self.result_coordinate
            if result_coordinate is None:
                raise ValueError("Applied mutation requires result coordinate")
            if result_coordinate.repository_binding_ref != binding_ref:
                raise ValueError("Mutation result coordinate binding differs")
            if (
                result_coordinate.kind
                is not RepositoryEvidenceCoordinateKind.OBSERVATION
            ):
                raise ValueError("Mutation result coordinate must be an observation")
            if self.mutation_kind is RepositoryMutationKind.DELETE:
                if any(
                    value is not None
                    for value in (
                        result_entry_ref,
                        result_digest,
                        self.result_size_bytes,
                        result_body_ref,
                    )
                ):
                    raise ValueError("Applied delete cannot carry resulting entry")
            elif any(
                value is None
                for value in (result_entry_ref, result_digest, self.result_size_bytes)
            ):
                raise ValueError("Applied create/update requires resulting entry")
            if error_code is not None:
                raise ValueError("Applied mutation cannot carry error_code")
        else:
            if any(
                value is not None
                for value in (
                    self.result_coordinate,
                    result_entry_ref,
                    result_digest,
                    self.result_size_bytes,
                    result_body_ref,
                    delta_ref,
                )
            ):
                raise ValueError("Unapplied mutation cannot carry result state")
            if error_code is None:
                raise ValueError("Unapplied mutation requires error_code")
        expected_ref = repository_mutation_receipt_ref(
            repository_binding_ref=binding_ref,
            operation_ref=operation_ref,
            idempotency_key=idempotency_key,
        )
        if self.mutation_receipt_ref != expected_ref:
            raise ValueError("Mutation receipt ref is not deterministic")
        object.__setattr__(self, "repository_binding_ref", binding_ref)
        object.__setattr__(self, "operation_ref", operation_ref)
        object.__setattr__(self, "idempotency_key", idempotency_key)
        object.__setattr__(self, "target_path", target_path)
        object.__setattr__(self, "expected_content_digest", expected_digest)
        object.__setattr__(self, "context_refs", context_refs)
        object.__setattr__(self, "result_entry_ref", result_entry_ref)
        object.__setattr__(self, "result_content_digest", result_digest)
        object.__setattr__(self, "request_body_evidence_ref", request_body_ref)
        object.__setattr__(self, "result_body_evidence_ref", result_body_ref)
        object.__setattr__(self, "delta_evidence_ref", delta_ref)
        object.__setattr__(self, "error_code", error_code)


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryChangeEvidence:
    evidence_ref: str
    evidence_key: str
    revision: int
    repository_binding_ref: str
    posture: RepositoryEvidencePosture
    resolution_state: RepositoryEvidenceResolutionState
    observed_at: datetime
    before_coordinate: WorkspaceRepositoryEvidenceCoordinate | None = None
    after_coordinate: WorkspaceRepositoryEvidenceCoordinate | None = None
    changed_entries: tuple[WorkspaceRepositoryChangedEntry, ...] = ()
    external_evidence_refs: tuple[str, ...] = ()
    mutation_receipt_refs: tuple[str, ...] = ()
    committed_revision_refs: tuple[str, ...] = ()
    reason: str | None = None
    complete: bool = True
    truncated: bool = False
    next_continuation_ref: str | None = None
    resolved_at: datetime | None = None

    def __post_init__(self) -> None:
        binding_ref = _required(self.repository_binding_ref, "repository_binding_ref")
        evidence_key = _required(self.evidence_key, "evidence_key")
        if self.revision < 0:
            raise ValueError("Evidence revision must be non-negative")
        before = self.before_coordinate
        after = self.after_coordinate
        if (before is None) != (after is None):
            raise ValueError("Evidence coordinates require both baseline and target")
        if before is not None and after is not None:
            _same_binding(before, after)
            if before.repository_binding_ref != binding_ref:
                raise ValueError("Evidence coordinate binding differs")
        entries = tuple(
            sorted(
                self.changed_entries,
                key=lambda item: (item.old_path or "", item.new_path or ""),
            )
        )
        if len(entries) > MAX_CHANGED_ENTRIES:
            raise ValueError("Changed entry count exceeds bound")
        if len({item.changed_entry_ref for item in entries}) != len(entries):
            raise ValueError("Changed entry refs must be unique")
        for entry in entries:
            if entry.before_coordinate != before or entry.after_coordinate != after:
                raise ValueError("Changed entry coordinates differ from evidence")
            if entry.posture is not self.posture:
                raise ValueError("Changed entry posture differs from evidence")
        external_refs = _unique_refs(
            self.external_evidence_refs,
            "external_evidence_refs",
            MAX_CONTEXT_REFS,
        )
        mutation_refs = _unique_refs(
            self.mutation_receipt_refs,
            "mutation_receipt_refs",
            MAX_CONTEXT_REFS,
        )
        revision_refs = _unique_refs(
            self.committed_revision_refs,
            "committed_revision_refs",
            MAX_CONTEXT_REFS,
        )
        reason = _optional(self.reason, "reason")
        expected_state = _resolution_state(self.posture)
        if self.resolution_state is not expected_state:
            raise ValueError("Evidence posture and resolution state differ")
        _validate_evidence_provenance(
            posture=self.posture,
            before=before,
            after=after,
            entries=entries,
            external_refs=external_refs,
            mutation_refs=mutation_refs,
            revision_refs=revision_refs,
            reason=reason,
        )
        if self.complete and (self.truncated or self.next_continuation_ref is not None):
            raise ValueError("Complete evidence cannot be truncated or continue")
        if (
            not self.complete
            and not self.truncated
            and self.next_continuation_ref is None
        ):
            raise ValueError("Incomplete evidence requires truncation or continuation")
        expected_ref = repository_change_evidence_ref(
            repository_binding_ref=binding_ref,
            evidence_key=evidence_key,
        )
        if self.evidence_ref != expected_ref:
            raise ValueError("Change evidence ref is not deterministic")
        resolved_at = _optional_utc(self.resolved_at)
        observed_at = _utc(self.observed_at)
        if resolved_at is not None and resolved_at < observed_at:
            raise ValueError("Evidence resolution precedes observation")
        object.__setattr__(self, "evidence_key", evidence_key)
        object.__setattr__(self, "repository_binding_ref", binding_ref)
        object.__setattr__(self, "observed_at", observed_at)
        object.__setattr__(self, "resolved_at", resolved_at)
        object.__setattr__(self, "changed_entries", entries)
        object.__setattr__(self, "external_evidence_refs", external_refs)
        object.__setattr__(self, "mutation_receipt_refs", mutation_refs)
        object.__setattr__(self, "committed_revision_refs", revision_refs)
        object.__setattr__(self, "reason", reason)
        object.__setattr__(
            self,
            "next_continuation_ref",
            _optional(self.next_continuation_ref, "next_continuation_ref"),
        )


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryDiffRequest:
    request_ref: str
    evidence_ref: str
    repository_binding_ref: str
    baseline: WorkspaceRepositoryEvidenceCoordinate
    target: WorkspaceRepositoryEvidenceCoordinate
    maximum_files: int
    maximum_lines: int
    maximum_bytes: int
    context_lines: int = 3
    changed_entry_ref: str | None = None
    continuation_ref: str | None = None
    cancellation_ref: str | None = None
    correlation_ref: str | None = None
    binary_policy: RepositoryDiffBinaryPolicy = RepositoryDiffBinaryPolicy.METADATA_ONLY

    def __post_init__(self) -> None:
        binding_ref = _required(self.repository_binding_ref, "repository_binding_ref")
        _same_binding(self.baseline, self.target)
        if self.baseline.repository_binding_ref != binding_ref:
            raise ValueError("Diff coordinate binding differs")
        _positive_bound(self.maximum_files, MAX_DIFF_FILE_BUDGET, "maximum_files")
        _positive_bound(self.maximum_lines, MAX_DIFF_LINE_BUDGET, "maximum_lines")
        _positive_bound(self.maximum_bytes, MAX_DIFF_BYTE_BUDGET, "maximum_bytes")
        if not 0 <= self.context_lines <= 20:
            raise ValueError("Diff context_lines must be from 0 through 20")
        evidence_ref = _required(self.evidence_ref, "evidence_ref")
        changed_entry_ref = _optional(self.changed_entry_ref, "changed_entry_ref")
        continuation_ref = _optional(self.continuation_ref, "continuation_ref")
        cancellation_ref = _optional(self.cancellation_ref, "cancellation_ref")
        correlation_ref = _optional(self.correlation_ref, "correlation_ref")
        expected_ref = repository_diff_request_ref(
            evidence_ref=evidence_ref,
            repository_binding_ref=binding_ref,
            baseline=self.baseline,
            target=self.target,
            changed_entry_ref=changed_entry_ref,
            continuation_ref=continuation_ref,
            maximum_files=self.maximum_files,
            maximum_lines=self.maximum_lines,
            maximum_bytes=self.maximum_bytes,
            context_lines=self.context_lines,
            binary_policy=self.binary_policy,
        )
        if self.request_ref != expected_ref:
            raise ValueError("Diff request ref is not deterministic")
        object.__setattr__(self, "evidence_ref", evidence_ref)
        object.__setattr__(self, "repository_binding_ref", binding_ref)
        object.__setattr__(self, "changed_entry_ref", changed_entry_ref)
        object.__setattr__(self, "continuation_ref", continuation_ref)
        object.__setattr__(self, "cancellation_ref", cancellation_ref)
        object.__setattr__(self, "correlation_ref", correlation_ref)


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryDiffLine:
    kind: RepositoryDiffLineKind
    text: str
    old_line_number: int | None = None
    new_line_number: int | None = None
    no_newline: bool = False

    def __post_init__(self) -> None:
        if len(self.text) > MAX_DIFF_LINE_CHARACTERS:
            raise ValueError("Diff line exceeds character bound")
        _optional_positive(self.old_line_number, "old_line_number")
        _optional_positive(self.new_line_number, "new_line_number")
        expected = {
            RepositoryDiffLineKind.CONTEXT: (True, True),
            RepositoryDiffLineKind.ADDITION: (False, True),
            RepositoryDiffLineKind.DELETION: (True, False),
        }[self.kind]
        actual = (self.old_line_number is not None, self.new_line_number is not None)
        if actual != expected:
            raise ValueError("Diff line numbers differ from line kind")


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryDiffHunk:
    hunk_ref: str
    hunk_index: int
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: tuple[WorkspaceRepositoryDiffLine, ...]

    def __post_init__(self) -> None:
        if self.hunk_index < 0:
            raise ValueError("Diff hunk index must be non-negative")
        if min(self.old_start, self.old_count, self.new_start, self.new_count) < 0:
            raise ValueError("Diff hunk ranges must be non-negative")
        lines = tuple(self.lines)
        if not lines or len(lines) > MAX_DIFF_LINES_PER_HUNK:
            raise ValueError("Diff hunk lines are empty or exceed bound")
        old_consumed = sum(
            line.kind is not RepositoryDiffLineKind.ADDITION for line in lines
        )
        new_consumed = sum(
            line.kind is not RepositoryDiffLineKind.DELETION for line in lines
        )
        if old_consumed != self.old_count or new_consumed != self.new_count:
            raise ValueError("Diff hunk line counts differ from ranges")
        object.__setattr__(self, "lines", lines)


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryDiffFile:
    file_ref: str
    kind: RepositoryChangedEntryKind
    old_path: str | None
    new_path: str | None
    old_content_digest: str | None
    new_content_digest: str | None
    binary: bool
    hunks: tuple[WorkspaceRepositoryDiffHunk, ...] = ()
    changed_entry_ref: str | None = None
    complete: bool = True
    truncated: bool = False
    next_continuation_ref: str | None = None

    def __post_init__(self) -> None:
        old_path = _optional_path(self.old_path)
        new_path = _optional_path(self.new_path)
        _validate_change_paths(self.kind, old_path, new_path)
        old_digest = _optional(self.old_content_digest, "old_content_digest")
        new_digest = _optional(self.new_content_digest, "new_content_digest")
        hunks = tuple(self.hunks)
        if len(hunks) > MAX_DIFF_HUNKS_PER_FILE:
            raise ValueError("Diff file hunk count exceeds bound")
        if self.binary and hunks:
            raise ValueError("Binary diff file cannot carry text hunks")
        indexes = tuple(hunk.hunk_index for hunk in hunks)
        if indexes != tuple(range(len(hunks))):
            raise ValueError("Diff hunk indexes must be contiguous from zero")
        for hunk in hunks:
            expected_hunk_ref = repository_diff_hunk_ref(
                file_ref=self.file_ref,
                hunk_index=hunk.hunk_index,
                old_start=hunk.old_start,
                old_count=hunk.old_count,
                new_start=hunk.new_start,
                new_count=hunk.new_count,
            )
            if hunk.hunk_ref != expected_hunk_ref:
                raise ValueError("Diff hunk ref is not deterministic")
        if self.complete and (self.truncated or self.next_continuation_ref is not None):
            raise ValueError("Complete diff file cannot truncate or continue")
        if (
            not self.complete
            and not self.truncated
            and self.next_continuation_ref is None
        ):
            raise ValueError("Incomplete diff file requires truncation or continuation")
        object.__setattr__(self, "old_path", old_path)
        object.__setattr__(self, "new_path", new_path)
        object.__setattr__(self, "old_content_digest", old_digest)
        object.__setattr__(self, "new_content_digest", new_digest)
        object.__setattr__(self, "hunks", hunks)
        object.__setattr__(
            self,
            "changed_entry_ref",
            _optional(self.changed_entry_ref, "changed_entry_ref"),
        )
        object.__setattr__(
            self,
            "next_continuation_ref",
            _optional(self.next_continuation_ref, "next_continuation_ref"),
        )


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryDiffPage:
    diff_ref: str
    evidence_ref: str
    repository_binding_ref: str
    posture: RepositoryEvidencePosture
    state: RepositoryDiffPageState
    baseline: WorkspaceRepositoryEvidenceCoordinate
    target: WorkspaceRepositoryEvidenceCoordinate
    files: tuple[WorkspaceRepositoryDiffFile, ...]
    returned_file_count: int
    total_file_count: int | None
    complete: bool
    truncated: bool = False
    continuation_ref: str | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        binding_ref = _required(self.repository_binding_ref, "repository_binding_ref")
        evidence_ref = _required(self.evidence_ref, "evidence_ref")
        _same_binding(self.baseline, self.target)
        if self.baseline.repository_binding_ref != binding_ref:
            raise ValueError("Diff page coordinate binding differs")
        allowed_postures = {
            RepositoryEvidencePosture.WORKSPACE_OBSERVED,
            RepositoryEvidencePosture.PROVIDER_CORRELATED,
            RepositoryEvidencePosture.WORKSPACE_AUTHORIZED,
            RepositoryEvidencePosture.COMMITTED_REVISION,
            RepositoryEvidencePosture.GAP,
        }
        if self.posture not in allowed_postures:
            raise ValueError("Workspace diff page posture is not authoritative enough")
        files = tuple(self.files)
        if len(files) > MAX_DIFF_FILES_PER_PAGE:
            raise ValueError("Diff page file count exceeds bound")
        if self.returned_file_count != len(files):
            raise ValueError("Diff returned file count differs")
        if self.total_file_count is not None and self.total_file_count < len(files):
            raise ValueError("Diff total file count is smaller than page")
        continuation_ref = _optional(self.continuation_ref, "continuation_ref")
        reason = _optional(self.reason, "reason")
        if self.state in {
            RepositoryDiffPageState.STALE,
            RepositoryDiffPageState.UNAVAILABLE,
            RepositoryDiffPageState.GAP,
        }:
            if files or reason is None or self.complete:
                raise ValueError("Unavailable diff state requires empty reasoned page")
        else:
            if reason is not None:
                raise ValueError("Available diff state cannot carry failure reason")
            if self.state is RepositoryDiffPageState.BINARY and any(
                not value.binary for value in files
            ):
                raise ValueError("Binary diff page must contain only binary files")
        if (
            self.posture is RepositoryEvidencePosture.GAP
            and self.state is not RepositoryDiffPageState.GAP
        ):
            raise ValueError("Gap posture requires gap page state")
        if (
            self.state is RepositoryDiffPageState.GAP
            and self.posture is not RepositoryEvidencePosture.GAP
        ):
            raise ValueError("Gap page state requires gap posture")
        if self.complete and (self.truncated or continuation_ref is not None):
            raise ValueError("Complete diff page cannot truncate or continue")
        if (
            not self.complete
            and not self.truncated
            and continuation_ref is None
            and reason is None
        ):
            raise ValueError("Incomplete diff page requires continuation or reason")
        expected_diff_ref = repository_diff_ref(
            repository_binding_ref=binding_ref,
            evidence_ref=evidence_ref,
            baseline=self.baseline,
            target=self.target,
        )
        if self.diff_ref != expected_diff_ref:
            raise ValueError("Diff ref is not deterministic")
        for file in files:
            expected_file_ref = repository_diff_file_ref(
                diff_ref=self.diff_ref,
                kind=file.kind,
                old_path=file.old_path,
                new_path=file.new_path,
            )
            if file.file_ref != expected_file_ref:
                raise ValueError("Diff file ref is not deterministic")
        object.__setattr__(self, "evidence_ref", evidence_ref)
        object.__setattr__(self, "repository_binding_ref", binding_ref)
        object.__setattr__(self, "files", files)
        object.__setattr__(self, "continuation_ref", continuation_ref)
        object.__setattr__(self, "reason", reason)


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryEvidenceCheckpoint:
    consumer_key: str
    repository_binding_ref: str
    observer_epoch: str
    accepted_cursor: int
    evidence_revision: int
    projection_digest: str
    accepted_at: datetime
    reset_required: bool = False

    def __post_init__(self) -> None:
        if self.accepted_cursor < 0 or self.evidence_revision < 0:
            raise ValueError("Evidence checkpoint coordinates must be non-negative")
        object.__setattr__(
            self, "consumer_key", _required(self.consumer_key, "consumer_key")
        )
        object.__setattr__(
            self,
            "repository_binding_ref",
            _required(self.repository_binding_ref, "repository_binding_ref"),
        )
        object.__setattr__(
            self, "observer_epoch", _required(self.observer_epoch, "observer_epoch")
        )
        object.__setattr__(
            self,
            "projection_digest",
            _required(self.projection_digest, "projection_digest"),
        )
        object.__setattr__(self, "accepted_at", _utc(self.accepted_at))


def repository_change_evidence_ref(
    *, repository_binding_ref: str, evidence_key: str
) -> str:
    return _digest_ref(
        "workspace-repository-change-evidence",
        _required(repository_binding_ref, "repository_binding_ref"),
        _required(evidence_key, "evidence_key"),
    )


def validate_repository_change_evidence_advance(
    previous: WorkspaceRepositoryChangeEvidence,
    candidate: WorkspaceRepositoryChangeEvidence,
) -> None:
    if (
        candidate.evidence_ref != previous.evidence_ref
        or candidate.evidence_key != previous.evidence_key
        or candidate.repository_binding_ref != previous.repository_binding_ref
    ):
        raise ValueError("Evidence advance cannot change stable identity or binding")
    if candidate.revision != previous.revision + 1:
        raise ValueError("Evidence advance revision must increase by exactly one")
    if candidate.observed_at != previous.observed_at:
        raise ValueError("Evidence advance cannot rewrite first observation time")
    allowed = {
        RepositoryEvidencePosture.PROVIDER_REPORTED: {
            RepositoryEvidencePosture.PROVIDER_REPORTED,
            RepositoryEvidencePosture.PROVIDER_CORRELATED,
            RepositoryEvidencePosture.WORKSPACE_AUTHORIZED,
            RepositoryEvidencePosture.COMMITTED_REVISION,
            RepositoryEvidencePosture.AMBIGUOUS,
            RepositoryEvidencePosture.GAP,
        },
        RepositoryEvidencePosture.WORKSPACE_OBSERVED: {
            RepositoryEvidencePosture.WORKSPACE_OBSERVED,
            RepositoryEvidencePosture.PROVIDER_CORRELATED,
            RepositoryEvidencePosture.WORKSPACE_AUTHORIZED,
            RepositoryEvidencePosture.COMMITTED_REVISION,
            RepositoryEvidencePosture.AMBIGUOUS,
            RepositoryEvidencePosture.GAP,
        },
        RepositoryEvidencePosture.PROVIDER_CORRELATED: {
            RepositoryEvidencePosture.PROVIDER_CORRELATED,
            RepositoryEvidencePosture.WORKSPACE_AUTHORIZED,
            RepositoryEvidencePosture.COMMITTED_REVISION,
            RepositoryEvidencePosture.AMBIGUOUS,
            RepositoryEvidencePosture.GAP,
        },
        RepositoryEvidencePosture.WORKSPACE_AUTHORIZED: {
            RepositoryEvidencePosture.WORKSPACE_AUTHORIZED,
            RepositoryEvidencePosture.COMMITTED_REVISION,
        },
        RepositoryEvidencePosture.COMMITTED_REVISION: {
            RepositoryEvidencePosture.COMMITTED_REVISION,
        },
        RepositoryEvidencePosture.AMBIGUOUS: {
            RepositoryEvidencePosture.PROVIDER_CORRELATED,
            RepositoryEvidencePosture.WORKSPACE_AUTHORIZED,
            RepositoryEvidencePosture.COMMITTED_REVISION,
            RepositoryEvidencePosture.AMBIGUOUS,
            RepositoryEvidencePosture.GAP,
        },
        RepositoryEvidencePosture.GAP: set(RepositoryEvidencePosture),
    }[previous.posture]
    if candidate.posture not in allowed:
        raise ValueError("Evidence advance cannot downgrade authority posture")
    provenance_fields = (
        "external_evidence_refs",
        "mutation_receipt_refs",
        "committed_revision_refs",
    )
    for field_name in provenance_fields:
        previous_refs = set(getattr(previous, field_name))
        candidate_refs = set(getattr(candidate, field_name))
        if not previous_refs.issubset(candidate_refs):
            raise ValueError("Evidence advance cannot erase provenance refs")


def repository_changed_entry_ref(
    *,
    repository_binding_ref: str,
    before_coordinate: WorkspaceRepositoryEvidenceCoordinate,
    after_coordinate: WorkspaceRepositoryEvidenceCoordinate,
    kind: RepositoryChangedEntryKind,
    old_path: str | None,
    new_path: str | None,
) -> str:
    _same_binding(before_coordinate, after_coordinate)
    return _digest_ref(
        "workspace-repository-changed-entry",
        _required(repository_binding_ref, "repository_binding_ref"),
        _coordinate_token(before_coordinate),
        _coordinate_token(after_coordinate),
        kind.value,
        old_path or "",
        new_path or "",
    )


def repository_mutation_receipt_ref(
    *, repository_binding_ref: str, operation_ref: str, idempotency_key: str
) -> str:
    return _digest_ref(
        "workspace-repository-mutation-receipt",
        _required(repository_binding_ref, "repository_binding_ref"),
        _required(operation_ref, "operation_ref"),
        _required(idempotency_key, "idempotency_key"),
    )


def repository_diff_ref(
    *,
    repository_binding_ref: str,
    evidence_ref: str,
    baseline: WorkspaceRepositoryEvidenceCoordinate,
    target: WorkspaceRepositoryEvidenceCoordinate,
) -> str:
    _same_binding(baseline, target)
    return _digest_ref(
        "workspace-repository-diff",
        _required(repository_binding_ref, "repository_binding_ref"),
        _required(evidence_ref, "evidence_ref"),
        _coordinate_token(baseline),
        _coordinate_token(target),
    )


def repository_diff_request_ref(
    *,
    evidence_ref: str,
    repository_binding_ref: str,
    baseline: WorkspaceRepositoryEvidenceCoordinate,
    target: WorkspaceRepositoryEvidenceCoordinate,
    changed_entry_ref: str | None,
    continuation_ref: str | None,
    maximum_files: int,
    maximum_lines: int,
    maximum_bytes: int,
    context_lines: int,
    binary_policy: RepositoryDiffBinaryPolicy,
) -> str:
    return _digest_ref(
        "workspace-repository-diff-request",
        _required(evidence_ref, "evidence_ref"),
        _required(repository_binding_ref, "repository_binding_ref"),
        _coordinate_token(baseline),
        _coordinate_token(target),
        changed_entry_ref or "",
        continuation_ref or "",
        str(maximum_files),
        str(maximum_lines),
        str(maximum_bytes),
        str(context_lines),
        binary_policy.value,
    )


def repository_diff_file_ref(
    *,
    diff_ref: str,
    kind: RepositoryChangedEntryKind,
    old_path: str | None,
    new_path: str | None,
) -> str:
    return _digest_ref(
        "workspace-repository-diff-file",
        _required(diff_ref, "diff_ref"),
        kind.value,
        old_path or "",
        new_path or "",
    )


def repository_diff_hunk_ref(
    *,
    file_ref: str,
    hunk_index: int,
    old_start: int,
    old_count: int,
    new_start: int,
    new_count: int,
) -> str:
    return _digest_ref(
        "workspace-repository-diff-hunk",
        _required(file_ref, "file_ref"),
        str(hunk_index),
        str(old_start),
        str(old_count),
        str(new_start),
        str(new_count),
    )


def repository_diff_continuation_ref(
    *, diff_ref: str, last_file_ref: str, page_index: int
) -> str:
    if page_index < 0:
        raise ValueError("Diff continuation page index must be non-negative")
    return _digest_ref(
        "workspace-repository-diff-continuation",
        _required(diff_ref, "diff_ref"),
        _required(last_file_ref, "last_file_ref"),
        str(page_index),
    )


def _validate_evidence_provenance(
    *,
    posture: RepositoryEvidencePosture,
    before: WorkspaceRepositoryEvidenceCoordinate | None,
    after: WorkspaceRepositoryEvidenceCoordinate | None,
    entries: tuple[WorkspaceRepositoryChangedEntry, ...],
    external_refs: tuple[str, ...],
    mutation_refs: tuple[str, ...],
    revision_refs: tuple[str, ...],
    reason: str | None,
) -> None:
    has_state = before is not None and after is not None and bool(entries)
    if posture is RepositoryEvidencePosture.PROVIDER_REPORTED:
        if (
            not external_refs
            or before is not None
            or entries
            or mutation_refs
            or revision_refs
            or reason is not None
        ):
            raise ValueError("Provider report requires external-only provenance")
    elif posture is RepositoryEvidencePosture.WORKSPACE_OBSERVED:
        if (
            not has_state
            or external_refs
            or mutation_refs
            or revision_refs
            or reason is not None
        ):
            raise ValueError("Workspace observation provenance is inconsistent")
    elif posture is RepositoryEvidencePosture.PROVIDER_CORRELATED:
        if (
            not has_state
            or not external_refs
            or mutation_refs
            or revision_refs
            or reason is not None
        ):
            raise ValueError("Provider correlation provenance is inconsistent")
    elif posture is RepositoryEvidencePosture.WORKSPACE_AUTHORIZED:
        if not has_state or not mutation_refs or reason is not None:
            raise ValueError("Workspace authorization requires mutation receipt")
    elif posture is RepositoryEvidencePosture.COMMITTED_REVISION:
        if (
            not has_state
            or before is None
            or after is None
            or before.kind is not RepositoryEvidenceCoordinateKind.COMMITTED_REVISION
            or after.kind is not RepositoryEvidenceCoordinateKind.COMMITTED_REVISION
            or not revision_refs
            or reason is not None
        ):
            raise ValueError("Committed evidence requires exact revision provenance")
    elif posture is RepositoryEvidencePosture.AMBIGUOUS:
        if reason is None or not (external_refs or has_state) or mutation_refs:
            raise ValueError("Ambiguous evidence requires evidence and reason")
    elif (
        reason is None
        or before is not None
        or entries
        or mutation_refs
        or revision_refs
    ):
        raise ValueError("Gap evidence requires reason without Workspace state")


def _resolution_state(
    posture: RepositoryEvidencePosture,
) -> RepositoryEvidenceResolutionState:
    if posture is RepositoryEvidencePosture.PROVIDER_REPORTED:
        return RepositoryEvidenceResolutionState.REPORTED
    if posture is RepositoryEvidencePosture.AMBIGUOUS:
        return RepositoryEvidenceResolutionState.AMBIGUOUS
    if posture is RepositoryEvidencePosture.GAP:
        return RepositoryEvidenceResolutionState.GAP
    return RepositoryEvidenceResolutionState.RESOLVED


def _validate_change_paths(
    kind: RepositoryChangedEntryKind, old_path: str | None, new_path: str | None
) -> None:
    if kind is RepositoryChangedEntryKind.CREATE:
        if old_path is not None or new_path is None:
            raise ValueError("Create diff file requires only new path")
    elif kind is RepositoryChangedEntryKind.DELETE:
        if old_path is None or new_path is not None:
            raise ValueError("Delete diff file requires only old path")
    elif kind is RepositoryChangedEntryKind.RENAME:
        if old_path is None or new_path is None or old_path == new_path:
            raise ValueError("Rename diff file requires distinct old/new paths")
    elif old_path is None or new_path is None or old_path != new_path:
        raise ValueError("Update/binary diff file requires one stable path")


def _coordinate_token(value: WorkspaceRepositoryEvidenceCoordinate) -> str:
    if value.observation is not None:
        observation = value.observation
        return "|".join(
            (
                value.kind.value,
                value.repository_binding_ref,
                observation.epoch,
                str(observation.cursor),
                observation.snapshot_digest,
                observation.visibility_policy_ref,
                observation.visibility_policy_version,
            )
        )
    return "|".join(
        (
            value.kind.value,
            value.repository_binding_ref,
            value.revision_ref or "",
            value.state_digest,
        )
    )


def _validate_observation_coordinate(value: RepositoryObservationCoordinate) -> None:
    _required(value.repository_binding_ref, "repository_binding_ref")
    _required(value.epoch, "epoch")
    if value.cursor < 0:
        raise ValueError("Observation coordinate cursor must be non-negative")
    _required(value.snapshot_digest, "snapshot_digest")
    _required(value.visibility_policy_ref, "visibility_policy_ref")
    _required(value.visibility_policy_version, "visibility_policy_version")


def _same_binding(
    first: WorkspaceRepositoryEvidenceCoordinate,
    second: WorkspaceRepositoryEvidenceCoordinate,
) -> None:
    if first.repository_binding_ref != second.repository_binding_ref:
        raise ValueError("Repository evidence coordinates use different bindings")


def _digest_ref(prefix: str, *values: str) -> str:
    digest = hashlib.sha256()
    for value in values:
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return f"{prefix}:sha256:{digest.hexdigest()}"


def _relative_path(value: str) -> str:
    normalized = value.strip().replace("\\", "/")
    path = PurePosixPath(normalized)
    if (
        not normalized
        or len(normalized) > 4096
        or path.is_absolute()
        or path.as_posix() != normalized
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError(f"Repository path must be confined and relative: {value!r}")
    return normalized


def _optional_path(value: str | None) -> str | None:
    return None if value is None else _relative_path(value)


def _required(value: str | None, field_name: str) -> str:
    if value is None:
        raise ValueError(f"{field_name} is required")
    normalized = value.strip()
    if not normalized or len(normalized) > 4096:
        raise ValueError(f"{field_name} must be bounded non-empty text")
    return normalized


def _optional(value: str | None, field_name: str) -> str | None:
    return None if value is None else _required(value, field_name)


def _unique_refs(
    values: tuple[str, ...], field_name: str, maximum: int
) -> tuple[str, ...]:
    refs = tuple(_required(value, field_name) for value in values)
    if len(refs) > maximum or len(refs) != len(set(refs)):
        raise ValueError(f"{field_name} must be unique and bounded")
    return refs


def _positive_bound(value: int, maximum: int, field_name: str) -> None:
    if isinstance(value, bool) or not 0 < value <= maximum:
        raise ValueError(f"{field_name} must be positive and bounded")


def _optional_non_negative(value: int | None, field_name: str) -> None:
    if value is not None and (isinstance(value, bool) or value < 0):
        raise ValueError(f"{field_name} must be non-negative")


def _optional_positive(value: int | None, field_name: str) -> None:
    if value is not None and (isinstance(value, bool) or value <= 0):
        raise ValueError(f"{field_name} must be positive")


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _optional_utc(value: datetime | None) -> datetime | None:
    return None if value is None else _utc(value)
