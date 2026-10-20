"""Trusted-local constructor ergonomics; Ontology owns execution and persistence.

Created handles carry settled identity evidence, not live snapshot, field or
mutation rights. Raw byte I/O and persistent writes belong to their owners.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Protocol, Self, TypeVar

from .facade import ScalarArguments, _digest, _text
from .owner_values import (
    ActionValueMode,
    OntologyObjectActionRole,
    OntologyObjectClassBinding,
    OntologyRuntimeActionInstanceRefTarget,
    ScalarKind,
    ShapeKind,
)

_Constructor = TypeVar("_Constructor", bound="OntologyObjectConstructor")
_KINDS = {ScalarKind.BOOLEAN: bool, ScalarKind.INTEGER: int, ScalarKind.STRING: str}
CONSTRUCTOR_RESERVED_NAMES = frozenset({
    "close", "invocation_state", "invocation_receipt", "object_reference",
})


class ObjectConstructorError(RuntimeError):
    """A constructor refusal; recovery points to the original backend attempt."""

    def __init__(self, reason: str, *, recovery_ref: str | None = None) -> None:
        super().__init__(reason)
        self.reason: str = reason
        self.recovery_ref: str | None = recovery_ref


@dataclass(frozen=True, slots=True)
class ObjectCreationReceipt:
    """Data projection of settled owner evidence; cannot admit another operation."""

    invocation_ref: str
    attempt_ref: str
    receipt_digest: str
    outcome: str
    provider_key: str
    provider_generation: str
    result_revision_ref: str
    canonical_commit_ref: str | None

    def __post_init__(self) -> None:
        if (any(not _text(value) for value in (
            self.invocation_ref, self.attempt_ref, self.provider_key,
            self.provider_generation, self.result_revision_ref,
        )) or not _digest(self.receipt_digest)
                or (self.canonical_commit_ref is not None and not _text(self.canonical_commit_ref))
                or type(self.outcome) is not str or self.outcome not in ("committed", "no_op")):
            raise ObjectConstructorError("constructor.invalid_receipt")


@dataclass(frozen=True, slots=True)
class ObjectCreationResult:
    """Infrastructure returns this only after commit/reread, journals and cleanup."""

    type_ref: str
    action_ref: str
    invocation_key: str
    binding_digest: str
    fragment_closure_digest: str
    target: OntologyRuntimeActionInstanceRefTarget
    receipt: ObjectCreationReceipt
    settled: bool
    worker_cleaned: bool
    reread_verified: bool


class ObjectConstructorInvoker(Protocol):
    async def invoke_constructor(
        self, *, type_ref: str, action_ref: str, arguments: ScalarArguments,
        invocation_key: str, binding_digest: str, fragment_closure_digest: str,
    ) -> ObjectCreationResult: ...


def require_constructor_profile(binding: OntologyObjectClassBinding) -> None:
    """Representation restrictions only; original owners still admit the call."""
    if type(binding) is not OntologyObjectClassBinding or len(binding.actions) != 1:
        raise ObjectConstructorError("constructor.unsupported_profile")
    if any(name in CONSTRUCTOR_RESERVED_NAMES for name in (
        *(field.attribute_name for field in binding.fields),
        *(relationship.method_name for relationship in binding.relationships),
    )):
        raise ObjectConstructorError("constructor.unsupported_profile")
    action = binding.actions[0]
    if (action.role is not OntologyObjectActionRole.CONSTRUCTOR
            or action.relationship_constructor_paths or not action.parameters
            or action.method_name in CONSTRUCTOR_RESERVED_NAMES):
        raise ObjectConstructorError("constructor.unsupported_profile")
    for parameter in action.parameters:
        if (parameter.value_mode is not ActionValueMode.VALUE
                or parameter.shape.kind is not ShapeKind.SCALAR
                or parameter.shape.scalar_kind not in _KINDS
                or parameter.required is not True or parameter.nullable is not False):
            raise ObjectConstructorError("constructor.unsupported_profile")


@dataclass(frozen=True, slots=True)
class ObjectConstructorContext:
    """Reusable source/binding descriptions and an infrastructure-owned port."""

    binding: OntologyObjectClassBinding
    fragment_closure_digest: str
    invoker: ObjectConstructorInvoker
    provider_key: str
    provider_generation: str

    def __post_init__(self) -> None:
        require_constructor_profile(self.binding)
        if (not _digest(self.fragment_closure_digest) or not _text(self.provider_key)
                or not _text(self.provider_generation)):
            raise ObjectConstructorError("constructor.invalid_context")

    def bind(self, constructor_type: type[_Constructor], *, invocation_key: str) -> _Constructor:
        if not isinstance(constructor_type, type) or not issubclass(constructor_type, OntologyObjectConstructor):
            raise ObjectConstructorError("constructor.invalid_binding")
        return constructor_type(self, invocation_key=invocation_key)


class OntologyObjectConstructor:
    """One constructor operation or an inert, typed created-object handle."""

    __ontology_type_ref__: ClassVar[str]
    __ontology_binding_digest__: ClassVar[str]
    __ontology_dependency_closure_digest__: ClassVar[str]
    __ontology_action_bindings__: ClassVar[tuple[tuple[str, str], ...]]

    def __init__(self, context: ObjectConstructorContext, *, invocation_key: str) -> None:
        if type(context) is not ObjectConstructorContext or not _text(invocation_key):
            raise ObjectConstructorError("constructor.invalid_binding")
        binding = context.binding
        if (type(self).__name__ != binding.class_name
                or self.__ontology_type_ref__ != binding.type_ref
                or self.__ontology_binding_digest__ != binding.binding_digest
                or self.__ontology_dependency_closure_digest__ != context.fragment_closure_digest
                or self.__ontology_action_bindings__ != tuple(
                    (action.action_ref, action.method_name) for action in binding.actions)):
            raise ObjectConstructorError("constructor.binding_mismatch")
        self._context: ObjectConstructorContext | None = context
        self._invocation_key: str = invocation_key
        self._state: str = "ready"
        self._receipt: ObjectCreationReceipt | None = None
        self._target: OntologyRuntimeActionInstanceRefTarget | None = None

    @property
    def invocation_state(self) -> str:
        return self._state

    @property
    def invocation_receipt(self) -> ObjectCreationReceipt | None:
        return self._receipt

    @property
    def object_reference(self) -> OntologyRuntimeActionInstanceRefTarget:
        if self._state != "created" or self._target is None:
            raise ObjectConstructorError("constructor.result_unavailable")
        return self._target

    def close(self) -> None:
        if self._state == "ready":
            self._state = "closed"
            self._context = None

    async def _invoke_constructor(self, action_ref: str, **arguments: object) -> Self:
        if self._state != "ready":
            raise ObjectConstructorError("constructor.operation_consumed")
        self._state = "pending"
        try:
            context = self._context
            if context is None:
                raise ObjectConstructorError("constructor.invalid_binding")
            binding = context.binding
            action = binding.actions[0]
            if action_ref != action.action_ref:
                raise ObjectConstructorError("constructor.action_mismatch")
            if set(arguments) != {parameter.parameter_ref for parameter in action.parameters}:
                raise ObjectConstructorError("constructor.invalid_arguments")
            ordered: list[tuple[str, bool | int | str | None]] = []
            for parameter in action.parameters:
                value = arguments[parameter.parameter_ref]
                kind = parameter.shape.scalar_kind
                if kind is None:
                    raise ObjectConstructorError("constructor.unsupported_profile")
                expected = _KINDS.get(kind)
                if type(value) is not expected:
                    raise ObjectConstructorError("constructor.invalid_arguments")
                if not isinstance(value, (bool, int, str)):
                    raise ObjectConstructorError("constructor.invalid_arguments")
                ordered.append((parameter.parameter_ref, value))
            result = await context.invoker.invoke_constructor(
                type_ref=binding.type_ref, action_ref=action_ref,
                arguments=tuple(ordered), invocation_key=self._invocation_key,
                binding_digest=binding.binding_digest,
                fragment_closure_digest=context.fragment_closure_digest,
            )
            self._check_result(result, context)
            # The returned handle has no operation right. Keep the original
            # constructor consumed; neither handle can dispatch this Action again.
            created = type(self)(context, invocation_key=self._invocation_key)
            created._target = result.target
            created._receipt = result.receipt
            created._state = "created"
            created._context = None
            self._receipt = result.receipt
            self._state = "complete"
            return created
        except BaseException:
            self._state = "failed"
            raise
        finally:
            self._context = None

    def _check_result(self, result: ObjectCreationResult, context: ObjectConstructorContext) -> None:
        if (type(result) is not ObjectCreationResult
                or type(result.target) is not OntologyRuntimeActionInstanceRefTarget
                or type(result.receipt) is not ObjectCreationReceipt
                or result.settled is not True or result.worker_cleaned is not True
                or result.reread_verified is not True):
            raise ObjectConstructorError("constructor.invalid_result")
        if any(not _text(value) for value in (
            result.type_ref, result.action_ref, result.invocation_key,
            result.binding_digest, result.fragment_closure_digest,
            result.target.type_ref, result.target.instance_ref,
            result.target.provider_key, result.target.provider_generation,
        )):
            raise ObjectConstructorError("constructor.invalid_result")
        binding = context.binding
        if (result.type_ref != binding.type_ref or result.target.type_ref != binding.type_ref
                or result.action_ref != binding.actions[0].action_ref
                or result.invocation_key != self._invocation_key
                or result.binding_digest != binding.binding_digest
                or result.fragment_closure_digest != context.fragment_closure_digest):
            raise ObjectConstructorError("constructor.result_mismatch")
        ObjectCreationReceipt.__post_init__(result.receipt)
        if (result.target.provider_key != result.receipt.provider_key
                or result.target.provider_generation != result.receipt.provider_generation
                or result.target.provider_key != context.provider_key
                or result.target.provider_generation != context.provider_generation):
            raise ObjectConstructorError("constructor.result_mismatch")
