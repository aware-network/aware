"""Generic Object observation framing using the single facade canonical engine.

Local grammar, wrapper joins and data budgets do not validate original model,
provider or issuer authority. Lower schema, branch and View semantics remain
owner-local. Budget helpers select detached bytes; the host must release its
operation-local records before delivering a refusal.
"""

from collections.abc import Callable
from typing import Any, NamedTuple, NoReturn, cast

from aware_meta_type_schema import (
    TypeSchemaSlice,
    decode_schema_bundle,
    decode_schema_slice,
    encode_schema_bundle,
    encode_schema_slice,
)

from . import codec as c
from . import owner_values as owner
from . import source_read_wire as w
from . import topology_v6

WireError = c.WireError


def _make_refusal() -> Callable[[str], NoReturn]:
    # Keep the original owner exception class, but never dispatch a constructor
    # or descriptor replaced while a nested owner decoder is returning.
    kind = WireError
    allocate, initialize = BaseException.__new__, BaseException.__init__
    dictionary = BaseException.__dict__["__dict__"].__get__
    put = dict.__setitem__

    def refuse(code: str) -> NoReturn:
        failure = allocate(kind)
        initialize(failure, code)
        put(dictionary(failure), "code", code)
        raise failure

    return refuse


_refuse = _make_refusal()


class _Carriage(NamedTuple):
    profile: str
    model: str
    observation: str
    intent: str
    result_digest: str
    preimage: str
    outcome_observation: str
    rejection: str


_V1 = _Carriage(w.PROFILE, w.MODEL_CONTRACT, w.OBSERVATION_CONTRACT,
    w.INTENT_CONTRACT, w.RESULT_DIGEST_DOMAIN, w.PREIMAGE_CONTRACT,
    w.OUTCOME_OBSERVATION_CONTRACT, w.REJECTION_CONTRACT)
_V2 = _Carriage(w.PROFILE_V2, w.MODEL_V2_CONTRACT, w.OBSERVATION_V2_CONTRACT,
    w.INTENT_V2_CONTRACT, w.RESULT_V2_DIGEST_DOMAIN, w.PREIMAGE_V2_CONTRACT,
    w.OUTCOME_OBSERVATION_V2_CONTRACT, w.REJECTION_V2_CONTRACT)


def canonical_bytes(value: object) -> bytes:
    """Bounded generic wrapper data, not an authority admission."""
    return c._canonical(value, c._READ_RESULT_POLICY)


def decode_canonical(raw: bytes) -> w.JsonValue:
    return c._decode(raw, c._READ_RESULT_POLICY)


def _snapshot(value: object, *, request: bool = False) -> dict[str, Any]:
    policy = c._READ_REQUEST_POLICY if request else c._READ_RESULT_POLICY
    return c._obj(c._decode(c._canonical(value, policy), policy))


def domain_digest(domain: str, value: object) -> str:
    c._ref(domain)
    return c.plain_digest(domain.encode("utf-8") + b"\x00" + canonical_bytes(value))


def make_body(contract_ref: str, raw: bytes) -> w.Body:
    """Frame unchanged owner bytes without certifying their meaning."""
    if type(raw) is not bytes:
        c._fail()
    if len(raw) > w.MAX_BODY_BYTES:
        c._fail("limit_exceeded")
    body: w.Body = {"contract_ref": contract_ref, "body_hex": raw.hex(),
                    "body_hash": c.plain_digest(raw)}
    c._body(body, policy=c._READ_RESULT_POLICY)
    canonical_bytes(body)
    return body


def _body(value: object, expected: str | None = None) -> bytes:
    return c._body(value, expected, policy=c._READ_RESULT_POLICY)


def _local_body(value: object, contract: str) -> dict[str, Any]:
    return c._obj(c._decode(_body(value, contract), c._READ_RESULT_POLICY))


def _field(value: object, spec: str) -> None:
    if spec == "ref":
        c._ref(value)
    elif spec == "ref?":
        if value is not None:
            c._ref(value)
    elif spec == "digest":
        c._digest(value)
    elif spec == "scope":
        _schema(value, _SCOPE)
    elif spec == "origin":
        _schema(value, _ORIGIN)
    elif spec == "body":
        _body(value)
    elif spec == "body?":
        if value is not None:
            _body(value)
    elif spec.startswith("body:"):
        _body(value, spec[5:])
    elif spec == "counter":
        c._uint(value)
    elif spec == "lifetime":
        c._uint(value, 1, w.MAX_LIFETIME_MS)
    elif spec == "entry":
        c._enum(value, ("view", "raw", "client"))
    else:
        raise AssertionError("owning schema specification")


