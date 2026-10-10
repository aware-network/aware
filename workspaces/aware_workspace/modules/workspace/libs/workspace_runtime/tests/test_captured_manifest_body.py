from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from uuid import UUID

import pytest
from aware_workspace_runtime.captured_manifest_body import (
    WorkspaceCapturedBodyRetentionStoreAuthority,
    WorkspaceCapturedManifestBodyAdmission,
    WorkspaceCapturedManifestBodyWriteEvidence,
    WorkspaceOperationCapturedManifestBodyRetentionAdmission,
    WorkspaceOperationManifestRetentionBindingAdmission,
    WorkspaceOperationManifestRetentionBindingCatalog,
    WorkspaceOperationManifestRetentionBindingCatalogRef,
    WorkspaceSemanticPackageBodyRef,
)
from aware_workspace_runtime.semantic_source_package_identity import (
    WorkspaceSemanticSourcePackageIdentityError,
    WorkspaceSemanticSourcePackageOriginAuthority,
    WorkspaceSemanticSourcePackageRegistryProjection,
    WorkspaceSemanticSourcePackageRegistryProjectionMember,
    WorkspaceSemanticSourcePackageRegistryProjectionRef,
)

WORKSPACE_ID = str(UUID("00000000-0000-4000-8000-000000000001"))
GENERATION_ID = str(UUID("00000000-0000-4000-8000-000000000002"))
OPERATION_ID = str(UUID("00000000-0000-4000-8000-000000000003"))
RESULT_REVISION_ID = str(UUID("00000000-0000-4000-8000-000000000004"))
RESULT_COMMIT_ID = str(UUID("00000000-0000-4000-8000-000000000005"))
RESULT_HEAD_COMMIT_ID = str(UUID("00000000-0000-4000-8000-000000000006"))


def _digest(character: str) -> str:
    return "sha256:" + character * 64


def _domain_digest(domain: str, body: dict[str, object]) -> str:
    canonical = json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    return "sha256:" + hashlib.sha256(domain.encode() + b"\0" + canonical).hexdigest()


class _ForeignStr(str):
    pass


def _closure() -> tuple[
    WorkspaceSemanticPackageBodyRef,
    WorkspaceCapturedManifestBodyWriteEvidence,
    WorkspaceOperationCapturedManifestBodyRetentionAdmission,
]:
    body_ref = WorkspaceSemanticPackageBodyRef.create(b"[package]\nname='demo'\n")
    store = WorkspaceCapturedBodyRetentionStoreAuthority.create(
        workspace_id=WORKSPACE_ID,
        storage_generation_id=GENERATION_ID,
    )
    evidence = WorkspaceCapturedManifestBodyWriteEvidence.create(
        store_authority_digest=store.store_authority_digest,
        source_package_origin_digest=_digest("a"),
        origin_membership_admission_digest=_digest("b"),
        capture_attempt_digest=_digest("c"),
        source_snapshot_digest=_digest("d"),
        source_movement_digest=_digest("e"),
        manifest_source_body_ref=body_ref,
    )
    retention = WorkspaceOperationCapturedManifestBodyRetentionAdmission.create(
        write_evidence=evidence,
        manifest_relative_path="modules/demo/aware.toml",
        manifest_kind="aware",
    )
    return body_ref, evidence, retention


