"""Candidate source controls, never dedicated-UID/backend qualification."""

import json
import os
import resource
import stat
import subprocess
import sys
import threading
from types import SimpleNamespace

import pytest
from aware_file_system import confined_mutation as native
from aware_file_system import staging_worker_canary as canary

_CLOSE = os.close
FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW


@pytest.fixture
def probe(tmp_path, monkeypatch):
    io = canary._OwnerIO()
    root = io.open("/", FLAGS)
    for component in tmp_path.parts[1:]:
        child = io.open(component, FLAGS, dir_fd=root)
        io.close(root)
        root = child
    boundaries = []
    monkeypatch.setattr(canary, "_boundary", boundaries.append)
    try:
        yield io, root, tmp_path, boundaries
    finally:
        native._settle_confined_read_ledger(io)


def record(**changes):
    return {
        "schema": "aware.filesystem.dedicated-worker-canary.v1",
        "case_id": canary.CASE,
        "writer_uid": canary.WRITER_UID,
        "writer_gid": canary.WRITER_GID,
        "requester_uid": canary.REQUESTER_UID,
        "root_identity": [1, 2],
        "closure_sha256": "sha256:" + "a" * 64,
        "freshness": "new-root-before-any-writer-exposure",
    } | changes


def validate(value):
    body = json.dumps(value).encode()
    return canary._validate_setup_record(body, canary._digest(body))


def test_fixed_private_probe_joins_original_primitives(probe):
    io, root, path, boundaries = probe
    canary._probe(io, root)
    assert boundaries == ["mkdir_return", "first_open"]
    assert (
        io.plan_digest == canary.validate_staging_plan(canary._fixed_plan()).plan_digest
    )
    payload = path / "probe/payload"
    assert payload.read_bytes() == canary.BODY
    assert stat.S_IMODE(payload.stat().st_mode) == 0o444
    assert io.created_identity == (payload.stat().st_dev, payload.stat().st_ino)
    assert io.postimage["content_digest"] == canary._digest(canary.BODY)
    assert io.postimage["observation_grade"] == "observed_state"
    assert io.postimage_cleanup["outcome"] == "closed"
    assert [e["state"] for e in io.effects] == ["applied", "applied"]
    assert native._settle_confined_read_ledger(io).outcome == "closed"
    assert payload.exists()  # no automatic deletion on completion


def test_spent_case_refuses_without_adopting_or_mutating(probe):
    io, root, path, boundaries = probe
    (path / "probe").mkdir()
    (path / "probe/foreign").write_bytes(b"keep")
    with pytest.raises(FileExistsError, match="already_spent"):
        canary._probe(io, root)
    assert io.effects == []
    assert boundaries == []
    assert (path / "probe/foreign").read_bytes() == b"keep"
    assert not (path / "probe/payload").exists()


def test_ambiguous_preflight_is_not_absence(probe, monkeypatch):
    io, root, path, boundaries = probe
    original = os.stat

    def lost(name, *args, **kwargs):
        if name == "probe":
            raise FileNotFoundError("missing stat return, no definite errno")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(os, "stat", lost)
    with pytest.raises(FileNotFoundError):
        canary._probe(io, root)
    assert io.effects == [] and boundaries == []
    assert not (path / "probe").exists()


def test_lost_mkdir_return_preserves_residue_without_acquisition(probe, monkeypatch):
    io, root, path, boundaries = probe
    original = canary._mkdir_explicit

    def lost(*args, **kwargs):
        original(*args, **kwargs)
        raise KeyboardInterrupt("lost mkdir return")

    monkeypatch.setattr(canary, "_mkdir_explicit", lost)
    with pytest.raises(KeyboardInterrupt):
        canary._probe(io, root)
    assert io.effects == [
        {"path": "probe", "kind": "directory_create", "state": "unknown"}
    ]
    assert boundaries == []
    assert (path / "probe").is_dir()
    assert not (path / "probe/payload").exists()


@pytest.mark.parametrize("boundary", ["mkdir_return", "first_open"])
def test_boundary_failure_does_not_continue_or_clean_up(probe, monkeypatch, boundary):
    io, root, path, _ = probe
    visited = []

    def fail(name):
        visited.append(name)
        if name == boundary:
            raise TimeoutError("controller unavailable")

    monkeypatch.setattr(canary, "_boundary", fail)
    with pytest.raises(TimeoutError):
        canary._probe(io, root)
    assert visited[-1] == boundary
    assert io.effects[0]["state"] == "applied"
    assert (path / "probe").is_dir()
    assert not (path / "probe/payload").exists()


