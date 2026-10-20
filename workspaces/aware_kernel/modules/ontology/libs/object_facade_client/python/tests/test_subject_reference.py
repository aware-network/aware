"""Requested values only: fixtures are never original Meta/source issuance."""

import ast
import json
from dataclasses import replace
from pathlib import Path
from uuid import UUID

import pytest
from aware_ontology_object_facade_client.subject_reference import (
    MAX_SUBJECT_REFERENCE_BYTES,
    SubjectIdentity,
    SubjectIdentityRole,
    SubjectReference,
    SubjectReferenceError,
    decode_subject_reference,
    encode_subject_reference,
)


def identity(role, number):
    return SubjectIdentity(
        role,
        "fixture:identity-profile:1",
        "meta-identity-product:sha256:" + "a" * 64,
        UUID(int=number),
        UUID(int=number + 10),
        UUID(int=number + 20),
    )


def reference():
    return SubjectReference(
        "fixture:namespace",
        "fixture:context",
        "fixture:existing-branch",
        identity(SubjectIdentityRole.PROJECTION, 1),
        identity(SubjectIdentityRole.OBSERVABLE_CONFIG, 2),
        identity(SubjectIdentityRole.SOURCE_ANCHOR, 3),
    )


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()


def test_roundtrip_is_content_not_issued_subject_or_object():
    original = reference()
    body = encode_subject_reference(original)
    copied = decode_subject_reference(body)
    assert copied == original and copied is not original
    assert encode_subject_reference(copied) == body
    for claim in (
        "read",
        "instance_ref",
        "admission_ref",
        "runtime_observable_id",
        "subject_id",
    ):
        assert not hasattr(original, claim)


@pytest.mark.parametrize("case", ["root", "identity", "deleted_field"])
def test_uninitialized_or_incomplete_values_refuse(case):
    if case == "root":
        value = object.__new__(SubjectReference)
    elif case == "identity":
        with pytest.raises(SubjectReferenceError):
            replace(reference(), source_anchor=object.__new__(SubjectIdentity))
        return
    else:
        value = reference()
        object.__delattr__(value, "namespace_ref")
    with pytest.raises(SubjectReferenceError):
        encode_subject_reference(value)


@pytest.mark.parametrize("field", ["namespace_ref", "context_ref", "branch_ref"])
@pytest.mark.parametrize(
    "value",
    ["", "with space", "line\nbreak", "x\x00y", "x" * 513, True, None, "\ud800"],
)
def test_invalid_context_tokens_refuse(field, value):
    with pytest.raises(SubjectReferenceError):
        replace(reference(), **{field: value})


@pytest.mark.parametrize("slot", ["projection", "observable_config", "source_anchor"])
def test_wrong_semantic_role_refuses(slot):
    wrong = identity(
        SubjectIdentityRole.SOURCE_ANCHOR
        if slot != "source_anchor"
        else SubjectIdentityRole.PROJECTION,
        7,
    )
    with pytest.raises(SubjectReferenceError, match="identity_role_mismatch"):
        replace(reference(), **{slot: wrong})


@pytest.mark.parametrize("field", ["class_id", "constructor_id", "value"])
def test_string_uuid_not_silently_normalized(field):
    with pytest.raises(SubjectReferenceError, match="exact_uuid_required"):
        replace(reference().source_anchor, **{field: str(UUID(int=1))})


@pytest.mark.parametrize("field", ["namespace_ref", "context_ref", "branch_ref"])
def test_reference_mutation_refuses_and_post_init_does_not_repair(field):
    value = reference()
    object.__setattr__(value, field, "fixture:substituted")
    with pytest.raises(SubjectReferenceError, match="reference_mutated"):
        encode_subject_reference(value)
    with pytest.raises(SubjectReferenceError, match="reference_mutated"):
        value.__post_init__()
    assert getattr(value, field) == "fixture:substituted"


