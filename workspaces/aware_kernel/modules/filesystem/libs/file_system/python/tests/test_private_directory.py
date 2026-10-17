"""Original private IO joins, detached owner evidence and preserved codecs."""

from __future__ import annotations

import ast
import copy
import errno
import gc
import hashlib
import json
import os
import re
import subprocess
import sys
import weakref
from dataclasses import fields, replace
from pathlib import Path

import pytest
from aware_file_system import confined_mutation as n
from aware_file_system import private_directory as p
from aware_file_system import retained_file_sequence as s

_PRIVATE_LOOKUP_PORTS = (
    "observe_private_directory",
    "validate_private_directory",
    "release_private_directory",
    "retain_private_file_sequence",
    "observe_private_directory_file",
    "observe_private_file_sequence",
    "verify_private_file_sequence",
    "execute_next_private_file_step",
    "release_private_file_sequence",
)


@pytest.mark.parametrize("operation", _PRIVATE_LOOKUP_PORTS)
def test_private_held_wrong_kind_refusal_releases_family(
    tmp_path, monkeypatch, operation
):
    """Keep the refusal, not the rejected handle or its actual descriptor rights."""
    tmp_path.chmod(0o700)
    directory = p.retain_private_directory(
        root=tmp_path, privacy_profile="effective_user_private_namespace_v1"
    )
    binding = p.observe_private_directory(directory).binding
    directory_port = operation in _PRIVATE_LOOKUP_PORTS[:5]
    child = private_sequence((tmp_path, directory, binding)) if directory_port else None
    rejected = child if directory_port else directory
    references = (weakref.ref(directory), weakref.ref(rejected))
    descriptors = [p._DIRECTORIES[id(directory)][1].fd]
    if child is not None:
        descriptors.append(
            p._original_private_sequence(child).directory.native_sequence.io.root_fd
        )
    kwargs = {}
    if operation in {
        "validate_private_directory",
        "observe_private_directory_file",
        "retain_private_file_sequence",
        "verify_private_file_sequence",
    }:
        kwargs["expected_binding"] = binding
    if operation == "observe_private_directory_file":
        kwargs.update(path="record", maximum_bytes=1024)
    if operation == "retain_private_file_sequence":
        kwargs.update(
            requests=(),
            limits=s.ConfinedSequenceLimits(**s._LIMIT_CAPS),
            confinement_profile=n.ConfinedMutationProfile.DESCRIPTOR_WALK_V1,
        )
    if operation == "execute_next_private_file_step":
        kwargs["expected_ordinal"] = 0
    try:
        getattr(p, operation)(rejected, **kwargs)
    except p.PrivateDirectoryRefusal as error:
        held = error
    else:
        pytest.fail("wrong-kind handle accepted")
    assert held.code == (
        "private_directory_foreign" if directory_port else "private_sequence_foreign"
    )
    assert held.evidence.directory is None
    assert held.evidence.cleanup is None
    assert (
        p.private_directory_value_from_payload(
            p.PrivateDirectoryRefusalEvidence,
            p.private_directory_value_to_payload(held.evidence),
        )
        == held.evidence
    )
    # Refusal neither retires nor cleans legitimate owners while the caller
    # still holds them. Original validation/verification remains available.
    assert (
        p.validate_private_directory(directory, expected_binding=binding).phase
        == "active"
    )
    if child is not None:
        observation = p.observe_private_file_sequence(child)
        assert (
            p.verify_private_file_sequence(
                child, expected_binding=observation.binding
            ).sequence.next_ordinal
            == 0
        )
    for fd in descriptors:
        os.fstat(fd)
    closes = []
    original_close = os.close

    def tracked_close(fd):
        closes.append(fd)
        return original_close(fd)

    monkeypatch.setitem(p._PHYSICAL, "close", tracked_close)
    monkeypatch.setitem(s._OS, "close", tracked_close)
    del directory, child, rejected
    gc.collect()
    assert all(reference() is None for reference in references)
    for fd in descriptors:
        with pytest.raises(OSError) as failure:
            os.fstat(fd)
        assert failure.value.errno == errno.EBADF
        assert closes.count(fd) == 1
    assert held.code.endswith("_foreign")  # The original refusal remains held.


def test_private_lookup_repair_conserves_original_execution():
    """Only the outer argument-lifetime boundary changes the nine operations."""
    repository = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "aware.repo.toml").exists()
    )
    path = Path(p.__file__).relative_to(repository)
    before = ast.parse(
        subprocess.check_output(
            ["git", "show", "b0440267ae9b:" + str(path)], cwd=repository, text=True
        )
    )
    after = ast.parse(Path(p.__file__).read_text())
    original = {
        node.name: node for node in before.body if isinstance(node, ast.FunctionDef)
    }
    current = {
        node.name: node for node in after.body if isinstance(node, ast.FunctionDef)
    }
    for name, node in original.items():
        if name not in _PRIVATE_LOOKUP_PORTS:
            assert ast.dump(current[name]) == ast.dump(node)
            continue
        preceding = (
            node.body[:1]
            if isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            else []
        )
        replacement = current[name].body[len(preceding)]
        assert isinstance(replacement, ast.Try) and replacement.finalbody
        assert any(
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Name)
            and child.func.id in {"_original_directory", "_original_private_sequence"}
            for child in ast.walk(replacement.body[0])
        )

        # Remove the predecessor's too-late argument-clearing finally clauses
        # and compare the complete operational body after lifting their guard.
        class RemoveArgumentClearing(ast.NodeTransformer):
            def visit_Try(self, statement):
                self.generic_visit(statement)
                if statement.finalbody and all(
                    isinstance(child, ast.Delete) for child in statement.finalbody
                ):
                    statement.finalbody = []
                return statement

        expected = RemoveArgumentClearing().visit(node)
        actual = copy.deepcopy(current[name])
        actual.body = actual.body[: len(preceding)] + actual.body[len(preceding)].body
        assert ast.dump(actual) == ast.dump(expected)


@pytest.fixture
def private_root(tmp_path):
    tmp_path.chmod(0o700)
    handle = p.retain_private_directory(
        root=tmp_path, privacy_profile="effective_user_private_namespace_v1"
    )
    try:
        yield tmp_path, handle, p.observe_private_directory(handle).binding
    finally:
        p.release_private_directory(handle)


def test_genuine_private_read_and_detached_cleanup(private_root):
    root, handle, binding = private_root
    (root / "record").write_bytes(b"\x00\xffexact\n")
    result = p.observe_private_directory_file(
        handle, expected_binding=binding, path="record", maximum_bytes=1024
    )
    assert result.original.observation.content == b"\x00\xffexact\n"
    assert result.original.cleanup.outcome == "closed"
    assert result.original.cleanup.acquired_count == 2
    assert (
        result.directory_after.validation_ordinal
        > result.directory_before.validation_ordinal
    )
    payload = p.private_directory_value_to_payload(result)
    p.release_private_directory(handle)
    assert (
        p.private_directory_value_from_payload(p.PrivateFileReadResult, payload)
        == result
    )
    assert (root / "record").read_bytes() == b"\x00\xffexact\n"


