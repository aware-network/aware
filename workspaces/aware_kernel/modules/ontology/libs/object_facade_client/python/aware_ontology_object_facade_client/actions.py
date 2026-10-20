"""Explicitly bound instance Actions; original hosts own execution and authority.

This trusted-local profile supports void and receiver-returning, target-scoped
Actions. A returned Object carries identity and settlement data. Field state is
not hydrated here. Configuration bytes are owner-supplied correspondence data,
not a capability, and an observation never becomes an operation permit.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import ClassVar, Protocol, TypeVar, cast

from aware_meta_type_schema import TypeKind, TypeSchemaBundle

from .facade import ScalarArguments, ScalarValue, _digest, _text
from .owner_values import (
    ActionValueMode,
    MutationScope,
    OntologyObjectActionBinding,
    OntologyObjectActionRole,
    OntologyObjectClassBinding,
    OntologyRuntimeActionInstanceRefTarget,
    ScalarKind,
    SchemaActionDefinition,
    ShapeKind,
    ValueShape,
)

MAX_CORRESPONDENCE_BYTES = 262_144
ACTION_RESERVED_NAMES = frozenset(
    {
        "object_reference",
        "invocation_state",
        "invocation_receipt",
        "invocation_result",
    }
)
_KINDS = {ScalarKind.BOOLEAN: bool, ScalarKind.INTEGER: int, ScalarKind.STRING: str}
_Actions = TypeVar("_Actions", bound="OntologyObjectActions")


class ObjectActionError(RuntimeError):
    def __init__(self, code: str, *, recovery_ref: str | None = None) -> None:
        super().__init__(code)
        self.code: str = code
        self.recovery_ref: str | None = recovery_ref


def _body(value: object) -> bool:
    return type(value) is bytes and 0 < len(value) <= MAX_CORRESPONDENCE_BYTES


def _deadline(value: object) -> bool:
    return type(value) is float and math.isfinite(value)


@dataclass(frozen=True, slots=True)
class ObjectActionRequest:
    """One explicit operation's data; the host must independently admit it."""

    target: OntologyRuntimeActionInstanceRefTarget
    action_ref: str
    arguments: ScalarArguments
    invocation_key: str
    binding_digest: str
    fragment_closure_digest: str
    branch_ref: str
    projection_ref: str
    configuration_binding: bytes
    expected_revision_ref: str
    deadline: float

    def __post_init__(self) -> None:
        if (
            type(self.target) is not OntologyRuntimeActionInstanceRefTarget
            or any(
                not _text(v)
                for v in (
                    self.action_ref,
                    self.invocation_key,
                    self.branch_ref,
                    self.projection_ref,
                    self.expected_revision_ref,
                )
            )
            or not _digest(self.binding_digest)
            or not _digest(self.fragment_closure_digest)
            or not _body(self.configuration_binding)
            or not _deadline(self.deadline)
            or type(self.arguments) is not tuple
        ):
            raise ObjectActionError("action.invalid_request")
        for row in self.arguments:
            if (
                type(row) is not tuple
                or len(row) != 2
                or not _text(row[0])
                or type(row[1]) not in (bool, int, str, type(None))
            ):
                raise ObjectActionError("action.invalid_request")


@dataclass(frozen=True, slots=True)
class ObjectActionReceipt:
    """Detached original outcome coordinates; no execution or read right."""

    invocation_ref: str
    attempt_ref: str
    receipt_digest: str
    outcome: str
    base_revision_ref: str
    result_revision_ref: str
    canonical_commit_ref: str | None

    def __post_init__(self) -> None:
        if (
            any(
                not _text(v)
                for v in (
                    self.invocation_ref,
                    self.attempt_ref,
                    self.base_revision_ref,
                    self.result_revision_ref,
                )
            )
            or not _digest(self.receipt_digest)
            or type(self.outcome) is not str
            or self.outcome not in ("committed", "no_op")
            or self.canonical_commit_ref is not None
            and not _text(self.canonical_commit_ref)
            or self.outcome == "no_op"
            and self.base_revision_ref != self.result_revision_ref
            or self.outcome == "committed"
            and self.base_revision_ref == self.result_revision_ref
        ):
            raise ObjectActionError("action.invalid_receipt")


@dataclass(frozen=True, slots=True)
class ObjectActionResult:
    """Infrastructure returns success only after settlement and cleanup.

    These consistency fields are not cryptographic witnesses. Original host
    authentication, admission and publication remain mandatory at the port.
    """

    request: ObjectActionRequest
    receipt: ObjectActionReceipt
    history_correspondence: bytes
    settled: bool
    worker_cleaned: bool
    reread_verified: bool
    returned_object: OntologyRuntimeActionInstanceRefTarget | None = None


