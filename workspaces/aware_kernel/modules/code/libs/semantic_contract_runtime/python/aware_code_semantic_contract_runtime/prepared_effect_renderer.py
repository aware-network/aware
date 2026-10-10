"""Owner-neutral prepared-effect renderer registration and execution."""

from __future__ import annotations

import inspect
import json
import os
from dataclasses import dataclass
from threading import RLock
from typing import Awaitable, Callable, Protocol, cast

from .contracts import (
    ContentDigest,
    ContractViolation,
    PredecessorCoordinate,
    SemanticConfigurationCoordinate,
    SemanticContractRef,
    SemanticImplementationCoordinate,
    SemanticPackageCoordinate,
    SemanticValueCoordinate,
    TypedEmptyCoordinate,
    canonical_json_bytes,
)
from .runtime import SemanticBody

_REGISTRATION_TOKEN = object()
_INPUT_CONTRACT = "aware.code.prepared-effect-renderer-input.v1"
_COVERAGE_CONTRACT = "aware.code.prepared-effect-renderer-coverage.v1"


def _token(value: object, field: str) -> str:
    if type(value) is not str or not value or any(char.isspace() for char in value):
        raise ContractViolation(f"{field} must be a nonempty token")
    return value


def _exact[T](value: object, expected: type[T], field: str) -> T:
    if type(value) is not expected:
        raise TypeError(f"{field} must be exact {expected.__name__}")
    check = getattr(value, "__post_init__", None)
    if callable(check):
        check()
    return value


def _ordered_values(
    values: object, *, field: str, nonempty: bool = False
) -> tuple[SemanticValueCoordinate, ...]:
    items = _exact(values, tuple, field)
    for index, item in enumerate(items):
        _exact(item, SemanticValueCoordinate, f"{field}[{index}]")
    ordered = tuple(
        sorted(set(items), key=lambda item: canonical_json_bytes(item.to_wire()))
    )
    if items != ordered or (nonempty and not items):
        raise ContractViolation(f"{field} must be nonempty, unique and ordered")
    return cast(tuple[SemanticValueCoordinate, ...], items)


def _predecessor(value: object, field: str) -> PredecessorCoordinate:
    if type(value) is TypedEmptyCoordinate:
        return _exact(value, TypedEmptyCoordinate, field)
    return _exact(value, SemanticValueCoordinate, field)


@dataclass(frozen=True, slots=True, order=True)
class PreparedEffectRequirement:
    role: str
    subject_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "role", _token(self.role, "requirement.role"))
        object.__setattr__(
            self, "subject_ref", _token(self.subject_ref, "requirement.subject_ref")
        )

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {"role": self.role, "subject_ref": self.subject_ref}


def _requirements(
    value: object, field: str
) -> tuple[PreparedEffectRequirement, ...]:
    items = _exact(value, tuple, field)
    for index, item in enumerate(items):
        _exact(item, PreparedEffectRequirement, f"{field}[{index}]")
    ordered = tuple(
        sorted(set(items), key=lambda item: canonical_json_bytes(item.to_wire()))
    )
    if items != ordered:
        raise ContractViolation(f"{field} must be unique and ordered")
    return cast(tuple[PreparedEffectRequirement, ...], items)