def _captured_admission(**overrides: object) -> WorkspaceCapturedManifestBodyAdmission:
    body_ref, _, retention = _closure()
    origin = WorkspaceSemanticSourcePackageOriginAuthority.create(
        workspace_id=WORKSPACE_ID,
        module_id="demo",
        module_package_id="ontology",
        module_package_kind="ontology",
        semantic_contract_role="ontology",
    )
    projection = WorkspaceSemanticSourcePackageRegistryProjection.create(
        workspace_id=WORKSPACE_ID,
        members=(
            WorkspaceSemanticSourcePackageRegistryProjectionMember.create(
                module_id="demo",
                module_package_id="ontology",
                module_package_kind="ontology",
                manifest_relative_path="modules/demo/aware.toml",
                semantic_contract_role="ontology",
                semantic_contract_name="aware",
                semantic_contract_provider_key="aware_ontology",
                semantic_contract_module="aware_ontology_runtime_aware_source",
            ),
        ),
    )
    projection_ref = WorkspaceSemanticSourcePackageRegistryProjectionRef.for_revision(
        projection
    )
    binding = WorkspaceOperationManifestRetentionBindingAdmission.create(
        operation_authority_digest=_digest("1"),
        operation_id=OPERATION_ID,
        operation_request_digest=_digest("2"),
        capture_attempt_digest=retention.capture_attempt_digest,
        source_package_origin_digest=origin.origin_digest,
        source_package_origin_admission_digest=_digest("3"),
        retention_admission_digest=retention.retention_admission_digest,
        manifest_relative_path=retention.manifest_relative_path,
        manifest_kind=retention.manifest_kind,
        manifest_source_body_ref=body_ref,
    )
    catalog = WorkspaceOperationManifestRetentionBindingCatalog.create(
        bindings=(binding,)
    )
    catalog_ref = WorkspaceOperationManifestRetentionBindingCatalogRef.create(catalog)
    values: dict[str, object] = {
        "operation_authority_digest": _digest("1"),
        "request_precondition_workspace_revision_id": OPERATION_ID,
        "registry_projection_ref": projection_ref,
        "registry_projection_digest": projection.registry_projection_digest,
        "result_workspace_revision_id": RESULT_REVISION_ID,
        "result_workspace_revision_persistence_status": "persisted",
        "result_workspace_revision_commit_id": RESULT_COMMIT_ID,
        "result_workspace_revision_head_commit_id": RESULT_HEAD_COMMIT_ID,
        "manifest_retention_binding_catalog_ref": catalog_ref,
        "manifest_retention_binding_catalog_digest": catalog.catalog_digest,
        "source_package_origin": origin,
        "source_package_origin_admission_digest": _digest("3"),
        "manifest_relative_path": retention.manifest_relative_path,
        "manifest_kind": retention.manifest_kind,
        "source_snapshot_digest": _digest("4"),
        "source_movement_digest": _digest("5"),
        "retention_admission_digest": retention.retention_admission_digest,
        "manifest_source_body_ref": body_ref,
    }
    values.update(overrides)
    return WorkspaceCapturedManifestBodyAdmission.create(**values)


def test_manifest_body_ref_and_retention_round_trip() -> None:
    body_ref, evidence, retention = _closure()
    assert body_ref.canonical_bytes() == (
        b'{"body_schema":"aware.workspace.semantic-package-manifest-source.v1",'
        b'"codec_version":1,"digest":"sha256:'
        b'587ada7790c9fa87e288d69e5a8a5ee10dcab222885f5b045ae640f1a53aa9b9",'
        b'"media_type":"application/toml;charset=utf-8","ref":'
        b'"cas://workspace-semantic-package/'
        b'587ada7790c9fa87e288d69e5a8a5ee10dcab222885f5b045ae640f1a53aa9b9.body",'
        b'"role":"manifest_source","schema":'
        b'"aware.workspace.semantic-package-body-ref.v1","size_bytes":22}'
    )
    assert (
        WorkspaceSemanticPackageBodyRef.from_canonical_bytes(
            body_ref.canonical_bytes()
        ).canonical_bytes()
        == body_ref.canonical_bytes()
    )
    assert (
        WorkspaceCapturedManifestBodyWriteEvidence.from_canonical_bytes(
            evidence.canonical_bytes()
        ).canonical_bytes()
        == evidence.canonical_bytes()
    )
    assert (
        WorkspaceOperationCapturedManifestBodyRetentionAdmission.from_canonical_bytes(
            retention.canonical_bytes()
        ).canonical_bytes()
        == retention.canonical_bytes()
    )


