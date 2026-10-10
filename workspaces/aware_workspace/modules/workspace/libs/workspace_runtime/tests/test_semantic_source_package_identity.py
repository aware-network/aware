from __future__ import annotations

import hashlib
import json
from copy import copy
from uuid import UUID

import pytest
from aware_workspace_runtime.semantic_source_package_identity import (
    WorkspaceSemanticProviderDeltaRequestKeyPreimage,
    WorkspaceSemanticSourcePackageIdentityError,
    WorkspaceSemanticSourcePackageIngressIdentityAuthority,
    WorkspaceSemanticSourcePackageModuleMembershipAuthority,
    WorkspaceSemanticSourcePackageOriginAuthority,
    WorkspaceSemanticSourcePackageOriginMembershipAdmission,
    WorkspaceSemanticSourcePackageOriginSelectionMember,
    WorkspaceSemanticSourcePackageOriginSelectionRecord,
    WorkspaceSemanticSourcePackageProviderRequestBindingAdmission,
    WorkspaceSemanticSourcePackageRegistryProjection,
    WorkspaceSemanticSourcePackageRegistryProjectionMember,
    WorkspaceSemanticSourcePackageRegistryProjectionRef,
)

WORKSPACE_ID = str(UUID("00000000-0000-4000-8000-000000000001"))
REVISION_ID = str(UUID("00000000-0000-4000-8000-000000000002"))
DIGEST_A = "sha256:" + "a" * 64


class _ForeignStr(str):
    pass


def _projection() -> tuple[
    WorkspaceSemanticSourcePackageRegistryProjection,
    WorkspaceSemanticSourcePackageRegistryProjectionRef,
]:
    member = WorkspaceSemanticSourcePackageRegistryProjectionMember.create(
        module_id="meta",
        module_package_id="ontology",
        module_package_kind="ontology",
        manifest_relative_path="workspaces/meta/ontology/aware.toml",
        semantic_contract_role="ontology",
        semantic_contract_name="aware",
        semantic_contract_provider_key="aware_ontology",
        semantic_contract_module="aware_ontology_runtime_aware_source",
    )
    projection = WorkspaceSemanticSourcePackageRegistryProjection.create(
        workspace_id=WORKSPACE_ID,
        members=(member,),
    )
    return projection, WorkspaceSemanticSourcePackageRegistryProjectionRef.for_revision(
        projection
    )


def _values() -> tuple[
    WorkspaceSemanticSourcePackageOriginAuthority,
    WorkspaceSemanticSourcePackageModuleMembershipAuthority,
    WorkspaceSemanticSourcePackageOriginMembershipAdmission,
]:
    projection, projection_ref = _projection()
    origin = WorkspaceSemanticSourcePackageOriginAuthority.create(
        workspace_id=WORKSPACE_ID,
        module_id="meta",
        module_package_id="ontology",
        module_package_kind="ontology",
        semantic_contract_role="ontology",
    )
    membership = WorkspaceSemanticSourcePackageModuleMembershipAuthority.create(
        workspace_id=WORKSPACE_ID,
        selected_workspace_revision_id=REVISION_ID,
        registry_projection_ref=projection_ref,
        registry_projection_digest=projection.registry_projection_digest,
        module_id="meta",
        module_package_id="ontology",
        module_package_kind="ontology",
        manifest_relative_path="workspaces/meta/ontology/aware.toml",
        semantic_contract_role="ontology",
        semantic_contract_name="aware",
        semantic_contract_provider_key="aware_ontology",
        semantic_contract_module="aware_ontology_runtime_aware_source",
    )
    admission = WorkspaceSemanticSourcePackageOriginMembershipAdmission.create(
        source_package_origin_digest=origin.origin_digest,
        selected_workspace_revision_id=membership.selected_workspace_revision_id,
        registry_projection_ref=membership.registry_projection_ref,
        registry_projection_digest=membership.registry_projection_digest,
        module_package_membership_digest=membership.membership_digest,
    )
    return origin, membership, admission


