"""Fixed source-resource assembly for the future direct command composition.

This internal step borrows already admitted repository resources. It does not
authenticate Code bootstrap, bind a partial Code context or expose a new CLI.
"""

from __future__ import annotations

import hashlib
import inspect
import os
import secrets
import time
from collections.abc import AsyncIterator, Callable, Iterator
from contextlib import ExitStack, asynccontextmanager, contextmanager, nullcontext
from dataclasses import dataclass, field, fields
from pathlib import Path
from threading import RLock, current_thread, get_ident
from typing import TYPE_CHECKING, Any, cast
from weakref import WeakKeyDictionary, WeakSet, finalize, ref

from aware_code_package_delta_contract import CodePackageOutputState
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    SemanticBody,
    SemanticContractProviderDeclaration,
    SemanticContractRef,
    SemanticPackageCoordinate,
)
from aware_code_semantic_contract_runtime import (
    selected_input_verification as _input_values,
)
from aware_code_semantic_contract_runtime.catalog_epoch_interfaces import (
    DirectInvocationExpectation,
)
from aware_code_semantic_contract_runtime.direct_origin_interfaces import (
    RetainedSemanticProductRuntimeExpectation,
    RetainedSemanticStageRuntimeExpectation,
)
from aware_code_semantic_contract_runtime.product_contribution import (
    SelectedProviderProductContribution,
    close_selected_provider_product_contribution,
    issue_selected_provider_product_contribution,
    produce_selected_provider_product_catalog_contribution,
    read_selected_provider_product_catalog_contribution,
    read_selected_provider_product_contribution,
)
from aware_code_semantic_contract_runtime.retained_declaration_scope import (
    CodeDeclarationScopeExpectation,
)
from aware_code_semantic_contract_runtime.selected_provider import (
    SelectedProviderInvocationClosure,
    _AdmittedSemanticProviderFactory,
)
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputPackageIdentity,
    SemanticInputProductionExpectation,
)
from aware_code_semantic_contract_runtime.stage_contribution import (
    SelectedProviderStageContribution,
    close_selected_provider_stage_contribution,
    compose_selected_provider_stage_catalog_input,
    issue_selected_provider_stage_contribution,
    produce_selected_provider_stage_catalog_contribution,
    read_selected_provider_stage_catalog_contribution,
    read_selected_provider_stage_contribution,
)
from aware_local_service_runtime import LocalOperationalNamespaceSnapshot
from aware_workspace_materialize_transport import (
    WorkspaceMaterializeCommandProposalV2,
    WorkspaceMaterializeCommandProposalV3,
    WorkspaceMaterializeSelectedRootV1,
)
from aware_workspace_materialize_transport.contracts import (
    WorkspaceMaterializeHostOperationReceiptV1,
)
from aware_workspace_sdk.repository_delta_retention import (
    WorkspaceRepositoryDeltaRetentionClient,
    WorkspaceRepositoryDeltaRetentionFactory,
)

from . import selected_owner_lifetime as _owner_lifetime
from .code_scope_adapter import WorkspaceCodeScopeAdapter
from .command_lifetime import (
    WorkspaceCommandLifetimeRuntime,
    WorkspaceDirectInvocationParent,
)
from .complete_scope_observation import (
    WorkspaceCompleteScopeObservationRuntime,
)
from .contracts import WorkspaceRepositoryBinding
from .declaration_scope_admission import (
    WorkspaceDeclarationScope,
    WorkspaceDeclarationScopeRuntime,
    WorkspaceSelectedPackageSource,
)
from .dependency_fulfillment import _Fulfillment
from .dependency_scope_adapter import WorkspaceCodeDependencyScopeAdapter
from .dependency_scope_admission import WorkspaceDependencyScopeRuntime
from .dependency_scope_operations import _install_operation_origin
from .materialization_declaration_selection import (
    WorkspaceDeclaredMaterializationRoot,
)
from .materialization_membership_catalog import (
    WorkspaceSemanticMaterializationMembershipCatalog,
)
from .materialization_selection import WorkspaceMaterializationSelectionProposal
from .observation import WorkspaceRepositoryObservationSession
from .observed_membership import WorkspaceObservedPackageMembershipRuntime
from .provider import FileSystemIndexObservationProvider
from .semantic_catalog_host import (
    WorkspaceSemanticCatalogHost,
    _assemble_command_catalog_host,
)
from .semantic_issuer_factory import WorkspaceSourcePlanningSemanticIssuerRuntime
from .source_admission import (
    WorkspaceOwnerDefinedSourceAdmissionRuntime,
    WorkspaceV3OwnerDefinedSourceAdmissionRuntime,
)
from .source_exclusion import WorkspaceSourceExclusion
from .source_observation import (
    WorkspaceRetainedDeclarationObservation,
    WorkspaceRetainedRootObservation,
    WorkspaceSourceObservationRuntime,
)
from .source_observation_io import SourceObservationUnavailable

if TYPE_CHECKING:
    from .semantic_materialization_publication import (
        WorkspaceMaterializationPackageOccurrenceV4,
    )

_COMMAND_ASSEMBLIES = WeakKeyDictionary()
_STAGED_ASSEMBLIES = WeakKeyDictionary()
_POLICY_HOSTS = WeakKeyDictionary()
_ORIGIN_FACTORIES = WeakSet()
_COMMAND_NODE_SESSIONS = WeakKeyDictionary()
_COMMAND_NODE_SESSIONS_LOCK = RLock()
_SELECTED_INPUT_FACTORIES = WeakKeyDictionary()
_SELECTED_INPUT_NODES: list[tuple[Any, Any]] = []
_SELECTED_INPUT_NODES_LOCK = RLock()
_SELECTED_INPUT_NODES_PID = os.getpid()


class _InstalledWorkspaceCommandContinuation:
    """Nonportable receiving handle; only an original pair can reach issuance."""

    __slots__ = (  # noqa: RUF023 - fixed seven-field receiving descriptor order
        "original_child_delivery", "original_installed_composition",
        "command_resources", "inspection", "execution_inputs",
        "candidate_result", "phase",
    )

    def __new__(cls):
        raise TypeError("original installed command continuation required")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("installed command continuation is final")

    def __reduce_ex__(self, protocol):
        raise TypeError("installed command continuation is process-local")


_INSTALLED_CONTINUATION_SLOTS = tuple(
    _InstalledWorkspaceCommandContinuation.__dict__[name]
    for name in _InstalledWorkspaceCommandContinuation.__slots__
)
_INSTALLED_CONTINUATION_PROCESS = os.getpid()
# One-family receiving custody, not an installation issuer. No constructor,
# content value or inspection can populate it before the original pair check.
_INSTALLED_CONTINUATION_RECORD = None


@dataclass(slots=True, eq=False)
class _InstalledWorkspaceContinuationRecord:
    continuation: object
    process_id: int
    thread: object
    references: tuple
    resources: tuple
    proposal_wire: bytes
    pair_calls: tuple
    phase: str = "opening"
    held: bool = False
    source_context: object = None
    host_context: object = None
    selected_host: object = None
    source_opened: bool = False
    host_opened: bool = False
    source_closed: bool = False
    host_closed: bool = False
    close_started: bool = False
    release_started: bool = False
    source_result: object = None
    registry_policy: object = None
    source_resources: object = None


def _installed_continuation_values(continuation):
    try:
        return tuple(
            slot.__get__(continuation, _InstalledWorkspaceCommandContinuation)
            for slot in _INSTALLED_CONTINUATION_SLOTS
        )
    finally:
        continuation = None


def _publish_installed_continuation_phase(record, phase):
    try:
        record.phase = phase
        _INSTALLED_CONTINUATION_SLOTS[6].__set__(record.continuation, phase)
    finally:
        record = phase = None


def _hold_installed_continuation(record):
    try:
        record.held = True
        _publish_installed_continuation_phase(record, "held")
    finally:
        record = None


def _require_installed_continuation_record(original_continuation):
    record = None
    values = None
    try:
        # A fork refuses before touching inherited custody or any lock.
        if os.getpid() != _INSTALLED_CONTINUATION_PROCESS:
            raise RuntimeError("installed continuation belongs to its original process")
        record = _INSTALLED_CONTINUATION_RECORD
        if type(record) is not _InstalledWorkspaceContinuationRecord or record.continuation is not original_continuation:
            raise TypeError("original enrolled Workspace continuation required")
        if record.thread is not current_thread() or record.process_id != os.getpid():
            raise RuntimeError("installed continuation belongs to its original thread")
        # Only the recognized local family may be held. Missing slots and
        # interruptions during structural checks must also make it terminal.
        try:
            if type(original_continuation) is not _InstalledWorkspaceCommandContinuation:
                raise TypeError("original enrolled Workspace continuation required")
            values = _installed_continuation_values(original_continuation)
            if (
                record.held
                or any(a is not b for a, b in zip(values[:6], record.references, strict=True))
                or type(values[6]) is not str or values[6] != record.phase
            ):
                raise RuntimeError("installed continuation changed or held")
            return record
        except BaseException:
            _hold_installed_continuation(record)
            raise
    finally:
        # An unknown lookup must not retain another family's custody in errors.
        original_continuation = record = values = None


def _require_installed_workspace_continuation_binding(
    original_continuation, *, original_child_delivery,
    original_installed_composition, original_command,
) -> None:
    record = None
    try:
        record = _require_installed_continuation_record(original_continuation)
        if (
            record.phase != "opening" or not record.source_opened
            or record.close_started
            or record.references[0] is not original_child_delivery
            or record.references[1] is not original_installed_composition
            or record.references[2] is not original_command
        ):
            raise RuntimeError("original Workspace command binding differs")
        _require_live_direct_workspace_command(original_command)
        if (
            type(record.source_resources) is not tuple
            or len(record.source_resources) != 2
            or original_command.sources.observation_runtime._session
            is not record.source_resources[0]
            or original_command.sources.observation_runtime._store
            is not record.source_resources[1]
        ):
            raise RuntimeError("original Workspace command resources differ")
    except BaseException:
        if record is not None:
            _hold_installed_continuation(record)
        raise
    finally:
        original_continuation = original_child_delivery = None
        original_installed_composition = original_command = record = None


def _read_installed_workspace_provider_key(
    original_continuation, *, original_child_delivery,
    original_installed_composition, original_command,
) -> str:
    """Read this live command's profile key before installed factory acquisition.

    The key is a non-authorizing installation request. Platform's full reader
    calls this before and after acquisition; neither read spends a resource
    borrow or supplies an original factory, registration or semantic input.
    """
    record = source_result = selected = inspection = root = binding = issuer = None
    provider_key = None
    try:
        record = _require_installed_continuation_record(original_continuation)
        _require_installed_workspace_continuation_binding(
            original_continuation, original_child_delivery=original_child_delivery,
            original_installed_composition=original_installed_composition,
            original_command=original_command,
        )
        # Full observation and Code eligibility must not reacquire the parent.
        if original_command.lifetime_runtime._guard is not None:
            raise RuntimeError("installed profile read requires released guard")
        source_result = record.source_result
        if (
            type(source_result) is not tuple or len(source_result) != 3
            or source_result[0] is not original_command
            or source_result[1] is not record.references[3]
        ):
            raise RuntimeError("installed original source-context result changed")
        inspection, selected = source_result[1:]
        if (
            type(inspection) is not WorkspaceDirectCLISourceInspection
            or type(selected) is not WorkspaceSelectedPackageSource
        ):
            raise SourceObservationUnavailable(
                "installed_exact_profile_source_unavailable"
            )
        root = inspection.selected_root
        if type(root) is not WorkspaceMaterializeSelectedRootV1:
            raise SourceObservationUnavailable(
                "installed_exact_profile_root_unavailable"
            )
        issuer = original_command.sources.declaration_scope_runtime
        binding = issuer.read_selected_package_source(selected)
        if (
            binding.expectation.scope_key != root.workspace_manifest_path
            or binding.expectation.module_id != root.module_id
            or binding.expectation.package_id != root.package_id
            or binding.expectation.source_identity_digest.to_wire()
            != root.source_identity_digest
        ):
            raise RuntimeError(
                "installed profile source differs from command selection"
            )
        provider_key = _resolve_direct_workspace_exact_provider_key(
            original_command, selected
        )
        if type(provider_key) is not str or not provider_key:
            raise RuntimeError("original selected profile key unavailable")
        if record.source_result is not source_result:
            raise RuntimeError("installed source changed during profile read")
        _require_installed_workspace_continuation_binding(
            original_continuation, original_child_delivery=original_child_delivery,
            original_installed_composition=original_installed_composition,
            original_command=original_command,
        )
        return provider_key
    except BaseException:
        if record is not None:
            _hold_installed_continuation(record)
        raise
    finally:
        original_continuation = original_child_delivery = None
        original_installed_composition = original_command = None
        record = source_result = selected = inspection = root = binding = issuer = None
        provider_key = None


def _require_installed_workspace_continuation_closed(
    original_continuation, *, original_child_delivery,
    original_installed_composition,
) -> None:
    record = None
    try:
        record = _require_installed_continuation_record(original_continuation)
        if (
            record.phase != "closed" or not record.close_started
            or not record.source_closed or not record.host_closed
            or record.references[0] is not original_child_delivery
            or record.references[1] is not original_installed_composition
        ):
            raise RuntimeError("known original Workspace closure unavailable")
        # The command registry is retired now; never call its live-use reader.
    except BaseException:
        if record is not None:
            _hold_installed_continuation(record)
        raise
    finally:
        original_continuation = original_child_delivery = None
        original_installed_composition = record = None


def _close_installed_workspace_contexts(record):
    """Spend cleanup once; uncertainty preserves custody and the parent."""
    command = None
    try:
        if os.getpid() != _INSTALLED_CONTINUATION_PROCESS or record.thread is not current_thread():
            raise RuntimeError("installed continuation close belongs to its original process/thread")
        if record.close_started:
            raise RuntimeError("installed continuation close already started")
        record.close_started = True
        if not record.held:
            _publish_installed_continuation_phase(record, "closing")
        command = record.references[2]
        if command is not None and command.owner_attachment_position[0] is not None:
            # Owner abort/cancellation routing must be joined before this can
            # close a command with an attached invocation. Never guess cleanup.
            raise SourceObservationUnavailable("installed_owner_cleanup_join_unavailable")
        if record.host_context is not None:
            if not record.host_opened:
                raise SourceObservationUnavailable("installed_host_entry_uncertain")
            record.host_context.__exit__(None, None, None)
            record.host_closed = True
        if record.source_context is not None:
            if not record.source_opened:
                raise SourceObservationUnavailable("installed_source_entry_uncertain")
            record.source_context.__exit__(None, None, None)
            record.source_closed = True
        if not record.held:
            _publish_installed_continuation_phase(record, "closed")
    except BaseException:
        _hold_installed_continuation(record)
        raise
    finally:
        command = record = None


@asynccontextmanager
async def _compose_installed_workspace_materialize_command(
    *, proposal_wire: bytes, original_child_delivery, original_installed_composition,
):
    """Borrow one authenticated pair into the existing live source/host contexts.

    Platform's original-pair gate is still closed. This source cannot create
    RELEASE, resources, private inputs or execution/publication permission.
    """
    global _INSTALLED_CONTINUATION_RECORD
    record = continuation = resources = source_resources = source_result = None
    proposal = pair_entry = require_pair = read_resources = None
    read_source_resources = bind_command = release_borrow = None
    errors = []
    try:
        from aware_environment_protected_store_delivery_runtime import (
            command_entry as pair_entry,
        )
        from aware_workspace_command.materialize_command import (
            _decode_installed_workspace_proposal_wire,
        )

        require_pair = pair_entry._require_original_installed_workspace_pair
        read_resources = pair_entry._read_original_installed_workspace_resources
        read_source_resources = (
            pair_entry._read_original_installed_workspace_source_resources
        )
        bind_command = pair_entry._bind_original_installed_workspace_command
        release_borrow = pair_entry._release_original_installed_workspace_borrow
        require_pair(
            original_child_delivery, original_installed_composition,
            proposal_wire=proposal_wire,
        )
        if os.getpid() != _INSTALLED_CONTINUATION_PROCESS or _INSTALLED_CONTINUATION_RECORD is not None:
            raise RuntimeError("installed receiving position unavailable")
        proposal = _decode_installed_workspace_proposal_wire(proposal_wire)
        continuation = object.__new__(_InstalledWorkspaceCommandContinuation)
        values = (original_child_delivery, original_installed_composition, None, None, None, None, "opening")
        for slot, value in zip(_INSTALLED_CONTINUATION_SLOTS, values, strict=True):
            slot.__set__(continuation, value)
        record = _InstalledWorkspaceContinuationRecord(
            continuation, os.getpid(), current_thread(), values[:6], (),
            proposal_wire, (
                pair_entry, require_pair, read_resources, bind_command,
                release_borrow, read_source_resources,
            ),
        )
        _INSTALLED_CONTINUATION_RECORD = record
        # Retain the actual return before any local qualification or cleanup.
        record.source_resources = read_source_resources(
            original_child_delivery, original_installed_composition,
            original_continuation=continuation,
        )
        source_resources = record.source_resources
        if type(source_resources) is not tuple or len(source_resources) != 2:
            raise TypeError("two original installed source resources required")
        if (
            type(source_resources[0]) is not WorkspaceRepositoryObservationSession
            or type(source_resources[1]) is not WorkspaceRepositoryDeltaRetentionClient
        ):
            raise TypeError("original Workspace observation and Delta store required")
        source_resources[1].verify_repository_binding(
            expected_binding_ref=source_resources[0].binding.binding_key,
        )
        if proposal.participant_checkout_root != str(
            source_resources[0].binding.root_path
        ):
            raise ValueError("proposal repository differs from original binding")
        require_pair(original_child_delivery, original_installed_composition, proposal_wire=proposal_wire)
        record.source_context = _compose_direct_workspace_command_source(
            session=source_resources[0], store=source_resources[1], proposal=proposal,
        )
        record.source_result = record.source_context.__enter__()
        record.source_opened = True
        source_result = record.source_result
        command, inspection, _selected = source_result
        if type(_selected) is not WorkspaceSelectedPackageSource:
            raise SourceObservationUnavailable(
                "installed_exact_profile_source_unavailable"
            )
        _INSTALLED_CONTINUATION_SLOTS[2].__set__(continuation, command)
        _INSTALLED_CONTINUATION_SLOTS[3].__set__(continuation, inspection)
        record.references = _installed_continuation_values(continuation)[:6]
        bind_command(
            original_child_delivery, original_installed_composition,
            original_continuation=continuation, original_command=command,
        )
        require_pair(
            original_child_delivery, original_installed_composition,
            proposal_wire=proposal_wire,
        )
        # Platform derives the original key through the fixed readback above;
        # its factory completion must preserve these same source borrowers.
        record.resources = read_resources(
            original_child_delivery, original_installed_composition,
            original_continuation=continuation,
        )
        resources = record.resources
        if (
            type(resources) is not tuple or len(resources) != 8
            or resources[0] is not source_resources[0]
            or resources[1] is not source_resources[1]
        ):
            raise TypeError(
                "eight original installed resources must preserve source borrow"
            )
        _require_installed_workspace_continuation_binding(
            continuation, original_child_delivery=original_child_delivery,
            original_installed_composition=original_installed_composition,
            original_command=command,
        )
        require_pair(original_child_delivery, original_installed_composition, proposal_wire=proposal_wire)
        record.host_context = compose_direct_workspace_selected_host(
            session=resources[0], store=resources[1], factory_admission=resources[2],
            product_factory_admissions=resources[3], composition_implementation=resources[4],
            composition_configuration=resources[5], policy_implementation=resources[6],
            policy_configuration=resources[7], workspace_manifest_path=proposal.workspace_manifest_name,
            command_resources=command,
        )
        record.selected_host = record.host_context.__enter__()
        record.host_opened = True
        _publish_installed_continuation_phase(record, "open")
        yield continuation
        _require_installed_continuation_record(continuation)
        if record.phase != "complete":
            raise SourceObservationUnavailable("installed_command_completion_unavailable")
    except BaseException as error:  # noqa: BLE001 - preserve cancellation and original unwind errors
        if record is not None:
            _hold_installed_continuation(record)
        errors.append(error)
    finally:
        if record is not None:
            try:
                _close_installed_workspace_contexts(record)
                if not record.held:
                    record.release_started = True
                    release_borrow(
                        original_child_delivery, original_installed_composition,
                        original_continuation=continuation,
                    )
                    # The caller may retain its spent handle. It must not keep
                    # a second strong alias to retired/borrowed owner resources.
                    for slot in _INSTALLED_CONTINUATION_SLOTS[:6]:
                        slot.__set__(continuation, None)
                    record.references = (None,) * 6
                    record.resources = ()
                    record.source_context = record.host_context = record.selected_host = None
                    record.source_result = record.registry_policy = None
                    record.source_resources = None
                    record.pair_calls = ()
                    record.proposal_wire = b""
                    _INSTALLED_CONTINUATION_RECORD = None
            except BaseException as error:  # noqa: BLE001 - preserve cancellation and original unwind errors
                _hold_installed_continuation(record)
                errors.append(error)
        # Preserve only admitted receiving custody, never additional locals in
        # held rejection frames. Borrowed resources aren't disposed here.
        proposal_wire = original_child_delivery = original_installed_composition = None
        record = continuation = resources = source_resources = source_result = None
        command = inspection = _selected = values = slot = value = None
        proposal = pair_entry = require_pair = read_resources = None
        read_source_resources = bind_command = release_borrow = None
    if len(errors) == 1:
        raise errors[0]
    if errors:
        raise BaseExceptionGroup("installed Workspace command/closure failed", errors)


