"""Detached complete snapshots never admit providers or operational Objects."""
import json
import os

import pytest
from aware_ontology_object_facade_client import owner_values as owner
from aware_ontology_object_facade_client import object_snapshot_codec as codec


def snapshot(grade="preview", source=False):
    value = owner.OntologyObjectValue.create(owner.ObjectInstance("o:1", "T", ()))
    provider = owner.OntologyObjectProviderAuthorityClaim(
        grade, "provider", "authority", "generation",
        "branch:canonical" if grade == "canonical_replica" else None,
        "commit:canonical" if grade == "canonical_replica" else None)
    evidence = owner.OntologyObjectSourceAuthorityEvidence.create(
        source_coordinate_ref="source:1", source_observation_ref="observation:1",
        source_mapping_digest="sha256:mapping") if source else None
    authority = owner.OntologyObjectSnapshotAuthorityData.create(
        value_digest=value.value_digest, provider_authority=provider,
        class_binding_digest="sha256:binding", topology_digest="sha256:topology",
        branch_ref="branch:1", revision_ref="revision:1", projection_ref="projection:1",
        view_digest="sha256:view", source_authority=evidence)
    return owner.OntologyObjectSnapshotData.create(value=value, authority=authority)

@pytest.mark.parametrize("grade", ["preview", "local_operational", "canonical_replica"])
@pytest.mark.parametrize("source", [False, True])
def test_complete_snapshot_roundtrip_and_independent_digest_domains(grade, source):
    value = snapshot(grade, source)
    body = codec.encode_object_snapshot_data(value)
    decoded = codec.decode_object_snapshot_data(body)
    assert decoded == value
    wire = json.loads(body)
    assert wire["authority"]["provider_authority"]["grade"] == grade
    assert (wire["authority"]["source_authority"] is not None) is source
    assert value.snapshot_digest == owner.digest_payload(owner.OBJECT_SNAPSHOT_CONTRACT, {k: v for k, v in wire.items() if k not in ("contract", "snapshot_digest")})
    assert type(decoded.authority.provider_authority) is owner.OntologyObjectProviderAuthorityClaim
    assert not hasattr(decoded, "activate")

@pytest.mark.parametrize("grade,branch,commit", [
    ("resident_local", None, None), ("source_backed", None, None),
    ("preview", "b", None), ("preview", None, "c"),
    ("local_operational", "b", "c"), ("canonical_replica", None, None),
    ("canonical_replica", "b", None), ("canonical_replica", None, "c"),
])
def test_provider_claim_grade_and_coordinate_law(grade, branch, commit):
    with pytest.raises((TypeError, ValueError)):
        owner.OntologyObjectProviderAuthorityClaim(grade, "p", "a", "g", branch, commit)

@pytest.mark.parametrize("change", ["extra", "missing", "value_digest", "authority_digest", "snapshot_digest", "provider_extra", "noncanonical", "duplicate"])
def test_snapshot_grammar_and_digest_substitution_refuse(change):
    body = codec.encode_object_snapshot_data(snapshot())
    wire = json.loads(body)
    if change == "extra": wire["extra"] = None
    elif change == "missing": del wire["authority"]
    elif change == "provider_extra": wire["authority"]["provider_authority"]["admitted"] = True
    elif change == "value_digest": wire["value"][change] = "sha256:foreign"
    elif change == "authority_digest": wire["authority"][change] = "sha256:foreign"
    elif change == "snapshot_digest": wire[change] = "sha256:foreign"
    elif change == "noncanonical": body = b" " + body
    else: body = body.replace(b'{"authority":', b'{"authority":null,"authority":', 1)
    if change not in ("noncanonical", "duplicate"): body = owner.canonical_json(wire).encode()
    with pytest.raises((TypeError, ValueError)):
        codec.decode_object_snapshot_data(body)

