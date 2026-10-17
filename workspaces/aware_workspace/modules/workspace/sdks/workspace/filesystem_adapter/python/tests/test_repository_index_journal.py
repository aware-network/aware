"""Exact byte history through original atomic metadata publication."""

from __future__ import annotations

import hashlib
import multiprocessing
import os
import struct
from pathlib import Path

import pytest
from aware_workspace_fs_adapter import repository_delta_store as store_module
from aware_workspace_fs_adapter.repository_index_journal import (
    DeferredIndexBytes,
    IndexJournal,
    IndexJournalError,
    _apply_delta,
    _frame,
    _parse,
)

# Names are installed in the original function's globals by the substitution
# controls. They must resolve there, not through a newly introduced closure.
_TEST_HITS = []
_TEST_VARIANT = None
_TEST_TARGET = None
_TEST_ORIGINAL_CODE = None


def writer(path, prepare):
    return store_module._atomic_write(path, DeferredIndexBytes(prepare))


def journal(tmp_path, *, binding="repo:original", index_format="events_v2", kind=1):
    return IndexJournal(
        tmp_path / "metadata/index.json",
        binding=binding,
        kind=kind,
        index_format=index_format,
    )


def literal(previous, current):
    return (
        b"RDX1"
        + struct.pack(">QI", len(current), int(bool(current)))
        + (b"\0" + struct.pack(">Q", len(current)) + current if current else b"")
    )


def unchanged(previous, current):
    assert previous == current
    return (
        b"RDX1"
        + struct.pack(">QI", len(current), 1)
        + b"\1"
        + struct.pack(">QQ", len(current), 0)
    )


def test_read_is_effect_free_and_existing_format_does_not_migrate(tmp_path):
    original = journal(tmp_path, index_format="auto")
    assert original.read() is None and not tuple(tmp_path.iterdir())
    original.index.parent.mkdir()
    original.index.write_bytes(b"legacy\n")
    assert journal(tmp_path, index_format="auto").format == "json_v1"
    with pytest.raises(IndexJournalError, match="migration"):
        journal(tmp_path)
    original.directory.mkdir()
    for format in ("json_v1", "auto", "events_v2"):
        with pytest.raises(IndexJournalError, match="Mixed"):
            journal(tmp_path, index_format=format)


def test_empty_v2_directory_is_not_genesis(tmp_path):
    (tmp_path / "metadata/index.events-v2").mkdir(parents=True)
    for format in ("events_v2", "auto"):
        with pytest.raises(IndexJournalError, match="no committed"):
            journal(tmp_path, index_format=format)


@pytest.mark.parametrize("kind", [1, 2])
@pytest.mark.parametrize(
    "body", [b"", b'{"records":[]}\n', b"NaN -0.0 \\ud800\n", bytes(range(256))]
)
def test_full_canonical_bytes_reopen_and_checkpoint(tmp_path, kind, body):
    original = journal(tmp_path, kind=kind)
    for sequence in range(1, 4):
        current = body + str(sequence).encode()
        original.publish(current, writer=writer, delta=literal)
        assert original.read() == current
        assert journal(tmp_path, kind=kind, index_format="auto").read() == current
        paths = tuple(original.directory.iterdir())
        assert len(paths) == 1
        assert paths[0].stat().st_mode & 0o777 == 0o600
        frame = _parse(paths[0].read_bytes(), kind=kind, binding=b"repo:original")
        assert frame.mode == 0 and frame.sequence == sequence


def test_lossless_delta_and_explicit_fresh_serialization(tmp_path):
    original = journal(tmp_path)
    content = b'{"retained":"' + b"x" * 10000 + b'"}\n'
    original.publish(content, writer=writer)
    calls = []

    def produce():
        calls.append("fresh")
        return content

    original.publish(produce, writer=writer, delta=unchanged)
    assert calls == ["fresh"]
    assert len(tuple(original.directory.iterdir())) == 2
    assert journal(tmp_path).read() == content
    # Current fields, including old rows, remain authoritative on every call.
    changed = content.replace(b"xxx", b"yxx", 1)
    original.publish(changed, writer=writer, delta=literal)
    assert journal(tmp_path).read() == changed
    assert len(tuple(original.directory.iterdir())) == 1