def _schema(value: object, schema: dict[str, str]) -> dict[str, Any]:
    obj = c._obj(value, set(schema))
    for key, spec in schema.items():
        _field(obj[key], spec)
    return obj


def _refs(*names: str) -> dict[str, str]:
    return dict.fromkeys(names, "ref")


_ORIGIN = _refs("owner_ref", "owner_generation", "request_ref", "principal_ref") | {"entry_kind": "entry"}
_SCOPE = _refs("ontology_ref", "namespace_ref", "context_ref", "branch_ref", "object_ref",
               "root_type_ref", "observable_ref", "projection_ref") | {"model_digest": "digest"}
_SELECTION = _SCOPE | {"expected_revision_ref": "ref?"}
_ORIGIN_BODY = _refs("read_admission_ref") | {
    "origin": "origin", "api_request": "body", "service_binding": "body",
    "caller_admission": "body", "experience_admission": "body?"}
_MODEL = _refs("model_ref", "model_revision_ref", "root_type_ref", "projection_ref") | {
    "schema_bundle": "body:aware.meta.semantic-type-schema.v1",
    "schema_slice": "body:aware.meta.semantic-type-schema-slice.v1",
    "topology": "body:aware.ontology.runtime-schema-topology.v5", "model_admission": "body"}
_MODEL_V2 = _MODEL | {"topology": "body:" + topology_v6.CONTRACT, "topology_profile_ref": "ref"}
_BINDING = _refs("owner_ref", "provider_ref", "provider_generation", "owner_profile_ref",
                 "binding_revision_ref") | {"scope": "scope", "namespace_admission": "body"}
_READING = _refs("reading_ref", "provider_ref", "provider_generation", "revision_ref") | {
    "scope": "scope", "provider_binding_digest": "digest", "owner_reading": "body",
    "input_evidence": "body", "typed_state": "body:" + w.ROOT_CONTRACT}
_TARGET = _refs("target_ref", "target_kind", "reading_ref", "authority_grade") | {
    "scope": "scope", "topology_digest": "digest"}
_OBSERVATION = _refs("observation_ref", "host_incarnation") | {
    "scope": "scope", "lifetime_ms": "lifetime", **{
        key: "body:" + contract for key, contract in (
            ("provider_binding", w.BINDING_CONTRACT), ("model_binding", w.MODEL_CONTRACT),
            ("provider_reading", w.READING_CONTRACT), ("branch", "aware.ontology.runtime-branch.v1"),
            ("view", "aware.ontology.runtime-view.v1"))}}
_FOCUS = _refs("observation_ref", "issuer_ref", "issuer_generation", "actor_ref",
               "attention_session_ref", "binding_ref", "section_ref") | {
    "observation_digest": "digest", "binding_revision": "counter",
    "mount_activation_epoch": "counter", "permission_evidence": "body", "remaining_lifetime_ms": "lifetime"}
_OUTCOME_OBSERVATION = _refs("issuer_ref", "issuer_generation", "verification_ref") | {
    "request_intent_digest": "digest", "outcome_hash": "digest", "owner_observation_body": "body"}
_TARGET_KEY = ("ontology_ref", "namespace_ref", "context_ref", "branch_ref", "object_ref",
               "observable_ref", "projection_ref")


def _signed(obj: dict[str, Any], contract: str, schema: dict[str, str], digest_field: str) -> None:
    _schema(obj, schema | {"contract": "ref", digest_field: "digest"})
    if obj["contract"] != contract:
        c._fail("unsupported_contract")
    if obj[digest_field] != domain_digest(contract, {k: v for k, v in obj.items() if k != digest_field}):
        c._fail()


def target_ref(key: object) -> str:
    """Derive the detached selector from its exact seven-field key."""
    obj = _snapshot(key)
    _schema(obj, _refs(*_TARGET_KEY))
    return "object-read-target:" + domain_digest(w.TARGET_KEY_DOMAIN, obj)


