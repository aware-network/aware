"""Bound completed scalar calls. Ontology retains execution authority.

This trusted-local profile has no snapshot reads, implicit activation, retries
or multi-method transaction. Generated metadata checks consistency only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Protocol, TypeVar, cast

from .local_scalar import (
    LocalScalarClient,
    ScalarInvocationError,
    ScalarReceipt,
    ScalarResult,
)
from .owner_values import (
    ActionValueMode,
    OntologyObjectActionBinding,
    OntologyObjectClassBinding,
    ScalarKind,
    ShapeKind,
)

ScalarValue = bool | int | str | None
ScalarArguments = tuple[tuple[str, ScalarValue], ...]
_Facade = TypeVar("_Facade", bound="OntologyObjectFacade")
_KINDS = {ScalarKind.BOOLEAN: bool, ScalarKind.INTEGER: int, ScalarKind.STRING: str}
_RESERVED = {"close", "invocation_receipt", "invocation_state"}


class ScalarActionInvoker(Protocol):
    """Infrastructure binds caller/deadline; the host authenticates execution."""

    async def invoke_action(
        self, *, object_ref: str, action_ref: str,
        arguments: ScalarArguments, invocation_key: str,
    ) -> ScalarResult: ...


def _text(value: object) -> bool:
    return type(value) is str and 0 < len(value.encode("utf-8")) <= 4096 and "\0" not in value


def _digest(value: object) -> bool:
    return (type(value) is str and len(value) == 71 and value.startswith("sha256:")
            and all(ch in "0123456789abcdef" for ch in value[7:]))


def _require_profile(binding: OntologyObjectClassBinding) -> None:
    if type(binding) is not OntologyObjectClassBinding or binding.fields or binding.relationships:
        raise ScalarInvocationError("facade.unsupported_profile")
    for action in binding.actions:
        if (action.role.value != "instance" or action.relationship_constructor_paths
                or action.method_name in _RESERVED):
            raise ScalarInvocationError("facade.unsupported_profile")
        for parameter in action.parameters:
            if (parameter.value_mode is not ActionValueMode.VALUE
                    or parameter.shape.kind is not ShapeKind.SCALAR
                    or parameter.shape.scalar_kind not in _KINDS):
                raise ScalarInvocationError("facade.unsupported_profile")


@dataclass(frozen=True, slots=True)
class _CompletedScalarInvoker:
    client: LocalScalarClient
    binding: OntologyObjectClassBinding

    async def invoke_action(
        self, *, object_ref: str, action_ref: str,
        arguments: ScalarArguments, invocation_key: str,
    ) -> ScalarResult:
        selected = tuple(a for a in self.binding.actions if a.action_ref == action_ref)
        if arguments or len(selected) != 1 or selected[0].parameters:
            raise ScalarInvocationError("facade.arguments_unavailable")
        return await self.client.invoke_scalar(
            object_ref=object_ref, action_ref=action_ref, invocation_key=invocation_key,
        )


@dataclass(frozen=True, slots=True)
class ScalarObjectContext:
    """Reusable descriptions and infrastructure wiring, not a live operation."""

    object_ref: str
    binding: OntologyObjectClassBinding
    fragment_closure_digest: str
    invoker: ScalarActionInvoker

    def __post_init__(self) -> None:
        if not _text(self.object_ref) or not _digest(self.fragment_closure_digest):
            raise ScalarInvocationError("facade.invalid_context")
        _require_profile(self.binding)

    @classmethod
    def for_local_scalar(
        cls, *, client: LocalScalarClient, object_ref: str,
        binding: OntologyObjectClassBinding, fragment_closure_digest: str,
    ) -> ScalarObjectContext:
        """Wrap the accepted no-argument v1 client without extending its wire."""
        if type(client) is not LocalScalarClient:
            raise ScalarInvocationError("facade.invalid_context")
        return cls(object_ref, binding, fragment_closure_digest, _CompletedScalarInvoker(client, binding))

    def bind(
        self, facade_type: type[_Facade], *, action_ref: str, invocation_key: str,
    ) -> _Facade:
        """Infrastructure creates one Action-specific operation for injection."""
        if not isinstance(facade_type, type) or not issubclass(facade_type, OntologyObjectFacade):
            raise ScalarInvocationError("facade.invalid_binding")
        return facade_type(self, action_ref=action_ref, invocation_key=invocation_key)


class OntologyObjectFacade:
    """Public base for the scalar successor's generated Python Objects."""

    __ontology_type_ref__: ClassVar[str]
    __ontology_binding_digest__: ClassVar[str]
    __ontology_dependency_closure_digest__: ClassVar[str]
    __ontology_action_bindings__: ClassVar[tuple[tuple[str, str], ...]]

    def __init__(
        self, context: ScalarObjectContext, *, action_ref: str, invocation_key: str,
    ) -> None:
        if (type(context) is not ScalarObjectContext or not _text(invocation_key)
                or not _text(action_ref)):
            raise ScalarInvocationError("facade.invalid_binding")
        binding = context.binding
        if (
            type(self).__name__ != binding.class_name
            or getattr(self, "__ontology_type_ref__", None) != binding.type_ref
            or getattr(self, "__ontology_binding_digest__", None) != binding.binding_digest
            or getattr(self, "__ontology_dependency_closure_digest__", None) != context.fragment_closure_digest
            or getattr(self, "__ontology_action_bindings__", None) != tuple(
                (action.action_ref, action.method_name) for action in binding.actions)
        ):
            raise ScalarInvocationError("facade.binding_mismatch")
        matches = tuple(action for action in binding.actions if action.action_ref == action_ref)
        if len(matches) != 1:
            raise ScalarInvocationError("facade.action_mismatch")
        self._context: ScalarObjectContext = context
        self._action: OntologyObjectActionBinding = matches[0]
        self._invocation_key: str = invocation_key
        self._state: str = "ready"
        self._receipt: ScalarReceipt | None = None

    @property
    def invocation_state(self) -> str:
        return self._state

    @property
    def invocation_receipt(self) -> ScalarReceipt | None:
        return self._receipt

    def close(self) -> None:
        if self._state == "ready":
            self._state = "closed"

    async def _invoke_action(self, action_ref: str, **arguments: object) -> ScalarValue:
        if self._state != "ready":
            raise ScalarInvocationError("facade.operation_consumed")
        # Consume before argument refusal or transport; a failure cannot revive it.
        self._state = "pending"
        try:
            if action_ref != self._action.action_ref:
                raise ScalarInvocationError("facade.action_mismatch")
            parameters = self._action.parameters
            if (not set(arguments) <= {p.parameter_ref for p in parameters}
                    or any(p.required and p.parameter_ref not in arguments for p in parameters)):
                raise ScalarInvocationError("facade.invalid_arguments")
            ordered: list[tuple[str, ScalarValue]] = []
            for parameter in parameters:
                if parameter.parameter_ref not in arguments:
                    continue
                value = arguments[parameter.parameter_ref]
                kind = parameter.shape.scalar_kind
                if kind is None:
                    raise ScalarInvocationError("facade.unsupported_profile")
                expected = _KINDS.get(kind)
                if (value is None and not parameter.nullable
                        or value is not None and type(value) is not expected):
                    raise ScalarInvocationError("facade.invalid_arguments")
                if type(value) not in (bool, int, str, type(None)):
                    raise ScalarInvocationError("facade.invalid_arguments")
                ordered.append((parameter.parameter_ref, cast(ScalarValue, value)))
            result = await self._context.invoker.invoke_action(
                object_ref=self._context.object_ref, action_ref=action_ref,
                arguments=tuple(ordered), invocation_key=self._invocation_key,
            )
            if (type(result) is not ScalarResult or type(result.receipt) is not ScalarReceipt
                    or type(result.value) not in (bool, int, str, type(None))):
                raise ScalarInvocationError("facade.invalid_result")
            receipt = result.receipt
            if (not _text(receipt.invocation_ref) or not _text(receipt.attempt_ref)
                    or not _digest(receipt.receipt_digest) or receipt.outcome != "no_op"):
                raise ScalarInvocationError("facade.invalid_result")
            self._receipt = result.receipt
            self._state = "complete"
            return result.value
        except BaseException:
            self._state = "failed"
            raise
