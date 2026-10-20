"""Detached exchange specimens; no original peer or Object authority is issued."""

import asyncio
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, cast

import pytest
from aware_ontology_object_facade_client import WireError, client, exchange_read
from aware_ontology_object_facade_client import source_read_wire as w

ARTIFACT = Path(__file__).resolve().parents[8] / "docs/reports/ontology-generic-object-observation-wire-successor-vectors-20261003.json"
VECTORS = {row["name"]: row for row in json.loads(ARTIFACT.read_text())["vectors"]}


def fixture(name: str) -> dict[str, Any]:
    return copy.deepcopy(VECTORS[name]["value"])


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode()


def digest(domain: str, value: object) -> str:
    return "sha256:" + hashlib.sha256(domain.encode() + b"\x00" + canonical(value)).hexdigest()


def body(contract: str, value: object) -> dict[str, str]:
    raw = canonical(value)
    return {"contract_ref": contract, "body_hex": raw.hex(),
            "body_hash": "sha256:" + hashlib.sha256(raw).hexdigest()}


def reseal_request(value: dict[str, Any]) -> None:
    value["intent_digest"] = digest(w.INTENT_CONTRACT, {
        k: v for k, v in value.items() if k not in ("intent_digest", "delivery")})


def reseal_result(value: dict[str, Any]) -> None:
    # Independent contract framing only. These witnesses authenticate no peer.
    base = {k: v for k, v in value.items() if k not in ("witnesses", "result_digest")}
    first = value["witnesses"][0]
    observed = json.loads(bytes.fromhex(first["body"]["body_hex"]))
    observed["request_intent_digest"] = value["intent_digest"]
    observed["outcome_hash"] = "sha256:" + hashlib.sha256(canonical({
        "contract": w.PREIMAGE_CONTRACT, "result": base})).hexdigest()
    observed["issuer_generation"] = value["responder_incarnation"]
    for witness in value["witnesses"]:
        witness["issuer_generation"] = value["responder_incarnation"]
    observed["observation_digest"] = digest(w.OUTCOME_OBSERVATION_CONTRACT, {
        k: v for k, v in observed.items() if k != "observation_digest"})
    first["body"] = body(w.OUTCOME_OBSERVATION_CONTRACT, observed)
    value["result_digest"] = digest(w.RESULT_DIGEST_DOMAIN, {
        k: v for k, v in value.items() if k != "result_digest"})


class FixtureTransport:
    def __init__(self, response: bytes, failure: BaseException | None = None):
        self.response = response
        self.failure = failure
        self.requests: list[bytes] = []

    async def exchange(self, request: bytes, /) -> bytes:
        self.requests.append(request)
        if self.failure is not None:
            raise self.failure
        return self.response


@pytest.mark.parametrize("name", ["positive_A", "refused", "unavailable", "rejection", "rejection_budget"])
def test_accepted_frames_are_returned_as_detached_data(name: str) -> None:
    request = canonical(fixture("request_A"))
    transport = FixtureTransport(canonical(fixture(name)))
    result = asyncio.run(exchange_read(transport, request))
    assert result == fixture(name)
    assert transport.requests == [request]
    assert transport.requests[0] is request
    cast(dict[str, Any], result)["contract"] = "fixture:changed-detached-copy"
    assert json.loads(transport.response)["contract"] == fixture(name)["contract"]


@pytest.mark.parametrize("name,code", [
    ("request_budget_1", "limit_exceeded"),
    ("request_budget_65535", "limit_exceeded"),
])
def test_minimum_budget_refuses_before_transport(name: str, code: str) -> None:
    transport = FixtureTransport(canonical(fixture("rejection")))
    with pytest.raises(WireError) as error:
        asyncio.run(exchange_read(transport, canonical(fixture(name))))
    assert error.value.code == code
    assert transport.requests == []


@pytest.mark.parametrize("raw", [b"{}", b"[]", b"null", b"\xff", b'{ "contract":1}', b'{"x":1,"x":1}'])
def test_malformed_request_never_dispatches(raw: bytes) -> None:
    transport = FixtureTransport(canonical(fixture("rejection")))
    with pytest.raises(WireError):
        asyncio.run(exchange_read(transport, raw))
    assert transport.requests == []


@pytest.mark.parametrize("field", ["contract", "profile_ref", "kind", "operation", "ordinal", "intent_digest", "extra"])
def test_wrong_request_profile_or_join_never_dispatches(field: str) -> None:
    request = fixture("request_A")
    request[field] = "fixture:wrong"
    transport = FixtureTransport(canonical(fixture("rejection")))
    with pytest.raises(WireError):
        asyncio.run(exchange_read(transport, canonical(request)))
    assert transport.requests == []