@pytest.mark.parametrize("boundary", ["encode", "fsync", "replace"])
@pytest.mark.parametrize("interrupt", [False, True])
def test_failed_publish_preserves_prior_history_and_is_terminal(
    tmp_path, monkeypatch, boundary, interrupt
):
    original = journal(tmp_path)
    original.publish(b"original", writer=writer)
    before = {p.name: p.read_bytes() for p in original.directory.iterdir()}
    error = (
        KeyboardInterrupt("original interrupt")
        if interrupt
        else OSError("original failure")
    )

    def fail(*args, **kwargs):
        raise error

    def produce():
        raise error

    with monkeypatch.context() as patch:
        if boundary != "encode":
            patch.setattr(store_module.os, boundary, fail)
        with pytest.raises(type(error)) as caught:
            original.publish(
                produce if boundary == "encode" else b"successor", writer=writer
            )
    assert caught.value is error
    assert original.failure_evidence.publication == "not_written"
    assert {p.name: p.read_bytes() for p in original.directory.iterdir()} == before
    assert journal(tmp_path).read() == b"original"
    with pytest.raises(IndexJournalError, match="terminal"):
        original.publish(b"restored", writer=writer)


@pytest.mark.parametrize("boundary", ["replace", "directory_sync", "obsolete_unlink"])
def test_lost_return_preserves_committed_successor_and_refuses_retry(
    tmp_path, monkeypatch, boundary
):
    original = journal(tmp_path)
    original.publish(b"original", writer=writer)
    error = OSError("lost original return")
    actual_replace, actual_fsync, actual_unlink = os.replace, os.fsync, Path.unlink

    def replace(*args, **kwargs):
        actual_replace(*args, **kwargs)
        raise error

    def fsync(descriptor):
        actual_fsync(descriptor)
        if os.path.isdir(f"/proc/self/fd/{descriptor}"):
            raise error

    def unlink(path, *args, **kwargs):
        actual_unlink(path, *args, **kwargs)
        if path.name.endswith(".txn"):
            raise error

    with monkeypatch.context() as patch:
        if boundary == "replace":
            patch.setattr(os, "replace", replace)
        elif boundary == "directory_sync":
            patch.setattr(os, "fsync", fsync)
        else:
            patch.setattr(Path, "unlink", unlink)
        with pytest.raises(OSError) as caught:
            original.publish(b"successor", writer=writer)
    assert caught.value is error
    assert original.failure_evidence.publication == "committed"
    assert original.failure_evidence.cleanup == "unknown"
    assert journal(tmp_path).read() == b"successor"
    with pytest.raises(IndexJournalError, match="terminal"):
        original.publish(b"retry", writer=writer)


def test_concurrent_originals_do_not_overwrite_fresh_history(tmp_path):
    first, stale = journal(tmp_path), journal(tmp_path)
    first.publish(b"one", writer=writer)
    with pytest.raises(IndexJournalError, match="changed"):
        stale.publish(b"foreign", writer=writer)
    assert journal(tmp_path).read() == b"one"


def _competing_process(root, ready, proceed, output):
    original = journal(Path(root))
    ready.set()
    proceed.wait(10)
    try:
        original.publish(b"competing", writer=writer)
    except IndexJournalError:
        output.put("refused")
    else:
        output.put("wrote")


def test_two_process_stale_writer_refuses(tmp_path):
    ctx = multiprocessing.get_context("spawn")
    ready, proceed, output = ctx.Event(), ctx.Event(), ctx.Queue()
    process = ctx.Process(
        target=_competing_process, args=(str(tmp_path), ready, proceed, output)
    )
    process.start()
    try:
        assert ready.wait(10)
        original = journal(tmp_path)
        original.publish(b"winning original", writer=writer)
        proceed.set()
        assert output.get(timeout=10) == "refused"
        process.join(10)
        assert process.exitcode == 0
        assert journal(tmp_path).read() == b"winning original"
    finally:
        if process.is_alive():
            process.terminate()
            process.join()


