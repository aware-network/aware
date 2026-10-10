"""Original graph-product registrations retained by one fixed Code host.

The catalog and registrations are checked here; node source/currentness and
execution admission remain separate Workspace and Code operations.
"""

from __future__ import annotations

import os
from copy import deepcopy
from dataclasses import dataclass, replace

from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.direct_origin_interfaces import (
    DirectCommandExpectedContext,
    RetainedSemanticProductRuntimeExpectation,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    CodeSemanticContractCatalogResolver,
)
from aware_code_semantic_contract_runtime.runtime import SemanticContractRuntime
from aware_code_semantic_contract_runtime.selected_provider import (
    _registration_state,
    validate_selected_provider_registration,
)


@dataclass(frozen=True, slots=True)
class _ProductRuntimeRetention:
    expected: DirectCommandExpectedContext
    identities: tuple[object, ...]
    products: tuple[tuple[SemanticContractRuntime, object], ...]
    executables: tuple[object, ...]
    entries: tuple[tuple[object, ...], ...]
    catalog_digest: object
    resolver: CodeSemanticContractCatalogResolver
    pid: int
    current_catalog: object = None

    def check_identities(self) -> None:
        """Nominal checks safe under the already-held command parent guard."""
        if self.pid != os.getpid():
            raise ContractViolation("product retention belongs to another process")
        expected = self.expected
        expected.__post_init__()
        if expected.process_id != self.pid or any(
            actual is not original
            for actual, original in zip(
                (
                    expected.invocation_identity,
                    expected.epoch_identity,
                    expected.runtime,
                    expected.catalog,
                ),
                self.identities,
                strict=True,
            )
        ):
            raise ContractViolation("product retention parent identities changed")
        if len(expected.product_runtime_bindings) != len(self.products):
            raise ContractViolation("product binding closure changed")
        for actual, (runtime, registration) in zip(
            expected.product_runtime_bindings, self.products, strict=True
        ):
            if (
                actual.runtime is not runtime
                or actual.registration is not registration
                or _registration_state(registration).runtime is not runtime
            ):
                raise ContractViolation("original product registration changed")

    def validate(self) -> None:
        self.check_identities()
        if self.resolver._admission is not (
            self.current_catalog
            if self.current_catalog is not None
            else self.expected.catalog
        ):
            raise ContractViolation("product catalog admission changed")
        self.resolver.validate_catalog()
        if self.resolver._catalog_coordinates()[2] != self.catalog_digest:
            raise ContractViolation("product catalog digest changed")
        for (runtime, registration), executable, retained in zip(
            self.products, self.executables, self.entries, strict=True
        ):
            provider_key, profile, declaration, binding, entry_digest = retained
            entry = self.resolver.read_profile_binding(
                profile=profile, semantic_provider_key=provider_key
            )
            if (
                entry.binding_digest != entry_digest
                or entry.semantic_provider_key != provider_key
                or entry.profile_declaration != profile
                or binding not in entry.provider_execution_bindings
            ):
                raise ContractViolation("original product catalog entry changed")
            if not any(
                item is executable for item in self.resolver._executable_closure
            ):
                raise ContractViolation("original product executable absent from catalog")
            validate_selected_provider_registration(
                runtime,
                registration,
                expected_profile=profile,
                expected_declaration=declaration,
                expected_binding=binding,
            )
        self.check_identities()

    def successor(
        self,
        resolver: CodeSemanticContractCatalogResolver,
        admission: object,
    ) -> _ProductRuntimeRetention:
        successor = replace(
            self,
            resolver=resolver,
            catalog_digest=resolver._catalog_coordinates()[2],
            current_catalog=admission,
        )
        successor.validate()
        return successor


def _capture_product_runtime_retention(
    expected: DirectCommandExpectedContext,
) -> _ProductRuntimeRetention:
    if type(expected) is not DirectCommandExpectedContext:
        raise TypeError("exact original product context required")
    expected.__post_init__()
    if expected.process_id != os.getpid():
        raise ContractViolation("foreign product context process")
    if not expected.product_runtime_bindings:
        raise ContractViolation("original product bindings required")
    resolver = CodeSemanticContractCatalogResolver(expected.catalog)
    catalog = resolver.catalog
    products = tuple(
        (item.runtime, item.registration)
        for item in expected.product_runtime_bindings
    )
    entries = []
    executables = []
    for runtime, registration in products:
        if type(runtime) is not SemanticContractRuntime:
            raise TypeError("exact product Code runtime required")
        original = _registration_state(registration)
        executables.append(original.provider)
        matches = [
            item
            for item in catalog.entries
            if item.profile_declaration == runtime.profile
            and item.semantic_provider_key == original.provider_key
        ]
        if len(matches) != 1:
            raise ContractViolation("unique live product catalog entry required")
        entry = matches[0]
        providers = [
            item
            for item in entry.profile_declaration.providers
            if item.provider_key == original.provider_key
        ]
        bindings = [
            item
            for item in entry.provider_execution_bindings
            if item.provider_key == original.provider_key
        ]
        if len(providers) != 1 or len(bindings) != 1:
            raise ContractViolation("exact product declaration/binding required")
        entries.append(
            deepcopy(
                (
                    original.provider_key,
                    entry.profile_declaration,
                    providers[0],
                    bindings[0],
                    entry.binding_digest,
                )
            )
        )
    retained = _ProductRuntimeRetention(
        expected,
        (
            expected.invocation_identity,
            expected.epoch_identity,
            expected.runtime,
            expected.catalog,
        ),
        products,
        tuple(executables),
        tuple(entries),
        catalog.catalog_root_digest,
        resolver,
        os.getpid(),
    )
    retained.validate()
    return retained