def _prepare_installed_workspace_private_stage_source(record) -> None:
    """Bind this continuing command's exact selected source to its Code policy.

    The original source context remains entered. This prepares no graph node,
    semantic input, predecessor approval or selected-provider invocation.
    """
    command = inspection = source_result = selected = binding = issuer = None
    selected_host = staged = host = policy = root = None
    code = binding_type = None
    recognized = False
    try:
        if type(record) is not _InstalledWorkspaceContinuationRecord or record is not _INSTALLED_CONTINUATION_RECORD:
            raise TypeError("original installed continuation record required")
        if _require_installed_continuation_record(record.continuation) is not record:
            raise RuntimeError("original installed continuation record required")
        recognized = True
        from aware_code_retained_registry_policy_runtime import direct_host as code
        from aware_code_semantic_contract_runtime.retained_declaration_scope import (
            CodeSelectedPackageSourceBinding as binding_type,
        )

        if record.phase != "reading" or record.registry_policy is not None:
            raise RuntimeError("installed selected-source preparation unavailable")
        command, inspection = record.references[2:4]
        _require_live_direct_workspace_command(command)
        if type(inspection) is not WorkspaceDirectCLISourceInspection:
            raise RuntimeError("original installed command inspection required")
        if type(command.sources) is not _DirectWorkspaceDeclarationSources:
            raise SourceObservationUnavailable("installed_private_stage_declaration_source_unavailable")
        source_result = record.source_result
        if (
            type(source_result) is not tuple or len(source_result) != 3
            or source_result[0] is not command or source_result[1] is not inspection
        ):
            raise RuntimeError("installed original source-context result changed")
        selected = source_result[2]
        if type(selected) is not WorkspaceSelectedPackageSource:
            raise SourceObservationUnavailable("installed_private_stage_selected_source_unavailable")
        selected_host = record.selected_host
        if type(selected_host) is not DirectWorkspaceSelectedHost:
            raise RuntimeError("original installed selected host required")
        staged, host = selected_host.staged, selected_host.code_host
        if (
            type(staged) is not _DirectWorkspaceStagedCommandResources
            or type(host) is not code.DirectValidationHost
            or staged.command is not command
            or _STAGED_ASSEMBLIES.get(command.lifetime_runtime, (None,))[0] is not staged
            or _POLICY_HOSTS.get(host) is not staged
        ):
            raise RuntimeError("installed selected host differs from continuing command")
        # Full selected-source/currentness work stays outside parent exclusion.
        if command.lifetime_runtime._guard is not None:
            raise RuntimeError("installed selected-source preparation requires released guard")
        issuer = command.sources.declaration_scope_runtime
        binding = issuer.read_selected_package_source(selected)
        root = inspection.selected_root
        if (
            type(binding) is not binding_type
            or type(root) is not WorkspaceMaterializeSelectedRootV1
            or binding.expectation.scope_key != root.workspace_manifest_path
            or binding.expectation.module_id != root.module_id
            or binding.expectation.package_id != root.package_id
            or binding.expectation.source_identity_digest.to_wire()
            != root.source_identity_digest
        ):
            raise RuntimeError("installed selected source differs from command selection")
        issuer.validate_selected_package_source(
            selected, expectation=binding.expectation,
            binding_digest=binding.binding_digest,
        )
        policy = code.produce_registry_policy(host, selected)
        record.registry_policy = policy
        code.validate_admitted_registry_policy(host, policy)
        issuer.validate_selected_package_source(
            selected, expectation=binding.expectation,
            binding_digest=binding.binding_digest,
        )
        if (
            record.selected_host is not selected_host
            or record.source_result is not source_result
            or selected_host.staged is not staged or selected_host.code_host is not host
            or staged.command is not command or _POLICY_HOSTS.get(host) is not staged
            or record.registry_policy is not policy
        ):
            raise RuntimeError("installed source/host changed during policy preparation")
        _require_live_direct_workspace_command(command)
        record.pair_calls[1](record.references[0], record.references[1], proposal_wire=record.proposal_wire)
        if _require_installed_continuation_record(record.continuation) is not record:
            raise RuntimeError("installed continuation changed during policy preparation")
    except BaseException:
        if recognized:
            _hold_installed_continuation(record)
        raise
    finally:
        record = command = inspection = source_result = selected = binding = issuer = None
        selected_host = staged = host = policy = root = None
        code = binding_type = None


def _read_installed_workspace_private_stage(original_continuation):
    """Spend read without substituting diagnostic inputs for the missing join."""
    record = None
    try:
        record = _require_installed_continuation_record(original_continuation)
        if record.phase != "open":
            raise RuntimeError("installed private-stage read unavailable")
        _publish_installed_continuation_phase(record, "reading")
        record.pair_calls[1](record.references[0], record.references[1], proposal_wire=record.proposal_wire)
        _require_live_direct_workspace_command(record.references[2])
        _prepare_installed_workspace_private_stage_source(record)
        # Policy is original and selected; the same command's admitted graph
        # node and complete private input still need their genuine producer.
        # Retain the policy, but expose no partial tuple or ready state.
        raise SourceObservationUnavailable("installed_private_stage_node_input_unavailable")
    except BaseException:
        if record is not None:
            _hold_installed_continuation(record)
        raise
    finally:
        original_continuation = record = None


async def _finish_installed_workspace_materialize_command(original_continuation):
    """Accept no caller result; genuine coupled retention remains required."""
    record = None
    try:
        record = _require_installed_continuation_record(original_continuation)
        if record.phase != "ready":
            raise RuntimeError("installed command finish unavailable")
        _publish_installed_continuation_phase(record, "finishing")
        record.pair_calls[1](record.references[0], record.references[1], proposal_wire=record.proposal_wire)
        _require_live_direct_workspace_command(record.references[2])
        raise SourceObservationUnavailable("installed_coupled_code_meta_outcome_unavailable")
    except BaseException:
        if record is not None:
            _hold_installed_continuation(record)
        raise
    finally:
        original_continuation = record = None


def _require_installed_selected_owner_inlet() -> None:
    """No original installed child enrollment exists in this composition.

    Do not appoint a delivery, slot, marker or callback as that missing origin.
    Installation must separately govern the actual inlet before owner dispatch.
    This closed guard is never patched or bypassed by production/fixture flags.
    """
    raise SourceObservationUnavailable("installed_selected_owner_inlet_unavailable")


def _open_installed_selected_owner_attachment(
    original_staged_command, original_code_host, original_registry_policy,
    original_operation_use, *, original_child_delivery,
    public_contribution, private_contribution,
):
    try:
        _require_installed_selected_owner_inlet()
    finally:
        del original_staged_command, original_code_host, original_registry_policy
        del original_operation_use, original_child_delivery, public_contribution, private_contribution


def _attach_installed_selected_owner_lifetime(
    original_attachment, original_selection, original_lifetime_delivery,
) -> None:
    try:
        _require_installed_selected_owner_inlet()
    finally:
        del original_attachment, original_selection, original_lifetime_delivery


def _capture_installed_selected_owner_cancellation(
    original_attachment, original_registration, original_native_cancellation,
) -> None:
    try:
        _require_installed_selected_owner_inlet()
        _owner_lifetime._capture_owner_attachment_cancellation(
            original_attachment, original_registration, original_native_cancellation,
        )
    finally:
        del original_attachment, original_registration, original_native_cancellation


def _read_installed_selected_owner_cancellation(
    original_command, original_operation_use, original_registration,
):
    try:
        _require_installed_selected_owner_inlet()
    finally:
        del original_command, original_operation_use, original_registration


def _release_installed_selected_owner_cancellation(
    original_command, original_operation_use, original_registration,
) -> None:
    try:
        _require_installed_selected_owner_inlet()
    finally:
        del original_command, original_operation_use, original_registration


def _seal_installed_selected_owner_attachment(original_attachment) -> None:
    try:
        _require_installed_selected_owner_inlet()
        _owner_lifetime._seal_owner_attachment_storage(original_attachment)
    finally:
        del original_attachment


def _retire_command_node_sessions_after_fork() -> None:
    global _COMMAND_NODE_SESSIONS_LOCK
    _COMMAND_NODE_SESSIONS_LOCK = RLock()
    _COMMAND_NODE_SESSIONS.clear()


if hasattr(os, "register_at_fork"):
    os.register_at_fork(after_in_child=_retire_command_node_sessions_after_fork)


def _resource_references(value):
    return tuple(getattr(value, field.name) for field in fields(value))


def _same_references(left, right):
    return len(left) == len(right) and all(a is b for a, b in zip(left, right))


@dataclass(frozen=True, slots=True)
class _DirectWorkspaceSourceResources:
    """Original resource references, not an origin product or bootstrap token."""

    exclusion: WorkspaceSourceExclusion
    observation_runtime: WorkspaceSourceObservationRuntime
    observation: WorkspaceRetainedRootObservation
    membership_runtime: WorkspaceObservedPackageMembershipRuntime
    scope_runtime: Any
    scope_snapshot: Any
    scope_adapter: Any
    semantic_issuer: WorkspaceSourcePlanningSemanticIssuerRuntime
    source_admission_runtime: WorkspaceOwnerDefinedSourceAdmissionRuntime


@dataclass(frozen=True, slots=True)
class _DirectWorkspaceDeclarationSources:
    """The same command's original v3 source records, without a legacy root."""

    exclusion: WorkspaceSourceExclusion
    observation_runtime: WorkspaceSourceObservationRuntime
    declaration_observation: WorkspaceRetainedDeclarationObservation
    declaration_scope_runtime: WorkspaceDeclarationScopeRuntime
    declaration_scope: WorkspaceDeclarationScope
    expectation: CodeDeclarationScopeExpectation
    source_admission_runtime: WorkspaceV3OwnerDefinedSourceAdmissionRuntime


@contextmanager
def _compose_direct_workspace_declaration_sources(
    *,
    session: WorkspaceRepositoryObservationSession,
    store: WorkspaceRepositoryDeltaRetentionClient,
    workspace_manifest_path: str,
    exclusion: WorkspaceSourceExclusion,
) -> Iterator[_DirectWorkspaceDeclarationSources]:
    """Retain real repository declarations under the original command parent."""
    if type(exclusion) is not WorkspaceSourceExclusion:
        raise TypeError("original WorkspaceSourceExclusion required")
    exclusion.check_live()
    cleanup: list[Callable[[], None]] = []
    errors: list[BaseException] = []
    try:
        observation_runtime = WorkspaceSourceObservationRuntime(
            session=session, store=store, exclusion=exclusion
        )
        cleanup.append(observation_runtime.close)
        observation = observation_runtime.observe_declarations()
        issuer = WorkspaceDeclarationScopeRuntime(
            observation_runtime=observation_runtime
        )
        cleanup.append(issuer.close)
        source_admission_runtime = WorkspaceV3OwnerDefinedSourceAdmissionRuntime._assemble(
            issuer=issuer
        )
        cleanup.append(source_admission_runtime.close)
        # These opaque strings correlate one fixed command operation. Only the
        # original retained handles and parent exclusion authorize their use.
        expectation = CodeDeclarationScopeExpectation(
            store.repository_binding_ref,
            secrets.token_hex(16),
            os.getpid(),
            secrets.token_hex(16),
            secrets.token_hex(16),
        )
        scope = issuer.capture_declaration_scope(
            observation=observation,
            consumer_scope_key=workspace_manifest_path,
            expectation=expectation,
        )
        closure = issuer.read_declaration_scope(scope)
        issuer.validate_declaration_scope(
            scope, expectation=expectation,
            closure_digest=closure.closure_digest,
        )
        yield _DirectWorkspaceDeclarationSources(
            exclusion, observation_runtime, observation, issuer, scope, expectation,
            source_admission_runtime,
        )
    except BaseException as error:
        errors.append(error)
    finally:
        for close in reversed(cleanup):
            try:
                close()
            except BaseException as error:
                errors.append(error)
    if len(errors) == 1:
        raise errors[0]
    if errors:
        raise BaseExceptionGroup("Workspace declaration assembly/unwind failed", errors)


@contextmanager
def _compose_direct_workspace_sources(
    *,
    session: WorkspaceRepositoryObservationSession,
    store: WorkspaceRepositoryDeltaRetentionClient,
    workspace_manifest_path: str,
    qualified: bool = False,
    exclusion: WorkspaceSourceExclusion,
) -> Iterator[_DirectWorkspaceSourceResources]:
    """Fixed constructors under one original source exclusion.

    Session and store are borrowed. Only the four runtimes constructed here are
    closed, in reverse dependency order, using their original bound close methods.
    Every cleanup is attempted, including on cancellation or partial construction.
    The exclusion is borrowed from the original command composition and passed by
    identity to every source runtime. The eventual command owner must revoke its
    Code lifetime before this unwind.
    """
    if type(exclusion) is not WorkspaceSourceExclusion:
        raise TypeError("original WorkspaceSourceExclusion required")
    exclusion.check_live()
    cleanup: list[Callable[[], None]] = []
    errors: list[BaseException] = []
    try:
        observation_runtime = WorkspaceSourceObservationRuntime(
            session=session, store=store, exclusion=exclusion
        )
        cleanup.append(observation_runtime.close)
        observation = observation_runtime.observe(root_relative_path=".")
        membership_runtime = WorkspaceObservedPackageMembershipRuntime(
            observation_runtime=observation_runtime, exclusion=exclusion
        )
        cleanup.append(membership_runtime.close)
        scope_runtime = WorkspaceCompleteScopeObservationRuntime(
            observation_runtime=observation_runtime,
            membership_runtime=membership_runtime,
            exclusion=exclusion,
        )
        cleanup.append(scope_runtime.close)
        if qualified:
            dependency_runtime = WorkspaceDependencyScopeRuntime(
                observation_runtime=observation_runtime, scope_runtime=scope_runtime
            )
            cleanup.append(dependency_runtime.close)
            scope_snapshot = dependency_runtime.capture(
                observation=observation, consumer_scope_key=workspace_manifest_path
            )
            scope_runtime = dependency_runtime
            scope_adapter = WorkspaceCodeDependencyScopeAdapter(
                runtime=dependency_runtime
            )
            scope_adapter.read_preliminary_dependency_scope_projection(scope_snapshot)
        else:
            scope_snapshot = scope_runtime.capture_complete_scope(
                observation=observation, workspace_manifest_path=workspace_manifest_path
            )
            scope_adapter = WorkspaceCodeScopeAdapter(scope_runtime=scope_runtime)
            scope_adapter.validate_complete_scope_projection(scope_snapshot)
        semantic_issuer = WorkspaceSourcePlanningSemanticIssuerRuntime._assemble(
            observation_runtime=observation_runtime,
            membership_runtime=membership_runtime,
            observation=observation,
        )
        cleanup.append(semantic_issuer.close)
        source_admission_runtime = WorkspaceOwnerDefinedSourceAdmissionRuntime._assemble(
            membership_runtime=membership_runtime,
            semantic_issuer=semantic_issuer,
        )
        cleanup.append(source_admission_runtime.close)
        if qualified:
            semantic_issuer._bind_original_dependency_source(
                scope_runtime, scope_snapshot
            )
        yield _DirectWorkspaceSourceResources(
            exclusion=exclusion,
            observation_runtime=observation_runtime,
            observation=observation,
            membership_runtime=membership_runtime,
            scope_runtime=scope_runtime,
            scope_snapshot=scope_snapshot,
            scope_adapter=scope_adapter,
            semantic_issuer=semantic_issuer,
            source_admission_runtime=source_admission_runtime,
        )
    except BaseException as error:
        errors.append(error)
    finally:
        for close in reversed(cleanup):
            try:
                close()
            except BaseException as error:
                errors.append(error)
    if len(errors) == 1:
        raise errors[0]
    if errors:
        raise BaseExceptionGroup("Workspace source assembly/unwind failed", errors)


@dataclass(frozen=True, slots=True)
class _DirectWorkspaceCommandResources:
    """Original parent and source resources; not Code bootstrap admission."""

    lifetime_runtime: WorkspaceCommandLifetimeRuntime
    invocation_parent: WorkspaceDirectInvocationParent
    sources: _DirectWorkspaceSourceResources | _DirectWorkspaceDeclarationSources
    catalog_host: WorkspaceSemanticCatalogHost
    # Strong command custody, not installation/enrollment. One spent position
    # survives interrupted publication; no global registry owns this slot.
    owner_attachment_position: list[object] = field(
        default_factory=lambda: [None], compare=False, repr=False
    )


@contextmanager
def _compose_direct_workspace_command_resources(
    *,
    session: WorkspaceRepositoryObservationSession,
    store: WorkspaceRepositoryDeltaRetentionClient,
    workspace_manifest_path: str,
    qualified: bool = False,
    source_rail: str = "existing",
) -> Iterator[_DirectWorkspaceCommandResources]:
    """Fixed ownership, with no runtime/factory/cleanup injection entrance.

    Before source construction succeeds no command lifetime is bound or exposed.
    After yield, revoke the original parent before source-resource teardown. The
    inner source assembly retains ownership of its own partial-failure unwind.
    Session/store remain borrowed. Code runtimes/registrations are not constructed
    here; their eventual fixed assembly must retain its own lawful cleanup.
    """
    if type(source_rail) is not str or source_rail not in (
        "existing", "declaration_v3"
    ) or (
        source_rail == "declaration_v3" and qualified
    ):
        raise ValueError("exact direct command source rail required")
    lifetime = WorkspaceCommandLifetimeRuntime()
    close_parent = lifetime.close
    parent_close_attempted = False
    close_host = None
    assembly_errors: list[BaseException] = []
    try:
        parent = lifetime._retain_direct_invocation_parent()
        host = _assemble_command_catalog_host(
            owner=lifetime,
            parent=parent,
            invocation=DirectInvocationExpectation(
                lifetime.invocation_identity, lifetime.epoch_identity, os.getpid()
            ),
        )
        close_host = host.close
        exclusion = WorkspaceSourceExclusion(
            runtime=lifetime,
            parent=parent,
            expected=DirectInvocationExpectation(
                lifetime.invocation_identity, lifetime.epoch_identity, os.getpid()
            ),
        )
        source_context = (
            _compose_direct_workspace_declaration_sources(
                session=session,
                store=store,
                workspace_manifest_path=workspace_manifest_path,
                exclusion=exclusion,
            )
            if source_rail == "declaration_v3"
            else _compose_direct_workspace_sources(
                session=session,
                store=store,
                workspace_manifest_path=workspace_manifest_path,
                qualified=qualified,
                exclusion=exclusion,
            )
        )
        with source_context as sources:
            errors: list[BaseException] = []
            try:
                resources = _DirectWorkspaceCommandResources(
                    lifetime, parent, sources, host
                )
                _COMMAND_ASSEMBLIES[lifetime] = (
                    resources,
                    _resource_references(resources),
                    _resource_references(sources),
                )
                yield resources
            except BaseException as error:
                errors.append(error)
            _COMMAND_ASSEMBLIES.pop(lifetime, None)
            if type(sources) is _DirectWorkspaceDeclarationSources:
                try:
                    sources.declaration_scope_runtime.release_dependency_targets()
                except BaseException as error:
                    errors.append(error)
            parent_close_attempted = True
            try:
                close_parent()
            except BaseException as error:
                errors.append(error)
            try:
                close_host()
            except BaseException as error:
                errors.append(error)
            if len(errors) == 1:
                raise errors[0]
            if errors:
                raise BaseExceptionGroup(
                    "Workspace command body/revocation failed", errors
                )
    except BaseException as error:
        assembly_errors.append(error)
    if not parent_close_attempted:
        try:
            close_parent()
        except BaseException as error:
            assembly_errors.append(error)
        if close_host is not None:
            try:
                close_host()
            except BaseException as error:
                assembly_errors.append(error)
    if len(assembly_errors) == 1:
        raise assembly_errors[0]
    if assembly_errors:
        raise BaseExceptionGroup(
            "Workspace command assembly/unwind failed", assembly_errors
        )


@dataclass(frozen=True, slots=True)
class WorkspaceDirectCLISourceInspection:
    """Detached correspondence only; the original command closes on return."""

    attempt_ref: str
    proposal_digest: str
    declaration_scope_digest: ContentDigest
    operation_receipt: WorkspaceMaterializeHostOperationReceiptV1
    selected_root: WorkspaceMaterializeSelectedRootV1 | None = None
    selected_timing_ns: int = 0


