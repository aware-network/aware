"""Exact local source membership preserves original owner checkpoints."""

from __future__ import annotations

import ast
import hashlib
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from aware_workspace_runtime import package_checkout as checkout
from aware_workspace_sdk.repository_workflow import (
    WorkspaceRepositoryWorkflowRefusal,
    read_original_repository_workflow_source,
    release_original_repository_workflow_source,
    verify_original_repository_workflow_source,
    verify_original_repository_workflow_source_paths,
)
from test_repository_workflow import commit, workflow_source
from test_repository_workflow import (
    inputs as inputs,  # noqa: PLC0414 -- original pytest fixture
)


def _predecessor(self, paths, *, _guard=checkout._check_retained_reader):
    """Literal preceding method, qualified through the same original readers."""
    _guard(self)
    if not paths:
        return ()
    rows = []
    for raw in checkout._read_git(
        self, "ls-files", "--stage", "-z", "--", *paths
    ).split(b"\0"):
        if not raw:
            continue
        metadata, path_wire = raw.split(b"\t", 1)
        mode, _, stage = metadata.decode().split()
        path = path_wire.decode("utf-8")
        if path not in paths or stage != "0" or mode not in {"100644", "100755"}:
            raise checkout.PackageCheckoutError(
                "repository file is not one tracked regular file"
            )
        _guard(self)
        if bool((self.root / path).stat().st_mode & 0o111) != (mode == "100755"):
            raise checkout.PackageCheckoutError("repository file mode changed")
        rows.append((mode, path))
    if {path for _, path in rows} != set(paths):
        raise checkout.PackageCheckoutError("repository file is not Git-tracked")
    return tuple(sorted(rows, key=lambda row: row[1]))


def _result(method, reader, paths, events):
    try:
        return (
            "return",
            method(reader, paths, _guard=lambda _: events.append("guard")),
        )
    except Exception as error:  # noqa: BLE001 -- compare original exception semantics
        return ("error", type(error), str(error))


def _wire(rows):
    return b"".join(
        f"{mode} {'a' * 40} {stage}\t{path}\0".encode() for mode, stage, path in rows
    )


@pytest.mark.parametrize(
    "rows,executable",
    [
        ((("100644", "0", "a"), ("100644", "0", "b")), False),
        ((("100755", "0", "a"), ("100644", "0", "b")), True),
        ((("100644", "0", "foreign"), ("100755", "0", "a")), False),
        ((("100644", "2", "a"), ("100755", "0", "b")), False),
        ((("120000", "0", "a"), ("100755", "0", "b")), False),
        ((("100755", "0", "a"), ("100644", "0", "b")), False),
        ((("100644", "0", "a"),), False),
        ((("100644", "0", "b"), ("100644", "0", "a")), False),
        ((), False),
    ],
)
def test_exact_membership_matches_literal_predecessor(
    tmp_path, monkeypatch, rows, executable
):
    for name in ("a", "b", "foreign"):
        (tmp_path / name).write_bytes(b"source")
        (tmp_path / name).chmod(0o755 if executable and name == "a" else 0o644)
    reader = object.__new__(checkout.PackageSourceCheckout)
    reader.root = tmp_path
    results = []
    for method in (_predecessor, checkout.PackageSourceCheckout._tracked_exact_sources):
        events = []

        def read(*args, _events=events):
            _events.append(("git", args[1:]))
            return _wire(rows)

        with monkeypatch.context() as patch:
            patch.setattr(checkout, "_read_git", read)
            results.append((_result(method, reader, ("a", "b"), events), events))
    assert results[0] == results[1]


@pytest.mark.parametrize("kind", ["tuple", "text", "list", "git_error", "rebind"])
def test_generic_behavior_and_local_keys_remain_original(tmp_path, monkeypatch, kind):
    (tmp_path / "a").write_bytes(b"a")
    (tmp_path / "a").chmod(0o644)
    reader = object.__new__(checkout.PackageSourceCheckout)
    reader.root = tmp_path
    outcomes = []
    for method in (_predecessor, checkout.PackageSourceCheckout._tracked_exact_sources):
        events = []

        class Paths(tuple):
            def __contains__(self, value, _events=events):
                _events.append(("contains", value))
                return super().__contains__(value)

        class Text(str):
            __hash__ = str.__hash__

            def __eq__(self, other, _events=events):
                _events.append(("equal", str(self), str(other)))
                return super().__eq__(other)

        paths = (
            Paths(("a",))
            if kind == "tuple"
            else (Text("a"),)
            if kind == "text"
            else ["a"]
            if kind == "list"
            else ("a",)
        )
        reader._repository_rows = (("100644", "a"),)

        def read(*args, _events=events):
            _events.append("git")
            if kind == "git_error":
                raise OSError("original git failure")
            if kind == "rebind":
                reader._repository_rows = (("100644", "other"),)
            return _wire((("100644", "0", "a"),))

        with monkeypatch.context() as patch:
            patch.setattr(checkout, "_read_git", read)
            outcomes.append((_result(method, reader, paths, events), events))
    assert outcomes[0] == outcomes[1]


