"""Complete detached values: byte domains and behavior-free refusal."""
import json
import os
from typing import Any, cast
from pathlib import Path

import pytest
from aware_ontology_object_facade_client import owner_values as owner
from aware_ontology_object_facade_client import object_value_codec as codec

FIXTURES = Path(__file__).resolve().parents[3] / "runtime/python/tests/fixtures"

@pytest.mark.parametrize("name", ["object-value-empty-v3.json", "object-value-complete-v3.json"])
def test_frozen_value_bodies_preserve_all_fields_and_endpoints(name):
    body = FIXTURES.joinpath(name).read_bytes()
    value = codec.decode_object_value(body)
    assert type(value) is owner.OntologyObjectValue
    assert codec.encode_object_value(value) == body
    assert value.to_wire() == json.loads(body)

@pytest.mark.parametrize("name,operation", [
    ("object-relationship-slice-v1.json", codec._slice),
    ("external-endpoint-evidence-claim-v1.json", lambda wire: codec._decode_endpoint_claim(wire, "claim")),
    ("external-association-endpoint-reference-v1.json", lambda wire: codec._decode_endpoint_reference(wire, "endpoint")),
    ("external-schema-field-endpoint-reference-v1.json", lambda wire: codec._decode_endpoint_reference(wire, "endpoint")),
])
def test_frozen_endpoint_and_relationship_bytes(name, operation):
    body = FIXTURES.joinpath(name).read_bytes()
    value = operation(json.loads(body))
    assert owner.canonical_json(value.to_wire()).encode() == body

@pytest.mark.parametrize("entrance", ["value", "nested", "wire", "claim", "collection", "comparison"])
def test_foreign_metaclass_and_native_subclasses_never_dispatch(entrance):
    calls = []
    class ForeignMeta(type):
        def __eq__(cls, other):
            calls.append("equality")
            return False
    class Foreign(metaclass=ForeignMeta):
        def __getattribute__(self, name):
            calls.append(name)
            raise AssertionError("foreign behavior")
    foreign = cast(Any, Foreign())
    value = owner.OntologyObjectValue.create(owner.ObjectInstance("o:1", "T", ()))
    with pytest.raises((TypeError, ValueError)):
        if entrance == "value": codec.encode_object_value(foreign)
        elif entrance == "nested": codec._preflight({"nested": [foreign]})
        elif entrance == "wire": codec._decode_endpoint_reference({"contract": foreign}, "endpoint")
        elif entrance == "claim": owner.OntologyObjectProviderAuthorityClaim(foreign, "p", "a", "g")
        elif entrance == "collection": owner.OntologyObjectValue.create(value.instance, foreign)
        else: value == foreign
    assert calls == []

@pytest.mark.parametrize("target", ["owner_guard", "codec_guard", "helper_binding", "helper_code", "builtin_shadow", "namespace_dunder", "enum_map"])
@pytest.mark.parametrize("entrance", ["construct", "encode", "decode"])
def test_public_value_guard_substitutions_reject_before_dispatch(target, entrance):
    value = owner.OntologyObjectValue.create(owner.ObjectInstance("o:1", "T", ()))
    body = codec.encode_object_value(value)
    pid = os.fork()
    if pid == 0:
        calls = []
        def foreign(*args, **kwargs):
            calls.append(True)
            raise AssertionError("foreign dispatch")
        try:
            if target == "owner_guard": owner._abi_guard = foreign
            elif target == "codec_guard": codec._codec_guard = foreign
            elif target == "helper_binding": codec._preflight = foreign
            elif target == "helper_code":
                def foreign_code(*args, **kwargs):
                    raise AssertionError("foreign code executed")
                cast(Any, codec._preflight).__wrapped__.__code__ = foreign_code.__code__
            elif target == "builtin_shadow": setattr(codec, "type", foreign)
            elif target == "namespace_dunder": setattr(codec, "__foreign__", foreign)
            else: cast(Any, owner.ExternalRelationshipEndpointVariant._member_map_)["FOREIGN"] = foreign
            try:
                if entrance == "construct": owner.OntologyObjectValue.create(value.instance)
                elif entrance == "encode": codec.encode_object_value(value)
                else: codec.decode_object_value(body)
            except (TypeError, ValueError): pass
            else: raise AssertionError("substitution accepted")
            assert calls == []
        except BaseException:
            os._exit(1)
        os._exit(0)
    assert os.waitpid(pid, 0)[1] == 0


@pytest.mark.parametrize("entrance", ["encode", "decode"])
@pytest.mark.parametrize("target", ["guard", "constructor", "helper"])
def test_value_actual_native_codec_return_authenticates_next_dispatch(monkeypatch, entrance, target):
    import sys
    from typing import Any, cast
    value = owner.OntologyObjectValue.create(owner.ObjectInstance("o:1", "T", ()))
    body = codec.encode_object_value(value)
    operation = codec._native_encode if entrance == "encode" else codec._native_decode
    boundary = cast(Any, operation).__wrapped__.__code__
    injected, calls = [], []
    def foreign(*args, **kwargs):
        calls.append(True)
        raise AssertionError("foreign return-boundary dispatch")
    def observe(frame, event, result):
        if event == "return" and frame.f_code is boundary:
            sys.setprofile(None)
            if target == "guard": monkeypatch.setattr(codec, "_codec_guard", foreign)
            elif target == "constructor": monkeypatch.setattr(owner.OntologyObjectValue, "__post_init__", foreign)
            else: monkeypatch.setattr(codec, "_reconstruct", foreign)
            injected.append(True)
    try:
        sys.setprofile(observe)
        with pytest.raises(TypeError, match="shape operation identity"):
            if entrance == "encode": codec.encode_object_value(value)
            else: codec.decode_object_value(body)
    finally:
        sys.setprofile(None)
    assert injected == [True] and calls == []


@pytest.mark.parametrize("kind", [owner.OntologyObjectValue, owner.OntologyObjectSourceAuthorityEvidence,
    owner.ExternalRelationshipEndpointEvidenceClaim, owner.ExternalAssociationEndpointReference,
    owner.ExternalSchemaFieldEndpointReference, owner.OntologyObjectSnapshotAuthorityData,
    owner.OntologyObjectSnapshotData])
def test_genuine_public_factories_reject_foreign_class_before_constructor(kind):
    calls = []
    class ForeignMeta(type):
        def __call__(cls, *args, **kwargs):
            calls.append(True)
            raise AssertionError("foreign constructor")
        def __eq__(cls, other):
            calls.append(True)
            raise AssertionError("foreign metaclass")
    class Foreign(metaclass=ForeignMeta): pass
    method = vars(kind)["create"].__func__
    with pytest.raises(TypeError, match="exact owning class"):
        method(Foreign)
    assert calls == []


def test_genuine_constructor_rejects_foreign_receiver_before_slot_writes():
    calls = []
    class Foreign:
        def __setattr__(self, name, value):
            calls.append(name)
            raise AssertionError("foreign slot write")
    with pytest.raises(TypeError, match="exact owning class"):
        owner.OntologyObjectProviderAuthorityClaim.__init__(cast(Any, Foreign()), "preview", "p", "a", "g")
    assert calls == []