@contextmanager
def _compose_direct_workspace_command_source(
    *,
    session: WorkspaceRepositoryObservationSession,
    store: WorkspaceRepositoryDeltaRetentionClient,
    proposal: WorkspaceMaterializeCommandProposalV2 | WorkspaceMaterializeCommandProposalV3,
) -> Iterator[
    tuple[
        _DirectWorkspaceCommandResources,
        WorkspaceDirectCLISourceInspection,
        WorkspaceSelectedPackageSource | None,
    ]
]:
    """Keep the original command and exact selected source live for its consumer.

    The tuple carries original resources, not a new admission. A detached
    inspection cannot reopen the context. Owner execution and source checks
    must finish before these borrowed handles are retired.
    """
    if type(proposal) not in (WorkspaceMaterializeCommandProposalV2, WorkspaceMaterializeCommandProposalV3):
        raise TypeError("exact direct command proposal required")
    proposal.__post_init__()
    with _compose_direct_workspace_command_resources(
        session=session,
        store=store,
        workspace_manifest_path=proposal.workspace_manifest_name,
        source_rail="declaration_v3",
    ) as command:
        expected_parent = DirectInvocationExpectation(
            command.lifetime_runtime.invocation_identity,
            command.lifetime_runtime.epoch_identity,
            os.getpid(),
        )
        command.lifetime_runtime.validate_direct_invocation_parent(
            command.invocation_parent, expected=expected_parent
        )
        sources = command.sources
        if type(sources) is not _DirectWorkspaceDeclarationSources:
            raise TypeError("original declaration source required")
        issuer = sources.declaration_scope_runtime
        closure = issuer.read_declaration_scope(sources.declaration_scope)
        issuer.validate_declaration_scope(
            sources.declaration_scope,
            expectation=sources.expectation,
            closure_digest=closure.closure_digest,
        )
        with ExitStack() as selected_stack:
            selected = None
            binding = None
            selected_root = None
            selected_started_ns = None
            if type(proposal) is WorkspaceMaterializeCommandProposalV3:
                selected_started_ns = time.perf_counter_ns()
                workspace_handle, module_id, package_id = proposal.package_address
                root = issuer.inspect_exact_materialization_root(
                    sources.declaration_scope,
                    workspace_handle=workspace_handle,
                    module_id=module_id,
                    package_id=package_id,
                )
                if root.workspace_manifest_path != proposal.workspace_manifest_name:
                    raise SourceObservationUnavailable("exact_materialization_workspace_differs")
                selected = selected_stack.enter_context(
                    _compose_direct_workspace_selected_package_source(
                        command,
                        workspace_manifest_path=root.workspace_manifest_path,
                        module_id=root.module_id,
                        package_id=root.package_id,
                    )
                )
                binding = issuer.read_selected_package_source(selected)
                if (
                    binding.expectation.scope_key != root.workspace_manifest_path
                    or binding.expectation.module_id != root.module_id
                    or binding.expectation.package_id != root.package_id
                ):
                    raise SourceObservationUnavailable("exact_materialization_source_differs")
                issuer.validate_selected_package_source(
                    selected,
                    expectation=binding.expectation,
                    binding_digest=binding.binding_digest,
                )
                selected_root = WorkspaceMaterializeSelectedRootV1.create(
                    workspace_handle=workspace_handle,
                    workspace_manifest_path=root.workspace_manifest_path,
                    module_id=root.module_id,
                    package_id=root.package_id,
                    semantic_package_name=root.semantic_package_name,
                    semantic_version=root.semantic_version,
                    source_identity_digest=binding.expectation.source_identity_digest.to_wire(),
                )
            # The exact selected handle remains live through receipt issuance.
            # The detached result grants no later source, Code or graph use.
            proposal.__post_init__()
            command.lifetime_runtime.validate_direct_invocation_parent(
                command.invocation_parent, expected=expected_parent
            )
            operation_ref, parent_ref, epoch_ref = (
                command.lifetime_runtime.issue_direct_source_operation_coordinates(
                    command.invocation_parent, expected=expected_parent
                )
            )
            operation_receipt = WorkspaceMaterializeHostOperationReceiptV1.create(
                operation_ref=operation_ref,
                parent_ref=parent_ref,
                epoch_ref=epoch_ref,
                attempt_ref=proposal.attempt_ref,
                proposal_digest=proposal.proposal_digest,
                declaration_scope_digest=closure.closure_digest.to_wire(),
            )
            if type(proposal) is WorkspaceMaterializeCommandProposalV3:
                if issuer.inspect_exact_materialization_root(
                    sources.declaration_scope,
                    workspace_handle=workspace_handle,
                    module_id=module_id,
                    package_id=package_id,
                ) != root:
                    raise SourceObservationUnavailable("exact_materialization_root_changed")
                issuer.validate_selected_package_source(
                    selected,
                    expectation=binding.expectation,
                    binding_digest=binding.binding_digest,
                )
                selected_timing_ns = time.perf_counter_ns() - selected_started_ns
            else:
                selected_timing_ns = 0
            issuer.validate_declaration_scope(
                sources.declaration_scope,
                expectation=sources.expectation,
                closure_digest=closure.closure_digest,
            )
            command.lifetime_runtime.validate_direct_invocation_parent(
                command.invocation_parent, expected=expected_parent
            )
            inspection = WorkspaceDirectCLISourceInspection(
                attempt_ref=proposal.attempt_ref,
                proposal_digest=proposal.proposal_digest,
                declaration_scope_digest=closure.closure_digest,
                operation_receipt=operation_receipt,
                selected_root=selected_root,
                selected_timing_ns=selected_timing_ns,
            )
            yield command, inspection, selected
            _require_live_direct_workspace_command(command)
            issuer.validate_declaration_scope(
                sources.declaration_scope,
                expectation=sources.expectation,
                closure_digest=closure.closure_digest,
            )
            if selected is not None:
                if binding is None:
                    raise RuntimeError("original selected source binding unavailable")
                issuer.validate_selected_package_source(
                    selected, expectation=binding.expectation,
                    binding_digest=binding.binding_digest,
                )
            command.lifetime_runtime.validate_direct_invocation_parent(
                command.invocation_parent, expected=expected_parent
            )


def admit_direct_workspace_command_source(
    *, session: WorkspaceRepositoryObservationSession,
    store: WorkspaceRepositoryDeltaRetentionClient,
    proposal: WorkspaceMaterializeCommandProposalV2 | WorkspaceMaterializeCommandProposalV3,
) -> WorkspaceDirectCLISourceInspection:
    """Return detached source evidence; original resources close before return."""
    with _compose_direct_workspace_command_source(
        session=session, store=store, proposal=proposal
    ) as (_command, inspection, _selected):
        return inspection


def _require_live_direct_workspace_command(command: _DirectWorkspaceCommandResources) -> None:
    if type(command) is not _DirectWorkspaceCommandResources:
        raise TypeError("original Workspace command resources required")
    record = _COMMAND_ASSEMBLIES.get(command.lifetime_runtime)
    if (
        record is None or record[0] is not command
        or not _same_references(record[1], _resource_references(command))
        or not _same_references(record[2], _resource_references(command.sources))
    ):
        raise RuntimeError("original Workspace command unavailable")
    command.sources.exclusion.check_live()


class WorkspaceDirectCommandRootUnavailable(ValueError):
    """The direct CLI did not name an existing absolute repository root."""


@asynccontextmanager
async def _compose_direct_workspace_cli_source(
    *, proposal: WorkspaceMaterializeCommandProposalV2 | WorkspaceMaterializeCommandProposalV3,
) -> AsyncIterator[
    tuple[
        _DirectWorkspaceCommandResources,
        WorkspaceDirectCLISourceInspection,
        WorkspaceSelectedPackageSource | None,
    ]
]:
    """Mount one process-local observer and original Workspace command parent.

    State placement is fixed by the direct Workspace runtime, not a proposal
    field or a Local Development service. This entrance only proves retained
    declarations; later Code catalog and graph admission remain separate.
    """
    if type(proposal) not in (WorkspaceMaterializeCommandProposalV2, WorkspaceMaterializeCommandProposalV3):
        raise TypeError("exact direct command proposal required")
    proposal.__post_init__()
    repository_root = proposal.participant_checkout_root
    if repository_root is None or not Path(repository_root).is_absolute():
        raise WorkspaceDirectCommandRootUnavailable("absolute repository root required")
    try:
        binding = WorkspaceRepositoryBinding(Path(repository_root))
    except (OSError, ValueError) as error:
        raise WorkspaceDirectCommandRootUnavailable(
            "repository root unavailable"
        ) from error
    # Cheap refusal before starting a repository-wide observer. The manifest
    # check grants no authority; retained Workspace admission reads its bytes.
    if not (binding.root_path / "aware.repo.toml").is_file():
        raise WorkspaceDirectCommandRootUnavailable(
            "repository manifest unavailable"
        )
    state_home = os.environ.get("XDG_STATE_HOME")
    state_root = (
        Path(state_home).expanduser()
        if state_home and Path(state_home).is_absolute()
        else Path.home() / ".local" / "state"
    ) / "aware" / "workspace-direct"
    cache_root = state_root / hashlib.sha256(
        str(binding.root_path).encode("utf-8")
    ).hexdigest()
    session = WorkspaceRepositoryObservationSession(
        binding=binding,
        provider=FileSystemIndexObservationProvider(
            binding=binding, cache_dir=cache_root
        ),
    )
    await session.start(background=False)
    try:
        store = WorkspaceRepositoryDeltaRetentionFactory.filesystem(
            state_root=cache_root,
        ).allocate_delta_retention()
        store.initialize_delta_retention(
            repository_binding_ref=binding.binding_key,
            body_capacity=4096,
            maximum_bytes=512 * 1024 * 1024,
        )
        with _compose_direct_workspace_command_source(
            session=session,
            store=store,
            proposal=proposal,
        ) as resources:
            yield resources
    finally:
        await session.stop()


async def admit_direct_workspace_cli_source(
    *, proposal: WorkspaceMaterializeCommandProposalV2 | WorkspaceMaterializeCommandProposalV3,
) -> WorkspaceDirectCLISourceInspection:
    """Preserve the source-only CLI receipt on the shared live composition."""
    async with _compose_direct_workspace_cli_source(proposal=proposal) as (
        _command, inspection, _selected,
    ):
        return inspection


@contextmanager
def _compose_direct_workspace_selected_package_source(
    command: _DirectWorkspaceCommandResources,
    *,
    workspace_manifest_path: str,
    module_id: str,
    package_id: str,
) -> Iterator[WorkspaceSelectedPackageSource]:
    """Bind one selected occurrence to this command's original v3 scope."""
    if type(command) is not _DirectWorkspaceCommandResources:
        raise TypeError("original Workspace command resources required")
    record = _COMMAND_ASSEMBLIES.get(command.lifetime_runtime)
    sources = command.sources
    if (
        record is None
        or record[0] is not command
        or not _same_references(record[1], _resource_references(command))
        or type(sources) is not _DirectWorkspaceDeclarationSources
        or not _same_references(record[2], _resource_references(sources))
        or sources.exclusion._runtime is not command.lifetime_runtime
        or sources.exclusion._parent is not command.invocation_parent
    ):
        raise RuntimeError("original v3 command assembly unavailable")
    sources.exclusion.check_live()
    selected = sources.observation_runtime.observe_selected_package(
        declaration=sources.declaration_observation,
        workspace_manifest_path=workspace_manifest_path,
        module_id=module_id,
        package_id=package_id,
    )
    handle = None
    errors: list[BaseException] = []
    try:
        handle = sources.declaration_scope_runtime.bind_selected_package_source(
            declaration=sources.declaration_scope, selected=selected
        )
        yield handle
    except BaseException as error:
        errors.append(error)
    finally:
        if handle is not None:
            try:
                sources.declaration_scope_runtime.release_selected_package_source(
                    handle
                )
            except BaseException as error:
                errors.append(error)
        try:
            sources.observation_runtime.release_selected_package(selected)
        except BaseException as error:
            errors.append(error)
    if len(errors) == 1:
        raise errors[0]
    if errors:
        raise BaseExceptionGroup("Workspace selected source/unwind failed", errors)


@contextmanager
def _compose_direct_workspace_selected_materialization_roots(
    command: _DirectWorkspaceCommandResources,
    *,
    selection: WorkspaceMaterializationSelectionProposal,
) -> Iterator[
    tuple[
        tuple[WorkspaceDeclaredMaterializationRoot, WorkspaceSelectedPackageSource],
        ...,
    ]
]:
    """Bind every declared root through this command's original source issuer."""
    if type(command) is not _DirectWorkspaceCommandResources:
        raise TypeError("original Workspace command resources required")
    sources = command.sources
    record = _COMMAND_ASSEMBLIES.get(command.lifetime_runtime)
    if (
        record is None
        or record[0] is not command
        or not _same_references(record[1], _resource_references(command))
        or type(sources) is not _DirectWorkspaceDeclarationSources
        or not _same_references(record[2], _resource_references(sources))
        or sources.exclusion._runtime is not command.lifetime_runtime
        or sources.exclusion._parent is not command.invocation_parent
    ):
        raise RuntimeError("original v3 command assembly unavailable")
    roots = sources.declaration_scope_runtime.inspect_materialization_roots(
        sources.declaration_scope, selection=selection
    )
    with ExitStack() as stack:
        bound = tuple(
            (
                root,
                stack.enter_context(
                    _compose_direct_workspace_selected_package_source(
                        command,
                        workspace_manifest_path=root.workspace_manifest_path,
                        module_id=root.module_id,
                        package_id=root.package_id,
                    )
                ),
            )
            for root in roots
        )
        if sources.declaration_scope_runtime.inspect_materialization_roots(
            sources.declaration_scope, selection=selection
        ) != roots:
            raise RuntimeError("materialization root selection changed")
        yield bound


def _read_direct_workspace_selected_participants(
    command: _DirectWorkspaceCommandResources,
    selected: WorkspaceSelectedPackageSource,
):
    """Bind Code's selected view to this original live command and source."""
    if type(command) is not _DirectWorkspaceCommandResources:
        raise TypeError("original Workspace command resources required")
    sources = command.sources
    record = _COMMAND_ASSEMBLIES.get(command.lifetime_runtime)
    if (
        type(sources) is not _DirectWorkspaceDeclarationSources
        or record is None
        or record[0] is not command
        or not _same_references(record[1], _resource_references(command))
        or not _same_references(record[2], _resource_references(sources))
        or sources.exclusion._runtime is not command.lifetime_runtime
        or sources.exclusion._parent is not command.invocation_parent
    ):
        raise RuntimeError("original v3 command assembly unavailable")
    sources.exclusion.check_live()
    issuer = sources.declaration_scope_runtime
    view = issuer.read_selected_participant_view(sources.declaration_scope, selected)
    issuer.validate_selected_participant_view(
        sources.declaration_scope, selected, view=view
    )
    sources.exclusion.check_live()
    if _COMMAND_ASSEMBLIES.get(command.lifetime_runtime) is not record:
        raise RuntimeError("original v3 command retired during selection")
    return view


def _resolve_direct_workspace_selected_provider_keys(
    command: _DirectWorkspaceCommandResources,
    *,
    selection: WorkspaceMaterializationSelectionProposal,
) -> tuple[tuple[WorkspaceDeclaredMaterializationRoot, str], ...]:
    """Resolve selected providers from this command's retained profile closure.

    The returned keys are installation requests, not provider or source
    authority. The original declaration issuer is checked on both sides of
    Code's neutral eligibility calculation.
    """
    from aware_code_retained_registry_policy_runtime.declaration_eligibility import (
        calculate_declaration_eligibility,
    )

    if type(command) is not _DirectWorkspaceCommandResources:
        raise TypeError("original Workspace command resources required")
    sources = command.sources
    record = _COMMAND_ASSEMBLIES.get(command.lifetime_runtime)
    if (
        type(sources) is not _DirectWorkspaceDeclarationSources
        or record is None
        or record[0] is not command
        or not _same_references(record[1], _resource_references(command))
        or not _same_references(record[2], _resource_references(sources))
    ):
        raise RuntimeError("original v3 command assembly unavailable")
    issuer = sources.declaration_scope_runtime
    roots = issuer.inspect_materialization_roots(
        sources.declaration_scope, selection=selection
    )
    closure = issuer.read_declaration_scope(sources.declaration_scope)
    issuer.validate_declaration_scope(
        sources.declaration_scope,
        expectation=sources.expectation,
        closure_digest=closure.closure_digest,
    )
    eligibility = calculate_declaration_eligibility(closure)
    if eligibility.closure_digest != closure.closure_digest:
        raise RuntimeError("selected provider closure changed")
    by_occurrence = {row.occurrence_key: row for row in eligibility.packages}
    resolved = []
    for root in roots:
        row = by_occurrence.get(
            (root.workspace_manifest_path, root.module_id, root.package_id)
        )
        if row is None:
            raise RuntimeError("selected provider declaration unavailable")
        resolved.append((root, row.provider_key))
    if issuer.inspect_materialization_roots(
        sources.declaration_scope, selection=selection
    ) != roots:
        raise RuntimeError("selected provider roots changed")
    issuer.validate_declaration_scope(
        sources.declaration_scope,
        expectation=sources.expectation,
        closure_digest=closure.closure_digest,
    )
    return tuple(resolved)


def _resolve_direct_workspace_exact_provider_key(
    command: _DirectWorkspaceCommandResources,
    selected: WorkspaceSelectedPackageSource,
) -> str:
    """Derive an installation request from the authenticated exact participant view.

    Complete observed declarations remain retained. Code interprets profile
    applicability; this key grants no factory, registration or execution.
    """
    from aware_code_retained_registry_policy_runtime.declaration_eligibility import (
        calculate_declaration_eligibility,
    )

    _require_live_direct_workspace_command(command)
    sources = command.sources
    if type(sources) is not _DirectWorkspaceDeclarationSources:
        raise TypeError("original declaration source required")
    issuer = sources.declaration_scope_runtime
    binding = issuer.read_selected_package_source(selected)
    view = _read_direct_workspace_selected_participants(command, selected)
    closure = issuer.read_declaration_scope(sources.declaration_scope)
    eligibility = calculate_declaration_eligibility(closure, selected_view=view)
    key = (
        binding.expectation.scope_key, binding.expectation.module_id,
        binding.expectation.package_id,
    )
    matches = tuple(row for row in eligibility.packages if row.occurrence_key == key)
    if eligibility.closure_digest != closure.closure_digest or len(matches) != 1:
        raise RuntimeError("exact selected provider declaration unavailable")
    issuer.validate_selected_participant_view(
        sources.declaration_scope, selected, view=view
    )
    issuer.validate_selected_package_source(
        selected, expectation=binding.expectation, binding_digest=binding.binding_digest
    )
    _require_live_direct_workspace_command(command)
    return matches[0].provider_key


def _validate_direct_workspace_root_plan_closure(
    command: _DirectWorkspaceCommandResources,
    *,
    selection: WorkspaceMaterializationSelectionProposal,
    bound_roots: tuple[
        tuple[WorkspaceDeclaredMaterializationRoot, WorkspaceSelectedPackageSource],
        ...,
    ],
    root_plans: tuple[object, ...],
) -> None:
    """Bind caller intent to original v3 roots; Code still admits its meaning."""
    from .materialization_graph_planner import WorkspaceSemanticRootCodePlan

    if type(command) is not _DirectWorkspaceCommandResources:
        raise TypeError("original Workspace command resources required")
    if type(selection) is not WorkspaceMaterializationSelectionProposal:
        raise TypeError("exact Workspace root selection required")
    if type(bound_roots) is not tuple or type(root_plans) is not tuple:
        raise TypeError("exact selected roots and Code plan tuples required")
    selection.__post_init__()
    sources = command.sources
    owner = command.lifetime_runtime
    record = _COMMAND_ASSEMBLIES.get(owner)
    if (
        type(sources) is not _DirectWorkspaceDeclarationSources
        or record is None
        or record[0] is not command
        or not _same_references(record[1], _resource_references(command))
        or not _same_references(record[2], _resource_references(sources))
        or sources.exclusion._runtime is not owner
        or sources.exclusion._parent is not command.invocation_parent
    ):
        raise RuntimeError("original v3 command root selection unavailable")
    sources.exclusion.check_live()
    issuer = sources.declaration_scope_runtime
    original = issuer.inspect_materialization_roots(
        sources.declaration_scope, selection=selection
    )
    if len(bound_roots) != len(original):
        raise RuntimeError("root plan selection differs from original roots")
    packages = []
    observed = []
    for expected_root, pair in zip(original, bound_roots, strict=True):
        if (
            type(pair) is not tuple
            or len(pair) != 2
            or type(pair[0]) is not WorkspaceDeclaredMaterializationRoot
            or type(pair[1]) is not WorkspaceSelectedPackageSource
            or pair[0] != expected_root
        ):
            raise RuntimeError("root plan selection differs from original roots")
        root, selected = pair
        evidence = issuer.inspect_selected_package_evidence(selected)
        context, _ = issuer.inspect_inputs(selected)
        if (
            evidence.workspace_manifest_path != root.workspace_manifest_path
            or evidence.module_id != root.module_id
            or evidence.package_id != root.package_id
            or context.package.package_kind != evidence.package_kind
            or context.semantic_version != root.semantic_version
            or context.package.package_ref
            != f"package:{root.semantic_package_name}@{root.semantic_version}"
        ):
            raise RuntimeError("root plan package differs from original source")
        packages.append(context.package.package_ref)
        observed.append((selected, context))
    expected_refs = tuple(sorted(packages, key=str.encode))
    if len(set(expected_refs)) != len(expected_refs):
        raise RuntimeError("root plan package identity is ambiguous")
    for plan in root_plans:
        if type(plan) is not WorkspaceSemanticRootCodePlan:
            raise TypeError("exact Code root plan required")
        plan.__post_init__()
    if tuple(plan.package_ref for plan in root_plans) != expected_refs:
        raise RuntimeError("root plans differ from original selected packages")
    if (
        issuer.inspect_materialization_roots(
            sources.declaration_scope, selection=selection
        )
        != original
        or _COMMAND_ASSEMBLIES.get(owner) is not record
        or not _same_references(record[1], _resource_references(command))
        or not _same_references(record[2], _resource_references(sources))
        or any(
            issuer.inspect_inputs(selected)[0] != context
            for selected, context in observed
        )
    ):
        raise RuntimeError("original root selection changed")
    sources.exclusion.check_live()


