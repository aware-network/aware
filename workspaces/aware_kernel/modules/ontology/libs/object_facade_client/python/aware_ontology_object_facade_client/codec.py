"""Strict detached framing. A valid frame never authenticates an issuer or peer."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, NamedTuple, cast

from . import wire as w


class _Policy(NamedTuple):
    """Owning, immutable budgets; no public callback or policy parameter."""

    message: int
    body: int
    entries: int
    depth: int
    aggregate_body: int | None


_V1_POLICY = _Policy(65_536, 16_384, 4_096, 32, None)
_READ_REQUEST_POLICY = _Policy(65_536, 262_144, 32_768, 32, 1_048_576)
_READ_RESULT_POLICY = _Policy(2_097_152, 262_144, 32_768, 32, 1_048_576)

# Filled once by the owning definition-time installer, before public dispatch.
_preparation_check: Any = None
_preparation_failure: Any = None


class _OperationProfile(NamedTuple):
    request: str
    result: str
    intent: str
    preimage: str
    observation: str
    association: str
    facts: str
    bundle: str


_V1_OPERATION = _OperationProfile(w.REQUEST_CONTRACT, w.RESULT_CONTRACT,
    w.INTENT_CONTRACT, w.PREIMAGE_CONTRACT, w.OBSERVATION_CONTRACT,
    w.ASSOCIATION_CONTRACT, "aware.ontology.facade-facts.v1", "aware.ontology.facade-bundle.v1")
_V4_OPERATION = _OperationProfile(w.OPERATION_REQUEST_CONTRACT, w.OPERATION_RESULT_CONTRACT,
    w.OPERATION_INTENT_CONTRACT, w.OPERATION_PREIMAGE_CONTRACT, w.OPERATION_OBSERVATION_CONTRACT,
    w.OPERATION_ASSOCIATION_CONTRACT, w.FACTS_CONTRACT, w.BUNDLE_CONTRACT)


def _operation_profile(value: object, *, result: bool = False) -> _OperationProfile:
    _text(value)
    for profile in (_V1_OPERATION, _V4_OPERATION):
        if value == (profile.result if result else profile.request):
            return profile
    _fail("unsupported_contract")
    raise AssertionError("unreachable")


class WireError(ValueError):
    """A data refusal, not a correlated host Result or execution observation."""

    def __init__(self, code: str = "malformed") -> None:
        self.code = code
        super().__init__(code)


def _fail(code: str = "malformed") -> None:
    raise WireError(code)


def _dump(value: object) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise WireError() from None


def _preflight(raw: bytes, policy: _Policy = _V1_POLICY) -> None:
    """Bound nesting and allocation before the stdlib parser builds a tree."""
    stack: list[list[Any]] = []
    quoted = escaped = False
    entries = 0
    for byte in raw:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
            continue
        if byte in (9, 10, 13, 32):
            continue
        if stack and stack[-1][0] == 91 and stack[-1][1] and byte != 93:
            entries += 1
            stack[-1][1] = False
        if byte == 34:
            quoted = True
        elif byte in (91, 123):
            stack.append([byte, True])
            if len(stack) > policy.depth:
                _fail("limit_exceeded")
        elif byte in (93, 125):
            if not stack or stack[-1][0] != (91 if byte == 93 else 123):
                _fail()
            stack.pop()
        elif byte == 58:
            entries += 1
        elif byte == 44 and stack:
            stack[-1][1] = True
        if entries > policy.entries:
            _fail("limit_exceeded")


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        if key in result:
            _fail()
        result[key] = value
    return result


def _constant(_: str) -> None:
    _fail()


def _parse(raw: bytes, policy: _Policy = _V1_POLICY) -> Any:
    _preflight(raw, policy)
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                          parse_constant=_constant)
    except (ValueError, UnicodeError, RecursionError):
        raise WireError() from None


def _text(value: object, policy: _Policy = _V1_POLICY) -> str:
    check, binding_failure = _preparation_check, _preparation_failure
    check_code = check.__code__
    casting: Any = cast
    casting_code = casting.__code__
    native_type, string_kind, length, encode = type, str, len, str.encode
    policy_kind, indexing = _Policy, tuple.__getitem__
    unicode_error, error_kind = UnicodeError, WireError
    allocate, initialize = BaseException.__new__, BaseException.__init__
    dictionary = BaseException.__dict__["__dict__"].__get__
    putting = dict.__setitem__
    # Refusals use native base slots, never the mutable error constructor or
    # its descriptors. Retain all primitives before any Python helper return.
    malformed = allocate(error_kind)
    initialize(malformed, "malformed")
    putting(dictionary(malformed), "code", "malformed")
    exceeded = allocate(error_kind)
    initialize(exceeded, "limit_exceeded")
    putting(dictionary(exceeded), "code", "limit_exceeded")
    if native_type(value) is not string_kind:
        raise malformed
    if native_type(policy) is not policy_kind:
        raise binding_failure
    # The owning tuple slot avoids a replaceable field descriptor. Budgets
    # remain the exact values of the three existing private policies.
    message = indexing(policy, 0)
    if native_type(message) is not int:
        raise binding_failure
    if casting.__code__ is not casting_code:
        raise binding_failure
    text = casting(string_kind, value)
    # The wrapper's check cannot cover its own return to this caller. Re-admit
    # the complete owner closure here before continuing with the result.
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    if native_type(text) is not string_kind or text is not value:
        raise binding_failure
    if length(text) > message:
        raise exceeded
    try:
        if length(encode(text, "utf-8")) > message:
            raise exceeded
    except unicode_error:
        raise malformed from None
    return text


def _tree(value: object, budget: list[int], depth: int = 0,
          ancestors: frozenset[int] = frozenset(), *, opaque: bool = False,
          policy: _Policy = _V1_POLICY) -> None:
    """Count outer and recursively JSON-framed Body structure cumulatively.

    Owner-body scalar meaning/canonicalization is not reinterpreted here.
    Body-shaped nested records are expanded only for the resource ceiling.
    """
    check, binding_failure = _preparation_check, _preparation_failure
    check_code = check.__code__
    casting: Any = cast
    casting_code = casting.__code__
    failing, reading_text, visiting, reading_body, parsing = (
        _fail, _text, _tree, _body, _parse,
    )
    fail_code, text_code, visit_code, body_code, parse_code = (
        failing.__code__, reading_text.__code__, visiting.__code__,
        reading_body.__code__, parsing.__code__,
    )
    wire_error = WireError
    exception_fields = BaseException.__dict__["__dict__"].__get__
    field_items = dict.items
    native_type, dictionary_kind, list_kind = type, dict, list
    string_kind, integer_kind, boolean_kind = str, int, bool
    none_kind, float_kind = type(None), float
    length, identity, integer_bits, native_set = len, id, int.bit_length, set
    indexing = tuple.__getitem__
    if native_type(policy) is not _Policy:
        raise binding_failure
    message, entries, depth_limit, aggregate = (
        indexing(policy, 0), indexing(policy, 2), indexing(policy, 3),
        indexing(policy, 4),
    )
    cls = native_type(value)
    if cls is dictionary_kind or cls is list_kind:
        if depth >= depth_limit or identity(value) in ancestors:
            if failing.__code__ is not fail_code:
                raise binding_failure
            failing("limit_exceeded")
        if casting.__code__ is not casting_code:
            raise binding_failure
        values: Any = casting(Any, value)
        # A protected helper cannot authenticate its return to this caller.
        # Re-admit the full owner before continuing with native data or policy.
        if check.__code__ is not check_code:
            raise binding_failure
        check()
        if values is not value:
            raise binding_failure
        budget[0] += length(values)
        if budget[0] > entries:
            if failing.__code__ is not fail_code:
                raise binding_failure
            failing("limit_exceeded")
        nested = ancestors | {identity(value)}
        if cls is dictionary_kind:
            obj: Any = values
            for key, item in obj.items():
                if reading_text.__code__ is not text_code:
                    raise binding_failure
                reading_text(key, policy)
                if check.__code__ is not check_code:
                    raise binding_failure
                check()
                if visiting.__code__ is not visit_code:
                    raise binding_failure
                visiting(item, budget, depth + 1, nested, opaque=opaque, policy=policy)
                if check.__code__ is not check_code:
                    raise binding_failure
                check()
            if native_set(obj) == {"contract_ref", "body_hex", "body_hash"}:
                if reading_body.__code__ is not body_code:
                    raise binding_failure
                raw = reading_body(obj, policy=policy)
                if check.__code__ is not check_code:
                    raise binding_failure
                check()
                if aggregate is not None:
                    budget[1] += length(raw)
                    if budget[1] > aggregate:
                        if failing.__code__ is not fail_code:
                            raise binding_failure
                        failing("limit_exceeded")
                # Framing budget only: lower semantic codecs are owner-local.
                try:
                    if parsing.__code__ is not parse_code:
                        raise binding_failure
                    decoded = parsing(raw, policy)
                except wire_error as error:
                    if check.__code__ is not check_code:
                        raise binding_failure from None
                    check()
                    # Inspect native storage without exception attribute dispatch.
                    if native_type(error) is not wire_error:
                        raise binding_failure from None
                    fields = exception_fields(error)
                    if native_type(fields) is not dictionary_kind:
                        raise binding_failure from None
                    code: Any = None
                    for field, field_data in field_items(fields):
                        if native_type(field) is not string_kind:
                            raise binding_failure from None
                        if field == "code":
                            code = field_data
                    if native_type(code) is not string_kind:
                        raise binding_failure from None
                    if code == "limit_exceeded":
                        raise
                    # Opaque non-JSON owner bytes require their owning codec.
                else:
                    if check.__code__ is not check_code:
                        raise binding_failure
                    check()
                    if visiting.__code__ is not visit_code:
                        raise binding_failure
                    visiting(decoded, budget, depth + 1, opaque=True, policy=policy)
                    if check.__code__ is not check_code:
                        raise binding_failure
                    check()
        else:
            for item in values:
                if visiting.__code__ is not visit_code:
                    raise binding_failure
                visiting(item, budget, depth + 1, nested, opaque=opaque, policy=policy)
                if check.__code__ is not check_code:
                    raise binding_failure
                check()
    elif cls is string_kind:
        if reading_text.__code__ is not text_code:
            raise binding_failure
        reading_text(value, policy)
        if check.__code__ is not check_code:
            raise binding_failure
        check()
    elif cls is integer_kind:
        integer: Any = value
        if integer_bits(integer) > message:
            if failing.__code__ is not fail_code:
                raise binding_failure
            failing("limit_exceeded")
    elif cls is boolean_kind or cls is none_kind:
        pass
    elif opaque and cls is float_kind:
        # An opaque owner's JSON scalar is not an outer facade scalar.
        pass
    else:
        if failing.__code__ is not fail_code:
            raise binding_failure
        failing()


def _canonical(value: object, policy: _Policy) -> bytes:
    _tree(value, [0, 0], policy=policy)
    raw = _dump(value)
    if len(raw) > policy.message:
        _fail("limit_exceeded")
    return raw


def _decode(raw: bytes, policy: _Policy) -> w.JsonValue:
    if type(raw) is not bytes:
        _fail()
    if len(raw) > policy.message:
        _fail("limit_exceeded")
    value = _parse(raw, policy)
    _tree(value, [0, 0], policy=policy)
    if _dump(value) != raw:
        _fail()
    return value


def canonical_bytes(value: object) -> bytes:
    """Encode bounded native JSON data; performs no schema or peer admission."""
    return _canonical(value, _V1_POLICY)


def decode_canonical(raw: bytes) -> w.JsonValue:
    """Decode bounded canonical data, with no authority derived from bytes."""
    return _decode(raw, _V1_POLICY)


def plain_digest(raw: bytes) -> str:
    if type(raw) is not bytes:
        _fail()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def domain_digest(domain: str, value: object) -> str:
    _ref(domain)
    return plain_digest(domain.encode("utf-8") + b"\x00" + canonical_bytes(value))


def _obj(value: object, keys: set[str] | None = None) -> dict[str, Any]:
    check, binding_failure = _preparation_check, _preparation_failure
    check_code = check.__code__
    reading_text, text_code = _text, _text.__code__
    native_set = set
    if type(value) is not dict:
        _fail()
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    obj: Any = value
    for key in obj:
        if reading_text.__code__ is not text_code:
            raise binding_failure
        reading_text(key)
    if keys is not None and native_set(obj) != keys:
        _fail()
    return obj


def _ref(value: object) -> str:
    text = _text(value)
    if not text or "\x00" in text or any(c.isspace() for c in text):
        _fail()
    if len(text.encode("utf-8")) > w.MAX_REF_BYTES:
        _fail("limit_exceeded")
    return text


def _digest(value: object) -> None:
    if type(value) is not str or re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None:
        _fail()


def _uint(value: object, low: int = 0, high: int = w.MAX_COUNTER) -> None:
    check, binding_failure = _preparation_check, _preparation_failure
    check_code = check.__code__
    native_type, integer_kind = type, int
    failing, fail_code = _fail, _fail.__code__
    if native_type(value) is not integer_kind:
        if failing.__code__ is not fail_code:
            raise binding_failure
        failing()
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    integer: Any = value
    if not low <= integer <= high:
        if failing.__code__ is not fail_code:
            raise binding_failure
        failing("limit_exceeded")


def _enum(value: object, choices: object) -> None:
    check, binding_failure = _preparation_check, _preparation_failure
    check_code = check.__code__
    native_type, string_kind = type, str
    failing, fail_code = _fail, _fail.__code__
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    admitted_choices: Any = choices
    if native_type(value) is not string_kind or value not in admitted_choices:
        if failing.__code__ is not fail_code:
            raise binding_failure
        failing()


def _body(value: object, expected: str | None = None, *,
          policy: _Policy = _V1_POLICY) -> bytes:
    obj = _obj(value, {"contract_ref", "body_hex", "body_hash"})
    _ref(obj["contract_ref"])
    if expected is not None and obj["contract_ref"] != expected:
        _fail("unsupported_contract")
    text = obj["body_hex"]
    if type(text) is not str:
        _fail()
    if len(text) > 2 * policy.body:
        _fail("limit_exceeded")
    if not text or len(text) % 2 or re.fullmatch(r"[0-9a-f]+", text) is None:
        _fail()
    _digest(obj["body_hash"])
    raw = bytes.fromhex(text)
    if obj["body_hash"] != plain_digest(raw):
        _fail()
    return raw


def make_body(contract_ref: str, raw: bytes) -> w.Body:
    """Wrap complete owner bytes unchanged. This does not implement its codec."""
    if type(raw) is not bytes:
        _fail()
    if len(raw) > w.MAX_BODY_BYTES:
        _fail("limit_exceeded")
    body: w.Body = {"contract_ref": contract_ref, "body_hex": raw.hex(),
                    "body_hash": plain_digest(raw)}
    _body(body)
    _tree(body, [0])
    return body


_ORIGIN = {k: "ref" for k in (
    "owner_ref", "owner_generation", "journal_namespace_ref", "invocation_ref",
    "attempt_ref", "principal_ref",
)}
_ORIGIN["entry_kind"] = "entry"
_OPERATION = {k: "ref" for k in (
    "ontology_ref", "branch_ref", "actor_ref", "projection_ref", "operation_ref",
    "idempotency_key", "provider_ref", "provider_generation",
)}
_OPERATION.update(object_abi_digest="digest", expected_revision_ref="ref?",
                  base_operational_digest="digest")
_OWNER_REQUEST = dict(purpose="initial", requesting_host_incarnation="ref",
    bundle="body:aware.ontology.facade-bundle.v1", owner_preparation_record_ref="ref",
    owner_preparation_record_digest="digest", owner_head_revision="uint",
    owner_head_digest="digest", contact_claim_body="body?", challenge="nonce",
    challenge_budget_ms="challenge")
_COMMAND_REQUEST = dict(purpose="scope", requesting_host_incarnation="ref",
    bundle_digest="digest", command_ordinal="command_ordinal",
    command_intent="body:" + w.INTENT_CONTRACT, owner_head_revision="uint",
    owner_head_digest="digest", challenge="nonce", challenge_budget_ms="challenge")
_OWNER_VALUE = dict(challenge="nonce", requesting_host_incarnation="ref",
    bundle_digest="digest", owner_profile_ref="ref", owner_generation="ref",
    preparation_record="body", owner_head="body", preparation_reread="body",
    head_reread="body", contact_claim="body?", initial_contact_state="claim_state")
_COMMAND_VALUE = dict(challenge="nonce", requesting_host_incarnation="ref",
    bundle_digest="digest", command_ordinal="command_ordinal",
    command_intent_digest="digest", owner_profile_ref="ref", owner_generation="ref",
    owner_head="body", head_reread="body", initial_contact_claim="body?",
    command_phase="phase")
_SELECTION = dict(selection="operation", origin_body="body:aware.ontology.facade-origin.v1")
_ACTION_VALUE = dict(action_digest="digest", return_value="return", snapshots="updates")
_PAYLOADS = {
    "facts.read": _SELECTION, "view.read": _SELECTION,
    "owner.verify": _OWNER_REQUEST, "owner.command_verify": _COMMAND_REQUEST,
    "operation.activate": dict(bundle="body:aware.ontology.facade-bundle.v1",
        owner_preparation_record_ref="ref", owner_preparation_record_digest="digest",
        contact_claim_body="body?"),
    "object.acquire": dict(session_ref="ref", type_ref="ref", instance_ref="ref",
                           binding_digest="digest"),
    "object.invoke": dict(session_ref="ref", object_ref="ref", action_ref="ref",
        binding_digest="digest", arguments="body:aware.ontology.facade-arguments.v1"),
    "object.construct": dict(session_ref="ref", type_ref="ref", action_ref="ref",
        binding_digest="digest", new_instance_ref="ref",
        arguments="body:aware.ontology.facade-arguments.v1"),
    "operation.complete": dict(session_ref="ref", last_command_ordinal="ordinal",
                               command_prefix_digest="digest"),
    "operation.abort": dict(session_ref="ref", reason="abort",
        last_command_ordinal="ordinal", command_prefix_digest="digest"),
    "operation.inspect": dict(bundle_digest="digest", lower_recovery_ref="ref",
        original_preparation_record_ref="ref", original_preparation_record_digest="digest"),
    "command.inspect": dict(command_ordinal="ordinal", command_intent_digest="digest"),
}
_VALUES = {
    "facts.read": dict(facts="body:aware.ontology.facade-facts.v1"),
    "view.read": dict(view="body"), "owner.verify": _OWNER_VALUE,
    "owner.command_verify": _COMMAND_VALUE,
    "operation.activate": dict(session_ref="ref", host_incarnation="ref",
                               bundle_digest="digest", remaining_ms="remaining"),
    "object.acquire": dict(object_ref="ref", snapshot="body"),
    "object.invoke": _ACTION_VALUE, "object.construct": _ACTION_VALUE,
    "operation.complete": dict(receipt="body", result_view="body",
        result_revision_ref="ref", result_operational_digest="digest"),
    "operation.abort": dict(abort_evidence="body"),
    "operation.inspect": dict(recovery_evidence="body", terminal_completion="body?"),
    "command.inspect": dict(command_phase="phase", stored_result="body?"),
}
_ENUMS = {
    "entry": ("view", "raw", "client"), "initial": ("initial_activation",),
    "scope": ("scope_command",), "claim_state": ("authorized", "unclaimed"),
    "phase": w.COMMAND_PHASES, "abort": w.ABORT_REASONS,
}


def _field(value: object, spec: str, profile: _OperationProfile = _V1_OPERATION) -> None:
    check, binding_failure = _preparation_check, _preparation_failure
    check_code = check.__code__
    reading_wrapper, wrapper_code = _wrapper, _wrapper.__code__
    reading_schema, schema_code = _schema, _schema.__code__
    length, ordering, native_set = len, sorted, set
    object_limit = w.MAX_OBJECTS
    if spec.endswith("?"):
        if value is None:
            return
        spec = spec[:-1]
    if spec.startswith("body"):
        expected = spec.split(":", 1)[1] if ":" in spec else None
        raw = _body(value, expected)
        if expected in _WRAPPERS:
            obj = _obj(decode_canonical(raw))
            if check.__code__ is not check_code:
                raise binding_failure
            check()
            if reading_wrapper.__code__ is not wrapper_code:
                raise binding_failure
            expected_ref: Any = expected
            reading_wrapper(obj, expected_ref, profile)
        elif expected == profile.intent:
            obj = _obj(decode_canonical(raw))
            _intent(obj, profile)
    elif spec == "ref":
        _ref(value)
    elif spec == "digest":
        _digest(value)
    elif spec in ("uint", "ordinal", "command_ordinal", "challenge", "remaining"):
        lo = 1 if spec in ("command_ordinal", "challenge") else 0
        hi = {"uint": w.MAX_COUNTER, "ordinal": 63, "command_ordinal": 63,
              "challenge": w.MAX_CHALLENGE_MS, "remaining": w.MAX_DELIVERY_MS}[spec]
        _uint(value, lo, hi)
    elif spec == "nonce":
        if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
            _fail()
    elif spec == "origin":
        _schema(value, _ORIGIN, profile)
    elif spec == "operation":
        _schema(value, _OPERATION, profile)
    elif spec == "return":
        obj = _obj(value)
        tag = obj.get("tag")
        _enum(tag, ("void", "runtime_value", "object_target"))
        _obj(obj, {"tag"} if tag == "void" else {"tag", "value"})
        if tag != "void":
            # Existing owner-tagged data is preserved, not semantically decoded.
            _obj(obj["value"])
    elif spec == "updates":
        if type(value) is not list:
            _fail()
        if check.__code__ is not check_code:
            raise binding_failure
        check()
        items: Any = value
        if length(items) > object_limit:
            _fail("limit_exceeded")
        refs: list[str] = []
        for item in items:
            if reading_schema.__code__ is not schema_code:
                raise binding_failure
            obj = reading_schema(item, {"object_ref": "ref", "snapshot": "body"})
            refs.append(obj["object_ref"])
        if refs != ordering(native_set(refs), key=lambda x: x.encode("utf-8")):
            _fail()
    elif spec in _ENUMS:
        _enum(value, _ENUMS[spec])
    elif spec == "data_list":
        if type(value) is not list:
            _fail()
    else:
        _fail()


def _schema(value: object, schema: dict[str, str], profile: _OperationProfile = _V1_OPERATION) -> dict[str, Any]:
    obj = _obj(value, set(schema))
    for key, spec in schema.items():
        _field(obj[key], spec, profile)
    return obj


_WRAPPERS = {
    "aware.ontology.facade-origin.v1": dict(origin="origin", api_request="body",
        service_binding="body", service_admission="body", function_plan="body",
        experience_admission="body?"),
    "aware.ontology.facade-facts.v1": dict(facts_ref="ref", host_incarnation="ref",
        origin="origin", operation="operation", topology_body="body", schema_body="body",
        schema_slice_body="body", object_abi_body="body", application_authority_body="body",
        selection_facts_body="body", selection_profile_body="body",
        precontact_profile_body="body", lifetime_ms="remaining"),
    "aware.ontology.facade-bundle.v1": dict(
        origin_body="body:aware.ontology.facade-origin.v1",
        facts_body="body:aware.ontology.facade-facts.v1", activation_preimage="body",
        execution_preimage="body", selection_admission_body="body", attempt_body="body",
        attempt_admission_body="body", precontact_profile_body="body"),
    "aware.ontology.facade-arguments.v1": dict(action_ref="ref", binding_digest="digest",
                                             arguments="data_list"),
}


_WRAPPERS[w.PREPARATION_BASE_CONTRACT] = dict(
    branch_ref="ref", retained_revision_ref="ref", provider_ref="ref", provider_generation="ref",
    topology_digest="digest", schema_digest="digest", schema_slice_digest="digest",
    object_abi_digest="digest", application_authority_digest="digest",
    selection_profile_digest="digest", base_operational_digest="digest")
_WRAPPERS[w.FACTS_CONTRACT] = dict(_WRAPPERS["aware.ontology.facade-facts.v1"],
    preparation_base_body="body:" + w.PREPARATION_BASE_CONTRACT)
_WRAPPERS[w.BUNDLE_CONTRACT] = dict(_WRAPPERS["aware.ontology.facade-bundle.v1"],
    facts_body="body:" + w.FACTS_CONTRACT)


def _wrapper(obj: dict[str, Any], contract: str, profile: _OperationProfile = _V1_OPERATION) -> None:
    schema = dict(_WRAPPERS[contract], contract="ref")
    digest_key = {"aware.ontology.facade-origin.v1": "origin_digest",
                  "aware.ontology.facade-facts.v1": "facts_digest",
                  "aware.ontology.facade-bundle.v1": "bundle_digest",
                  w.PREPARATION_BASE_CONTRACT: "base_digest", w.FACTS_CONTRACT: "facts_digest",
                  w.BUNDLE_CONTRACT: "bundle_digest"}.get(contract)
    if digest_key:
        schema[digest_key] = "digest"
    _schema(obj, schema, profile)
    if obj["contract"] != contract:
        _fail("unsupported_contract")
    if digest_key and obj[digest_key] != domain_digest(contract,
            {k: v for k, v in obj.items() if k != digest_key}):
        _fail()
    if contract == "aware.ontology.facade-origin.v1":
        if (obj["origin"]["entry_kind"] == "view") != (obj["experience_admission"] is not None):
            _fail()


def _correlation(obj: dict[str, Any]) -> str:
    kind = obj["kind"]
    _enum(kind, w.COMMANDS)
    _field(obj["origin"], "origin")
    if kind in ("facts.read", "view.read"):
        if obj["operation"] is not None or obj["ordinal"] is not None:
            _fail()
    else:
        _field(obj["operation"], "operation")
        if kind in w.ACTIVE_COMMANDS:
            _uint(obj["ordinal"], 0 if kind == "operation.activate" else 1,
                  0 if kind == "operation.activate" else 63)
        elif obj["ordinal"] is not None:
            _fail()
    return kind


def request_intent_digest(request: object) -> str:
    obj = _obj(request)
    profile = _operation_profile(obj.get("contract"))
    return domain_digest(profile.intent,
        {k: v for k, v in obj.items() if k not in ("intent_digest", "delivery")})


def _intent(obj: dict[str, Any], profile: _OperationProfile = _V1_OPERATION) -> None:
    _obj(obj, {"contract", "kind", "origin", "operation", "ordinal", "payload",
               "result_budget_bytes"})
    if obj["contract"] != profile.request:
        _fail("unsupported_contract")
    kind = _correlation(obj)
    schema = dict(_PAYLOADS[kind])
    if kind in ("owner.verify", "operation.activate"):
        schema["bundle"] = "body:" + profile.bundle
    elif kind == "owner.command_verify":
        schema["command_intent"] = "body:" + profile.intent
    payload = _schema(obj["payload"], schema, profile)
    _uint(obj["result_budget_bytes"], 1,
          w.MAX_BODY_BYTES if kind in w.ACTIVE_COMMANDS else w.MAX_MESSAGE_BYTES)
    if kind in ("operation.complete", "operation.abort"):
        if payload["last_command_ordinal"] != obj["ordinal"] - 1:
            _fail()
    if kind in ("object.invoke", "object.construct"):
        arguments = _obj(decode_canonical(_body(payload["arguments"])))
        for field in ("action_ref", "binding_digest"):
            if arguments[field] != payload[field]:
                _fail()
    if kind in ("facts.read", "view.read"):
        origin = _obj(decode_canonical(_body(payload["origin_body"])))
        if origin["origin"] != obj["origin"]:
            _fail()
    if kind in ("operation.activate", "owner.verify"):
        bundle = _obj(decode_canonical(_body(payload["bundle"])))
        origin = _obj(decode_canonical(_body(bundle["origin_body"])))
        facts = _obj(decode_canonical(_body(bundle["facts_body"])))
        if origin["origin"] != obj["origin"] or facts["origin"] != obj["origin"]:
            _fail()
        if facts["operation"] != obj["operation"]:
            _fail()


def _request(obj: dict[str, Any]) -> None:
    _obj(obj, {"contract", "kind", "origin", "operation", "ordinal", "payload",
               "result_budget_bytes", "intent_digest", "delivery"})
    profile = _operation_profile(obj["contract"])
    _intent({k: v for k, v in obj.items() if k not in ("intent_digest", "delivery")}, profile)
    _schema(obj["delivery"], dict(delivery_ref="ref", recipient_incarnation="ref",
                                 timeout_ms="uint"))
    _uint(obj["delivery"]["timeout_ms"], 1, w.MAX_DELIVERY_MS)
    _digest(obj["intent_digest"])
    if obj["intent_digest"] != request_intent_digest(obj):
        _fail()


def outcome_preimage(result: object) -> w.Record:
    obj = _obj(result)
    _tree(obj, [0])
    keys = {"contract", "kind", "origin", "operation", "ordinal", "intent_digest",
            "delivery_ref", "responder_incarnation", "outcome"}
    if not keys <= set(obj):
        _fail()
    profile = _operation_profile(obj["contract"], result=True)
    preimage: Any = {"contract": profile.preimage,
                     "result": {key: obj[key] for key in keys}}
    return preimage


def outcome_hash(result: object) -> str:
    return plain_digest(canonical_bytes(outcome_preimage(result)))


def result_digest(result: object) -> str:
    obj = _obj(result)
    profile = _operation_profile(obj.get("contract"), result=True)
    return domain_digest(profile.result,
                         {k: v for k, v in obj.items() if k != "result_digest"})


def required_witness_roles(kind: str, outcome: str) -> frozenset[str]:
    """Unconditional structure only; profile-dependent claim is owner-verified."""
    _enum(kind, w.COMMANDS)
    _enum(outcome, ("ok", "refused", "unavailable", "pending", "indeterminate",
                    "replay.active", "replay.historical"))
    roles = {"command_outcome"}
    if outcome == "ok":
        roles.update({
            "facts.read": ("facts_issuance",), "view.read": ("view_observation",),
            "owner.verify": ("owner_preparation", "owner_head", "owner_reread"),
            "owner.command_verify": ("owner_head", "owner_reread"),
            "operation.activate": ("provider_fence",),
            "operation.complete": ("operation_completion",),
            "operation.abort": ("operation_completion",),
            "operation.inspect": ("historical_recovery",),
            "command.inspect": ("owner_head", "owner_reread"),
        }.get(kind, ()))
    elif outcome in ("pending", "indeterminate", "replay.active", "replay.historical"):
        if kind not in w.ACTIVE_COMMANDS:
            _fail()
        if outcome in ("pending", "replay.active", "replay.historical"):
            roles.update(("owner_head", "owner_reread"))
        if outcome == "replay.active":
            if kind in ("operation.complete", "operation.abort"):
                _fail()
            roles.add("provider_fence")
        elif outcome == "replay.historical":
            roles.add("historical_recovery")
    return frozenset(roles)


def _observation(body: object, result: dict[str, Any], profile: _OperationProfile = _V1_OPERATION) -> dict[str, Any]:
    raw = _body(body, profile.observation)
    obj = _schema(decode_canonical(raw), dict(contract="ref", role="ref", origin="origin",
        operation="operation?", ordinal="ordinal?", intent_digest="digest",
        outcome_hash="digest", responder_incarnation="ref", session_ref="ref?",
        source_observation="body?", observation_digest="digest"))
    if obj["contract"] != profile.observation or obj["role"] != "command_outcome":
        _fail()
    for field in ("origin", "operation", "ordinal", "intent_digest", "responder_incarnation"):
        if obj[field] != result[field]:
            _fail()
    if obj["outcome_hash"] != outcome_hash(result):
        _fail()
    if obj["observation_digest"] != domain_digest(profile.observation,
            {k: v for k, v in obj.items() if k != "observation_digest"}):
        _fail()
    if result["kind"] in ("owner.verify", "owner.command_verify") and obj["session_ref"] is not None:
        _fail()
    outcome = result["outcome"]
    if outcome["tag"] == "ok" and result["kind"] == "operation.activate":
        if obj["session_ref"] != outcome["value"]["session_ref"]:
            _fail()
        if outcome["value"]["host_incarnation"] != result["responder_incarnation"]:
            _fail()
    if outcome["tag"] == "pending" or (outcome["tag"] in ("refused", "unavailable", "indeterminate")
            and "observed" in (outcome["command_contact"], outcome["operation_contact"])):
        if obj["source_observation"] is None:
            _fail()
    if outcome["tag"] == "replay":
        if obj["source_observation"] is None:
            _fail()
        if obj["session_ref"] != outcome["association"]["original_session_ref"]:
            _fail()
    return obj


def _replay(outcome: dict[str, Any], outer: dict[str, Any], profile: _OperationProfile = _V1_OPERATION) -> None:
    _obj(outcome, {"tag", "mode", "stored_result", "original_command_intent_digest", "association"})
    _enum(outcome["mode"], ("active", "historical"))
    _digest(outcome["original_command_intent_digest"])
    assoc = _schema(outcome["association"], dict(contract="ref", original_result_digest="digest",
        original_delivery_ref="ref", original_responder_incarnation="ref",
        original_session_ref="ref?", observing_host_incarnation="ref", current_session_ref="ref?"))
    if assoc["contract"] != profile.association:
        _fail("unsupported_contract")
    original = _obj(decode_canonical(_body(outcome["stored_result"], profile.result)))
    # Reject before recursively interpreting another replay envelope.
    if _obj(original.get("outcome")).get("tag") == "replay":
        _fail()
    _result(original, profile)
    for field in ("kind", "origin", "operation", "ordinal", "intent_digest"):
        if original[field] != outer[field]:
            _fail()
    if outcome["original_command_intent_digest"] != outer["intent_digest"]:
        _fail()
    for association_field, original_field in (
        ("original_result_digest", "result_digest"), ("original_delivery_ref", "delivery_ref"),
        ("original_responder_incarnation", "responder_incarnation"),
    ):
        if assoc[association_field] != original[original_field]:
            _fail()
    if assoc["observing_host_incarnation"] != outer["responder_incarnation"]:
        _fail()
    original_observation = next(x for x in original["witnesses"] if x["role"] == "command_outcome")
    retained_session = _obj(decode_canonical(_body(original_observation["body"])))["session_ref"]
    if assoc["original_session_ref"] != retained_session:
        _fail()
    if outcome["mode"] == "active":
        if assoc["original_session_ref"] is None or assoc["current_session_ref"] != retained_session:
            _fail()
        if original["responder_incarnation"] != outer["responder_incarnation"]:
            _fail()
    elif assoc["current_session_ref"] is not None:
        _fail()


def _result(obj: dict[str, Any], expected_profile: _OperationProfile | None = None) -> None:
    check, binding_failure = _preparation_check, _preparation_failure
    check_code = check.__code__
    reading_roles, roles_code = required_witness_roles, required_witness_roles.__code__
    native_set = set
    _obj(obj, {"contract", "kind", "origin", "operation", "ordinal", "intent_digest",
               "delivery_ref", "responder_incarnation", "outcome", "witnesses", "result_digest"})
    profile = _operation_profile(obj["contract"], result=True)
    if expected_profile is not None and profile is not expected_profile:
        _fail("unsupported_contract")
    kind = _correlation(obj)
    _digest(obj["intent_digest"])
    _ref(obj["delivery_ref"])
    _ref(obj["responder_incarnation"])
    outcome = _obj(obj["outcome"])
    tag = outcome.get("tag")
    _enum(tag, ("ok", "refused", "unavailable", "pending", "indeterminate", "replay"))
    value: dict[str, Any] = {}
    if tag == "ok":
        _obj(outcome, {"tag", "value", "finality"})
        finality = ("observation" if kind in w.COMMANDS[:4] else "historical" if kind in
            ("operation.inspect", "command.inspect") else "scope_complete" if kind in
            ("operation.complete", "operation.abort") else "provisional")
        if outcome["finality"] != finality:
            _fail()
        schema = dict(_VALUES[kind])
        if kind == "facts.read":
            schema["facts"] = "body:" + profile.facts
        value = _schema(outcome["value"], schema, profile)
        if kind == "command.inspect" and value["stored_result"] is not None:
            original = _obj(decode_canonical(_body(value["stored_result"], profile.result)))
            if _obj(original.get("outcome")).get("tag") == "replay":
                _fail()
            _result(original, profile)
    elif tag == "replay":
        _replay(outcome, obj, profile)
    else:
        _obj(outcome, {"tag", "code", "stage", "command_contact", "operation_contact", "recovery_ref"})
        _enum(outcome["code"], w.REFUSAL_CODES)
        _enum(outcome["stage"], w.FAILURE_STAGES)
        _enum(outcome["command_contact"], w.CONTACT_STATES)
        _enum(outcome["operation_contact"], w.CONTACT_STATES)
        _field(outcome["recovery_ref"], "ref?")
        if tag == "indeterminate" and outcome["command_contact"] == "not_started":
            _fail()
    label = "replay." + outcome["mode"] if tag == "replay" else tag
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    if reading_roles.__code__ is not roles_code:
        raise binding_failure
    admitted_label: Any = label
    required = native_set(reading_roles(kind, admitted_label))
    if (tag not in ("ok", "replay") and outcome["recovery_ref"] is not None) or (
            kind == "command.inspect" and tag == "ok" and value["stored_result"] is not None):
        required.add("historical_recovery")
    optional: set[str] = set()
    if (tag == "ok" and kind in ("owner.verify", "owner.command_verify")) or label in ("pending", "replay.active"):
        optional.add("owner_contact_claim")
    claim_field = "contact_claim" if kind == "owner.verify" else "initial_contact_claim"
    if tag == "ok" and kind in ("owner.verify", "owner.command_verify") and value[claim_field] is not None:
        required.add("owner_contact_claim")
    if type(obj["witnesses"]) is not list:
        _fail()
    witnesses = obj["witnesses"]
    if len(witnesses) > w.MAX_WITNESSES:
        _fail("limit_exceeded")
    identities: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    observations = 0
    reread_fields: set[str] = set()
    direct_reread = False
    for witness in witnesses:
        x = _schema(witness, dict(role="ref", issuer_ref="ref", issuer_generation="ref",
                                 body="body?", value_field="ref?"))
        role = x["role"]
        if role not in required | optional or (x["body"] is None) == (x["value_field"] is None):
            _fail()
        seen.add(role)
        body = x["body"]
        if x["value_field"] is not None:
            field = x["value_field"]
            if tag != "ok" or field not in w.WITNESS_FIELDS[role] or field not in value:
                _fail()
            body = value[field]
            _body(body)
            if role == "owner_reread":
                reread_fields.add(field)
        elif role == "owner_reread":
            direct_reread = True  # Its fixed owner codec must prove head/preparation membership.
        if role == "command_outcome":
            _observation(body, obj, profile)
            observations += 1
        identities.append((role, x["issuer_ref"], _obj(body)["body_hash"]))
    if not required <= seen or observations != 1:
        _fail()
    if identities != sorted(set(identities), key=lambda x: tuple(y.encode("utf-8") for y in x)):
        _fail()
    if tag == "ok" and kind == "owner.verify" and not direct_reread:
        if reread_fields != {"preparation_reread", "head_reread"}:
            _fail()
    elif "owner_reread" in required and not direct_reread and reread_fields != {"head_reread"}:
        _fail()
    _digest(obj["result_digest"])
    if obj["result_digest"] != result_digest(obj):
        _fail()


def encode_request(value: object) -> bytes:
    raw = canonical_bytes(value)
    _request(_obj(value))
    return raw


def decode_request(raw: bytes) -> w.Request:
    obj = _obj(decode_canonical(raw))
    _request(obj)
    record: Any = obj
    return record


def encode_result(value: object) -> bytes:
    raw = canonical_bytes(value)
    _result(_obj(value))
    return raw


def decode_result(raw: bytes) -> w.Result:
    obj = _obj(decode_canonical(raw))
    _result(obj)
    record: Any = obj
    return record


def match_result(request: object, result: object) -> None:
    """Check data correlation/reserve only; not authenticated peer association."""
    req = decode_request(encode_request(request))
    res = decode_result(encode_result(result))
    if res["contract"] != _operation_profile(req["contract"]).result:
        _fail("unsupported_contract")
    for field in ("kind", "origin", "operation", "ordinal", "intent_digest"):
        if req[field] != res[field]:
            _fail()
    if res["delivery_ref"] != req["delivery"]["delivery_ref"]:
        _fail()
    if res["responder_incarnation"] != req["delivery"]["recipient_incarnation"]:
        _fail()
    payload = req["payload"]
    outcome = res["outcome"]
    observation = next(x for x in res["witnesses"] if x["role"] == "command_outcome")
    observed = _obj(decode_canonical(_body(observation["body"])))
    if outcome["tag"] == "ok" and "session_ref" in payload and observed["session_ref"] != payload["session_ref"]:
        _fail()
    if outcome["tag"] == "ok":
        value = _obj(outcome["value"])
        kind = req["kind"]
        if kind in ("owner.verify", "owner.command_verify"):
            for field in ("challenge", "requesting_host_incarnation"):
                if value[field] != payload[field]:
                    _fail()
        if kind in ("owner.verify", "operation.activate"):
            bundle = _obj(decode_canonical(_body(payload["bundle"])))
            if value["bundle_digest"] != bundle["bundle_digest"]:
                _fail()
        if kind == "owner.command_verify":
            for field in ("bundle_digest", "command_ordinal"):
                if value[field] != payload[field]:
                    _fail()
            intent = _obj(decode_canonical(_body(payload["command_intent"])))
            if value["command_intent_digest"] != domain_digest(_operation_profile(req["contract"]).intent, intent):
                _fail()
        if kind == "facts.read":
            facts = _obj(decode_canonical(_body(value["facts"])))
            if facts["origin"] != req["origin"] or facts["operation"] != payload["selection"]:
                _fail()
    if len(encode_result(res)) > req["result_budget_bytes"]:
        _fail("limit_exceeded")


def encode_rejection(value: object) -> bytes:
    obj = _obj(value, {"contract", "code"})
    _text(obj["contract"])
    _text(obj["code"])
    if obj["contract"] != w.REJECTION_CONTRACT:
        _fail("unsupported_contract")
    _enum(obj["code"], ("malformed", "unsupported_contract", "limit_exceeded"))
    return canonical_bytes(obj)


def decode_rejection(raw: bytes) -> w.Record:
    obj = _obj(decode_canonical(raw))
    encode_rejection(obj)
    return obj


def command_prefix_digest(entries: object) -> str:
    check, binding_failure = _preparation_check, _preparation_failure
    check_code = check.__code__
    reading_schema, schema_code = _schema, _schema.__code__
    length = len
    if type(entries) is not list:
        _fail()
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    items: Any = entries
    if length(items) > 63:
        _fail("limit_exceeded")
    for ordinal, item in enumerate(items):
        if reading_schema.__code__ is not schema_code:
            raise binding_failure
        obj = reading_schema(item, {
            "ordinal": "ordinal", "intent_digest": "digest", "result_digest": "digest",
        })
        if obj["ordinal"] != ordinal:
            _fail()
    return domain_digest(w.PREFIX_CONTRACT, items)

# Native data helpers for the separately owned positive path. The old codec
# entry points and their check/cast frequency are unchanged.
from importlib import import_module as _positive_import_module
from types import ModuleType as _positive_module_kind

# The package context already governs the original relative wire import.
assert __package__ is not None
_positive_module_type: Any = _positive_module_kind

try:
    _positive_native_kernel = _positive_import_module(__package__ + "._preparation_scan")
except ModuleNotFoundError as _positive_native_error:
    _positive_native_error_name = ImportError.__dict__["name"].__get__(_positive_native_error)
    # Native ImportError.name accepts arbitrary objects. Reject their kind
    # before equality; immutable literal type/str access invokes no foreign code.
    if (0 .__class__.__getattribute__(0, "__class__").__class__(_positive_native_error_name) is not "".__class__
            or _positive_native_error_name != __package__ + "._preparation_scan"):
        raise
    _positive_native_kernel = None

# Absence of this optional data export preserves the original native profile.
# Loader errors and actual native-call refusals remain failures, without retry.
_positive_canonical_entry = (
    dict.get(_positive_module_type.__dict__["__dict__"].__get__(_positive_native_kernel),
             "_positive_canonical_data_probe")
    if _positive_native_kernel is not None else None
)


def _positive_canonical_data(value: object, policy: _Policy) -> bytes:
    """Pure data only: fresh traversal, original Body/parser/dump and budgets."""
    native_entry: Any = "__positive_canonical_kernel_entry_v1__"
    unavailable_type: Any = "__positive_canonical_unavailable_type_v3__"
    if native_entry is None:
        raise unavailable_type("positive_native_data_unavailable")
    check, failure = _preparation_check, _preparation_failure
    code_get = (lambda: None).__class__.__dict__["__code__"].__get__
    native_type, tuple_kind, int_kind, bytes_kind = type, tuple, int, bytes
    length, indexing = tuple.__len__, tuple.__getitem__
    check_code = code_get(check)
    original_body, original_parse, original_dump = _body, _parse, _dump
    body_code, parse_code, dump_code = (
        code_get(original_body), code_get(original_parse), code_get(original_dump)
    )
    error_kind = WireError
    allocate, initialize = BaseException.__new__, BaseException.__init__
    dictionary = BaseException.__dict__["__dict__"].__get__
    putting = dict.__setitem__
    if code_get(check) is not check_code:
        raise failure
    check()
    if (code_get(check) is not check_code
            or code_get(original_body) is not body_code
            or code_get(original_parse) is not parse_code
            or code_get(original_dump) is not dump_code):
        raise failure
    result = native_entry(value, policy, original_body, original_parse,
                          check, error_kind, original_dump)
    if code_get(check) is not check_code:
        raise failure
    check()
    if (code_get(check) is not check_code
            or code_get(original_body) is not body_code
            or code_get(original_parse) is not parse_code
            or code_get(original_dump) is not dump_code):
        raise failure
    if native_type(result) is not tuple_kind or length(result) != 4:
        raise failure
    status, raw = indexing(result, 0), indexing(result, 1)
    if native_type(status) is not int_kind:
        raise failure
    if status == 1 or status == 2:
        refusal_code = "malformed" if status == 1 else "limit_exceeded"
        refusal = allocate(error_kind)
        initialize(refusal, refusal_code)
        putting(dictionary(refusal), "code", refusal_code)
        if code_get(check) is not check_code:
            raise failure
        check()
        raise refusal
    if status != 0 or native_type(raw) is not bytes_kind:
        raise failure
    return raw


def _positive_decode_data(raw: bytes, policy: _Policy) -> w.JsonValue:
    """Original parser followed by fresh native traversal and byte comparison."""
    native_entry: Any = "__positive_decode_kernel_entry_v1__"
    unavailable_type: Any = "__positive_decode_unavailable_type_v3__"
    if native_entry is None:
        raise unavailable_type("positive_native_data_unavailable")
    check, failure = _preparation_check, _preparation_failure
    code_get = (lambda: None).__class__.__dict__["__code__"].__get__
    check_code = code_get(check)
    parsing, canonicalizing = _parse, _positive_canonical_data
    failing = _fail
    parse_code, canonical_code = code_get(parsing), code_get(canonicalizing)
    fail_code = code_get(failing)
    if type(raw) is not bytes:
        if code_get(failing) is not fail_code:
            raise failure
        failing()
    if type(policy) is not _Policy:
        raise failure
    if len(raw) > tuple.__getitem__(policy, 0):
        if code_get(failing) is not fail_code:
            raise failure
        failing("limit_exceeded")
    if code_get(check) is not check_code:
        raise failure
    check()
    if code_get(parsing) is not parse_code:
        raise failure
    value = parsing(raw, policy)
    if code_get(check) is not check_code:
        raise failure
    check()
    if code_get(canonicalizing) is not canonical_code:
        raise failure
    canonical = canonicalizing(value, policy)
    if code_get(check) is not check_code:
        raise failure
    check()
    if canonical != raw:
        if code_get(failing) is not fail_code:
            raise failure
        failing()
    return value


# Retain the actual immutable native exception TYPE at definition. Each
# unavailable call creates a fresh exception, releasing its request traceback.
_positive_native_unavailable_type = ValueError

# Retain the actual optional native port inside immutable Code constants before
# the owning preparation installer admits any helper. None is a refusal only.
_positive_canonical_data.__code__ = _positive_canonical_data.__code__.replace(co_consts=tuple(
    _positive_canonical_entry if type(value) is str and value == "__positive_canonical_kernel_entry_v1__"
    else _positive_native_unavailable_type
    if type(value) is str and value == "__positive_canonical_unavailable_type_v3__"
    else value for value in _positive_canonical_data.__code__.co_consts))
_positive_decode_data.__code__ = _positive_decode_data.__code__.replace(co_consts=tuple(
    _positive_canonical_entry if type(value) is str and value == "__positive_decode_kernel_entry_v1__"
    else _positive_native_unavailable_type
    if type(value) is str and value == "__positive_decode_unavailable_type_v3__"
    else value for value in _positive_decode_data.__code__.co_consts))

# Bootstrap-only importlib function is not a runtime helper dependency. Drop
# this NEW alias before first Prep inventory; preserve every original row.
del _positive_import_module