def _target(obj: dict[str, Any]) -> None:
    _signed(obj, w.TARGET_CONTRACT, _TARGET, "target_digest")
    if obj["target_kind"] != "branch" or obj["authority_grade"] != "local_operational":
        c._fail("unsupported_authority")
    if obj["target_ref"] != target_ref({k: obj["scope"][k] for k in _TARGET_KEY}):
        c._fail()


def _typed_root(obj: dict[str, Any]) -> None:
    c._obj(obj, {"contract", "object"})
    c._ref(obj["contract"])
    if obj["contract"] != w.ROOT_CONTRACT:
        c._fail("unsupported_contract")
    root = c._obj(obj["object"], {"instance_ref", "type_ref", "fields"})
    c._ref(root["instance_ref"])
    c._ref(root["type_ref"])
    if type(root["fields"]) is not list:
        c._fail()
    fields = []
    for field in root["fields"]:
        item = c._obj(field, {"field_ref", "value"})
        c._ref(item["field_ref"])
        value = c._obj(item["value"], {"value_kind", "value"})
        c._ref(value["value_kind"])
        try:
            # Scalar and record meaning have one existing portable owner.
            runtime = owner.RuntimeValue.of(owner.ValueKind(value["value_kind"]), value["value"])
            fields.append(owner.FieldValue(item["field_ref"], runtime))
        except (TypeError, ValueError):
            c._fail()
    try:
        reconstructed = owner.ObjectInstance(root["instance_ref"], root["type_ref"], tuple(fields)).to_wire()
    except (TypeError, ValueError):
        raise WireError() from None
    if reconstructed != root:
        c._fail()


def _reading(obj: dict[str, Any]) -> None:
    _signed(obj, w.READING_CONTRACT, _READING, "reading_digest")
    root = _local_body(obj["typed_state"], w.ROOT_CONTRACT)
    _typed_root(root)
    if root["object"]["instance_ref"] != obj["scope"]["object_ref"] or root["object"]["type_ref"] != obj["scope"]["root_type_ref"]:
        c._fail()


def _model(obj: dict[str, Any], carriage: _Carriage) -> tuple[dict[str, Any], str] | None:
    _signed(obj, carriage.model, _MODEL if carriage == _V1 else _MODEL_V2, "model_digest")
    if carriage == _V1:
        return None
    if obj["topology_profile_ref"] != topology_v6.PROFILE:
        _refuse("unsupported_profile")
    bundle_raw = _body(obj["schema_bundle"])
    slice_raw = _body(obj["schema_slice"])
    topology_raw = _body(obj["topology"], topology_v6.CONTRACT)
    try:
        bundle = decode_schema_bundle(bundle_raw)
        slice_ = decode_schema_slice(slice_raw)
        topology = topology_v6.decode_portal_topology_v6(topology_raw)
        if (encode_schema_bundle(bundle) != bundle_raw or encode_schema_slice(slice_) != slice_raw
                or encode_schema_slice(TypeSchemaSlice.create(bundle, root_type_refs=slice_.root_type_refs)) != slice_raw):
            _refuse("binding_mismatch")
    except (TypeError, ValueError) as error:
        if isinstance(error, WireError):
            raise
        _refuse("binding_mismatch")
    if (topology["schema_digest"] != bundle.schema_digest
            or topology["schema_slice_digest"] != slice_.slice_digest
            or topology["namespace"] != bundle.namespace
            or topology["semantic_version"] != bundle.semantic_version
            or obj["root_type_ref"] not in slice_.root_type_refs):
        _refuse("binding_mismatch")
    projection = next((row for row in cast(list[dict[str, Any]], topology["projections"])
                       if row["projection_ref"] == obj["projection_ref"]), None)
    if projection is None:
        _refuse("binding_mismatch")
    if sum(node[1] == obj["root_type_ref"] and node[2] is True for node in projection["nodes"]) != 1:
        _refuse("binding_mismatch")
    by_type = {definition.type_ref: definition for definition in bundle.types}
    for row in cast(list[dict[str, Any]], topology["projections"]):
        if any(node[1] not in by_type for node in row["nodes"]):
            _refuse("binding_mismatch")
    for relationship in cast(list[list[Any]], topology["relationships"]):
        source = by_type.get(relationship[1])
        field = next((item for item in source.fields if item.field_ref == relationship[2]), None) if source else None
        if field is None or field.shape.type_ref != relationship[3] or relationship[3] not in by_type:
            _refuse("binding_mismatch")
    digest = topology_v6.content_digest(topology_v6.CONTRACT, canonical_bytes(topology))
    return projection, digest


