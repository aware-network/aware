"""Original temporary stream primitive, not staging or backend qualification."""

import hashlib
import os
import stat

import pytest
from aware_file_system import confined_mutation as native


def digest(body):
    return "sha256:" + hashlib.sha256(body).hexdigest()


class RecordedIO:
    def __init__(self, *, fail=None):
        self.calls = []
        self.fail = fail

    def open(self, *args, **kwargs):
        self.calls.append(("open", args[0], args[2]))
        return os.open(*args, **kwargs)

    def write(self, fd, content):
        self.calls.append(("write", len(content)))
        if self.fail == "write":
            os.write(fd, content[:1])
            raise KeyboardInterrupt("unknown partial write return")
        return os.write(fd, content)

    def fchmod(self, fd, mode):
        self.calls.append(("mode", mode))
        os.fchmod(fd, mode)
        if self.fail == "mode":
            raise OSError("unknown mode return")

    def fsync(self, fd):
        self.calls.append(("sync",))
        if self.fail == "sync":
            raise OSError("unknown sync return")
        os.fsync(fd)

    def close(self, fd):
        self.calls.append(("close",))
        os.close(fd)
        if self.fail == "close":
            raise OSError("unknown close return")


def run(root, chunks, *, io=None, **changes):
    parent = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    kwargs = {
        "parent_descriptor": parent,
        "name": "scratch",
        "chunks": chunks,
        "size_bytes": 3,
        "content_digest": digest(b"abc"),
        "mode": 0o444,
        "_io": io or RecordedIO(),
    }
    kwargs.update(changes)
    try:
        native._drive_confined_writer(native._write_temporary_stream_steps(**kwargs))
    finally:
        os.close(parent)


@pytest.mark.parametrize("mode", [0o444, 0o555, 0o600, 0o644, 0o700, 0o755])
def test_final_modes_and_single_original_lifecycle(tmp_path, mode):
    io = RecordedIO()
    previous = os.umask(0o077)
    try:
        run(tmp_path, iter((b"a", b"bc")), io=io, mode=mode)
    finally:
        os.umask(previous)
    target = tmp_path / "scratch"
    assert target.read_bytes() == b"abc"
    assert stat.S_IMODE(target.stat().st_mode) == mode
    assert target.stat().st_nlink == 1
    assert io.calls == [
        ("open", "scratch", 0o600),
        ("write", 1),
        ("write", 2),
        ("mode", mode),
        ("sync",),
        ("close",),
    ]


def test_empty_file(tmp_path):
    io = RecordedIO()
    run(tmp_path, iter(()), io=io, size_bytes=0, content_digest=digest(b""))
    assert (tmp_path / "scratch").read_bytes() == b""
    assert [call[0] for call in io.calls] == ["open", "mode", "sync", "close"]


@pytest.mark.parametrize(
    "changes",
    [
        {"size_bytes": True},
        {"size_bytes": -1},
        {"size_bytes": 256 * 1024 * 1024 + 1},
        {"maximum_chunk_bytes": True},
        {"maximum_chunk_bytes": 0},
        {"maximum_chunk_bytes": 65537},
        {"maximum_chunks": False},
        {"maximum_chunks": 0},
        {"maximum_chunks": 4097},
        {"maximum_chunks": 1, "maximum_chunk_bytes": 2},
        {"content_digest": "SHA256:" + "a" * 64},
        {"content_digest": "sha256:" + "A" * 64},
        {"content_digest": "sha256:" + "z" * 64},
        {"content_digest": None},
        {"size_bytes": 0},
        {"mode": True},
        {"mode": 0o777},
        {"mode": 0o4755},
        {"mode": 0o1755},
        {"name": "../scratch"},
        {"name": "dir/scratch"},
        {"name": "scratch\x00"},
        {"chunks": None},
    ],
)
def test_invalid_metadata_before_acquisition(tmp_path, changes):
    io = RecordedIO()
    with pytest.raises((ValueError, TypeError)):
        run(tmp_path, iter((b"abc",)), io=io, **changes)
    assert io.calls == []
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    ("chunks", "changes", "code", "prefix"),
    [
        ((b"ab",), {}, "length_mismatch", b"ab"),
        ((b"ab", b"cd"), {}, "length_exceeded", b"ab"),
        ((b"abd",), {}, "digest_mismatch", b"abd"),
        ((b"a", b"", b"bc"), {}, "chunk_invalid", b"a"),
        ((b"a", bytearray(b"bc")), {}, "chunk_invalid", b"a"),
        ((b"a", memoryview(b"bc")), {}, "chunk_invalid", b"a"),
        ((b"a", "bc"), {}, "chunk_invalid", b"a"),
        (
            (b"a", b"b", b"c"),
            {"maximum_chunks": 2, "maximum_chunk_bytes": 2},
            "chunk_count_exceeded",
            b"ab",
        ),
        ((b"abc",), {"maximum_chunk_bytes": 2}, "chunk_invalid", b""),
    ],
)
def test_bad_stream_leaves_prefix_without_sealing_or_cleanup(
    tmp_path, chunks, changes, code, prefix
):
    io = RecordedIO()
    with pytest.raises(ValueError, match=code):
        run(tmp_path, iter(chunks), io=io, **changes)
    assert (tmp_path / "scratch").read_bytes() == prefix
    assert [call[0] for call in io.calls].count("close") == 1
    assert not any(call[0] in {"mode", "sync"} for call in io.calls)