@pytest.mark.parametrize("target", ["guard", "decoder", "constructor", "type", "dunder"])
@pytest.mark.parametrize("entrance", ["construct", "encode", "decode"])
def test_snapshot_module_and_constructor_substitution_refuse(target, entrance):
    value = snapshot()
    body = codec.encode_object_snapshot_data(value)
    pid = os.fork()
    if pid == 0:
        calls = []
        def foreign(*args, **kwargs):
            calls.append(True)
            raise AssertionError("foreign dispatch")
        try:
            if target == "guard": codec._codec_guard = foreign
            elif target == "decoder": codec._provider = foreign
            elif target == "constructor": owner.OntologyObjectSnapshotData.__post_init__ = foreign
            elif target == "type": setattr(codec, "type", foreign)
            else: setattr(codec, "__foreign__", foreign)
            try:
                if entrance == "construct": snapshot()
                elif entrance == "encode": codec.encode_object_snapshot_data(value)
                else: codec.decode_object_snapshot_data(body)
            except (TypeError, ValueError): pass
            else: raise AssertionError("substitution accepted")
            assert calls == []
        except BaseException: os._exit(1)
        os._exit(0)
    assert os.waitpid(pid, 0)[1] == 0


@pytest.mark.parametrize("target", ["guard", "provider_constructor", "snapshot_constructor", "decoder"])
def test_snapshot_actual_provider_return_authenticates_next_dispatch(monkeypatch, target):
    import sys
    from typing import Any, cast
    value = snapshot()
    body = codec.encode_object_snapshot_data(value)
    boundary = cast(Any, codec._provider).__wrapped__.__code__
    injected, calls = [], []
    def foreign(*args, **kwargs):
        calls.append(True)
        raise AssertionError("foreign snapshot return-boundary dispatch")
    def observe(frame, event, result):
        if event == "return" and frame.f_code is boundary:
            sys.setprofile(None)
            if target == "guard": monkeypatch.setattr(codec, "_codec_guard", foreign)
            elif target == "provider_constructor": monkeypatch.setattr(owner.OntologyObjectProviderAuthorityClaim, "__post_init__", foreign)
            elif target == "snapshot_constructor": monkeypatch.setattr(owner.OntologyObjectSnapshotData, "__init__", foreign)
            else: monkeypatch.setattr(codec, "_authority", foreign)
            injected.append(True)
    try:
        sys.setprofile(observe)
        with pytest.raises(TypeError, match="shape operation identity"):
            codec.decode_object_snapshot_data(body)
    finally:
        sys.setprofile(None)
    assert injected == [True] and calls == []


def _copy_data(record, **changes):
    """Make a by-value record without invoking construction or adding provenance."""
    result = object.__new__(type(record))
    for name in type(record).__dataclass_fields__:
        object.__setattr__(result, name, changes.get(name, object.__getattribute__(record, name)))
    return result


@pytest.fixture(scope="module")
def complete_snapshot():
    from pathlib import Path
    from aware_ontology_object_facade_client import object_value_codec
    path = Path(__file__).resolve().parents[3] / "runtime/python/tests/fixtures/object-value-complete-v3.json"
    value = object_value_codec.decode_object_value(path.read_bytes())
    baseline = snapshot(source=True)
    authority = owner.OntologyObjectSnapshotAuthorityData.create(
        value_digest=value.value_digest, provider_authority=baseline.authority.provider_authority,
        class_binding_digest="sha256:binding", topology_digest="sha256:topology",
        branch_ref="branch:1", revision_ref="revision:1", projection_ref="projection:1",
        view_digest="sha256:view", source_authority=baseline.authority.source_authority)
    return owner.OntologyObjectSnapshotData.create(value=value, authority=authority)


def _authority_arguments(authority):
    return {name: object.__getattribute__(authority, name)
            for name in type(authority).__dataclass_fields__ if name != "authority_digest"}