def _observation(obj: dict[str, Any], carriage: _Carriage = _V1) -> None:
    schema = _OBSERVATION if carriage == _V1 else _OBSERVATION | {"model_binding": "body:" + carriage.model}
    c._obj(obj, set(_OBSERVATION) | {"contract", "observation_digest", "target"})
    target = c._obj(obj["target"])
    _target(target)
    _schema({k: v for k, v in obj.items() if k != "target"}, schema | {"contract": "ref", "observation_digest": "digest"})
    if obj["contract"] != carriage.observation:
        c._fail("unsupported_contract")
    if obj["observation_digest"] != domain_digest(carriage.observation, {k: v for k, v in obj.items() if k != "observation_digest"}):
        c._fail()
    binding = _local_body(obj["provider_binding"], w.BINDING_CONTRACT)
    _signed(binding, w.BINDING_CONTRACT, _BINDING, "binding_digest")
    model = _local_body(obj["model_binding"], carriage.model)
    model_content = _model(model, carriage)
    reading = _local_body(obj["provider_reading"], w.READING_CONTRACT)
    _reading(reading)
    scope = obj["scope"]
    if any(scope != record["scope"] for record in (binding, reading, target)):
        c._fail()
    if any(model[k] != scope[k] for k in ("root_type_ref", "projection_ref", "model_digest")):
        c._fail()
    if reading["provider_binding_digest"] != binding["binding_digest"] or target["reading_ref"] != reading["reading_ref"]:
        c._fail()
    if any(reading[k] != binding[k] for k in ("provider_ref", "provider_generation")):
        c._fail()
    if model_content is not None:
        projection, topology_digest = model_content
        if scope["observable_ref"] not in projection["observables"] or target["topology_digest"] != topology_digest:
            c._fail("binding_mismatch")
    # Lower topology/branch/View meaning and original authority are owner-local.


def _origin_body(obj: dict[str, Any]) -> None:
    _signed(obj, w.ORIGIN_CONTRACT, _ORIGIN_BODY, "origin_digest")
    if (obj["origin"]["entry_kind"] == "view") != (obj["experience_admission"] is not None):
        c._fail()


def _focus(obj: dict[str, Any]) -> None:
    c._obj(obj, set(_FOCUS) | {"contract", "target", "admission_digest"})
    _target(c._obj(obj["target"]))
    _schema({k: v for k, v in obj.items() if k != "target"}, _FOCUS | {"contract": "ref", "admission_digest": "digest"})
    if obj["contract"] != w.FOCUS_CONTRACT:
        c._fail("unsupported_contract")
    if obj["admission_digest"] != domain_digest(w.FOCUS_CONTRACT, {k: v for k, v in obj.items() if k != "admission_digest"}):
        c._fail()


def _wrapper(obj: dict[str, Any], contract: str, carriage: _Carriage = _V1) -> None:
    if contract == carriage.model:
        _model(obj, carriage)
    elif contract == w.BINDING_CONTRACT:
        _signed(obj, contract, _BINDING, "binding_digest")
    elif contract == w.ROOT_CONTRACT:
        _typed_root(obj)
    elif contract == w.READING_CONTRACT:
        _reading(obj)
    elif contract == w.TARGET_CONTRACT:
        _target(obj)
    elif contract == carriage.observation:
        _observation(obj, carriage)
    elif contract == w.ORIGIN_CONTRACT:
        _origin_body(obj)
    elif contract == w.FOCUS_CONTRACT:
        _focus(obj)
    elif contract == carriage.outcome_observation:
        _signed(obj, contract, _OUTCOME_OBSERVATION, "observation_digest")
        forbidden = (
            w.RESULT_CONTRACT,
            w.OUTCOME_OBSERVATION_CONTRACT,
            w.PREIMAGE_CONTRACT,
            w.OUTCOME_OBSERVATION_V2_CONTRACT,
            w.PREIMAGE_V2_CONTRACT,
        )
        if obj["owner_observation_body"]["contract_ref"] in forbidden:
            c._fail()
    else:
        raise AssertionError("owning wrapper contract")


def _encode_wrapper(value: object, contract: str, carriage: _Carriage = _V1) -> bytes:
    obj = _snapshot(value)
    _wrapper(obj, contract, carriage)
    return canonical_bytes(obj)