def _compose_direct_workspace_selected_root_code_plans(
    staged: _DirectWorkspaceStagedCommandResources,
    code_host: object,
    *,
    epoch: object,
    expected_epoch: object,
    selection: WorkspaceMaterializationSelectionProposal,
    bound_roots: tuple[
        tuple[WorkspaceDeclaredMaterializationRoot, WorkspaceSelectedPackageSource],
        ...,
    ],
    selected_product_roots: tuple[tuple[str, str, object], ...] = (),
):
    """Bind Code-selected meaning to this command's original v3 root sources."""
    from aware_code_retained_registry_policy_runtime import direct_host
    from aware_code_retained_registry_policy_runtime.selected_root_intent import (
        derive_selected_product_root_intent,
        derive_selected_root_intent,
    )

    from .materialization_graph_planner import WorkspaceSemanticRootCodePlan

    if type(staged) is not _DirectWorkspaceStagedCommandResources:
        raise TypeError("original staged Workspace command required")
    command = staged.command
    if type(command) is not _DirectWorkspaceCommandResources:
        raise RuntimeError("original Workspace command required")
    owner = command.lifetime_runtime
    command_record = _COMMAND_ASSEMBLIES.get(owner)
    staged_record = _STAGED_ASSEMBLIES.get(owner)
    if (
        command_record is None
        or staged_record is None
        or command_record[0] is not command
        or staged_record[0] is not staged
        or not _same_references(command_record[1], _resource_references(command))
        or not _same_references(command_record[2], _resource_references(command.sources))
        or not _same_references(staged_record[1], _resource_references(staged))
        or _POLICY_HOSTS.get(code_host) is not staged
        or type(command.sources) is not _DirectWorkspaceDeclarationSources
    ):
        raise RuntimeError("original v3 Code/Workspace root host unavailable")
    command.sources.exclusion.check_live()
    issuer = command.sources.declaration_scope_runtime
    original = issuer.inspect_materialization_roots(
        command.sources.declaration_scope, selection=selection
    )
    if type(bound_roots) is not tuple or len(bound_roots) != len(original):
        raise RuntimeError("selected root set differs from original declaration")
    if type(selected_product_roots) is not tuple:
        raise TypeError("selected product roots must be an exact tuple")
    products = {}
    for item in selected_product_roots:
        if (
            type(item) is not tuple
            or len(item) != 3
            or type(item[0]) is not str
            or not item[0]
            or type(item[1]) is not str
            or not item[1]
            or not any(
                retained.registration is item[2]
                for retained in staged.product_runtime_bindings
            )
            or item[0] in products
        ):
            raise RuntimeError("original selected graph product root required")
        products[item[0]] = (item[1], item[2])
    if tuple(products) != tuple(sorted(products, key=str.encode)):
        raise RuntimeError("selected graph product roots must be ordered")
    for expected, pair in zip(original, bound_roots, strict=True):
        if (
            type(pair) is not tuple
            or len(pair) != 2
            or type(pair[0]) is not WorkspaceDeclaredMaterializationRoot
            or type(pair[1]) is not WorkspaceSelectedPackageSource
            or pair[0] != expected
        ):
            raise RuntimeError("selected root set differs from original declaration")
    joint = command.catalog_host
    joint.validate_current_catalog_epoch(epoch, expected=expected_epoch)
    pair = joint._result
    if pair is None:
        raise RuntimeError("current Workspace catalog pair unavailable")
    plans = []
    for root, selected in bound_roots:
        evidence = issuer.inspect_selected_package_evidence(selected)
        context, _ = issuer.inspect_inputs(selected)
        if (
            evidence.workspace_manifest_path != root.workspace_manifest_path
            or evidence.module_id != root.module_id
            or evidence.package_id != root.package_id
            or context.package.package_kind != evidence.package_kind
            or context.semantic_version != root.semantic_version
            or context.package.package_ref
            != f"package:{root.semantic_package_name}@{root.semantic_version}"
        ):
            raise RuntimeError("selected root differs from original source")
        policy = direct_host.produce_registry_policy(code_host, selected)
        selected_product = products.pop(context.package.package_ref, None)
        if selected_product is None:
            intent, product = derive_selected_root_intent(code_host, policy)
            provider_keys = ()
        else:
            role, registration = selected_product
            intent, product, provider_key = derive_selected_product_root_intent(
                code_host, policy, requested_role=role,
                selected_product_registration=registration,
            )
            provider_keys = (provider_key,)
        entry = pair.workspace.package(context.package.package_ref)
        if (
            entry.package != context.package
            or entry.owned_semantic_root_refs != intent.requested_semantic_root_refs
            or not entry.participation_policy.admits(intent)
        ):
            raise RuntimeError("Code root intent differs from Workspace participation")
        plans.append(
            WorkspaceSemanticRootCodePlan.create(
                package_ref=context.package.package_ref,
                code_intent=intent,
                required_result_products=(product,),
                required_semantic_provider_keys=provider_keys,
            )
        )
    if products:
        raise RuntimeError("selected graph product differs from original roots")
    result = tuple(sorted(plans, key=lambda plan: plan.package_ref.encode()))
    _validate_direct_workspace_root_plan_closure(
        command, selection=selection, bound_roots=bound_roots, root_plans=result
    )
    if joint._result is not pair:
        raise RuntimeError("Workspace catalog pair changed during root derivation")
    joint.validate_current_catalog_epoch(epoch, expected=expected_epoch)
    return result


def _derive_direct_workspace_graph_selection(
    command: _DirectWorkspaceCommandResources,
    *,
    selection: WorkspaceMaterializationSelectionProposal,
    bound_roots: tuple[
        tuple[WorkspaceDeclaredMaterializationRoot, WorkspaceSelectedPackageSource],
        ...,
    ],
    root_plans: tuple,
) -> WorkspaceMaterializationSelectionProposal:
    """Resolve the original four-scope selection to exact graph package refs."""
    from .materialization_selection import (
        WorkspaceMaterializationRootSelector,
        _internal_canonical_bytes,
    )

    _validate_direct_workspace_root_plan_closure(
        command, selection=selection, bound_roots=bound_roots, root_plans=root_plans
    )
    selectors = tuple(
        WorkspaceMaterializationRootSelector.create(
            selector_kind="package", selector_ref=plan.package_ref
        )
        for plan in root_plans
    )
    return WorkspaceMaterializationSelectionProposal.create(
        selectors=tuple(
            sorted(
                selectors,
                key=lambda selector: _internal_canonical_bytes(selector.to_wire()),
            )
        )
    )


def _validate_direct_workspace_graph_source_closure(
    *,
    bound_roots: tuple[
        tuple[WorkspaceDeclaredMaterializationRoot, WorkspaceSelectedPackageSource],
        ...,
    ],
    selected_sources: tuple[WorkspaceSelectedPackageSource, ...],
    source_correspondences: tuple[object, ...],
) -> None:
    """Require the same original selected handles throughout v3 graph planning."""
    from .source_admission_catalog import WorkspaceV3GraphSourceCorrespondence

    if (
        type(bound_roots) is not tuple
        or type(selected_sources) is not tuple
        or not selected_sources
        or type(source_correspondences) is not tuple
        or len(source_correspondences) != len(selected_sources)
    ):
        raise RuntimeError("complete original graph source closure required")
    if any(
        type(source) is not WorkspaceSelectedPackageSource
        for source in selected_sources
    ):
        raise TypeError("original v3 selected source required")
    if any(
        any(source is prior for prior in selected_sources[:index])
        for index, source in enumerate(selected_sources)
    ):
        raise RuntimeError("duplicate original graph selected source")
    if any(
        sum(source is root_source for source in selected_sources) != 1
        for _, root_source in bound_roots
    ):
        raise RuntimeError("graph selected sources omit an original root")
    for item in source_correspondences:
        if type(item) is not WorkspaceV3GraphSourceCorrespondence:
            raise TypeError("original v3 graph source correspondence required")
    if any(
        sum(
            item.original_selected_source() is source
            for item in source_correspondences
        )
        != 1
        for source in selected_sources
    ):
        raise RuntimeError("graph source correspondence differs from selected sources")


@dataclass(frozen=True, slots=True)
class _SuccessorGraphNodeSourceInputs:
    """Original successor resources, carried as data by the nominal node use."""

    staged: _DirectWorkspaceStagedCommandResources
    code_host: object
    planning_source: object
    package_closure: tuple[object, ...]
    correspondence: object
    epoch: object
    expected_epoch: object


def _compose_successor_graph_node_source_inputs(
    staged: _DirectWorkspaceStagedCommandResources,
    code_host: object,
    *,
    planning_source: object,
    package_closure: tuple[object, ...],
    correspondence: object,
    epoch: object,
    expected_epoch: object,
) -> _SuccessorGraphNodeSourceInputs:
    """Retain the original committed successor resources for one graph node."""
    from aware_code_retained_registry_policy_runtime.planning_source_composition import (
        validate_composed_retained_planning_source,
    )
    from aware_code_semantic_contract_runtime import SemanticPackageCoordinate

    from .source_admission_catalog import WorkspaceV3GraphSourceCorrespondence

    if (
        type(staged) is not _DirectWorkspaceStagedCommandResources
        or type(staged.command.sources) is not _DirectWorkspaceDeclarationSources
        or _STAGED_ASSEMBLIES.get(staged.command.lifetime_runtime, (None,))[0]
        is not staged
        or _POLICY_HOSTS.get(code_host) is not staged
        or type(correspondence) is not WorkspaceV3GraphSourceCorrespondence
        or type(package_closure) is not tuple
        or not 1 <= len(package_closure) <= 4096
        or any(type(item) is not SemanticPackageCoordinate for item in package_closure)
    ):
        raise RuntimeError("original successor graph source unavailable")
    joint = staged.command.catalog_host
    joint.validate_current_catalog_epoch(epoch, expected=expected_epoch)
    parent = joint._command_parent
    if parent is None:
        raise RuntimeError("successor graph catalog parent unavailable")
    current = parent.current_record(expected_epoch)
    if (
        current.preparation is not epoch
        or current.attempt.predecessor is None
        or current.transfer is None
    ):
        raise RuntimeError("committed successor graph pair required")
    validate_composed_retained_planning_source(
        code_host, planning_source, package_closure
    )
    if correspondence.package() not in package_closure:
        raise RuntimeError("successor graph source package differs")
    joint.validate_current_catalog_epoch(epoch, expected=expected_epoch)
    return _SuccessorGraphNodeSourceInputs(
        staged,
        code_host,
        planning_source,
        package_closure,
        correspondence,
        epoch,
        expected_epoch,
    )


def _validate_successor_graph_node_source(
    command: _DirectWorkspaceCommandResources,
    node_admission: object,
    value: _SuccessorGraphNodeSourceInputs,
) -> None:
    """Join the current Code reader to original Workspace source membership."""
    from aware_code_retained_registry_policy_runtime.planning_source_composition import (
        validate_composed_retained_planning_source,
    )
    from aware_code_semantic_contract_runtime import SemanticPackageCoordinate

    from .materialization_operation import _graph_node_admission_state
    from .source_admission_catalog import WorkspaceV3GraphSourceCorrespondence

    if (
        type(command.sources) is not _DirectWorkspaceDeclarationSources
        or type(value) is not _SuccessorGraphNodeSourceInputs
        or type(value.staged) is not _DirectWorkspaceStagedCommandResources
        or value.staged.command is not command
        or _STAGED_ASSEMBLIES.get(command.lifetime_runtime, (None,))[0]
        is not value.staged
        or _POLICY_HOSTS.get(value.code_host) is not value.staged
        or type(value.correspondence) is not WorkspaceV3GraphSourceCorrespondence
        or type(value.package_closure) is not tuple
        or not 1 <= len(value.package_closure) <= 4096
        or any(
            type(item) is not SemanticPackageCoordinate
            for item in value.package_closure
        )
    ):
        raise RuntimeError("original successor graph source unavailable")
    state = _graph_node_admission_state(node_admission)
    package = state.node_binding.package
    if (
        value.correspondence.package() != package
        or package not in value.package_closure
        or tuple(sorted(
            (node.package for node in state.plan_result.graph.nodes),
            key=lambda item: item.package_ref,
        )) != value.package_closure
    ):
        raise RuntimeError("successor graph source package differs")
    command.catalog_host.validate_current_catalog_epoch(
        value.epoch, expected=value.expected_epoch
    )
    parent = command.catalog_host._command_parent
    if parent is None:
        raise RuntimeError("successor graph catalog parent unavailable")
    current = parent.current_record(value.expected_epoch)
    if (
        current.preparation is not value.epoch
        or current.attempt.predecessor is None
        or current.transfer is None
    ):
        raise RuntimeError("committed successor graph pair required")
    validate_composed_retained_planning_source(
        value.code_host, value.planning_source, value.package_closure
    )
    pair = command.catalog_host._result
    if pair is None:
        raise RuntimeError("successor graph catalog pair unavailable")
    entry = pair.workspace.package(package.package_ref)
    if entry != state.node_binding.package_entry:
        raise RuntimeError("successor graph node entry differs")
    planning_input = value.planning_source.read_dependencies(package)
    value.correspondence.validate(entry, planning_input)
    validate_composed_retained_planning_source(
        value.code_host, value.planning_source, value.package_closure
    )
    command.catalog_host.validate_current_catalog_epoch(
        value.epoch, expected=value.expected_epoch
    )
    if _graph_node_admission_state(node_admission) is not state:
        raise RuntimeError("successor graph node changed during source validation")


def _validate_command_owned_graph_node_source(
    command: _DirectWorkspaceCommandResources,
    node_admission: object,
    source_admission: object,
) -> None:
    """Check original command, graph owner and source without issuing approval.

    The installed graph host must use this command's lifetime as its owner.
    This check cannot authenticate a separately installed provider or Meta
    issuer, and its successful return is not a reusable authority token.
    """
    from .materialization_operation import (
        _graph_node_admission_state,
        _validate_graph_node_owner_source,
    )

    if type(command) is not _DirectWorkspaceCommandResources:
        raise TypeError("original Workspace command resources required")
    if type(command.sources) not in (
        _DirectWorkspaceSourceResources,
        _DirectWorkspaceDeclarationSources,
    ):
        raise RuntimeError("graph_v3_source_join_unavailable")
    owner = command.lifetime_runtime
    record = _COMMAND_ASSEMBLIES.get(owner)
    if (
        record is None
        or record[0] is not command
        or not _same_references(record[1], _resource_references(command))
        or not _same_references(record[2], _resource_references(command.sources))
        or command.sources.exclusion._runtime is not owner
        or command.sources.exclusion._parent is not command.invocation_parent
    ):
        raise RuntimeError("foreign or retired Workspace command assembly")
    command.sources.exclusion.check_live()
    if _graph_node_admission_state(node_admission).owner is not owner:
        raise RuntimeError("graph node is not owned by original Workspace command")
    if type(source_admission) is _SuccessorGraphNodeSourceInputs:
        _validate_successor_graph_node_source(
            command, node_admission, source_admission
        )
    else:
        _validate_graph_node_owner_source(
            node_admission,
            source_runtime=command.sources.source_admission_runtime,
            source_admission=source_admission,
        )
    if _graph_node_admission_state(node_admission).owner is not owner:
        raise RuntimeError("graph node owner changed during source validation")
    if (
        _COMMAND_ASSEMBLIES.get(owner) is not record
        or not _same_references(record[1], _resource_references(command))
        or not _same_references(record[2], _resource_references(command.sources))
    ):
        raise RuntimeError("Workspace command retired during source validation")
    command.sources.exclusion.check_live()


@dataclass(slots=True)
class _CommandNodeSourceSessionRecord:
    command: _DirectWorkspaceCommandResources
    node_admission: object
    source_admission: object
    process_id: int
    thread_id: int
    live: bool = True
    execution_plan: object | None = None
    publisher: object | None = None
    product_contribution: SelectedProviderProductContribution | None = None
    prior_output_state: _GraphPriorOutputStateBinding | None = None
    genesis_lineage: _GraphGenesisLineageBinding | None = None


@dataclass(frozen=True, slots=True)
class _GraphPriorOutputStateBinding:
    package: SemanticPackageCoordinate
    head_revision: int
    head_digest: ContentDigest
    occurrence: WorkspaceMaterializationPackageOccurrenceV4
    output_role: str
    output_state_name: str
    state: CodePackageOutputState | None


@dataclass(frozen=True, slots=True)
class _GraphGenesisLineageBinding:
    package: SemanticPackageCoordinate
    occurrence: WorkspaceMaterializationPackageOccurrenceV4
    namespace_snapshot: LocalOperationalNamespaceSnapshot


def _original_graph_node_state(admission: object):
    from .materialization_operation import (
        AdmittedWorkspaceSemanticMaterializationGraphNodeExecution,
        _graph_node_admission_state,
    )

    return _graph_node_admission_state(
        cast(AdmittedWorkspaceSemanticMaterializationGraphNodeExecution, admission)
    )


def _original_graph_head_observation(node_state):
    selected = node_state.node_binding
    nodes = tuple(
        node
        for node in node_state.plan_result.graph.nodes
        if node.node_digest == selected.node_digest
        and node.package == selected.package
    )
    if len(nodes) != 1:
        raise RuntimeError("original graph head observation unavailable")
    return nodes[0].head_observation


def _original_graph_semantic_source(record: _CommandNodeSourceSessionRecord):
    from .source_admission_catalog import WorkspaceV3GraphSourceCorrespondence

    source_inputs = record.source_admission
    if (
        not record.live
        or type(source_inputs) is not _SuccessorGraphNodeSourceInputs
        or type(record.command.sources) is not _DirectWorkspaceDeclarationSources
    ):
        raise RuntimeError("successor graph semantic source unavailable")
    entry = _original_graph_node_state(record.node_admission).node_binding.package_entry
    correspondence = source_inputs.correspondence
    if type(correspondence) is not WorkspaceV3GraphSourceCorrespondence:
        raise RuntimeError("original graph source correspondence unavailable")
    runtime, admission = correspondence.original_semantic_input_source(entry)
    if runtime is not record.command.sources.source_admission_runtime:
        raise RuntimeError("graph semantic source runtime differs from command")
    return runtime, admission


def _read_graph_prior_output_state(
    record: _CommandNodeSourceSessionRecord,
    binding: _GraphPriorOutputStateBinding,
):
    from .semantic_materialization_publication import (
        WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V4,
        WorkspaceSemanticMaterializationHeadRereadEvidenceV4,
        WorkspaceSemanticMaterializationPublisher,
    )

    node = _original_graph_node_state(record.node_admission)
    observation = _original_graph_head_observation(node)
    publisher = record.publisher
    contribution = record.product_contribution
    if (
        type(publisher) is not WorkspaceSemanticMaterializationPublisher
        or publisher is not node.operation._publisher
        or type(contribution) is not SelectedProviderProductContribution
        or observation.stored_head_contract
        != WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V4
        or observation.state != "stale"
        or observation.package != binding.package
        or observation.predecessor_head_revision != binding.head_revision
        or observation.predecessor_head_digest != binding.head_digest
        or observation.stored_package_occurrence != binding.occurrence
    ):
        raise RuntimeError("original V4 graph predecessor unavailable")
    selected = read_selected_provider_product_contribution(contribution)
    if (
        selected.expected.runtime is not node.operation._runtime
        or selected.expected.registration
        is not node.operation._graph_product_registration
    ):
        raise RuntimeError("V4 predecessor selected product differs")
    declaration = getattr(selected.executable, "declaration", None)
    if type(declaration) is not SemanticContractProviderDeclaration:
        raise RuntimeError("V4 predecessor selected declaration unavailable")
    source_runtime, source_admission = _original_graph_semantic_source(record)
    source_runtime.validate_publication_package_occurrence(
        source_admission, occurrence=binding.occurrence
    )
    head = publisher._read_graph_v4_head_evidence(
        binding.package.package_ref, observation_role="package_reuse"
    )
    if (
        type(head) is not WorkspaceSemanticMaterializationHeadRereadEvidenceV4
        or head.materialization_head_revision != binding.head_revision
        or head.materialization_head_digest != binding.head_digest
        or head.head.package_occurrence != binding.occurrence
        or head.head.base_head.package != binding.package
    ):
        raise RuntimeError("V4 graph predecessor changed")
    state = publisher._read_graph_v4_current_output_state(
        package=binding.package,
        expected_head_revision=binding.head_revision,
        expected_head_digest=binding.head_digest,
        declaration=declaration,
        output_role=binding.output_role,
        output_state_name=binding.output_state_name,
    )
    refreshed = read_selected_provider_product_contribution(contribution)
    if (
        refreshed.expected.runtime is not selected.expected.runtime
        or refreshed.expected.registration is not selected.expected.registration
        or refreshed.executable is not selected.executable
    ):
        raise RuntimeError("V4 predecessor selected product changed")
    source_runtime.validate_publication_package_occurrence(
        source_admission, occurrence=binding.occurrence
    )
    if (
        publisher._read_graph_v4_head(binding.package.package_ref)
        != (head.materialization_head_revision, head.head)
    ):
        raise RuntimeError("V4 graph predecessor changed during state read")
    return state


def _validate_graph_genesis_lineage(
    record: _CommandNodeSourceSessionRecord,
    binding: _GraphGenesisLineageBinding,
) -> None:
    from .semantic_materialization_publication import (
        WorkspaceSemanticMaterializationPublisher,
    )

    node = _original_graph_node_state(record.node_admission)
    observation = _original_graph_head_observation(node)
    publisher = record.publisher
    contribution = record.product_contribution
    if (
        type(publisher) is not WorkspaceSemanticMaterializationPublisher
        or publisher is not node.operation._publisher
        or type(contribution) is not SelectedProviderProductContribution
        or observation.package != binding.package
        or observation.state != "missing"
        or observation.stored_head_contract is not None
        or observation.predecessor_head_revision is not None
        or observation.predecessor_head_digest is not None
        or observation.stored_package_occurrence is not None
        or observation.expected_post_revision != 1
    ):
        raise RuntimeError("original graph genesis observation unavailable")
    selected = read_selected_provider_product_contribution(contribution)
    if (
        selected.expected.runtime is not node.operation._runtime
        or selected.expected.registration
        is not node.operation._graph_product_registration
    ):
        raise RuntimeError("graph genesis selected product changed")
    source_runtime, source_admission = _original_graph_semantic_source(record)
    source_runtime.validate_publication_package_occurrence(
        source_admission, occurrence=binding.occurrence
    )
    if publisher._read_graph_package_head_evidence(
        binding.package.package_ref, observation_role="package_reuse"
    ) is not None:
        raise RuntimeError("graph genesis package head appeared")
    publisher._validate_v4_occurrence_absence(
        binding.namespace_snapshot, binding.package, binding.occurrence
    )
    source_runtime.validate_publication_package_occurrence(
        source_admission, occurrence=binding.occurrence
    )
    if publisher._read_graph_package_head_evidence(
        binding.package.package_ref, observation_role="package_reuse"
    ) is not None:
        raise RuntimeError("graph genesis package head appeared")


def _retire_command_node_session_by_identity(operation_use) -> None:
    """Revoke the original registration without invoking a changed use class."""
    with _COMMAND_NODE_SESSIONS_LOCK:
        for retained_key in _COMMAND_NODE_SESSIONS.keyrefs():
            if retained_key() is operation_use:
                # Use the original, already-hashed weak key. Constructing a
                # new key would invoke the possibly substituted use's hash.
                record = vars(_COMMAND_NODE_SESSIONS)["data"].pop(retained_key)
                record.live = False
                return


