"""Fixed portable profile binding, not original product or host admission."""

from dataclasses import FrozenInstanceError, replace

import pytest
from aware_code_semantic_contract_runtime import (
    ContractViolation,
    SemanticBodyCodecBinding,
    SemanticContractRuntime,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.dependency_input_codec import (
    SEMANTIC_DEPENDENCY_PRODUCT_INPUT_REF as INPUT,
)
from aware_code_semantic_contract_runtime.dependency_input_codec import (
    SemanticDependencyProductInputCodec,
)
from aware_code_semantic_contract_runtime.profile_dependency_codec import (
    ProfileBoundDependencyProductInputCodec,
)
from test_contracts import SOURCE
from test_dependency_input_execution import execution
from test_profile_runtime import body_codecs


def pair():
    source_runtime, provider, call, body, value = execution()
    source = source_runtime.profile
    consumer = replace(source, profile_ref="test.authority-consumer")
    codec = ProfileBoundDependencyProductInputCodec(
        source_profile=source, consumer_profile=consumer
    )
    codecs = body_codecs()
    del codecs[SOURCE]
    codecs[INPUT] = codec
    call = replace(
        call,
        profile_ref=consumer.profile_ref,
        profile_digest=consumer.digest,
        body_codec_bindings=tuple(
            SemanticBodyCodecBinding(ref, item.implementation)
            for ref, item in sorted(
                codecs.items(), key=lambda item: canonical_json_bytes(item[0].to_wire())
            )
        ),
    )
    runtime = SemanticContractRuntime(consumer, {"sdk": provider}, codecs)
    return runtime, provider, call, body, value, codec, source, consumer


@pytest.mark.asyncio
async def test_original_source_profile_and_bytes_survive_consumer_execution():
    runtime, provider, call, body, value, codec, source, _ = pair()
    wire = codec.encode(value)
    assert wire == SemanticDependencyProductInputCodec().encode(value)
    assert codec.decode(wire) == value
    completion = await runtime.execute(call, (body,))
    assert runtime.owns_completion(completion)
    seen = provider.seen[0].inputs[0].value
    assert seen.demand_set.profile_ref == source.profile_ref
    assert seen.demand_set.profile_digest == source.digest
    assert codec.encode(seen) == body.canonical_body
    with pytest.raises(ContractViolation):
        SemanticDependencyProductInputCodec().validate_invocation(value, call)


@pytest.mark.parametrize(
    "change",
    [
        "source_ref",
        "source_digest",
        "consumer_ref",
        "consumer_digest",
        "package",
        "dependencies",
        "operation",
    ],
)
def test_wrong_profile_pair_or_existing_invocation_correspondence_rejects(change):
    _, _, call, _, value, codec, source, consumer = pair()
    if change == "source_ref":
        codec = ProfileBoundDependencyProductInputCodec(
            source_profile=replace(source, profile_ref="foreign"),
            consumer_profile=consumer,
        )
    elif change == "source_digest":
        codec = ProfileBoundDependencyProductInputCodec(
            source_profile=replace(source, version="2"), consumer_profile=consumer
        )
    elif change == "consumer_ref":
        call = replace(call, profile_ref="foreign")
    elif change == "consumer_digest":
        call = replace(call, profile_digest=source.digest)
    elif change == "package":
        call = replace(
            call, target_package=replace(call.target_package, package_ref="foreign")
        )
    elif change == "dependencies":
        call = replace(call, dependencies=())
    else:
        call = replace(call, operation_kind="foreign")
    with pytest.raises(ContractViolation):
        codec.validate_invocation(value, call)


@pytest.mark.asyncio
async def test_reconfigured_codec_cannot_use_old_invocation_binding():
    _, provider, call, body, _, _, source, consumer = pair()
    changed = ProfileBoundDependencyProductInputCodec(
        source_profile=replace(source, version="2"), consumer_profile=consumer
    )
    codecs = body_codecs()
    del codecs[SOURCE]
    codecs[INPUT] = changed
    runtime = SemanticContractRuntime(consumer, {"sdk": provider}, codecs)
    with pytest.raises(ContractViolation):
        await runtime.execute(call, (body,))
    assert provider.seen == []


def test_configuration_is_detached_and_implementation_binds_both_profiles():
    _, _, call, _, value, codec, source, consumer = pair()
    implementation = codec.implementation
    other = ProfileBoundDependencyProductInputCodec(
        source_profile=source, consumer_profile=replace(consumer, version="2")
    )
    assert other.implementation != implementation
    object.__setattr__(source, "profile_ref", "changed-after-construction")
    codec.validate_invocation(value, call)
    assert codec.implementation == implementation
    with pytest.raises(FrozenInstanceError):
        codec._profiles = ("foreign",) * 4
    object.__setattr__(codec, "_profiles", ("foreign",) * 4)
    with pytest.raises(ContractViolation):
        codec.encode(value)


def test_exact_distinct_profiles_required():
    *_, source, consumer = pair()
    with pytest.raises(TypeError):
        ProfileBoundDependencyProductInputCodec(
            source_profile=object(), consumer_profile=consumer
        )
    with pytest.raises(ContractViolation):
        ProfileBoundDependencyProductInputCodec(
            source_profile=source, consumer_profile=source
        )