@pytest.mark.parametrize("mode", (0o755, 0o777, 0o1700, 0o2700))
def test_private_root_mode_denial(tmp_path, mode):
    tmp_path.chmod(mode)
    with pytest.raises(p.PrivateDirectoryRefusal) as caught:
        p.retain_private_directory(
            root=tmp_path, privacy_profile="effective_user_private_namespace_v1"
        )
    assert caught.value.code == "private_root_mode_mismatch"
    assert caught.value.evidence.cleanup.release == "confirmed"
    assert tmp_path.stat().st_mode & 0o7777 == mode


def test_private_mode_restore_cannot_revive(private_root):
    root, handle, binding = private_root
    root.chmod(0o755)
    with pytest.raises(p.PrivateDirectoryRefusal, match="private_root_mode_mismatch"):
        p.validate_private_directory(handle, expected_binding=binding)
    root.chmod(0o700)
    with pytest.raises(p.PrivateDirectoryRefusal, match="private_directory_retired"):
        p.validate_private_directory(handle, expected_binding=binding)
    assert p.release_private_directory(handle).release == "confirmed"


def test_private_read_hardlink_refused_before_bytes(private_root, monkeypatch):
    root, handle, binding = private_root
    (root / "record").write_bytes(b"private")
    os.link(root / "record", root / "alias")
    called = []
    monkeypatch.setattr(os, "read", lambda *args: called.append(args))
    with pytest.raises(p.PrivateDirectoryRefusal) as caught:
        p.observe_private_directory_file(
            handle, expected_binding=binding, path="record", maximum_bytes=1024
        )
    assert caught.value.code == "private_leaf_link_count_refused"
    assert caught.value.evidence.read.cleanup.outcome == "closed"
    assert not called


@pytest.mark.parametrize("kind", ("missing", "fifo", "symlink"))
def test_private_leaf_refusals(private_root, kind):
    root, handle, binding = private_root
    if kind == "fifo":
        os.mkfifo(root / "record")
    elif kind == "symlink":
        (root / "record").symlink_to("outside")
    with pytest.raises(p.PrivateDirectoryRefusal) as caught:
        p.observe_private_directory_file(
            handle, expected_binding=binding, path="record", maximum_bytes=1024
        )
    assert caught.value.code == (
        "private_leaf_missing" if kind == "missing" else "private_leaf_not_regular"
    )
    assert caught.value.evidence.read is not None


def test_private_postread_failure_retains_original(private_root, monkeypatch):
    root, handle, binding = private_root
    (root / "record").write_bytes(b"captured")
    original = n._observe_confined_file_with_custody

    def read_then_chmod(**kwargs):
        result = original(**kwargs)
        root.chmod(0o755)
        return result

    monkeypatch.setattr(n, "_observe_confined_file_with_custody", read_then_chmod)
    # Explicit owner-port fault seam after the genuine read. Ordinary export
    # substitution is separately refused before foreign execution.
    monkeypatch.setitem(
        p._ORIGINAL_PORTS,
        "read",
        (
            n,
            "_observe_confined_file_with_custody",
            read_then_chmod,
            read_then_chmod.__code__,
        ),
    )
    with pytest.raises(p.PrivateDirectoryRefusal) as caught:
        p.observe_private_directory_file(
            handle, expected_binding=binding, path="record", maximum_bytes=1024
        )
    assert caught.value.evidence.read.observation.content == b"captured"
    assert caught.value.evidence.directory.phase == "retired"
    assert not caught.value.evidence.ledger_complete


def test_private_lookup_refusal_does_not_retain_other_directory(tmp_path):
    handle = p.retain_private_directory(
        root=tmp_path, privacy_profile="effective_user_private_namespace_v1"
    )
    ref = weakref.ref(handle)
    baseline = len(os.listdir("/proc/self/fd"))
    with pytest.raises(p.PrivateDirectoryRefusal) as caught:
        p.observe_private_directory(object())
    del handle
    gc.collect()
    assert caught.value.code == "private_directory_foreign"
    assert ref() is None
    assert len(os.listdir("/proc/self/fd")) == baseline - 1


def test_private_cleanup_spends_before_close_interruption(private_root, monkeypatch):
    _, handle, _ = private_root
    original = p._PHYSICAL["close"]
    calls = []

    def close_then_interrupt(fd):
        calls.append(fd)
        original(fd)
        raise KeyboardInterrupt

    monkeypatch.setitem(p._PHYSICAL, "close", close_then_interrupt)
    with pytest.raises(p.PrivateDirectoryRefusal) as caught:
        p.release_private_directory(handle)
    assert caught.value.evidence.cleanup.release == "unknown"
    with pytest.raises(p.PrivateDirectoryRefusal):
        p.release_private_directory(handle)
    assert len(calls) == 1
    monkeypatch.setitem(p._PHYSICAL, "close", original)
    # Fixture release observes the terminal unknown refusal, not another close.
    state = p._original_directory(handle)
    state.release = "confirmed"


@pytest.mark.parametrize("operation", (copy.copy, copy.deepcopy))
def test_private_handles_cannot_be_copied(private_root, operation):
    with pytest.raises(TypeError):
        operation(private_root[1])


def private_sequence(private_root, names=("record",)):
    _, handle, binding = private_root
    return p.retain_private_file_sequence(
        handle,
        expected_binding=binding,
        requests=tuple(
            n.ConfinedFileMutationRequest(
                n.ConfinedMutationKind.CREATE, name, False, None, b"retained body"
            )
            for name in names
        ),
        limits=s.ConfinedSequenceLimits(**s._LIMIT_CAPS),
        confinement_profile=n.ConfinedMutationProfile.DESCRIPTOR_WALK_V1,
    )


def finish_private(handle):
    binding = p.observe_private_file_sequence(handle).binding
    for step in binding.sequence.ordered_steps:
        p.verify_private_file_sequence(handle, expected_binding=binding)
        last = p.execute_next_private_file_step(handle, expected_ordinal=step.ordinal)
    return last


@pytest.mark.parametrize("umask", (0o022, 0o077))
def test_private_original_writer_lifecycle(private_root, umask):
    root, parent, binding = private_root
    previous = os.umask(umask)
    try:
        child = private_sequence(private_root, ("a", "b"))
        assert not (root / "a").exists()
        last = finish_private(child)
        assert last.sequence.phase == "completed"
        assert (root / "a").read_bytes() == b"retained body"
        assert (root / "a").stat().st_mode & 0o777 == 0o666 & ~umask
        assert (root / "a").stat().st_nlink == 1
        cleanup = p.release_private_file_sequence(child)
        assert cleanup.sequence.release == "confirmed"
        assert p.release_private_file_sequence(child) == cleanup
        read = p.observe_private_directory_file(
            parent, expected_binding=binding, path="a", maximum_bytes=1024
        )
        assert read.original.observation.content == b"retained body"
    finally:
        os.umask(previous)
        if "child" in locals():
            p.release_private_file_sequence(child)


def test_private_parent_refuses_while_child_retains_custody(private_root):
    _, parent, _ = private_root
    child = private_sequence(private_root)
    try:
        with pytest.raises(p.PrivateDirectoryRefusal, match="private_directory_in_use"):
            p.release_private_directory(parent)
        with pytest.raises(p.PrivateDirectoryRefusal, match="private_directory_in_use"):
            private_sequence(private_root, ("other",))
        assert p.observe_private_directory(parent).phase == "active"
        finish_private(child)
    finally:
        p.release_private_file_sequence(child)


