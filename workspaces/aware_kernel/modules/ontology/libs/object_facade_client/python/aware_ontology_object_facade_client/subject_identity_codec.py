"""Detached subject profiles. Valid content never establishes original issuance.

Only the existing facade engine owns canonical bytes, Body framing and budgets.
Lower producer/identity schemas remain opaque and require their original owners.
"""

import re
from typing import Any, TypedDict, cast

from . import codec as c
from . import source_read_codec as read
from . import source_read_wire as wire

WireError = read.WireError
EPOCH = "aware.ontology.subject-owner-epoch.v1"
INPUTS = "aware.meta.observable-identity-inputs.v1"
ALLOCATION = "aware.ontology.source-instance-allocation.v1"
ASSOCIATION = "aware.ontology.source-instance-association.v1"
MODEL = "aware.meta.observable-identity-model-admission.v1"
SUBJECT = "aware.ontology.source-observable-subject-admission.v1"
INVENTORY = "aware.ontology.subject-input-inventory.v1"


class SemanticContractRef(TypedDict):
    key: str
    version: str
    schema_digest: str


class SemanticValueCoordinate(TypedDict):
    role: str
    contract: SemanticContractRef
    value_ref: str
    digest: str
    size_bytes: int


class RetainedBody(TypedDict):
    coordinate: SemanticValueCoordinate
    body: wire.Body


Record = dict[str, Any]


def _refs(*keys: str) -> dict[str, str]:
    return dict.fromkeys(keys, "ref")


_INSTANCE_IDS = ("oig_id", "oig_identity_id", "history_branch_id", "oig_branch_id",
                 "class_instance_id", "class_instance_identity_id")
_MODEL_IDS = ("ocg_identity_id", "opg_id", "opg_identity_id", "observable_id",
              "observable_node_id", "root_class_id")
_SCHEMAS: dict[str, tuple[str, dict[str, str]]] = {
    EPOCH: ("epoch_digest", _refs("issuer_ref", "issuer_generation", "source_scope_ref", "source_epoch_ref")
            | {"inventory": "retained_list", "inventory_digest": "digest"}),
    INPUTS: ("evidence_digest", _refs("evidence_ref", "issuer_ref", "issuer_generation", "model_ref", "model_revision_ref")
             | {"source_epoch": "epoch", "products": "retained_list",
                "production_evidence": "retained_list", "derivations": "derivations"}),
    ALLOCATION: ("allocation_digest", _refs("allocation_ref", "issuer_ref", "issuer_generation", "namespace_ref",
                 "context_ref", "owner_ref", "owner_profile_ref", "binding_revision_ref", "model_ref",
                 "identity_definition_ref") | dict.fromkeys(_INSTANCE_IDS, "id")
                 | {"identity_inputs": "body:" + INPUTS, "allocation_epoch": "epoch", "source_identity": "body"}),
    ASSOCIATION: ("association_digest", _refs("association_ref", "issuer_ref", "issuer_generation", "provider_ref",
                  "provider_generation", "owner_profile_ref", "binding_revision_ref")
                  | {"scope": "scope", "allocation": "body:" + ALLOCATION, "source_epoch": "epoch",
                     "original_reading": "retained", "typed_root": "root"}),
    MODEL: ("admission_digest", _refs("admission_ref", "issuer_ref", "issuer_generation", "model_ref",
            "model_revision_ref", "root_type_ref", "projection_ref", "observable_ref",
            "identity_definition_ref", "branch_identity_profile_ref") | dict.fromkeys(_MODEL_IDS, "id")
            | {"identity_inputs": "body:" + INPUTS, "schema_bundle_hash": "digest", "schema_slice_hash": "digest",
               "topology_hash": "digest", "is_branchable": "bool"}),
    SUBJECT: ("admission_digest", _refs("admission_ref", "issuer_ref", "issuer_generation", "owner_profile_ref",
              "binding_revision_ref") | dict.fromkeys((*_INSTANCE_IDS, "observable_branch_id", "observable_branch_node_id"), "id")
              | {"scope": "scope", "meta_model_admission": "body:" + MODEL,
                 "instance_identity_admission": "body:" + ALLOCATION, "source_association": "body:" + ASSOCIATION,
                 "backing_kind": "source_namespace"}),
}
SUPPORTED_CONTRACTS = frozenset(_SCHEMAS)


def _snapshot(value: object) -> Record:
    return c._obj(read.decode_canonical(read.canonical_bytes(value)))


def _retained(value: object) -> Record:
    obj = c._obj(value, {"coordinate", "body"})
    coordinate = c._obj(obj["coordinate"], {"role", "contract", "value_ref", "digest", "size_bytes"})
    contract = c._obj(coordinate["contract"], {"key", "version", "schema_digest"})
    for key in ("key", "version"):
        c._ref(contract[key])
    c._digest(contract["schema_digest"])
    for key in ("role", "value_ref"):
        c._ref(coordinate[key])
    c._digest(coordinate["digest"])
    c._uint(coordinate["size_bytes"], 1, wire.MAX_BODY_BYTES)
    raw = read._body(obj["body"], contract["key"])
    if coordinate["digest"] != obj["body"]["body_hash"] or coordinate["size_bytes"] != len(raw):
        c._fail()
    return obj


