"""Internal direct assembly and policy retention, never a public bootstrap root.

Only fixed original Workspace application assembly may call the underscore
installer. It supplies already admitted resources, not caller-selected callbacks.
Source mechanics tests do not authenticate that external assembly or installation.
"""

from __future__ import annotations

import inspect
import os
from copy import deepcopy
from dataclasses import dataclass
from threading import RLock
from typing import TYPE_CHECKING, Any, Literal, overload
from weakref import WeakKeyDictionary

from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.direct_origin_interfaces import (
    DirectCommandExpectedContext,
    DirectWorkspaceOriginProduct,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    CodeSemanticContractCatalog,
    CodeSemanticContractCatalogResolver,
)
from aware_code_semantic_contract_runtime.registry_policy import RegistryPolicy
from aware_code_semantic_contract_runtime.retained_scope_interfaces import (
    CodeRetainedScopeProjection,
)
from aware_code_semantic_contract_runtime.runtime import SemanticContractRuntime

from .calculation import calculate_registry_policy
from .declaration_eligibility import calculate_declaration_eligibility
from .direct_epoch_tracking import _epoch_closed, _tracked_policy
from .qualified_calculation import calculate_qualified_registry_policy
from .stage_runtime_retention import _StageRuntimeRetention
from .product_runtime_retention import _ProductRuntimeRetention

if TYPE_CHECKING:
    from .dependency_source_binding import _RetainedDependencySource
    from .declaration_host import _PreparedDeclarationSource


class _Opaque:
    def __new__(cls):
        raise TypeError("direct host handles are module-issued")

    def __reduce__(self):
        raise TypeError("direct host handles cannot be copied or serialized")


class DirectCommandBootstrap(_Opaque):
    def __init_subclass__(cls, **kwargs):
        raise TypeError("bootstrap is sealed")


class DirectValidationHost(_Opaque):
    def __init_subclass__(cls, **kwargs):
        raise TypeError("host is sealed")


class AdmittedRegistryPolicy(_Opaque):
    """Command-bound internal result, not selected-provider execution admission."""

    def __init_subclass__(cls, **kwargs):
        raise TypeError("policy admission is sealed")


@dataclass(frozen=True)
class _Entrance:
    receiver: object
    name: str
    descriptor: object
    method: Any

    def check(self):
        if inspect.getattr_static(self.receiver, self.name) is not self.descriptor:
            raise ContractViolation("original direct entrance substituted")

    def call(self, *args, **kwargs):
        self.check()
        result = self.method(*args, **kwargs)
        self.check()
        return result


def _capture(receiver, name):
    descriptor = inspect.getattr_static(receiver, name)
    method = getattr(receiver, name)
    if not inspect.ismethod(method) or method.__self__ is not receiver:
        raise ContractViolation("original bound direct entrance required")
    return _Entrance(receiver, name, descriptor, method)


