"""Mechanical catalog-entry input from a live Workspace source admission."""

from __future__ import annotations

import os
from threading import RLock
from typing import TYPE_CHECKING
from weakref import WeakKeyDictionary

from aware_code_semantic_contract_runtime import ContentDigest, canonical_json_bytes
from aware_code_semantic_contract_runtime.dependency_inputs import (
    SemanticDependencyPlanningInput,
)

if TYPE_CHECKING:
    from aware_code_retained_registry_policy_runtime.selected_catalog_eligibility import (
        SelectedProductCatalogEligibility,
    )

from .materialization_membership_catalog import (
    WorkspaceSemanticAuthoredDependency,
    WorkspaceSemanticMaterializationPackageEntry,
)
from .materialization_selection import (
    WorkspaceSemanticMaterializationParticipationPolicy,
)
from .source_admission import (
    WorkspaceOwnerDefinedSourceAdmission,
    WorkspaceOwnerDefinedSourceAdmissionRuntime,
    WorkspaceV3OwnerDefinedSourceAdmissionRuntime,
)


def derive_owner_defined_catalog_entry(
    runtime: (
        WorkspaceOwnerDefinedSourceAdmissionRuntime
        | WorkspaceV3OwnerDefinedSourceAdmissionRuntime
    ),
    admission: WorkspaceOwnerDefinedSourceAdmission,
    *,
    product_eligibilities: tuple[SelectedProductCatalogEligibility, ...] = (),
) -> WorkspaceSemanticMaterializationPackageEntry:
    """Derive an entry input; the existing catalog host remains sole issuer."""
    if type(runtime) not in (
        WorkspaceOwnerDefinedSourceAdmissionRuntime,
        WorkspaceV3OwnerDefinedSourceAdmissionRuntime,
    ):
        raise TypeError("exact Workspace source-admission runtime required")
    if type(admission) is not WorkspaceOwnerDefinedSourceAdmission:
        raise TypeError("exact Workspace source admission required")
    return _entry_from_inspection(runtime.inspect(admission), product_eligibilities)


def _entry_from_inspection(value, product_eligibilities):
    views = _product_eligibility_views(value, product_eligibilities)
    authority = value.package_authority
    if value.configured:
        # The occurrence carries Code config identity, while this catalog policy
        # requires a full semantic configuration coordinate.  Do not infer one.
        raise RuntimeError("configured semantic catalog coordinate unavailable")
    dependencies = tuple(
        WorkspaceSemanticAuthoredDependency.create(
            dependency_kind=entry.dependency_kind,
            dependency_ref=entry.dependency_ref,
            admitted_target_package_refs=tuple(
                target.package.package_ref for target in entry.targets
            ),
            allowed_target_constraints=entry.target_constraints,
        )
        for entry in value.declaration_inventory.entries
    )
    policy_payload = {
        "package_ref": value.package.package_ref,
        "profile_ref": value.profile_ref,
        "source_identity_digest": value.source_identity_digest.to_wire(),
    }
    if views:
        policy_payload["product_eligibilities"] = [
            {
                "profile_ref": view.profile_ref,
                "semantic_provider_key": view.semantic_provider_key,
                "terminal_roles": list(view.terminal_roles),
            }
            for view in views
        ]
    policy_ref = "workspace-source-policy:" + ContentDigest.of_bytes(
        canonical_json_bytes(policy_payload)
    ).value
    policy = WorkspaceSemanticMaterializationParticipationPolicy.create(
        policy_ref=policy_ref,
        policy_revision=2 if views else 1,
        package_ref=value.package.package_ref,
        allowed_operation_kinds=value.operation_kinds,
        allowed_semantic_root_refs=authority.owned_semantic_root_refs,
        allowed_terminal_output_roles=tuple(sorted(
            set(value.terminal_roles).union(
                *(view.terminal_roles for view in views)
            ), key=str.encode,
        )),
        allow_unconfigured=True,
        allowed_semantic_configuration_coordinates=(),
    )
    return WorkspaceSemanticMaterializationPackageEntry.create(
        repository_ref=value.repository_ref,
        workspace_ref=value.workspace_ref,
        module_ref=value.module_ref,
        package=value.package,
        package_family=authority.semantic_package.family,
        package_role=authority.semantic_contract.role,
        manifest_contract=value.manifest_contract,
        manifest_relative_path=value.manifest_relative_path,
        source_authority_ref=value.authority_result_coordinate.value_ref,
        source_authority_digest=value.authority_result_coordinate.digest,
        owned_semantic_root_refs=authority.owned_semantic_root_refs,
        authored_dependencies=dependencies,
        participation_policy=policy,
        allowed_profile_refs=tuple(sorted(
            {value.profile_ref, *(view.profile_ref for view in views)},
            key=str.encode,
        )),
    )


