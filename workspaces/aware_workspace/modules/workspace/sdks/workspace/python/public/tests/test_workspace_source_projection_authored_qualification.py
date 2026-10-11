"""Real descriptive lowering and fixed-port intake, not executed SDK authority."""

from __future__ import annotations

import ast
import hashlib
import json
import stat
import subprocess
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
WORKSPACE = "workspaces/aware_workspace/modules/workspace/"
RUNTIME = WORKSPACE + "libs/workspace_runtime/aware_workspace_runtime/"
SDK = ROOT / WORKSPACE / "sdks/workspace/aware"
FIXTURES = Path(__file__).parent / "fixtures"
SOURCE = FIXTURES / "workspace_source_projection_values.aware"
SIGNATURES = FIXTURES / "workspace_source_projection_signatures.pyi"
REPORT = (
    ROOT / "docs/reports/workspace-source-projection-authored-qualification-20261010.md"
)
LEDGER = json.loads(
    (
        ROOT / "docs/reports/workspace-source-projection-authored-inputs-20261010.json"
    ).read_text()
)
ROOTS = (
    "RepositoryObservationCoordinate",
    "WorkspaceRepositoryPhysicalEffect",
    "WorkspaceRepositoryMutationExecutionEvidence",
    "WorkspaceSourceProviderBinding",
    "WorkspaceSourceFileIdentity",
    "WorkspaceSourceObservation",
    "WorkspaceSourceProjectionRequest",
    "WorkspaceSourceProjectionBinding",
    "WorkspaceSourceProjectionPlanObservation",
    "WorkspaceSourceProjectionRetentionObservation",
    "WorkspaceSourceProjectionCleanupObservation",
    "WorkspaceSourceProjectionObservation",
    "WorkspaceSourceProjectionRefusalEvidence",
)
OPAQUE = (
    "WorkspaceSourceProjectionPlan",
    "WorkspaceSourceProjectionAdmission",
    "IssueStartProgressProjectionPlan",
    "IssueSourceProjectionAdmission",
    "IssueSourceProjectionConsumption",
)
PORTS = {
    "WorkspaceRepositorySourceProjectionClient": (
        "filesystem",
        "observe_source",
        "retain_projection_body",
        "prepare_source_projection",
        "observe_source_projection_plan",
        "verify_source_projection_plan",
        "enroll_issue_projection",
        "project_source",
        "observe_source_projection",
        "resolve_source_projection_receipt",
        "release_source_projection",
    ),
    "IssueStartProgressProjectionClient": (
        "filesystem",
        "prepare_start_progress_projection",
        "admit_start_progress_projection",
        "execute_start_progress_projection",
    ),
}
LEAVES = (
    "verify_source_projection_admission",
    "consume_source_projection_admission",
)
SYNC = {
    "filesystem",
    "observe_source_projection_plan",
    "verify_source_projection_plan",
    "observe_source_projection",
    *LEAVES,
}
FORBIDDEN_PARAMETERS = {
    "authorized",
    "validated",
    "callback",
    "evaluator",
    "method_name",
    "may_cleanup",
    "provider",
    "suppliers",
}


def tree():
    return ast.parse(SIGNATURES.read_text())


def classes():
    return {node.name: node for node in tree().body if isinstance(node, ast.ClassDef)}


def fields(name):
    return {
        node.target.id: node.annotation
        for node in classes()[name].body
        if isinstance(node, ast.AnnAssign)
    }


def enums():
    return {
        node.name.id: tuple(option.value for option in node.value.slice.elts)
        for node in tree().body
        if isinstance(node, ast.TypeAlias)
    }


def spelling(annotation):
    if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
        assert ast.unparse(annotation.right) == "None"
        return spelling(annotation.left) + "?"
    if isinstance(annotation, ast.Name):
        return {"str": "String", "int": "Int", "bool": "Bool"}.get(
            annotation.id, annotation.id
        )
    assert isinstance(annotation, ast.Subscript)
    assert ast.unparse(annotation.value) == "tuple"
    assert isinstance(annotation.slice, ast.Tuple)
    assert ast.unparse(annotation.slice.elts[1]) == "..."
    return spelling(annotation.slice.elts[0]) + "[]"