@pytest.mark.parametrize("boundary", ("verify", "execute"))
def test_private_child_mode_drift_retires_before_effect(private_root, boundary):
    root, _, _ = private_root
    child = private_sequence(private_root)
    binding = p.observe_private_file_sequence(child).binding
    root.chmod(0o755)
    try:
        with pytest.raises(
            p.PrivateDirectoryRefusal, match="private_root_mode_mismatch"
        ):
            if boundary == "verify":
                p.verify_private_file_sequence(child, expected_binding=binding)
            else:
                p.execute_next_private_file_step(child, expected_ordinal=0)
        assert list(root.iterdir()) == []
        root.chmod(0o700)
        with pytest.raises(
            p.PrivateDirectoryRefusal, match="private_directory_retired"
        ):
            p.execute_next_private_file_step(child, expected_ordinal=0)
    finally:
        p.release_private_file_sequence(child)


def test_private_child_posteffect_result_failure_keeps_known_write(
    private_root, monkeypatch
):
    root, _, _ = private_root
    child = private_sequence(private_root)
    binding = p.observe_private_file_sequence(child).binding
    try:
        for step in binding.sequence.ordered_steps:
            if step.kind == "target_link":
                break
            p.execute_next_private_file_step(child, expected_ordinal=step.ordinal)
        original = p.PrivateSequenceStepResult

        def refuse_result(*args):
            raise KeyboardInterrupt

        monkeypatch.setattr(p, "PrivateSequenceStepResult", refuse_result)
        with pytest.raises(p.PrivateDirectoryRefusal) as caught:
            p.execute_next_private_file_step(child, expected_ordinal=step.ordinal)
        assert (root / "record").read_bytes() == b"retained body"
        observed = caught.value.evidence.sequence.observation
        assert observed.next_ordinal == step.ordinal + 1
        assert observed.effects[-1].effect_state == "applied"
        monkeypatch.setattr(p, "PrivateSequenceStepResult", original)
        with pytest.raises(p.PrivateDirectoryRefusal):
            p.execute_next_private_file_step(child, expected_ordinal=step.ordinal)
    finally:
        p.release_private_file_sequence(child)


@pytest.mark.parametrize("name", ("a/b",))
def test_private_sequence_rejects_nested_layout(private_root, name):
    root, _, _ = private_root
    with pytest.raises(
        p.PrivateDirectoryRefusal, match="private_sequence_request_unsupported"
    ):
        private_sequence(private_root, (name,))
    assert list(root.iterdir()) == []


def test_private_child_lifetime_retains_parent(tmp_path):
    parent = p.retain_private_directory(
        root=tmp_path, privacy_profile="effective_user_private_namespace_v1"
    )
    parent_ref = weakref.ref(parent)
    fixture = (tmp_path, parent, p.observe_private_directory(parent).binding)
    child = private_sequence(fixture)
    baseline = len(os.listdir("/proc/self/fd"))
    del parent, fixture
    gc.collect()
    assert parent_ref() is not None
    finish_private(child)
    p.release_private_file_sequence(child)
    del child
    gc.collect()
    assert parent_ref() is None
    assert len(os.listdir("/proc/self/fd")) < baseline


def test_private_root_rename_and_restore_does_not_revive(private_root):
    root, handle, binding = private_root
    moved = root.with_name(root.name + "-moved")
    root.rename(moved)
    root.mkdir(mode=0o700)
    try:
        with pytest.raises(p.PrivateDirectoryRefusal, match="private_root_changed"):
            p.validate_private_directory(handle, expected_binding=binding)
        root.rmdir()
        moved.rename(root)
        with pytest.raises(
            p.PrivateDirectoryRefusal, match="private_directory_retired"
        ):
            p.validate_private_directory(handle, expected_binding=binding)
    finally:
        if moved.exists():
            root.rmdir()
            moved.rename(root)


def test_private_root_symlink_is_not_adopted(tmp_path):
    target = tmp_path / "target"
    target.mkdir(mode=0o700)
    alias = tmp_path / "alias"
    alias.symlink_to(target, target_is_directory=True)
    with pytest.raises(p.PrivateDirectoryRefusal, match="private_root_symlink_refused"):
        p.retain_private_directory(
            root=alias, privacy_profile="effective_user_private_namespace_v1"
        )
    assert target.stat().st_mode & 0o777 == 0o700


def test_private_wrong_binding_retires_original(private_root):
    _, handle, binding = private_root
    with pytest.raises(
        p.PrivateDirectoryRefusal, match="private_directory_binding_mismatch"
    ):
        p.validate_private_directory(
            handle, expected_binding=replace(binding, directory_ref="foreign")
        )
    with pytest.raises(p.PrivateDirectoryRefusal, match="private_directory_retired"):
        p.validate_private_directory(handle, expected_binding=binding)


def test_private_cross_thread_refusal_does_not_retire_original(private_root):
    from concurrent.futures import ThreadPoolExecutor

    _, handle, binding = private_root
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(p.observe_private_directory, handle)
        with pytest.raises(
            p.PrivateDirectoryRefusal, match="private_directory_foreign"
        ):
            future.result()
    assert (
        p.validate_private_directory(handle, expected_binding=binding).phase == "active"
    )