def _decode_wrapper(raw: bytes, contract: str, carriage: _Carriage = _V1) -> dict[str, Any]:
    obj = c._obj(decode_canonical(raw))
    _wrapper(obj, contract, carriage)
    return obj


def _correlation(obj: dict[str, Any], contract: str, carriage: _Carriage = _V1) -> None:
    c._ref(obj["contract"])
    c._ref(obj["profile_ref"])
    if obj["contract"] != contract:
        c._fail("unsupported_contract")
    if obj["profile_ref"] != carriage.profile:
        c._fail("unsupported_profile")
    c._enum(obj["kind"], ("view.read",))
    _schema(obj["origin"], _ORIGIN)
    if obj["operation"] is not None or obj["ordinal"] is not None:
        c._fail("unsupported_authority")


def _request_intent_digest(request: object, carriage: _Carriage) -> str:
    obj = _snapshot(request, request=True)
    return domain_digest(carriage.intent, {k: v for k, v in obj.items() if k not in ("intent_digest", "delivery")})


def request_intent_digest(request: object) -> str:
    return _request_intent_digest(request, _V1)


def _request(obj: dict[str, Any], carriage: _Carriage = _V1) -> None:
    c._obj(obj, {"contract", "profile_ref", "kind", "origin", "operation", "ordinal", "payload",
                 "result_budget_bytes", "intent_digest", "delivery"})
    _correlation(obj, w.REQUEST_CONTRACT, carriage)
    c._uint(obj["result_budget_bytes"], 1, w.MAX_RESULT_BYTES)
    c._digest(obj["intent_digest"])
    payload = c._obj(obj["payload"], {"selection", "origin_body"})
    _schema(payload["selection"], _SELECTION)
    origin = _local_body(payload["origin_body"], w.ORIGIN_CONTRACT)
    _origin_body(origin)
    if origin["origin"] != obj["origin"]:
        c._fail()
    delivery = c._obj(obj["delivery"], {"delivery_ref", "recipient_incarnation", "timeout_ms"})
    c._ref(delivery["delivery_ref"])
    c._ref(delivery["recipient_incarnation"])
    c._uint(delivery["timeout_ms"], 1, w.MAX_DELIVERY_MS)
    if obj["intent_digest"] != _request_intent_digest(obj, carriage):
        c._fail()


def _encode_request(request: object, carriage: _Carriage) -> bytes:
    obj = _snapshot(request, request=True)
    _request(obj, carriage)
    return c._canonical(obj, c._READ_REQUEST_POLICY)


def _decode_request(raw: bytes, carriage: _Carriage) -> dict[str, Any]:
    obj = c._obj(c._decode(raw, c._READ_REQUEST_POLICY))
    _request(obj, carriage)
    return obj


def encode_request(request: object) -> bytes:
    return _encode_request(request, _V1)


def decode_request(raw: bytes) -> w.Request:
    return cast(w.Request, _decode_request(raw, _V1))


def _outcome(value: object, carriage: _Carriage = _V1) -> None:
    obj = c._obj(value)
    c._enum(obj.get("tag"), ("ok", "refused", "unavailable"))
    if obj["tag"] == "ok":
        c._obj(obj, {"tag", "value", "finality"})
        c._enum(obj["finality"], ("observation",))
        val = c._obj(obj["value"], {"view"})
        _observation(_local_body(val["view"], carriage.observation), carriage)
    else:
        c._obj(obj, {"tag", "code", "stage", "command_contact", "operation_contact", "recovery_ref"})
        c._enum(obj["code"], w.REFUSED_CODES if obj["tag"] == "refused" else w.UNAVAILABLE_CODES)
        c._enum(obj["stage"], w.FAILURE_STAGES)
        c._enum(obj["command_contact"], w.CONTACT_STATES)
        c._enum(obj["operation_contact"], ("not_started",))
        if obj["recovery_ref"] is not None:
            c._fail()
        if obj["stage"] in ("decode", "selection", "owner_verification") and obj["command_contact"] != "not_started":
            c._fail()
        if obj["stage"] in ("contact", "inspection") and obj["command_contact"] == "not_started":
            c._fail()


_RESULT_BASE = {"contract", "profile_ref", "kind", "origin", "operation", "ordinal", "intent_digest",
                "delivery_ref", "responder_incarnation", "outcome"}


