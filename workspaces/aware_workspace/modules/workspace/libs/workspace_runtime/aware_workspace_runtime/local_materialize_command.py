"""Local command composition over the existing source, catalog and Code rails.

Application composition supplies original provider admissions and coordinates.
The CLI proposal supplies only selection and intent. This module neither issues
installation authority nor implements another planner or semantic executor.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from aware_code_retained_registry_policy_runtime import direct_host, operation_context
from aware_code_retained_registry_policy_runtime.operation_derivation import (
    RetainedSourcePlanningRequest,
)
from aware_code_retained_registry_policy_runtime.planning_execution import (
    bind_planning_execution_origin,
)
from aware_code_retained_registry_policy_runtime.retained_input_admission import (
    assemble_retained_input_admission_origin,
)
from aware_code_semantic_contract_runtime import (
    ExecutionCompletion,
    SemanticConfigurationCoordinate,
    SemanticContractInvocation,
    SemanticImplementationCoordinate,
)
from aware_code_semantic_contract_runtime.selected_provider import (
    SelectedProviderInvocationClosure,
    _AdmittedSemanticProviderFactory,
    execute_selected_provider,
    issue_selected_provider_execution,
)
from aware_workspace_materialize_transport import WorkspaceMaterializeCommandProposalV3
from aware_workspace_sdk.repository_delta_retention import (
    WorkspaceRepositoryDeltaRetentionClient,
)

from . import direct_command_composition as composition
from .declaration_scope_admission import WorkspaceSelectedPackageSource
from .observation import WorkspaceRepositoryObservationSession


@dataclass(frozen=True, slots=True)
class LocalWorkspaceMaterializeCommand:
    """Borrowed views of one live original command; construction grants nothing."""

    host: composition.DirectWorkspaceSelectedHost
    inspection: composition.WorkspaceDirectCLISourceInspection
    selected_source: WorkspaceSelectedPackageSource
    provider_key: str

    def validate(self) -> None:
        composition._require_live_direct_workspace_command(self.host.staged.command)
        if composition._POLICY_HOSTS.get(self.host.code_host) is not self.host.staged:
            raise RuntimeError("original local Code host is no longer live")
        actual = composition._resolve_direct_workspace_exact_provider_key(
            self.host.staged.command, self.selected_source,
        )
        if actual != self.provider_key:
            raise RuntimeError("local selected provider changed")

    def execute_planning(
        self,
        *,
        request: RetainedSourcePlanningRequest,
        invocation: SemanticContractInvocation,
    ) -> ExecutionCompletion:
        """Use the original three-admission join and tracked selected executor.

        The owner supplies its body contracts and invocation. Code validates
        their exact correspondence to retained Workspace source. No owner
        parser, result, completion or genesis is manufactured here.
        """
        self.validate()
        if type(request) is not RetainedSourcePlanningRequest:
            raise TypeError("exact retained planning request required")
        if type(invocation) is not SemanticContractInvocation:
            raise TypeError("exact selected invocation required")
        host = self.host.code_host
        if type(host) is not direct_host.DirectValidationHost:
            raise TypeError("original Code host required")
        stage = self.host.staged.stage_runtime_bindings[0]
        policy = direct_host.produce_registry_policy(host, self.selected_source)
        context = operation_context.begin_source_planning_operation(
            host, policy, stage.registration, request,
        )
        expected = operation_context.source_planning_expectation(host, context)
        sources = self.host.staged.command.sources
        if type(sources) is not composition._DirectWorkspaceDeclarationSources:
            raise TypeError("original declaration sources required")
        issuer = sources.declaration_scope_runtime
        package, inventory = issuer.issue_source_planning_pair(
            self.selected_source, context=context, expected=expected,
        )
        origin = assemble_retained_input_admission_origin(host)
        registry = origin.issue_registry_package_admission(context, package)
        joined = origin.join(context, registry, package, inventory)
        origin.validate(joined)
        bind_planning_execution_origin(
            host, stage.registration, terminal_mode="runtime_completion",
        )
        bodies = tuple(sorted(
            (
                request.manifest_source, request.candidate_listing,
                request.registry_package, request.package_context,
                request.declaration_inventory,
            ),
            key=lambda body: body.coordinate.role,
        ))
        execution = issue_selected_provider_execution(
            stage.runtime, stage.registration,
            SelectedProviderInvocationClosure(invocation, bodies),
            operation_context=context,
        )
        completion = execute_selected_provider(stage.runtime, execution)
        self.validate()
        if type(completion) is not ExecutionCompletion or not stage.runtime.owns_completion(completion):
            raise RuntimeError("original Code planning completion required")
        return completion


@contextmanager
def compose_local_materialize_command(
    *,
    proposal: WorkspaceMaterializeCommandProposalV3,
    session: WorkspaceRepositoryObservationSession,
    store: WorkspaceRepositoryDeltaRetentionClient,
    factory_admission: _AdmittedSemanticProviderFactory,
    composition_implementation: SemanticImplementationCoordinate,
    composition_configuration: SemanticConfigurationCoordinate,
    policy_implementation: SemanticImplementationCoordinate,
    policy_configuration: SemanticConfigurationCoordinate,
    product_factory_admissions: tuple[_AdmittedSemanticProviderFactory, ...] = (),
) -> Iterator[LocalWorkspaceMaterializeCommand]:
    """Keep selection, Code execution and consumer work in one command lifetime.

    Source resources are borrowed; the caller closes them after this context.
    Factories are original Code admissions selected by application composition,
    never request fields. Profile applicability remains Code's responsibility.
    The installed Platform continuation is not used or changed.
    """
    if type(proposal) is not WorkspaceMaterializeCommandProposalV3:
        raise TypeError("exact-address local command proposal required")
    if proposal.participant_checkout_root != str(session.binding.root_path):
        raise RuntimeError("local proposal differs from original repository binding")
    with composition._compose_direct_workspace_command_source(
        session=session, store=store, proposal=proposal,
    ) as (command, inspection, selected):
        if selected is None:
            raise RuntimeError("original exact selected source required")
        provider_key = composition._resolve_direct_workspace_exact_provider_key(
            command, selected,
        )
        with composition.compose_direct_workspace_selected_host(
            factory_admission=factory_admission,
            product_factory_admissions=product_factory_admissions,
            session=session, store=store,
            workspace_manifest_path=proposal.workspace_manifest_name,
            command_resources=command,
            composition_implementation=composition_implementation,
            composition_configuration=composition_configuration,
            policy_implementation=policy_implementation,
            policy_configuration=policy_configuration,
        ) as host:
            if any(
                tuple(owner.provider_key for owner in stage.runtime.profile.providers)
                != (provider_key,)
                for stage in host.staged.stage_runtime_bindings
            ):
                raise RuntimeError("local factory differs from selected profile provider")
            local = LocalWorkspaceMaterializeCommand(
                host, inspection, selected, provider_key,
            )
            local.validate()
            try:
                yield local
                local.validate()
            finally:
                # Do not leave the context-manager frame as additional custody
                # when its consumer keeps an exception traceback alive.
                local = None
