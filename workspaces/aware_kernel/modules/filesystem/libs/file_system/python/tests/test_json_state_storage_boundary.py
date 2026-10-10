"""Storage-owner regression proofs, not installed or confinement acceptance."""

from __future__ import annotations

import errno
import hashlib
import os
import stat
import tomllib
from fcntl import LOCK_EX, LOCK_NB, flock
from pathlib import Path

import pytest
from aware_file_system import local_json_state as storage
from packaging.requirements import Requirement

FILESYSTEM = Path(__file__).resolve().parents[1]
REPOSITORY = FILESYSTEM.parents[6]
WORKFLOW = REPOSITORY / "workspaces/aware_coordination/modules/workflow"


def test_storage_implementation_matches_the_original_owner_bytes():
    # Retain the original helper, not a freshly implemented approximation.
    original = "6f4891fec71e62a36bda415904aa5625884c3b2c3dccc78a4d628dc5f3deb36b"
    assert hashlib.sha256(Path(storage.__file__).read_bytes()).hexdigest() == original


def test_runtime_no_longer_ships_storage_or_depends_on_its_owner():
    runtime = WORKFLOW / "libs/issue_runtime"
    metadata = tomllib.loads((runtime / "pyproject.toml").read_text())
    assert metadata["project"]["version"] == "0.3.0"
    assert metadata["project"]["dependencies"] == [
        "aware-issue-operational-runtime>=0.1.0"
    ]
    assert not (runtime / "aware_issue_runtime/local_json_state.py").exists()
    assert not (runtime / "tests/test_local_json_state.py").exists()
    sources = list((runtime / "aware_issue_runtime").glob("*.py"))
    assert sources
    for source in sources:
        text = source.read_text()
        assert "local_json_state" not in text
        assert "aware_file_system" not in text


@pytest.mark.parametrize(
    "relative,version,requirements",
    [
        (
            "sdks/issue/python",
            "0.10.1",
            {
                "aware-file-system": ("0.3.0", "0.3.1", "0.4.0"),
                "aware-issue-runtime": ("0.2.0", "0.3.0", "0.4.0"),
            },
        ),
        (
            "sdks/issue/filesystem_adapter/python",
            "0.9.1",
            {
                "aware-file-system": ("0.3.0", "0.3.1", "0.4.0"),
                "aware-issue-sdk": ("0.10.0", "0.10.1", "0.11.0"),
                "aware-issue-runtime": ("0.2.0", "0.3.0", "0.4.0"),
            },
        ),
        (
            "sdks/issue/cli/python",
            "0.7.1",
            {
                "aware-issue-sdk": ("0.10.0", "0.10.1", "0.11.0"),
                "aware-issue-fs-adapter": ("0.9.0", "0.9.1", "0.10.0"),
            },
        ),
        (
            "services/issue",
            "0.1.1",
            {
                "aware-file-system": ("0.3.0", "0.3.1", "0.4.0"),
            },
        ),
        (
            "libs/issue_local_service_runtime",
            "0.1.2",
            {
                "aware-issue-runtime": ("0.2.0", "0.3.0", "0.4.0"),
            },
        ),
        (
            "libs/issue_api_view_source_adapters/python",
            "0.1.2",
            {
                "aware-issue-runtime": ("0.2.0", "0.3.0", "0.4.0"),
                "aware-issue-local-service-runtime": ("0.1.1", "0.1.2", "0.2.0"),
            },
        ),
    ],
)
def test_successor_callers_bind_storage_free_runtime_and_real_storage_owner(
    relative,
    version,
    requirements,
):
    project = tomllib.loads((WORKFLOW / relative / "pyproject.toml").read_text())[
        "project"
    ]
    assert project["version"] == version
    dependencies = {
        Requirement(text).name: Requirement(text) for text in project["dependencies"]
    }
    for name, (old, current, successor) in requirements.items():
        requirement = dependencies[name]
        assert old not in requirement.specifier
        assert current in requirement.specifier
        assert successor not in requirement.specifier
        assert requirement.url is None
        assert requirement.marker is None
    if relative == "services/issue":
        assert "aware-issue-runtime" not in dependencies


def test_filesystem_allocation_and_local_dev_caller_floors():
    project = tomllib.loads((FILESYSTEM / "pyproject.toml").read_text())["project"]
    assert project["version"] == "0.3.2"
    project = tomllib.loads(
        (
            REPOSITORY
            / ("workspaces/aware_dev/modules/dev/services/local_dev/pyproject.toml")
        ).read_text()
    )["project"]
    dependencies = {
        Requirement(text).name: Requirement(text) for text in project["dependencies"]
    }
    assert "0.3.0" in dependencies["aware-issue-runtime"].specifier
    assert "0.2.0" not in dependencies["aware-issue-runtime"].specifier
    assert "0.1.2" in dependencies["aware-issue-local-service-runtime"].specifier
    assert "0.1.1" not in dependencies["aware-issue-local-service-runtime"].specifier