@pytest.mark.parametrize("poison", ["foreign", "text_subclass", "integer_subclass", "list_subclass"])
@pytest.mark.parametrize("entrance", [
    "provider", "source", "authority_scalar", "nested_provider", "nested_source",
    "snapshot_value", "snapshot_authority", "snapshot_nested", "instance", "branch_ref",
    "revision_ref", "projection_ref", "view_digest", "topology_digest", "class_binding_digest",
    "association_claim", "schema_claim", "endpoint_nested_claim", "endpoint_enum", "claim_enum",
    "claim_scalar", "source_scalar", "object_instance", "object_members", "edge_direction",
])
def test_returned_a5_factories_and_properties_reject_foreign_operands_without_calls(complete_snapshot, poison, entrance):
    from typing import Any, cast
    value = complete_snapshot
    calls = []
    class ForeignMeta(type):
        def __eq__(cls, other):
            calls.append("metaclass equality")
            raise AssertionError("foreign metaclass equality")
    class Hooks:
        def __getattribute__(self, name):
            calls.append("attribute")
            raise AssertionError("foreign attribute")
        def __eq__(self, other):
            calls.append("equality")
            raise AssertionError("foreign equality")
        def __hash__(self):
            calls.append("hash")
            raise AssertionError("foreign hash")
        def __iter__(self):
            calls.append("iteration")
            raise AssertionError("foreign iteration")
        def __str__(self):
            calls.append("string")
            raise AssertionError("foreign string")
    class Foreign(Hooks, metaclass=ForeignMeta): pass
    class Text(Hooks, str): pass
    class Integer(Hooks, int): pass
    class Items(Hooks, list): pass
    bad = cast(Any, {"foreign": Foreign, "text_subclass": Text,
                     "integer_subclass": Integer, "list_subclass": Items}[poison]())
    authority_args = _authority_arguments(value.authority)
    association = next(item for item in value.value.external_endpoint_references
                       if type(item) is owner.ExternalAssociationEndpointReference)
    schema = next(item for item in value.value.external_endpoint_references
                  if type(item) is owner.ExternalSchemaFieldEndpointReference)
    with pytest.raises((TypeError, ValueError)):
        if entrance in ("provider", "source", "authority_scalar", "nested_provider", "nested_source"):
            if entrance == "provider": authority_args["provider_authority"] = bad
            elif entrance == "source": authority_args["source_authority"] = bad
            elif entrance == "authority_scalar": authority_args["branch_ref"] = bad
            elif entrance == "nested_provider": authority_args["provider_authority"] = _copy_data(value.authority.provider_authority, provider_key=bad)
            else: authority_args["source_authority"] = _copy_data(value.authority.source_authority, source_mapping_digest=bad)
            owner.OntologyObjectSnapshotAuthorityData.create(**authority_args)
        elif entrance == "snapshot_value": owner.OntologyObjectSnapshotData.create(value=bad, authority=value.authority)
        elif entrance == "snapshot_authority": owner.OntologyObjectSnapshotData.create(value=value.value, authority=bad)
        elif entrance == "snapshot_nested": owner.OntologyObjectSnapshotData.create(value=value.value, authority=_copy_data(value.authority, provider_authority=bad))
        elif entrance in ("instance", "branch_ref", "revision_ref", "projection_ref", "view_digest", "topology_digest", "class_binding_digest"):
            restamped = _copy_data(value, **({"value": bad} if entrance == "instance" else {"authority": bad}))
            getattr(restamped, entrance)
        elif entrance in ("association_claim", "schema_claim", "endpoint_nested_claim", "endpoint_enum"):
            endpoint = association if entrance == "association_claim" else schema
            args = {name: object.__getattribute__(endpoint, name)
                    for name in type(endpoint).__dataclass_fields__ if name != "reference_digest"}
            if entrance == "endpoint_enum": args["endpoint_residence"] = bad
            elif entrance == "endpoint_nested_claim": args["evidence_claim"] = _copy_data(endpoint.evidence_claim, evidence_ref=bad)
            else: args["evidence_claim"] = bad
            type(endpoint).create(**args)
        elif entrance in ("claim_enum", "claim_scalar"):
            owner.ExternalRelationshipEndpointEvidenceClaim.create(provider_key=bad if entrance == "claim_scalar" else "p", provider_generation="g", profile=bad if entrance == "claim_enum" else owner.ExternalRelationshipEndpointEvidenceProfile.RESIDENT_LOCAL, evidence_ref="e")
        elif entrance == "source_scalar": owner.OntologyObjectSourceAuthorityEvidence.create(source_coordinate_ref=bad, source_observation_ref="o", source_mapping_digest="d")
        elif entrance == "object_instance": owner.OntologyObjectValue.create(bad)
        elif entrance == "object_members": owner.OntologyObjectValue.create(value.instance, [bad])
        else: owner.OntologyObjectRelationshipEdgeValue.from_instance(owner.RelationshipInstance("r", "T.r", "a", "b"), direction=bad)
    assert calls == []


