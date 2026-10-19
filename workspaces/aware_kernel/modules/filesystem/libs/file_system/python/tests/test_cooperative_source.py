"""Real local custody and OS locks; not Subject/Actor/namespace admission."""

import asyncio
import copy
import os
import pickle
import subprocess
import sys
import threading
from contextlib import contextmanager

import pytest
from aware_file_system import cooperative_source as source


@pytest.fixture
def root(tmp_path):
    (tmp_path / "record.txt").write_bytes(b"original")
    source.initialize_source_authority(tmp_path)
    return tmp_path


def capture(root):
    return source.capture_source_read(root, ("record.txt",))


def test_read_does_not_initialize_or_allocate(tmp_path):
    (tmp_path / "record.txt").write_bytes(b"original")
    with pytest.raises(source.SourceAuthorityError, match="uninitialized"):
        capture(tmp_path)
    assert {path.name for path in tmp_path.iterdir()} == {"record.txt"}


def test_unsupported_lock_backend_refuses_without_initialization(tmp_path, monkeypatch):
    (tmp_path / "record.txt").write_bytes(b"original")
    monkeypatch.setattr(source, "fcntl", None)
    for operation in (
        lambda: capture(tmp_path),
        lambda: source.initialize_source_authority(tmp_path),
    ):
        with pytest.raises(source.SourceAuthorityError, match="platform_unsupported"):
            operation()
    assert {path.name for path in tmp_path.iterdir()} == {"record.txt"}


def test_original_capture_and_release(root):
    read = capture(root)
    assert read.profile == source.PROFILE
    assert read.sources[0].path == "record.txt"
    assert read.sources[0].content == b"original"
    read.require_current()
    read.release()
    read.release()
    with pytest.raises(source.SourceAuthorityError):
        read.require_current()


def test_lifetime_retains_no_lock_between_publications(root):
    read = capture(root)
    with source.cooperative_source_write(root):
        (root / "record.txt").write_bytes(b"advanced")
    with pytest.raises(source.SourceAuthorityError):
        read.require_current()
    read.release()


def test_change_and_restore_spends_epoch_even_with_same_content(root):
    read = capture(root)
    for body in (b"changed", b"original"):
        with source.cooperative_source_write(root):
            (root / "record.txt").write_bytes(body)
    with pytest.raises(source.SourceAuthorityError):
        read.require_current()
    read.release()
    fresh = capture(root)
    fresh.require_current()
    fresh.release()


def test_noeffect_writer_attempt_conservatively_advances_epoch(root):
    read = capture(root)
    with source.cooperative_source_write(root):
        pass
    with pytest.raises(source.SourceAuthorityError):
        read.require_current()
    read.release()


def test_reservation_blocks_actual_writer_and_retires_token(root):
    read = capture(root)
    with read.reserve_publication() as token:
        token.require_current()
        with (
            pytest.raises(source.SourceAuthorityError, match="busy"),
            source.cooperative_source_write(root),
        ):
            pytest.fail("writer entered")
        token.require_current()
    with pytest.raises(source.SourceAuthorityError):
        token.require_current()
    with source.cooperative_source_write(root):
        pass
    read.release()


