"""Physical source ownership and exact original-body parity, not installation."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path

import pytest

ROOT = next(
    p for p in Path(__file__).resolve().parents if (p / "aware.repo.toml").is_file()
)
LEDGER = json.loads(
    (
        ROOT
        / "docs/reports/workspace-sdk-service-source-extraction-inputs-20261010.json"
    ).read_text()
)
SDK = (
    ROOT
    / "workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk"
)
SERVICE = (
    ROOT
    / "workspaces/aware_workspace/modules/workspace/sdks/workspace/service_adapter/python/aware_workspace_service_sdk_adapter"
)


def _original(path):
    return subprocess.check_output(
        ["git", "show", LEDGER["preimage_revision"] + ":" + path], cwd=ROOT
    )


def _expected(body, source):
    mapped = re.sub(
        r"\baware_workspace_sdk\.(?!repository_publication(?:\b|\.))",
        "aware_workspace_service_sdk_adapter.",
        body,
    )
    if source.endswith("test_workspace_sdk_import_boundaries.py"):
        mapped = mapped.replace(
            "sdks/workspace/python/public", "sdks/workspace/service_adapter/python"
        )
        mapped = mapped.replace(
            '"aware_workspace_sdk"', '"aware_workspace_service_sdk_adapter"'
        )
    if source.endswith("test_workspace_service_operation_contract_inventory.py"):
        mapped = mapped.replace(
            "sdks/workspace/python/public/aware_workspace_sdk",
            "sdks/workspace/service_adapter/python/aware_workspace_service_sdk_adapter",
        )
    if Path(source).name in {
        "test_workspace_sdk_operation_catalog.py",
        "test_workspace_sdk_semantic_workflow_catalog.py",
        "test_workspace_sdk_session_submission.py",
    }:
        mapped = mapped.replace(
            '/ "aware_workspace_sdk"', '/ "aware_workspace_service_sdk_adapter"'
        )
    return mapped


@pytest.mark.parametrize("row", LEDGER["moves"], ids=lambda r: r["source"])
def test_original_body_is_moved_once_with_only_declared_namespace_changes(row):
    old = _original(row["source"])
    assert hashlib.sha256(old).hexdigest() == row["sha256"]
    assert not (ROOT / row["source"]).exists()
    target = ROOT / row["target"]
    assert target.stat().st_mode & 0o777 == row["mode"]
    expected = ast.dump(
        ast.parse(_expected(old.decode(), row["source"])), include_attributes=False
    )
    assert ast.dump(ast.parse(target.read_text()), include_attributes=False) == expected


@pytest.mark.parametrize("path", sorted(LEDGER["callers"]))
def test_actual_external_caller_preserves_original_body_and_neutral_imports(path):
    old = _original(path)
    assert hashlib.sha256(old).hexdigest() == LEDGER["callers"][path]["sha256"]
    assert ast.dump(
        ast.parse((ROOT / path).read_text()), include_attributes=False
    ) == ast.dump(ast.parse(_expected(old.decode(), path)), include_attributes=False)


@pytest.mark.parametrize("path", sorted(LEDGER["preserved"]))
def test_original_neutral_values_runtime_and_single_writer_are_unchanged(path):
    assert (
        hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        == LEDGER["preserved"][path]
    )


def test_core_contains_only_neutral_publication_and_no_service_forwarding():
    expected = {"__init__.py"} | {
        Path(path).relative_to(SDK.relative_to(ROOT)).as_posix()
        for path in LEDGER["preserved"]
        if path.startswith(SDK.relative_to(ROOT).as_posix() + "/")
        and path.endswith(".py")
    }
    assert {p.relative_to(SDK).as_posix() for p in SDK.rglob("*.py")} == expected
    for path in SDK.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            names = (
                [a.name for a in node.names]
                if isinstance(node, ast.Import)
                else [node.module]
                if isinstance(node, ast.ImportFrom) and node.module
                else []
            )
            assert not any(
                name.startswith("aware_workspace_service_sdk_adapter") for name in names
            )
    assert (SERVICE / "client.py").is_file()
    assert not (SDK / "client.py").exists()


def test_related_orm_and_stable_domain_identity_are_not_namespace_migrations():
    source = (SERVICE / "state/schema.py").read_text()
    assert "import aware_workspace_sdk_local_ontology_orm_models" in source
    assert (
        'sdk: str = "aware_workspace_sdk"'
        in (SERVICE / "features/session/submission_contracts.py").read_text()
    )
    assert LEDGER["source_only"] and not LEDGER["package_adoption"]
