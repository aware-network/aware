"""Strict V5 HEAD data for the existing materialization publisher.

The original publisher must separately authenticate installation, lineage,
selected completion and owner currentness. These codecs and byte checks issue
no approval, store authority, predecessor view or publication capability.
"""

from __future__ import annotations

import json
import math
from typing import Never, cast

from aware_code_semantic_contract_runtime import ContentDigest, canonical_json_bytes

from . import semantic_materialization_publication as publication

HEAD_CONTRACT = "aware.workspace.semantic-materialization-head.v5"
BINDING_CONTRACT = "aware.workspace.retained-owner-body-binding.v1"
_HEAD_FIELDS = frozenset(
    (
        "contract",
        "base_head",
        "package_occurrence",
        "incarnation_ref",
        "source_epoch_digest",
        "meta_pair_binding",
        "ontology_product_binding",
        "predecessor_head_digest",
        "operation_ref",
        "operation_digest",
        "output_state_bindings",
        "head_digest",
    )
)
_BINDING_FIELDS = frozenset(
    (
        "contract",
        "role",
        "owner_contract",
        "coordinate_digest",
        "body_ref",
        "body_digest",
        "body_size",
    )
)
_BINDING_ROLES = frozenset(
    (
        "meta_committed_pair",
        "ontology_terminal_product",
        "public_v5_head",
        "lineage_checkpoint",
    )
)
_MAX_HEAD_BYTES = 262_144
_MAX_BODY_BYTES = 67_108_864


def _reject(message: str) -> Never:
    raise publication.WorkspaceSemanticMaterializationPublicationError(message)


def _native(value: object, *, metadata_tokens: bool = False) -> None:
    """Reject foreign behavior and bound traversal before existing decoders."""
    remaining = 20_000
    stack = [(value, 0)]
    while stack:
        item, depth = stack.pop()
        remaining -= 1
        if remaining < 0 or depth > 20:
            _reject("V5 HEAD metadata traversal bound")
        if item is None or type(item) in (int, bool):
            continue
        if type(item) is str:
            text = item
            if len(text) > _MAX_HEAD_BYTES:
                _reject("V5 HEAD metadata string bound")
            try:
                if len(text.encode("utf-8")) > _MAX_HEAD_BYTES:
                    _reject("V5 HEAD metadata string bound")
            except UnicodeError as error:
                raise publication.WorkspaceSemanticMaterializationPublicationError(
                    "V5 invalid UTF-8 metadata"
                ) from error
            if metadata_tokens:
                _ = publication._v5_text(text, _MAX_HEAD_BYTES)
        elif type(item) is float:
            number = item
            if not math.isfinite(number) or (
                number == 0 and math.copysign(1, number) < 0
            ):
                _reject("V5 noncanonical JSON number")
        elif type(item) is list:
            rows = cast(list[object], item)
            if len(rows) > 20_000:
                _reject("V5 HEAD metadata collection bound")
            stack.extend((row, depth + 1) for row in rows)
        elif type(item) is dict:
            fields = cast(dict[object, object], item)
            if len(fields) > 20_000:
                _reject("V5 HEAD metadata collection bound")
            for key, row in fields.items():
                if type(key) is not str:
                    _reject("V5 HEAD exact metadata key required")
                if metadata_tokens:
                    _ = publication._v5_text(key, 192, token=True)
                stack.append((row, depth + 1))
        else:
            _reject("V5 HEAD exact native metadata required")


def _binding(value: object, *, role: str | None = None) -> dict[str, object]:
    fields = publication._v5_fields(value, _BINDING_FIELDS)
    if publication._v5_text(fields["contract"], 192, token=True) != BINDING_CONTRACT:
        _reject("V5 owner-body binding contract differs")
    actual_role = publication._v5_text(fields["role"], 192, token=True)
    if actual_role not in _BINDING_ROLES or (role is not None and actual_role != role):
        _reject("V5 owner-body binding role differs")
    owner = publication._v5_text(fields["owner_contract"], 192, token=True)
    coordinate = publication._v5_sha(fields["coordinate_digest"])
    digest = publication._v5_sha(fields["body_digest"])
    body_ref = publication._v5_text(fields["body_ref"], 192, token=True)
    if body_ref != publication._body_ref(digest):
        _reject("V5 owner-body reference differs from digest")
    size = fields["body_size"]
    if type(size) is not int or not 1 <= size <= _MAX_BODY_BYTES:
        _reject("V5 owner-body size bound")
    result: dict[str, object] = {
        "contract": BINDING_CONTRACT,
        "role": actual_role,
        "owner_contract": owner,
        "coordinate_digest": coordinate,
        "body_ref": body_ref,
        "body_digest": digest,
        "body_size": size,
    }
    if len(canonical_json_bytes(result)) > 4096:
        _reject("V5 owner-body binding byte bound")
    return result


