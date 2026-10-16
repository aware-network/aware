from __future__ import annotations

import ast
import copy
import hashlib
import itertools
import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from aware_code_semantic_contract_runtime import grammar_product_contracts as products
from aware_code_semantic_contract_runtime.codec import (
    decode_profile_declaration,
    encode_profile_declaration,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.grammar_product_contracts import (
    GRAMMAR_CLEANUP_CAUSES,
    GRAMMAR_CLEANUP_COMPLETIONS,
    GRAMMAR_CLEANUP_EPOCH_STATES,
    GRAMMAR_CLEANUP_RESOURCE_KINDS,
    GRAMMAR_CLEANUP_RESOURCE_STATUSES,
    GRAMMAR_CLEANUP_WORK_STATES,
    GRAMMAR_FAILURE_PHASES,
    GRAMMAR_FAILURE_REASONS,
    GRAMMAR_FAILURE_RESULT_STATES,
    GRAMMAR_PROFILE_PROVIDER_REF,
    GRAMMAR_READ_EFFECT_REF,
    GRAMMAR_READ_TRANSITION_REF,
    GRAMMAR_ROLE_CLEANUP_REF,
    GRAMMAR_ROLE_FAILURE_REF,
    GRAMMAR_SOURCE_ROLE_SELECTION_REF,
    GRAMMAR_SYNTAX_PROVIDER_V2_REF,
    CodeGrammarReadEffectV1,
    CodeGrammarReadTransitionV1,
    CodeGrammarRoleCleanupReceiptV1,
    CodeGrammarRoleCleanupResourceV1,
    CodeGrammarRoleFailureEvidenceV1,
    CodeGrammarSourceRoleSelectionV1,
    decode_grammar_role_cleanup,
    decode_grammar_role_failure,
    decode_grammar_source_role_selection,
    encode_grammar_role_cleanup,
    encode_grammar_role_failure,
    encode_grammar_source_role_selection,
    grammar_operational_contracts,
    grammar_operational_profile,
)
from aware_code_semantic_contract_runtime.grammar_profile_codec import (
    grammar_profile_selection_body,
    grammar_syntax_binding_body,
)
from test_grammar_profile_contract import DIGEST, ROOT, declaration, syntax_fixture
from test_profile_runtime import profile


@pytest.mark.parametrize("stage", ("profile_selection", "syntax_binding"))
def test_complete_operational_profile_matches_frozen_domain_and_body(stage):
    account = json.loads(
        (
            ROOT / "docs/reports/code-language-grammar-product-contract-20261012.json"
        ).read_bytes()
    )
    expected = next(row for row in account["products"] if row["slot"] == stage)
    value = grammar_operational_profile(stage)
    body = encode_profile_declaration(value)
    assert decode_profile_declaration(body) == value
    body_bytes = body.encode("utf-8")
    identity = account["identity_account"]["profiles"][stage]
    assert len(body_bytes) == identity["body_bytes"]
    assert value.digest.value == identity["domain_digest"]
    assert (
        "sha256:" + hashlib.sha256(body_bytes).hexdigest()
        == identity["encoded_body_digest"]
    )
    assert value.profile_ref == expected["profile_ref"]
    assert value.version == expected["version"]
    assert value.package_kinds == tuple(account["scope"]["package_kinds"])
    assert value.operation_kinds == ("resolve_grammar_profile",)
    provider = value.providers[0]
    assert provider.provider_key == expected["provider_key"]
    assert provider.allows_typed_empty is True
    assert provider.predecessor_required is False
    assert provider.terminal_statuses == ("delta",)
    assert value.terminal_output_roles == ()


@pytest.mark.parametrize(
    ("name", "reference"),
    (
        ("profile_provider", GRAMMAR_PROFILE_PROVIDER_REF),
        ("syntax_provider", GRAMMAR_SYNTAX_PROVIDER_V2_REF),
    ),
)
def test_provider_reference_preserves_complete_frozen_descriptor(name, reference):
    descriptor = json.loads(
        (
            ROOT / "docs/reports/code-language-grammar-product-contract-20261012.json"
        ).read_bytes()
    )["descriptors"][name]
    assert reference.key == descriptor["contract"]
    assert reference.version == descriptor["version"]
    assert reference.schema_digest == ContentDigest.of_bytes(
        canonical_json_bytes(descriptor)
    )


@pytest.mark.parametrize("stage", ("profile_selection", "syntax_binding"))
def test_complete_contract_inventory_and_role_binding(stage):
    value = grammar_operational_profile(stage)
    declaration = value.providers[0]
    expected = {row.contract for row in value.inputs} | {
        declaration.result_role.contract,
        declaration.transition_contract,
        declaration.effect_role.contract,
    }
    actual = grammar_operational_contracts(stage)
    assert set(actual) == expected
    assert len(actual) == (6 if stage == "profile_selection" else 7)
    assert actual == tuple(
        sorted(expected, key=lambda ref: canonical_json_bytes(ref.to_wire()))
    )
    assert tuple(row.role for row in value.inputs) == tuple(
        row.role for row in declaration.consumed_roles
    )
    assert tuple(
        (row.target_role, row.source_role) for row in value.steps[0].bindings
    ) == tuple((row.role, row.role) for row in value.inputs)
    if stage == "syntax_binding":
        selected = next(
            row for row in value.inputs if row.role == "code.profile_selection"
        )
        assert selected.contract == products.GRAMMAR_PROFILE_RESULT_REF
        assert (
            declaration.result_role.contract == products.GRAMMAR_SYNTAX_BINDING_V2_REF
        )
        assert selected.contract != declaration.result_role.contract


class _StageString(str):
    pass


@pytest.mark.parametrize(
    "bad",
    (
        None,
        True,
        1,
        {},
        [],
        "",
        "profile",
        "syntax_binding ",
        "PROFILE_SELECTION",
        _StageString("profile_selection"),
    ),
)
@pytest.mark.parametrize(
    "entrance", (grammar_operational_profile, grammar_operational_contracts)
)
def test_operational_stage_is_exact_closed_without_fallback(entrance, bad):
    with pytest.raises((TypeError, ContractViolation)):
        entrance(bad)


def test_foreign_stage_refuses_before_comparison_callback():
    class Foreign:
        def __eq__(self, other):
            raise AssertionError("foreign stage callback")

    for entrance in (grammar_operational_profile, grammar_operational_contracts):
        with pytest.raises(TypeError):
            entrance(Foreign())


@pytest.mark.parametrize("stage", ("profile_selection", "syntax_binding"))
def test_fresh_graph_without_provider_runtime_or_registration(monkeypatch, stage):
    from aware_code_semantic_contract_runtime import selected_provider
    from aware_code_semantic_contract_runtime.runtime import SemanticContractRuntime

    def forbidden(*args, **kwargs):
        raise AssertionError("declarations cannot issue runtime authority")

    monkeypatch.setattr(
        selected_provider, "_admit_selected_provider_factory", forbidden
    )
    monkeypatch.setattr(SemanticContractRuntime, "__init__", forbidden)
    first, second = (
        grammar_operational_profile(stage),
        grammar_operational_profile(stage),
    )
    assert first == second and first is not second
    assert first.providers[0] is not second.providers[0]
    assert first.steps[0] is not second.steps[0]
    assert first.inputs[0] is not second.inputs[0]


@pytest.mark.parametrize("stage", ("profile_selection", "syntax_binding"))
def test_original_graph_validator_refuses_missing_or_mismatched_role(stage):
    value = grammar_operational_profile(stage)
    with pytest.raises(ContractViolation):
        replace(
            value,
            steps=(replace(value.steps[0], bindings=value.steps[0].bindings[:-1]),),
        )
    with pytest.raises(ContractViolation):
        replace(value, terminal_result_role="foreign")


def test_original_portable_definitions_and_wires_not_rewritten():
    relative = "workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/aware_code_semantic_contract_runtime/grammar_product_contracts.py"
    old = subprocess.check_output(
        ["git", "show", "4e31d46e875bcd2921c98be413a2a906373f4f79:" + relative],
        cwd=ROOT,
        text=True,
    )
    before = ast.parse(old)
    after = ast.parse(Path(products.__file__).read_text())
    definitions = {
        node.name: ast.dump(node, include_attributes=False)
        for node in after.body
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
    }
    for node in before.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            assert definitions[node.name] == ast.dump(node, include_attributes=False)


def test_public_exports_and_site_free_neutral_construction(tmp_path):
    import aware_code_semantic_contract_runtime as root

    names = (
        "GRAMMAR_PROFILE_PROVIDER_REF",
        "GRAMMAR_SYNTAX_PROVIDER_V2_REF",
        "grammar_operational_profile",
        "grammar_operational_contracts",
    )
    for name in names:
        assert name in root.__all__
        assert getattr(root, name) is getattr(products, name)
    script = (
        "import sys; import aware_code_semantic_contract_runtime as c; "
        "assert len(c.grammar_operational_contracts('profile_selection')) == 6; "
        "assert len(c.grammar_operational_contracts('syntax_binding')) == 7; "
        "assert not any(n.startswith(('aware_language','aware_workspace','aware_meta','aware_ontology','aware_dev','aware_service')) for n in sys.modules)"
    )
    subprocess.run(
        [sys.executable, "-B", "-S", "-c", script],
        cwd=tmp_path,
        env={
            "PYTHONPATH": str(Path(products.__file__).resolve().parent.parent),
            "PATH": os.defpath,
        },
        check=True,
        capture_output=True,
        text=True,
    )


def cleanup_fixture():
    return CodeGrammarRoleCleanupReceiptV1(
        "attempt-1",
        "operation-1",
        DIGEST,
        DIGEST,
        "execution_failure",
        "quiescent",
        "finished",
        (CodeGrammarRoleCleanupResourceV1("role_host", "role-host-1", "released"),),
        "verified",
    )


def known_results():
    results = (
        grammar_profile_selection_body(profile()).coordinate,
        grammar_syntax_binding_body(syntax_fixture()).coordinate,
    )
    return tuple(sorted(results, key=lambda c: canonical_json_bytes(c.to_wire())))


def failure_fixture():
    return CodeGrammarRoleFailureEvidenceV1(
        "validate_result",
        "result_unvalidated",
        "unvalidated",
        known_results(),
        cleanup_fixture(),
    )


def test_references_and_portable_fields_match_full_frozen_descriptors():
    account = json.loads(
        (
            ROOT
            / "docs/reports/code-language-grammar-role-cleanup-contract-20261012.json"
        ).read_bytes()
    )
    for name, ref, value in (
        ("cleanup", GRAMMAR_ROLE_CLEANUP_REF, cleanup_fixture()),
        ("failure", GRAMMAR_ROLE_FAILURE_REF, failure_fixture()),
    ):
        descriptor = account["descriptors"][name]
        assert ref.schema_digest == ContentDigest.of_bytes(
            canonical_json_bytes(descriptor)
        )
        assert set(value.to_wire()) == set(descriptor["fields"])
    descriptor = account["descriptors"]["cleanup"]
    for name, values in (
        ("resource_kind", GRAMMAR_CLEANUP_RESOURCE_KINDS),
        ("resource_status", GRAMMAR_CLEANUP_RESOURCE_STATUSES),
        ("cause", GRAMMAR_CLEANUP_CAUSES),
        ("work_state", GRAMMAR_CLEANUP_WORK_STATES),
        ("epoch_state", GRAMMAR_CLEANUP_EPOCH_STATES),
        ("completion", GRAMMAR_CLEANUP_COMPLETIONS),
    ):
        assert tuple(descriptor["enums"][name]) == values
    for name, values in (
        ("phase", GRAMMAR_FAILURE_PHASES),
        ("reason", GRAMMAR_FAILURE_REASONS),
        ("results_state", GRAMMAR_FAILURE_RESULT_STATES),
    ):
        assert tuple(account["descriptors"]["failure"]["enums"][name]) == values


def test_product_descriptor_refs_include_complete_expanded_nested_shapes():
    account = json.loads(
        (
            ROOT / "docs/reports/code-language-grammar-product-contract-20261012.json"
        ).read_bytes()
    )
    base = json.loads(
        (
            ROOT / "docs/reports/code-language-production-role-contract-20261012.json"
        ).read_bytes()
    )
    source = json.loads(
        (
            ROOT
            / "docs/reports/code-language-original-declaration-binding-20261012.json"
        ).read_bytes()
    )["declaration_source_descriptor"]
    for name, ref in (
        ("selection", GRAMMAR_SOURCE_ROLE_SELECTION_REF),
        ("transition", GRAMMAR_READ_TRANSITION_REF),
        ("effect", GRAMMAR_READ_EFFECT_REF),
    ):
        descriptor = copy.deepcopy(account["descriptors"][name])
        if name == "selection":
            descriptor["nested_fields"] = source["fields"]
            descriptor["nested_bounds"] = source["bounds"]
        else:
            descriptor["nested_fields"] = {
                key: base["descriptors"]["syntax"]["nested_fields"][key]
                for key in (
                    "SemanticValueCoordinate",
                    "SemanticContractRef",
                    "ContentDigest",
                )
            }
        assert ref.schema_digest == ContentDigest.of_bytes(
            canonical_json_bytes(descriptor)
        )


def test_selection_strict_owner_round_trip_and_no_write():
    value = CodeGrammarSourceRoleSelectionV1(
        "operation-1",
        "profile_selection",
        DIGEST,
        "occurrence-1",
        "selected",
        declaration(),
    )
    assert (
        decode_grammar_source_role_selection(
            encode_grammar_source_role_selection(value)
        )
        == value
    )
    with pytest.raises(ContractViolation):
        replace(value, stage="other")
    with pytest.raises(ContractViolation):
        replace(value, profile_source=declaration("module"))
    wire = value.to_wire()
    for key in wire:
        changed = dict(wire)
        del changed[key]
        with pytest.raises(ContractViolation):
            decode_grammar_source_role_selection(canonical_json_bytes(changed))


def test_read_transition_effect_values_are_not_context_free_output_codecs():
    import aware_code_semantic_contract_runtime.grammar_product_contracts as product

    coordinate = grammar_profile_selection_body(profile()).coordinate
    transition = CodeGrammarReadTransitionV1(
        "profile_selection", DIGEST, DIGEST, coordinate
    )
    effect = CodeGrammarReadEffectV1("profile_selection", DIGEST, DIGEST, coordinate)
    assert effect.to_wire()["physical_effect"] == "none"
    assert transition.to_wire()["result"] == coordinate.to_wire()
    assert not hasattr(product, "decode_grammar_read_transition")
    assert not hasattr(product, "decode_grammar_read_effect")
    assert not hasattr(effect, "decode")
    with pytest.raises(ContractViolation):
        replace(effect, stage="syntax_binding")


@pytest.mark.parametrize(
    ("work", "epoch", "status"),
    itertools.product(
        GRAMMAR_CLEANUP_WORK_STATES,
        GRAMMAR_CLEANUP_EPOCH_STATES,
        GRAMMAR_CLEANUP_RESOURCE_STATUSES,
    ),
)
def test_complete_cleanup_truth_table_and_no_uncertainty_upgrade(work, epoch, status):
    settled = (
        work in {"not_started", "quiescent"}
        and epoch in {"not_started", "finished"}
        and status in {"not_acquired", "released"}
    )
    resource = CodeGrammarRoleCleanupResourceV1("role_host", "role-host-1", status)
    value = replace(
        cleanup_fixture(),
        work_state=work,
        epoch_state=epoch,
        resources=(resource,),
        completion="verified" if settled else "unverified",
    )
    assert decode_grammar_role_cleanup(encode_grammar_role_cleanup(value)) == value
    with pytest.raises(ContractViolation):
        replace(value, completion="unverified" if settled else "verified")


def test_explicit_nulls_are_required_and_have_no_implicit_defaults():
    value = CodeGrammarRoleCleanupReceiptV1(
        None,
        None,
        None,
        None,
        "construction_failure",
        "not_started",
        "not_started",
        (),
        "verified",
    )
    body = encode_grammar_role_cleanup(value)
    assert decode_grammar_role_cleanup(body) == value
    for key in (
        "attempt_ref",
        "operation_ref",
        "profile_input_digest",
        "syntax_input_digest",
    ):
        wire = value.to_wire()
        assert wire[key] is None
        del wire[key]
        with pytest.raises(ContractViolation):
            decode_grammar_role_cleanup(canonical_json_bytes(wire))


def test_correlation_resources_bounds_and_inventory_order():
    value = cleanup_fixture()
    for changes in (
        {"attempt_ref": None},
        {"operation_ref": None},
        {"resources": list(value.resources)},
        {"resources": value.resources * 2},
        {"resources": value.resources * 17},
    ):
        with pytest.raises((ContractViolation, TypeError)):
            replace(value, **changes)
    resources = tuple(
        CodeGrammarRoleCleanupResourceV1("role_host", f"r-{i:02}", "released")
        for i in range(16)
    )
    assert len(replace(value, resources=resources).resources) == 16
    with pytest.raises(ContractViolation):
        replace(value, resources=tuple(reversed(resources)))
    for field in ("attempt_ref", "operation_ref"):
        with pytest.raises(ContractViolation):
            replace(value, **{field: "x" * 513})


def test_known_results_preserve_failed_operation_and_original_correlation():
    value = failure_fixture()
    assert decode_grammar_role_failure(encode_grammar_role_failure(value)) == value
    assert value.cleanup.completion == "verified"
    assert value.reason == "result_unvalidated"
    assert len(value.known_results) == 2
    for changes in (
        {"results_state": "not_started"},
        {"results_state": "known", "known_results": ()},
        {"known_results": tuple(reversed(value.known_results))},
        {"known_results": value.known_results * 2},
        {"cleanup": replace(value.cleanup, profile_input_digest=None)},
        {"cleanup": replace(value.cleanup, syntax_input_digest=None)},
        {
            "known_results": (
                next(c for c in value.known_results if c.role == "code.syntax_binding"),
            )
        },
    ):
        with pytest.raises(ContractViolation):
            replace(value, **changes)
    changed = replace(value.known_results[0], role="other")
    with pytest.raises(ContractViolation):
        replace(value, known_results=(changed,))


@pytest.mark.parametrize("field", ("phase", "reason", "results_state"))
@pytest.mark.parametrize("bad", (None, "other", 0))
def test_failure_enums_are_closed(field, bad):
    with pytest.raises((TypeError, ContractViolation)):
        replace(failure_fixture(), **{field: bad})


@pytest.mark.parametrize(
    "location", ("failure", "cleanup", "resource", "coordinate", "reference")
)
@pytest.mark.parametrize("mode", ("missing", "extra", "null"))
def test_failure_nested_wire_is_closed(location, mode):
    wire = failure_fixture().to_wire()
    row = {
        "failure": wire,
        "cleanup": wire["cleanup"],
        "resource": wire["cleanup"]["resources"][0],
        "coordinate": wire["known_results"][0],
        "reference": wire["known_results"][0]["contract"],
    }[location]
    key = "contract" if "contract" in row else "key"
    if mode == "missing":
        del row[key]
    elif mode == "extra":
        row["raw_return"] = "never portable"
    else:
        row[key] = None
    with pytest.raises((ContractViolation, TypeError)):
        decode_grammar_role_failure(canonical_json_bytes(wire))


@pytest.mark.parametrize(
    ("decoder", "size"),
    ((decode_grammar_role_cleanup, 65_536), (decode_grammar_role_failure, 131_072)),
)
def test_failure_wire_bound_and_canonicality(decoder, size):
    with pytest.raises(ContractViolation):
        decoder(b" " * (size + 1))
    with pytest.raises(TypeError):
        decoder("{}")
    with pytest.raises(ContractViolation):
        decoder(b'{"contract":null,"contract":null}')


def test_portable_evidence_has_no_authority_or_raw_exception_fields():
    import aware_code_semantic_contract_runtime.grammar_product_contracts as product

    for name in (
        "CodeGrammarRoleCleanup",
        "dispose_grammar_role_cleanup",
        "read_grammar_role_cleanup",
        "CodeGrammarRoleFailureEvidenceError",
    ):
        assert not hasattr(product, name)
    wire = failure_fixture().to_wire()
    assert "raw_return" not in wire
    assert "cleanup_ticket" not in wire
    assert "primary_exception" not in wire
    assert "source_admission" not in wire