@pytest.mark.parametrize("request_side", [True, False])
@pytest.mark.parametrize("variant", ["foreign", "bytes_subclass", "bytearray", "memoryview", "dict"])
def test_native_byte_admission_executes_no_foreign_behavior(request_side: bool, variant: str) -> None:
    calls: list[str] = []

    class ForeignMeta(type):
        def __eq__(cls, other):
            calls.append("equality")
            raise AssertionError("foreign equality")

    class Foreign(metaclass=ForeignMeta):
        def __getattribute__(self, name):
            calls.append(name)
            raise AssertionError("foreign attribute")

    class ForeignBytes(bytes):
        def __len__(self):
            calls.append("length")
            raise AssertionError("foreign length")

        def decode(self, *args, **kwargs):
            calls.append("decode")
            raise AssertionError("foreign decoder")

    raw = canonical(fixture("request_A" if request_side else "rejection"))
    invalid = {"foreign": Foreign(), "bytes_subclass": ForeignBytes(raw),
               "bytearray": bytearray(raw), "memoryview": memoryview(raw), "dict": {}}[variant]
    transport = FixtureTransport(canonical(fixture("rejection")) if request_side else cast(bytes, invalid))
    with pytest.raises(WireError):
        asyncio.run(exchange_read(transport, cast(bytes, invalid) if request_side else canonical(fixture("request_A"))))
    assert len(transport.requests) == (0 if request_side else 1)
    assert calls == []


@pytest.mark.parametrize("raw,code", [
    (b"[]", "malformed"), (b"null", "malformed"), (b"{}", "malformed"),
    (b'{"contract":true}', "malformed"), (b'{"contract":{}}', "malformed"),
    (b'{"contract":"fixture:unknown"}', "unsupported_contract"),
    (b'{ "contract":"fixture:unknown"}', "malformed"),
])
def test_malformed_or_unknown_response_is_not_retried(raw: bytes, code: str) -> None:
    transport = FixtureTransport(raw)
    with pytest.raises(WireError) as error:
        asyncio.run(exchange_read(transport, canonical(fixture("request_A"))))
    assert error.value.code == code
    assert len(transport.requests) == 1


@pytest.mark.parametrize("name", ["unavailable", "rejection"])
@pytest.mark.parametrize("field", ["contract", "profile_ref", "extra"])
def test_declared_response_grammar_has_no_fallback(name: str, field: str) -> None:
    response = fixture(name)
    response[field] = "fixture:wrong"
    transport = FixtureTransport(canonical(response))
    with pytest.raises(WireError):
        asyncio.run(exchange_read(transport, canonical(fixture("request_A"))))
    assert len(transport.requests) == 1


@pytest.mark.parametrize("field", ["owner_ref", "owner_generation", "request_ref", "principal_ref", "entry_kind", "intent_digest", "delivery_ref", "responder_incarnation"])
def test_fully_sealed_foreign_correlation_rejects(field: str) -> None:
    result = fixture("unavailable")
    if field in result["origin"]:
        result["origin"][field] = "raw" if field == "entry_kind" else "fixture:other"
    else:
        result[field] = "sha256:" + "f" * 64 if field == "intent_digest" else "fixture:other"
    reseal_result(result)
    raw = canonical(result)
    transport = FixtureTransport(raw)
    with pytest.raises(WireError) as error:
        asyncio.run(exchange_read(transport, canonical(fixture("request_A"))))
    assert error.value.code == "result_invalid"
    assert len(transport.requests) == 1


@pytest.mark.parametrize("field", ["ontology_ref", "namespace_ref", "context_ref", "branch_ref", "object_ref", "root_type_ref", "observable_ref", "projection_ref", "model_digest", "expected_revision_ref"])
def test_positive_observation_must_match_the_complete_selection(field: str) -> None:
    request, result = fixture("request_A"), fixture("positive_A")
    request["payload"]["selection"][field] = "sha256:" + "f" * 64 if field == "model_digest" else "fixture:other"
    reseal_request(request)
    result["intent_digest"] = request["intent_digest"]
    reseal_result(result)
    raw = canonical(result)
    transport = FixtureTransport(raw)
    with pytest.raises(WireError) as error:
        asyncio.run(exchange_read(transport, canonical(request)))
    assert error.value.code == ("source_stale" if field == "expected_revision_ref" else "result_invalid")
    assert len(transport.requests) == 1


@pytest.mark.parametrize("budget", [74534, 74535, 74536])
def test_final_result_budget_never_truncates_or_retries(budget: int) -> None:
    request = canonical(fixture("request_final_budget_" + str(budget)))
    expected = fixture("unavailable_final_budget_" + str(budget))
    raw = canonical(expected)
    assert len(raw) == 74535
    transport = FixtureTransport(raw)
    if budget < len(raw):
        with pytest.raises(WireError) as error:
            asyncio.run(exchange_read(transport, request))
        assert error.value.code == "limit_exceeded"
    else:
        assert asyncio.run(exchange_read(transport, request)) == expected
    assert transport.requests == [request]
    assert transport.response == raw


@pytest.mark.parametrize("request_side", [True, False])
def test_outer_byte_limit_is_not_relaxed(request_side: bool) -> None:
    oversized = b"x" * ((w.MAX_REQUEST_BYTES if request_side else w.MAX_RESULT_BYTES) + 1)
    transport = FixtureTransport(canonical(fixture("rejection")) if request_side else oversized)
    with pytest.raises(WireError) as error:
        asyncio.run(exchange_read(transport, oversized if request_side else canonical(fixture("request_A"))))
    assert error.value.code == "limit_exceeded"
    assert len(transport.requests) == (0 if request_side else 1)


