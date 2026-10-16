from __future__ import annotations

import copy
import json
from dataclasses import replace
from pathlib import Path

import pytest
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    SemanticContractRef,
    SemanticValueCoordinate,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.grammar_profile_codec import (
    grammar_profile_selection_body,
)
from aware_code_semantic_contract_runtime.grammar_profile_contract import (
    GRAMMAR_DECLARATION_SOURCE_REF,
    GRAMMAR_PROFILE_RESULT_REF,
    GRAMMAR_SYNTAX_BINDING_V2_REF,
    CodeGrammarAnchorRequirementV1,
    CodeGrammarContributionBindingV1,
    CodeGrammarDeclarationSourceV1,
    CodeGrammarProviderBindingV2,
    CodeGrammarSyntaxBindingV2,
)
from test_profile_runtime import profile

ROOT = next(
    p for p in Path(__file__).resolve().parents if (p / "aware.repo.toml").is_file()
)
DIGEST = ContentDigest.of_bytes(b"unchanged")
CONSUMER = SemanticContractRef("consumer.syntax", "1", DIGEST)


def declaration(kind="profile"):
    return CodeGrammarDeclarationSourceV1(
        "repository-1",
        "workspaces/demo",
        kind,
        "workspaces/demo/aware.module.toml",
        "original-body-1",
        DIGEST,
        9,
    )


def syntax_fixture():
    value = profile()
    providers = tuple(
        CodeGrammarProviderBindingV2(
            occ, "same-module", "same-provider", CONSUMER, declaration("module"), DIGEST
        )
        for occ in ("z-occurrence", "a-occurrence")
    )
    contributions = tuple(
        CodeGrammarContributionBindingV1(
            occ,
            "same.syntax.json",
            SemanticValueCoordinate("syntax_contribution", CONSUMER, occ, DIGEST, 9),
        )
        for occ in ("a-occurrence", "z-occurrence")
    )
    coords = tuple(
        sorted(
            (b.contribution_coordinate for b in contributions),
            key=lambda c: canonical_json_bytes(c.to_wire()),
        )
    )
    anchor = CodeGrammarAnchorRequirementV1(
        "same-provider", CONSUMER, "node", "syntax_root", ("z", "a"), True, False
    )
    return CodeGrammarSyntaxBindingV2(
        "selected",
        value.profile_ref,
        value.version,
        value.digest,
        declaration(),
        providers,
        coords,
        contributions,
        (anchor,),
        grammar_profile_selection_body(value).coordinate,
    )


def test_wire_fields_and_descriptor_identity_match_accepted_freeze():
    base = json.loads(
        (
            ROOT / "docs/reports/code-language-production-role-contract-20261012.json"
        ).read_bytes()
    )
    amendment = json.loads(
        (
            ROOT
            / "docs/reports/code-language-original-declaration-binding-20261012.json"
        ).read_bytes()
    )
    descriptor = copy.deepcopy(base["descriptors"]["syntax"])
    successor = amendment["syntax_successor"]
    descriptor.update(root=successor["type"], contract=successor["contract"], version=2)
    descriptor["fields"].update(
        contract="literal " + successor["contract"],
        profile_source=successor["profile_source_type"],
        provider_bindings="CodeGrammarProviderBindingV2[] original authored provider order; unique occurrence_ref,provider_key pairs",
    )
    nested = descriptor["nested_fields"]
    provider = nested.pop("CodeGrammarProviderBindingV1")
    provider.update(
        contract="literal " + successor["provider_binding_contract"],
        declaration=successor["provider_declaration_type"],
    )
    nested["CodeGrammarProviderBindingV2"] = provider
    del nested["SemanticInputSourceCoordinate"]
    source = amendment["declaration_source_descriptor"]
    nested[source["root"]] = source["fields"]
    descriptor["declaration_source_bounds"] = source["bounds"]
    descriptor["laws"].extend(source["laws"])
    assert GRAMMAR_SYNTAX_BINDING_V2_REF.schema_digest == ContentDigest.of_bytes(
        canonical_json_bytes(descriptor)
    )
    assert GRAMMAR_DECLARATION_SOURCE_REF.schema_digest == ContentDigest.of_bytes(
        canonical_json_bytes(source)
    )
    assert GRAMMAR_PROFILE_RESULT_REF.schema_digest == ContentDigest.of_bytes(
        canonical_json_bytes(base["descriptors"]["profile"])
    )
    wire = syntax_fixture().to_wire()
    assert set(wire) == set(descriptor["fields"])
    for name, row in (
        ("CodeGrammarProviderBindingV2", wire["provider_bindings"][0]),
        ("CodeGrammarDeclarationSourceV1", wire["profile_source"]),
        ("CodeGrammarContributionBindingV1", wire["contribution_bindings"][0]),
        ("CodeGrammarAnchorRequirementV1", wire["anchor_requirements"][0]),
    ):
        assert set(row) == set(nested[name])