def _raw_wire(snapshot_data):
    """Trusted vector assembly, independent of the validators under test."""
    def render(record):
        kind = type(record)
        if record is None or kind is str or kind is int or kind is bool:
            return record
        if kind is tuple:
            return [render(item) for item in record]
        if isinstance(record, owner.StrEnum):
            return record.value
        # Complete value grammar is already frozen; use an independent copy of
        # its accepted wire for tests that restamp its digest or nested claims.
        if kind is owner.FieldValue or kind is owner.RuntimeValue:
            return record.to_wire()
        wire = {name: render(object.__getattribute__(record, name)) for name in kind.__dataclass_fields__}
        contracts = {owner.OntologyObjectSnapshotData: owner.OBJECT_SNAPSHOT_CONTRACT,
                     owner.OntologyObjectSnapshotAuthorityData: owner.OBJECT_SNAPSHOT_AUTHORITY_CONTRACT,
                     owner.OntologyObjectSourceAuthorityEvidence: owner.OBJECT_SOURCE_AUTHORITY_CONTRACT,
                     owner.OntologyObjectValue: owner.OBJECT_VALUE_CONTRACT,
                     owner.OntologyObjectRelationshipSlice: owner.OBJECT_RELATIONSHIP_SLICE_CONTRACT,
                     owner.ExternalRelationshipEndpointEvidenceClaim: owner.EXTERNAL_RELATIONSHIP_ENDPOINT_EVIDENCE_CLAIM_CONTRACT,
                     owner.ExternalAssociationEndpointReference: owner.EXTERNAL_ASSOCIATION_ENDPOINT_REFERENCE_CONTRACT,
                     owner.ExternalSchemaFieldEndpointReference: owner.EXTERNAL_SCHEMA_FIELD_ENDPOINT_REFERENCE_CONTRACT}
        if kind in contracts:
            wire["contract"] = contracts[kind]
        return wire
    return render(snapshot_data)


def _restamp_snapshot(record, *, authority=None, value=None, recompute_authority=False):
    value = record.value if value is None else value
    authority = record.authority if authority is None else authority
    if recompute_authority:
        wire = _raw_wire(_copy_data(record, authority=authority))["authority"]
        digest = owner.digest_payload(owner.OBJECT_SNAPSHOT_AUTHORITY_CONTRACT,
                                      {k: v for k, v in wire.items() if k not in ("contract", "authority_digest")})
        authority = _copy_data(authority, authority_digest=digest)
    result = _copy_data(record, value=value, authority=authority)
    wire = _raw_wire(result)
    return _copy_data(result, snapshot_digest=owner.digest_payload(owner.OBJECT_SNAPSHOT_CONTRACT,
                      {k: v for k, v in wire.items() if k not in ("contract", "snapshot_digest")}))


@pytest.mark.parametrize("change", ["source_digest", "source_payload", "authority_digest", "authority_payload",
    "value_digest", "value_authority_join", "snapshot_digest", "provider_grade", "provider_coordinates"])
@pytest.mark.parametrize("entrance", ["encode", "wire", "canonical", "direct_construct", "factory"])
def test_returned_a5_semantic_restamps_reject_even_under_recomputed_outer_digests(complete_snapshot, change, entrance):
    baseline = complete_snapshot
    if change.startswith("source"):
        evidence = baseline.authority.source_authority
        evidence = _copy_data(evidence, **({"source_authority_digest": "sha256:wrong"} if change == "source_digest" else {"source_mapping_digest": "sha256:changed"}))
        candidate = _restamp_snapshot(baseline, authority=_copy_data(baseline.authority, source_authority=evidence), recompute_authority=True)
    elif change.startswith("authority"):
        authority = _copy_data(baseline.authority, **({"authority_digest": "sha256:wrong"} if change == "authority_digest" else {"view_digest": "sha256:changed"}))
        candidate = _restamp_snapshot(baseline, authority=authority)
    elif change == "value_digest": candidate = _restamp_snapshot(baseline, value=_copy_data(baseline.value, value_digest="sha256:wrong"))
    elif change == "value_authority_join": candidate = _restamp_snapshot(baseline, authority=_copy_data(baseline.authority, value_digest="sha256:another-value"), recompute_authority=True)
    elif change == "snapshot_digest": candidate = _copy_data(baseline, snapshot_digest="sha256:wrong")
    else:
        provider = _copy_data(baseline.authority.provider_authority, **({"grade": "unsupported"} if change == "provider_grade" else {"canonical_branch_ref": "branch:foreign"}))
        candidate = _restamp_snapshot(baseline, authority=_copy_data(baseline.authority, provider_authority=provider), recompute_authority=True)
    with pytest.raises((TypeError, ValueError)):
        if entrance == "encode": codec.encode_object_snapshot_data(candidate)
        elif entrance == "wire": candidate.to_wire()
        elif entrance == "canonical": candidate.canonical_bytes()
        elif entrance == "direct_construct": owner.OntologyObjectSnapshotData(candidate.value, candidate.authority, candidate.snapshot_digest)
        else:
            if change == "snapshot_digest":
                # Factories derive, rather than consume, the outer digest.
                owner.OntologyObjectSnapshotData(candidate.value, candidate.authority, candidate.snapshot_digest)
            else: owner.OntologyObjectSnapshotData.create(value=candidate.value, authority=candidate.authority)