def test_origin_membership_and_selection_round_trip_strictly() -> None:
    origin, membership, admission = _values()
    assert origin.canonical_bytes() == (
        b'{"codec_version":1,"module_id":"meta","module_package_id":"ontology",'
        b'"module_package_kind":"ontology","origin_digest":"sha256:'
        b'c096aaac3e70d154d03c54bc70703e9a01c6bdaaafb7c8c3ad3a1fc2472bf652",'
        b'"schema":"aware.workspace.semantic-source-package-origin-authority.v1",'
        b'"semantic_contract_role":"ontology","workspace_id":'
        b'"00000000-0000-4000-8000-000000000001"}'
    )
    member = WorkspaceSemanticSourcePackageOriginSelectionMember(
        request_position=0,
        requested_package_coordinate="module-package:meta/ontology",
        membership_authority=membership,
        origin_authority=origin,
        membership_admission=admission,
    )
    record = WorkspaceSemanticSourcePackageOriginSelectionRecord.create(
        workspace_id=WORKSPACE_ID,
        operation_id=REVISION_ID,
        operation_request_digest=DIGEST_A,
        branch_key="default",
        selection_basis="session_baseline",
        selected_workspace_revision_id=REVISION_ID,
        registry_projection_ref=membership.registry_projection_ref,
        registry_projection_digest=membership.registry_projection_digest,
        resolved_request_package_coordinates=("module-package:meta/ontology",),
        members=(member,),
    )

    assert type(record.to_wire()["members"]) is list
    assert (
        WorkspaceSemanticSourcePackageOriginSelectionRecord.from_canonical_bytes(
            record.canonical_bytes()
        ).canonical_bytes()
        == record.canonical_bytes()
    )


def test_duplicate_and_noncanonical_json_fail() -> None:
    origin, _, _ = _values()
    body = origin.canonical_bytes()
    duplicate = body[:-1] + b',"workspace_id":"' + WORKSPACE_ID.encode() + b'"}'

    with pytest.raises(WorkspaceSemanticSourcePackageIdentityError):
        WorkspaceSemanticSourcePackageOriginAuthority.from_canonical_bytes(duplicate)
    with pytest.raises(WorkspaceSemanticSourcePackageIdentityError):
        WorkspaceSemanticSourcePackageOriginAuthority.from_canonical_bytes(
            json.dumps(origin.to_wire(), indent=2).encode()
        )


def test_copy_and_coherent_mutation_fail() -> None:
    origin, _, _ = _values()
    with pytest.raises(WorkspaceSemanticSourcePackageIdentityError):
        copy(origin)

    replacement = WorkspaceSemanticSourcePackageOriginAuthority.create(
        workspace_id=origin.workspace_id,
        module_id="other",
        module_package_id=origin.module_package_id,
        module_package_kind=origin.module_package_kind,
        semantic_contract_role=origin.semantic_contract_role,
    )
    object.__setattr__(origin, "module_id", replacement.module_id)
    object.__setattr__(origin, "origin_digest", replacement.origin_digest)
    with pytest.raises(WorkspaceSemanticSourcePackageIdentityError):
        origin.canonical_bytes()


def test_bool_codec_version_and_list_tuple_substitution_fail() -> None:
    origin, membership, admission = _values()
    wire = origin.to_wire()
    wire["codec_version"] = True
    with pytest.raises((TypeError, WorkspaceSemanticSourcePackageIdentityError)):
        WorkspaceSemanticSourcePackageOriginAuthority.from_wire(wire)

    member = WorkspaceSemanticSourcePackageOriginSelectionMember(
        request_position=0,
        requested_package_coordinate="module-package:meta/ontology",
        membership_authority=membership,
        origin_authority=origin,
        membership_admission=admission,
    )
    with pytest.raises(TypeError):
        WorkspaceSemanticSourcePackageOriginSelectionRecord.create(
            workspace_id=WORKSPACE_ID,
            operation_id=REVISION_ID,
            operation_request_digest=DIGEST_A,
            branch_key="default",
            selection_basis="session_baseline",
            selected_workspace_revision_id=REVISION_ID,
            registry_projection_ref=membership.registry_projection_ref,
            registry_projection_digest=membership.registry_projection_digest,
            resolved_request_package_coordinates=["module-package:meta/ontology"],
            members=(member,),
        )


