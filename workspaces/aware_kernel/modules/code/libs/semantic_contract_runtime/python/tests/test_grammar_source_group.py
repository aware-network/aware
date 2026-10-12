"""Real portable codec proofs; original Workspace admission remains external."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tomllib
from dataclasses import replace
from pathlib import Path

import aware_code_semantic_contract_runtime as public
import aware_code_semantic_contract_runtime.grammar_source_group as group_module
import pytest
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.grammar_source_group import (
    GRAMMAR_SOURCE_GROUP_CODEC_IMPLEMENTATION,
    GRAMMAR_SOURCE_GROUP_DESCRIPTOR,
    GRAMMAR_SOURCE_GROUP_REF,
    MAX_GROUP_BYTES,
    CodeGrammarSourceBodyV1,
    CodeGrammarSourceEdgeV1,
    CodeGrammarSourceGroupCodec,
    CodeGrammarSourceGroupV1,
    CodeGrammarSourceMemberV1,
    decode_grammar_source_group,
    encode_grammar_source_group,
    grammar_source_group_body,
)
from aware_code_semantic_contract_runtime.runtime import SemanticBody
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    _validate_context_bodies,
)

REPO = Path(__file__).resolve().parents[8]
VECTOR_PATH = "docs/reports/code-grammar-source-group-freeze-vectors-20261011.json"
VECTORS_REV = "5df2a43d4835a12dd8bf0a0df33e7ed73cb61446"
ERRORS = (ContractViolation, TypeError)


@pytest.fixture(scope="module")
def packet():
    body = subprocess.check_output(
        ["git", "show", VECTORS_REV + ":" + VECTOR_PATH], cwd=REPO
    )
    assert (
        hashlib.sha256(body).hexdigest()
        == "14f10f0e82883a7ed2bbe4cc4a32bc9709c07a127fc5ab0c9d11730b4aa97154"
    )
    return json.loads(body)


def test_descriptor_and_codec_identity_match_accepted_packet(packet):
    assert GRAMMAR_SOURCE_GROUP_DESCRIPTOR.hex() == packet["descriptor_body_hex"]
    assert len(GRAMMAR_SOURCE_GROUP_DESCRIPTOR) == 1497
    assert GRAMMAR_SOURCE_GROUP_REF.to_wire() == packet["contract_ref"]
    assert (
        GRAMMAR_SOURCE_GROUP_CODEC_IMPLEMENTATION.to_wire()
        == packet["codec_implementation"]
    )


@pytest.mark.parametrize("index", [0, 1])
def test_golden_round_trip_all_public_entrances(packet, index):
    vector = packet["vectors"][index]
    body = bytes.fromhex(vector["body_hex"])
    codec = CodeGrammarSourceGroupCodec()
    group = decode_grammar_source_group(body)
    assert group.to_wire() == vector["value"]
    assert encode_grammar_source_group(group) == body
    assert codec.decode(body) == group
    assert codec.encode(group) == body
    assert codec.contract == GRAMMAR_SOURCE_GROUP_REF
    assert codec.implementation == GRAMMAR_SOURCE_GROUP_CODEC_IMPLEMENTATION
    retained = grammar_source_group_body(group)
    assert retained.canonical_body == body
    assert retained.coordinate.to_wire() == vector["coordinate"]
    _validate_context_bodies((retained,))


def test_direct_construction_and_each_nested_projection(packet):
    group = decode_grammar_source_group(bytes.fromhex(packet["vectors"][1]["body_hex"]))
    member = group.members[0]
    assert (
        CodeGrammarSourceMemberV1(
            member.occurrence_ref,
            member.selection_coordinate,
            member.selection_body_hex,
            member.origin_coordinate,
            member.origin_body_hex,
            member.sources,
        )
        == member
    )
    assert member.to_wire() == packet["vectors"][1]["value"]["members"][0]
    assert member.sources[0].to_wire() == member.to_wire()["sources"][0]
    assert (
        group.dependency_edges[0].to_wire()
        == packet["vectors"][1]["value"]["dependency_edges"][0]
    )


def test_equal_source_bytes_and_paths_are_not_merged(packet):
    group = decode_grammar_source_group(bytes.fromhex(packet["vectors"][1]["body_hex"]))
    left, right = group.members
    assert left.sources == right.sources
    assert left.occurrence_ref != right.occurrence_ref
    assert len(group.members) == 2


def test_package_cycles_and_self_edges_are_portable_connectivity(packet):
    group = decode_grammar_source_group(bytes.fromhex(packet["vectors"][1]["body_hex"]))
    left, right = (member.occurrence_ref for member in group.members)
    edges = (
        CodeGrammarSourceEdgeV1(left, left, "opaque", "fixture:self"),
        CodeGrammarSourceEdgeV1(left, right, "opaque", "fixture:right"),
        CodeGrammarSourceEdgeV1(right, left, "opaque", "fixture:left"),
    )
    assert (
        decode_grammar_source_group(
            encode_grammar_source_group(replace(group, dependency_edges=edges))
        ).dependency_edges
        == edges
    )


def changed(wire, path, value):
    row = copy.deepcopy(wire)
    node = row
    for component in path[:-1]:
        node = node[component]
    node[path[-1]] = value
    return row


@pytest.mark.parametrize(
    "path,value",
    [
        (("contract",), "aware.code.grammar-source-group.v2"),
        (("contract",), None),
        (("root_occurrence_ref",), "fixture:absent"),
        (("members",), []),
        (("members",), None),
        (("members",), {}),
        (("dependency_edges",), None),
        (("members", 0, "occurrence_ref"), "fixture:wrong"),
        (("members", 0, "sources"), []),
        (("members", 0, "selection_body_hex"), "FF"),
        (("members", 0, "selection_body_hex"), "0"),
        (("members", 0, "selection_body_hex"), "00 "),
        (("members", 0, "selection_coordinate", "size_bytes"), True),
        (("members", 0, "selection_coordinate", "size_bytes"), -1),
        (("members", 0, "selection_coordinate", "size_bytes"), MAX_GROUP_BYTES + 1),
        (("members", 0, "selection_coordinate", "contract", "version"), "2"),
        (("members", 0, "selection_coordinate", "digest"), "sha256:" + "0" * 64),
        (("members", 0, "origin_coordinate", "digest"), "sha256:" + "0" * 64),
        (("members", 0, "sources", 0, "relative_path"), "../foreign"),
        (("members", 0, "sources", 0, "relative_path"), "/absolute"),
        (("members", 0, "sources", 0, "relative_path"), "syntax/wrong.syntax.json"),
        (("members", 0, "sources", 0, "body_hex"), "00"),
        (("members", 0, "sources", 0, "coordinate", "role"), "foreign"),
        (("members", 0, "sources", 0, "coordinate", "value_ref"), "foreign"),
        (
            ("members", 0, "sources", 0, "coordinate", "contract", "schema_digest"),
            "sha256:" + "0" * 64,
        ),
    ],
)
def test_coordinate_path_literal_type_and_hex_mutations_refuse(packet, path, value):
    with pytest.raises(ERRORS):
        decode_grammar_source_group(
            canonical_json_bytes(changed(packet["vectors"][0]["value"], path, value))
        )


@pytest.mark.parametrize(
    "part", ["group", "member", "source", "coordinate", "contract", "edge"]
)
@pytest.mark.parametrize("mode", ["unknown", "missing"])
def test_closed_field_sets_at_every_level(packet, part, mode):
    wire = copy.deepcopy(packet["vectors"][1]["value"])
    target = {
        "group": wire,
        "member": wire["members"][0],
        "source": wire["members"][0]["sources"][0],
        "coordinate": wire["members"][0]["sources"][0]["coordinate"],
        "contract": wire["members"][0]["sources"][0]["coordinate"]["contract"],
        "edge": wire["dependency_edges"][0],
    }[part]
    if mode == "unknown":
        target["caller_validated"] = True
    else:
        del target[next(iter(target))]
    with pytest.raises(ERRORS):
        decode_grammar_source_group(canonical_json_bytes(wire))


@pytest.mark.parametrize("index", [0, 1])
def test_duplicate_json_keys_in_root_and_nested_source_refuse(packet, index):
    body = bytes.fromhex(packet["vectors"][index]["body_hex"])
    for malformed in (
        b'{"contract":"anything",' + body[1:],
        body.replace(
            b'"relative_path":', b'"relative_path":"poison","relative_path":', 1
        ),
    ):
        with pytest.raises(ContractViolation):
            decode_grammar_source_group(malformed)


@pytest.mark.parametrize(
    "value", [b"", b"{", b"\xff", b"NaN", b"Infinity", b"null", b"[]", b"0", b"true"]
)
def test_invalid_json_refuses(value):
    with pytest.raises(ERRORS):
        decode_grammar_source_group(value)


def test_noncanonical_and_oversized_or_deep_json_refuse(packet):
    body = bytes.fromhex(packet["vectors"][0]["body_hex"])
    for malformed in (
        body + b"\n",
        b" " + body,
        json.dumps(packet["vectors"][0]["value"]).encode(),
        b"x" * (MAX_GROUP_BYTES + 1),
        b"[" * 65 + b"0" + b"]" * 65,
        b"[" * 2000 + b"0" + b"]" * 2000,
    ):
        with pytest.raises(ERRORS):
            decode_grammar_source_group(malformed)


@pytest.mark.parametrize(
    "mode",
    [
        "reverse",
        "duplicate",
        "no-edges",
        "absent-endpoint",
        "wrong-root",
        "source-order",
    ],
)
def test_inventory_order_graph_membership_and_complete_sources_refuse(packet, mode):
    wire = copy.deepcopy(packet["vectors"][1]["value"])
    if mode == "reverse":
        wire["members"].reverse()
    elif mode == "duplicate":
        wire["members"].append(copy.deepcopy(wire["members"][0]))
    elif mode == "no-edges":
        wire["dependency_edges"] = []
    elif mode == "absent-endpoint":
        wire["dependency_edges"][0]["target_occurrence_ref"] = "fixture:absent"
    elif mode == "wrong-root":
        wire["root_occurrence_ref"] = "fixture:absent"
    else:
        wire["members"][0]["sources"].append(
            copy.deepcopy(wire["members"][0]["sources"][0])
        )
    with pytest.raises(ERRORS):
        decode_grammar_source_group(canonical_json_bytes(wire))


def test_cross_member_selection_and_origin_pairs_refuse(packet):
    wire = copy.deepcopy(packet["vectors"][1]["value"])
    left, right = wire["members"]
    left["selection_coordinate"] = right["selection_coordinate"]
    left["selection_body_hex"] = right["selection_body_hex"]
    with pytest.raises(ERRORS):
        decode_grammar_source_group(canonical_json_bytes(wire))


def test_count_bounds_checked_before_graph_or_source_work(packet):
    group = decode_grammar_source_group(bytes.fromhex(packet["vectors"][0]["body_hex"]))
    member = group.members[0]
    with pytest.raises(ContractViolation):
        replace(group, members=(member,) * 129)
    edge = CodeGrammarSourceEdgeV1(
        member.occurrence_ref, member.occurrence_ref, "x", "x"
    )
    with pytest.raises(ContractViolation):
        replace(group, dependency_edges=(edge,) * 257)
    with pytest.raises(ContractViolation):
        replace(member, sources=member.sources * 16385)
    for kind in ("", "has space", "x" * 513):
        with pytest.raises(ContractViolation):
            replace(edge, dependency_kind=kind)


def test_edge_tokens_preserve_original_grammar_and_utf8_byte_bound(packet):
    group = decode_grammar_source_group(bytes.fromhex(packet["vectors"][0]["body_hex"]))
    ref = group.members[0].occurrence_ref
    for token in ("é" * 256, "e\u0301", "opaque\x00token"):
        edge = CodeGrammarSourceEdgeV1(ref, ref, token, "fixture:edge")
        result = decode_grammar_source_group(
            encode_grammar_source_group(replace(group, dependency_edges=(edge,)))
        )
        assert result.dependency_edges[0].dependency_kind == token
    with pytest.raises(ContractViolation):
        CodeGrammarSourceEdgeV1(ref, ref, "é" * 257, "fixture:edge")


def test_edge_order_is_preserved_not_silently_sorted(packet):
    group = decode_grammar_source_group(bytes.fromhex(packet["vectors"][0]["body_hex"]))
    ref = group.members[0].occurrence_ref
    edges = tuple(
        CodeGrammarSourceEdgeV1(ref, ref, "x", f"fixture:{key}") for key in ("a", "b")
    )
    assert replace(group, dependency_edges=edges).dependency_edges == edges
    with pytest.raises(ContractViolation):
        replace(group, dependency_edges=edges[::-1])


def test_group_hex_expansion_bound_precedes_original_decoders(packet, monkeypatch):
    group = decode_grammar_source_group(bytes.fromhex(packet["vectors"][0]["body_hex"]))
    object.__setattr__(
        group.members[0], "selection_body_hex", "0" * (MAX_GROUP_BYTES + 1)
    )

    def unreachable(*args, **kwargs):
        raise AssertionError("decoder entered after aggregate bound exceeded")

    monkeypatch.setattr(group_module, "decode_source_origin_selection", unreachable)
    with pytest.raises(ContractViolation):
        encode_grammar_source_group(group)


@pytest.mark.parametrize("kind", ["selection", "origin"])
def test_restamped_noncanonical_original_bodies_refuse(packet, kind):
    wire = copy.deepcopy(packet["vectors"][0]["value"])
    member = wire["members"][0]
    body = bytes.fromhex(member[f"{kind}_body_hex"]) + b"\n"
    member[f"{kind}_body_hex"] = body.hex()
    coordinate = member[f"{kind}_coordinate"]
    coordinate["digest"] = ContentDigest.of_bytes(body).value
    coordinate["size_bytes"] = len(body)
    with pytest.raises(ContractViolation):
        decode_grammar_source_group(canonical_json_bytes(wire))


class PoisonMeta(type):
    def __getattribute__(self, name):
        raise AssertionError("foreign metaclass executed")


class Poison(metaclass=PoisonMeta):
    def __getattribute__(self, name):
        raise AssertionError("foreign attribute executed")

    def __eq__(self, other):
        raise AssertionError("foreign equality executed")

    def __iter__(self):
        raise AssertionError("foreign iteration executed")


@pytest.mark.parametrize(
    "field", ["root_occurrence_ref", "members", "dependency_edges"]
)
def test_poisoned_forged_group_refuses_without_callbacks(packet, field):
    group = decode_grammar_source_group(bytes.fromhex(packet["vectors"][0]["body_hex"]))
    object.__setattr__(group, field, Poison())
    for entrance in (
        encode_grammar_source_group,
        grammar_source_group_body,
        CodeGrammarSourceGroupCodec().encode,
    ):
        with pytest.raises(ERRORS):
            entrance(group)


@pytest.mark.parametrize(
    "target,field",
    [
        ("member", "occurrence_ref"),
        ("member", "selection_coordinate"),
        ("member", "selection_body_hex"),
        ("member", "origin_coordinate"),
        ("member", "origin_body_hex"),
        ("member", "sources"),
        ("source", "relative_path"),
        ("source", "coordinate"),
        ("source", "body_hex"),
        ("coordinate", "contract"),
        ("coordinate", "digest"),
        ("coordinate", "size_bytes"),
        ("contract", "schema_digest"),
        ("digest", "value"),
    ],
)
def test_poisoned_nested_fields_refuse_without_callbacks(packet, target, field):
    group = decode_grammar_source_group(bytes.fromhex(packet["vectors"][0]["body_hex"]))
    source = group.members[0].sources[0]
    value = {
        "member": group.members[0],
        "source": source,
        "coordinate": source.coordinate,
        "contract": source.coordinate.contract,
        "digest": source.coordinate.digest,
    }[target]
    object.__setattr__(value, field, Poison())
    with pytest.raises(ERRORS):
        encode_grammar_source_group(group)


@pytest.mark.parametrize(
    "cls",
    [
        CodeGrammarSourceGroupV1,
        CodeGrammarSourceMemberV1,
        CodeGrammarSourceBodyV1,
        CodeGrammarSourceEdgeV1,
    ],
)
def test_uninitialized_and_subclassed_values_refuse(packet, cls):
    value = object.__new__(cls)
    with pytest.raises(ERRORS):
        value.to_wire()
    subclass = type("Foreign", (cls,), {"__post_init__": lambda self: None})
    foreign = object.__new__(subclass)
    with pytest.raises(ERRORS):
        foreign.to_wire()


@pytest.mark.parametrize("value", [None, {}, [], "{}", bytearray(b"{}"), 1])
def test_wrong_top_level_types_refuse(value):
    for entrance in (
        encode_grammar_source_group,
        grammar_source_group_body,
        CodeGrammarSourceGroupCodec().encode,
        decode_grammar_source_group,
    ):
        with pytest.raises(ERRORS):
            entrance(value)


def test_group_body_uses_original_aggregate_context_budget(packet):
    group = decode_grammar_source_group(bytes.fromhex(packet["vectors"][0]["body_hex"]))
    body = grammar_source_group_body(group)
    extra_bytes = b"x" * (MAX_GROUP_BYTES - len(body.canonical_body))
    extra = SemanticBody(
        replace(
            body.coordinate,
            role="extra",
            digest=ContentDigest.of_bytes(extra_bytes),
            size_bytes=len(extra_bytes),
        ),
        extra_bytes,
    )
    with pytest.raises(ContractViolation):
        _validate_context_bodies((body, extra))


def test_raw_source_text_is_opaque_not_json_normalized():
    body = b'{"a": 1}\n'
    packet_coordinate = decode_coordinate_for_raw(body)
    source = CodeGrammarSourceBodyV1(
        "syntax/source.syntax.json", packet_coordinate, body.hex()
    )
    assert bytes.fromhex(source.to_wire()["body_hex"]) == body


def decode_coordinate_for_raw(body):
    from aware_code_semantic_contract_runtime.contracts import (
        SemanticContractRef,
        SemanticValueCoordinate,
    )

    return SemanticValueCoordinate(
        "opaque",
        SemanticContractRef("fixture:raw.v1", "1", ContentDigest.of_bytes(b"schema")),
        "fixture:raw",
        ContentDigest.of_bytes(body),
        len(body),
    )


def test_root_exports_and_dependencies_remain_neutral():
    assert public.CodeGrammarSourceGroupCodec is CodeGrammarSourceGroupCodec
    base = Path(__file__).resolve().parents[1]
    assert (
        tomllib.loads((base / "pyproject.toml").read_text())["project"]["dependencies"]
        == []
    )
    code = 'import sys, aware_code_semantic_contract_runtime; assert not any(n.startswith(("aware_workspace", "aware_filesystem", "aware_language", "aware_meta", "aware_ontology", "aware_code_sdk", "aware_code_service")) for n in sys.modules)'
    subprocess.run([sys.executable, "-B", "-c", code], check=True)
