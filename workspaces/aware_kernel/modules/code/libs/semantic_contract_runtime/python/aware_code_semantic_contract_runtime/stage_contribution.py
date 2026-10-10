"""Atomic acquisition through Code's original factory and registration authority.

A contribution owns registrations, not a command parent, policy or execution.
Semantic owners supply products without being imported by Code.
"""

from __future__ import annotations

import inspect
import os
from copy import deepcopy
from dataclasses import dataclass
from types import MemberDescriptorType
from typing import TYPE_CHECKING

from . import selected_provider as selected
from .contracts import (
    ContractViolation,
    ProviderExecutionBinding,
    SemanticConfigurationCoordinate,
    SemanticImplementationCoordinate,
)
from .direct_origin_interfaces import RetainedSemanticStageRuntimeExpectation
from .materialization_catalog import (
    CodeSemanticContractCatalog,
    CodeSemanticMaterializationProfileBinding,
)

if TYPE_CHECKING:
    from .product_contribution import SelectedProviderProductContribution

_TOKEN = object()


class SelectedProviderStageContribution:
    """Nominal process-local pair; portable reconstruction grants no authority."""

    __slots__ = ("_token",)

    def __init__(self, token: object) -> None:
        if token is not _TOKEN:
            raise TypeError("stage contribution is Code-issued only")
        self._token = token

    def __copy__(self) -> None:
        raise TypeError("stage contribution cannot be copied")

    def __deepcopy__(self, memo: object) -> None:
        del memo
        raise TypeError("stage contribution cannot be copied")


@dataclass(frozen=True, slots=True)
class _ContributionState:
    pid: int
    products: selected.SelectedProviderStageFactoryProduct
    catalog_producer: object
    stages: tuple[
        RetainedSemanticStageRuntimeExpectation, RetainedSemanticStageRuntimeExpectation
    ]


# Same original selection lock guards publication, inspection and cleanup.
_CONTRIBUTIONS: dict[SelectedProviderStageContribution, _ContributionState] = {}
_CATALOG_PENDING = object()
_CATALOG_PRODUCTS: dict[SelectedProviderStageContribution, object] = {}


@dataclass(frozen=True, slots=True)
class SelectedProviderStageCatalogContribution:
    """Read projection only; retain the original pair for every host use."""

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


def _state(contribution: SelectedProviderStageContribution) -> _ContributionState:
    if type(contribution) is not SelectedProviderStageContribution:
        raise TypeError("stage contribution must be exact")
    state = _CONTRIBUTIONS.get(contribution)
    if state is None or contribution._token is not _TOKEN:
        raise ContractViolation("stage contribution is not nominally admitted")
    if state.pid != os.getpid():
        raise ContractViolation("stage contribution belongs to another process")
    if state.products.catalog_contribution_producer is not state.catalog_producer:
        raise ContractViolation("stage catalog producer changed")
    return state


def read_selected_provider_stage_contribution(
    contribution: SelectedProviderStageContribution,
) -> tuple[
    RetainedSemanticStageRuntimeExpectation, RetainedSemanticStageRuntimeExpectation
]:
    """Validate both original registrations and expose their expected identities."""

    with selected._LOCK:
        state = _state(contribution)
        for stage, product in zip(
            state.stages,
            (state.products.source_planning, state.products.authority_derivation),
            strict=True,
        ):
            selected.validate_selected_provider_registration(
                stage.runtime,
                stage.registration,
                expected_profile=stage.runtime.profile,
                expected_declaration=product.provider.declaration,
                expected_binding=product.binding,
            )
        # Reentrant owner properties cannot revoke the pair during validation.
        if _state(contribution) is not state:
            raise ContractViolation("stage contribution changed during validation")
        for stage in state.stages:
            selected._registration_state(stage.registration)
        return (
            RetainedSemanticStageRuntimeExpectation(
                state.stages[0].stage,
                state.stages[0].runtime,
                state.stages[0].registration,
            ),
            RetainedSemanticStageRuntimeExpectation(
                state.stages[1].stage,
                state.stages[1].runtime,
                state.stages[1].registration,
            ),
        )


@dataclass(frozen=True, slots=True)
class SelectedProviderStageCatalogInput:
    """Read projection, not catalog admission or independent execution authority.

    Consumers must retain and revalidate the original contribution. Constructing
    this value or retaining an executable reference does not preserve liveness.
    """

    stage: RetainedSemanticStageRuntimeExpectation
    binding: ProviderExecutionBinding
    executable: object