@dataclass(frozen=True, slots=True)
class PreparedEffectRendererInput:
    package: SemanticPackageCoordinate
    package_result: SemanticValueCoordinate
    manifest: SemanticValueCoordinate
    transition: PredecessorCoordinate
    effect: SemanticValueCoordinate
    historical_predecessor: PredecessorCoordinate
    requirements: SemanticValueCoordinate
    r1_profile_ref: str
    r1_profile_digest: ContentDigest
    configuration: SemanticConfigurationCoordinate
    output_namespace: str
    target_ref: str
    target_plan: SemanticValueCoordinate
    prior_output_state: PredecessorCoordinate
    required_obligations: tuple[PreparedEffectRequirement, ...]
    invocation_digest: ContentDigest
    result_digest: ContentDigest
    completion_digest: ContentDigest
    input_digest: ContentDigest

    def __post_init__(self) -> None:
        _exact(self.package, SemanticPackageCoordinate, "package")
        for field in ("package_result", "manifest", "effect", "requirements", "target_plan"):
            _exact(getattr(self, field), SemanticValueCoordinate, field)
        _predecessor(self.transition, "transition")
        _predecessor(self.historical_predecessor, "historical_predecessor")
        _predecessor(self.prior_output_state, "prior_output_state")
        for field in ("r1_profile_ref", "output_namespace", "target_ref"):
            object.__setattr__(self, field, _token(getattr(self, field), field))
        _exact(self.r1_profile_digest, ContentDigest, "r1_profile_digest")
        _exact(self.configuration, SemanticConfigurationCoordinate, "configuration")
        _requirements(self.required_obligations, "required_obligations")
        for field in ("invocation_digest", "result_digest", "completion_digest"):
            _exact(getattr(self, field), ContentDigest, field)
        _exact(self.input_digest, ContentDigest, "input_digest")
        if self.input_digest != ContentDigest.of_bytes(
            canonical_json_bytes(self._wire_without_digest())
        ):
            raise ContractViolation("renderer input digest mismatched")

    @classmethod
    def create(cls, **values: object) -> PreparedEffectRendererInput:
        payload = _renderer_input_wire(values)
        return cls(
            **values,  # type: ignore[arg-type]
            input_digest=ContentDigest.of_bytes(canonical_json_bytes(payload)),
        )

    def _wire_without_digest(self) -> dict[str, object]:
        return _renderer_input_wire(
            {
                field: getattr(self, field)
                for field in self.__dataclass_fields__
                if field != "input_digest"
            }
        )

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": _INPUT_CONTRACT,
            **self._wire_without_digest(),
            "input_digest": self.input_digest.to_wire(),
        }


def _predecessor_wire(value: object) -> dict[str, object]:
    admitted = _predecessor(value, "predecessor")
    return admitted.to_wire()


def _renderer_input_wire(values: object) -> dict[str, object]:
    item = cast(dict[str, object], values)
    return {
        "completion_digest": cast(ContentDigest, item["completion_digest"]).to_wire(),
        "configuration": cast(SemanticConfigurationCoordinate, item["configuration"]).to_wire(),
        "effect": cast(SemanticValueCoordinate, item["effect"]).to_wire(),
        "historical_predecessor": _predecessor_wire(item["historical_predecessor"]),
        "invocation_digest": cast(ContentDigest, item["invocation_digest"]).to_wire(),
        "manifest": cast(SemanticValueCoordinate, item["manifest"]).to_wire(),
        "output_namespace": item["output_namespace"],
        "package": cast(SemanticPackageCoordinate, item["package"]).to_wire(),
        "package_result": cast(SemanticValueCoordinate, item["package_result"]).to_wire(),
        "prior_output_state": _predecessor_wire(item["prior_output_state"]),
        "r1_profile_digest": cast(ContentDigest, item["r1_profile_digest"]).to_wire(),
        "r1_profile_ref": item["r1_profile_ref"],
        "required_obligations": [
            value.to_wire()
            for value in cast(tuple[PreparedEffectRequirement, ...], item["required_obligations"])
        ],
        "requirements": cast(SemanticValueCoordinate, item["requirements"]).to_wire(),
        "result_digest": cast(ContentDigest, item["result_digest"]).to_wire(),
        "target_plan": cast(SemanticValueCoordinate, item["target_plan"]).to_wire(),
        "target_ref": item["target_ref"],
        "transition": _predecessor_wire(item["transition"]),
    }