@pytest.mark.parametrize(
    "mutation", ["digest", "binding", "kind", "sequence", "missing", "data"]
)
def test_corrupt_current_frame_refuses(tmp_path, mutation):
    original = journal(tmp_path)
    original.publish(b"x" * 1000, writer=writer)
    original.publish(b"x" * 1000, writer=writer, delta=unchanged)
    paths = sorted(original.directory.iterdir())
    latest = paths[-1]
    if mutation == "missing":
        paths[0].unlink()
    else:
        encoded = latest.read_bytes()
        if mutation == "digest":
            encoded = encoded[:-1] + bytes([encoded[-1] ^ 1])
        elif mutation == "binding":
            encoded = _frame(
                1,
                2,
                b"repo:foreign!",
                1,
                encoded[encoded.find(b"repo:original") + 13 :][:32],
                1000,
                unchanged(b"x" * 1000, b"x" * 1000),
            )
        elif mutation == "kind":
            encoded = _frame(
                2,
                2,
                b"repo:original",
                1,
                b"x" * 32,
                1000,
                unchanged(b"x" * 1000, b"x" * 1000),
            )
        elif mutation == "sequence":
            encoded = _frame(
                1,
                3,
                b"repo:original",
                1,
                b"x" * 32,
                1000,
                unchanged(b"x" * 1000, b"x" * 1000),
            )
        else:
            encoded = _frame(
                1,
                2,
                b"repo:original",
                1,
                hashlib.sha256(paths[0].read_bytes()[:-32]).digest(),
                1000,
                b"invalid",
            )
        latest.write_bytes(encoded)
    with pytest.raises(IndexJournalError):
        journal(tmp_path)


@pytest.mark.parametrize(
    "data,length",
    [
        (b"", 0),
        (b"RDX1" + bytes(12), 1),
        (b"RDX1" + struct.pack(">QI", 1, 1) + b"\1" + struct.pack(">QQ", 1, 10), 1),
        (b"RDX1" + struct.pack(">QI", 1, 1) + b"\0" + struct.pack(">Q", 2) + b"ab", 1),
    ],
)
def test_delta_rejects_malformed_expansion(data, length):
    with pytest.raises(IndexJournalError):
        _apply_delta(b"a", data, length)


def test_mutated_deferred_producer_never_executes(tmp_path):
    calls = []

    def original(calls=calls):
        return b"original"

    def foreign(calls=calls):
        calls.append(True)
        return b"foreign"

    deferred = DeferredIndexBytes(original)
    original.__code__ = foreign.__code__
    with pytest.raises(IndexJournalError):
        deferred.read()
    assert calls == []
    with pytest.raises(IndexJournalError, match="spent"):
        deferred.read()


@pytest.mark.parametrize("variant", ["return", "raise", "restore"])
def test_deferred_cell_substitution_before_io_return_never_runs(
    tmp_path, monkeypatch, variant
):
    calls = []

    def original():
        return b"original"

    def foreign():
        calls.append(True)
        if variant == "restore":
            callback_cell.cell_contents = original
        if variant == "raise":
            raise OSError("foreign")
        return b"foreign"

    callback = original

    def prepare():
        return callback()

    callback_cell = prepare.__closure__[0]
    deferred = DeferredIndexBytes(prepare)
    actual = store_module.os.fdopen

    def fdopen(*args, **kwargs):
        stream = actual(*args, **kwargs)
        callback_cell.cell_contents = foreign
        return stream

    with monkeypatch.context() as patch:
        patch.setattr(store_module.os, "fdopen", fdopen)
        with pytest.raises(IndexJournalError, match="substituted"):
            store_module._atomic_write(tmp_path / "value", deferred)
    assert calls == [] and not (tmp_path / "value").exists()
    callback_cell.cell_contents = original
    with pytest.raises(IndexJournalError, match="spent"):
        deferred.read()


@pytest.mark.parametrize("variant", ["return", "raise", "restore"])
def test_deferred_read_substitution_during_io_never_runs(
    tmp_path, monkeypatch, variant
):
    calls = []
    original_read = DeferredIndexBytes.read

    def foreign(self):
        calls.append(True)
        if variant == "restore":
            DeferredIndexBytes.read = original_read
        if variant == "raise":
            raise OSError("foreign")
        return b"foreign"

    def prepare():
        return b"original"

    deferred = DeferredIndexBytes(prepare)
    actual = store_module.os.fdopen

    def fdopen(*args, **kwargs):
        stream = actual(*args, **kwargs)
        monkeypatch.setattr(DeferredIndexBytes, "read", foreign)
        return stream

    with monkeypatch.context() as patch:
        patch.setattr(store_module.os, "fdopen", fdopen)
        with pytest.raises(IndexJournalError, match="substituted"):
            store_module._atomic_write(tmp_path / "value", deferred)
    monkeypatch.setattr(DeferredIndexBytes, "read", original_read)
    assert calls == [] and not (tmp_path / "value").exists()


