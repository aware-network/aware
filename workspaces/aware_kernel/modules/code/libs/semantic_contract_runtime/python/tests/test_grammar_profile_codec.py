from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime.codec import encode_profile_declaration
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.grammar_profile_codec import (
    GRAMMAR_PROFILE_CODEC_IMPLEMENTATION,
    GRAMMAR_SYNTAX_V2_CODEC_IMPLEMENTATION,
    CodeGrammarProfileSelectionCodec,
    CodeGrammarSyntaxBindingCodec,
    decode_grammar_syntax_binding,
    encode_grammar_syntax_binding,
    grammar_profile_selection_body,
    grammar_syntax_binding_body,
)
from aware_code_semantic_contract_runtime.grammar_profile_contract import (
    GRAMMAR_PROFILE_RESULT_REF,
    GRAMMAR_SYNTAX_BINDING_V2_REF,
    MAX_GRAMMAR_BODY_BYTES,
)
from test_grammar_profile_contract import ROOT, syntax_fixture
from test_profile_runtime import profile


def test_real_code_owner_round_trip_and_body_identity():
    value = syntax_fixture()
    body = encode_grammar_syntax_binding(value)
    assert decode_grammar_syntax_binding(body) == value
    codec = CodeGrammarSyntaxBindingCodec()
    assert codec.decode(codec.encode(value)) == value
    retained = grammar_syntax_binding_body(value)
    assert retained.canonical_body == body
    assert retained.coordinate.contract == GRAMMAR_SYNTAX_BINDING_V2_REF
    assert retained.coordinate.role == "code.syntax_binding"
    assert retained.coordinate.digest == ContentDigest.of_bytes(body)
    assert retained.coordinate.size_bytes == len(body)
    assert (
        retained.coordinate.value_ref
        == "code-grammar-syntax-binding:" + retained.coordinate.digest.value
    )


def test_profile_adapter_preserves_complete_original_wire():
    value = profile()
    codec = CodeGrammarProfileSelectionCodec()
    body = codec.encode(value)
    assert body == encode_profile_declaration(value).encode("utf-8")
    assert codec.decode(body) == value
    retained = grammar_profile_selection_body(value)
    assert retained.canonical_body == body
    assert retained.coordinate.contract == GRAMMAR_PROFILE_RESULT_REF
    assert retained.coordinate.digest == ContentDigest.of_bytes(body) != value.digest
    assert (
        retained.coordinate.value_ref
        == "code-profile-selection:" + retained.coordinate.digest.value
    )


def test_codec_recipe_identity_matches_accepted_original_recipe():
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
    for implementation, reference, name, recipe in (
        (
            GRAMMAR_PROFILE_CODEC_IMPLEMENTATION,
            GRAMMAR_PROFILE_RESULT_REF,
            base["codec_implementations"]["profile"]["implementation_ref"],
            base["codec_implementations"]["profile"]["recipe"],
        ),
        (
            GRAMMAR_SYNTAX_V2_CODEC_IMPLEMENTATION,
            GRAMMAR_SYNTAX_BINDING_V2_REF,
            amendment["syntax_successor"]["codec_implementation_ref"],
            amendment["syntax_successor"]["codec_recipe"],
        ),
    ):
        assert implementation.implementation_ref == name
        assert implementation.closure_digest == ContentDigest.of_bytes(
            canonical_json_bytes({"contract": reference.to_wire(), "recipe": recipe})
        )


@pytest.mark.parametrize(
    "location",
    (
        "root",
        "profile_source",
        "provider",
        "provider_source",
        "contribution",
        "anchor",
        "coordinate",
        "reference",
    ),
)
@pytest.mark.parametrize("mutation", ("extra", "missing", "null"))
def test_every_nested_wire_is_closed(location, mutation):
    wire = syntax_fixture().to_wire()
    rows = {
        "root": wire,
        "profile_source": wire["profile_source"],
        "provider": wire["provider_bindings"][0],
        "provider_source": wire["provider_bindings"][0]["declaration"],
        "contribution": wire["contribution_bindings"][0],
        "anchor": wire["anchor_requirements"][0],
        "coordinate": wire["interpretation_profile"],
        "reference": wire["interpretation_profile"]["contract"],
    }
    row = rows[location]
    key = next(iter(row))
    if mutation == "extra":
        row["extra"] = "not permitted"
    elif mutation == "missing":
        del row[key]
    else:
        row[key] = None
    with pytest.raises((TypeError, ContractViolation)):
        decode_grammar_syntax_binding(canonical_json_bytes(wire))


