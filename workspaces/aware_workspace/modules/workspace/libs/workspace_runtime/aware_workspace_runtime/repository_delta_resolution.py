from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from .change_evidence import (
    MAX_CONTEXT_REFS,
    RepositoryEvidenceCoordinateKind,
    RepositoryEvidenceResolutionState,
    WorkspaceRepositoryChangedEntry,
    WorkspaceRepositoryChangeEvidence,
)
from .repository_access import RepositoryObservationCoordinate
from .repository_delta import (
    RepositoryContentDeltaState,
    WorkspaceRepositoryContentDelta,
    WorkspaceRepositoryDeltaCapture,
)


class WorkspaceRepositoryDeltaIndex(Protocol):
    @property
    def repository_binding_ref(self) -> str: ...

    def retained_captures(self) -> tuple[WorkspaceRepositoryDeltaCapture, ...]: ...

    def retained_deltas(self) -> tuple[WorkspaceRepositoryContentDelta, ...]: ...

    def contains_body(self, body_ref: str) -> bool: ...


class RepositoryContentDeltaResolutionState(StrEnum):
    AVAILABLE = "available"
    PENDING = "pending"
    MISSING_CAPTURE = "missing_capture"
    MISSING_DELTA = "missing_delta"
    AMBIGUOUS = "ambiguous"
    INCOMPATIBLE = "incompatible"
    UNAVAILABLE = "unavailable"
    EVICTED = "evicted"
    GAP = "gap"


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryContentDeltaResolution:
    resolution_ref: str
    repository_binding_ref: str
    evidence_ref: str
    evidence_revision: int
    context_refs: tuple[str, ...]
    state: RepositoryContentDeltaResolutionState
    capture_ref: str | None = None
    delta_refs: tuple[str, ...] = ()
    reason: str | None = None

    def __post_init__(self) -> None:
        binding_ref = _required(self.repository_binding_ref, "repository_binding_ref")
        evidence_ref = _required(self.evidence_ref, "evidence_ref")
        if isinstance(self.evidence_revision, bool) or self.evidence_revision < 0:
            raise ValueError("Evidence revision must be non-negative")
        context_refs = _context_refs(self.context_refs)
        expected_ref = repository_content_delta_resolution_ref(
            repository_binding_ref=binding_ref,
            evidence_ref=evidence_ref,
            evidence_revision=self.evidence_revision,
            context_refs=context_refs,
        )
        if self.resolution_ref != expected_ref:
            raise ValueError("Content delta resolution ref is not deterministic")
        capture_ref = (
            None
            if self.capture_ref is None
            else _required(self.capture_ref, "capture_ref")
        )
        delta_refs = tuple(_required(value, "delta_ref") for value in self.delta_refs)
        if len(set(delta_refs)) != len(delta_refs):
            raise ValueError("Content delta refs must be unique")
        reason = None if self.reason is None else _required(self.reason, "reason")
        if self.state is RepositoryContentDeltaResolutionState.AVAILABLE:
            if not delta_refs or reason is not None:
                raise ValueError("Available resolution requires exact deltas")
        elif delta_refs:
            raise ValueError("Unavailable resolution cannot claim content deltas")
        elif reason is None:
            raise ValueError("Unavailable resolution requires reason")
        object.__setattr__(self, "repository_binding_ref", binding_ref)
        object.__setattr__(self, "evidence_ref", evidence_ref)
        object.__setattr__(self, "context_refs", context_refs)
        object.__setattr__(self, "capture_ref", capture_ref)
        object.__setattr__(self, "delta_refs", delta_refs)
        object.__setattr__(self, "reason", reason)