@pytest.mark.parametrize("entrance", ["source", "authority", "snapshot"])
def test_returned_a5_nested_invalid_source_rejects_during_each_constructor(complete_snapshot, entrance):
    evidence = _copy_data(complete_snapshot.authority.source_authority, source_authority_digest="sha256:wrong")
    authority = _copy_data(complete_snapshot.authority, source_authority=evidence)
    candidate = _restamp_snapshot(complete_snapshot, authority=authority, recompute_authority=True)
    with pytest.raises(ValueError):
        if entrance == "source": owner.OntologyObjectSourceAuthorityEvidence(**{name: object.__getattribute__(evidence, name) for name in type(evidence).__dataclass_fields__})
        elif entrance == "authority": owner.OntologyObjectSnapshotAuthorityData(**{name: object.__getattribute__(candidate.authority, name) for name in type(candidate.authority).__dataclass_fields__})
        else: owner.OntologyObjectSnapshotAuthorityData.create(**_authority_arguments(candidate.authority))


def test_returned_a5_valid_detached_copies_preserve_canonical_bytes(complete_snapshot):
    record = complete_snapshot
    authority = _copy_data(record.authority, provider_authority=_copy_data(record.authority.provider_authority), source_authority=_copy_data(record.authority.source_authority))
    candidate = _copy_data(record, value=_copy_data(record.value), authority=authority)
    assert candidate is not record and candidate.authority is not record.authority
    expected = codec.encode_object_snapshot_data(record)
    assert codec.encode_object_snapshot_data(candidate) == expected
    assert codec.encode_object_snapshot_data(codec.decode_object_snapshot_data(expected)) == expected
    assert owner.OntologyObjectSnapshotData.create(value=candidate.value, authority=candidate.authority).canonical_bytes() == expected


@pytest.mark.parametrize("change", ["relationship_digest", "endpoint_digest", "claim_digest", "claim_payload",
    "relationship_owner", "relationship_type", "edge_direction", "endpoint_owner", "endpoint_relationship",
    "duplicate_field", "duplicate_relationship", "duplicate_endpoint", "coverage_correspondence"])
