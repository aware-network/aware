"""Original graph-product registrations retained by one fixed Code host.

The catalog and registrations are checked here; node source/currentness and
execution admission remain separate Workspace and Code operations.
"""

from __future__ import annotations

import os
from copy import deepcopy
from dataclasses import dataclass, replace

from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    ProviderExecutionBinding,
)
from aware_code_semantic_contract_runtime.direct_origin_interfaces import (
    DirectCommandExpectedContext,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    CodeSemanticContractCatalogResolver,
    CodeSemanticMaterializationProfileBinding,
)
from aware_code_semantic_contract_runtime.profile import (
    SemanticContractProfileDeclaration,
    SemanticContractProviderDeclaration,
)
from aware_code_semantic_contract_runtime.runtime import SemanticContractRuntime
from aware_code_semantic_contract_runtime.selected_provider import (
    AdmittedSemanticProviderRegistration,
    _registration_state,
    validate_selected_provider_registration,
)

type _ProductEntry = tuple[
    str, SemanticContractProfileDeclaration, SemanticContractProviderDeclaration,
    ProviderExecutionBinding, ContentDigest,
]


@dataclass(frozen=True, slots=True)
class _ProductRuntimeRetention:
    expected: DirectCommandExpectedContext
    identities: tuple[object, ...]
    products: tuple[tuple[SemanticContractRuntime, AdmittedSemanticProviderRegistration], ...]
    executables: tuple[object, ...]
    entries: tuple[_ProductEntry, ...]
    catalog_digest: ContentDigest
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
        if self.resolver._validate_retained_catalog_coordinate()[2] != self.catalog_digest:
            raise ContractViolation("product catalog digest changed")
        for (runtime, registration), executable, retained in zip(
            self.products, self.executables, self.entries, strict=True
        ):
            provider_key, profile, declaration, binding, entry_digest = retained
            entry = self._read_original_entry(provider_key, profile, entry_digest)
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

    def _read_original_entry(self, provider_key, profile, entry_digest):
        """Detached metadata under the original complete catalog coordinate fence."""
        if self.resolver._validate_retained_catalog_coordinate()[2] != self.catalog_digest:
            raise ContractViolation("product catalog digest changed")
        matches = [
            entry for entry in self.resolver._catalog.entries
            if entry.semantic_provider_key == provider_key
            and entry.profile_declaration.profile_ref == profile.profile_ref
            and entry.profile_declaration.version == profile.version
        ]
        if len(matches) != 1:
            raise ContractViolation("exact product catalog entry unavailable")
        snapshot = deepcopy(matches[0])
        if (
            type(snapshot) is not CodeSemanticMaterializationProfileBinding
            or snapshot.binding_digest != entry_digest
        ):
            raise ContractViolation("original product catalog entry changed")
        if self.resolver._validate_retained_catalog_coordinate()[2] != self.catalog_digest:
            raise ContractViolation("product catalog digest changed")
        return snapshot

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

    def validate_declared_profile(
        self, declaration, *, package_kind: str,
    ) -> tuple[AdmittedSemanticProviderRegistration, CodeSemanticMaterializationProfileBinding]:
        """Bind an authenticated v3 graph_product declaration to its live owner.

        No package kind, role or matching name can substitute for the exact
        declared profile digest and original catalog-backed registration.
        Source/participation authority remains the enclosing selected policy.
        """
        from .calculation import _execution_entry_correspondence, _plain

        self.validate()
        value = _plain(declaration)
        profiles = value["profiles"]
        if len(profiles) != 1 or profiles[0]["stage"] != "graph_product":
            raise ContractViolation("one declared graph_product profile required")
        declared = profiles[0]
        provider_key = value["semantic_contract"]["provider_key"]
        matches = [
            ((runtime, original), retained)
            for (runtime, original), retained in zip(
                self.products, self.entries, strict=True
            )
            if retained[0] == provider_key
            and declared == {
                "stage": "graph_product",
                "profile_ref": retained[1].profile_ref,
                "profile_version": retained[1].version,
                "profile_digest": retained[1].digest.to_wire(),
            }
        ]
        if len(matches) != 1:
            raise ContractViolation("exact declared live product profile unavailable")
        (runtime, registration), retained = matches[0]
        profile = retained[1]
        entry = self._read_original_entry(provider_key, profile, retained[4])
        if entry.binding_digest != retained[4] or runtime.profile != profile:
            raise ContractViolation("declared product catalog binding changed")
        _execution_entry_correspondence(value, entry, package_kind=package_kind)
        if "materialize" not in profile.operation_kinds:
            raise ContractViolation("declared product profile inapplicable")
        self.validate()
        return registration, entry


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
    entries: list[_ProductEntry] = []
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
