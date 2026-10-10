from __future__ import annotations

import asyncio
import copy
import json
import pickle
from collections import Counter
from dataclasses import replace
from typing import cast

import pytest
from test_contracts import (
    CODEC_IMPLEMENTATION,
    EFFECT,
    EFFECT_BODY,
    OUTPUT,
    OUTPUT_BODY,
    RESULT,
    RESULT_BODY,
    SOURCE,
    TRANSITION,
    body_coordinate,
    codec_bindings,
    declaration,
    delta_bodies,
    delta_result,
    digest,
    input_bodies,
    invocation,
)

from aware_code_semantic_contract_runtime import (
    ConsumedRoleDeclaration,
    ContextualSemanticBodyCodec,
    ContractViolation,
    ExecutionCompletion,
    PreparedSemanticEffectEnvelope,
    ProducedRoleDeclaration,
    ProfileInputDeclaration,
    ProfileStepDeclaration,
    ProviderDerivation,
    ProviderStepInvocation,
    ProviderTerminalFailure,
    RoleBinding,
    SemanticBody,
    SemanticBodyCodec,
    SemanticBodyValidationContext,
    SemanticContractProfileDeclaration,
    SemanticContractProviderDeclaration,
    SemanticContractRef,
    SemanticContractResult,
    SemanticContractRuntime,
    SemanticImpactCoordinate,
    SemanticImplementationCoordinate,
    TerminalStatus,
    canonical_json_bytes,
    canonical_json_text,
    decode_profile_declaration,
    encode_profile_declaration,
    resolve_profile,
)


class JsonBodyCodec:
    def __init__(self, contract: SemanticContractRef) -> None:
        self._contract = contract
        self._implementation = CODEC_IMPLEMENTATION
        self.contexts: list[SemanticBodyValidationContext] = []

    @property
    def contract(self) -> SemanticContractRef:
        return self._contract

    @property
    def implementation(self) -> SemanticImplementationCoordinate:
        return self._implementation

    def decode(self, canonical_body: bytes) -> object:
        if type(canonical_body) is not bytes:
            raise TypeError("body must be exact bytes")
        value = json.loads(canonical_body)
        if canonical_json_text(value).encode() != canonical_body:
            raise ContractViolation("body is not canonical JSON")
        return value

    def encode(self, value: object) -> bytes:
        return canonical_json_text(value).encode()

    def decode_contextual(
        self, canonical_body: bytes, context: SemanticBodyValidationContext
    ) -> object:
        context.__post_init__()
        self.contexts.append(context)
        return self.decode(canonical_body)

    def encode_contextual(
        self, value: object, context: SemanticBodyValidationContext
    ) -> bytes:
        context.__post_init__()
        return self.encode(value)


class ContextFreeJsonBodyCodec:
    def __init__(self, contract: SemanticContractRef) -> None:
        self._contract = contract

    @property
    def contract(self) -> SemanticContractRef:
        return self._contract

    @property
    def implementation(self) -> SemanticImplementationCoordinate:
        return CODEC_IMPLEMENTATION

    def decode(self, canonical_body: bytes) -> object:
        return json.loads(canonical_body)

    def encode(self, value: object) -> bytes:
        return canonical_json_text(value).encode()


class CountingBodyCodec:
    def __init__(
        self,
        codec: SemanticBodyCodec | ContextualSemanticBodyCodec,
        calls: Counter[tuple[SemanticContractRef, str]],
    ) -> None:
        self._codec = codec
        self._calls = calls

    @property
    def contract(self) -> SemanticContractRef:
        return self._codec.contract

    @property
    def implementation(self) -> SemanticImplementationCoordinate:
        return self._codec.implementation

    def decode(self, canonical_body: bytes) -> object:
        self._calls[(self.contract, "decode")] += 1
        return self._codec.decode(canonical_body)

    def encode(self, value: object) -> bytes:
        self._calls[(self.contract, "encode")] += 1
        return self._codec.encode(value)

    def decode_contextual(
        self, canonical_body: bytes, context: SemanticBodyValidationContext
    ) -> object:
        self._calls[(self.contract, "decode_contextual")] += 1
        return cast(ContextualSemanticBodyCodec, self._codec).decode_contextual(
            canonical_body, context
        )

    def encode_contextual(
        self, value: object, context: SemanticBodyValidationContext
    ) -> bytes:
        self._calls[(self.contract, "encode_contextual")] += 1
        return cast(ContextualSemanticBodyCodec, self._codec).encode_contextual(
            value, context
        )


