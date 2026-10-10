"""Original dependency-product admission through retained host resources.

Only fixed composition may install this origin. The existing registered source
origin and semantic_issuer resource supply its original owner methods. Missing
methods refuse; no argument can nominate another validator or resource.
"""

import inspect
import os
from copy import deepcopy
from dataclasses import dataclass
from typing import Any
from weakref import WeakKeyDictionary, ref

from aware_code_semantic_contract_runtime.contracts import (
    ContractViolation,
    SemanticValueCoordinate,
)
from aware_code_semantic_contract_runtime.dependency_admission_interfaces import (
    RetainedDependencyFulfillmentExpectation,
)
from aware_code_semantic_contract_runtime.dependency_input_codec import (
    SemanticDependencyProductInputCodec,
)
from aware_code_semantic_contract_runtime.runtime import SemanticBody

from . import dependency_operation_validator as code_validation
from . import direct_epoch_tracking as hooks
from . import direct_host as hosts
from . import retained_demand_operation as demands
from . import retained_input_admission as sources


@dataclass
class _Origin:
    host: Any
    source_origin: Any
    source_state: Any
    issuer: Any
    validator: code_validation.OriginalDependencyOperationValidator
    methods: dict[str, hosts._Entrance]
    pid: int

    def identity(self):
        if self.pid != os.getpid():
            raise ContractViolation("foreign dependency consumer process")
        if (
            sources._INSTALLED.get(self.host, lambda: None)() is not self.source_origin
            or sources._ORIGINS.get(self.source_origin) is not self.source_state
            or self.source_state.host is not self.host
            or self.source_state.issuer is not self.issuer
            or code_validation._identity(self.validator) is not self.host
        ):
            raise ContractViolation("original dependency consumer origin changed")
        for entrance in self.methods.values():
            entrance.check()

    def check(self):
        self.identity()
        if sources._state(self.source_origin) is not self.source_state:
            raise ContractViolation("original source origin differs")


_ORIGINS = WeakKeyDictionary()
_INSTALLED = WeakKeyDictionary()


def _state(origin):
    if type(origin) is not DependencyAdmissionConsumer:
        raise TypeError("exact dependency consumer required")
    state = _ORIGINS.get(origin)
    if state is None or _INSTALLED.get(state.host, lambda: None)() is not origin:
        raise ContractViolation("foreign dependency consumer")
    _check_methods(origin)
    state.check()
    return state


def _product_value(body, resolution):
    if type(body) is not SemanticBody:
        raise TypeError("exact dependency product body required")
    body.__post_init__()
    codec = SemanticDependencyProductInputCodec()
    if body.coordinate.contract != codec.contract:
        raise ContractViolation("dependency product contract differs")
    # The full original owner coordinate is validated below. Binding its role to
    # an authority profile belongs to the subsequent selected invocation, not a
    # hard-coded role name in this owner-neutral product correspondence check.
    value = codec.decode(body.canonical_body)
    if codec.encode(value) != body.canonical_body:
        raise ContractViolation("dependency products are not canonical")
    planning = resolution.planning_input
    keys = tuple((d.dependency_kind, d.dependency_ref) for d in planning.dependencies)
    for actual, original in (
        (value.package, planning.package),
        (value.source_identity_digest, planning.source_identity_digest),
        (value.declared_dependencies, keys),
        (value.demand_set, resolution.demand_set),
        (value.intent, resolution.planning_context.code_intent),
    ):
        if not code_validation._same_portable(actual, original):
            raise ContractViolation(
                "dependency products differ from original Code demand"
            )
    return value


@dataclass(frozen=True)
class _Products:
    origin: Any
    operation: Any
    resolution: Any
    fulfillment: Any
    coordinate: SemanticValueCoordinate
    wire: bytes
    pid: int


_PRODUCTS = WeakKeyDictionary()


class AdmittedDependencyProducts(hosts._Opaque):
    """Original retained input evidence, never an execution or transfer admission."""

    def __init_subclass__(cls, **kwargs):
        raise TypeError("admitted dependency products are sealed")

    def read_products(self):
        retained = _product_record(self)
        body = SemanticBody(deepcopy(retained.coordinate), retained.wire)
        return _consume(
            retained.origin,
            retained.operation,
            retained.resolution,
            retained.fulfillment,
            body=body,
            retain=False,
            existing=self,
            retained=retained,
        )


_READ_PRODUCTS = AdmittedDependencyProducts.read_products


def _product_record(handle):
    if type(handle) is not AdmittedDependencyProducts:
        raise TypeError("exact admitted dependency products required")
    record = _PRODUCTS.get(handle)
    if record is None:
        raise ContractViolation("foreign admitted dependency products")
    if record.pid != os.getpid():
        raise ContractViolation("foreign dependency product process")
    if inspect.getattr_static(handle, "read_products") is not _READ_PRODUCTS:
        raise ContractViolation("original product reader substituted")
    return record


class DependencyAdmissionConsumer(hosts._Opaque):
    def __init_subclass__(cls, **kwargs):
        raise TypeError("dependency consumer is sealed")

    def validate_dependency_products(
        self, operation, resolution_admission, fulfillment_admission, *, body
    ):
        _consume(
            self,
            operation,
            resolution_admission,
            fulfillment_admission,
            body=body,
            retain=False,
        )

    def admit_dependency_products(
        self, operation, resolution_admission, fulfillment_admission, *, body
    ):
        """Retain original evidence atomically after the final exclusion check."""
        return _consume(
            self,
            operation,
            resolution_admission,
            fulfillment_admission,
            body=body,
            retain=True,
        )