@dataclass(frozen=True, slots=True)
class OntologyReturnedObject:
    """Settled receiver identity; acquisition and fresh Action admission follow.

    This value supplies neither field state nor another operation permit.
    """

    object_reference: OntologyRuntimeActionInstanceRefTarget
    invocation_receipt: ObjectActionReceipt
    history_correspondence: bytes


class ObjectActionInvoker(Protocol):
    async def invoke_action(
        self, request: ObjectActionRequest, /
    ) -> ObjectActionResult:
        """Fresh admission, journal-before-contact, execution and complete cleanup."""
        ...


def _enum_values(shape: ValueShape, schema: TypeSchemaBundle) -> tuple[str, ...]:
    if shape.kind is ShapeKind.NAMED:
        matches = tuple(t for t in schema.types if t.type_ref == shape.type_ref)
        if len(matches) == 1 and matches[0].kind is TypeKind.ENUM:
            return matches[0].enum_values
    return ()


def action_definition(
    binding: OntologyObjectClassBinding,
    definitions: tuple[SchemaActionDefinition, ...],
    action_ref: str,
) -> tuple[OntologyObjectActionBinding, SchemaActionDefinition]:
    """Check original declaration/ABI correspondence, without issuing authority."""
    if (
        type(binding) is not OntologyObjectClassBinding
        or type(definitions) is not tuple
        or any(type(d) is not SchemaActionDefinition for d in definitions)
    ):
        raise ObjectActionError("action.invalid_binding")
    actions = tuple(a for a in binding.actions if a.action_ref == action_ref)
    declared = tuple(d for d in definitions if d.action_ref == action_ref)
    if len(actions) != 1 or len(declared) != 1:
        raise ObjectActionError("action.action_mismatch")
    action, definition = actions[0], declared[0]
    if (
        action.role is not OntologyObjectActionRole.INSTANCE
        or action.relationship_constructor_paths
        or action.method_name in ACTION_RESERVED_NAMES
        or definition.target_type_ref != binding.type_ref
        or not (
            definition.result_shape is None
            and definition.result_value_mode is ActionValueMode.VALUE
            or definition.result_shape is not None
            and definition.result_shape.kind is ShapeKind.NAMED
            and definition.result_shape.type_ref == binding.type_ref
            and definition.result_value_mode is ActionValueMode.INSTANCE_REF
        )
        or definition.mutation_scope is not MutationScope.TARGET
        or tuple(p.to_wire() for p in action.parameters)
        != tuple(p.to_wire() for p in definition.parameters)
    ):
        raise ObjectActionError("action.unsupported_profile")
    return action, definition


def require_action_arguments(
    action: OntologyObjectActionBinding,
    schema: TypeSchemaBundle,
    arguments: ScalarArguments,
) -> ScalarArguments:
    """Validate declared values without coercion; omission and null stay distinct."""
    if (
        type(action) is not OntologyObjectActionBinding
        or type(schema) is not TypeSchemaBundle
    ):
        raise ObjectActionError("action.invalid_binding")
    for parameter in action.parameters:
        if parameter.value_mode is not ActionValueMode.VALUE or not (
            parameter.shape.kind is ShapeKind.SCALAR
            and parameter.shape.scalar_kind in _KINDS
            or _enum_values(parameter.shape, schema)
        ):
            raise ObjectActionError("action.unsupported_profile")
    if type(arguments) is not tuple:
        raise ObjectActionError("action.invalid_arguments")
    for row in arguments:
        if type(row) is not tuple or len(row) != 2 or type(row[0]) is not str:
            raise ObjectActionError("action.invalid_arguments")
    refs = tuple(row[0] for row in arguments)
    if (
        len(refs) != len(set(refs))
        or any(ref not in {p.parameter_ref for p in action.parameters} for ref in refs)
        or any(p.required and p.parameter_ref not in refs for p in action.parameters)
        or refs
        != tuple(p.parameter_ref for p in action.parameters if p.parameter_ref in refs)
    ):
        raise ObjectActionError("action.invalid_arguments")
    values = dict(arguments)
    for parameter in action.parameters:
        if parameter.parameter_ref not in values:
            continue
        value = values[parameter.parameter_ref]
        if value is None:
            if not parameter.nullable:
                raise ObjectActionError("action.invalid_arguments")
        elif parameter.shape.kind is ShapeKind.SCALAR:
            kind = parameter.shape.scalar_kind
            if kind is None or type(value) is not _KINDS.get(kind):
                raise ObjectActionError("action.invalid_arguments")
        elif type(value) is not str or value not in _enum_values(
            parameter.shape, schema
        ):
            raise ObjectActionError("action.invalid_arguments")
        if type(value) is str and (len(value.encode()) > 4096 or "\0" in value):
            raise ObjectActionError("action.invalid_arguments")
        if type(value) is int and not -(2**53 - 1) <= value <= 2**53 - 1:
            raise ObjectActionError("action.invalid_arguments")
    return arguments