def body_codecs() -> dict[SemanticContractRef, SemanticBodyCodec]:
    return {
        binding.contract: JsonBodyCodec(binding.contract)
        for binding in codec_bindings()
    }


def profile() -> SemanticContractProfileDeclaration:
    return SemanticContractProfileDeclaration(
        profile_ref="sdk-profile",
        version="1",
        package_kinds=("sdk",),
        operation_kinds=("materialize",),
        inputs=(ProfileInputDeclaration("source", SOURCE),),
        providers=(declaration(),),
        steps=(
            ProfileStepDeclaration(
                "sdk-step", "sdk", (RoleBinding("source", "source"),)
            ),
        ),
        terminal_result_role="result",
        terminal_effect_role="effect",
        terminal_output_roles=("output",),
    )


class DeltaProvider:
    def __init__(
        self, provider_declaration: SemanticContractProviderDeclaration | None = None
    ) -> None:
        self._declaration = provider_declaration or declaration()
        self.seen = []

    @property
    def declaration(self) -> SemanticContractProviderDeclaration:
        return self._declaration

    async def derive(self, invocation: ProviderStepInvocation) -> ProviderDerivation:
        self.seen.append(invocation)
        result = delta_result(invocation.invocation, invocation.input_closure_digest)
        return ProviderDerivation(result, delta_bodies(result))


class CurrentProvider(DeltaProvider):
    async def derive(self, invocation: ProviderStepInvocation) -> ProviderDerivation:
        if invocation.predecessor is None:
            raise ValueError("CURRENT proof requires an admitted predecessor")
        candidate = invocation.predecessor.coordinate
        effect_body = body_coordinate("effect", EFFECT, "effect-current", EFFECT_BODY)
        effect = PreparedSemanticEffectEnvelope(
            provider_key="sdk",
            effect_contract=EFFECT,
            transition_digest=digest("2"),
            base_state=invocation.invocation.predecessor,
            candidate_state=candidate,
            effect_body=effect_body,
            renderer_inputs=(),
            impacts=(
                SemanticImpactCoordinate("aware.sdk.demo", "definition", "current"),
            ),
            work_counters=(("movements", 0),),
        )
        result = SemanticContractResult(
            TerminalStatus.CURRENT,
            invocation.invocation.digest,
            current_result=candidate,
            effect=effect,
        )
        return ProviderDerivation(result, (SemanticBody(effect_body, EFFECT_BODY),))


class MissingRequestedOutputProvider(DeltaProvider):
    async def derive(self, invocation: ProviderStepInvocation) -> ProviderDerivation:
        complete = delta_result(invocation.invocation, invocation.input_closure_digest)
        missing = replace(complete, outputs=())
        bodies = tuple(
            body
            for body in delta_bodies(complete)
            if body.coordinate.contract != OUTPUT
        )
        return ProviderDerivation(missing, bodies)


class FailedProvider(DeltaProvider):
    async def derive(self, invocation: ProviderStepInvocation) -> ProviderDerivation:
        return ProviderDerivation(
            SemanticContractResult(
                TerminalStatus.FAILED, invocation.invocation.digest, reason="blocked"
            )
        )


class WaitingProvider(DeltaProvider):
    def __init__(self) -> None:
        super().__init__()
        self.entered = asyncio.Event()
        self.release = asyncio.Event()

    async def derive(self, invocation: ProviderStepInvocation) -> ProviderDerivation:
        self.entered.set()
        await self.release.wait()
        result = delta_result(invocation.invocation, invocation.input_closure_digest)
        return ProviderDerivation(result, delta_bodies(result))


