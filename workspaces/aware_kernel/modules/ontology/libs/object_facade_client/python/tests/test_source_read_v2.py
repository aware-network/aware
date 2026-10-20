"""Detached V6 carriage; fixture admissions establish no original authority."""

import asyncio
import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest


def canonical(value):
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()


def digest(domain, value):
    return (
        "sha256:"
        + hashlib.sha256(domain.encode() + b"\x00" + canonical(value)).hexdigest()
    )


def seal(value, field):
    value[field] = digest(
        value["contract"], {k: v for k, v in value.items() if k != field}
    )
    return value


def body(contract, value):
    raw = value if type(value) is bytes else canonical(value)
    return {
        "contract_ref": contract,
        "body_hex": raw.hex(),
        "body_hash": "sha256:" + hashlib.sha256(raw).hexdigest(),
    }


def unpack(value):
    return json.loads(bytes.fromhex(value["body_hex"]))


def model_from_bodies(bundle, slice_, topology, root_type, projection):
    return seal(
        {
            "contract": "aware.ontology.object-read-model-binding.v2",
            "model_ref": "fixture:model",
            "model_revision_ref": "fixture:model-epoch",
            "root_type_ref": root_type,
            "projection_ref": projection,
            "schema_bundle": body("aware.meta.semantic-type-schema.v1", bundle),
            "schema_slice": body("aware.meta.semantic-type-schema-slice.v1", slice_),
            "topology": body("aware.ontology.runtime-schema-topology.v6", topology),
            "topology_profile_ref": "meta-inspect-forward-portals.v1",
            "model_admission": body("fixture.unissued-model.v1", {"detached": True}),
        },
        "model_digest",
    )


def result_for(ctx, outcome=None):
    w, request = ctx["wire"], ctx["request"]
    if outcome is None:
        outcome = {
            "tag": "ok",
            "finality": "observation",
            "value": {"view": body(w.OBSERVATION_V2_CONTRACT, ctx["observation"])},
        }
    result = {
        "contract": w.RESULT_CONTRACT,
        "profile_ref": w.PROFILE_V2,
        "kind": "view.read",
        "origin": request["origin"],
        "operation": None,
        "ordinal": None,
        "intent_digest": request["intent_digest"],
        "delivery_ref": request["delivery"]["delivery_ref"],
        "responder_incarnation": request["delivery"]["recipient_incarnation"],
        "outcome": outcome,
    }
    observed = seal(
        {
            "contract": w.OUTCOME_OBSERVATION_V2_CONTRACT,
            "request_intent_digest": request["intent_digest"],
            "outcome_hash": "sha256:"
            + hashlib.sha256(
                canonical({"contract": w.PREIMAGE_V2_CONTRACT, "result": result})
            ).hexdigest(),
            "issuer_ref": "fixture:host",
            "issuer_generation": result["responder_incarnation"],
            "verification_ref": "fixture:unissued",
            "owner_observation_body": body("fixture.unissued.v1", {}),
        },
        "observation_digest",
    )
    result["witnesses"] = [
        {
            "role": "command_outcome",
            "issuer_ref": observed["issuer_ref"],
            "issuer_generation": observed["issuer_generation"],
            "body": body(w.OUTCOME_OBSERVATION_V2_CONTRACT, observed),
            "value_field": None,
        }
    ]
    if outcome["tag"] == "ok":
        result["witnesses"].append(
            {
                "role": "view_observation",
                "issuer_ref": observed["issuer_ref"],
                "issuer_generation": observed["issuer_generation"],
                "body": None,
                "value_field": "view",
            }
        )
    result["result_digest"] = digest(w.RESULT_V2_DIGEST_DOMAIN, result)
    return result


