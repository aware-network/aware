"""Descriptive lowering and exact signature parity, not an executable owner port."""

from __future__ import annotations

import ast
import hashlib
import json
import stat
import subprocess
import sys
import tomllib
from functools import lru_cache
from pathlib import Path

import pytest
from tree_sitter_aware.neutral_ir import parse_neutral_aware_source
from tree_sitter_aware.ontology_meaning import meaning_value_to_json
from tree_sitter_aware.ontology_meaning_resolver import (
    OntologyMeaningPackageInput,
    resolve_ontology_meaning,
)

ROOT = next(
    p for p in Path(__file__).resolve().parents if (p / "aware.repo.toml").is_file()
)
LEDGER = json.loads(
    (
        ROOT / "docs/reports/workspace-delta-retention-authored-inputs-20261010.json"
    ).read_text()
)
FIXTURES = Path(__file__).parent / "fixtures"
SOURCE = FIXTURES / "workspace_delta_retention_values.aware"
SIGNATURES = FIXTURES / "workspace_delta_retention_signatures.pyi"
SDK = ROOT / "workspaces/aware_workspace/modules/workspace/sdks/workspace/aware"
CONTRACT = (
    ROOT / "docs/reports/workspace-delta-retention-owner-port-contract-20261010.md"
)
PREFIX = "WorkspaceRepositoryDeltaRetention"
OBSERVATION = PREFIX + "Observation"
EVIDENCE = PREFIX + "RefusalEvidence"
PHASES = ("allocated", "initializing", "active", "refused", "released")
CODES = (
    "retention_not_issued",
    "retention_owner_mismatch",
    "retention_binding_mismatch",
    "retention_process_mismatch",
    "retention_not_active",
    "retention_initializer_spent",
    "retention_storage_initialization_refused",
    "retention_supplier_unavailable",
)
MEMBERS = (
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
)


def classes():
    return {
        n.name: n
        for n in ast.parse(SIGNATURES.read_text()).body
        if isinstance(n, ast.ClassDef)
    }


def lower(source=None):
    manifest = tomllib.loads((SDK / "aware.sdk.toml").read_text())["sdk"]
    path = "/qualification/workspace/delta-retention-values.aware"
    doc = parse_neutral_aware_source(
        SOURCE.read_text() if source is None else source, source_path=path
    )
    return resolve_ontology_meaning(
        (
            OntologyMeaningPackageInput(
                package_name=manifest["package_name"],
                fqn_prefix=manifest["fqn_prefix"],
                sources_root="/qualification/workspace",
                dependencies=(),
                documents=(doc,),
                namespace_by_source_path=((path, ""),),
            ),
        ),
        selected_package_names=frozenset({manifest["package_name"]}),
    )


@lru_cache
def meaning():
    return lower()


def fields(name):
    return {
        n.target.id: n.annotation
        for n in classes()[name].body
        if isinstance(n, ast.AnnAssign)
    }


def spelling(annotation):
    if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
        assert ast.unparse(annotation.right) == "None"
        return spelling(annotation.left) + "?"
    if isinstance(annotation, ast.Name):
        return {"str": "String", "int": "Int"}.get(annotation.id, annotation.id)
    assert isinstance(annotation, ast.Subscript)
    if ast.unparse(annotation.value) == "tuple":
        assert ast.unparse(annotation.slice.elts[1]) == "..."
        return spelling(annotation.slice.elts[0]) + "[]"
    assert ast.unparse(annotation.value) == "Literal"
    return PREFIX + (
        "Phase" if annotation.slice.elts[0].value == "allocated" else "RefusalCode"
    )


