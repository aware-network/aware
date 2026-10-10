from __future__ import annotations

import hashlib
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from aware_workspace_runtime import (
    RepositoryChangedEntryKind,
    RepositoryContentDeltaState,
    RepositoryDeltaCapturePathState,
    RepositoryObservationCoordinate,
    WorkspaceRepositoryContentDelta,
    WorkspaceRepositoryDeltaCapture,
    WorkspaceRepositoryDeltaCapturePath,
    WorkspaceRepositoryDeltaCapturePolicy,
    repository_content_delta_ref,
    repository_delta_body_ref,
    repository_delta_capture_ref,
    repository_delta_selection_shards,
    repository_delta_selection_digest,
    repository_delta_scope_selection,
    validate_repository_delta_capture_advance,
)

BINDING = "repository:delta-test"
NOW = datetime(2026, 8, 23, 10, 42, tzinfo=UTC)


def test_delta_selection_shards_preserve_bounded_deterministic_scope() -> None:
    paths = tuple(f"path-{index:03d}.dart" for index in range(88, -1, -1))

    shards = repository_delta_selection_shards(
        paths,
        policy=WorkspaceRepositoryDeltaCapturePolicy(),
    )

    assert tuple(len(shard) for shard in shards) == (64, 25)
    assert tuple(path for shard in shards for path in shard) == tuple(sorted(paths))
    with pytest.raises(ValueError, match="unique"):
        repository_delta_selection_shards(
            ("same.dart", "same.dart"),
            policy=WorkspaceRepositoryDeltaCapturePolicy(),
        )


def test_delta_scope_selection_resolves_from_resident_paths_without_scanning() -> None:
    selected = repository_delta_scope_selection(
        ("docs/specs", "lib/main.dart", "future/new.dart", "docs"),
        observed_paths=(
            "docs/README.md",
            "docs/specs/one.md",
            "docs/specs/two.md",
            "lib/main.dart",
            "other.txt",
        ),
    )

    assert selected == (
        "docs/README.md",
        "docs/specs/one.md",
        "docs/specs/two.md",
        "future/new.dart",
        "lib/main.dart",
    )
    with pytest.raises(ValueError, match="unique"):
        repository_delta_scope_selection(
            ("docs", "docs"),
            observed_paths=("docs/README.md",),
        )
    with pytest.raises(ValueError, match="expansion exceeds policy"):
        repository_delta_scope_selection(
            ("generated",),
            observed_paths=tuple(
                f"generated/file-{index:04d}.txt" for index in range(513)
            ),
        )


