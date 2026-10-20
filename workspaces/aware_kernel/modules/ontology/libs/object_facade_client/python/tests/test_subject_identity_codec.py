"""Synthetic detached content only: no allocator, original issuer or View grant."""

import copy
import hashlib
import json
from typing import Any

import pytest

from aware_ontology_object_facade_client import source_read_codec as read
from aware_ontology_object_facade_client import source_read_wire as wire
from aware_ontology_object_facade_client import subject_identity_codec as codec


def signed(value: dict[str, Any], field: str) -> dict[str, Any]:
    value[field] = read.domain_digest(value["contract"], {k: v for k, v in value.items() if k != field})
    return value


def redigest_probe(value: dict[str, Any], field: str) -> None:
    """Unchecked TEST serialization deliberately bypasses valid-Body admission."""
    raw = json.dumps({k: v for k, v in value.items() if k != field},
        sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
    value[field] = "sha256:" + hashlib.sha256(value["contract"].encode() + b"\x00" + raw).hexdigest()


def body(contract: str, value: object) -> dict[str, str]:
    return dict(read.make_body(contract, read.canonical_bytes(value)))


def retained(role: str, ref: str, framed: dict[str, str]) -> dict[str, Any]:
    return {"coordinate": {"role": role, "value_ref": ref,
            "contract": {"key": framed["contract_ref"], "version": "1", "schema_digest": "sha256:" + "a" * 64},
            "digest": framed["body_hash"], "size_bytes": len(bytes.fromhex(framed["body_hex"]))}, "body": framed}


def epoch(items: list[dict[str, Any]]) -> dict[str, Any]:
    inventory = sorted(items, key=lambda r: (r["coordinate"]["role"].encode(),
        r["coordinate"]["contract"]["key"].encode(), r["coordinate"]["value_ref"].encode()))
    return signed({"contract": codec.EPOCH, "issuer_ref": "fixture:owner", "issuer_generation": "fixture:generation",
        "source_scope_ref": "fixture:scope", "source_epoch_ref": "fixture:historical-epoch",
        "inventory": inventory, "inventory_digest": read.domain_digest(codec.INVENTORY, inventory)}, "epoch_digest")


def sample() -> dict[str, Any]:
    """Coherent content; expectations and IDs are fabricated, not Meta-issued."""
    names = ("ocg_identity_id", "opg_id", "opg_identity_id", "observable_id", "observable_node_id", "root_class_id",
        "oig_id", "oig_identity_id", "history_branch_id", "oig_branch_id", "class_instance_id",
        "class_instance_identity_id", "observable_branch_id", "observable_branch_node_id")
    ids = {name: f"00000000-0000-0000-0000-{i:012x}" for i, name in enumerate(names, 1)}
    product = retained("artifact:product", "fixture:product", body("fixture.product.v1", {"detached": True}))
    production = retained("artifact:production", "fixture:production", body("fixture.production.v1", {"detached": True}))
    derivations = sorted([{"role": "result:" + name, "product_ref": "fixture:product", "constructor_ref": "fixture:constructor",
        "function_ref": "fixture:function:" + name, "arguments": body("fixture.arguments.v1", {"detached": True}),
        "result_id": identity} for name, identity in ids.items()], key=lambda d: d["role"].encode())
    inputs = signed({"contract": codec.INPUTS, "evidence_ref": "fixture:inputs", "issuer_ref": "fixture:meta",
        "issuer_generation": "fixture:meta-generation", "model_ref": "fixture:model", "model_revision_ref": "fixture:model-revision",
        "source_epoch": epoch([product, production]), "products": [product], "production_evidence": [production],
        "derivations": derivations}, "evidence_digest")
    model = signed({"contract": codec.MODEL, "admission_ref": "fixture:model-admission", "issuer_ref": "fixture:meta",
        "issuer_generation": "fixture:meta-generation", "model_ref": "fixture:model", "model_revision_ref": "fixture:model-revision",
        "root_type_ref": "type:root", "projection_ref": "projection:one", "observable_ref": "observable:one",
        **{k: ids[k] for k in names[:6]}, "identity_inputs": body(codec.INPUTS, inputs),
        "schema_bundle_hash": body("aware.meta.semantic-type-schema.v1", {})["body_hash"],
        "schema_slice_hash": body("aware.meta.semantic-type-schema-slice.v1", {})["body_hash"],
        "topology_hash": body("aware.ontology.runtime-schema-topology.v5", {})["body_hash"],
        "identity_definition_ref": "fixture:identity-definition", "branch_identity_profile_ref": "fixture:branch-profile",
        "is_branchable": True}, "admission_digest")
    model_binding = signed({"contract": wire.MODEL_CONTRACT, "model_ref": "fixture:model", "model_revision_ref": "fixture:model-revision",
        "root_type_ref": "type:root", "projection_ref": "projection:one", "model_admission": body(codec.MODEL, model),
        "schema_bundle": body("aware.meta.semantic-type-schema.v1", {}),
        "schema_slice": body("aware.meta.semantic-type-schema-slice.v1", {}),
        "topology": body("aware.ontology.runtime-schema-topology.v5", {})}, "model_digest")
    scope = {"ontology_ref": "ontology:one", "namespace_ref": "namespace:one", "context_ref": "context:one",
        "branch_ref": "opaque:branch-address", "object_ref": "opaque:object-address", "root_type_ref": "type:root",
        "observable_ref": "observable:one", "projection_ref": "projection:one", "model_digest": model_binding["model_digest"]}
    source = body("fixture.source-identity.v1", {"key": "content-owned-not-a-path"})
    allocation = signed({"contract": codec.ALLOCATION, "allocation_ref": "fixture:allocation", "issuer_ref": "fixture:namespace-owner",
        "issuer_generation": "fixture:namespace-generation", "namespace_ref": "namespace:one", "context_ref": "context:one",
        "owner_ref": "fixture:owner", "owner_profile_ref": "fixture:allocation-profile", "binding_revision_ref": "fixture:allocation-revision",
        "model_ref": "fixture:model", "identity_definition_ref": "fixture:identity-definition", "identity_inputs": body(codec.INPUTS, inputs),
        "allocation_epoch": epoch([retained("source:identity", "fixture:identity", source)]), "source_identity": source,
        **{k: ids[k] for k in names[6:12]}}, "allocation_digest")
    root = {"contract": wire.ROOT_CONTRACT, "object": {"instance_ref": scope["object_ref"], "type_ref": "type:root", "fields": []}}
    original = retained("source:reading", "fixture:reading", body("fixture.reading.v1", {"detached": True}))
    association = signed({"contract": codec.ASSOCIATION, "association_ref": "fixture:association", "issuer_ref": "fixture:provider-owner",
        "issuer_generation": "fixture:provider-owner-generation", "scope": scope, "provider_ref": "fixture:provider",
        "provider_generation": "fixture:provider-generation", "owner_profile_ref": "fixture:provider-profile",
        "binding_revision_ref": "fixture:provider-binding", "allocation": body(codec.ALLOCATION, allocation),
        "source_epoch": epoch([original]), "original_reading": original, "typed_root": body(wire.ROOT_CONTRACT, root)}, "association_digest")
    admission = signed({"contract": codec.SUBJECT, "admission_ref": "fixture:subject", "issuer_ref": "fixture:namespace-owner",
        "issuer_generation": "fixture:namespace-generation", "owner_profile_ref": "fixture:provider-profile",
        "binding_revision_ref": "fixture:provider-binding", "scope": scope, "meta_model_admission": body(codec.MODEL, model),
        "instance_identity_admission": body(codec.ALLOCATION, allocation), "source_association": body(codec.ASSOCIATION, association),
        **{k: ids[k] for k in names[6:]}, "backing_kind": "source_namespace"}, "admission_digest")
    binding = signed({"contract": wire.BINDING_CONTRACT, "owner_ref": "fixture:owner", "provider_ref": "fixture:provider",
        "provider_generation": "fixture:provider-generation", "owner_profile_ref": "fixture:provider-profile",
        "binding_revision_ref": "fixture:provider-binding", "scope": scope, "namespace_admission": body(codec.SUBJECT, admission)}, "binding_digest")
    return {"epoch": epoch([original]), "inputs": inputs, "allocation": allocation, "association": association,
        "model": model, "subject": admission, "model_binding": model_binding, "provider_binding": binding,
        "root": root, "scope": scope, "derivations": derivations, "result_roles": {k: "result:" + k for k in names}}


SIGNED = {"epoch": "epoch_digest", "inputs": "evidence_digest", "allocation": "allocation_digest",
    "association": "association_digest", "model": "admission_digest", "subject": "admission_digest"}


@pytest.mark.parametrize("name", SIGNED)
def test_all_wrapper_roundtrips_preserve_epochs_and_content_without_authority(name: str) -> None:
    value = sample()[name]
    assert codec.decode_record(codec.encode_record(value)) == value
    assert codec.validate_record(value) == value
    assert codec.validate_record(value) is not value


@pytest.mark.parametrize("name", SIGNED)
@pytest.mark.parametrize("defect", ["extra", "missing", "issuer_type", "contract", "digest", "digest_domain"])
def test_redigested_wrappers_fail_closed(name: str, defect: str) -> None:
    value = sample()[name]
    if defect == "extra": value["current"] = True
    elif defect == "missing": del value["issuer_ref"]
    elif defect == "issuer_type": value["issuer_ref"] = 1
    elif defect == "contract": value["contract"] += ".foreign"
    if defect not in ("digest", "digest_domain"):
        signed(value, SIGNED[name])
    else:
        value[SIGNED[name]] = "sha256:" + "0" * 64 if defect == "digest" else read.domain_digest("fixture:wrong-domain", value)
    with pytest.raises(codec.WireError): codec.decode_record(read.canonical_bytes(value))


@pytest.mark.parametrize("defect", ["uuid", "bool", "version", "size", "coordinate_digest", "body", "contract", "inventory", "order", "duplicate", "products", "role", "arguments"])
def test_nested_malformed_and_relabelled_data_refuses(defect: str) -> None:
    value = sample()["inputs"]
    if defect == "uuid": value["derivations"][0]["result_id"] = "00000000-0000-0000-0000-00000000000A"
    elif defect == "bool": value["source_epoch"]["inventory"][0]["coordinate"]["size_bytes"] = True
    elif defect == "version": value["source_epoch"]["inventory"][0]["coordinate"]["contract"]["version"] = 1
    elif defect == "size": value["source_epoch"]["inventory"][0]["coordinate"]["size_bytes"] += 1
    elif defect == "coordinate_digest": value["source_epoch"]["inventory"][0]["coordinate"]["digest"] = "sha256:" + "0" * 64
    elif defect == "body": value["source_epoch"]["inventory"][0]["body"]["body_hash"] = "sha256:" + "0" * 64
    elif defect == "contract": value["source_epoch"]["inventory"][0]["coordinate"]["contract"]["key"] = "foreign:key"
    elif defect == "inventory": value["source_epoch"]["inventory"] = []
    elif defect == "order": value["source_epoch"]["inventory"].reverse()
    elif defect == "duplicate": value["source_epoch"]["inventory"].append(copy.deepcopy(value["source_epoch"]["inventory"][0]))
    elif defect == "products": value["products"][0]["coordinate"]["value_ref"] = "foreign:product"
    elif defect == "role": value["derivations"].append(copy.deepcopy(value["derivations"][0]))
    elif defect == "arguments": value["derivations"][0]["arguments"]["body_hash"] = "sha256:" + "0" * 64
    raw = json.dumps(value["source_epoch"]["inventory"], sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    value["source_epoch"]["inventory_digest"] = "sha256:" + hashlib.sha256(codec.INVENTORY.encode() + b"\x00" + raw).hexdigest()
    redigest_probe(value["source_epoch"], "epoch_digest")
    redigest_probe(value, "evidence_digest")
    with pytest.raises(codec.WireError): codec.encode_record(value)


@pytest.mark.parametrize("name", ["allocation", "association", "model", "subject"])
def test_unknown_nested_profile_is_not_a_message_selected_parser(name: str) -> None:
    value = sample()[name]
    slot = {"allocation": "identity_inputs", "association": "allocation", "model": "identity_inputs", "subject": "meta_model_admission"}[name]
    value[slot]["contract_ref"] = "foreign:profile"
    signed(value, SIGNED[name])
    with pytest.raises(codec.WireError, match="unsupported_contract"): codec.encode_record(value)


def test_retained_common_grammar_roundtrip_and_no_parent_mutation_repair() -> None:
    value = sample()["inputs"]["products"][0]
    assert codec.decode_retained_body(codec.encode_retained_body(value)) == value
    epoch_value = sample()["epoch"]
    epoch_value["issuer_generation"] = "foreign:generation"
    before = copy.deepcopy(epoch_value)
    with pytest.raises(codec.WireError): codec.validate_record(epoch_value)
    assert epoch_value == before


@pytest.mark.parametrize("raw", [b'{"contract":1,"contract":2}', b'{ "contract":1}', b'[]', b'null'])
def test_duplicate_noncanonical_and_wrong_container_refuse(raw: bytes) -> None:
    with pytest.raises(codec.WireError): codec.decode_record(raw)


def test_no_bool_state_or_canonical_grade_and_wrong_expected_contract() -> None:
    model = sample()["model"]
    model["is_branchable"] = 1
    signed(model, "admission_digest")
    with pytest.raises(codec.WireError): codec.encode_record(model)
    value = sample()["subject"]
    value["backing_kind"] = "canonical"
    signed(value, "admission_digest")
    with pytest.raises(codec.WireError): codec.encode_record(value)
    with pytest.raises(codec.WireError): codec.decode_record(codec.encode_record(sample()["epoch"]), expected_contract=codec.MODEL)


def test_complete_inventory_bound_refuses_overflow_instead_of_truncation() -> None:
    items = [retained("artifact:one", f"fixture:item:{i:03d}", body("fixture.opaque.v1", {"i": i})) for i in range(257)]
    with pytest.raises(codec.WireError, match="limit_exceeded"): codec.encode_record(epoch(items))


@pytest.mark.parametrize("name", ["allocation", "association"])
def test_consumed_source_or_reading_cannot_disappear_from_declared_inventory(name: str) -> None:
    value = sample()[name]
    slot = "allocation_epoch" if name == "allocation" else "source_epoch"
    value[slot] = epoch([retained("source:foreign", "fixture:foreign", body("fixture.foreign.v1", {}))])
    signed(value, SIGNED[name])
    with pytest.raises(codec.WireError): codec.encode_record(value)


def test_same_ref_under_different_inventory_role_and_scope_unknown_field_refuse() -> None:
    item = sample()["inputs"]["products"][0]
    other = copy.deepcopy(item)
    other["coordinate"]["role"] = "z:another-role"
    with pytest.raises(codec.WireError): codec.encode_record(epoch([item, other]))
    value = sample()["association"]
    value["scope"]["current"] = True
    signed(value, "association_digest")
    with pytest.raises(codec.WireError): codec.encode_record(value)


@pytest.mark.parametrize("raw", [b'{"number":-0.0}', b'{"deadline":"1.000"}', b'\x00\xffopaque-owner-bytes'])
def test_lower_owner_bytes_are_preserved_not_semantically_rewritten(raw: bytes) -> None:
    framed = dict(read.make_body("fixture.opaque.v1", raw))
    value = retained("source:opaque", "fixture:opaque", framed)
    result = codec.decode_retained_body(codec.encode_retained_body(value))
    assert bytes.fromhex(result["body"]["body_hex"]) == raw
    assert result == value
