"""Observed committed source capture, not migration admission or live authority."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path

import pytest

ROOT = next(
    p for p in Path(__file__).resolve().parents if (p / "aware.repo.toml").is_file()
)
BASE = "workspaces/aware_workspace/modules/workspace"
RUNTIME = BASE + "/libs/workspace_runtime/aware_workspace_runtime"
SDK = BASE + "/sdks/workspace/python/public/aware_workspace_sdk"
FS = BASE + "/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter"
ROOTS = (
    BASE + "/libs/workspace_runtime",
    BASE + "/sdks/workspace/python/public",
    BASE + "/sdks/workspace/filesystem_adapter/python",
    BASE + "/sdks/workspace/aware",
)
HISTORY = (
    "docs/reports/workspace-delta-retention-production-values-inputs-20261010.json"
)
SNAPSHOT = (
    ROOT / "docs/reports/workspace-delta-retention-migration-inputs-20261010.json"
)
ENV = (
    "workspaces/aware_network/modules/environment/libs/protected_store_delivery_runtime"
)
EXTRA = (
    HISTORY,
    "docs/reports/workspace-delta-retention-production-values-codec-20261010.md",
    ENV
    + "/aware_environment_protected_store_delivery_runtime/service_store_delivery.py",
    ENV + "/native/backed_command_entry.c",
    ENV + "/native/backed_command_entry.h",
    ENV + "/native/runtime-inputs.toml",
    ENV + "/tests/test_command_entry.py",
    ENV + "/tests/test_service_store_delivery.py",
    ENV + "/tests/test_backed_command_entry.py",
    ENV + "/tests/test_enforcement.py",
)
PHYSICAL_NAME = "repository_delta" + "_store.py"
CLASS_NAME = "WorkspaceRepositoryDelta" + "Store"
REFERENCE_PATTERN = CLASS_NAME + "|repository_delta" + "_store"
EXCLUDED = (
    BASE + "/libs/workspace_runtime/tests/test_delta_retention_owner_port_contract.py",
)
MEANING = {
    "standalone": (
        25,
        "bfcfd2108d0647003c3c33089d42b83c80d4183b0246c66ad8d7b30704b3eb35",
    ),
    "combined": (
        298,
        "7f04fa7ff858cfe04ca847e96568b0dc1f68c6c4738f8960c304180d405e5278",
    ),
}
NEW_TARGETS = {
    FS
    + "/"
    + PHYSICAL_NAME: "Relocate the one original physical implementation; preserve its algorithm.",
    FS
    + "/repository_delta_retention.py": "Genuine FS allocation/adoption/identity/retirement owner ports.",
    SDK
    + "/repository_delta_retention.py": "Original SDK factory/client facade; consume accepted descriptive values.",
    RUNTIME
    + "/repository_delta_retention.py": "Neutral lifecycle and SDK-to-own-provider composition; no physical IO.",
    BASE
    + "/sdks/workspace/filesystem_adapter/python/tests/test_"
    + PHYSICAL_NAME: "Relocate original physical tests once, retaining baseline failures.",
    BASE
    + "/sdks/workspace/filesystem_adapter/python/tests/test_repository_delta_retention.py": "Original-owner identity, independent lifetimes and interruption/race regressions.",
    BASE
    + "/sdks/workspace/python/public/tests/test_repository_delta_retention_client.py": "Genuine client issuance, process affinity, forged-owner and lifecycle proofs.",
    BASE
    + "/libs/workspace_runtime/tests/test_repository_delta_retention.py": "Neutral orchestration and caller boundary proofs.",
}


class CaptureRefusal(ValueError):
    """Typed diagnostic failure, never a source-write permission."""


def _git(*args: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=ROOT, input=input_bytes, capture_output=True, check=True
    ).stdout


def _head() -> str:
    return _git("rev-parse", "HEAD").decode().strip()


def _json(path: str) -> dict:
    return json.loads(_read_file(ROOT / path)[0])


def _members() -> tuple[str, ...]:
    return tuple(
        sorted(
            set(
                _git(
                    "ls-files",
                    "--cached",
                    "--others",
                    "--exclude-standard",
                    "-z",
                    "--",
                    *ROOTS,
                )
                .decode()
                .rstrip("\0")
                .split("\0")
            )
        )
    )


def _references() -> tuple[str, ...]:
    result = subprocess.run(
        ["rg", "-l", REFERENCE_PATTERN, "--glob", "*.py", "workspaces"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    return tuple(sorted(set(result.stdout.decode().splitlines()) - set(EXCLUDED)))


def _read_file(path: Path) -> tuple[bytes, int]:
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, "rb") as source:
            before = os.fstat(source.fileno())
            if not stat.S_ISREG(before.st_mode):
                raise CaptureRefusal(f"nonregular_source:{path}")
            body = source.read()
            after = os.fstat(source.fileno())
            fields = (
                "st_dev",
                "st_ino",
                "st_mode",
                "st_nlink",
                "st_size",
                "st_mtime_ns",
                "st_ctime_ns",
            )
            if any(getattr(before, field) != getattr(after, field) for field in fields):
                raise CaptureRefusal(f"source_changed_during_read:{path}")
            return body, stat.S_IMODE(after.st_mode)
    except OSError as error:
        raise CaptureRefusal(f"source_read_failed:{path}") from error


def _tree(revision: str, paths: tuple[str, ...]) -> dict:
    entries = {}
    for row in _git("ls-tree", "-rz", "--full-tree", revision, "--", *paths).split(
        b"\0"
    ):
        if not row:
            continue
        header, path = row.split(b"\t", 1)
        mode, kind, oid = header.decode().split()
        if kind != "blob" or mode not in ("100644", "100755"):
            raise CaptureRefusal("nonregular_committed_source")
        entries[path.decode()] = (mode, oid)
    if set(entries) != set(paths):
        raise CaptureRefusal("uncommitted_or_missing_source")
    order = tuple(entries)
    output = _git(
        "cat-file",
        "--batch",
        input_bytes="".join(entries[p][1] + "\n" for p in order).encode(),
    )
    offset, result = 0, {}
    for path in order:
        end = output.index(b"\n", offset)
        oid, kind, size = output[offset:end].decode().split()
        mode, expected = entries[path]
        start, finish = end + 1, end + 1 + int(size)
        if oid != expected or kind != "blob" or output[finish : finish + 1] != b"\n":
            raise CaptureRefusal("invalid_committed_blob_response")
        result[path] = mode, oid, output[start:finish]
        offset = finish + 1
    if offset != len(output):
        raise CaptureRefusal("invalid_committed_blob_response")
    return result


def _record(path: str, committed: tuple) -> dict:
    git_mode, oid, blob = committed
    body, mode = _read_file(ROOT / path)
    if body != blob or bool(mode & 0o111) != (git_mode == "100755"):
        raise CaptureRefusal(f"source_differs_from_commit:{path}")
    return {
        "sha256": hashlib.sha256(body).hexdigest(),
        "mode": mode,
        "git_mode": git_mode,
        "git_blob_oid": oid,
    }


def _disposition(path: str) -> dict[str, str]:
    name = Path(path).name
    if path == RUNTIME + "/" + PHYSICAL_NAME:
        action = "one_store_move_value_aliases_only"
        reason = "Move physical class/helpers once into FS. Leave only original neutral aliases for historical pickle/import coordinates; no runtime-to-FS shim."
    elif (
        name == "repository_delta" + "_store_contract.py"
        or name == "complete_scope_observation.py"
    ):
        action, reason = (
            "preserve",
            "Already neutral; preserve original values and algorithms.",
        )
    elif path == RUNTIME + "/__init__.py":
        action, reason = (
            "remove_physical_export",
            "Remove one physical class export, preserve other 560 original export identities/order; no raw FS forwarding.",
        )
    elif "/aware_local_dev_service/" in path:
        action, reason = (
            "semantic_factory_migration",
            "Replace caller-injected callable factory with genuine SDK factory selection. Retain client before initialization and preserve participant/failure evidence.",
        )
    elif path.startswith(ENV):
        action, reason = (
            "native_original_pair_sdk_migration",
            "Allocate and retain genuine disabled SDK client before initialization. Preserve exact session/client tuple identity, native custody and configured capacities; no raw unwrap.",
        )
    elif "/benchmarks/" in path:
        action, reason = (
            "benchmark_fixture_migration",
            "Select explicit SDK FS factory and preserve measurements/limits; no installed-readiness inference.",
        )
    elif "/tests/" in path:
        action = (
            "physical_test_relocation"
            if name == "test_" + PHYSICAL_NAME
            else "genuine_fixture_or_current_boundary_migration"
        )
        reason = "Preserve original assertions and baseline diagnostics; use genuine SDK client fixtures where operational, and original FS store tests at their one new location. Historical capture diagnostics remain historical."
    else:
        action, reason = (
            "sdk_client_composition",
            "Use genuine SDK client/owner verification before effects, not structural typing or string binding; preserve neutral coordinator algorithm and original limits.",
        )
    return {"action": action, "reason": reason}


def _original_implementation() -> dict:
    tree = ast.parse(_read_file(ROOT / (RUNTIME + "/" + PHYSICAL_NAME))[0])
    implementation = [
        node for node in tree.body if not isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    original = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == CLASS_NAME
    )
    members = {
        node.name: ast.unparse(node.args)
        for node in original.body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    }
    return {
        "nonimport_ast_sha256": hashlib.sha256(
            ast.dump(
                ast.Module(body=implementation, type_ignores=[]),
                include_attributes=False,
            ).encode()
        ).hexdigest(),
        "physical_members": members,
    }


def _guard(
    head: str,
    members: tuple[str, ...],
    references: tuple[str, ...],
    paths: tuple[str, ...],
) -> None:
    if _head() != head:
        raise CaptureRefusal("head_changed")
    if _members() != members or _references() != references:
        raise CaptureRefusal("source_membership_changed")
    if _git("status", "--porcelain=v1", "-z", "--", *paths):
        raise CaptureRefusal("dirty_source_inputs")
    if any(os.path.lexists(ROOT / p) for p in NEW_TARGETS):
        raise CaptureRefusal("new_target_already_exists")


def capture(*, revision: str | None = None) -> dict:
    head = _head()
    revision = revision or head
    _git("merge-base", "--is-ancestor", revision, head)
    previous = _json(HISTORY)
    members, references = _members(), _references()
    if set(references) != set(previous["original_reference_paths"]):
        raise CaptureRefusal("reference_closure_changed")
    paths = tuple(sorted(set(members) | set(previous["preserved_inputs"]) | set(EXTRA)))
    _guard(head, members, references, paths)
    committed = _tree(revision, paths)
    records = {p: _record(p, committed[p]) for p in paths}
    for p, pin in previous["preserved_inputs"].items():
        if any(records[p][key] != pin[key] for key in ("sha256", "mode", "git_mode")):
            raise CaptureRefusal(f"accepted_input_changed:{p}")
    result = {
        "revision": revision,
        "execution": "codex-01a122a6-588d-7450-86b3-dd45aa7617de",
        "authority": "diagnostic_read_capture_only",
        "roots": list(ROOTS),
        "root_membership": list(members),
        "inputs": records,
        "accepted_preserved_inputs": list(previous["preserved_inputs"]),
        "reference_dispositions": {p: _disposition(p) for p in references},
        "excluded_reference_paths": list(EXCLUDED),
        "proposed_absent_targets": NEW_TARGETS,
        "original_implementation": _original_implementation(),
        "meaning": {
            name: {"entries": count, "sha256": digest}
            for name, (count, digest) in MEANING.items()
        },
    }
    # Repeat byte/mode observation as well as membership/HEAD/index guards.
    if any(_record(p, committed[p]) != records[p] for p in paths):
        raise CaptureRefusal("source_changed_during_capture")
    _guard(head, members, references, paths)
    return result


def test_frozen_snapshot_reproduces_complete_capture_at_original_revision():
    saved = json.loads(SNAPSHOT.read_bytes())
    assert capture(revision=saved["revision"]) == saved
    assert len(saved["accepted_preserved_inputs"]) == 49
    assert len(saved["reference_dispositions"]) == 26
    assert len(saved["proposed_absent_targets"]) == 8
    assert len(saved["original_implementation"]["physical_members"]) == 13
    assert Path(__file__).relative_to(ROOT).as_posix() in saved["root_membership"]


def test_frozen_meaning_reproduces_genuine_standalone_and_combined_lowering():
    from test_workspace_delta_retention_value_codec import lower

    for name, (count, digest) in MEANING.items():
        meaning = lower(combined=name == "combined")
        assert (len(meaning.entries), meaning.canonical_sha256) == (count, digest)


@pytest.mark.parametrize("kind", ("missing", "symlink", "fifo", "directory"))
def test_nonregular_sources_refuse_without_blocking_or_mutation(tmp_path, kind):
    path = tmp_path / "source"
    if kind == "symlink":
        path.symlink_to(tmp_path / "absent")
    elif kind == "fifo":
        os.mkfifo(path)
    elif kind == "directory":
        path.mkdir()
    with pytest.raises(CaptureRefusal):
        _read_file(path)
    assert path.is_symlink() or path.exists() or kind == "missing"


def test_read_records_exact_bytes_and_nonexecutable_mode(tmp_path):
    path = tmp_path / "source"
    path.write_bytes(b"exact\x00bytes\n")
    path.chmod(0o640)
    assert _read_file(path) == (b"exact\x00bytes\n", 0o640)


def test_open_time_fifo_substitution_refuses_without_blocking(tmp_path, monkeypatch):
    path = tmp_path / "source"
    path.write_bytes(b"original")
    original_open = os.open

    def substituted_open(selected, flags):
        path.unlink()
        os.mkfifo(path)
        return original_open(selected, flags)

    monkeypatch.setattr(os, "open", substituted_open)
    with pytest.raises(CaptureRefusal, match="nonregular"):
        _read_file(path)
    assert stat.S_ISFIFO(path.stat().st_mode)


def test_in_read_metadata_change_refuses(tmp_path, monkeypatch):
    path = tmp_path / "source"
    path.write_bytes(b"original")
    original_fstat, observations = os.fstat, []

    def changing_fstat(descriptor):
        if observations:
            path.write_bytes(b"changed body")
        observations.append(descriptor)
        return original_fstat(descriptor)

    monkeypatch.setattr(os, "fstat", changing_fstat)
    with pytest.raises(CaptureRefusal, match="changed_during_read"):
        _read_file(path)


@pytest.mark.parametrize("mismatch", ("bytes", "executable"))
def test_uncommitted_body_or_executable_mode_refuses(tmp_path, monkeypatch, mismatch):
    monkeypatch.setattr(__import__(__name__), "ROOT", tmp_path)
    path = tmp_path / "source"
    path.write_bytes(b"changed" if mismatch == "bytes" else b"original")
    path.chmod(0o755 if mismatch == "executable" else 0o644)
    with pytest.raises(CaptureRefusal, match="differs_from_commit"):
        _record("source", ("100644", "oid", b"original"))


@pytest.mark.parametrize(
    "mismatch", ("head", "members", "references", "dirty", "target")
)
def test_guards_refuse_exact_capture_drift_without_writes(monkeypatch, mismatch):
    module = __import__(__name__)
    monkeypatch.setattr(
        module, "_head", lambda: "different" if mismatch == "head" else "head"
    )
    monkeypatch.setattr(
        module, "_members", lambda: ("extra",) if mismatch == "members" else ()
    )
    monkeypatch.setattr(
        module, "_references", lambda: ("extra",) if mismatch == "references" else ()
    )
    monkeypatch.setattr(
        module, "_git", lambda *args: b"dirty" if mismatch == "dirty" else b""
    )
    monkeypatch.setattr(os.path, "lexists", lambda p: mismatch == "target")
    with pytest.raises(CaptureRefusal):
        _guard("head", (), (), ())


@pytest.mark.parametrize(
    "row", (b"120000 blob oid\tsource\0", b"160000 commit oid\tsource\0", b"")
)
def test_nonregular_or_missing_committed_members_refuse(monkeypatch, row):
    monkeypatch.setattr(__import__(__name__), "_git", lambda *args, **kwargs: row)
    with pytest.raises(CaptureRefusal):
        _tree("revision", ("source",))


def test_frozen_migration_semantics_preserve_factory_and_native_custody_distinctions():
    dispositions = json.loads(SNAPSHOT.read_bytes())["reference_dispositions"]
    assert (
        sum(d["action"] == "semantic_factory_migration" for d in dispositions.values())
        == 1
    )
    assert (
        sum(
            d["action"] == "native_original_pair_sdk_migration"
            for d in dispositions.values()
        )
        == 1
    )
    assert (
        sum(
            d["action"] == "one_store_move_value_aliases_only"
            for d in dispositions.values()
        )
        == 1
    )
    assert (
        sum(d["action"] == "physical_test_relocation" for d in dispositions.values())
        == 1
    )
    assert all(d["action"] and d["reason"] for d in dispositions.values())