def lower(source=None):
    manifest = tomllib.loads((SDK / "aware.sdk.toml").read_text())["sdk"]
    path = "/qualification/workspace/source-projection-values.aware"
    document = parse_neutral_aware_source(
        SOURCE.read_text() if source is None else source, source_path=path
    )
    return resolve_ontology_meaning(
        (
            OntologyMeaningPackageInput(
                package_name=manifest["package_name"],
                fqn_prefix=manifest["fqn_prefix"],
                sources_root="/qualification/workspace",
                dependencies=(),
                documents=(document,),
                namespace_by_source_path=((path, ""),),
            ),
        ),
        selected_package_names=frozenset({manifest["package_name"]}),
    )


@lru_cache
def meaning():
    return lower()


def members(name):
    return {
        entry.fqn.rsplit(".", 1)[1]: meaning_value_to_json(entry.payload)
        for entry in meaning().entries
        if entry.kind == "member"
        and entry.fqn.rsplit(".", 1)[0] == "aware_workspace_sdk." + name
    }


def original_class(path, name):
    return next(
        node
        for node in ast.parse((ROOT / path).read_text()).body
        if isinstance(node, ast.ClassDef) and node.name == name
    )


@pytest.mark.parametrize("path", tuple(LEDGER["inputs"]))
def test_bounded_inputs_match_current_committed_blobs_and_modes(path):
    pin = LEDGER["inputs"][path]
    target = ROOT / path
    raw = target.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == pin["sha256"]
    assert len(raw) == pin["size_bytes"]
    assert stat.S_IMODE(target.stat().st_mode) == pin["mode"]
    assert (
        subprocess.check_output(
            ["git", "show", LEDGER["revision"] + ":" + path], cwd=ROOT
        )
        == raw
    )
    entry = subprocess.check_output(
        ["git", "ls-tree", LEDGER["revision"], "--", path], cwd=ROOT, text=True
    ).split()
    assert entry[:3] == [pin["git_mode"], "blob", pin["git_blob"]]


@pytest.mark.parametrize("name", ROOTS)
def test_each_value_preserves_fields_order_nullability_and_resolved_targets(name):
    observed = members(name)
    expected = fields(name)
    assert set(observed) == set(expected)
    for position, (field, annotation) in enumerate(expected.items()):
        member = observed[field]
        text = spelling(annotation)
        assert member["position"] == position
        assert member["type_expression"] == text
        assert member["nullable"] is text.endswith("?")
        assert member["collection"] is text.removesuffix("?").endswith("[]")
        assert member["identity_key"] is False
        if not member["primitive"]:
            assert member["target_fqn"] is not None
            assert member["target_symbol_kind"] in {"class_def", "enum_def"}
    symbol = next(
        entry
        for entry in meaning().entries
        if entry.kind == "symbol" and entry.fqn == "aware_workspace_sdk." + name
    )
    assert meaning_value_to_json(symbol.payload)["inline_value"] is True
    assert all(isinstance(node, ast.AnnAssign) for node in classes()[name].body)


@pytest.mark.parametrize("name", tuple(enums()))
def test_finite_state_vocabulary_lowers_in_exact_order(name):
    options = sorted(
        (
            entry
            for entry in meaning().entries
            if entry.kind == "enum_option"
            and entry.fqn.rsplit(".", 1)[0] == "aware_workspace_sdk." + name
        ),
        key=lambda entry: meaning_value_to_json(entry.payload)["position"],
    )
    assert tuple(entry.fqn.rsplit(".", 1)[1] for entry in options) == enums()[name]


@pytest.mark.parametrize(
    ("name", "path", "enum_fields"),
    (
        ("RepositoryObservationCoordinate", RUNTIME + "repository_access.py", {}),
        (
            "WorkspaceRepositoryPhysicalEffect",
            RUNTIME + "change_evidence.py",
            {"state": "str"},
        ),
        (
            "WorkspaceRepositoryMutationExecutionEvidence",
            RUNTIME + "repository_mutation.py",
            {"physical_return_state": "str", "body_retention_state": "str"},
        ),
    ),
)
def test_original_owner_mirrors_preserve_exact_fields_and_annotations(
    name, path, enum_fields
):
    original = {
        node.target.id: ast.unparse(node.annotation)
        for node in original_class(path, name).body
        if isinstance(node, ast.AnnAssign)
    }
    companion = {
        field: enum_fields.get(field, ast.unparse(annotation))
        for field, annotation in fields(name).items()
    }
    assert tuple(companion) == tuple(original)
    assert companion == original