def test_private_fork_refusal_preserves_parent(private_root):
    _, handle, binding = private_root
    pid = os.fork()
    if pid == 0:
        try:
            p.observe_private_directory(handle)
        except p.PrivateDirectoryRefusal:
            os._exit(0)
        os._exit(1)
    _, status = os.waitpid(pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0
    assert (
        p.validate_private_directory(handle, expected_binding=binding).phase == "active"
    )


def test_private_fifo_open_substitution_refuses_without_read(private_root, monkeypatch):
    root, handle, binding = private_root
    leaf = root / "record"
    leaf.write_bytes(b"old")
    original = n._ReadLedger.open
    called = []

    def substitute(self, path, flags, **kwargs):
        if path == "record" and kwargs.get("dir_fd") is not None:
            assert flags & os.O_NONBLOCK
            leaf.unlink()
            os.mkfifo(leaf)
        return original(self, path, flags, **kwargs)

    monkeypatch.setattr(n._ReadLedger, "open", substitute)
    monkeypatch.setattr(os, "read", lambda *args: called.append(args))
    with pytest.raises(p.PrivateDirectoryRefusal):
        p.observe_private_directory_file(
            handle, expected_binding=binding, path="record", maximum_bytes=1024
        )
    assert not called


def test_private_root_validation_counter_cannot_renew(private_root):
    _, handle, binding = private_root
    state = p._original_directory(handle)
    state.validations = 65536
    with pytest.raises(
        p.PrivateDirectoryRefusal, match="private_directory_capacity_exceeded"
    ):
        p.validate_private_directory(handle, expected_binding=binding)
    assert p.observe_private_directory(handle).phase == "retired"


def test_private_four_file_batch_completes_with_full_cleanup(private_root):
    child = private_sequence(private_root, ("chunk0", "chunk1", "chunk2", "index"))
    try:
        assert finish_private(child).sequence.phase == "completed"
        assert p.release_private_file_sequence(child).sequence.release == "confirmed"
    finally:
        p.release_private_file_sequence(child)


def test_private_capacity_refuses_before_target_effect(private_root, monkeypatch):
    root, parent, _ = private_root
    writes = []
    original = os.write

    def trace(fd, body):
        writes.append(fd)
        return original(fd, body)

    monkeypatch.setattr(os, "write", trace)
    monkeypatch.setitem(s._OS, "write", trace)
    with pytest.raises(
        p.PrivateDirectoryRefusal, match="private_directory_capacity_exceeded"
    ):
        private_sequence(private_root, tuple("record" + str(i) for i in range(10)))
    assert list(root.iterdir()) == []
    assert writes == []
    assert p.observe_private_directory(parent).active_sequence_ref is None


def test_private_root_fd_really_used_by_original_reader(private_root, monkeypatch):
    root, handle, binding = private_root
    (root / "record").write_bytes(b"actual")
    original = n._ReadLedger.open
    fds = []

    def trace(self, path, flags, **kwargs):
        fd = original(self, path, flags, **kwargs)
        if kwargs.get("dir_fd") is None:
            fds.append(os.fstat(fd))
        return fd

    monkeypatch.setattr(n._ReadLedger, "open", trace)
    result = p.observe_private_directory_file(
        handle, expected_binding=binding, path="record", maximum_bytes=1024
    )
    assert result.original.observation.content == b"actual"
    assert [(info.st_dev, info.st_ino) for info in fds] == [
        (binding.device, binding.inode)
    ]


def test_private_sequence_unknown_lookup_refusal_holds_no_family(private_root):
    root, _, _ = private_root
    child = private_sequence(private_root)
    ref = weakref.ref(child)
    with pytest.raises(p.PrivateDirectoryRefusal):
        p.observe_private_file_sequence(object())
    del child
    gc.collect()
    assert ref() is None
    assert list(root.iterdir()) == []


def test_private_native_nonjoined_methods_are_conserved():
    repository = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "aware.repo.toml").exists()
    )
    path = Path(s.__file__).relative_to(repository)
    before = ast.parse(
        subprocess.check_output(
            ["git", "show", "3010b76cd464:" + str(path)], cwd=repository, text=True
        )
    )
    after = ast.parse(Path(s.__file__).read_text())

    def methods(tree):
        cls = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "_SequenceIO"
        )
        return {
            node.name: ast.dump(node)
            for node in cls.body
            if isinstance(node, ast.FunctionDef)
            and node.name not in {"__init__", "open"}
        }

    assert methods(before) == methods(after)


def test_private_successful_close_then_snapshot_failure_is_retained(
    private_root, monkeypatch
):
    _, handle, _ = private_root
    original = p._directory_observation

    def snapshot(state):
        if state.close_attempted:
            raise MemoryError("post-close snapshot")
        return original(state)

    monkeypatch.setattr(p, "_directory_observation", snapshot)
    with pytest.raises(p.PrivateDirectoryRefusal) as caught:
        p.release_private_directory(handle)
    cleanup = caught.value.evidence.cleanup
    assert cleanup.release == "confirmed"
    assert cleanup.observation.resources[0].ownership == "released"
    assert cleanup.observation.resources[0].release_attempted
    assert not cleanup.observation.ledger_complete
    monkeypatch.setattr(p, "_directory_observation", original)
    assert p.release_private_directory(handle).release == "confirmed"


@pytest.mark.parametrize("port", ("read", "prepare", "execute", "verify"))
def test_private_native_export_substitution_refuses_before_foreign_execution(
    private_root, monkeypatch, port
):
    _, parent, binding = private_root
    child = private_sequence(private_root) if port in {"execute", "verify"} else None
    module, attribute, _, _ = p._ORIGINAL_PORTS[port]
    calls = []

    def foreign(*args, **kwargs):
        calls.append(True)
        raise AssertionError("foreign body executed")

    monkeypatch.setattr(module, attribute, foreign)
    try:
        with pytest.raises(
            p.PrivateDirectoryRefusal, match="private_root_validation_unavailable"
        ):
            if port == "read":
                p.observe_private_directory_file(
                    parent, expected_binding=binding, path="record", maximum_bytes=1024
                )
            elif port == "prepare":
                private_sequence(private_root)
            elif port == "verify":
                p.verify_private_file_sequence(
                    child,
                    expected_binding=p.observe_private_file_sequence(child).binding,
                )
            else:
                p.execute_next_private_file_step(child, expected_ordinal=0)
        assert calls == []
    finally:
        if child is not None:
            p.release_private_file_sequence(child)


def test_private_exact_four_mib_batch(private_root):
    root, parent, binding = private_root
    child = p.retain_private_file_sequence(
        parent,
        expected_binding=binding,
        requests=tuple(
            n.ConfinedFileMutationRequest(
                n.ConfinedMutationKind.CREATE,
                "chunk" + str(i),
                False,
                None,
                bytes([i]) * 1048576,
            )
            for i in range(4)
        ),
        limits=s.ConfinedSequenceLimits(**s._LIMIT_CAPS),
        confinement_profile=n.ConfinedMutationProfile.DESCRIPTOR_WALK_V1,
    )
    try:
        assert finish_private(child).sequence.phase == "completed"
        assert sum(path.stat().st_size for path in root.iterdir()) == 4 * 1048576
    finally:
        p.release_private_file_sequence(child)


def test_private_child_unknown_cleanup_does_not_transfer_uncertainty(
    private_root, monkeypatch
):
    _, parent, _ = private_root
    child = private_sequence(private_root)
    finish_private(child)
    original = s._OS["close"]
    calls = []

    def close_and_interrupt(fd):
        calls.append(fd)
        original(fd)
        raise KeyboardInterrupt

    monkeypatch.setitem(s._OS, "close", close_and_interrupt)
    with pytest.raises(p.PrivateDirectoryRefusal) as caught:
        p.release_private_file_sequence(child)
    assert caught.value.evidence.sequence.cleanup.release == "unknown"
    assert p.observe_private_directory(parent).phase == "retired"
    count = len(calls)
    with pytest.raises(p.PrivateDirectoryRefusal):
        p.release_private_file_sequence(child)
    assert len(calls) == count
    assert p.release_private_directory(parent).release == "confirmed"
    assert caught.value.evidence.sequence.cleanup.release == "unknown"


def test_private_root_missing_has_typed_acquisition_evidence(tmp_path):
    with pytest.raises(p.PrivateDirectoryRefusal) as caught:
        p.retain_private_directory(
            root=tmp_path / "missing",
            privacy_profile="effective_user_private_namespace_v1",
        )
    assert caught.value.evidence.cause_type == "FileNotFoundError"
    assert caught.value.evidence.cleanup.release == "confirmed"
    assert caught.value.evidence.directory.resources == ()