def assert_parity(name, lowered):
    entries = {
        e.fqn.rsplit(".", 1)[1]: meaning_value_to_json(e.payload)
        for e in lowered.entries
        if e.kind == "member"
        and e.fqn.rsplit(".", 1)[0] == "aware_workspace_sdk." + name
    }
    assert set(entries) == set(fields(name))
    for i, (field, annotation) in enumerate(fields(name).items()):
        expected = spelling(annotation)
        member = entries[field]
        assert member["position"] == i
        assert member["type_expression"] == expected
        assert member["nullable"] is expected.endswith("?")
        assert member["collection"] is expected.removesuffix("?").endswith("[]")
        assert member["identity_key"] is False
        if not member["primitive"]:
            assert member["target_fqn"] is not None
            assert member["target_symbol_kind"] in {"class_def", "enum_def"}


@pytest.mark.parametrize("path", tuple(LEDGER["inputs"]))
def test_all_inputs_match_current_committed_bytes_and_modes(path):
    p = ROOT / path
    pin = LEDGER["inputs"][path]
    assert hashlib.sha256(p.read_bytes()).hexdigest() == pin["sha256"]
    assert stat.S_IMODE(p.stat().st_mode) == pin["mode"]
    assert (
        subprocess.check_output(
            ["git", "show", LEDGER["revision"] + ":" + path], cwd=ROOT
        )
        == p.read_bytes()
    )
    assert (
        subprocess.check_output(
            ["git", "ls-tree", LEDGER["revision"], "--", path], cwd=ROOT, text=True
        ).split()[0]
        == pin["git_mode"]
    )


@pytest.mark.parametrize("name", (OBSERVATION, EVIDENCE))
def test_all_value_fields_order_nullability_and_collections_lower(name):
    assert_parity(name, meaning())
    symbol = next(
        e
        for e in meaning().entries
        if e.kind == "symbol" and e.fqn == "aware_workspace_sdk." + name
    )
    assert meaning_value_to_json(symbol.payload)["inline_value"] is True


@pytest.mark.parametrize(
    ("name", "options"), ((PREFIX + "Phase", PHASES), (PREFIX + "RefusalCode", CODES))
)
def test_exact_finite_enum_order_lowers(name, options):
    enums = sorted(
        (
            e
            for e in meaning().entries
            if e.kind == "enum_option"
            and e.fqn.rsplit(".", 1)[0] == "aware_workspace_sdk." + name
        ),
        key=lambda e: meaning_value_to_json(e.payload)["position"],
    )
    assert tuple(e.fqn.rsplit(".", 1)[1] for e in enums) == options


def test_observation_is_exact_accepted_six_field_contract():
    text = CONTRACT.read_text()
    block = (
        text.split("The detached observation has exactly these fields:", 1)[1]
        .split("```python\n", 1)[1]
        .split("```", 1)[0]
    )
    accepted = {n.target.id: ast.dump(n.annotation) for n in ast.parse(block).body}
    assert {n: ast.dump(a) for n, a in fields(OBSERVATION).items()} == accepted
    assert len(accepted) == 6


@pytest.mark.parametrize("code", CODES)
def test_refusal_vocabulary_is_exact_accepted_owner_boundary(code):
    assert f"`{code}`" in CONTRACT.read_text()
    annotation = fields(EVIDENCE)["code"]
    assert code in tuple(x.value for x in annotation.slice.elts)


def methods(name):
    return {n.name: n for n in classes()[name].body if isinstance(n, ast.FunctionDef)}


def original_methods():
    tree = ast.parse((ROOT / LEDGER["roles"]["physical_store"]).read_text())
    cls = next(
        n
        for n in tree.body
        if isinstance(n, ast.ClassDef)
        and n.name == "WorkspaceRepositoryDelta" + "Store"
    )
    return {n.name: n for n in cls.body if isinstance(n, ast.FunctionDef)}


@pytest.mark.parametrize("member", MEMBERS)
def test_each_neutral_member_preserves_original_signature_and_decorator(member):
    original = original_methods()[member]
    for owner in (PREFIX + "Client", "FilesystemRepositoryDeltaRetentionOwner"):
        target = methods(owner)[member]
        assert ast.dump(target.args) == ast.dump(original.args)
        assert ast.dump(target.returns) == ast.dump(original.returns)
        assert [ast.dump(d) for d in target.decorator_list] == [
            ast.dump(d) for d in original.decorator_list
        ]


