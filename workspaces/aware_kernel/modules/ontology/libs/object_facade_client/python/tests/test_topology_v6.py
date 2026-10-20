"""Literal detached V6 vectors and boundary checks, not original model issuance."""

import copy
import gc
import hashlib
import json
import weakref

import pytest


@pytest.fixture
def codec():
    # Do not seal the existing facade owner while other test modules are still
    # being collected and importing its retained TypeSchema dependencies.
    from aware_ontology_object_facade_client import topology_v6

    return topology_v6


def uid(number):
    return f"00000000-0000-0000-0000-{number:012d}"


@pytest.fixture
def vector(codec):
    projections = [
        {"projection_ref": name, "graph_ref": "opg:" + uid(index), "identity_ref": "opg-identity:" + uid(index),
         "is_branchable": False, "root_node_refs": ["opg-node:" + uid(index)],
         "nodes": [["opg-node:" + uid(index), cls, True, True, "one", None]], "observables": []}
        for index, name, cls in ((1, "demo:Source", "demo.Source"), (2, "demo:Target", "demo.Target"))]
    policy = ["many_to_one", "reference", "forward", False, "forward", "target_id", False, False, False,
        False, True, None, None, False, False, None, None, None, None, None, None, False, False, None, None]
    return {"contract": codec.CONTRACT, "profile": codec.PROFILE, "namespace": "demo", "semantic_version": "1.0.0",
        "schema_digest": "sha256:" + "1" * 64, "schema_slice_digest": "sha256:" + "2" * 64,
        "input_grade": "portable_input", "evidence_digest": "sha256:" + "3" * 64,
        "projections": projections,
        "relationships": [["relationship:" + uid(3), "demo.Source", "demo.Source.target", "demo.Target",
            [0], [0], None, None, False, False, False, True, False, policy]],
        "portals": [["opg-portal:" + uid(4), "demo:Source", "demo:Target", "relationship:" + uid(3),
            "demo.Source.target", "opg-node:" + uid(1), "opg-node:" + uid(2), "demo.Source", "demo.Target", uid(5)]]}


