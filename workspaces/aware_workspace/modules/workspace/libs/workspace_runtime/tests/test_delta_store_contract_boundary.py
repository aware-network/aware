"""Neutral evidence extraction without changing storage or issuer authority."""

from __future__ import annotations

import ast
import dataclasses
import hashlib
import importlib
import json
import pickle
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[7]
ROOT = "workspaces/aware_workspace/modules/workspace/libs/workspace_runtime"
PACKAGE = ROOT + "/aware_workspace_runtime"
LEDGER = json.loads(
    (
        REPO
        / "docs/reports/workspace-delta-store-neutral-contract-inputs-20261010.json"
    ).read_text(encoding="utf-8")
)
NAMES = tuple(LEDGER["neutral_exports"])


def _original(relative_path):
    body = subprocess.check_output(
        ["git", "show", LEDGER["preimage_revision"] + ":" + relative_path],
        cwd=REPO,
    )
    assert hashlib.sha256(body).hexdigest() == LEDGER["inputs"][relative_path]["sha256"]
    return ast.parse(body)


def _name(node):
    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        return node.name
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
        return node.targets[0].id
    return None


def _without_imports(tree, excluded=()):
    return ast.dump(
        ast.Module(
            body=[
                node
                for node in tree.body
                if not isinstance(node, (ast.Import, ast.ImportFrom))
                and _name(node) not in excluded
            ],
            type_ignores=[],
        ),
        include_attributes=False,
    )


@pytest.mark.parametrize("name", NAMES)
def test_neutral_declaration_is_exact_original_ast(name):
    original = _original(PACKAGE + "/repository_delta_store.py")
    current = ast.parse(
        (REPO / PACKAGE / "repository_delta_store_contract.py").read_bytes()
    )
    before = next(node for node in original.body if _name(node) == name)
    after = next(node for node in current.body if _name(node) == name)
    assert ast.dump(before, include_attributes=False) == ast.dump(
        after, include_attributes=False
    )


def test_complete_physical_algorithm_is_unchanged():
    path = PACKAGE + "/repository_delta_store.py"
    before = _original(path)
    destination = "workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter/repository_delta_store.py"
    after = ast.parse((REPO / destination).read_bytes())
    assert _without_imports(before, NAMES) == _without_imports(after)
    assert all(_name(node) not in NAMES for node in after.body)
    assert (REPO / destination).stat().st_mode & 0o777 == LEDGER["inputs"][path]["mode"]


@pytest.mark.parametrize(
    "filename",
    (
        "complete_scope_observation.py",
    ),
)
def test_consumer_changes_are_import_only(filename):
    path = PACKAGE + "/" + filename
    before = _original(path)
    after = ast.parse((REPO / path).read_bytes())
    assert _without_imports(before) == _without_imports(after)
    assert (REPO / path).stat().st_mode & 0o777 == LEDGER["inputs"][path]["mode"]