def test_primary_exception_and_precise_evidence_survive_lost_lock_close(
    tmp_path, monkeypatch
):
    original = journal(tmp_path)
    original.publish(b"old", writer=writer)
    primary = KeyboardInterrupt("original producer interruption")
    secondary = OSError("lost lock close")
    actual = os.close
    calls = []

    def close(descriptor):
        target = os.readlink(f"/proc/self/fd/{descriptor}")
        actual(descriptor)
        if target.endswith(".index.lock"):
            calls.append(True)
            raise secondary

    def prepare():
        raise primary

    with monkeypatch.context() as patch:
        patch.setattr(os, "close", close)
        with pytest.raises(KeyboardInterrupt) as caught:
            original.publish(prepare, writer=writer)
    assert caught.value is primary and calls == [True]
    assert original.failure_evidence.sequence == 2
    assert original.failure_evidence.publication == "not_written"
    assert original.failure_evidence.cleanup == "unknown"
    assert "lock cleanup uncertain" in " ".join(primary.__notes__)
    assert journal(tmp_path).read() == b"old"


def test_removed_checkpoint_rejects_before_successor_publication(tmp_path):
    original = journal(tmp_path)
    body = b"x" * 10000
    original.publish(body, writer=writer)
    original.publish(body, writer=writer, delta=unchanged)
    paths = sorted(original.directory.iterdir())
    paths[0].unlink()
    with pytest.raises(FileNotFoundError):
        original.publish(body, writer=writer, delta=unchanged)
    assert sorted(original.directory.iterdir()) == paths[1:]
    with pytest.raises(IndexJournalError, match="terminal"):
        original.publish(body, writer=writer)


@pytest.mark.parametrize("debt", ["obsolete", "pending"])
def test_restart_decodes_but_cannot_reuse_capacity_with_cleanup_debt(
    tmp_path, monkeypatch, debt
):
    original = journal(tmp_path)
    body = b"x" * 10000
    original.publish(body, writer=writer)
    old = next(original.directory.iterdir())
    old_bytes = old.read_bytes()
    original.publish(body + b"changed", writer=writer, delta=literal)
    if debt == "obsolete":
        old.write_bytes(old_bytes)
    else:
        (original.directory / ".pending-unknown").write_bytes(b"pending")
    reopened = journal(tmp_path)
    assert reopened.read() == body + b"changed"
    before = {p.name: p.read_bytes() for p in original.directory.iterdir()}
    assert reopened.failure_evidence.phase == "restart_cleanup_debt"
    with pytest.raises(IndexJournalError, match="terminal"):
        reopened.publish(body + b"changed", writer=writer, delta=unchanged)
    assert {p.name: p.read_bytes() for p in original.directory.iterdir()} == before


@pytest.mark.parametrize("entrance", ["reader", "verify"])
@pytest.mark.parametrize("variant", ["return", "raise", "restore"])
def test_captured_reader_and_nested_verifier_code_checked_before_entry(
    tmp_path, monkeypatch, entrance, variant
):
    import types

    from aware_workspace_fs_adapter import repository_index_journal as identity

    guard = next(
        value
        for value in store_module._atomic_write.__code__.co_consts
        if type(value) is types.FunctionType and value.__name__ == "read"
    )
    target = (
        guard
        if entrance == "reader"
        else next(
            cell.cell_contents
            for cell in guard.__closure__
            if type(cell.cell_contents) is types.FunctionType
            and cell.cell_contents.__name__ == "verify"
        )
    )
    calls = []

    def foreign():
        _TEST_HITS.append(True)
        if _TEST_VARIANT == "restore":
            _TEST_TARGET.__code__ = _TEST_ORIGINAL_CODE
        if _TEST_VARIANT == "raise":
            raise OSError("foreign")
        return b"foreign"

    original_code = target.__code__
    for name, value in {
        "_TEST_HITS": calls,
        "_TEST_VARIANT": variant,
        "_TEST_TARGET": target,
        "_TEST_ORIGINAL_CODE": original_code,
    }.items():
        monkeypatch.setitem(vars(identity), name, value)

    def prepare():
        return b"original"

    deferred = DeferredIndexBytes(prepare)
    target.__code__ = foreign.__code__.replace(co_freevars=target.__code__.co_freevars)
    try:
        with pytest.raises(IndexJournalError, match="entry was substituted"):
            store_module._atomic_write(tmp_path / "value", deferred)
        assert calls == [] and not (tmp_path / "value").exists()
    finally:
        target.__code__ = original_code


