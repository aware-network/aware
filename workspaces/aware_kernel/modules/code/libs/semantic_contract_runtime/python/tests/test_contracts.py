from __future__ import annotations

from dataclasses import replace
from typing import Any, cast

import pytest
from aware_code_semantic_contract_runtime import (
    ConsumedRoleDeclaration,
    ContentDigest,
    ContractViolation,
    PreparedSemanticEffectEnvelope,
    ProducedRoleDeclaration,
    ProviderExecutionBinding,
    SemanticBody,
    SemanticBodyCodecBinding,
    SemanticConfigurationCoordinate,
    SemanticContractInvocation,
    SemanticContractProviderDeclaration,
    SemanticContractRef,
    SemanticContractResult,
    SemanticImpactCoordinate,
    SemanticImplementationCoordinate,
    SemanticOutputEnvelope,
    SemanticPackageCoordinate,
    SemanticTransitionEnvelope,
    SemanticValueCoordinate,
    TerminalStatus,
    TypedEmptyCoordinate,
    canonical_json_text,
)


def digest(character: str) -> ContentDigest:
    return ContentDigest(f"sha256:{character * 64}")


SOURCE = SemanticContractRef("aware.language.parsed", "1", digest("1"))
RESULT = SemanticContractRef("aware.sdk.definition", "1", digest("2"))
TRANSITION = SemanticContractRef("aware.sdk.transition", "1", digest("3"))
EFFECT = SemanticContractRef("aware.sdk.effect", "1", digest("4"))
OUTPUT = SemanticContractRef("aware.code.package-delta", "1", digest("5"))
PROVIDER = SemanticContractRef("aware.sdk.provider", "1", digest("6"))
CODEC_IMPLEMENTATION = SemanticImplementationCoordinate(
    "canonical-json-codec", digest("7")
)

SOURCE_BODY = b'{"source":"demo"}'
RESULT_BODY = b'{"sdk":"demo"}'
TRANSITION_BODY = b'{"movement":"create"}'
EFFECT_BODY = b'{"creates":["client"]}'
OUTPUT_BODY = b'{"paths":["client.py"]}'


def body_coordinate(
    role: str,
    contract: SemanticContractRef,
    value_ref: str,
    body: bytes,
) -> SemanticValueCoordinate:
    return SemanticValueCoordinate(
        role,
        contract,
        value_ref,
        ContentDigest.of_bytes(body),
        len(body),
    )


def codec_bindings() -> tuple[SemanticBodyCodecBinding, ...]:
    return tuple(
        SemanticBodyCodecBinding(contract, CODEC_IMPLEMENTATION)
        for contract in sorted(
            (SOURCE, RESULT, TRANSITION, EFFECT, OUTPUT),
            key=lambda item: canonical_json_text(item.to_wire()).encode(),
        )
    )


def declaration() -> SemanticContractProviderDeclaration:
    return SemanticContractProviderDeclaration(
        provider_key="sdk",
        provider_contract=PROVIDER,
        package_kinds=("sdk",),
        operation_kinds=("materialize",),
        consumed_roles=(ConsumedRoleDeclaration("source", (SOURCE,)),),
        result_role=ProducedRoleDeclaration("result", RESULT),
        transition_contract=TRANSITION,
        effect_role=ProducedRoleDeclaration("effect", EFFECT),
        effect_contract=EFFECT,
        output_roles=(ProducedRoleDeclaration("output", OUTPUT),),
        allows_typed_empty=True,
        counter_keys=("movements",),
    )


def invocation(
    profile_ref: str = "sdk-profile", profile_digest: ContentDigest | None = None
) -> SemanticContractInvocation:
    return SemanticContractInvocation(
        invocation_ref="invocation-1",
        idempotency_key="idem-1",
        profile_ref=profile_ref,
        profile_digest=profile_digest or digest("7"),
        target_package=SemanticPackageCoordinate("aware.sdk.demo", "sdk", digest("8")),
        operation_kind="materialize",
        inputs=(body_coordinate("source", SOURCE, "parsed-1", SOURCE_BODY),),
        predecessor=TypedEmptyCoordinate(RESULT),
        dependencies=(),
        body_codec_bindings=codec_bindings(),
        provider_bindings=(
            ProviderExecutionBinding(
                "sdk",
                SemanticImplementationCoordinate("sdk-impl", digest("a")),
                SemanticConfigurationCoordinate("sdk-config", digest("b")),
            ),
        ),
        requested_output_roles=("output",),
    )


def delta_result(
    call: SemanticContractInvocation,
    input_closure_digest: ContentDigest | None = None,
) -> SemanticContractResult:
    candidate = body_coordinate("result", RESULT, "definition-1", RESULT_BODY)
    impacts = (SemanticImpactCoordinate("aware.sdk.demo", "member", "client"),)
    transition = SemanticTransitionEnvelope(
        provider_key="sdk",
        result_contract=RESULT,
        transition_contract=TRANSITION,
        predecessor=call.predecessor,
        result=candidate,
        transition_body=body_coordinate(
            "transition-body", TRANSITION, "transition-1", TRANSITION_BODY
        ),
        impacts=impacts,
        input_closure_digest=input_closure_digest or digest("e"),
    )
    effect = PreparedSemanticEffectEnvelope(
        provider_key="sdk",
        effect_contract=EFFECT,
        transition_digest=transition.digest,
        base_state=call.predecessor,
        candidate_state=candidate,
        effect_body=body_coordinate("effect", EFFECT, "effect-1", EFFECT_BODY),
        renderer_inputs=(),
        impacts=impacts,
        work_counters=(("movements", 1),),
    )
    output = SemanticOutputEnvelope(
        "sdk",
        body_coordinate("output", OUTPUT, "delta-1", OUTPUT_BODY),
        effect.digest,
    )
    return SemanticContractResult(
        TerminalStatus.DELTA,
        call.digest,
        transition=transition,
        effect=effect,
        outputs=(output,),
    )


