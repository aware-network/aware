"""One-shot dedicated-writer canary candidate, never backend certification."""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import select
import stat
import sys
import threading
import time
from dataclasses import asdict
from pathlib import Path

from . import confined_mutation as native
from .retained_mutation import _mkdir_explicit
from .staging_plan import (
    StagingDirectory,
    StagingFile,
    StagingPlan,
    StagingPlanLimits,
    validate_staging_plan,
)

CASE = "9cd6bc0f8e9753b8b5ce318eef15b2ae"
WRITER_UID = WRITER_GID = 62041
REQUESTER_UID = 1000
SETUP = Path("/etc/aware/filesystem-staging-canary/v1") / CASE / "setup.json"
ROOT = Path("/var/lib/aware/filesystem-staging-canary/v1") / CASE / "writer"
CODE_PARENT = Path("/usr/local/lib/aware-filesystem-canary")
BODY = b"Aware FileSystem dedicated-UID canary v1\n"


def _digest(body):
    return "sha256:" + hashlib.sha256(body).hexdigest()


def _digest_valid(value):
    return (
        type(value) is str
        and len(value) == 71
        and value.startswith("sha256:")
        and all(c in "0123456789abcdef" for c in value[7:])
    )


def _proc_text(path):
    with open(path, "rb") as source:
        body = source.read(16385)
    if len(body) > 16384:
        raise ValueError("canary_proc_input_limit")
    return body.decode("ascii")


def _require_launch():
    if sys.platform != "linux":
        raise RuntimeError("canary_linux_required")
    if (os.getuid(), os.geteuid(), os.getgid(), os.getegid()) != (
        WRITER_UID,
        WRITER_UID,
        WRITER_GID,
        WRITER_GID,
    ) or not set(os.getgroups()) <= {WRITER_GID}:
        raise RuntimeError("canary_dedicated_identity_required")
    if not sys.flags.isolated or not sys.flags.dont_write_bytecode:
        raise RuntimeError("canary_isolated_runtime_required")
    status = {}
    selected = {"Uid", "Gid", "CapInh", "CapPrm", "CapEff", "CapAmb", "NoNewPrivs"}
    for line in _proc_text("/proc/self/status").splitlines():
        key, separator, value = line.partition(":")
        if separator and key in selected:
            if key in status:
                raise ValueError("canary_duplicate_proc_field")
            status[key] = value.split()
    if (
        set(status) != selected
        or status["Uid"] != [str(WRITER_UID)] * 4
        or status["Gid"] != [str(WRITER_GID)] * 4
    ):
        raise RuntimeError("canary_kernel_identity_mismatch")
    if status["NoNewPrivs"] != ["1"] or any(
        len(status[key]) != 1
        or not 1 <= len(status[key][0]) <= 16
        or any(c not in "0123456789abcdefABCDEF" for c in status[key][0])
        or int(status[key][0], 16) != 0
        for key in ("CapInh", "CapPrm", "CapEff", "CapAmb")
    ):
        raise RuntimeError("canary_privilege_policy_mismatch")
    for name in ("uid_map", "gid_map"):
        if _proc_text("/proc/self/" + name).split() != ["0", "0", "4294967295"]:
            raise RuntimeError("canary_initial_identity_map_required")
    import resource

    for kind, limit in (
        (resource.RLIMIT_CPU, 10),
        (resource.RLIMIT_AS, 256 * 1024 * 1024),
        (resource.RLIMIT_NOFILE, 64),
        (resource.RLIMIT_FSIZE, 1024 * 1024),
        (resource.RLIMIT_CORE, 0),
    ):
        if resource.getrlimit(kind) != (limit, limit):
            raise RuntimeError("canary_launch_limits_required")
    _require_pipes_and_descriptors()