def test_partial_payload_is_retained_without_retry(probe, monkeypatch):
    io, root, path, _ = probe
    calls = []

    def interrupted(fd, content):
        calls.append(fd)
        os.write(fd, content[:1])
        raise KeyboardInterrupt("unknown write return")

    monkeypatch.setattr(io, "write", interrupted)
    with pytest.raises(KeyboardInterrupt):
        canary._probe(io, root)
    assert len(calls) == 1
    assert io.effects[-1]["state"] == "unknown"
    assert (path / "probe/payload").read_bytes() == canary.BODY[:1]
    assert io.postimage is None


def test_unknown_writer_close_prevents_success_and_never_recloses(probe, monkeypatch):
    io, root, path, _ = probe
    calls = []

    def lost(fd):
        calls.append(fd)
        _CLOSE(fd)
        raise KeyboardInterrupt("lost close return")

    monkeypatch.setattr(os, "close", lost)
    with pytest.raises(RuntimeError, match="payload_cleanup_unknown"):
        canary._probe(io, root)
    cleanup = native._settle_confined_read_ledger(io)
    assert cleanup.outcome == "unknown"
    assert len(calls) == len(set(calls)) == 3  # payload, child, root: once each
    assert (path / "probe/payload").exists()


def test_stored_postimage_failure_is_not_input_hash_success(probe, monkeypatch):
    io, root, path, _ = probe
    original = io.fchmod

    def tamper(fd, mode):
        original(fd, mode)
        os.pwrite(fd, b"X", 0)

    monkeypatch.setattr(io, "fchmod", tamper)
    with pytest.raises(native._FilePostimageError):
        canary._probe(io, root)
    assert io.stage == "probe_postimage"
    assert io.postimage is None
    assert io.postimage_cleanup["outcome"] == "closed"
    assert (path / "probe/payload").read_bytes().startswith(b"X")


def test_foreign_thread_cannot_borrow_original_descriptor(probe):
    io, root, _, _ = probe
    failures = []

    def foreign():
        try:
            io.fsync(root)
        except RuntimeError as error:
            failures.append(error)

    thread = threading.Thread(target=foreign)
    thread.start()
    thread.join(timeout=2)
    assert not thread.is_alive() and len(failures) == 1
    io.fsync(root)  # original execution's custody survives


def test_descriptor_borrow_and_acquisition_limits(probe):
    io, root, _, _ = probe
    with pytest.raises(RuntimeError, match="original_descriptor"):
        io.write(-1, b"no")
    with pytest.raises(RuntimeError, match="original_root"):
        io.open("/tmp", FLAGS)
    io.resources.extend(native._ReadResource() for _ in range(32 - len(io.resources)))
    with pytest.raises(RuntimeError, match="descriptor_budget"):
        io.open("/", FLAGS)
    io.fsync(root)


def test_setup_shape_positive_is_not_authentication():
    expected = record()
    assert validate(expected) == expected


@pytest.mark.parametrize(
    "changes",
    [
        {"schema": "other"},
        {"case_id": "../other"},
        {"writer_uid": True},
        {"writer_uid": 1000},
        {"writer_gid": 0},
        {"requester_uid": 62041},
        {"freshness": "existing"},
        {"extra": "field"},
        {"root_identity": [0, 2]},
        {"root_identity": [1, True]},
        {"root_identity": [1]},
        {"root_identity": [1, 2**64]},
        {"closure_sha256": "sha256:" + "0" * 64},
        {"closure_sha256": "sha256:" + "A" * 64},
    ],
)
def test_setup_shape_refuses_ambiguous_or_wrong_inputs(changes):
    with pytest.raises(ValueError):
        validate(record(**changes))


@pytest.mark.parametrize(
    "body", [b"{}", b"[]", b'{"case_id":1,"case_id":2}', b"x" * 8193]
)
def test_setup_bounds_and_duplicate_keys(body):
    with pytest.raises(ValueError):
        canary._validate_setup_record(body, canary._digest(body))


def test_setup_snapshot_digest_mismatch():
    body = json.dumps(record()).encode()
    with pytest.raises(ValueError, match="bytes_invalid"):
        canary._validate_setup_record(body, "sha256:" + "a" * 64)


def test_current_normal_identity_refuses_before_any_setup(monkeypatch):
    monkeypatch.setattr(os, "getuid", lambda: canary.REQUESTER_UID)
    with pytest.raises(RuntimeError, match="dedicated_identity"):
        canary._require_launch()