@pytest.mark.parametrize("entrance", ["encode", "direct_construct", "factory"])
def test_returned_a5_nested_value_laws_survive_recomputed_ancestor_digests(complete_snapshot, change, entrance):
    original = complete_snapshot.value
    value = original
    if change.startswith("relationship") or change in ("edge_direction", "coverage_correspondence"):
        relationship = original.relationships[0]
        if change == "relationship_digest": relationship = _copy_data(relationship, relationship_value_digest="sha256:wrong")
        elif change == "relationship_owner": relationship = _copy_data(relationship, owner_instance_ref="object:another")
        elif change == "relationship_type": relationship = _copy_data(relationship, owner_type_ref="Type:another")
        elif change == "edge_direction": relationship = _copy_data(relationship, edges=(_copy_data(relationship.edges[0], peer_instance_ref="object:another"), *relationship.edges[1:]))
        else: relationship = _copy_data(relationship, coverage=_copy_data(relationship.coverage, grade=owner.CoverageGrade.COMPLETE, missing_refs=("missing",)))
        if change != "relationship_digest":
            wire = _raw_wire(relationship)
            relationship = _copy_data(relationship, relationship_value_digest=owner.digest_payload(owner.OBJECT_RELATIONSHIP_SLICE_CONTRACT,
                    {k: v for k, v in wire.items() if k not in ("contract", "relationship_value_digest")}))
        value = _copy_data(original, relationships=(relationship, *original.relationships[1:]))
    elif change.startswith("endpoint") or change.startswith("claim"):
        endpoint = original.external_endpoint_references[0]
        if change.startswith("claim"):
            claim = _copy_data(endpoint.evidence_claim, **({"claim_digest": "sha256:wrong"} if change == "claim_digest" else {"evidence_ref": "evidence:changed"}))
            endpoint = _copy_data(endpoint, evidence_claim=claim)
        elif change == "endpoint_digest": endpoint = _copy_data(endpoint, reference_digest="sha256:wrong")
        elif change == "endpoint_owner":
            endpoint = _copy_data(endpoint, **({"source_instance_ref": "object:another"} if type(endpoint) is owner.ExternalSchemaFieldEndpointReference else {"association_instance_ref": "object:another"}))
        else:
            endpoint = _copy_data(endpoint, **({"relationship_ref": "Unrelated.field"} if type(endpoint) is owner.ExternalSchemaFieldEndpointReference else {"role_ref": "Unrelated.role"}))
        if change != "endpoint_digest":
            wire = _raw_wire(endpoint)
            endpoint = _copy_data(endpoint, reference_digest=owner.digest_payload(wire["contract"],
                    {k: v for k, v in wire.items() if k not in ("contract", "reference_digest")}))
        value = _copy_data(original, external_endpoint_references=(endpoint, *original.external_endpoint_references[1:]))
    elif change == "duplicate_field": value = _copy_data(original, fields=(*original.fields, original.fields[0]))
    elif change == "duplicate_relationship": value = _copy_data(original, relationships=(*original.relationships, original.relationships[0]))
    else: value = _copy_data(original, external_endpoint_references=(*original.external_endpoint_references, original.external_endpoint_references[0]))
    wire = _raw_wire(value)
    value = _copy_data(value, value_digest=owner.digest_payload(owner.OBJECT_VALUE_CONTRACT,
                {k: v for k, v in wire.items() if k not in ("contract", "value_digest")}))
    candidate = _restamp_snapshot(complete_snapshot, value=value,
                  authority=_copy_data(complete_snapshot.authority, value_digest=value.value_digest), recompute_authority=True)
    with pytest.raises((TypeError, ValueError)):
        if entrance == "encode": codec.encode_object_snapshot_data(candidate)
        elif entrance == "direct_construct": owner.OntologyObjectSnapshotData(candidate.value, candidate.authority, candidate.snapshot_digest)
        else: owner.OntologyObjectSnapshotData.create(value=candidate.value, authority=candidate.authority)


@pytest.mark.parametrize("target", ["source_validator", "authority_validator", "snapshot_validator", "encoder"])
def test_returned_a5_actual_source_validation_return_checks_next_dispatch(monkeypatch, complete_snapshot, target):
    import sys
    from typing import Any, cast
    boundary = cast(Any, owner._value_source_wire).__wrapped__.__code__
    calls, injected = [], []
    def foreign(*args, **kwargs):
        calls.append(True)
        raise AssertionError("foreign semantic validation dispatch")
    def observe(frame, event, result):
        if event == "return" and frame.f_code is boundary:
            sys.setprofile(None)
            if target == "encoder": monkeypatch.setattr(codec, "_canonical", foreign)
            else: monkeypatch.setattr(owner, {"source_validator": "_value_source_wire", "authority_validator": "_value_authority_wire", "snapshot_validator": "_value_snapshot_wire"}[target], foreign)
            injected.append(True)
    try:
        sys.setprofile(observe)
        with pytest.raises(TypeError, match="shape operation identity"):
            codec.encode_object_snapshot_data(complete_snapshot)
    finally:
        sys.setprofile(None)
    assert injected == [True] and calls == []


@pytest.mark.parametrize("location", ["value", "authority", "provider", "source", "field", "claim"])
@pytest.mark.parametrize("entrance", ["encode", "construct", "wire"])
def test_returned_a5_recursive_operand_preflight_precedes_all_nested_behavior(complete_snapshot, location, entrance):
    from typing import Any, cast
    calls = []
    class Foreign:
        def __getattribute__(self, name):
            calls.append(name)
            raise AssertionError("foreign nested attribute")
        def __eq__(self, other):
            calls.append("equality")
            raise AssertionError("foreign nested equality")
    bad = cast(Any, Foreign())
    record = complete_snapshot
    if location == "value": candidate = _copy_data(record, value=bad)
    elif location == "authority": candidate = _copy_data(record, authority=bad)
    elif location == "provider": candidate = _copy_data(record, authority=_copy_data(record.authority, provider_authority=bad))
    elif location == "source": candidate = _copy_data(record, authority=_copy_data(record.authority, source_authority=bad))
    elif location == "field":
        first = _copy_data(record.value.fields[0], value=bad)
        candidate = _copy_data(record, value=_copy_data(record.value, fields=(first, *record.value.fields[1:])))
    else:
        first = _copy_data(record.value.external_endpoint_references[0], evidence_claim=bad)
        candidate = _copy_data(record, value=_copy_data(record.value, external_endpoint_references=(first, *record.value.external_endpoint_references[1:])))
    with pytest.raises((TypeError, ValueError)):
        if entrance == "encode": codec.encode_object_snapshot_data(candidate)
        elif entrance == "construct": owner.OntologyObjectSnapshotData(candidate.value, candidate.authority, candidate.snapshot_digest)
        else: candidate.to_wire()
    assert calls == []