def _require_pipes_and_descriptors():
    import fcntl

    for fd, access in ((0, os.O_RDONLY), (1, os.O_WRONLY), (2, os.O_WRONLY)):
        info = os.fstat(fd)
        target = os.readlink("/proc/self/fd/" + str(fd))
        if (
            not stat.S_ISFIFO(info.st_mode)
            or info.st_uid != 0
            or not target.startswith("pipe:[")
            or not target.endswith("]")
            or not target[6:-1].isascii()
            or not target[6:-1].isdigit()
            or fcntl.fcntl(fd, fcntl.F_GETFL) & os.O_ACCMODE != access
        ):
            raise RuntimeError("canary_private_controller_pipes_required")
    names = os.listdir("/proc/self/fd")
    if len(names) > 64:
        raise RuntimeError("canary_inherited_descriptor_budget")
    for name in names:
        if not name.isascii() or not name.isdigit():
            raise RuntimeError("canary_proc_descriptor_invalid")
        fd = int(name)
        if fd <= 2:
            continue
        try:
            os.fstat(fd)
        except OSError as error:
            if error.errno == errno.EBADF:
                continue  # listdir's own transient descriptor is already closed
            raise
        raise RuntimeError("canary_unexpected_inherited_descriptor")


class _OwnerIO(native._ReadLedger):
    """Original once-only descriptor ledger, private to the fixed probe."""

    def __init__(self):
        super().__init__()
        self.execution = os.getpid(), threading.get_ident()
        self.created_identity = None
        self.effects = []
        self.postimage = None
        self.postimage_cleanup = None
        self.plan_digest = None

    def require_owned(self, descriptor):
        if self.execution != (os.getpid(), threading.get_ident()) or not any(
            row.descriptor == descriptor and not row.spent for row in self.resources
        ):
            raise RuntimeError("canary_original_descriptor_required")

    def open(self, path, flags, mode=None, *, dir_fd=None):
        if self.execution != (os.getpid(), threading.get_ident()):
            raise RuntimeError("canary_original_execution_required")
        if len(self.resources) >= 32:
            raise RuntimeError("canary_descriptor_budget")
        if dir_fd is not None:
            self.require_owned(dir_fd)
        elif path != "/" or flags != os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW:
            raise RuntimeError("canary_original_root_required")
        fd = super().open(path, flags, mode=mode, dir_fd=dir_fd)
        if flags & os.O_CREAT:
            info = os.fstat(fd)
            self.created_identity = info.st_dev, info.st_ino
        return fd

    def write(self, fd, content):
        self.require_owned(fd)
        return os.write(fd, content)

    def fchmod(self, fd, mode):
        self.require_owned(fd)
        os.fchmod(fd, mode)

    def fsync(self, fd):
        self.require_owned(fd)
        os.fsync(fd)


def _protected_directory(io, path, *, leaf_uid=0):
    if (
        type(path) is not type(Path())
        or not path.is_absolute()
        or str(path) != str(Path(str(path)))
        or ".." in path.parts
        or len(path.parts) > 24
    ):
        raise ValueError("canary_canonical_path_required")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = io.open("/", flags)
    parts = path.parts[1:]
    for index in range(len(parts) + 1):
        expected_uid = leaf_uid if index == len(parts) else 0
        info = os.fstat(fd)
        expected_mode = 0o755 if expected_uid == 0 else 0o700
        if (
            not stat.S_ISDIR(info.st_mode)
            or info.st_uid != expected_uid
            or stat.S_IMODE(info.st_mode) != expected_mode
        ):
            raise RuntimeError("canary_protected_ancestor_required")
        if index < len(parts):
            child = io.open(parts[index], flags, dir_fd=fd)
            io.close(fd)
            if io.release_unknown:
                raise RuntimeError("canary_ancestor_cleanup_unknown")
            fd = child
    return fd


def _require_code(io):
    path = Path(__file__).absolute()
    if not path.is_relative_to(CODE_PARENT):
        raise RuntimeError("canary_protected_install_required")
    parent = _protected_directory(io, path.parent)
    fd = io.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    info = os.fstat(fd)
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_uid != 0
        or info.st_nlink != 1
        or stat.S_IMODE(info.st_mode) not in (0o444, 0o555)
    ):
        raise RuntimeError("canary_protected_code_required")
    io.close(fd)
    io.close(parent)
    if io.release_unknown:
        raise RuntimeError("canary_code_cleanup_unknown")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("canary_duplicate_setup_field")
        result[key] = value
    return result