@pytest.mark.parametrize(
    "location", ("root", "profile_source", "provider", "contribution", "anchor")
)
def test_duplicate_contract_keys_refuse_even_when_values_equal(location):
    wire = syntax_fixture().to_wire()
    literals = {
        "root": "aware.code.grammar-syntax-binding.v2",
        "profile_source": "aware.code.grammar-declaration-source.v1",
        "provider": "aware.code.grammar-provider-binding.v2",
        "contribution": "aware.code.grammar-contribution-binding.v1",
        "anchor": "aware.code.grammar-anchor-requirement.v1",
    }
    fragment = '"contract":"' + literals[location] + '"'
    body = canonical_json_bytes(wire).replace(
        fragment.encode(), (fragment + "," + fragment).encode(), 1
    )
    with pytest.raises(ContractViolation):
        decode_grammar_syntax_binding(body)


@pytest.mark.parametrize(
    "bad",
    (
        b"",
        b"null",
        b"[]",
        b"NaN",
        b"{}\n",
        b"\xff",
        b"\xef\xbb\xbf{}",
        b'{"a":1,"a":1}',
        b"[" * 1200 + b"]" * 1200,
    ),
)
def test_invalid_json_refuses(bad):
    with pytest.raises((TypeError, ContractViolation)):
        decode_grammar_syntax_binding(bad)


@pytest.mark.parametrize(
    "decoder",
    (decode_grammar_syntax_binding, CodeGrammarProfileSelectionCodec().decode),
)
def test_bound_checked_before_json_and_exact_bytes_required(decoder):
    with pytest.raises(ContractViolation):
        decoder(b" " * (MAX_GRAMMAR_BODY_BYTES + 1))
    with pytest.raises(TypeError):
        decoder(bytearray(b"{}"))


@pytest.mark.parametrize("value", ("aware.code.grammar-syntax-binding.v1", "other"))
def test_syntax_version_has_no_fallback(value):
    wire = syntax_fixture().to_wire()
    wire["contract"] = value
    with pytest.raises(ContractViolation):
        decode_grammar_syntax_binding(canonical_json_bytes(wire))


def test_nullable_bool_and_digest_substitutions_refuse():
    for path, bad in (
        (("anchor_requirements", 0, "required"), 1),
        (("code_profile_digest",), "sha256:" + "A" * 64),
        (("profile_source", "size_bytes"), True),
        (("profile_source", "content_digest"), None),
    ):
        wire = syntax_fixture().to_wire()
        target = wire
        for part in path[:-1]:
            target = target[part]
        target[path[-1]] = bad
        with pytest.raises((TypeError, ContractViolation)):
            decode_grammar_syntax_binding(canonical_json_bytes(wire))


def test_noncanonical_bytes_and_profile_digest_changes_refuse():
    value = syntax_fixture()
    with pytest.raises(ContractViolation):
        decode_grammar_syntax_binding(json.dumps(value.to_wire(), indent=2).encode())
    wire = profile().to_wire()
    wire["digest"] = ContentDigest.of_bytes(b"foreign").value
    with pytest.raises(ContractViolation):
        CodeGrammarProfileSelectionCodec().decode(canonical_json_bytes(wire))


def test_complete_syntax_byte_bound_after_valid_collection_checks():
    value = syntax_fixture()
    anchors = tuple(
        replace(
            value.anchor_requirements[0],
            rule_name=f"r-{i:04d}",
            field_path=("x" * 512,) * 64,
        )
        for i in range(260)
    )
    anchors = tuple(sorted(anchors, key=lambda a: canonical_json_bytes(a.to_wire())))
    with pytest.raises(ContractViolation, match="body exceeds bound"):
        replace(value, anchor_requirements=anchors)


def test_portable_body_has_no_retained_use_or_admission_handle():
    body = grammar_syntax_binding_body(syntax_fixture())
    assert not hasattr(body, "source_admission")
    assert not hasattr(body, "registration")
    assert not hasattr(body, "cleanup_ticket")


def test_real_root_exports_and_site_free_source_import(tmp_path):
    source = (
        ROOT
        / "workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python"
    )
    script = (
        "import sys; import aware_code_semantic_contract_runtime as c; "
        "assert len(c.__all__) == len(set(c.__all__)); "
        "assert all(hasattr(c, n) for n in c.__all__); "
        "assert c.CodeGrammarSyntaxBindingCodec.contract == c.GRAMMAR_SYNTAX_BINDING_V2_REF; "
        "assert not any(n.startswith(('aware_workspace', 'aware_language', 'aware_meta', "
        "'aware_ontology', 'aware_dev', 'aware_sdk', 'aware_service')) for n in sys.modules)"
    )
    subprocess.run(
        [sys.executable, "-B", "-S", "-c", script],
        cwd=tmp_path,
        env={
            "PYTHONPATH": str(source),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PATH": os.defpath,
        },
        check=True,
    )