def read_selected_provider_stage_catalog_inputs(
    contribution: SelectedProviderStageContribution,
) -> tuple[SelectedProviderStageCatalogInput, SelectedProviderStageCatalogInput]:
    """Expose the original pair without another supplier or registration path."""
    with selected._LOCK:
        state = _state(contribution)
        original = read_selected_provider_stage_contribution(contribution)
        products = (state.products.source_planning, state.products.authority_derivation)
        result = tuple(
            SelectedProviderStageCatalogInput(
                stage, deepcopy(product.binding), product.provider
            )
            for stage, product in zip(original, products, strict=True)
        )
        # Revalidate after projection construction; copied binding values cannot
        # substitute for the original provider/registration retained by Code.
        current = read_selected_provider_stage_contribution(contribution)
        if _state(contribution) is not state or any(
            before.stage != after.stage
            or before.runtime is not after.runtime
            or before.registration is not after.registration
            for before, after in zip(original, current, strict=True)
        ):
            raise ContractViolation("stage catalog inputs changed during read")
        return result[0], result[1]


def _validate_catalog_product(
    contribution: SelectedProviderStageContribution,
    product: object,
) -> _CatalogProductState:
    if type(product).__getattribute__ is not object.__getattribute__ or any(
        type(inspect.getattr_static(product, field, None)) is not MemberDescriptorType
        for field in ("original", "entries", "executables", "planner")
    ):
        raise ContractViolation("owner catalog product must have inert slots")
    if object.__getattribute__(product, "original") is not contribution:
        raise ContractViolation("owner catalog product differs from original pair")
    entries = object.__getattribute__(product, "entries")
    executables = object.__getattribute__(product, "executables")
    planner = object.__getattribute__(product, "planner")
    if (
        type(entries) is not tuple
        or len(entries) != 2
        or any(
            type(item) is not CodeSemanticMaterializationProfileBinding
            for item in entries
        )
        or type(executables) is not tuple
        or len(executables) != 2
        or any(type(item) is not tuple or len(item) != 3 for item in executables)
    ):
        raise ContractViolation("complete owner catalog pair required")
    originals = read_selected_provider_stage_catalog_inputs(contribution)
    for entry in entries:
        entry.__post_init__()
    keys = tuple(
        (
            entry.semantic_owner_key,
            entry.semantic_provider_key,
            entry.profile_declaration.profile_ref,
            entry.profile_declaration.digest.value,
        )
        for entry in entries
    )
    canonical = tuple(
        sorted(set(keys), key=lambda key: tuple(part.encode() for part in key))
    )
    if keys != canonical:
        raise ContractViolation("owner catalog entries must be unique and ordered")
    for original, executable in zip(originals, executables, strict=True):
        implementation, configuration, provider = executable
        if (
            type(implementation) is not SemanticImplementationCoordinate
            or type(configuration) is not SemanticConfigurationCoordinate
            or implementation != original.binding.implementation
            or configuration != original.binding.configuration
            or provider is not original.executable
        ):
            raise ContractViolation("owner catalog executable differs from original")
        matching = [
            entry
            for entry in entries
            if entry.profile_declaration == original.stage.runtime.profile
            and entry.semantic_provider_key == original.binding.provider_key
            and entry.provider_execution_bindings == (original.binding,)
        ]
        if len(matching) != 1:
            raise ContractViolation("owner catalog entry differs from original stage")
    if type(planner).__getattribute__ is not object.__getattribute__:
        raise ContractViolation("owner planner accessor substituted")
    descriptor = inspect.getattr_static(planner, "plan", None)
    if not inspect.isfunction(descriptor):
        raise ContractViolation("original owner planner method required")
    method = object.__getattribute__(planner, "plan")
    if (
        not inspect.ismethod(method)
        or method.__self__ is not planner
        or descriptor is not method.__func__
    ):
        raise ContractViolation("owner planner method substituted")
    return _CatalogProductState(
        product, entries, executables, planner, descriptor, method.__func__
    )