def _outcome_preimage(result: object, carriage: _Carriage) -> w.Record:
    obj = _snapshot(result)
    base = {k: v for k, v in obj.items() if k not in ("witnesses", "result_digest")}
    c._obj(base, _RESULT_BASE)
    _correlation(base, w.RESULT_CONTRACT, carriage)
    c._digest(base["intent_digest"])
    c._ref(base["delivery_ref"])
    c._ref(base["responder_incarnation"])
    _outcome(base["outcome"], carriage)
    return cast(w.Record, {"contract": carriage.preimage, "result": base})


def outcome_preimage(result: object) -> w.Record:
    return _outcome_preimage(result, _V1)


def outcome_hash(result: object) -> str:
    return c.plain_digest(canonical_bytes(outcome_preimage(result)))


def _result_digest(result: object, carriage: _Carriage) -> str:
    obj = _snapshot(result)
    return domain_digest(carriage.result_digest, {k: v for k, v in obj.items() if k != "result_digest"})


def result_digest(result: object) -> str:
    return _result_digest(result, _V1)


def required_witness_roles(tag: str) -> tuple[str, ...]:
    c._enum(tag, ("ok", "refused", "unavailable"))
    return ("command_outcome", "view_observation") if tag == "ok" else ("command_outcome",)


def _result(obj: dict[str, Any], carriage: _Carriage = _V1) -> None:
    c._obj(obj, _RESULT_BASE | {"witnesses", "result_digest"})
    preimage_hash = c.plain_digest(canonical_bytes(_outcome_preimage(obj, carriage)))
    witnesses = obj["witnesses"]
    if type(witnesses) is not list:
        c._fail()
    roles = required_witness_roles(obj["outcome"]["tag"])
    if len(witnesses) != len(roles):
        c._fail()
    for witness, role in zip(witnesses, roles):
        _schema(witness, {"role": "ref", "issuer_ref": "ref", "issuer_generation": "ref",
                          "body": "body?", "value_field": "ref?"})
        if witness["role"] != role or witness["issuer_generation"] != obj["responder_incarnation"]:
            c._fail()
    first = witnesses[0]
    if first["value_field"] is not None:
        c._fail()
    observed = _local_body(first["body"], carriage.outcome_observation)
    _wrapper(observed, carriage.outcome_observation, carriage)
    if observed["request_intent_digest"] != obj["intent_digest"] or observed["outcome_hash"] != preimage_hash:
        c._fail()
    if any(observed[k] != first[k] for k in ("issuer_ref", "issuer_generation")):
        c._fail()
    if len(witnesses) == 2:
        second = witnesses[1]
        if second["body"] is not None or second["value_field"] != "view" or second["issuer_ref"] != first["issuer_ref"]:
            c._fail()
        view = _local_body(obj["outcome"]["value"]["view"], carriage.observation)
        if view["host_incarnation"] != obj["responder_incarnation"]:
            c._fail()
    c._digest(obj["result_digest"])
    if obj["result_digest"] != _result_digest(obj, carriage):
        c._fail()


def _encode_result(result: object, carriage: _Carriage) -> bytes:
    obj = _snapshot(result)
    _result(obj, carriage)
    return canonical_bytes(obj)


def _decode_result(raw: bytes, carriage: _Carriage) -> dict[str, Any]:
    obj = c._obj(decode_canonical(raw))
    _result(obj, carriage)
    return obj


def encode_result(result: object) -> bytes:
    return _encode_result(result, _V1)


def decode_result(raw: bytes) -> w.Result:
    return cast(w.Result, _decode_result(raw, _V1))


def _match_result(request: object, result: object, carriage: _Carriage) -> dict[str, Any]:
    req = _decode_request(_encode_request(request, carriage), carriage)
    _admitted_budget(req)
    raw = _encode_result(result, carriage)
    res = _decode_result(raw, carriage)
    if any(res[k] != req[k] for k in ("profile_ref", "kind", "origin", "operation", "ordinal", "intent_digest")):
        c._fail("result_invalid")
    if res["delivery_ref"] != req["delivery"]["delivery_ref"] or res["responder_incarnation"] != req["delivery"]["recipient_incarnation"]:
        c._fail("result_invalid")
    if len(raw) > req["result_budget_bytes"]:
        c._fail("limit_exceeded")
    if res["outcome"]["tag"] == "ok":
        obs = _local_body(res["outcome"]["value"]["view"], carriage.observation)
        selection = req["payload"]["selection"]
        if obs["scope"] != {k: selection[k] for k in _SCOPE}:
            c._fail("result_invalid")
        reading = _local_body(obs["provider_reading"], w.READING_CONTRACT)
        expected = selection["expected_revision_ref"]
        if expected is not None and reading["revision_ref"] != expected:
            c._fail("source_stale")
    return res