@dataclass(frozen=True, slots=True)
class PreparedEffectRendererDeclaration:
    renderer_ref: str
    product_profile_ref: str
    product_profile_digest: ContentDigest
    language_profile_ref: str
    language_profile_digest: ContentDigest
    implementation: SemanticImplementationCoordinate
    configuration: SemanticConfigurationCoordinate
    target_plan_contract: SemanticContractRef
    delta_contract: SemanticContractRef

    def __post_init__(self) -> None:
        for field in ("renderer_ref", "product_profile_ref", "language_profile_ref"):
            object.__setattr__(self, field, _token(getattr(self, field), field))
        for field in ("product_profile_digest", "language_profile_digest"):
            _exact(getattr(self, field), ContentDigest, field)
        _exact(self.implementation, SemanticImplementationCoordinate, "implementation")
        _exact(self.configuration, SemanticConfigurationCoordinate, "configuration")
        _exact(self.target_plan_contract, SemanticContractRef, "target_plan_contract")
        _exact(self.delta_contract, SemanticContractRef, "delta_contract")


@dataclass(frozen=True, slots=True)
class PreparedEffectRendererCoverage:
    requirements_digest: ContentDigest
    covered_obligations: tuple[PreparedEffectRequirement, ...]
    target_ref: str
    target_plan_digest: ContentDigest
    product_profile_ref: str
    product_profile_digest: ContentDigest
    language_profile_ref: str
    language_profile_digest: ContentDigest
    configuration: SemanticConfigurationCoordinate
    invocation_digest: ContentDigest
    result_digest: ContentDigest
    completion_digest: ContentDigest
    delta: SemanticValueCoordinate
    outputs: tuple[SemanticValueCoordinate, ...]
    coverage_digest: ContentDigest

    def __post_init__(self) -> None:
        for field in (
            "requirements_digest",
            "target_plan_digest",
            "product_profile_digest",
            "language_profile_digest",
            "invocation_digest",
            "result_digest",
            "completion_digest",
        ):
            _exact(getattr(self, field), ContentDigest, field)
        _requirements(self.covered_obligations, "covered_obligations")
        for field in ("target_ref", "product_profile_ref", "language_profile_ref"):
            object.__setattr__(self, field, _token(getattr(self, field), field))
        _exact(self.configuration, SemanticConfigurationCoordinate, "configuration")
        _exact(self.delta, SemanticValueCoordinate, "delta")
        _ordered_values(self.outputs, field="outputs", nonempty=True)
        _exact(self.coverage_digest, ContentDigest, "coverage_digest")
        if self.coverage_digest != ContentDigest.of_bytes(
            canonical_json_bytes(self._wire_without_digest())
        ):
            raise ContractViolation("renderer coverage digest mismatched")

    @classmethod
    def create(cls, **values: object) -> PreparedEffectRendererCoverage:
        payload = _coverage_wire(values)
        return cls(
            **values,  # type: ignore[arg-type]
            coverage_digest=ContentDigest.of_bytes(canonical_json_bytes(payload)),
        )

    def _wire_without_digest(self) -> dict[str, object]:
        return _coverage_wire(
            {
                field: getattr(self, field)
                for field in self.__dataclass_fields__
                if field != "coverage_digest"
            }
        )

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": _COVERAGE_CONTRACT,
            **self._wire_without_digest(),
            "coverage_digest": self.coverage_digest.to_wire(),
        }


def _coverage_wire(values: object) -> dict[str, object]:
    item = cast(dict[str, object], values)
    return {
        "completion_digest": cast(ContentDigest, item["completion_digest"]).to_wire(),
        "configuration": cast(SemanticConfigurationCoordinate, item["configuration"]).to_wire(),
        "covered_obligations": [
            value.to_wire()
            for value in cast(tuple[PreparedEffectRequirement, ...], item["covered_obligations"])
        ],
        "delta": cast(SemanticValueCoordinate, item["delta"]).to_wire(),
        "invocation_digest": cast(ContentDigest, item["invocation_digest"]).to_wire(),
        "language_profile_digest": cast(ContentDigest, item["language_profile_digest"]).to_wire(),
        "language_profile_ref": item["language_profile_ref"],
        "outputs": [
            value.to_wire()
            for value in cast(tuple[SemanticValueCoordinate, ...], item["outputs"])
        ],
        "product_profile_digest": cast(ContentDigest, item["product_profile_digest"]).to_wire(),
        "product_profile_ref": item["product_profile_ref"],
        "requirements_digest": cast(ContentDigest, item["requirements_digest"]).to_wire(),
        "result_digest": cast(ContentDigest, item["result_digest"]).to_wire(),
        "target_plan_digest": cast(ContentDigest, item["target_plan_digest"]).to_wire(),
        "target_ref": item["target_ref"],
    }


