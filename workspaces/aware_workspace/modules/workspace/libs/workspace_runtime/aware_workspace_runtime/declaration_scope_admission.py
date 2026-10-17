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
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, fields, replace
from pathlib import PurePosixPath
from typing import Any, NamedTuple, cast
from weakref import WeakKeyDictionary

from aware_code_module_manifest_contract_runtime import (
    AwareModuleSpecV3,
    parse_module_manifest,
)
from aware_code_semantic_contract_runtime import (
    SemanticDependencyTargetConstraint,
    encode_semantic_candidate_listing,
)
from aware_code_semantic_contract_runtime import (
    retained_declaration_scope_codec as _declaration_codec,
)
from aware_code_semantic_contract_runtime import (
    retained_declaration_scope_validation as _declaration_validation,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    SemanticContractRef,
    SemanticPackageCoordinate,
    SemanticValueCoordinate,
)
from aware_code_semantic_contract_runtime.dependency_admission_interfaces import (
    RetainedDependencyFulfillmentExpectation,
    RetainedDependencyResolutionExpectation,
    RetainedProductPlanningExpectation,
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
    validate_registered_semantic_input_result,
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
class WorkspaceSelectedSourceInputV1:
    """Borrow an original Code selection; construction grants no admission."""

    selected: WorkspaceSelectedPackageSource
    host: SemanticInputProducerHost
    registration: AdmittedSemanticInputProducerRegistration
    selection_expected: SemanticInputProductionExpectation
    result: SemanticBody
    source_contracts: tuple[SemanticInputSourceContract, ...]


@dataclass(frozen=True, slots=True)
class WorkspaceSelectedDependencyInputV1:
    """Compare an original declared edge and target under their owner's lifetime."""

    owner: WorkspaceSelectedPackageSource
    target: WorkspaceSelectedPackageSource
    inventory_admission: WorkspaceDeclarationInventoryAdmission
    expected: RetainedTargetExpectation
    dependency_kind: str
    dependency_ref: str


_GROUP_MEMBER_FIELDS = (
    "selected",
    "host",
    "registration",
    "selection_expected",
    "result",
    "source_contracts",
)
_GROUP_EDGE_FIELDS = (
    "owner",
    "target",
    "inventory_admission",
    "expected",
    "dependency_kind",
    "dependency_ref",
)
_GROUP_MEMBER_SLOTS = tuple(
    inspect.getattr_static(WorkspaceSelectedSourceInputV1, name)
    for name in _GROUP_MEMBER_FIELDS
)
_GROUP_EDGE_SLOTS = tuple(
    inspect.getattr_static(WorkspaceSelectedDependencyInputV1, name)
    for name in _GROUP_EDGE_FIELDS
)


def _group_fields(value, kind, names, descriptors):
    # Recognize exact nominal inputs before accessing fields. Never dispatch a
    # substituted slot, foreign property, iteration or equality implementation.
    if type(value) is not kind or any(
        inspect.getattr_static(kind, name, None) is not descriptor
        for name, descriptor in zip(names, descriptors, strict=True)
    ):
        raise SourceObservationUnavailable("grouped_input_exact_type_required")
    try:
        return tuple(descriptor.__get__(value, kind) for descriptor in descriptors)
    except AttributeError as exc:
        raise SourceObservationUnavailable("grouped_input_fields_required") from exc


@dataclass(slots=True)
class _GroupedInputOrigin:
    members: tuple[tuple[WorkspaceSelectedSourceInputV1, tuple[Any, ...]], ...]
    edges: tuple[tuple[WorkspaceSelectedDependencyInputV1, tuple[Any, ...]], ...]
    declaration_requested: bool = False
    declaration_handle: WorkspaceDeclarationScope | None = None
    declaration_record: _DeclarationRecord | None = None
@dataclass(frozen=True, slots=True)
class _DeclarationRecord:
    observation: WorkspaceRetainedDeclarationObservation
    source_record: WorkspaceObservedDeclarationEvidence
    expectation: CodeDeclarationScopeExpectation
    consumer_scope_key: str
    digest: ContentDigest
    projection: CodeRetainedDependencyScopeClosureV3


class _DeclarationOrigin(NamedTuple):
    # Tuple fields cannot be restamped with object.__setattr__. In particular,
    # the digest string and consumer are independent of the mutable record and
    # all objects reachable through its projection.
    handle: WorkspaceDeclarationScope
    record: _DeclarationRecord
    observation: WorkspaceRetainedDeclarationObservation
    source_record: WorkspaceObservedDeclarationEvidence
    source_digest: str
    expectation: CodeDeclarationScopeExpectation
    expectation_fields: tuple[str, str, int, str, str]
    consumer_scope_key: str
    projection: CodeRetainedDependencyScopeClosureV3
    projection_digest: str
    projection_coordinate: _declaration_validation.RetainedDeclarationScopeCoordinate


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
    expectation: RetainedSemanticAdmissionExpectation | RetainedProductPlanningExpectation
    context: CodeSemanticPackageContextInput
    inventory: CodeSemanticDeclarationTargetInventory
    namespace: str
    owned_roots: tuple[str, ...]
    closure_digest: ContentDigest
    targets: tuple[_V3TargetRecord, ...]
    product_dependency: RetainedDependencyResolutionExpectation | None = None

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
    grouped_origin: _GroupedInputOrigin | None = None


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
        if (
            type(package) is not SemanticPackageCoordinate
            or type(target) is not SemanticDependencyTarget
            or type(dependency_kind) is not str or type(dependency_ref) is not str
        ):
            raise SourceObservationUnavailable("original_graph_target_coordinates_required")
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
            # Source-only graph planning already retains the selected target
            # under this issuer and command. Verify that original occurrence
            # directly; this does not mint a dependency-resolution admission.
            selected_targets = tuple(
                handle for handle in selected
                if issuer._semantic_values(handle)[0].package == target.package
            )
            if selected_targets:
                if len(selected_targets) != 1:
                    raise SourceObservationUnavailable("graph_target_membership_differs")
                selected_target, = selected_targets
                if issuer._semantic_values(selected_target)[3] != target.semantic_root_refs:
                    raise SourceObservationUnavailable("graph_target_roots_differ")
                if issuer._semantic_values(owner)[1] != inventory:
                    raise SourceObservationUnavailable("graph_target_declaration_differs")
                return
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


def _bind_original_code_result_validator(original):
    """Retain Code's callable in a closure, independently of mutable aliases."""
    workspace_namespace = globals()
    code_namespace = original.__globals__

    def invoke(self, host, registration, *, source_admission, expected, result):
        try:
            if (workspace_namespace.get("validate_registered_semantic_input_result") is not original
                or code_namespace.get("validate_registered_semantic_input_result") is not original):
                raise SourceObservationUnavailable("original_code_result_validator_changed")
            original(
                host, registration, source_admission=source_admission,
                expected=expected, result=result,
            )
            if (workspace_namespace.get("validate_registered_semantic_input_result") is not original
                or code_namespace.get("validate_registered_semantic_input_result") is not original):
                raise SourceObservationUnavailable("original_code_result_validator_changed")
        finally:
            del self, host, registration, source_admission, expected, result

    return invoke


def _bind_original_declaration_coordinate_entrances():
    namespace = vars(_declaration_validation)
    capture = _declaration_validation.capture_retained_declaration_scope
    validate = _declaration_validation.validate_retained_declaration_scope_coordinate
    detached = _declaration_validation.validate_detached_declaration_scope_coordinate
    copy_value = _declaration_validation.copy_retained_declaration_scope
    binding_capture = _declaration_validation.capture_selected_source_binding_coordinate
    binding_validate = _declaration_validation.validate_selected_source_binding_coordinate
    coordinate_type = _declaration_validation.RetainedDeclarationScopeCoordinate
    capture_code, validate_code = capture.__code__, validate.__code__
    detached_code = detached.__code__
    binding_capture_code, binding_validate_code = binding_capture.__code__, binding_validate.__code__
    # Independently retain the complete callable origins before any owner IO.
    # This also authenticates optional native delegation cells at terminal return.
    callable_origins = tuple(
        (function, function.__code__, function.__defaults__, function.__kwdefaults__,
         function.__closure__,
         () if function.__closure__ is None else tuple(
             cell.cell_contents for cell in function.__closure__
         ),
         () if function.__kwdefaults__ is None else tuple(function.__kwdefaults__.items()))
        for function in (capture, validate, detached, binding_capture, binding_validate, copy_value)
    )

    def origins():
        for function, code, defaults, keywords, cells, contents, keyword_items in callable_origins:
            if (function.__code__ is not code
                or function.__defaults__ is not defaults
                or function.__kwdefaults__ is not keywords
                or function.__closure__ is not cells
                or (cells is not None and any(
                    cell.cell_contents is not expected
                    for cell, expected in zip(cells, contents, strict=True)
                ))
                or (keywords is not None and (
                    len(keywords) != len(keyword_items)
                    or any(key is not old_key or value is not old_value
                           for (key, value), (old_key, old_value)
                           in zip(keywords.items(), keyword_items, strict=True))
                ))):
                raise SourceObservationUnavailable("original_declaration_coordinate_validator_changed")
        if (namespace.get("capture_retained_declaration_scope") is not capture
            or namespace.get("validate_retained_declaration_scope_coordinate") is not validate
            or namespace.get("validate_detached_declaration_scope_coordinate") is not detached
            or namespace.get("copy_retained_declaration_scope") is not copy_value
            or namespace.get("capture_selected_source_binding_coordinate") is not binding_capture
            or namespace.get("validate_selected_source_binding_coordinate") is not binding_validate
            or capture.__code__ is not capture_code or validate.__code__ is not validate_code
            or detached.__code__ is not detached_code
            or binding_capture.__code__ is not binding_capture_code
            or binding_validate.__code__ is not binding_validate_code):
            raise SourceObservationUnavailable("original_declaration_coordinate_validator_changed")

    def issue(self, value):
        try:
            origins()
            coordinate = capture(value)
            origins()
            return coordinate
        finally:
            del self, value

    def check(self, origin, value=None):
        try:
            origins()
            coordinate = origin.projection_coordinate
            if (type(coordinate) is not coordinate_type
                or tuple.__getitem__(coordinate, 0) is not origin.projection
                or type(tuple.__getitem__(coordinate, 1)) is not str
                or tuple.__getitem__(coordinate, 1) != origin.projection_digest):
                raise SourceObservationUnavailable("declaration_projection_changed")
            try:
                validate(coordinate, origin.projection)
                if value is not None:
                    detached(coordinate, value)
                    origins()
                    # Detached comparison may observe callbacks or mutation.
                    # Recheck the complete original commitment at this boundary.
                    validate(coordinate, origin.projection)
            except ContractViolation as error:
                raise SourceObservationUnavailable("declaration_projection_changed") from error
            origins()
        except BaseException:
            # Retire only this original family. The borrowed source observer
            # and unrelated declarations remain owned by their original owner.
            if (type(origin) is _DeclarationOrigin
                and any(item is origin for item in self._declaration_origins)
                and not any(item is origin.record for item in self._retired_declaration_records)):
                self._retired_declaration_records.append(origin.record)
            raise
        finally:
            del self, origin, value

    def binding_issue(self, value):
        try:
            origins()
            coordinate = binding_capture(value)
            origins()
            return coordinate
        finally:
            del self, value

    def binding_check(self, coordinate, value, *, detached):
        try:
            origins()
            binding_validate(coordinate, value, detached=detached)
            origins()
        except ContractViolation as error:
            raise SourceObservationUnavailable("selected_source_binding_changed") from error
        finally:
            del self, coordinate, value, detached

    def copy_declaration(self, origin, value):
        result = None
        try:
            origins()
            try:
                result = copy_value(value)
            except ContractViolation as error:
                raise SourceObservationUnavailable("declaration_projection_changed") from error
            origins()
            return result
        except BaseException:
            if (type(origin) is _DeclarationOrigin
                and any(item is origin for item in self._declaration_origins)
                and not any(item is origin.record for item in self._retired_declaration_records)):
                self._retired_declaration_records.append(origin.record)
            raise
        finally:
            del self, origin, value, result

    return issue, check, binding_issue, binding_check, copy_declaration


def _bind_source_origin_checks(kind):
    namespace = type.__getattribute__(kind, "__dict__")
    dictionary = namespace["__dict__"]
    lookup = dict.get
    ismethod = inspect.ismethod

    def readers(self):
        source = self._source
        if type(source) is not kind or namespace.get("__dict__") is not dictionary:
            raise SourceObservationUnavailable("declaration_reader_origin_changed")
        instance = dictionary.__get__(source, kind)
        for name, (descriptor, method) in self._methods.items():
            if (
                not ismethod(method)
                or method.__self__ is not source
                or method.__func__ is not descriptor
                or namespace.get(name) is not descriptor
                or lookup(instance, name, descriptor) is not descriptor
            ):
                raise SourceObservationUnavailable("declaration_reader_origin_changed")

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
        readers(self)

    def _check_origin_locked(
        self, guard: WorkspaceCatalogEpochExclusionGuard
    ) -> None:
        """Check the retained issuer under an existing parent guard only."""
        self._exclusion.check_locked(guard)
        if os.getpid() != self._pid:
            raise SourceObservationUnavailable("declaration_process_changed")
        if self._closed or self._source._exclusion is not self._exclusion:
            raise SourceObservationUnavailable("declaration_scope_closed_or_replaced")
        readers(self)

    return _check_origin, _check_origin_locked


def _bind_group_method_check(kind, descriptors):
    namespace = type.__getattribute__(kind, "__dict__")
    dictionary = namespace["__dict__"]
    lookup = dict.get

    def check(issuer):
        if type(issuer) is not kind:
            raise SourceObservationUnavailable("original_grouped_issuer_required")
        # Authenticate the dictionary descriptor before accessing it. No live
        # descriptor, instance attribute or general MRO lookup is dispatched.
        if namespace.get("__dict__") is not dictionary:
            raise SourceObservationUnavailable("grouped_issuer_method_substituted")
        instance = dictionary.__get__(issuer, kind)
        if any(
            namespace.get(name) is not original
            or lookup(instance, name, original) is not original
            for name, original in descriptors
        ):
            raise SourceObservationUnavailable("grouped_issuer_method_substituted")

    return check


def _bind_original_group_method(check, descriptors, functions):
    namespace = globals()
    originals = tuple(functions.items())

    def origins():
        if (namespace.get("_check_group_methods") is not check
            or namespace.get("_GROUP_METHOD_DESCRIPTORS") is not descriptors
            or namespace.get("_GROUP_METHOD_FUNCTIONS") is not functions
            or namespace.get("_original_group_method") is not invoke):
            raise SourceObservationUnavailable("grouped_issuer_method_substituted")

    def invoke(issuer, name: str, *args, **kwargs):
        """Keep original dispatch independent of mutable lookup aliases."""
        origins()
        if type(name) is not str:
            raise SourceObservationUnavailable("grouped_issuer_method_substituted")
        method = next((method for key, method in originals if key == name), None)
        if method is None or functions.get(name) is not method:
            raise SourceObservationUnavailable("grouped_issuer_method_substituted")
        check(issuer)
        value = method(issuer, *args, **kwargs)
        origins()
        if functions.get(name) is not method:
            raise SourceObservationUnavailable("grouped_issuer_method_substituted")
        check(issuer)
        return value

    return invoke


def _build_declaration_scope_runtime():
    class WorkspaceDeclarationScopeRuntime:
        """Borrow the original observer and parent exclusion, owning only new handles."""

        _call_original_code_result_validator = _bind_original_code_result_validator(
            validate_registered_semantic_input_result,
        )
        (_capture_original_declaration_coordinate,
         _check_original_declaration_coordinate,
         _capture_original_binding_coordinate,
         _check_original_binding_coordinate,
         _copy_original_declaration_scope) = _bind_original_declaration_coordinate_entrances()

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
            self._declaration_origins: list[_DeclarationOrigin] = []
            self._retired_declaration_records: list[_DeclarationRecord] = []
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

        _check_origin, _check_origin_locked = _bind_source_origin_checks(
            WorkspaceSourceObservationRuntime,
        )

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
            *,
            _bracketed_origin: _DeclarationOrigin | None = None,
        ) -> CodeRetainedDependencyScopeClosureV3:
            # Interpretation belongs to the original admission. Every caller still
            # performs its original live/retained-byte rereads around this projection.
            # Never expose the private projection itself or use it as currentness.
            for origin in self._declaration_origins:
                if (
                    origin.observation is observation
                    and origin.consumer_scope_key == consumer_scope_key
                ):
                    original = origin.record
                    self._checked_declaration_origin(original)
                    if _bracketed_origin is None:
                        self._call("read_declarations", observation)
                    elif _bracketed_origin is not origin:
                        raise SourceObservationUnavailable("declaration_copy_origin_differs")
                    self._checked_declaration_origin(original)
                    if (
                        type(original.projection) is not CodeRetainedDependencyScopeClosureV3
                    ):
                        raise SourceObservationUnavailable("declaration_projection_changed")
                    _original_group_method(self, "_check_original_declaration_coordinate", origin)
                    detached = _original_group_method(
                        self, "_copy_original_declaration_scope", origin, original.projection,
                    )
                    self._check_declaration_projection_result(origin, detached)
                    return detached
            if _bracketed_origin is not None:
                raise SourceObservationUnavailable("declaration_copy_origin_differs")
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
                closure.closure_digest, closure,
            )
            handle = object.__new__(WorkspaceDeclarationScope)
            origin = _DeclarationOrigin(
                handle, record, observation, original, original.observation_digest,
                expectation,
                (
                    expectation.repository_binding_ref, expectation.parent_identity,
                    expectation.process_id, expectation.operation_identity,
                    expectation.epoch_identity,
                ),
                consumer_scope_key, closure, closure.closure_digest.value,
                _original_group_method(self, "_capture_original_declaration_coordinate", closure),
            )
            _original_group_method(self, "_check_original_declaration_coordinate", origin)
            with self._exclusion.mutation() as guard:
                with self._lock:
                    self._check_origin()
                    self._call(
                        "_check_declaration_record_locked", observation,
                        guard=guard, expected_record=original,
                    )
                    self._declarations[handle] = record
                    self._declaration_origins.append(origin)
            return handle

        def _checked_declaration_origin(self, record: _DeclarationRecord) -> _DeclarationOrigin:
            origin = next(
                (item for item in self._declaration_origins if item.record is record), None
            )
            if (origin is None or self._declarations.get(origin.handle) is not record
                or any(item is record for item in self._retired_declaration_records)):
                raise SourceObservationUnavailable("declaration_projection_changed")
            if (
                type(record) is not _DeclarationRecord
                or record.observation is not origin.observation
                or record.source_record is not origin.source_record
                or type(record.source_record) is not WorkspaceObservedDeclarationEvidence
                or type(record.source_record.observation_digest) is not str
                or record.source_record.observation_digest != origin.source_digest
                or record.expectation is not origin.expectation
                or type(record.expectation) is not CodeDeclarationScopeExpectation
                or type(record.consumer_scope_key) is not str
                or record.consumer_scope_key != origin.consumer_scope_key
                or record.projection is not origin.projection
                or type(record.projection) is not CodeRetainedDependencyScopeClosureV3
                or type(record.digest) is not ContentDigest
                or type(record.digest.value) is not str
                or record.digest.value != origin.projection_digest
            ):
                raise SourceObservationUnavailable("declaration_projection_changed")
            expectation_fields = (
                record.expectation.repository_binding_ref, record.expectation.parent_identity,
                record.expectation.process_id, record.expectation.operation_identity,
                record.expectation.epoch_identity,
            )
            if (
                any(type(value) is not type(expected) for value, expected in
                    zip(expectation_fields, origin.expectation_fields, strict=True))
                or expectation_fields != origin.expectation_fields
            ):
                raise SourceObservationUnavailable("declaration_projection_changed")
            return origin

        def _declaration_record(
            self, handle: WorkspaceDeclarationScope
        ) -> _DeclarationRecord:
            self._check_origin()
            if type(handle) is not WorkspaceDeclarationScope:
                raise SourceObservationUnavailable("foreign_declaration_scope")
            record = self._declarations.get(handle)
            if record is None:
                raise SourceObservationUnavailable("foreign_declaration_scope")
            if self._checked_declaration_origin(record).handle is not handle:
                raise SourceObservationUnavailable("declaration_projection_changed")
            with self._source._lock:
                if (
                    self._source._declaration_evidence(record.observation)
                    is not record.source_record
                ):
                    raise SourceObservationUnavailable("declaration_source_replaced")
            return record

        def _check_declaration_projection_result(
            self,
            origin: _DeclarationOrigin,
            value: CodeRetainedDependencyScopeClosureV3,
        ) -> None:
            # The detached copy must match the admission even if a transient
            # mutation restored the private projection and record before this check.
            if (
                self._checked_declaration_origin(origin.record) is not origin
                or type(value) is not CodeRetainedDependencyScopeClosureV3
            ):
                raise SourceObservationUnavailable("declaration_projection_changed")
            _original_group_method(self, "_check_original_declaration_coordinate", origin, value)
            # Recheck original custody after copying/encoding and at terminal return.
            if (
                self._declaration_record(origin.handle) is not origin.record
                or self._checked_declaration_origin(origin.record) is not origin
            ):
                raise SourceObservationUnavailable("declaration_projection_changed")

        def read_declaration_scope(
            self, handle: WorkspaceDeclarationScope
        ) -> CodeRetainedDependencyScopeClosureV3:
            with self._lock:
                record = self._declaration_record(handle)
                origin = self._checked_declaration_origin(record)
                semantic_window = self._semantic_source_window
                if semantic_window is not None:
                    if semantic_window.thread_id != threading.get_ident():
                        raise SourceObservationUnavailable("semantic_source_window_thread_changed")
                    if handle is semantic_window.record.declaration:
                        if record is not semantic_window.record.declaration_record:
                            raise SourceObservationUnavailable("declaration_source_replaced")
                        _original_group_method(self, "_check_original_declaration_coordinate", origin, semantic_window.closure)
                        detached = _original_group_method(
                            self, "_copy_original_declaration_scope", origin, semantic_window.closure,
                        )
                        self._check_declaration_projection_result(origin, detached)
                        return detached
                window = self._dependency_source_window
                if (
                    window is not None
                    and window.thread_id == threading.get_ident()
                    and handle is window.declaration
                ):
                    if record is not window.declaration_record:
                        raise SourceObservationUnavailable("declaration_source_replaced")
                    detached = _original_group_method(
                        self, "_copy_original_declaration_scope", origin, window.closure,
                    )
                    self._check_declaration_projection_result(origin, detached)
                    return detached
                self._call("revalidate_declarations", record.observation)
                # The original byte revalidations bracket this reconstruction.
                # Copy the already admitted interpretation rather than deliver
                # and discard the complete retained declaration bodies again.
                closure = _original_group_method(
                    self, "_closure", record.observation, record.consumer_scope_key,
                    _bracketed_origin=origin,
                )
                self._call("revalidate_declarations", record.observation)
                self._check_origin()
                self._check_declaration_projection_result(origin, closure)
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
            return _original_group_method(self, "_source_projection_pair", record, selected)[0]

        def _source_projection_pair(
            self,
            record: _DeclarationRecord,
            selected: WorkspaceRetainedSelectedPackageObservation,
        ) -> tuple[CodeSelectedPackageSourceBinding, CodeRetainedDependencyScopeClosureV3]:
            """Keep the declaration copy already used to derive this binding."""
            origin = self._checked_declaration_origin(record)
            evidence = self._call("selected_package_evidence", selected)
            # Original selected-source validation brackets every admitted use
            # of this private reconstruction, including the owning window's
            # terminal check. No extra declaration delivery supplies its bytes.
            closure = _original_group_method(
                self, "_closure", record.observation, record.consumer_scope_key,
                _bracketed_origin=origin,
            )
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
                ContentDigest.of_wire(origin.projection_digest),
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
            result = CodeSelectedPackageSourceBinding(expectation, candidates)
            _original_group_method(self, "_check_declaration_projection_result", origin, closure)
            return result, closure

        def _read_source_projection_pair(
            self, handle: WorkspaceSelectedPackageSource, *, terminal: bool,
            closing: _SemanticSourceValidationWindow | None = None,
        ) -> tuple[CodeSelectedPackageSourceBinding, CodeRetainedDependencyScopeClosureV3]:
            """Read an original pair; only its owning window may defer closing.

        With terminal=False these are provisional setup values. The synchronous
        semantic validation window must perform its full closing source read and
        immutable checks before returning. No owner execution or await is allowed.
        An original owning window may close after reconstruction instead of
        starting another standalone before/after bracket. Its entry check has
        already run; the terminal selected-source check below remains mandatory.
        """
            if type(terminal) is not bool:
                raise TypeError("exact terminal-check mode required")
            with self._lock:
                record = self._selected_record(handle)
                origin = self._checked_declaration_origin(record.declaration_record)
                if closing is None:
                    self._call("revalidate_selected_package", record.observation)
                else:
                    if (not terminal
                        or type(closing) is not _SemanticSourceValidationWindow
                        or self._semantic_source_window is not closing):
                        raise SourceObservationUnavailable("semantic_source_window_origin_changed")
                    # Only the original window can spend its closing path.
                    # Its mutable metadata must not dispatch a descriptor or
                    # select the source. Use the original handle/record above;
                    # the owner checks its independent entry journals below.
                    # Disable reuse before reconstruction; all fresh source I/O
                    # runs afterwards, before the immutable terminal checks.
                    self._semantic_source_window = None
                binding, closure = _original_group_method(
                    self, "_source_projection_pair", record.declaration_record, record.observation,
                )
                if type(binding) is not CodeSelectedPackageSourceBinding:
                    raise SourceObservationUnavailable("selected_source_binding_changed")
                binding_digest = binding.binding_digest.value
                if (binding_digest != record.digest.value
                    or binding.expectation != record.expectation):
                    raise SourceObservationUnavailable("selected_source_binding_changed")
                if terminal:
                    self._call("revalidate_selected_package", record.observation)
                self._check_origin()
                if (self._selected_record(handle) is not record
                    or self._checked_declaration_origin(record.declaration_record) is not origin
                    or binding.expectation.closure_digest.value != origin.projection_digest):
                    raise SourceObservationUnavailable("declaration_projection_changed")
                _original_group_method(self, "_check_declaration_projection_result", origin, closure)
                if (type(binding) is not CodeSelectedPackageSourceBinding
                    or binding.binding_digest.value != binding_digest
                    or record.digest.value != binding_digest
                    or binding.expectation != record.expectation):
                    raise SourceObservationUnavailable("selected_source_binding_changed")
                return binding, closure

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
            if self._checked_declaration_origin(record.declaration_record).handle is not record.declaration:
                raise SourceObservationUnavailable("declaration_projection_changed")
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
                declaration_origin = self._checked_declaration_origin(record.declaration_record)
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
                if (
                    self._selected_record(handle) is not record
                    or self._checked_declaration_origin(record.declaration_record) is not declaration_origin
                    or binding.expectation.closure_digest.value != declaration_origin.projection_digest
                ):
                    raise SourceObservationUnavailable("declaration_projection_changed")
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
                with _original_group_method(
                    self, "_original_participant_source_window", declaration, selected,
                ):
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
                with _original_group_method(
                    self, "_original_participant_source_window", declaration, selected,
                ):
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

        def _read_product_projection_inputs(
            self, declaration: WorkspaceDeclarationScope, selected: WorkspaceSelectedPackageSource,
        ):
            """Read original metadata under one synchronous source bracket.

            Product interpretation/execution stays outside this window. Every
            original reader still runs; the window performs terminal source and
            independent immutable-coordinate checks before returning any tuple.
            """
            binding = closure = view = inputs = origin = None
            try:
                origin = self._checked_declaration_origin(self._declaration_record(declaration))
                with _original_group_method(
                    self, "_original_participant_source_window", declaration, selected,
                ):
                    binding = _original_group_method(self, "read_selected_package_source", selected)
                    closure = _original_group_method(self, "read_declaration_scope", declaration)
                    view = _original_group_method(self, "read_selected_participant_view", declaration, selected)
                    inputs = _original_group_method(self, "inspect_inputs", selected)
                _original_group_method(self, "_check_declaration_projection_result", origin, closure)
                return binding, closure, view, inputs
            finally:
                del self, declaration, selected, binding, closure, view, inputs, origin

        def selected_source_validation_scope(
            self, declaration: WorkspaceDeclarationScope, selected: WorkspaceSelectedPackageSource,
        ) -> Iterator[None]:
            """Lend the original window to synchronous Code policy checks only."""
            try:
                with scope_dispatch(
                    self, "_original_participant_source_window", declaration, selected,
                ):
                    yield
            except BaseException as error:
                _clear_group_failure_frames(error)
                raise
            finally:
                del self, declaration, selected

        @contextmanager
        def _original_participant_source_window(
            self, declaration: WorkspaceDeclarationScope, selected: WorkspaceSelectedPackageSource,
        ) -> Iterator[None]:
            """Share projections only within one synchronous participant calculation.

        This is not an admission. Original methods still validate every input;
        full source checks bracket the calculation before any result can return.
        Existing semantic/dependency windows keep their original ownership.
        """
            record = source = origin = binding = closure = coordinate = fresh = current = None
            owns_window = False
            try:
                with self._lock:
                    record = _original_group_method(self, "_declaration_record", declaration)
                    source = _original_group_method(self, "_selected_record", selected)
                    if source.declaration is not declaration or source.declaration_record is not record:
                        raise SourceObservationUnavailable("selected_participant_origin_differs")
                    current = self._semantic_source_window
                    if current is not None:
                        if current.thread_id != threading.get_ident():
                            raise SourceObservationUnavailable("semantic_source_window_origin_changed")
                        if current.selected is selected:
                            if current.record is not source:
                                raise SourceObservationUnavailable("semantic_source_window_origin_changed")
                        else:
                            # A dependency supplier may be checked within a
                            # consumer's metadata window. Do not borrow that
                            # window: original foreign-source readers perform
                            # their full checks and leave its custody intact.
                            current = None
                    elif self._dependency_source_window is None:
                        origin = self._checked_declaration_origin(record)
                        binding, closure = _original_group_method(
                            self, "_read_source_projection_pair", selected, terminal=False,
                        )
                        coordinate = _original_group_method(
                            self, "_capture_original_binding_coordinate", binding,
                        )
                        current = _SemanticSourceValidationWindow(
                            threading.get_ident(), selected, source, closure, binding,
                        )
                        owns_window = True
                        self._semantic_source_window = current
                try:
                    yield
                finally:
                    if owns_window:
                        with self._lock:
                            if self._dependency_source_window is not None:
                                raise SourceObservationUnavailable("participant_source_window_changed")
                            fresh = _original_group_method(
                                self, "_read_source_projection_pair", selected,
                                terminal=True, closing=current,
                            )[0]
                            _original_group_method(
                                self, "_check_original_binding_coordinate", coordinate,
                                binding, detached=fresh,
                            )
                            _original_group_method(
                                self, "_check_declaration_projection_result", origin, closure,
                            )
                            if (_original_group_method(self, "_selected_record", selected) is not source
                                or _original_group_method(self, "_declaration_record", declaration) is not record):
                                raise SourceObservationUnavailable("selected_participant_origin_differs")
            except BaseException as error:
                _clear_group_failure_frames(error)
                raise
            finally:
                if owns_window and self._semantic_source_window is current:
                    self._semantic_source_window = None
                del self, declaration, selected, record, source, origin
                del binding, closure, coordinate, fresh, current

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
            origin = self._checked_declaration_origin(record.declaration_record)
            try:
                binding = self.read_selected_package_source(selected)
                closure = self.read_declaration_scope(record.declaration)
                # Match the independently retained original commitment instead
                # of serializing this complete declaration closure again.
                _original_group_method(self, "_check_declaration_projection_result", origin, closure)
                if self._checked_declaration_origin(record.declaration_record) is not origin:
                    raise SourceObservationUnavailable("declaration_projection_changed")
            finally:
                del origin
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
            grouped_body: SemanticBody | None = None,
            declaration_body: SemanticBody | None = None,
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
            if grouped_body is not None and contract == grouped_body.coordinate.contract:
                return grouped_body.canonical_body
            if declaration_body is not None and contract == declaration_body.coordinate.contract:
                return declaration_body.canonical_body
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
            grouped_origin: _GroupedInputOrigin | None = None,
        ) -> Iterator[SemanticInputProductionExpectation]:
            grouped_body = declaration_body = None
            if grouped_origin is None:
                selection, source_origin = self._selection_context_values(
                    selected, selection_origin, context_contracts,
                )
            else:
                grouped_body, selection, source_origin, source_coordinates, declaration_body = (
                    _original_group_projection(self, grouped_origin)
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
                    if grouped_body is not None and item.contract == grouped_body.coordinate.contract:
                        if item.role != grouped_body.coordinate.role:
                            raise SourceObservationUnavailable("grouped_context_role_differs")
                        bodies.append(copy.deepcopy(grouped_body))
                        continue
                    if declaration_body is not None and item.contract == declaration_body.coordinate.contract:
                        if item.role != declaration_body.coordinate.role:
                            raise SourceObservationUnavailable("declaration_context_role_differs")
                        bodies.append(copy.deepcopy(declaration_body))
                        continue
                    body = self._pre_request_context_bytes(
                        context=values[0], inventory=values[1], binding=values[3],
                        contract=item.contract,
                        selection=selection, source_origin=source_origin,
                        grouped_body=grouped_body, declaration_body=declaration_body,
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
                    grouped_origin=grouped_origin,
                )
            with self._exclusion.mutation(), self._lock:
                if key in self._pre_request_inputs or key in self._retired_pre_request_inputs:
                    raise SourceObservationUnavailable("pre_request_input_replayed")
                if self._selected_record(selected) is not record:
                    raise SourceObservationUnavailable("pre_request_source_changed")
                self._pre_request_inputs[key] = retained
                self._retired_pre_request_inputs.add(key)
            try:
                _original_group_method(self, "validate_semantic_input_source", selected, expected=expected)
                yield expected
                _original_group_method(self, "validate_semantic_input_source", selected, expected=expected)
            finally:
                retained.live = False
                retained.selection_origin = None
                retained.grouped_origin = None
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

        def _grouped_declaration_body(
            self,
            family: _GroupedInputOrigin,
            records: tuple[_SelectedRecord, ...],
        ) -> SemanticBody:
            """Read the original complete declaration; never accept a caller scope."""
            _check_group_methods(self)
            _check_declaration_codec()
            _GROUP_ORIGINAL_ORIGIN(self)
            if not records or any(type(item) is not _SelectedRecord for item in records):
                raise SourceObservationUnavailable("grouped_declaration_members_required")
            with self._lock:
                root = records[0]
                handle = root.declaration
                original = _original_group_method(self, "_declaration_record", handle)
                if any(
                    item.declaration is not handle or item.declaration_record is not original
                    for item in records
                ):
                    raise SourceObservationUnavailable("grouped_declaration_member_differs")
                if family.declaration_handle is None:
                    family.declaration_handle = handle
                    family.declaration_record = original
                if (
                    family.declaration_handle is not handle
                    or family.declaration_record is not original
                ):
                    raise SourceObservationUnavailable("grouped_declaration_origin_changed")
            # Full declaration/source work stays outside parent publication exclusion.
            # The existing reader authenticates its own original expectation/digest.
            closure = _original_group_method(self, "read_declaration_scope", handle)
            _check_declaration_codec()
            raw = _DECLARATION_ENCODER(closure)
            _check_declaration_codec()
            with self._lock:
                if (
                    _original_group_method(self, "_declaration_record", handle) is not original
                    or closure.closure_digest != original.digest
                    or any(
                        item.declaration is not handle
                        or item.declaration_record is not original
                        for item in records
                    )
                ):
                    raise SourceObservationUnavailable("grouped_declaration_origin_changed")
            digest = ContentDigest.of_bytes(raw)
            return SemanticBody(
                SemanticValueCoordinate(
                    "declaration_scope",
                    cast(SemanticContractRef, _DECLARATION_CONTEXT_REF),
                    f"workspace-context:{digest.value}",
                    digest,
                    len(raw),
                ),
                raw,
            )

        def _grouped_selected_values(self, family: _GroupedInputOrigin):
            """Project original member results and edges outside parent exclusion."""
            # The Code owner supplies the only portable group codec. Existing
            # single-package callers do not need to import this additive surface.
            from aware_code_semantic_contract_runtime.grammar_source_group import (
                CodeGrammarSourceBodyV1,
                CodeGrammarSourceEdgeV1,
                CodeGrammarSourceGroupV1,
                CodeGrammarSourceMemberV1,
                grammar_source_group_body,
            )

            _check_group_methods(self)
            _GROUP_ORIGINAL_ORIGIN(self)  # Reject inherited process state before any lock.
            members = []
            selected_records = []
            handles = []
            refs = []
            root_values = None
            for carrier, retained_fields in family.members:
                current = _group_fields(
                    carrier,
                    WorkspaceSelectedSourceInputV1,
                    _GROUP_MEMBER_FIELDS,
                    _GROUP_MEMBER_SLOTS,
                )
                if any(a is not b for a, b in zip(current, retained_fields, strict=True)):
                    raise SourceObservationUnavailable("grouped_member_binding_changed")
                selected, host, registration, expected, result, contracts = current
                if (
                    type(selected) is not WorkspaceSelectedPackageSource
                    or type(host) is not SemanticInputProducerHost
                    or type(registration) is not AdmittedSemanticInputProducerRegistration
                    or type(expected) is not SemanticInputProductionExpectation
                    or type(result) is not SemanticBody
                ):
                    raise SourceObservationUnavailable("grouped_member_origin_required")
                _original_group_contracts(self, contracts)
                origin = _SelectedInputOrigin(host, registration, expected, result, contracts)
                selection, coordinates = _original_group_method(
                    self, "_selected_input_values", selected, origin
                )
                selection, occurrence = _original_group_method(
                    self,
                    "_selection_context_values",
                    selected,
                    origin,
                    (SemanticInputContextContract("source_origin", SOURCE_ORIGIN_REF),),
                    selected_values=(selection, coordinates),
                )
                if selection is None or occurrence is None:
                    raise SourceObservationUnavailable("grouped_member_origin_unavailable")
                occurrence_body = encode_source_origin(occurrence)
                digest = ContentDigest.of_bytes(occurrence_body)
                occurrence_coordinate = SemanticValueCoordinate(
                    "source_origin",
                    SOURCE_ORIGIN_REF,
                    f"workspace-context:{digest.value}",
                    digest,
                    len(occurrence_body),
                )
                with self._lock:
                    record = _original_group_method(
                        self, "_pre_request_record", selected, expected
                    )
                    selected_records.append(record.selected_record)
                    sources = tuple(
                        CodeGrammarSourceBodyV1(
                            item.relative_path,
                            copy.deepcopy(item.coordinate),
                            cast(
                                bytes,
                                _original_group_method(
                                    self,
                                    "_call",
                                    "read_selected_package",
                                    record.selected_record.observation,
                                    relative_path=item.relative_path,
                                ),
                            ).hex(),
                        )
                        for item in coordinates
                    )
                members.append(
                    CodeGrammarSourceMemberV1(
                        occurrence.occurrence.occurrence_ref,
                        copy.deepcopy(result.coordinate),
                        result.canonical_body.hex(),
                        occurrence_coordinate,
                        occurrence_body.hex(),
                        sources,
                    )
                )
                # Every member keeps the original predecessor result, not a portable
                # body supplied by a caller. Check again after retained source reads.
                _original_group_method(self, "_selected_input_values", selected, origin)
                handles.append(selected)
                refs.append(occurrence.occurrence.occurrence_ref)
                if root_values is None:
                    root_values = selection, occurrence, coordinates
            if root_values is None or len(set(refs)) != len(refs):
                raise SourceObservationUnavailable("grouped_members_not_unique")
            edges = []
            for carrier, retained_fields in family.edges:
                current = _group_fields(
                    carrier,
                    WorkspaceSelectedDependencyInputV1,
                    _GROUP_EDGE_FIELDS,
                    _GROUP_EDGE_SLOTS,
                )
                if any(a is not b for a, b in zip(current, retained_fields, strict=True)):
                    raise SourceObservationUnavailable("grouped_edge_binding_changed")
                owner, target, inventory, expected, kind, ref = current
                if (
                    type(owner) is not WorkspaceSelectedPackageSource
                    or type(target) is not WorkspaceSelectedPackageSource
                    or type(inventory) is not WorkspaceDeclarationInventoryAdmission
                    or type(expected) is not RetainedTargetExpectation
                    or type(kind) is not str
                    or type(ref) is not str
                ):
                    raise SourceObservationUnavailable("grouped_edge_origin_required")
                owner_indices = [i for i, handle in enumerate(handles) if handle is owner]
                target_indices = [i for i, handle in enumerate(handles) if handle is target]
                if len(owner_indices) != 1 or len(target_indices) != 1:
                    raise SourceObservationUnavailable("grouped_edge_endpoint_unavailable")
                _original_group_method(
                    self,
                    "validate_dependency_target_admission",
                    target,
                    inventory_admission=inventory,
                    expected=expected,
                )
                with self._lock:
                    original = _original_group_method(
                        self,
                        "_validate_semantic_admission",
                        inventory,
                        expected=expected.source_planning,
                        kind=WorkspaceDeclarationInventoryAdmission,
                    )
                    if original.selected is not owner:
                        raise SourceObservationUnavailable("grouped_edge_owner_differs")
                    declared = tuple(
                        item
                        for item in original.inventory.entries
                        if (item.dependency_kind, item.dependency_ref) == (kind, ref)
                    )
                    target_record = _original_group_method(
                        self, "_target_record", inventory, expected
                    )
                    target_roots = _original_group_method(
                        self, "_semantic_values", target_record.membership
                    )[3]
                    if len(declared) != 1 or not any(
                        item.package == target_record.context.package
                        and item.semantic_root_refs == target_roots
                        for item in declared[0].targets
                    ):
                        raise SourceObservationUnavailable("grouped_edge_declaration_differs")
                edges.append(
                    CodeGrammarSourceEdgeV1(
                        refs[owner_indices[0]],
                        refs[target_indices[0]],
                        kind,
                        ref,
                    )
                )
            members.sort(key=lambda item: item.occurrence_ref.encode("utf-8"))
            edges.sort(
                key=lambda item: tuple(
                    text.encode("utf-8")
                    for text in (
                        item.owner_occurrence_ref,
                        item.target_occurrence_ref,
                        item.dependency_kind,
                        item.dependency_ref,
                    )
                )
            )
            group = CodeGrammarSourceGroupV1(refs[0], tuple(members), tuple(edges))
            body = grammar_source_group_body(group)
            declaration_body = None
            if family.declaration_requested:
                declaration_body = _original_group_method(
                    self, "_grouped_declaration_body", family, tuple(selected_records),
                )
            return body, *root_values, declaration_body


        @staticmethod
        def _check_group_source_contracts(
            contracts,
            kind: type[
                SemanticInputSourceContract | SemanticInputContextContract
            ] = SemanticInputSourceContract,
        ):
            if type(contracts) is not tuple or not contracts:
                raise SourceObservationUnavailable("grouped_source_contracts_invalid")
            roles = []
            for item in contracts:
                if type(item) is not kind or type(item.role) is not str:
                    raise SourceObservationUnavailable("grouped_source_contracts_invalid")
                if type(item.contract) is not SemanticContractRef:
                    raise SourceObservationUnavailable("grouped_source_contracts_invalid")
                # Revalidate the exact neutral contract before hashing/comparison.
                if (
                    type(item.contract.key) is not str
                    or type(item.contract.version) is not str
                    or type(item.contract.schema_digest) is not ContentDigest
                    or type(item.contract.schema_digest.value) is not str
                ):
                    raise SourceObservationUnavailable("grouped_source_contracts_invalid")
                SemanticContractRef.__post_init__(item.contract)
                roles.append(item.role)
            if len(set(roles)) != len(roles):
                raise SourceObservationUnavailable("grouped_source_contracts_invalid")


        @contextmanager
        def original_grouped_selected_source_input(
            self,
            *,
            root: WorkspaceSelectedSourceInputV1,
            participants: tuple[WorkspaceSelectedSourceInputV1, ...],
            dependency_edges: tuple[WorkspaceSelectedDependencyInputV1, ...],
            use_ref: str,
            stage: str,
            source_contracts: tuple[SemanticInputSourceContract, ...],
            context_contracts: tuple[SemanticInputContextContract, ...],
        ) -> Iterator[SemanticInputProductionExpectation]:
            """Borrow original selections and edges for one neutral grouped use."""
            family = None
            root_fields = origin = expected = None
            try:
                from aware_code_semantic_contract_runtime.grammar_source_group import (
                    GRAMMAR_SOURCE_GROUP_REF,
                )

                _check_group_methods(self)
                _GROUP_ORIGINAL_ORIGIN(self)
                if (
                    type(participants) is not tuple
                    or len(participants) >= 128
                    or type(dependency_edges) is not tuple
                    or len(dependency_edges) > 256
                ):
                    raise SourceObservationUnavailable("grouped_input_bounds_invalid")
                _original_group_contracts(self, source_contracts)
                if type(context_contracts) is not tuple or any(
                    type(item) is not SemanticInputContextContract for item in context_contracts
                ):
                    raise SourceObservationUnavailable("grouped_context_contracts_invalid")
                _original_group_contracts(self, context_contracts, SemanticInputContextContract)
                if (
                    sum(
                        item.role == "grammar_source_group"
                        and item.contract == GRAMMAR_SOURCE_GROUP_REF
                        for item in context_contracts
                    )
                    != 1
                ):
                    raise SourceObservationUnavailable("original_grouped_context_required")
                declaration_requested = any(
                    item.role == "declaration_scope"
                    or item.contract.key == "aware.code.retained-dependency-scope-closure.v3"
                    for item in context_contracts
                )
                if declaration_requested:
                    _check_declaration_codec()
                    matches = tuple(
                        item
                        for item in context_contracts
                        if (
                            item.role == "declaration_scope"
                            or item.contract.key
                            == "aware.code.retained-dependency-scope-closure.v3"
                        )
                    )
                    if (
                        len(matches) != 1
                        or matches[0].role != "declaration_scope"
                        or matches[0].contract != _DECLARATION_CONTEXT_REF
                    ):
                        raise SourceObservationUnavailable(
                            "original_declaration_context_required"
                        )
                family = _GroupedInputOrigin(
                    tuple(
                        (
                            item,
                            _group_fields(
                                item,
                                WorkspaceSelectedSourceInputV1,
                                _GROUP_MEMBER_FIELDS,
                                _GROUP_MEMBER_SLOTS,
                            ),
                        )
                        for item in (root, *participants)
                    ),
                    tuple(
                        (
                            item,
                            _group_fields(
                                item,
                                WorkspaceSelectedDependencyInputV1,
                                _GROUP_EDGE_FIELDS,
                                _GROUP_EDGE_SLOTS,
                            ),
                        )
                        for item in dependency_edges
                    ),
                    declaration_requested=declaration_requested,
                )
                root_fields = family.members[0][1]
                _original_group_contracts(self, root_fields[5])
                if root_fields[5] != source_contracts:
                    raise SourceObservationUnavailable("grouped_root_contracts_differ")
                origin = _SelectedInputOrigin(*root_fields[1:])
                with _original_group_method(
                    self,
                    "_original_pre_request_input",
                    root_fields[0],
                    use_ref=use_ref,
                    stage=stage,
                    source_coordinates=(),
                    context_contracts=context_contracts,
                    selection_origin=origin,
                    grouped_origin=family,
                ) as expected:
                    yield expected
            except BaseException as error:
                _clear_group_failure_frames(error)
                raise
            finally:
                if family is not None:
                    family.members = ()
                    family.edges = ()
                    family.declaration_handle = None
                    family.declaration_record = None
                del (
                    self,
                    root,
                    participants,
                    dependency_edges,
                    source_contracts,
                    context_contracts,
                )
                del family, root_fields, origin, expected

        def semantic_input_validation_scope(
            self, source_admission: object, *, expected: SemanticInputProductionExpectation,
        ) -> Iterator[None]:
            """Bracket synchronous Code retained-result checks, never execution.

        Grouped inputs keep their original distinct-member scopes. This port
        lends no authority: every original source/context callback still runs.
        """
            retained = None
            try:
                scope_dispatch(self, "_check_origin")
                with self._lock:
                    retained = scope_dispatch(
                        self, "_pre_request_record", source_admission, expected,
                    )
                if retained.grouped_origin is not None:
                    yield
                else:
                    with scope_dispatch(
                        self, "_original_semantic_source_window", source_admission, expected,
                    ):
                        yield
                if scope_dispatch(
                    self, "_pre_request_record", source_admission, expected,
                ) is not retained:
                    raise SourceObservationUnavailable("pre_request_source_changed")
            except BaseException as error:
                if retained is not None:
                    retained.live = False
                    retained.selection_origin = None
                    retained.grouped_origin = None
                _clear_group_failure_frames(error)
                raise
            finally:
                del self, source_admission, expected, retained

        def validate_semantic_input_source(
            self, source_admission: object, *, expected: SemanticInputProductionExpectation,
        ) -> None:
            """Revalidate the original pre-request source, context and parent."""
            if os.getpid() != self._pid:
                raise SourceObservationUnavailable("declaration_process_changed")
            with self._lock:
                original = next((item for item in self._pre_request_inputs.values()
                                 if item.expected is expected), None)
            grouped_values = None
            try:
                # Borrowing an expectation does not admit a foreign source handle.
                if (original is not None and original.grouped_origin is not None
                    and source_admission is not original.selected):
                    original = None
                    raise SourceObservationUnavailable("original_pre_request_input_required")
                if original is not None and original.grouped_origin is not None:
                    if original.thread_id != threading.get_ident():
                        raise SourceObservationUnavailable("original_pre_request_input_required")
                    # Each original member's Code validation can reenter this issuer.
                    # Do not carry the root's synchronous window into another member.
                    grouped_values = _original_group_projection(self, original.grouped_origin)
                # Only synchronous original-result validation runs inside this
                # window. It never encloses producer execution, await or yield to
                # a semantic owner. Recursive callbacks still check every original
                # input/result; detached source projections are reused locally.
                window = (
                    self._original_semantic_source_window(source_admission, expected)
                    if grouped_values is None else _original_group_method(
                        self, "_original_semantic_source_window", source_admission, expected,
                    )
                )
                with window:
                    if grouped_values is None:
                        self._validate_semantic_input_source(source_admission, expected=expected)
                    else:
                        _original_group_method(
                            self, "_validate_semantic_input_source", source_admission,
                            expected=expected, grouped_values=grouped_values,
                        )
            except BaseException as error:
                if original is not None:
                    original.live = False
                    original.selection_origin = None
                    original.grouped_origin = None
                _clear_group_failure_frames(error)
                del self, source_admission, expected, original, grouped_values
                raise

        def _validate_retained_semantic_inputs(
            self, selected: object, *, expectations: tuple, results: tuple,
        ) -> None:
            """Verify one node's retained inputs synchronously, never execute an owner.

        Each original validator still runs. Only complete source rereads share
        the existing local window; its final checks precede this method's return.
        Grouped inputs keep separate windows for their distinct source owners.
        """
            retained = ()
            item = expected = host = registration = result = None
            try:
                _check_group_methods(self)
                if type(expectations) is not tuple or type(results) is not tuple:
                    raise SourceObservationUnavailable("original_pre_request_input_required")
                with self._lock:
                    retained = tuple(
                        _original_group_method(self, "_pre_request_record", selected, value)
                        for value in expectations
                    )
                grouped = any(item.grouped_origin is not None for item in retained)
                # No window crosses producer execution, await, or a different member.
                with ExitStack() as stack:
                    if expectations and not grouped:
                        stack.enter_context(_original_group_method(
                            self, "_original_semantic_source_window", selected, expectations[0],
                        ))
                    for expected in expectations:
                        _original_group_method(
                            self, "validate_semantic_input_source", selected, expected=expected,
                        )
                    for host, registration, expected, result in results:
                        if not any(expected is value for value in expectations):
                            raise SourceObservationUnavailable("original_pre_request_input_required")
                        _original_group_method(
                            self, "_call_original_code_result_validator", host, registration,
                            source_admission=selected,
                            expected=expected, result=result,
                        )
                        _check_group_methods(self)
                    for item in retained:
                        if _original_group_method(
                            self, "_pre_request_record", selected, item.expected,
                        ) is not item:
                            raise SourceObservationUnavailable("pre_request_source_changed")
                _check_group_methods(self)
            except BaseException as error:
                for item in retained:
                    item.live = False
                    item.selection_origin = None
                    item.grouped_origin = None
                _clear_group_failure_frames(error)
                raise
            finally:
                del self, selected, expectations, results, retained, item
                del expected, host, registration, result

        @contextmanager
        def _original_semantic_source_window(
            self, selected: object, expected: SemanticInputProductionExpectation,
        ) -> Iterator[None]:
            retained = current = binding = closure = None
            source_record = declaration_origin = binding_coordinate = fresh_binding = None
            owns_window = False
            try:
                with self._lock:
                    retained = _original_group_method(self, "_pre_request_record", selected, expected)
                    current = self._semantic_source_window
                    if current is not None:
                        if (current.thread_id != threading.get_ident()
                            or current.selected is not selected
                            or current.record is not retained.selected_record):
                            raise SourceObservationUnavailable("semantic_source_window_origin_changed")
                    else:
                        # Only this synchronous window may defer the pair's
                        # closing source check. The full closing read below is
                        # mandatory before any validation result can escape.
                        source_record = retained.selected_record
                        declaration_origin = self._checked_declaration_origin(
                            source_record.declaration_record,
                        )
                        binding, closure = _original_group_method(
                            self, "_read_source_projection_pair", retained.selected,
                            terminal=False,
                        )
                        binding_coordinate = _original_group_method(
                            self, "_capture_original_binding_coordinate", binding,
                        )
                        current = _SemanticSourceValidationWindow(
                            threading.get_ident(), retained.selected, retained.selected_record,
                            closure, binding,
                        )
                        owns_window = True
                        self._semantic_source_window = current
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
                        fresh_binding = _original_group_method(
                            self, "_read_source_projection_pair", retained.selected,
                            terminal=True, closing=current,
                        )[0]
                        _original_group_method(
                            self, "_check_original_binding_coordinate", binding_coordinate,
                            binding, detached=fresh_binding,
                        )
                        _original_group_method(
                            self, "_check_declaration_projection_result", declaration_origin, closure,
                        )
                        if completed:
                            _original_group_method(self, "_pre_request_record", selected, expected)
            except BaseException as error:
                _clear_group_failure_frames(error)
                raise
            finally:
                if owns_window and self._semantic_source_window is current:
                    self._semantic_source_window = None
                del self, selected, expected, retained, current, binding, closure
                del source_record, declaration_origin, binding_coordinate, fresh_binding

        def _validate_semantic_input_source(
            self, source_admission: object, *, expected: SemanticInputProductionExpectation,
            grouped_values=None,
        ) -> None:
            with self._lock:
                original = next((item for item in self._pre_request_inputs.values()
                                 if item.expected is expected), None)
            try:
                selection = None
                source_origin = None
                grouped_body = declaration_body = None
                if grouped_values is not None:
                    grouped_body, selection, source_origin, coordinates, declaration_body = grouped_values
                    if coordinates != expected.source_coordinates:
                        raise SourceObservationUnavailable("grouped_root_coordinates_changed")
                elif original is not None and original.selection_origin is not None:
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
                    original.grouped_origin = None
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
                            grouped_body=grouped_body, declaration_body=declaration_body,
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
                        retained.grouped_origin = None
                    raise

        def validate_semantic_input_context(
            self, source_admission: object, *, expected: SemanticInputProductionExpectation,
        ) -> None:
            try:
                self.validate_semantic_input_source(source_admission, expected=expected)
            except BaseException as error:
                _clear_group_failure_frames(error)
                del self, source_admission, expected
                raise

        def read_semantic_input_sources(
            self, source_admission: object, *, expected: SemanticInputProductionExpectation,
        ) -> tuple[SemanticInputSourceBody, ...]:
            self.validate_semantic_input_source(source_admission, expected=expected)
            with self._lock:
                retained = self._pre_request_record(source_admission, expected)
                try:
                    bodies = tuple(SemanticInputSourceBody(
                        copy.deepcopy(source), cast(bytes,
                            self._call("read_selected_package", retained.selected_record.observation,
                                       relative_path=source.relative_path)
                            if retained.grouped_origin is None else _original_group_method(
                                self, "_call", "read_selected_package", retained.selected_record.observation,
                                relative_path=source.relative_path,
                            )
                        ),
                    ) for source in expected.source_coordinates)
                except BaseException:
                    retained.live = False
                    retained.selection_origin = None
                    retained.grouped_origin = None
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
            if type(record.expectation) is RetainedProductPlanningExpectation:
                return self._validate_product_dependency_inventory(
                    admission, expected=expected,
                )
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

        def _bind_original_dependency_validator(self, validator, *, product_source=False) -> None:
            """Retain Code's original demand validator, never a caller callback."""
            with self._lock:
                self._check_origin()
                if (type(product_source) is not bool
                    or (not product_source and self._planning_validator is None)
                    or self._dependency_validator is not None):
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

        def issue_product_dependency_inventory(self, operation, *, expected):
            """Bind the actual returned Code product demand to this issuer's source.

            The freely constructible expectation is verified by the original
            Code validator before source identity is inspected. No stage,
            context or registry admission is reconstructed.
            """
            from .dependency_resolution import _freeze

            with self._lock:
                self._check_origin()
                if (
                    type(expected) is not RetainedDependencyResolutionExpectation
                    or type(expected.source_planning) is not RetainedProductPlanningExpectation
                    or expected.demand_operation_identity is not operation
                    or self._dependency_validator is None
                ):
                    raise SourceObservationUnavailable("original_product_demand_required")
                validator, descriptor, method = self._dependency_validator
                if inspect.getattr_static(validator, "validate_retained_dependency_operation") is not descriptor:
                    raise SourceObservationUnavailable("dependency_validator_substituted")
                if method(operation, expected=expected) is not None:
                    raise SourceObservationUnavailable("dependency_validator_result_invalid")
                if inspect.getattr_static(validator, "validate_retained_dependency_operation") is not descriptor:
                    raise SourceObservationUnavailable("dependency_validator_substituted")
                retained = _freeze(expected)
                source_planning = retained.source_planning
                if type(source_planning) is not RetainedProductPlanningExpectation:
                    raise SourceObservationUnavailable("original_product_source_required")
                selected = source_planning.source_input.source_identity
                if type(selected) is not WorkspaceSelectedPackageSource:
                    raise SourceObservationUnavailable("original_product_selected_source_required")
                if any(
                    self._semantic_contexts.get(handle) is operation
                    for handle in self._semantic
                ) or len(self._semantic) >= 128:
                    raise SourceObservationUnavailable("product_inventory_replay_or_capacity")
                original_input = self._original_product_dependency_source_input(source_planning)
                self.validate_semantic_input_source(selected, expected=original_input)
                values = self._semantic_values(selected)
                if (values[0].package != source_planning.package
                    or values[0].source_identity_digest != source_planning.source_identity_digest):
                    raise SourceObservationUnavailable("product_inventory_source_differs")
                targets = self._retain_targets(selected, values[6])
                record = _SemanticRecord(
                    selected, source_planning, values[0], values[1],
                    values[2], values[3], self._selected_record(selected).declaration_record.digest,
                    targets, retained,
                )
                inventory = object.__new__(WorkspaceDeclarationInventoryAdmission)
                self._semantic[inventory] = record
                self._semantic_contexts[inventory] = operation
                try:
                    self._validate_dependency_inventory(operation, inventory, expected=expected)
                except BaseException:
                    self._semantic.pop(inventory, None)
                    self._semantic_contexts.pop(inventory, None)
                    raise
                return inventory

        def _original_product_dependency_source_input(self, source):
            """Find this issuer's original input; the Code snapshot is comparison only."""
            if type(source) is not RetainedProductPlanningExpectation:
                raise SourceObservationUnavailable("original_product_source_required")
            selected, comparison = source.source_input.source_identity, source.source_input
            matches = tuple(
                item.expected for item in self._pre_request_inputs.values()
                if item.live and item.selected is selected
                and item.expected.use_ref == comparison.use_ref
                and item.expected.input_digest == comparison.input_digest
            )
            if len(matches) != 1:
                raise SourceObservationUnavailable("original_product_input_unavailable")
            original, = matches
            self._pre_request_record(selected, original)
            return original

        def _validate_product_dependency_inventory(self, admission, *, expected):
            record = self._semantic.get(admission)
            if (
                type(record) is not _SemanticRecord
                or type(expected) is not RetainedProductPlanningExpectation
                or type(record.product_dependency) is not RetainedDependencyResolutionExpectation
                or record.product_dependency.source_planning is not record.expectation
                or self._dependency_validator is None
            ):
                raise SourceObservationUnavailable("original_product_inventory_required")
            operation = self._semantic_contexts.get(admission)
            if operation is not record.product_dependency.demand_operation_identity:
                raise SourceObservationUnavailable("product_inventory_operation_differs")
            validator, descriptor, method = self._dependency_validator
            comparison = replace(record.product_dependency, source_planning=expected)
            for check in (record.product_dependency, comparison):
                if inspect.getattr_static(validator, "validate_retained_dependency_operation") is not descriptor:
                    raise SourceObservationUnavailable("dependency_validator_substituted")
                if method(operation, expected=check) is not None:
                    raise SourceObservationUnavailable("dependency_validator_result_invalid")
                if inspect.getattr_static(validator, "validate_retained_dependency_operation") is not descriptor:
                    raise SourceObservationUnavailable("dependency_validator_substituted")
            if expected.source_input.source_identity is not record.selected:
                raise SourceObservationUnavailable("product_inventory_selected_source_differs")
            original_input = self._original_product_dependency_source_input(expected)
            self.validate_semantic_input_source(record.selected, expected=original_input)
            values = self._semantic_values(record.selected)
            if (
                values[:4] != (record.context, record.inventory, record.namespace, record.owned_roots)
                or values[0].package != expected.package
                or values[0].source_identity_digest != expected.source_identity_digest
                or self._selected_record(record.selected).declaration_record.digest != record.closure_digest
                or tuple((item.address, item.context.package.package_ref) for item in record.targets) != values[6]
            ):
                raise SourceObservationUnavailable("product_inventory_source_changed")
            for target in record.targets:
                self._target_source(target.membership)
            if method(operation, expected=comparison) is not None:
                raise SourceObservationUnavailable("dependency_validator_result_invalid")
            if inspect.getattr_static(validator, "validate_retained_dependency_operation") is not descriptor:
                raise SourceObservationUnavailable("dependency_validator_substituted")
            self._check_origin()
            if self._semantic.get(admission) is not record or self._semantic_contexts.get(admission) is not operation:
                raise SourceObservationUnavailable("product_inventory_retired")
            return record

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
            from .dependency_fulfillment import (
                _WorkspaceEmptyDependencyFulfillmentRuntime,
            )
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

        def _bind_original_dependency_product_publisher(self, publisher, *, source_correspondences=()):
            """Retain borrowed HEAD/body readers on the original command issuer."""
            with self._lock:
                self._check_origin()
                if self._dependency_fulfillment is None:
                    raise SourceObservationUnavailable("dependency_fulfillment_unavailable")
                self._dependency_fulfillment.bind_publisher(publisher, source_correspondences=source_correspondences)

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
                            retained.grouped_origin = None

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
                    self._declaration_origins[:] = [
                        origin for origin in self._declaration_origins
                        if origin.handle is not handle
                    ]
                    self._retired_declaration_records[:] = [
                        record for record in self._retired_declaration_records
                        if any(item.record is record for item in self._declaration_origins)
                    ]

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
                        record.grouped_origin = None
                    self._pre_request_inputs.clear()
                    self._retired_pre_request_inputs.clear()
                    self._semantic.clear()
                    self._semantic_contexts.clear()
                    self._issued_semantic.clear()
                    self._declarations.clear()
                    self._declaration_origins.clear()
                    self._retired_declaration_records.clear()
                    self._closed = True


    _GROUP_METHOD_DESCRIPTORS = tuple(
        (name, inspect.getattr_static(WorkspaceDeclarationScopeRuntime, name))
        for name in (
            "_check_origin",
            "_grouped_selected_values",
            "_check_group_source_contracts",
            "_selected_input_values",
            "_selection_context_values",
            "_pre_request_record",
            "_call",
            "validate_dependency_target_admission",
            "_validate_semantic_admission",
            "_target_record",
            "_semantic_values",
            "_original_pre_request_input",
            "_validate_semantic_input_source",
            "validate_semantic_input_source",
            "semantic_input_validation_scope",
            "_validate_retained_semantic_inputs",
            "_call_original_code_result_validator",
            "_original_semantic_source_window",
            "_original_participant_source_window",
            "selected_source_validation_scope",
            "_pre_request_context_bytes",
            "_grouped_declaration_body",
            "read_declaration_scope",
            "read_selected_package_source",
            "read_selected_participant_view",
            "inspect_inputs",
            "_read_product_projection_inputs",
            "_source_projection_pair",
            "_read_source_projection_pair",
            "_closure",
            "_check_declaration_projection_result",
            "_capture_original_declaration_coordinate",
            "_check_original_declaration_coordinate",
            "_copy_original_declaration_scope",
            "_capture_original_binding_coordinate",
            "_check_original_binding_coordinate",
            "_declaration_record",
            "_selected_record",
        )
    )

    _GROUP_METHOD_FUNCTIONS = {
        name: getattr(WorkspaceDeclarationScopeRuntime, name)
        for name, _ in _GROUP_METHOD_DESCRIPTORS
    }


    _check_group_methods = _bind_group_method_check(
        WorkspaceDeclarationScopeRuntime, _GROUP_METHOD_DESCRIPTORS,
    )

    _original_group_method = _bind_original_group_method(
        _check_group_methods, _GROUP_METHOD_DESCRIPTORS, _GROUP_METHOD_FUNCTIONS,
    )

    scope_dispatch = _original_group_method

    return (WorkspaceDeclarationScopeRuntime, _GROUP_METHOD_DESCRIPTORS,
            _GROUP_METHOD_FUNCTIONS, _check_group_methods, _original_group_method)


(WorkspaceDeclarationScopeRuntime, _GROUP_METHOD_DESCRIPTORS,
 _GROUP_METHOD_FUNCTIONS, _check_group_methods,
 _original_group_method) = _build_declaration_scope_runtime()
WorkspaceDeclarationScopeRuntime.__qualname__ = "WorkspaceDeclarationScopeRuntime"
del _build_declaration_scope_runtime


# Capture original Code codec entrances once; older Code packages may omit the
# additive reference, in which case only the new context refuses.
_DECLARATION_ENCODER = _declaration_codec.encode_retained_declaration_scope
_DECLARATION_CONTEXT_REF = getattr(
    _declaration_codec, "RETAINED_DECLARATION_SCOPE_V3_REF", None
)


# Bind new helper dispatch once, as the original issuer is defined. A copied or
# self-restoring attribute must never execute before a later identity check.
_GROUP_ORIGINAL_ORIGIN = WorkspaceDeclarationScopeRuntime._check_origin
_GROUP_ORIGINAL_PROJECTION = WorkspaceDeclarationScopeRuntime._grouped_selected_values
_GROUP_ORIGINAL_CONTRACTS = (
    WorkspaceDeclarationScopeRuntime._check_group_source_contracts
)

def _original_group_contracts(
    issuer,
    contracts,
    kind: type[
        SemanticInputSourceContract | SemanticInputContextContract
    ] = SemanticInputSourceContract,
):
    _check_group_methods(issuer)
    _GROUP_ORIGINAL_CONTRACTS(contracts, kind)
    _check_group_methods(issuer)


def _original_group_projection(issuer, family):
    _check_group_methods(issuer)
    value = _GROUP_ORIGINAL_PROJECTION(issuer, family)
    _check_group_methods(issuer)
    return value


def _clear_group_failure_frames(error: BaseException) -> None:
    """Release inactive Workspace frames without clearing foreign owner frames."""
    # Read the built-in exception slot without dispatching a foreign attribute.
    trace = BaseException.__dict__["__traceback__"].__get__(error, type(error))
    frame = None
    try:
        while trace is not None:
            frame = trace.tb_frame
            if frame.f_globals is globals():
                try:
                    frame.clear()
                except RuntimeError:
                    # Still-active caller frames clear their arguments explicitly.
                    pass
            trace = trace.tb_next
    finally:
        del error, trace, frame




def _check_declaration_codec() -> None:
    if (
        _DECLARATION_CONTEXT_REF is None
        or inspect.getattr_static(
            _declaration_codec, "encode_retained_declaration_scope", None
        )
        is not _DECLARATION_ENCODER
        or inspect.getattr_static(
            _declaration_codec, "RETAINED_DECLARATION_SCOPE_V3_REF", None
        )
        is not _DECLARATION_CONTEXT_REF
    ):
        raise SourceObservationUnavailable(
            "original_declaration_context_codec_unavailable"
        )