def test_empty_inputs_preserve_guard_without_git(monkeypatch):
    events = []
    reader = object.__new__(checkout.PackageSourceCheckout)
    monkeypatch.setattr(
        checkout, "_read_git", lambda *args: pytest.fail("empty input dispatched Git")
    )
    assert (
        checkout.PackageSourceCheckout._tracked_exact_sources(
            reader, (), _guard=lambda _: events.append("guard")
        )
        == ()
    )
    assert events == ["guard"]


def test_original_public_source_full_and_selected_validation_1000_paths(inputs):
    root, _, _, package, client, request = inputs
    # Two original package files plus 998 new regular files comprise 1000 leaves.
    for ordinal in range(998):
        (package / f"member-{ordinal:04}.txt").write_text(f"body:{ordinal}\n")
    request = replace(request, source_commit=commit(root))
    attempt, source, observed = workflow_source((*inputs[:-1], request))
    assert len(observed.files) == 1000
    selected = (observed.files[500].output_path,)
    verify_original_repository_workflow_source_paths(
        source, expected_binding=observed.binding, output_paths=selected
    )
    verify_original_repository_workflow_source(
        source, expected_binding=observed.binding
    )
    batch = read_original_repository_workflow_source(
        source, expected_binding=observed.binding, output_paths=selected
    )
    assert batch.bodies[0].file == observed.files[500]
    assert hashlib.sha256(batch.bodies[0].body).hexdigest() == (
        observed.files[500].content_digest.removeprefix("sha256:")
    )
    assert release_original_repository_workflow_source(source).state == "completed"
    client.release_repository_workflow(attempt)


def test_only_membership_method_changes_from_captured_source():
    module = ast.parse(Path(checkout.__file__).read_text())
    owner = next(
        n
        for n in module.body
        if isinstance(n, ast.ClassDef) and n.name == "PackageSourceCheckout"
    )
    owner.body = [
        n
        for n in owner.body
        if getattr(n, "name", None)
        not in ("_tracked_exact_sources", "revalidate_paths")
    ]
    assert (
        hashlib.sha256(ast.dump(module, include_attributes=False).encode()).hexdigest()
        == "a5276e93722ffc55e0a1bca698c72ff486e916fed032248ed8b32e07a34c186d"
    )


def _selected_source(inputs):
    from aware_workspace_sdk import repository_workflow as sdk

    parent, source, observed = workflow_source(inputs)
    runtime = next(
        entry[0] for handle, entry in sdk._SOURCES.items() if handle is source
    )
    record = runtime._sources[-1][1]
    selected = next(
        row for row in observed.files if row.source_path.endswith("source.py")
    )
    return parent, source, observed, record, selected