@pytest.mark.parametrize(
    "field", ["profile_ref", "product_ref", "class_id", "constructor_id", "value"]
)
def test_nested_mutation_refuses_without_repair(field):
    value = reference()
    changed = (
        "fixture:changed"
        if field == "profile_ref"
        else (
            "meta-identity-product:sha256:" + "b" * 64
            if field == "product_ref"
            else UUID(int=91)
        )
    )
    object.__setattr__(value.source_anchor, field, changed)
    with pytest.raises(SubjectReferenceError):
        encode_subject_reference(value)
    with pytest.raises(SubjectReferenceError):
        value.source_anchor.__post_init__()
    assert getattr(value.source_anchor, field) == changed


@pytest.mark.parametrize(
    "field",
    [
        "permission",
        "current",
        "instance_ref",
        "runtime_observable_id",
        "source_revision",
    ],
)
def test_extra_claims_refuse(field):
    wire = json.loads(encode_subject_reference(reference()))
    wire[field] = "fixture:claim"
    with pytest.raises(SubjectReferenceError):
        decode_subject_reference(canonical(wire))


@pytest.mark.parametrize(
    "case",
    [
        "nested_extra",
        "unknown_role",
        "unknown_contract",
        "missing_branch",
        "config_as_root",
        "wrong_uuid",
        "wrong_product",
        "bool_uuid",
    ],
)
def test_malformed_or_role_substituted_wire_refuses(case):
    wire = json.loads(encode_subject_reference(reference()))
    if case == "nested_extra":
        wire["source_anchor"]["verified"] = True
    elif case == "unknown_role":
        wire["source_anchor"]["role"] = "object_address"
    elif case == "unknown_contract":
        wire["contract"] = "aware.ontology.issued-subject.v1"
    elif case == "missing_branch":
        del wire["branch_ref"]
    elif case == "config_as_root":
        wire["source_anchor"] = wire["observable_config"]
    elif case == "wrong_uuid":
        wire["source_anchor"]["value"] = UUID(int=1).hex
    elif case == "wrong_product":
        wire["source_anchor"]["product_ref"] = "caller:hash"
    else:
        wire["source_anchor"]["value"] = True
    with pytest.raises(SubjectReferenceError):
        decode_subject_reference(canonical(wire))


def test_duplicate_noncanonical_and_oversized_bodies_refuse():
    body = encode_subject_reference(reference())
    for invalid in (
        b'{"namespace_ref":"foreign",' + body[1:],
        body + b"\n",
        b"[]",
        b"null",
        b"",
        b"x" * (MAX_SUBJECT_REFERENCE_BYTES + 1),
        b"[" * 2000 + b"]" * 2000,
        body.decode(),
    ):
        with pytest.raises(SubjectReferenceError):
            decode_subject_reference(invalid)


def test_valid_coherent_substitution_is_another_request_not_authority():
    original = reference()
    other = replace(
        original, source_anchor=replace(original.source_anchor, value=UUID(int=999))
    )
    assert decode_subject_reference(encode_subject_reference(other)) == other
    assert other != original
    assert not hasattr(other, "verified")


def test_nonidentity_read_epochs_do_not_enter_reference_contract():
    wire = json.loads(encode_subject_reference(reference()))
    assert set(wire) == {
        "contract",
        "namespace_ref",
        "context_ref",
        "branch_ref",
        "projection",
        "observable_config",
        "source_anchor",
    }
    assert not {
        "head",
        "source_revision",
        "provider_generation",
        "focus",
        "actor",
    } & set(wire)


def test_reference_implementation_has_no_identity_engine_or_source_owner_import():
    module = (
        Path(__file__).resolve().parents[1]
        / "aware_ontology_object_facade_client/subject_reference.py"
    )
    tree = ast.parse(module.read_bytes())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert {item.name for item in node.names} <= {"re"}
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                assert node.level == 1 and node.module == "codec"
            else:
                assert node.module in {
                    "__future__",
                    "dataclasses",
                    "enum",
                    "typing",
                    "uuid",
                }
                assert all(item.name != "uuid5" for item in node.names)
