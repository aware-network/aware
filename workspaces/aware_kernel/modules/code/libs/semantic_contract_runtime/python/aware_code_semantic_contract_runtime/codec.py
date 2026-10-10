from __future__ import annotations

import json
from collections.abc import Callable
from typing import Protocol

from .contracts import (
    ConsumedRoleDeclaration,
    ContentDigest,
    ContractViolation,
    PreparedSemanticEffectEnvelope,
    ProducedRoleDeclaration,
    ProviderExecutionBinding,
    SemanticBodyCodecBinding,
    SemanticConfigurationCoordinate,
    SemanticContractInvocation,
    SemanticContractProviderDeclaration,
    SemanticContractRef,
    SemanticContractResult,
    SemanticDependencyCoordinate,
    SemanticImpactCoordinate,
    SemanticImplementationCoordinate,
    SemanticOutputEnvelope,
    SemanticPackageCoordinate,
    SemanticTransitionEnvelope,
    SemanticValueCoordinate,
    TerminalStatus,
    TypedEmptyCoordinate,
    WireObject,
    canonical_json_text,
    predecessor_wire,
)
from .profile import (
    ProfileInputDeclaration,
    ProfileStepDeclaration,
    RoleBinding,
    SemanticContractProfileDeclaration,
)


def _reject_constant(value: str) -> None:
    raise ContractViolation(f"noncanonical JSON constant {value}")


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ContractViolation(f"duplicate JSON key {key}")
        result[key] = value
    return result


def _load(text: object) -> WireObject:
    if type(text) is not str:
        raise TypeError("canonical payload must be exact str")
    try:
        value = json.loads(
            text, object_pairs_hook=_pairs, parse_constant=_reject_constant
        )
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ContractViolation("invalid canonical JSON") from error
    return _object(value, "root")


def _object(value: object, path: str) -> WireObject:
    if type(value) is not dict:
        raise TypeError(f"{path} must be exact object")
    if any(type(key) is not str for key in value):
        raise TypeError(f"{path} keys must be exact strings")
    return value


def _list(value: object, path: str) -> list[object]:
    if type(value) is not list:
        raise TypeError(f"{path} must be exact list")
    return value