@dataclass(frozen=True, slots=True)
class PreparedEffectRendererExecution:
    use_ref: str
    operation_identity: object
    renderer_input: PreparedEffectRendererInput
    bodies: tuple[SemanticBody, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "use_ref", _token(self.use_ref, "use_ref"))
        if self.operation_identity is None:
            raise ContractViolation("original operation identity required")
        _exact(self.renderer_input, PreparedEffectRendererInput, "renderer_input")
        items = _exact(self.bodies, tuple, "bodies")
        for index, body in enumerate(items):
            _exact(body, SemanticBody, f"bodies[{index}]")
        coordinates = tuple(body.coordinate for body in items)
        if coordinates != tuple(
            sorted(set(coordinates), key=lambda item: canonical_json_bytes(item.to_wire()))
        ):
            raise ContractViolation("renderer bodies must be coordinate-unique and ordered")
        required = _renderer_required_coordinates(self.renderer_input)
        if coordinates != required:
            raise ContractViolation("renderer body closure is incomplete or extra")


def _renderer_required_coordinates(
    value: PreparedEffectRendererInput,
) -> tuple[SemanticValueCoordinate, ...]:
    coordinates = [
        value.package_result,
        value.manifest,
        value.effect,
        value.requirements,
        value.target_plan,
    ]
    for predecessor in (
        value.transition,
        value.historical_predecessor,
        value.prior_output_state,
    ):
        if type(predecessor) is SemanticValueCoordinate:
            coordinates.append(predecessor)
    return tuple(
        sorted(set(coordinates), key=lambda item: canonical_json_bytes(item.to_wire()))
    )


@dataclass(frozen=True, slots=True)
class PreparedEffectRendererProduct:
    delta: SemanticBody
    outputs: tuple[SemanticBody, ...]
    coverage: PreparedEffectRendererCoverage

    def __post_init__(self) -> None:
        _exact(self.delta, SemanticBody, "delta")
        bodies = _exact(self.outputs, tuple, "outputs")
        for index, body in enumerate(bodies):
            _exact(body, SemanticBody, f"outputs[{index}]")
        coordinates = tuple(body.coordinate for body in bodies)
        if coordinates != tuple(
            sorted(set(coordinates), key=lambda item: canonical_json_bytes(item.to_wire()))
        ):
            raise ContractViolation("output bodies must be coordinate-unique and ordered")
        _exact(self.coverage, PreparedEffectRendererCoverage, "coverage")
        if self.coverage.delta != self.delta.coordinate or self.coverage.outputs != coordinates:
            raise ContractViolation("coverage differs from exact renderer bodies")


def validate_prepared_effect_renderer_coverage(
    value: PreparedEffectRendererCoverage,
    *,
    renderer_input: PreparedEffectRendererInput,
    declaration: PreparedEffectRendererDeclaration,
) -> None:
    _exact(value, PreparedEffectRendererCoverage, "coverage")
    _exact(renderer_input, PreparedEffectRendererInput, "renderer_input")
    _exact(declaration, PreparedEffectRendererDeclaration, "declaration")
    expected = (
        value.requirements_digest == renderer_input.requirements.digest
        and value.covered_obligations == renderer_input.required_obligations
        and value.target_ref == renderer_input.target_ref
        and value.target_plan_digest == renderer_input.target_plan.digest
        and value.product_profile_ref == declaration.product_profile_ref
        and value.product_profile_digest == declaration.product_profile_digest
        and value.language_profile_ref == declaration.language_profile_ref
        and value.language_profile_digest == declaration.language_profile_digest
        and value.configuration == declaration.configuration
        and value.invocation_digest == renderer_input.invocation_digest
        and value.result_digest == renderer_input.result_digest
        and value.completion_digest == renderer_input.completion_digest
        and value.delta.contract == declaration.delta_contract
    )
    if not expected:
        raise ContractViolation("renderer coverage differs from admitted execution")


