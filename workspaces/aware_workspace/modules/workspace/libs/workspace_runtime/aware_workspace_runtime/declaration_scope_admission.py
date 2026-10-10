"""Original Workspace issuer for Code's declaration and selected-source values.

This adapter projects retained source evidence. It neither selects a Code
provider nor grants Code host, policy, or execution authority.
"""

from __future__ import annotations

import copy
import inspect
import os
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, fields
from pathlib import PurePosixPath
from typing import Any, cast
from weakref import WeakKeyDictionary

from aware_code_module_manifest_contract_runtime import (
    AwareModuleSpecV3,
    parse_module_manifest,
)
from aware_code_semantic_contract_runtime import (
    SemanticDependencyTargetConstraint,
    encode_semantic_candidate_listing,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    SemanticContractRef,
    SemanticPackageCoordinate,
    SemanticValueCoordinate,
)
from aware_code_semantic_contract_runtime.dependency_admission_interfaces import (
    RetainedDependencyFulfillmentExpectation,
    RetainedDependencyResolutionExpectation,
)
from aware_code_semantic_contract_runtime.dependency_inputs import (
    SemanticDependencyTarget,
)
from aware_code_semantic_contract_runtime.dependency_scope_closure import (
    MAX_EDGES,
    MAX_SCOPES,
)
from aware_code_semantic_contract_runtime.dependency_scope_closure_v2 import (
    DependencyScopeProfileAssociation,
)
from aware_code_semantic_contract_runtime.retained_admission_interfaces import (
    RetainedSemanticAdmissionExpectation,
)
from aware_code_semantic_contract_runtime.retained_declaration_scope import (
    CodeDeclarationScopeExpectation,
    CodeRetainedDeclarationPackage,
    CodeRetainedDeclarationScopeEntry,
    CodeRetainedDeclarationScopeProjection,
    CodeRetainedDependencyScopeClosureV3,
    CodeRetainedLocalProfilePublication,
    CodeSelectedPackageSourceBinding,
    CodeSelectedPackageSourceExpectation,
)
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    DECLARATION_TARGET_INVENTORY_REF,
    PACKAGE_CONTEXT_INPUT_REF,
    encode_declaration_target_inventory,
    encode_package_context_input,
)
from aware_code_semantic_contract_runtime.retained_input_projections import (
    CodeSemanticDeclarationTarget,
    CodeSemanticDeclarationTargetInventory,
    CodeSemanticPackageContextInput,
)
from aware_code_semantic_contract_runtime.retained_scope_interfaces import (
    CodeRetainedScopeBody,
    CodeRetainedScopeModule,
)
from aware_code_semantic_contract_runtime.runtime import SemanticBody
from aware_code_semantic_contract_runtime.selected_participant_scope import (
    CodeSelectedParticipantViewV1,
)
from aware_code_semantic_contract_runtime.semantic_candidates import (
    SEMANTIC_CANDIDATE_LISTING_REF,
    CodeSemanticCandidate,
    CodeSemanticCandidateListing,
)
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    AdmittedSemanticInputProducerRegistration,
    SemanticInputContextContract,
    SemanticInputPackageIdentity,
    SemanticInputProducerHost,
    SemanticInputProductionExpectation,
    SemanticInputSourceBody,
    SemanticInputSourceContract,
    SemanticInputSourceCoordinate,
    read_registered_semantic_input_source_selection,
)
from aware_code_semantic_contract_runtime.source_origin import (
    SOURCE_ORIGIN_REF,
    SemanticInputPackageOccurrence,
    SemanticInputSourceOccurrence,
    SemanticInputSourceOrigin,
    encode_source_origin,
    source_occurrence_ref,
    validate_source_origin_selection,
)
from aware_code_semantic_contract_runtime.source_selection import (
    SOURCE_SELECTION_REF,
    SemanticSourceSelection,
    encode_source_selection,
)
from aware_code_semantic_contract_runtime.target_context_interfaces import (
    RetainedTargetExpectation,
)

from .code_scope_adapter import _body
from .command_lifetime import WorkspaceCatalogEpochExclusionGuard
from .composition import RetainedWorkspaceCompositionProvider
from .materialization_declaration_selection import (
    WorkspaceDeclaredMaterializationRoot,
    select_declared_materialization_roots,
    select_exact_declared_materialization_root,
)
from .materialization_selection import WorkspaceMaterializationSelectionProposal
from .observed_semantic_issuers import (
    _IDENTITIES,
    WorkspaceDeclarationInventoryAdmission,
    WorkspacePackageContextAdmission,
    _claim,
    _snapshot,
)
from .source_observation import (
    WorkspaceObservedDeclarationEvidence,
    WorkspaceObservedSelectedPackageEvidence,
    WorkspaceRetainedDeclarationObservation,
    WorkspaceRetainedSelectedPackageObservation,
    WorkspaceSourceObservationRuntime,
)
from .source_observation_io import SourceObservationUnavailable
from .workspace_profile_declarations import local_profile_paths_from_bytes


class WorkspaceDeclarationScope:
    __slots__ = ()

    def __new__(cls):
        raise TypeError("Workspace issues declaration scope handles")

    def __reduce__(self):
        raise TypeError("declaration scope handles cannot be serialized")


class WorkspaceSelectedPackageSource:
    __slots__ = ()

    def __new__(cls):
        raise TypeError("Workspace issues selected source handles")

    def __reduce__(self):
        raise TypeError("selected source handles cannot be serialized")


@dataclass(frozen=True, slots=True)
class _DeclarationRecord:
    observation: WorkspaceRetainedDeclarationObservation
    source_record: WorkspaceObservedDeclarationEvidence
    expectation: CodeDeclarationScopeExpectation
    consumer_scope_key: str
    digest: ContentDigest


@dataclass(frozen=True, slots=True)
class _SelectedRecord:
    declaration: WorkspaceDeclarationScope
    declaration_record: _DeclarationRecord
    observation: WorkspaceRetainedSelectedPackageObservation
    source_record: object
    expectation: CodeSelectedPackageSourceExpectation
    digest: ContentDigest


@dataclass(frozen=True, slots=True)
class _SemanticRecord:
    selected: WorkspaceSelectedPackageSource
    expectation: RetainedSemanticAdmissionExpectation
    context: CodeSemanticPackageContextInput
    inventory: CodeSemanticDeclarationTargetInventory
    namespace: str
    owned_roots: tuple[str, ...]
    closure_digest: ContentDigest
    targets: tuple[_V3TargetRecord, ...]

    @property
    def source(self) -> _SemanticRecord:
        """The shared resolver reads this original source context by identity."""
        return self


@dataclass(slots=True)
class _SelectedInputOrigin:
    host: SemanticInputProducerHost
    registration: AdmittedSemanticInputProducerRegistration
    expected: SemanticInputProductionExpectation
    result: SemanticBody
    source_contracts: tuple[SemanticInputSourceContract, ...]


@dataclass(slots=True)
class _PreRequestInputRecord:
    selected: WorkspaceSelectedPackageSource
    selected_record: _SelectedRecord
    expected: SemanticInputProductionExpectation
    input_digest: str
    thread_id: int
    live: bool = True
    selection_origin: _SelectedInputOrigin | None = None


@dataclass(frozen=True, slots=True)
class _V3TargetRecord:
    membership: WorkspaceSelectedPackageSource
    observation: WorkspaceRetainedSelectedPackageObservation
    context: CodeSemanticPackageContextInput
    address: tuple[str, str, str]


class WorkspaceOriginalGraphTargetValidator:
    """Read original v3 target membership; never issue a target admission."""

    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("Workspace issues graph target validators")

    @staticmethod
    def _origin(value):
        if type(value) is not WorkspaceOriginalGraphTargetValidator:
            raise SourceObservationUnavailable("original_graph_target_validator_required")
        result = _GRAPH_TARGET_VALIDATORS.get(value)
        if result is None or result[2] != os.getpid():
            raise SourceObservationUnavailable("foreign_graph_target_validator")
        return result[0], result[1]

    def validate_source_packages(self, packages):
        issuer, selected = self._origin(self)
        with issuer._lock:
            issuer._check_origin()
            actual = tuple(sorted(
                (issuer._semantic_values(handle)[0].package for handle in selected),
                key=lambda package: package.package_ref,
            ))
            if actual != packages:
                raise SourceObservationUnavailable("graph_target_source_closure_differs")

    def validate_target(self, *, package, dependency_kind, dependency_ref, target):
        issuer, selected = self._origin(self)
        with issuer._lock:
            issuer._check_origin()
            roots = [
                handle for handle in selected
                if issuer._semantic_values(handle)[0].package == package
            ]
            if len(roots) != 1:
                raise SourceObservationUnavailable("graph_target_owner_unavailable")
            owner = roots[0]
            inventory = issuer._semantic_values(owner)[1]
            declarations = tuple(
                item for item in inventory.entries
                if (item.dependency_kind, item.dependency_ref)
                == (dependency_kind, dependency_ref)
            )
            if len(declarations) != 1 or target not in declarations[0].targets:
                raise SourceObservationUnavailable("graph_target_declaration_differs")
            records = issuer._selected_targets.get(owner)
            if records is None:
                raise SourceObservationUnavailable("graph_target_admission_unavailable")
            matches = tuple(
                item for item in records
                if item.context.package == target.package
            )
            if len(matches) != 1 or issuer._target_source(matches[0].membership) is not matches[0]:
                raise SourceObservationUnavailable("graph_target_membership_differs")
            if issuer._semantic_values(matches[0].membership)[3] != target.semantic_root_refs:
                raise SourceObservationUnavailable("graph_target_roots_differ")


_GRAPH_TARGET_VALIDATORS = WeakKeyDictionary()


@dataclass(frozen=True, slots=True)
class _V3DependencySourceWindow:
    thread_id: int
    declaration: WorkspaceDeclarationScope
    declaration_record: _DeclarationRecord
    closure: CodeRetainedDependencyScopeClosureV3
    bindings: dict[
        WorkspaceSelectedPackageSource,
        tuple[_SelectedRecord, CodeSelectedPackageSourceBinding],
    ]


