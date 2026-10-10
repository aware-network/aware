from __future__ import annotations

import asyncio
import os
import stat
import threading
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import PurePosixPath

from aware_workspace_sdk.repository_delta_retention import (
    WorkspaceRepositoryDeltaRetentionClient,
)

from .change_evidence import RepositoryChangedEntryKind
from .contracts import (
    ObservationChangeKind,
    RepositoryObservationChange,
    RepositorySnapshotEntry,
    WorkspaceRepositoryBinding,
    WorkspaceRepositoryObservationBatch,
    WorkspaceRepositoryObservationSnapshot,
)
from .repository_access import (
    WORKSPACE_REPOSITORY_VISIBILITY_POLICY_REF,
    RepositoryObservationCoordinate,
)
from .repository_delta import (
    RepositoryContentDeltaState,
    RepositoryDeltaCapturePathState,
    WorkspaceRepositoryContentDelta,
    WorkspaceRepositoryDeltaCapture,
    WorkspaceRepositoryDeltaCapturePath,
    WorkspaceRepositoryDeltaCapturePolicy,
    repository_content_delta_ref,
    repository_delta_capture_ref,
    repository_delta_selection_digest,
)


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryDeltaCaptureMetrics:
    preparation_count: int
    observed_batch_count: int
    no_change_count: int
    selected_body_read_count: int
    selected_body_read_bytes: int
    changed_body_read_count: int
    changed_body_read_bytes: int
    unstable_body_count: int
    over_budget_body_count: int