def input_bodies(call: SemanticContractInvocation) -> tuple[SemanticBody, ...]:
    return (SemanticBody(call.inputs[0], SOURCE_BODY),)


def delta_bodies(result: SemanticContractResult) -> tuple[SemanticBody, ...]:
    assert result.transition is not None
    assert result.effect is not None
    return tuple(
        sorted(
            (
                SemanticBody(result.transition.result, RESULT_BODY),
                SemanticBody(result.transition.transition_body, TRANSITION_BODY),
                SemanticBody(result.effect.effect_body, EFFECT_BODY),
                SemanticBody(result.outputs[0].output, OUTPUT_BODY),
            ),
            key=lambda item: canonical_json_text(item.coordinate.to_wire()).encode(),
        )
    )


def test_portable_values_are_stable_and_canonical() -> None:
    value = declaration()
    assert value.digest == ContentDigest.of_bytes(
        canonical_json_text(value._wire_without_digest()).encode()
    )
    assert canonical_json_text({"z": False, "a": 1}) == '{"a":1,"z":false}'
    result = delta_result(invocation())
    assert result.effect is not None
    assert result.transition is not None
    assert result.effect.transition_digest == result.transition.digest


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -0.0])
def test_noncanonical_numbers_fail(value: float) -> None:
    with pytest.raises(ContractViolation):
        canonical_json_text({"value": value})


def test_boolean_is_not_an_integer_size() -> None:
    with pytest.raises(TypeError):
        SemanticValueCoordinate("source", SOURCE, "parsed-1", digest("9"), True)


def test_semantic_body_binds_exact_bytes_digest_and_size() -> None:
    call = invocation()
    assert SemanticBody(call.inputs[0], SOURCE_BODY).canonical_body == SOURCE_BODY
    with pytest.raises(ContractViolation, match="digest differs"):
        SemanticBody(replace(call.inputs[0], digest=digest("1")), SOURCE_BODY)
    with pytest.raises(ContractViolation, match="size differs"):
        SemanticBody(replace(call.inputs[0], size_bytes=1), SOURCE_BODY)
    with pytest.raises(TypeError):
        SemanticBody(call.inputs[0], cast(Any, bytearray(SOURCE_BODY)))


def test_subclass_and_uninitialized_values_fail_before_serialization() -> None:
    class ForeignDigest(ContentDigest):
        pass

    with pytest.raises(TypeError):
        SemanticContractRef("foreign", "1", ForeignDigest(digest("1").value))
    poisoned = object.__new__(SemanticContractRef)
    with pytest.raises((AttributeError, TypeError)):
        SemanticValueCoordinate("source", poisoned, "parsed", digest("1"), 1)


def test_nested_restamp_fails_before_foreign_method_execution() -> None:
    calls: list[str] = []

    class ForeignContract(SemanticContractRef):
        def __eq__(self, other):
            calls.append("foreign_eq")
            return super().__eq__(other)

        def to_wire(self):
            calls.append("foreign_to_wire")
            return super().to_wire()

    result = delta_result(invocation())
    assert result.transition is not None
    foreign = ForeignContract("foreign", "1", digest("1"))
    object.__setattr__(result.transition.transition_body, "contract", foreign)
    with pytest.raises(TypeError):
        result.to_wire()
    assert calls == []


def test_nested_object_new_and_digest_restamp_fail() -> None:
    result = delta_result(invocation())
    assert result.effect is not None
    object.__setattr__(
        result.effect.effect_body,
        "digest",
        object.__new__(ContentDigest),
    )
    with pytest.raises((AttributeError, TypeError)):
        _ = result.digest


def test_terminal_union_rejects_publishable_failure_and_unbound_output() -> None:
    call = invocation()
    successful = delta_result(call)
    with pytest.raises(ContractViolation):
        SemanticContractResult(
            TerminalStatus.FAILED,
            call.digest,
            effect=successful.effect,
            reason="provider_failed",
        )
    with pytest.raises(ContractViolation):
        replace(
            successful,
            outputs=(
                replace(successful.outputs[0], prepared_effect_digest=digest("1")),
            ),
        )


def test_current_terminal_requires_matching_retained_effect() -> None:
    call = invocation()
    candidate = SemanticValueCoordinate(
        "result", RESULT, "definition-current", digest("1"), 9
    )
    effect = PreparedSemanticEffectEnvelope(
        provider_key="sdk",
        effect_contract=EFFECT,
        transition_digest=digest("2"),
        base_state=call.predecessor,
        candidate_state=candidate,
        effect_body=SemanticValueCoordinate(
            "effect", EFFECT, "effect-current", digest("3"), 8
        ),
        renderer_inputs=(),
        impacts=(SemanticImpactCoordinate("aware.sdk.demo", "definition", "current"),),
        work_counters=(),
    )
    current = SemanticContractResult(
        TerminalStatus.CURRENT,
        call.digest,
        current_result=candidate,
        effect=effect,
    )
    assert current.current_result == candidate
    with pytest.raises(ContractViolation, match="candidate differs"):
        replace(current, current_result=replace(candidate, digest=digest("4")))


def test_collections_require_exact_ordered_tuples() -> None:
    with pytest.raises(TypeError):
        replace(declaration(), package_kinds=["sdk"])
    with pytest.raises(ContractViolation):
        replace(declaration(), terminal_statuses=("failed", "delta"))