@pytest.mark.parametrize("name", OPAQUE)
def test_live_handles_are_not_inline_values_or_constructible_ports(name):
    assert name not in ROOTS
    assert "class " + name + " " not in SOURCE.read_text()
    node = classes()[name]
    assert len(node.body) == 1
    assert isinstance(node.body[0], ast.Expr)
    assert node.body[0].value.value is Ellipsis
    assert not node.bases and not node.decorator_list


@pytest.mark.parametrize("owner", tuple(PORTS))
def test_owner_port_set_is_exact_without_generic_dispatch(owner):
    methods = [
        node
        for node in classes()[owner].body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    ]
    assert tuple(node.name for node in methods) == PORTS[owner]
    for node in methods:
        assert isinstance(node, ast.FunctionDef) is (node.name in SYNC)
        assert not node.args.vararg and not node.args.kwarg
        assert not FORBIDDEN_PARAMETERS.intersection(
            arg.arg for arg in node.args.args + node.args.kwonlyargs
        )
        assert len(node.body) == 1
        assert isinstance(node.body[0], ast.Expr)
        assert node.body[0].value.value is Ellipsis


@pytest.mark.parametrize("name", LEAVES)
def test_supplying_issue_ports_are_fixed_module_leaves_not_callbacks(name):
    leaves = {
        node.name: node for node in tree().body if isinstance(node, ast.FunctionDef)
    }
    assert tuple(leaves) == LEAVES
    node = leaves[name]
    assert [arg.arg for arg in node.args.args] == ["admission"]
    assert ast.unparse(node.args.args[0].annotation) == "IssueSourceProjectionAdmission"
    assert len(node.args.kwonlyargs) == 1
    assert (
        ast.unparse(node.args.kwonlyargs[0].annotation)
        == "WorkspaceSourceProjectionBinding"
    )
    assert not node.args.vararg and not node.args.kwarg
    assert node.body[0].value.value is Ellipsis


@pytest.mark.parametrize(
    ("owner", "arguments"),
    (
        (
            "WorkspaceRepositorySourceProjectionClient",
            ("repository_root", "state_root", "execution_id"),
        ),
        ("IssueStartProgressProjectionClient", ("repository_root", "execution_id")),
    ),
)
def test_explicit_filesystem_selection_has_no_unqualified_adoption(owner, arguments):
    method = next(node for node in classes()[owner].body if node.name == "filesystem")
    assert [ast.unparse(item) for item in method.decorator_list] == ["classmethod"]
    assert tuple(arg.arg for arg in method.args.kwonlyargs) == arguments
    assert method.args.kw_defaults == [None] * len(arguments)
    assert ast.unparse(method.returns) == owner


def test_full_original_mutation_result_is_resolvable_without_renewing_admission():
    method = next(
        node
        for node in classes()["WorkspaceRepositorySourceProjectionClient"].body
        if node.name == "resolve_source_projection_receipt"
    )
    assert isinstance(method, ast.AsyncFunctionDef)
    assert ast.unparse(method.returns) == "WorkspaceRepositoryAuthorizedMutation | None"
    assert [arg.arg for arg in method.args.args] == ["self", "admission"]
    assert (
        ast.unparse(method.args.args[1].annotation)
        == "WorkspaceSourceProjectionAdmission"
    )
    assert not method.args.kwonlyargs
    report = REPORT.read_text()
    assert "Receipt resolution never dispatches a write" in report


def test_domain_request_result_and_original_operation_remain_intact():
    methods = {
        node.name: node for node in classes()["IssueStartProgressProjectionClient"].body
    }
    prepare = methods["prepare_start_progress_projection"]
    execute = methods["execute_start_progress_projection"]
    assert ast.unparse(prepare.args.args[1].annotation) == "IssueStartProgressRequest"
    assert ast.unparse(execute.returns) == "IssueMutationResult"
    assert LEDGER["operation_ref"] == "issue_sdk.start_issue_progress"
    assert LEDGER["profile_ref"] == "issue_start_progress_v0"
    assert "StartIssueProgressIntent" in REPORT.read_text()
    assert "apply_issue_intent" in REPORT.read_text()


def test_input_scope_cannot_admit_source_writers_or_runtime_implementation():
    assert LEDGER["scope_grade"] == "descriptive_qualification_only"
    assert not LEDGER["runtime_acceptance"]
    assert not LEDGER["installed_acceptance"]
    assert len(LEDGER["inputs"]) == 25
    assert len(LEDGER["effect_paths"]) == 6
    assert set(LEDGER["effect_paths"]).isdisjoint(LEDGER["inputs"])
    assert set(ROOTS).isdisjoint(OPAQUE)
    assert len(ROOTS) == 13 and len(enums()) == 8