@pytest.fixture(scope="module")
def original_values():
    from aware_meta_type_schema import (
        FieldDefinition,
        ShapeKind,
        TypeDefinition,
        TypeKind,
        TypeSchemaBundle,
        TypeSchemaSlice,
        ValueShape,
        encode_schema_bundle,
        encode_schema_slice,
    )
    from aware_ontology_object_facade_client import source_read_codec as read
    from aware_ontology_object_facade_client import source_read_wire as w
    from aware_ontology_object_facade_client import topology_v6 as v6
    from test_topology_v6 import vector

    artifact = (
        Path(__file__).resolve().parents[8]
        / "docs/reports/ontology-generic-object-observation-wire-successor-vectors-20261003.json"
    )
    legacy = {row["name"]: row for row in json.loads(artifact.read_bytes())["vectors"]}
    source = TypeDefinition(
        "demo.Source",
        "Source",
        TypeKind.GRAPH_OBJECT,
        fields=(
            FieldDefinition(
                "demo.Source.target",
                "target",
                ValueShape(ShapeKind.NAMED, type_ref="demo.Target"),
            ),
        ),
    )
    target_type = TypeDefinition("demo.Target", "Target", TypeKind.GRAPH_OBJECT)
    bundle = TypeSchemaBundle.create(
        namespace="demo", semantic_version="1.0.0", types=(source, target_type)
    )
    slice_ = TypeSchemaSlice.create(bundle, root_type_refs=(source.type_ref,))
    topology = vector.__wrapped__(v6)
    topology.update(
        schema_digest=bundle.schema_digest, schema_slice_digest=slice_.slice_digest
    )
    topology["projections"][0]["observables"] = [
        "observable:00000000-0000-0000-0000-000000000001"
    ]
    topology_raw = v6.encode_portal_topology_v6(topology)
    model = model_from_bodies(
        encode_schema_bundle(bundle),
        encode_schema_slice(slice_),
        topology_raw,
        source.type_ref,
        "demo:Source",
    )
    obs = copy.deepcopy(legacy["observation"]["value"])
    scope = {
        **obs["scope"],
        "root_type_ref": source.type_ref,
        "projection_ref": "demo:Source",
        "observable_ref": topology["projections"][0]["observables"][0],
        "model_digest": model["model_digest"],
    }
    provider = unpack(obs["provider_binding"])
    provider["scope"] = scope
    obs["provider_binding"] = body(w.BINDING_CONTRACT, seal(provider, "binding_digest"))
    reading = unpack(obs["provider_reading"])
    reading.update(scope=scope, provider_binding_digest=provider["binding_digest"])
    root = unpack(reading["typed_state"])
    root["object"].update(type_ref=source.type_ref, fields=[])
    reading["typed_state"] = body(w.ROOT_CONTRACT, root)
    obs["provider_reading"] = body(w.READING_CONTRACT, seal(reading, "reading_digest"))
    target = obs["target"]
    target.update(
        scope=scope, topology_digest=json.loads(topology_raw)["topology_digest"]
    )
    target["target_ref"] = "object-read-target:" + digest(
        w.TARGET_KEY_DOMAIN,
        {
            k: scope[k]
            for k in (
                "ontology_ref",
                "namespace_ref",
                "context_ref",
                "branch_ref",
                "object_ref",
                "observable_ref",
                "projection_ref",
            )
        },
    )
    seal(target, "target_digest")
    obs.update(
        contract=w.OBSERVATION_V2_CONTRACT,
        scope=scope,
        model_binding=body(w.MODEL_V2_CONTRACT, model),
    )
    seal(obs, "observation_digest")
    request = copy.deepcopy(legacy["request_A"]["value"])
    request.update(profile_ref=w.PROFILE_V2, result_budget_bytes=w.MAX_RESULT_BYTES)
    request["payload"]["selection"] = {
        **scope,
        "expected_revision_ref": reading["revision_ref"],
    }
    request["intent_digest"] = digest(
        w.INTENT_V2_CONTRACT,
        {k: v for k, v in request.items() if k not in ("intent_digest", "delivery")},
    )
    return {
        "read": read,
        "wire": w,
        "topology": v6,
        "legacy": legacy,
        "model": model,
        "observation": obs,
        "request": request,
    }


@pytest.fixture
def ctx(original_values):
    return {
        k: v if k in ("read", "wire", "topology") else copy.deepcopy(v)
        for k, v in original_values.items()
    }


def test_explicit_v2_complete_carriage_preserves_exact_bytes(ctx):
    read = ctx["read"]
    for name in ("model_binding", "observation", "request"):
        value = ctx["model" if name == "model_binding" else name]
        raw = getattr(read, "encode_" + name + "_v2")(value)
        assert raw == canonical(value)
        assert getattr(read, "decode_" + name + "_v2")(raw) == value
        with pytest.raises(read.WireError):
            getattr(read, "decode_" + name)(raw)
    result = result_for(ctx)
    assert read.decode_result_v2(read.encode_result_v2(result)) == result
    assert read.match_result_v2(ctx["request"], result) == result
    assert read.fit_response_v2(ctx["request"], result) == canonical(result)
    assert (
        read.request_intent_digest_v2(ctx["request"]) == ctx["request"]["intent_digest"]
    )
    assert read.result_digest_v2(result) == result["result_digest"]
    assert read.admit_result_budget_v2(ctx["request"]) == ctx["wire"].MAX_RESULT_BYTES


