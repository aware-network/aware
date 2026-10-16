"""Local syntax closure is data; original Code use owns source admission."""

from dataclasses import replace

import pytest
from aware_code_module_manifest_contract_runtime import (
    grammar_profile_composition as owner,
)
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.grammar_profile_codec import (
    CodeGrammarSyntaxBindingCodec,
)
from aware_language_parsed_document_contract import (
    SyntaxAssemblyContractError,
    SyntaxContributionV1,
    decode_syntax_assembly_value,
)
from test_grammar_profile_composition import admitted_catalog as admitted_catalog
from test_grammar_syntax_composition import syntax_inputs


def local_args(catalog, **options):
    args = syntax_inputs(catalog, **options)
    return {k: v for k, v in args.items() if k != "observed_contributions"}


@pytest.mark.parametrize("count", (2, 4))
@pytest.mark.parametrize("scanner", (False, True))
def test_selected_local_dependencies_preserve_complete_binding(
    admitted_catalog, count, scanner
):
    args = local_args(admitted_catalog, count=count, dependency=True, scanner=scanner)
    result = owner.reconstruct_grammar_local_dependency_binding(**args)
    value = CodeGrammarSyntaxBindingCodec().decode(result.canonical_body)
    assert len(value.contribution_bindings) == count
    assert {row.occurrence_ref for row in value.contribution_bindings} == set(
        args["provider_occurrences"]
    )
    assert value.interpretation_profile == args["input"].predecessors[0].coordinate


@pytest.mark.parametrize("scanner", (False, True))
def test_dependency_free_body_is_unchanged(admitted_catalog, scanner):
    args = local_args(admitted_catalog, scanner=scanner)
    assert owner.reconstruct_grammar_local_dependency_binding(
        **args
    ) == owner.reconstruct_grammar_source_binding(**args)


@pytest.mark.parametrize(
    "options",
    (
        {"missing_dependency": True},
        {"count": 2, "dependency": True, "bad_dependency_digest": True},
    ),
)
def test_incomplete_local_target_refuses(admitted_catalog, options):
    with pytest.raises(SyntaxAssemblyContractError):
        owner.reconstruct_grammar_local_dependency_binding(
            **local_args(admitted_catalog, **options)
        )


def contribution_account(catalog):
    args = syntax_inputs(catalog, count=2, dependency=True)
    values = tuple(
        decode_syntax_assembly_value(
            row[2].canonical_body, expected_type=SyntaxContributionV1
        )
        for row in args["observed_contributions"]
    )
    return {value.contribution_ref: ("same", value) for value in values}


@pytest.mark.parametrize("edges", (set(), {("same", "foreign")}))
def test_cross_occurrence_target_refuses_even_with_portable_edge(
    admitted_catalog, edges
):
    account = contribution_account(admitted_catalog)
    occurrence, target = account["sample-1"]
    account["sample-1"] = ("foreign", target)
    with pytest.raises(ContractViolation, match="target admission required"):
        owner._validate_selected_contribution_dependencies(
            account, edges, local_only=True
        )
    assert occurrence == "same"


def test_wrong_dependency_version_refuses(admitted_catalog):
    account = contribution_account(admitted_catalog)
    occurrence, target = account["sample-1"]
    account["sample-1"] = (occurrence, replace(target, version="2"))
    with pytest.raises(SyntaxAssemblyContractError, match="version/digest"):
        owner._validate_selected_contribution_dependencies(
            account, set(), local_only=True
        )


def test_original_dependency_free_entrance_still_refuses(admitted_catalog):
    args = local_args(admitted_catalog, count=2, dependency=True)
    with pytest.raises(ContractViolation, match="dependency admission required"):
        owner.reconstruct_grammar_source_binding(**args)


@pytest.mark.parametrize("kind", ("duplicate_label", "anchor_mismatch"))
def test_original_namespace_and_anchor_refusals_survive(admitted_catalog, kind):
    with pytest.raises((ContractViolation, SyntaxAssemblyContractError)):
        owner.reconstruct_grammar_local_dependency_binding(
            **local_args(admitted_catalog, count=2, **{kind: True})
        )