def _consume(
    origin,
    operation,
    resolution_admission,
    fulfillment_admission,
    *,
    body,
    retain,
    existing=None,
    retained: _Products | None = None,
):
    state = _state(origin)
    record = code_validation._operation(state.validator, operation)
    with demands.dependency_resolution_validation_session(operation):
        # The session validates the original demand and source context before
        # owner contact. Nested expectation and owner callbacks retain nominal
        # lineage; session exit performs the matching complete validations.
        expected = state.methods["expectation"].call(operation)
        value = _product_value(body, expected)
        coordinate = deepcopy(body.coordinate)
        wire = body.canonical_body
        fulfilled = RetainedDependencyFulfillmentExpectation(
            resolution=expected,
            dependency_products_coordinate=deepcopy(coordinate),
            dependency_products=value,
        )
        state.identity()
        if body.canonical_body != wire or not code_validation._same_portable(
            body.coordinate, coordinate
        ):
            raise ContractViolation(
                "dependency product body changed before fulfillment"
            )
        if (
            state.methods["fulfillment"].call(
                fulfillment_admission,
                resolution_admission=resolution_admission,
                expected=fulfilled,
            )
            is not None
        ):
            raise ContractViolation("fulfillment validator returned non-None")
        if state.methods["demand"].call(operation, expected=expected) is not None:
            raise ContractViolation("Code demand validator returned non-None")
    state.check()
    with hooks._guard(record.binding) as guard:
        record.check_locked(guard)
        state.identity()
        _check_methods(origin)
        code_validation._compare(expected, code_validation._snapshot(record, operation))
        if (
            fulfilled.resolution is not expected
            or not code_validation._same_portable(
                fulfilled.dependency_products_coordinate, coordinate
            )
            or not code_validation._same_portable(body.coordinate, coordinate)
            or body.canonical_body != wire
            or SemanticDependencyProductInputCodec().encode(
                fulfilled.dependency_products
            )
            != wire
        ):
            raise ContractViolation(
                "dependency product closure changed during validation"
            )

        if existing is not None:
            if retained is None or _product_record(existing) is not retained:
                raise ContractViolation("original retained products changed")
            if (
                retained.origin is not origin
                or retained.operation is not operation
                or retained.resolution is not resolution_admission
                or retained.fulfillment is not fulfillment_admission
                or retained.wire != wire
                or not code_validation._same_portable(retained.coordinate, coordinate)
            ):
                raise ContractViolation("retained dependency evidence substituted")
        detached = SemanticBody(deepcopy(coordinate), wire)
        if retain:
            handle = object.__new__(AdmittedDependencyProducts)
            _PRODUCTS[handle] = _Products(
                origin,
                operation,
                resolution_admission,
                fulfillment_admission,
                deepcopy(coordinate),
                wire,
                os.getpid(),
            )
            return handle
        return detached


_VALIDATE = DependencyAdmissionConsumer.validate_dependency_products
_ADMIT = DependencyAdmissionConsumer.admit_dependency_products


def _check_methods(origin):
    for name, original in (
        ("validate_dependency_products", _VALIDATE),
        ("admit_dependency_products", _ADMIT),
    ):
        if inspect.getattr_static(origin, name) is not original:
            raise ContractViolation("original dependency consumer method substituted")


def assemble_dependency_admission_consumer(host):
    """Bind only the existing original host issuer; not bootstrap authentication.

    Does not configure or manufacture owner issuers or
    register caller callbacks. Fixed composition must retain the returned origin.
    """
    hosts._state(host)
    source_origin = sources._INSTALLED.get(host, lambda: None)()
    source_state = sources._state(source_origin)
    issuer = source_state.issuer
    try:
        methods = {
            "resolution": hosts._capture(
                issuer, "validate_dependency_resolution_admission"
            ),
            "fulfillment": hosts._capture(
                issuer, "validate_dependency_fulfillment_admission"
            ),
        }
    except AttributeError as exc:
        raise ContractViolation(
            "original dependency issuer entrances unavailable"
        ) from exc
    existing = _INSTALLED.get(host)
    if existing is not None:
        origin = existing()
        if origin is None:
            raise ContractViolation("original dependency consumer was released")
        _state(origin)
        return origin
    validator = code_validation.retained_dependency_operation_validator(host)
    methods["expectation"] = hosts._capture(validator, "expectation")
    methods["demand"] = hosts._capture(
        validator, "validate_retained_dependency_operation"
    )
    state = _Origin(
        host, source_origin, source_state, issuer, validator, methods, os.getpid()
    )
    state.check()
    binding = hooks._BINDINGS.get(host)
    if binding is None:
        raise ContractViolation("original dependency epoch binding unavailable")
    origin = object.__new__(DependencyAdmissionConsumer)
    with hooks._guard(binding) as guard:
        hooks._original(binding, host, guard)
        state.identity()
        if host in _INSTALLED:
            raise ContractViolation("dependency consumer registration replay")
        _ORIGINS[origin] = state
        _INSTALLED[host] = ref(origin)
    return origin