def _string(value: object, path: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{path} must be exact string")
    return value


def _integer(value: object, path: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{path} must be exact integer")
    return value


def _boolean(value: object, path: str) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{path} must be exact boolean")
    return value


def _nullable[T](
    value: object, decoder: Callable[[object, str], T], path: str
) -> T | None:
    return None if value is None else decoder(value, path)


def _keys(value: WireObject, expected: set[str], path: str) -> None:
    if set(value) != expected:
        raise ContractViolation(
            f"{path} field set differs: expected {sorted(expected)}, got {sorted(value)}"
        )


def _schema(value: WireObject, expected: str, path: str) -> None:
    if _string(value["schema"], f"{path}.schema") != expected:
        raise ContractViolation(f"{path} has an unknown schema")


def _digest(value: object, path: str) -> ContentDigest:
    return ContentDigest.of_wire(value, path)


class _DigestValue(Protocol):
    @property
    def digest(self) -> ContentDigest: ...

    def to_wire(self) -> WireObject: ...


def _verify_digest(value: _DigestValue, supplied: object, path: str) -> None:
    if _digest(supplied, f"{path}.digest") != value.digest:
        raise ContractViolation(f"{path} digest differs from canonical derivation")


def _contract(value: object, path: str) -> SemanticContractRef:
    root = _object(value, path)
    _keys(root, {"key", "schema_digest", "version"}, path)
    return SemanticContractRef(
        key=_string(root["key"], f"{path}.key"),
        version=_string(root["version"], f"{path}.version"),
        schema_digest=_digest(root["schema_digest"], f"{path}.schema_digest"),
    )


def _package(value: object, path: str) -> SemanticPackageCoordinate:
    root = _object(value, path)
    _keys(root, {"manifest_digest", "package_kind", "package_ref"}, path)
    return SemanticPackageCoordinate(
        package_ref=_string(root["package_ref"], f"{path}.package_ref"),
        package_kind=_string(root["package_kind"], f"{path}.package_kind"),
        manifest_digest=_digest(root["manifest_digest"], f"{path}.manifest_digest"),
    )


def _value(value: object, path: str) -> SemanticValueCoordinate:
    root = _object(value, path)
    _keys(root, {"contract", "digest", "role", "size_bytes", "value_ref"}, path)
    return SemanticValueCoordinate(
        role=_string(root["role"], f"{path}.role"),
        contract=_contract(root["contract"], f"{path}.contract"),
        value_ref=_string(root["value_ref"], f"{path}.value_ref"),
        digest=_digest(root["digest"], f"{path}.digest"),
        size_bytes=_integer(root["size_bytes"], f"{path}.size_bytes"),
    )


def _implementation(value: object, path: str) -> SemanticImplementationCoordinate:
    root = _object(value, path)
    _keys(root, {"closure_digest", "implementation_ref"}, path)
    return SemanticImplementationCoordinate(
        implementation_ref=_string(
            root["implementation_ref"], f"{path}.implementation_ref"
        ),
        closure_digest=_digest(root["closure_digest"], f"{path}.closure_digest"),
    )


def _configuration(value: object, path: str) -> SemanticConfigurationCoordinate:
    root = _object(value, path)
    _keys(root, {"configuration_ref", "digest"}, path)
    return SemanticConfigurationCoordinate(
        configuration_ref=_string(
            root["configuration_ref"], f"{path}.configuration_ref"
        ),
        digest=_digest(root["digest"], f"{path}.digest"),
    )


def _dependency(value: object, path: str) -> SemanticDependencyCoordinate:
    root = _object(value, path)
    _keys(root, {"package", "result_contract", "result_digest", "result_ref"}, path)
    return SemanticDependencyCoordinate(
        package=_package(root["package"], f"{path}.package"),
        result_contract=_contract(root["result_contract"], f"{path}.result_contract"),
        result_ref=_string(root["result_ref"], f"{path}.result_ref"),
        result_digest=_digest(root["result_digest"], f"{path}.result_digest"),
    )


def _predecessor(
    value: object, path: str
) -> TypedEmptyCoordinate | SemanticValueCoordinate:
    root = _object(value, path)
    if root.get("kind") == "typed_empty":
        _keys(root, {"contract", "kind"}, path)
        return TypedEmptyCoordinate(_contract(root["contract"], f"{path}.contract"))
    return _value(root, path)


def _impact(value: object, path: str) -> SemanticImpactCoordinate:
    root = _object(value, path)
    _keys(root, {"identifier", "kind", "namespace"}, path)
    return SemanticImpactCoordinate(
        namespace=_string(root["namespace"], f"{path}.namespace"),
        kind=_string(root["kind"], f"{path}.kind"),
        identifier=_string(root["identifier"], f"{path}.identifier"),
    )


def _consumed(value: object, path: str) -> ConsumedRoleDeclaration:
    root = _object(value, path)
    _keys(root, {"accepted_contracts", "required", "role"}, path)
    return ConsumedRoleDeclaration(
        role=_string(root["role"], f"{path}.role"),
        accepted_contracts=tuple(
            _contract(item, f"{path}.accepted_contracts[{index}]")
            for index, item in enumerate(
                _list(root["accepted_contracts"], f"{path}.accepted_contracts")
            )
        ),
        required=_boolean(root["required"], f"{path}.required"),
    )


def _produced(value: object, path: str) -> ProducedRoleDeclaration:
    root = _object(value, path)
    _keys(root, {"contract", "role"}, path)
    return ProducedRoleDeclaration(
        role=_string(root["role"], f"{path}.role"),
        contract=_contract(root["contract"], f"{path}.contract"),
    )


def _provider(value: object, path: str) -> SemanticContractProviderDeclaration:
    root = _object(value, path)
    _keys(
        root,
        {
            "allows_typed_empty",
            "consumed_roles",
            "counter_keys",
            "digest",
            "effect_contract",
            "effect_role",
            "operation_kinds",
            "output_roles",
            "package_kinds",
            "predecessor_required",
            "provider_contract",
            "provider_key",
            "result_role",
            "schema",
            "terminal_statuses",
            "transition_contract",
        },
        path,
    )
    _schema(root, "aware.code.semantic-provider-declaration.v1", path)
    result = SemanticContractProviderDeclaration(
        provider_key=_string(root["provider_key"], f"{path}.provider_key"),
        provider_contract=_contract(
            root["provider_contract"], f"{path}.provider_contract"
        ),
        package_kinds=tuple(
            _string(item, f"{path}.package_kinds[{index}]")
            for index, item in enumerate(
                _list(root["package_kinds"], f"{path}.package_kinds")
            )
        ),
        operation_kinds=tuple(
            _string(item, f"{path}.operation_kinds[{index}]")
            for index, item in enumerate(
                _list(root["operation_kinds"], f"{path}.operation_kinds")
            )
        ),
        consumed_roles=tuple(
            _consumed(item, f"{path}.consumed_roles[{index}]")
            for index, item in enumerate(
                _list(root["consumed_roles"], f"{path}.consumed_roles")
            )
        ),
        result_role=_produced(root["result_role"], f"{path}.result_role"),
        transition_contract=_contract(
            root["transition_contract"], f"{path}.transition_contract"
        ),
        effect_role=_produced(root["effect_role"], f"{path}.effect_role"),
        effect_contract=_contract(root["effect_contract"], f"{path}.effect_contract"),
        output_roles=tuple(
            _produced(item, f"{path}.output_roles[{index}]")
            for index, item in enumerate(
                _list(root["output_roles"], f"{path}.output_roles")
            )
        ),
        allows_typed_empty=_boolean(
            root["allows_typed_empty"], f"{path}.allows_typed_empty"
        ),
        predecessor_required=_boolean(
            root["predecessor_required"], f"{path}.predecessor_required"
        ),
        terminal_statuses=tuple(
            _string(item, f"{path}.terminal_statuses[{index}]")
            for index, item in enumerate(
                _list(root["terminal_statuses"], f"{path}.terminal_statuses")
            )
        ),
        counter_keys=tuple(
            _string(item, f"{path}.counter_keys[{index}]")
            for index, item in enumerate(
                _list(root["counter_keys"], f"{path}.counter_keys")
            )
        ),
    )
    _verify_digest(result, root["digest"], path)
    return result


def _binding(value: object, path: str) -> ProviderExecutionBinding:
    root = _object(value, path)
    _keys(root, {"configuration", "implementation", "provider_key"}, path)
    return ProviderExecutionBinding(
        provider_key=_string(root["provider_key"], f"{path}.provider_key"),
        implementation=_implementation(
            root["implementation"], f"{path}.implementation"
        ),
        configuration=_configuration(root["configuration"], f"{path}.configuration"),
    )


def _codec_binding(value: object, path: str) -> SemanticBodyCodecBinding:
    root = _object(value, path)
    _keys(root, {"contract", "implementation"}, path)
    return SemanticBodyCodecBinding(
        contract=_contract(root["contract"], f"{path}.contract"),
        implementation=_implementation(
            root["implementation"], f"{path}.implementation"
        ),
    )


def _invocation(value: object, path: str) -> SemanticContractInvocation:
    root = _object(value, path)
    _keys(
        root,
        {
            "body_codec_bindings",
            "dependencies",
            "digest",
            "idempotency_key",
            "inputs",
            "invocation_ref",
            "operation_kind",
            "predecessor",
            "profile_digest",
            "profile_ref",
            "provider_bindings",
            "requested_output_roles",
            "schema",
            "target_package",
        },
        path,
    )
    _schema(root, "aware.code.semantic-contract-invocation.v1", path)
    result = SemanticContractInvocation(
        invocation_ref=_string(root["invocation_ref"], f"{path}.invocation_ref"),
        idempotency_key=_string(root["idempotency_key"], f"{path}.idempotency_key"),
        profile_ref=_string(root["profile_ref"], f"{path}.profile_ref"),
        profile_digest=_digest(root["profile_digest"], f"{path}.profile_digest"),
        target_package=_package(root["target_package"], f"{path}.target_package"),
        operation_kind=_string(root["operation_kind"], f"{path}.operation_kind"),
        inputs=tuple(
            _value(item, f"{path}.inputs[{index}]")
            for index, item in enumerate(_list(root["inputs"], f"{path}.inputs"))
        ),
        predecessor=_predecessor(root["predecessor"], f"{path}.predecessor"),
        dependencies=tuple(
            _dependency(item, f"{path}.dependencies[{index}]")
            for index, item in enumerate(
                _list(root["dependencies"], f"{path}.dependencies")
            )
        ),
        body_codec_bindings=tuple(
            _codec_binding(item, f"{path}.body_codec_bindings[{index}]")
            for index, item in enumerate(
                _list(root["body_codec_bindings"], f"{path}.body_codec_bindings")
            )
        ),
        provider_bindings=tuple(
            _binding(item, f"{path}.provider_bindings[{index}]")
            for index, item in enumerate(
                _list(root["provider_bindings"], f"{path}.provider_bindings")
            )
        ),
        requested_output_roles=tuple(
            _string(item, f"{path}.requested_output_roles[{index}]")
            for index, item in enumerate(
                _list(root["requested_output_roles"], f"{path}.requested_output_roles")
            )
        ),
    )
    _verify_digest(result, root["digest"], path)
    return result


def _transition(value: object, path: str) -> SemanticTransitionEnvelope:
    root = _object(value, path)
    _keys(
        root,
        {
            "digest",
            "impacts",
            "input_closure_digest",
            "predecessor",
            "provider_key",
            "result",
            "result_contract",
            "schema",
            "transition_body",
            "transition_contract",
        },
        path,
    )
    _schema(root, "aware.code.semantic-transition-envelope.v1", path)
    result = SemanticTransitionEnvelope(
        provider_key=_string(root["provider_key"], f"{path}.provider_key"),
        result_contract=_contract(root["result_contract"], f"{path}.result_contract"),
        transition_contract=_contract(
            root["transition_contract"], f"{path}.transition_contract"
        ),
        predecessor=_predecessor(root["predecessor"], f"{path}.predecessor"),
        result=_value(root["result"], f"{path}.result"),
        transition_body=_value(root["transition_body"], f"{path}.transition_body"),
        impacts=tuple(
            _impact(item, f"{path}.impacts[{index}]")
            for index, item in enumerate(_list(root["impacts"], f"{path}.impacts"))
        ),
        input_closure_digest=_digest(
            root["input_closure_digest"], f"{path}.input_closure_digest"
        ),
    )
    _verify_digest(result, root["digest"], path)
    return result


def _effect(value: object, path: str) -> PreparedSemanticEffectEnvelope:
    root = _object(value, path)
    _keys(
        root,
        {
            "base_state",
            "candidate_state",
            "digest",
            "effect_body",
            "effect_contract",
            "impacts",
            "provider_key",
            "renderer_inputs",
            "schema",
            "transition_digest",
            "work_counters",
        },
        path,
    )
    _schema(root, "aware.code.prepared-semantic-effect-envelope.v1", path)
    counters: list[tuple[str, int]] = []
    for index, item in enumerate(_list(root["work_counters"], f"{path}.work_counters")):
        pair = _list(item, f"{path}.work_counters[{index}]")
        if len(pair) != 2:
            raise ContractViolation("work counter must contain exactly two members")
        counters.append(
            (
                _string(pair[0], f"{path}.work_counters[{index}][0]"),
                _integer(pair[1], f"{path}.work_counters[{index}][1]"),
            )
        )
    result = PreparedSemanticEffectEnvelope(
        provider_key=_string(root["provider_key"], f"{path}.provider_key"),
        effect_contract=_contract(root["effect_contract"], f"{path}.effect_contract"),
        transition_digest=_digest(
            root["transition_digest"], f"{path}.transition_digest"
        ),
        base_state=_predecessor(root["base_state"], f"{path}.base_state"),
        candidate_state=_value(root["candidate_state"], f"{path}.candidate_state"),
        effect_body=_value(root["effect_body"], f"{path}.effect_body"),
        renderer_inputs=tuple(
            _value(item, f"{path}.renderer_inputs[{index}]")
            for index, item in enumerate(
                _list(root["renderer_inputs"], f"{path}.renderer_inputs")
            )
        ),
        impacts=tuple(
            _impact(item, f"{path}.impacts[{index}]")
            for index, item in enumerate(_list(root["impacts"], f"{path}.impacts"))
        ),
        work_counters=tuple(counters),
    )
    _verify_digest(result, root["digest"], path)
    return result


def _output(value: object, path: str) -> SemanticOutputEnvelope:
    root = _object(value, path)
    _keys(
        root,
        {"digest", "output", "prepared_effect_digest", "provider_key", "schema"},
        path,
    )
    _schema(root, "aware.code.semantic-output-envelope.v1", path)
    result = SemanticOutputEnvelope(
        provider_key=_string(root["provider_key"], f"{path}.provider_key"),
        output=_value(root["output"], f"{path}.output"),
        prepared_effect_digest=_digest(
            root["prepared_effect_digest"], f"{path}.prepared_effect_digest"
        ),
    )
    _verify_digest(result, root["digest"], path)
    return result


def _result(value: object, path: str) -> SemanticContractResult:
    root = _object(value, path)
    _keys(
        root,
        {
            "current_result",
            "digest",
            "effect",
            "invocation_digest",
            "outputs",
            "reason",
            "schema",
            "status",
            "transition",
        },
        path,
    )
    _schema(root, "aware.code.semantic-contract-result.v1", path)
    try:
        status = TerminalStatus(_string(root["status"], f"{path}.status"))
    except ValueError as error:
        raise ContractViolation("unknown terminal status") from error
    result = SemanticContractResult(
        status=status,
        invocation_digest=_digest(
            root["invocation_digest"], f"{path}.invocation_digest"
        ),
        current_result=_nullable(
            root["current_result"], _value, f"{path}.current_result"
        ),
        transition=_nullable(root["transition"], _transition, f"{path}.transition"),
        effect=_nullable(root["effect"], _effect, f"{path}.effect"),
        outputs=tuple(
            _output(item, f"{path}.outputs[{index}]")
            for index, item in enumerate(_list(root["outputs"], f"{path}.outputs"))
        ),
        reason=None
        if root["reason"] is None
        else _string(root["reason"], f"{path}.reason"),
    )
    _verify_digest(result, root["digest"], path)
    return result


def _profile_input(value: object, path: str) -> ProfileInputDeclaration:
    root = _object(value, path)
    _keys(root, {"contract", "role"}, path)
    return ProfileInputDeclaration(
        _string(root["role"], f"{path}.role"),
        _contract(root["contract"], f"{path}.contract"),
    )


def _role_binding(value: object, path: str) -> RoleBinding:
    root = _object(value, path)
    _keys(root, {"source_role", "target_role"}, path)
    return RoleBinding(
        _string(root["target_role"], f"{path}.target_role"),
        _string(root["source_role"], f"{path}.source_role"),
    )


def _step(value: object, path: str) -> ProfileStepDeclaration:
    root = _object(value, path)
    _keys(root, {"bindings", "provider_key", "step_key"}, path)
    return ProfileStepDeclaration(
        step_key=_string(root["step_key"], f"{path}.step_key"),
        provider_key=_string(root["provider_key"], f"{path}.provider_key"),
        bindings=tuple(
            _role_binding(item, f"{path}.bindings[{index}]")
            for index, item in enumerate(_list(root["bindings"], f"{path}.bindings"))
        ),
    )


def _profile(value: object, path: str) -> SemanticContractProfileDeclaration:
    root = _object(value, path)
    _keys(
        root,
        {
            "digest",
            "inputs",
            "operation_kinds",
            "package_kinds",
            "profile_ref",
            "providers",
            "schema",
            "steps",
            "terminal_effect_role",
            "terminal_output_roles",
            "terminal_result_role",
            "version",
        },
        path,
    )
    _schema(root, "aware.code.semantic-contract-profile.v1", path)
    result = SemanticContractProfileDeclaration(
        profile_ref=_string(root["profile_ref"], f"{path}.profile_ref"),
        version=_string(root["version"], f"{path}.version"),
        package_kinds=tuple(
            _string(item, f"{path}.package_kinds[{index}]")
            for index, item in enumerate(
                _list(root["package_kinds"], f"{path}.package_kinds")
            )
        ),
        operation_kinds=tuple(
            _string(item, f"{path}.operation_kinds[{index}]")
            for index, item in enumerate(
                _list(root["operation_kinds"], f"{path}.operation_kinds")
            )
        ),
        inputs=tuple(
            _profile_input(item, f"{path}.inputs[{index}]")
            for index, item in enumerate(_list(root["inputs"], f"{path}.inputs"))
        ),
        providers=tuple(
            _provider(item, f"{path}.providers[{index}]")
            for index, item in enumerate(_list(root["providers"], f"{path}.providers"))
        ),
        steps=tuple(
            _step(item, f"{path}.steps[{index}]")
            for index, item in enumerate(_list(root["steps"], f"{path}.steps"))
        ),
        terminal_result_role=_string(
            root["terminal_result_role"], f"{path}.terminal_result_role"
        ),
        terminal_effect_role=_string(
            root["terminal_effect_role"], f"{path}.terminal_effect_role"
        ),
        terminal_output_roles=tuple(
            _string(item, f"{path}.terminal_output_roles[{index}]")
            for index, item in enumerate(
                _list(root["terminal_output_roles"], f"{path}.terminal_output_roles")
            )
        ),
    )
    _verify_digest(result, root["digest"], path)
    return result


def validate_result_context(
    result: SemanticContractResult,
    declaration: SemanticContractProviderDeclaration,
    invocation: SemanticContractInvocation,
) -> None:
    if (
        type(result) is not SemanticContractResult
        or type(declaration) is not SemanticContractProviderDeclaration
        or type(invocation) is not SemanticContractInvocation
    ):
        raise TypeError("result context requires exact module-owned values")
    if result.invocation_digest != invocation.digest:
        raise ContractViolation("result does not bind the exact invocation")
    if result.status.value not in declaration.terminal_statuses:
        raise ContractViolation(
            "provider returned a terminal status it did not declare"
        )
    if (
        type(invocation.predecessor) is TypedEmptyCoordinate
        and not declaration.allows_typed_empty
    ):
        raise ContractViolation("provider does not admit typed-empty predecessor")
    if declaration.predecessor_required and invocation.predecessor is None:
        raise ContractViolation("provider requires a predecessor coordinate")
    candidate = (
        result.current_result
        if result.status is TerminalStatus.CURRENT
        else (result.transition.result if result.transition else None)
    )
    if candidate is not None and (
        candidate.role != declaration.result_role.role
        or candidate.contract != declaration.result_role.contract
    ):
        raise ContractViolation("result coordinate differs from provider declaration")
    if result.transition is not None:
        transition = result.transition
        if (
            transition.provider_key != declaration.provider_key
            or transition.result_contract != declaration.result_role.contract
            or transition.transition_contract != declaration.transition_contract
        ):
            raise ContractViolation("transition differs from provider declaration")
        if predecessor_wire(transition.predecessor) != predecessor_wire(
            invocation.predecessor
        ):
            raise ContractViolation("transition predecessor differs from invocation")
    if result.effect is not None:
        effect = result.effect
        if (
            effect.provider_key != declaration.provider_key
            or effect.effect_contract != declaration.effect_contract
            or effect.effect_body.role != declaration.effect_role.role
            or effect.effect_body.contract != declaration.effect_role.contract
        ):
            raise ContractViolation("prepared effect differs from provider declaration")
        if predecessor_wire(effect.base_state) != predecessor_wire(
            invocation.predecessor
        ):
            raise ContractViolation("effect base differs from invocation predecessor")
        counters = tuple(key for key, _ in effect.work_counters)
        if any(key not in declaration.counter_keys for key in counters):
            raise ContractViolation("prepared effect uses an undeclared counter")
    output_contracts = {item.role: item.contract for item in declaration.output_roles}
    for output in result.outputs:
        if (
            output.provider_key != declaration.provider_key
            or output_contracts.get(output.output.role) != output.output.contract
        ):
            raise ContractViolation("output differs from provider declaration")


def _encode[T: _DigestValue](value: T, expected: type[T]) -> str:
    if type(value) is not expected:
        raise TypeError(f"value must be exact {expected.__name__}")
    return canonical_json_text(value.to_wire())


def _decode[T: _DigestValue](
    text: object, decoder: Callable[[object, str], T], expected: type[T]
) -> T:
    value = decoder(_load(text), "root")
    if type(value) is not expected:
        raise TypeError("decoder produced an unexpected value")
    canonical = canonical_json_text(value.to_wire())
    if text != canonical:
        raise ContractViolation("payload is not the exact canonical encoding")
    return value


def encode_provider_declaration(value: SemanticContractProviderDeclaration) -> str:
    return _encode(value, SemanticContractProviderDeclaration)


def decode_provider_declaration(text: str) -> SemanticContractProviderDeclaration:
    return _decode(text, _provider, SemanticContractProviderDeclaration)


def encode_profile_declaration(value: SemanticContractProfileDeclaration) -> str:
    return _encode(value, SemanticContractProfileDeclaration)


def decode_profile_declaration(text: str) -> SemanticContractProfileDeclaration:
    return _decode(text, _profile, SemanticContractProfileDeclaration)


def encode_invocation(value: SemanticContractInvocation) -> str:
    return _encode(value, SemanticContractInvocation)


def decode_invocation(text: str) -> SemanticContractInvocation:
    return _decode(text, _invocation, SemanticContractInvocation)


def encode_result(
    result: SemanticContractResult,
    declaration: SemanticContractProviderDeclaration,
    invocation: SemanticContractInvocation,
) -> str:
    validate_result_context(result, declaration, invocation)
    return _encode(result, SemanticContractResult)


def decode_result(
    text: str,
    declaration: SemanticContractProviderDeclaration,
    invocation: SemanticContractInvocation,
) -> SemanticContractResult:
    result = _decode(text, _result, SemanticContractResult)
    validate_result_context(result, declaration, invocation)
    return result


__all__ = [
    "decode_invocation",
    "decode_profile_declaration",
    "decode_provider_declaration",
    "decode_result",
    "encode_invocation",
    "encode_profile_declaration",
    "encode_provider_declaration",
    "encode_result",
    "validate_result_context",
]