@pytest.mark.parametrize("failure", [RuntimeError("delivery failed"), TimeoutError("reply lost"), asyncio.CancelledError("cancelled")])
def test_transport_failure_propagates_without_retry(failure: BaseException) -> None:
    transport = FixtureTransport(b"", failure)
    with pytest.raises(type(failure)) as error:
        asyncio.run(exchange_read(transport, canonical(fixture("request_A"))))
    assert error.value is failure
    assert len(transport.requests) == 1


def test_cancellation_of_suspended_exchange_reaches_transport_cleanup() -> None:
    async def proof() -> None:
        started = asyncio.Event()
        settled: list[str] = []
        requests: list[bytes] = []

        class SuspendedTransport:
            async def exchange(self, request: bytes, /) -> bytes:
                requests.append(request)
                started.set()
                try:
                    await asyncio.Event().wait()
                    raise AssertionError("unreachable")
                finally:
                    settled.append("transport settled")

        task = asyncio.create_task(exchange_read(SuspendedTransport(), canonical(fixture("request_A"))))
        await asyncio.wait_for(started.wait(), 10)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert task.done()
        assert len(requests) == 1
        assert settled == ["transport settled"]

    asyncio.run(proof())


@pytest.mark.parametrize("target,name", [
    ("_decode_frame", "unavailable"),
    ("_match_result", "unavailable"), ("_decode_rejection", "rejection"),
    ("RESULT_CONTRACT", "unavailable"), ("REJECTION_CONTRACT", "rejection"),
])
def test_transport_return_cannot_replace_retained_dispatch_bindings(monkeypatch, target: str, name: str) -> None:
    calls: list[str] = []

    def foreign(*args, **kwargs):
        calls.append("foreign")
        raise AssertionError("foreign dispatch")

    class SubstitutingTransport(FixtureTransport):
        async def exchange(self, request: bytes, /) -> bytes:
            response = await super().exchange(request)
            monkeypatch.setattr(client, target, "fixture:other" if target.endswith("CONTRACT") else foreign)
            return response

    transport = SubstitutingTransport(canonical(fixture(name)))
    assert asyncio.run(exchange_read(transport, canonical(fixture("request_A")))) == fixture(name)
    assert len(transport.requests) == 1
    assert calls == []


@pytest.mark.parametrize("target", ["type", "dict", "str"])
def test_transport_return_builtin_shadows_cannot_execute(monkeypatch: pytest.MonkeyPatch, target: str) -> None:
    calls: list[str] = []

    def foreign(*args, **kwargs):
        calls.append("foreign")
        raise AssertionError("foreign primitive")

    class SubstitutingTransport(FixtureTransport):
        async def exchange(self, request: bytes, /) -> bytes:
            response = await super().exchange(request)
            monkeypatch.setattr(client, target, foreign, raising=False)
            return response

    transport = SubstitutingTransport(canonical(fixture("unavailable")))
    assert asyncio.run(exchange_read(transport, canonical(fixture("request_A")))) == fixture("unavailable")
    assert calls == []
    assert len(transport.requests) == 1


def test_request_decoder_return_keeps_the_original_budget_entrance(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    injected: list[bool] = []
    watched = client._decode_request.__code__

    def foreign(*args, **kwargs):
        calls.append("foreign")
        raise AssertionError("foreign budget dispatch")

    def observe(frame, event, arg):
        if event == "return" and frame.f_code is watched and not injected:
            injected.append(True)
            monkeypatch.setattr(client, "_admit_decoded_budget", foreign)

    transport = FixtureTransport(canonical(fixture("unavailable")))
    sys.setprofile(observe)
    try:
        assert asyncio.run(exchange_read(transport, canonical(fixture("request_A")))) == fixture("unavailable")
    finally:
        sys.setprofile(None)
    assert injected == [True]
    assert calls == []
    assert len(transport.requests) == 1


def test_explicit_exchanges_use_no_second_journal_or_response_cache() -> None:
    request = canonical(fixture("request_A"))
    transport = FixtureTransport(canonical(fixture("unavailable")))
    first = asyncio.run(exchange_read(transport, request))
    second = asyncio.run(exchange_read(transport, request))
    assert first == second and first is not second
    assert transport.requests == [request, request]


def test_response_decoder_return_cannot_execute_a_substituted_error_constructor(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    injected: list[bool] = []
    watched = client._decode_frame.__code__

    def foreign(self, *args, **kwargs):
        calls.append("foreign constructor")
        raise AssertionError("foreign error constructor")

    def observe(frame, event, arg):
        if event == "return" and frame.f_code is watched and not injected:
            injected.append(True)
            monkeypatch.setattr(WireError, "__init__", foreign)

    transport = FixtureTransport(b"[]")
    sys.setprofile(observe)
    try:
        with pytest.raises(WireError):
            asyncio.run(exchange_read(transport, canonical(fixture("request_A"))))
    finally:
        sys.setprofile(None)
    assert injected == [True]
    assert calls == []
    assert len(transport.requests) == 1