class RestampingProvider(DeltaProvider):
    async def derive(self, invocation: ProviderStepInvocation) -> ProviderDerivation:
        object.__setattr__(invocation.invocation, "idempotency_key", "restamped")
        result = delta_result(invocation.invocation, invocation.input_closure_digest)
        return ProviderDerivation(result, delta_bodies(result))


class MissingBodyProvider(DeltaProvider):
    async def derive(self, invocation: ProviderStepInvocation) -> ProviderDerivation:
        result = delta_result(invocation.invocation, invocation.input_closure_digest)
        return ProviderDerivation(result, delta_bodies(result)[:-1])


class MutatingInputProvider(DeltaProvider):
    async def derive(self, invocation: ProviderStepInvocation) -> ProviderDerivation:
        value = cast(dict[str, object], invocation.inputs[0].value)
        value["source"] = "mutated"
        result = delta_result(invocation.invocation, invocation.input_closure_digest)
        return ProviderDerivation(result, delta_bodies(result))


def test_profile_round_trip_and_deterministic_resolution() -> None:
    value = profile()
    assert resolve_profile(value) == value.steps
    assert decode_profile_declaration(encode_profile_declaration(value)) == value


def test_profile_rejects_missing_binding_and_provider_substitution() -> None:
    with pytest.raises(ContractViolation, match="exact consumed closure"):
        replace(profile(), steps=(ProfileStepDeclaration("sdk-step", "sdk", ()),))
    substituted = replace(
        declaration(), provider_contract=SemanticContractRef("other", "1", digest("1"))
    )
    with pytest.raises(ContractViolation, match="declaration differs"):
        SemanticContractRuntime(
            profile(), {"sdk": DeltaProvider(substituted)}, body_codecs()
        )


def test_optional_consumed_role_is_explicit_and_cannot_leak_to_required() -> None:
    optional = ConsumedRoleDeclaration("optional", (SOURCE,), required=False)
    provider = replace(
        declaration(),
        consumed_roles=(optional, declaration().consumed_roles[0]),
    )
    admitted = replace(profile(), providers=(provider,))
    assert resolve_profile(admitted) == admitted.steps
    required = replace(optional, required=True)
    with pytest.raises(ContractViolation, match="exact consumed closure"):
        replace(
            admitted,
            providers=(
                replace(
                    provider, consumed_roles=(required, provider.consumed_roles[1])
                ),
            ),
        )


def test_profile_cycle_is_rejected() -> None:
    a_result = SemanticContractRef("a.result", "1", digest("1"))
    b_result = SemanticContractRef("b.result", "1", digest("2"))

    def provider(
        key: str,
        consumed: SemanticContractRef,
        result: SemanticContractRef,
        marker: str,
    ):
        effect = SemanticContractRef(f"{key}.effect", "1", digest(marker))
        return SemanticContractProviderDeclaration(
            provider_key=key,
            provider_contract=SemanticContractRef(
                f"{key}.provider", "1", digest(marker)
            ),
            package_kinds=("sdk",),
            operation_kinds=("materialize",),
            consumed_roles=(ConsumedRoleDeclaration(f"{key}.input", (consumed,)),),
            result_role=ProducedRoleDeclaration(f"{key}.result", result),
            transition_contract=SemanticContractRef(
                f"{key}.transition", "1", digest(marker)
            ),
            effect_role=ProducedRoleDeclaration(f"{key}.effect", effect),
            effect_contract=effect,
        )

    with pytest.raises(ContractViolation, match="cycle"):
        SemanticContractProfileDeclaration(
            profile_ref="cycle",
            version="1",
            package_kinds=("sdk",),
            operation_kinds=("materialize",),
            inputs=(),
            providers=(
                provider("a", b_result, a_result, "3"),
                provider("b", a_result, b_result, "4"),
            ),
            steps=(
                ProfileStepDeclaration("a", "a", (RoleBinding("a.input", "b.result"),)),
                ProfileStepDeclaration("b", "b", (RoleBinding("b.input", "a.result"),)),
            ),
            terminal_result_role="b.result",
            terminal_effect_role="b.effect",
        )


