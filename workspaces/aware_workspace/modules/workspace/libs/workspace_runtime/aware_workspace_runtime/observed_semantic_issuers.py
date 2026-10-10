"""Shared retained-source issuer core and explicitly isolated compatibility factory.

The isolated factory remains ineligible for production origin registration.
The operation-context-bound factory lives in semantic_issuer_factory.py.
"""

from __future__ import annotations

import copy
import inspect
import os
import threading
from dataclasses import dataclass, fields
from typing import Any, Never, Self

from aware_code_module_manifest_contract_runtime import (
    AwareModuleSpecV2,
    AwareModuleSpecV3,
    DeclarationTable,
    parse_module_manifest,
)
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    SemanticDependencyTargetConstraint,
    SemanticPackageCoordinate,
    encode_semantic_candidate_listing,
)
from aware_code_semantic_contract_runtime.dependency_inputs import (
    SemanticDependencyTarget,
)
from aware_code_semantic_contract_runtime.retained_admission_interfaces import (
    RetainedSemanticAdmissionExpectation,
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
from aware_code_semantic_contract_runtime.semantic_candidates import (
    SEMANTIC_CANDIDATE_LISTING_REF,
)

from .observed_membership import (
    WorkspaceObservedPackageMembership,
    WorkspaceObservedPackageMembershipRuntime,
)
from .source_observation import (
    WorkspaceRetainedRootObservation,
    WorkspaceSourceObservationRuntime,
)
from .source_observation_io import SourceObservationUnavailable


class WorkspacePackageContextAdmission:
    __slots__ = ()

    def __new__(cls):
        raise TypeError("Workspace issues nominal handles")

    def __reduce__(self):
        raise TypeError("admissions cannot be serialized or copied")


class WorkspaceDeclarationInventoryAdmission(WorkspacePackageContextAdmission):
    __slots__ = ()


@dataclass(frozen=True)
class _Source:
    membership: WorkspaceObservedPackageMembership
    module_body: bytes
    manifest_body: bytes
    context: CodeSemanticPackageContextInput
    namespace: str
    roots: tuple[str, ...]
    mappings: tuple


@dataclass(frozen=True)
class _Record:
    source: _Source
    inventory: CodeSemanticDeclarationTargetInventory
    targets: tuple[_Source, ...]
    expected: RetainedSemanticAdmissionExpectation


_IDENTITIES = frozenset(
    {
        "runtime",
        "generation_identity",
        "operation_identity",
        "selected_provider_registration",
    }
)


def _unavailable(reason: str) -> Never:
    raise SourceObservationUnavailable(reason)


def _plain(value) -> Any:
    if type(value) is DeclarationTable:
        return {k: _plain(v) for k, v in value.entries}
    if type(value) is tuple:
        return tuple(_plain(v) for v in value)
    return value


def _claim(tag, *, nullable=False) -> Any:
    if tag.state == "present":
        return _plain(tag.value)
    if nullable and tag.state == "absent":
        return None
    _unavailable("occurrence_evidence_unavailable")


def _snapshot(expected):
    if type(expected) is not RetainedSemanticAdmissionExpectation:
        _unavailable("exact_expectation_required")
    return RetainedSemanticAdmissionExpectation(
        **{
            f.name: (
                getattr(expected, f.name)
                if f.name in _IDENTITIES
                else copy.deepcopy(getattr(expected, f.name))
            )
            for f in fields(expected)
        }
    )


class _WorkspaceSemanticIssuerCore:
    """One original runtime for two handles and internal assignment comparison.

    Internal source derivation only. Concrete factories separately bind either
    fixture expectations or original nominal Code operation contexts.
    """

    _observation_runtime: WorkspaceSourceObservationRuntime
    _membership_runtime: WorkspaceObservedPackageMembershipRuntime
    _observation: WorkspaceRetainedRootObservation
    _pid: int
    _closed: bool
    _records: dict[object, _Record]
    _members: dict[tuple[str, str, str], WorkspaceObservedPackageMembership]
    _issued: list[tuple[object, str]]
    _source_validation_depth: int
    _lock: Any

    def __init__(self, *args, **kwargs):
        raise TypeError("use the owning issuer assembly")

    @classmethod
    def _initialize(
        cls,
        *,
        observation_runtime,
        membership_runtime,
        observation,
    ) -> Self:
        if type(observation_runtime) is not WorkspaceSourceObservationRuntime:
            raise TypeError("original Workspace observation runtime required")
        if type(membership_runtime) is not WorkspaceObservedPackageMembershipRuntime:
            raise TypeError("original Workspace membership runtime required")
        observation_runtime.revalidate(observation)
        self = object.__new__(cls)
        self._observation_runtime = observation_runtime
        self._membership_runtime = membership_runtime
        self._observation = observation
        self._pid = os.getpid()
        self._closed = False
        self._records = {}
        self._members = {}
        self._issued = []
        self._dependency_source_binding = None
        self._source_validation_depth = 0
        self._lock = threading.RLock()
        return self

    def _bind_original_dependency_source(self, runtime, source):
        """Fixed Workspace assembly only; borrows the original source, never a projection."""
        from .dependency_scope_admission import WorkspaceDependencyScopeRuntime

        with self._lock:
            if (
                self._closed
                or self._pid != os.getpid()
                or self._dependency_source_binding is not None
                or self._records
                or self._members
                or self._issued
            ):
                _unavailable("qualified_issuer_binding_unavailable")
            if type(runtime) is not WorkspaceDependencyScopeRuntime:
                _unavailable("original_dependency_source_runtime_required")
            record = runtime._record(source)
            if (
                runtime._observation is not self._observation_runtime
                or runtime._scope._membership_runtime is not self._membership_runtime
                or record.observation is not self._observation
            ):
                _unavailable("qualified_issuer_source_origin_differs")
            name = "read_preliminary_closure"
            method = getattr(runtime, name)
            descriptor = inspect.getattr_static(runtime, name)
            if (
                not inspect.ismethod(method)
                or method.__self__ is not runtime
                or method.__func__ is not descriptor
            ):
                _unavailable("original_dependency_source_reader_required")
            closure = method(source)
            validate_name = "validate_preliminary_closure"
            validate_method = getattr(runtime, validate_name)
            validate_descriptor = inspect.getattr_static(runtime, validate_name)
            if (
                not inspect.ismethod(validate_method)
                or validate_method.__self__ is not runtime
                or validate_method.__func__ is not validate_descriptor
            ):
                _unavailable("original_dependency_source_validator_required")
            self._dependency_source_binding = (
                runtime,
                source,
                record,
                descriptor,
                method,
                validate_descriptor,
                validate_method,
                closure,
                closure.closure_digest,
            )

    def _qualified_closure(self):
        binding = self._dependency_source_binding
        if binding is None:
            return None
        (
            runtime,
            source,
            record,
            descriptor,
            method,
            validate_descriptor,
            validate_method,
            closure,
            digest,
        ) = binding
        if (
            self._closed
            or self._pid != os.getpid()
            or inspect.getattr_static(runtime, "read_preliminary_closure")
            is not descriptor
            or not inspect.ismethod(method)
            or method.__self__ is not runtime
            or method.__func__ is not descriptor
            or inspect.getattr_static(runtime, "validate_preliminary_closure")
            is not validate_descriptor
            or not inspect.ismethod(validate_method)
            or validate_method.__self__ is not runtime
            or validate_method.__func__ is not validate_descriptor
            or runtime._record(source) is not record
            or runtime._observation is not self._observation_runtime
            or runtime._scope._membership_runtime is not self._membership_runtime
            or record.observation is not self._observation
        ):
            _unavailable("qualified_issuer_source_changed")
        if self._source_validation_depth == 0:
            validate_method(source)
        if closure.closure_digest != digest or runtime._record(source) is not record:
            _unavailable("qualified_issuer_source_changed")
        return closure

    def _evidence(self, membership):
        if self._source_validation_depth:
            return self._membership_runtime._evidence_after_observation_validation(
                membership,
                observation_runtime=self._observation_runtime,
                observation=self._observation,
            )
        return self._membership_runtime.evidence(membership)

    def _qualified_member(self, membership, closure):
        evidence = self._evidence(membership)
        matches = [
            p
            for scope in closure.scopes
            if scope.scope_key == evidence.workspace_manifest_path
            for p in scope.projection.packages
            if (p.module_id, p.package_id) == (evidence.module_id, evidence.package_id)
        ]
        if len(matches) != 1:
            _unavailable("package_outside_original_qualified_scope")
        package = matches[0]
        for name in (
            "package_kind",
            "module_manifest_path",
            "package_root",
            "manifest_relative_path",
            "source_identity_digest",
        ):
            if getattr(package, name) != getattr(evidence, name):
                _unavailable("qualified_membership_correspondence_differs")
        return package

    @property
    def observation_runtime(self):
        return self._observation_runtime

    @property
    def membership_runtime(self):
        return self._membership_runtime

    def _check(self, membership):
        if self._closed or self._pid != os.getpid():
            _unavailable("issuer_lifetime_unavailable")
        if self._source_validation_depth:
            self._membership_runtime._validate_observation_origin_after_revalidation(
                membership,
                observation_runtime=self._observation_runtime,
                observation=self._observation,
            )
        else:
            self._membership_runtime.validate_observation_origin(
                membership,
                observation_runtime=self._observation_runtime,
                observation=self._observation,
            )

    def _resolve(self, scope, address, *, closure=None):
        address_scope = address.get("scope")
        if address_scope is not None and address_scope["kind"] == "dependency":
            if closure is None:
                _unavailable("qualified_dependency_source_required")
            matches = [
                entry.scope_key
                for entry in closure.scopes
                if entry.workspace_handle == address_scope["workspace_handle"]
            ]
            if len(matches) != 1 or not any(
                edge.declaring_scope_key == scope
                and edge.target_scope_key == matches[0]
                for edge in closure.edges
            ):
                _unavailable("original_direct_dependency_edge_required")
            scope = matches[0]
        if closure is not None and scope not in {
            entry.scope_key for entry in closure.scopes
        }:
            _unavailable("workspace_outside_original_qualified_scope")
        key = (scope, address["module_id"], address["package_id"])
        if key not in self._members:
            if len(self._members) >= 1024:
                _unavailable("issuer_membership_capacity")
            self._members[key] = self._membership_runtime.admit(
                observation=self._observation,
                workspace_manifest_path=scope,
                module_id=key[1],
                package_id=key[2],
            )
        self._check(self._members[key])
        if closure is not None:
            self._qualified_member(self._members[key], closure)
        return self._members[key]

    def _declaration(self, membership):
        self._check(membership)
        evidence = self._evidence(membership)
        body = self._membership_runtime.read_declaring_module(membership)
        model = parse_module_manifest(body)
        if (
            type(model) is not AwareModuleSpecV2
            and type(model) is not AwareModuleSpecV3
        ):
            _unavailable("v2_or_v3_occurrence_required")
        if type(model) is AwareModuleSpecV3 and self._dependency_source_binding is None:
            _unavailable("qualified_dependency_source_required")
        matches = [
            d for d in model.package_declarations if d.package_id == evidence.package_id
        ]
        if len(matches) != 1:
            _unavailable("ambiguous_occurrence")
        return evidence, body, matches[0]

    def _source(self, membership, *, closure=None):
        if closure is None:
            closure = self._qualified_closure()
        if closure is not None:
            self._qualified_member(membership, closure)
        evidence, module_body, declaration = self._declaration(membership)
        occurrence = declaration.occurrence
        address = _claim(occurrence.registration)
        provider = self._resolve(
            evidence.workspace_manifest_path, address, closure=closure
        )
        _, _, provider_declaration = self._declaration(provider)
        registrations = [_plain(r) for r in provider_declaration.registrations]
        selected = [r for r in registrations if r["key"] == address["registration_key"]]
        if len(selected) != 1:
            _unavailable("registration_declaration_unavailable")
        registration = selected[0]
        if closure is not None:
            # Code interprets exact retained profile restrictions and kind pairing.
            # Portable interpretation does not issue live provider authority.
            from aware_code_retained_registry_policy_runtime.qualified_calculation import (
                qualified_occurrence,
            )

            package, interpreted, declared = qualified_occurrence(
                closure, evidence.source_identity_digest
            )
            if (
                package != self._qualified_member(membership, closure)
                or interpreted != occurrence
                or _plain(declared) != registration
            ):
                _unavailable("qualified_registration_correspondence_differs")
        # Workspace preserves observed occurrence identity. Code owns the
        # declared/semantic kind correspondence through its original registration
        # admission; source inspection cannot manufacture or replace that grant.
        if (
            evidence.manifest_relative_path.split("/")[-1]
            != registration["manifest_filename"]
        ):
            _unavailable("manifest_registration_mismatch")
        # Declared correspondence only; live Code registry admission is separate.
        manifest = self._membership_runtime.read(
            membership, relative_path=evidence.manifest_relative_path
        )
        name = _claim(occurrence.semantic_package_name)
        version = _claim(occurrence.semantic_version)
        config = _claim(occurrence.configuration, nullable=True)
        package = SemanticPackageCoordinate(
            f"package:{name}@{version}",
            evidence.package_kind,
            ContentDigest.of_bytes(manifest),
        )
        context = CodeSemanticPackageContextInput(
            package,
            evidence.source_identity_digest,
            evidence.manifest_relative_path,
            _claim(occurrence.code_package_name),
            version,
            _claim(occurrence.source_code_package_id, nullable=True),
            None if config is None else config["config_id"],
            None if config is None else config["config_key"],
        )
        return _Source(
            membership,
            module_body,
            manifest,
            context,
            _claim(occurrence.namespace),
            _claim(occurrence.owned_roots),
            _claim(occurrence.dependency_targets),
        )

    def _derive(self, membership):
        closure = self._qualified_closure()
        source = self._source(membership, closure=closure)
        scope = self._evidence(membership).workspace_manifest_path
        entries, retained_targets = [], []
        for mapping in source.mappings:
            targets = []
            for address in mapping["targets"]:
                target = self._source(
                    self._resolve(scope, address, closure=closure), closure=closure
                )
                retained_targets.append(target)
                targets.append(
                    SemanticDependencyTarget(target.context.package, target.roots)
                )
            targets.sort(key=lambda t: t.package.package_ref)
            entries.append(
                CodeSemanticDeclarationTarget(
                    mapping["dependency_kind"],
                    mapping["dependency_ref"],
                    tuple(targets),
                    tuple(
                        SemanticDependencyTargetConstraint.create(**c)
                        for c in mapping["constraints"]
                    ),
                )
            )
        inventory = CodeSemanticDeclarationTargetInventory(
            source.context.package,
            source.context.source_identity_digest,
            tuple(entries),
        )
        self._check(membership)
        self._qualified_closure()
        return source, inventory, tuple(retained_targets)

    def inspect_inputs(self, membership):
        """Portable source projections, not admission or entitlement."""
        with self._lock:
            source, inventory, _ = self._derive(membership)
            return copy.deepcopy((source.context, inventory))

    def _match_inputs(self, source, inventory, expected):
        if (
            expected.process_id != self._pid
            or expected.stage not in ("source_planning", "authority_derivation")
            or expected.package != source.context.package
            or expected.source_identity_digest != source.context.source_identity_digest
        ):
            _unavailable("input_context_mismatch")
        evidence = self._evidence(source.membership)
        checks = (
            (expected.manifest_coordinate, source.manifest_body, None),
            (
                expected.candidate_coordinate,
                encode_semantic_candidate_listing(evidence.candidate_listing),
                SEMANTIC_CANDIDATE_LISTING_REF,
            ),
            (
                expected.package_context_coordinate,
                encode_package_context_input(source.context),
                PACKAGE_CONTEXT_INPUT_REF,
            ),
            (
                expected.declaration_inventory_coordinate,
                encode_declaration_target_inventory(inventory),
                DECLARATION_TARGET_INVENTORY_REF,
            ),
        )
        for coordinate, body, contract in checks:
            if (
                coordinate.digest != ContentDigest.of_bytes(body)
                or coordinate.size_bytes != len(body)
                or (contract is not None and coordinate.contract != contract)
            ):
                _unavailable("retained_coordinate_mismatch")

    def _validate(self, admission, expected, kind):
        if type(admission) is not kind or admission not in self._records:
            _unavailable("foreign_or_reconstructed_admission")
        record = self._records[admission]
        closure = self._qualified_closure()
        self._check(record.source.membership)
        if type(expected) is not RetainedSemanticAdmissionExpectation:
            _unavailable("exact_expectation_required")
        for f in fields(expected):
            a, b = getattr(expected, f.name), getattr(record.expected, f.name)
            matches = (a is b) if f.name in _IDENTITIES else (a == b)
            if not matches:
                _unavailable("original_context_mismatch")
        for source in (record.source, *record.targets):
            self._check(source.membership)
            if closure is not None:
                self._qualified_member(source.membership, closure)
        self._match_inputs(record.source, record.inventory, expected)
        self._qualified_closure()
        return record

    def validate_package_context_admission(
        self,
        admission: WorkspacePackageContextAdmission,
        *,
        expected: RetainedSemanticAdmissionExpectation,
    ) -> None:
        with self._lock:
            self._validate(admission, expected, WorkspacePackageContextAdmission)

    def validate_declaration_inventory_admission(
        self,
        admission: WorkspaceDeclarationInventoryAdmission,
        *,
        expected: RetainedSemanticAdmissionExpectation,
    ) -> None:
        with self._lock:
            self._validate(admission, expected, WorkspaceDeclarationInventoryAdmission)

    def validate_occurrence_assignments(
        self,
        admission: WorkspacePackageContextAdmission,
        *,
        expected: RetainedSemanticAdmissionExpectation,
        namespace: str,
        owned_roots: tuple[str, ...],
    ) -> None:
        with self._lock:
            record = self._validate(
                admission, expected, WorkspacePackageContextAdmission
            )
            if (
                type(namespace) is not str
                or namespace != record.source.namespace
                or type(owned_roots) is not tuple
                or owned_roots != record.source.roots
            ):
                _unavailable("occurrence_assignment_mismatch")

    def close(self) -> None:
        with self._lock:
            self._closed = True
            self._records.clear()
            # Release only memberships this issuer created. Invalidated evidence
            # may already be unavailable; the host owns final runtime cleanup.
            for membership in self._members.values():
                try:
                    self._membership_runtime.release(membership)
                except SourceObservationUnavailable:
                    pass
            self._members.clear()
            self._issued.clear()


class WorkspaceObservedSemanticIssuerRuntime(_WorkspaceSemanticIssuerCore):
    """Explicitly isolated source/proof factory; never promoted to a real origin."""

    @classmethod
    def for_isolated_proof(
        cls, *, observation_runtime, membership_runtime, observation
    ):
        return cls._initialize(
            observation_runtime=observation_runtime,
            membership_runtime=membership_runtime,
            observation=observation,
        )

    def issue_isolated_pair(self, membership, *, expected):
        """Issue fixture-bound handles; expected is NOT a trusted bootstrap context.

        This pins fixture context to test substitution rejection only. Code host
        admission and namespace policy are not supplied by this operation.
        """
        with self._lock:
            if len(self._records) >= 128:
                _unavailable("issuer_admission_capacity")
            original = _snapshot(expected)
            if any(
                op is original.operation_identity and stage == original.stage
                for op, stage in self._issued
            ):
                _unavailable("isolated_issuance_replay")
            source, inventory, targets = self._derive(membership)
            self._match_inputs(source, inventory, original)
            self._check(membership)
            record = _Record(source, inventory, targets, original)
            context = object.__new__(WorkspacePackageContextAdmission)
            target = object.__new__(WorkspaceDeclarationInventoryAdmission)
            self._records[context] = self._records[target] = record
            self._issued.append((original.operation_identity, original.stage))
            return context, target