def test_equal_labels_paths_and_bytes_keep_occurrences_and_authored_order():
    value = syntax_fixture()
    assert tuple(p.occurrence_ref for p in value.provider_bindings) == (
        "z-occurrence",
        "a-occurrence",
    )
    assert (
        value.provider_bindings[0].declaration == value.provider_bindings[1].declaration
    )
    assert len(value.contribution_bindings) == 2
    assert value.anchor_requirements[0].field_path == ("z", "a")
    assert value.interpretation_profile.digest != value.code_profile_digest


@pytest.mark.parametrize("field", ("profile_key", "profile_ref", "profile_version"))
@pytest.mark.parametrize("bad", ("", "white space", "x" * 513, 1, None))
def test_root_tokens_refuse(field, bad):
    with pytest.raises((TypeError, ContractViolation)):
        replace(syntax_fixture(), **{field: bad})


@pytest.mark.parametrize("field", ("relative_path", "scope_key"))
@pytest.mark.parametrize(
    "bad", ("/absolute", "../escape", "a/./b", "a//b", "a\\b", "a\x00b", "e\u0301/path")
)
def test_declaration_paths_preserve_original_code_path_law(field, bad):
    with pytest.raises((TypeError, ContractViolation)):
        replace(declaration(), **{field: bad})


@pytest.mark.parametrize("size", (-1, True, 8_388_609, "1", None))
def test_declaration_size_refuses(size):
    with pytest.raises((TypeError, ContractViolation)):
        replace(declaration(), size_bytes=size)


def test_declaration_bounds_inclusive():
    assert replace(declaration(), size_bytes=8_388_608).size_bytes == 8_388_608
    assert replace(declaration(), body_ref="x" * 4096).body_ref == "x" * 4096
    with pytest.raises(ContractViolation):
        replace(declaration(), body_ref="x" * 4097)


@pytest.mark.parametrize(
    "field",
    (
        "provider_bindings",
        "contribution_coordinates",
        "contribution_bindings",
        "anchor_requirements",
    ),
)
def test_root_arrays_require_exact_tuples(field):
    with pytest.raises(TypeError):
        replace(syntax_fixture(), **{field: []})


def test_profile_module_kinds_and_full_predecessor_ref_are_not_interchangeable():
    value = syntax_fixture()
    with pytest.raises(ContractViolation):
        replace(value, profile_source=declaration("module"))
    with pytest.raises(ContractViolation):
        replace(value.provider_bindings[0], declaration=declaration())
    for coordinate in (
        replace(value.interpretation_profile, role="other"),
        replace(value.interpretation_profile, contract=CONSUMER),
    ):
        with pytest.raises(ContractViolation):
            replace(value, interpretation_profile=coordinate)


def test_provider_duplicates_and_inclusive_limits():
    value = syntax_fixture()
    with pytest.raises(ContractViolation):
        replace(value, provider_bindings=(value.provider_bindings[0],) * 2)
    providers = tuple(
        replace(value.provider_bindings[0], occurrence_ref=f"occ-{i}")
        for i in range(256)
    )
    assert len(replace(value, provider_bindings=providers).provider_bindings) == 256
    with pytest.raises(ContractViolation):
        replace(
            value,
            provider_bindings=providers
            + (replace(providers[0], occurrence_ref="extra"),),
        )
    providers = tuple(
        replace(
            value.provider_bindings[0],
            occurrence_ref=f"occ-{i}",
            semantic_contract=SemanticContractRef(f"ref-{i}", "1", DIGEST),
        )
        for i in range(32)
    )
    assert len(replace(value, provider_bindings=providers).provider_bindings) == 32
    with pytest.raises(ContractViolation):
        replace(
            value,
            provider_bindings=providers
            + (
                replace(
                    providers[0], occurrence_ref="extra", semantic_contract=CONSUMER
                ),
            ),
        )