def test_fixture_is_outside_production_sdk_source_membership():
    manifest = tomllib.loads((SDK / "aware.sdk.toml").read_text())
    assert manifest["build"]["sources_dir"] == "."
    assert manifest["build"]["include_paths"] == ["*.aware"]
    assert not SOURCE.is_relative_to(SDK)
    assert not (SDK / SOURCE.name).exists()
    assert not (SDK / SIGNATURES.name).exists()
    sdk_init = (
        ROOT
        / WORKSPACE
        / "sdks/workspace/python/public/aware_workspace_sdk/__init__.py"
    )
    assert "repository_source_projection" not in sdk_init.read_text()


def test_original_writer_selector_enum_is_not_backend_availability():
    from aware_file_system.confined_mutation import ConfinedMutationProfile

    assert enums()["WorkspaceSourcePhysicalGuarantee"] == tuple(
        value.value for value in ConfinedMutationProfile
    )
    assert "remains unavailable and must refuse without downgrade" in REPORT.read_text()


def test_total_uncertainty_does_not_fabricate_original_physical_boolean_fields():
    assert ast.unparse(
        fields("WorkspaceSourceProjectionObservation")["physical_effect"]
    ) == ("WorkspaceRepositoryPhysicalEffect | None")
    assert "unknown" in enums()["WorkspaceSourcePhysicalEffectState"]
    assert "unavailable" in enums()["WorkspaceSourcePhysicalReturnState"]
    effect = fields("WorkspaceRepositoryPhysicalEffect")
    assert ast.unparse(effect["before_exists"]) == "bool"
    assert ast.unparse(effect["after_exists"]) == "bool"
    assert "Do not fabricate" in REPORT.read_text()


def test_known_source_convergence_retention_and_cleanup_remain_separate():
    observation = fields("WorkspaceSourceProjectionObservation")
    assert {"source_effect_state", "convergence_state", "retention", "cleanup"} <= set(
        observation
    )
    assert "content_delta_ref" in fields(
        "WorkspaceSourceProjectionRetentionObservation"
    )
    assert "delta_evidence_ref" not in fields(
        "WorkspaceSourceProjectionRetentionObservation"
    )
    assert "Unknown cleanup does not imply unlock or completion" in REPORT.read_text()


def test_snapshot_digest_is_deterministic_with_provenance_not_a_byte_guard():
    again = lower()
    assert again.canonical_sha256 == meaning().canonical_sha256
    commented = lower(SOURCE.read_text() + "\n// Unchanged descriptive semantics.\n")
    # This snapshot includes source provenance; it is not ProtocolManifest's
    # normalized-semantics digest. Appended comments preserve all field meaning
    # but change the original document fingerprint in the snapshot.
    assert commented.canonical_sha256 != meaning().canonical_sha256
    stable_fields = (
        "position",
        "type_expression",
        "nullable",
        "collection",
        "identity_key",
        "primitive",
        "target_fqn",
        "target_symbol_kind",
    )
    for name in ROOTS:
        changed_members = {
            entry.fqn.rsplit(".", 1)[1]: meaning_value_to_json(entry.payload)
            for entry in commented.entries
            if entry.kind == "member"
            and entry.fqn.rsplit(".", 1)[0] == "aware_workspace_sdk." + name
        }
        for field, original in members(name).items():
            assert {key: changed_members[field].get(key) for key in stable_fields} == {
                key: original.get(key) for key in stable_fields
            }
    assert (
        hashlib.sha256(
            (SOURCE.read_text() + "\n// Unchanged descriptive semantics.\n").encode()
        ).hexdigest()
        != hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    )


def test_real_parser_entrypoints_match_the_pinned_source_inputs():
    import tree_sitter_aware.neutral_ir as parser
    import tree_sitter_aware.ontology_meaning as values
    import tree_sitter_aware.ontology_meaning_resolver as resolver

    for module in (parser, values, resolver):
        path = Path(module.__file__).resolve()
        relative = path.relative_to(ROOT).as_posix()
        assert relative in LEDGER["inputs"]
        assert (
            hashlib.sha256(path.read_bytes()).hexdigest()
            == LEDGER["inputs"][relative]["sha256"]
        )


