"""Owner-port preparation/currentness, not implemented retention authority."""

from __future__ import annotations

import ast
import hashlib
import json
import stat
import subprocess
import tomllib
from pathlib import Path

import pytest

REPO = next(
    p for p in Path(__file__).resolve().parents if (p / "aware.repo.toml").is_file()
)
ROOT = "workspaces/aware_workspace/modules/workspace"
RUNTIME = ROOT + "/libs/workspace_runtime/aware_workspace_runtime"
SDK = ROOT + "/sdks/workspace/python/public/aware_workspace_sdk"
FS = ROOT + "/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter"
PRODUCER = (
    "workspaces/aware_network/modules/environment/libs/protected_store_delivery_runtime/"
    "aware_environment_protected_store_delivery_runtime/command_entry.py"
)
LEDGER = json.loads(
    (
        REPO / "docs/reports/workspace-delta-retention-owner-port-inputs-20261010.json"
    ).read_text()
)
REPORT = (
    REPO / "docs/reports/workspace-delta-retention-owner-port-contract-20261010.md"
).read_text()


def _tree(path):
    return ast.parse((REPO / path).read_bytes())


def _function(path, name):
    return next(
        n
        for n in _tree(path).body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name
    )


@pytest.mark.parametrize("path, pin", tuple(LEDGER["inputs"].items()))
def test_all_captured_inputs_are_committed_current_and_mode_bound(path, pin):
    current = REPO / path
    body = current.read_bytes()
    assert hashlib.sha256(body).hexdigest() == pin["sha256"]
    assert stat.S_IMODE(current.stat().st_mode) == pin["mode"]
    original = subprocess.check_output(
        ["git", "show", LEDGER["revision"] + ":" + path], cwd=REPO
    )
    assert original == body


def test_reference_scan_closure_and_caller_categories():
    result = subprocess.check_output(
        ["rg", "-l", LEDGER["reference_pattern"], "--glob", "*.py", "workspaces"],
        cwd=REPO,
        text=True,
    )
    observed = set(result.splitlines()) - set(LEDGER["excluded_reference_paths"])
    assert observed == set(LEDGER["reference_paths"])
    assert len(observed) == LEDGER["reference_count"] == 26
    assert sum("/tests/" in p for p in observed) == 14
    assert sum("/benchmarks/" in p for p in observed) == 1
    assert sum("/tests/" not in p and "/benchmarks/" not in p for p in observed) == 11
    assert PRODUCER in observed


def test_three_exact_store_checks_are_identified_without_replacing_them():
    gates = []
    for path in (
        RUNTIME + "/source_observation.py",
        RUNTIME + "/direct_command_composition.py",
    ):
        for node in ast.walk(_tree(path)):
            if isinstance(node, ast.Compare) and any(
                isinstance(value, ast.Name)
                and value.id == "WorkspaceRepositoryDeltaStore"
                for value in node.comparators
            ):
                assert len(node.ops) == 1 and isinstance(node.ops[0], ast.IsNot)
                assert (
                    isinstance(node.left, ast.Call)
                    and ast.unparse(node.left.func) == "type"
                )
                gates.append((path, ast.unparse(node.left.args[0])))
    assert gates == [
        (RUNTIME + "/source_observation.py", "store"),
        (RUNTIME + "/direct_command_composition.py", "source_resources[1]"),
        (RUNTIME + "/direct_command_composition.py", "resources[1]"),
    ]


def test_store_member_inventory_contains_only_one_physical_location_accessor():
    tree = _tree(RUNTIME + "/repository_delta_store.py")
    original = next(
        n
        for n in tree.body
        if isinstance(n, ast.ClassDef) and n.name == "WorkspaceRepositoryDeltaStore"
    )
    members = {
        n.name: ast.unparse(n.args)
        for n in original.body
        if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")
    }
    assert members == LEDGER["physical_members"]
    assert len(members) == 13
    assert set(members) - {"store_root"} == {
        "repository_binding_ref",
        "snapshot",
        "record_body",
        "record_bodies",
        "contains_body",
        "resolve_body",
        "record_capture",
        "resolve_capture",
        "retained_captures",
        "record_delta",
        "resolve_delta",
        "retained_deltas",
    }
    for name in set(members) - {"store_root", "repository_binding_ref"}:
        assert "client." + name + "(" in REPORT