class _CommandOwnedGraphNodeSourceSession:
    """Nominal lifetime for repeated checks of the same original handles."""

    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("command-owned node session is issuer-created only")

    def __init_subclass__(cls, **kwargs):
        del kwargs
        raise TypeError("command-owned node session is sealed")

    def __copy__(self):
        raise TypeError("command-owned node session cannot be copied")

    def __deepcopy__(self, memo):
        del memo
        raise TypeError("command-owned node session cannot be copied")

    def __reduce__(self):
        raise TypeError("command-owned node session cannot be serialized")

    def __reduce_ex__(self, protocol):
        del protocol
        raise TypeError("command-owned node session cannot be serialized")

    def validate(self) -> None:
        if type(self) is not _CommandOwnedGraphNodeSourceSession:
            raise TypeError("original command-owned node session required")
        with _COMMAND_NODE_SESSIONS_LOCK:
            record = _COMMAND_NODE_SESSIONS.get(self)
        if record is None or not record.live:
            raise RuntimeError("command-owned node session is closed")
        if record.process_id != os.getpid() or record.thread_id != get_ident():
            self.close()
            raise RuntimeError("command-owned node session context changed")
        try:
            _validate_command_owned_graph_node_source(
                record.command, record.node_admission, record.source_admission
            )
            if record.prior_output_state is not None:
                current = _read_graph_prior_output_state(
                    record, record.prior_output_state
                )
                if current != record.prior_output_state.state:
                    raise RuntimeError("V4 graph prior output state changed")
            if record.genesis_lineage is not None:
                _validate_graph_genesis_lineage(record, record.genesis_lineage)
        except BaseException:
            self.close()
            raise
        with _COMMAND_NODE_SESSIONS_LOCK:
            if _COMMAND_NODE_SESSIONS.get(self) is not record or not record.live:
                raise RuntimeError("command-owned node session retired during check")

    def bind_execution_plan(self, plan: object) -> None:
        """Retain the operation's resolved plan for exact selected execution."""
        from .materialization_operation import (
            WorkspaceMaterializeExecutionPlan,
            _graph_node_admission_state,
            derive_workspace_materialize_execution_input_closure_digest,
        )

        self.validate()
        if type(plan) is not WorkspaceMaterializeExecutionPlan:
            raise TypeError("exact graph-node execution plan required")
        plan.__post_init__()
        with _COMMAND_NODE_SESSIONS_LOCK:
            record = _COMMAND_NODE_SESSIONS.get(self)
        if record is None or not record.live or record.execution_plan is not None:
            raise RuntimeError("graph-node execution plan unavailable or already bound")
        state = _graph_node_admission_state(record.node_admission)
        request = state.operation_admission.request
        state.operation._validate_plan(request, plan)
        if (
            plan.invocation.target_package != state.node_binding.package
            or derive_workspace_materialize_execution_input_closure_digest(
                plan.input_bodies
            ) != state.execution_input_closure_digest.value
        ):
            raise RuntimeError("graph-node execution plan differs from original node")
        self.validate()
        with _COMMAND_NODE_SESSIONS_LOCK:
            if _COMMAND_NODE_SESSIONS.get(self) is not record or not record.live:
                raise RuntimeError("graph-node session retired during plan binding")
            record.execution_plan = plan

    @contextmanager
    def original_semantic_input_source(self):
        """Keep one original source admission under this graph-node lifetime."""
        self.validate()
        with _COMMAND_NODE_SESSIONS_LOCK:
            record = _COMMAND_NODE_SESSIONS.get(self)
        if record is None:
            raise RuntimeError("command-owned node session is closed")
        runtime, admission = _original_graph_semantic_source(record)
        self.validate()
        try:
            yield runtime, admission
        finally:
            self.validate()

    def prepare_semantic_input_expectation(
        self,
        *,
        use_ref: str,
        stage: str,
        source_scope: str,
        role: str,
        contract: SemanticContractRef,
    ) -> SemanticInputProductionExpectation:
        """Bind a Code input proposal to this original node and source use.

        The selected Code producer still owns stage, role and contract meaning.
        This value grants no source admission or producer registration.
        """
        try:
            self.validate()
            with _COMMAND_NODE_SESSIONS_LOCK:
                record = _COMMAND_NODE_SESSIONS.get(self)
            if record is None or not record.live:
                raise RuntimeError("command-owned node session is closed")
            node = _original_graph_node_state(record.node_admission)
            runtime, admission = _original_graph_semantic_source(record)
            inspection = runtime.inspect(admission)
            if inspection.package != node.node_binding.package:
                raise RuntimeError("graph semantic input package differs from node")
            sources = runtime.semantic_input_source_coordinates(
                admission,
                source_scope=source_scope,
                role=role,
                contract=contract,
            )
            expected = SemanticInputProductionExpectation.create(
                use_ref=use_ref,
                operation_ref=node.operation_admission.request.operation_ref,
                stage=stage,
                package_identity=SemanticInputPackageIdentity(
                    inspection.package,
                    inspection.package_authority.semantic_package.name,
                ),
                operation_identity=self,
                source_identity=admission,
                source_coordinates=sources,
            )
            runtime.validate_semantic_input_source(admission, expected=expected)
            self.validate()
            return expected
        except BaseException:
            self.close()
            raise

    def read_current_output_state(
        self, *, output_role: str, output_state_name: str
    ) -> CodePackageOutputState:
        """Read one original V4 prior state under this selected graph-node use.

        Missing heads remain unavailable. The retained binding makes subsequent
        node-use checks reread the same head, selected result and state body.
        """
        self.validate()
        with _COMMAND_NODE_SESSIONS_LOCK:
            record = _COMMAND_NODE_SESSIONS.get(self)
        if (
            record is None or not record.live
            or record.prior_output_state is not None
            or record.genesis_lineage is not None
        ):
            raise RuntimeError("V4 graph prior output state already read or unavailable")
        observation = _original_graph_head_observation(
            _original_graph_node_state(record.node_admission)
        )
        if (
            type(output_role) is not str
            or not output_role
            or type(output_state_name) is not str
            or not output_state_name
            or observation.predecessor_head_revision is None
            or observation.predecessor_head_digest is None
            or observation.stored_package_occurrence is None
        ):
            raise RuntimeError("V4 graph prior output state is unavailable")
        binding = _GraphPriorOutputStateBinding(
            observation.package,
            observation.predecessor_head_revision,
            observation.predecessor_head_digest,
            observation.stored_package_occurrence,
            output_role,
            output_state_name,
            None,
        )
        try:
            state = _read_graph_prior_output_state(record, binding)
            self.validate()
        except BaseException:
            self.close()
            raise
        with _COMMAND_NODE_SESSIONS_LOCK:
            if (
                _COMMAND_NODE_SESSIONS.get(self) is not record
                or not record.live
                or record.prior_output_state is not None
            ):
                raise RuntimeError("V4 graph prior state session changed")
            record.prior_output_state = _GraphPriorOutputStateBinding(
                binding.package,
                binding.head_revision,
                binding.head_digest,
                binding.occurrence,
                binding.output_role,
                binding.output_state_name,
                state,
            )
        self.validate()
        return state

    def observe_genesis_lineage_absence(self) -> None:
        """Retain only original Workspace lineage absence under this node use.

        Historical Development continuity is separate. This method issues no
        empty output state and cannot authorize a genesis Code input by itself.
        """
        from .semantic_materialization_publication import (
            WorkspaceSemanticMaterializationPublisher,
        )

        try:
            self.validate()
            with _COMMAND_NODE_SESSIONS_LOCK:
                record = _COMMAND_NODE_SESSIONS.get(self)
            if (
                record is None or not record.live
                or record.genesis_lineage is not None
                or record.prior_output_state is not None
            ):
                raise RuntimeError("graph genesis lineage observation unavailable")
            node = _original_graph_node_state(record.node_admission)
            publisher = record.publisher
            if type(publisher) is not WorkspaceSemanticMaterializationPublisher:
                raise RuntimeError("original graph publisher unavailable")
            source_runtime, source_admission = _original_graph_semantic_source(record)
            occurrence = source_runtime.read_publication_package_occurrence(
                source_admission
            )
            snapshot = publisher._observe_v4_occurrence_absence(
                node.node_binding.package, occurrence
            )
            binding = _GraphGenesisLineageBinding(
                node.node_binding.package, occurrence, snapshot
            )
            _validate_graph_genesis_lineage(record, binding)
            self.validate()
            with _COMMAND_NODE_SESSIONS_LOCK:
                if _COMMAND_NODE_SESSIONS.get(self) is not record or not record.live:
                    raise RuntimeError("graph genesis node use retired")
                record.genesis_lineage = binding
            self.validate()
        except BaseException:
            self.close()
            raise

    def validate_genesis_lineage_absence(self) -> None:
        """Recheck this use's original negative observation without detaching it."""
        self.validate()
        with _COMMAND_NODE_SESSIONS_LOCK:
            record = _COMMAND_NODE_SESSIONS.get(self)
        if record is None or not record.live or record.genesis_lineage is None:
            raise RuntimeError("graph genesis lineage observation unavailable")

    def close(self) -> None:
        if type(self) is not _CommandOwnedGraphNodeSourceSession:
            raise TypeError("original command-owned node session required")
        with _COMMAND_NODE_SESSIONS_LOCK:
            record = _COMMAND_NODE_SESSIONS.pop(self, None)
            if record is not None:
                record.live = False


@contextmanager
def _command_owned_graph_node_source_session(
    command: _DirectWorkspaceCommandResources,
    node_admission: object,
    source_admission: object,
    *,
    publisher: object | None = None,
    product_contribution: SelectedProviderProductContribution | None = None,
) -> Iterator[_CommandOwnedGraphNodeSourceSession]:
    """Retain original inputs across an owner await, with terminal cleanup."""
    _validate_command_owned_graph_node_source(
        command, node_admission, source_admission
    )
    if (publisher is None) != (product_contribution is None):
        raise RuntimeError("graph prior-state origin is incomplete")
    if publisher is not None:
        from .semantic_materialization_publication import (
            WorkspaceSemanticMaterializationPublisher,
        )

        node = _original_graph_node_state(node_admission)
        selected = read_selected_provider_product_contribution(product_contribution)
        if (
            type(publisher) is not WorkspaceSemanticMaterializationPublisher
            or node.operation._publisher is not publisher
            or selected.expected.runtime is not node.operation._runtime
            or selected.expected.registration
            is not node.operation._graph_product_registration
        ):
            raise RuntimeError("graph prior-state origin differs from selected node")
    session = object.__new__(_CommandOwnedGraphNodeSourceSession)
    with _COMMAND_NODE_SESSIONS_LOCK:
        _COMMAND_NODE_SESSIONS[session] = _CommandNodeSourceSessionRecord(
            command, node_admission, source_admission, os.getpid(), get_ident(),
            publisher=publisher,
            product_contribution=product_contribution,
        )
    try:
        yield session
    finally:
        session.close()


@dataclass(slots=True)
class _SelectedInputReadRecord:
    command: Any
    host: Any
    factory: Any
    selected: Any
    contribution: Any
    registration: Any
    epoch: Any
    epoch_expected: Any
    thread: Any
    stack: ExitStack | None
    expectations: tuple[SemanticInputProductionExpectation, ...] = ()
    source_depths: tuple[int, ...] = ()
    results: tuple[tuple[Any, Any, Any, Any], ...] = ()
    live: bool = True
    assembly_binding: Any = None
    dependency_binding: Any = None
    closure: Any = None
    full_checkpoints: int = 0


_INPUT_ASSEMBLY_KIND = _input_values.SelectedInputVerificationAssembly
_INPUT_SOURCE_KIND = _input_values.SelectedInputSourceResult
_INPUT_ASSEMBLY_FIELDS = (
    "semantic_input", "input_bodies", "source_results", "source_input_roles",
    "context_input_roles", "dependency_products", "dependency_input_role",
)
_INPUT_SOURCE_FIELDS = ("host", "registration", "source_admission", "expected", "result")
_INPUT_ASSEMBLY_SLOTS = tuple(_INPUT_ASSEMBLY_KIND.__dict__[name] for name in _INPUT_ASSEMBLY_FIELDS)
_INPUT_SOURCE_SLOTS = tuple(_INPUT_SOURCE_KIND.__dict__[name] for name in _INPUT_SOURCE_FIELDS)
_INPUT_CLOSURE_KIND = SelectedProviderInvocationClosure
_INPUT_CLOSURE_BODY_SLOT = _INPUT_CLOSURE_KIND.__dict__["input_bodies"]
_SELECTED_INPUT_DEPENDENCY_RECORD_LIMIT = 2_048
_FULFILLMENT_RECORD_KIND = _Fulfillment
_FULFILLMENT_RECORD_DICT = type.__getattribute__(_Fulfillment, "__dict__")["__dict__"]
_FULFILLMENT_RECORD_ABSENT = object()
_FULFILLMENT_RECORD_ENTRANCES = tuple(
    (name, inspect.getattr_static(_Fulfillment, name, _FULFILLMENT_RECORD_ABSENT))
    for name in ("resolution", "body", "heads", "terminal", "__getattribute__", "__setattr__", "retire")
)


def _clear_selected_input_rejection_frames(error):
    """Release only inactive Workspace frames; foreign owner frames stay intact."""
    traceback = frame = None
    try:
        traceback = BaseException.__dict__["__traceback__"].__get__(error)
        while traceback is not None:
            frame = traceback.tb_frame
            if frame.f_code.co_filename == __file__:
                try:
                    frame.clear()
                except RuntimeError:
                    pass  # Running frames clear their owned locals in finally.
            traceback = traceback.tb_next
    finally:
        traceback = frame = error = None


def _selected_input_slots(kind, names, slots):
    namespace = type.__getattribute__(kind, "__dict__")
    if any(namespace.get(name) is not slot for name, slot in zip(names, slots, strict=True)):
        raise RuntimeError("selected-input original value descriptor changed")


@dataclass(frozen=True, slots=True)
class _SelectedInputAssemblyBinding:
    assembly: Any
    fields: tuple[Any, ...]
    sources: tuple[tuple[Any, tuple[Any, ...]], ...]
    role_rows: tuple[tuple[tuple[Any, ...], tuple[Any, ...]], ...]

    def check(self, record, *, assembly=None, closure=None):
        try:
            if (type(self.assembly) is not _INPUT_ASSEMBLY_KIND
                    or _input_values.SelectedInputVerificationAssembly is not _INPUT_ASSEMBLY_KIND
                    or _input_values.SelectedInputSourceResult is not _INPUT_SOURCE_KIND
                    or (assembly is not None and assembly is not self.assembly)):
                raise RuntimeError("selected-input original assembly differs")
            _selected_input_slots(_INPUT_ASSEMBLY_KIND, _INPUT_ASSEMBLY_FIELDS, _INPUT_ASSEMBLY_SLOTS)
            _selected_input_slots(_INPUT_SOURCE_KIND, _INPUT_SOURCE_FIELDS, _INPUT_SOURCE_SLOTS)
            if any(slot.__get__(self.assembly) is not value
                   for slot, value in zip(_INPUT_ASSEMBLY_SLOTS, self.fields, strict=True)):
                raise RuntimeError("selected-input assembly field changed")
            if len(self.sources) != len(record.results):
                raise RuntimeError("selected-input retained source closure differs")
            for (source, fields), original in zip(self.sources, record.results, strict=True):
                if (type(source) is not _INPUT_SOURCE_KIND
                        or any(slot.__get__(source) is not value
                               for slot, value in zip(_INPUT_SOURCE_SLOTS, fields, strict=True))
                        or fields[2] is not record.selected
                        or any(value is not retained for value, retained in zip(
                            (fields[0], fields[1], fields[3], fields[4]), original, strict=True))):
                    raise RuntimeError("selected-input source association changed")
            for rows, originals in self.role_rows:
                if len(rows) != len(originals) or any(row is not original for row, original in zip(rows, originals, strict=True)):
                    raise RuntimeError("selected-input role tuple changed")
            if record.dependency_binding is not None:
                if self.fields[5] is not record.dependency_binding.admission:
                    raise RuntimeError("selected-input dependency association changed")
                record.dependency_binding.check(record)
            elif self.fields[5] is not None:
                raise RuntimeError("selected-input original products unavailable")
            if closure is not None:
                namespace = type.__getattribute__(_INPUT_CLOSURE_KIND, "__dict__")
                if (SelectedProviderInvocationClosure is not _INPUT_CLOSURE_KIND
                        or type(closure) is not _INPUT_CLOSURE_KIND
                        or namespace.get("input_bodies") is not _INPUT_CLOSURE_BODY_SLOT
                        or _INPUT_CLOSURE_BODY_SLOT.__get__(closure) is not self.fields[1]
                        or (record.closure is not None and closure is not record.closure)):
                    raise RuntimeError("selected-input original closure differs")
        finally:
            self = record = assembly = closure = fields = original = source = None  # noqa: PLW0642 - clear rejection custody
            rows = originals = namespace = None


def _selected_input_dependency_records(record, operation, resolution, fulfillment):
    try:
        from aware_code_semantic_contract_runtime.dependency_admission_interfaces import (
            RetainedDependencyResolutionExpectation,
        )

        from .declaration_scope_admission import _SemanticRecord
        from .dependency_fulfillment import (
            WorkspaceDependencyFulfillmentAdmission,
            _Fulfillment,
            _WorkspaceEmptyDependencyFulfillmentRuntime,
        )
        from .dependency_resolution import (
            WorkspaceDependencyResolutionAdmission,
            _Resolution,
            _WorkspaceDependencyResolutionRuntime,
        )

        if (type(resolution) is not WorkspaceDependencyResolutionAdmission
                or type(fulfillment) is not WorkspaceDependencyFulfillmentAdmission):
            raise RuntimeError("selected-input original dependency admissions required")
        issuer = record.command.sources.declaration_scope_runtime
        resolutions, fulfillments = issuer._dependency_resolution, issuer._dependency_fulfillment
        if (type(resolutions) is not _WorkspaceDependencyResolutionRuntime
                or type(fulfillments) is not _WorkspaceEmptyDependencyFulfillmentRuntime):
            raise RuntimeError("selected-input original dependency issuer unavailable")
        tables = (resolutions.records, fulfillments.records, issuer._semantic)
        if any(type(table) is not dict or len(table) > _SELECTED_INPUT_DEPENDENCY_RECORD_LIMIT
               for table in tables):
            raise RuntimeError("selected-input dependency association work bound exceeded")
        original = _selected_input_identity_lookup(resolutions.records, resolution)
        fulfilled = _selected_input_identity_lookup(fulfillments.records, fulfillment)
        if (type(original) is not _Resolution
                or type(fulfilled) is not _FULFILLMENT_RECORD_KIND
                or _Fulfillment is not _FULFILLMENT_RECORD_KIND
                or type.__getattribute__(_FULFILLMENT_RECORD_KIND, "__dict__").get("__dict__")
                is not _FULFILLMENT_RECORD_DICT
                or any(inspect.getattr_static(_FULFILLMENT_RECORD_KIND, name, _FULFILLMENT_RECORD_ABSENT)
                       is not descriptor for name, descriptor in _FULFILLMENT_RECORD_ENTRANCES)):
            raise RuntimeError("selected-input dependency admission retired")
        fields = _FULFILLMENT_RECORD_DICT.__get__(fulfilled)
        if (type(fields) is not dict or fields.get("terminal") is not False
                or type(fields.get("body")) is not SemanticBody
                or type(fields.get("heads")) is not tuple):
            raise RuntimeError("selected-input dependency admission retired")
        source = _selected_input_identity_lookup(issuer._semantic, original.inventory)
        if (original.operation is not operation or type(source) is not _SemanticRecord
                or type(original.expected) is not RetainedDependencyResolutionExpectation
                or source.selected is not record.selected
                or original.expected.parent_identity is not record.command.invocation_parent
                or original.expected.epoch_identity is not record.epoch
                or fields.get("resolution") is not resolution):
            raise RuntimeError("selected-input dependency node/source association differs")
        # Retain the original body and head tuple as well as their family. Equal
        # replacements cannot revive or silently change this read association.
        return resolutions, fulfillments, original, fulfilled, source, fields["body"], fields["heads"]
    finally:
        record = operation = resolution = fulfillment = issuer = resolutions = fulfillments = None
        original = fulfilled = source = tables = fields = None


@dataclass(frozen=True, slots=True)
class _SelectedInputDependencyBinding:
    consumer: Any
    admission: Any
    operation: Any
    resolution: Any
    fulfillment: Any
    originals: tuple[Any, ...]

    def check(self, record):
        try:
            current = _selected_input_dependency_records(
                record, self.operation, self.resolution, self.fulfillment,
            )
            if any(actual is not original for actual, original in zip(current, self.originals, strict=True)):
                raise RuntimeError("selected-input original dependency records changed")
        finally:
            self = record = current = None  # noqa: PLW0642 - clear rejection custody


def _selected_input_identity_lookup(mapping, value):
    key = retained = None
    try:
        for key, retained in mapping.items():
            if key is value:
                return retained
        return None
    finally:
        key = retained = value = None


def _selected_input_read_record(node):
    # Refuse a fork before touching a potentially inherited locked mutex.
    if os.getpid() != _SELECTED_INPUT_NODES_PID:
        raise RuntimeError("selected-input read belongs to another process")
    candidate = record = None
    try:
        with _SELECTED_INPUT_NODES_LOCK:
            for weak_node, record in _SELECTED_INPUT_NODES:
                candidate = weak_node()
                if candidate is node:
                    if not record.live:
                        raise RuntimeError("selected-input read is terminal")
                    return record
        raise RuntimeError("unknown or terminal selected-input read")
    finally:
        # A held unknown-node error must not pin the last unrelated family.
        candidate = record = None
        node = None


def _retire_selected_input_read(record):
    """Drop local custody before cleanup; never dispose borrowed Code owners."""
    if os.getpid() != _SELECTED_INPUT_NODES_PID:
        raise RuntimeError("selected-input read belongs to another process")
    if record.command is None:
        return
    stack = None
    errors = []
    retirement_entered = False
    try:
        record.live = False
        if record.command.lifetime_runtime._guard is not None:
            # A failed Code release can leave the original exclusion held.
            # Mark terminal without reacquisition or dropping borrowed inputs.
            return
        try:
            with record.command.sources.exclusion.mutation(retiring=True):
                retirement_entered = True
                record.live = False
        except BaseException as error:  # noqa: BLE001 - independently unwind owned contexts
            record.live = False
            errors.append(error)
            if retirement_entered or record.command.lifetime_runtime._guard is not None:
                # A failed mutation exit cannot confirm guard release. Keep the
                # terminal family discoverable, including its stack and inputs,
                # until a later retirement can confirm exclusion exit.
                raise BaseExceptionGroup("selected-input read retirement release pending", errors)
            # An acquisition refusal with no held guard may still dispose local
            # custody after parent expiration; borrowed owners remain untouched.
        with _SELECTED_INPUT_NODES_LOCK:
            for index in range(len(_SELECTED_INPUT_NODES) - 1, -1, -1):
                if _SELECTED_INPUT_NODES[index][1] is record:
                    del _SELECTED_INPUT_NODES[index]
        stack, record.stack = record.stack, None
        record.expectations = ()
        record.source_depths = ()
        record.results = ()
        record.assembly_binding = record.dependency_binding = record.closure = None
        record.command = record.host = record.factory = record.selected = None
        record.contribution = record.registration = record.epoch = None
        record.epoch_expected = record.thread = None
        # Owned source contexts unwind outside parent/registry exclusion.
        if stack is not None:
            try:
                stack.close()
            except BaseException as error:  # noqa: BLE001 - independently unwind owned contexts
                errors.append(error)
        if errors:
            raise BaseExceptionGroup("selected-input read retirement failed", errors)
    finally:
        stack = record = None