def test_runtime_returns_owned_nonportable_completion() -> None:
    async def prove() -> None:
        selected = profile()
        provider = DeltaProvider()
        runtime = SemanticContractRuntime(selected, {"sdk": provider}, body_codecs())
        call = invocation(profile_digest=selected.digest)
        completion = await runtime.execute(call, input_bodies(call))
        assert runtime.owns_completion(completion)
        assert completion.result == delta_result(
            call, provider.seen[0].input_closure_digest
        )
        assert (
            completion.body_for(completion.result.outputs[0].output).canonical_body
            == OUTPUT_BODY
        )
        assert provider.seen[0].binding.provider_key == "sdk"
        assert provider.seen[0].inputs[0].target_role == "source"
        assert provider.seen[0].inputs[0].value == {"source": "demo"}
        with pytest.raises(TypeError):
            ExecutionCompletion(
                None, None, call.digest, selected.digest, completion.result, ()
            )
        with pytest.raises(TypeError):
            pickle.dumps(completion)

    asyncio.run(prove())


def test_current_omits_admitted_delta_outputs_without_provider_preflight() -> None:
    async def prove() -> None:
        selected = profile()
        candidate = body_coordinate("result", RESULT, "definition-current", RESULT_BODY)
        call = replace(
            invocation(profile_digest=selected.digest),
            predecessor=candidate,
        )
        runtime = SemanticContractRuntime(
            selected, {"sdk": CurrentProvider()}, body_codecs()
        )

        completion = await runtime.execute(
            call,
            input_bodies(call),
            predecessor_body=SemanticBody(candidate, RESULT_BODY),
        )

        assert call.requested_output_roles == ("output",)
        assert completion.result.status is TerminalStatus.CURRENT
        assert completion.result.current_result == candidate
        assert completion.result.outputs == ()
        assert runtime.owns_completion(completion)

    asyncio.run(prove())


def test_delta_cannot_omit_an_admitted_requested_output() -> None:
    async def prove() -> None:
        selected = profile()
        runtime = SemanticContractRuntime(
            selected, {"sdk": MissingRequestedOutputProvider()}, body_codecs()
        )
        call = invocation(profile_digest=selected.digest)

        with pytest.raises(
            ContractViolation,
            match="output closure differs from terminal-status demand",
        ):
            await runtime.execute(call, input_bodies(call))

    asyncio.run(prove())


def test_execution_epoch_has_linear_body_codec_admission_budget() -> None:
    async def prove() -> None:
        selected = profile()
        calls: Counter[tuple[SemanticContractRef, str]] = Counter()
        codecs: dict[SemanticContractRef, SemanticBodyCodec] = {
            contract: CountingBodyCodec(codec, calls)
            for contract, codec in body_codecs().items()
        }
        runtime = SemanticContractRuntime(selected, {"sdk": DeltaProvider()}, codecs)
        call = invocation(profile_digest=selected.digest)
        await runtime.execute(call, input_bodies(call))

        assert calls[(SOURCE, "decode")] == 1
        assert calls[(SOURCE, "encode")] == 2
        assert calls[(RESULT, "decode")] == 1
        assert calls[(RESULT, "encode")] == 1
        for contract in (TRANSITION, EFFECT, OUTPUT):
            assert calls[(contract, "decode_contextual")] == 1
            assert calls[(contract, "encode_contextual")] == 1

    asyncio.run(prove())


