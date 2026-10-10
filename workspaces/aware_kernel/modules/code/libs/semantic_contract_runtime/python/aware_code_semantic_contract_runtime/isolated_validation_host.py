"""Isolated host/origin mechanics, deliberately ineligible for registry issuance.

The installer accepts fixture composition, not authenticated bootstrap evidence.
Nothing in this module authenticates that fixture, grants namespace entitlement,
issues Workspace handles, or enters selected-provider execution.
"""

from __future__ import annotations

import inspect
import os
from collections.abc import Callable
from dataclasses import dataclass, fields
from threading import RLock
from typing import Any, Never
from weakref import WeakKeyDictionary

from .contracts import ContractViolation, canonical_json_bytes
from .retained_admission_interfaces import RetainedSemanticAdmissionExpectation
from .runtime import SemanticContractRuntime


class IsolatedValidationHost:
    def __new__(cls) -> Never:
        raise TypeError("isolated host is module-issued")

    def __init_subclass__(cls, **kwargs: object) -> Never:
        raise TypeError("isolated host is sealed")

    def __reduce__(self) -> Never:
        raise TypeError("isolated host cannot be copied or serialized")


class IsolatedWorkspaceValidationOrigin:
    def __new__(cls) -> Never:
        raise TypeError("isolated origin is module-issued")

    def __init_subclass__(cls, **kwargs: object) -> Never:
        raise TypeError("isolated origin is sealed")

    def __reduce__(self) -> Never:
        raise TypeError("isolated origin cannot be copied or serialized")


@dataclass(frozen=True, slots=True)
class IsolatedWorkspaceOriginProduct:
    observation_runtime: object
    membership_runtime: object
    issuer: object


@dataclass(frozen=True, slots=True)
class _Entrance:
    receiver: object
    name: str
    descriptor: object
    callable: Callable[..., Any]
    function: object

    def check(self) -> None:
        if (
            not inspect.ismethod(self.callable)
            or self.callable.__self__ is not self.receiver
            or self.callable.__func__ is not self.function
            or inspect.getattr_static(self.receiver, self.name) is not self.descriptor
        ):
            raise ContractViolation("registered method entrance changed")


def _entrance(receiver: object, name: str) -> _Entrance:
    descriptor = inspect.getattr_static(receiver, name)
    method = getattr(receiver, name)  # Capture once, at isolated registration only.
    if not inspect.ismethod(method) or method.__self__ is not receiver:
        raise TypeError("original bound method required")
    result = _Entrance(receiver, name, descriptor, method, method.__func__)
    result.check()
    return result


@dataclass(slots=True)
class _Host:
    runtime: SemanticContractRuntime
    runtime_token: object
    generation: object
    observation: object
    membership: object
    factory: _Entrance
    pid: int
    binding_attempted: bool = False
    closed: bool = False


@dataclass(frozen=True, slots=True)
class _Origin:
    host: IsolatedValidationHost
    issuer: object
    package: _Entrance
    inventory: _Entrance
    assignments: _Entrance


_HOSTS: WeakKeyDictionary[IsolatedValidationHost, _Host] = WeakKeyDictionary()
_ORIGINS: WeakKeyDictionary[IsolatedWorkspaceValidationOrigin, _Origin] = (
    WeakKeyDictionary()
)
_LOCK = RLock()


def install_isolated_validation_host(
    *,
    runtime: SemanticContractRuntime,
    generation_identity: object,
    observation_runtime: object,
    membership_runtime: object,
    factory_owner: object,
    factory_method: str,
) -> IsolatedValidationHost:
    """Fixture-only composition; this entrance does not admit trusted bootstrap."""
    if type(runtime) is not SemanticContractRuntime:
        raise TypeError("exact Code runtime required")
    if any(
        v is None
        for v in (generation_identity, observation_runtime, membership_runtime)
    ):
        raise TypeError("original fixture contexts required")
    factory = _entrance(factory_owner, factory_method)
    if inspect.signature(factory.callable).parameters:
        raise TypeError("isolated owner factory must take no arguments")
    result = object.__new__(IsolatedValidationHost)
    with _LOCK:
        _HOSTS[result] = _Host(
            runtime,
            runtime._runtime_token,
            generation_identity,
            observation_runtime,
            membership_runtime,
            factory,
            os.getpid(),
        )
    return result


def _host(handle: IsolatedValidationHost) -> _Host:
    if type(handle) is not IsolatedValidationHost:
        raise TypeError("exact isolated host required")
    state = _HOSTS.get(handle)
    if state is None or state.closed:
        raise ContractViolation("isolated host is not live")
    if (
        state.pid != os.getpid()
        or state.runtime._runtime_token is not state.runtime_token
    ):
        raise ContractViolation("isolated host process/runtime changed")
    state.factory.check()
    return state