def test_private_reader_return_failure_preserves_captured_bytes(
    private_root, monkeypatch
):
    root, parent, binding = private_root
    (root / "record").write_bytes(b"known bytes")
    called = []

    def foreign(*args):
        called.append(True)
        raise MemoryError

    monkeypatch.setattr(p, "PrivateFileReadResult", foreign)
    with pytest.raises(p.PrivateDirectoryRefusal) as caught:
        p.observe_private_directory_file(
            parent, expected_binding=binding, path="record", maximum_bytes=1024
        )
    assert caught.value.evidence.read.observation.content == b"known bytes"
    assert caught.value.evidence.read.cleanup.outcome == "closed"
    assert (
        not called
    )  # Original value authentication precedes a substituted constructor.


def test_private_observed_snapshots_remain_detached(private_root):
    _, parent, binding = private_root
    before = p.observe_private_directory(parent)
    p.validate_private_directory(parent, expected_binding=binding)
    cleanup = p.release_private_directory(parent)
    assert before.phase == "active"
    assert before.resources[0].ownership == "owned"
    assert cleanup.observation.resources[0].ownership == "released"


def test_private_cleanup_uses_original_after_export_substitution(
    private_root, monkeypatch
):
    child = private_sequence(private_root)
    calls = []

    def foreign(*args):
        calls.append(True)
        raise AssertionError("replacement cleanup")

    monkeypatch.setattr(s, "release_confined_file_sequence", foreign)
    assert p.release_private_file_sequence(child).sequence.release == "confirmed"
    assert calls == []


@pytest.fixture
def values(tmp_path):
    """Real native writer evidence; private correlation remains descriptive."""
    handle = s.retain_confined_file_sequence(
        root=tmp_path,
        requests=(
            n.ConfinedFileMutationRequest(
                n.ConfinedMutationKind.CREATE, "original", False, None, b"native bytes"
            ),
        ),
        limits=s.ConfinedSequenceLimits(**s._LIMIT_CAPS),
        confinement_profile=n.ConfinedMutationProfile.DESCRIPTOR_WALK_V1,
    )
    try:
        binding = s.observe_confined_file_sequence(handle).binding
        for step in binding.ordered_steps:
            last = s.execute_next_confined_file_step(
                handle, expected_ordinal=step.ordinal
            )
        observed = s.observe_confined_file_sequence(handle)
    finally:
        cleanup = s.release_confined_file_sequence(handle)
    info = tmp_path.stat()
    directory = p.PrivateDirectoryBinding(
        "provider:fixture",
        "generation:fixture",
        "directory:fixture",
        str(tmp_path),
        info.st_dev,
        info.st_ino,
        os.geteuid(),
        os.geteuid(),
        0o700,
        "effective_user_private_namespace_v1",
        os.getpid(),
        1,
    )
    root = p.PrivateRootObservation(
        "observed",
        info.st_dev,
        info.st_ino,
        os.geteuid(),
        os.geteuid(),
        0o700,
        info.st_ctime_ns,
    )
    no_failure = s.ConfinedSequencePrimaryFailure("none", None, None, None, None, False)
    view = p.PrivateDirectoryObservation(
        directory, "released", root, 3, None, (), no_failure, True
    )
    private_binding = p.PrivateSequenceBinding(
        "private-sequence:fixture", directory, binding
    )
    read = n.observe_confined_file_with_cleanup(root=tmp_path, path="original")
    failed_read = p.PrivateReadFailure(
        "filesystem_read_cleanup_unverified",
        "cleanup",
        "interrupted",
        str(tmp_path),
        "original",
        read.observation,
        n.ConfinedFileReadCleanup("unknown", 2, 2, None, ("interrupted",)),
    )
    by_type = {
        p.PrivateDirectoryBinding: directory,
        p.PrivateRootObservation: root,
        p.PrivateDirectoryObservation: view,
        p.PrivateSequenceBinding: private_binding,
        p.PrivateSequenceObservation: p.PrivateSequenceObservation(
            private_binding, view, observed
        ),
        p.PrivateSequenceStepResult: p.PrivateSequenceStepResult(
            private_binding, view, view, last
        ),
        p.PrivateSequenceCleanup: p.PrivateSequenceCleanup(
            private_binding, view, cleanup
        ),
        p.PrivateDirectoryCleanup: p.PrivateDirectoryCleanup(view, "confirmed"),
        p.PrivateFileReadResult: p.PrivateFileReadResult(view, view, read),
        p.PrivateReadFailure: failed_read,
        p.PrivateDirectoryRefusalEvidence: p.PrivateDirectoryRefusalEvidence(
            "private_return_incomplete",
            "KeyboardInterrupt",
            "result",
            view,
            None,
            failed_read,
            None,
            s.ConfinedSequencePrimaryFailure(
                "observed",
                "provider:fixture",
                "result",
                "interrupted",
                "KeyboardInterrupt",
                True,
            ),
            False,
        ),
    }
    return by_type


@pytest.mark.parametrize("cls", p._PRIVATE_TYPES, ids=lambda cls: cls.__name__)
def test_eleven_roots_round_trip_exact_detached_types(values, cls):
    original = values[cls]
    payload = p.private_directory_value_to_payload(original)
    decoded = p.private_directory_value_from_payload(cls, payload)
    assert decoded == original and type(decoded) is cls and decoded is not original
    assert p.private_directory_value_to_payload(decoded) == payload
    assert json.loads(json.dumps(payload, allow_nan=False)) == payload
    payload["value"].clear()
    assert decoded == original


@pytest.mark.parametrize("cls", p._PRIVATE_TYPES, ids=lambda cls: cls.__name__)
def test_production_fields_match_accepted_authored_contract(cls):
    repository = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "aware.repo.toml").exists()
    )
    report = (
        repository / "docs/reports/filesystem-private-directory-io-contract-20261016.md"
    ).read_text()
    code = re.search(r"```python\n(.*?)\n```", report, re.DOTALL).group(1)
    declaration = next(
        node
        for node in ast.parse(code).body
        if isinstance(node, ast.ClassDef) and node.name == cls.__name__
    )
    assert [f.name for f in fields(cls)] == [
        node.target.id for node in declaration.body if isinstance(node, ast.AnnAssign)
    ]
    production = next(
        node
        for node in ast.parse(Path(p.__file__).read_text()).body
        if isinstance(node, ast.ClassDef) and node.name == cls.__name__
    )
    assert [
        ast.dump(node.annotation)
        for node in production.body
        if isinstance(node, ast.AnnAssign)
    ] == [
        ast.dump(node.annotation)
        for node in declaration.body
        if isinstance(node, ast.AnnAssign)
    ]


@pytest.mark.parametrize(
    "body", (b"", b"\x00", b"\xff\xfe", b"\r\nx\n", bytes(range(256)), b"a" * 1048576)
)
def test_lossless_original_bytes_and_null_are_distinct(values, body):
    original = n.ConfinedFileObservation(
        "original",
        n.ConfinedObservationOutcome.OBSERVED,
        True,
        "sha256:" + hashlib.sha256(body).hexdigest(),
        len(body),
        body,
    )
    value = replace(values[p.PrivateReadFailure], observation=original)
    payload = p.private_directory_value_to_payload(value)
    encoded = payload["value"]["observation"]["value"]["content"]
    assert encoded["value"]["byte_count"] == len(body)
    assert (
        p.private_directory_value_from_payload(type(value), payload).observation.content
        == body
    )
    null_value = replace(value, observation=None)
    assert (
        p.private_directory_value_to_payload(null_value)["value"]["observation"] is None
    )