def match_result(request: object, result: object) -> w.Result:
    return cast(w.Result, _match_result(request, result, _V1))


def _rejection(obj: dict[str, Any], carriage: _Carriage = _V1) -> None:
    _schema(obj, {"contract": "ref", "profile_ref": "ref", "tag": "ref", "code": "ref"})
    if obj["contract"] != carriage.rejection:
        c._fail("unsupported_contract")
    if obj["profile_ref"] != carriage.profile:
        c._fail("unsupported_profile")
    c._enum(obj["tag"], ("refused", "unavailable"))
    c._enum(obj["code"], w.REFUSED_CODES if obj["tag"] == "refused" else w.UNAVAILABLE_CODES)


def encode_rejection(rejection: object) -> bytes:
    obj = _snapshot(rejection, request=True)
    _rejection(obj)
    return c._canonical(obj, c._READ_REQUEST_POLICY)


def decode_rejection(raw: bytes) -> w.Rejection:
    obj = c._obj(c._decode(raw, c._READ_REQUEST_POLICY))
    _rejection(obj)
    return cast(w.Rejection, obj)


def encode_origin(value: object) -> bytes:
    return _encode_wrapper(value, w.ORIGIN_CONTRACT)


def decode_origin(raw: bytes) -> w.ReadOriginBody:
    return cast(w.ReadOriginBody, _decode_wrapper(raw, w.ORIGIN_CONTRACT))


def encode_model_binding(value: object) -> bytes:
    return _encode_wrapper(value, w.MODEL_CONTRACT)


def decode_model_binding(raw: bytes) -> w.ModelBinding:
    return cast(w.ModelBinding, _decode_wrapper(raw, w.MODEL_CONTRACT))


def encode_provider_binding(value: object) -> bytes:
    return _encode_wrapper(value, w.BINDING_CONTRACT)


def decode_provider_binding(raw: bytes) -> w.ProviderBinding:
    return cast(w.ProviderBinding, _decode_wrapper(raw, w.BINDING_CONTRACT))


def encode_typed_root(value: object) -> bytes:
    return _encode_wrapper(value, w.ROOT_CONTRACT)


def decode_typed_root(raw: bytes) -> w.TypedRoot:
    return cast(w.TypedRoot, _decode_wrapper(raw, w.ROOT_CONTRACT))


def encode_provider_reading(value: object) -> bytes:
    return _encode_wrapper(value, w.READING_CONTRACT)


def decode_provider_reading(raw: bytes) -> w.ProviderReading:
    return cast(w.ProviderReading, _decode_wrapper(raw, w.READING_CONTRACT))


def encode_target(value: object) -> bytes:
    return _encode_wrapper(value, w.TARGET_CONTRACT)


def decode_target(raw: bytes) -> w.Target:
    return cast(w.Target, _decode_wrapper(raw, w.TARGET_CONTRACT))


def encode_observation(value: object) -> bytes:
    return _encode_wrapper(value, w.OBSERVATION_CONTRACT)


def decode_observation(raw: bytes) -> w.Observation:
    return cast(w.Observation, _decode_wrapper(raw, w.OBSERVATION_CONTRACT))


def encode_focus_admission(value: object) -> bytes:
    return _encode_wrapper(value, w.FOCUS_CONTRACT)


def decode_focus_admission(raw: bytes) -> w.FocusAdmission:
    return cast(w.FocusAdmission, _decode_wrapper(raw, w.FOCUS_CONTRACT))


def encode_outcome_observation(value: object) -> bytes:
    return _encode_wrapper(value, w.OUTCOME_OBSERVATION_CONTRACT)


def decode_outcome_observation(raw: bytes) -> w.OutcomeObservation:
    return cast(w.OutcomeObservation, _decode_wrapper(raw, w.OUTCOME_OBSERVATION_CONTRACT))


def _admitted_budget(request: dict[str, Any]) -> int:
    budget = request["result_budget_bytes"]
    if budget < w.MIN_RESULT_BUDGET_BYTES:
        c._fail("limit_exceeded")
    return cast(int, budget)