@pytest.mark.parametrize("field", ["_output_rows", "_bodies"])
@pytest.mark.parametrize(
    "checkpoint", ["initial_git", "membership_git", "body_capture", "final_git"]
)
def test_original_tuple_substitution_is_terminal_before_foreign_iteration(
    inputs, field, checkpoint
):
    _, source, observed, record, selected = _selected_source(inputs)
    reader = record.reader
    original = object.__getattribute__(reader, field)
    calls = []
    changed = []
    git_count = []

    class Foreign(tuple):
        def __iter__(self):
            calls.append("iterated")
            raise AssertionError("foreign capture tuple executed")

        def __len__(self):
            calls.append("length")
            raise AssertionError("foreign capture tuple executed")

        def __getitem__(self, key):
            calls.append("indexed")
            raise AssertionError("foreign capture tuple executed")

    previous = sys.getprofile()
    original_git = checkout._git.__code__
    original_capture = checkout.capture_exact_paths.__code__

    def observe(frame, event, _arg):
        if event != "return" or changed:
            return
        if frame.f_code is original_git:
            git_count.append(True)
        if (
            checkpoint == "initial_git"
            and frame.f_code is original_git
            and len(git_count) == 1
            or checkpoint == "membership_git"
            and frame.f_code is original_git
            and len(git_count) == 2
            or checkpoint == "final_git"
            and frame.f_code is original_git
            and len(git_count) == 3
            or checkpoint == "body_capture"
            and frame.f_code is original_capture
        ):
            object.__setattr__(reader, field, Foreign())
            changed.append(True)

    error = None
    try:
        sys.setprofile(observe)
        try:
            verify_original_repository_workflow_source_paths(
                source,
                expected_binding=observed.binding,
                output_paths=(selected.output_path,),
            )
        except WorkspaceRepositoryWorkflowRefusal as caught:
            error = caught
        else:
            pytest.fail("substituted original tuple was accepted")
    finally:
        sys.setprofile(previous)
        object.__setattr__(reader, field, original)
    assert changed == [True] and calls == []
    assert record.status == "terminal" and record.parent.status == "held"
    assert record.reader is None and record.state == ()
    assert error is not None
    seen = set()
    current = error
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        trace = current.__traceback__
        while trace is not None:
            frame = trace.tb_frame
            if frame.f_code.co_name == "revalidate_paths":
                assert (
                    not {
                        "self",
                        "output_paths",
                        "_original_capture",
                        "originals",
                        "original_bodies",
                        "outputs",
                        "modes",
                        "captured",
                        "actual",
                        "expected",
                        "row",
                    }
                    & frame.f_locals.keys()
                )
            if frame.f_code.co_name == "_validate_source":
                assert (
                    not {
                        "self",
                        "record",
                        "reader",
                        "output_paths",
                        "original_outputs",
                        "original_bodies",
                        "name",
                        "original",
                    }
                    & frame.f_locals.keys()
                )
            trace = trace.tb_next
        current = current.__cause__ or current.__context__
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        verify_original_repository_workflow_source_paths(
            source,
            expected_binding=observed.binding,
            output_paths=(selected.output_path,),
        )


@pytest.mark.parametrize("field", ["_guard", "_original_capture"])
def test_original_private_defaults_authentication_precedes_consumption(inputs, field):
    _, source, observed, record, selected = _selected_source(inputs)
    method = checkout.PackageSourceCheckout.revalidate_paths
    defaults = method.__kwdefaults__
    original = defaults[field]
    calls = []

    def foreign(*args):
        calls.append(True)
        return ()

    defaults[field] = foreign
    try:
        with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
            verify_original_repository_workflow_source_paths(
                source,
                expected_binding=observed.binding,
                output_paths=(selected.output_path,),
            )
    finally:
        defaults[field] = original
    assert calls == [] and record.status == "terminal"
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        verify_original_repository_workflow_source_paths(
            source,
            expected_binding=observed.binding,
            output_paths=(selected.output_path,),
        )


def test_existing_private_reader_fallback_preserves_aliases_and_body_read_order(
    tmp_path, monkeypatch
):
    reader = object.__new__(checkout.PackageSourceCheckout)
    reader.root = tmp_path
    reader._inventory = {}
    reader._reader_guard = None
    reader._fd = -1
    reader._output_rows = (
        ("100644", "alias.txt", "body.txt"),
        ("100644", "second.txt", "body.txt"),
    )
    reader._bodies = (("body.txt", b"body"),)
    calls = []
    monkeypatch.setattr(
        checkout.PackageSourceCheckout, "_check", lambda _: calls.append("check")
    )
    monkeypatch.setattr(
        checkout.PackageSourceCheckout,
        "_tracked_exact_sources",
        lambda _, paths: (("100644", "body.txt"),),
    )
    monkeypatch.setattr(
        checkout,
        "capture_exact_paths",
        lambda *args, **kwargs: calls.append("capture") or (("body.txt", b"body"),),
    )
    reader.revalidate_paths(
        ("alias.txt", "second.txt"), _guard=lambda _: calls.append("guard")
    )
    fallback_calls = tuple(calls)
    calls.clear()
    reader.revalidate_paths(
        ("alias.txt", "second.txt"),
        _guard=lambda _: calls.append("guard"),
        _original_capture=(reader._output_rows, reader._bodies),
    )
    assert tuple(calls) == fallback_calls
    assert calls.count("capture") == 1 and calls.count("check") == 2
    reader._bodies = ()
    calls.clear()
    with pytest.raises(KeyError, match="body.txt"):
        reader.revalidate_paths(
            ("alias.txt",),
            _guard=lambda _: None,
            _original_capture=(reader._output_rows, reader._bodies),
        )
    assert "capture" in calls