@pytest.mark.parametrize(
    "fault",
    (
        "profile",
        "v5",
        "schema",
        "slice",
        "root",
        "projection",
        "missing",
        "extra",
        "inner_profile",
        "inner_digest",
    ),
)
def test_redigested_model_substitutions_refuse(ctx, fault):
    model = ctx["model"]
    if fault == "profile":
        model["topology_profile_ref"] = "unknown"
    elif fault == "v5":
        model["topology"]["contract_ref"] = "aware.ontology.runtime-schema-topology.v5"
    elif fault == "root":
        model["root_type_ref"] = "demo.Target"
    elif fault == "projection":
        model["projection_ref"] = "demo:Target"
    elif fault == "missing":
        model.pop("topology_profile_ref")
    elif fault == "extra":
        model["authority"] = "issued"
    else:
        field = (
            "schema_bundle"
            if fault == "schema"
            else "schema_slice"
            if fault == "slice"
            else "topology"
        )
        inner = unpack(model[field])
        if fault == "inner_profile":
            inner["profile"] = "unknown"
        elif fault == "inner_digest":
            inner["topology_digest"] = "sha256:" + "0" * 64
        else:
            inner["namespace"] = "foreign"
        model[field] = body(model[field]["contract_ref"], inner)
    seal(model, "model_digest")
    with pytest.raises(ctx["read"].WireError):
        ctx["read"].decode_model_binding_v2(canonical(model))


@pytest.mark.parametrize(
    "fault",
    (
        "observable",
        "topology_digest",
        "model_digest",
        "profile_mix",
        "scope",
        "reading",
        "provider",
    ),
)
def test_redigested_observation_joins_refuse(ctx, fault):
    obs = ctx["observation"]
    if fault == "topology_digest":
        obs["target"]["topology_digest"] = "sha256:" + "0" * 64
        seal(obs["target"], "target_digest")
    elif fault == "model_digest":
        obs["scope"]["model_digest"] = "sha256:" + "0" * 64
    elif fault == "profile_mix":
        obs["model_binding"]["contract_ref"] = ctx["wire"].MODEL_CONTRACT
    elif fault == "scope":
        obs["scope"]["object_ref"] = "foreign:address"
    elif fault == "reading":
        obs["target"]["reading_ref"] = "foreign:reading"
        seal(obs["target"], "target_digest")
    elif fault == "provider":
        reading = unpack(obs["provider_reading"])
        reading["provider_generation"] = "foreign:generation"
        obs["provider_reading"] = body(
            ctx["wire"].READING_CONTRACT, seal(reading, "reading_digest")
        )
    else:
        # Restamp every scope coherently: the remaining defect is actual V6 membership.
        scope = {
            **obs["scope"],
            "observable_ref": "observable:00000000-0000-0000-0000-000000000002",
        }
        obs["scope"] = scope
        provider = unpack(obs["provider_binding"])
        provider["scope"] = scope
        obs["provider_binding"] = body(
            ctx["wire"].BINDING_CONTRACT, seal(provider, "binding_digest")
        )
        reading = unpack(obs["provider_reading"])
        reading.update(scope=scope, provider_binding_digest=provider["binding_digest"])
        obs["provider_reading"] = body(
            ctx["wire"].READING_CONTRACT, seal(reading, "reading_digest")
        )
        obs["target"]["scope"] = scope
        obs["target"]["target_ref"] = ctx["read"].target_ref(
            {
                k: scope[k]
                for k in (
                    "ontology_ref",
                    "namespace_ref",
                    "context_ref",
                    "branch_ref",
                    "object_ref",
                    "observable_ref",
                    "projection_ref",
                )
            }
        )
        seal(obs["target"], "target_digest")
    seal(obs, "observation_digest")
    with pytest.raises(ctx["read"].WireError):
        ctx["read"].decode_observation_v2(canonical(obs))