@dataclass
class _State:
    lifetime: object
    expected: DirectCommandExpectedContext
    resources: tuple
    coordinates: tuple
    identities: tuple
    methods: dict[str, _Entrance]
    catalog_digest: object
    catalog_resolver: CodeSemanticContractCatalogResolver
    pid: int
    current_catalog: object = None
    pending_successor: object = None
    closed: bool = False
    stage_retention: _StageRuntimeRetention | None = None
    product_retention: _ProductRuntimeRetention | None = None
    qualified: bool = False
    dependency_binding: _RetainedDependencySource | None = None
    declaration_binding: _PreparedDeclarationSource | None = None
    source_rail: str = "existing"

    @overload
    def check(
        self, *, read_catalog: Literal[True] = True,
        check_catalog: Literal[True] = True,
    ) -> CodeSemanticContractCatalog: ...

    @overload
    def check(
        self, *, read_catalog: Literal[False],
        check_catalog: Literal[True] = True,
    ) -> None: ...

    @overload
    def check(
        self, *, read_catalog: bool = False,
        check_catalog: Literal[False],
    ) -> None: ...

    def check(self, *, read_catalog=True, check_catalog=True):
        if self.pid != os.getpid() or self.closed:
            raise ContractViolation("direct host unavailable")
        value = self.expected
        value.__post_init__()
        retained = self.stage_retention
        if value.stage_runtime_bindings:
            if retained is None or retained.expected is not value:
                raise ContractViolation("original stage retention unavailable")
            retained.check_identities()
        elif retained is not None:
            raise ContractViolation("original stage bindings removed")
        product_retained = self.product_retention
        if value.product_runtime_bindings:
            if product_retained is None or product_retained.expected is not value:
                raise ContractViolation("original product retention unavailable")
            product_retained.check_identities()
        elif product_retained is not None:
            raise ContractViolation("original product bindings removed")
        current = (
            value.invocation_identity,
            value.epoch_identity,
            value.runtime,
            value.catalog,
        )
        if any(a is not b for a, b in zip(current, self.identities, strict=True)):
            raise ContractViolation("direct expected identities substituted")
        if value.process_id != self.pid:
            raise ContractViolation("direct process context substituted")
        for original, binding in zip(self.resources, value.resources, strict=True):
            role, resource, disposition = original
            if (
                role != binding.role
                or resource is not binding.resource
                or disposition != binding.disposition
            ):
                raise ContractViolation("direct resource substituted")
        coordinates = (
            value.composition_implementation,
            value.composition_configuration,
            value.policy_implementation,
            value.policy_configuration,
        )
        if coordinates != self.coordinates:
            raise ContractViolation("direct implementation/configuration substituted")
        producer = next(
            resource
            for role, resource, _ in self.resources
            if role == "policy_producer"
        )
        if self.source_rail != value.source_rail or (
            self.source_rail == "declaration_v3"
        ) != (producer is calculate_declaration_eligibility):
            raise ContractViolation("original direct source rail changed")
        if self.qualified != (producer is calculate_qualified_registry_policy):
            raise ContractViolation("original policy mode changed")
        for method in self.methods.values():
            method.check()
        if self.methods["lifetime"].call(self.lifetime, expected=value) is not None:
            raise ContractViolation("lifetime validator returned non-None")
        if not check_catalog:
            return None
        # Reuse indexes for the exact original admission. The public catalog
        # reader still validates liveness/content and returns a detached snapshot.
        if (
            type(self.catalog_resolver) is not CodeSemanticContractCatalogResolver
            or self.catalog_resolver._admission is not (
                self.current_catalog if self.current_catalog is not None else value.catalog
            )
        ):
            raise ContractViolation("direct catalog resolver substituted")
        if not read_catalog:
            coordinates = (
                self.catalog_resolver._validate_retained_catalog_coordinate()
            )
            if coordinates[2] != self.catalog_digest:
                raise ContractViolation("direct catalog changed")
            return None
        catalog = self.catalog_resolver.catalog
        if catalog.catalog_root_digest != self.catalog_digest:
            raise ContractViolation("direct catalog changed")
        return catalog


_BOOTSTRAPS: WeakKeyDictionary[DirectCommandBootstrap, _State] = WeakKeyDictionary()
_HOSTS: WeakKeyDictionary[DirectValidationHost, _State] = WeakKeyDictionary()
_POLICIES: WeakKeyDictionary[AdmittedRegistryPolicy, tuple] = WeakKeyDictionary()
# Original lifetime runtime is weakly keyed; value is its single issued lifetime.
# This is a nominal replay ledger, not ambient discovery or authority selection.
_INSTALLED: WeakKeyDictionary[object, object] = WeakKeyDictionary()
_LOCK = RLock()