def produce_selected_provider_stage_catalog_contribution(
    contribution: SelectedProviderStageContribution,
) -> SelectedProviderStageCatalogContribution:
    """Call the producer retained by the original factory once, without admission.

    Only an independently authenticated host installation can select the factory.
    This operation validates its result against the original pair; its detached
    read projection cannot authorize catalog publication or provider execution.
    """
    with selected._LOCK:
        state = _state(contribution)
        producer = state.catalog_producer
        if producer is None:
            raise ContractViolation("owner catalog producer unavailable")
        if contribution in _CATALOG_PRODUCTS:
            raise ContractViolation("owner catalog producer already consumed")
        read_selected_provider_stage_contribution(contribution)
        _CATALOG_PRODUCTS[contribution] = _CATALOG_PENDING
        product = producer(contribution)
        if _state(contribution) is not state:
            raise ContractViolation(
                "original stage pair changed during catalog production"
            )
        observed = _validate_catalog_product(contribution, product)
        _CATALOG_PRODUCTS[contribution] = observed
        return read_selected_provider_stage_catalog_contribution(contribution)


def read_selected_provider_stage_catalog_contribution(
    contribution: SelectedProviderStageContribution,
) -> SelectedProviderStageCatalogContribution:
    """Recheck one retained owner product and original live stages before use."""
    with selected._LOCK:
        state = _state(contribution)
        retained = _CATALOG_PRODUCTS.get(contribution)
        if type(retained) is not _CatalogProductState:
            raise ContractViolation("owner catalog contribution unavailable")
        observed = _validate_catalog_product(contribution, retained.product)
        if (
            observed.entries is not retained.entries
            or observed.executables is not retained.executables
            or observed.planner is not retained.planner
            or observed.plan_descriptor is not retained.plan_descriptor
            or observed.plan_function is not retained.plan_function
        ):
            raise ContractViolation("owner catalog product changed")
        if _state(contribution) is not state:
            raise ContractViolation("stage contribution changed during catalog read")
        return SelectedProviderStageCatalogContribution(
            retained.entries, retained.executables, retained.planner
        )


def compose_selected_provider_stage_catalog_input(
    contributions: tuple[SelectedProviderStageContribution, ...],
    *,
    catalog_ref: str,
    catalog_generation: int,
    product_contributions: tuple[SelectedProviderProductContribution, ...] = (),
) -> CodeSemanticContractCatalog:
    """Compose the existing Code catalog value from live original owner products.

    The result is constructible input. Only the existing Code/Workspace catalog
    host can admit and publish it under an original command or service lifetime.
    """
    # DirectCommandExpectedContext admits at most 8192 stage bindings, or 4096
    # complete pairs. Keep this input ceiling identical to the eventual host.
    if (
        type(contributions) is not tuple
        or not 0 < len(contributions) <= 4096
        or any(
            type(item) is not SelectedProviderStageContribution
            for item in contributions
        )
    ):
        raise ContractViolation("bounded original stage contributions required")
    if len({id(item) for item in contributions}) != len(contributions):
        raise ContractViolation("duplicate original stage contribution")
    from .product_contribution import (
        SelectedProviderProductContribution,
        read_selected_provider_product_catalog_contribution,
    )

    if (
        type(product_contributions) is not tuple
        or len(product_contributions) > 4096
        or any(
            type(item) is not SelectedProviderProductContribution
            for item in product_contributions
        )
        or len({id(item) for item in product_contributions})
        != len(product_contributions)
    ):
        raise ContractViolation("bounded original product contributions required")
    observed = tuple(
        read_selected_provider_stage_catalog_contribution(item)
        for item in contributions
    )
    product_observed = tuple(
        read_selected_provider_product_catalog_contribution(item)
        for item in product_contributions
    )
    keys = tuple(value.entries[0].semantic_provider_key for value in observed)
    if keys != tuple(sorted(set(keys), key=str.encode)):
        raise ContractViolation("original catalog owners must be unique and ordered")
    product_keys = tuple(
        value.entries[0].semantic_provider_key for value in product_observed
    )
    if (
        product_keys != tuple(sorted(set(product_keys), key=str.encode))
        or set(product_keys) & set(keys)
    ):
        raise ContractViolation("product catalog owners must be distinct and ordered")
    entries = tuple(
        sorted(
            (
                entry
                for value in (*observed, *product_observed)
                for entry in value.entries
            ),
            key=lambda entry: (
                entry.semantic_owner_key.encode(),
                entry.semantic_provider_key.encode(),
                entry.profile_declaration.profile_ref.encode(),
                entry.profile_declaration.digest.value.encode(),
            ),
        )
    )
    catalog = CodeSemanticContractCatalog.create(
        catalog_ref=catalog_ref,
        catalog_generation=catalog_generation,
        entries=entries,
    )
    for original, first in zip(contributions, observed, strict=True):
        current = read_selected_provider_stage_catalog_contribution(original)
        if (
            current.entries is not first.entries
            or current.executables is not first.executables
            or current.planner is not first.planner
        ):
            raise ContractViolation("owner catalog changed during composition")
    for original, first in zip(
        product_contributions, product_observed, strict=True
    ):
        current = read_selected_provider_product_catalog_contribution(original)
        if (
            current.entries is not first.entries
            or current.executables is not first.executables
            or current.planner is not first.planner
        ):
            raise ContractViolation("owner product catalog changed during composition")
    return catalog