def digest(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def coordinate(cursor: int) -> RepositoryObservationCoordinate:
    return RepositoryObservationCoordinate(
        repository_binding_ref=BINDING,
        epoch="observer:delta-test",
        cursor=cursor,
        snapshot_digest=f"snapshot:{cursor}",
        visibility_policy_ref=(
            "aware.workspace.repository-visibility.canonical-source.v1"
        ),
        visibility_policy_version="canonical-source-v1",
    )


def capture(
    *,
    body: bytes = b"before\n",
    revision: int = 0,
    updated_at: datetime = NOW,
    context_refs: tuple[str, ...] = ("work:one",),
) -> WorkspaceRepositoryDeltaCapture:
    content_digest = digest(body)
    selected_paths = ("source.txt", "will-exist.txt")
    selection_digest = repository_delta_selection_digest(selected_paths)
    policy = WorkspaceRepositoryDeltaCapturePolicy()
    return WorkspaceRepositoryDeltaCapture(
        capture_ref=repository_delta_capture_ref(
            repository_binding_ref=BINDING,
            admitted_coordinate=coordinate(0),
            selection_digest=selection_digest,
            policy_version=policy.policy_version,
        ),
        repository_binding_ref=BINDING,
        admitted_coordinate=coordinate(0),
        selection_digest=selection_digest,
        selected_paths=selected_paths,
        path_states=(
            WorkspaceRepositoryDeltaCapturePath(
                path="source.txt",
                state=RepositoryDeltaCapturePathState.COVERED,
                content_digest=content_digest,
                size_bytes=len(body),
                body_ref=repository_delta_body_ref(content_digest),
            ),
            WorkspaceRepositoryDeltaCapturePath(
                path="will-exist.txt",
                state=RepositoryDeltaCapturePathState.ABSENT,
            ),
        ),
        policy=policy,
        checkpoint_revision=revision,
        opened_at=NOW,
        updated_at=updated_at,
        context_refs=context_refs,
    )


def content_delta(
    value: WorkspaceRepositoryDeltaCapture,
    *,
    before: bytes = b"before\n",
    after: bytes = b"after\n",
) -> WorkspaceRepositoryContentDelta:
    old_digest = digest(before)
    new_digest = digest(after)
    values = {
        "capture_ref": value.capture_ref,
        "repository_binding_ref": BINDING,
        "before_coordinate": coordinate(0),
        "after_coordinate": coordinate(1),
        "kind": RepositoryChangedEntryKind.UPDATE,
        "old_path": "source.txt",
        "new_path": "source.txt",
        "old_content_digest": old_digest,
        "new_content_digest": new_digest,
    }
    return WorkspaceRepositoryContentDelta(
        delta_ref=repository_content_delta_ref(**values),
        state=RepositoryContentDeltaState.AVAILABLE,
        path_sequence=1,
        capture_checkpoint_revision=1,
        old_size_bytes=len(before),
        new_size_bytes=len(after),
        old_body_ref=repository_delta_body_ref(old_digest),
        new_body_ref=repository_delta_body_ref(new_digest),
        **values,
    )


def test_capture_selection_and_refs_are_deterministic_and_bounded() -> None:
    value = capture()
    assert value.selected_paths == ("source.txt", "will-exist.txt")
    assert value.path_states[0].state is RepositoryDeltaCapturePathState.COVERED
    assert value.path_states[1].state is RepositoryDeltaCapturePathState.ABSENT
    assert value.capture_ref.startswith("workspace-repository-delta-capture:sha256:")

    with pytest.raises(ValueError, match="exactly one state"):
        replace(value, path_states=value.path_states[:1])
    with pytest.raises(ValueError, match="selection digest"):
        replace(value, selection_digest="sha256:" + "0" * 64)


def test_capture_advance_preserves_authority_and_is_exactly_monotonic() -> None:
    first = capture()
    second = capture(
        revision=1,
        updated_at=NOW + timedelta(seconds=1),
        context_refs=("work:one", "work:two"),
    )
    validate_repository_delta_capture_advance(first, second)

    with pytest.raises(ValueError, match="exactly one"):
        validate_repository_delta_capture_advance(
            first, replace(second, checkpoint_revision=2)
        )
    with pytest.raises(ValueError, match="erase context"):
        validate_repository_delta_capture_advance(
            replace(first, context_refs=("work:one", "work:two")),
            replace(second, context_refs=("work:one",)),
        )


def test_content_delta_requires_exact_sides_and_forward_coordinate() -> None:
    value = content_delta(capture())
    assert value.state is RepositoryContentDeltaState.AVAILABLE
    assert value.old_body_ref == repository_delta_body_ref(value.old_content_digest)
    assert value.new_body_ref == repository_delta_body_ref(value.new_content_digest)

    with pytest.raises(ValueError, match="retained old body"):
        replace(value, old_body_ref=None)
    with pytest.raises(ValueError, match="forward observer"):
        replace(value, after_coordinate=coordinate(0))
    with pytest.raises(ValueError, match="Unavailable content delta requires reason"):
        replace(
            value,
            state=RepositoryContentDeltaState.MISSING_PREIMAGE,
            old_body_ref=None,
        )


def test_unavailable_delta_retains_known_coordinates_without_inventing_body() -> None:
    available = content_delta(capture())
    missing = replace(
        available,
        state=RepositoryContentDeltaState.MISSING_PREIMAGE,
        old_body_ref=None,
        reason="capture opened after the direct write",
    )
    assert missing.old_content_digest == available.old_content_digest
    assert missing.new_body_ref == available.new_body_ref
    assert missing.reason == "capture opened after the direct write"