def admit_result_budget(request: object) -> int:
    """Check full Request first; no owner verification or contact is performed."""
    return _admitted_budget(cast(dict[str, Any], decode_request(encode_request(request))))


def fit_response(request: object, result: object) -> bytes:
    """Select complete response bytes. Host cleanup must precede delivery.

    Below-minimum budgets do not inspect the candidate. Otherwise only a full,
    correlated Result can fit. Resource refusal uses the separate Rejection
    allowance; no witness is truncated and no owner work is retried here.
    """
    req = decode_request(encode_request(request))
    try:
        _admitted_budget(cast(dict[str, Any], req))
        matched = match_result(req, result)
        return encode_result(matched)
    except WireError as error:
        if error.code != "limit_exceeded":
            raise
        return encode_rejection({"contract": w.REJECTION_CONTRACT, "profile_ref": w.PROFILE,
                                 "tag": "refused", "code": "limit_exceeded"})


# Explicit V2 doors over the same owning framing and budget implementation.
# No function auto-selects a successor from supplied bytes or retries V1 as V2.
def request_intent_digest_v2(request: object) -> str:
    return _request_intent_digest(request, _V2)


def encode_request_v2(request: object) -> bytes:
    return _encode_request(request, _V2)


def decode_request_v2(raw: bytes) -> w.RequestV2:
    return cast(w.RequestV2, _decode_request(raw, _V2))


def outcome_preimage_v2(result: object) -> w.Record:
    return _outcome_preimage(result, _V2)


def outcome_hash_v2(result: object) -> str:
    return c.plain_digest(canonical_bytes(outcome_preimage_v2(result)))


def result_digest_v2(result: object) -> str:
    return _result_digest(result, _V2)


def encode_result_v2(result: object) -> bytes:
    return _encode_result(result, _V2)


def decode_result_v2(raw: bytes) -> w.ResultV2:
    return cast(w.ResultV2, _decode_result(raw, _V2))


def match_result_v2(request: object, result: object) -> w.ResultV2:
    return cast(w.ResultV2, _match_result(request, result, _V2))


def encode_model_binding_v2(value: object) -> bytes:
    return _encode_wrapper(value, w.MODEL_V2_CONTRACT, _V2)


def decode_model_binding_v2(raw: bytes) -> w.ModelBindingV2:
    return cast(w.ModelBindingV2, _decode_wrapper(raw, w.MODEL_V2_CONTRACT, _V2))


def encode_observation_v2(value: object) -> bytes:
    return _encode_wrapper(value, w.OBSERVATION_V2_CONTRACT, _V2)


def decode_observation_v2(raw: bytes) -> w.ObservationV2:
    return cast(w.ObservationV2, _decode_wrapper(raw, w.OBSERVATION_V2_CONTRACT, _V2))


def encode_outcome_observation_v2(value: object) -> bytes:
    return _encode_wrapper(value, w.OUTCOME_OBSERVATION_V2_CONTRACT, _V2)


def decode_outcome_observation_v2(raw: bytes) -> w.OutcomeObservationV2:
    return cast(w.OutcomeObservationV2, _decode_wrapper(raw, w.OUTCOME_OBSERVATION_V2_CONTRACT, _V2))


def encode_rejection_v2(rejection: object) -> bytes:
    obj = _snapshot(rejection, request=True)
    _rejection(obj, _V2)
    return c._canonical(obj, c._READ_REQUEST_POLICY)


def decode_rejection_v2(raw: bytes) -> w.RejectionV2:
    obj = c._obj(c._decode(raw, c._READ_REQUEST_POLICY))
    _rejection(obj, _V2)
    return cast(w.RejectionV2, obj)


def admit_result_budget_v2(request: object) -> int:
    return _admitted_budget(_decode_request(encode_request_v2(request), _V2))


def fit_response_v2(request: object, result: object) -> bytes:
    """Complete correlated V2 response or bounded V2 resource rejection."""
    req = decode_request_v2(encode_request_v2(request))
    try:
        _admitted_budget(cast(dict[str, Any], req))
        return encode_result_v2(match_result_v2(req, result))
    except WireError as error:
        if error.code != "limit_exceeded":
            raise
        return encode_rejection_v2({"contract": w.REJECTION_V2_CONTRACT,
            "profile_ref": w.PROFILE_V2, "tag": "refused", "code": "limit_exceeded"})
