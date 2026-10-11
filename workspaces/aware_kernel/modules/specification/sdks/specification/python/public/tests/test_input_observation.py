import hashlib
from dataclasses import replace

import pytest
from aware_specification_sdk import (
    SPECIFICATION_INPUT_LIMIT,
    SPECIFICATION_INPUT_WIRE_LIMIT,
    SpecificationInputCleanup,
    SpecificationInputObservationClient,
    SpecificationInputObservationError,
    SpecificationInputObservationRequest,
    SpecificationInputObservationResult,
    decode_specification_input_value,
    encode_specification_input_value,
)


def request():
    return SpecificationInputObservationRequest("input", "/customer")


def result(value=None, body=b"\x00\xff"):
    return SpecificationInputObservationResult(
        value or request(),
        "/customer/input",
        "provider",
        "distribution",
        "0.4.3",
        body.hex(),
        len(body),
        "sha256:" + hashlib.sha256(body).hexdigest(),
    )


@pytest.mark.parametrize(
    "value", [request(), result(), SpecificationInputObservationError("missing")]
)
def test_wire_roundtrip(value):
    body = encode_specification_input_value(value)
    restored = decode_specification_input_value(body)
    assert restored == value and restored is not value
    assert encode_specification_input_value(restored) == body


@pytest.mark.parametrize("body", [b"", b"x" * SPECIFICATION_INPUT_LIMIT])
def test_boundary_bytes_are_exact(body):
    value = result(body=body)
    assert value.body == body
    assert (
        decode_specification_input_value(encode_specification_input_value(value)).body
        == body
    )


@pytest.mark.parametrize(
    "patch",
    [
        {"byte_count": True},
        {"byte_count": 0},
        {"body_hex": "00FF"},
        {"source_sha256": "sha256:" + "0" * 64},
        {"cleanup": SpecificationInputCleanup.UNKNOWN},
        {"cleanup": "closed"},
        {"observation_grade": "every_write"},
        {"body_hex": "00" * (SPECIFICATION_INPUT_LIMIT + 1)},
    ],
)
def test_invalid_result_values_refuse(patch):
    with pytest.raises(ValueError):
        replace(result(), **patch)


def test_initial_invalid_request_never_dispatches():
    class Never:
        def observe_draft_input(self, value):
            raise AssertionError("dispatched")

    with pytest.raises(SpecificationInputObservationError) as caught:
        SpecificationInputObservationClient(Never()).observe_draft_input(object())
    assert caught.value.provider_invoked is False
    assert caught.value.cleanup is SpecificationInputCleanup.NOT_ACQUIRED


@pytest.mark.parametrize(
    "field,value",
    [
        ("request", SpecificationInputObservationRequest("other", "/customer")),
        ("request", SpecificationInputObservationRequest("input", "/other")),
        ("source_sha256", "wrong"),
        ("byte_count", True),
        ("cleanup", "closed"),
    ],
)
def test_malformed_provider_result_is_not_a_guard(field, value):
    returned = result()
    object.__setattr__(returned, field, value)

    class Provider:
        def observe_draft_input(self, value):
            return returned

    with pytest.raises(SpecificationInputObservationError) as caught:
        SpecificationInputObservationClient(Provider()).observe_draft_input(request())
    assert caught.value.request == request()
    assert caught.value.effect == "unknown"
    assert caught.value.cleanup is SpecificationInputCleanup.UNKNOWN
    assert caught.value.reported_result_type is not None
    assert caught.value.diagnostics == ("provider_report_unvalidated",)


def test_dispatch_and_return_are_detached():
    original = request()
    retained = {}

    class Provider:
        def observe_draft_input(self, value):
            retained["value"] = result(value)
            return retained["value"]

    observed = SpecificationInputObservationClient(Provider()).observe_draft_input(
        original
    )
    object.__setattr__(retained["value"].request, "source_ref", "changed")
    assert original == observed.request == request()