def bind_isolated_workspace_validation_origin(
    host: IsolatedValidationHost,
) -> IsolatedWorkspaceValidationOrigin:
    with _LOCK:
        state = _host(host)
        if state.binding_attempted:
            raise ContractViolation("isolated origin binding already attempted")
        state.binding_attempted = True
        factory = state.factory.callable
    product = factory()
    with _LOCK:
        _host(host)
        if type(product) is not IsolatedWorkspaceOriginProduct:
            raise TypeError("exact isolated owner product required")
        if (
            product.observation_runtime is not state.observation
            or product.membership_runtime is not state.membership
        ):
            raise ContractViolation("owner factory substituted original context")
        result = object.__new__(IsolatedWorkspaceValidationOrigin)
        _ORIGINS[result] = _Origin(
            host,
            product.issuer,
            _entrance(product.issuer, "validate_package_context_admission"),
            _entrance(product.issuer, "validate_declaration_inventory_admission"),
            _entrance(product.issuer, "validate_occurrence_assignments"),
        )
    return result


def _origin(handle: IsolatedWorkspaceValidationOrigin) -> tuple[_Origin, _Host]:
    if type(handle) is not IsolatedWorkspaceValidationOrigin:
        raise TypeError("exact isolated origin required")
    state = _ORIGINS.get(handle)
    if state is None:
        raise ContractViolation("isolated origin is not retained")
    host = _host(state.host)
    for entrance in (state.package, state.inventory, state.assignments):
        if entrance.receiver is not state.issuer:
            raise ContractViolation("original issuer changed")
        entrance.check()
    return state, host


def _expected(value: RetainedSemanticAdmissionExpectation, host: _Host) -> tuple:
    if type(value) is not RetainedSemanticAdmissionExpectation:
        raise TypeError("exact expected context required")
    if (
        value.runtime is not host.runtime
        or value.generation_identity is not host.generation
        or type(value.process_id) is not int
        or value.process_id != host.pid
    ):
        raise ContractViolation("expected runtime/process/generation differs")
    if value.stage not in ("source_planning", "authority_derivation"):
        raise ContractViolation("expected stage differs")
    identities = (value.operation_identity, value.selected_provider_registration)
    wire = {}
    for field in fields(value):
        if field.name in (
            "runtime",
            "generation_identity",
            "operation_identity",
            "selected_provider_registration",
        ):
            continue
        item = getattr(value, field.name)
        wire[field.name] = item if type(item) in (str, int) else item.to_wire()
    return identities, canonical_json_bytes(wire)


def validate_isolated_workspace_admission(
    origin: IsolatedWorkspaceValidationOrigin,
    admission: object,
    *,
    expected: RetainedSemanticAdmissionExpectation,
    kind: str,
    namespace: str | None = None,
    owned_roots: tuple[str, ...] | None = None,
) -> None:
    """Exercise original validators; success never qualifies integrated issuance."""
    with _LOCK:
        state, host = _origin(origin)
        before = _expected(expected, host)
        if kind == "package_context":
            entrance = state.package
        elif kind == "declaration_inventory":
            entrance = state.inventory
        elif kind == "occurrence_assignments":
            entrance = state.assignments
        else:
            raise ValueError("unknown isolated validation kind")
        if kind != "occurrence_assignments" and (
            namespace is not None or owned_roots is not None
        ):
            raise ValueError("assignment arguments on non-assignment check")
        if kind == "occurrence_assignments" and (
            type(namespace) is not str
            or type(owned_roots) is not tuple
            or any(type(v) is not str for v in owned_roots)
        ):
            raise TypeError("exact assignment expectations required")
        call = entrance.callable
    if kind == "occurrence_assignments":
        result = call(
            admission, expected=expected, namespace=namespace, owned_roots=owned_roots
        )
    else:
        result = call(admission, expected=expected)
    with _LOCK:
        _, current_host = _origin(origin)
        after = _expected(expected, current_host)
        if (
            any(a is not b for a, b in zip(before[0], after[0], strict=True))
            or before[1] != after[1]
        ):
            raise ContractViolation("expected context changed during validation")
        if result is not None:
            raise ContractViolation("validator must return None or raise")


def require_trusted_validation_origin(
    origin: IsolatedWorkspaceValidationOrigin,
) -> Never:
    """Explicit refusal: fixture installation can never upgrade to host authority."""
    with _LOCK:
        _origin(origin)
    raise ContractViolation("trusted bootstrap unavailable: isolated origin only")


def close_isolated_validation_host(host: IsolatedValidationHost) -> None:
    with _LOCK:
        state = _host(host)
        state.closed = True