class PreparedEffectRendererInputValidator(Protocol):
    def validate_prepared_effect_renderer_input(
        self,
        input_admission: object,
        *,
        expected: PreparedEffectRendererExecution,
    ) -> None: ...


type PreparedEffectRenderer = Callable[
    [object, PreparedEffectRendererExecution],
    PreparedEffectRendererProduct | Awaitable[PreparedEffectRendererProduct],
]


class AdmittedPreparedEffectRendererRegistration:
    __slots__ = ("_token",)

    def __init__(self, token: object) -> None:
        if token is not _REGISTRATION_TOKEN:
            raise TypeError("renderer registration is Code-issued only")
        self._token = token


@dataclass(slots=True)
class _RendererState:
    declaration: PreparedEffectRendererDeclaration
    renderer: PreparedEffectRenderer
    validator: PreparedEffectRendererInputValidator
    validator_entrance: Callable[..., None]
    closed: bool = False
    running: int = 0


@dataclass(slots=True)
class _RendererUse:
    operation_identity: object
    input_digest: ContentDigest
    running: bool = False
    consumed: bool = False


class PreparedEffectRendererHost:
    def __init__(self) -> None:
        self._pid = os.getpid()
        self._lock = RLock()
        self._registrations: dict[
            AdmittedPreparedEffectRendererRegistration, _RendererState
        ] = {}
        self._uses: dict[
            tuple[AdmittedPreparedEffectRendererRegistration, str], _RendererUse
        ] = {}
        self._closed = False

    def _check(self) -> None:
        if self._pid != os.getpid():
            raise ContractViolation("renderer host belongs to another process")
        if self._closed:
            raise ContractViolation("renderer host is closed")

    def close(self) -> None:
        with self._lock:
            self._check()
            if any(state.running for state in self._registrations.values()):
                raise ContractViolation("renderer execution is active")
            for state in self._registrations.values():
                state.closed = True
            self._closed = True


def _original_validator(
    validator: PreparedEffectRendererInputValidator, entrance: Callable[..., None]
) -> bool:
    return (
        inspect.ismethod(entrance)
        and entrance.__self__ is validator
        and entrance.__func__
        is type(validator).validate_prepared_effect_renderer_input  # type: ignore[attr-defined]
    )


def register_prepared_effect_renderer(
    host: PreparedEffectRendererHost,
    *,
    declaration: PreparedEffectRendererDeclaration,
    renderer: PreparedEffectRenderer,
    validator: PreparedEffectRendererInputValidator,
    validator_entrance: Callable[..., None],
) -> AdmittedPreparedEffectRendererRegistration:
    _exact(host, PreparedEffectRendererHost, "host")
    _exact(declaration, PreparedEffectRendererDeclaration, "declaration")
    if not callable(renderer):
        raise TypeError("renderer must be callable")
    if not _original_validator(validator, validator_entrance):
        raise ContractViolation("original renderer validator entrance required")
    with host._lock:
        host._check()
        if any(
            state.declaration.renderer_ref == declaration.renderer_ref
            for state in host._registrations.values()
            if not state.closed
        ):
            raise ContractViolation("renderer already registered")
        registration = AdmittedPreparedEffectRendererRegistration(_REGISTRATION_TOKEN)
        host._registrations[registration] = _RendererState(
            declaration, renderer, validator, validator_entrance
        )
        return registration