def test_publication_snapshot_is_one_portable_pass_without_codec_reentry() -> None:
    async def prove() -> None:
        selected = profile()
        calls: Counter[tuple[SemanticContractRef, str]] = Counter()
        codecs: dict[SemanticContractRef, SemanticBodyCodec] = {
            contract: CountingBodyCodec(codec, calls)
            for contract, codec in body_codecs().items()
        }
        runtime = SemanticContractRuntime(selected, {"sdk": DeltaProvider()}, codecs)
        call = invocation(profile_digest=selected.digest)
        completion = await runtime.execute(call, input_bodies(call))
        before = calls.copy()

        snapshot = runtime.snapshot_completion(completion)

        assert calls == before
        assert snapshot.invocation_digest == call.digest
        assert snapshot.profile_digest == selected.digest
        assert snapshot.result == completion.result
        assert snapshot.result_digest == completion.result.digest
        assert snapshot.result_wire == canonical_json_bytes(completion.result.to_wire())
        assert completion.result.effect is not None
        assert completion.result.transition is not None
        assert snapshot.effect_digest == completion.result.effect.digest
        assert snapshot.transition_digest == completion.result.transition.digest
        assert len(snapshot.bodies) == 4
        assert (
            snapshot.body_for(snapshot.result.outputs[0].output).canonical_body
            == OUTPUT_BODY
        )
        with pytest.raises(ContractViolation, match="does not own"):
            SemanticContractRuntime(
                selected, {"sdk": DeltaProvider()}, body_codecs()
            ).snapshot_completion(completion)

    asyncio.run(prove())


def test_publication_snapshot_rejects_portable_byte_restamp() -> None:
    async def prove() -> None:
        selected = profile()
        runtime = SemanticContractRuntime(
            selected, {"sdk": DeltaProvider()}, body_codecs()
        )
        call = invocation(profile_digest=selected.digest)
        completion = await runtime.execute(call, input_bodies(call))
        output = completion.result.outputs[0].output
        target = next(item for item in completion._bodies if item._coordinate == output)
        object.__setattr__(target, "_canonical_body", b"{}")
        with pytest.raises(
            ContractViolation, match="restamped|differs from coordinate"
        ):
            runtime.snapshot_completion(completion)

    asyncio.run(prove())


def test_publication_snapshot_rejects_cached_envelope_restamp() -> None:
    async def prove() -> None:
        selected = profile()
        runtime = SemanticContractRuntime(
            selected, {"sdk": DeltaProvider()}, body_codecs()
        )
        call = invocation(profile_digest=selected.digest)
        completion = await runtime.execute(call, input_bodies(call))
        object.__setattr__(completion, "_result_wire", b"{}")
        with pytest.raises(ContractViolation, match="cache was restamped"):
            runtime.snapshot_completion(completion)

    asyncio.run(prove())


@pytest.mark.parametrize(
    "poison",
    (
        "context",
        "context_removal",
        "epoch",
        "execution_attempt",
        "outer_impact",
        "admitted_value",
        "coherent_retry_registration",
        "coherent_identity_restamp",
        "identity_tuple_replacement",
    ),
)
def test_publication_snapshot_rejects_registered_context_and_body_poison(
    poison: str,
) -> None:
    async def prove() -> None:
        selected = profile()
        runtime = SemanticContractRuntime(
            selected, {"sdk": DeltaProvider()}, body_codecs()
        )
        call = invocation(profile_digest=selected.digest)
        completion = await runtime.execute(call, input_bodies(call))
        retry = await runtime.execute(call, input_bodies(call))
        contextual = tuple(item for item in completion._bodies if item._context)
        retry_contextual = tuple(item for item in retry._bodies if item._context)
        target = next(item for item in contextual if item._context.purpose == "effect")
        retry_target = next(
            item for item in retry_contextual if item._context.purpose == "effect"
        )
        assert target._context is not None
        assert retry_target._context is not None
        publication_record = runtime._publication_records[completion]
        assert (
            publication_record.admitted_body_identities
            is not completion._publication_identities
        )
        assert all(
            retained is not exposed
            for retained, exposed in zip(
                publication_record.admitted_body_identities,
                completion._publication_identities,
            )
        )

        if poison == "context":
            alternate = next(
                item for item in contextual if item._coordinate != target._coordinate
            )
            object.__setattr__(target._context, "coordinate", alternate._coordinate)
        elif poison == "context_removal":
            object.__setattr__(target, "_context", None)
        elif poison == "epoch":
            object.__setattr__(
                target._context,
                "_validation_epoch",
                retry_target._context._validation_epoch,
            )
        elif poison == "execution_attempt":
            object.__setattr__(target._context, "_execution_attempt_token", object())
        elif poison == "outer_impact":
            object.__setattr__(
                target._context,
                "outer_effect_impacts",
                (SemanticImpactCoordinate("foreign", "definition", "foreign"),),
            )
        elif poison == "admitted_value":
            bodies = tuple(
                retry_target if item is target else item for item in completion._bodies
            )
            object.__setattr__(completion, "_bodies", bodies)
        elif poison in {
            "coherent_retry_registration",
            "coherent_identity_restamp",
        }:
            object.__setattr__(target, "_context", retry_target._context)
            object.__setattr__(
                target,
                "_admission_token",
                retry_target._admission_token,
            )
            if poison == "coherent_identity_restamp":
                target_index = completion._bodies.index(target)
                retry_index = retry._bodies.index(retry_target)
                identity = completion._publication_identities[target_index]
                retry_identity = retry._publication_identities[retry_index]
                for field in (
                    "context",
                    "admission_token",
                    "epoch",
                    "attempt_token",
                    "registration_snapshot",
                ):
                    object.__setattr__(identity, field, getattr(retry_identity, field))
        else:
            object.__setattr__(
                completion,
                "_publication_identities",
                retry._publication_identities,
            )

        assert not runtime.owns_completion(completion)
        with pytest.raises(ContractViolation):
            runtime.snapshot_completion(completion)

    asyncio.run(prove())