@pytest.mark.parametrize("location", ["claim_profile", "claim_grade", "endpoint_residence", "slice_direction", "slot_role", "member_role", "runtime_value_role", "coverage_member_role"])
@pytest.mark.parametrize("entrance", ["encode", "factory"])
def test_returned_a5_wrong_native_slot_types_produce_typed_refusal(complete_snapshot, location, entrance):
    baseline = complete_snapshot
    if location.startswith("claim") or location == "endpoint_residence":
        endpoint = baseline.value.external_endpoint_references[0]
        if location.startswith("claim"):
            claim = _copy_data(endpoint.evidence_claim, **({"profile": "resident_local"} if location == "claim_profile" else {"input_grade": 1}))
            endpoint = _copy_data(endpoint, evidence_claim=claim)
        else: endpoint = _copy_data(endpoint, endpoint_residence="external_dependency")
        value = _copy_data(baseline.value, external_endpoint_references=(endpoint, *baseline.value.external_endpoint_references[1:]))
        candidate = _copy_data(baseline, value=value)
    elif location == "slice_direction":
        relationship = _copy_data(baseline.value.relationships[0], direction="outgoing")
        candidate = _copy_data(baseline, value=_copy_data(baseline.value, relationships=(relationship,)))
    elif location == "runtime_value_role":
        field = baseline.value.fields[0]
        invalid = _copy_data(field.value, value=field.value)
        candidate = _copy_data(baseline, value=_copy_data(baseline.value, fields=(_copy_data(field, value=invalid), *baseline.value.fields[1:])))
    elif location == "coverage_member_role":
        relationship = baseline.value.relationships[0]
        relationship = _copy_data(relationship, coverage=_copy_data(relationship.coverage, missing_refs=(baseline.value,)))
        candidate = _copy_data(baseline, value=_copy_data(baseline.value, relationships=(relationship,)))
    elif location == "slot_role": candidate = _copy_data(baseline, authority=_copy_data(baseline.authority, provider_authority=baseline.value))
    else: candidate = _copy_data(baseline, value=_copy_data(baseline.value, relationships=(baseline.value,)))
    with pytest.raises((TypeError, ValueError)):
        if entrance == "encode": codec.encode_object_snapshot_data(candidate)
        else: owner.OntologyObjectSnapshotData.create(value=candidate.value, authority=candidate.authority)


@pytest.mark.parametrize("kind", [owner.OntologyObjectProviderAuthorityClaim, owner.OntologyObjectSourceAuthorityEvidence,
    owner.OntologyObjectSnapshotAuthorityData, owner.OntologyObjectValue])
@pytest.mark.parametrize("entrance", ["encode", "factory"])
def test_returned_a5_missing_native_slots_are_typed_refusals(complete_snapshot, kind, entrance):
    incomplete = object.__new__(kind)
    baseline = complete_snapshot
    if kind is owner.OntologyObjectValue: candidate = _copy_data(baseline, value=incomplete)
    elif kind is owner.OntologyObjectSnapshotAuthorityData: candidate = _copy_data(baseline, authority=incomplete)
    elif kind is owner.OntologyObjectProviderAuthorityClaim: candidate = _copy_data(baseline, authority=_copy_data(baseline.authority, provider_authority=incomplete))
    else: candidate = _copy_data(baseline, authority=_copy_data(baseline.authority, source_authority=incomplete))
    with pytest.raises(TypeError, match="missing a required slot"):
        if entrance == "encode": codec.encode_object_snapshot_data(candidate)
        else: owner.OntologyObjectSnapshotData.create(value=candidate.value, authority=candidate.authority)
