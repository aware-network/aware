"""Declared constructor successor for the same neutral instance-Action profile.

Defaults belong to the original FunctionImpl. Omission is transmitted as
omission; the client does not recreate constructor behavior or derive targets.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import ClassVar, Protocol, TypeVar, cast
from uuid import UUID

from aware_meta_type_schema import TypeSchemaBundle

from .actions import ObjectActionError, _body, _deadline, _enum_values
from .constructor import ObjectCreationReceipt, ObjectCreationResult
from .facade import ScalarArguments, ScalarValue, _digest, _text
from .owner_values import (
    ActionValueMode,
    OntologyObjectActionRole,
    OntologyObjectClassBinding,
    OntologyRuntimeActionInstanceRefTarget,
    ScalarKind,
    SchemaActionDefinition,
    ShapeKind,
)

_Factory = TypeVar("_Factory", bound="OntologyObjectFactory")
_KINDS = {
    ScalarKind.BOOLEAN: bool,
    ScalarKind.INTEGER: int,
    ScalarKind.STRING: str,
    ScalarKind.UUID: str,
}


@dataclass(frozen=True, slots=True)
class ObjectFactoryRequest:
    type_ref: str
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
            any(
                not _text(v)
                for v in (
                    self.type_ref,
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
            raise ObjectActionError("factory.invalid_request")
        for row in self.arguments:
            if (
                type(row) is not tuple
                or len(row) != 2
                or not _text(row[0])
                or type(row[1]) not in (bool, int, str, type(None))
            ):
                raise ObjectActionError("factory.invalid_request")


@dataclass(frozen=True, slots=True)
class ObjectFactoryResult:
    request: ObjectFactoryRequest
    creation: ObjectCreationResult
    history_correspondence: bytes


@dataclass(frozen=True, slots=True)
class OntologyCreatedObject:
    """Original settled identity/receipt data, without a read or Action port."""

    creation: ObjectCreationResult
    history_correspondence: bytes

    @property
    def object_reference(self) -> OntologyRuntimeActionInstanceRefTarget:
        return self.creation.target

    @property
    def invocation_receipt(self) -> ObjectCreationReceipt:
        return self.creation.receipt


class ObjectFactoryInvoker(Protocol):
    async def invoke_constructor(
        self, request: ObjectFactoryRequest, /
    ) -> ObjectFactoryResult: ...


def require_factory_arguments(
    binding: OntologyObjectClassBinding,
    schema: TypeSchemaBundle,
    definition: SchemaActionDefinition,
    arguments: ScalarArguments,
) -> ScalarArguments:
    if (
        type(binding) is not OntologyObjectClassBinding
        or type(schema) is not TypeSchemaBundle
        or type(definition) is not SchemaActionDefinition
        or type(arguments) is not tuple
    ):
        raise ObjectActionError("factory.invalid_binding")
    matches = tuple(a for a in binding.actions if a.action_ref == definition.action_ref)
    if (
        len(matches) != 1
        or matches[0].role is not OntologyObjectActionRole.CONSTRUCTOR
        or matches[0].relationship_constructor_paths
        or definition.target_type_ref != binding.type_ref
        or definition.result_shape is None
        or definition.result_shape.kind is not ShapeKind.NAMED
        or definition.result_shape.type_ref != binding.type_ref
        or definition.result_value_mode is not ActionValueMode.INSTANCE_REF
        or tuple(p.to_wire() for p in matches[0].parameters)
        != tuple(p.to_wire() for p in definition.parameters)
    ):
        raise ObjectActionError("factory.unsupported_profile")
    for row in arguments:
        if type(row) is not tuple or len(row) != 2 or type(row[0]) is not str:
            raise ObjectActionError("factory.invalid_arguments")
    # Check the entire declared profile before testing required omissions. A
    # missing required value must not conceal an unsupported declaration.
    for p in definition.parameters:
        if p.value_mode is not ActionValueMode.VALUE or not (
            p.shape.kind is ShapeKind.SCALAR
            and p.shape.scalar_kind in _KINDS
            or _enum_values(p.shape, schema)
        ):
            raise ObjectActionError("factory.unsupported_profile")
    refs = tuple(row[0] for row in arguments)
    if (
        len(refs) != len(set(refs))
        or any(
            ref not in {p.parameter_ref for p in definition.parameters} for ref in refs
        )
        or any(
            p.required and p.parameter_ref not in refs for p in definition.parameters
        )
        or refs
        != tuple(
            p.parameter_ref for p in definition.parameters if p.parameter_ref in refs
        )
    ):
        raise ObjectActionError("factory.invalid_arguments")
    values = dict(arguments)
    for p in definition.parameters:
        if p.parameter_ref not in values:
            continue
        value = values[p.parameter_ref]
        if value is None:
            if not p.nullable:
                raise ObjectActionError("factory.invalid_arguments")
            continue
        if p.shape.kind is ShapeKind.SCALAR:
            kind = p.shape.scalar_kind
            if kind is None or type(value) is not _KINDS.get(kind):
                raise ObjectActionError("factory.invalid_arguments")
            if kind is ScalarKind.UUID:
                try:
                    if str(UUID(cast(str, value))) != value:
                        raise ValueError("noncanonical UUID")
                except ValueError as error:
                    raise ObjectActionError("factory.invalid_arguments") from error
        elif type(value) is not str or value not in _enum_values(p.shape, schema):
            raise ObjectActionError("factory.invalid_arguments")
        if type(value) is str and (len(value.encode()) > 4096 or "\0" in value):
            raise ObjectActionError("factory.invalid_arguments")
        if type(value) is int and not -(2**53 - 1) <= value <= 2**53 - 1:
            raise ObjectActionError("factory.invalid_arguments")
    return arguments


@dataclass(slots=True)
class _Lifetime:
    closed: bool = False


@dataclass(frozen=True, slots=True)
class ObjectFactoryContext:
    binding: OntologyObjectClassBinding
    schema: TypeSchemaBundle
    definition: SchemaActionDefinition
    fragment_closure_digest: str
    provider_key: str
    provider_generation: str
    branch_ref: str
    projection_ref: str
    configuration_binding: bytes
    invoker: ObjectFactoryInvoker
    _lifetime: _Lifetime = field(default_factory=_Lifetime, init=False, repr=False)

    def __post_init__(self) -> None:
        # Validate the full declaration with representative required omissions
        # checked later. The original host still validates all original products.
        if (
            type(self.binding) is not OntologyObjectClassBinding
            or type(self.schema) is not TypeSchemaBundle
            or type(self.definition) is not SchemaActionDefinition
            or not _digest(self.fragment_closure_digest)
            or not _body(self.configuration_binding)
            or any(
                not _text(v)
                for v in (
                    self.provider_key,
                    self.provider_generation,
                    self.branch_ref,
                    self.projection_ref,
                )
            )
        ):
            raise ObjectActionError("factory.invalid_context")
        # No defaults or sample values are synthesized to validate a context.
        try:
            require_factory_arguments(self.binding, self.schema, self.definition, ())
        except ObjectActionError as error:
            if error.code != "factory.invalid_arguments":
                raise

    @property
    def closed(self) -> bool:
        return self._lifetime.closed

    def close(self) -> None:
        self._lifetime.closed = True

    def bind(
        self,
        factory_type: type[_Factory],
        *,
        invocation_key: str,
        expected_revision_ref: str,
        deadline: float,
    ) -> _Factory:
        if not isinstance(factory_type, type) or not issubclass(
            factory_type, OntologyObjectFactory
        ):
            raise ObjectActionError("factory.invalid_binding")
        return factory_type(
            self,
            invocation_key=invocation_key,
            expected_revision_ref=expected_revision_ref,
            deadline=deadline,
        )


class OntologyObjectFactory:
    __ontology_type_ref__: ClassVar[str]
    __ontology_binding_digest__: ClassVar[str]
    __ontology_dependency_closure_digest__: ClassVar[str]
    __ontology_schema_digest__: ClassVar[str]
    __ontology_constructor_ref__: ClassVar[str]

    def __init__(
        self,
        context: ObjectFactoryContext,
        *,
        invocation_key: str,
        expected_revision_ref: str,
        deadline: float,
    ) -> None:
        if (
            type(context) is not ObjectFactoryContext
            or context.closed
            or not _text(invocation_key)
            or not _text(expected_revision_ref)
            or not _deadline(deadline)
        ):
            raise ObjectActionError("factory.invalid_binding")
        if (
            type(self).__name__ != context.binding.class_name + "Factory"
            or self.__ontology_type_ref__ != context.binding.type_ref
            or self.__ontology_binding_digest__ != context.binding.binding_digest
            or self.__ontology_dependency_closure_digest__
            != context.fragment_closure_digest
            or self.__ontology_schema_digest__ != context.schema.schema_digest
            or self.__ontology_constructor_ref__ != context.definition.action_ref
        ):
            raise ObjectActionError("factory.binding_mismatch")
        self._context: ObjectFactoryContext | None = context
        self._key, self._expected, self._deadline = (
            invocation_key,
            expected_revision_ref,
            deadline,
        )
        self._state: str = "ready"
        self._result: ObjectFactoryResult | None = None

    @property
    def invocation_state(self) -> str:
        return self._state

    @property
    def invocation_result(self) -> ObjectFactoryResult | None:
        return self._result

    async def _invoke_constructor(
        self, action_ref: str, **arguments: object
    ) -> OntologyCreatedObject:
        if self._state != "ready":
            raise ObjectActionError("factory.operation_consumed")
        self._state = "pending"
        try:
            c = self._context
            if c is None or c.closed:
                raise ObjectActionError("factory.context_closed")
            if action_ref != c.definition.action_ref:
                raise ObjectActionError("factory.action_mismatch")
            if not set(arguments) <= {p.parameter_ref for p in c.definition.parameters}:
                raise ObjectActionError("factory.invalid_arguments")
            ordered = tuple(
                (p.parameter_ref, cast(ScalarValue, arguments[p.parameter_ref]))
                for p in c.definition.parameters
                if p.parameter_ref in arguments
            )
            _ = require_factory_arguments(c.binding, c.schema, c.definition, ordered)
            request = ObjectFactoryRequest(
                c.binding.type_ref,
                action_ref,
                ordered,
                self._key,
                c.binding.binding_digest,
                c.fragment_closure_digest,
                c.branch_ref,
                c.projection_ref,
                c.configuration_binding,
                self._expected,
                self._deadline,
            )
            if time.monotonic() >= self._deadline:
                raise TimeoutError("factory.deadline_elapsed")
            result = await c.invoker.invoke_constructor(request)
            if (
                type(result) is not ObjectFactoryResult
                or type(result.request) is not ObjectFactoryRequest
                or result.request != request
                or type(result.creation) is not ObjectCreationResult
                or not _body(result.history_correspondence)
            ):
                raise ObjectActionError("factory.invalid_result")
            creation = result.creation
            if (
                type(creation.target) is not OntologyRuntimeActionInstanceRefTarget
                or type(creation.receipt) is not ObjectCreationReceipt
                or (creation.type_ref, creation.target.type_ref)
                != (request.type_ref, request.type_ref)
                or (
                    creation.action_ref,
                    creation.invocation_key,
                    creation.binding_digest,
                    creation.fragment_closure_digest,
                )
                != (
                    action_ref,
                    self._key,
                    c.binding.binding_digest,
                    c.fragment_closure_digest,
                )
                or (creation.target.provider_key, creation.target.provider_generation)
                != (c.provider_key, c.provider_generation)
                or (creation.receipt.provider_key, creation.receipt.provider_generation)
                != (c.provider_key, c.provider_generation)
                or creation.settled is not True
                or creation.worker_cleaned is not True
                or creation.reread_verified is not True
            ):
                raise ObjectActionError("factory.invalid_result")
            ObjectCreationReceipt.__post_init__(creation.receipt)
            self._result = result
            if time.monotonic() >= self._deadline:
                raise TimeoutError("factory.deadline_elapsed")
            if c.closed:
                raise ObjectActionError(
                    "factory.context_closed", recovery_ref=creation.receipt.attempt_ref
                )
            self._state = "complete"
            return OntologyCreatedObject(creation, result.history_correspondence)
        except BaseException as error:
            self._state = "failed"
            if self._result is not None:
                for name in ("attempt_ref", "recovery_ref"):
                    if getattr(error, name, None) is None:
                        setattr(error, name, self._result.creation.receipt.attempt_ref)
            raise
        finally:
            self._context = None