def test_missing_document_default_is_detached_and_existing_lock_behavior_preserved(
    tmp_path,
):
    path = tmp_path / "nested/state.json"
    default = {"row": "original"}
    document = storage.read_json_state_document(state_path=path, default=default)
    document["row"] = "changed"
    assert default == {"row": "original"}
    assert not path.exists()
    assert (path.parent / ".state.json.lock").is_file()


@pytest.mark.parametrize("mode", [0o600, 0o640, 0o664])
def test_atomic_replacement_preserves_existing_mode_under_restrictive_umask(
    tmp_path,
    mode,
):
    path = tmp_path / "state.json"
    path.write_text('{"old": true}')
    path.chmod(mode)
    previous_umask = os.umask(0o077)
    try:
        storage.write_json_state_document(state_path=path, document={"new": True})
    finally:
        os.umask(previous_umask)
    assert stat.S_IMODE(path.stat().st_mode) == mode
    assert storage.read_json_state_document(state_path=path) == {"new": True}


def test_default_mode_and_canonical_encoding_preserved(tmp_path):
    path = tmp_path / "state.json"
    previous_umask = os.umask(0o077)
    try:
        storage.write_json_state_document(state_path=path, document={"z": 2, "a": 1})
    finally:
        os.umask(previous_umask)
    assert stat.S_IMODE(path.stat().st_mode) == 0o664
    assert path.read_bytes() == b'{\n  "a": 1,\n  "z": 2\n}\n'


@pytest.mark.parametrize("body", [b"[]", b"null", b"true", b"bad-json"])
def test_malformed_or_non_object_documents_are_not_replaced(tmp_path, body):
    path = tmp_path / "state.json"
    path.write_bytes(body)
    with pytest.raises(ValueError, match="Invalid JSON state"):
        storage.update_json_state_document(state_path=path, update=lambda _: {})
    assert path.read_bytes() == body


def test_entire_update_holds_the_original_cross_process_lock(tmp_path):
    path = tmp_path / "state.json"

    def update(document):
        with (path.parent / ".state.json.lock").open("a+b") as contender:
            with pytest.raises(BlockingIOError) as failure:
                flock(contender.fileno(), LOCK_EX | LOCK_NB)
            assert failure.value.errno in (errno.EAGAIN, errno.EACCES)
        return {**document, "updated": True}

    assert storage.update_json_state_document(state_path=path, update=update) == {
        "updated": True
    }


@pytest.mark.parametrize(
    "failure_stage",
    ["callback", "serialize", "replace", "file_fsync", "directory_fsync"],
)
def test_failures_preserve_prior_or_published_bytes_without_retry_or_fd_leak(
    tmp_path,
    monkeypatch,
    failure_stage,
):
    path = tmp_path / "state.json"
    prior = b'{"prior": true}\n'
    path.write_bytes(prior)
    descriptors = len(list(Path("/proc/self/fd").iterdir()))
    actual_replace = storage.os.replace
    actual_fsync = storage.os.fsync
    replaces = []

    def replace(source, target):
        replaces.append((source, target))
        if failure_stage == "replace":
            raise OSError("replacement failed")
        actual_replace(source, target)

    def fsync(descriptor):
        directory = stat.S_ISDIR(os.fstat(descriptor).st_mode)
        if failure_stage == ("directory_fsync" if directory else "file_fsync"):
            raise OSError("durability failed")
        actual_fsync(descriptor)

    def update(_):
        if failure_stage == "callback":
            raise RuntimeError("callback failed")
        return {"new": object() if failure_stage == "serialize" else True}

    monkeypatch.setattr(storage.os, "replace", replace)
    monkeypatch.setattr(storage.os, "fsync", fsync)
    with pytest.raises((RuntimeError, TypeError, OSError)):
        storage.update_json_state_document(state_path=path, update=update)
    if failure_stage == "directory_fsync":
        assert path.read_bytes() == b'{\n  "new": true\n}\n'
        assert len(replaces) == 1
    else:
        assert path.read_bytes() == prior
        assert len(replaces) == (1 if failure_stage == "replace" else 0)
    assert not list(tmp_path.glob("*.tmp"))
    assert len(list(Path("/proc/self/fd").iterdir())) == descriptors
    # Exception exits must release the original lock as well as descriptors.
    with (path.parent / ".state.json.lock").open("a+b") as contender:
        flock(contender.fileno(), LOCK_EX | LOCK_NB)
