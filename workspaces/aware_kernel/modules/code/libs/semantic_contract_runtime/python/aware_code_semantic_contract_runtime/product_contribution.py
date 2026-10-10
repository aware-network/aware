"""One original selected graph-product registration from a semantic owner.

This contribution is process-local. Its catalog projection is input to the
existing catalog host, never a catalog admission or an execution token.
"""

from __future__ import annotations

import inspect
import os
from copy import deepcopy
from dataclasses import dataclass
from types import MemberDescriptorType

from . import selected_provider as selected
from .contracts import (
    ContractViolation,
    ProviderExecutionBinding,
    SemanticConfigurationCoordinate,
    SemanticImplementationCoordinate,
)
from .direct_origin_interfaces import RetainedSemanticProductRuntimeExpectation
from .materialization_catalog import CodeSemanticMaterializationProfileBinding
from .private_stage_contract import (
    CodePrivateStagePlanV1,
    decode_private_stage_plan,
    encode_private_stage_plan,
)
from .profile import SemanticContractProfileDeclaration

_TOKEN = object()


class SelectedProviderProductContribution:
    __slots__ = ("_token",)

    def __init__(self, token: object) -> None:
        if token is not _TOKEN:
            raise TypeError("product contribution is Code-issued only")
        self._token = token

    def __copy__(self) -> None:
        raise TypeError("product contribution cannot be copied")

    def __deepcopy__(self, memo: object) -> None:
        del memo
        raise TypeError("product contribution cannot be copied")


@dataclass(frozen=True, slots=True)
class _State:
    pid: int
    factory: object
    product: selected._SelectedProviderFactoryProduct
    catalog_producer: object
    private_stage_plan_producer: object
    expected: RetainedSemanticProductRuntimeExpectation


@dataclass(frozen=True, slots=True)
class SelectedProviderProductCatalogInput:
    """Portable catalog input plus original executable; no host authority."""

    expected: RetainedSemanticProductRuntimeExpectation
    profile: SemanticContractProfileDeclaration
    binding: ProviderExecutionBinding
    executable: object


@dataclass(frozen=True, slots=True)
class SelectedProviderProductCatalogContribution:
    """Detached read projection; the paired host remains sole catalog issuer."""

    entries: tuple[CodeSemanticMaterializationProfileBinding, ...]
    executables: tuple[tuple[object, object, object], ...]
    planner: object


@dataclass(frozen=True, slots=True)
class _CatalogProductState:
    product: object
    entries: tuple[CodeSemanticMaterializationProfileBinding, ...]
    executables: tuple[tuple[object, object, object], ...]
    planner: object
    plan_descriptor: object
    plan_function: object


@dataclass(frozen=True, slots=True)
class _PrivatePlanState:
    original: CodePrivateStagePlanV1
    body: bytes


_CONTRIBUTIONS: dict[SelectedProviderProductContribution, _State] = {}
_CATALOG_PENDING = object()
_CATALOG_PRODUCTS: dict[SelectedProviderProductContribution, object] = {}
_PRIVATE_PLAN_PENDING = object()
_PRIVATE_PLANS: dict[SelectedProviderProductContribution, object] = {}


def _state(contribution: SelectedProviderProductContribution) -> _State:
    if type(contribution) is not SelectedProviderProductContribution:
        raise TypeError("exact product contribution required")
    state = _CONTRIBUTIONS.get(contribution)
    if state is None or contribution._token is not _TOKEN:
        raise ContractViolation("product contribution is unavailable")
    if state.pid != os.getpid():
        raise ContractViolation("product contribution belongs to another process")
    selected._factory_state(state.factory)
    if state.product.catalog_contribution_producer is not state.catalog_producer:
        raise ContractViolation("product catalog producer changed")
    if state.product.private_stage_plan_producer is not state.private_stage_plan_producer:
        raise ContractViolation("private-stage plan producer changed")
    return state


def read_selected_provider_product_contribution(
    contribution: SelectedProviderProductContribution,
) -> SelectedProviderProductCatalogInput:
    """Recheck the original live registration around the detached catalog read."""
    with selected._LOCK:
        state = _state(contribution)
        expected = state.expected
        product = state.product
        selected.validate_selected_provider_registration(
            expected.runtime,
            expected.registration,
            expected_profile=product.runtime.profile,
            expected_declaration=product.provider.declaration,
            expected_binding=product.binding,
        )
        result = SelectedProviderProductCatalogInput(
            RetainedSemanticProductRuntimeExpectation(
                expected.runtime, expected.registration
            ),
            deepcopy(product.runtime.profile),
            deepcopy(product.binding),
            product.provider,
        )
        if _state(contribution) is not state:
            raise ContractViolation("product contribution changed during read")
        selected._registration_state(expected.registration)
        return result


