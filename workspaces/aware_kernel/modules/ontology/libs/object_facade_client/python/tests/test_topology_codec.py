"""Detached v5 semantics and executable-boundary proofs; no host imports."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from aware_meta_type_schema import decode_schema_slice
from aware_meta_type_schema import model as meta_model
from aware_ontology_object_facade_client import owner_values as owner
from aware_ontology_object_facade_client import topology_codec as codec
from aware_ontology_object_facade_client import topology_validation as validation
from aware_ontology_object_facade_client import topology_values as values

FIXTURE = Path(__file__).resolve().parents[3] / "runtime/contracts/v5/aware-home"
FROZEN_FIXTURE_HASHES = {
    "schema-slice.json": "05344e1d392edab27c4127b2dcc16ef12537642a4b901e30bdef2017b270f3e8",
    "topology.json": "adefefc91b07a1f8b376d3d374aa70ea0e9b08475ee4328c399168630aeed401",
}


@pytest.fixture(scope="module")
def portable():
    for name, expected in FROZEN_FIXTURE_HASHES.items():
        assert (
            hashlib.sha256(FIXTURE.joinpath(name).read_bytes()).hexdigest() == expected
        )
    schema = decode_schema_slice(FIXTURE.joinpath("schema-slice.json").read_bytes())
    body = FIXTURE.joinpath("topology.json").read_bytes().rstrip(b"\n")
    topology = codec.decode_schema_topology_manifest(body, schema)
    return schema, topology, body


def copy_record(value, **changes):
    # Detached by-value reconstruction, without an issuer/provenance marker.
    clone = object.__new__(type(value))
    for field in dataclasses.fields(value):
        object.__setattr__(
            clone, field.name, changes.get(field.name, getattr(value, field.name))
        )
    return clone


def restamp(wire):
    payload = {
        name: item
        for name, item in wire.items()
        if name not in ("contract", "topology_digest")
    }
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    wire["topology_digest"] = (
        "sha256:"
        + hashlib.sha256(
            values.SCHEMA_TOPOLOGY_CONTRACT.encode() + b"\n" + canonical
        ).hexdigest()
    )
    return json.dumps(wire, sort_keys=True, separators=(",", ":")).encode()


def test_canonical_roundtrip_and_detached_reconstruction(portable):
    schema, topology, body = portable
    assert codec.encode_schema_topology_manifest(topology, schema) == body
    detached = copy_record(topology)
    assert detached is not topology
    assert codec.encode_schema_topology_manifest(detached, copy_record(schema)) == body
    created = values.SchemaOntologyRuntimeTopology.create(
        namespace=topology.namespace,
        semantic_version=topology.semantic_version,
        schema_slice=schema,
        graph_types=topology.graph_types,
        relationships=topology.relationships,
        projections=topology.projections,
        actions=topology.actions,
    )
    assert codec.encode_schema_topology_manifest(created, schema) == body
    assert (
        codec.negotiate_schema_topology_contract([values.SCHEMA_TOPOLOGY_CONTRACT])
        == values.SCHEMA_TOPOLOGY_CONTRACT
    )
    assert owner.ValueShape is meta_model.ValueShape


@pytest.mark.parametrize(
    "change",
    (
        "digest",
        "unknown",
        "predecessor",
        "input_grade",
        "identity",
        "relationship",
        "projection",
        "shape",
    ),
)
def test_complete_coherent_semantic_refusal(portable, change):
    schema, topology, body = portable
    wire = json.loads(body)
    if change == "digest":
        wire["topology_digest"] = "sha256:" + "0" * 64
    elif change == "unknown":
        wire["extra"] = 1
    elif change == "predecessor":
        wire["contract"] = "aware.ontology.runtime-schema-topology.v1"
    elif change == "input_grade":
        wire["input_grade"] = "admitted"
    elif change == "identity":
        wire["graph_types"][0]["identity_field_refs"] = []
    elif change == "relationship":
        wire["relationships"][0]["target_type_ref"] = "missing.Type"
    elif change == "projection":
        wire["projections"][0]["field_refs"].append("missing.field")
    else:
        wire["actions"][0]["result_shape"]["type_ref"] = "missing.Type"
    encoded = (
        restamp(wire)
        if change not in ("digest", "unknown", "predecessor")
        else json.dumps(wire).encode()
    )
    with pytest.raises((TypeError, ValueError)):
        codec.decode_schema_topology_manifest(encoded, schema)
    if change in ("identity", "relationship", "projection"):
        if change == "identity":
            nested = copy_record(topology.graph_types[0], identity_field_refs=())
            invalid = copy_record(
                topology,
                graph_types=(nested, *topology.graph_types[1:]),
                topology_digest=wire["topology_digest"],
            )
        elif change == "relationship":
            nested = copy_record(
                topology.relationships[0], target_type_ref="missing.Type"
            )
            invalid = copy_record(
                topology,
                relationships=(nested,),
                topology_digest=wire["topology_digest"],
            )
        else:
            nested = copy_record(
                topology.projections[0],
                field_refs=tuple(wire["projections"][0]["field_refs"]),
            )
            invalid = copy_record(
                topology, projections=(nested,), topology_digest=wire["topology_digest"]
            )
        with pytest.raises((TypeError, ValueError)):
            codec.encode_schema_topology_manifest(invalid, schema)
        with pytest.raises((TypeError, ValueError)):
            validation.validate_schema_topology(invalid, schema)


@pytest.mark.parametrize("place", ("token", "nested", "enum", "slice", "payload"))
def test_foreign_operands_reject_without_behavior(portable, place):
    schema, topology, _ = portable
    calls = []

    class ForeignMeta(type):
        def __eq__(cls, other):
            calls.append("class equality")
            return False

        def __hash__(cls):
            calls.append("class hash")
            return 0

    class Foreign(metaclass=ForeignMeta):
        def __getattribute__(self, name):
            calls.append("attribute")
            raise AssertionError(name)

        def __iter__(self):
            calls.append("iteration")
            return iter(())

        def __eq__(self, other):
            calls.append("equality")
            return False

    class Text(str):
        def strip(self, *args):
            calls.append("strip")
            return self

    foreign: Any = Foreign()
    with pytest.raises(TypeError):
        if place == "token":
            values.GraphTypeBinding(
                Text("T"), values.GraphIdentityMode.INSTANCE_REF, (), (), ()
            )
        elif place == "nested":
            codec.encode_schema_topology_manifest(
                copy_record(topology, projections=(foreign,)), schema
            )
        elif place == "enum":
            values.GraphTypeBinding("T", foreign, (), (), ())
        elif place == "slice":
            codec.encode_schema_topology_manifest(topology, foreign)
        else:
            codec.decode_schema_topology_manifest(foreign, schema)
    assert calls == []


@pytest.mark.parametrize(
    "entrance", ("construct", "encode", "decode", "validate", "lookup")
)
@pytest.mark.parametrize(
    "target",
    ("guard_binding", "absent_builtin", "constructor", "enum_map", "decoder_state"),
)
def test_retained_public_dispatch_substitutions(
    portable, monkeypatch, entrance, target
):
    schema, topology, body = portable
    calls = []

    def foreign(*args, **kwargs):
        calls.append("foreign")
        raise AssertionError("foreign body")

    if target == "guard_binding":
        monkeypatch.setattr(codec, "_call", foreign)
    elif target == "absent_builtin":
        monkeypatch.setattr(values, "type", foreign, raising=False)
    elif target == "constructor":
        monkeypatch.setattr(values.GraphTypeBinding, "__post_init__", foreign)
    elif target == "enum_map":
        monkeypatch.setitem(meta_model.ShapeKind._member_map_, "foreign", [foreign])
    else:
        monkeypatch.setattr(vars(json)["_default_decoder"], "parse_int", foreign)
    with pytest.raises(TypeError):
        if entrance == "construct":
            values.GraphTypeBinding(
                "T", values.GraphIdentityMode.INSTANCE_REF, (), (), ()
            )
        elif entrance == "encode":
            codec.encode_schema_topology_manifest(topology, schema)
        elif entrance == "decode":
            codec.decode_schema_topology_manifest(body, schema)
        elif entrance == "validate":
            validation.validate_schema_topology(topology, schema)
        else:
            codec.negotiate_schema_topology_contract([values.SCHEMA_TOPOLOGY_CONTRACT])
    assert calls == []
    monkeypatch.undo()
    assert (
        codec.negotiate_schema_topology_contract([values.SCHEMA_TOPOLOGY_CONTRACT])
        == values.SCHEMA_TOPOLOGY_CONTRACT
    )


@pytest.mark.parametrize("substitution", ("constructor", "is_", "itemgetter", "attrgetter"))
@pytest.mark.parametrize("boundary", ("token", "shape", "pairs", "digest"))
def test_actual_nested_return_rechecks_before_next_dispatch(
    portable, monkeypatch, boundary, substitution
):
    import _operator
    schema, _, body = portable
    calls, observed = [], []
    target = {
        "token": owner._strict_token,
        "shape": meta_model._token,
        "pairs": codec._without_duplicates,
        "digest": owner.digest_payload,
    }[boundary]
    while hasattr(target, "__wrapped__"):
        target = target.__wrapped__
    watched = target.__code__

    def foreign(*args, **kwargs):
        calls.append("foreign")
        raise AssertionError("foreign body")

    def observe(frame, event, arg):
        if event == "return" and frame.f_code is watched and not observed:
            observed.append(True)
            if substitution == "constructor":
                monkeypatch.setattr(values.GraphTypeBinding, "__init__", foreign)
            else:
                monkeypatch.setattr(_operator, substitution, foreign)

    previous = sys.getprofile()
    sys.setprofile(observe)
    try:
        with pytest.raises(TypeError):
            codec.decode_schema_topology_manifest(body, schema)
    finally:
        sys.setprofile(previous)
    assert observed == [True] and calls == []


@pytest.mark.parametrize("body", (b'{"x":1,"x":2}', b"{}", b"null", b"[]", b"\xff"))
def test_strict_json_refuses(portable, body):
    with pytest.raises((TypeError, ValueError)):
        codec.decode_schema_topology_manifest(body, portable[0])


def test_native_callable_rebinding_is_rejected_before_dispatch(portable, monkeypatch):
    schema, topology, _ = portable
    injected = []
    target: Any = owner._strict_token
    while hasattr(target, "__wrapped__"):
        target = target.__wrapped__
    watched = target.__code__

    def observe(frame, event, arg):
        if event == "return" and frame.f_code is watched and not injected:
            injected.append(True)
            # Another genuine native callable is still a substituted binding.
            monkeypatch.setattr(values, "_normalize_topology", tuple)

    previous = sys.getprofile()
    sys.setprofile(observe)
    try:
        with pytest.raises(TypeError, match="identity mismatched"):
            codec.encode_schema_topology_manifest(topology, schema)
    finally:
        sys.setprofile(previous)
    assert injected == [True]


def _substitute_reachable_identity(monkeypatch, target, calls):
    if target == "module_binding":

        class ForeignModule(ModuleType):
            def __getattribute__(self, name):
                calls.append("module attribute")
                raise AssertionError("foreign module attribute")

        monkeypatch.setitem(
            sys.modules, validation.__name__, ForeignModule(validation.__name__)
        )
    else:
        singleton_name = (
            "_default_decoder" if target == "decoder_class" else "_default_encoder"
        )
        singleton = vars(json)[singleton_name]
        original_class = type(singleton)

        class ForeignReceiver(original_class):
            def __getattribute__(self, name):
                calls.append("receiver attribute")
                raise AssertionError("foreign receiver attribute")

        monkeypatch.setattr(singleton, "__class__", ForeignReceiver)
        assert type(singleton) is ForeignReceiver


@pytest.mark.parametrize("target", ("module_binding", "decoder_class", "encoder_class"))
@pytest.mark.parametrize(
    "entrance", ("create", "encode", "decode", "validate", "reconstruct")
)
def test_reachable_identity_preflight(portable, monkeypatch, target, entrance):
    schema, topology, body = portable
    arguments = {
        "namespace": topology.namespace,
        "semantic_version": topology.semantic_version,
        "schema_slice": schema,
        "graph_types": topology.graph_types,
        "relationships": topology.relationships,
        "projections": topology.projections,
        "actions": topology.actions,
    }
    calls = []
    _substitute_reachable_identity(monkeypatch, target, calls)
    with pytest.raises(TypeError):
        if entrance == "create":
            values.SchemaOntologyRuntimeTopology.create(**arguments)
        elif entrance == "encode":
            codec.encode_schema_topology_manifest(topology, schema)
        elif entrance == "decode":
            codec.decode_schema_topology_manifest(body, schema)
        elif entrance == "validate":
            validation.validate_schema_topology(topology, schema)
        else:
            # This actual Meta record reconstructs FrozenJson using json.loads.
            values._revalidate(schema)
    assert calls == []
    monkeypatch.undo()
    assert (
        codec.negotiate_schema_topology_contract([values.SCHEMA_TOPOLOGY_CONTRACT])
        == values.SCHEMA_TOPOLOGY_CONTRACT
    )


@pytest.mark.parametrize("target", ("module_binding", "decoder_class", "encoder_class"))
def test_reachable_identity_nested_return(portable, monkeypatch, target):
    schema, topology, _ = portable
    calls, injected = [], []
    original: Any = owner._strict_token
    while hasattr(original, "__wrapped__"):
        original = original.__wrapped__
    watched = original.__code__

    def observe(frame, event, arg):
        if event == "return" and frame.f_code is watched and not injected:
            injected.append(True)
            _substitute_reachable_identity(monkeypatch, target, calls)

    previous = sys.getprofile()
    sys.setprofile(observe)
    try:
        with pytest.raises(TypeError):
            codec.encode_schema_topology_manifest(topology, schema)
    finally:
        sys.setprofile(previous)
    assert injected == [True] and calls == []


def test_create_and_meta_reconstruction_keep_original_bytes(portable):
    schema, topology, body = portable
    reconstructed = values._revalidate(schema)
    assert reconstructed.to_wire() == schema.to_wire()
    created = values.SchemaOntologyRuntimeTopology.create(
        namespace=topology.namespace,
        semantic_version=topology.semantic_version,
        schema_slice=schema,
        graph_types=topology.graph_types,
        relationships=topology.relationships,
        projections=topology.projections,
        actions=topology.actions,
    )
    assert codec.encode_schema_topology_manifest(created, reconstructed) == body


def _replace_native_key(namespace, requested_name, calls):
    # The foreign key has the same native string hash as the real lookup key.
    # Setup/restore use identity inspection and keep every unrelated entry.
    original = tuple(dict.items(namespace))
    name, value = next(
        (key, value)
        for key, value in original
        if type(key) is str and key == requested_name
    )

    class ForeignKey(str):
        __hash__ = str.__hash__

        def __eq__(self, other):
            calls.append("foreign equality")
            return False

    foreign_key = ForeignKey(name)
    dict.pop(namespace, name)
    dict.__setitem__(namespace, foreign_key, value)
    assert any(key is foreign_key for key in dict.keys(namespace))

    def restore():
        current = {
            id(key): (key, value)
            for key, value in dict.items(namespace)
            if key is not foreign_key
        }
        ordered = []
        for key, old_value in original:
            if key is name:
                ordered.append((key, old_value))
            elif id(key) in current:
                ordered.append(current.pop(id(key)))
        ordered.extend(current.values())
        dict.clear(namespace)
        dict.update(namespace, ordered)

    return restore


@pytest.mark.parametrize("target", ("sys_keys", "registry_keys", "public_keys"))
@pytest.mark.parametrize(
    "entrance", ("create", "encode", "decode", "validate", "reconstruct")
)
def test_registry_key_entry_preflight(portable, target, entrance):
    schema, topology, body = portable
    arguments = {
        "namespace": topology.namespace,
        "semantic_version": topology.semantic_version,
        "schema_slice": schema,
        "graph_types": topology.graph_types,
        "relationships": topology.relationships,
        "projections": topology.projections,
        "actions": topology.actions,
    }
    namespace, name = {
        "sys_keys": (vars(sys), "modules"),
        "registry_keys": (sys.modules, validation.__name__),
        "public_keys": (vars(values), "_validate_topology"),
    }[target]
    calls = []
    restore = _replace_native_key(namespace, name, calls)
    try:
        with pytest.raises(TypeError):
            if entrance == "create":
                values.SchemaOntologyRuntimeTopology.create(**arguments)
            elif entrance == "encode":
                codec.encode_schema_topology_manifest(topology, schema)
            elif entrance == "decode":
                codec.decode_schema_topology_manifest(body, schema)
            elif entrance == "validate":
                validation.validate_schema_topology(topology, schema)
            else:
                values._revalidate(schema)
        assert calls == []
    finally:
        restore()
    assert (
        codec.negotiate_schema_topology_contract([values.SCHEMA_TOPOLOGY_CONTRACT])
        == values.SCHEMA_TOPOLOGY_CONTRACT
    )


@pytest.mark.parametrize("target", ("sys_keys", "registry_keys", "public_keys"))
def test_registry_key_nested_return(portable, target):
    schema, topology, _ = portable
    namespace, name = {
        "sys_keys": (vars(sys), "modules"),
        "registry_keys": (sys.modules, validation.__name__),
        "public_keys": (vars(values), "_validate_topology"),
    }[target]
    calls, restorers = [], []
    original: Any = owner._strict_token
    while hasattr(original, "__wrapped__"):
        original = original.__wrapped__
    watched = original.__code__

    def observe(frame, event, arg):
        if event == "return" and frame.f_code is watched and not restorers:
            restorers.append(_replace_native_key(namespace, name, calls))

    previous = sys.getprofile()
    sys.setprofile(observe)
    try:
        with pytest.raises(TypeError):
            codec.encode_schema_topology_manifest(topology, schema)
        assert len(restorers) == 1 and calls == []
    finally:
        sys.setprofile(previous)
        for restore in restorers:
            restore()


def test_unrelated_native_imports_remain_allowed(portable, monkeypatch):
    extra = ModuleType("t1_unrelated_native_import")
    monkeypatch.setitem(sys.modules, extra.__name__, extra)
    schema, topology, body = portable
    assert codec.encode_schema_topology_manifest(topology, schema) == body
    assert sys.modules[extra.__name__] is extra