def _retire_selected_input_reads_for_host(host):
    """Terminal local cleanup before the enclosing Code host is disposed."""
    if os.getpid() != _SELECTED_INPUT_NODES_PID:
        raise RuntimeError("selected-input read belongs to another process")
    records = record = None
    errors = []
    try:
        with _SELECTED_INPUT_NODES_LOCK:
            records = tuple(
                item for _, item in _SELECTED_INPUT_NODES if item.host is host
            )
        if records:
            from aware_code_retained_registry_policy_runtime import product_execution

            command = records[0].command
            if command.lifetime_runtime._guard is not None:
                for record in records:
                    record.live = False
                product_execution._retire_selected_input_host(host, exclusion_pending=True)
                raise RuntimeError("selected-input disposal awaits original guard release")
            with command.sources.exclusion.mutation(retiring=True):
                for record in records:
                    record.live = False
                product_execution._retire_selected_input_host(host)
            # Code drops its borrowed source references before the owning
            # Workspace source contexts unwind, outside confirmed exclusion.
            product_execution._dispose_retired_selected_inputs(host)
        for record in reversed(records):
            try:
                _retire_selected_input_read(record)
            except BaseException as error:  # noqa: BLE001 - unwind every owned family
                errors.append(error)
        if errors:
            raise BaseExceptionGroup("selected-input host retirement failed", errors)
    finally:
        records = record = host = command = None


def _validate_selected_input_read_record(record):
    """Original owner checks only; never a replacement source verifier."""
    command = issuer = product = host = registration = expected = result = None
    try:
        command = record.command
        _require_live_direct_workspace_command(command)
        if record.dependency_binding is not None:
            record.dependency_binding.check(record)
        if record.assembly_binding is not None:
            record.assembly_binding.check(record)
        staged = _POLICY_HOSTS.get(record.host)
        if (
            staged is None
            or staged.command is not command
            or _SELECTED_INPUT_FACTORIES.get(record.host) is not record.factory
            or record.factory._command is not command
            or record.factory._epoch is not record.epoch
            or record.factory._epoch_expected is not record.epoch_expected
            or not any(
                item is record.contribution for item in staged.product_contributions
            )
        ):
            raise RuntimeError("selected-input read host or catalog epoch changed")
        product = read_selected_provider_product_contribution(record.contribution)
        if product.expected.registration is not record.registration:
            raise RuntimeError("selected-input read registration changed")
        command.catalog_host.validate_current_catalog_epoch(
            record.epoch, expected=record.epoch_expected
        )
        _read_direct_workspace_selected_participants(command, record.selected)
        issuer = command.sources.declaration_scope_runtime
        for expected in record.expectations:
            if (
                type(expected) is not SemanticInputProductionExpectation
                or expected.operation_identity is not command.invocation_parent
                or expected.source_identity is not record.selected
            ):
                raise RuntimeError("selected-input parent/source association changed")
            issuer.validate_semantic_input_source(record.selected, expected=expected)
        from aware_code_semantic_contract_runtime.semantic_input_producer import (
            validate_registered_semantic_input_result,
        )

        for host, registration, expected, result in record.results:
            validate_registered_semantic_input_result(
                host,
                registration,
                source_admission=record.selected,
                expected=expected,
                result=result,
            )
        _require_live_direct_workspace_command(command)
    finally:
        command = issuer = product = host = registration = expected = result = (
            record
        ) = None


def _selected_input_retained_bytes(record):
    # Count each occurrence, including equal/shared source and context bodies.
    return sum(
        sum(item.coordinate.size_bytes for item in expected.source_coordinates)
        + sum(len(body.canonical_body) for body in expected.context_bodies)
        for expected in record.expectations
    ) + sum(len(result.canonical_body) for _, _, _, result in record.results)


def _retain_selected_input_expectation(record, expected, *, depth):
    record.expectations += (expected,)
    record.source_depths += (depth,)
    if (
        len(record.expectations) > 32
        or depth > 8
        or len(expected.source_coordinates) > 512
        or sum(item.coordinate.size_bytes for item in expected.source_coordinates)
        + sum(len(body.canonical_body) for body in expected.context_bodies)
        > 8 * 1024 * 1024
        or _selected_input_retained_bytes(record) > 32 * 1024 * 1024
    ):
        raise RuntimeError("selected-input source retention budget exceeded")