@pytest.fixture
def simulated_launch(monkeypatch):
    monkeypatch.setattr(canary, "_require_pipes_and_descriptors", lambda: None)
    monkeypatch.setattr(
        canary,
        "sys",
        SimpleNamespace(
            platform="linux",
            flags=SimpleNamespace(isolated=True, dont_write_bytecode=True),
        ),
    )
    monkeypatch.setattr(os, "getuid", lambda: canary.WRITER_UID)
    monkeypatch.setattr(os, "geteuid", lambda: canary.WRITER_UID)
    monkeypatch.setattr(os, "getgid", lambda: canary.WRITER_GID)
    monkeypatch.setattr(os, "getegid", lambda: canary.WRITER_GID)
    monkeypatch.setattr(os, "getgroups", lambda: [canary.WRITER_GID])
    status = {
        "Uid": "62041 62041 62041 62041",
        "Gid": "62041 62041 62041 62041",
        "CapInh": "0000000000000000",
        "CapPrm": "0000000000000000",
        "CapEff": "0000000000000000",
        "CapAmb": "0000000000000000",
        "NoNewPrivs": "1",
    }
    texts = {
        "/proc/self/" + name: "0 0 4294967295\n" for name in ("uid_map", "gid_map")
    }
    monkeypatch.setattr(
        canary,
        "_proc_text",
        lambda path: (
            "\n".join(k + ": " + v for k, v in status.items())
            if path.endswith("status")
            else texts[path]
        ),
    )
    limits = {
        resource.RLIMIT_CPU: (10, 10),
        resource.RLIMIT_AS: (256 * 1024 * 1024,) * 2,
        resource.RLIMIT_NOFILE: (64, 64),
        resource.RLIMIT_FSIZE: (1024 * 1024,) * 2,
        resource.RLIMIT_CORE: (0, 0),
    }
    monkeypatch.setattr(resource, "getrlimit", limits.__getitem__)
    return status, texts, limits


def test_simulated_launch_gates_only(simulated_launch):
    canary._require_launch()  # unit simulation; no account/privilege/limit changes


@pytest.mark.parametrize(
    "field,value",
    [
        ("NoNewPrivs", "0"),
        ("CapEff", "1"),
        ("CapPrm", "1"),
        ("CapInh", "1"),
        ("CapAmb", "1"),
        ("Uid", "62041 0 62041 62041"),
        ("Gid", "62041 62041 62041 0"),
    ],
)
def test_simulated_privilege_and_saved_identity_refusals(
    simulated_launch, field, value
):
    status, _, _ = simulated_launch
    status[field] = value
    with pytest.raises(RuntimeError):
        canary._require_launch()


@pytest.mark.parametrize("target", ["uid_map", "gid_map"])
def test_simulated_user_namespace_maps_are_not_initial(simulated_launch, target):
    _, texts, _ = simulated_launch
    texts["/proc/self/" + target] = "0 1000 1\n"
    with pytest.raises(RuntimeError, match="identity_map"):
        canary._require_launch()


def test_simulated_unbounded_launch_refuses(simulated_launch):
    _, _, limits = simulated_launch
    limits[resource.RLIMIT_AS] = (-1, -1)
    with pytest.raises(RuntimeError, match="launch_limits"):
        canary._require_launch()


def test_source_checkout_is_not_protected_install(probe):
    io, _, _, _ = probe
    with pytest.raises(RuntimeError, match="protected_install"):
        canary._require_code(io)


def test_user_owned_ancestor_is_not_protected(probe):
    io, _, path, _ = probe
    with pytest.raises(RuntimeError, match="protected_ancestor"):
        canary._protected_directory(io, path)


@pytest.mark.parametrize("boundary", ["mkdir_return", "first_open"])
def test_exact_boundary_ack(monkeypatch, boundary):
    emitted = []
    monkeypatch.setattr(canary, "_emit", emitted.append)
    monkeypatch.setattr(canary.select, "select", lambda *args: ([0], [], []))
    monkeypatch.setattr(
        os, "read", lambda *args: ("continue:" + boundary + "\n").encode()
    )
    canary._boundary(boundary)
    assert emitted[0]["boundary"] == boundary


@pytest.mark.parametrize(
    "reply",
    [
        b"continue\n",
        b"continue:other\n",
        b"",
        b"continue:mkdir_return\ncontinue:first_open\n",
    ],
)
def test_boundary_wrong_ack_refuses(monkeypatch, reply):
    monkeypatch.setattr(canary, "_emit", lambda value: None)
    monkeypatch.setattr(canary.select, "select", lambda *args: ([0], [], []))
    monkeypatch.setattr(os, "read", lambda *args: reply)
    with pytest.raises(RuntimeError, match="ack_invalid"):
        canary._boundary("mkdir_return")


def test_boundary_timeout_does_not_read(monkeypatch):
    monkeypatch.setattr(canary, "_emit", lambda value: None)
    monkeypatch.setattr(canary.select, "select", lambda *args: ([], [], []))
    monkeypatch.setattr(os, "read", lambda *args: pytest.fail("read after timeout"))
    with pytest.raises(TimeoutError):
        canary._boundary("mkdir_return")