def _setup_record(io, expected_digest):
    if not _digest_valid(expected_digest):
        raise ValueError("canary_setup_digest_required")
    parent = _protected_directory(io, SETUP.parent)
    current = native._read_current(
        parent_descriptor=parent, leaf=SETUP.name, maximum_bytes=8192, _read_ledger=io
    )
    if isinstance(current, str) or current[0] is None or current[1] is None:
        raise RuntimeError("canary_setup_unavailable")
    body, info = current
    if (
        info.st_uid != 0
        or info.st_nlink != 1
        or stat.S_IMODE(info.st_mode) != 0o444
        or _digest(body) != expected_digest
    ):
        raise RuntimeError("canary_setup_correspondence_failed")
    record = _validate_setup_record(body, expected_digest)
    io.close(parent)
    if io.release_unknown:
        raise RuntimeError("canary_setup_cleanup_unknown")
    return record


def _validate_setup_record(body, expected_digest):
    """Shape/correspondence only; this cannot authenticate a setup record."""
    if (
        type(body) is not bytes
        or len(body) > 8192
        or not _digest_valid(expected_digest)
        or _digest(body) != expected_digest
    ):
        raise ValueError("canary_setup_bytes_invalid")
    record = json.loads(body, object_pairs_hook=_unique_object)
    expected = {
        "schema": "aware.filesystem.dedicated-worker-canary.v1",
        "case_id": CASE,
        "writer_uid": WRITER_UID,
        "writer_gid": WRITER_GID,
        "requester_uid": REQUESTER_UID,
        "freshness": "new-root-before-any-writer-exposure",
    }
    if (
        type(record) is not dict
        or set(record) != set(expected) | {"root_identity", "closure_sha256"}
        or any(
            type(record[key]) is not type(value) or record[key] != value
            for key, value in expected.items()
        )
    ):
        raise ValueError("canary_setup_shape_mismatch")
    identity = record["root_identity"]
    if (
        type(identity) is not list
        or len(identity) != 2
        or any(type(value) is not int or not 0 < value < 2**64 for value in identity)
    ):
        raise ValueError("canary_setup_identity_invalid")
    if (
        not _digest_valid(record["closure_sha256"])
        or record["closure_sha256"] == "sha256:" + "0" * 64
    ):
        raise ValueError("canary_setup_closure_required")
    return record


def _emit(value):
    body = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if len(body) > 8192:
        raise RuntimeError("canary_output_limit")
    native._write_confined_bytes(os, 1, body)


def _boundary(name):
    _emit(
        {
            "schema": "aware.filesystem.canary-boundary.v1",
            "case_id": CASE,
            "boundary": name,
        }
    )
    if not select.select([0], [], [], 5)[0]:
        raise TimeoutError("canary_boundary_timeout")
    if os.read(0, 128) != ("continue:" + name + "\n").encode("ascii"):
        raise RuntimeError("canary_boundary_ack_invalid")


def _fixed_plan():
    return StagingPlan(
        StagingPlanLimits(2, len(BODY), len(BODY), 64, 2, 1024),
        (
            StagingDirectory("probe", 0o700),
            StagingFile("probe/payload", 0o444, len(BODY), _digest(BODY)),
        ),
    )