@pytest.mark.parametrize(
    "field,replacement",
    (
        ("data", "Zh=="),
        ("data", "Zg===\n"),
        ("byte_count", True),
        ("byte_count", -1),
        ("byte_count", 16777217),
        ("content_sha256", "sha256:" + "0" * 64),
        ("encoding", "utf8"),
    ),
)
def test_corrupt_byte_envelopes_refuse(values, field, replacement):
    value = values[p.PrivateReadFailure]
    body = b"f"
    value = replace(
        value,
        observation=n.ConfinedFileObservation(
            "original",
            n.ConfinedObservationOutcome.OBSERVED,
            True,
            "sha256:" + hashlib.sha256(body).hexdigest(),
            1,
            body,
        ),
    )
    payload = p.private_directory_value_to_payload(value)
    payload["value"]["observation"]["value"]["content"]["value"][field] = replacement
    with pytest.raises(p.PrivateDirectoryRefusal):
        p.private_directory_value_from_payload(type(value), payload)


@pytest.mark.parametrize(
    "change",
    (
        "missing",
        "extra",
        "unknown_contract",
        "bool_integer",
        "bad_literal",
        "nonfinite",
        "custom_dict",
    ),
)
def test_strict_closed_fields_and_scalars(values, change):
    value = values[p.PrivateDirectoryBinding]
    payload = p.private_directory_value_to_payload(value)
    if change == "missing":
        del payload["value"]["inode"]
    elif change == "extra":
        payload["value"]["extra"] = None
    elif change == "unknown_contract":
        payload["contract"] += ".future"
    elif change == "bool_integer":
        payload["value"]["inode"] = True
    elif change == "bad_literal":
        payload["value"]["privacy_profile"] = "private"
    elif change == "nonfinite":
        payload["value"]["inode"] = float("inf")
    else:

        class Dict(dict):
            pass

        payload = Dict(payload)
    with pytest.raises(p.PrivateDirectoryRefusal, match="private_codec_value_invalid"):
        p.private_directory_value_from_payload(type(value), payload)


@pytest.mark.parametrize(
    "bad_type",
    (dict, object, p.PrivateDirectoryRefusal, s.RetainedConfinedFileSequence),
)
def test_decode_cannot_construct_live_or_foreign_types(values, bad_type):
    payload = p.private_directory_value_to_payload(values[p.PrivateDirectoryBinding])
    with pytest.raises(p.PrivateDirectoryRefusal, match="private_codec_value_invalid"):
        p.private_directory_value_from_payload(bad_type, payload)


def test_codec_performs_no_io_or_registry_enrollment(values, monkeypatch):
    before = dict(s._HANDLES)
    value = values[p.PrivateDirectoryRefusalEvidence]

    def forbidden(*args, **kwargs):
        raise AssertionError("codec_io")

    for name in (
        "open",
        "read",
        "write",
        "close",
        "stat",
        "lstat",
        "fstat",
        "chmod",
        "unlink",
    ):
        monkeypatch.setattr(os, name, forbidden)
    payload = p.private_directory_value_to_payload(value)
    assert p.private_directory_value_from_payload(type(value), payload) == value
    assert s._HANDLES == before


def test_native_owner_inverse_and_encoder_retain_exact_original_payload(values):
    value = values[p.PrivateSequenceBinding].sequence
    payload = s.confined_sequence_value_to_payload(value)
    assert s._confined_sequence_value_from_payload(type(value), payload) == value
    assert (
        p.private_directory_value_to_payload(values[p.PrivateSequenceBinding])["value"][
            "sequence"
        ]
        == payload
    )


def test_native_read_owner_inverse_keeps_unknown_cleanup(values):
    value = values[p.PrivateReadFailure].cleanup
    payload = n._confined_read_value_to_payload(value)
    assert n._confined_read_value_from_payload(type(value), payload) == value
    assert value.closed_count is None


def test_full_read_refusal_union_survives_json_and_cleanup(values):
    value = values[p.PrivateDirectoryRefusalEvidence]
    payload = json.loads(json.dumps(p.private_directory_value_to_payload(value)))
    decoded = p.private_directory_value_from_payload(type(value), payload)
    assert type(decoded.read) is p.PrivateReadFailure
    assert decoded.read.cleanup.outcome == "unknown"
    assert decoded.read.cleanup.closed_count is None
    assert decoded.read.observation.content == b"native bytes"
    assert decoded.ledger_complete is False


def test_native_constructor_substitution_refuses_without_invocation(
    values, monkeypatch
):
    payload = p.private_directory_value_to_payload(values[p.PrivateSequenceBinding])
    called = []

    def substitute(*args, **kwargs):
        called.append(True)
        raise AssertionError("foreign_constructor")

    monkeypatch.setattr(s.ConfinedSequenceBinding, "__init__", substitute)
    with pytest.raises(p.PrivateDirectoryRefusal):
        p.private_directory_value_from_payload(p.PrivateSequenceBinding, payload)
    assert not called


@pytest.mark.parametrize(
    "limit", ("_MAX_PRIVATE", "_MAX_NATIVE", "_MAX_WIRE", "_MAX_BYTES")
)
def test_shared_limits_refuse_in_both_directions(values, monkeypatch, limit):
    value = (
        values[p.PrivateSequenceStepResult]
        if limit == "_MAX_NATIVE"
        else values[p.PrivateReadFailure]
    )
    payload = p.private_directory_value_to_payload(value)
    monkeypatch.setattr(p, limit, 1)
    for operation in (
        lambda: p.private_directory_value_to_payload(value),
        lambda: p.private_directory_value_from_payload(type(value), payload),
    ):
        with pytest.raises(
            p.PrivateDirectoryRefusal, match="private_codec_capacity_exceeded"
        ):
            operation()