def test_main_normal_identity_reports_failure_without_setup(monkeypatch):
    emitted = []
    monkeypatch.setattr(canary, "_emit", emitted.append)
    monkeypatch.setattr(
        canary,
        "_require_launch",
        lambda: (_ for _ in ()).throw(RuntimeError("not admitted")),
    )
    monkeypatch.setattr(
        canary, "_require_code", lambda *args: pytest.fail("unadmitted startup")
    )
    assert canary.main(["--setup-sha256", "sha256:" + "a" * 64]) == 1
    assert emitted[0]["qualified_backend"] is False
    assert emitted[0]["namespace_sealed"] is False
    assert emitted[0]["effects"] == []
    assert emitted[0]["cleanup"]["outcome"] == "not_acquired"


def test_simulated_main_success_never_certifies_backend(probe, monkeypatch):
    io, root, path, _ = probe
    emitted = []
    info = os.fstat(root)
    path.chmod(0o700)
    monkeypatch.setattr(canary, "ROOT", path)
    monkeypatch.setattr(canary, "WRITER_UID", os.geteuid())
    monkeypatch.setattr(canary, "_OwnerIO", lambda: io)
    monkeypatch.setattr(canary, "_require_launch", lambda: None)
    monkeypatch.setattr(canary, "_require_code", lambda *args: None)
    monkeypatch.setattr(
        canary,
        "_setup_record",
        lambda *args: {"root_identity": [info.st_dev, info.st_ino]},
    )
    monkeypatch.setattr(canary, "_protected_directory", lambda *args, **kwargs: root)
    monkeypatch.setattr(canary, "_emit", emitted.append)
    assert canary.main(["--setup-sha256", "sha256:" + "a" * 64]) == 0
    assert emitted[0]["status"] == "observed"
    assert emitted[0]["qualified_backend"] is False
    assert emitted[0]["namespace_sealed"] is False
    assert (path / "probe/payload").exists()


def test_no_arbitrary_root_or_unsafe_option():
    with pytest.raises(SystemExit) as error:
        canary.main(["--setup-sha256", "sha256:" + "a" * 64, "--root", "/tmp"])
    assert error.value.code == 2


def test_source_cli_really_refuses_unprivileged_launch_before_setup():
    if os.geteuid() == canary.WRITER_UID:
        pytest.skip("refusal control requires a different actual execution UID")
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "aware_file_system.staging_worker_canary",
            "--setup-sha256",
            "sha256:" + "a" * 64,
        ],
        capture_output=True,
        timeout=5,
        check=False,
    )
    assert result.returncode == 1
    assert result.stderr == b""
    lines = result.stdout.splitlines()
    assert len(lines) == 1
    value = json.loads(lines[0])
    assert value["status"] == "failed"
    assert value["qualified_backend"] is False
    assert value["effects"] == []
    assert value["cleanup"]["outcome"] == "not_acquired"


@pytest.fixture
def simulated_descriptors(monkeypatch):
    import fcntl

    infos = {
        fd: SimpleNamespace(st_mode=stat.S_IFIFO | 0o600, st_uid=0) for fd in range(3)
    }
    names = ["0", "1", "2", "3"]

    def fstat(fd):
        if fd in infos:
            return infos[fd]
        raise OSError(9, "transient listdir fd closed")

    monkeypatch.setattr(os, "fstat", fstat)
    monkeypatch.setattr(os, "readlink", lambda *args: "pipe:[1234]")
    monkeypatch.setattr(os, "listdir", lambda *args: names)
    monkeypatch.setattr(
        fcntl, "fcntl", lambda fd, *args: os.O_RDONLY if fd == 0 else os.O_WRONLY
    )
    return infos, names


def test_simulated_private_pipes_and_no_leaked_descriptors(simulated_descriptors):
    canary._require_pipes_and_descriptors()


@pytest.mark.parametrize(
    "change", ["owner", "regular", "inherited", "budget", "invalid"]
)
def test_simulated_descriptor_policy_refusals(simulated_descriptors, change):
    infos, names = simulated_descriptors
    if change == "owner":
        infos[1].st_uid = 1000
    elif change == "regular":
        infos[1].st_mode = stat.S_IFREG | 0o600
    elif change == "inherited":
        infos[3] = SimpleNamespace(st_mode=stat.S_IFDIR | 0o700, st_uid=1000)
    elif change == "budget":
        names.extend(str(n) for n in range(4, 66))
    else:
        names.append("not-a-descriptor")
    with pytest.raises(RuntimeError):
        canary._require_pipes_and_descriptors()


@pytest.mark.parametrize("target", ["/tmp/named-pipe", "pipe:[]", "pipe:[oops]"])
def test_simulated_named_or_malformed_pipes_refuse(
    simulated_descriptors, monkeypatch, target
):
    monkeypatch.setattr(os, "readlink", lambda *args: target)
    with pytest.raises(RuntimeError, match="controller_pipes"):
        canary._require_pipes_and_descriptors()
