"""Original persistence extraction, not new authority or installed closure."""

from __future__ import annotations

import ast
import hashlib
import importlib
import json
import subprocess
from pathlib import Path

import pytest

ROOT = next(
    p for p in Path(__file__).resolve().parents if (p / "aware.repo.toml").is_file()
)
LEDGER = json.loads(
    (
        ROOT
        / "docs/reports/workspace-mutation-store-fs-separation-inputs-20261010.json"
    ).read_text()
)


def _original(path):
    raw = subprocess.check_output(
        ["git", "show", LEDGER["preimage_revision"] + ":" + path], cwd=ROOT
    )
    assert hashlib.sha256(raw).hexdigest() == LEDGER["inputs"][path]["sha256"]
    return raw


def test_one_physical_body_preserves_every_statement_and_original_mode():
    original = ast.parse(_original(LEDGER["source"]))
    for node in original.body:
        if isinstance(node, ast.ImportFrom) and node.level == 1:
            node.level = 0
            node.module = "aware_workspace_runtime." + node.module
    current = ROOT / LEDGER["target"]
    assert not (ROOT / LEDGER["source"]).exists()
    assert current.stat().st_mode & 0o777 == LEDGER["inputs"][LEDGER["source"]]["mode"]
    assert ast.dump(
        ast.parse(current.read_text()), include_attributes=False
    ) == ast.dump(original, include_attributes=False)


def test_runtime_root_changes_only_the_seven_physical_exports():
    path = "workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/__init__.py"
    original = ast.parse(_original(path))
    for node in original.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "_EXPORT_GROUPS" for t in node.targets
        ):
            pairs = [
                (key, value)
                for key, value in zip(node.value.keys, node.value.values, strict=True)
                if ast.literal_eval(key) != "repository_mutation_store"
            ]
            node.value.keys = [key for key, _ in pairs]
            node.value.values = [value for _, value in pairs]
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets
        ):
            node.value.elts = [
                value
                for value in node.value.elts
                if ast.literal_eval(value) not in LEDGER["export_migration"]
            ]
    assert ast.dump(
        ast.parse((ROOT / path).read_text()), include_attributes=False
    ) == ast.dump(original, include_attributes=False)


@pytest.mark.parametrize("path", sorted(LEDGER["preserved"]))
def test_coordinator_neutral_ports_writer_and_identity_held_source_stay_original(path):
    assert (
        hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        == LEDGER["preserved"][path]
    )


def test_coordinator_keeps_original_structural_port_without_fs_import():
    from aware_workspace_runtime.repository_mutation import (
        WorkspaceRepositoryMutationCoordinator,
        WorkspaceRepositoryMutationResultStore,
    )

    assert (
        WorkspaceRepositoryMutationResultStore.__module__
        == WorkspaceRepositoryMutationCoordinator.__module__
    )
    source = (
        ROOT
        / "workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/repository_mutation.py"
    ).read_text()
    assert "aware_workspace_fs_adapter" not in source
    assert "repository_mutation_store" not in source


def test_explicit_fs_module_owns_all_migrated_names():
    store = importlib.import_module(
        "aware_workspace_fs_adapter.repository_mutation_store"
    )
    assert set(store.__all__) == set(LEDGER["export_migration"])
    for name in LEDGER["export_migration"]:
        assert getattr(store, name) is not None
    assert store.WorkspaceRepositoryMutationStore.__module__ == store.__name__


@pytest.mark.parametrize(
    "path",
    [
        "workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_repository_mutation.py",
        "workspaces/aware_dev/modules/dev/services/local_dev/aware_local_dev_service/workspace_runtime_adapter.py",
    ],
)
def test_physical_composition_callers_only_change_store_imports(path):
    original = ast.parse(_original(path))
    current = ast.parse((ROOT / path).read_text())
    selected = set(LEDGER["export_migration"])

    def separate_imports(tree, *, migrate):
        imports = set()
        statements = []
        for node in tree.body:
            if isinstance(node, ast.ImportFrom):
                for name in node.names:
                    module = node.module
                    if (
                        migrate
                        and module == "aware_workspace_runtime"
                        and name.name in selected
                    ):
                        module = "aware_workspace_fs_adapter.repository_mutation_store"
                    imports.add(("from", node.level, module, name.name, name.asname))
            elif isinstance(node, ast.Import):
                for name in node.names:
                    imports.add(("import", name.name, name.asname))
            else:
                statements.append(ast.dump(node, include_attributes=False))
        return imports, statements

    assert separate_imports(current, migrate=False) == separate_imports(
        original, migrate=True
    )