class _CommandOwnedSelectedInputReadSession:
    """Original source/input association for Code's generic read delivery."""

    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls):
        raise TypeError("selected-input read is issuer-created only")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("selected-input read is sealed")

    def __copy__(self):
        raise TypeError("selected-input read cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("selected-input read cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("selected-input read cannot be serialized")

    def validate(self) -> None:
        record = None
        try:
            record = _selected_input_read_record(self)
            if type(self) is not _CommandOwnedSelectedInputReadSession:
                raise TypeError("original selected-input read required")
            if record.thread is not current_thread() or not record.thread.is_alive():
                raise RuntimeError("selected-input read thread changed")
            _validate_selected_input_read_record(record)
            if _selected_input_read_record(self) is not record:
                raise RuntimeError("selected-input read retired during validation")
        except BaseException as error:
            _clear_selected_input_rejection_frames(error)
            if record is not None:
                _retire_selected_input_read(record)
            raise
        finally:
            record = self = None  # noqa: PLW0642 - clear rejection custody

    def prepare_source_expectation(
        self, *, use_ref, stage, source_coordinates, context_contracts=()
    ):
        """Own the existing issuer's context, without rewriting its identity."""
        record = expected = None
        try:
            _SELECTED_INPUT_READ_VALIDATE(self)
            record = _selected_input_read_record(self)
            if record.assembly_binding is not None:
                raise RuntimeError("selected-input assembly is already frozen")
            if len(record.expectations) >= 32:
                raise RuntimeError("selected-input retained source limit exceeded")
            issuer = record.command.sources.declaration_scope_runtime
            assert record.stack is not None
            expected = record.stack.enter_context(
                issuer.original_pre_request_input(
                    record.selected,
                    use_ref=use_ref,
                    stage=stage,
                    source_coordinates=source_coordinates,
                    context_contracts=context_contracts,
                )
            )
            _retain_selected_input_expectation(record, expected, depth=1)
            _SELECTED_INPUT_READ_VALIDATE(self)
            return expected
        except BaseException as error:
            _clear_selected_input_rejection_frames(error)
            if record is not None:
                _retire_selected_input_read(record)
            raise
        finally:
            record = expected = self = None  # noqa: PLW0642 - clear rejection custody
            issuer = source_coordinates = context_contracts = None

    def prepare_selected_source_expectation(
        self,
        host,
        registration,
        *,
        selection_expected,
        result,
        use_ref,
        stage,
        source_contracts,
        context_contracts=(),
    ):
        """Reuse the original selected-source reader and this node's predecessor."""
        record = expected = issuer = None
        try:
            _SELECTED_INPUT_READ_VALIDATE(self)
            record = _selected_input_read_record(self)
            if record.assembly_binding is not None:
                raise RuntimeError("selected-input assembly is already frozen")
            if not any(
                a is host
                and b is registration
                and c is selection_expected
                and d is result
                for a, b, c, d in record.results
            ):
                raise RuntimeError("selected source lacks original node predecessor")
            index = next(
                index
                for index, value in enumerate(record.expectations)
                if value is selection_expected
            )
            depth = record.source_depths[index] + 1
            if depth > 8 or len(record.expectations) >= 32:
                raise RuntimeError("selected-input source chain limit exceeded")
            issuer = record.command.sources.declaration_scope_runtime
            assert record.stack is not None
            expected = record.stack.enter_context(
                issuer.original_selected_source_input(
                    record.selected,
                    host=host,
                    registration=registration,
                    selection_expected=selection_expected,
                    result=result,
                    use_ref=use_ref,
                    stage=stage,
                    source_contracts=source_contracts,
                    context_contracts=context_contracts,
                )
            )
            _retain_selected_input_expectation(record, expected, depth=depth)
            _SELECTED_INPUT_READ_VALIDATE(self)
            return expected
        except BaseException as error:
            _clear_selected_input_rejection_frames(error)
            if record is not None:
                _retire_selected_input_read(record)
            raise
        finally:
            record = expected = issuer = host = registration = result = None
            self = selection_expected = source_contracts = context_contracts = None  # noqa: PLW0642 - clear rejection custody

    def retain_source_result(self, host, registration, *, expected, result) -> None:
        """Associate one original Code return with a node-owned expectation.

        Producer hosts, registrations and returned results remain borrowed.
        Their owning composer must keep them live and release them separately.
        """
        record = None
        try:
            _SELECTED_INPUT_READ_VALIDATE(self)
            record = _selected_input_read_record(self)
            if record.assembly_binding is not None:
                raise RuntimeError("selected-input assembly is already frozen")
            if (
                not any(item is expected for item in record.expectations)
                or any(item[2] is expected for item in record.results)
                or len(record.results) >= 32
            ):
                raise RuntimeError("foreign, replayed or excessive source result")
            from aware_code_semantic_contract_runtime.semantic_input_producer import (
                validate_registered_semantic_input_result,
            )

            validate_registered_semantic_input_result(
                host,
                registration,
                source_admission=record.selected,
                expected=expected,
                result=result,
            )
            record.results += ((host, registration, expected, result),)
            if _selected_input_retained_bytes(record) > 32 * 1024 * 1024:
                raise RuntimeError("selected-input result retention budget exceeded")
            _SELECTED_INPUT_READ_VALIDATE(self)
        except BaseException as error:
            _clear_selected_input_rejection_frames(error)
            if record is not None:
                _retire_selected_input_read(record)
            raise
        finally:
            record = self = host = registration = expected = result = None  # noqa: PLW0642 - clear rejection custody

    def admit_dependency_products(self, operation, resolution, fulfillment, *, body):
        """Use the existing consumer only for this node's original admissions."""
        record = originals = consumer = admission = None
        try:
            _SELECTED_INPUT_READ_VALIDATE(self)
            record = _selected_input_read_record(self)
            if record.assembly_binding is not None or record.dependency_binding is not None:
                raise RuntimeError("selected-input products are already frozen")
            originals = _selected_input_dependency_records(record, operation, resolution, fulfillment)
            from aware_code_retained_registry_policy_runtime.dependency_admission_origin import (
                assemble_dependency_admission_consumer,
            )

            consumer = assemble_dependency_admission_consumer(record.host)
            admission = consumer.admit_dependency_products(operation, resolution, fulfillment, body=body)
            record.dependency_binding = _SelectedInputDependencyBinding(
                consumer, admission, operation, resolution, fulfillment, originals,
            )
            _SELECTED_INPUT_READ_VALIDATE(self)
            return admission
        except BaseException as error:
            _clear_selected_input_rejection_frames(error)
            if record is not None:
                _retire_selected_input_read(record)
            raise
        finally:
            record = originals = consumer = admission = self = None  # noqa: PLW0642 - clear rejection custody
            operation = resolution = fulfillment = body = None

    def assemble_inputs(
        self, semantic_input, input_bodies, *, source_input_roles=(),
        context_input_roles=(), dependency_input_role=None,
    ):
        """Construct the shared value from the complete node-retained closure."""
        record = assembly = sources = fields = binding = None
        try:
            _SELECTED_INPUT_READ_VALIDATE(self)
            record = _selected_input_read_record(self)
            if record.assembly_binding is not None:
                raise RuntimeError("selected-input assembly replay")
            if not record.results or len(record.results) != len(record.expectations):
                raise RuntimeError("selected-input source-result closure incomplete")
            _selected_input_slots(_INPUT_ASSEMBLY_KIND, _INPUT_ASSEMBLY_FIELDS, _INPUT_ASSEMBLY_SLOTS)
            _selected_input_slots(_INPUT_SOURCE_KIND, _INPUT_SOURCE_FIELDS, _INPUT_SOURCE_SLOTS)
            sources = tuple(_INPUT_SOURCE_KIND(host, registration, record.selected, expected, result)
                            for host, registration, expected, result in record.results)
            assembly = _INPUT_ASSEMBLY_KIND(
                semantic_input, input_bodies, sources,
                source_input_roles=source_input_roles, context_input_roles=context_input_roles,
                dependency_products=(None if record.dependency_binding is None
                                     else record.dependency_binding.admission),
                dependency_input_role=dependency_input_role,
            )
            fields = tuple(slot.__get__(assembly) for slot in _INPUT_ASSEMBLY_SLOTS)
            binding = _SelectedInputAssemblyBinding(
                assembly, fields,
                tuple((source, tuple(slot.__get__(source) for slot in _INPUT_SOURCE_SLOTS))
                      for source in sources),
                ((fields[3], tuple(row for row in fields[3])),
                 (fields[4], tuple(row for row in fields[4]))),
            )
            record.assembly_binding = binding
            _SELECTED_INPUT_READ_VALIDATE(self)
            return assembly
        except BaseException as error:
            _clear_selected_input_rejection_frames(error)
            if record is not None:
                _retire_selected_input_read(record)
            raise
        finally:
            record = assembly = sources = fields = binding = self = None  # noqa: PLW0642 - clear rejection custody
            semantic_input = input_bodies = source_input_roles = context_input_roles = dependency_input_role = None

    def close(self) -> None:
        record = None
        try:
            if os.getpid() != _SELECTED_INPUT_NODES_PID:
                raise RuntimeError("selected-input read belongs to another process")
            # Identity lookup precedes class checks; restamping cannot evade release.
            with _SELECTED_INPUT_NODES_LOCK:
                record = next(
                    (item for key, item in _SELECTED_INPUT_NODES if key() is self), None
                )
            if record is not None:
                _retire_selected_input_read(record)
        finally:
            record = self = None  # noqa: PLW0642 - clear rejection custody


_SELECTED_INPUT_READ_VALIDATE = _CommandOwnedSelectedInputReadSession.validate
_SELECTED_INPUT_READ_CLOSE = _CommandOwnedSelectedInputReadSession.close


@contextmanager
def _command_owned_selected_input_read_session(
    command,
    *,
    host,
    selected_source,
    registration,
) -> Iterator[_CommandOwnedSelectedInputReadSession]:
    """One additive read per original command; no public inspect entrance."""
    node = record = factory = contribution = staged = item = cleanup = None
    try:
        if os.getpid() != _SELECTED_INPUT_NODES_PID:
            raise RuntimeError("selected-input read belongs to another process")
        _require_live_direct_workspace_command(command)
        if type(command.sources) is not _DirectWorkspaceDeclarationSources:
            raise RuntimeError("original declaration source required for read")
        staged = _selected_input_identity_lookup(_POLICY_HOSTS, host)
        factory = _selected_input_identity_lookup(_SELECTED_INPUT_FACTORIES, host)
        if staged is None or staged.command is not command or factory is None:
            raise RuntimeError("original selected read host required")
        for item in staged.product_contributions:
            if (
                read_selected_provider_product_contribution(item).expected.registration
                is registration
            ):
                contribution = item
                break
        if contribution is None:
            raise RuntimeError("original selected product registration required")
        record = _SelectedInputReadRecord(
            command,
            host,
            factory,
            selected_source,
            contribution,
            registration,
            factory._epoch,
            factory._epoch_expected,
            current_thread(),
            ExitStack(),
        )
        _validate_selected_input_read_record(record)
        node = object.__new__(_CommandOwnedSelectedInputReadSession)
        with command.sources.exclusion.mutation(), _SELECTED_INPUT_NODES_LOCK:
            if any(item.command is command for _, item in _SELECTED_INPUT_NODES):
                raise RuntimeError("command already has an active selected-input read")
            _SELECTED_INPUT_NODES.append((ref(node), record))
        cleanup = finalize(node, _retire_selected_input_read, record)
        try:
            yield node
        finally:
            try:
                _SELECTED_INPUT_READ_CLOSE(node)
            finally:
                cleanup.detach()
    finally:
        node = record = factory = contribution = staged = item = cleanup = None
        command = host = selected_source = registration = None


@dataclass(frozen=True, slots=True)
class _DirectWorkspaceStagedCommandResources:
    """Owned Code contribution plus original Workspace resources; no host admission."""

    command: _DirectWorkspaceCommandResources
    contribution: SelectedProviderStageContribution
    stage_runtime_bindings: tuple[
        RetainedSemanticStageRuntimeExpectation,
        RetainedSemanticStageRuntimeExpectation,
    ]
    product_contributions: tuple[SelectedProviderProductContribution, ...] = ()
    product_runtime_bindings: tuple[RetainedSemanticProductRuntimeExpectation, ...] = ()


@dataclass(frozen=True, slots=True)
class DirectWorkspaceSelectedHost:
    """One original command, paired catalog, and Code host in one lifetime."""

    staged: _DirectWorkspaceStagedCommandResources
    catalog_pair: object
    code_host: object


@contextmanager
def compose_direct_workspace_selected_host(
    *,
    factory_admission: _AdmittedSemanticProviderFactory,
    session: WorkspaceRepositoryObservationSession,
    store: WorkspaceRepositoryDeltaRetentionClient,
    workspace_manifest_path: str,
    composition_implementation,
    composition_configuration,
    policy_implementation,
    policy_configuration,
    product_factory_admissions: tuple[_AdmittedSemanticProviderFactory, ...] = (),
    command_resources: _DirectWorkspaceCommandResources | None = None,
) -> Iterator[DirectWorkspaceSelectedHost]:
    """Enter the existing selected catalog and Code host under one command.

    Factory and bootstrap coordinates must come from the installed application
    composition, never from a materialization proposal. This entrance does not
    issue them or interpret provider meaning. When original command resources
    are supplied, their parent stays borrowed and must outlive this host.
    """
    with _compose_direct_workspace_staged_command_resources(
        factory_admission=factory_admission,
        product_factory_admissions=product_factory_admissions,
        session=session,
        store=store,
        workspace_manifest_path=workspace_manifest_path,
        source_rail="declaration_v3",
        command_resources=command_resources,
    ) as staged:
        pair = _admit_direct_workspace_selected_provider_catalogs(staged)
        with _compose_direct_workspace_policy_host(
            staged,
            composition_implementation=composition_implementation,
            composition_configuration=composition_configuration,
            policy_implementation=policy_implementation,
            policy_configuration=policy_configuration,
        ) as code_host:
            yield DirectWorkspaceSelectedHost(staged, pair, code_host)


@contextmanager
def _compose_direct_workspace_staged_command_resources(
    *,
    factory_admission: _AdmittedSemanticProviderFactory,
    product_factory_admissions: tuple[_AdmittedSemanticProviderFactory, ...] = (),
    session: WorkspaceRepositoryObservationSession,
    store: WorkspaceRepositoryDeltaRetentionClient,
    workspace_manifest_path: str,
    qualified: bool = False,
    source_rail: str = "existing",
    command_resources: _DirectWorkspaceCommandResources | None = None,
) -> Iterator[_DirectWorkspaceStagedCommandResources]:
    """Acquire only through original Code factory authority, never a callback.

    Code rolls back partial acquisition. After success this assembly owns both
    registrations. After yielded host cleanup, close those registrations before
    the command parent and source resources. No execution is mounted here;
    this construction envelope is not the later live-operation quiescence join.
    """
    if command_resources is not None:
        _require_live_direct_workspace_command(command_resources)
        if command_resources.lifetime_runtime in _STAGED_ASSEMBLIES:
            raise RuntimeError("original command already has a selected host")
        sources = command_resources.sources
        if (
            source_rail != "declaration_v3"
            or qualified
            or type(sources) is not _DirectWorkspaceDeclarationSources
        ):
            raise TypeError("borrowed command requires its original v3 source")
        if (
            sources.observation_runtime._session is not session
            or sources.observation_runtime._store is not store
            or sources.declaration_scope_runtime.read_declaration_scope(
                sources.declaration_scope
            ).consumer_scope_key != workspace_manifest_path
        ):
            raise RuntimeError("borrowed command source resources differ")
    if type(product_factory_admissions) is not tuple or len(product_factory_admissions) > 4096:
        raise TypeError("bounded original product factory tuple required")
    if len({id(item) for item in product_factory_admissions}) != len(product_factory_admissions):
        raise ValueError("duplicate original product factory")
    contribution = issue_selected_provider_stage_contribution(factory_admission)
    close_contribution = close_selected_provider_stage_contribution
    products: list[SelectedProviderProductContribution] = []
    errors: list[BaseException] = []
    cleanup_attempted = False
    try:
        for product_factory in product_factory_admissions:
            products.append(issue_selected_provider_product_contribution(product_factory))
        command_context = (
            nullcontext(command_resources)
            if command_resources is not None
            else _compose_direct_workspace_command_resources(
                session=session,
                store=store,
                workspace_manifest_path=workspace_manifest_path,
                qualified=qualified,
                source_rail=source_rail,
            )
        )
        with command_context as command:
            _require_live_direct_workspace_command(command)
            try:
                stages = read_selected_provider_stage_contribution(contribution)
                product_bindings = tuple(
                    read_selected_provider_product_contribution(product).expected
                    for product in products
                )
                resources = _DirectWorkspaceStagedCommandResources(
                    command, contribution, stages, tuple(products), product_bindings
                )
                _STAGED_ASSEMBLIES[command.lifetime_runtime] = (
                    resources,
                    _resource_references(resources),
                )
                try:
                    yield resources
                finally:
                    _STAGED_ASSEMBLIES.pop(command.lifetime_runtime, None)
            finally:
                cleanup_attempted = True
                for product in reversed(products):
                    try:
                        close_selected_provider_product_contribution(product)
                    except BaseException as error:
                        errors.append(error)
                try:
                    close_contribution(contribution)
                except BaseException as error:
                    errors.append(error)
    except BaseException as error:
        errors.append(error)
    if not cleanup_attempted:
        for product in reversed(products):
            try:
                close_selected_provider_product_contribution(product)
            except BaseException as error:
                errors.append(error)
        try:
            close_contribution(contribution)
        except BaseException as error:
            errors.append(error)
    if len(errors) == 1:
        raise errors[0]
    if errors:
        raise BaseExceptionGroup("Workspace staged command/unwind failed", errors)


def _admit_direct_workspace_selected_provider_catalogs(
    staged: _DirectWorkspaceStagedCommandResources,
):
    """Admit only owner-produced Code inputs through this command's paired host."""
    if type(staged) is not _DirectWorkspaceStagedCommandResources:
        raise TypeError("original staged command required")
    command = staged.command
    if type(command) is not _DirectWorkspaceCommandResources:
        raise TypeError("original command resources required")
    owner = command.lifetime_runtime
    command_record = _COMMAND_ASSEMBLIES.get(owner)
    staged_record = _STAGED_ASSEMBLIES.get(owner)
    if (
        command_record is None
        or staged_record is None
        or command_record[0] is not command
        or staged_record[0] is not staged
        or not _same_references(command_record[1], _resource_references(command))
        or not _same_references(command_record[2], _resource_references(command.sources))
        or not _same_references(staged_record[1], _resource_references(staged))
    ):
        raise RuntimeError("original staged catalog command unavailable")
    command.sources.exclusion.check_live()
    stages = read_selected_provider_stage_contribution(staged.contribution)
    if any(
        current.runtime is not retained.runtime
        or current.registration is not retained.registration
        for current, retained in zip(stages, staged.stage_runtime_bindings, strict=True)
    ):
        raise RuntimeError("original stage catalog registration changed")
    products = tuple(
        read_selected_provider_product_contribution(value).expected
        for value in staged.product_contributions
    )
    if len(products) != len(staged.product_runtime_bindings) or any(
        current.runtime is not retained.runtime
        or current.registration is not retained.registration
        for current, retained in zip(products, staged.product_runtime_bindings, strict=True)
    ):
        raise RuntimeError("original product catalog registration changed")

    produce_selected_provider_stage_catalog_contribution(staged.contribution)
    for product in staged.product_contributions:
        produce_selected_provider_product_catalog_contribution(product)
    code_catalog = compose_selected_provider_stage_catalog_input(
        (staged.contribution,),
        catalog_ref="workspace.direct.selected-providers.v1",
        catalog_generation=1,
        product_contributions=staged.product_contributions,
    )
    owner_catalogs = (
        read_selected_provider_stage_catalog_contribution(staged.contribution),
        *(
            read_selected_provider_product_catalog_contribution(value)
            for value in staged.product_contributions
        ),
    )
    executables = tuple(
        executable
        for value in owner_catalogs
        for executable in value.executables
    )
    planners = {}
    for value in owner_catalogs:
        for entry in value.entries:
            coordinate = (
                entry.dependency_planner_implementation,
                entry.dependency_planner_configuration,
            )
            previous = planners.setdefault(coordinate, value.planner)
            if previous is not value.planner:
                raise RuntimeError("different owner planners share one coordinate")
    workspace_catalog = WorkspaceSemanticMaterializationMembershipCatalog.create(
        catalog_ref="workspace.direct.initial-membership.v1",
        catalog_generation=1,
        entries=(),
    )
    return command.catalog_host.admit_catalogs(
        code_catalog=code_catalog,
        workspace_catalog_reader=lambda: workspace_catalog,
        provider_executable_bindings=executables,
        dependency_planner_bindings=tuple(
            (implementation, configuration, planner)
            for (implementation, configuration), planner in planners.items()
        ),
    )


class _DirectWorkspaceOriginFactory:
    """Original-resource product factory, not bootstrap authentication.

    Only the internal assembler constructs this value. Code still authenticates
    the assembly and checks the original live stage/catalog correspondence.
    """

    _entrances: Any
    _owner: Any
    _expected: Any
    _used: bool
    _lifetime: Any
    _contribution: Any
    _stages: Any
    _scope_adapter: Any
    _scope_snapshot: Any
    _joint: Any
    _epoch: Any
    _epoch_expected: Any
    _command: Any
    _private_reads: Any

    def prepare_selected_owner_lifetime(self, operation_use, registration) -> None:
        try:
            _require_installed_selected_owner_inlet()
        finally:
            del self, operation_use, registration

    def retain_selected_owner_completion(self, operation_use, registration, completion) -> None:
        try:
            _require_installed_selected_owner_inlet()
        finally:
            del self, operation_use, registration, completion

    def abort_selected_owner_lifetime(self, operation_use) -> None:
        try:
            _require_installed_selected_owner_inlet()
        finally:
            del self, operation_use

    def __new__(cls):
        raise TypeError("original Workspace assembly required")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("Workspace origin factory is final")

    def __reduce__(self):
        raise TypeError("Workspace origin factory is process-local")

    def _call(self, key, *args, **kwargs):
        receiver, name, descriptor, method = self._entrances[key]
        if inspect.getattr_static(receiver, name) is not descriptor:
            raise RuntimeError("original factory dependency substituted")
        result = method(*args, **kwargs)
        if inspect.getattr_static(receiver, name) is not descriptor:
            raise RuntimeError("original factory dependency substituted")
        return result

    def _selected_graph_node_record(self, node_use):
        if (
            type(self) is not _DirectWorkspaceOriginFactory
            or self not in _ORIGIN_FACTORIES
            or type(node_use) is not _CommandOwnedGraphNodeSourceSession
        ):
            raise RuntimeError("original fixed graph-node use required")
        with _COMMAND_NODE_SESSIONS_LOCK:
            record = _COMMAND_NODE_SESSIONS.get(node_use)
        if (
            record is None
            or not record.live
            or record.command is not self._command
            or record.process_id != os.getpid()
            or record.thread_id != get_ident()
            or self._command.lifetime_runtime is not self._owner
            or self._command.catalog_host is not self._joint
        ):
            raise RuntimeError("foreign or retired fixed graph-node use")
        return record

    def validate_selected_input_node_use(self, operation_context, *, assembly=None, closure=None):
        """Validate the retained association outside parent exclusion."""
        record = None
        try:
            record = _selected_input_read_record(operation_context)
            if (
                type(self) is not _DirectWorkspaceOriginFactory
                or self not in _ORIGIN_FACTORIES
                or record.factory is not self
            ):
                raise RuntimeError("original selected-input factory required")
            if assembly is not None or closure is not None:
                if record.assembly_binding is None:
                    raise RuntimeError("selected_input_invocation_binding_unavailable")
                record.full_checkpoints += 1
                if record.full_checkpoints > 32:
                    raise RuntimeError("selected-input full checkpoint limit exceeded")
                record.assembly_binding.check(record, assembly=assembly, closure=closure)
            _SELECTED_INPUT_READ_VALIDATE(operation_context)
            if closure is not None:
                record.closure = closure
        except BaseException as error:
            _clear_selected_input_rejection_frames(error)
            if record is not None:
                _retire_selected_input_read(record)
            raise
        finally:
            record = self = operation_context = assembly = closure = None  # noqa: PLW0642 - clear rejection custody

    def check_selected_input_node_use_locked(self, operation_context):
        """Identity-only local check under the existing held parent exclusion."""
        record = None
        try:
            record = _selected_input_read_record(operation_context)
            if (
                type(self) is not _DirectWorkspaceOriginFactory
                or self not in _ORIGIN_FACTORIES
                or type(operation_context) is not _CommandOwnedSelectedInputReadSession
                or record.factory is not self
                or record.thread is not current_thread()
                or not record.thread.is_alive()
                or record.command is not self._command
                or _SELECTED_INPUT_FACTORIES.get(record.host) is not self
                or _POLICY_HOSTS.get(record.host) is None
                or record.epoch is not self._epoch
                or record.epoch_expected is not self._epoch_expected
            ):
                raise RuntimeError("selected-input read origin changed")
            self._command.sources.exclusion.check_locked(self._owner._guard)
            command_record = _COMMAND_ASSEMBLIES.get(self._owner)
            if (
                command_record is None or command_record[0] is not record.command
                or not _same_references(command_record[1], _resource_references(record.command))
                or not _same_references(command_record[2], _resource_references(record.command.sources))
            ):
                raise RuntimeError("selected-input command retired")
            parent = self._joint._command_parent
            if parent is None or parent.records._read_current(
                self._owner._guard, expected=record.epoch_expected,
            ).preparation is not record.epoch:
                raise RuntimeError("selected-input catalog pair changed")
            if record.assembly_binding is not None:
                record.assembly_binding.check(record, closure=record.closure)
        except BaseException as error:
            _clear_selected_input_rejection_frames(error)
            if record is not None:
                # Retire in place. Context exit performs disposal outside this guard.
                record.live = False
            raise
        finally:
            record = self = operation_context = None  # noqa: PLW0642 - clear rejection custody
            parent = command_record = None

    def validate_selected_graph_node_use(self, node_use, *, closure=None):
        """Revalidate original node/source and the exact resolved invocation."""
        from aware_code_semantic_contract_runtime.selected_provider import (
            SelectedProviderInvocationClosure,
        )

        record = self._selected_graph_node_record(node_use)
        node_use.validate()
        if closure is not None:
            if type(closure) is not SelectedProviderInvocationClosure:
                raise TypeError("exact selected graph-product closure required")
            closure.__post_init__()
            plan = record.execution_plan
            if (
                plan is None
                or closure.invocation is not plan.invocation
                or closure.input_bodies is not plan.input_bodies
                or closure.predecessor_body is not plan.predecessor_body
                or closure.input_values is not None
            ):
                raise RuntimeError("selected closure differs from original node plan")
            plan.__post_init__()
            node_use.validate()
        self._selected_graph_node_record(node_use)

    def check_selected_graph_node_use_locked(self, node_use):
        """Check only retained identities under Code's held parent exclusion."""
        record = self._selected_graph_node_record(node_use)
        owner = self._owner
        self._command.sources.exclusion.check_locked(owner._guard)
        command_record = _COMMAND_ASSEMBLIES.get(owner)
        if (
            command_record is None
            or command_record[0] is not self._command
            or not _same_references(
                command_record[1], _resource_references(self._command)
            )
            or not _same_references(
                command_record[2], _resource_references(self._command.sources)
            )
        ):
            raise RuntimeError("original fixed graph-node command retired")
        from .materialization_operation import _graph_node_admission_state

        if _graph_node_admission_state(record.node_admission).owner is not owner:
            raise RuntimeError("original graph-node owner changed")
        if type(record.source_admission) is _SuccessorGraphNodeSourceInputs:
            value = record.source_admission
            if (
                _POLICY_HOSTS.get(value.code_host) is not value.staged
                or value.staged.command is not self._command
            ):
                raise RuntimeError("successor graph source composition changed")
            joint = self._command.catalog_host
            parent = joint._command_parent
            if parent is None:
                raise RuntimeError("successor graph catalog parent unavailable")
            current = parent.records._read_current(
                owner._guard, expected=value.expected_epoch
            )
            if (
                current.preparation is not value.epoch
                or current.attempt.predecessor is None
                or current.transfer is None
                or current.attempt.pair[0] is not joint._code_leg
                or current.attempt.pair[1] is not joint._workspace_admission
            ):
                raise RuntimeError("successor graph catalog pair changed")

    def _private_stage_read_runtime(self):
        from .private_stage_read_admission import (
            _RUNTIMES,
            _WorkspacePrivateStageReadRuntime,
        )

        if type(self) is not _DirectWorkspaceOriginFactory or self not in _ORIGIN_FACTORIES:
            raise RuntimeError("original fixed Workspace factory required")
        runtime = inspect.getattr_static(self, "_private_reads", None)
        if type(runtime) is not _WorkspacePrivateStageReadRuntime:
            raise RuntimeError("original Workspace private-read runtime required")
        state = _RUNTIMES.get(runtime)
        if state is None or state.factory() is not self:
            raise RuntimeError("Workspace private-read runtime substituted")
        return runtime

    def validate_private_stage_input_use(self, operation_use, semantic_input) -> None:
        return self._private_stage_read_runtime().validate(operation_use, semantic_input)

    def check_private_stage_input_use_locked(self, operation_use, semantic_input) -> None:
        return self._private_stage_read_runtime().check_locked(
            operation_use, semantic_input, self._owner._guard
        )

    def prepare_private_stage_read_input(self, operation_use, semantic_input) -> None:
        return self._private_stage_read_runtime().prepare(operation_use, semantic_input)

    def spend_private_stage_read_input_locked(self, operation_use, semantic_input, guard) -> None:
        return self._private_stage_read_runtime().spend_locked(
            operation_use, semantic_input, guard
        )

    def abort_private_stage_read_input(self, operation_use) -> None:
        return self._private_stage_read_runtime().abort(operation_use)

    def create_direct_semantic_origin(self, lifetime):
        from aware_code_semantic_contract_runtime.direct_origin_interfaces import (
            DirectWorkspaceOriginProduct,
        )

        if self not in _ORIGIN_FACTORIES:
            raise RuntimeError("foreign Workspace origin factory")
        self._call("lifetime", lifetime, expected=self._expected)
        # A failed attempt consumes this factory entrance too; Code separately
        # consumes its bootstrap registration. Neither can be replayed.
        with self._owner._lock:
            if self._used or lifetime is not self._lifetime:
                raise RuntimeError("original origin lifetime unavailable or consumed")
            self._used = True
        stages = read_selected_provider_stage_contribution(self._contribution)
        for current, retained in zip(stages, self._stages, strict=True):
            if (
                current.runtime is not retained.runtime
                or current.registration is not retained.registration
            ):
                raise RuntimeError("original stage contribution changed")
        for contribution, retained in zip(
            self._product_contributions, self._products, strict=True
        ):
            current = read_selected_provider_product_contribution(contribution).expected
            if (
                current.runtime is not retained.runtime
                or current.registration is not retained.registration
            ):
                raise RuntimeError("original product contribution changed")
        if self._expected.source_rail == "declaration_v3":
            self._call(
                "scope", self._scope_snapshot,
                expectation=self._declaration_expectation,
                closure_digest=self._declaration_digest,
            )
        else:
            self._call("scope", self._scope_snapshot)
        self._call("epoch", self._epoch, expected=self._epoch_expected)
        if (
            self._call("catalog", self._epoch, expected=self._epoch_expected)
            is not self._expected.catalog
        ):
            raise RuntimeError("original catalog changed")
        self._call("lifetime", lifetime, expected=self._expected)
        return DirectWorkspaceOriginProduct(lifetime, self._expected)


def _assemble_direct_workspace_origin_factory(
    staged,
    *,
    composition_implementation,
    composition_configuration,
    policy_implementation,
    policy_configuration,
):
    """Derive resource references mechanically; supplied coordinates confer no trust.

    A future fixed bootstrap supplies authenticated implementation/configuration
    coordinates. No CLI, factory callback or ready-made resource context is accepted.
    This internal product cannot authenticate its caller or installed bytes.
    """
    if type(staged) is not _DirectWorkspaceStagedCommandResources:
        raise TypeError("original staged command required")
    command = staged.command
    if type(command) is not _DirectWorkspaceCommandResources:
        raise TypeError("original command resources required")
    declaration_v3 = type(command.sources) is _DirectWorkspaceDeclarationSources
    if not declaration_v3 and type(command.sources) is not _DirectWorkspaceSourceResources:
        raise RuntimeError("original command source resources required")
    from aware_code_semantic_contract_runtime.direct_origin_interfaces import (
        DECLARATION_V3_TWO_STAGE_RESOURCE_ROLES,
        TWO_STAGE_RESOURCE_ROLES,
        DirectCommandExpectedContext,
        DirectCommandResourceBinding,
    )
    command_record = _COMMAND_ASSEMBLIES.get(command.lifetime_runtime)
    staged_record = _STAGED_ASSEMBLIES.get(command.lifetime_runtime)
    if (
        command_record is None
        or staged_record is None
        or command_record[0] is not command
        or staged_record[0] is not staged
        or not _same_references(command_record[1], _resource_references(command))
        or not _same_references(
            command_record[2], _resource_references(command.sources)
        )
        or not _same_references(staged_record[1], _resource_references(staged))
    ):
        raise RuntimeError("foreign, substituted or retired fixed assembly")
    from aware_code_retained_registry_policy_runtime.calculation import (
        calculate_registry_policy,
    )
    stages = read_selected_provider_stage_contribution(staged.contribution)
    for current, retained in zip(stages, staged.stage_runtime_bindings, strict=True):
        if (
            current.runtime is not retained.runtime
            or current.registration is not retained.registration
        ):
            raise RuntimeError("substituted staged command")
    products = tuple(
        read_selected_provider_product_contribution(product).expected
        for product in staged.product_contributions
    )
    if len(products) != len(staged.product_runtime_bindings) or any(
        current.runtime is not retained.runtime
        or current.registration is not retained.registration
        for current, retained in zip(products, staged.product_runtime_bindings, strict=True)
    ):
        raise RuntimeError("substituted product contribution")
    owner, sources, joint = (
        command.lifetime_runtime,
        command.sources,
        command.catalog_host,
    )
    epoch_expected = joint.read_initial_publication()
    owner.validate_direct_invocation_parent(
        command.invocation_parent, expected=epoch_expected.invocation
    )
    if (
        joint._command_parent is None
        or joint._command_parent.owner is not owner
        or joint._command_parent.parent is not command.invocation_parent
    ):
        raise RuntimeError("foreign command catalog parent")
    epoch = joint.read_initial_epoch()
    catalog = joint.read_code_catalog_for_epoch(epoch, expected=epoch_expected)
    qualified = not declaration_v3 and type(sources.scope_runtime) is WorkspaceDependencyScopeRuntime
    if declaration_v3:
        scope_method = "validate_declaration_scope"
        scope_receiver = sources.declaration_scope_runtime
        scope_snapshot = sources.declaration_scope
        closure = scope_receiver.read_declaration_scope(scope_snapshot)
        scope_receiver.validate_declaration_scope(
            scope_snapshot, expectation=sources.expectation,
            closure_digest=closure.closure_digest,
        )
        from aware_code_retained_registry_policy_runtime.declaration_eligibility import (
            calculate_declaration_eligibility,
        )

        policy_producer = calculate_declaration_eligibility
    else:
        scope_method = (
            "read_preliminary_dependency_scope_projection"
            if qualified else "validate_complete_scope_projection"
        )
        scope_receiver = sources.scope_adapter
        scope_snapshot = sources.scope_snapshot
        getattr(scope_receiver, scope_method)(scope_snapshot)
    if qualified:
        from aware_code_retained_registry_policy_runtime.qualified_calculation import (
            calculate_qualified_registry_policy,
        )

        policy_producer = calculate_qualified_registry_policy
    elif not declaration_v3:
        policy_producer = calculate_registry_policy
    factory = object.__new__(_DirectWorkspaceOriginFactory)
    objects = dict(
        authority_code_runtime=stages[1].runtime,
        catalog=catalog,
        code_runtime=stages[0].runtime,
        composition_factory=factory,
        lifetime_runtime=owner,
        policy_producer=policy_producer,
    )
    if declaration_v3:
        objects["declaration_scope_runtime"] = sources.declaration_scope_runtime
    else:
        objects.update(
            membership_runtime=sources.membership_runtime,
            observation_runtime=sources.observation_runtime,
            repository_store=sources.observation_runtime._store,
            scope_adapter=sources.scope_adapter,
            scope_runtime=sources.scope_runtime,
            semantic_issuer=sources.semantic_issuer,
        )
    # Ownership remains with the enclosing source/stage envelopes. This factory
    # borrows every resource and never invents a runtime close method.
    expected = DirectCommandExpectedContext(
        owner.invocation_identity,
        owner.epoch_identity,
        os.getpid(),
        stages[0].runtime,
        catalog,
        composition_implementation,
        composition_configuration,
        policy_implementation,
        policy_configuration,
        tuple(
            DirectCommandResourceBinding(role, objects[role], "borrowed")
            for role in (
                DECLARATION_V3_TWO_STAGE_RESOURCE_ROLES
                if declaration_v3 else TWO_STAGE_RESOURCE_ROLES
            )
        ),
        stages,
        source_rail="declaration_v3" if declaration_v3 else "existing",
        product_runtime_bindings=products,
    )
    factory._owner, factory._expected = owner, expected
    factory._command = command
    factory._contribution, factory._stages = staged.contribution, stages
    factory._product_contributions, factory._products = (
        staged.product_contributions, products
    )
    factory._scope_adapter, factory._scope_snapshot = scope_receiver, scope_snapshot
    factory._declaration_expectation = sources.expectation if declaration_v3 else None
    factory._declaration_digest = closure.closure_digest if declaration_v3 else None
    factory._joint, factory._epoch, factory._epoch_expected = (
        joint,
        epoch,
        epoch_expected,
    )
    factory._entrances = {}
    for key, receiver, name in (
        ("lifetime", owner, "validate_command_lifetime"),
        ("scope", scope_receiver, scope_method),
        ("epoch", joint, "validate_current_catalog_epoch"),
        ("catalog", joint, "read_code_catalog_for_epoch"),
    ):
        descriptor = inspect.getattr_static(receiver, name)
        method = getattr(receiver, name)
        if (
            not inspect.ismethod(method)
            or method.__self__ is not receiver
            or method.__func__ is not descriptor
        ):
            raise RuntimeError("original factory dependency required")
        factory._entrances[key] = receiver, name, descriptor, method
    factory._used = False
    factory._lifetime = owner.bind_command_lifetime(expected=expected)
    _ORIGIN_FACTORIES.add(factory)
    from .private_stage_read_admission import _assemble_private_stage_read_runtime

    factory._private_reads = _assemble_private_stage_read_runtime(factory)
    return factory


@contextmanager
def _compose_direct_workspace_policy_host(staged, **coordinates):
    """Own Code host/participant cleanup inside the existing staged envelope.

    Fixed internal call site only. Coordinates still require original bootstrap
    provenance; this source composition does not authenticate installed bytes.
    """
    from aware_code_retained_registry_policy_runtime import (
        authority_operation_context as authority_contexts,
    )
    from aware_code_retained_registry_policy_runtime import (
        dependency_operation_validator as dependency_contexts,
    )
    from aware_code_retained_registry_policy_runtime import direct_host as code
    from aware_code_retained_registry_policy_runtime import (
        operation_context as planning_contexts,
    )
    from aware_code_retained_registry_policy_runtime.declaration_host import (
        _prepare_declaration_source,
    )
    from aware_code_retained_registry_policy_runtime.direct_epoch_tracking import (
        _bind_direct_policy_epoch,
    )
    from aware_code_retained_registry_policy_runtime.epoch_participation import (
        _assemble_code_epoch_participation,
    )
    from aware_code_retained_registry_policy_runtime.qualified_host import (
        _qualified_dependency_validator,
    )
    from aware_code_retained_registry_policy_runtime.target_context import (
        assemble_target_context_origin,
    )

    factory = _assemble_direct_workspace_origin_factory(staged, **coordinates)
    bootstrap = code._assemble_direct_command_bootstrap(
        lifetime=factory._lifetime, expected=factory._expected
    )
    host = code.register_direct_workspace_origin(bootstrap, factory._lifetime)
    close_code = code.close_direct_validation_host
    command = staged.command
    owner, joint = command.lifetime_runtime, command.catalog_host
    participant = None
    declaration_v3 = type(command.sources) is _DirectWorkspaceDeclarationSources
    prepared_declaration = None
    expected = None
    epoch_bound = False
    code_closed = False
    errors = []
    try:
        if declaration_v3:
            prepared_declaration = _prepare_declaration_source(
                host, command.sources.declaration_scope, command.sources.expectation
            )
        expected = joint.read_initial_publication()
        epoch = joint.read_initial_epoch()
        guard = owner.acquire_catalog_epoch_exclusion(
            command.invocation_parent, expected=expected.invocation
        )
        try:
            participant = _assemble_code_epoch_participation(
                owner=owner,
                parent=command.invocation_parent,
                invocation=expected.invocation,
                epoch_owner=joint,
                guard=guard,
            )
            kwargs = (
                {"declaration_source": prepared_declaration}
                if declaration_v3 else (
                    {"dependency_source": command.sources.scope_snapshot}
                    if type(command.sources.scope_runtime)
                    is WorkspaceDependencyScopeRuntime else {}
                )
            )
            _bind_direct_policy_epoch(
                host, participant, epoch, expected=expected, guard=guard, **kwargs
            )
            epoch_bound = True
        finally:
            owner.release_catalog_epoch_exclusion(guard)
        if not declaration_v3 and type(command.sources.scope_runtime) is WorkspaceDependencyScopeRuntime:
            _install_operation_origin(
                command.sources.scope_runtime,
                validator=_qualified_dependency_validator(host),
                epoch=epoch,
            )
        issuer = (
            command.sources.declaration_scope_runtime if declaration_v3
            else command.sources.semantic_issuer
        )
        issuer._bind_original_code_validator(
            planning_contexts.source_planning_context_validator(host)
        )
        issuer._bind_original_authority_validator(
            authority_contexts.authority_context_validator(host)
        )
        if declaration_v3 or type(command.sources.scope_runtime) is WorkspaceDependencyScopeRuntime:
            issuer._bind_original_dependency_validator(
                dependency_contexts.retained_dependency_operation_validator(host)
            )
        if declaration_v3 or type(command.sources.scope_runtime) is WorkspaceDependencyScopeRuntime:
            issuer._bind_original_resolution_resources(
                target_origin=assemble_target_context_origin(host),
                catalog=joint.read_code_catalog_for_epoch(epoch, expected=expected),
            )
        _POLICY_HOSTS[host] = staged
        _SELECTED_INPUT_FACTORIES[host] = factory
        yield host
    except BaseException as error:
        errors.append(error)
    finally:
        try:
            _retire_selected_input_reads_for_host(host)
        except BaseException as error:  # noqa: BLE001 - independently close borrowed Code host
            errors.append(error)
        _POLICY_HOSTS.pop(host, None)
        _SELECTED_INPUT_FACTORIES.pop(host, None)
        try:
            close_code(host)
            code_closed = True
        except BaseException as error:
            errors.append(error)
        try:
            factory._private_stage_read_runtime().close()
        except BaseException as error:
            errors.append(error)
        if (
            participant is not None
            and expected is not None
            and not (epoch_bound and code_closed)
        ):
            try:
                guard = owner.acquire_catalog_epoch_exclusion(
                    command.invocation_parent, expected=expected.invocation
                )
                try:
                    participant._close_under_exclusion(guard)
                finally:
                    owner.release_catalog_epoch_exclusion(guard)
            except BaseException as error:
                errors.append(error)
    if len(errors) == 1:
        raise errors[0]
    if errors:
        raise BaseExceptionGroup("Workspace Code host/unwind failed", errors)


def _compose_direct_workspace_current_graph_planner(
    staged,
    code_host,
    *,
    epoch,
    expected_epoch,
    original_sources,
    package_closure,
    backing,
    selected_sources=None,
    source_correspondences=(),
    selection=None,
    bound_roots=None,
    root_plans=None,
):
    """Pass only this fixed command's original host and pair to neutral graph.

    This is a composition check, not another graph planner or host issuer.
    Code validates the returned owner sources inside the neutral entrance.
    """
    from .materialization_graph_host_composition import (
        compose_current_workspace_graph_planner,
    )
    if type(staged) is not _DirectWorkspaceStagedCommandResources:
        raise TypeError("original staged Workspace command required")
    command = staged.command
    if type(command) is not _DirectWorkspaceCommandResources:
        raise RuntimeError("original command resources required")
    owner = command.lifetime_runtime
    command_record = _COMMAND_ASSEMBLIES.get(owner)
    staged_record = _STAGED_ASSEMBLIES.get(owner)

    def validate_originals():
        if (
            _COMMAND_ASSEMBLIES.get(owner) is not command_record
            or _STAGED_ASSEMBLIES.get(owner) is not staged_record
            or command_record is None
            or staged_record is None
            or command_record[0] is not command
            or staged_record[0] is not staged
            or not _same_references(
                command_record[1], _resource_references(command)
            )
            or not _same_references(
                command_record[2], _resource_references(command.sources)
            )
            or not _same_references(
                staged_record[1], _resource_references(staged)
            )
            or _POLICY_HOSTS.get(code_host) is not staged
            or type(command.sources) is not _DirectWorkspaceDeclarationSources
        ):
            raise RuntimeError("original v3 Code/Workspace graph host unavailable")
        command.sources.exclusion.check_live()

    validate_originals()
    if any(value is None for value in (selection, bound_roots, root_plans)):
        raise RuntimeError("complete original root-plan closure required")
    _validate_direct_workspace_root_plan_closure(
        command,
        selection=selection,
        bound_roots=bound_roots,
        root_plans=root_plans,
    )
    _validate_direct_workspace_graph_source_closure(
        bound_roots=bound_roots,
        selected_sources=selected_sources,
        source_correspondences=source_correspondences,
    )
    target_validator = (
        command.sources.declaration_scope_runtime
        .bind_original_graph_target_validator(selected_sources)
    )
    planner = compose_current_workspace_graph_planner(
        code_host=code_host,
        catalog_host=command.catalog_host,
        epoch=epoch,
        expected_epoch=expected_epoch,
        original_sources=original_sources,
        package_closure=package_closure,
        backing=backing,
        source_only_target_validator=target_validator,
        source_correspondences=source_correspondences,
    )
    validate_originals()
    _validate_direct_workspace_root_plan_closure(
        command,
        selection=selection,
        bound_roots=bound_roots,
        root_plans=root_plans,
    )
    _validate_direct_workspace_graph_source_closure(
        bound_roots=bound_roots,
        selected_sources=selected_sources,
        source_correspondences=source_correspondences,
    )
    return planner


async def _plan_direct_workspace_selected_graph(
    staged,
    code_host,
    *,
    epoch,
    expected_epoch,
    original_sources,
    package_closure,
    backing,
    selected_sources,
    source_correspondences,
    selection,
    bound_roots,
    selected_product_roots=(),
):
    """Run the neutral graph planner with only Code-selected original roots."""
    from .materialization_graph_host_composition import (
        plan_current_workspace_materialization_graph,
    )

    root_plans = _compose_direct_workspace_selected_root_code_plans(
        staged,
        code_host,
        epoch=epoch,
        expected_epoch=expected_epoch,
        selection=selection,
        bound_roots=bound_roots,
        selected_product_roots=selected_product_roots,
    )
    graph_selection = _derive_direct_workspace_graph_selection(
        staged.command,
        selection=selection,
        bound_roots=bound_roots,
        root_plans=root_plans,
    )
    _validate_direct_workspace_graph_source_closure(
        bound_roots=bound_roots,
        selected_sources=selected_sources,
        source_correspondences=source_correspondences,
    )
    target_validator = (
        staged.command.sources.declaration_scope_runtime
        .bind_original_graph_target_validator(selected_sources)
    )
    result, _wire = await plan_current_workspace_materialization_graph(
        code_host=code_host,
        catalog_host=staged.command.catalog_host,
        epoch=epoch,
        expected_epoch=expected_epoch,
        original_sources=original_sources,
        package_closure=package_closure,
        backing=backing,
        source_only_target_validator=target_validator,
        source_correspondences=source_correspondences,
        selection=graph_selection,
        root_plans=root_plans,
    )
    if _POLICY_HOSTS.get(code_host) is not staged:
        raise RuntimeError("original v3 Code/Workspace graph host unavailable")
    _validate_direct_workspace_root_plan_closure(
        staged.command,
        selection=selection,
        bound_roots=bound_roots,
        root_plans=root_plans,
    )
    _validate_direct_workspace_graph_source_closure(
        bound_roots=bound_roots,
        selected_sources=selected_sources,
        source_correspondences=source_correspondences,
    )
    staged.command.catalog_host.validate_current_catalog_epoch(
        epoch, expected=expected_epoch
    )
    return result


def _compose_direct_workspace_current_graph_product_operations(
    staged,
    code_host,
    *,
    plan_result,
    planning_source,
    package_closure,
    source_correspondences,
    epoch,
    expected_epoch,
    backing,
):
    """Bind every selected node to original successor sources and products."""
    from aware_code_retained_registry_policy_runtime.direct_host import (
        close_direct_validation_host,
    )

    from .materialization_graph_host_composition import (
        WorkspaceCurrentGraphProductOperationSet,
        WorkspaceMaterializationGraphBacking,
    )
    from .semantic_dependency_graph import (
        WorkspaceSemanticMaterializationGraphPlanResult,
    )
    from .source_admission_catalog import WorkspaceV3GraphSourceCorrespondence

    if (
        type(staged) is not _DirectWorkspaceStagedCommandResources
        or _POLICY_HOSTS.get(code_host) is not staged
        or type(staged.command.sources) is not _DirectWorkspaceDeclarationSources
        or _STAGED_ASSEMBLIES.get(staged.command.lifetime_runtime, (None,))[0]
        is not staged
        or type(plan_result) is not WorkspaceSemanticMaterializationGraphPlanResult
        or type(backing) is not WorkspaceMaterializationGraphBacking
        or type(package_closure) is not tuple
        or type(source_correspondences) is not tuple
    ):
        raise RuntimeError("original fixed graph-product command required")
    command = staged.command
    plan_result.__post_init__()
    nodes = plan_result.graph_execution_binding.ordered_node_bindings
    if (
        tuple(sorted((node.package for node in nodes), key=lambda item: item.package_ref))
        != package_closure
        or len(source_correspondences) != len(nodes)
        or any(
            type(item) is not WorkspaceV3GraphSourceCorrespondence
            for item in source_correspondences
        )
    ):
        raise RuntimeError("complete original graph-node correspondence required")
    command.sources.exclusion.check_live()
    joint = command.catalog_host
    joint.validate_current_catalog_epoch(epoch, expected=expected_epoch)
    pair = joint._result
    if pair is None:
        raise RuntimeError("original successor catalog pair unavailable")
    issuer = command.sources.declaration_scope_runtime
    by_ref = {}
    for correspondence in source_correspondences:
        package_ref = correspondence.package().package_ref
        if package_ref in by_ref:
            raise RuntimeError("duplicate original graph-node correspondence")
        selected = correspondence.original_selected_source()
        context, _inventory = issuer.inspect_inputs(selected)
        if context.package.package_ref != package_ref:
            raise RuntimeError("graph-node correspondence differs from command source")
        by_ref[package_ref] = correspondence
    if set(by_ref) != {node.package.package_ref for node in nodes}:
        raise RuntimeError("graph-node correspondence differs from selected graph")
    source_inputs = []
    for node in nodes:
        package = node.package
        correspondence = by_ref[package.package_ref]
        entry = pair.workspace.package(package.package_ref)
        if entry != node.package_entry:
            raise RuntimeError("graph-node entry differs from current catalog")
        planning_input = planning_source.read_dependencies(package)
        correspondence.validate(entry, planning_input)
        source_inputs.append(
            _compose_successor_graph_node_source_inputs(
                staged,
                code_host,
                planning_source=planning_source,
                package_closure=package_closure,
                correspondence=correspondence,
                epoch=epoch,
                expected_epoch=expected_epoch,
            )
        )
    joint.validate_current_catalog_epoch(epoch, expected=expected_epoch)
    try:
        operations = WorkspaceCurrentGraphProductOperationSet(
            staged=staged,
            code_host=code_host,
            plan_result=plan_result,
            source_inputs=tuple(source_inputs),
            backing=backing,
        )
        joint.validate_current_catalog_epoch(epoch, expected=expected_epoch)
        return operations
    except BaseException:
        close_direct_validation_host(code_host)
        raise


def _compose_direct_workspace_dependency_product_issuer(staged, host, *, publisher):
    """Attach the existing package publisher to this fixed host's original issuer.

    The caller must supply the application-owned publisher resource. This does
    not install a store, grant V5 approval or authorize any publication.
    """
    from aware_code_retained_registry_policy_runtime.direct_host import (
        DirectValidationHost,
    )

    from .declaration_scope_admission import WorkspaceDeclarationScopeRuntime
    from .semantic_materialization_publication import (
        WorkspaceSemanticMaterializationPublisher,
    )

    if (
        type(staged) is not _DirectWorkspaceStagedCommandResources
        or type(host) is not DirectValidationHost
        or _POLICY_HOSTS.get(host) is not staged
        or type(publisher) is not WorkspaceSemanticMaterializationPublisher
    ):
        raise RuntimeError("original fixed host and Workspace publisher required")
    issuer = staged.command.sources.declaration_scope_runtime
    if type(issuer) is not WorkspaceDeclarationScopeRuntime:
        raise RuntimeError("original v3 dependency issuer required")
    issuer._bind_original_dependency_product_publisher(publisher)
    return issuer


@contextmanager
def _compose_direct_workspace_authority_predecessor_issuer(staged, host, *, publisher):
    """Bind the existing head rail to the exact fixed Code/Workspace host."""
    from aware_code_retained_registry_policy_runtime import (
        authority_operation_context as authority_contexts,
    )

    from .semantic_materialization_publication import (
        WorkspaceAuthorityPredecessorIssuerRuntime,
        WorkspaceSemanticMaterializationPublisher,
    )

    if (
        type(staged) is not _DirectWorkspaceStagedCommandResources
        or _POLICY_HOSTS.get(host) is not staged
        or type(publisher) is not WorkspaceSemanticMaterializationPublisher
    ):
        raise RuntimeError("original fixed host and Workspace publisher required")
    command = staged.command
    joint = command.catalog_host
    expected = joint.read_initial_publication()
    epoch = joint.read_initial_epoch()
    issuer = WorkspaceAuthorityPredecessorIssuerRuntime._assemble(
        publisher=publisher,
        command_runtime=command.lifetime_runtime,
        command_parent=command.invocation_parent,
        catalog_host=joint,
        catalog_epoch=epoch,
        catalog_expected=expected,
        authority_validator=authority_contexts.authority_context_validator(host),
    )
    try:
        yield issuer
    finally:
        issuer.close()


async def _construct_original_installed_workspace_host(
    *, proposal_wire, original_child_delivery, original_installed_composition,
):
    """Construct and retire a genuine host, never finish a semantic command.

    Uses the existing original command/source/contribution/Code-host entrances.
    It creates no graph node, private input, V5 grant, Meta attempt, result or
    package publisher. The materialization continuation and public command
    remain unchanged and unavailable. Failure must retain the native owner.
    """
    global _INSTALLED_CONTINUATION_RECORD
    record = None
    candidate = None
    try:
        from aware_environment_protected_store_delivery_runtime import (
            command_entry as pair_entry,
        )
        from aware_workspace_command.materialize_command import (
            _decode_installed_workspace_proposal_wire,
        )

        pair_entry._require_original_installed_workspace_pair(
            original_child_delivery, original_installed_composition,
            proposal_wire=proposal_wire,
        )
        if (os.getpid() != _INSTALLED_CONTINUATION_PROCESS
                or _INSTALLED_CONTINUATION_RECORD is not None):
            raise RuntimeError("original Workspace receiving position occupied")
        proposal = _decode_installed_workspace_proposal_wire(proposal_wire)
        continuation = object.__new__(_InstalledWorkspaceCommandContinuation)
        values = (original_child_delivery, original_installed_composition,
                  None, None, None, None, "opening")
        for slot, value in zip(_INSTALLED_CONTINUATION_SLOTS, values, strict=True):
            slot.__set__(continuation, value)
        record = _InstalledWorkspaceContinuationRecord(
            continuation, os.getpid(), current_thread(), values[:6], (), proposal_wire,
            (pair_entry, pair_entry._require_original_installed_workspace_pair,
             pair_entry._read_original_installed_workspace_resources,
             pair_entry._bind_original_installed_workspace_command,
             pair_entry._release_original_installed_workspace_borrow,
             pair_entry._read_original_installed_workspace_source_resources),
        )
        _INSTALLED_CONTINUATION_RECORD = record
        record.source_resources = pair_entry._read_original_installed_workspace_source_resources(
            original_child_delivery, original_installed_composition,
            original_continuation=continuation,
        )
        resources = record.source_resources
        if (type(resources) is not tuple or len(resources) != 2
                or type(resources[0]) is not WorkspaceRepositoryObservationSession
                or type(resources[1]) is not WorkspaceRepositoryDeltaRetentionClient
                or proposal.participant_checkout_root != str(resources[0].binding.root_path)):
            raise TypeError("same original source session/Delta/repository required")
        resources[1].verify_repository_binding(expected_binding_ref=resources[0].binding.binding_key)
        record.source_context = _compose_direct_workspace_command_source(
            session=resources[0], store=resources[1], proposal=proposal,
        )
        record.source_result = record.source_context.__enter__()
        record.source_opened = True
        command, inspection, selected = record.source_result
        if type(selected) is not WorkspaceSelectedPackageSource:
            raise SourceObservationUnavailable("original exact-profile source required")
        _INSTALLED_CONTINUATION_SLOTS[2].__set__(continuation, command)
        _INSTALLED_CONTINUATION_SLOTS[3].__set__(continuation, inspection)
        record.references = _installed_continuation_values(continuation)[:6]
        pair_entry._bind_original_installed_workspace_command(
            original_child_delivery, original_installed_composition,
            original_continuation=continuation, original_command=command,
        )
        record.resources = pair_entry._read_original_installed_workspace_resources(
            original_child_delivery, original_installed_composition,
            original_continuation=continuation,
        )
        resources = record.resources
        if (type(resources) is not tuple or len(resources) != 8
                or any(resources[index] is not record.source_resources[index] for index in (0, 1))
                or type(resources[3]) is not tuple or resources[3] != ()):
            raise TypeError("original host-only resource scope differs")
        record.host_context = compose_direct_workspace_selected_host(
            session=resources[0], store=resources[1], factory_admission=resources[2],
            product_factory_admissions=resources[3], composition_implementation=resources[4],
            composition_configuration=resources[5], policy_implementation=resources[6],
            policy_configuration=resources[7], workspace_manifest_path=proposal.workspace_manifest_name,
            command_resources=command,
        )
        record.selected_host = record.host_context.__enter__()
        record.host_opened = True
        _publish_installed_continuation_phase(record, "reading")
        # This helper reads the retained source and produces/validates one real
        # Code registry policy. It creates no private node/input or V5 grant.
        _prepare_installed_workspace_private_stage_source(record)
        staged = record.selected_host.staged
        if (type(staged) is not _DirectWorkspaceStagedCommandResources
                or staged.command is not command or len(staged.stage_runtime_bindings) != 2
                or staged.product_runtime_bindings != () or record.registry_policy is None):
            raise RuntimeError("actual original host construction differs")
        candidate = {
            "contract": "aware.workspace.original-host-construction.v1",
            "repository_binding": resources[0].binding.binding_key,
            "workspace_manifest": proposal.workspace_manifest_name,
            "source_identity_digest": inspection.selected_root.source_identity_digest,
            "stage_registration_count": len(staged.stage_runtime_bindings),
            "product_registration_count": len(staged.product_runtime_bindings),
            "registry_policy_prepared": True,
            "semantic_invocation_submitted": False,
            "v5_approval_issued": False,
            "materialization_admitted": False,
        }
        # Keep this candidate inside original receiving custody until actual
        # host/source __exit__ and fixed Platform closure readback return.
        _close_installed_workspace_contexts(record)
        record.release_started = True
        pair_entry._release_original_installed_workspace_borrow(
            original_child_delivery, original_installed_composition,
            original_continuation=continuation,
        )
        for slot in _INSTALLED_CONTINUATION_SLOTS[:6]:
            slot.__set__(continuation, None)
        record.references = (None,) * 6
        record.resources = ()
        record.source_context = record.host_context = record.selected_host = None
        record.source_result = record.registry_policy = record.source_resources = None
        record.pair_calls = ()
        record.proposal_wire = b""
        _INSTALLED_CONTINUATION_RECORD = None
        # Normal result means known consumer host/source closure only. Native
        # process/runtime/backing and outer parent settlement are still owned.
        return candidate
    except BaseException:
        if record is not None:
            _hold_installed_continuation(record)
        # No best-effort __exit__/stop/retry after uncertainty. Native root
        # retains the same actual process and all partial original resources.
        raise
