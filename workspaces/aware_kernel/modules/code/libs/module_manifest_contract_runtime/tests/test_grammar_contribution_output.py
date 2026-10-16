"""Code output data uses original Language codecs; these fixtures issue no authority."""

from dataclasses import replace

import pytest
from aware_code_module_manifest_contract_runtime import (
    grammar_contribution_output as output,
)
from aware_code_module_manifest_contract_runtime import (
    grammar_profile_composition as owner,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    SemanticContractRef,
)
from aware_code_semantic_contract_runtime.grammar_contribution_contract import (
    GRAMMAR_CONTRIBUTION_OUTPUT_DESCRIPTOR,
    GRAMMAR_CONTRIBUTION_OUTPUT_REF,
)
from aware_code_semantic_contract_runtime.grammar_profile_codec import (
    CodeGrammarSyntaxBindingCodec,
)
from aware_code_semantic_contract_runtime.runtime import SemanticBody
from aware_language_parsed_document_contract import (
    SyntaxContributionV1,
    decode_syntax_assembly_value,
    encode_syntax_assembly_value,
)
from test_grammar_profile_composition import admitted_catalog as admitted_catalog
from test_grammar_syntax_composition import syntax_inputs


def args(catalog, **options):
    values = syntax_inputs(catalog, **options)
    return values, {
        key: value for key, value in values.items() if key != "observed_contributions"
    }


def test_code_descriptor_is_explicit_and_hash_bound():
    assert (
        GRAMMAR_CONTRIBUTION_OUTPUT_REF.key
        == "aware.code.grammar-contribution-output.v1"
    )
    assert GRAMMAR_CONTRIBUTION_OUTPUT_REF.schema_digest == ContentDigest.of_bytes(
        GRAMMAR_CONTRIBUTION_OUTPUT_DESCRIPTOR
    )


def test_output_delegates_complete_canonical_language_payload(admitted_catalog):
    values, _ = args(admitted_catalog, scanner=True)
    raw = values["observed_contributions"][0][2].canonical_body
    value = decode_syntax_assembly_value(raw, expected_type=SyntaxContributionV1)
    body = output.grammar_contribution_output_body(value)
    assert body.canonical_body == raw == encode_syntax_assembly_value(value)
    assert body.coordinate.contract == GRAMMAR_CONTRIBUTION_OUTPUT_REF
    assert output.decode_grammar_contribution_output(body) == value
    assert len(value.sources) == 2 and value.scanner is not None


@pytest.mark.parametrize("count", (1, 2, 4))
def test_reconstruction_emits_only_code_owned_coordinates(admitted_catalog, count):
    _, selected = args(admitted_catalog, count=count)
    body = owner.reconstruct_grammar_source_binding(**selected)
    value = CodeGrammarSyntaxBindingCodec().decode(body.canonical_body)
    assert len(value.contribution_bindings) == count
    assert all(
        row.contract == GRAMMAR_CONTRIBUTION_OUTPUT_REF
        and row.role == "code.syntax_contribution"
        for row in value.contribution_coordinates
    )
    assert all(
        not row.value_ref.startswith("fixture:")
        for row in value.contribution_coordinates
    )


@pytest.mark.parametrize(
    "options",
    (
        {"dependency": True, "count": 2},
        {"missing_dependency": True},
        {"dependency": True, "count": 2, "bad_dependency_digest": True},
    ),
)
def test_nonempty_dependency_declarations_refuse_without_filtering(
    admitted_catalog, options
):
    values, selected = args(admitted_catalog, **options)
    before = values["input"]
    with pytest.raises(ContractViolation, match="dependency admission required"):
        owner.reconstruct_grammar_source_binding(**selected)
    assert values["input"] is before


@pytest.mark.parametrize(
    "field", ("role", "contract", "value_ref", "size_bytes", "digest")
)
def test_output_coordinate_substitution_is_not_accepted(admitted_catalog, field):
    values, _ = args(admitted_catalog)
    value = decode_syntax_assembly_value(
        values["observed_contributions"][0][2].canonical_body,
        expected_type=SyntaxContributionV1,
    )
    body = output.grammar_contribution_output_body(value)
    replacements = {
        "role": "foreign",
        "contract": SemanticContractRef(
            "foreign", "1", ContentDigest.of_bytes(b"foreign")
        ),
        "value_ref": "foreign",
        "size_bytes": body.coordinate.size_bytes + 1,
        "digest": ContentDigest.of_bytes(b"foreign"),
    }
    with pytest.raises(ContractViolation):
        modified = SemanticBody(
            replace(body.coordinate, **{field: replacements[field]}),
            body.canonical_body,
        )
        output.decode_grammar_contribution_output(modified)


def test_legacy_observed_entrance_does_not_auto_reconstruct_none(admitted_catalog):
    values, _ = args(admitted_catalog)
    values["observed_contributions"] = None
    with pytest.raises(TypeError, match="observed contribution"):
        owner.produce_grammar_source_binding(**values)


@pytest.mark.parametrize("scanner", (False, True))
def test_scanner_and_occurrence_accounts_survive_reconstruction(
    admitted_catalog, scanner
):
    _, selected = args(admitted_catalog, scanner=scanner)
    value = CodeGrammarSyntaxBindingCodec().decode(
        owner.reconstruct_grammar_source_binding(**selected).canonical_body
    )
    assert (
        value.contribution_bindings[0].occurrence_ref
        == selected["provider_occurrences"][0]
    )


def test_duplicate_contribution_namespace_still_refuses(admitted_catalog):
    _, selected = args(admitted_catalog, count=2, duplicate_label=True)
    with pytest.raises(ValueError, match="contribution label"):
        owner.reconstruct_grammar_source_binding(**selected)
