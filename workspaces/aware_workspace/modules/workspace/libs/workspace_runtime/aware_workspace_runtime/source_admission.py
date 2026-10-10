"""Contextual admission of owner-defined retained semantic source.

This is the non-``.aware`` sibling of R1.  It contextualizes Code's existing
owner-produced package authority with the original Workspace observation and
nominal issuer handles.  It does not parse an owner manifest, mint Code
authority, admit a catalog, or create a WorkspaceRevision.
"""

from __future__ import annotations

import copy
import os
from dataclasses import dataclass, replace
from threading import RLock
from weakref import WeakKeyDictionary

from aware_code_semantic_contract_runtime import (
    ContentDigest,
    SemanticContractRef,
    SemanticInputProductionExpectation,
    SemanticInputSourceBody,
    SemanticInputSourceCoordinate,
    SemanticPackageCoordinate,
    SemanticValueCoordinate,
    TerminalStatus,
)
from aware_code_semantic_contract_runtime.package_authority_body_codec import (
    PackageAuthorityBodyCodec,
)
from aware_code_semantic_contract_runtime.portable_semantic_package_authority import (
    CodePortableSemanticPackageAuthority,
)
from aware_code_semantic_contract_runtime.retained_admission_interfaces import (
    RetainedSemanticAdmissionExpectation,
)
from aware_code_semantic_contract_runtime.retained_input_projections import (
    CodeSemanticDeclarationTargetInventory,
)
from aware_code_semantic_contract_runtime.runtime import ExecutionCompletion

from .declaration_scope_admission import (
    WorkspaceDeclarationScopeRuntime,
    WorkspaceSelectedPackageSource,
)
from .materialization_declaration_selection import WorkspaceDeclaredMaterializationRoot
from .observed_membership import (
    WorkspaceObservedPackageMembership,
    WorkspaceObservedPackageMembershipRuntime,
)
from .observed_semantic_issuers import (
    WorkspaceDeclarationInventoryAdmission,
    WorkspacePackageContextAdmission,
)
from .semantic_issuer_factory import WorkspaceSourcePlanningSemanticIssuerRuntime
from .semantic_materialization_publication import (
    WorkspaceMaterializationPackageOccurrenceV4,
)
from .source_observation import WorkspaceObservedSelectedPackageEvidence


class WorkspaceOwnerDefinedSourceAdmission:
    """Nominal contextual source authority; never portable or serializable."""

    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("Workspace issues owner-defined source admissions")

    def __reduce__(self):
        raise TypeError("owner-defined source admissions are process-local")


@dataclass(frozen=True, slots=True)
class WorkspaceOwnerDefinedSourceInspection:
    repository_ref: str
    workspace_ref: str
    module_ref: str
    package_id: str
    package_root: str
    package_kind: str
    manifest_relative_path: str
    source_identity_digest: ContentDigest
    package: SemanticPackageCoordinate
    manifest_contract: SemanticContractRef
    profile_ref: str
    operation_kinds: tuple[str, ...]
    terminal_roles: tuple[str, ...]
    configured: bool
    package_authority: CodePortableSemanticPackageAuthority
    declaration_inventory: CodeSemanticDeclarationTargetInventory
    authority_result_coordinate: SemanticValueCoordinate


@dataclass(slots=True)
class _Record:
    membership: WorkspaceObservedPackageMembership
    package_admission: WorkspacePackageContextAdmission
    inventory_admission: WorkspaceDeclarationInventoryAdmission
    context: object
    expected: RetainedSemanticAdmissionExpectation
    completion: ExecutionCompletion
    inspection: WorkspaceOwnerDefinedSourceInspection


