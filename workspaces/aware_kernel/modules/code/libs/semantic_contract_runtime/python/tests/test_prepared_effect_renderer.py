from __future__ import annotations

import json
from dataclasses import replace

import pytest

from aware_code_semantic_contract_runtime import (
    ContentDigest,
    ContractViolation,
    SemanticConfigurationCoordinate,
    SemanticContractRef,
    SemanticImplementationCoordinate,
    SemanticPackageCoordinate,
    SemanticValueCoordinate,
    TypedEmptyCoordinate,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.prepared_effect_renderer import (
    PreparedEffectRendererCoverage,
    PreparedEffectRendererDeclaration,
    PreparedEffectRendererExecution,
    PreparedEffectRendererHost,
    PreparedEffectRendererInput,
    PreparedEffectRendererProduct,
    PreparedEffectRequirement,
    close_prepared_effect_renderer_registration,
    decode_prepared_effect_renderer_coverage,
    decode_prepared_effect_renderer_input,
    encode_prepared_effect_renderer_coverage,
    encode_prepared_effect_renderer_input,
    execute_registered_prepared_effect_renderer,
    register_prepared_effect_renderer,
    validate_prepared_effect_renderer_coverage,
)
from aware_code_semantic_contract_runtime.runtime import SemanticBody


def _digest(label: str) -> ContentDigest:
    return ContentDigest.of_bytes(label.encode())


def _contract(label: str) -> SemanticContractRef:
    return SemanticContractRef(f"example.{label}.v1", "1", _digest(label + "-schema"))


def _body(role: str, label: str, contract: SemanticContractRef | None = None) -> SemanticBody:
    payload = canonical_json_bytes({"label": label})
    return SemanticBody(
        SemanticValueCoordinate(
            role,
            contract or _contract(label),
            f"cas://{label}",
            ContentDigest.of_bytes(payload),
            len(payload),
        ),
        payload,
    )


_PLAN_CONTRACT = _contract("sdk-plan")
_DELTA_CONTRACT = _contract("package-delta")
_CONFIGURATION = SemanticConfigurationCoordinate(
    "example.sdk.python.v1", _digest("configuration")
)
_DECLARATION = PreparedEffectRendererDeclaration(
    "example.python.sdk",
    "example.sdk.v1",
    _digest("product-profile"),
    "example.python.v1",
    _digest("language-profile"),
    SemanticImplementationCoordinate("example-python@1/sdk", _digest("implementation")),
    _CONFIGURATION,
    _PLAN_CONTRACT,
    _DELTA_CONTRACT,
)


def _renderer_input() -> tuple[PreparedEffectRendererInput, tuple[SemanticBody, ...]]:
    result = _body("package_result", "result")
    manifest = _body("manifest", "manifest")
    effect = _body("effect", "effect")
    requirements = _body("requirements", "requirements")
    plan = _body("target_plan", "plan", _PLAN_CONTRACT)
    empty = TypedEmptyCoordinate(_contract("predecessor"))
    obligations = tuple(
        sorted(
            (
                PreparedEffectRequirement("definition_catalog", "api://goal"),
                PreparedEffectRequirement("view_contract", "api://goal/view/main"),
            ),
            key=lambda item: canonical_json_bytes(item.to_wire()),
        )
    )
    value = PreparedEffectRendererInput.create(
        package=SemanticPackageCoordinate("goal-service-api", "api", _digest("manifest")),
        package_result=result.coordinate,
        manifest=manifest.coordinate,
        transition=empty,
        effect=effect.coordinate,
        historical_predecessor=empty,
        requirements=requirements.coordinate,
        r1_profile_ref="aware.api.renderer.sdk-client.v1",
        r1_profile_digest=_digest("r1"),
        configuration=_CONFIGURATION,
        output_namespace="python/aware_goal_service_api",
        target_ref="goal-service-api/python/sdk",
        target_plan=plan.coordinate,
        prior_output_state=empty,
        required_obligations=obligations,
        invocation_digest=_digest("invocation"),
        result_digest=_digest("semantic-result"),
        completion_digest=_digest("completion"),
    )
    bodies = tuple(
        sorted(
            (result, manifest, effect, requirements, plan),
            key=lambda item: canonical_json_bytes(item.coordinate.to_wire()),
        )
    )
    return value, bodies


def _product(renderer_input: PreparedEffectRendererInput) -> PreparedEffectRendererProduct:
    delta = _body("delta", "delta", _DELTA_CONTRACT)
    output = _body("sdk_product", "sdk-product")
    coverage = PreparedEffectRendererCoverage.create(
        requirements_digest=renderer_input.requirements.digest,
        covered_obligations=renderer_input.required_obligations,
        target_ref=renderer_input.target_ref,
        target_plan_digest=renderer_input.target_plan.digest,
        product_profile_ref=_DECLARATION.product_profile_ref,
        product_profile_digest=_DECLARATION.product_profile_digest,
        language_profile_ref=_DECLARATION.language_profile_ref,
        language_profile_digest=_DECLARATION.language_profile_digest,
        configuration=_DECLARATION.configuration,
        invocation_digest=renderer_input.invocation_digest,
        result_digest=renderer_input.result_digest,
        completion_digest=renderer_input.completion_digest,
        delta=delta.coordinate,
        outputs=(output.coordinate,),
    )
    return PreparedEffectRendererProduct(delta, (output,), coverage)


class _Validator:
    def __init__(self, admission: object, operation: object) -> None:
        self.admission = admission
        self.operation = operation
        self.live = True
        self.calls = 0

    def validate_prepared_effect_renderer_input(
        self,
        input_admission: object,
        *,
        expected: PreparedEffectRendererExecution,
    ) -> None:
        self.calls += 1
        if (
            not self.live
            or input_admission is not self.admission
            or expected.operation_identity is not self.operation
        ):
            raise ContractViolation("renderer input unavailable")


def _execution(operation: object, use_ref: str = "render-use-1") -> PreparedEffectRendererExecution:
    renderer_input, bodies = _renderer_input()
    return PreparedEffectRendererExecution(use_ref, operation, renderer_input, bodies)


def test_input_and_coverage_codecs_are_strict_and_canonical():
    renderer_input, _ = _renderer_input()
    input_body = encode_prepared_effect_renderer_input(renderer_input)
    assert decode_prepared_effect_renderer_input(input_body) == renderer_input
    coverage = _product(renderer_input).coverage
    coverage_body = encode_prepared_effect_renderer_coverage(coverage)
    assert decode_prepared_effect_renderer_coverage(coverage_body) == coverage
    with pytest.raises(ContractViolation, match="noncanonical"):
        decode_prepared_effect_renderer_input(input_body + b" ")
    with pytest.raises(ContractViolation, match="digest mismatched"):
        replace(renderer_input, input_digest=_digest("foreign"))


def test_input_and_coverage_codecs_reject_missing_fields_as_contract_failures():
    renderer_input, _ = _renderer_input()
    input_wire = json.loads(encode_prepared_effect_renderer_input(renderer_input))
    del input_wire["package_result"]
    with pytest.raises(ContractViolation, match="input fields differ"):
        decode_prepared_effect_renderer_input(canonical_json_bytes(input_wire))

    coverage = _product(renderer_input).coverage
    coverage_wire = json.loads(encode_prepared_effect_renderer_coverage(coverage))
    del coverage_wire["outputs"]
    with pytest.raises(ContractViolation, match="coverage fields differ"):
        decode_prepared_effect_renderer_coverage(canonical_json_bytes(coverage_wire))


@pytest.mark.asyncio
async def test_original_validator_wraps_renderer_and_use_is_single_shot():
    host = PreparedEffectRendererHost()
    admission, operation = object(), object()
    validator = _Validator(admission, operation)
    executions = []

    async def render(actual_admission, expected):
        executions.extend((actual_admission, expected.operation_identity))
        return _product(expected.renderer_input)

    registration = register_prepared_effect_renderer(
        host,
        declaration=_DECLARATION,
        renderer=render,
        validator=validator,
        validator_entrance=validator.validate_prepared_effect_renderer_input,
    )
    execution = _execution(operation)
    result = await execute_registered_prepared_effect_renderer(
        host, registration, input_admission=admission, expected=execution
    )
    assert result == _product(execution.renderer_input)
    assert executions == [admission, operation]
    assert validator.calls == 2
    with pytest.raises(ContractViolation, match="already consumed"):
        await execute_registered_prepared_effect_renderer(
            host, registration, input_admission=admission, expected=execution
        )


@pytest.mark.asyncio
async def test_post_validation_rejects_revocation_and_consumes_use():
    host = PreparedEffectRendererHost()
    admission, operation = object(), object()
    validator = _Validator(admission, operation)

    def render(_admission, expected):
        validator.live = False
        return _product(expected.renderer_input)

    registration = register_prepared_effect_renderer(
        host,
        declaration=_DECLARATION,
        renderer=render,
        validator=validator,
        validator_entrance=validator.validate_prepared_effect_renderer_input,
    )
    execution = _execution(operation)
    with pytest.raises(ContractViolation, match="unavailable"):
        await execute_registered_prepared_effect_renderer(
            host, registration, input_admission=admission, expected=execution
        )
    with pytest.raises(ContractViolation, match="already consumed"):
        await execute_registered_prepared_effect_renderer(
            host, registration, input_admission=admission, expected=execution
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field",
    [
        "requirements_digest",
        "covered_obligations",
        "target_ref",
        "target_plan_digest",
        "product_profile_digest",
        "language_profile_digest",
        "configuration",
        "invocation_digest",
        "result_digest",
        "completion_digest",
        "delta",
    ],
)
async def test_coverage_substitution_rejects(field):
    renderer_input, _ = _renderer_input()
    coverage = _product(renderer_input).coverage
    replacement = _digest("foreign")
    if field == "covered_obligations":
        replacement = ()
    elif field == "target_ref":
        replacement = "foreign-target"
    elif field == "configuration":
        replacement = SemanticConfigurationCoordinate("foreign", _digest("foreign"))
    elif field == "delta":
        replacement = replace(coverage.delta, contract=_contract("foreign-delta"))
    values = {
        name: getattr(coverage, name)
        for name in coverage.__dataclass_fields__
        if name != "coverage_digest"
    }
    values[field] = replacement
    poisoned = PreparedEffectRendererCoverage.create(
        **values,
    )
    # A structurally valid restamp still fails admitted execution correspondence.
    with pytest.raises(ContractViolation):
        validate_prepared_effect_renderer_coverage(
            poisoned, renderer_input=renderer_input, declaration=_DECLARATION
        )


def test_execution_requires_complete_exact_body_closure():
    renderer_input, bodies = _renderer_input()
    with pytest.raises(ContractViolation, match="incomplete or extra"):
        PreparedEffectRendererExecution("use", object(), renderer_input, bodies[:-1])
    extra = _body("extra", "extra")
    with pytest.raises(ContractViolation, match="incomplete or extra"):
        PreparedEffectRendererExecution(
            "use",
            object(),
            renderer_input,
            tuple(
                sorted(
                    (*bodies, extra),
                    key=lambda item: canonical_json_bytes(item.coordinate.to_wire()),
                )
            ),
        )


def test_registration_requires_original_validator_and_close_revokes():
    host = PreparedEffectRendererHost()
    admission, operation = object(), object()
    validator = _Validator(admission, operation)
    renderer = lambda _admission, expected: _product(expected.renderer_input)
    with pytest.raises(ContractViolation, match="original renderer"):
        register_prepared_effect_renderer(
            host,
            declaration=_DECLARATION,
            renderer=renderer,
            validator=validator,
            validator_entrance=lambda *_args, **_kwargs: None,
        )
    registration = register_prepared_effect_renderer(
        host,
        declaration=_DECLARATION,
        renderer=renderer,
        validator=validator,
        validator_entrance=validator.validate_prepared_effect_renderer_input,
    )
    close_prepared_effect_renderer_registration(host, registration)
    with pytest.raises(ContractViolation, match="unavailable"):
        close_prepared_effect_renderer_registration(host, registration)