class WorkspaceRepositoryDeltaCaptureCoordinator:
    """Bounded body capture over canonical Workspace observation values."""

    def __init__(
        self,
        *,
        binding: WorkspaceRepositoryBinding,
        store: WorkspaceRepositoryDeltaRetentionClient,
    ) -> None:
        if type(store) is not WorkspaceRepositoryDeltaRetentionClient:
            raise TypeError("original Workspace retention client required")
        store.verify_repository_binding(expected_binding_ref=binding.binding_key)
        self._binding = binding
        self._store = store
        self._captures: dict[str, WorkspaceRepositoryDeltaCapture] = {}
        self._path_sequences: dict[str, int] = {}
        self._processed_batches: dict[
            tuple[str, int], tuple[WorkspaceRepositoryContentDelta, ...]
        ] = {}
        self._lock = threading.RLock()
        self._preparation_count = 0
        self._observed_batch_count = 0
        self._no_change_count = 0
        self._selected_body_read_count = 0
        self._selected_body_read_bytes = 0
        self._changed_body_read_count = 0
        self._changed_body_read_bytes = 0
        self._unstable_body_count = 0
        self._over_budget_body_count = 0

    @property
    def binding(self) -> WorkspaceRepositoryBinding:
        return self._binding

    def metrics(self) -> WorkspaceRepositoryDeltaCaptureMetrics:
        with self._lock:
            return WorkspaceRepositoryDeltaCaptureMetrics(
                preparation_count=self._preparation_count,
                observed_batch_count=self._observed_batch_count,
                no_change_count=self._no_change_count,
                selected_body_read_count=self._selected_body_read_count,
                selected_body_read_bytes=self._selected_body_read_bytes,
                changed_body_read_count=self._changed_body_read_count,
                changed_body_read_bytes=self._changed_body_read_bytes,
                unstable_body_count=self._unstable_body_count,
                over_budget_body_count=self._over_budget_body_count,
            )

    async def prepare_async(
        self,
        *,
        snapshot: WorkspaceRepositoryObservationSnapshot,
        selected_paths: tuple[str, ...],
        policy: WorkspaceRepositoryDeltaCapturePolicy,
        context_refs: tuple[str, ...] = (),
    ) -> WorkspaceRepositoryDeltaCapture:
        return await asyncio.to_thread(
            self.prepare,
            snapshot=snapshot,
            selected_paths=selected_paths,
            policy=policy,
            context_refs=context_refs,
        )

    def prepare(
        self,
        *,
        snapshot: WorkspaceRepositoryObservationSnapshot,
        selected_paths: tuple[str, ...],
        policy: WorkspaceRepositoryDeltaCapturePolicy,
        context_refs: tuple[str, ...] = (),
    ) -> WorkspaceRepositoryDeltaCapture:
        self._validate_snapshot(snapshot)
        normalized_paths = _normalized_paths(selected_paths)
        selection_digest = repository_delta_selection_digest(normalized_paths)
        coordinate = _coordinate(snapshot, self._binding.filter_version)
        capture_ref = repository_delta_capture_ref(
            repository_binding_ref=self._binding_ref,
            admitted_coordinate=coordinate,
            selection_digest=selection_digest,
            policy_version=policy.policy_version,
        )
        with self._lock:
            existing = self._captures.get(capture_ref) or self._store.resolve_capture(
                capture_ref
            )
            if existing is not None:
                merged_context = tuple(
                    dict.fromkeys((*existing.context_refs, *context_refs))
                )
                if merged_context == existing.context_refs:
                    self._captures[capture_ref] = existing
                    return existing
                candidate = replace(
                    existing,
                    checkpoint_revision=existing.checkpoint_revision + 1,
                    updated_at=datetime.now(UTC),
                    context_refs=merged_context,
                )
                self._store.record_capture(candidate)
                self._captures[capture_ref] = candidate
                return candidate

            entries = {entry.path: entry for entry in snapshot.entries}
            bodies: list[bytes] = []
            pending: list[tuple[str, RepositorySnapshotEntry, bytes] | None] = []
            states: list[WorkspaceRepositoryDeltaCapturePath] = []
            selected_bytes = 0
            for path in normalized_paths:
                entry = entries.get(path)
                if entry is None:
                    states.append(
                        WorkspaceRepositoryDeltaCapturePath(
                            path=path,
                            state=RepositoryDeltaCapturePathState.ABSENT,
                        )
                    )
                    pending.append(None)
                    continue
                if (
                    entry.size_bytes > policy.maximum_body_bytes
                    or selected_bytes + entry.size_bytes > policy.maximum_selected_bytes
                ):
                    states.append(
                        WorkspaceRepositoryDeltaCapturePath(
                            path=path,
                            state=RepositoryDeltaCapturePathState.OVER_BUDGET,
                            size_bytes=entry.size_bytes,
                            reason="selected body exceeds capture policy",
                        )
                    )
                    pending.append(None)
                    self._over_budget_body_count += 1
                    continue
                try:
                    content = _read_stable_body(
                        root=self._binding.root_path,
                        path=path,
                        entry=entry,
                        maximum_bytes=policy.maximum_body_bytes,
                        maximum_attempts=policy.maximum_read_attempts,
                        on_body_read=self._record_selected_body_read,
                    )
                except _UnstableBody as error:
                    states.append(
                        WorkspaceRepositoryDeltaCapturePath(
                            path=path,
                            state=RepositoryDeltaCapturePathState.UNSTABLE,
                            size_bytes=entry.size_bytes,
                            reason=str(error),
                        )
                    )
                    pending.append(None)
                    self._unstable_body_count += 1
                    continue
                selected_bytes += len(content)
                bodies.append(content)
                states.append(
                    WorkspaceRepositoryDeltaCapturePath(
                        path=path,
                        state=RepositoryDeltaCapturePathState.UNSTABLE,
                        size_bytes=len(content),
                        reason="body ref pending CAS admission",
                    )
                )
                pending.append((path, entry, content))
            body_refs = iter(self._store.record_bodies(tuple(bodies)))
            for index, value in enumerate(pending):
                if value is None:
                    continue
                path, _entry, content = value
                body_ref = next(body_refs)
                content_digest = body_ref.removeprefix("workspace-repository-body:")
                states[index] = WorkspaceRepositoryDeltaCapturePath(
                    path=path,
                    state=RepositoryDeltaCapturePathState.COVERED,
                    content_digest=content_digest,
                    size_bytes=len(content),
                    body_ref=body_ref,
                )
            now = datetime.now(UTC)
            capture = WorkspaceRepositoryDeltaCapture(
                capture_ref=capture_ref,
                repository_binding_ref=self._binding_ref,
                admitted_coordinate=coordinate,
                selection_digest=selection_digest,
                selected_paths=normalized_paths,
                path_states=tuple(states),
                policy=policy,
                checkpoint_revision=0,
                opened_at=now,
                updated_at=now,
                context_refs=context_refs,
            )
            self._store.record_capture(capture)
            self._captures[capture_ref] = capture
            self._preparation_count += 1
            return capture

    async def observe_async(
        self, batch: WorkspaceRepositoryObservationBatch | None
    ) -> tuple[WorkspaceRepositoryContentDelta, ...]:
        return await asyncio.to_thread(self.observe, batch)

    def observe(
        self, batch: WorkspaceRepositoryObservationBatch | None
    ) -> tuple[WorkspaceRepositoryContentDelta, ...]:
        with self._lock:
            if batch is None:
                self._no_change_count += 1
                return ()
            if batch.binding_key != self._binding_ref:
                raise ValueError("Observation batch binding differs from coordinator")
            batch_key = (batch.epoch, batch.cursor)
            processed = self._processed_batches.get(batch_key)
            if processed is not None:
                return processed
            self._observed_batch_count += 1
            captures_by_path: dict[str, list[WorkspaceRepositoryDeltaCapture]] = {}
            for capture in self._captures.values():
                if (
                    capture.closed_at is not None
                    or capture.admitted_coordinate.epoch != batch.epoch
                    or capture.admitted_coordinate.cursor >= batch.cursor
                ):
                    continue
                for path in capture.selected_paths:
                    captures_by_path.setdefault(path, []).append(capture)
            relevant = tuple(
                change for change in batch.changes if change.path in captures_by_path
            )
            if not relevant:
                return ()

            targets: dict[str, _CapturedTarget] = {}
            for change in relevant:
                if change.kind is ObservationChangeKind.DELETE:
                    continue
                entry = change.entry
                if entry is None:
                    raise ValueError("Observed create/update requires target entry")
                policies = tuple(
                    capture.policy for capture in captures_by_path[change.path]
                )
                maximum_body = max(policy.maximum_body_bytes for policy in policies)
                maximum_attempts = max(
                    policy.maximum_read_attempts for policy in policies
                )
                if entry.size_bytes > maximum_body:
                    targets[change.path] = _CapturedTarget(
                        content=None,
                        body_ref=None,
                        size_bytes=entry.size_bytes,
                        failure_state=RepositoryContentDeltaState.OVER_BUDGET,
                        reason="changed body exceeds every active capture policy",
                    )
                    self._over_budget_body_count += 1
                    continue
                try:
                    content = _read_stable_body(
                        root=self._binding.root_path,
                        path=change.path,
                        entry=entry,
                        maximum_bytes=maximum_body,
                        maximum_attempts=maximum_attempts,
                        on_body_read=self._record_changed_body_read,
                    )
                except _UnstableBody as error:
                    targets[change.path] = _CapturedTarget(
                        content=None,
                        body_ref=None,
                        size_bytes=entry.size_bytes,
                        failure_state=RepositoryContentDeltaState.MISSING_TARGET,
                        reason=str(error),
                    )
                    self._unstable_body_count += 1
                    continue
                body_ref = self._store.record_body(content)
                targets[change.path] = _CapturedTarget(
                    content=content,
                    body_ref=body_ref,
                    size_bytes=len(content),
                    failure_state=None,
                    reason=None,
                )

            deltas: list[WorkspaceRepositoryContentDelta] = []
            for capture in tuple(self._captures.values()):
                current = capture
                for change in relevant:
                    if change.path not in capture.selected_paths:
                        continue
                    delta, candidate = self._content_delta(
                        current, change, batch, targets
                    )
                    self._store.record_capture(candidate)
                    self._store.record_delta(delta)
                    current = candidate
                    deltas.append(delta)
                self._captures[capture.capture_ref] = current
            result = tuple(deltas)
            self._processed_batches[batch_key] = result
            while len(self._processed_batches) > 256:
                self._processed_batches.pop(next(iter(self._processed_batches)))
            return result

    def _content_delta(
        self,
        capture: WorkspaceRepositoryDeltaCapture,
        change: RepositoryObservationChange,
        batch: WorkspaceRepositoryObservationBatch,
        targets: dict[str, _CapturedTarget],
    ) -> tuple[WorkspaceRepositoryContentDelta, WorkspaceRepositoryDeltaCapture]:
        observed = change
        path = observed.path
        old_state = next(value for value in capture.path_states if value.path == path)
        before = RepositoryObservationCoordinate(
            repository_binding_ref=self._binding_ref,
            epoch=batch.epoch,
            cursor=batch.cursor - 1,
            snapshot_digest=batch.before_snapshot_digest,
            visibility_policy_ref=WORKSPACE_REPOSITORY_VISIBILITY_POLICY_REF,
            visibility_policy_version=self._binding.filter_version,
        )
        after = RepositoryObservationCoordinate(
            repository_binding_ref=self._binding_ref,
            epoch=batch.epoch,
            cursor=batch.cursor,
            snapshot_digest=batch.after_snapshot_digest,
            visibility_policy_ref=WORKSPACE_REPOSITORY_VISIBILITY_POLICY_REF,
            visibility_policy_version=self._binding.filter_version,
        )
        old_body_ref = (
            old_state.body_ref
            if old_state.body_ref is not None
            and self._store.contains_body(old_state.body_ref)
            else None
        )
        old_digest = old_state.content_digest
        old_size = old_state.size_bytes
        target = targets.get(path)
        new_body_ref = target.body_ref if target is not None else None
        new_digest = (
            new_body_ref.removeprefix("workspace-repository-body:")
            if new_body_ref is not None
            else None
        )
        new_size = target.size_bytes if target is not None else None
        covered_other_bytes = sum(
            value.size_bytes or 0
            for value in capture.path_states
            if value.path != path
            and value.state is RepositoryDeltaCapturePathState.COVERED
        )
        capture_over_budget = (
            target is not None
            and target.content is not None
            and (
                len(target.content) > capture.policy.maximum_body_bytes
                or covered_other_bytes + len(target.content)
                > capture.policy.maximum_selected_bytes
            )
        )
        if capture_over_budget:
            new_body_ref = None
            new_digest = None

        if observed.kind is ObservationChangeKind.CREATE:
            kind = RepositoryChangedEntryKind.CREATE
            old_path = None
            new_path = path
            old_digest = old_size = old_body_ref = None
            exact_old = old_state.state is RepositoryDeltaCapturePathState.ABSENT
        elif observed.kind is ObservationChangeKind.DELETE:
            kind = RepositoryChangedEntryKind.DELETE
            old_path = path
            new_path = None
            new_digest = new_size = new_body_ref = None
            exact_old = old_body_ref is not None
        else:
            binary = (
                target is not None
                and target.content is not None
                and b"\x00" in target.content
            )
            kind = (
                RepositoryChangedEntryKind.BINARY
                if binary
                else RepositoryChangedEntryKind.UPDATE
            )
            old_path = new_path = path
            exact_old = old_body_ref is not None

        if capture_over_budget:
            state = RepositoryContentDeltaState.OVER_BUDGET
            reason = "changed body exceeds capture policy"
        elif target is not None and target.failure_state is not None:
            state = target.failure_state
            reason = target.reason
        elif not exact_old:
            state = (
                RepositoryContentDeltaState.EVICTED
                if old_state.body_ref is not None
                else (
                    RepositoryContentDeltaState.GAP
                    if observed.kind is ObservationChangeKind.CREATE
                    else RepositoryContentDeltaState.MISSING_PREIMAGE
                )
            )
            reason = "exact captured preimage is unavailable"
        elif kind is RepositoryChangedEntryKind.BINARY:
            state = RepositoryContentDeltaState.BINARY
            reason = None
        else:
            state = RepositoryContentDeltaState.AVAILABLE
            reason = None

        if observed.kind is ObservationChangeKind.DELETE:
            next_path_state = WorkspaceRepositoryDeltaCapturePath(
                path=path,
                state=RepositoryDeltaCapturePathState.ABSENT,
            )
        elif new_body_ref is not None:
            next_path_state = WorkspaceRepositoryDeltaCapturePath(
                path=path,
                state=RepositoryDeltaCapturePathState.COVERED,
                content_digest=new_digest,
                size_bytes=new_size,
                body_ref=new_body_ref,
            )
        elif state is RepositoryContentDeltaState.OVER_BUDGET:
            next_path_state = WorkspaceRepositoryDeltaCapturePath(
                path=path,
                state=RepositoryDeltaCapturePathState.OVER_BUDGET,
                size_bytes=new_size,
                reason=reason,
            )
        else:
            next_path_state = WorkspaceRepositoryDeltaCapturePath(
                path=path,
                state=RepositoryDeltaCapturePathState.UNSTABLE,
                size_bytes=new_size,
                reason=reason,
            )
        path_states = tuple(
            next_path_state if value.path == path else value
            for value in capture.path_states
        )
        candidate = replace(
            capture,
            path_states=path_states,
            checkpoint_revision=capture.checkpoint_revision + 1,
            updated_at=batch.observed_at,
        )
        sequence = self._path_sequences.get(path, 0) + 1
        self._path_sequences[path] = sequence
        values = {
            "capture_ref": capture.capture_ref,
            "repository_binding_ref": self._binding_ref,
            "before_coordinate": before,
            "after_coordinate": after,
            "kind": kind,
            "old_path": old_path,
            "new_path": new_path,
            "old_content_digest": old_digest,
            "new_content_digest": new_digest,
        }
        delta = WorkspaceRepositoryContentDelta(
            delta_ref=repository_content_delta_ref(**values),
            state=state,
            path_sequence=sequence,
            capture_checkpoint_revision=candidate.checkpoint_revision,
            old_size_bytes=old_size,
            new_size_bytes=new_size,
            old_body_ref=old_body_ref,
            new_body_ref=new_body_ref,
            reason=reason,
            **values,
        )
        return delta, candidate

    @property
    def _binding_ref(self) -> str:
        value = self._binding.binding_key
        if value is None:
            raise ValueError("Repository binding key is unavailable")
        return value

    def _validate_snapshot(
        self, snapshot: WorkspaceRepositoryObservationSnapshot
    ) -> None:
        if snapshot.binding_key != self._binding_ref:
            raise ValueError("Observation snapshot binding differs from coordinator")

    def _record_selected_body_read(self, byte_count: int) -> None:
        self._selected_body_read_count += 1
        self._selected_body_read_bytes += byte_count

    def _record_changed_body_read(self, byte_count: int) -> None:
        self._changed_body_read_count += 1
        self._changed_body_read_bytes += byte_count


