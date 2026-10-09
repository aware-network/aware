"""Qualify accepted Issue storage successors through actual neutral owners.

This is a source composition proof, not a consumer projection or installation.
"""

import importlib.util
import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from aware_file_system import local_json_state
from aware_issue_sdk import local_state
from aware_specification_fs_sdk_adapter import open_governed_specification_draft
from aware_specification_sdk import (
    SpecificationObserveRequest,
    SpecificationOperationError,
)
from packaging.requirements import Requirement

ROOT = Path(__file__).resolve().parents[9]
PRODUCERS = {
    "aware-file-system": (
        "workspaces/aware_kernel/modules/filesystem/libs/file_system/python",
        "0.3.1",
    ),
    "aware-issue-sdk": (
        "workspaces/aware_coordination/modules/workflow/sdks/issue/python",
        "0.10.1",
    ),
    "aware-issue-fs-adapter": (
        "workspaces/aware_coordination/modules/workflow/sdks/issue/filesystem_adapter/python",
        "0.9.1",
    ),
}


@pytest.mark.parametrize("name", PRODUCERS)
def test_actual_successor_metadata_and_direct_storage_edge(name):
    path, version = PRODUCERS[name]
    project = tomllib.loads((ROOT / path / "pyproject.toml").read_text())["project"]
    assert (project["name"], project["version"]) == (name, version)
    if name != "aware-file-system":
        requirements = {
            requirement.name: requirement
            for value in project["dependencies"]
            if (requirement := Requirement(value))
        }
        assert "0.3.1" in requirements["aware-file-system"].specifier
        assert "0.3.0" not in requirements["aware-file-system"].specifier
        assert "0.3.0" in requirements["aware-issue-runtime"].specifier
        assert "0.2.99" not in requirements["aware-issue-runtime"].specifier


def test_existing_cli_admits_adapter_successor_without_new_reader_edges():
    cli = tomllib.loads((Path(__file__).parents[2] / "cli/pyproject.toml").read_text())[
        "project"
    ]
    assert cli["version"] == "0.4.2"
    for value, extra in (
        (cli["dependencies"][1], "protocol"),
        (cli["optional-dependencies"]["governed"][0], "governed"),
    ):
        requirement = Requirement(value)
        assert requirement.name == "aware-specification-fs-sdk-adapter"
        assert requirement.extras == {extra}
        assert "0.4.2" in requirement.specifier
        assert "0.5.0" not in requirement.specifier
    assert all("issue" not in value for value in cli["dependencies"])


@pytest.mark.parametrize(
    "name",
    [
        "read_json_state_document",
        "write_json_state_document",
        "update_json_state_document",
    ],
)
def test_issue_sdk_uses_actual_filesystem_owner_exports(name):
    assert getattr(local_state, name) is getattr(local_json_state, name)


def test_sdk_cache_roundtrip_preserves_unrelated_bytes_and_private_file_mode(tmp_path):
    state = tmp_path / "state.json"
    state.write_text('{"issues_by_id": {}, "issue_id_by_tag": {}}\n')
    state.chmod(0o600)
    unrelated = tmp_path / "unrelated.txt"
    unrelated.write_bytes(b"unrelated work\n")
    store = local_state.load_workflow_issue_state_store(state_path=state)
    local_state.save_workflow_issue_state_store(state_path=state, store=store)
    assert local_state.load_workflow_issue_state_store(state_path=state) == store
    assert state.stat().st_mode & 0o777 == 0o600
    assert unrelated.read_bytes() == b"unrelated work\n"


def test_malformed_sdk_cache_refuses_without_replacing_bytes(tmp_path):
    state = tmp_path / "state.json"
    state.write_bytes(b"not-json\n")
    with pytest.raises(ValueError, match="Invalid issue-state JSON"):
        local_state.load_workflow_issue_state_store(state_path=state)
    assert state.read_bytes() == b"not-json\n"