class WorkspaceRepositoryContentDeltaResolver:
    """Join exact Workspace evidence to retained delta refs without body I/O."""

    def __init__(self, *, store: WorkspaceRepositoryDeltaIndex) -> None:
        self._store = store

    @property
    def store(self) -> WorkspaceRepositoryDeltaIndex:
        return self._store

    def resolve(
        self,
        evidence: WorkspaceRepositoryChangeEvidence,
        *,
        context_refs: tuple[str, ...],
        observed_epoch: str | None = None,
        observed_cursor: int | None = None,
        resident_error: str | None = None,
    ) -> WorkspaceRepositoryContentDeltaResolution:
        contexts = _context_refs(context_refs)
        common = {
            "resolution_ref": repository_content_delta_resolution_ref(
                repository_binding_ref=evidence.repository_binding_ref,
                evidence_ref=evidence.evidence_ref,
                evidence_revision=evidence.revision,
                context_refs=contexts,
            ),
            "repository_binding_ref": evidence.repository_binding_ref,
            "evidence_ref": evidence.evidence_ref,
            "evidence_revision": evidence.revision,
            "context_refs": contexts,
        }
        if evidence.repository_binding_ref != self._store.repository_binding_ref:
            return WorkspaceRepositoryContentDeltaResolution(
                **common,
                state=RepositoryContentDeltaResolutionState.INCOMPATIBLE,
                reason="evidence repository binding differs from delta store",
            )
        before = evidence.before_coordinate
        after = evidence.after_coordinate
        if (
            evidence.resolution_state is not RepositoryEvidenceResolutionState.RESOLVED
            or before is None
            or after is None
            or before.kind is not RepositoryEvidenceCoordinateKind.OBSERVATION
            or after.kind is not RepositoryEvidenceCoordinateKind.OBSERVATION
            or before.observation is None
            or after.observation is None
            or not evidence.changed_entries
        ):
            return WorkspaceRepositoryContentDeltaResolution(
                **common,
                state=RepositoryContentDeltaResolutionState.INCOMPATIBLE,
                reason="evidence does not carry one resolved observation transition",
            )
        captures = tuple(
            capture
            for capture in self._store.retained_captures()
            if _capture_is_compatible(
                capture,
                before=before.observation,
                context_refs=contexts,
            )
        )
        if not captures:
            return WorkspaceRepositoryContentDeltaResolution(
                **common,
                state=RepositoryContentDeltaResolutionState.MISSING_CAPTURE,
                reason="no retained selected-path preimage covers this context",
            )
        capture_by_entry: list[WorkspaceRepositoryDeltaCapture] = []
        for entry in evidence.changed_entries:
            entry_paths = _entry_paths(entry)
            candidates = tuple(
                capture
                for capture in captures
                if entry_paths.issubset(capture.selected_paths)
            )
            if not candidates:
                return WorkspaceRepositoryContentDeltaResolution(
                    **common,
                    state=RepositoryContentDeltaResolutionState.MISSING_CAPTURE,
                    reason="no retained selected-path preimage covers one changed entry",
                )
            if len(candidates) > 1:
                return WorkspaceRepositoryContentDeltaResolution(
                    **common,
                    state=RepositoryContentDeltaResolutionState.AMBIGUOUS,
                    reason="multiple retained captures cover one changed entry",
                )
            capture_by_entry.append(candidates[0])

        retained_deltas = self._store.retained_deltas()
        deltas: list[WorkspaceRepositoryContentDelta] = []
        missing_delta = False
        for entry, capture in zip(
            evidence.changed_entries,
            capture_by_entry,
            strict=True,
        ):
            matches = _matching_entry_deltas(
                capture,
                entry,
                before=before.observation,
                after=after.observation,
                retained=retained_deltas,
            )
            if len(matches) > 1:
                return WorkspaceRepositoryContentDeltaResolution(
                    **common,
                    state=RepositoryContentDeltaResolutionState.AMBIGUOUS,
                    reason="multiple retained deltas match one changed entry",
                )
            if not matches:
                missing_delta = True
                continue
            deltas.append(matches[0])

        selected_capture_refs = tuple(
            dict.fromkeys(capture.capture_ref for capture in capture_by_entry)
        )
        single_capture_ref = (
            selected_capture_refs[0] if len(selected_capture_refs) == 1 else None
        )
        if not missing_delta:
            unavailable = tuple(
                delta
                for delta in deltas
                if delta.state
                not in {
                    RepositoryContentDeltaState.AVAILABLE,
                    RepositoryContentDeltaState.BINARY,
                }
            )
            if unavailable:
                states = ",".join(sorted({value.state.value for value in unavailable}))
                return WorkspaceRepositoryContentDeltaResolution(
                    **common,
                    state=RepositoryContentDeltaResolutionState.UNAVAILABLE,
                    capture_ref=single_capture_ref,
                    reason=f"content delta state is unavailable: {states}",
                )
            body_refs = {
                body_ref
                for delta in deltas
                for body_ref in (delta.old_body_ref, delta.new_body_ref)
                if body_ref is not None
            }
            if any(not self._store.contains_body(body_ref) for body_ref in body_refs):
                return WorkspaceRepositoryContentDeltaResolution(
                    **common,
                    state=RepositoryContentDeltaResolutionState.EVICTED,
                    capture_ref=single_capture_ref,
                    reason="one or more exact content delta bodies were evicted",
                )
            return WorkspaceRepositoryContentDeltaResolution(
                **common,
                state=RepositoryContentDeltaResolutionState.AVAILABLE,
                capture_ref=single_capture_ref,
                delta_refs=tuple(value.delta_ref for value in deltas),
            )
        if resident_error is not None:
            return WorkspaceRepositoryContentDeltaResolution(
                **common,
                state=RepositoryContentDeltaResolutionState.GAP,
                capture_ref=single_capture_ref,
                reason=f"delta resident cannot reach target: {resident_error}",
            )
        if (
            observed_epoch == after.observation.epoch
            and observed_cursor is not None
            and observed_cursor < after.observation.cursor
        ):
            return WorkspaceRepositoryContentDeltaResolution(
                **common,
                state=RepositoryContentDeltaResolutionState.PENDING,
                capture_ref=single_capture_ref,
                reason="delta resident has not consumed the evidence target cursor",
            )
        return WorkspaceRepositoryContentDeltaResolution(
            **common,
            state=RepositoryContentDeltaResolutionState.MISSING_DELTA,
            capture_ref=single_capture_ref,
            reason="retained capture set lacks an exact content delta transition",
        )