@dataclass(slots=True)
class _Lifetime:
    closed: bool = False


@dataclass(frozen=True, slots=True)
class ObjectActionContext:
    """Reusable infrastructure descriptions, with a fresh bound operation per call."""

    binding: OntologyObjectClassBinding
    schema: TypeSchemaBundle
    definitions: tuple[SchemaActionDefinition, ...]
    fragment_closure_digest: str
    provider_key: str
    provider_generation: str
    branch_ref: str
    projection_ref: str
    configuration_binding: bytes
    invoker: ObjectActionInvoker
    _lifetime: _Lifetime = field(default_factory=_Lifetime, init=False, repr=False)

    def __post_init__(self) -> None:
        if (
            type(self.binding) is not OntologyObjectClassBinding
            or type(self.schema) is not TypeSchemaBundle
            or type(self.definitions) is not tuple
            or not self.definitions
            or any(type(d) is not SchemaActionDefinition for d in self.definitions)
            or len({d.action_ref for d in self.definitions}) != len(self.definitions)
            or not _digest(self.fragment_closure_digest)
            or any(
                not _text(v)
                for v in (
                    self.provider_key,
                    self.provider_generation,
                    self.branch_ref,
                    self.projection_ref,
                )
            )
            or not _body(self.configuration_binding)
        ):
            raise ObjectActionError("action.invalid_context")
        for declaration in self.definitions:
            action, _ = action_definition(
                self.binding, self.definitions, declaration.action_ref
            )
            for parameter in action.parameters:
                if parameter.value_mode is not ActionValueMode.VALUE or not (
                    parameter.shape.kind is ShapeKind.SCALAR
                    and parameter.shape.scalar_kind in _KINDS
                    or _enum_values(parameter.shape, self.schema)
                ):
                    raise ObjectActionError("action.unsupported_profile")
        object.__setattr__(
            self,
            "definitions",
            tuple(sorted(self.definitions, key=lambda d: d.action_ref)),
        )

    def close(self) -> None:
        """Prevent new dispatch; a borrowed host or transport remains open."""
        self._lifetime.closed = True

    @property
    def closed(self) -> bool:
        return self._lifetime.closed

    def bind(
        self,
        facade_type: type[_Actions],
        target: OntologyRuntimeActionInstanceRefTarget,
        *,
        action_ref: str,
        invocation_key: str,
        expected_revision_ref: str,
        deadline: float,
    ) -> _Actions:
        if self._lifetime.closed:
            raise ObjectActionError("action.context_closed")
        if (
            not isinstance(facade_type, type)
            or not issubclass(facade_type, OntologyObjectActions)
            or type(target) is not OntologyRuntimeActionInstanceRefTarget
            or (target.type_ref, target.provider_key, target.provider_generation)
            != (self.binding.type_ref, self.provider_key, self.provider_generation)
            or not _text(invocation_key)
            or not _text(expected_revision_ref)
            or not _deadline(deadline)
        ):
            raise ObjectActionError("action.invalid_binding")
        return facade_type(
            self,
            target,
            action_ref=action_ref,
            invocation_key=invocation_key,
            expected_revision_ref=expected_revision_ref,
            deadline=deadline,
        )