@dataclass(frozen=True, slots=True)
class _CapturedTarget:
    content: bytes | None
    body_ref: str | None
    size_bytes: int | None
    failure_state: RepositoryContentDeltaState | None
    reason: str | None


class _UnstableBody(RuntimeError):
    pass


def _read_stable_body(
    *,
    root: os.PathLike[str],
    path: str,
    entry: RepositorySnapshotEntry,
    maximum_bytes: int,
    maximum_attempts: int,
    on_body_read: Callable[[int], None],
) -> bytes:
    failure: Exception | None = None
    for _attempt in range(maximum_attempts):
        try:
            return _read_stable_body_once(
                root=root,
                path=path,
                entry=entry,
                maximum_bytes=maximum_bytes,
                on_body_read=on_body_read,
            )
        except (OSError, _UnstableBody) as error:
            failure = error
    raise _UnstableBody(
        "source changed, disappeared, or crossed confinement"
    ) from failure


def _read_stable_body_once(
    *,
    root: os.PathLike[str],
    path: str,
    entry: RepositorySnapshotEntry,
    maximum_bytes: int,
    on_body_read: Callable[[int], None],
) -> bytes:
    if not all(hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW")):
        raise _UnstableBody("secure confined reads are unavailable")
    descriptors: list[int] = []
    try:
        current = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        descriptors.append(current)
        parts = PurePosixPath(path).parts
        for part in parts[:-1]:
            current = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=current,
            )
            descriptors.append(current)
        source = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=current)
        descriptors.append(source)
        before = os.fstat(source)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_size != entry.size_bytes
            or before.st_mtime_ns != entry.modified_ns
        ):
            raise _UnstableBody("source metadata differs from observation")
        chunks: list[bytes] = []
        remaining = maximum_bytes + 1
        while remaining:
            chunk = os.read(source, min(64 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        content = b"".join(chunks)
        on_body_read(len(content))
        after = os.fstat(source)
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)
    if (
        len(content) != entry.size_bytes
        or len(content) > maximum_bytes
        or after.st_size != before.st_size
        or after.st_mtime_ns != before.st_mtime_ns
    ):
        raise _UnstableBody("source changed during stable read")
    return content


def _normalized_paths(paths: tuple[str, ...]) -> tuple[str, ...]:
    normalized = tuple(
        sorted(
            {
                PurePosixPath(path.strip().replace("\\", "/")).as_posix()
                for path in paths
            }
        )
    )
    repository_delta_selection_digest(normalized)
    if len(normalized) != len(paths):
        raise ValueError("Delta capture paths must be unique")
    return normalized


def _coordinate(
    snapshot: WorkspaceRepositoryObservationSnapshot, filter_version: str
) -> RepositoryObservationCoordinate:
    return RepositoryObservationCoordinate(
        repository_binding_ref=snapshot.binding_key,
        epoch=snapshot.epoch,
        cursor=snapshot.cursor,
        snapshot_digest=snapshot.snapshot_digest,
        visibility_policy_ref=WORKSPACE_REPOSITORY_VISIBILITY_POLICY_REF,
        visibility_policy_version=filter_version,
    )
