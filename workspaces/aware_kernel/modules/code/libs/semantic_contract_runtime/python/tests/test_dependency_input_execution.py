from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime import (
    ConsumedRoleDeclaration,
    ContractViolation,
    ProfileInputDeclaration,
    SemanticBodyCodecBinding,
    SemanticConfigurationCoordinate,
    SemanticContractRuntime,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.dependency_input_codec import (
    SEMANTIC_DEPENDENCY_PRODUCT_INPUT_REF as INPUT,
)
from aware_code_semantic_contract_runtime.dependency_input_codec import (
    SemanticDependencyProductInputCodec,
    dependency_product_input_body,
)
from aware_code_semantic_contract_runtime.materialization_planning import (
    SemanticDependencyDemandSet,
)
from test_contracts import SOURCE, declaration, invocation
from test_dependency_inputs import product_input
from test_profile_runtime import DeltaProvider, body_codecs, profile


def execution(codec=None):
    provider_declaration = replace(
        declaration(), consumed_roles=(ConsumedRoleDeclaration("source", (INPUT,)),)
    )
    selected = replace(
        profile(),
        inputs=(ProfileInputDeclaration("source", INPUT),),
        providers=(provider_declaration,),
    )
    value = product_input()
    demand = value.demand_set
    demands = SemanticDependencyDemandSet.create(
        package=value.package,
        intent=value.intent,
        profile_ref=selected.profile_ref,
        profile_digest=selected.digest,
        contract_profile_binding_digest=demand.contract_profile_binding_digest,
        planner_implementation_ref=demand.planner_implementation_ref,
        planner_implementation_digest=demand.planner_implementation_digest,
        planner_configuration=SemanticConfigurationCoordinate(
            demand.planner_configuration_ref, demand.planner_configuration_digest
        ),
        demands=demand.demands,
    )
    value = replace(value, demand_set=demands)
    body = dependency_product_input_body(value, role="source")
    codecs = body_codecs()
    del codecs[SOURCE]
    codecs[INPUT] = codec or SemanticDependencyProductInputCodec()
    call = replace(
        invocation(profile_digest=selected.digest),
        target_package=value.package,
        inputs=(body.coordinate,),
        dependencies=tuple(
            sorted(
                {p.coordinate for p in value.products},
                key=lambda p: canonical_json_bytes(p.to_wire()),
            )
        ),
        body_codec_bindings=tuple(
            SemanticBodyCodecBinding(c, codecs[c].implementation)
            for c in sorted(codecs, key=lambda c: canonical_json_bytes(c.to_wire()))
        ),
    )
    provider = DeltaProvider(provider_declaration)
    return (
        SemanticContractRuntime(selected, {"sdk": provider}, codecs),
        provider,
        call,
        body,
        value,
    )


@pytest.mark.asyncio
async def test_registered_codec_delivers_neutral_input_through_existing_runtime():
    runtime, provider, call, body, value = execution()
    completion = await runtime.execute(call, (body,))
    assert runtime.owns_completion(completion)
    assert provider.seen[0].inputs[0].value == value


@pytest.mark.asyncio
@pytest.mark.parametrize("change", ["package", "dependencies", "profile"])
async def test_invocation_mismatch_rejected_before_provider(change):
    runtime, provider, call, body, _ = execution()
    if change == "package":
        call = replace(
            call, target_package=replace(call.target_package, package_ref="foreign")
        )
    elif change == "dependencies":
        call = replace(call, dependencies=())
    else:
        # Structurally valid input for another profile, bound by valid body digest.
        body = dependency_product_input_body(product_input(), role="source")
        call = replace(call, inputs=(body.coordinate,))
    with pytest.raises(ContractViolation, match="differs from invocation"):
        await runtime.execute(call, (body,))
    assert provider.seen == []


@pytest.mark.asyncio
@pytest.mark.parametrize("change", ["value", "invocation", "return"])
async def test_validator_cannot_mutate_inputs_or_return_a_replacement(change):
    class MutatingCodec(SemanticDependencyProductInputCodec):
        def validate_invocation(self, value, invocation):
            super().validate_invocation(value, invocation)
            if change == "value":
                object.__setattr__(
                    value, "source_identity_digest", value.package.manifest_digest
                )
            elif change == "invocation":
                object.__setattr__(invocation, "invocation_ref", "changed")
            else:
                return value

    runtime, provider, call, body, _ = execution(MutatingCodec())
    with pytest.raises(ContractViolation, match="validator changed its inputs"):
        await runtime.execute(call, (body,))
    assert provider.seen == []