def _renderer_state(
    host: PreparedEffectRendererHost,
    registration: AdmittedPreparedEffectRendererRegistration,
) -> _RendererState:
    _exact(registration, AdmittedPreparedEffectRendererRegistration, "registration")
    state = host._registrations.get(registration)
    if state is None or registration._token is not _REGISTRATION_TOKEN or state.closed:
        raise ContractViolation("renderer registration is unavailable")
    if not _original_validator(state.validator, state.validator_entrance):
        raise ContractViolation("renderer validator entrance changed")
    return state


async def execute_registered_prepared_effect_renderer(
    host: PreparedEffectRendererHost,
    registration: AdmittedPreparedEffectRendererRegistration,
    *,
    input_admission: object,
    expected: PreparedEffectRendererExecution,
) -> PreparedEffectRendererProduct:
    _exact(host, PreparedEffectRendererHost, "host")
    _exact(expected, PreparedEffectRendererExecution, "expected")
    key = (registration, expected.use_ref)
    with host._lock:
        host._check()
        state = _renderer_state(host, registration)
        use = host._uses.get(key)
        if use is None:
            use = _RendererUse(
                expected.operation_identity, expected.renderer_input.input_digest
            )
            host._uses[key] = use
        if (
            use.operation_identity is not expected.operation_identity
            or use.input_digest != expected.renderer_input.input_digest
        ):
            raise ContractViolation("renderer use identity differs")
        if use.running or use.consumed:
            raise ContractViolation("renderer use already consumed")
        if expected.renderer_input.configuration != state.declaration.configuration:
            raise ContractViolation("renderer configuration differs")
        if expected.renderer_input.target_plan.contract != state.declaration.target_plan_contract:
            raise ContractViolation("renderer target plan contract differs")
        use.running = True
        state.running += 1
        renderer, validator = state.renderer, state.validator_entrance
    try:
        if validator(input_admission, expected=expected) is not None:
            raise ContractViolation("renderer validator must return None")
        produced = renderer(input_admission, expected)
        result = await produced if inspect.isawaitable(produced) else produced
        _exact(result, PreparedEffectRendererProduct, "renderer product")
        validate_prepared_effect_renderer_coverage(
            result.coverage,
            renderer_input=expected.renderer_input,
            declaration=state.declaration,
        )
        if validator(input_admission, expected=expected) is not None:
            raise ContractViolation("renderer validator must return None")
        with host._lock:
            host._check()
            if _renderer_state(host, registration) is not state:
                raise ContractViolation("renderer registration changed")
            if host._uses.get(key) is not use or not use.running:
                raise ContractViolation("renderer use changed")
        return result
    finally:
        with host._lock:
            use.running = False
            use.consumed = True
            state.running -= 1


def close_prepared_effect_renderer_registration(
    host: PreparedEffectRendererHost,
    registration: AdmittedPreparedEffectRendererRegistration,
) -> None:
    _exact(host, PreparedEffectRendererHost, "host")
    with host._lock:
        host._check()
        state = _renderer_state(host, registration)
        if state.running:
            raise ContractViolation("renderer execution is active")
        state.closed = True


def encode_prepared_effect_renderer_input(value: PreparedEffectRendererInput) -> bytes:
    _exact(value, PreparedEffectRendererInput, "value")
    return canonical_json_bytes(value.to_wire())


def encode_prepared_effect_renderer_coverage(
    value: PreparedEffectRendererCoverage,
) -> bytes:
    _exact(value, PreparedEffectRendererCoverage, "value")
    return canonical_json_bytes(value.to_wire())


def _json_object(body: bytes, contract: str) -> dict[str, object]:
    if type(body) is not bytes or not body:
        raise TypeError("canonical body must be nonempty exact bytes")
    try:
        value = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractViolation("canonical body is not JSON") from error
    if type(value) is not dict or value.get("contract") != contract:
        raise ContractViolation("canonical body contract differs")
    if canonical_json_bytes(value) != body:
        raise ContractViolation("canonical body is noncanonical")
    return cast(dict[str, object], value)