def test_same_object_repeated_native_occurrences_share_one_budget(values, monkeypatch):
    value = values[p.PrivateSequenceStepResult]
    payload = p.private_directory_value_to_payload(value)
    size = len(
        json.dumps(
            payload["value"]["binding"]["value"]["sequence"],
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode()
    )
    monkeypatch.setattr(p, "_MAX_NATIVE", size + 1)
    with pytest.raises(
        p.PrivateDirectoryRefusal, match="private_codec_capacity_exceeded"
    ):
        p.private_directory_value_to_payload(value)


def test_invalid_input_is_not_mutated(values):
    payload = p.private_directory_value_to_payload(values[p.PrivateReadFailure])
    payload["value"]["cleanup"]["value"]["closed_count"] = True
    before = copy.deepcopy(payload)
    with pytest.raises(p.PrivateDirectoryRefusal):
        p.private_directory_value_from_payload(p.PrivateReadFailure, payload)
    assert payload == before


def test_partial_module_does_not_advertise_unimplemented_io():
    assert callable(p.retain_private_file_sequence)
    assert callable(p.retain_private_directory)
    assert callable(p.observe_private_directory_file)


def test_foreign_metaclass_equality_is_never_invoked():
    called = []

    class Meta(type):
        def __eq__(cls, other):
            called.append(True)
            return True

        __hash__ = type.__hash__

    class Foreign(metaclass=Meta):
        pass

    with pytest.raises(p.PrivateDirectoryRefusal):
        p.private_directory_value_to_payload(Foreign())
    assert not called


@pytest.mark.parametrize("nested", (False, True))
def test_nonstring_mapping_key_refuses_without_hash_or_equality(values, nested):
    called = []

    class Key:
        def __hash__(self):
            called.append("hash")
            return hash("contract")

        def __eq__(self, other):
            called.append("eq")
            return False

    payload = p.private_directory_value_to_payload(values[p.PrivateDirectoryBinding])
    target = payload["value"] if nested else payload
    target[Key()] = "foreign"
    called.clear()
    with pytest.raises(p.PrivateDirectoryRefusal):
        p.private_directory_value_from_payload(p.PrivateDirectoryBinding, payload)
    assert not called


@pytest.mark.parametrize("method", ("__getattribute__",))
def test_private_constructor_and_accessor_substitution_is_not_executed(
    values, monkeypatch, method
):
    payload = p.private_directory_value_to_payload(values[p.PrivateDirectoryBinding])
    called = []

    def substitute(*args, **kwargs):
        called.append(True)
        raise AssertionError("foreign execution")

    monkeypatch.setattr(p.PrivateDirectoryBinding, method, substitute)
    with pytest.raises(p.PrivateDirectoryRefusal):
        p.private_directory_value_from_payload(p.PrivateDirectoryBinding, payload)
    assert not called


def test_private_new_substitution_refuses_in_isolated_process():
    # Restoring __new__ in-place changes CPython type-slot dispatch; isolate
    # the diagnostic so later fixtures do not inherit that interpreter state.
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
from aware_file_system import private_directory as p
value = p.PrivateRootObservation('unavailable', None, None, None, None, None, None)
payload = p.private_directory_value_to_payload(value)
called = []
def foreign(*args, **kwargs):
    called.append(True)
    raise AssertionError('foreign new')
p.PrivateRootObservation.__new__ = staticmethod(foreign)
try:
    p.private_directory_value_from_payload(p.PrivateRootObservation, payload)
except p.PrivateDirectoryRefusal:
    pass
else:
    raise AssertionError('missing refusal')
assert not called
""",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_byte_budget_refuses_before_decode_allocation(values, monkeypatch):
    payload = p.private_directory_value_to_payload(values[p.PrivateReadFailure])
    payload["value"]["observation"]["value"]["content"]["value"]["byte_count"] = (
        p._MAX_BYTES + 1
    )
    called = []

    def forbidden(*args, **kwargs):
        called.append(True)
        raise AssertionError("allocation before bound")

    monkeypatch.setattr(p.base64, "b64decode", forbidden)
    with pytest.raises(
        p.PrivateDirectoryRefusal, match="private_codec_capacity_exceeded"
    ):
        p.private_directory_value_from_payload(p.PrivateReadFailure, payload)
    assert not called


def test_genuine_native_refusal_preserves_original_error_and_cleanup(values, tmp_path):
    (tmp_path / "collision").write_bytes(b"original")
    with pytest.raises(s.ConfinedSequenceRefusal) as refused:
        s.retain_confined_file_sequence(
            root=tmp_path,
            requests=(
                n.ConfinedFileMutationRequest(
                    n.ConfinedMutationKind.CREATE, "collision", False, None, b"new"
                ),
            ),
            limits=s.ConfinedSequenceLimits(**s._LIMIT_CAPS),
            confinement_profile=n.ConfinedMutationProfile.DESCRIPTOR_WALK_V1,
        )
    original = refused.value.evidence
    value = replace(values[p.PrivateDirectoryRefusalEvidence], sequence=original)
    decoded = p.private_directory_value_from_payload(
        type(value), p.private_directory_value_to_payload(value)
    )
    assert decoded.sequence == original
    assert (tmp_path / "collision").read_bytes() == b"original"


@pytest.mark.parametrize(
    "module,added",
    (
        (n, {"_confined_read_value_to_payload", "_confined_read_value_from_payload"}),
        (s, {"_confined_sequence_value_from_payload"}),
    ),
)
def test_all_predecessor_native_executable_ast_is_unchanged(module, added):
    repository = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "aware.repo.toml").exists()
    )
    path = Path(module.__file__).relative_to(repository)
    predecessor = subprocess.check_output(
        ["git", "show", "7ad2ef01498d876b064c4682996750a4b29a70fd:" + str(path)],
        cwd=repository,
        text=True,
    )
    original = ast.parse(predecessor)
    current = ast.parse(Path(module.__file__).read_text())
    current.body = [
        node
        for node in current.body
        if not isinstance(node, ast.FunctionDef) or node.name not in added
    ]
    if module is n:
        # The admitted IO successor changes only the original read ledger and
        # reader; conserve every other predecessor top-level declaration.
        joined = {"_ReadLedger", "_observe_confined_file_with_custody", "_read_current"}
        original.body = [
            node for node in original.body if getattr(node, "name", None) not in joined
        ]
        current.body = [
            node for node in current.body if getattr(node, "name", None) not in joined
        ]
    if module is s:
        joined = {
            "_snapshot",
            "_SequenceState",
            "_SequenceIO",
            "_check_current",
            "retain_confined_file_sequence",
            "_retain_confined_file_sequence",
        }
        original.body = [
            node for node in original.body if getattr(node, "name", None) not in joined
        ]
        current.body = [
            node for node in current.body if getattr(node, "name", None) not in joined
        ]
    assert ast.dump(current) == ast.dump(original)


@pytest.mark.parametrize(
    "module,name,cls,decode",
    (
        (n, "_confined_read_value_to_payload", p.PrivateReadFailure, False),
        (n, "_confined_read_value_from_payload", p.PrivateReadFailure, True),
        (s, "_confined_sequence_value_from_payload", p.PrivateSequenceBinding, True),
    ),
)
def test_owner_helper_substitution_refuses_before_foreign_execution(
    values, monkeypatch, module, name, cls, decode
):
    value = values[cls]
    payload = p.private_directory_value_to_payload(value)
    called = []

    def foreign(*args, **kwargs):
        called.append(True)
        raise AssertionError("foreign helper")

    monkeypatch.setattr(module, name, foreign)
    with pytest.raises(p.PrivateDirectoryRefusal):
        if decode:
            p.private_directory_value_from_payload(cls, payload)
        else:
            p.private_directory_value_to_payload(value)
    assert not called


def test_held_refusal_does_not_retain_rejected_original_handle(tmp_path):
    def reject():
        handle = s.retain_confined_file_sequence(
            root=tmp_path,
            requests=(
                n.ConfinedFileMutationRequest(
                    n.ConfinedMutationKind.CREATE, "absent", False, None, b"body"
                ),
            ),
            limits=s.ConfinedSequenceLimits(**s._LIMIT_CAPS),
            confinement_profile=n.ConfinedMutationProfile.DESCRIPTOR_WALK_V1,
        )
        reference = weakref.ref(handle)
        try:
            p.private_directory_value_to_payload(handle)
        except p.PrivateDirectoryRefusal as error:
            return reference, error
        finally:
            handle = None

    reference, held = reject()
    gc.collect()
    assert held.code == "private_codec_value_invalid"
    assert reference() is None
    assert not (tmp_path / "absent").exists()


def test_all_defined_exports_resolve_and_no_live_classes_exist():
    assert len(p.__all__) == len(set(p.__all__))
    for name in p.__all__:
        assert getattr(p, name) is not None
    assert "RetainedPrivateDirectory" in p.__all__
    assert "RetainedPrivateFileSequence" in p.__all__


@pytest.mark.parametrize("text", ("é", 'a"\\\n\x00', "🌍", "\u2028"))
def test_exact_unicode_wire_accounting_before_copy(values, text):
    value = replace(values[p.PrivateDirectoryBinding], provider_ref=text)
    payload = p.private_directory_value_to_payload(value)
    size = len(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode())
    budget = p._Budget()
    p._value(value, type(value), budget)
    assert p._MAX_WIRE - budget.wire == size
    assert p.private_directory_value_from_payload(type(value), payload) == value


def test_large_private_string_refuses_before_json_copy(values, monkeypatch):
    payload = p.private_directory_value_to_payload(values[p.PrivateDirectoryBinding])
    payload["value"]["provider_ref"] = "🌍" * (p._MAX_PRIVATE // 2)
    original = p.json.dumps
    called = []

    def guarded(value, *args, **kwargs):
        if type(value) is str and len(value) > 4096:
            called.append(True)
            raise AssertionError("large string copy")
        return original(value, *args, **kwargs)

    monkeypatch.setattr(p.json, "dumps", guarded)
    with pytest.raises(
        p.PrivateDirectoryRefusal, match="private_codec_capacity_exceeded"
    ):
        p.private_directory_value_from_payload(p.PrivateDirectoryBinding, payload)
    assert not called


@pytest.mark.parametrize("read_kind", ("none", "success", "failure"))
@pytest.mark.parametrize("cleanup_kind", ("none", "directory", "sequence"))
def test_complete_read_and_cleanup_unions_preserve_exact_variants(
    values, read_kind, cleanup_kind
):
    read = {
        "none": None,
        "success": values[p.PrivateFileReadResult].original,
        "failure": values[p.PrivateReadFailure],
    }[read_kind]
    cleanup = {
        "none": None,
        "directory": values[p.PrivateDirectoryCleanup],
        "sequence": values[p.PrivateSequenceCleanup],
    }[cleanup_kind]
    value = replace(
        values[p.PrivateDirectoryRefusalEvidence], read=read, cleanup=cleanup
    )
    payload = p.private_directory_value_to_payload(value)
    decoded = p.private_directory_value_from_payload(type(value), payload)
    assert decoded == value
    assert type(decoded.read) is type(read)
    assert type(decoded.cleanup) is type(cleanup)


INVALID_READ_FIELDS = (
    ("root_locator", "relative/root"),
    ("root_locator", "/tmp/../escape"),
    ("root_locator", "/tmp//alias"),
    ("root_locator", "/tmp/./alias"),
    ("root_locator", "/tmp/alias/"),
    ("root_locator", "/" + "x" * 4096),
    ("root_locator", "/tmp/\u0080root"),
    ("path", "../escape"),
    ("path", "/absolute"),
    ("path", "a/" + "/".join(["b"] * 64)),
    ("path", "a//b"),
    ("path", "a\\b"),
    ("path", "x" * 1025),
    ("path", "e\u0301"),
    ("code", "bad\ncode"),
    ("code", "bad\u007fcode"),
    ("code", "bad\u009fcode"),
    ("stage", "x" * 1025),
    ("stage", "é" * 513),
    ("cause_kind", "e\u0301"),
    ("cause_kind", "x" * 1025),
)


@pytest.mark.parametrize("field,bad", INVALID_READ_FIELDS)
@pytest.mark.parametrize("decode", (False, True))
def test_private_read_failure_reuses_original_field_rules(values, field, bad, decode):
    original = values[p.PrivateReadFailure]
    invalid = replace(original, **{field: bad})
    kwargs = {item.name: getattr(invalid, item.name) for item in fields(invalid)}
    code = kwargs.pop("code")
    with pytest.raises((ValueError, TypeError)):
        n.ConfinedFileObservationError(code, **kwargs)
    if decode:
        payload = p.private_directory_value_to_payload(original)
        payload["value"][field] = bad
        before = copy.deepcopy(payload)
        with pytest.raises(
            p.PrivateDirectoryRefusal, match="private_codec_value_invalid"
        ):
            p.private_directory_value_from_payload(type(original), payload)
        assert payload == before
    else:
        with pytest.raises(
            p.PrivateDirectoryRefusal, match="private_codec_value_invalid"
        ):
            p.private_directory_value_to_payload(invalid)
        assert getattr(invalid, field) == bad


@pytest.mark.parametrize(
    "field,good",
    (
        ("root_locator", None),
        ("root_locator", "/"),
        ("root_locator", "/" + "x" * 4095),
        ("path", None),
        ("path", "/".join(["a"] * 64)),
        ("path", "x" * 1024),
        ("code", "x" * 1024),
        ("stage", "é" * 512),
        ("cause_kind", "valid_é"),
    ),
)
def test_private_read_failure_preserves_valid_boundaries_and_unknown_cleanup(
    values, field, good
):
    value = replace(values[p.PrivateReadFailure], **{field: good})
    payload = p.private_directory_value_to_payload(value)
    decoded = p.private_directory_value_from_payload(type(value), payload)
    assert decoded == value
    assert decoded.cleanup.closed_count is None
    assert decoded.cleanup.outcome == "unknown"


@pytest.mark.parametrize("decode", (False, True))
def test_read_failure_validation_does_not_construct_errors_or_do_io(
    values, monkeypatch, decode
):
    value = values[p.PrivateReadFailure]
    payload = p.private_directory_value_to_payload(value)
    called = []

    def forbidden(*args, **kwargs):
        called.append(True)
        raise AssertionError("validation effect")

    monkeypatch.setattr(n.ConfinedFileObservationError, "__init__", forbidden)
    for name in (
        "open",
        "read",
        "write",
        "close",
        "stat",
        "lstat",
        "fstat",
        "chmod",
        "unlink",
    ):
        monkeypatch.setattr(os, name, forbidden)
    if decode:
        assert p.private_directory_value_from_payload(type(value), payload) == value
    else:
        assert p.private_directory_value_to_payload(value) == payload
    assert not called


@pytest.mark.parametrize("helper", ("_read_text", "_read_root", "_saved_read_path"))
@pytest.mark.parametrize("decode", (False, True))
def test_original_read_field_validator_substitution_refuses(
    values, monkeypatch, helper, decode
):
    value = values[p.PrivateReadFailure]
    payload = p.private_directory_value_to_payload(value)
    called = []

    def foreign(*args, **kwargs):
        called.append(True)
        raise AssertionError("foreign validator")

    monkeypatch.setattr(n, helper, foreign)
    with pytest.raises(p.PrivateDirectoryRefusal):
        if decode:
            p.private_directory_value_from_payload(type(value), payload)
        else:
            p.private_directory_value_to_payload(value)
    assert not called