def test_contribution_inventory_is_ordered_and_bijective():
    value = syntax_fixture()
    for changed in (
        {"contribution_coordinates": tuple(reversed(value.contribution_coordinates))},
        {"contribution_bindings": tuple(reversed(value.contribution_bindings))},
        {"contribution_coordinates": value.contribution_coordinates[:1]},
        {"contribution_bindings": (value.contribution_bindings[0],) * 2},
        {
            "contribution_bindings": (
                value.contribution_bindings[0],
                replace(
                    value.contribution_bindings[1],
                    contribution_coordinate=value.contribution_bindings[
                        0
                    ].contribution_coordinate,
                ),
            )
        },
    ):
        with pytest.raises(ContractViolation):
            replace(value, **changed)
    with pytest.raises(ContractViolation):
        replace(value.contribution_bindings[0], relative_path="other.json")


def test_anchor_bounds_exact_flags_and_canonical_order():
    value = syntax_fixture()
    anchor = value.anchor_requirements[0]
    assert len(replace(anchor, field_path=("s",) * 64).field_path) == 64
    with pytest.raises(ContractViolation):
        replace(anchor, field_path=("s",) * 65)
    for field in ("required", "top_level"):
        with pytest.raises(TypeError):
            replace(anchor, **{field: 1})
    with pytest.raises(ContractViolation):
        replace(value, anchor_requirements=(anchor, anchor))
    with pytest.raises(ContractViolation):
        replace(value, anchor_requirements=(anchor,) * 8193)


def test_contribution_bound_inclusive_and_complete_anchor_inventory():
    value = syntax_fixture()
    bindings = tuple(
        replace(
            value.contribution_bindings[0],
            occurrence_ref=f"occ-{i:03d}",
            contribution_coordinate=replace(
                value.contribution_coordinates[0], value_ref=f"contribution-{i:03d}"
            ),
        )
        for i in range(128)
    )
    coords = tuple(
        sorted(
            (b.contribution_coordinate for b in bindings),
            key=lambda c: canonical_json_bytes(c.to_wire()),
        )
    )
    assert (
        len(
            replace(
                value, contribution_bindings=bindings, contribution_coordinates=coords
            ).contribution_bindings
        )
        == 128
    )
    with pytest.raises(ContractViolation):
        replace(value, contribution_bindings=bindings + (bindings[0],))
    anchors = tuple(
        replace(value.anchor_requirements[0], rule_name=f"r-{i:04d}")
        for i in range(8192)
    )
    anchors = tuple(sorted(anchors, key=lambda a: canonical_json_bytes(a.to_wire())))
    assert len(replace(value, anchor_requirements=anchors).anchor_requirements) == 8192


def test_no_foreign_callbacks_or_subclasses_on_restamped_graphs():
    calls = []

    class Foreign:
        def to_wire(self):
            calls.append("wire")
            raise AssertionError

        def __eq__(self, other):
            calls.append("eq")
            raise AssertionError

    for field in ("profile_source", "code_profile_digest", "interpretation_profile"):
        value = syntax_fixture()
        object.__setattr__(value, field, Foreign())
        with pytest.raises(TypeError):
            value.to_wire()
    for field in (
        "provider_bindings",
        "contribution_coordinates",
        "contribution_bindings",
        "anchor_requirements",
    ):
        value = syntax_fixture()
        object.__setattr__(value, field, (Foreign(),))
        with pytest.raises(TypeError):
            value.to_wire()
    assert calls == []

    class Derived(CodeGrammarDeclarationSourceV1):
        pass

    with pytest.raises(TypeError):
        Derived("repository", "scope", "module", "module.toml", "body", DIGEST, 1)