@pytest.mark.parametrize(
    "fault", ("profile", "intent", "witness", "preimage", "generation", "delivery")
)
def test_v2_result_substitution_refuses(ctx, fault):
    w, read = ctx["wire"], ctx["read"]
    result = result_for(ctx)
    if fault == "profile":
        result["profile_ref"] = w.PROFILE
    elif fault == "intent":
        result["intent_digest"] = "sha256:" + "0" * 64
    elif fault == "witness":
        result["witnesses"][0]["body"]["contract_ref"] = w.OUTCOME_OBSERVATION_CONTRACT
    elif fault == "generation":
        result["responder_incarnation"] = "foreign:generation"
    elif fault == "delivery":
        result["delivery_ref"] = "foreign:delivery"
    else:
        witness = unpack(result["witnesses"][0]["body"])
        base = {
            k: v for k, v in result.items() if k not in ("witnesses", "result_digest")
        }
        witness["outcome_hash"] = (
            "sha256:"
            + hashlib.sha256(
                canonical({"contract": w.PREIMAGE_CONTRACT, "result": base})
            ).hexdigest()
        )
        result["witnesses"][0]["body"] = body(
            w.OUTCOME_OBSERVATION_V2_CONTRACT, seal(witness, "observation_digest")
        )
    result["result_digest"] = digest(
        w.RESULT_V2_DIGEST_DOMAIN,
        {k: v for k, v in result.items() if k != "result_digest"},
    )
    with pytest.raises(read.WireError):
        read.match_result_v2(ctx["request"], result)


@pytest.mark.parametrize(
    "tag,code", (("refused", "source_stale"), ("unavailable", "owner_unavailable"))
)
def test_v2_negative_results_keep_full_witness_without_observation(ctx, tag, code):
    result = result_for(
        ctx,
        {
            "tag": tag,
            "code": code,
            "stage": "owner_verification",
            "command_contact": "not_started",
            "operation_contact": "not_started",
            "recovery_ref": None,
        },
    )
    assert ctx["read"].match_result_v2(ctx["request"], result) == result


def test_v2_expected_revision_and_below_minimum_budget_fail_closed(ctx):
    read, w = ctx["read"], ctx["wire"]
    ctx["request"]["payload"]["selection"]["expected_revision_ref"] = "foreign:revision"
    ctx["request"]["intent_digest"] = read.request_intent_digest_v2(ctx["request"])
    with pytest.raises(read.WireError, match="source_stale"):
        read.match_result_v2(ctx["request"], result_for(ctx))
    ctx["request"]["result_budget_bytes"] = w.MIN_RESULT_BUDGET_BYTES - 1
    ctx["request"]["intent_digest"] = read.request_intent_digest_v2(ctx["request"])

    class NeverRead:
        def __getattribute__(self, name):
            raise AssertionError("candidate inspected below budget")

    raw = read.fit_response_v2(ctx["request"], NeverRead())
    assert read.decode_rejection_v2(raw)["code"] == "limit_exceeded"
    with pytest.raises(read.WireError):
        read.decode_rejection(raw)


def test_all_legacy_golden_vectors_remain_byte_exact_and_v2_refuses_them(ctx):
    read, w = ctx["read"], ctx["wire"]
    ports = {
        w.MODEL_CONTRACT: "model_binding",
        w.OBSERVATION_CONTRACT: "observation",
        w.REQUEST_CONTRACT: "request",
        w.RESULT_CONTRACT: "result",
        w.REJECTION_CONTRACT: "rejection",
    }
    for vector in ctx["legacy"].values():
        value = vector["value"]
        port = ports.get(value["contract"])
        if port is None:
            continue
        raw = getattr(read, "encode_" + port)(value)
        assert len(raw) == vector["canonical_bytes"]
        assert "sha256:" + hashlib.sha256(raw).hexdigest() == vector["sha256"]
        assert getattr(read, "decode_" + port)(raw) == value
        with pytest.raises(read.WireError):
            getattr(read, "decode_" + port + "_v2")(raw)