@pytest.mark.parametrize("variant", ["return", "raise", "restore"])
def test_writer_code_substitution_during_tip_io_refuses_before_dispatch(
    tmp_path, monkeypatch, variant
):
    original = journal(tmp_path)
    original.publish(b"old", writer=writer)

    def selected(path, prepare):
        return writer(path, prepare)

    selected_code = selected.__code__
    calls = []

    def foreign():
        _TEST_HITS.append(True)
        if _TEST_VARIANT == "restore":
            _TEST_TARGET.__code__ = _TEST_ORIGINAL_CODE
        if _TEST_VARIANT == "raise":
            raise OSError("foreign")

    for name, value in {
        "_TEST_HITS": calls,
        "_TEST_VARIANT": variant,
        "_TEST_TARGET": selected,
        "_TEST_ORIGINAL_CODE": selected_code,
    }.items():
        monkeypatch.setitem(globals(), name, value)
    actual = Path.read_bytes

    def read(path):
        result = actual(path)
        if path.name.endswith(".txn"):
            selected.__code__ = foreign.__code__.replace(
                co_argcount=2,
                co_varnames=("path", "prepare"),
                co_nlocals=2,
                co_freevars=selected_code.co_freevars,
            )
        return result

    before = {p.name: p.read_bytes() for p in original.directory.iterdir()}
    try:
        with monkeypatch.context() as patch:
            patch.setattr(Path, "read_bytes", read)
            with pytest.raises(IndexJournalError, match="writer entry was substituted"):
                original.publish(b"new", writer=selected)
        assert calls == []
    finally:
        selected.__code__ = selected_code
    assert {p.name: p.read_bytes() for p in original.directory.iterdir()} == before
    with pytest.raises(IndexJournalError, match="terminal"):
        original.publish(b"new", writer=selected)


def test_producer_code_substitution_after_pending_io_refuses_before_entry(
    tmp_path, monkeypatch
):
    calls = []

    def original(calls=calls):
        return b"original"

    def foreign(calls=calls):
        calls.append(True)
        return b"foreign"

    original_code = original.__code__
    selected = journal(tmp_path)
    actual = store_module.os.fdopen

    def fdopen(*args, **kwargs):
        result = actual(*args, **kwargs)
        original.__code__ = foreign.__code__
        return result

    try:
        with monkeypatch.context() as patch:
            patch.setattr(store_module.os, "fdopen", fdopen)
            with pytest.raises(
                IndexJournalError, match="canonical producer was substituted"
            ):
                selected.publish(original, writer=writer)
        assert calls == []
    finally:
        original.__code__ = original_code
    with pytest.raises(IndexJournalError, match="terminal"):
        selected.publish(original, writer=writer)


def test_reentrant_publication_cannot_publish_after_close_or_competing_entry(tmp_path):
    original = journal(tmp_path)
    calls = []

    def prepare():
        with pytest.raises(IndexJournalError, match="active"):
            original.publish(b"nested", writer=writer)
        calls.append(True)
        return b"original"

    original.publish(prepare, writer=writer)
    assert calls == [True] and journal(tmp_path).read() == b"original"


def test_updated_legacy_and_v2_writers_share_exclusion_and_refuse_mixing(tmp_path):
    old = journal(tmp_path, index_format="json_v1")
    new = journal(tmp_path)
    with old.publication_guard(), pytest.raises(BlockingIOError):
        new.publish(b"v2", writer=writer)
    old.index.parent.mkdir(exist_ok=True)
    old.index.write_bytes(b"original v1")
    fresh = journal(tmp_path, index_format="json_v1")
    assert fresh.format == "json_v1"
    with pytest.raises(IndexJournalError, match="migration"):
        journal(tmp_path)
    assert old.index.read_bytes() == b"original v1"


