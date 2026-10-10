"""Neutral retained-manifest references and portable admission evidence.

The values here contain no host path, ORM value, storage handle, parser, or
process identity.  Contextual Workspace adapters own persistence and
capability issuance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self, cast

from .semantic_source_package_identity import (
    CODEC_VERSION,
    WorkspaceSemanticSourcePackageIdentityError,
    WorkspaceSemanticSourcePackageOriginAuthority,
    WorkspaceSemanticSourcePackageRegistryProjectionRef,
    _decode_canonical,
    _dict,
    _digest,
    _digest_value,
    _exact,
    _finish,
    _keys,
    _list,
    _non_negative,
    _plain_sha,
    _Portable,
    _relative_path,
    _token,
    _uuid,
)

SEMANTIC_PACKAGE_BODY_REF_SCHEMA = "aware.workspace.semantic-package-body-ref.v1"
SEMANTIC_PACKAGE_MANIFEST_SOURCE_SCHEMA = (
    "aware.workspace.semantic-package-manifest-source.v1"
)
CAPTURED_BODY_STORE_AUTHORITY_SCHEMA = (
    "aware.workspace.captured-body-retention-store-authority.v1"
)
CAPTURED_MANIFEST_WRITE_EVIDENCE_SCHEMA = (
    "aware.workspace.captured-manifest-body-write-evidence.v1"
)
CAPTURED_MANIFEST_WRITE_ATTEMPT_DOMAIN = (
    "aware.workspace.captured-manifest-body-write-attempt.v1"
)
CAPTURED_MANIFEST_RETENTION_ADMISSION_SCHEMA = (
    "aware.workspace.operation-captured-manifest-body-retention-admission.v1"
)
MANIFEST_RETENTION_BINDING_ADMISSION_SCHEMA = (
    "aware.workspace.operation-manifest-retention-binding-admission.v1"
)
MANIFEST_RETENTION_BINDING_CATALOG_SCHEMA = (
    "aware.workspace.operation-manifest-retention-binding-catalog.v1"
)
MANIFEST_RETENTION_BINDING_CATALOG_REF_SCHEMA = (
    "aware.workspace.operation-manifest-retention-binding-catalog-ref.v1"
)
CAPTURED_MANIFEST_BODY_ADMISSION_SCHEMA = (
    "aware.workspace.captured-manifest-body-admission.v1"
)
MANIFEST_BODY_MEDIA_TYPE = "application/toml;charset=utf-8"
CATALOG_MEDIA_TYPE = "application/json"


Error = WorkspaceSemanticSourcePackageIdentityError


def _manifest_path(value: object, field: str) -> str:
    result = _relative_path(value, field)
    if not result.endswith(".toml"):
        raise Error(f"{field} must identify a .toml manifest")
    return result


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceSemanticPackageBodyRef(_Portable):
    ref: str
    digest: str
    size_bytes: int
    schema: str = SEMANTIC_PACKAGE_BODY_REF_SCHEMA
    codec_version: int = CODEC_VERSION
    role: str = "manifest_source"
    body_schema: str = SEMANTIC_PACKAGE_MANIFEST_SOURCE_SCHEMA
    media_type: str = MANIFEST_BODY_MEDIA_TYPE

    def __post_init__(self) -> None:
        if type(self) is not WorkspaceSemanticPackageBodyRef:
            raise TypeError("manifest body ref must be exact")
        digest = _digest_value(self.digest, "digest")
        _non_negative(self.size_bytes, "size_bytes")
        expected_ref = f"cas://workspace-semantic-package/{digest[7:]}.body"
        if self.ref != expected_ref:
            raise Error("manifest body ref suffix mismatched digest")
        if (
            self.schema != SEMANTIC_PACKAGE_BODY_REF_SCHEMA
            or type(self.codec_version) is not int
            or self.codec_version != 1
            or self.role != "manifest_source"
            or self.body_schema != SEMANTIC_PACKAGE_MANIFEST_SOURCE_SCHEMA
            or self.media_type != MANIFEST_BODY_MEDIA_TYPE
        ):
            raise Error("manifest body reference constants are unsupported")
        _finish(self)

    def _wire_unchecked(self) -> dict[str, object]:
        return {
            "body_schema": self.body_schema,
            "codec_version": self.codec_version,
            "digest": self.digest,
            "media_type": self.media_type,
            "ref": self.ref,
            "role": self.role,
            "schema": self.schema,
            "size_bytes": self.size_bytes,
        }

    @classmethod
    def create(cls, body: object) -> Self:
        exact = _exact(body, bytes, "manifest bytes")
        digest = _plain_sha(exact)
        return cls(
            ref=f"cas://workspace-semantic-package/{digest[7:]}.body",
            digest=digest,
            size_bytes=len(exact),
        )

    @classmethod
    def from_wire(cls, value: object) -> Self:
        body = _dict(value, "manifest body ref")
        _keys(
            body,
            frozenset(
                {
                    "schema",
                    "codec_version",
                    "role",
                    "body_schema",
                    "media_type",
                    "ref",
                    "digest",
                    "size_bytes",
                }
            ),
            "manifest body ref",
        )
        return cls(**body)  # pyright: ignore[reportArgumentType]

    @classmethod
    def from_canonical_bytes(cls, value: object) -> Self:
        return cls.from_wire(_decode_canonical(value))


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceCapturedBodyRetentionStoreAuthority(_Portable):
    workspace_id: str
    storage_generation_id: str
    store_authority_digest: str
    schema: str = CAPTURED_BODY_STORE_AUTHORITY_SCHEMA
    codec_version: int = CODEC_VERSION
    storage_contract: str = "immutable-content-addressed-body-v1"

    def __post_init__(self) -> None:
        if type(self) is not WorkspaceCapturedBodyRetentionStoreAuthority:
            raise TypeError("retention store authority must be exact")
        _uuid(self.workspace_id, "workspace_id")
        _uuid(self.storage_generation_id, "storage_generation_id")
        if (
            self.schema != CAPTURED_BODY_STORE_AUTHORITY_SCHEMA
            or type(self.codec_version) is not int
            or self.codec_version != 1
            or self.storage_contract != "immutable-content-addressed-body-v1"
        ):
            raise Error("retention store constants are unsupported")
        if self.store_authority_digest != _digest(self.schema, self._body()):
            raise Error("retention store authority digest mismatched")
        _finish(self)

    def _body(self) -> dict[str, object]:
        return {
            "codec_version": self.codec_version,
            "schema": self.schema,
            "storage_contract": self.storage_contract,
            "storage_generation_id": self.storage_generation_id,
            "workspace_id": self.workspace_id,
        }

    def _wire_unchecked(self) -> dict[str, object]:
        return {**self._body(), "store_authority_digest": self.store_authority_digest}

    @classmethod
    def create(cls, *, workspace_id: str, storage_generation_id: str) -> Self:
        body = {
            "codec_version": 1,
            "schema": CAPTURED_BODY_STORE_AUTHORITY_SCHEMA,
            "storage_contract": "immutable-content-addressed-body-v1",
            "storage_generation_id": storage_generation_id,
            "workspace_id": workspace_id,
        }
        return cls(
            workspace_id=workspace_id,
            storage_generation_id=storage_generation_id,
            store_authority_digest=_digest(CAPTURED_BODY_STORE_AUTHORITY_SCHEMA, body),
        )

    @classmethod
    def from_wire(cls, value: object) -> Self:
        body = _dict(value, "retention store authority")
        _keys(
            body,
            frozenset(
                {
                    "schema",
                    "codec_version",
                    "workspace_id",
                    "storage_generation_id",
                    "storage_contract",
                    "store_authority_digest",
                }
            ),
            "retention store authority",
        )
        return cls(**body)  # pyright: ignore[reportArgumentType]

    @classmethod
    def from_canonical_bytes(cls, value: object) -> Self:
        return cls.from_wire(_decode_canonical(value))


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceCapturedManifestBodyWriteEvidence(_Portable):
    store_authority_digest: str
    source_package_origin_digest: str
    origin_membership_admission_digest: str
    capture_attempt_digest: str
    source_snapshot_digest: str
    source_movement_digest: str
    manifest_source_body_ref: WorkspaceSemanticPackageBodyRef
    write_attempt_digest: str
    write_evidence_digest: str
    schema: str = CAPTURED_MANIFEST_WRITE_EVIDENCE_SCHEMA
    codec_version: int = CODEC_VERSION
    disposition: str = "durable_present"

    def __post_init__(self) -> None:
        if type(self) is not WorkspaceCapturedManifestBodyWriteEvidence:
            raise TypeError("write evidence must be exact")
        for field in (
            "store_authority_digest",
            "source_package_origin_digest",
            "origin_membership_admission_digest",
            "capture_attempt_digest",
            "source_snapshot_digest",
            "source_movement_digest",
        ):
            _digest_value(getattr(self, field), field)
        body_ref = WorkspaceSemanticPackageBodyRef.from_wire(
            _exact(
                self.manifest_source_body_ref,
                WorkspaceSemanticPackageBodyRef,
                "manifest_source_body_ref",
            ).to_wire()
        )
        if (
            self.schema != CAPTURED_MANIFEST_WRITE_EVIDENCE_SCHEMA
            or type(self.codec_version) is not int
            or self.codec_version != 1
            or self.disposition != "durable_present"
        ):
            raise Error("write evidence constants are unsupported")
        if self.write_attempt_digest != _digest(
            CAPTURED_MANIFEST_WRITE_ATTEMPT_DOMAIN, self._attempt_body(body_ref)
        ):
            raise Error("write attempt digest mismatched")
        if self.write_evidence_digest != _digest(self.schema, self._body(body_ref)):
            raise Error("write evidence digest mismatched")
        _finish(self)

    def _attempt_body(
        self, body_ref: WorkspaceSemanticPackageBodyRef | None = None
    ) -> dict[str, object]:
        ref_value = body_ref or self.manifest_source_body_ref
        return {
            "capture_attempt_digest": self.capture_attempt_digest,
            "manifest_source_body_ref": ref_value.to_wire(),
            "origin_membership_admission_digest": self.origin_membership_admission_digest,
            "source_movement_digest": self.source_movement_digest,
            "source_package_origin_digest": self.source_package_origin_digest,
            "source_snapshot_digest": self.source_snapshot_digest,
            "store_authority_digest": self.store_authority_digest,
        }

    def _body(
        self, body_ref: WorkspaceSemanticPackageBodyRef | None = None
    ) -> dict[str, object]:
        return {
            "codec_version": self.codec_version,
            "disposition": self.disposition,
            "schema": self.schema,
            **self._attempt_body(body_ref),
            "write_attempt_digest": self.write_attempt_digest,
        }

    def _wire_unchecked(self) -> dict[str, object]:
        return {**self._body(), "write_evidence_digest": self.write_evidence_digest}

    @classmethod
    def create(cls, **values: object) -> Self:
        body_ref = _exact(
            values.get("manifest_source_body_ref"),
            WorkspaceSemanticPackageBodyRef,
            "manifest_source_body_ref",
        )
        attempt = {
            "capture_attempt_digest": values["capture_attempt_digest"],
            "manifest_source_body_ref": body_ref.to_wire(),
            "origin_membership_admission_digest": values[
                "origin_membership_admission_digest"
            ],
            "source_movement_digest": values["source_movement_digest"],
            "source_package_origin_digest": values["source_package_origin_digest"],
            "source_snapshot_digest": values["source_snapshot_digest"],
            "store_authority_digest": values["store_authority_digest"],
        }
        write_attempt = _digest(CAPTURED_MANIFEST_WRITE_ATTEMPT_DOMAIN, attempt)
        body = {
            "schema": CAPTURED_MANIFEST_WRITE_EVIDENCE_SCHEMA,
            "codec_version": 1,
            "disposition": "durable_present",
            **attempt,
            "write_attempt_digest": write_attempt,
        }
        return cls(
            **cast(dict[str, object], values),  # pyright: ignore[reportArgumentType]
            write_attempt_digest=write_attempt,
            write_evidence_digest=_digest(
                CAPTURED_MANIFEST_WRITE_EVIDENCE_SCHEMA, body
            ),
        )  # pyright: ignore[reportArgumentType]

    @classmethod
    def from_wire(cls, value: object) -> Self:
        body = _dict(value, "write evidence")
        _keys(
            body,
            frozenset(
                {
                    "schema",
                    "codec_version",
                    "disposition",
                    "store_authority_digest",
                    "source_package_origin_digest",
                    "origin_membership_admission_digest",
                    "capture_attempt_digest",
                    "source_snapshot_digest",
                    "source_movement_digest",
                    "manifest_source_body_ref",
                    "write_attempt_digest",
                    "write_evidence_digest",
                }
            ),
            "write evidence",
        )
        return cls(
            **{  # pyright: ignore[reportArgumentType]
                key: item
                for key, item in body.items()
                if key != "manifest_source_body_ref"
            },
            manifest_source_body_ref=WorkspaceSemanticPackageBodyRef.from_wire(
                body["manifest_source_body_ref"]
            ),
        )  # pyright: ignore[reportArgumentType]

    @classmethod
    def from_canonical_bytes(cls, value: object) -> Self:
        return cls.from_wire(_decode_canonical(value))


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceOperationCapturedManifestBodyRetentionAdmission(_Portable):
    source_package_origin_digest: str
    origin_membership_admission_digest: str
    capture_attempt_digest: str
    source_snapshot_digest: str
    source_movement_digest: str
    manifest_relative_path: str
    manifest_kind: str
    manifest_source_body_ref: WorkspaceSemanticPackageBodyRef
    store_authority_digest: str
    write_attempt_digest: str
    write_evidence_digest: str
    retention_admission_digest: str
    schema: str = CAPTURED_MANIFEST_RETENTION_ADMISSION_SCHEMA
    codec_version: int = CODEC_VERSION
    disposition: str = "retained"

    def __post_init__(self) -> None:
        if type(self) is not WorkspaceOperationCapturedManifestBodyRetentionAdmission:
            raise TypeError("retention admission must be exact")
        for field in (
            "source_package_origin_digest",
            "origin_membership_admission_digest",
            "capture_attempt_digest",
            "source_snapshot_digest",
            "source_movement_digest",
            "store_authority_digest",
            "write_attempt_digest",
            "write_evidence_digest",
        ):
            _digest_value(getattr(self, field), field)
        _manifest_path(self.manifest_relative_path, "manifest_relative_path")
        _token(self.manifest_kind, "manifest_kind")
        WorkspaceSemanticPackageBodyRef.from_wire(
            _exact(
                self.manifest_source_body_ref,
                WorkspaceSemanticPackageBodyRef,
                "manifest_source_body_ref",
            ).to_wire()
        )
        if (
            self.schema != CAPTURED_MANIFEST_RETENTION_ADMISSION_SCHEMA
            or type(self.codec_version) is not int
            or self.codec_version != 1
            or self.disposition != "retained"
        ):
            raise Error("retention constants are unsupported")
        if self.retention_admission_digest != _digest(self.schema, self._body()):
            raise Error("retention admission digest mismatched")
        _finish(self)

    def _body(self) -> dict[str, object]:
        return {
            "capture_attempt_digest": self.capture_attempt_digest,
            "codec_version": self.codec_version,
            "disposition": self.disposition,
            "manifest_kind": self.manifest_kind,
            "manifest_relative_path": self.manifest_relative_path,
            "manifest_source_body_ref": self.manifest_source_body_ref.to_wire(),
            "origin_membership_admission_digest": self.origin_membership_admission_digest,
            "schema": self.schema,
            "source_movement_digest": self.source_movement_digest,
            "source_package_origin_digest": self.source_package_origin_digest,
            "source_snapshot_digest": self.source_snapshot_digest,
            "store_authority_digest": self.store_authority_digest,
            "write_attempt_digest": self.write_attempt_digest,
            "write_evidence_digest": self.write_evidence_digest,
        }

    def _wire_unchecked(self) -> dict[str, object]:
        return {
            **self._body(),
            "retention_admission_digest": self.retention_admission_digest,
        }

    @classmethod
    def create(
        cls,
        *,
        write_evidence: WorkspaceCapturedManifestBodyWriteEvidence,
        manifest_relative_path: str,
        manifest_kind: str,
    ) -> Self:
        evidence = WorkspaceCapturedManifestBodyWriteEvidence.from_wire(
            _exact(
                write_evidence,
                WorkspaceCapturedManifestBodyWriteEvidence,
                "write_evidence",
            ).to_wire()
        )
        values = {
            "source_package_origin_digest": evidence.source_package_origin_digest,
            "origin_membership_admission_digest": evidence.origin_membership_admission_digest,
            "capture_attempt_digest": evidence.capture_attempt_digest,
            "source_snapshot_digest": evidence.source_snapshot_digest,
            "source_movement_digest": evidence.source_movement_digest,
            "manifest_relative_path": manifest_relative_path,
            "manifest_kind": manifest_kind,
            "manifest_source_body_ref": evidence.manifest_source_body_ref,
            "store_authority_digest": evidence.store_authority_digest,
            "write_attempt_digest": evidence.write_attempt_digest,
            "write_evidence_digest": evidence.write_evidence_digest,
        }
        body = {
            "schema": CAPTURED_MANIFEST_RETENTION_ADMISSION_SCHEMA,
            "codec_version": 1,
            "disposition": "retained",
            **{
                key: (
                    value.to_wire()
                    if type(value) is WorkspaceSemanticPackageBodyRef
                    else value
                )
                for key, value in values.items()
            },
        }
        return cls(
            **values,  # pyright: ignore[reportArgumentType]
            retention_admission_digest=_digest(
                CAPTURED_MANIFEST_RETENTION_ADMISSION_SCHEMA, body
            ),
        )  # pyright: ignore[reportArgumentType]

    @classmethod
    def from_wire(cls, value: object) -> Self:
        body = _dict(value, "retention admission")
        _keys(
            body,
            frozenset(
                {
                    "schema",
                    "codec_version",
                    "disposition",
                    "source_package_origin_digest",
                    "origin_membership_admission_digest",
                    "capture_attempt_digest",
                    "source_snapshot_digest",
                    "source_movement_digest",
                    "manifest_relative_path",
                    "manifest_kind",
                    "manifest_source_body_ref",
                    "store_authority_digest",
                    "write_attempt_digest",
                    "write_evidence_digest",
                    "retention_admission_digest",
                }
            ),
            "retention admission",
        )
        return cls(
            **{  # pyright: ignore[reportArgumentType]
                key: item
                for key, item in body.items()
                if key != "manifest_source_body_ref"
            },
            manifest_source_body_ref=WorkspaceSemanticPackageBodyRef.from_wire(
                body["manifest_source_body_ref"]
            ),
        )  # pyright: ignore[reportArgumentType]

    @classmethod
    def from_canonical_bytes(cls, value: object) -> Self:
        return cls.from_wire(_decode_canonical(value))


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceOperationManifestRetentionBindingAdmission(_Portable):
    operation_authority_digest: str
    operation_id: str
    operation_request_digest: str
    capture_attempt_digest: str
    source_package_origin_digest: str
    source_package_origin_admission_digest: str
    retention_admission_digest: str
    manifest_relative_path: str
    manifest_kind: str
    manifest_source_body_ref: WorkspaceSemanticPackageBodyRef
    binding_admission_digest: str
    schema: str = MANIFEST_RETENTION_BINDING_ADMISSION_SCHEMA
    codec_version: int = CODEC_VERSION
    disposition: str = "bound"

    def __post_init__(self) -> None:
        if type(self) is not WorkspaceOperationManifestRetentionBindingAdmission:
            raise TypeError("retention binding must be exact")
        for field in (
            "operation_authority_digest",
            "operation_request_digest",
            "capture_attempt_digest",
            "source_package_origin_digest",
            "source_package_origin_admission_digest",
            "retention_admission_digest",
        ):
            _digest_value(getattr(self, field), field)
        _uuid(self.operation_id, "operation_id")
        _manifest_path(self.manifest_relative_path, "manifest_relative_path")
        _token(self.manifest_kind, "manifest_kind")
        WorkspaceSemanticPackageBodyRef.from_wire(
            _exact(
                self.manifest_source_body_ref,
                WorkspaceSemanticPackageBodyRef,
                "manifest_source_body_ref",
            ).to_wire()
        )
        if (
            self.schema != MANIFEST_RETENTION_BINDING_ADMISSION_SCHEMA
            or type(self.codec_version) is not int
            or self.codec_version != 1
            or self.disposition != "bound"
        ):
            raise Error("binding constants are unsupported")
        if self.binding_admission_digest != _digest(self.schema, self._body()):
            raise Error("binding admission digest mismatched")
        _finish(self)

    def coordinate(self) -> tuple[bytes, bytes, bytes]:
        return (
            self.operation_id.encode("utf-8"),
            self.source_package_origin_digest.encode("utf-8"),
            self.manifest_relative_path.encode("utf-8"),
        )

    def _body(self) -> dict[str, object]:
        return {
            "capture_attempt_digest": self.capture_attempt_digest,
            "codec_version": self.codec_version,
            "disposition": self.disposition,
            "manifest_kind": self.manifest_kind,
            "manifest_relative_path": self.manifest_relative_path,
            "manifest_source_body_ref": self.manifest_source_body_ref.to_wire(),
            "operation_authority_digest": self.operation_authority_digest,
            "operation_id": self.operation_id,
            "operation_request_digest": self.operation_request_digest,
            "retention_admission_digest": self.retention_admission_digest,
            "schema": self.schema,
            "source_package_origin_admission_digest": self.source_package_origin_admission_digest,
            "source_package_origin_digest": self.source_package_origin_digest,
        }

    def _wire_unchecked(self) -> dict[str, object]:
        return {
            **self._body(),
            "binding_admission_digest": self.binding_admission_digest,
        }

    @classmethod
    def create(cls, **values: object) -> Self:
        body = {
            "schema": MANIFEST_RETENTION_BINDING_ADMISSION_SCHEMA,
            "codec_version": 1,
            "disposition": "bound",
            **{
                key: (
                    value.to_wire()
                    if type(value) is WorkspaceSemanticPackageBodyRef
                    else value
                )
                for key, value in values.items()
            },
        }
        return cls(
            **cast(dict[str, object], values),  # pyright: ignore[reportArgumentType]
            binding_admission_digest=_digest(
                MANIFEST_RETENTION_BINDING_ADMISSION_SCHEMA, body
            ),
        )  # pyright: ignore[reportArgumentType]

    @classmethod
    def from_wire(cls, value: object) -> Self:
        body = _dict(value, "retention binding")
        _keys(
            body,
            frozenset(
                {
                    "schema",
                    "codec_version",
                    "disposition",
                    "operation_authority_digest",
                    "operation_id",
                    "operation_request_digest",
                    "capture_attempt_digest",
                    "source_package_origin_digest",
                    "source_package_origin_admission_digest",
                    "retention_admission_digest",
                    "manifest_relative_path",
                    "manifest_kind",
                    "manifest_source_body_ref",
                    "binding_admission_digest",
                }
            ),
            "retention binding",
        )
        return cls(
            **{  # pyright: ignore[reportArgumentType]
                key: item
                for key, item in body.items()
                if key != "manifest_source_body_ref"
            },
            manifest_source_body_ref=WorkspaceSemanticPackageBodyRef.from_wire(
                body["manifest_source_body_ref"]
            ),
        )  # pyright: ignore[reportArgumentType]

    @classmethod
    def from_canonical_bytes(cls, value: object) -> Self:
        return cls.from_wire(_decode_canonical(value))


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceOperationManifestRetentionBindingCatalog(_Portable):
    bindings: tuple[WorkspaceOperationManifestRetentionBindingAdmission, ...]
    catalog_digest: str
    schema: str = MANIFEST_RETENTION_BINDING_CATALOG_SCHEMA
    codec_version: int = CODEC_VERSION

    def __post_init__(self) -> None:
        if type(self) is not WorkspaceOperationManifestRetentionBindingCatalog:
            raise TypeError("retention catalog must be exact")
        if type(self.bindings) is not tuple:
            raise TypeError("catalog bindings must be exact tuple")
        reconstructed = tuple(
            WorkspaceOperationManifestRetentionBindingAdmission.from_wire(
                _exact(
                    item, WorkspaceOperationManifestRetentionBindingAdmission, "binding"
                ).to_wire()
            )
            for item in self.bindings
        )
        coordinates = tuple(item.coordinate() for item in reconstructed)
        if coordinates != tuple(sorted(coordinates)) or len(coordinates) != len(
            set(coordinates)
        ):
            raise Error("catalog bindings must be coordinate ordered and unique")
        if (
            self.schema != MANIFEST_RETENTION_BINDING_CATALOG_SCHEMA
            or type(self.codec_version) is not int
            or self.codec_version != 1
        ):
            raise Error("catalog constants are unsupported")
        if self.catalog_digest != _digest(self.schema, self._body()):
            raise Error("catalog digest mismatched")
        _finish(self)

    def _body(self) -> dict[str, object]:
        return {
            "bindings": [item.to_wire() for item in self.bindings],
            "codec_version": self.codec_version,
            "schema": self.schema,
        }

    def _wire_unchecked(self) -> dict[str, object]:
        return {**self._body(), "catalog_digest": self.catalog_digest}

    @classmethod
    def create(
        cls,
        *,
        bindings: tuple[WorkspaceOperationManifestRetentionBindingAdmission, ...],
    ) -> Self:
        exact = _exact(bindings, tuple, "bindings")
        ordered = tuple(
            sorted(
                (
                    _exact(
                        item,
                        WorkspaceOperationManifestRetentionBindingAdmission,
                        "binding",
                    )
                    for item in exact
                ),
                key=lambda item: item.coordinate(),
            )
        )
        body = {
            "bindings": [item.to_wire() for item in ordered],
            "codec_version": 1,
            "schema": MANIFEST_RETENTION_BINDING_CATALOG_SCHEMA,
        }
        return cls(
            bindings=ordered,
            catalog_digest=_digest(MANIFEST_RETENTION_BINDING_CATALOG_SCHEMA, body),
        )

    @classmethod
    def from_wire(cls, value: object) -> Self:
        body = _dict(value, "retention catalog")
        _keys(
            body,
            frozenset({"schema", "codec_version", "bindings", "catalog_digest"}),
            "retention catalog",
        )
        return cls(
            bindings=tuple(
                WorkspaceOperationManifestRetentionBindingAdmission.from_wire(item)
                for item in _list(body["bindings"], "bindings")
            ),
            catalog_digest=_exact(body["catalog_digest"], str, "catalog_digest"),
            schema=_exact(body["schema"], str, "schema"),
            codec_version=_exact(body["codec_version"], int, "codec_version"),
        )

    @classmethod
    def from_canonical_bytes(cls, value: object) -> Self:
        return cls.from_wire(_decode_canonical(value))


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceOperationManifestRetentionBindingCatalogRef(_Portable):
    ref: str
    body_sha256: str
    size_bytes: int
    schema: str = MANIFEST_RETENTION_BINDING_CATALOG_REF_SCHEMA
    codec_version: int = CODEC_VERSION
    role: str = "operation_manifest_retention_binding_catalog"
    body_schema: str = MANIFEST_RETENTION_BINDING_CATALOG_SCHEMA
    media_type: str = CATALOG_MEDIA_TYPE

    def __post_init__(self) -> None:
        if type(self) is not WorkspaceOperationManifestRetentionBindingCatalogRef:
            raise TypeError("catalog ref must be exact")
        digest = _digest_value(self.body_sha256, "body_sha256")
        _non_negative(self.size_bytes, "size_bytes")
        if (
            self.ref
            != f"cas://workspace-operation-manifest-retention-catalog/{digest[7:]}.json"
        ):
            raise Error("catalog ref suffix mismatched body SHA")
        if (
            self.schema != MANIFEST_RETENTION_BINDING_CATALOG_REF_SCHEMA
            or type(self.codec_version) is not int
            or self.codec_version != 1
            or self.role != "operation_manifest_retention_binding_catalog"
            or self.body_schema != MANIFEST_RETENTION_BINDING_CATALOG_SCHEMA
            or self.media_type != CATALOG_MEDIA_TYPE
        ):
            raise Error("catalog ref constants are unsupported")
        _finish(self)

    def _wire_unchecked(self) -> dict[str, object]:
        return {
            "body_schema": self.body_schema,
            "body_sha256": self.body_sha256,
            "codec_version": self.codec_version,
            "media_type": self.media_type,
            "ref": self.ref,
            "role": self.role,
            "schema": self.schema,
            "size_bytes": self.size_bytes,
        }

    @classmethod
    def create(cls, catalog: WorkspaceOperationManifestRetentionBindingCatalog) -> Self:
        exact = _exact(
            catalog, WorkspaceOperationManifestRetentionBindingCatalog, "catalog"
        )
        body = exact.canonical_bytes()
        digest = _plain_sha(body)
        return cls(
            ref=f"cas://workspace-operation-manifest-retention-catalog/{digest[7:]}.json",
            body_sha256=digest,
            size_bytes=len(body),
        )

    @classmethod
    def from_wire(cls, value: object) -> Self:
        body = _dict(value, "catalog ref")
        _keys(
            body,
            frozenset(
                {
                    "schema",
                    "codec_version",
                    "role",
                    "body_schema",
                    "media_type",
                    "ref",
                    "body_sha256",
                    "size_bytes",
                }
            ),
            "catalog ref",
        )
        return cls(**body)  # pyright: ignore[reportArgumentType]

    @classmethod
    def from_canonical_bytes(cls, value: object) -> Self:
        return cls.from_wire(_decode_canonical(value))


@dataclass(frozen=True, slots=True, weakref_slot=True)
class WorkspaceCapturedManifestBodyAdmission(_Portable):
    operation_authority_digest: str
    request_precondition_workspace_revision_id: str
    registry_projection_ref: WorkspaceSemanticSourcePackageRegistryProjectionRef
    registry_projection_digest: str
    result_workspace_revision_id: str
    result_workspace_revision_persistence_status: str
    result_workspace_revision_commit_id: str | None
    result_workspace_revision_head_commit_id: str
    manifest_retention_binding_catalog_ref: (
        WorkspaceOperationManifestRetentionBindingCatalogRef
    )
    manifest_retention_binding_catalog_digest: str
    source_package_origin: WorkspaceSemanticSourcePackageOriginAuthority
    source_package_origin_admission_digest: str
    manifest_relative_path: str
    manifest_kind: str
    source_snapshot_digest: str
    source_movement_digest: str
    retention_admission_digest: str
    manifest_source_body_ref: WorkspaceSemanticPackageBodyRef
    capture_admission_digest: str
    schema: str = CAPTURED_MANIFEST_BODY_ADMISSION_SCHEMA
    codec_version: int = CODEC_VERSION
    disposition: str = "admitted"

    def __post_init__(self) -> None:
        if type(self) is not WorkspaceCapturedManifestBodyAdmission:
            raise TypeError("captured manifest admission must be exact")
        for field in (
            "operation_authority_digest",
            "registry_projection_digest",
            "manifest_retention_binding_catalog_digest",
            "source_package_origin_admission_digest",
            "source_snapshot_digest",
            "source_movement_digest",
            "retention_admission_digest",
        ):
            _digest_value(getattr(self, field), field)
        _uuid(
            self.request_precondition_workspace_revision_id,
            "request_precondition_workspace_revision_id",
        )
        _uuid(self.result_workspace_revision_id, "result_workspace_revision_id")
        if self.result_workspace_revision_persistence_status != "persisted":
            raise Error("result workspace revision must be persisted")
        if self.result_workspace_revision_commit_id is not None:
            _uuid(
                self.result_workspace_revision_commit_id,
                "result_workspace_revision_commit_id",
            )
        _uuid(
            self.result_workspace_revision_head_commit_id,
            "result_workspace_revision_head_commit_id",
        )
        WorkspaceSemanticSourcePackageRegistryProjectionRef.from_wire(
            _exact(
                self.registry_projection_ref,
                WorkspaceSemanticSourcePackageRegistryProjectionRef,
                "registry_projection_ref",
            ).to_wire()
        )
        WorkspaceOperationManifestRetentionBindingCatalogRef.from_wire(
            _exact(
                self.manifest_retention_binding_catalog_ref,
                WorkspaceOperationManifestRetentionBindingCatalogRef,
                "manifest_retention_binding_catalog_ref",
            ).to_wire()
        )
        WorkspaceSemanticSourcePackageOriginAuthority.from_wire(
            _exact(
                self.source_package_origin,
                WorkspaceSemanticSourcePackageOriginAuthority,
                "source_package_origin",
            ).to_wire()
        )
        WorkspaceSemanticPackageBodyRef.from_wire(
            _exact(
                self.manifest_source_body_ref,
                WorkspaceSemanticPackageBodyRef,
                "manifest_source_body_ref",
            ).to_wire()
        )
        _manifest_path(self.manifest_relative_path, "manifest_relative_path")
        _token(self.manifest_kind, "manifest_kind")
        if (
            self.schema != CAPTURED_MANIFEST_BODY_ADMISSION_SCHEMA
            or type(self.codec_version) is not int
            or self.codec_version != 1
            or self.disposition != "admitted"
        ):
            raise Error("captured manifest constants are unsupported")
        if self.capture_admission_digest != _digest(self.schema, self._body()):
            raise Error("capture admission digest mismatched")
        _finish(self)

    def _body(self) -> dict[str, object]:
        return {
            "codec_version": self.codec_version,
            "disposition": self.disposition,
            "manifest_kind": self.manifest_kind,
            "manifest_relative_path": self.manifest_relative_path,
            "manifest_source_body_ref": self.manifest_source_body_ref.to_wire(),
            "operation_authority_digest": self.operation_authority_digest,
            "request_precondition_workspace_revision_id": (
                self.request_precondition_workspace_revision_id
            ),
            "registry_projection_ref": self.registry_projection_ref.to_wire(),
            "registry_projection_digest": self.registry_projection_digest,
            "result_workspace_revision_id": self.result_workspace_revision_id,
            "result_workspace_revision_persistence_status": (
                self.result_workspace_revision_persistence_status
            ),
            "result_workspace_revision_commit_id": (
                self.result_workspace_revision_commit_id
            ),
            "result_workspace_revision_head_commit_id": (
                self.result_workspace_revision_head_commit_id
            ),
            "manifest_retention_binding_catalog_ref": (
                self.manifest_retention_binding_catalog_ref.to_wire()
            ),
            "manifest_retention_binding_catalog_digest": (
                self.manifest_retention_binding_catalog_digest
            ),
            "retention_admission_digest": self.retention_admission_digest,
            "schema": self.schema,
            "source_movement_digest": self.source_movement_digest,
            "source_package_origin": self.source_package_origin.to_wire(),
            "source_package_origin_admission_digest": self.source_package_origin_admission_digest,
            "source_snapshot_digest": self.source_snapshot_digest,
        }

    def _wire_unchecked(self) -> dict[str, object]:
        return {
            **self._body(),
            "capture_admission_digest": self.capture_admission_digest,
        }

    @classmethod
    def create(cls, **values: object) -> Self:
        origin = _exact(
            values.get("source_package_origin"),
            WorkspaceSemanticSourcePackageOriginAuthority,
            "source_package_origin",
        )
        body_ref = _exact(
            values.get("manifest_source_body_ref"),
            WorkspaceSemanticPackageBodyRef,
            "manifest_source_body_ref",
        )
        projection_ref = _exact(
            values.get("registry_projection_ref"),
            WorkspaceSemanticSourcePackageRegistryProjectionRef,
            "registry_projection_ref",
        )
        catalog_ref = _exact(
            values.get("manifest_retention_binding_catalog_ref"),
            WorkspaceOperationManifestRetentionBindingCatalogRef,
            "manifest_retention_binding_catalog_ref",
        )
        body = {
            "schema": CAPTURED_MANIFEST_BODY_ADMISSION_SCHEMA,
            "codec_version": 1,
            "disposition": "admitted",
            **{
                key: (
                    origin.to_wire()
                    if key == "source_package_origin"
                    else body_ref.to_wire()
                    if key == "manifest_source_body_ref"
                    else projection_ref.to_wire()
                    if key == "registry_projection_ref"
                    else catalog_ref.to_wire()
                    if key == "manifest_retention_binding_catalog_ref"
                    else value
                )
                for key, value in values.items()
            },
        }
        return cls(
            **cast(dict[str, object], values),  # pyright: ignore[reportArgumentType]
            capture_admission_digest=_digest(
                CAPTURED_MANIFEST_BODY_ADMISSION_SCHEMA, body
            ),
        )  # pyright: ignore[reportArgumentType]

    @classmethod
    def from_wire(cls, value: object) -> Self:
        body = _dict(value, "captured manifest admission")
        _keys(
            body,
            frozenset(
                {
                    "schema",
                    "codec_version",
                    "disposition",
                    "operation_authority_digest",
                    "request_precondition_workspace_revision_id",
                    "registry_projection_ref",
                    "registry_projection_digest",
                    "result_workspace_revision_id",
                    "result_workspace_revision_persistence_status",
                    "result_workspace_revision_commit_id",
                    "result_workspace_revision_head_commit_id",
                    "manifest_retention_binding_catalog_ref",
                    "manifest_retention_binding_catalog_digest",
                    "source_package_origin",
                    "source_package_origin_admission_digest",
                    "manifest_relative_path",
                    "manifest_kind",
                    "source_snapshot_digest",
                    "source_movement_digest",
                    "retention_admission_digest",
                    "manifest_source_body_ref",
                    "capture_admission_digest",
                }
            ),
            "captured manifest admission",
        )
        values = {
            key: item
            for key, item in body.items()
            if key
            not in {
                "source_package_origin",
                "manifest_source_body_ref",
                "registry_projection_ref",
                "manifest_retention_binding_catalog_ref",
            }
        }
        return cls(
            **values,  # pyright: ignore[reportArgumentType]
            source_package_origin=WorkspaceSemanticSourcePackageOriginAuthority.from_wire(
                body["source_package_origin"]
            ),
            manifest_source_body_ref=WorkspaceSemanticPackageBodyRef.from_wire(
                body["manifest_source_body_ref"]
            ),
            registry_projection_ref=WorkspaceSemanticSourcePackageRegistryProjectionRef.from_wire(
                body["registry_projection_ref"]
            ),
            manifest_retention_binding_catalog_ref=WorkspaceOperationManifestRetentionBindingCatalogRef.from_wire(
                body["manifest_retention_binding_catalog_ref"]
            ),
        )  # pyright: ignore[reportArgumentType]

    @classmethod
    def from_canonical_bytes(cls, value: object) -> Self:
        return cls.from_wire(_decode_canonical(value))


__all__ = [
    "CAPTURED_BODY_STORE_AUTHORITY_SCHEMA",
    "CAPTURED_MANIFEST_BODY_ADMISSION_SCHEMA",
    "CAPTURED_MANIFEST_RETENTION_ADMISSION_SCHEMA",
    "CAPTURED_MANIFEST_WRITE_EVIDENCE_SCHEMA",
    "MANIFEST_RETENTION_BINDING_ADMISSION_SCHEMA",
    "MANIFEST_RETENTION_BINDING_CATALOG_REF_SCHEMA",
    "MANIFEST_RETENTION_BINDING_CATALOG_SCHEMA",
    "SEMANTIC_PACKAGE_BODY_REF_SCHEMA",
    "WorkspaceCapturedBodyRetentionStoreAuthority",
    "WorkspaceCapturedManifestBodyAdmission",
    "WorkspaceCapturedManifestBodyWriteEvidence",
    "WorkspaceOperationCapturedManifestBodyRetentionAdmission",
    "WorkspaceOperationManifestRetentionBindingAdmission",
    "WorkspaceOperationManifestRetentionBindingCatalog",
    "WorkspaceOperationManifestRetentionBindingCatalogRef",
    "WorkspaceSemanticPackageBodyRef",
]