def test_binding_catalog_has_distinct_semantic_and_body_digests() -> None:
    body_ref, _, retention = _closure()
    binding = WorkspaceOperationManifestRetentionBindingAdmission.create(
        operation_authority_digest=_digest("1"),
        operation_id=OPERATION_ID,
        operation_request_digest=_digest("2"),
        capture_attempt_digest=retention.capture_attempt_digest,
        source_package_origin_digest=retention.source_package_origin_digest,
        source_package_origin_admission_digest=_digest("3"),
        retention_admission_digest=retention.retention_admission_digest,
        manifest_relative_path=retention.manifest_relative_path,
        manifest_kind=retention.manifest_kind,
        manifest_source_body_ref=body_ref,
    )
    catalog = WorkspaceOperationManifestRetentionBindingCatalog.create(
        bindings=(binding,)
    )
    reference = WorkspaceOperationManifestRetentionBindingCatalogRef.create(catalog)

    assert catalog.catalog_digest != reference.body_sha256
    assert reference.ref.endswith(reference.body_sha256[7:] + ".json")
    assert (
        WorkspaceOperationManifestRetentionBindingCatalog.from_canonical_bytes(
            catalog.canonical_bytes()
        ).canonical_bytes()
        == catalog.canonical_bytes()
    )


def test_reference_and_nested_coherent_restamping_fail() -> None:
    body_ref, evidence, _ = _closure()
    other = WorkspaceSemanticPackageBodyRef.create(b"other")
    object.__setattr__(body_ref, "digest", other.digest)
    object.__setattr__(body_ref, "ref", other.ref)
    object.__setattr__(body_ref, "size_bytes", other.size_bytes)
    with pytest.raises(WorkspaceSemanticSourcePackageIdentityError):
        body_ref.canonical_bytes()
    with pytest.raises(WorkspaceSemanticSourcePackageIdentityError):
        evidence.canonical_bytes()


def test_bool_size_and_list_catalog_fail() -> None:
    body_ref, _, retention = _closure()
    wire = body_ref.to_wire()
    wire["size_bytes"] = True
    with pytest.raises((TypeError, WorkspaceSemanticSourcePackageIdentityError)):
        WorkspaceSemanticPackageBodyRef.from_wire(wire)

    binding = WorkspaceOperationManifestRetentionBindingAdmission.create(
        operation_authority_digest=_digest("1"),
        operation_id=OPERATION_ID,
        operation_request_digest=_digest("2"),
        capture_attempt_digest=retention.capture_attempt_digest,
        source_package_origin_digest=retention.source_package_origin_digest,
        source_package_origin_admission_digest=_digest("3"),
        retention_admission_digest=retention.retention_admission_digest,
        manifest_relative_path=retention.manifest_relative_path,
        manifest_kind=retention.manifest_kind,
        manifest_source_body_ref=body_ref,
    )
    with pytest.raises(TypeError):
        WorkspaceOperationManifestRetentionBindingCatalog(
            bindings=[binding],  # pyright: ignore[reportArgumentType]
            catalog_digest=_digest("4"),
        )


def test_captured_wire_rejects_exact_string_subclasses() -> None:
    body_ref, _, _ = _closure()
    wire = body_ref.to_wire()
    wire["role"] = _ForeignStr("manifest_source")
    with pytest.raises(TypeError):
        WorkspaceSemanticPackageBodyRef.from_wire(wire)
    with pytest.raises(TypeError):
        WorkspaceSemanticPackageBodyRef(
            ref=body_ref.ref,
            digest=body_ref.digest,
            size_bytes=body_ref.size_bytes,
            role=_ForeignStr("manifest_source"),
        )