@dataclass(slots=True)
class _SemanticSourceValidationWindow:
    thread_id: int
    selected: WorkspaceSelectedPackageSource
    record: _SelectedRecord
    closure: CodeRetainedDependencyScopeClosureV3
    binding: CodeSelectedPackageSourceBinding
    location: str | None = None


class WorkspaceDeclarationScopeRuntime:
    """Borrow the original observer and parent exclusion, owning only new handles."""

    def __init__(self, *, observation_runtime: WorkspaceSourceObservationRuntime):
        if type(observation_runtime) is not WorkspaceSourceObservationRuntime:
            raise TypeError("exact Workspace source observation runtime required")
        if observation_runtime._exclusion is None:
            raise SourceObservationUnavailable(
                "declaration_parent_exclusion_unavailable"
            )
        observation_runtime._exclusion.check_live()
        self._source = observation_runtime
        self._exclusion = observation_runtime._exclusion
        self._pid = os.getpid()
        self._lock = threading.RLock()
        self._closed = False
        self._declarations: dict[WorkspaceDeclarationScope, _DeclarationRecord] = {}
        self._selected: dict[WorkspaceSelectedPackageSource, _SelectedRecord] = {}
        self._pre_request_inputs: dict[
            tuple[str, str, str, str], _PreRequestInputRecord
        ] = {}
        self._retired_pre_request_inputs: set[
            tuple[str, str, str, str]
        ] = set()
        self._semantic: dict[object, _SemanticRecord] = {}
        self._semantic_contexts: dict[object, object] = {}
        # The existing Workspace dependency resolver consumes this original
        # context map; it never creates another target or membership issuer.
        self._contexts = self._semantic_contexts
        self._issued_semantic: list[tuple[object, str]] = []
        self._target_records: dict[WorkspaceSelectedPackageSource, _V3TargetRecord] = {}
        self._selected_targets: dict[
            WorkspaceSelectedPackageSource, tuple[_V3TargetRecord, ...]
        ] = {}
        self._planning_validator = None
        self._authority_validator = None
        self._dependency_validator = None
        self._dependency_resolution = None
        self._dependency_fulfillment = None
        self._dependency_source_window: _V3DependencySourceWindow | None = None
        self._semantic_source_window: _SemanticSourceValidationWindow | None = None
        self._methods = {}
        for name in (
            "declaration_evidence",
            "read_declarations",
            "revalidate_declarations",
            "selected_package_evidence",
            "revalidate_selected_package",
            "_selected_description",
            "_check_declaration_record_locked",
            "_check_selected_record_locked",
            "read_selected_package",
            "read_selected_package_location",
        ):
            method = getattr(observation_runtime, name)
            self._methods[name] = (
                inspect.getattr_static(observation_runtime, name), method
            )
        self._check_origin()

    def _check_origin(self, *, retiring: bool = False) -> None:
        if os.getpid() != self._pid:
            raise SourceObservationUnavailable("declaration_process_changed")
        if self._closed and not retiring:
            raise SourceObservationUnavailable("declaration_scope_closed")
        if self._source._exclusion is not self._exclusion:
            raise SourceObservationUnavailable("declaration_parent_changed")
        if not retiring:
            self._exclusion.check_live()
        else:
            return
        for name, (descriptor, method) in self._methods.items():
            if (
                not inspect.ismethod(method)
                or method.__self__ is not self._source
                or method.__func__ is not descriptor
                or inspect.getattr_static(self._source, name) is not descriptor
            ):
                raise SourceObservationUnavailable("declaration_reader_origin_changed")

    def _check_origin_locked(
        self, guard: WorkspaceCatalogEpochExclusionGuard
    ) -> None:
        """Check the retained issuer under an existing parent guard only."""
        self._exclusion.check_locked(guard)
        if os.getpid() != self._pid:
            raise SourceObservationUnavailable("declaration_process_changed")
        if self._closed or self._source._exclusion is not self._exclusion:
            raise SourceObservationUnavailable("declaration_scope_closed_or_replaced")
        for name, (descriptor, method) in self._methods.items():
            if (
                not inspect.ismethod(method)
                or method.__self__ is not self._source
                or method.__func__ is not descriptor
                or inspect.getattr_static(self._source, name) is not descriptor
            ):
                raise SourceObservationUnavailable("declaration_reader_origin_changed")

    def _call(self, name: str, *args, **kwargs):
        return self._methods[name][1](*args, **kwargs)

    def _retained_bodies(
        self, observation: WorkspaceRetainedDeclarationObservation
    ) -> tuple[WorkspaceObservedDeclarationEvidence, dict[str, CodeRetainedScopeBody],
               RetainedWorkspaceCompositionProvider, dict[str, object]]:
        evidence = self._call("declaration_evidence", observation)
        rows = []
        coordinates: dict[str, CodeRetainedScopeBody] = {}
        for coordinate, body in self._call("read_declarations", observation):
            rows.append((coordinate.relative_path, body))
            coordinates[coordinate.relative_path] = _body(coordinate, body)
        provider = RetainedWorkspaceCompositionProvider()
        description = provider.describe_captured_bodies(tuple(rows))
        if description["root_kind"] != "repository" or (
            provider.declaration_body_paths(description) != tuple(coordinates)
        ):
            raise SourceObservationUnavailable(
                "complete_repository_declaration_required"
            )
        return evidence, coordinates, provider, description

    def _closure(
        self,
        observation: WorkspaceRetainedDeclarationObservation,
        consumer_scope_key: str,
    ) -> CodeRetainedDependencyScopeClosureV3:
        evidence, bodies, provider, description = self._retained_bodies(observation)
        targets = provider.qualified_repository_membership()
        if consumer_scope_key not in targets.values() or len(targets) > MAX_SCOPES:
            raise SourceObservationUnavailable("declaration_consumer_not_member")
        repository = cast(dict[str, Any], description["repository"])
        workspaces = {w["manifest_path"]: w for w in repository["workspaces"]}
        if set(workspaces) != set(targets.values()):
            raise SourceObservationUnavailable("declaration_membership_incomplete")
        # The retained observation covers the whole repository, but one Code
        # closure contains only the consumer and its declared provider imports.
        # An unrelated Workspace must not acquire policy scope merely because
        # it appears in the same repository manifest.
        reachable = {consumer_scope_key}
        pending = [consumer_scope_key]
        selected_edges = []
        while pending:
            scope_key = pending.pop()
            for edge in provider.qualified_dependency_selections(
                scope_key, targets=targets
            ):
                if edge.target_scope_key not in workspaces:
                    raise SourceObservationUnavailable(
                        "declaration_dependency_not_member"
                    )
                selected_edges.append(edge)
                if edge.target_scope_key not in reachable:
                    reachable.add(edge.target_scope_key)
                    pending.append(edge.target_scope_key)
        if len(reachable) > MAX_SCOPES or len(selected_edges) > MAX_EDGES:
            raise SourceObservationUnavailable("declaration_scope_bound")
        entries = []
        publications = []
        edges = sorted(selected_edges, key=lambda edge: edge.ordering_key)
        for scope_key in sorted(reachable, key=str.encode):
            workspace = workspaces[scope_key]
            handle = workspace["workspace_handle"]
            modules = []
            packages = []
            for module in workspace["modules"]:
                module_path = module["manifest_path"]
                modules.append(
                    CodeRetainedScopeModule(
                        module["module_id"], bodies[module_path]
                    )
                )
                for package in module["packages"]:
                    root = package["package_root"]
                    prefix = "" if root == "." else root + "/"
                    manifest_path = package["manifest_path"]
                    packages.append(
                        CodeRetainedDeclarationPackage(
                            module["module_id"],
                            package["package_id"],
                            package["package_kind"],
                            module_path,
                            root,
                            manifest_path[len(prefix):],
                            bodies[manifest_path],
                        )
                    )
            modules.sort(key=lambda row: row.module_id.encode())
            packages.sort(
                key=lambda row: (row.module_id.encode(), row.package_id.encode())
            )
            projection = CodeRetainedDeclarationScopeProjection(
                evidence.repository_binding_ref,
                ContentDigest.of_wire(evidence.observation_digest),
                bodies[scope_key],
                tuple(modules),
                tuple(packages),
            )
            entries.append(
                CodeRetainedDeclarationScopeEntry(scope_key, handle, projection)
            )
            for key, local_path in local_profile_paths_from_bytes(
                bodies[scope_key].body, workspace_handle=handle
            ):
                path = str(PurePosixPath(scope_key).parent / local_path)
                publications.append(
                    CodeRetainedLocalProfilePublication(scope_key, key, bodies[path])
                )
        publications.sort(
            key=lambda p: (p.owning_scope_key.encode(), p.profile_key.encode())
        )
        local = {(p.owning_scope_key, p.profile_key): p for p in publications}
        associations = []
        for edge in edges:
            key = edge.profile_key.value
            owner = local.get((edge.target_scope_key, key))
            if owner is None:
                raise SourceObservationUnavailable("imported_profile_not_published")
            associations.append(
                DependencyScopeProfileAssociation(
                    edge.declaring_scope_key,
                    edge.declaration,
                    edge.target_scope_key,
                    owner.manifest,
                )
            )
        return CodeRetainedDependencyScopeClosureV3(
            consumer_scope_key,
            evidence.repository_binding_ref,
            bodies["aware.repo.toml"],
            tuple(entries),
            tuple(edges),
            tuple(publications),
            tuple(associations),
        )

    def capture_declaration_scope(
        self,
        *,
        observation: WorkspaceRetainedDeclarationObservation,
        consumer_scope_key: str,
        expectation: CodeDeclarationScopeExpectation,
    ) -> WorkspaceDeclarationScope:
        self._check_origin()
        if type(expectation) is not CodeDeclarationScopeExpectation:
            raise TypeError("exact Code declaration expectation required")
        expectation.__post_init__()
        if (
            expectation.process_id != self._pid
            or expectation.repository_binding_ref
            != self._source._store.repository_binding_ref
        ):
            raise SourceObservationUnavailable("declaration_context_differs")
        self._call("revalidate_declarations", observation)
        with self._source._lock:
            original = self._source._declaration_evidence(observation)
        closure = self._closure(observation, consumer_scope_key)
        self._call("revalidate_declarations", observation)
        record = _DeclarationRecord(
            observation, original, expectation, consumer_scope_key,
            closure.closure_digest,
        )
        handle = object.__new__(WorkspaceDeclarationScope)
        with self._exclusion.mutation() as guard:
            with self._lock:
                self._check_origin()
                self._call(
                    "_check_declaration_record_locked", observation,
                    guard=guard, expected_record=original,
                )
                self._declarations[handle] = record
        return handle

    def _declaration_record(
        self, handle: WorkspaceDeclarationScope
    ) -> _DeclarationRecord:
        self._check_origin()
        if type(handle) is not WorkspaceDeclarationScope:
            raise SourceObservationUnavailable("foreign_declaration_scope")
        record = self._declarations.get(handle)
        if record is None:
            raise SourceObservationUnavailable("foreign_declaration_scope")
        with self._source._lock:
            if (
                self._source._declaration_evidence(record.observation)
                is not record.source_record
            ):
                raise SourceObservationUnavailable("declaration_source_replaced")
        return record

    def read_declaration_scope(
        self, handle: WorkspaceDeclarationScope
    ) -> CodeRetainedDependencyScopeClosureV3:
        with self._lock:
            record = self._declaration_record(handle)
            semantic_window = self._semantic_source_window
            if semantic_window is not None:
                if semantic_window.thread_id != threading.get_ident():
                    raise SourceObservationUnavailable("semantic_source_window_thread_changed")
                if handle is semantic_window.record.declaration:
                    if (record is not semantic_window.record.declaration_record
                        or type(record.digest) is not ContentDigest
                        or record.digest != semantic_window.closure.closure_digest):
                        raise SourceObservationUnavailable("declaration_source_replaced")
                    return copy.deepcopy(semantic_window.closure)
            window = self._dependency_source_window
            if (
                window is not None
                and window.thread_id == threading.get_ident()
                and handle is window.declaration
            ):
                if record is not window.declaration_record:
                    raise SourceObservationUnavailable("declaration_source_replaced")
                return copy.deepcopy(window.closure)
            self._call("revalidate_declarations", record.observation)
            closure = self._closure(record.observation, record.consumer_scope_key)
            if closure.closure_digest != record.digest:
                raise SourceObservationUnavailable("declaration_closure_changed")
            self._call("revalidate_declarations", record.observation)
            self._check_origin()
            return closure

    def inspect_materialization_roots(
        self,
        handle: WorkspaceDeclarationScope,
        *,
        selection: WorkspaceMaterializationSelectionProposal,
    ) -> tuple[WorkspaceDeclaredMaterializationRoot, ...]:
        """Read candidates through the original issuer; issue no authority."""
        with self._lock:
            record = self._declaration_record(handle)
            closure = self.read_declaration_scope(handle)
            _, _, _, description = self._retained_bodies(record.observation)
            repository = cast(dict[str, Any], description["repository"])
            roots = select_declared_materialization_roots(
                closure=closure,
                repository_handle=cast(str, repository["repository_handle"]),
                selection=selection,
            )
            self.validate_declaration_scope(
                handle,
                expectation=record.expectation,
                closure_digest=record.digest,
            )
            return roots

    def inspect_exact_materialization_root(
        self,
        handle: WorkspaceDeclarationScope,
        *,
        workspace_handle: str,
        module_id: str,
        package_id: str,
    ) -> WorkspaceDeclaredMaterializationRoot:
        """Inspect one addressed root through this issuer's original evidence."""
        with self._lock:
            record = self._declaration_record(handle)
            closure = self.read_declaration_scope(handle)
            root = select_exact_declared_materialization_root(
                closure=closure,
                workspace_handle=workspace_handle,
                module_id=module_id,
                package_id=package_id,
            )
            self.validate_declaration_scope(
                handle,
                expectation=record.expectation,
                closure_digest=record.digest,
            )
            return root

    def validate_declaration_scope(
        self,
        handle: WorkspaceDeclarationScope,
        *,
        expectation: CodeDeclarationScopeExpectation,
        closure_digest: ContentDigest | None = None,
    ) -> None:
        with self._lock:
            record = self._declaration_record(handle)
            if (
                type(expectation) is not CodeDeclarationScopeExpectation
                or expectation != record.expectation
            ):
                raise SourceObservationUnavailable("declaration_expectation_differs")
            if closure_digest is not None and (
                type(closure_digest) is not ContentDigest
                or closure_digest != record.digest
            ):
                raise SourceObservationUnavailable("declaration_digest_differs")
            self.read_declaration_scope(handle)

    def _check_declaration_scope_locked(
        self,
        handle: WorkspaceDeclarationScope,
        *,
        expectation: CodeDeclarationScopeExpectation,
        closure_digest: ContentDigest,
        guard: WorkspaceCatalogEpochExclusionGuard,
    ) -> _DeclarationRecord:
        self._check_origin_locked(guard)
        if type(handle) is not WorkspaceDeclarationScope:
            raise SourceObservationUnavailable("foreign_declaration_scope")
        record = self._declarations.get(handle)
        if record is None:
            raise SourceObservationUnavailable("foreign_declaration_scope")
        if (
            type(expectation) is not CodeDeclarationScopeExpectation
            or expectation != record.expectation
        ):
            raise SourceObservationUnavailable("declaration_expectation_differs")
        if (
            type(closure_digest) is not ContentDigest
            or closure_digest != record.digest
        ):
            raise SourceObservationUnavailable("declaration_digest_differs")
        self._call(
            "_check_declaration_record_locked",
            record.observation,
            guard=guard,
            expected_record=record.source_record,
        )
        return record

    def check_declaration_scope_locked(
        self,
        handle: WorkspaceDeclarationScope,
        *,
        expectation: CodeDeclarationScopeExpectation,
        closure_digest: ContentDigest,
        guard: WorkspaceCatalogEpochExclusionGuard,
    ) -> None:
        """In-place identity check after full validation, without reacquisition."""
        with self._lock:
            self._check_declaration_scope_locked(
                handle, expectation=expectation,
                closure_digest=closure_digest, guard=guard,
            )

    def bind_selected_package_source(
        self,
        *,
        declaration: WorkspaceDeclarationScope,
        selected: WorkspaceRetainedSelectedPackageObservation,
    ) -> WorkspaceSelectedPackageSource:
        with self._lock:
            record = self._declaration_record(declaration)
            with self._source._lock:
                source_record = self._source._selected.get(selected)
                if source_record is None or source_record[0] is not record.observation:
                    raise SourceObservationUnavailable(
                        "selected_declaration_origin_differs"
                    )
            self._call("revalidate_selected_package", selected)
            binding = self._binding(record, selected)
            self._call("revalidate_selected_package", selected)
            original = _SelectedRecord(
                declaration, record, selected, source_record,
                binding.expectation, binding.binding_digest,
            )
            handle = object.__new__(WorkspaceSelectedPackageSource)
        with self._exclusion.mutation() as guard:
            with self._lock:
                self._check_origin()
                if self._declarations.get(declaration) is not record:
                    raise SourceObservationUnavailable("declaration_scope_retired")
                self._call(
                    "_check_selected_record_locked", selected,
                    guard=guard, expected_record=source_record,
                )
                self._selected[handle] = original
        return handle

    def _binding(
        self,
        record: _DeclarationRecord,
        selected: WorkspaceRetainedSelectedPackageObservation,
    ) -> CodeSelectedPackageSourceBinding:
        evidence = self._call("selected_package_evidence", selected)
        closure = self._closure(record.observation, record.consumer_scope_key)
        if closure.closure_digest != record.digest:
            raise SourceObservationUnavailable("declaration_closure_changed")
        scope = next(
            (
                s
                for s in closure.scopes
                if s.scope_key == evidence.workspace_manifest_path
            ),
            None,
        )
        package = None if scope is None else next(
            (
                p
                for p in scope.projection.packages
                if (p.module_id, p.package_id)
                == (evidence.module_id, evidence.package_id)
            ),
            None,
        )
        if (
            package is None
            or package.package_kind != evidence.package_kind
            or package.manifest_relative_path != evidence.manifest_relative_path
            or package.package_root != evidence.package_root
        ):
            raise SourceObservationUnavailable("selected_package_occurrence_differs")
        source = ContentDigest.of_wire(evidence.source_identity_digest)
        expectation = CodeSelectedPackageSourceExpectation(
            record.expectation,
            record.digest,
            evidence.workspace_manifest_path,
            evidence.module_id,
            evidence.package_id,
            evidence.manifest_relative_path,
            package.manifest.content_digest,
            source,
        )
        candidates = CodeSemanticCandidateListing(
            source,
            tuple(
                CodeSemanticCandidate(
                    body.relative_path, ContentDigest.of_wire(body.content_digest)
                )
                for body in evidence.bodies
            ),
        )
        return CodeSelectedPackageSourceBinding(expectation, candidates)

    def _selected_record(
        self, handle: WorkspaceSelectedPackageSource
    ) -> _SelectedRecord:
        self._check_origin()
        if type(handle) is not WorkspaceSelectedPackageSource:
            raise SourceObservationUnavailable("foreign_selected_source")
        record = self._selected.get(handle)
        if (
            record is None
            or self._declarations.get(record.declaration)
            is not record.declaration_record
        ):
            raise SourceObservationUnavailable("foreign_selected_source")
        with self._source._lock:
            if (
                self._source._selected.get(record.observation)
                is not record.source_record
            ):
                raise SourceObservationUnavailable("selected_source_replaced")
        return record

    def read_selected_package_source(
        self, handle: WorkspaceSelectedPackageSource
    ) -> CodeSelectedPackageSourceBinding:
        with self._lock:
            record = self._selected_record(handle)
            semantic_window = self._semantic_source_window
            if semantic_window is not None:
                if semantic_window.thread_id != threading.get_ident():
                    raise SourceObservationUnavailable("semantic_source_window_thread_changed")
                if handle is semantic_window.selected:
                    if (record is not semantic_window.record
                        or type(record.expectation) is not CodeSelectedPackageSourceExpectation
                        or type(record.digest) is not ContentDigest
                        or record.expectation != semantic_window.binding.expectation
                        or record.digest != semantic_window.binding.binding_digest):
                        raise SourceObservationUnavailable("selected_source_replaced")
                    return copy.deepcopy(semantic_window.binding)
            window = self._dependency_source_window
            if window is not None and window.thread_id == threading.get_ident():
                retained = window.bindings.get(handle)
                if retained is not None:
                    original, binding = retained
                    if (
                        record is not original
                        or record.expectation != binding.expectation
                        or record.digest != binding.binding_digest
                    ):
                        raise SourceObservationUnavailable("selected_source_replaced")
                    return copy.deepcopy(binding)
            self._call("revalidate_selected_package", record.observation)
            binding = self._binding(record.declaration_record, record.observation)
            if (
                binding.binding_digest != record.digest
                or binding.expectation != record.expectation
            ):
                raise SourceObservationUnavailable("selected_source_binding_changed")
            self._call("revalidate_selected_package", record.observation)
            self._check_origin()
            return binding

    def inspect_selected_package_evidence(
        self, handle: WorkspaceSelectedPackageSource
    ) -> WorkspaceObservedSelectedPackageEvidence:
        """Return detached occurrence evidence after original source revalidation."""
        with self._lock:
            record = self._selected_record(handle)
            self.read_selected_package_source(handle)
            evidence = self._call("selected_package_evidence", record.observation)
            self.validate_selected_package_source(
                handle, expectation=record.expectation, binding_digest=record.digest
            )
            return evidence

    def validate_selected_package_source(
        self,
        handle: WorkspaceSelectedPackageSource,
        *,
        expectation: CodeSelectedPackageSourceExpectation,
        binding_digest: ContentDigest | None = None,
    ) -> None:
        with self._lock:
            record = self._selected_record(handle)
            if (
                type(expectation) is not CodeSelectedPackageSourceExpectation
                or expectation != record.expectation
            ):
                raise SourceObservationUnavailable(
                    "selected_source_expectation_differs"
                )
            if binding_digest is not None and (
                type(binding_digest) is not ContentDigest
                or binding_digest != record.digest
            ):
                raise SourceObservationUnavailable("selected_source_digest_differs")
            self.read_selected_package_source(handle)

    def read_selected_participant_view(
        self,
        declaration: WorkspaceDeclarationScope,
        selected: WorkspaceSelectedPackageSource,
    ) -> CodeSelectedParticipantViewV1:
        """Compute Code meaning while retaining the original source handles."""
        from aware_code_retained_registry_policy_runtime.selected_participant_calculation import (
            derive_selected_participant_view,
        )

        with self._lock:
            record = self._declaration_record(declaration)
            source = self._selected_record(selected)
            if source.declaration is not declaration or source.declaration_record is not record:
                raise SourceObservationUnavailable("selected_participant_origin_differs")
            closure = self.read_declaration_scope(declaration)
            binding = self.read_selected_package_source(selected)
            view = derive_selected_participant_view(
                closure,
                scope_key=binding.expectation.scope_key,
                module_id=binding.expectation.module_id,
                package_id=binding.expectation.package_id,
            )
            self.validate_selected_participant_view(declaration, selected, view=view)
            return view

    def validate_selected_participant_view(
        self,
        declaration: WorkspaceDeclarationScope,
        selected: WorkspaceSelectedPackageSource,
        *,
        view: CodeSelectedParticipantViewV1,
    ) -> None:
        """Recompute the complete view against this original live observation."""
        from aware_code_retained_registry_policy_runtime.selected_participant_calculation import (
            validate_selected_participant_view,
        )

        with self._lock:
            record = self._declaration_record(declaration)
            source = self._selected_record(selected)
            if source.declaration is not declaration or source.declaration_record is not record:
                raise SourceObservationUnavailable("selected_participant_origin_differs")
            if type(view) is not CodeSelectedParticipantViewV1:
                raise TypeError("exact Code selected-participant view required")
            view.__post_init__()
            binding = self.read_selected_package_source(selected)
            root = view.root
            if (
                view.declaration_closure_digest != record.digest
                or (root.scope_key, root.module_id, root.package_id)
                != (
                    binding.expectation.scope_key,
                    binding.expectation.module_id,
                    binding.expectation.package_id,
                )
            ):
                raise SourceObservationUnavailable("selected_participant_root_differs")
            closure = self.read_declaration_scope(declaration)
            validate_selected_participant_view(closure, view)
            self.validate_selected_package_source(
                selected,
                expectation=binding.expectation,
                binding_digest=binding.binding_digest,
            )
            self.validate_declaration_scope(
                declaration,
                expectation=record.expectation,
                closure_digest=record.digest,
            )

    def check_selected_package_source_locked(
        self,
        handle: WorkspaceSelectedPackageSource,
        *,
        expectation: CodeSelectedPackageSourceExpectation,
        binding_digest: ContentDigest,
        guard: WorkspaceCatalogEpochExclusionGuard,
    ) -> None:
        """Check both original handles under the same already-held guard."""
        with self._lock:
            self._check_origin_locked(guard)
            if type(handle) is not WorkspaceSelectedPackageSource:
                raise SourceObservationUnavailable("foreign_selected_source")
            record = self._selected.get(handle)
            if record is None:
                raise SourceObservationUnavailable("foreign_selected_source")
            if (
                type(expectation) is not CodeSelectedPackageSourceExpectation
                or expectation != record.expectation
            ):
                raise SourceObservationUnavailable(
                    "selected_source_expectation_differs"
                )
            if (
                type(binding_digest) is not ContentDigest
                or binding_digest != record.digest
            ):
                raise SourceObservationUnavailable("selected_source_digest_differs")
            self._check_declaration_scope_locked(
                record.declaration,
                expectation=record.declaration_record.expectation,
                closure_digest=record.declaration_record.digest,
                guard=guard,
            )
            if self._declarations.get(record.declaration) is not record.declaration_record:
                raise SourceObservationUnavailable("selected_declaration_origin_differs")
            self._call(
                "_check_selected_record_locked",
                record.observation,
                guard=guard,
                expected_record=record.source_record,
            )

    def _bind_original_code_validator(self, validator) -> None:
        self._bind_semantic_validator(validator, "source_planning")

    def _bind_original_authority_validator(self, validator) -> None:
        self._bind_semantic_validator(validator, "authority_derivation")

    def _bind_semantic_validator(self, validator, stage: str) -> None:
        name = "validate_retained_semantic_operation_context"
        with self._lock:
            self._check_origin()
            if (self._planning_validator if stage == "source_planning" else
                self._authority_validator) is not None:
                raise SourceObservationUnavailable("semantic_validator_already_bound")
            if stage == "authority_derivation" and self._planning_validator is None:
                raise SourceObservationUnavailable("planning_validator_required_first")
            descriptor = inspect.getattr_static(validator, name)
            method = getattr(validator, name)
            if (not inspect.ismethod(method) or method.__self__ is not validator
                or method.__func__ is not descriptor):
                raise SourceObservationUnavailable("original_code_validator_required")
            binding = (validator, descriptor, method)
            if stage == "source_planning":
                self._planning_validator = binding
            else:
                if validator is self._planning_validator[0]:
                    raise SourceObservationUnavailable("distinct_authority_validator_required")
                self._authority_validator = binding

    def _validate_code_context(self, context, expected) -> None:
        self._check_origin()
        if type(expected) is not RetainedSemanticAdmissionExpectation:
            raise SourceObservationUnavailable("exact_semantic_expectation_required")
        binding = (self._planning_validator if expected.stage == "source_planning"
                   else self._authority_validator if expected.stage == "authority_derivation"
                   else None)
        if binding is None:
            raise SourceObservationUnavailable("original_stage_validator_unavailable")
        validator, descriptor, method = binding
        name = "validate_retained_semantic_operation_context"
        if inspect.getattr_static(validator, name) is not descriptor:
            raise SourceObservationUnavailable("semantic_validator_substituted")
        if method(context, expected=expected) is not None:
            raise SourceObservationUnavailable("semantic_validator_result_invalid")
        if inspect.getattr_static(validator, name) is not descriptor:
            raise SourceObservationUnavailable("semantic_validator_substituted")
        self._check_origin()

    @staticmethod
    def _occurrence(closure, scope_key, module_id, package_id):
        scope = next((s for s in closure.scopes if s.scope_key == scope_key), None)
        package = None if scope is None else next(
            (p for p in scope.projection.packages
             if (p.module_id, p.package_id) == (module_id, package_id)), None,
        )
        module = None if scope is None else next(
            (m for m in scope.projection.modules if m.module_id == module_id), None,
        )
        if package is None or module is None:
            raise SourceObservationUnavailable("declaration_package_not_member")
        model = parse_module_manifest(module.manifest.body)
        if type(model) is not AwareModuleSpecV3:
            raise SourceObservationUnavailable("v3_occurrence_required")
        rows = tuple(d for d in model.package_declarations if d.package_id == package_id)
        if len(rows) != 1:
            raise SourceObservationUnavailable("occurrence_not_exact")
        return package, rows[0].occurrence

    @staticmethod
    def _target_scope(closure, current_scope: str, address: dict) -> str:
        scope = address.get("scope")
        if scope is None or scope["kind"] == "local":
            return current_scope
        if scope["kind"] != "dependency":
            raise SourceObservationUnavailable("target_scope_invalid")
        matches = tuple(
            s.scope_key for s in closure.scopes
            if s.workspace_handle == scope["workspace_handle"]
        )
        if len(matches) != 1 or not any(
            edge.declaring_scope_key == current_scope
            and edge.target_scope_key == matches[0]
            for edge in closure.edges
        ):
            raise SourceObservationUnavailable("original_direct_dependency_edge_required")
        return matches[0]

    def _source_projection_values(self, selected: WorkspaceSelectedPackageSource):
        """Original source projections before semantic root assignments exist.

        Package/context and declaration-inventory contracts carry no namespace
        or owned roots for this occurrence. Target roots remain required where
        the existing dependency inventory contract actually carries them.
        Execution admission adds the occurrence assignments separately.
        """
        record = self._selected_record(selected)
        binding = self.read_selected_package_source(selected)
        closure = self.read_declaration_scope(record.declaration)
        if closure.closure_digest != record.declaration_record.digest:
            raise SourceObservationUnavailable("declaration_closure_changed")
        choice = binding.expectation
        package, occurrence = self._occurrence(
            closure, choice.scope_key, choice.module_id, choice.package_id
        )
        manifest = self._call(
            "read_selected_package", record.observation,
            relative_path=choice.manifest_relative_path,
        )
        if ContentDigest.of_bytes(manifest) != package.manifest.content_digest:
            raise SourceObservationUnavailable("selected_manifest_differs")
        name = _claim(occurrence.semantic_package_name)
        version = _claim(occurrence.semantic_version)
        configuration = _claim(occurrence.configuration, nullable=True)
        coordinate = SemanticPackageCoordinate(
            f"package:{name}@{version}", package.package_kind,
            ContentDigest.of_bytes(manifest),
        )
        context = CodeSemanticPackageContextInput(
            coordinate, binding.candidates.source_identity_digest,
            choice.manifest_relative_path, _claim(occurrence.code_package_name),
            version, _claim(occurrence.source_code_package_id, nullable=True),
            None if configuration is None else configuration["config_id"],
            None if configuration is None else configuration["config_key"],
        )
        entries = []
        target_addresses = {}
        for mapping in _claim(occurrence.dependency_targets):
            targets = []
            for address in mapping["targets"]:
                target_scope = self._target_scope(
                    closure, choice.scope_key, address
                )
                target_package, target_occurrence = self._occurrence(
                    closure, target_scope, address["module_id"], address["package_id"]
                )
                target_name = _claim(target_occurrence.semantic_package_name)
                target_version = _claim(target_occurrence.semantic_version)
                target_addresses[
                    target_scope, address["module_id"], address["package_id"]
                ] = f"package:{target_name}@{target_version}"
                targets.append(SemanticDependencyTarget(
                    SemanticPackageCoordinate(
                        f"package:{target_name}@{target_version}",
                        target_package.package_kind,
                        target_package.manifest.content_digest,
                    ), _claim(target_occurrence.owned_roots),
                ))
            targets.sort(key=lambda target: target.package.package_ref)
            entries.append(CodeSemanticDeclarationTarget(
                mapping["dependency_kind"], mapping["dependency_ref"],
                tuple(targets), tuple(
                    SemanticDependencyTargetConstraint.create(**constraint)
                    for constraint in mapping["constraints"]
                ),
            ))
        inventory = CodeSemanticDeclarationTargetInventory(
            coordinate, context.source_identity_digest, tuple(entries)
        )
        self.validate_selected_package_source(
            selected, expectation=record.expectation, binding_digest=record.digest
        )
        return (
            context, inventory, manifest, binding,
            tuple(sorted(target_addresses.items())), occurrence,
        )

    def _semantic_values(self, selected: WorkspaceSelectedPackageSource):
        """Execution projections require the complete original assignments."""
        context, inventory, manifest, binding, addresses, occurrence = (
            self._source_projection_values(selected)
        )
        return (
            context, inventory, _claim(occurrence.namespace),
            _claim(occurrence.owned_roots), manifest, binding, addresses,
        )

    def inspect_inputs(self, selected: WorkspaceSelectedPackageSource):
        """Detached values for input construction; no admission from inspection."""
        with self._lock:
            context, inventory, _, _, _, _, _ = self._semantic_values(selected)
            return copy.deepcopy((context, inventory))

    def _pre_request_context_bytes(
        self, *, context: CodeSemanticPackageContextInput,
        inventory: CodeSemanticDeclarationTargetInventory,
        binding: CodeSelectedPackageSourceBinding, contract: SemanticContractRef,
        selection: SemanticSourceSelection | None = None,
        source_origin: SemanticInputSourceOrigin | None = None,
    ) -> bytes:
        """Only existing Code projections have an original source here.

        Owner-defined scope contracts need their original producer before this
        issuer can authenticate them. Portable caller bodies are never retained
        as substitute evidence.
        """
        if contract == PACKAGE_CONTEXT_INPUT_REF:
            return encode_package_context_input(context)
        if contract == DECLARATION_TARGET_INVENTORY_REF:
            return encode_declaration_target_inventory(inventory)
        if contract == SEMANTIC_CANDIDATE_LISTING_REF:
            return encode_semantic_candidate_listing(binding.candidates)
        if contract == SOURCE_SELECTION_REF and selection is not None:
            return encode_source_selection(selection)
        if contract == SOURCE_ORIGIN_REF and source_origin is not None:
            return encode_source_origin(source_origin)
        raise SourceObservationUnavailable("original_pre_request_context_unavailable")

    @contextmanager
    def original_pre_request_input(
        self, selected: WorkspaceSelectedPackageSource, *, use_ref: str,
        stage: str, source_coordinates: tuple[SemanticInputSourceCoordinate, ...],
        context_contracts: tuple[SemanticInputContextContract, ...] = (),
    ) -> Iterator[SemanticInputProductionExpectation]:
        """Keep a source-bound proposal live for Code's existing producer rail.

        Coordinates propose retained files; they do not select an owner grammar
        or grant execution. Code still admits the producer and complete roles.
        No post-authority source admission is manufactured for this earlier read.
        """
        with self._original_pre_request_input(
            selected, use_ref=use_ref, stage=stage,
            source_coordinates=source_coordinates, context_contracts=context_contracts,
        ) as expected:
            yield expected

    @contextmanager
    def _original_pre_request_input(
        self, selected: WorkspaceSelectedPackageSource, *, use_ref: str,
        stage: str, source_coordinates: tuple[SemanticInputSourceCoordinate, ...],
        context_contracts: tuple[SemanticInputContextContract, ...],
        selection_origin: _SelectedInputOrigin | None = None,
    ) -> Iterator[SemanticInputProductionExpectation]:
        selection, source_origin = self._selection_context_values(
            selected, selection_origin, context_contracts,
        )
        with self._lock:
            record = self._selected_record(selected)
            values = self._source_projection_values(selected)
            context = values[0]
            choice = record.expectation
            _, occurrence = self._occurrence(
                self.read_declaration_scope(record.declaration),
                choice.scope_key, choice.module_id, choice.package_id,
            )
            if type(context_contracts) is not tuple or any(
                type(item) is not SemanticInputContextContract
                for item in context_contracts
            ):
                raise SourceObservationUnavailable("pre_request_context_contracts_invalid")
            bodies: list[SemanticBody] = []
            for item in context_contracts:
                body = self._pre_request_context_bytes(
                    context=values[0], inventory=values[1], binding=values[3],
                    contract=item.contract,
                    selection=selection, source_origin=source_origin,
                )
                digest = ContentDigest.of_bytes(body)
                bodies.append(SemanticBody(SemanticValueCoordinate(
                    item.role, item.contract, f"workspace-context:{digest.value}",
                    digest, len(body),
                ), body))
            expected = SemanticInputProductionExpectation.create(
                use_ref=use_ref,
                operation_ref=record.declaration_record.expectation.operation_identity,
                stage=stage,
                package_identity=SemanticInputPackageIdentity(
                    context.package, cast(str, _claim(occurrence.semantic_package_name)),
                ),
                operation_identity=self._exclusion._parent,
                source_identity=selected,
                source_coordinates=copy.deepcopy(source_coordinates),
                context_bodies=tuple(bodies),
            )
            # Immutable qualified data indexes private state; authority remains
            # the retained selected handle/record by identity. Cleanup never
            # hashes a restamped nominal handle or calls its foreign behavior.
            key = (choice.scope_key, choice.module_id, choice.package_id, expected.use_ref)
            retained = _PreRequestInputRecord(
                selected, record, expected, expected.input_digest.value, threading.get_ident(),
                selection_origin=selection_origin,
            )
        with self._exclusion.mutation(), self._lock:
            if key in self._pre_request_inputs or key in self._retired_pre_request_inputs:
                raise SourceObservationUnavailable("pre_request_input_replayed")
            if self._selected_record(selected) is not record:
                raise SourceObservationUnavailable("pre_request_source_changed")
            self._pre_request_inputs[key] = retained
            self._retired_pre_request_inputs.add(key)
        try:
            self.validate_semantic_input_source(selected, expected=expected)
            yield expected
            self.validate_semantic_input_source(selected, expected=expected)
        finally:
            retained.live = False
            retained.selection_origin = None
            with self._exclusion.mutation(retiring=True), self._lock:
                self._pre_request_inputs.pop(key, None)

    def _pre_request_record(
        self, selected: object, expected: SemanticInputProductionExpectation,
    ) -> _PreRequestInputRecord:
        record = self._selected_record(cast(WorkspaceSelectedPackageSource, selected))
        if type(expected) is not SemanticInputProductionExpectation:
            raise SourceObservationUnavailable("original_pre_request_input_required")
        retained = next((item for item in self._pre_request_inputs.values()
                         if item.expected is expected), None)
        if (
            retained is None or not retained.live
            or retained.thread_id != threading.get_ident()
            or retained.selected is not selected
            or retained.selected_record is not record
            or retained.expected is not expected
            or expected.source_identity is not selected
            or expected.operation_identity is not self._exclusion._parent
        ):
            raise SourceObservationUnavailable("original_pre_request_input_required")
        return retained

    def _selected_input_coordinates(
        self, selected: WorkspaceSelectedPackageSource, origin: _SelectedInputOrigin,
    ) -> tuple[SemanticInputSourceCoordinate, ...]:
        return self._selected_input_values(selected, origin)[1]

    def _selected_input_values(
        self, selected: WorkspaceSelectedPackageSource, origin: _SelectedInputOrigin,
    ) -> tuple[SemanticSourceSelection, tuple[SemanticInputSourceCoordinate, ...]]:
        # Code's original reader calls our full source validators. It must run
        # outside both this issuer lock and the parent publication exclusion.
        with self._lock:
            self._pre_request_record(selected, origin.expected)
        selection: SemanticSourceSelection = read_registered_semantic_input_source_selection(
            origin.host, origin.registration, source_admission=selected,
            expected=origin.expected, result=origin.result,
        )
        with self._lock:
            retained = self._pre_request_record(selected, origin.expected)
            values = self._source_projection_values(selected)
            if (selection.package != values[0].package
                or selection.source_identity_digest != values[0].source_identity_digest):
                raise SourceObservationUnavailable("selected_input_identity_differs")
            contracts = {item.role: item.contract for item in origin.source_contracts}
            if {item.role for item in selection.sources} != set(contracts) or any(
                contracts[item.role] != item.contract for item in selection.sources
            ):
                raise SourceObservationUnavailable("selected_input_contracts_differ")
            evidence = cast(WorkspaceObservedSelectedPackageEvidence, self._call(
                "selected_package_evidence", retained.selected_record.observation,
            ))
            paths = {item.relative_path: item for item in evidence.bodies}
            coordinates: list[SemanticInputSourceCoordinate] = []
            for source in selection.sources:
                body = paths.get(source.relative_path)
                if body is None or source.content_digest.value != body.content_digest:
                    raise SourceObservationUnavailable("selected_input_member_differs")
                coordinates.append(SemanticInputSourceCoordinate(
                    source.relative_path, SemanticValueCoordinate(
                        source.role, source.contract, body.body_ref,
                        ContentDigest(body.content_digest), body.size_bytes,
                    ),
                ))
            self.validate_selected_package_source(
                selected, expectation=retained.selected_record.expectation,
                binding_digest=retained.selected_record.digest,
            )
            return selection, tuple(coordinates)

    def _selection_context_values(
        self, selected: WorkspaceSelectedPackageSource,
        origin: _SelectedInputOrigin | None,
        contracts: tuple[SemanticInputContextContract, ...],
        *, selected_values: tuple[
            SemanticSourceSelection, tuple[SemanticInputSourceCoordinate, ...],
        ] | None = None,
    ) -> tuple[SemanticSourceSelection | None, SemanticInputSourceOrigin | None]:
        if type(contracts) is not tuple or any(
            type(item) is not SemanticInputContextContract for item in contracts
        ):
            raise SourceObservationUnavailable("pre_request_context_contracts_invalid")
        if not any(item.contract in (SOURCE_SELECTION_REF, SOURCE_ORIGIN_REF)
                   for item in contracts):
            return None, None
        if origin is None:
            raise SourceObservationUnavailable("original_pre_request_context_unavailable")
        selection, coordinates = (
            self._selected_input_values(selected, origin)
            if selected_values is None else selected_values
        )
        if not any(item.contract == SOURCE_ORIGIN_REF for item in contracts):
            return selection, None
        with self._lock:
            record = self._selected_record(selected)
            evidence = cast(WorkspaceObservedSelectedPackageEvidence, self._call(
                "selected_package_evidence", record.observation,
            ))
            # Follow only the actual retained predecessor associations. An
            # unrelated live scope with a matching path cannot supply origin.
            ancestor = self._pre_request_record(selected, origin.expected)
            seen: list[_PreRequestInputRecord] = []
            while True:
                if any(ancestor is prior for prior in seen):
                    raise SourceObservationUnavailable("selected_input_origin_cycle")
                seen.append(ancestor)
                outer = tuple(source for source in ancestor.expected.source_coordinates
                              if source.relative_path == evidence.manifest_relative_path)
                if len(outer) == 1:
                    break
                if outer or ancestor.selection_origin is None:
                    raise SourceObservationUnavailable("original_outer_manifest_unavailable")
                ancestor = self._pre_request_record(selected, ancestor.selection_origin.expected)
            occurrence = SemanticInputPackageOccurrence(
                evidence.repository_binding_ref, evidence.workspace_manifest_path,
                evidence.module_id, evidence.package_id,
                "" if evidence.package_root == "." else evidence.package_root,
                evidence.manifest_relative_path,
            )
        # The captured reader checks the original location through its admitted
        # descriptor. Full source/Code calls do not run under parent exclusion.
        window = self._semantic_source_window
        if window is not None and selected is window.selected:
            if window.location is None:
                window.location = cast(str, self._call(
                    "read_selected_package_location", record.observation,
                ))
            location = window.location
        else:
            location = cast(str, self._call("read_selected_package_location", record.observation))
        value = SemanticInputSourceOrigin(
            selection.package, selection.source_identity_digest,
            copy.deepcopy(origin.result.coordinate), selection.production_input_digest,
            occurrence, location, copy.deepcopy(outer[0]),
            tuple(SemanticInputSourceOccurrence(
                source, source_occurrence_ref(occurrence, source.relative_path),
            ) for source in coordinates),
        )
        validate_source_origin_selection(
            value, selection=selection, selection_coordinate=origin.result.coordinate,
            source_coordinates=coordinates,
        )
        with self._lock:
            if self._selected_record(selected) is not record:
                raise SourceObservationUnavailable("pre_request_source_changed")
        return selection, value

    @contextmanager
    def original_selected_source_input(
        self, selected: WorkspaceSelectedPackageSource, *,
        host: SemanticInputProducerHost,
        registration: AdmittedSemanticInputProducerRegistration,
        selection_expected: SemanticInputProductionExpectation,
        result: SemanticBody, use_ref: str, stage: str,
        source_contracts: tuple[SemanticInputSourceContract, ...],
        context_contracts: tuple[SemanticInputContextContract, ...] = (),
    ) -> Iterator[SemanticInputProductionExpectation]:
        """Bind an original owner selection to retained inputs for the next call.

        Fixed composition supplies original Code resources and declared next
        inputs. Code still admits that next producer. This scope borrows the
        producer/result and original outer scopes; it closes none of them.
        Lost origin or membership is terminal for this input, never repairable
        by supplying a portable selection or restoring source bytes.
        """
        if (type(source_contracts) is not tuple
            or any(type(item) is not SemanticInputSourceContract for item in source_contracts)
            or len({item.role for item in source_contracts}) != len(source_contracts)):
            raise SourceObservationUnavailable("selected_input_contracts_invalid")
        origin = _SelectedInputOrigin(
            host, registration, selection_expected, result, copy.deepcopy(source_contracts),
        )
        coordinates = self._selected_input_coordinates(selected, origin)
        with self._original_pre_request_input(
            selected, use_ref=use_ref, stage=stage, source_coordinates=coordinates,
            context_contracts=context_contracts,
            selection_origin=origin,
        ) as expected:
            self.validate_semantic_input_source(selected, expected=expected)
            yield expected

    def validate_semantic_input_source(
        self, source_admission: object, *, expected: SemanticInputProductionExpectation,
    ) -> None:
        """Revalidate the original pre-request source, context and parent."""
        with self._lock:
            original = next((item for item in self._pre_request_inputs.values()
                             if item.expected is expected), None)
        try:
            # Only synchronous original-result validation runs inside this
            # window. It never encloses producer execution, await or yield to
            # a semantic owner. Recursive callbacks still check every original
            # input/result; detached source projections are reused locally.
            with self._original_semantic_source_window(source_admission, expected):
                self._validate_semantic_input_source(source_admission, expected=expected)
        except BaseException:
            if original is not None:
                original.live = False
                original.selection_origin = None
            raise

    @contextmanager
    def _original_semantic_source_window(
        self, selected: object, expected: SemanticInputProductionExpectation,
    ) -> Iterator[None]:
        owns_window = False
        with self._lock:
            retained = self._pre_request_record(selected, expected)
            current = self._semantic_source_window
            if current is not None:
                if (current.thread_id != threading.get_ident()
                    or current.selected is not selected
                    or current.record is not retained.selected_record):
                    raise SourceObservationUnavailable("semantic_source_window_origin_changed")
            else:
                # Existing readers perform complete declaration/source checks.
                # Reuse starts only after both original projections agree.
                binding = self.read_selected_package_source(retained.selected)
                closure = self.read_declaration_scope(retained.selected_record.declaration)
                current = _SemanticSourceValidationWindow(
                    threading.get_ident(), retained.selected, retained.selected_record,
                    closure, binding,
                )
                self._semantic_source_window = current
                owns_window = True
        if not owns_window:
            yield
            return
        completed = False
        try:
            yield
            completed = True
        finally:
            # End reuse before final full checks, also on cancellation/failure.
            # No detached result escapes this caller until these checks pass.
            with self._lock:
                self._semantic_source_window = None
                self.read_selected_package_source(retained.selected)
                if completed:
                    self._pre_request_record(selected, expected)

    def _validate_semantic_input_source(
        self, source_admission: object, *, expected: SemanticInputProductionExpectation,
    ) -> None:
        with self._lock:
            original = next((item for item in self._pre_request_inputs.values()
                             if item.expected is expected), None)
        try:
            selection = None
            source_origin = None
            if original is not None and original.selection_origin is not None:
                with self._lock:
                    self._pre_request_record(source_admission, expected)
                selection, coordinates = self._selected_input_values(
                    original.selected, original.selection_origin,
                )
                if coordinates != expected.source_coordinates:
                    raise SourceObservationUnavailable("selected_input_coordinates_changed")
                selection, source_origin = self._selection_context_values(
                    original.selected, original.selection_origin,
                    tuple(SemanticInputContextContract(body.coordinate.role, body.coordinate.contract)
                          for body in expected.context_bodies),
                    selected_values=(selection, coordinates),
                )
        except BaseException:
            if original is not None:
                original.live = False
                original.selection_origin = None
            raise
        with self._lock:
            # Find a registered expectation by identity before rejecting changed
            # operation/source fields, so restoring them cannot resume that use.
            retained = next((item for item in self._pre_request_inputs.values()
                             if item.expected is expected), None)
            try:
                retained = self._pre_request_record(source_admission, expected)
                reproduced = SemanticInputProductionExpectation.create(
                    use_ref=expected.use_ref, operation_ref=expected.operation_ref,
                    stage=expected.stage, package_identity=expected.package_identity,
                    operation_identity=expected.operation_identity,
                    source_identity=expected.source_identity,
                    source_coordinates=expected.source_coordinates,
                    context_bodies=expected.context_bodies,
                )
                if (reproduced.input_digest.value != retained.input_digest
                    or expected.input_digest.value != retained.input_digest):
                    raise SourceObservationUnavailable("pre_request_input_changed")
                values = self._source_projection_values(retained.selected)
                context = values[0]
                if expected.package_identity.package != context.package:
                    raise SourceObservationUnavailable("pre_request_package_differs")
                evidence = cast(WorkspaceObservedSelectedPackageEvidence, self._call(
                    "selected_package_evidence", retained.selected_record.observation,
                ))
                paths = {item.relative_path: item for item in evidence.bodies}
                for source in expected.source_coordinates:
                    item = paths.get(source.relative_path)
                    if item is None or (
                        source.coordinate.value_ref != item.body_ref
                        or source.coordinate.digest.value != item.content_digest
                        or source.coordinate.size_bytes != item.size_bytes
                    ):
                        raise SourceObservationUnavailable("pre_request_source_differs")
                for body in expected.context_bodies:
                    if body.canonical_body != self._pre_request_context_bytes(
                        context=values[0], inventory=values[1], binding=values[3],
                        contract=body.coordinate.contract,
                        selection=selection, source_origin=source_origin,
                    ):
                        raise SourceObservationUnavailable("pre_request_context_differs")
                self.validate_selected_package_source(
                    retained.selected, expectation=retained.selected_record.expectation,
                    binding_digest=retained.selected_record.digest,
                )
            except BaseException:
                if retained is not None:
                    retained.live = False
                    retained.selection_origin = None
                raise

    def validate_semantic_input_context(
        self, source_admission: object, *, expected: SemanticInputProductionExpectation,
    ) -> None:
        self.validate_semantic_input_source(source_admission, expected=expected)

    def read_semantic_input_sources(
        self, source_admission: object, *, expected: SemanticInputProductionExpectation,
    ) -> tuple[SemanticInputSourceBody, ...]:
        self.validate_semantic_input_source(source_admission, expected=expected)
        with self._lock:
            retained = self._pre_request_record(source_admission, expected)
            try:
                bodies = tuple(SemanticInputSourceBody(
                    copy.deepcopy(source), cast(bytes, self._call(
                        "read_selected_package", retained.selected_record.observation,
                        relative_path=source.relative_path,
                    )),
                ) for source in expected.source_coordinates)
            except BaseException:
                retained.live = False
                retained.selection_origin = None
                raise
        self.validate_semantic_input_source(source_admission, expected=expected)
        return bodies

    @staticmethod
    def _match_semantic_inputs(values, expected):
        context, inventory, _, _, manifest, binding, _ = values
        if (expected.package != context.package
            or expected.source_identity_digest != context.source_identity_digest):
            raise SourceObservationUnavailable("semantic_package_context_differs")
        checks = (
            (expected.manifest_coordinate, manifest, None),
            (expected.candidate_coordinate,
             encode_semantic_candidate_listing(binding.candidates),
             SEMANTIC_CANDIDATE_LISTING_REF),
            (expected.package_context_coordinate,
             encode_package_context_input(context), PACKAGE_CONTEXT_INPUT_REF),
            (expected.declaration_inventory_coordinate,
             encode_declaration_target_inventory(inventory),
             DECLARATION_TARGET_INVENTORY_REF),
        )
        for coordinate, body, contract in checks:
            if (coordinate.digest != ContentDigest.of_bytes(body)
                or coordinate.size_bytes != len(body)
                or (contract is not None and coordinate.contract != contract)):
                raise SourceObservationUnavailable("retained_semantic_coordinate_differs")

    def issue_source_planning_pair(self, selected, *, context, expected):
        return self._issue_semantic_pair(selected, context=context, expected=expected,
                                         stage="source_planning")

    def issue_authority_pair(self, selected, *, context, expected):
        return self._issue_semantic_pair(selected, context=context, expected=expected,
                                         stage="authority_derivation")

    def _retain_targets(self, selected, addresses):
        existing = self._selected_targets.get(selected)
        if existing is not None:
            if tuple((item.address, item.context.package.package_ref)
                     for item in existing) != addresses:
                raise SourceObservationUnavailable("direct_target_set_changed")
            for item in existing:
                self._target_source(item.membership)
            return existing
        source = self._selected_record(selected)
        retained = []
        try:
            for address, package_ref in addresses:
                observation = self._source.observe_selected_package(
                    declaration=source.declaration_record.observation,
                    workspace_manifest_path=address[0],
                    module_id=address[1], package_id=address[2],
                )
                handle = None
                try:
                    handle = self.bind_selected_package_source(
                        declaration=source.declaration, selected=observation
                    )
                    context = self._semantic_values(handle)[0]
                    if context.package.package_ref != package_ref:
                        raise SourceObservationUnavailable("direct_target_coordinate_changed")
                    retained.append(_V3TargetRecord(
                        handle, observation, context, address
                    ))
                except BaseException:
                    if handle is not None:
                        self.release_selected_package_source(handle)
                    self._source.release_selected_package(observation)
                    raise
        except BaseException:
            for item in reversed(retained):
                self.release_selected_package_source(item.membership)
                self._source.release_selected_package(item.observation)
            raise
        result = tuple(retained)
        self._selected_targets[selected] = result
        self._target_records.update((item.membership, item) for item in result)
        return result

    def _target_source(self, target):
        record = self._target_records.get(target)
        if record is None:
            raise SourceObservationUnavailable("foreign_direct_target")
        context = self._semantic_values(record.membership)[0]
        binding = self.read_selected_package_source(record.membership)
        if (
            context != record.context
            or (binding.expectation.scope_key, binding.expectation.module_id,
                binding.expectation.package_id) != record.address
        ):
            raise SourceObservationUnavailable("direct_target_source_changed")
        return record

    def _issue_semantic_pair(self, selected, *, context, expected, stage):
        with self._lock:
            if (type(expected) is not RetainedSemanticAdmissionExpectation
                or expected.stage != stage or expected.process_id != self._pid):
                raise SourceObservationUnavailable("semantic_stage_context_differs")
            self._validate_code_context(context, expected)
            if (len(self._semantic) >= 128 or any(
                operation is expected.operation_identity and prior_stage == stage
                for operation, prior_stage in self._issued_semantic
            )):
                raise SourceObservationUnavailable("semantic_issuance_replay_or_capacity")
            values = self._semantic_values(selected)
            self._match_semantic_inputs(values, expected)
            targets = self._retain_targets(selected, values[6])
            self._validate_code_context(context, expected)
            self.validate_selected_package_source(
                selected, expectation=self._selected_record(selected).expectation
            )
            record = _SemanticRecord(
                selected, _snapshot(expected), values[0], values[1],
                values[2], values[3],
                self._selected_record(selected).declaration_record.digest,
                targets,
            )
            package = object.__new__(WorkspacePackageContextAdmission)
            inventory = object.__new__(WorkspaceDeclarationInventoryAdmission)
            self._semantic[package] = self._semantic[inventory] = record
            self._semantic_contexts[package] = self._semantic_contexts[inventory] = context
            self._issued_semantic.append((expected.operation_identity, stage))
            return package, inventory

    def _validate_semantic_admission(self, admission, *, expected, kind):
        if type(admission) is not kind or admission not in self._semantic:
            raise SourceObservationUnavailable("foreign_semantic_admission")
        record = self._semantic[admission]
        if type(expected) is not RetainedSemanticAdmissionExpectation:
            raise SourceObservationUnavailable("exact_semantic_expectation_required")
        for field in fields(expected):
            original = getattr(record.expectation, field.name)
            current = getattr(expected, field.name)
            if not ((current is original) if field.name in _IDENTITIES
                    else (current == original)):
                raise SourceObservationUnavailable("semantic_admission_context_differs")
        self._validate_code_context(self._semantic_contexts[admission], expected)
        values = self._semantic_values(record.selected)
        self._match_semantic_inputs(values, expected)
        if (values[:4] != (record.context, record.inventory,
                           record.namespace, record.owned_roots)
            or self._selected_record(record.selected).declaration_record.digest
            != record.closure_digest
            or tuple((item.address, item.context.package.package_ref)
                     for item in record.targets) != values[6]):
            raise SourceObservationUnavailable("semantic_admission_source_changed")
        for target in record.targets:
            if self._target_source(target.membership) is not target:
                raise SourceObservationUnavailable("direct_target_source_changed")
        self._validate_code_context(self._semantic_contexts[admission], expected)
        return record

    def validate_package_context_admission(self, admission, *, expected):
        with self._lock:
            self._validate_semantic_admission(
                admission, expected=expected, kind=WorkspacePackageContextAdmission
            )

    def validate_declaration_inventory_admission(self, admission, *, expected):
        with self._lock:
            self._validate_semantic_admission(
                admission, expected=expected, kind=WorkspaceDeclarationInventoryAdmission
            )

    def validate_occurrence_assignments(self, admission, *, expected, namespace,
                                        owned_roots):
        with self._lock:
            record = self._validate_semantic_admission(
                admission, expected=expected, kind=WorkspacePackageContextAdmission
            )
            if namespace != record.namespace or owned_roots != record.owned_roots:
                raise SourceObservationUnavailable("occurrence_assignment_differs")

    def _bind_original_dependency_validator(self, validator) -> None:
        """Retain Code's original demand validator, never a caller callback."""
        with self._lock:
            self._check_origin()
            if self._planning_validator is None or self._dependency_validator is not None:
                raise SourceObservationUnavailable("dependency_validator_binding_unavailable")
            name = "validate_retained_dependency_operation"
            descriptor = inspect.getattr_static(validator, name)
            method = getattr(validator, name)
            if (
                not inspect.ismethod(method)
                or method.__self__ is not validator
                or method.__func__ is not descriptor
            ):
                raise SourceObservationUnavailable("original_dependency_validator_required")
            self._dependency_validator = (validator, descriptor, method)

    def _validate_dependency_inventory(self, operation, inventory_admission, *, expected):
        with self._lock:
            if (
                type(expected) is not RetainedDependencyResolutionExpectation
                or expected.demand_operation_identity is not operation
                or self._dependency_validator is None
            ):
                raise SourceObservationUnavailable("original_dependency_demand_required")
            validator, descriptor, method = self._dependency_validator
            name = "validate_retained_dependency_operation"

            def validate_demand():
                if inspect.getattr_static(validator, name) is not descriptor:
                    raise SourceObservationUnavailable("dependency_validator_substituted")
                if method(operation, expected=expected) is not None:
                    raise SourceObservationUnavailable("dependency_validator_result_invalid")
                if inspect.getattr_static(validator, name) is not descriptor:
                    raise SourceObservationUnavailable("dependency_validator_substituted")
                self._check_origin()

            validate_demand()
            record = self._validate_semantic_admission(
                inventory_admission,
                expected=expected.source_planning,
                kind=WorkspaceDeclarationInventoryAdmission,
            )
            validate_demand()
            if self._validate_semantic_admission(
                inventory_admission,
                expected=expected.source_planning,
                kind=WorkspaceDeclarationInventoryAdmission,
            ) is not record:
                raise SourceObservationUnavailable("original_inventory_changed")
            return record

    def _target_record(self, inventory_admission, expected):
        if type(expected) is not RetainedTargetExpectation:
            raise SourceObservationUnavailable("exact_target_expectation_required")
        record = self._validate_semantic_admission(
            inventory_admission,
            expected=expected.source_planning,
            kind=WorkspaceDeclarationInventoryAdmission,
        )
        matches = tuple(
            target for target in record.targets
            if target.context.package == expected.target_package
            and target.context.source_identity_digest
            == expected.target_source_identity_digest
        )
        if len(matches) != 1:
            raise SourceObservationUnavailable("original_direct_target_not_unique")
        target = matches[0]
        if self._target_source(target.membership) is not target:
            raise SourceObservationUnavailable("original_direct_target_changed")
        if self._validate_semantic_admission(
            inventory_admission,
            expected=expected.source_planning,
            kind=WorkspaceDeclarationInventoryAdmission,
        ) is not record:
            raise SourceObservationUnavailable("original_inventory_changed")
        return target

    def select_dependency_target_admission(self, *, inventory_admission, expected):
        with self._lock:
            return self._target_record(inventory_admission, expected).membership

    def validate_dependency_target_admission(
        self, admission, *, inventory_admission, expected
    ) -> None:
        with self._lock:
            target = self._target_record(inventory_admission, expected)
            if admission is not target.membership:
                raise SourceObservationUnavailable("foreign_dependency_target_admission")

    def bind_original_graph_target_validator(self, selected_sources):
        """Retain original selected handles for source-only graph relationships."""
        if type(selected_sources) is not tuple or not selected_sources:
            raise SourceObservationUnavailable("graph_target_sources_required")
        with self._lock:
            self._check_origin()
            for selected in selected_sources:
                if type(selected) is not WorkspaceSelectedPackageSource:
                    raise SourceObservationUnavailable("original_selected_source_required")
                self._semantic_values(selected)
            result = object.__new__(WorkspaceOriginalGraphTargetValidator)
            _GRAPH_TARGET_VALIDATORS[result] = (self, selected_sources, os.getpid())
            return result

    def _bind_original_resolution_resources(self, *, target_origin, catalog):
        """Use the existing Workspace resolver once Code admits its v3 target origin."""
        from .dependency_fulfillment import _WorkspaceEmptyDependencyFulfillmentRuntime
        from .dependency_resolution import _WorkspaceDependencyResolutionRuntime

        with self._lock:
            self._check_origin()
            if self._dependency_validator is None or self._dependency_resolution is not None:
                raise SourceObservationUnavailable("dependency_resolution_binding_unavailable")
            self._dependency_resolution = _WorkspaceDependencyResolutionRuntime(
                self, target_origin, catalog
            )
            self._dependency_fulfillment = _WorkspaceEmptyDependencyFulfillmentRuntime(
                self._dependency_resolution
            )

    @contextmanager
    def _original_dependency_source_window(self, inventory_admission, expected):
        """Bracket one synchronous resolution with complete source checks.

        Original handles stay live and are checked on every nested read. Cached
        detached values exist only on this issuer and thread until the final
        complete revalidation; no token or source authority escapes.
        """
        if self._dependency_source_window is not None:
            raise SourceObservationUnavailable("dependency_source_window_reentry")
        record = self._validate_semantic_admission(
            inventory_admission,
            expected=expected.source_planning,
            kind=WorkspaceDeclarationInventoryAdmission,
        )
        declaration = self._selected_record(record.selected).declaration
        closure = self.read_declaration_scope(declaration)
        bindings = {}
        handles = (record.selected, *(target.membership for target in record.targets))
        for handle in handles:
            source = self._selected_record(handle)
            binding = self._binding(source.declaration_record, source.observation)
            if (
                binding.expectation != source.expectation
                or binding.binding_digest != source.digest
            ):
                raise SourceObservationUnavailable("selected_source_binding_changed")
            bindings[handle] = (source, binding)
        self._dependency_source_window = _V3DependencySourceWindow(
            threading.get_ident(), declaration,
            self._declaration_record(declaration), closure, bindings,
        )
        try:
            yield
        finally:
            self._dependency_source_window = None
            self._validate_semantic_admission(
                inventory_admission,
                expected=expected.source_planning,
                kind=WorkspaceDeclarationInventoryAdmission,
            )

    def issue_dependency_resolution(self, operation, *, inventory_admission, expected):
        with self._lock:
            if self._dependency_resolution is None:
                raise SourceObservationUnavailable("dependency_resolution_unavailable")
            return self._dependency_resolution.issue(
                operation, inventory_admission, expected
            )

    def validate_dependency_resolution_admission(self, admission, *, expected):
        with self._lock:
            if self._dependency_resolution is None:
                raise SourceObservationUnavailable("dependency_resolution_unavailable")
            record = self._dependency_resolution.records.get(admission)
            if record is None:
                raise SourceObservationUnavailable("foreign_dependency_resolution")
            with self._original_dependency_source_window(record.inventory, expected):
                self._dependency_resolution.validate(admission, expected)

    def issue_empty_dependency_fulfillment(self, resolution_admission, *, expected):
        with self._lock:
            if self._dependency_fulfillment is None:
                raise SourceObservationUnavailable("dependency_fulfillment_unavailable")
            return self._dependency_fulfillment.issue(resolution_admission, expected)

    def _bind_original_dependency_product_publisher(self, publisher):
        """Retain borrowed HEAD/body readers on the original command issuer."""
        with self._lock:
            self._check_origin()
            if self._dependency_fulfillment is None:
                raise SourceObservationUnavailable("dependency_fulfillment_unavailable")
            self._dependency_fulfillment.bind_publisher(publisher)

    def issue_dependency_fulfillment(self, resolution_admission, *, expected):
        """Fulfill exact demands from original published heads, never supplied bodies."""
        with self._lock:
            self._check_origin()
            if self._dependency_fulfillment is None:
                raise SourceObservationUnavailable("dependency_fulfillment_unavailable")
            return self._dependency_fulfillment.issue_products(
                resolution_admission, expected
            )

    def read_dependency_products(self, admission, *, resolution_admission, expected):
        with self._lock:
            if self._dependency_fulfillment is None:
                raise SourceObservationUnavailable("dependency_fulfillment_unavailable")
            return self._dependency_fulfillment.read(
                admission, resolution_admission, expected
            )

    def issue_empty_dependency_products(
        self, operation, *, inventory_admission, expected
    ):
        """Use the original Code demand and Workspace source validation windows."""
        from aware_code_retained_registry_policy_runtime.retained_demand_operation import (
            dependency_resolution_validation_session,
        )

        with self._lock, dependency_resolution_validation_session(operation):
            with self._original_dependency_source_window(inventory_admission, expected):
                resolution = self.issue_dependency_resolution(
                    operation,
                    inventory_admission=inventory_admission,
                    expected=expected,
                )
                fulfillment = self.issue_empty_dependency_fulfillment(
                    resolution, expected=expected
                )
                body = self.read_dependency_products(
                    fulfillment,
                    resolution_admission=resolution,
                    expected=expected,
                )
                return resolution, fulfillment, body

    def validate_dependency_fulfillment_admission(
        self, admission, *, resolution_admission, expected
    ):
        with self._lock:
            if self._dependency_fulfillment is None:
                raise SourceObservationUnavailable("dependency_fulfillment_unavailable")
            if type(expected) is not RetainedDependencyFulfillmentExpectation:
                raise SourceObservationUnavailable("exact_fulfillment_expectation_required")
            record = self._dependency_resolution.records.get(resolution_admission)
            if record is None:
                raise SourceObservationUnavailable("foreign_dependency_resolution")
            with self._original_dependency_source_window(
                record.inventory, expected.resolution
            ):
                self._dependency_fulfillment.validate(
                    admission, resolution_admission, expected
                )

    def release_dependency_targets(self) -> None:
        """Retire owned target observations before the command parent closes."""
        with self._lock:
            self._check_origin()
            if self._dependency_fulfillment is not None:
                self._dependency_fulfillment.close()
            if self._dependency_resolution is not None:
                self._dependency_resolution.close()
            for target in reversed(tuple(self._target_records.values())):
                self.release_selected_package_source(target.membership)
                self._source.release_selected_package(target.observation)
            self._target_records.clear()
            self._selected_targets.clear()

    def release_selected_package_source(
        self, handle: WorkspaceSelectedPackageSource
    ) -> None:
        self._check_origin(retiring=True)
        with self._exclusion.mutation(retiring=True):
            with self._lock:
                if (
                    type(handle) is not WorkspaceSelectedPackageSource
                    or handle not in self._selected
                ):
                    raise SourceObservationUnavailable("foreign_selected_source")
                del self._selected[handle]
                for key, retained in tuple(self._pre_request_inputs.items()):
                    if retained.selected is handle:
                        self._pre_request_inputs.pop(key)
                        retained.live = False
                        retained.selection_origin = None

    def release_declaration_scope(self, handle: WorkspaceDeclarationScope) -> None:
        self._check_origin(retiring=True)
        with self._exclusion.mutation(retiring=True):
            with self._lock:
                if (
                    type(handle) is not WorkspaceDeclarationScope
                    or handle not in self._declarations
                ):
                    raise SourceObservationUnavailable("foreign_declaration_scope")
                if any(
                    record.declaration is handle
                    for record in self._selected.values()
                ):
                    raise SourceObservationUnavailable("selected_source_still_live")
                del self._declarations[handle]

    def close(self) -> None:
        self._check_origin(retiring=True)
        if self._target_records:
            self.release_dependency_targets()
        if self._dependency_fulfillment is not None:
            self._dependency_fulfillment.close()
        if self._dependency_resolution is not None:
            self._dependency_resolution.close()
        with self._exclusion.mutation(retiring=True):
            with self._lock:
                self._selected.clear()
                for record in self._pre_request_inputs.values():
                    record.live = False
                    record.selection_origin = None
                self._pre_request_inputs.clear()
                self._retired_pre_request_inputs.clear()
                self._semantic.clear()
                self._semantic_contexts.clear()
                self._issued_semantic.clear()
                self._declarations.clear()
                self._closed = True