class OntologyObjectActions:
    """Generated methods over one injected, single-use instance operation."""

    __ontology_type_ref__: ClassVar[str]
    __ontology_binding_digest__: ClassVar[str]
    __ontology_dependency_closure_digest__: ClassVar[str]
    __ontology_schema_digest__: ClassVar[str]
    __ontology_action_bindings__: ClassVar[tuple[tuple[str, str], ...]]

    def __init__(
        self,
        context: ObjectActionContext,
        target: OntologyRuntimeActionInstanceRefTarget,
        *,
        action_ref: str,
        invocation_key: str,
        expected_revision_ref: str,
        deadline: float,
    ) -> None:
        if (
            type(context) is not ObjectActionContext
            or type(target) is not OntologyRuntimeActionInstanceRefTarget
            or (target.type_ref, target.provider_key, target.provider_generation)
            != (
                context.binding.type_ref,
                context.provider_key,
                context.provider_generation,
            )
            or not _text(invocation_key)
            or not _text(expected_revision_ref)
            or not _deadline(deadline)
        ):
            raise ObjectActionError("action.invalid_binding")
        if (
            type(self).__name__ != context.binding.class_name
            or self.__ontology_type_ref__ != context.binding.type_ref
            or self.__ontology_binding_digest__ != context.binding.binding_digest
            or self.__ontology_dependency_closure_digest__
            != context.fragment_closure_digest
            or self.__ontology_schema_digest__ != context.schema.schema_digest
            or self.__ontology_action_bindings__
            != tuple(
                (
                    d.action_ref,
                    next(
                        a.method_name
                        for a in context.binding.actions
                        if a.action_ref == d.action_ref
                    ),
                )
                for d in context.definitions
            )
        ):
            raise ObjectActionError("action.binding_mismatch")
        action, definition = action_definition(
            context.binding, context.definitions, action_ref
        )
        self._action: OntologyObjectActionBinding = action
        self._returns_object: bool = definition.result_shape is not None
        self._context: ObjectActionContext | None = context
        self._target: OntologyRuntimeActionInstanceRefTarget = target
        self._key: str = invocation_key
        self._expected: str = expected_revision_ref
        self._deadline: float = deadline
        self._state: str = "ready"
        self._receipt: ObjectActionReceipt | None = None
        self._result: ObjectActionResult | None = None

    @property
    def object_reference(self) -> OntologyRuntimeActionInstanceRefTarget:
        return self._target

    @property
    def invocation_state(self) -> str:
        return self._state

    @property
    def invocation_receipt(self) -> ObjectActionReceipt | None:
        return self._receipt

    @property
    def invocation_result(self) -> ObjectActionResult | None:
        """Retain original history/outcome data, including a late known commit."""
        return self._result

    def _close_operation(self) -> None:
        """Infrastructure-only local retirement; leaves declared `close` available."""
        if self._state == "ready":
            self._state, self._context = "closed", None

    async def _invoke_action(
        self, action_ref: str, **arguments: object
    ) -> OntologyReturnedObject | None:
        if self._state != "ready":
            raise ObjectActionError("action.operation_consumed")
        self._state = "pending"
        try:
            context = self._context
            if context is None or context.closed:
                raise ObjectActionError("action.context_closed")
            if action_ref != self._action.action_ref:
                raise ObjectActionError("action.action_mismatch")
            declared = {p.parameter_ref for p in self._action.parameters}
            if not set(arguments) <= declared:
                raise ObjectActionError("action.invalid_arguments")
            ordered = tuple(
                (p.parameter_ref, cast(ScalarValue, arguments[p.parameter_ref]))
                for p in self._action.parameters
                if p.parameter_ref in arguments
            )
            _ = require_action_arguments(self._action, context.schema, ordered)
            request = ObjectActionRequest(
                self._target,
                action_ref,
                ordered,
                self._key,
                context.binding.binding_digest,
                context.fragment_closure_digest,
                context.branch_ref,
                context.projection_ref,
                context.configuration_binding,
                self._expected,
                self._deadline,
            )
            if time.monotonic() >= self._deadline:
                raise TimeoutError("action.deadline_elapsed")
            result = await context.invoker.invoke_action(request)
            if (
                type(result) is not ObjectActionResult
                or type(result.request) is not ObjectActionRequest
                or result.request != request
                or type(result.receipt) is not ObjectActionReceipt
                or result.receipt.base_revision_ref != request.expected_revision_ref
                or not _body(result.history_correspondence)
                or result.settled is not True
                or result.worker_cleaned is not True
                or result.reread_verified is not True
            ):
                raise ObjectActionError("action.invalid_result")
            # Preserve the original outcome even if the deadline/context ceased
            # during dispatch. Failure here is not evidence of rollback.
            self._receipt = result.receipt
            self._result = result
            if self._returns_object:
                if (
                    type(result.returned_object)
                    is not OntologyRuntimeActionInstanceRefTarget
                    or result.returned_object != request.target
                ):
                    raise ObjectActionError("action.invalid_returned_object")
            elif result.returned_object is not None:
                raise ObjectActionError("action.unexpected_returned_object")
            if time.monotonic() >= self._deadline:
                raise TimeoutError("action.deadline_elapsed")
            if context.closed:
                raise ObjectActionError(
                    "action.context_closed", recovery_ref=result.receipt.attempt_ref
                )
            self._state = "complete"
            if self._returns_object:
                return OntologyReturnedObject(
                    cast(
                        OntologyRuntimeActionInstanceRefTarget, result.returned_object
                    ),
                    result.receipt,
                    result.history_correspondence,
                )
            return None
        except BaseException as error:
            self._state = "failed"
            if self._result is not None:
                for name in ("attempt_ref", "recovery_ref"):
                    if getattr(error, name, None) is None:
                        setattr(error, name, self._result.receipt.attempt_ref)
            raise
        finally:
            self._context = None