def test_provider_bodies_receive_exact_ordered_validation_context() -> None:
    async def prove() -> None:
        selected = profile()
        codecs = body_codecs()
        runtime = SemanticContractRuntime(selected, {"sdk": DeltaProvider()}, codecs)
        call = invocation(profile_digest=selected.digest)
        completion = await runtime.execute(call, input_bodies(call))
        assert runtime.owns_completion(completion)

        transition_codec = cast(JsonBodyCodec, codecs[TRANSITION])
        effect_codec = cast(JsonBodyCodec, codecs[EFFECT])
        output_codec = cast(JsonBodyCodec, codecs[OUTPUT])
        assert [value.purpose for value in transition_codec.contexts] == ["transition"]
        assert [value.purpose for value in effect_codec.contexts] == ["effect"]
        assert [value.purpose for value in output_codec.contexts] == ["output"]
        transition_context = transition_codec.contexts[0]
        effect_context = effect_codec.contexts[0]
        output_context = output_codec.contexts[0]
        assert transition_context.predecessor_value is None
        assert transition_context.candidate_value == {"sdk": "demo"}
        assert transition_context.target_package == call.target_package
        assert output_context.input_value("source") == {"source": "demo"}
        with pytest.raises(ContractViolation, match="input role"):
            output_context.input_value("absent")
        assert effect_context.transition_value == {"movement": "create"}
        assert output_context.effect_value == {"creates": ["client"]}
        assert (
            output_context.input_closure_digest
            == transition_context.input_closure_digest
        )

    asyncio.run(prove())