@pytest.mark.parametrize("relative_path, digest", tuple(LEDGER["preserved"].items()))
def test_supplier_identity_is_preserved(relative_path, digest):
    assert hashlib.sha256((REPO / relative_path).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize("name", NAMES)
def test_evidence_import_does_not_load_the_physical_store_or_other_owners(name):
    code = f"""
import importlib.abc, importlib, sys
sys.path[:0] = [{str(REPO / ROOT)!r}]
allowed = {{'aware_workspace_runtime', 'aware_workspace_runtime.repository_delta_store_contract'}}
class Guard(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith('aware_') and fullname not in allowed:
            raise ImportError('physical_or_foreign_import:' + fullname)
sys.meta_path.insert(0, Guard())
runtime = importlib.import_module('aware_workspace_runtime')
contract = importlib.import_module('aware_workspace_runtime.repository_delta_store_contract')
assert getattr(runtime, {name!r}) is getattr(contract, {name!r})
assert set(n for n in sys.modules if n.startswith('aware_')) <= allowed
assert sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode
"""
    result = subprocess.run(
        [sys.executable, "-I", "-S", "-B", "-c", code],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("name", NAMES)
def test_original_store_alias_and_root_resolve_one_neutral_object(name):
    runtime = importlib.import_module("aware_workspace_runtime")
    store = importlib.import_module("aware_workspace_runtime.repository_delta_store")
    contract = importlib.import_module(
        "aware_workspace_runtime.repository_delta_store_contract"
    )
    assert getattr(runtime, name) is getattr(store, name) is getattr(contract, name)


def test_root_mapping_changes_only_the_fifteen_neutral_targets():
    before = _original(PACKAGE + "/__init__.py")
    after = ast.parse((REPO / PACKAGE / "__init__.py").read_bytes())

    def groups(tree):
        return next(
            ast.literal_eval(node.value)
            for node in tree.body
            if isinstance(node, ast.Assign) and _name(node) == "_EXPORT_GROUPS"
        )

    before_groups, after_groups = groups(before), groups(after)
    prior_names = before_groups.pop("repository_delta_store")
    assert set(prior_names) == set(NAMES) | {"WorkspaceRepositoryDeltaStore"}
    assert "repository_delta_store" not in after_groups
    assert set(after_groups.pop("repository_delta_store_contract")) == set(NAMES)
    assert before_groups == after_groups
    # Besides the admitted group split, the initializer is byte-structure equivalent.
    for tree in (before, after):
        tree.body = [node for node in tree.body if _name(node) != "_EXPORT_GROUPS"]
    before_all = next(node for node in before.body if _name(node) == "__all__")
    before_all.value.elts = [node for node in before_all.value.elts if ast.literal_eval(node) != "WorkspaceRepositoryDeltaStore"]
    assert ast.dump(before, include_attributes=False) == ast.dump(
        after, include_attributes=False
    )


def test_detached_evidence_is_immutable_and_legacy_pickle_coordinates_still_resolve():
    from aware_workspace_runtime.repository_delta_store_contract import (
        WorkspaceRepositoryDeltaStoreMetrics,
        WorkspaceRepositoryDeltaStoreSnapshot,
    )

    metrics = WorkspaceRepositoryDeltaStoreMetrics(*range(9))
    snapshot = WorkspaceRepositoryDeltaStoreSnapshot(
        "repository:example", 1, 2, 3, 4, metrics
    )
    assert len(dataclasses.fields(metrics)) == 9
    assert len(dataclasses.fields(snapshot)) == 6
    for value in (metrics, snapshot):
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(value, dataclasses.fields(value)[0].name, "changed")
        payload = pickle.dumps(value, protocol=0)
        assert pickle.loads(payload) == value
        legacy = payload.replace(
            b"aware_workspace_runtime.repository_delta_store_contract",
            b"aware_workspace_runtime.repository_delta_store",
        )
        assert legacy != payload
        restored = pickle.loads(legacy)
        assert restored == value and type(restored) is type(value)
        assert not any(
            hasattr(restored, name)
            for name in (
                "resolve_body",
                "record_body",
                "observe",
                "publish",
                "release",
            )
        )


@pytest.mark.parametrize(
    "name",
    (
        "WorkspaceRepositoryDeltaStoreError",
        "WorkspaceRepositoryDeltaStoreCapacityError",
        "WorkspaceRepositoryDeltaStoreCorrupt",
    ),
)
def test_error_hierarchy_and_original_serialization_coordinate_are_preserved(name):
    contract = importlib.import_module(
        "aware_workspace_runtime.repository_delta_store_contract"
    )
    error = getattr(contract, name)("original failure")
    assert isinstance(error, contract.WorkspaceRepositoryDeltaStoreError)
    payload = pickle.dumps(error, protocol=0)
    legacy = payload.replace(
        b"aware_workspace_runtime.repository_delta_store_contract",
        b"aware_workspace_runtime.repository_delta_store",
    )
    assert legacy != payload
    restored = pickle.loads(legacy)
    assert type(restored) is type(error) and restored.args == error.args


@pytest.mark.parametrize("substitute", ("duck", "subclass", "wrong_binding"))
async def test_source_observer_still_refuses_nonoriginal_store_before_root_open(
    tmp_path, monkeypatch, substitute
):
    from aware_workspace_runtime import (
        FileSystemIndexObservationProvider,
        SourceObservationUnavailable,
        WorkspaceRepositoryBinding,
        WorkspaceRepositoryObservationSession,
        WorkspaceSourceObservationRuntime,
    )
    from aware_workspace_sdk.repository_delta_retention import (
        WorkspaceRepositoryDeltaRetentionClient,
    )
    from test_repository_delta_retention_client import retained

    root = tmp_path / "repository"
    root.mkdir()
    binding = WorkspaceRepositoryBinding(root)
    session = WorkspaceRepositoryObservationSession(
        binding=binding,
        provider=FileSystemIndexObservationProvider(binding=binding),
    )
    await session.start(background=False)
    try:
        if substitute == "duck":

            class Duck:
                repository_binding_ref = binding.binding_key

            store = Duck()
        else:

            class Derived(WorkspaceRepositoryDeltaRetentionClient):
                pass

            store = object.__new__(Derived) if substitute == "subclass" else retained(
                repository_binding_ref="other", state_root=tmp_path / "state",
            )

        def forbidden_open(*args, **kwargs):
            pytest.fail("Rejected store reached retained root IO")

        with monkeypatch.context() as patch:
            patch.setattr(
                "aware_workspace_runtime.source_observation.os.open", forbidden_open
            )
            with pytest.raises(
                SourceObservationUnavailable, match="retention_binding_mismatch"
            ):
                WorkspaceSourceObservationRuntime(session=session, store=store)
    finally:
        await session.stop()