def _close_owned(
    stages: list[RetainedSemanticStageRuntimeExpectation],
) -> list[BaseException]:
    errors: list[BaseException] = []
    for stage in reversed(stages):
        try:
            # Permit retry after partial cleanup; never suppress active execution.
            retained = selected._REGISTRATIONS.get(id(stage.registration))
            if (
                retained is not None
                and retained[0] is stage.registration
                and retained[1].closed
            ):
                continue
            selected.close_selected_provider_registration(
                stage.runtime, stage.registration
            )
        except BaseException as error:  # noqa: BLE001 - attempt all cleanup, then re-raise as a group
            errors.append(error)
    return errors


def close_selected_provider_stage_contribution(
    contribution: SelectedProviderStageContribution,
) -> None:
    """Close owned registrations after application quiescence; retain failed cleanup."""

    with selected._LOCK:
        state = _state(contribution)
        errors = _close_owned(list(state.stages))
        if errors:
            raise BaseExceptionGroup("stage contribution cleanup failed", errors)
        _CATALOG_PRODUCTS.pop(contribution, None)
        del _CONTRIBUTIONS[contribution]


def issue_selected_provider_stage_contribution(
    factory_admission: selected._AdmittedSemanticProviderFactory,
) -> SelectedProviderStageContribution:
    """Invoke the original factory once; never expose a partly registered pair."""

    with selected._LOCK:
        factory = selected._factory_state(factory_admission)
        entrance = factory.selection_factory
    products = entrance()
    if type(products) is not selected.SelectedProviderStageFactoryProduct:
        raise TypeError("stage factory must return the exact pair product")
    products.__post_init__()
    stages: list[RetainedSemanticStageRuntimeExpectation] = []
    roots: list[selected.AdmittedSemanticProviderSelectionRoot] = []
    contribution: SelectedProviderStageContribution | None = None
    with selected._LOCK:
        if selected._factory_state(factory_admission) is not factory:
            raise ContractViolation("stage factory changed during construction")
        pair = (products.source_planning, products.authority_derivation)
        # Fresh ownership is mandatory, including runtimes previously closed.
        if any(
            state.runtime is product.runtime
            for product in pair
            for _, state in selected._SELECTION_ROOTS.values()
        ):
            raise ContractViolation("stage factory must supply fresh owned runtimes")
        if pair[0].runtime.profile.profile_ref == pair[1].runtime.profile.profile_ref:
            raise ContractViolation("stage factory profiles must be distinct")
        try:
            # The same validator serves single-product and paired acquisition.
            for product in pair:
                roots.append(
                    selected._selection_root_from_factory_product(
                        factory_admission, product
                    )
                )
            for label, product, root in zip(
                ("source_planning", "authority_derivation"), pair, roots, strict=True
            ):
                registration = selected.register_selected_provider(
                    product.runtime, root
                )
                stages.append(
                    RetainedSemanticStageRuntimeExpectation(
                        label, product.runtime, registration
                    )
                )
            contribution = SelectedProviderStageContribution(_TOKEN)
            _CONTRIBUTIONS[contribution] = _ContributionState(
                os.getpid(), products, products.catalog_contribution_producer,
                (stages[0], stages[1])
            )
            read_selected_provider_stage_contribution(contribution)
            return contribution
        except BaseException as primary:
            if contribution is not None:
                _CONTRIBUTIONS.pop(contribution, None)
            errors = _close_owned(stages)
            # Registered roots remain part of their original registration history.
            for root in roots:
                if not any(
                    state.selection_root is root
                    for _, state in selected._REGISTRATIONS.values()
                ):
                    selected._SELECTION_ROOTS.pop(id(root), None)
            if errors:
                raise BaseExceptionGroup(
                    "stage acquisition failed with cleanup failures", [primary, *errors]
                ) from None
            raise