def test_validation_epoch_is_nominal_invocation_local_and_opaque() -> None:
    async def prove() -> None:
        selected = profile()
        codecs = body_codecs()
        runtime = SemanticContractRuntime(selected, {"sdk": DeltaProvider()}, codecs)
        first_call = invocation(profile_digest=selected.digest)
        first_completion = await runtime.execute(first_call, input_bodies(first_call))

        transition_codec = cast(JsonBodyCodec, codecs[TRANSITION])
        effect_codec = cast(JsonBodyCodec, codecs[EFFECT])
        transition_context = transition_codec.contexts[0]
        effect_context = effect_codec.contexts[0]
        assert transition_context.has_validation_epoch
        assert effect_context.has_validation_epoch
        assert transition_context._validation_epoch is effect_context._validation_epoch

        witness = object()
        transition_context.remember_validation_witness(
            "test.definition-closure",
            b"exact-codec-context",
            witness,
        )
        assert (
            effect_context.validation_witness(
                "test.definition-closure",
                b"exact-codec-context",
            )
            is witness
        )

        epoch = transition_context._validation_epoch
        assert epoch is not None
        with pytest.raises(TypeError, match="not copyable"):
            copy.copy(epoch)
        with pytest.raises(TypeError, match="not copyable"):
            copy.deepcopy(epoch)
        with pytest.raises(TypeError, match="not serializable"):
            pickle.dumps(epoch)

        second_call = first_call
        await runtime.execute(second_call, input_bodies(second_call))
        second_context = transition_codec.contexts[1]
        assert second_context._validation_epoch is not epoch
        assert second_context.invocation_digest == transition_context.invocation_digest
        assert (
            second_context.validation_witness(
                "test.definition-closure",
                b"exact-codec-context",
            )
            is None
        )
        second_epoch = second_context._validation_epoch
        object.__setattr__(second_context, "_validation_epoch", epoch)
        with pytest.raises(ContractViolation, match="execution attempt differs"):
            second_context.validation_witness(
                "test.definition-closure",
                b"exact-codec-context",
            )
        object.__setattr__(
            second_context,
            "_execution_attempt_token",
            transition_context._execution_attempt_token,
        )
        with pytest.raises(ContractViolation, match="not registered"):
            second_context.validation_witness(
                "test.definition-closure",
                b"exact-codec-context",
            )
        object.__setattr__(second_context, "_validation_epoch", second_epoch)

        other_codecs = body_codecs()
        other_runtime = SemanticContractRuntime(
            selected,
            {"sdk": DeltaProvider()},
            other_codecs,
        )
        third_call = replace(
            first_call,
            invocation_ref="sdk-invocation-third",
            idempotency_key="sdk-invocation-third",
        )
        await other_runtime.execute(third_call, input_bodies(third_call))
        foreign_context = cast(JsonBodyCodec, other_codecs[TRANSITION]).contexts[0]
        object.__setattr__(foreign_context, "_validation_epoch", epoch)
        with pytest.raises(ContractViolation, match="runtime differs"):
            foreign_context.validation_witness(
                "test.definition-closure",
                b"exact-codec-context",
            )

        shell = object.__new__(type(epoch))
        object.__setattr__(second_context, "_validation_epoch", shell)
        with pytest.raises((AttributeError, ContractViolation, TypeError)):
            second_context.validation_witness(
                "test.definition-closure",
                b"exact-codec-context",
            )

        object.__setattr__(
            transition_context,
            "coordinate",
            effect_context.coordinate,
        )
        assert not runtime.owns_completion(first_completion)

    asyncio.run(prove())


def test_context_bound_provider_body_cannot_fall_back_to_plain_codec() -> None:
    async def prove() -> None:
        selected = profile()
        codecs = body_codecs()
        codecs[TRANSITION] = ContextFreeJsonBodyCodec(TRANSITION)
        runtime = SemanticContractRuntime(selected, {"sdk": DeltaProvider()}, codecs)
        call = invocation(profile_digest=selected.digest)
        with pytest.raises(ContractViolation, match="contextual decoder"):
            await runtime.execute(call, input_bodies(call))

    asyncio.run(prove())


def test_runtime_rejects_missing_noncanonical_and_mutated_body_closures() -> None:
    async def prove() -> None:
        selected = profile()
        call = invocation(profile_digest=selected.digest)
        runtime = SemanticContractRuntime(
            selected, {"sdk": DeltaProvider()}, body_codecs()
        )
        with pytest.raises(ContractViolation, match="input body closure"):
            await runtime.execute(call, ())

        noncanonical = b'{"source": "demo"}'
        coordinate = body_coordinate("source", SOURCE, "parsed-1", noncanonical)
        changed_call = replace(call, inputs=(coordinate,))
        with pytest.raises(ContractViolation, match="not canonical JSON"):
            await runtime.execute(
                changed_call,
                (SemanticBody(coordinate, noncanonical),),
            )

        runtime = SemanticContractRuntime(
            selected, {"sdk": MissingBodyProvider()}, body_codecs()
        )
        with pytest.raises(ContractViolation, match="provider body closure"):
            await runtime.execute(call, input_bodies(call))

        runtime = SemanticContractRuntime(
            selected, {"sdk": MutatingInputProvider()}, body_codecs()
        )
        with pytest.raises(ContractViolation, match="value changed"):
            await runtime.execute(call, input_bodies(call))

    asyncio.run(prove())