def _assemble_direct_command_bootstrap(
    *,
    lifetime: object,
    expected: DirectCommandExpectedContext,
) -> DirectCommandBootstrap:
    """Privileged fixed application assembly only; does not authenticate its caller.

    The public command must not expose this dependency-injection entrance.
    Workspace must prove the original fixed call site and resource provenance.
    """
    if type(expected) is not DirectCommandExpectedContext:
        raise TypeError("exact direct context required")
    expected.__post_init__()
    from .stage_runtime_retention import _capture_stage_runtime_retention
    from .product_runtime_retention import _capture_product_runtime_retention

    stages = (
        _capture_stage_runtime_retention(expected)
        if expected.stage_runtime_bindings
        else None
    )
    products = (
        _capture_product_runtime_retention(expected)
        if expected.product_runtime_bindings
        else None
    )
    if type(expected.runtime) is not SemanticContractRuntime:
        raise TypeError("exact Code runtime required")
    if expected.process_id != os.getpid():
        raise ContractViolation("wrong bootstrap process")
    resources = {b.role: b.resource for b in expected.resources}
    producer = resources["policy_producer"]
    qualified = producer is calculate_qualified_registry_policy
    declaration_v3 = producer is calculate_declaration_eligibility
    if (
        expected.source_rail == "declaration_v3"
    ) != declaration_v3 or (
        producer is not calculate_registry_policy and not qualified and not declaration_v3
    ):
        raise ContractViolation("fixed policy producer substituted")
    methods = {
        "lifetime": _capture(
            resources["lifetime_runtime"], "validate_command_lifetime"
        ),
        "acquire": _capture(
            resources["lifetime_runtime"], "acquire_command_publication_guard"
        ),
        "guard": _capture(
            resources["lifetime_runtime"], "validate_command_publication_guard"
        ),
        "release": _capture(
            resources["lifetime_runtime"], "release_command_publication_guard"
        ),
        "factory": _capture(
            resources["composition_factory"], "create_direct_semantic_origin"
        ),
        "read": _capture(
            resources["declaration_scope_runtime"]
            if declaration_v3 else resources["scope_adapter"],
            "read_declaration_scope" if declaration_v3 else (
                "read_dependency_scope_closure" if qualified
                else "read_complete_scope_projection"
            ),
        ),
        "scope": _capture(
            resources["declaration_scope_runtime"] if declaration_v3 else (
                resources["scope_runtime"] if qualified else resources["scope_adapter"]
            ),
            "validate_declaration_scope" if declaration_v3 else (
                "validate_dependency_scope_closure" if qualified
                else "validate_complete_scope_projection"
            ),
        ),
    }
    if declaration_v3:
        runtime = resources["declaration_scope_runtime"]
        methods["scope_locked"] = _capture(runtime, "check_declaration_scope_locked")
        methods["selected_read"] = _capture(runtime, "read_selected_package_source")
        methods["selected_validate"] = _capture(
            runtime, "validate_selected_package_source"
        )
        methods["participant_read"] = _capture(
            runtime, "read_selected_participant_view"
        )
        methods["participant_validate"] = _capture(
            runtime, "validate_selected_participant_view"
        )
        methods["selected_locked"] = _capture(
            runtime, "check_selected_package_source_locked"
        )
    catalog_resolver = CodeSemanticContractCatalogResolver(expected.catalog)
    catalog = catalog_resolver.catalog
    state = _State(
        lifetime,
        expected,
        tuple((b.role, b.resource, b.disposition) for b in expected.resources),
        deepcopy(
            (
                expected.composition_implementation,
                expected.composition_configuration,
                expected.policy_implementation,
                expected.policy_configuration,
            )
        ),
        (
            expected.invocation_identity,
            expected.epoch_identity,
            expected.runtime,
            expected.catalog,
        ),
        methods,
        catalog.catalog_root_digest,
        catalog_resolver,
        os.getpid(),
    )
    state.stage_retention = stages
    state.product_retention = products
    state.qualified = qualified
    state.source_rail = expected.source_rail
    state.check(read_catalog=False)
    with _LOCK:
        owner = resources["lifetime_runtime"]
        if owner in _INSTALLED:
            raise ContractViolation("direct bootstrap replay")
        _INSTALLED[owner] = lifetime
        bootstrap = object.__new__(DirectCommandBootstrap)
        _BOOTSTRAPS[bootstrap] = state
    return bootstrap


def register_direct_workspace_origin(
    bootstrap: DirectCommandBootstrap,
    lifetime: object,
) -> DirectValidationHost:
    """Consume original bootstrap once and invoke its retained owner factory.

    Product is obtained internally, not supplied by the caller. A failed attempt
    also consumes the slot. This refines the earlier three-argument proposal.
    """
    if type(bootstrap) is not DirectCommandBootstrap:
        raise TypeError("exact bootstrap required")
    state = _BOOTSTRAPS.get(bootstrap)
    if state is None or state.pid != os.getpid():
        raise ContractViolation("foreign or consumed bootstrap")
    with _LOCK:
        if _BOOTSTRAPS.pop(bootstrap, None) is not state:
            raise ContractViolation("bootstrap replay")
    try:
        state.check(read_catalog=False)
        if lifetime is not state.lifetime:
            raise ContractViolation("foreign command lifetime")
        product = state.methods["factory"].call(lifetime)
        if (
            type(product) is not DirectWorkspaceOriginProduct
            or product.lifetime is not lifetime
            or product.expected is not state.expected
        ):
            raise ContractViolation("original factory product differs")
        state.check(read_catalog=False)
        host = object.__new__(DirectValidationHost)
        with _LOCK:
            _HOSTS[host] = state
        return host
    except BaseException:
        state.closed = True
        raise


def _state(host):
    if type(host) is not DirectValidationHost:
        raise TypeError("exact direct host required")
    state = _HOSTS.get(host)
    if state is None:
        raise ContractViolation("foreign or closed host")
    try:
        state.check(read_catalog=False)
    except BaseException:
        # A sealed transfer deliberately retires the predecessor catalog.
        # Its old handles must refuse without destroying the original host,
        # which still has to adopt the committed successor under one parent.
        from . import catalog_completion_transfer as transfers

        pending = state.pending_successor
        record = transfers._TRANSFERS.get(pending) if pending is not None else None
        expected_retirement = (
            record is not None
            and record.status == "sealed"
            and record.binding.state is state
        )
        if expected_retirement:
            try:
                state.check(read_catalog=False, check_catalog=False)
            except BaseException:
                expected_retirement = False
        if state.pid == os.getpid() and not expected_retirement:
            state.closed = True
        raise
    return state