def _product_eligibility_views(value, handles):
    if type(handles) is not tuple:
        raise TypeError("original product eligibility tuple required")
    if not handles:
        return ()
    from aware_code_retained_registry_policy_runtime.selected_catalog_eligibility import (
        SelectedProductCatalogEligibility,
        read_selected_product_catalog_eligibility,
    )

    views = []
    for handle in handles:
        if type(handle) is not SelectedProductCatalogEligibility:
            raise TypeError("original Code product eligibility required")
        view = read_selected_product_catalog_eligibility(handle)
        if (
            view.scope_key != value.workspace_ref
            or view.module_id != value.module_ref
            or view.package_id != value.package_id
            or view.source_identity_digest != value.source_identity_digest
        ):
            raise RuntimeError("Code product eligibility differs from Workspace source")
        views.append(view)
    keys = tuple((view.profile_ref, view.semantic_provider_key) for view in views)
    if keys != tuple(sorted(set(keys), key=lambda item: (item[0].encode(), item[1].encode()))):
        raise RuntimeError("product eligibility profiles must be unique and ordered")
    return tuple(views)


class WorkspaceV3GraphSourceCorrespondence:
    """Original v3 candidate-to-published-entry comparison, not authority."""

    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("Workspace issues graph source correspondences")

    def __reduce__(self):
        raise TypeError("graph source correspondences cannot be serialized")

    def original_selected_source(self):
        return _graph_source_state(self)[2].selected

    def original_semantic_input_source(
        self, entry: WorkspaceSemanticMaterializationPackageEntry
    ) -> tuple[
        WorkspaceV3OwnerDefinedSourceAdmissionRuntime,
        WorkspaceOwnerDefinedSourceAdmission,
    ]:
        """Return the original Code-facing source methods and nominal handle.

        This is a retained-resource handoff, not a fresh source admission.
        The caller must keep the graph node's original use alive while Code
        executes its semantic input producer.
        """

        self.validate_catalog_entry(entry)
        runtime, admission, *_ = _graph_source_state(self)
        if (
            type(runtime) is not WorkspaceV3OwnerDefinedSourceAdmissionRuntime
            or type(admission) is not WorkspaceOwnerDefinedSourceAdmission
        ):
            raise RuntimeError("original graph semantic source unavailable")
        return runtime, admission

    def package(self):
        return _graph_source_state(self)[3].package

    def validate_catalog_entry(self, entry) -> None:
        runtime, admission, record, inspection, original, pid, handles = (
            _graph_source_state(self)
        )
        if type(entry) is not WorkspaceSemanticMaterializationPackageEntry:
            raise TypeError("exact Workspace catalog entry required")
        if (
            pid != os.getpid()
            or runtime._pid != pid
            or runtime._closed
            or runtime._records.get(admission) is not record
            or entry != original
        ):
            raise RuntimeError("original graph catalog entry changed")
        current = runtime.inspect(admission)
        if current != inspection or _entry_from_inspection(current, handles) != original:
            raise RuntimeError("original graph catalog entry changed")

    def check_catalog_entry_locked(self, entry, guard) -> None:
        runtime, admission, record, _inspection, original, pid, handles = (
            _graph_source_state(self)
        )
        if (
            type(entry) is not WorkspaceSemanticMaterializationPackageEntry
            or entry != original
            or pid != os.getpid()
            or runtime._pid != pid
            or runtime._closed
            or runtime._records.get(admission) is not record
        ):
            raise RuntimeError("original graph catalog entry retired")
        if handles:
            from aware_code_retained_registry_policy_runtime.selected_catalog_eligibility import (
                check_selected_product_catalog_eligibility_locked,
            )

            for handle in handles:
                check_selected_product_catalog_eligibility_locked(
                    handle, guard=guard
                )

    def validate(self, entry, planning_input) -> None:
        runtime, admission, record, inspection, original_entry, pid, _handles = (
            _graph_source_state(self)
        )
        with runtime._lock:
            if (
                pid != os.getpid()
                or runtime._pid != pid
                or runtime._closed
                or runtime._records.get(admission) is not record
            ):
                raise RuntimeError("graph_source_correspondence_expired")
        if type(entry) is not WorkspaceSemanticMaterializationPackageEntry:
            raise TypeError("exact Workspace graph entry required")
        if type(planning_input) is not SemanticDependencyPlanningInput:
            raise TypeError("exact owner planning input required")
        entry.__post_init__()
        planning_input.__post_init__()
        issuer = runtime._issuer
        context, inventory = issuer.inspect_inputs(record.selected)
        if (
            context.package != inspection.package
            or context.source_identity_digest != inspection.source_identity_digest
            or inventory != inspection.declaration_inventory
            or entry != original_entry
            or entry.entry_digest != original_entry.entry_digest
            or entry.source_authority_ref
            != inspection.authority_result_coordinate.value_ref
            or entry.source_authority_digest
            != inspection.authority_result_coordinate.digest
            or planning_input.package != inspection.package
            or planning_input.source_identity_digest
            != inspection.source_identity_digest
        ):
            raise RuntimeError("graph_source_correspondence_changed")
        with runtime._lock:
            if (
                runtime._records.get(admission) is not record
                or runtime._closed
                or runtime._pid != pid
                or os.getpid() != pid
            ):
                raise RuntimeError("graph_source_correspondence_expired")