def test_actual_cross_process_writer_is_excluded(root):
    read = capture(root)
    script = """
import sys
from pathlib import Path
from aware_file_system.cooperative_source import cooperative_source_write, SourceAuthorityError
try:
    with cooperative_source_write(Path(sys.argv[1])):
        print('entered')
except SourceAuthorityError as error:
    print(error.code)
"""
    with read.reserve_publication() as token:
        result = subprocess.run(
            [sys.executable, "-B", "-c", script, str(root)],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout == "source_authority_busy\n"
        token.require_current()
    read.release()


@pytest.mark.asyncio
async def test_publication_reservation_cannot_survive_an_await(root):
    read = capture(root)
    with read.reserve_publication() as token:
        token.require_current()
        await asyncio.sleep(0)
        with pytest.raises(source.SourceAuthorityError):
            token.require_current()
    with pytest.raises(source.SourceAuthorityError):
        read.require_current()
    # Yield revoked its lock instead of blocking unrelated work forever.
    with source.cooperative_source_write(root):
        pass
    read.release()


def test_copy_pickle_subclass_and_forged_handles_have_no_custody(root):
    for cls in (source.RetainedSourceRead, source.SourcePublicationReservation):
        with pytest.raises(TypeError):
            cls()
    read = capture(root)
    for copier in (copy.copy, copy.deepcopy, pickle.dumps):
        with pytest.raises(TypeError):
            copier(read)
    with read.reserve_publication() as token:
        for copier in (copy.copy, copy.deepcopy, pickle.dumps):
            with pytest.raises(TypeError):
                copier(token)
    forged = object.__new__(source.RetainedSourceRead)
    with pytest.raises(source.SourceAuthorityError):
        forged.require_current()
    read.release()


def test_snapshot_mutation_does_not_rewrite_retained_source(root):
    read = capture(root)
    snapshot = read.sources[0]
    object.__setattr__(snapshot, "content", b"foreign")
    assert read.sources[0].content == b"original"
    read.require_current()
    read.release()


def test_releasing_one_reader_does_not_retire_borrowed_other_reader(root):
    first, second = capture(root), capture(root)
    first.release()
    second.require_current()
    second.release()


@pytest.mark.parametrize(
    "path",
    [
        "",
        "/absolute",
        "../outside",
        "a/../b",
        "a//b",
        "a/./b",
        "./record.txt",
        "a\\b",
        source.CONTROL_NAME,
        "\ud800",
    ],
)
def test_noncanonical_source_paths_refuse(root, path):
    with pytest.raises(source.SourceAuthorityError):
        source.capture_source_read(root, (path,))


def test_duplicate_inventory_and_size_bounds_refuse(root):
    with pytest.raises(source.SourceAuthorityError):
        source.capture_source_read(root, ("record.txt", "record.txt"))
    (root / "record.txt").write_bytes(b"x" * (source.MAX_SOURCE_BYTES + 1))
    with pytest.raises(source.SourceAuthorityError):
        capture(root)


def test_leaf_parent_symlinks_and_hardlinks_refuse(root, tmp_path):
    target = root / "elsewhere"
    target.mkdir()
    (target / "source").write_bytes(b"value")
    (root / "leaf").symlink_to(target / "source")
    (root / "parent").symlink_to(target, target_is_directory=True)
    os.link(root / "record.txt", root / "alias")
    for path in ("leaf", "parent/source", "record.txt"):
        with pytest.raises(OSError):
            source.capture_source_read(root, (path,))


def test_raw_os_change_is_detected_but_not_claimed_excluded(root):
    read = capture(root)
    with read.reserve_publication() as token:
        (root / "record.txt").write_bytes(b"uncooperative")
        with pytest.raises(source.SourceAuthorityError):
            token.require_current()
    read.release()


@pytest.mark.parametrize("replacement", ["root", "control"])
def test_root_or_control_replacement_permanently_retires(root, replacement):
    read = capture(root)
    if replacement == "root":
        old = root.with_name(root.name + "-old")
        root.rename(old)
        root.mkdir()
    else:
        control = root / source.CONTROL_NAME
        body = control.read_bytes()
        control.rename(root / "old-control")
        control.write_bytes(body)
        control.chmod(0o600)
    with pytest.raises(source.SourceAuthorityError):
        read.require_current()
    with pytest.raises(source.SourceAuthorityError):
        read.require_current()
    read.release()


def test_corrupt_control_is_not_repaired(root):
    control = root / source.CONTROL_NAME
    control.write_bytes(b"corrupt")
    with pytest.raises(source.SourceAuthorityError):
        source.initialize_source_authority(root)
    assert control.read_bytes() == b"corrupt"


def test_cleanup_uncertainty_is_not_cleared_by_release_retry(root, monkeypatch):
    read = capture(root)
    real_close = source._close
    failed = False

    def uncertain(fd):
        nonlocal failed
        result = real_close(fd)
        if fd >= 0 and not failed:
            failed = True
            return False
        return result

    monkeypatch.setattr(source, "_close", uncertain)
    for _ in range(2):
        with pytest.raises(source.SourceAuthorityError, match="cleanup_unresolved"):
            read.release()


def test_capture_teardown_failure_closes_unissued_retained_descriptors(
    root, monkeypatch
):
    original_scope = source._locked_root
    original_dup = os.dup
    retained = []

    def record_dup(fd):
        result = original_dup(fd)
        retained.append(result)
        return result

    @contextmanager
    def failed_teardown(*args, **kwargs):
        with original_scope(*args, **kwargs) as descriptors:
            yield descriptors
        raise source.SourceAuthorityError("source_cleanup_unresolved")

    monkeypatch.setattr(source, "_locked_root", failed_teardown)
    monkeypatch.setattr(source.os, "dup", record_dup)
    with pytest.raises(source.SourceAuthorityError, match="cleanup_unresolved"):
        capture(root)
    assert len(retained) == 2
    for fd in retained:
        with pytest.raises(OSError):
            os.fstat(fd)


def test_success_and_failed_capture_leave_no_descriptors(root):
    before = set(os.listdir("/proc/self/fd"))
    read = capture(root)
    read.require_current()
    read.release()
    assert set(os.listdir("/proc/self/fd")) == before
    with pytest.raises(OSError):
        source.capture_source_read(root, ("missing",))
    assert set(os.listdir("/proc/self/fd")) == before


def test_reservation_cannot_be_used_by_another_thread(root):
    read = capture(root)
    refused = []
    with read.reserve_publication() as token:

        def other_thread():
            for operation in (token.require_current, read.release):
                try:
                    operation()
                except source.SourceAuthorityError as error:
                    refused.append(error.code)

        worker = threading.Thread(target=other_thread)
        worker.start()
        worker.join(timeout=5)
        assert not worker.is_alive()
        assert refused == ["original_source_reservation_required"] * 2
        token.require_current()
    read.release()


def test_fork_does_not_inherit_read_authority_or_unlock_parent(root):
    read = capture(root)
    context = read.reserve_publication()
    with context as token:
        pid = os.fork()
        if pid == 0:
            try:
                for operation in (
                    token.require_current,
                    read.require_current,
                    read.release,
                    lambda: context.__exit__(None, None, None),
                ):
                    try:
                        operation()
                    except source.SourceAuthorityError:
                        continue
                    os._exit(2)
                os._exit(0)
            except BaseException:  # noqa: BLE001 - child must never continue the parent test runner
                os._exit(3)
        _, status = os.waitpid(pid, 0)
        assert os.waitstatus_to_exitcode(status) == 0
        token.require_current()
        with (
            pytest.raises(source.SourceAuthorityError, match="busy"),
            source.cooperative_source_write(root),
        ):
            pytest.fail("child unlocked parent reservation")
    read.release()


@pytest.mark.parametrize("copier", [copy.copy, copy.deepcopy, pickle.dumps])
def test_publication_context_itself_cannot_be_copied_or_serialized(root, copier):
    read = capture(root)
    context = read.reserve_publication()
    with context as token:
        with pytest.raises(TypeError):
            copier(context)
        token.require_current()
    read.release()


def test_context_reentry_or_old_exit_cannot_release_a_successor(root):
    read = capture(root)
    context = read.reserve_publication()
    with context as token:
        with pytest.raises(source.SourceAuthorityError, match="context_consumed"):
            context.__enter__()
        token.require_current()
    with read.reserve_publication() as successor:
        with pytest.raises(source.SourceAuthorityError):
            context.__exit__(None, None, None)
        successor.require_current()
        with (
            pytest.raises(source.SourceAuthorityError, match="busy"),
            source.cooperative_source_write(root),
        ):
            pytest.fail("old exit released a new reservation")
    read.release()


def test_exceptional_owner_exit_does_not_suppress_and_releases_writer(root):
    read = capture(root)
    with (
        pytest.raises(ValueError, match="publication failed"),
        read.reserve_publication() as token,
    ):
        token.require_current()
        raise ValueError("publication failed")
    with source.cooperative_source_write(root):
        pass
    read.release()


def test_unlock_failure_closes_owned_fd_and_permanently_reports_uncertainty(
    root, monkeypatch
):
    read = capture(root)
    context = read.reserve_publication()
    token = context.__enter__()
    fd = source._RESERVATIONS[token].fd
    original_flock = source.fcntl.flock

    def failed_unlock(descriptor, operation):
        if descriptor == fd and operation == source.fcntl.LOCK_UN:
            raise OSError("injected unlock failure")
        return original_flock(descriptor, operation)

    monkeypatch.setattr(source.fcntl, "flock", failed_unlock)
    with pytest.raises(source.SourceAuthorityError, match="cleanup_unresolved"):
        context.__exit__(None, None, None)
    with pytest.raises(OSError):
        os.fstat(fd)
    with pytest.raises(source.SourceAuthorityError):
        read.require_current()
    with pytest.raises(source.SourceAuthorityError, match="cleanup_unresolved"):
        read.release()


def test_owner_unlock_does_not_release_another_reads_reservation(root):
    first, second = capture(root), capture(root)
    first_context = first.reserve_publication()
    first_context.__enter__()
    with second.reserve_publication() as token:
        first_context.__exit__(None, None, None)
        first.release()
        token.require_current()
        with (
            pytest.raises(source.SourceAuthorityError, match="busy"),
            source.cooperative_source_write(root),
        ):
            pytest.fail("one read unlocked another read's reservation")
    with source.cooperative_source_write(root):
        pass
    second.release()


def test_foreign_thread_cannot_consume_publication_context_exit(root):
    read = capture(root)
    context = read.reserve_publication()
    token = context.__enter__()
    refused = []
    try:

        def foreign_exit():
            try:
                context.__exit__(None, None, None)
            except source.SourceAuthorityError as error:
                refused.append(error.code)

        worker = threading.Thread(target=foreign_exit)
        worker.start()
        worker.join(timeout=5)
        assert not worker.is_alive()
        assert refused == ["original_source_reservation_required"]
        token.require_current()
        with (
            pytest.raises(source.SourceAuthorityError, match="busy"),
            source.cooperative_source_write(root),
        ):
            pytest.fail("foreign exit released the owner lock")
    finally:
        context.__exit__(None, None, None)
    with source.cooperative_source_write(root):
        pass
    read.release()


@pytest.mark.asyncio
async def test_foreign_task_cannot_consume_publication_context_exit(root):
    read = capture(root)
    context = read.reserve_publication()
    token = context.__enter__()
    owner = asyncio.current_task()
    try:

        async def foreign_exit():
            assert asyncio.current_task() is not owner
            try:
                context.__exit__(None, None, None)
            except source.SourceAuthorityError as error:
                return error.code
            return "incorrectly_exited"

        # Execute a genuine different Task without yielding the owner. Yielding
        # would intentionally retire this no-await reservation first.
        child = asyncio.Task(
            foreign_exit(), loop=asyncio.get_running_loop(), eager_start=True
        )
        assert child.done()
        assert child.result() == "original_source_reservation_required"
        token.require_current()
        with (
            pytest.raises(source.SourceAuthorityError, match="busy"),
            source.cooperative_source_write(root),
        ):
            pytest.fail("foreign task released the owner lock")
    finally:
        context.__exit__(None, None, None)
    with source.cooperative_source_write(root):
        pass
    read.release()


def test_parent_exit_unlocks_even_while_forked_child_retains_descriptors(root):
    read = capture(root)
    gate_read, gate_write = os.pipe()
    ready_read, ready_write = os.pipe()
    pid = -1
    try:
        with read.reserve_publication() as token:
            pid = os.fork()
            if pid == 0:
                try:
                    os.close(gate_write)
                    os.close(ready_read)
                    os.write(ready_write, b"ready")
                    os.close(ready_write)
                    os.read(gate_read, 1)
                    os._exit(0)
                except BaseException:  # noqa: BLE001 - child must never enter the parent runner
                    os._exit(3)
            os.close(gate_read)
            gate_read = -1
            os.close(ready_write)
            ready_write = -1
            assert os.read(ready_read, 5) == b"ready"
            token.require_current()
        assert os.waitid(os.P_PID, pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is None
        with source.cooperative_source_write(root):
            pass
        # The child is still blocked, retaining the inherited open-file
        # description. Successful admission cannot depend on child exit.
        assert os.waitid(os.P_PID, pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is None
    finally:
        os.write(gate_write, b"x")
        for fd in (gate_read, gate_write, ready_read, ready_write):
            if fd >= 0:
                os.close(fd)
        if pid > 0:
            _, status = os.waitpid(pid, 0)
            assert os.waitstatus_to_exitcode(status) == 0
        read.release()