def test_retention_binding_requires_canonical_operation_uuid() -> None:
    body_ref, _, retention = _closure()
    values = {
        "operation_authority_digest": _digest("1"),
        "operation_id": "not-a-uuid",
        "operation_request_digest": _digest("2"),
        "capture_attempt_digest": retention.capture_attempt_digest,
        "source_package_origin_digest": retention.source_package_origin_digest,
        "source_package_origin_admission_digest": _digest("3"),
        "retention_admission_digest": retention.retention_admission_digest,
        "manifest_relative_path": retention.manifest_relative_path,
        "manifest_kind": retention.manifest_kind,
        "manifest_source_body_ref": body_ref,
    }
    with pytest.raises(WorkspaceSemanticSourcePackageIdentityError):
        WorkspaceOperationManifestRetentionBindingAdmission.create(**values)

    valid = WorkspaceOperationManifestRetentionBindingAdmission.create(
        **{**values, "operation_id": OPERATION_ID}
    )
    wire = valid.to_wire()
    wire["operation_id"] = "not-a-uuid"
    digest_body = {
        key: value for key, value in wire.items() if key != "binding_admission_digest"
    }
    wire["binding_admission_digest"] = _domain_digest(valid.schema, digest_body)
    encoded = json.dumps(
        wire, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    with pytest.raises(WorkspaceSemanticSourcePackageIdentityError):
        WorkspaceOperationManifestRetentionBindingAdmission.from_canonical_bytes(
            encoded
        )


def test_dataclass_replace_creates_new_lawful_value_but_does_not_repair_old() -> None:
    body_ref, _, _ = _closure()
    same = replace(body_ref)
    assert same.canonical_bytes() == body_ref.canonical_bytes()


@pytest.mark.parametrize("result_commit_id", [RESULT_COMMIT_ID, None])
def test_captured_admission_round_trips_for_fresh_and_reused_revision(
    result_commit_id: str | None,
) -> None:
    admission = _captured_admission(
        result_workspace_revision_commit_id=result_commit_id
    )
    decoded = WorkspaceCapturedManifestBodyAdmission.from_canonical_bytes(
        admission.canonical_bytes()
    )

    assert decoded.canonical_bytes() == admission.canonical_bytes()
    assert decoded.result_workspace_revision_commit_id == result_commit_id
    assert decoded.result_workspace_revision_persistence_status == "persisted"


def test_captured_admission_rejects_retired_revision_coordinates() -> None:
    wire = _captured_admission().to_wire()
    wire["request_precondition_workspace_revision_ref"] = (
        "cas://workspace-revision/retired.json"
    )
    with pytest.raises(WorkspaceSemanticSourcePackageIdentityError):
        WorkspaceCapturedManifestBodyAdmission.from_wire(wire)
    with pytest.raises(WorkspaceSemanticSourcePackageIdentityError):
        WorkspaceCapturedManifestBodyAdmission.from_canonical_bytes(
            json.dumps(wire, sort_keys=True, separators=(",", ":")).encode()
        )


def test_captured_admission_rejects_duplicate_and_noncanonical_json() -> None:
    admission = _captured_admission()
    body = admission.canonical_bytes()
    duplicate = body[:-1] + b',"disposition":"admitted"}'

    with pytest.raises(WorkspaceSemanticSourcePackageIdentityError):
        WorkspaceCapturedManifestBodyAdmission.from_canonical_bytes(duplicate)
    with pytest.raises(WorkspaceSemanticSourcePackageIdentityError):
        WorkspaceCapturedManifestBodyAdmission.from_canonical_bytes(
            json.dumps(admission.to_wire(), indent=2).encode()
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        (
            "request_precondition_workspace_revision_id",
            "AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA",
        ),
        ("result_workspace_revision_id", True),
        ("result_workspace_revision_persistence_status", "pending"),
        (
            "result_workspace_revision_commit_id",
            "BBBBBBBB-BBBB-4BBB-8BBB-BBBBBBBBBBBB",
        ),
        ("result_workspace_revision_head_commit_id", None),
    ],
)
def test_captured_admission_rejects_invalid_revision_evidence(
    field: str, value: object
) -> None:
    with pytest.raises((TypeError, WorkspaceSemanticSourcePackageIdentityError)):
        _captured_admission(**{field: value})


def test_captured_admission_coherent_revision_restamping_fails() -> None:
    admission = _captured_admission()
    replacement = _captured_admission(result_workspace_revision_commit_id=None)
    object.__setattr__(admission, "result_workspace_revision_commit_id", None)
    object.__setattr__(
        admission, "capture_admission_digest", replacement.capture_admission_digest
    )

    with pytest.raises(WorkspaceSemanticSourcePackageIdentityError):
        admission.canonical_bytes()