class WorkspaceOwnerDefinedSourceAdmissionRuntime:
    """One Workspace contextual issuer over original retained resources."""

    _membership_runtime: WorkspaceObservedPackageMembershipRuntime
    _semantic_issuer: WorkspaceSourcePlanningSemanticIssuerRuntime
    _records: WeakKeyDictionary
    _issued: set[tuple[object, str]]
    _lock: RLock
    _pid: int
    _closed: bool

    def __init_subclass__(cls, **kwargs):
        raise TypeError("owner-defined source admission runtime is sealed")

    def __new__(cls):
        raise TypeError("owner-defined source runtime requires fixed assembly")

    @classmethod
    def _assemble(
        cls,
        *,
        membership_runtime: WorkspaceObservedPackageMembershipRuntime,
        semantic_issuer: WorkspaceSourcePlanningSemanticIssuerRuntime,
    ):
        if type(membership_runtime) is not WorkspaceObservedPackageMembershipRuntime:
            raise TypeError("exact Workspace membership runtime required")
        if type(semantic_issuer) is not WorkspaceSourcePlanningSemanticIssuerRuntime:
            raise TypeError("exact Workspace semantic issuer required")
        value = object.__new__(cls)
        value._membership_runtime = membership_runtime
        value._semantic_issuer = semantic_issuer
        value._records = WeakKeyDictionary()
        value._issued = set()
        value._lock = RLock()
        value._pid = os.getpid()
        value._closed = False
        return value

    @staticmethod
    def _result_coordinate(completion):
        result = completion.result
        if result.status is TerminalStatus.CURRENT:
            coordinate = result.current_result
        elif result.status is TerminalStatus.DELTA and result.transition is not None:
            coordinate = result.transition.result
        else:
            raise RuntimeError("successful package-authority completion required")
        if coordinate is None or coordinate.role != "package_authority":
            raise RuntimeError("exact package-authority result required")
        return coordinate

    def _validate_record(self, record: _Record) -> None:
        from aware_code_retained_registry_policy_runtime.authority_execution import (
            read_authority_completion,
        )

        if self._closed or self._pid != os.getpid():
            raise RuntimeError("owner_defined_source_runtime_unavailable")
        self._membership_runtime.revalidate(record.membership)
        self._semantic_issuer.validate_package_context_admission(
            record.package_admission, expected=record.expected
        )
        self._semantic_issuer.validate_declaration_inventory_admission(
            record.inventory_admission, expected=record.expected
        )
        if read_authority_completion(record.context) is not record.completion:
            raise RuntimeError("original authority completion changed")
        coordinate = self._result_coordinate(record.completion)
        body = record.completion.body_for(coordinate)
        if (
            coordinate != record.inspection.authority_result_coordinate
            or body.canonical_body
            != record.inspection.package_authority.canonical_bytes()
        ):
            raise RuntimeError("owner-defined authority result changed")
        self._membership_runtime.revalidate(record.membership)

    def issue(
        self,
        membership,
        package_admission,
        inventory_admission,
        *,
        context,
        expected,
        completion,
    ) -> WorkspaceOwnerDefinedSourceAdmission:
        if type(membership) is not WorkspaceObservedPackageMembership:
            raise TypeError("original Workspace membership required")
        if type(package_admission) is not WorkspacePackageContextAdmission:
            raise TypeError("original Workspace package admission required")
        if type(inventory_admission) is not WorkspaceDeclarationInventoryAdmission:
            raise TypeError("original Workspace inventory admission required")
        if (
            type(expected) is not RetainedSemanticAdmissionExpectation
            or expected.stage != "authority_derivation"
            or type(completion) is not ExecutionCompletion
        ):
            raise TypeError("exact authority operation evidence required")
        with self._lock:
            key = (expected.operation_identity, expected.stage)
            if key in self._issued:
                raise RuntimeError("owner_defined_source_admission_replay")
            evidence = self._membership_runtime.evidence(membership)
            workspace_ref = self._semantic_issuer.inspect_workspace_ref(membership)
            if evidence.manifest_relative_path.endswith(".aware"):
                raise RuntimeError("aware source requires R1 composition authority")
            package_context, inventory = self._semantic_issuer.inspect_inputs(membership)
            self._semantic_issuer.validate_package_context_admission(
                package_admission, expected=expected
            )
            self._semantic_issuer.validate_declaration_inventory_admission(
                inventory_admission, expected=expected
            )
            coordinate = self._result_coordinate(completion)
            authority = PackageAuthorityBodyCodec().decode(
                completion.body_for(coordinate).canonical_body
            )
            if type(authority) is not CodePortableSemanticPackageAuthority:
                raise RuntimeError("exact Code package authority required")
            candidates = {
                candidate.relative_path
                for candidate in evidence.candidate_listing.candidates
            }
            direct_targets = tuple(
                sorted(
                    {
                        target.package.package_ref
                        for entry in inventory.entries
                        for target in entry.targets
                    },
                    key=str.encode,
                )
            )
            if (
                expected.package != package_context.package
                or authority.package_ref != package_context.package.package_ref
                or authority.semantic_version != package_context.semantic_version
                or authority.manifest_relative_path
                != package_context.manifest_relative_path
                or authority.manifest_relative_path != evidence.manifest_relative_path
                or authority.direct_dependency_package_refs != direct_targets
                or not set(authority.declared_source_paths) <= candidates
            ):
                raise RuntimeError("owner-defined authority differs from retained source")
            self._semantic_issuer.validate_occurrence_assignments(
                package_admission,
                expected=expected,
                namespace=authority.fqn_prefix,
                owned_roots=authority.owned_semantic_root_refs,
            )
            inspection = WorkspaceOwnerDefinedSourceInspection(
                repository_ref=evidence.repository_binding_ref,
                workspace_ref=workspace_ref,
                module_ref=evidence.module_id,
                package_id=evidence.package_id,
                package_root=evidence.package_root,
                package_kind=evidence.package_kind,
                manifest_relative_path=evidence.manifest_relative_path,
                source_identity_digest=copy.deepcopy(evidence.source_identity_digest),
                package=copy.deepcopy(expected.package),
                manifest_contract=copy.deepcopy(expected.manifest_coordinate.contract),
                profile_ref=expected.profile.profile_ref,
                operation_kinds=expected.profile.operation_kinds,
                terminal_roles=tuple(
                    sorted(
                        {
                            expected.profile.terminal_result_role,
                            expected.profile.terminal_effect_role,
                            *expected.profile.terminal_output_roles,
                        },
                        key=str.encode,
                    )
                ),
                configured=package_context.config_id is not None,
                package_authority=authority,
                declaration_inventory=copy.deepcopy(inventory),
                authority_result_coordinate=copy.deepcopy(coordinate),
            )
            admission = object.__new__(WorkspaceOwnerDefinedSourceAdmission)
            record = _Record(
                membership,
                package_admission,
                inventory_admission,
                context,
                expected,
                completion,
                inspection,
            )
            self._records[admission] = record
            self._issued.add(key)
            self._validate_record(record)
            return admission

    def inspect(self, admission) -> WorkspaceOwnerDefinedSourceInspection:
        with self._lock:
            if type(admission) is not WorkspaceOwnerDefinedSourceAdmission:
                raise TypeError("exact owner-defined source admission required")
            record = self._records.get(admission)
            if record is None:
                raise RuntimeError("foreign_or_expired_source_admission")
            self._validate_record(record)
            detached_authority = PackageAuthorityBodyCodec().decode(
                record.inspection.package_authority.canonical_bytes()
            )
            if type(detached_authority) is not CodePortableSemanticPackageAuthority:
                raise RuntimeError("exact detached Code package authority required")
            return replace(
                record.inspection,
                package_authority=detached_authority,
                declaration_inventory=copy.deepcopy(
                    record.inspection.declaration_inventory
                ),
                authority_result_coordinate=copy.deepcopy(
                    record.inspection.authority_result_coordinate
                ),
            )

    def _semantic_input_record(
        self,
        admission: object,
        *,
        expected: SemanticInputProductionExpectation,
    ) -> _Record:
        if type(admission) is not WorkspaceOwnerDefinedSourceAdmission:
            raise TypeError("exact owner-defined source admission required")
        if type(expected) is not SemanticInputProductionExpectation:
            raise TypeError("exact semantic input expectation required")
        expected.__post_init__()
        record = self._records.get(admission)
        if record is None:
            raise RuntimeError("foreign_or_expired_source_admission")
        if expected.source_identity is not admission:
            raise RuntimeError("semantic_input_source_identity_mismatch")
        self._validate_record(record)
        if expected.package_identity.package != record.inspection.package:
            raise RuntimeError("semantic_input_package_coordinate_mismatch")
        if (
            expected.package_identity.package_name
            != record.inspection.package_authority.semantic_package.name
        ):
            raise RuntimeError("semantic_input_package_name_mismatch")
        return record

    def _validate_semantic_input_coordinates(
        self,
        record: _Record,
        coordinates: tuple[SemanticInputSourceCoordinate, ...],
    ) -> None:
        evidence = self._membership_runtime.evidence(record.membership)
        candidates = {
            candidate.relative_path: candidate.content_digest
            for candidate in evidence.candidate_listing.candidates
        }
        allowed_paths = {
            evidence.manifest_relative_path,
            *record.inspection.package_authority.declared_source_paths,
        }
        for source in coordinates:
            digest = candidates.get(source.relative_path)
            if source.relative_path not in allowed_paths or digest is None:
                raise RuntimeError("semantic_input_source_not_admitted")
            if digest != source.coordinate.digest:
                raise RuntimeError("semantic_input_source_coordinate_mismatch")

    def validate_semantic_input_source(
        self,
        source_admission: object,
        *,
        expected: SemanticInputProductionExpectation,
    ) -> None:
        """Validate one Code use against the original Workspace source authority."""

        with self._lock:
            record = self._semantic_input_record(
                source_admission, expected=expected
            )
            self._validate_semantic_input_coordinates(
                record, expected.source_coordinates
            )
            for source in expected.source_coordinates:
                body = self._membership_runtime.read(
                    record.membership, relative_path=source.relative_path
                )
                SemanticInputSourceBody(source, body).__post_init__()
            self._validate_record(record)

    def read_semantic_input_sources(
        self,
        source_admission: object,
        *,
        expected: SemanticInputProductionExpectation,
    ) -> tuple[SemanticInputSourceBody, ...]:
        """Return detached retained bytes; the admission never crosses into owners."""

        with self._lock:
            record = self._semantic_input_record(
                source_admission, expected=expected
            )
            self._validate_semantic_input_coordinates(
                record, expected.source_coordinates
            )
            sources = tuple(
                SemanticInputSourceBody(
                    source,
                    bytes(
                        self._membership_runtime.read(
                            record.membership,
                            relative_path=source.relative_path,
                        )
                    ),
                )
                for source in expected.source_coordinates
            )
            self._validate_record(record)
            return sources

    def close(self) -> None:
        with self._lock:
            self._closed = True
            self._records.clear()


