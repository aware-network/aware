"""Generic selected product composition for the local public CLI.

The retained declarations select the key. Code's original installed-key intake
supplies its factory; the existing Workspace/Code host checks applicability.
Local source coordinates identify this executable composition, not a Platform
release or protected store. No semantic owner is imported by this module.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple, TypedDict, cast

from aware_code_retained_registry_policy_runtime import (
    declaration_eligibility,
    direct_host,
)
from aware_code_retained_registry_policy_runtime.selected_catalog_eligibility import (
    issue_selected_product_catalog_eligibility,
    read_selected_product_catalog_eligibility,
)
from aware_code_retained_registry_policy_runtime.selected_root_intent import (
    derive_selected_root_intent,
)
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    ContractViolation,
    SemanticConfigurationCoordinate,
    SemanticImplementationCoordinate,
)
from aware_code_semantic_contract_runtime.installed_provider_factory import (
    admit_installed_semantic_stage_factory,
)
from aware_code_semantic_contract_runtime.product_contribution import (
    SelectedProviderProductContribution,
    read_selected_provider_product_contribution,
)

from . import direct_command_composition as composition
from .declaration_scope_admission import WorkspaceSelectedPackageSource
from .semantic_catalog_host import WorkspaceJointCatalogResolvers


class DirectCLIProviderFactoryUnavailable(ContractViolation):
    """The derived key has no original local executable factory admission."""


class DirectCLISelectedDeclarationUnavailable(ContractViolation):
    """The retained selected declaration did not admit a provider request."""


class DirectCLIProductParticipant(NamedTuple):
    """Borrowed original source, selected policy and factory contribution."""

    source: WorkspaceSelectedPackageSource
    provider_key: str
    package_ref: str
    policy: direct_host.AdmittedRegistryPolicy
    contribution: SelectedProviderProductContribution


@dataclass(frozen=True, slots=True)
class DirectCLISelectedProduct:
    """Borrowed host and detached intent; valid only inside its composition."""

    host: composition.DirectWorkspaceSelectedHost
    provider_key: str
    requested_role: str
    catalog_timing_ns: int
    package_ref: str
    package_membership_present: bool
    policy: direct_host.AdmittedRegistryPolicy
    participants: tuple[DirectCLIProductParticipant, ...] = ()


class _Coordinates(TypedDict):
    composition_implementation: SemanticImplementationCoordinate
    composition_configuration: SemanticConfigurationCoordinate
    policy_implementation: SemanticImplementationCoordinate
    policy_configuration: SemanticConfigurationCoordinate


def _coordinates() -> _Coordinates:
    # These are identifiers for the actual local composition and fixed policy.
    # Code's original resource association supplies live authority separately.
    configuration = ContentDigest.of_bytes(
        b'{"contract":"aware.workspace.direct-cli-composition.v1",'
        b'"observation_mode":"command","source_rail":"declaration_v3"}'
    )
    return {
        "composition_implementation": SemanticImplementationCoordinate(
            "aware.workspace.direct-cli.composition",
            ContentDigest.of_bytes(Path(composition.__file__).read_bytes()),
        ),
        "composition_configuration": SemanticConfigurationCoordinate(
            "aware.workspace.direct-cli.composition",
            configuration,
        ),
        "policy_implementation": SemanticImplementationCoordinate(
            "aware.code.declaration-eligibility",
            ContentDigest.of_bytes(Path(declaration_eligibility.__file__).read_bytes()),
        ),
        "policy_configuration": SemanticConfigurationCoordinate(
            "aware.code.declaration-eligibility",
            configuration,
        ),
    }


@contextmanager
def compose_direct_cli_product_candidates(command, selected):
    """Retain declared supplier candidates, never manufacture graph demands.

    Registration/profile members authenticate selection but are not themselves
    materialization candidates. Only direct-dependency arrows reachable from
    the selected semantic occurrence enter this source set.
    """
    view = composition._read_direct_workspace_selected_participants(command, selected)
    original = view.digest
    reached = {view.root}
    pending = [view.root]
    while pending:
        source = pending.pop()
        for edge in view.relationships:
            if edge.kind == "direct_dependency" and edge.source == source and edge.target not in reached:
                reached.add(edge.target)
                pending.append(edge.target)
    addresses = (view.root,) + tuple(sorted(reached - {view.root}))
    try:
        with ExitStack() as retained:
            candidates = (selected,) + tuple(retained.enter_context(
                composition._compose_direct_workspace_selected_package_source(
                    command, workspace_manifest_path=item.scope_key,
                    module_id=item.module_id, package_id=item.package_id,
                )) for item in addresses[1:])
            if composition._read_direct_workspace_selected_participants(command, selected).digest != original:
                raise ContractViolation("original product candidate closure changed")
            for candidate in candidates:
                command.sources.declaration_scope_runtime.read_selected_package_source(candidate)
            yield candidates
            if composition._read_direct_workspace_selected_participants(command, selected).digest != original:
                raise ContractViolation("original product candidate closure changed")
            for candidate in candidates:
                command.sources.declaration_scope_runtime.read_selected_package_source(candidate)
    finally:
        command = selected = view = candidates = candidate = None


@contextmanager
def compose_direct_cli_selected_product(
    command: composition._DirectWorkspaceCommandResources,
    selected: WorkspaceSelectedPackageSource,
    *,
    participating_sources: tuple[WorkspaceSelectedPackageSource, ...] = (),
) -> Iterator[DirectCLISelectedProduct]:
    """Bind selected products under the caller's one original live command.

    No factory callback, key, configuration or registration comes from the
    request. The host owns its contribution and retires it before the borrowed
    command/source lifetime. This does not open a graph node or publish HEAD.
    """
    if type(participating_sources) is not tuple:
        raise TypeError("original participating source tuple required")
    selected_sources = participating_sources or (selected,)
    if (
        not 1 <= len(selected_sources) <= 256
        or selected_sources[0] is not selected
        or any(type(source) is not WorkspaceSelectedPackageSource for source in selected_sources)
        or len({id(source) for source in selected_sources}) != len(selected_sources)
    ):
        raise ContractViolation("unique original participants with selected root first required")
    keys = []
    for source in selected_sources:
        try:
            keys.append(composition._resolve_direct_workspace_exact_provider_key(command, source))
        except ContractViolation as error:
            raise DirectCLISelectedDeclarationUnavailable(str(error)) from error
    factories = {}
    for key in keys:
        if key not in factories:
            try:
                factories[key] = admit_installed_semantic_stage_factory(key)
            except (ContractViolation, ImportError, AttributeError) as error:
                raise DirectCLIProviderFactoryUnavailable(key) from error
    # Entry loading may run Python imports; reject moved source before invoking
    # its factory or assembling a catalog.
    for source, key in zip(selected_sources, keys, strict=True):
        if composition._resolve_direct_workspace_exact_provider_key(command, source) != key:
            raise ContractViolation("selected factory key changed during intake")
    provider_key = keys[0]
    sources = command.sources
    if type(sources) is not composition._DirectWorkspaceDeclarationSources:
        raise TypeError("original declaration sources required")
    issuer = sources.declaration_scope_runtime
    binding = issuer.read_selected_package_source(selected)
    started_ns = time.perf_counter_ns()
    with composition.compose_direct_workspace_selected_host(
        product_factory_admissions=tuple(factories.values()),
        session=sources.observation_runtime._session,
        store=sources.observation_runtime._store,
        workspace_manifest_path=binding.expectation.scope_key,
        command_resources=command,
        selected_package_sources=selected_sources,
        **_coordinates(),
    ) as host:
        catalog_timing_ns = time.perf_counter_ns() - started_ns
        if type(host.code_host) is not direct_host.DirectValidationHost:
            raise TypeError("original Code direct host required")
        code_host = cast(direct_host.DirectValidationHost, host.code_host)
        participants = []
        eligibilities = []
        for source, key in zip(selected_sources, keys, strict=True):
            policy = direct_host.produce_registry_policy(code_host, source)
            matches = tuple(
                contribution for contribution in host.staged.product_contributions
                if read_selected_provider_product_contribution(contribution).binding.provider_key == key
            )
            if len(matches) != 1:
                raise ContractViolation("unique original participant contribution required")
            contribution, = matches
            registration = read_selected_provider_product_contribution(contribution).expected.registration
            eligibility = issue_selected_product_catalog_eligibility(code_host, policy, registration)
            view = read_selected_product_catalog_eligibility(eligibility)
            if view.semantic_provider_key != key:
                raise ContractViolation("original product differs from selected declaration")
            context, _inventory = issuer.inspect_inputs(source)
            participants.append(DirectCLIProductParticipant(
                source, key, context.package.package_ref, policy, contribution,
            ))
            eligibilities.append(eligibility)
        if len({item.package_ref for item in participants}) != len(participants):
            raise ContractViolation("participating package coordinates collide")
        policy = participants[0].policy
        _intent, product = derive_selected_root_intent(code_host, policy)
        root_view = read_selected_product_catalog_eligibility(eligibilities[0])
        if product.role not in root_view.terminal_roles:
            raise ContractViolation("original product differs from selected declaration")
        package_context, _inventory = issuer.inspect_inputs(selected)
        if type(host.catalog_pair) is not WorkspaceJointCatalogResolvers:
            raise TypeError("original Workspace paired catalog required")
        pair = cast(WorkspaceJointCatalogResolvers, host.catalog_pair)
        member = pair.workspace.package_if_present(package_context.package.package_ref)
        result = DirectCLISelectedProduct(
            host,
            provider_key,
            product.role,
            catalog_timing_ns,
            package_context.package.package_ref,
            member is not None,
            policy,
            tuple(participants),
        )
        try:
            yield result
            for eligibility in eligibilities:
                read_selected_product_catalog_eligibility(eligibility)
            composition._require_live_direct_workspace_command(command)
        finally:
            result = policy = eligibility = registration = None