def test_v6_canonical_digest_matches_independent_json_and_hash(vector, codec):
    before = copy.deepcopy(vector)
    body = codec.encode_portal_topology_v6(vector)
    payload = json.dumps(vector, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    digest = "sha256:" + hashlib.sha256(codec.CONTRACT.encode() + b"\n" + payload).hexdigest()
    expected = json.dumps({**vector, "topology_digest": digest}, ensure_ascii=False,
        sort_keys=True, separators=(",", ":")).encode()
    assert body == expected and codec.decode_portal_topology_v6(body) == vector
    assert len(body) == 1940
    assert digest == "sha256:685389d71aa97acb5f8c51af2722f38bc59eafb8de7b1c2b8263b824f75cf41e"
    assert vector == before
    assert len(body) < codec.MAX_BYTES


@pytest.mark.parametrize("field", ("contract", "profile", "input_grade", "namespace", "schema_digest",
    "schema_slice_digest", "evidence_digest", "projections", "relationships", "portals"))
def test_v6_closed_root_requires_every_declared_field(vector, field, codec):
    vector.pop(field)
    with pytest.raises(ValueError):
        codec.encode_portal_topology_v6(vector)


@pytest.mark.parametrize("field,value", (("contract", "aware.ontology.runtime-schema-topology.v5"),
    ("profile", "unknown"), ("input_grade", "issued"), ("namespace", ""), ("schema_digest", "sha256:bad"),
    ("extra", None)))
def test_v6_never_accepts_v5_or_unknown_grade_fields(vector, field, value, codec):
    vector[field] = value
    with pytest.raises(ValueError):
        codec.encode_portal_topology_v6(vector)


@pytest.mark.parametrize("fault", ("same_projection", "wrong_target_type", "wrong_target_node", "wrong_source_node",
    "wrong_field", "no_relationship", "orphan_relationship", "duplicate_portal", "wrong_binding", "family",
    "node_family", "no_root", "extra_root", "duplicate_graph", "duplicate_identity", "node_alias", "table_order",
    "bool_slot", "bool_integer", "join_integer", "policy", "reverse", "constructed", "unique"))
def test_v6_closed_endpoint_and_membership_laws(vector, fault, codec):
    portal = vector["portals"][0]
    relation = vector["relationships"][0]
    if fault in ("same_projection", "wrong_target_type", "wrong_target_node", "wrong_source_node", "wrong_field", "wrong_binding", "family"):
        position, value = {"same_projection": (2, "demo:Source"), "wrong_target_type": (8, "demo.Other"),
            "wrong_target_node": (6, "opg-node:" + uid(1)), "wrong_source_node": (5, "opg-node:" + uid(2)),
            "wrong_field": (4, "demo.Source.other"), "wrong_binding": (9, "bad"), "family": (0, "opg:" + uid(4))}[fault]
        portal[position] = value
    elif fault == "no_relationship":
        vector["relationships"] = []
    elif fault == "orphan_relationship":
        vector["portals"] = []
    elif fault == "duplicate_portal":
        vector["portals"].append(copy.deepcopy(portal))
    elif fault == "node_family":
        vector["projections"][0]["nodes"][0][0] = "opg:" + uid(1)
    elif fault in ("no_root", "extra_root"):
        vector["projections"][0]["root_node_refs"] = [] if fault == "no_root" else ["opg-node:" + uid(2)]
    elif fault in ("duplicate_graph", "duplicate_identity"):
        field = "graph_ref" if fault == "duplicate_graph" else "identity_ref"
        vector["projections"][1][field] = vector["projections"][0][field]
    elif fault == "node_alias":
        vector["projections"][1]["nodes"] = copy.deepcopy(vector["projections"][0]["nodes"])
    elif fault == "table_order":
        vector["projections"].reverse()
    elif fault == "bool_slot":
        relation[4] = [False]
    elif fault == "bool_integer":
        vector["projections"][0]["nodes"][0][2] = 1
    elif fault == "join_integer":
        relation[13][3] = 0
    elif fault == "policy":
        relation[13][0] = "many_to_many"
    elif fault == "reverse":
        relation[13][11] = "list"
    elif fault == "constructed":
        relation[12] = True
    elif fault == "unique":
        relation[10] = True
    with pytest.raises(ValueError):
        codec.encode_portal_topology_v6(vector)


@pytest.mark.parametrize("fault", ("digest", "whitespace", "unknown", "duplicate", "trailing", "nan", "depth", "oversize"))
def test_v6_framing_and_preparse_bounds(vector, fault, codec):
    body = codec.encode_portal_topology_v6(vector)
    if fault == "digest":
        root = json.loads(body)
        root["topology_digest"] = "sha256:" + "0" * 64
        body = json.dumps(root, sort_keys=True, separators=(",", ":")).encode()
    elif fault == "whitespace":
        body = b" " + body
    elif fault == "unknown":
        body = body[:-1] + b',"extra":null}'
    elif fault == "duplicate":
        body = body[:-1] + b',"contract":"anything"}'
    elif fault == "trailing":
        body += b"{}"
    elif fault == "nan":
        body = b'{"x":NaN}'
    elif fault == "depth":
        body = b"[" * 65 + b"0" + b"]" * 65
    else:
        body = b" " * (codec.MAX_BYTES + 1)
    with pytest.raises(ValueError):
        codec.decode_portal_topology_v6(body)


def test_v6_hostile_values_reject_without_behavior(vector, codec):
    calls = []

    class Foreign:
        def __eq__(self, other):
            calls.append("eq")
            return True

        def __iter__(self):
            calls.append("iter")
            return iter(())

        def __str__(self):
            calls.append("str")
            return "anything"

    vector["portals"][0][2] = Foreign()
    with pytest.raises(ValueError):
        codec.encode_portal_topology_v6(vector)
    with pytest.raises(ValueError):
        codec.decode_portal_topology_v6(Foreign())
    assert calls == []


def test_v6_evidence_binding_is_ordered_exact_and_detached(codec):
    bodies = (b"first", b"second")
    facts = ("facts", ())
    digest = codec.evidence_digest(b"bundle", b"slice", bodies, facts)
    assert digest == "sha256:3e48f9e4afe459bab303656345a60e2046ca83316ff8291ffa4ab433062cedda"
    assert digest == codec.evidence_digest(b"bundle", b"slice", bodies, facts)
    assert digest != codec.evidence_digest(b"bundle", b"slice", bodies[::-1], facts)
    assert digest != codec.evidence_digest(b"bundle", b"slice", bodies, ("facts", (1,)))
    assert digest != codec.evidence_digest(b"bundle!", b"slice", bodies, facts)


@pytest.mark.parametrize("body", (b"[" * 65 + b"0" + b"]" * 65,
    b"[" + b"0," * 16_384 + b"0]", b'[' + b'"x",' * 16_384 + b'"x"]'))
def test_v6_overflow_refuses_before_json_decode(monkeypatch, body, codec):
    def foreign(*args, **kwargs):
        raise AssertionError("decoder must not run")

    with monkeypatch.context() as changed:
        changed.setattr(codec.json, "loads", foreign)
        with pytest.raises(ValueError, match="preparse"):
            codec.decode_portal_topology_v6(body)


def test_v6_held_encoder_failure_releases_complete_caller_payload(vector, codec):
    class Foreign:
        pass

    foreign = Foreign()
    reference = weakref.ref(foreign)
    vector["portals"][0][2] = foreign
    with pytest.raises(ValueError) as held:
        codec.encode_portal_topology_v6(vector)
    vector["portals"][0][2] = None
    del foreign
    gc.collect()
    assert reference() is None
    trace = held.value.__traceback__
    while trace is not None:
        if trace.tb_frame.f_code.co_filename == codec.__file__:
            assert not trace.tb_frame.f_locals or all(value is None for value in trace.tb_frame.f_locals.values())
        trace = trace.tb_next


def test_v6_held_parser_failure_drops_body_retaining_context(codec):
    with pytest.raises(ValueError) as held:
        codec.decode_portal_topology_v6(b'{"x":')
    assert held.value.__cause__ is held.value.__context__ is None
    trace = held.value.__traceback__
    while trace is not None:
        if trace.tb_frame.f_code.co_filename == codec.__file__:
            assert not trace.tb_frame.f_locals or all(value is None for value in trace.tb_frame.f_locals.values())
        trace = trace.tb_next


def test_v6_preparse_scan_is_string_aware(vector, codec):
    vector["namespace"] = "[" * 65 + '\\"{☃}'
    body = codec.encode_portal_topology_v6(vector)
    assert codec.decode_portal_topology_v6(body) == vector