def test_generated_scalar_authority_rejects_spoofed_subclass() -> None:
    base = WorkspaceSemanticSourcePackageIngressIdentityAuthority
    spoof = type(base.__name__, (base,), {"__module__": base.__module__})
    with pytest.raises(TypeError, match="must be exact"):
        spoof.create(
            workspace_id=WORKSPACE_ID,
            materialization_operation_id=REVISION_ID,
            operation_request_digest=DIGEST_A,
            origin_selection_digest=DIGEST_A,
            request_position=0,
            requested_package_coordinate="module-package:meta/ontology",
            module_package_id="ontology",
            source_package_origin_digest=DIGEST_A,
            module_package_membership_digest=DIGEST_A,
            capture_attempt_digest=DIGEST_A,
            source_snapshot_digest=DIGEST_A,
            source_movement_digest=DIGEST_A,
            package_name="meta-ontology",
            manifest_relative_path="workspaces/meta/ontology/aware.toml",
            ingress_source_change_authority_digest=DIGEST_A,
        )


def test_registry_projection_and_reference_round_trip_strictly() -> None:
    projection, projection_ref = _projection()

    assert (
        WorkspaceSemanticSourcePackageRegistryProjection.from_canonical_bytes(
            projection.canonical_bytes()
        ).canonical_bytes()
        == projection.canonical_bytes()
    )
    assert (
        WorkspaceSemanticSourcePackageRegistryProjectionRef.from_canonical_bytes(
            projection_ref.canonical_bytes()
        ).canonical_bytes()
        == projection_ref.canonical_bytes()
    )
    assert (
        projection_ref.digest
        == "sha256:" + hashlib.sha256(projection.canonical_bytes()).hexdigest()
    )
    assert projection_ref.size_bytes == len(projection.canonical_bytes())


def _request_key_payload() -> dict[str, object]:
    return {
        "package": {
            "package_name": "meta-ontology",
            "workspace_manifest_kind": "ontology",
            "manifest_path": "workspaces/meta/ontology/aware.toml",
            "source_code_package_id": None,
            "package_authority": None,
        },
        "semantic_contract": {
            "module": "aware_ontology_runtime_aware_source",
            "provider_key": "aware_ontology",
            "role": "ontology",
            "name": "aware",
        },
        "current_delta_fingerprint": DIGEST_A,
        "baseline_oig_commit_refs": {
            "source_object_instance_graph_commit_id": None,
            "semantic_object_instance_graph_commit_id": None,
            "semantic_root_object_instance_graph_commit_id": None,
        },
        "baseline_ref": None,
        "provider_delta_lane_state": None,
        "source_change_set_digest": DIGEST_A,
        "execution_authority": {},
        "semantic_migration_authority": {},
    }


def test_provider_request_preimage_and_binding_round_trip_strictly() -> None:
    origin, membership, _ = _values()
    preimage = WorkspaceSemanticProviderDeltaRequestKeyPreimage.create(
        key_payload=_request_key_payload()
    )
    request_key = "provider_delta_request:sha256:" + preimage.key_payload_sha256[7:]
    ingress = WorkspaceSemanticSourcePackageIngressIdentityAuthority.create(
        workspace_id=WORKSPACE_ID,
        materialization_operation_id=REVISION_ID,
        operation_request_digest=DIGEST_A,
        origin_selection_digest=DIGEST_A,
        request_position=0,
        requested_package_coordinate="module-package:meta/ontology",
        module_package_id="ontology",
        source_package_origin_digest=origin.origin_digest,
        module_package_membership_digest=membership.membership_digest,
        capture_attempt_digest=DIGEST_A,
        source_snapshot_digest=DIGEST_A,
        source_movement_digest=DIGEST_A,
        package_name="meta-ontology",
        manifest_relative_path=membership.manifest_relative_path,
        ingress_source_change_authority_digest=DIGEST_A,
    )
    binding = WorkspaceSemanticSourcePackageProviderRequestBindingAdmission.create(
        materialization_operation_id=REVISION_ID,
        operation_request_digest=DIGEST_A,
        origin_selection_digest=DIGEST_A,
        request_position=0,
        requested_package_coordinate="module-package:meta/ontology",
        source_package_origin_digest=origin.origin_digest,
        module_package_membership_digest=membership.membership_digest,
        ingress_identity_digest=ingress.ingress_identity_digest,
        semantic_contract_role=membership.semantic_contract_role,
        semantic_contract_name=membership.semantic_contract_name,
        semantic_contract_provider_key=membership.semantic_contract_provider_key,
        semantic_contract_module=membership.semantic_contract_module,
        package_name="meta-ontology",
        provider_delta_request_key=request_key,
        provider_request_key_preimage_digest=preimage.preimage_digest,
        provider_delta_operation_id="provider-operation-1",
        provider_delta_operation_authority_digest=DIGEST_A,
        selected_workspace_revision_id=membership.selected_workspace_revision_id,
        registry_projection_body_sha256=membership.registry_projection_ref.digest,
        registry_projection_digest=membership.registry_projection_digest,
    )

    assert (
        WorkspaceSemanticProviderDeltaRequestKeyPreimage.from_canonical_bytes(
            preimage.canonical_bytes()
        ).canonical_bytes()
        == preimage.canonical_bytes()
    )
    assert (
        WorkspaceSemanticSourcePackageProviderRequestBindingAdmission.from_canonical_bytes(
            binding.canonical_bytes()
        ).canonical_bytes()
        == binding.canonical_bytes()
    )