_GRAPH_SOURCE_CORRESPONDENCES = WeakKeyDictionary()
_GRAPH_SOURCE_LOCK = RLock()


def _graph_source_state(value):
    if type(value) is not WorkspaceV3GraphSourceCorrespondence:
        raise TypeError("original v3 graph source correspondence required")
    with _GRAPH_SOURCE_LOCK:
        state = _GRAPH_SOURCE_CORRESPONDENCES.get(value)
    if state is None:
        raise RuntimeError("foreign_graph_source_correspondence")
    return state


def capture_v3_graph_source_correspondence(
    runtime: WorkspaceV3OwnerDefinedSourceAdmissionRuntime,
    admission: WorkspaceOwnerDefinedSourceAdmission,
    entry: WorkspaceSemanticMaterializationPackageEntry,
    *,
    product_eligibilities: tuple[SelectedProductCatalogEligibility, ...] = (),
) -> WorkspaceV3GraphSourceCorrespondence:
    """Capture both source-identity domains before completion transfer."""
    if (
        type(runtime) is not WorkspaceV3OwnerDefinedSourceAdmissionRuntime
        or type(admission) is not WorkspaceOwnerDefinedSourceAdmission
        or type(entry) is not WorkspaceSemanticMaterializationPackageEntry
    ):
        raise TypeError("exact original v3 source and entry required")
    inspection = runtime.inspect(admission)
    if _entry_from_inspection(inspection, product_eligibilities) != entry:
        raise RuntimeError("graph_source_entry_differs_from_original_admission")
    with runtime._lock:
        record = runtime._records.get(admission)
        if record is None or runtime._closed or record.inspection != inspection:
            raise RuntimeError("graph_source_admission_unavailable")
        result = object.__new__(WorkspaceV3GraphSourceCorrespondence)
        with _GRAPH_SOURCE_LOCK:
            _GRAPH_SOURCE_CORRESPONDENCES[result] = (
                runtime, admission, record, inspection, entry, os.getpid(),
                product_eligibilities,
            )
        return result