def _validate_catalog_product(
    contribution: SelectedProviderProductContribution,
    product: object,
) -> _CatalogProductState:
    fields = ("original", "entries", "executables", "planner")
    if (
        type(type(product)) is not type
        or type.__getattribute__(type(product), "__getattribute__")
        is not object.__getattribute__
        or any(
            type(inspect.getattr_static(product, field, None))
            is not MemberDescriptorType
            for field in fields
        )
    ):
        raise ContractViolation("owner product catalog must have inert slots")
    if object.__getattribute__(product, "original") is not contribution:
        raise ContractViolation("owner product catalog differs from original")
    entries = object.__getattribute__(product, "entries")
    executables = object.__getattribute__(product, "executables")
    planner = object.__getattribute__(product, "planner")
    if (
        type(entries) is not tuple
        or len(entries) != 1
        or type(entries[0]) is not CodeSemanticMaterializationProfileBinding
        or type(executables) is not tuple
        or len(executables) != 1
        or type(executables[0]) is not tuple
        or len(executables[0]) != 3
    ):
        raise ContractViolation("one complete product catalog entry required")
    entry = entries[0]
    entry.__post_init__()
    original = read_selected_provider_product_contribution(contribution)
    implementation, configuration, provider = executables[0]
    if (
        entry.profile_declaration != original.profile
        or entry.semantic_provider_key != original.binding.provider_key
        or entry.provider_execution_bindings != (original.binding,)
        or type(implementation) is not SemanticImplementationCoordinate
        or type(configuration) is not SemanticConfigurationCoordinate
        or implementation != original.binding.implementation
        or configuration != original.binding.configuration
        or provider is not original.executable
    ):
        raise ContractViolation("product catalog differs from original registration")
    if (
        type(type(planner)) is not type
        or type.__getattribute__(type(planner), "__getattribute__")
        is not object.__getattribute__
    ):
        raise ContractViolation("owner product planner accessor substituted")
    descriptor = inspect.getattr_static(planner, "plan", None)
    if not inspect.isfunction(descriptor):
        raise ContractViolation("original product planner method required")
    method = object.__getattribute__(planner, "plan")
    if (
        not inspect.ismethod(method)
        or method.__self__ is not planner
        or descriptor is not method.__func__
    ):
        raise ContractViolation("owner product planner method substituted")
    return _CatalogProductState(
        product, entries, executables, planner, descriptor, method.__func__
    )


def produce_selected_provider_product_catalog_contribution(
    contribution: SelectedProviderProductContribution,
) -> SelectedProviderProductCatalogContribution:
    """Call the exact owner-factory producer once and retain its original result."""
    with selected._LOCK:
        state = _state(contribution)
        producer = state.catalog_producer
        if producer is None:
            raise ContractViolation("owner product catalog producer unavailable")
        if contribution in _CATALOG_PRODUCTS:
            raise ContractViolation("owner product catalog producer already consumed")
        read_selected_provider_product_contribution(contribution)
        _CATALOG_PRODUCTS[contribution] = _CATALOG_PENDING
        product = producer(contribution)
        if _state(contribution) is not state:
            raise ContractViolation("original product registration changed during production")
        _CATALOG_PRODUCTS[contribution] = _validate_catalog_product(
            contribution, product
        )
        return read_selected_provider_product_catalog_contribution(contribution)


def read_selected_provider_product_catalog_contribution(
    contribution: SelectedProviderProductContribution,
) -> SelectedProviderProductCatalogContribution:
    """Revalidate one retained owner value; this does not admit a catalog."""
    with selected._LOCK:
        state = _state(contribution)
        retained = _CATALOG_PRODUCTS.get(contribution)
        if type(retained) is not _CatalogProductState:
            raise ContractViolation("owner product catalog contribution unavailable")
        observed = _validate_catalog_product(contribution, retained.product)
        if (
            observed.entries is not retained.entries
            or observed.executables is not retained.executables
            or observed.planner is not retained.planner
            or observed.plan_descriptor is not retained.plan_descriptor
            or observed.plan_function is not retained.plan_function
            or _state(contribution) is not state
        ):
            raise ContractViolation("owner product catalog changed")
        return SelectedProviderProductCatalogContribution(
            retained.entries, retained.executables, retained.planner
        )