def verify_retained_owner_body(
    binding: object,
    *,
    coordinate_wire: object,
    body: bytes,
) -> None:
    """Compare semantic-owner commitments; original verification stays required.

    Owner bodies are hashed, never decoded or expanded into semantic graphs.
    The owner supplies their canonical bytes and authenticates their meaning.
    """
    fields = _binding(binding)
    if fields["role"] not in ("meta_committed_pair", "ontology_terminal_product"):
        _reject("V5 semantic-owner body role required")
    _native(coordinate_wire)
    coordinate_bytes = canonical_json_bytes(coordinate_wire)
    if len(coordinate_bytes) > 8192:
        _reject("V5 owner coordinate byte bound")
    if type(body) is not bytes or len(body) != fields["body_size"]:
        _reject("V5 retained owner body size differs")
    if ContentDigest.of_bytes(body).value != fields["body_digest"]:
        _reject("V5 retained owner body digest differs")
    if ContentDigest.of_bytes(coordinate_bytes).value != fields["coordinate_digest"]:
        _reject("V5 retained owner coordinate differs")


def encode_head(value: object, *, expected_output_roles: tuple[str, ...]) -> bytes:
    """Encode the accepted envelope against supplied profile data, not authority."""
    fields = publication._v5_fields(value, _HEAD_FIELDS)
    _native(fields, metadata_tokens=True)
    if publication._v5_text(fields["contract"], 192, token=True) != HEAD_CONTRACT:
        _reject("V5 HEAD contract differs")
    base = publication._parse_publication_head_v2_wire(fields["base_head"])
    if base.request.expected_head_revision > publication._V5_MAX_INTEGER:
        _reject("V5 HEAD prior record revision bound")
    occurrence = cast(
        dict[str, object],
        json.loads(publication._encode_v5_occurrence(fields["package_occurrence"])),
    )
    incarnation = publication._v5_text(fields["incarnation_ref"], 192, token=True)
    source = publication._v5_sha(fields["source_epoch_digest"])
    if source != base.source_identity_digest.value:
        _reject("V5 HEAD source epoch differs from original base")
    pair = _binding(fields["meta_pair_binding"], role="meta_committed_pair")
    product = _binding(
        fields["ontology_product_binding"], role="ontology_terminal_product"
    )
    coordinate = base.result_coordinate
    if (
        product["owner_contract"] != coordinate.contract.key
        or product["coordinate_digest"]
        != ContentDigest.of_bytes(canonical_json_bytes(coordinate.to_wire())).value
        or product["body_digest"] != coordinate.digest.value
        or product["body_size"] != coordinate.size_bytes
    ):
        _reject("V5 HEAD terminal binding differs from original result")
    predecessor = fields["predecessor_head_digest"]
    if predecessor is not None:
        predecessor = publication._v5_sha(predecessor)
    operation_ref = publication._v5_text(fields["operation_ref"], 192, token=True)
    operation_digest = publication._v5_sha(fields["operation_digest"])
    if type(expected_output_roles) is not tuple or len(expected_output_roles) > 64:
        _reject("V5 HEAD exact bounded declared output roles required")
    roles = tuple(
        publication._v5_text(r, 192, token=True) for r in expected_output_roles
    )
    if len(set(roles)) != len(roles):
        _reject("V5 HEAD duplicate declared output role")
    wires = fields["output_state_bindings"]
    if type(wires) is not list:
        _reject("V5 HEAD output-state binding bound")
    wire_list = cast(list[object], wires)
    if len(wire_list) > 64:
        _reject("V5 HEAD output-state binding bound")
    bindings = tuple(
        publication._parse_publication_output_state_binding_v4_wire(
            wire,
            "V5 HEAD output state",
        )
        for wire in wire_list
    )
    actual_roles = tuple(binding.output_coordinate.role for binding in bindings)
    if len(set(actual_roles)) != len(actual_roles) or set(actual_roles) != set(roles):
        _reject("V5 HEAD selected output-state roles differ")
    payload = {
        "contract": HEAD_CONTRACT,
        "base_head": base.to_wire(),
        "package_occurrence": occurrence,
        "incarnation_ref": incarnation,
        "source_epoch_digest": source,
        "meta_pair_binding": pair,
        "ontology_product_binding": product,
        "predecessor_head_digest": predecessor,
        "operation_ref": operation_ref,
        "operation_digest": operation_digest,
        "output_state_bindings": [binding.to_wire() for binding in bindings],
    }
    digest = publication._v5_sha(fields["head_digest"])
    if digest != publication._v5_digest(HEAD_CONTRACT, payload):
        _reject("V5 HEAD digest differs")
    body = canonical_json_bytes({**payload, "head_digest": digest})
    if len(body) > _MAX_HEAD_BYTES:
        _reject("V5 HEAD byte bound")
    return body


def decode_head(
    body: bytes, *, expected_output_roles: tuple[str, ...]
) -> dict[str, object]:
    """Return detached wire data; decoding cannot authenticate a current HEAD."""
    value = publication._v5_decode(body, _MAX_HEAD_BYTES)
    if encode_head(value, expected_output_roles=expected_output_roles) != body:
        _reject("V5 HEAD noncanonical bytes")
    return cast(dict[str, object], value)