@pytest.mark.parametrize(
    "fault", ("unknown_node_type", "wrong_schema_field", "wrong_schema_target")
)
def test_valid_v6_resealed_against_incompatible_schema_refuses(ctx, fault):
    model, v6 = ctx["model"], ctx["topology"]
    topology = v6.decode_portal_topology_v6(
        bytes.fromhex(model["topology"]["body_hex"])
    )
    if fault == "unknown_node_type":
        topology["projections"][1]["nodes"][0][1] = "demo.Foreign"
        topology["relationships"][0][3] = "demo.Foreign"
        topology["portals"][0][8] = "demo.Foreign"
    else:
        replacement = (
            "demo.Source.missing" if fault == "wrong_schema_field" else "demo.Source"
        )
        if fault == "wrong_schema_field":
            topology["relationships"][0][2] = replacement
            topology["portals"][0][4] = replacement
        else:
            topology["projections"][1]["nodes"][0][1] = replacement
            topology["relationships"][0][3] = replacement
            topology["portals"][0][8] = replacement
    model["topology"] = body(v6.CONTRACT, v6.encode_portal_topology_v6(topology))
    seal(model, "model_digest")
    with pytest.raises(ctx["read"].WireError):
        ctx["read"].decode_model_binding_v2(canonical(model))


def test_v2_outcome_wrapper_and_domain_isolation(ctx):
    read, w = ctx["read"], ctx["wire"]
    result = result_for(ctx)
    observed = unpack(result["witnesses"][0]["body"])
    assert (
        read.decode_outcome_observation_v2(read.encode_outcome_observation_v2(observed))
        == observed
    )
    assert read.outcome_hash_v2(result) == observed["outcome_hash"]
    assert read.outcome_preimage_v2(result)["contract"] == w.PREIMAGE_V2_CONTRACT
    for contract in (
        w.PREIMAGE_CONTRACT,
        w.PREIMAGE_V2_CONTRACT,
        w.OUTCOME_OBSERVATION_CONTRACT,
    ):
        observed["owner_observation_body"] = body(contract, {})
        seal(observed, "observation_digest")
        with pytest.raises(read.WireError):
            read.encode_outcome_observation_v2(observed)


@pytest.mark.parametrize("version", (1, 2))
@pytest.mark.parametrize("lower_version", (1, 2))
@pytest.mark.parametrize("lower_kind", ("witness", "preimage"))
def test_both_carriages_reject_restamped_self_evidence(
    ctx, version, lower_version, lower_kind
):
    read = ctx["read"]
    legacy = ctx["legacy"]["positive_A"]["value"]
    successor = result_for(ctx)
    lower_result = legacy if lower_version == 1 else successor
    if lower_kind == "witness":
        lower = unpack(lower_result["witnesses"][0]["body"])
    else:
        preimage = (
            read.outcome_preimage if lower_version == 1 else read.outcome_preimage_v2
        )
        lower = preimage(lower_result)
    result = copy.deepcopy(legacy if version == 1 else successor)
    observed = unpack(result["witnesses"][0]["body"])
    observed["owner_observation_body"] = body(lower["contract"], lower)
    seal(observed, "observation_digest")
    result["witnesses"][0]["body"] = body(observed["contract"], observed)
    result_digest = read.result_digest if version == 1 else read.result_digest_v2
    result["result_digest"] = result_digest(result)
    decode = read.decode_result if version == 1 else read.decode_result_v2
    with pytest.raises(read.WireError):
        decode(canonical(result))
    encode = read.encode_result if version == 1 else read.encode_result_v2
    with pytest.raises(read.WireError):
        encode(result)
    witness_decode = (
        read.decode_outcome_observation
        if version == 1
        else read.decode_outcome_observation_v2
    )
    with pytest.raises(read.WireError):
        witness_decode(canonical(observed))


def test_valid_legacy_positive_result_remains_byte_exact(ctx):
    read = ctx["read"]
    vector = ctx["legacy"]["positive_A"]
    raw = canonical(vector["value"])
    assert len(raw) == vector["canonical_bytes"]
    assert "sha256:" + hashlib.sha256(raw).hexdigest() == vector["sha256"]
    assert read.encode_result(read.decode_result(raw)) == raw


@pytest.mark.parametrize(
    "fault", ("none", "foreign_result_profile", "budget", "request_profile", "timeout")
)
def test_existing_transport_has_explicit_v2_door_and_no_retry(ctx, fault):
    from aware_ontology_object_facade_client.client import (
        exchange_read,
        exchange_read_v2,
    )

    calls = []
    read, w = ctx["read"], ctx["wire"]
    response = result_for(ctx)
    if fault == "foreign_result_profile":
        response = ctx["legacy"]["positive_A"]["value"]
    if fault == "budget":
        ctx["request"]["result_budget_bytes"] = w.MIN_RESULT_BUDGET_BYTES - 1
    if fault == "request_profile":
        ctx["request"]["profile_ref"] = w.PROFILE
    ctx["request"]["intent_digest"] = read.request_intent_digest_v2(ctx["request"])
    request = canonical(ctx["request"])

    class Transport:
        async def exchange(self, raw):
            calls.append(raw)
            if fault == "timeout":
                raise TimeoutError("original attempt")
            return canonical(response)

    if fault == "none":
        assert asyncio.run(exchange_read_v2(Transport(), request)) == response
    else:
        with pytest.raises(TimeoutError if fault == "timeout" else read.WireError):
            asyncio.run(exchange_read_v2(Transport(), request))
    assert len(calls) == (0 if fault in ("budget", "request_profile") else 1)
    calls.clear()
    with pytest.raises(read.WireError):
        asyncio.run(exchange_read(Transport(), request))
    assert calls == []