def issue_selected_provider_product_contribution(
    factory_admission: selected._AdmittedSemanticProviderFactory,
) -> SelectedProviderProductContribution:
    """Acquire one fresh owner product through the existing exact factory rail."""
    with selected._LOCK:
        factory = selected._factory_state(factory_admission)
        entrance = factory.selection_factory
    product = entrance()
    if type(product) is not selected._SelectedProviderFactoryProduct:
        raise TypeError("product factory must return one exact selected product")
    producer = product.catalog_contribution_producer
    if producer is not None:
        if not inspect.isfunction(producer):
            raise TypeError("product catalog producer must be an exact function")
        parameters = tuple(inspect.signature(producer).parameters.values())
        if (
            len(parameters) != 1
            or parameters[0].kind
            not in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
            or parameters[0].default is not inspect.Parameter.empty
        ):
            raise TypeError("product catalog producer must take one original product")
    private_plan_producer = product.private_stage_plan_producer
    if private_plan_producer is not None:
        if not inspect.isfunction(private_plan_producer):
            raise TypeError("private-stage plan producer must be an exact function")
        parameters = tuple(inspect.signature(private_plan_producer).parameters.values())
        if (
            len(parameters) != 1
            or parameters[0].kind
            not in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
            or parameters[0].default is not inspect.Parameter.empty
        ):
            raise TypeError("private-stage plan producer must take original product")
    root = None
    registration = None
    contribution = None
    with selected._LOCK:
        if selected._factory_state(factory_admission) is not factory:
            raise ContractViolation("product factory changed during construction")
        if any(
            state.runtime is product.runtime
            for _, state in selected._SELECTION_ROOTS.values()
        ):
            raise ContractViolation("product factory must supply a fresh runtime")
        try:
            root = selected._selection_root_from_factory_product(
                factory_admission, product
            )
            registration = selected.register_selected_provider(product.runtime, root)
            contribution = SelectedProviderProductContribution(_TOKEN)
            _CONTRIBUTIONS[contribution] = _State(
                os.getpid(),
                factory_admission,
                product,
                producer,
                private_plan_producer,
                RetainedSemanticProductRuntimeExpectation(
                    product.runtime, registration
                ),
            )
            read_selected_provider_product_contribution(contribution)
            return contribution
        except BaseException:
            if contribution is not None:
                _CONTRIBUTIONS.pop(contribution, None)
            if registration is not None:
                selected.close_selected_provider_registration(
                    product.runtime, registration
                )
            if root is not None and registration is None:
                selected._SELECTION_ROOTS.pop(id(root), None)
            raise


def close_selected_provider_product_contribution(
    contribution: SelectedProviderProductContribution,
) -> None:
    """Revoke the original registration after the parent quiesces."""
    with selected._LOCK:
        state = _state(contribution)
        selected.close_selected_provider_registration(
            state.expected.runtime, state.expected.registration
        )
        _CATALOG_PRODUCTS.pop(contribution, None)
        _PRIVATE_PLANS.pop(contribution, None)
        del _CONTRIBUTIONS[contribution]


def _validate_private_stage_plan(
    contribution: SelectedProviderProductContribution,
    value: CodePrivateStagePlanV1,
) -> bytes:
    if type(value) is not CodePrivateStagePlanV1:
        raise TypeError("owner must return exact CodePrivateStagePlanV1")
    body = encode_private_stage_plan(value)
    state = _state(contribution)
    original = read_selected_provider_product_contribution(contribution)
    profile = original.profile
    binding = original.binding
    terminal = value.stages[1]
    if (
        value.public_profile.profile_ref != profile.profile_ref
        or value.public_profile.version != profile.version
        or value.public_profile.digest != profile.digest
        or terminal.provider_key != binding.provider_key
        or terminal.implementation != binding.implementation
        or terminal.configuration != binding.configuration
    ):
        raise ContractViolation("private-stage plan differs from public registration")
    declaration = state.product.provider.declaration
    declared_results = (declaration.result_role, *declaration.output_roles)
    if not any(
        terminal.terminal.role == item.role
        and terminal.terminal.contract == item.contract
        for item in declared_results
    ):
        raise ContractViolation("private-stage terminal is not public result")
    return body


def produce_selected_provider_private_stage_plan(
    contribution: SelectedProviderProductContribution,
) -> CodePrivateStagePlanV1:
    """Invoke the original owner producer once; return portable meaning only."""
    with selected._LOCK:
        state = _state(contribution)
        producer = state.private_stage_plan_producer
        if producer is None:
            raise ContractViolation("private-stage plan producer unavailable")
        if contribution in _PRIVATE_PLANS:
            raise ContractViolation("private-stage plan producer already consumed")
        read_selected_provider_product_contribution(contribution)
        _PRIVATE_PLANS[contribution] = _PRIVATE_PLAN_PENDING
        value = producer(contribution)
        if _state(contribution) is not state:
            raise ContractViolation("original product registration changed")
        body = _validate_private_stage_plan(contribution, value)
        _PRIVATE_PLANS[contribution] = _PrivatePlanState(value, body)
        return read_selected_provider_private_stage_plan(contribution)


def read_selected_provider_private_stage_plan(
    contribution: SelectedProviderProductContribution,
) -> CodePrivateStagePlanV1:
    """Recheck the retained original; a decoded plan is never the registration."""
    with selected._LOCK:
        state = _state(contribution)
        retained = _PRIVATE_PLANS.get(contribution)
        if type(retained) is not _PrivatePlanState:
            raise ContractViolation("private-stage plan unavailable")
        current = _validate_private_stage_plan(contribution, retained.original)
        if current != retained.body or _state(contribution) is not state:
            raise ContractViolation("retained private-stage plan changed")
        return decode_private_stage_plan(retained.body)