def _fresh_issue_sdk_cache_import(*, restore_retired_storage=False):
    script = """
import importlib.abc, importlib.machinery, importlib.util, json, sys, types
sys.path[:0] = json.loads(sys.argv[1])
class RejectPrivateImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith('aware_') and any(
            marker in fullname for marker in ('service', 'ontology', 'orm', 'experience')
        ):
            raise ImportError('excluded_owner_import:' + fullname)
sys.meta_path.insert(0, RejectPrivateImports())
from aware_issue_sdk import local_state
from aware_file_system import local_json_state
assert local_state.update_json_state_document is local_json_state.update_json_state_document
retired_name = 'aware_issue_runtime.local_json_state'
if sys.argv[2] == 'restore':
    restored = types.ModuleType(retired_name)
    restored.__spec__ = importlib.machinery.ModuleSpec(retired_name, loader=None)
    sys.modules[retired_name] = restored
    assert importlib.import_module(retired_name) is restored
assert importlib.util.find_spec(retired_name) is None, (
    'retired_storage_module_present:' + retired_name
)
"""
    paths = [str(ROOT / path) for path, _ in PRODUCERS.values()]
    paths.append(
        str(ROOT / "workspaces/aware_coordination/modules/workflow/libs/issue_runtime")
    )
    return subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "-c",
            script,
            json.dumps(paths),
            "restore" if restore_retired_storage else "absent",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def test_fresh_issue_sdk_cache_import_needs_no_service_or_retired_storage():
    result = _fresh_issue_sdk_cache_import()
    assert result.returncode == 0, result.stderr
    assert result.stdout == result.stderr == ""


def test_fresh_import_check_rejects_restored_actual_retired_module():
    result = _fresh_issue_sdk_cache_import(restore_retired_storage=True)
    assert result.returncode == 1, result.stderr
    assert result.stdout == ""
    assert (
        "AssertionError: retired_storage_module_present:aware_issue_runtime.local_json_state"
        in result.stderr
    )


@pytest.fixture
def inputs(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "storage_successor_original_fixture",
        Path(__file__).with_name("test_governed_draft.py"),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fixture = module.context.__wrapped__(tmp_path, monkeypatch)
    yield next(fixture)
    monkeypatch.undo()
    with pytest.raises(StopIteration):
        next(fixture)


@pytest.mark.parametrize("stale_issue", [False, True])
def test_genuine_successor_composition_preserves_sources_and_disposes_inputs(
    inputs, stale_issue
):
    root, manifest, issue, kwargs = inputs
    original_issue, original_manifest = issue.read_bytes(), manifest.read_bytes()
    guard = kwargs["issue_provider"].retain_draft_inputs(
        attempt_ref="storage-successor:actual-owners",
        client_intent_id=kwargs["client_intent_id"],
        protocol_target=kwargs["protocol_draft_target"],
        physical_plan=kwargs["physical_package_plan"],
    )
    if stale_issue:
        kwargs = {**kwargs, "expected_issue_sha256": "sha256:" + "0" * 64}
    manager = open_governed_specification_draft(**kwargs, input_custody=guard)
    if stale_issue:
        with pytest.raises(SpecificationOperationError):
            manager.__enter__()
        assert not (root / "customer/specs/widget").exists()
    else:
        with manager as client:
            result = client.create_draft(kwargs["request"])
            assert result.evidence.package_outcome == "published"
            assert result.evidence.completion_verified
            assert client.observe(SpecificationObserveRequest()) == result.observation
    cleanup = manager.observe_draft_cleanup()
    assert cleanup.input_custody.attempt_ref == "storage-successor:actual-owners"
    assert cleanup.input_custody.physical.owner_cleanup_outcome == "completed"
    assert cleanup.protocol_owner_attempted is True
    assert cleanup.protocol_owner_outcome == "completed"
    assert issue.read_bytes() == original_issue
    assert manifest.read_bytes() == original_manifest
    assert (root / "unrelated.txt").read_bytes() == b"untouched dirty work\n"
    descriptors = []
    for entry in Path("/proc/self/fd").iterdir():
        try:
            target = entry.readlink()
        except FileNotFoundError:
            continue
        if target == root or root in target.parents:
            descriptors.append(entry.name)
    assert descriptors == []