@dataclass(slots=True)
class _V3Record:
    root: WorkspaceDeclaredMaterializationRoot
    selected: WorkspaceSelectedPackageSource
    package_admission: WorkspacePackageContextAdmission
    inventory_admission: WorkspaceDeclarationInventoryAdmission
    context: object
    expected: RetainedSemanticAdmissionExpectation
    completion: ExecutionCompletion
    inspection: WorkspaceOwnerDefinedSourceInspection | None


class WorkspaceV3OwnerDefinedSourceAdmissionRuntime:
    """Versioned contextual join over the original v3 issuer and Code completion.

    This runtime issues the existing nominal source handle and the existing
    inspection shape. It neither constructs portable package meaning nor admits
    a catalog. Its fixed assembly retains the original command's v3 issuer.
    """

    def __init_subclass__(cls, **kwargs):
        raise TypeError("v3 owner-defined source runtime is sealed")

    def __new__(cls):
        raise TypeError("v3 owner-defined source runtime requires fixed assembly")

    @classmethod
    def _assemble(cls, *, issuer: WorkspaceDeclarationScopeRuntime):
        if type(issuer) is not WorkspaceDeclarationScopeRuntime:
            raise TypeError("original v3 Workspace issuer required")
        issuer._check_origin()
        value = object.__new__(cls)
        value._issuer = issuer
        value._records = WeakKeyDictionary()
        value._issued = set()
        value._lock = RLock()
        value._pid = os.getpid()
        value._closed = False
        return value

    def _inspect_original(
        self, record: _V3Record
    ) -> WorkspaceOwnerDefinedSourceInspection:
        from aware_code_retained_registry_policy_runtime.authority_execution import (
            read_authority_completion,
        )

        if self._closed or self._pid != os.getpid():
            raise RuntimeError("v3_owner_defined_source_runtime_unavailable")
        root, selected, expected = record.root, record.selected, record.expected
        binding = self._issuer.read_selected_package_source(selected)
        evidence = self._issuer.inspect_selected_package_evidence(selected)
        package_context, inventory = self._issuer.inspect_inputs(selected)
        if (
            root.workspace_manifest_path != evidence.workspace_manifest_path
            or root.module_id != evidence.module_id
            or root.package_id != evidence.package_id
            or binding.expectation.scope_key != root.workspace_manifest_path
            or binding.expectation.source_identity_digest
            != package_context.source_identity_digest
            or expected.package != package_context.package
            or expected.source_identity_digest != package_context.source_identity_digest
            or package_context.package.package_ref
            != f"package:{root.semantic_package_name}@{root.semantic_version}"
            or package_context.semantic_version != root.semantic_version
            or package_context.manifest_relative_path != evidence.manifest_relative_path
            or inventory.package != package_context.package
            or inventory.source_identity_digest != package_context.source_identity_digest
        ):
            raise RuntimeError("v3_selected_occurrence_or_context_differs")
        self._issuer.validate_package_context_admission(
            record.package_admission, expected=expected
        )
        self._issuer.validate_declaration_inventory_admission(
            record.inventory_admission, expected=expected
        )
        if read_authority_completion(record.context) is not record.completion:
            raise RuntimeError("original authority completion changed")
        coordinate = WorkspaceOwnerDefinedSourceAdmissionRuntime._result_coordinate(
            record.completion
        )
        authority = PackageAuthorityBodyCodec().decode(
            record.completion.body_for(coordinate).canonical_body
        )
        candidates = {
            candidate.relative_path for candidate in binding.candidates.candidates
        }
        direct_targets = tuple(
            sorted(
                {
                    target.package.package_ref
                    for entry in inventory.entries
                    for target in entry.targets
                },
                key=str.encode,
            )
        )
        if (
            authority.package_ref != package_context.package.package_ref
            or authority.semantic_package.name != root.semantic_package_name
            or authority.semantic_version != root.semantic_version
            or authority.manifest_relative_path != evidence.manifest_relative_path
            or authority.code_package.name != package_context.code_package_name
            or authority.code_package.source_code_package_id
            != package_context.source_code_package_id
            or authority.code_package.config_id != package_context.config_id
            or authority.code_package.config_key != package_context.config_key
            or authority.direct_dependency_package_refs != direct_targets
            or not set(authority.declared_source_paths) <= candidates
        ):
            raise RuntimeError("v3_owner_authority_differs_from_retained_source")
        self._issuer.validate_occurrence_assignments(
            record.package_admission,
            expected=expected,
            namespace=authority.fqn_prefix,
            owned_roots=authority.owned_semantic_root_refs,
        )
        self._issuer.validate_selected_package_source(
            selected,
            expectation=binding.expectation,
            binding_digest=binding.binding_digest,
        )
        if read_authority_completion(record.context) is not record.completion:
            raise RuntimeError("original authority completion changed")
        return WorkspaceOwnerDefinedSourceInspection(
            repository_ref=evidence.repository_binding_ref,
            workspace_ref=evidence.workspace_manifest_path,
            module_ref=evidence.module_id,
            package_id=evidence.package_id,
            package_root=evidence.package_root,
            package_kind=evidence.package_kind,
            manifest_relative_path=evidence.manifest_relative_path,
            source_identity_digest=package_context.source_identity_digest,
            package=package_context.package,
            manifest_contract=expected.manifest_coordinate.contract,
            profile_ref=expected.profile.profile_ref,
            operation_kinds=expected.profile.operation_kinds,
            terminal_roles=tuple(
                sorted(
                    {
                        expected.profile.terminal_result_role,
                        expected.profile.terminal_effect_role,
                        *expected.profile.terminal_output_roles,
                    },
                    key=str.encode,
                )
            ),
            configured=package_context.config_id is not None,
            package_authority=authority,
            declaration_inventory=inventory,
            authority_result_coordinate=coordinate,
        )

    def issue(
        self,
        root: WorkspaceDeclaredMaterializationRoot,
        selected: WorkspaceSelectedPackageSource,
        package_admission: WorkspacePackageContextAdmission,
        inventory_admission: WorkspaceDeclarationInventoryAdmission,
        *,
        context,
        expected: RetainedSemanticAdmissionExpectation,
        completion: ExecutionCompletion,
    ) -> WorkspaceOwnerDefinedSourceAdmission:
        if (
            type(root) is not WorkspaceDeclaredMaterializationRoot
            or type(selected) is not WorkspaceSelectedPackageSource
            or type(package_admission) is not WorkspacePackageContextAdmission
            or type(inventory_admission) is not WorkspaceDeclarationInventoryAdmission
            or type(expected) is not RetainedSemanticAdmissionExpectation
            or expected.stage != "authority_derivation"
            or type(completion) is not ExecutionCompletion
        ):
            raise TypeError("exact v3 selected authority evidence required")
        with self._lock:
            key = (expected.operation_identity, expected.stage)
            if key in self._issued:
                raise RuntimeError("v3_owner_defined_source_admission_replay")
            record = _V3Record(
                root,
                selected,
                package_admission,
                inventory_admission,
                context,
                expected,
                completion,
                None,
            )
            inspection = self._inspect_original(record)
            record.inspection = inspection
            admission = object.__new__(WorkspaceOwnerDefinedSourceAdmission)
            self._records[admission] = record
            self._issued.add(key)
            return admission

    def inspect(self, admission) -> WorkspaceOwnerDefinedSourceInspection:
        with self._lock:
            if type(admission) is not WorkspaceOwnerDefinedSourceAdmission:
                raise TypeError("exact Workspace source admission required")
            record = self._records.get(admission)
            if record is None:
                raise RuntimeError("foreign_or_expired_source_admission")
            current = self._inspect_original(record)
            if current != record.inspection:
                raise RuntimeError("v3_owner_defined_source_changed")
            return current

    def read_publication_package_occurrence(
        self, admission: WorkspaceOwnerDefinedSourceAdmission
    ) -> WorkspaceMaterializationPackageOccurrenceV4:
        """Detach the stable occurrence from the original v3 source admission."""
        with self._lock:
            before = self.inspect(admission)
            occurrence = WorkspaceMaterializationPackageOccurrenceV4(
                repository_ref=before.repository_ref,
                workspace_ref=before.workspace_ref,
                module_ref=before.module_ref,
                package_id=before.package_id,
                package_root=before.package_root,
                manifest_relative_path=before.manifest_relative_path,
            )
            if self.inspect(admission) != before:
                raise RuntimeError("v3_publication_occurrence_source_changed")
            return occurrence

    def validate_publication_package_occurrence(
        self,
        admission: WorkspaceOwnerDefinedSourceAdmission,
        *,
        occurrence: WorkspaceMaterializationPackageOccurrenceV4,
    ) -> None:
        if type(occurrence) is not WorkspaceMaterializationPackageOccurrenceV4:
            raise TypeError("exact Workspace publication occurrence required")
        occurrence.__post_init__()
        if self.read_publication_package_occurrence(admission) != occurrence:
            raise RuntimeError("v3_publication_occurrence_differs")

    def _semantic_input_record(
        self,
        admission: object,
        expected: SemanticInputProductionExpectation,
    ) -> tuple[_V3Record, WorkspaceObservedSelectedPackageEvidence]:
        if type(admission) is not WorkspaceOwnerDefinedSourceAdmission:
            raise TypeError("exact v3 owner-defined source admission required")
        if type(expected) is not SemanticInputProductionExpectation:
            raise TypeError("exact semantic input expectation required")
        expected.__post_init__()
        record = self._records.get(admission)
        if record is None:
            raise RuntimeError("foreign_or_expired_source_admission")
        inspection = self.inspect(admission)
        if (
            expected.source_identity is not admission
            or expected.package_identity.package != inspection.package
            or expected.package_identity.package_name
            != inspection.package_authority.semantic_package.name
        ):
            raise RuntimeError("v3_semantic_input_source_identity_differs")
        evidence = self._issuer.inspect_selected_package_evidence(record.selected)
        if (
            evidence.source_identity_digest != inspection.source_identity_digest.value
            or evidence.manifest_relative_path != inspection.manifest_relative_path
        ):
            raise RuntimeError("v3_semantic_input_observation_changed")
        observed = {body.relative_path: body for body in evidence.bodies}
        allowed = {
            inspection.manifest_relative_path,
            *inspection.package_authority.declared_source_paths,
        }
        for source in expected.source_coordinates:
            body = observed.get(source.relative_path)
            if source.relative_path not in allowed or body is None:
                raise RuntimeError("v3_semantic_input_source_not_admitted")
            if (
                source.coordinate.digest.value != body.content_digest
                or source.coordinate.size_bytes != body.size_bytes
            ):
                raise RuntimeError("v3_semantic_input_source_coordinate_differs")
        return record, evidence

    def semantic_input_source_coordinates(
        self,
        admission: WorkspaceOwnerDefinedSourceAdmission,
        *,
        source_scope: str,
        role: str,
        contract: SemanticContractRef,
    ) -> tuple[SemanticInputSourceCoordinate, ...]:
        """Describe the retained manifest or complete owner-declared source set.

        These detached coordinates are input proposals, not an admission. Code
        still checks the selected producer contract and calls this runtime's
        original validator and reader around owner execution.
        """
        if source_scope not in ("manifest", "declared"):
            raise ValueError("semantic input source scope is unsupported")
        if type(role) is not str or not role or role.strip() != role:
            raise ValueError("semantic input source role must be exact")
        if type(contract) is not SemanticContractRef:
            raise TypeError("exact semantic input source contract required")
        contract.__post_init__()
        with self._lock:
            if type(admission) is not WorkspaceOwnerDefinedSourceAdmission:
                raise TypeError("exact v3 owner-defined source admission required")
            record = self._records.get(admission)
            if record is None:
                raise RuntimeError("foreign_or_expired_source_admission")
            inspection = self.inspect(admission)
            evidence = self._issuer.inspect_selected_package_evidence(record.selected)
            observed = {body.relative_path: body for body in evidence.bodies}
            paths = (
                (inspection.manifest_relative_path,)
                if source_scope == "manifest"
                else inspection.package_authority.declared_source_paths
            )
            if any(path not in observed for path in paths):
                raise RuntimeError("v3_declared_semantic_input_source_unavailable")
            coordinates = tuple(
                SemanticInputSourceCoordinate(
                    path,
                    SemanticValueCoordinate(
                        role,
                        contract,
                        observed[path].body_ref,
                        ContentDigest(observed[path].content_digest),
                        observed[path].size_bytes,
                    ),
                )
                for path in paths
            )
            if self.inspect(admission) != inspection:
                raise RuntimeError("v3_semantic_input_source_changed")
            return coordinates

    def validate_semantic_input_source(
        self,
        source_admission: object,
        *,
        expected: SemanticInputProductionExpectation,
    ) -> None:
        """Validate Code's use through the original v3 observation runtime."""
        with self._lock:
            _ = self._read_semantic_input_sources(
                source_admission, expected=expected
            )

    def _read_semantic_input_sources(
        self,
        source_admission: object,
        *,
        expected: SemanticInputProductionExpectation,
    ) -> tuple[SemanticInputSourceBody, ...]:
        record, _ = self._semantic_input_record(source_admission, expected)
        selected = self._issuer._selected_record(record.selected)
        sources = tuple(
            SemanticInputSourceBody(
                source,
                bytes(
                    self._issuer._call(
                        "read_selected_package",
                        selected.observation,
                        relative_path=source.relative_path,
                    )
                ),
            )
            for source in expected.source_coordinates
        )
        _ = self._semantic_input_record(source_admission, expected)
        return sources

    def read_semantic_input_sources(
        self,
        source_admission: object,
        *,
        expected: SemanticInputProductionExpectation,
    ) -> tuple[SemanticInputSourceBody, ...]:
        """Return detached bytes; only Workspace retains nominal v3 handles."""
        with self._lock:
            return self._read_semantic_input_sources(
                source_admission, expected=expected
            )

    def close(self) -> None:
        with self._lock:
            self._closed = True
            self._records.clear()