@pytest.mark.parametrize(
    ("owner", "method"),
    (
        (PREFIX + "Client", "initialize_delta_retention"),
        ("FilesystemRepositoryDeltaRetentionOwner", "initialize_original_store"),
    ),
)
def test_initializer_preserves_all_original_args_defaults_except_factory_state_root(
    owner, method
):
    original = original_methods()["__init__"].args
    target = methods(owner)[method].args
    expected = {
        a.arg: (ast.dump(a.annotation), None if default is None else ast.dump(default))
        for a, default in zip(original.kwonlyargs, original.kw_defaults, strict=True)
        if a.arg != "state_root"
    }
    observed = {
        a.arg: (ast.dump(a.annotation), None if default is None else ast.dump(default))
        for a, default in zip(target.kwonlyargs, target.kw_defaults, strict=True)
    }
    assert observed == expected
    assert not target.vararg and not target.kwarg
    assert [a.arg for a in target.args] == ["self"]


@pytest.mark.parametrize(
    ("owner", "names"),
    (
        (
            PREFIX + "Factory",
            ("filesystem", "allocate_delta_retention", "retain_delta_retention"),
        ),
        (
            PREFIX + "Client",
            (
                "initialize_delta_retention",
                "verify_repository_binding",
                "observe_retention",
                "release_retention",
                *MEMBERS,
            ),
        ),
        (
            "FilesystemRepositoryDeltaRetentionFactory",
            ("verify_original_factory", "allocate_owner", "retain_owner"),
        ),
        (
            "FilesystemRepositoryDeltaRetentionOwner",
            (
                "verify_original_owner",
                "initialize_original_store",
                "retire_owner",
                *MEMBERS,
            ),
        ),
    ),
)
def test_exact_fixed_port_set_without_constructor_or_generic_dispatch(owner, names):
    assert tuple(methods(owner)) == names
    for method in methods(owner).values():
        assert (
            len(method.body) == 1
            and isinstance(method.body[0], ast.Expr)
            and method.body[0].value.value is Ellipsis
        )
        assert not method.args.vararg and not method.args.kwarg
        assert not {a.arg for a in method.args.args + method.args.kwonlyargs} & {
            "authorized",
            "provider",
            "callback",
            "validated",
            "method_name",
            "may_cleanup",
        }


def test_selection_and_adoption_preserve_location_and_exact_original_coordinate():
    sdk = methods(PREFIX + "Factory")
    assert [ast.unparse(d) for d in sdk["filesystem"].decorator_list] == ["classmethod"]
    assert [
        (a.arg, ast.unparse(a.annotation)) for a in sdk["filesystem"].args.kwonlyargs
    ] == [("state_root", "Path")]
    for owner, method in (
        (PREFIX + "Factory", "retain_delta_retention"),
        ("FilesystemRepositoryDeltaRetentionFactory", "retain_owner"),
    ):
        args = methods(owner)[method].args
        assert [
            (a.arg, None if a.annotation is None else ast.unparse(a.annotation))
            for a in args.args
        ] == [("self", None), ("original_store", "object")]
        assert [(a.arg, ast.unparse(a.annotation)) for a in args.kwonlyargs] == [
            ("expected_binding_ref", "str")
        ]


def test_refusal_projection_preserves_nullable_evidence_without_serializing_live_cause():
    assert tuple(fields(EVIDENCE)) == ("code", "observation")
    assert ast.unparse(fields(EVIDENCE)["observation"]) == OBSERVATION + " | None"
    assert "chained original error" in " ".join(CONTRACT.read_text().split())
    assert "live exception cause" in SOURCE.read_text()