def test_original_producer_retains_delta_before_effectful_initializer():
    body = _function(PRODUCER, "_acquire_original_workspace_host_sources").body
    allocation = next(
        i
        for i, n in enumerate(body)
        if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == "record.delta"
    )
    initializer = next(
        i
        for i, n in enumerate(body)
        if isinstance(n, ast.Expr)
        and isinstance(n.value, ast.Call)
        and ast.unparse(n.value.func) == "WorkspaceRepositoryDeltaStore.__init__"
    )
    assert allocation < initializer
    assert (
        ast.unparse(body[allocation].value)
        == "object.__new__(WorkspaceRepositoryDeltaStore)"
    )
    assert ast.unparse(body[initializer].value.args[0]) == "record.delta"
    assert "The caller records that client before initialization." in REPORT
    assert "terminally refuses that initialization" in REPORT


def test_original_native_readback_requires_exact_retained_pair_member():
    body = _function(PRODUCER, "_workspace_host_native_readback_record")
    comparisons = [ast.unparse(n) for n in ast.walk(body) if isinstance(n, ast.Compare)]
    assert "pair.source_resources[1] is not record.delta" in comparisons
    assert "pair.source_resources[0] is not record.session" in comparisons
    assert "pair is not _ACTIVE_WORKSPACE_PAIR" in comparisons
    assert "preserves `is` correspondence" in REPORT
    assert "SDK verification" in REPORT


def test_existing_read_protocols_are_not_nominal_admission():
    resolution = _tree(RUNTIME + "/repository_delta_resolution.py")
    index = next(
        n
        for n in resolution.body
        if isinstance(n, ast.ClassDef) and n.name == "WorkspaceRepositoryDeltaIndex"
    )
    assert [ast.unparse(n) for n in index.bases] == ["Protocol"]
    assert {n.name for n in index.body if isinstance(n, ast.FunctionDef)} == {
        "repository_binding_ref",
        "retained_captures",
        "retained_deltas",
        "contains_body",
    }
    assert "must\nnot be silently redesigned as such" in REPORT


def test_original_lower_selection_pattern_is_explicit_not_public_registration():
    body = (REPO / FS / "repository_publication.py").read_text()
    assert "_CANDIDATE_PORT_TYPES.add(FilesystemRepositoryCandidatePort)" in body
    assert "no public type-registration operation" in REPORT
    assert "Type identity is necessary, not sufficient" in REPORT
    assert "Both original SDK and FS issuance are necessary" in REPORT


def test_contract_has_public_lifecycle_and_typed_failure_carriers():
    for signature in (
        "factory.allocate_delta_retention()",
        "factory.retain_delta_retention(",
        "client.initialize_delta_retention(",
        "client.verify_repository_binding(",
        "client.observe_retention()",
        "client.release_retention()",
    ):
        assert signature in REPORT
    for field in (
        "retention_ref: str",
        "repository_binding_ref: str | None",
        'phase: Literal["allocated", "initializing", "active", "refused", "released"]',
        "provider_generation: str",
        "original_process_id: int",
        "diagnostics: tuple[str, ...]",
    ):
        assert field in REPORT
    assert "WorkspaceRepositoryDeltaRetentionRefusal" in REPORT
    assert "after physical dispatch an exception cannot" in REPORT
    assert "no store effect occurred" in REPORT
    assert "process affinity, not thread affinity" in REPORT


def test_dependency_allocations_do_not_change_current_metadata():
    versions = {
        ROOT + "/sdks/workspace/python/public/pyproject.toml": "0.1.0",
        ROOT + "/libs/workspace_runtime/pyproject.toml": "0.1.1",
        ROOT + "/sdks/workspace/filesystem_adapter/python/pyproject.toml": "0.0.1",
    }
    for path, version in versions.items():
        data = tomllib.loads((REPO / path).read_text())
        assert data["project"]["version"] == version
    for target in (
        "SDK **0.2.0**",
        "runtime\n**0.2.0**",
        "FS adapter **0.1.0**",
        ">=0.2.0,<0.3.0",
        ">=0.1.0,<0.2.0",
    ):
        assert target in REPORT
    assert "not adopted metadata or compatibility PASS" in REPORT


def test_owner_refusal_codes_preserve_source_and_storage_failure_distinctions():
    for code in (
        "retention_not_issued",
        "retention_owner_mismatch",
        "retention_binding_mismatch",
        "retention_process_mismatch",
        "retention_not_active",
        "retention_initializer_spent",
        "retention_storage_initialization_refused",
        "retention_supplier_unavailable",
    ):
        assert "`" + code + "`" in REPORT
    assert 'SourceObservationUnavailable("retention_binding_mismatch")' in REPORT
    assert "Store errors keep their original types/causes." in REPORT


def test_target_ports_are_not_misreported_as_implemented():
    assert not (REPO / SDK / "repository_delta_retention").exists()
    assert not (REPO / SDK / "repository_delta_retention.py").exists()
    assert not (REPO / FS / "repository_delta_store.py").exists()
    assert (
        "target\ninterfaces, not available runtime or installed capabilities" in REPORT
    )
    assert "No runtime implementation, package change" in REPORT