@pytest.mark.parametrize(
    ("before", "after", "owner", "field", "property_name", "changed"),
    (
        (
            "target_path String",
            "target_path Int",
            "WorkspaceSourceObservation",
            "target_path",
            "type_expression",
            "Int",
        ),
        (
            "before_exists Bool",
            "before_exists Bool?",
            "WorkspaceRepositoryPhysicalEffect",
            "before_exists",
            "nullable",
            True,
        ),
        (
            "cursor Int",
            "cursor String",
            "RepositoryObservationCoordinate",
            "cursor",
            "type_expression",
            "String",
        ),
        (
            "diagnostics String[]",
            "diagnostics String",
            "WorkspaceRepositoryMutationExecutionEvidence",
            "diagnostics",
            "collection",
            False,
        ),
        (
            "physical_effect WorkspaceRepositoryPhysicalEffect?",
            "physical_effect WorkspaceRepositoryPhysicalEffect",
            "WorkspaceSourceProjectionObservation",
            "physical_effect",
            "nullable",
            False,
        ),
    ),
)
def test_real_lowering_exposes_field_regressions(
    before, after, owner, field, property_name, changed
):
    altered = lower(SOURCE.read_text().replace(before, after))
    entry = next(
        entry
        for entry in altered.entries
        if entry.kind == "member"
        and entry.fqn == f"aware_workspace_sdk.{owner}.{field}"
    )
    observed = meaning_value_to_json(entry.payload)[property_name]
    assert observed == changed
    assert observed != members(owner)[field][property_name]


@pytest.mark.parametrize("key", ("values_fixture", "signatures_fixture"))
def test_qualification_artifacts_match_their_recorded_byte_pins(key):
    pin = LEDGER["qualification"][key]
    assert (
        hashlib.sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]
    )


def test_qualified_snapshot_and_signature_counts_match_the_intake():
    qualification = LEDGER["qualification"]
    assert qualification["value_root_count"] == len(ROOTS)
    assert qualification["finite_enum_count"] == len(enums())
    assert qualification["opaque_handle_count"] == len(OPAQUE)
    assert qualification["port_signature_count"] == sum(map(len, PORTS.values())) + len(
        LEAVES
    )
    assert qualification["meaning_entry_count"] == len(meaning().entries)
    assert qualification["meaning_canonical_sha256"] == meaning().canonical_sha256


def test_complete_lowered_symbol_set_has_no_undeclared_value_or_live_handle():
    symbols = {
        entry.fqn.rsplit(".", 1)[1]
        for entry in meaning().entries
        if entry.kind == "symbol"
    }
    assert symbols == set(ROOTS) | set(enums())
    assert symbols.isdisjoint(OPAQUE)


def assert_public_preparation_handoff(declarations):
    """Inspect declared ports only; never simulate an owner or issue authority."""
    owner = next(
        node
        for node in declarations.body
        if isinstance(node, ast.ClassDef)
        and node.name == "WorkspaceRepositorySourceProjectionClient"
    )
    methods = {node.name: node for node in owner.body}
    retain = methods["retain_projection_body"]
    assert isinstance(retain, ast.AsyncFunctionDef)
    assert [(arg.arg, ast.unparse(arg.annotation)) for arg in retain.args.args[1:]] == [
        ("content", "bytes")
    ]
    assert [
        (arg.arg, ast.unparse(arg.annotation)) for arg in retain.args.kwonlyargs
    ] == [("expected_content_digest", "str"), ("expected_size_bytes", "int")]
    assert retain.args.kw_defaults == [None, None]
    assert ast.unparse(retain.returns) == "str"

    prepare = methods["prepare_source_projection"]
    observe = methods["observe_source_projection_plan"]
    verify = methods["verify_source_projection_plan"]
    assert ast.unparse(prepare.returns) == "WorkspaceSourceProjectionPlan"
    assert isinstance(observe, ast.FunctionDef)
    assert [
        (arg.arg, ast.unparse(arg.annotation)) for arg in observe.args.args[1:]
    ] == [("plan", "WorkspaceSourceProjectionPlan")]
    assert not observe.args.kwonlyargs
    assert ast.unparse(observe.returns) == "WorkspaceSourceProjectionPlanObservation"
    assert (
        ast.unparse(verify.args.args[1].annotation) == "WorkspaceSourceProjectionPlan"
    )
    assert [
        (arg.arg, ast.unparse(arg.annotation)) for arg in verify.args.kwonlyargs
    ] == [("expected_binding", "WorkspaceSourceProjectionBinding")]
    assert verify.args.kw_defaults == [None]
    assert (
        ast.unparse(fields("WorkspaceSourceProjectionPlanObservation")["binding"])
        == "WorkspaceSourceProjectionBinding"
    )