def test_model_refusal_after_owner_decode_does_not_call_changed_error_constructor(
    ctx, monkeypatch
):
    model, read, v6 = ctx["model"], ctx["read"], ctx["topology"]
    model["projection_ref"] = "fixture:missing-projection"
    seal(model, "model_digest")
    calls, injected = [], []
    original_profile = sys.getprofile()
    watched = v6.decode_portal_topology_v6.__code__

    def foreign(*args, **kwargs):
        calls.append(True)
        raise AssertionError("foreign error constructor")

    def observe(frame, event, arg):
        if event == "return" and frame.f_code is watched and not injected:
            injected.append(True)
            monkeypatch.setattr(read.WireError, "__init__", foreign)

    try:
        sys.setprofile(observe)
        with pytest.raises(read.WireError):
            read.decode_model_binding_v2(canonical(model))
    finally:
        sys.setprofile(original_profile)
    assert injected == [True]
    assert calls == []


def test_v2_model_cannot_select_two_root_nodes_by_one_type_label(ctx):
    model, v6 = ctx["model"], ctx["topology"]
    topology = v6.decode_portal_topology_v6(
        bytes.fromhex(model["topology"]["body_hex"])
    )
    projection = topology["projections"][0]
    node = copy.deepcopy(projection["nodes"][0])
    node[0] = "opg-node:00000000-0000-0000-0000-000000000009"
    projection["nodes"].append(node)
    projection["root_node_refs"].append(node[0])
    model["topology"] = body(v6.CONTRACT, v6.encode_portal_topology_v6(topology))
    seal(model, "model_digest")
    with pytest.raises(ctx["read"].WireError):
        ctx["read"].decode_model_binding_v2(canonical(model))


def test_v2_full_result_budget_never_truncates_owner_witness(ctx):
    read, w = ctx["read"], ctx["wire"]
    ctx["request"]["result_budget_bytes"] = w.MIN_RESULT_BUDGET_BYTES
    ctx["request"]["intent_digest"] = read.request_intent_digest_v2(ctx["request"])
    result = result_for(ctx)
    observed = unpack(result["witnesses"][0]["body"])
    observed["owner_observation_body"] = body(
        "fixture.unissued-owner.v1", {"complete": "x" * 40_000}
    )
    seal(observed, "observation_digest")
    result["witnesses"][0]["body"] = body(w.OUTCOME_OBSERVATION_V2_CONTRACT, observed)
    result["result_digest"] = digest(
        w.RESULT_V2_DIGEST_DOMAIN,
        {k: v for k, v in result.items() if k != "result_digest"},
    )
    before = canonical(result)
    assert len(before) > w.MIN_RESULT_BUDGET_BYTES
    assert read.decode_result_v2(before) == result
    with pytest.raises(read.WireError, match="limit_exceeded"):
        read.match_result_v2(ctx["request"], result)
    assert (
        read.decode_rejection_v2(read.fit_response_v2(ctx["request"], result))["code"]
        == "limit_exceeded"
    )
    assert canonical(result) == before


def test_v2_suspended_exchange_cancellation_settles_original_attempt(ctx):
    from aware_ontology_object_facade_client.client import exchange_read_v2

    async def proof():
        started = asyncio.Event()
        calls, settled = [], []

        class Transport:
            async def exchange(self, raw):
                calls.append(raw)
                started.set()
                try:
                    await asyncio.Event().wait()
                finally:
                    settled.append(True)

        request = canonical(ctx["request"])
        task = asyncio.create_task(exchange_read_v2(Transport(), request))
        await asyncio.wait_for(started.wait(), 30)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert calls == [request] and settled == [True]

    asyncio.run(proof())