def _qualified_mode(host):
    """Dispatch on retained fixed producer, without another catalog export/check."""
    if type(host) is not DirectValidationHost:
        raise TypeError("exact direct host required")
    state = _HOSTS.get(host)
    if state is None:
        raise ContractViolation("foreign or closed host")
    if state.pid != os.getpid():
        raise ContractViolation("direct process changed")
    producer = next(
        resource for role, resource, _ in state.resources if role == "policy_producer"
    )
    qualified = producer is calculate_qualified_registry_policy
    if state.qualified is not qualified:
        raise ContractViolation("original policy mode changed")
    return qualified


def produce_registry_policy(
    host: DirectValidationHost, scope_snapshot: object
) -> AdmittedRegistryPolicy:
    qualified = _qualified_mode(host)
    if _state(host).source_rail == "declaration_v3":
        from .declaration_host import _produce_selected_registry_policy

        return _produce_selected_registry_policy(host, scope_snapshot)
    if qualified:
        from .qualified_host import produce_registry_policy as produce

        return produce(host, scope_snapshot)
    return _produce_local_registry_policy(host, scope_snapshot)


def validate_admitted_registry_policy(
    host: DirectValidationHost, admission: AdmittedRegistryPolicy
) -> RegistryPolicy:
    qualified = _qualified_mode(host)
    if _state(host).source_rail == "declaration_v3":
        from .declaration_host import _validate_selected_registry_policy

        return _validate_selected_registry_policy(host, admission)
    if qualified:
        from .qualified_host import validate_registry_policy

        return validate_registry_policy(host, admission)
    return _validate_local_registry_policy(host, admission)


@_tracked_policy
def _produce_local_registry_policy(
    host: DirectValidationHost,
    scope_snapshot: object,
) -> AdmittedRegistryPolicy:
    state = _state(host)
    methods = state.methods
    try:
        methods["scope"].call(scope_snapshot)
        projection = methods["read"].call(scope_snapshot)
        if type(projection) is not CodeRetainedScopeProjection:
            raise ContractViolation("exact scope projection required")
        digest = projection.projection_digest
        policy = calculate_registry_policy(projection, state.check())
        methods["scope"].call(scope_snapshot, projection_digest=digest)
        state.check(read_catalog=False)
        guard = methods["acquire"].call(state.lifetime, expected=state.expected)
        try:
            methods["guard"].call(
                guard, lifetime=state.lifetime, expected=state.expected
            )
            state.check(read_catalog=False)
            with _LOCK:
                if state.closed:
                    raise ContractViolation("host closed during policy calculation")
                result = object.__new__(AdmittedRegistryPolicy)
                _POLICIES[result] = (host, scope_snapshot, digest, policy)
        finally:
            # Always release original retained method, even if its descriptor was
            # replaced while the guard was held. Then report substitution.
            methods["release"].method(guard)
            methods["release"].check()
        return result
    except BaseException:
        state.closed = True
        raise


@_tracked_policy
def _validate_local_registry_policy(
    host: DirectValidationHost,
    admission: AdmittedRegistryPolicy,
) -> RegistryPolicy:
    """Return detached portable result after original parent/scope validation."""
    state = _state(host)
    if type(admission) is not AdmittedRegistryPolicy:
        raise TypeError("exact policy admission required")
    retained = _POLICIES.get(admission)
    if retained is None or retained[0] is not host:
        raise ContractViolation("foreign policy admission")
    _, snapshot, digest, policy = retained
    try:
        state.methods["scope"].call(snapshot, projection_digest=digest)
        state.check(read_catalog=False)
        return deepcopy(policy)
    except BaseException:
        state.closed = True
        raise


@_epoch_closed
def close_direct_validation_host(host: DirectValidationHost) -> None:
    """Revoke Code records only; original composition owns resource cleanup."""
    if type(host) is not DirectValidationHost:
        raise TypeError("exact direct host required")
    state = _HOSTS.get(host)
    if state is None:
        return
    if state.pid != os.getpid():
        raise ContractViolation("direct process changed")
    with _LOCK:
        state.closed = True
        _HOSTS.pop(host, None)
        for admission, value in list(_POLICIES.items()):
            if value[0] is host:
                _POLICIES.pop(admission, None)