def test_actual_lowering_is_deterministic_with_exact_source_provenance():
    first, second = lower(), lower()
    assert first.canonical_bytes() == second.canonical_bytes()
    assert first.canonical_sha256 == second.canonical_sha256
    assert {p.source_sha256 for e in first.entries for p in e.provenance} == {
        hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    }
    assert all(e.fqn.startswith("aware_workspace_sdk.") for e in first.entries)


def test_only_descriptive_roots_lower_not_factories_clients_or_owner_claims():
    symbols = {e.fqn.rsplit(".", 1)[1] for e in meaning().entries if e.kind == "symbol"}
    assert symbols == {OBSERVATION, EVIDENCE, PREFIX + "Phase", PREFIX + "RefusalCode"}
    for name in (OBSERVATION, EVIDENCE):
        assert not set(fields(name)) & {
            "authorized",
            "admitted",
            "may_write",
            "may_cleanup",
            "store",
            "owner",
            "claim",
            "thread_id",
            "ledger_complete",
        }


@pytest.mark.parametrize(
    ("before", "after", "name"),
    (
        (
            "repository_binding_ref String?",
            "repository_binding_ref String",
            OBSERVATION,
        ),
        ("diagnostics String[]", "diagnostics String", OBSERVATION),
        ("    original_process_id Int\n", "", OBSERVATION),
        ("original_process_id Int", "original_process_id Bool", OBSERVATION),
        (
            "WorkspaceRepositoryDeltaRetentionObservation?",
            "WorkspaceRepositoryDeltaRetentionObservation",
            EVIDENCE,
        ),
    ),
)
def test_missing_type_collection_and_nullability_drift_cannot_pass(before, after, name):
    source = SOURCE.read_text()
    assert before in source
    with pytest.raises(AssertionError):
        assert_parity(name, lower(source.replace(before, after, 1)))


def test_unknown_owner_type_is_refused_by_genuine_resolver():
    source = SOURCE.read_text().replace(
        "retention_ref String", "retention_ref ForgedOwnerClaim", 1
    )
    with pytest.raises(
        ValueError, match="ForgedOwnerClaim.*does not resolve exactly once"
    ):
        lower(source)


def test_fixture_is_not_registered_or_installed_and_does_not_change_original_references():
    manifest = tomllib.loads((SDK / "aware.sdk.toml").read_text())
    assert manifest["build"]["sources_dir"] == "."
    assert SOURCE.parent != SDK
    assert not (SDK / SOURCE.name).exists()
    assert not (
        Path(__file__).parents[1] / "aware_workspace_sdk/repository_delta_retention"
    ).exists()
    assert not (
        Path(__file__).parents[1] / "aware_workspace_sdk/repository_delta_retention.py"
    ).exists()
    pattern = "WorkspaceRepositoryDelta" + "Store|repository_delta" + "_store"
    scanned = subprocess.check_output(
        ["rg", "-l", pattern, "--glob", "*.py", "workspaces"], cwd=ROOT, text=True
    ).splitlines()
    excluded = "workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_delta_retention_owner_port_contract.py"
    assert (
        sorted(p for p in scanned if p != excluded)
        == LEDGER["original_reference_paths"]
    )


def test_fresh_lowering_does_not_import_sdk_runtime_physical_or_foreign_owners():
    script = """
import importlib.util, json, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("qualification_probe", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
meaning = module.lower()
blocked = ("aware_workspace_sdk", "aware_workspace_runtime", "aware_workspace_fs_adapter", "aware_workspace_service_sdk_adapter", "aware_issue", "aware_environment", "aware_local_dev", "aware_workspace_ontology")
print(json.dumps({"digest": meaning.canonical_sha256, "imports": [n for n in sys.modules if n.startswith(blocked)]}))
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(Path(__file__))],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    output = json.loads(result.stdout)
    assert output["digest"] == meaning().canonical_sha256
    assert output["imports"] == []