def _retained_list(value: object) -> list[Record]:
    if type(value) is not list:
        c._fail()
    items = cast(list[object], value)
    if not 1 <= len(items) <= 256:
        c._fail("limit_exceeded")
    records = [_retained(item) for item in items]
    keys = [(r["coordinate"]["role"].encode(), r["coordinate"]["contract"]["key"].encode(),
             r["coordinate"]["value_ref"].encode()) for r in records]
    if keys != sorted(set(keys)) or len({r["coordinate"]["value_ref"] for r in records}) != len(records):
        c._fail()
    return records


def _derivations(value: object) -> None:
    if type(value) is not list:
        c._fail()
    items = cast(list[object], value)
    if not 1 <= len(items) <= 256:
        c._fail("limit_exceeded")
    roles = []
    for item in items:
        obj = c._obj(item, {"role", "product_ref", "constructor_ref", "function_ref", "arguments", "result_id"})
        for key in ("role", "product_ref", "constructor_ref", "function_ref"):
            c._ref(obj[key])
        read._body(obj["arguments"])
        _field(obj["result_id"], "id")
        roles.append(obj["role"].encode())
    if roles != sorted(set(roles)):
        c._fail()


def _field(value: object, spec: str) -> None:
    if spec == "id":
        if type(value) is not str or re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", value) is None:
            c._fail()
    elif spec == "bool":
        if type(value) is not bool:
            c._fail()
    elif spec == "source_namespace":
        c._enum(value, ("source_namespace",))
    elif spec == "epoch":
        _record(c._obj(value), EPOCH)
    elif spec == "retained":
        _retained(value)
    elif spec == "retained_list":
        _retained_list(value)
    elif spec == "derivations":
        _derivations(value)
    elif spec == "root":
        read.decode_typed_root(read._body(value, wire.ROOT_CONTRACT))
    elif spec.startswith("body:"):
        decode_record(read._body(value, spec[5:]), expected_contract=spec[5:])
    else:
        read._field(value, spec)


def _record(obj: Record, expected: str | None = None) -> None:
    contract = c._ref(obj.get("contract"))
    if contract not in SUPPORTED_CONTRACTS or (expected is not None and contract != expected):
        c._fail("unsupported_contract")
    digest_field, schema = _SCHEMAS[contract]
    c._obj(obj, set(schema) | {"contract", digest_field})
    for key, spec in schema.items():
        _field(obj[key], spec)
    c._digest(obj[digest_field])
    if obj[digest_field] != read.domain_digest(contract, {k: v for k, v in obj.items() if k != digest_field}):
        c._fail()
    if contract == EPOCH:
        if obj["inventory_digest"] != read.domain_digest(INVENTORY, obj["inventory"]):
            c._fail()
    elif contract == INPUTS:
        inventory = obj["source_epoch"]["inventory"]
        declared = obj["products"] + obj["production_evidence"]
        if any(item not in inventory for item in declared):
            c._fail()
        if len({item["coordinate"]["value_ref"] for item in declared}) != len(declared):
            c._fail()
        products = {r["coordinate"]["value_ref"] for r in obj["products"]}
        if any(d["product_ref"] not in products for d in obj["derivations"]):
            c._fail()
    elif contract == ASSOCIATION:
        if obj["original_reading"] not in obj["source_epoch"]["inventory"]:
            c._fail()
    elif contract == ALLOCATION:
        if not any(item["body"] == obj["source_identity"] for item in obj["allocation_epoch"]["inventory"]):
            c._fail()


def validate_record(value: object, *, expected_contract: str | None = None) -> Record:
    """Return a detached checked snapshot, never an owner-issued handle."""
    obj = _snapshot(value)
    _record(obj, expected_contract)
    return obj


def encode_record(value: object, *, expected_contract: str | None = None) -> bytes:
    return read.canonical_bytes(validate_record(value, expected_contract=expected_contract))


def decode_record(raw: bytes, *, expected_contract: str | None = None) -> Record:
    obj = c._obj(read.decode_canonical(raw))
    _record(obj, expected_contract)
    return obj


def encode_retained_body(value: object) -> bytes:
    obj = _snapshot(value)
    _retained(obj)
    return read.canonical_bytes(obj)


def decode_retained_body(raw: bytes) -> Record:
    return _retained(c._obj(read.decode_canonical(raw)))


def validate_derivations(value: object) -> list[Record]:
    snapshot = read.decode_canonical(read.canonical_bytes(value))
    _derivations(snapshot)
    return cast(list[Record], snapshot)


def validate_scope(value: object) -> Record:
    obj = _snapshot(value)
    read._field(obj, "scope")
    return obj