def test_declared_preparation_handoff_needs_bytes_and_original_plan_only():
    assert_public_preparation_handoff(tree())
    # Observation has no admission or caller-built provider coordinates. Its
    # detached result is not a live handle or an alternative verification port.
    assert "binding" not in fields("WorkspaceSourceProjectionRequest")
    assert "original_plan_recognized" in fields(
        "WorkspaceSourceProjectionPlanObservation"
    )
    report = REPORT.read_text()
    assert "record_body(content)" in report
    assert "binding observation is not admission" in " ".join(report.split())


@pytest.mark.parametrize(
    ("before", "after"),
    (
        ("retain_projection_body", "missing_body_handoff"),
        ("content: bytes", "content: str"),
        ("expected_content_digest: str", "expected_content_digest: bytes"),
        ("expected_size_bytes: int", "expected_size_bytes: str"),
        ("observe_source_projection_plan", "missing_plan_observation"),
        (
            "self, plan: WorkspaceSourceProjectionPlan\n    ) -> WorkspaceSourceProjectionPlanObservation",
            "self, plan: WorkspaceSourceProjectionAdmission\n    ) -> WorkspaceSourceProjectionPlanObservation",
        ),
    ),
)
def test_preparation_handoff_regressions_are_detected_without_executing_stubs(
    before, after
):
    source = SIGNATURES.read_text()
    assert before in source
    with pytest.raises((AssertionError, KeyError)):
        assert_public_preparation_handoff(ast.parse(source.replace(before, after)))


@pytest.mark.parametrize(
    "content", (b"", b"Issue-owned postimage\n", "NFC café\n".encode())
)
def test_genuine_retention_requires_bytes_in_the_receiving_owner(tmp_path, content):
    from aware_workspace_sdk.repository_delta_retention import (
        WorkspaceRepositoryDeltaRetentionFactory,
    )

    first = WorkspaceRepositoryDeltaRetentionFactory.filesystem(
        state_root=tmp_path / "issue-owner"
    ).allocate_delta_retention()
    receiving = WorkspaceRepositoryDeltaRetentionFactory.filesystem(
        state_root=tmp_path / "workspace-owner"
    ).allocate_delta_retention()
    try:
        first.initialize_delta_retention(repository_binding_ref="repository:qualified")
        receiving.initialize_delta_retention(
            repository_binding_ref="repository:qualified"
        )
        ref = first.record_body(content)
        assert not receiving.contains_body(ref)
        assert receiving.resolve_body(ref) is None
        before = receiving.snapshot()
        assert before.retained_body_count == 0

        # This is the existing supplying SDK, not an implementation of the
        # proposed wrapper. A reference alone never transfers bytes or custody.
        received_ref = receiving.record_body(content)
        expected_digest = "sha256:" + hashlib.sha256(content).hexdigest()
        assert received_ref == ref == "workspace-repository-body:" + expected_digest
        resolved = receiving.resolve_body(received_ref)
        assert resolved == content and len(resolved) == len(content)
        assert receiving.snapshot().retained_body_count == 1
        assert receiving.snapshot().retained_capture_count == 0
        assert receiving.snapshot().retained_delta_count == 0
        first.release_retention()
        assert receiving.resolve_body(received_ref) == content
    finally:
        first.release_retention()
        receiving.release_retention()


def test_correction_preserves_predecessor_inputs_and_all_value_meaning():
    correction = LEDGER["interface_correction"]
    path = "docs/reports/workspace-source-projection-authored-inputs-20261010.json"
    predecessor = json.loads(
        subprocess.check_output(
            ["git", "show", correction["predecessor_commit"] + ":" + path], cwd=ROOT
        )
    )
    assert LEDGER["inputs"] == predecessor["inputs"]
    assert LEDGER["revision"] == predecessor["revision"]
    for key in (
        "values_fixture",
        "value_root_count",
        "finite_enum_count",
        "opaque_handle_count",
        "meaning_canonical_sha256",
        "meaning_entry_count",
    ):
        assert LEDGER["qualification"][key] == predecessor["qualification"][key]
    assert LEDGER["qualification"]["port_signature_count"] == (
        predecessor["qualification"]["port_signature_count"] + 2
    )
    assert (
        correction["predecessor_signatures_sha256"]
        == (predecessor["qualification"]["signatures_fixture"]["sha256"])
    )