def _probe(io, root):
    """Fixed private primitive; unit use does not qualify dedicated-UID setup."""
    io.require_owned(root)
    plan = _fixed_plan()
    io.plan_digest = validate_staging_plan(plan).plan_digest
    directory, member = plan.members
    leaf = member.path.rpartition("/")[2]
    io.stage = "probe_preflight"
    try:
        os.stat(directory.path, dir_fd=root, follow_symlinks=False)
    except FileNotFoundError as error:
        if error.errno != errno.ENOENT:
            raise
    else:
        raise FileExistsError("canary_case_already_spent")
    io.stage = "probe_mkdir"
    effect = {"path": directory.path, "kind": "directory_create", "state": "unknown"}
    io.effects.append(effect)
    _mkdir_explicit(directory.path, mode=directory.mode, dir_fd=root)
    effect["state"] = "applied"
    _boundary("mkdir_return")
    _boundary("first_open")
    io.stage = "probe_acquire"
    child = io.open(
        directory.path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=root
    )
    created = os.fstat(child)
    if (
        created.st_uid != os.geteuid()
        or stat.S_IMODE(created.st_mode) != directory.mode
    ):
        raise RuntimeError("canary_probe_directory_mismatch")
    io.stage = "probe_payload"
    effect = {"path": member.path, "kind": "file_create", "state": "unknown"}
    io.effects.append(effect)
    native._drive_confined_writer(
        native._write_temporary_stream_steps(
            parent_descriptor=child,
            name=leaf,
            chunks=iter((BODY,)),
            size_bytes=member.size_bytes,
            content_digest=member.content_digest,
            mode=member.mode,
            _io=io,
        )
    )
    if io.release_unknown or io.created_identity is None:
        raise RuntimeError("canary_payload_cleanup_unknown")
    effect["state"] = "applied"
    io.stage = "probe_postimage"
    try:
        result = native._verify_confined_file_postimage(
            parent_descriptor=child,
            leaf=leaf,
            expected_identity=io.created_identity,
            size_bytes=member.size_bytes,
            content_digest=member.content_digest,
            mode=member.mode,
        )
    except native._FilePostimageError as error:
        io.postimage_cleanup = asdict(error.cleanup)
        io.postimage = (
            asdict(error.observation) if error.observation is not None else None
        )
        raise
    io.postimage = asdict(result.observation)
    io.postimage_cleanup = asdict(result.cleanup)
    io.stage = "probe_directory_sync"
    io.fsync(child)
    io.fsync(root)
    named = os.stat(directory.path, dir_fd=root, follow_symlinks=False)
    if not stat.S_ISDIR(named.st_mode) or (
        named.st_dev,
        named.st_ino,
        named.st_uid,
        stat.S_IMODE(named.st_mode),
    ) != (created.st_dev, created.st_ino, created.st_uid, directory.mode):
        raise RuntimeError("canary_probe_correspondence_failed")
    io.stage = "probe_observed"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--setup-sha256", required=True)
    args = parser.parse_args(argv)
    io = _OwnerIO()
    primary = None
    started = time.monotonic_ns()
    try:
        _require_launch()
        _require_code(io)
        record = _setup_record(io, args.setup_sha256)
        root = _protected_directory(io, ROOT, leaf_uid=WRITER_UID)
        info = os.fstat(root)
        if [info.st_dev, info.st_ino] != record["root_identity"]:
            raise RuntimeError("canary_root_identity_mismatch")
        _probe(io, root)
        io.stage = "root_correspondence"
        named = os.stat(ROOT, follow_symlinks=False)
        if (
            ROOT.resolve(strict=True) != ROOT
            or not stat.S_ISDIR(named.st_mode)
            or (named.st_dev, named.st_ino, named.st_uid, stat.S_IMODE(named.st_mode))
            != (info.st_dev, info.st_ino, WRITER_UID, 0o700)
        ):
            raise RuntimeError("canary_root_correspondence_failed")
        io.stage = "probe_observed"
    except BaseException as error:  # noqa: BLE001 - canary records interruptions and never retries effects
        primary = error
    finally:
        cleanup = native._settle_confined_read_ledger(io)
    observed = (
        primary is None and cleanup.outcome == "closed" and io.stage == "probe_observed"
    )
    _emit(
        {
            "schema": "aware.filesystem.worker-canary-result.v1",
            "case_id": CASE,
            "status": "observed" if observed else "failed",
            "stage": io.stage,
            "qualified_backend": False,
            "namespace_sealed": False,
            "plan_digest": io.plan_digest,
            "effects": io.effects,
            "cleanup": asdict(cleanup),
            "postimage": io.postimage,
            "postimage_cleanup": io.postimage_cleanup,
            "failure_kind": type(primary).__name__ if primary is not None else None,
            "residue_policy": "retain_no_retry",
            "elapsed_ns": time.monotonic_ns() - started,
        }
    )
    return 0 if observed else 1


if __name__ == "__main__":
    raise SystemExit(main())