@pytest.mark.parametrize("variant", ["return", "raise", "restore"])
def test_producer_keyword_contents_authenticated_before_pending_dispatch(
    tmp_path, monkeypatch, variant
):
    calls = []

    def safe():
        return b"original"

    def produce(*, guard=safe):
        return guard()

    def foreign():
        calls.append(True)
        if variant == "restore":
            produce.__kwdefaults__["guard"] = safe
        if variant == "raise":
            raise OSError("foreign")
        return b"foreign"

    original = journal(tmp_path)
    actual = store_module.os.fdopen

    def fdopen(*args, **kwargs):
        result = actual(*args, **kwargs)
        produce.__kwdefaults__["guard"] = foreign
        return result

    with monkeypatch.context() as patch:
        patch.setattr(store_module.os, "fdopen", fdopen)
        with pytest.raises(
            IndexJournalError, match="canonical producer was substituted"
        ):
            original.publish(produce, writer=writer)
    assert calls == []
    produce.__kwdefaults__["guard"] = safe
    with pytest.raises(IndexJournalError, match="terminal"):
        original.publish(produce, writer=writer)


@pytest.mark.parametrize("mask", [0o022, 0o077])
def test_private_transaction_directory_preserves_umask(tmp_path, mask):
    previous = os.umask(mask)
    try:
        original = journal(tmp_path)
        original.publish(b"original", writer=writer)
        assert original.directory.stat().st_mode & 0o777 == 0o700
        assert next(original.directory.glob("*.txn")).stat().st_mode & 0o777 == 0o600
    finally:
        os.umask(previous)


@pytest.mark.parametrize("deferred", [False, True])
def test_runtime_typing_helpers_never_select_or_consume_index_bytes(
    tmp_path, monkeypatch, deferred
):
    from aware_workspace_fs_adapter import repository_index_journal as module

    original = journal(tmp_path)
    original.publish(b"previous", writer=writer)
    calls = []

    def foreign(*args):
        calls.append(True)
        raise AssertionError("runtime typing helper")

    monkeypatch.setattr(module, "cast", foreign, raising=False)
    monkeypatch.setattr(store_module, "cast", foreign)
    original.publish((lambda: b"fresh") if deferred else b"fresh", writer=writer)
    assert original.read() == b"fresh" and calls == []
    assert journal(tmp_path).read() == b"fresh"


def append_delta(previous, current):
    assert current.startswith(previous)
    tail = current[len(previous) :]
    return (
        b"RDX1"
        + struct.pack(">QI", len(current), 2)
        + b"\1"
        + struct.pack(">QQ", len(previous), 0)
        + b"\0"
        + struct.pack(">Q", len(tail))
        + tail
    )


def test_checkpoint_bounds_required_fragments_without_lifetime_or_history_limit(
    tmp_path,
):
    original = journal(tmp_path)
    current = b"complete original retained history:" + b"x" * 10000
    checkpoints = []
    for sequence in range(1, 81):
        current += ("retained-%04d;" % sequence).encode()
        original.publish(current, writer=writer, delta=append_delta)
        assert len(original._segments) <= 16
        assert len(tuple(original.directory.glob("*.txn"))) <= 16
        assert journal(tmp_path).read() == current
        frame = _parse(
            original._segments[-1][0].read_bytes(),
            kind=1,
            binding=b"repo:original",
        )
        assert frame.sequence == sequence
        if frame.mode == 0:
            checkpoints.append(sequence)
            assert frame.data == current
    assert checkpoints == [1, 17, 33, 49, 65]
    resumed = journal(tmp_path)
    resumed.publish(current + b"after-restart", writer=writer, delta=append_delta)
    assert journal(tmp_path).read() == current + b"after-restart"
    assert resumed._sequence == 81


@pytest.mark.parametrize("after_rename", [False, True])
def test_boundary_checkpoint_failure_retains_history_and_terminal_evidence(
    tmp_path, monkeypatch, after_rename
):
    original = journal(tmp_path)
    current = b"x" * 10000
    for _ in range(16):
        original.publish(current, writer=writer, delta=unchanged)
    assert len(original._segments) == 16
    actual = os.replace
    error = OSError("boundary original rename return")

    def fail(*args, **kwargs):
        if after_rename:
            actual(*args, **kwargs)
        raise error

    with monkeypatch.context() as patch:
        patch.setattr(os, "replace", fail)
        with pytest.raises(OSError) as caught:
            original.publish(current + b"latest", writer=writer, delta=append_delta)
    assert caught.value is error
    reopened = journal(tmp_path)
    assert reopened.read() == (current + b"latest" if after_rename else current)
    assert original.failure_evidence.publication == (
        "committed" if after_rename else "not_written"
    )
    if after_rename:
        assert reopened.failure_evidence.cleanup == "unknown"
    with pytest.raises(IndexJournalError, match="terminal"):
        original.publish(current, writer=writer)
