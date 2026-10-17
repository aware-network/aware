"""Fresh delta path semantics against the literal allocation-heavy predecessor."""

from __future__ import annotations

import random
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path, PurePosixPath

import pytest
from aware_workspace_runtime import repository_delta as delta
from aware_workspace_runtime.repository_access import RepositoryObservationCoordinate


def _predecessor(value):
    normalized = value.strip().replace("\\", "/")
    path = PurePosixPath(normalized)
    if (
        not normalized
        or path.is_absolute()
        or normalized != path.as_posix()
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError(f"Repository path must be normalized and relative: {value!r}")
    return normalized


def _outcome(function, value):
    try:
        result = function(value)
        return ("returned", type(result), result, result is value)
    except (AttributeError, TypeError, ValueError) as error:
        return ("raised", type(error), str(error))


def test_exact_current_source_is_loaded():
    expected = Path(__file__).parents[1] / "aware_workspace_runtime/repository_delta.py"
    assert Path(delta.__file__).resolve() == expected.resolve()


@pytest.mark.parametrize(
    "value",
    (
        "a",
        ".aware/file",
        ".../file",
        "a\x00b",
        "é/文件",
        "e\u0301/file",
        "\ud800/file",
        " leading",
        "trailing ",
        "\u2003a\u2003",
        "a\\b",
        "a\\\\b",
        "a//b",
        "a/./b",
        "a/../b",
        "a/",
        "/a",
        "//a",
        "///a",
        "C:/file",
        "",
        ".",
        "..",
        "a" * 8192,
        None,
        False,
        7,
        b"a",
        (),
    ),
)
def test_normalization_return_identity_and_refusal_parity(value):
    assert _outcome(delta._relative_path, value) == _outcome(_predecessor, value)


def test_random_paths_match_one_hundred_thousand_predecessor_decisions():
    generator = random.Random(20261015)
    alphabet = "abXYZ019._-/\\ \t\n\x00é中\u0301\ud800"
    for _ in range(100_000):
        value = "".join(
            generator.choice(alphabet) for _ in range(generator.randrange(35))
        )
        assert _outcome(delta._relative_path, value) == _outcome(_predecessor, value)


def test_string_subclass_keeps_original_method_dispatch():
    calls = []

    class Subclass(str):
        def strip(self, *args, **kwargs):
            calls.append("strip")
            return super().strip(*args, **kwargs)

    value = Subclass("  source/file  ")
    assert _outcome(delta._relative_path, value) == _outcome(_predecessor, value)
    assert calls == ["strip", "strip"]


def _complete_capture(count=1000):
    now = datetime(2026, 10, 15, tzinfo=UTC)
    paths = tuple(f"source/file_{index:04d}.py" for index in range(count))
    policy = delta.WorkspaceRepositoryDeltaCapturePolicy(maximum_selected_files=1024)
    coordinate = RepositoryObservationCoordinate(
        "repository:delta-path-test",
        "epoch:delta-path-test",
        0,
        "snapshot:delta-path-test",
        "policy:delta-path-test",
        "1",
    )
    digest = delta.repository_delta_selection_digest(paths)
    return delta.WorkspaceRepositoryDeltaCapture(
        delta.repository_delta_capture_ref(
            repository_binding_ref=coordinate.repository_binding_ref,
            admitted_coordinate=coordinate,
            selection_digest=digest,
            policy_version=policy.policy_version,
        ),
        coordinate.repository_binding_ref,
        coordinate,
        digest,
        paths,
        tuple(
            delta.WorkspaceRepositoryDeltaCapturePath(
                path, delta.RepositoryDeltaCapturePathState.ABSENT
            )
            for path in paths
        ),
        policy,
        0,
        now,
        now,
    )


def test_complete_capture_successors_keep_fresh_validation_and_exact_commitments(
    monkeypatch,
):
    current = _complete_capture()
    with monkeypatch.context() as previous:
        previous.setattr(delta, "_relative_path", _predecessor)
        expected = _complete_capture()
    assert current == expected
    for revision in range(1, 4):
        stamp = current.opened_at + timedelta(seconds=revision)
        advanced = replace(current, checkpoint_revision=revision, updated_at=stamp)
        with monkeypatch.context() as previous:
            previous.setattr(delta, "_relative_path", _predecessor)
            expected = replace(expected, checkpoint_revision=revision, updated_at=stamp)
        delta.validate_repository_delta_capture_advance(current, advanced)
        assert advanced == expected
        current = advanced
    with pytest.raises(ValueError, match="normalized and relative"):
        replace(current, selected_paths=("../changed", *current.selected_paths[1:]))
    with pytest.raises(ValueError, match="deterministic"):
        replace(current, selection_digest="sha256:" + "0" * 64)
    assert current == expected