def _digest(value: object, field: str) -> ContentDigest:
    return ContentDigest(_exact(value, str, field))


def _contract(value: object, field: str) -> SemanticContractRef:
    item = _exact(value, dict, field)
    if set(item) != {"key", "schema_digest", "version"}:
        raise ContractViolation(f"{field} fields differ")
    return SemanticContractRef(
        _exact(item["key"], str, field),
        _exact(item["version"], str, field),
        _digest(item["schema_digest"], field),
    )


def _value(value: object, field: str) -> SemanticValueCoordinate:
    item = _exact(value, dict, field)
    if set(item) != {"contract", "digest", "role", "size_bytes", "value_ref"}:
        raise ContractViolation(f"{field} fields differ")
    return SemanticValueCoordinate(
        _exact(item["role"], str, field),
        _contract(item["contract"], field),
        _exact(item["value_ref"], str, field),
        _digest(item["digest"], field),
        _exact(item["size_bytes"], int, field),
    )


def _package(value: object) -> SemanticPackageCoordinate:
    item = _exact(value, dict, "package")
    if set(item) != {"manifest_digest", "package_kind", "package_ref"}:
        raise ContractViolation("package fields differ")
    return SemanticPackageCoordinate(
        _exact(item["package_ref"], str, "package_ref"),
        _exact(item["package_kind"], str, "package_kind"),
        _digest(item["manifest_digest"], "manifest_digest"),
    )


def _configuration(value: object) -> SemanticConfigurationCoordinate:
    item = _exact(value, dict, "configuration")
    if set(item) != {"configuration_ref", "digest"}:
        raise ContractViolation("configuration fields differ")
    return SemanticConfigurationCoordinate(
        _exact(item["configuration_ref"], str, "configuration_ref"),
        _digest(item["digest"], "configuration.digest"),
    )


def _decoded_predecessor(value: object, field: str) -> PredecessorCoordinate:
    item = _exact(value, dict, field)
    if set(item) == {"contract", "kind"} and item["kind"] == "typed_empty":
        return TypedEmptyCoordinate(_contract(item["contract"], field))
    return _value(item, field)


def _decoded_requirements(value: object, field: str) -> tuple[PreparedEffectRequirement, ...]:
    items = _exact(value, list, field)
    result = []
    for index, raw in enumerate(items):
        item = _exact(raw, dict, f"{field}[{index}]")
        if set(item) != {"role", "subject_ref"}:
            raise ContractViolation("requirement fields differ")
        result.append(
            PreparedEffectRequirement(
                _exact(item["role"], str, field),
                _exact(item["subject_ref"], str, field),
            )
        )
    return tuple(result)


def decode_prepared_effect_renderer_input(body: bytes) -> PreparedEffectRendererInput:
    item = _json_object(body, _INPUT_CONTRACT)
    expected_fields = {
        "completion_digest",
        "configuration",
        "contract",
        "effect",
        "historical_predecessor",
        "input_digest",
        "invocation_digest",
        "manifest",
        "output_namespace",
        "package",
        "package_result",
        "prior_output_state",
        "r1_profile_digest",
        "r1_profile_ref",
        "required_obligations",
        "requirements",
        "result_digest",
        "target_plan",
        "target_ref",
        "transition",
    }
    if set(item) != expected_fields:
        raise ContractViolation("renderer input fields differ")
    values = {
        "package": _package(item["package"]),
        "package_result": _value(item["package_result"], "package_result"),
        "manifest": _value(item["manifest"], "manifest"),
        "transition": _decoded_predecessor(item["transition"], "transition"),
        "effect": _value(item["effect"], "effect"),
        "historical_predecessor": _decoded_predecessor(
            item["historical_predecessor"], "historical_predecessor"
        ),
        "requirements": _value(item["requirements"], "requirements"),
        "r1_profile_ref": _exact(item["r1_profile_ref"], str, "r1_profile_ref"),
        "r1_profile_digest": _digest(item["r1_profile_digest"], "r1_profile_digest"),
        "configuration": _configuration(item["configuration"]),
        "output_namespace": _exact(item["output_namespace"], str, "output_namespace"),
        "target_ref": _exact(item["target_ref"], str, "target_ref"),
        "target_plan": _value(item["target_plan"], "target_plan"),
        "prior_output_state": _decoded_predecessor(
            item["prior_output_state"], "prior_output_state"
        ),
        "required_obligations": _decoded_requirements(
            item["required_obligations"], "required_obligations"
        ),
        "invocation_digest": _digest(item["invocation_digest"], "invocation_digest"),
        "result_digest": _digest(item["result_digest"], "result_digest"),
        "completion_digest": _digest(item["completion_digest"], "completion_digest"),
        "input_digest": _digest(item["input_digest"], "input_digest"),
    }
    result = PreparedEffectRendererInput(**values)  # type: ignore[arg-type]
    if encode_prepared_effect_renderer_input(result) != body:
        raise ContractViolation("renderer input does not round trip")
    return result