def test_lazy_stream_with_short_writes(tmp_path):
    io = RecordedIO()
    delivered = 0
    original_write = io.write

    def short(fd, content):
        assert delivered == 1 or any(call[0] == "write" for call in io.calls)
        return original_write(fd, content[:1])

    def chunks():
        nonlocal delivered
        for chunk in (b"ab", b"c"):
            if delivered:
                assert sum(call[0] == "write" for call in io.calls) == 2
            delivered += 1
            yield chunk

    io.write = short
    run(tmp_path, chunks(), io=io)
    assert (tmp_path / "scratch").read_bytes() == b"abc"
    assert [c for c in io.calls if c[0] == "write"] == [("write", 1)] * 3


def test_interrupted_source_is_not_replayed(tmp_path):
    io = RecordedIO()
    visits = 0

    def chunks():
        nonlocal visits
        visits += 1
        yield b"a"
        raise KeyboardInterrupt("source interrupted")

    with pytest.raises(KeyboardInterrupt, match="source interrupted"):
        run(tmp_path, chunks(), io=io)
    assert visits == 1
    assert (tmp_path / "scratch").read_bytes() == b"a"
    assert [c[0] for c in io.calls] == ["open", "write", "close"]


@pytest.mark.parametrize("failure", ["write", "mode", "sync", "close"])
def test_uncertain_physical_returns_are_not_retried(tmp_path, failure):
    io = RecordedIO(fail=failure)
    with pytest.raises((KeyboardInterrupt, OSError)):
        run(tmp_path, iter((b"abc",)), io=io)
    assert [c[0] for c in io.calls].count("open") == 1
    assert [c[0] for c in io.calls].count("write") == 1
    assert [c[0] for c in io.calls].count("close") == 1
    assert (tmp_path / "scratch").exists()


def test_primary_and_close_failures_remain_chained(tmp_path):
    io = RecordedIO(fail="close")
    with pytest.raises(OSError, match="unknown close return") as result:
        run(tmp_path, iter((b"abd",)), io=io)
    assert isinstance(result.value.__context__, ValueError)
    assert "digest_mismatch" in str(result.value.__context__)
    assert [c[0] for c in io.calls].count("close") == 1


@pytest.mark.parametrize("symlink", [True, False])
def test_existing_leaf_is_not_opened_or_overwritten(tmp_path, symlink):
    target = tmp_path / "original"
    target.write_bytes(b"keep")
    leaf = tmp_path / "scratch"
    if symlink:
        leaf.symlink_to(target)
    else:
        leaf.write_bytes(b"keep")
    io = RecordedIO()
    with pytest.raises(FileExistsError):
        run(tmp_path, iter((b"abc",)), io=io)
    assert target.read_bytes() == b"keep"
    assert leaf.read_bytes() == b"keep"
    assert [c[0] for c in io.calls] == ["open"]


def test_legacy_whole_body_trace_is_unchanged(tmp_path):
    parent = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    io = RecordedIO()
    try:
        native._write_temporary(
            parent_descriptor=parent,
            name="legacy",
            content=b"abc",
            mode=0o644,
            preserve_mode=True,
            _io=io,
        )
    finally:
        os.close(parent)
    assert io.calls == [
        ("open", "legacy", 0o644),
        ("write", 3),
        ("mode", 0o644),
        ("sync",),
        ("close",),
    ]


def test_multi_chunk_file_without_whole_body_concatenation(tmp_path):
    chunk = b"x" * 65536
    count = 128
    expected = hashlib.sha256()
    for _ in range(count):
        expected.update(chunk)
    run(
        tmp_path,
        (chunk for _ in range(count)),
        size_bytes=count * len(chunk),
        content_digest="sha256:" + expected.hexdigest(),
    )
    observed = hashlib.sha256()
    with (tmp_path / "scratch").open("rb") as source:
        while piece := source.read(65536):
            observed.update(piece)
    assert observed.digest() == expected.digest()