def test_codec_binding_and_runtime_codec_restamps_fail() -> None:
    async def prove() -> None:
        selected = profile()
        call = invocation(profile_digest=selected.digest)
        changed = replace(
            call,
            body_codec_bindings=(
                replace(
                    call.body_codec_bindings[0],
                    implementation=SemanticImplementationCoordinate(
                        "foreign-codec", digest("1")
                    ),
                ),
                *call.body_codec_bindings[1:],
            ),
        )
        runtime = SemanticContractRuntime(
            selected, {"sdk": DeltaProvider()}, body_codecs()
        )
        with pytest.raises(ContractViolation, match="codec closure"):
            runtime._validate_invocation(changed)

        codecs = body_codecs()
        runtime = SemanticContractRuntime(selected, {"sdk": DeltaProvider()}, codecs)
        codec = cast(JsonBodyCodec, next(iter(codecs.values())))
        codec._implementation = SemanticImplementationCoordinate(
            "restamped-codec", digest("2")
        )
        with pytest.raises(ContractViolation, match="codec changed"):
            await runtime.execute(call, input_bodies(call))

    asyncio.run(prove())


def test_failure_and_cancellation_issue_no_completion() -> None:
    async def prove() -> None:
        selected = profile()
        call = invocation(profile_digest=selected.digest)
        with pytest.raises(ProviderTerminalFailure):
            await SemanticContractRuntime(
                selected, {"sdk": FailedProvider()}, body_codecs()
            ).execute(call, input_bodies(call))

        provider = WaitingProvider()
        runtime = SemanticContractRuntime(selected, {"sdk": provider}, body_codecs())
        task = asyncio.create_task(runtime.execute(call, input_bodies(call)))
        await provider.entered.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(prove())


def test_runtime_rejects_profile_and_invocation_restamp_races() -> None:
    async def prove() -> None:
        selected = profile()
        call = invocation(profile_digest=selected.digest)
        runtime = SemanticContractRuntime(
            selected, {"sdk": RestampingProvider()}, body_codecs()
        )
        with pytest.raises(ContractViolation, match="changed during"):
            await runtime.execute(call, input_bodies(call))

        selected = profile()
        runtime = SemanticContractRuntime(
            selected, {"sdk": DeltaProvider()}, body_codecs()
        )
        object.__setattr__(selected, "version", "2")
        with pytest.raises(ContractViolation, match="profile was restamped"):
            changed_call = invocation(profile_digest=selected.digest)
            await runtime.execute(changed_call, input_bodies(changed_call))

    asyncio.run(prove())


def test_completion_detects_post_execution_result_restamp() -> None:
    async def prove() -> None:
        selected = profile()
        runtime = SemanticContractRuntime(
            selected, {"sdk": DeltaProvider()}, body_codecs()
        )
        call = invocation(profile_digest=selected.digest)
        completion = await runtime.execute(call, input_bodies(call))
        result = completion.result
        assert result.effect is not None
        object.__setattr__(result.effect.effect_body, "digest", digest("1"))
        assert not runtime.owns_completion(completion)
        with pytest.raises(ContractViolation, match="restamped|bind"):
            _ = completion.result

    asyncio.run(prove())


def test_invocation_profile_and_output_substitutions_fail() -> None:
    selected = profile()
    runtime = SemanticContractRuntime(selected, {"sdk": DeltaProvider()}, body_codecs())
    with pytest.raises(ContractViolation, match="different profile"):
        runtime._validate_invocation(invocation())
    with pytest.raises(ContractViolation, match="undeclared terminal"):
        runtime._validate_invocation(
            replace(
                invocation(profile_digest=selected.digest),
                requested_output_roles=("other",),
            )
        )