@pytest.mark.parametrize("fault", [KeyboardInterrupt, SystemExit, OSError])
def test_unknown_provider_failure_has_unknown_cleanup(fault):
    class Provider:
        def observe_draft_input(self, value):
            raise fault("interrupted")

    with pytest.raises(SpecificationInputObservationError) as caught:
        SpecificationInputObservationClient(Provider()).observe_draft_input(request())
    assert caught.value.effect == "unknown" and caught.value.provider_invoked


def test_genuine_error_is_detached_and_correlated():
    retained = SpecificationInputObservationError(
        "read_failed",
        request(),
        True,
        SpecificationInputCleanup.CLOSED,
        diagnostics=("original",),
    )

    class Provider:
        def observe_draft_input(self, value):
            raise retained

    with pytest.raises(SpecificationInputObservationError) as caught:
        SpecificationInputObservationClient(Provider()).observe_draft_input(request())
    retained.diagnostics = ("changed",)
    assert caught.value.diagnostics == ("original",)
    assert caught.value.cleanup is SpecificationInputCleanup.CLOSED


def test_oversized_wire_refuses_before_decoding():
    with pytest.raises(
        SpecificationInputObservationError, match="input_wire_limit_exceeded"
    ):
        decode_specification_input_value(b" " * (SPECIFICATION_INPUT_WIRE_LIMIT + 1))


def test_caller_and_dispatch_mutation_cannot_rewrite_original_request():
    original = request()

    class Provider:
        def observe_draft_input(self, value):
            object.__setattr__(original, "source_ref", "changed caller")
            object.__setattr__(value, "source_ref", "changed dispatch")
            return result(value)

    with pytest.raises(SpecificationInputObservationError) as caught:
        SpecificationInputObservationClient(Provider()).observe_draft_input(original)
    assert caught.value.request == request()


@pytest.mark.parametrize("stage", ["request", "result"])
def test_snapshot_interruption_is_typed_without_dispatch_replay(monkeypatch, stage):
    import aware_specification_sdk.input_observation as owner

    original = request()
    returned = result()
    calls = []
    constructor = owner.replace

    def interrupt(value):
        if type(value) is (type(original) if stage == "request" else type(returned)):
            raise KeyboardInterrupt("validation interrupted")
        return constructor(value)

    class Provider:
        def observe_draft_input(self, value):
            calls.append(value)
            return returned

    monkeypatch.setattr(owner, "replace", interrupt)
    with pytest.raises(SpecificationInputObservationError) as caught:
        SpecificationInputObservationClient(Provider()).observe_draft_input(original)
    assert len(calls) == (0 if stage == "request" else 1)
    assert caught.value.provider_invoked is (stage == "result")


@pytest.mark.parametrize("fault", [KeyboardInterrupt, ValueError])
def test_dispatch_snapshot_failure_preserves_original_uninvoked_evidence(
    monkeypatch, fault
):
    import aware_specification_sdk.input_observation as owner

    original = request()
    constructor = owner.replace
    snapshots = []
    calls = []

    def fail_second_snapshot(value):
        snapshots.append(value)
        if len(snapshots) == 2:
            raise fault("dispatch request preparation failed")
        return constructor(value)

    class Provider:
        def observe_draft_input(self, value):
            calls.append(value)
            return result(value)

    monkeypatch.setattr(owner, "replace", fail_second_snapshot)
    with pytest.raises(SpecificationInputObservationError) as caught:
        SpecificationInputObservationClient(Provider()).observe_draft_input(original)
    assert len(snapshots) >= 2
    assert not calls
    assert caught.value.request == original == request()
    assert caught.value.request is not original
    assert caught.value.provider_invoked is False
    assert caught.value.cleanup is SpecificationInputCleanup.NOT_ACQUIRED
    assert caught.value.effect == "none"
    assert caught.value.observed_body_hex is None
    assert caught.value.reported_result_type is None
    assert isinstance(caught.value.__cause__, fault)


@pytest.mark.parametrize("body", [b"{}", b"null", b"[]", b"bad", b"{}\n"])
def test_malformed_wire_uses_input_error_carrier(body):
    with pytest.raises(SpecificationInputObservationError):
        decode_specification_input_value(body)