def decode_prepared_effect_renderer_coverage(
    body: bytes,
) -> PreparedEffectRendererCoverage:
    item = _json_object(body, _COVERAGE_CONTRACT)
    expected_fields = {
        "completion_digest",
        "configuration",
        "contract",
        "coverage_digest",
        "covered_obligations",
        "delta",
        "invocation_digest",
        "language_profile_digest",
        "language_profile_ref",
        "outputs",
        "product_profile_digest",
        "product_profile_ref",
        "requirements_digest",
        "result_digest",
        "target_plan_digest",
        "target_ref",
    }
    if set(item) != expected_fields:
        raise ContractViolation("renderer coverage fields differ")
    values = {
        "requirements_digest": _digest(item["requirements_digest"], "requirements_digest"),
        "covered_obligations": _decoded_requirements(
            item["covered_obligations"], "covered_obligations"
        ),
        "target_ref": _exact(item["target_ref"], str, "target_ref"),
        "target_plan_digest": _digest(item["target_plan_digest"], "target_plan_digest"),
        "product_profile_ref": _exact(item["product_profile_ref"], str, "product_profile_ref"),
        "product_profile_digest": _digest(item["product_profile_digest"], "product_profile_digest"),
        "language_profile_ref": _exact(item["language_profile_ref"], str, "language_profile_ref"),
        "language_profile_digest": _digest(
            item["language_profile_digest"], "language_profile_digest"
        ),
        "configuration": _configuration(item["configuration"]),
        "invocation_digest": _digest(item["invocation_digest"], "invocation_digest"),
        "result_digest": _digest(item["result_digest"], "result_digest"),
        "completion_digest": _digest(item["completion_digest"], "completion_digest"),
        "delta": _value(item["delta"], "delta"),
        "outputs": tuple(_value(raw, "output") for raw in _exact(item["outputs"], list, "outputs")),
        "coverage_digest": _digest(item["coverage_digest"], "coverage_digest"),
    }
    result = PreparedEffectRendererCoverage(**values)  # type: ignore[arg-type]
    if encode_prepared_effect_renderer_coverage(result) != body:
        raise ContractViolation("renderer coverage does not round trip")
    return result


__all__ = [
    "AdmittedPreparedEffectRendererRegistration",
    "PreparedEffectRendererCoverage",
    "PreparedEffectRendererDeclaration",
    "PreparedEffectRendererExecution",
    "PreparedEffectRendererHost",
    "PreparedEffectRendererInput",
    "PreparedEffectRendererInputValidator",
    "PreparedEffectRendererProduct",
    "PreparedEffectRequirement",
    "close_prepared_effect_renderer_registration",
    "decode_prepared_effect_renderer_coverage",
    "decode_prepared_effect_renderer_input",
    "encode_prepared_effect_renderer_coverage",
    "encode_prepared_effect_renderer_input",
    "execute_registered_prepared_effect_renderer",
    "register_prepared_effect_renderer",
    "validate_prepared_effect_renderer_coverage",
]