def repository_content_delta_resolution_ref(
    *,
    repository_binding_ref: str,
    evidence_ref: str,
    evidence_revision: int,
    context_refs: tuple[str, ...],
) -> str:
    digest = hashlib.sha256()
    for value in (
        _required(repository_binding_ref, "repository_binding_ref"),
        _required(evidence_ref, "evidence_ref"),
        str(evidence_revision),
        *_context_refs(context_refs),
    ):
        digest.update(value.encode("utf-8"))
        digest.update(b"\0")
    return f"workspace-content-delta-resolution:{digest.hexdigest()}"


def _capture_is_compatible(
    capture: WorkspaceRepositoryDeltaCapture,
    *,
    before: RepositoryObservationCoordinate,
    context_refs: tuple[str, ...],
) -> bool:
    observation = capture.admitted_coordinate
    return (
        before.repository_binding_ref == capture.repository_binding_ref
        and before.epoch == observation.epoch
        and observation.cursor <= before.cursor
        and set(context_refs).issubset(capture.context_refs)
    )


def _entry_paths(entry: WorkspaceRepositoryChangedEntry) -> set[str]:
    return {path for path in (entry.old_path, entry.new_path) if path is not None}


def _matching_entry_deltas(
    capture: WorkspaceRepositoryDeltaCapture,
    entry: WorkspaceRepositoryChangedEntry,
    *,
    before: RepositoryObservationCoordinate,
    after: RepositoryObservationCoordinate,
    retained: tuple[WorkspaceRepositoryContentDelta, ...],
) -> tuple[WorkspaceRepositoryContentDelta, ...]:
    return tuple(
        delta
        for delta in retained
        if delta.capture_ref == capture.capture_ref
        and delta.before_coordinate == before
        and delta.after_coordinate == after
        and _delta_matches(delta, entry)
    )


def _delta_matches(
    delta: WorkspaceRepositoryContentDelta,
    entry: WorkspaceRepositoryChangedEntry,
) -> bool:
    return (
        delta.kind is entry.kind
        and delta.old_path == entry.old_path
        and delta.new_path == entry.new_path
    )


def _context_refs(values: tuple[str, ...]) -> tuple[str, ...]:
    result = tuple(dict.fromkeys(_required(value, "context_ref") for value in values))
    if not result or len(result) > MAX_CONTEXT_REFS:
        raise ValueError("Content delta resolution requires bounded context refs")
    return result


def _required(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty")
    return value.strip()