def test_request_preimage_detaches_input_and_returned_wire() -> None:
    payload = _request_key_payload()
    preimage = WorkspaceSemanticProviderDeltaRequestKeyPreimage.create(
        key_payload=payload
    )
    canonical = preimage.canonical_bytes()
    package = payload["package"]
    assert type(package) is dict
    package["package_name"] = "mutated-input"
    assert preimage.canonical_bytes() == canonical

    wire = preimage.to_wire()
    wire_payload = wire["key_payload"]
    assert type(wire_payload) is dict
    wire_package = wire_payload["package"]
    assert type(wire_package) is dict
    wire_package["package_name"] = "mutated-wire"
    assert preimage.canonical_bytes() == canonical


def test_identity_wire_rejects_exact_string_subclasses() -> None:
    origin, _, _ = _values()
    wire = origin.to_wire()
    wire["schema"] = _ForeignStr(origin.schema)
    with pytest.raises(TypeError):
        WorkspaceSemanticSourcePackageOriginAuthority.from_wire(wire)
    with pytest.raises(TypeError):
        WorkspaceSemanticSourcePackageOriginAuthority(
            workspace_id=origin.workspace_id,
            module_id=origin.module_id,
            module_package_id=origin.module_package_id,
            module_package_kind=origin.module_package_kind,
            semantic_contract_role=origin.semantic_contract_role,
            origin_digest=origin.origin_digest,
            schema=_ForeignStr(origin.schema),
        )


def test_projection_and_request_binding_coherent_restamping_fail() -> None:
    projection, projection_ref = _projection()
    replacement_member = WorkspaceSemanticSourcePackageRegistryProjectionMember.create(
        module_id="meta",
        module_package_id="other",
        module_package_kind="ontology",
        manifest_relative_path="workspaces/meta/other/aware.toml",
        semantic_contract_role="ontology",
        semantic_contract_name="aware",
        semantic_contract_provider_key="aware_ontology",
        semantic_contract_module="aware_ontology_runtime_aware_source",
    )
    replacement = WorkspaceSemanticSourcePackageRegistryProjection.create(
        workspace_id=WORKSPACE_ID,
        members=(replacement_member,),
    )
    object.__setattr__(projection, "members", replacement.members)
    object.__setattr__(
        projection, "registry_projection_digest", replacement.registry_projection_digest
    )
    with pytest.raises(WorkspaceSemanticSourcePackageIdentityError):
        projection.canonical_bytes()

    object.__setattr__(projection_ref, "digest", "sha256:" + "b" * 64)
    object.__setattr__(
        projection_ref,
        "ref",
        "cas://workspace-semantic-source-package-registry-projection/"
        + "b" * 64
        + ".json",
    )
    with pytest.raises(WorkspaceSemanticSourcePackageIdentityError):
        projection_ref.canonical_bytes()
