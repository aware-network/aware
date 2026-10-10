"""Committed source snapshot diagnostics; no admission, extraction or writer."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
from pathlib import Path

import pytest
import test_workspace_publication_authored_types as predecessor
import test_workspace_publication_port_codec as production

ROOT = predecessor.ROOT
SNAPSHOT = (
    ROOT / "docs/reports/workspace-publication-successor-source-capture-20261009.json"
)
PRODUCER = Path(__file__).relative_to(ROOT).as_posix()
CODEC_COMMIT = "ada3c39b3f7eb303b25b475e50bc4d143600a1dd"
CODEC_REPORT = "docs/reports/workspace-publication-port-codecs-20261009.md"
HISTORY = {
    "docs/reports/workspace-publication-source-capture-20261009.json": "07c55187a2009ddf19b47aa4db42d16f4855c46c4b4e66a0468a538025d43ecf",
    "docs/reports/workspace-publication-sdk-contract-inputs-20261009.json": "f1c9d440011c89d0e1f4e6219f344d7204a6da15bfe011debc5d171e9147b5ab",
    "docs/reports/workspace-publication-extraction-callers-20261009.json": "baa83a5b762d1f8173b8c36ec3a7e65c165190873a592cdfaa61e56a2278e5b5",
}
MEANING = {
    "workspace": (
        273,
        "8cd52313bea8cfd5d49a4ec308f03ed2cb14cedc87ff81786283adbeda4bc674",
    ),
    "issue": (234, "3f0206e535f16ef476a9b9b4f8d18c8cebf52ee7fb9d15c0ebf57980c1c247d3"),
}


class CaptureRefusal(ValueError):
    """Diagnostic refusal only; it confers no operational authority."""


def _git(*args: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=ROOT, input=input_bytes, capture_output=True, check=True
    ).stdout


def _head() -> str:
    return _git("rev-parse", "HEAD").decode().strip()


def _paths() -> tuple[str, ...]:
    # Preserve historical roots/exclusions; add no caller migration authority.
    return predecessor._source_paths()


def _qualification_paths() -> tuple[str, ...]:
    # Keep predecessor extraction exclusions, but bind the diagnostic supplier
    # and fixtures used by the imported producer as a separate read-set.
    return tuple(path.as_posix() for path in predecessor.QUALIFICATION_PATHS)


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


def _tree(head: str, paths: tuple[str, ...]) -> dict[str, tuple[str, str, bytes]]:
    rows = _git("ls-tree", "-rz", "--full-tree", head, "--", *paths)
    entries = {}
    for row in rows.split(b"\0"):
        if not row:
            continue
        header, path = row.split(b"\t", 1)
        mode, kind, oid = header.decode().split()
        if kind != "blob" or mode not in ("100644", "100755"):
            raise CaptureRefusal(f"nonregular_committed_source:{path!r}")
        entries[path.decode()] = (mode, oid)
    if set(entries) != set(paths):
        raise CaptureRefusal("uncommitted_or_missing_source")
    order = tuple(entries)
    output = _git(
        "cat-file",
        "--batch",
        input_bytes="".join(entries[path][1] + "\n" for path in order).encode(),
    )
    offset = 0
    result = {}
    for path in order:
        end = output.index(b"\n", offset)
        oid, kind, size = output[offset:end].decode().split()
        mode, expected = entries[path]
        if oid != expected or kind != "blob":
            raise CaptureRefusal("committed_blob_unavailable")
        start = end + 1
        finish = start + int(size)
        if output[finish : finish + 1] != b"\n":
            raise CaptureRefusal("invalid_blob_response")
        result[path] = (mode, oid, output[start:finish])
        offset = finish + 1
    if offset != len(output):
        raise CaptureRefusal("invalid_blob_response")
    return result


def _file_record(path: str, committed: tuple[str, str, bytes]) -> dict[str, object]:
    mode, oid, blob = committed
    body, observed_mode = _read_file(ROOT / path)
    if body != blob or bool(observed_mode & 0o111) != (mode == "100755"):
        raise CaptureRefusal(f"source_differs_from_commit:{path}")
    return {
        "sha256": hashlib.sha256(body).hexdigest(),
        "mode": observed_mode,
        "git_blob_oid": oid,
        "git_mode": mode,
    }


def _guard_revision(head: str, paths: tuple[str, ...]) -> None:
    if _paths() != paths:
        raise CaptureRefusal("source_membership_changed")
    if _head() != head:
        raise CaptureRefusal("head_changed")
    if _git("status", "--porcelain=v1", "-z", "--", *paths, *_qualification_paths()):
        raise CaptureRefusal("dirty_source_inputs")


def _production_closure() -> dict[str, object]:
    production.lower.cache_clear()
    result = {}
    for owner, (count, digest) in MEANING.items():
        meaning = production.lower(owner)
        if (len(meaning.entries), meaning.canonical_sha256) != (count, digest):
            raise CaptureRefusal(f"production_meaning_changed:{owner}")
        result[owner] = {
            "entry_count": count,
            "meaning_sha256": digest,
            "sources": {
                (production.OWNERS[owner] / name)
                .relative_to(ROOT)
                .as_posix(): hashlib.sha256(
                    (production.OWNERS[owner] / name).read_bytes()
                ).hexdigest()
                for name in (
                    "repository_publication_values.aware",
                    "repository_publication_ports.aware",
                )
            },
        }
    return result


def _codec_pins() -> dict[str, str]:
    report = _git("show", f"{CODEC_COMMIT}:{CODEC_REPORT}").decode()
    pins = dict(re.findall(r"\| `(workspaces/[^`]+)` \| `([0-9a-f]{64})` \|", report))
    if len(pins) != 8:
        raise CaptureRefusal("invalid_accepted_codec_pin_inventory")
    return pins


def _differential(old: dict[str, object], new: dict[str, object]) -> dict[str, object]:
    return {
        "added": sorted(new.keys() - old.keys()),
        "removed": sorted(old.keys() - new.keys()),
        "changed": {
            path: {"before": old[path], "after": new[path]}
            for path in sorted(old.keys() & new.keys())
            if any(old[path][key] != new[path][key] for key in ("sha256", "mode"))
        },
    }


def capture_sources() -> dict[str, object]:
    head, paths = _head(), _paths()
    _guard_revision(head, paths)
    _git("merge-base", "--is-ancestor", CODEC_COMMIT, head)
    qualification_paths = _qualification_paths()
    read_set = tuple(sorted(set(paths) | set(qualification_paths)))
    tree = _tree(head, read_set)
    files = {path: _file_record(path, tree[path]) for path in paths}
    qualification_inputs = {
        path: _file_record(path, tree[path]) for path in qualification_paths
    }
    history = {}
    for path, expected in HISTORY.items():
        body, _ = _read_file(ROOT / path)
        if hashlib.sha256(body).hexdigest() != expected:
            raise CaptureRefusal(f"historical_artifact_changed:{path}")
        history[path] = expected
    old = json.loads((ROOT / next(iter(HISTORY))).read_text())["source_files"]
    pins = _codec_pins()
    if any(
        files.get(path, {}).get("sha256") != digest for path, digest in pins.items()
    ):
        raise CaptureRefusal("accepted_codec_source_changed")
    # No renewal of the original physical writer, provider or scope policy.
    for path in predecessor.contract.PINS:
        name = path.as_posix()
        if files[name]["sha256"] != old[name]["sha256"]:
            raise CaptureRefusal(f"original_contract_input_changed:{name}")
    closure = _production_closure()
    tooling = {
        name: {
            "path": str(Path(module.__file__).relative_to(ROOT)),
            "sha256": hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
        }
        for name, module in (
            ("grammar", predecessor.grammar_binding),
            ("tree_sitter", predecessor.parser_binding),
        )
    }
    observed = files | qualification_inputs
    for path in read_set:
        if _file_record(path, tree[path]) != observed[path]:
            raise CaptureRefusal(f"source_changed_during_capture:{path}")
    for path, expected in history.items():
        if hashlib.sha256(_read_file(ROOT / path)[0]).hexdigest() != expected:
            raise CaptureRefusal(f"historical_artifact_changed:{path}")
    for record in tooling.values():
        if (
            hashlib.sha256(_read_file(ROOT / record["path"])[0]).hexdigest()
            != record["sha256"]
        ):
            raise CaptureRefusal("observed_tooling_changed")
    _guard_revision(head, paths)
    return {
        "purpose": "publication-successor-pre-extraction-source-capture",
        "activation_authority": False,
        "captured_head": head,
        "canonical_producer": PRODUCER,
        "source_roots": [path.as_posix() for path in predecessor.SOURCE_ROOTS],
        "excluded_qualification_paths": [
            path.as_posix() for path in predecessor.QUALIFICATION_PATHS
        ],
        "source_files": files,
        "qualification_inputs": qualification_inputs,
        "dirty_source_paths": [],
        "preserved_historical_artifacts": history,
        "accepted_codec_source": {"commit": CODEC_COMMIT, "source_pins": pins},
        "qualified_production_value_closure": closure,
        "observed_parser_artifacts": tooling,
        "predecessor_differential": _differential(old, files),
    }


def test_successor_snapshot_is_current_and_matches_original_committed_blobs():
    recorded = json.loads(SNAPSHOT.read_text())
    actual = capture_sources()
    _git(
        "merge-base",
        "--is-ancestor",
        recorded["captured_head"],
        actual["captured_head"],
    )
    actual["captured_head"] = recorded["captured_head"]
    assert actual == recorded
    observations = recorded["source_files"] | recorded["qualification_inputs"]
    committed = _tree(recorded["captured_head"], tuple(observations))
    assert set(committed) == set(observations)
    assert PRODUCER in committed
    assert set(recorded["qualification_inputs"]) == set(_qualification_paths())
    for path, (mode, oid, body) in committed.items():
        entry = observations[path]
        assert entry["git_blob_oid"] == oid and entry["git_mode"] == mode
        assert entry["sha256"] == hashlib.sha256(body).hexdigest()


@pytest.mark.parametrize("mode", [0o644, 0o664, 0o755])
def test_regular_source_read_preserves_observed_mode_and_exact_bytes(tmp_path, mode):
    path = tmp_path / "source"
    path.write_bytes(b"exact\x00bytes\n")
    path.chmod(mode)
    assert _read_file(path) == (b"exact\x00bytes\n", mode)


@pytest.mark.parametrize("kind", ["missing", "symlink", "fifo", "directory"])
def test_nonregular_sources_refuse_without_blocking(tmp_path, kind):
    path = tmp_path / "source"
    if kind == "symlink":
        path.symlink_to(tmp_path / "missing")
    elif kind == "fifo":
        os.mkfifo(path)
    elif kind == "directory":
        path.mkdir()
    with pytest.raises(CaptureRefusal):
        _read_file(path)


def test_source_mutation_during_read_refuses(tmp_path, monkeypatch):
    path = tmp_path / "source"
    path.write_bytes(b"before")
    original = os.fstat
    calls = 0

    def changing_stat(descriptor):
        nonlocal calls
        calls += 1
        if calls == 2:
            path.write_bytes(b"changed-size")
        return original(descriptor)

    monkeypatch.setattr(os, "fstat", changing_stat)
    with pytest.raises(CaptureRefusal, match="source_changed_during_read"):
        _read_file(path)


@pytest.mark.parametrize("replacement", ["fifo", "symlink"])
def test_open_time_substitution_cannot_block_or_follow_a_leaf(
    tmp_path, monkeypatch, replacement
):
    path = tmp_path / "source"
    path.write_bytes(b"original")
    original_open = os.open

    def substitute(selected_path, flags):
        path.unlink()
        if replacement == "fifo":
            os.mkfifo(path)
        else:
            path.symlink_to(tmp_path / "missing")
        return original_open(selected_path, flags)

    monkeypatch.setattr(os, "open", substitute)
    with pytest.raises(CaptureRefusal):
        _read_file(path)


@pytest.mark.parametrize(
    "body,mode,git_mode",
    [
        (b"changed", 0o664, "100644"),
        (b"original", 0o755, "100644"),
        (b"original", 0o664, "100755"),
    ],
)
def test_source_blob_or_executable_drift_refuses(monkeypatch, body, mode, git_mode):
    monkeypatch.setattr(__import__(__name__), "_read_file", lambda path: (body, mode))
    with pytest.raises(CaptureRefusal, match="source_differs_from_commit"):
        _file_record("diagnostic", (git_mode, "original-oid", b"original"))


@pytest.mark.parametrize("drift", ["membership", "head", "dirty"])
def test_revision_guard_refuses_concurrent_drift(monkeypatch, drift):
    module = __import__(__name__)
    monkeypatch.setattr(
        module, "_paths", lambda: ("other",) if drift == "membership" else ("path",)
    )
    monkeypatch.setattr(module, "_head", lambda: "other" if drift == "head" else "head")
    monkeypatch.setattr(
        module, "_git", lambda *a: b" M path\0" if drift == "dirty" else b""
    )
    with pytest.raises(CaptureRefusal):
        _guard_revision("head", ("path",))


def test_untracked_read_set_member_cannot_become_a_committed_capture(monkeypatch):
    monkeypatch.setattr(__import__(__name__), "_git", lambda *a, **kw: b"")
    with pytest.raises(CaptureRefusal, match="uncommitted_or_missing_source"):
        _tree("head", ("untracked",))


@pytest.mark.parametrize("mode,kind", [("120000", "blob"), ("160000", "commit")])
def test_nonregular_git_tree_entries_refuse(monkeypatch, mode, kind):
    monkeypatch.setattr(
        __import__(__name__),
        "_git",
        lambda *a, **kw: f"{mode} {kind} oid\tpath\0".encode(),
    )
    with pytest.raises(CaptureRefusal, match="nonregular_committed_source"):
        _tree("head", ("path",))


def test_differential_keeps_modes_separate_from_bytes_and_does_not_grant_authority():
    old = {
        "same": {"sha256": "a", "mode": 0o664},
        "changed": {"sha256": "b", "mode": 0o664},
        "removed": {"sha256": "c", "mode": 0o664},
    }
    new = {
        "same": {"sha256": "a", "mode": 0o664, "git_blob_oid": "a"},
        "changed": {"sha256": "b", "mode": 0o644, "git_blob_oid": "b"},
        "added": {"sha256": "d", "mode": 0o664, "git_blob_oid": "d"},
    }
    result = _differential(old, new)
    assert result["added"] == ["added"] and result["removed"] == ["removed"]
    assert tuple(result["changed"]) == ("changed",)
    assert not any("authority" in key for key in result)


if __name__ == "__main__":
    print(json.dumps(capture_sources(), indent=2, sort_keys=True))
