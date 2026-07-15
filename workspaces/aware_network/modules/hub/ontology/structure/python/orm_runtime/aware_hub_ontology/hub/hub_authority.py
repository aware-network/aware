from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Hub Ontology
from aware_hub_ontology.hub.hub_enums import (
    HubAuthorityVisibility,
    HubPublicationReceiptStatus,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_hub_ontology.hub.hub_artifact import HubArtifact
    from aware_hub_ontology.hub.hub_artifact import HubArtifactRevision
    from aware_hub_ontology.hub.hub_channel import HubChannel
    from aware_hub_ontology.hub.hub_code_package_publication import HubCodePackagePublication
    from aware_hub_ontology.hub.hub_publication_receipt import HubPublicationReceipt


class HubAuthority(ORMModel):
    # Relationships
    artifacts: list[HubArtifact] = Field(default_factory=list, exclude=True)
    channels: list[HubChannel] = Field(default_factory=list, exclude=True)
    code_package_publications: list[HubCodePackagePublication] = Field(default_factory=list, exclude=True)
    receipts: list[HubPublicationReceipt] = Field(default_factory=list, exclude=True)

    # Attributes
    authority_key: str
    base_url: str | None = Field(default=None)
    description: str | None = Field(default=None)
    title: str | None = Field(default=None)
    visibility: HubAuthorityVisibility = Field(default=HubAuthorityVisibility.public)

    @classmethod
    async def ensure_authority(
        cls,
        authority_key: str = "default",
        title: str | None = "Aware Hub",
        base_url: str | None = None,
        description: str | None = None,
        visibility: HubAuthorityVisibility = HubAuthorityVisibility.public,
    ) -> HubAuthority:
        """
        Ensure one committed Hub authority root.

        Contract:
        - Hub authority truth is commit-backed.
        - Identity is stable by `authority_key`.
        - This root owns channel heads, generic artifact locks, CodePackage publications,
          and publication receipts.
        """

        payload = {
            "authority_key": authority_key,
            "title": title,
            "base_url": base_url,
            "description": description,
            "visibility": visibility,
        }
        result = await invoke_constructor(orm_class=cls, function_name="ensure_authority", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, HubAuthority):
            return value
        return HubAuthority.validate_invocation_value(value)

    async def ensure_channel(
        self,
        channel_key: str = "stable",
        title: str | None = None,
        description: str | None = None,
        visibility: HubAuthorityVisibility = HubAuthorityVisibility.public,
    ) -> HubChannel:
        """Ensure one Hub-owned publication channel under this authority."""

        payload = {"channel_key": channel_key, "title": title, "description": description, "visibility": visibility}
        result = await invoke_instance(orm_model=self, function_name="ensure_channel", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_hub_ontology.hub.hub_channel import HubChannel

        if isinstance(value, HubChannel):
            return value
        return HubChannel.validate_invocation_value(value)

    async def ensure_artifact(
        self,
        artifact_family: str,
        artifact_key: str,
        title: str | None = None,
        description: str | None = None,
        media_type: str | None = None,
    ) -> HubArtifact:
        """Ensure one Hub-owned artifact identity under this authority."""

        payload = {
            "artifact_family": artifact_family,
            "artifact_key": artifact_key,
            "title": title,
            "description": description,
            "media_type": media_type,
        }
        result = await invoke_instance(orm_model=self, function_name="ensure_artifact", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_hub_ontology.hub.hub_artifact import HubArtifact

        if isinstance(value, HubArtifact):
            return value
        return HubArtifact.validate_invocation_value(value)

    async def publish_artifact(
        self,
        artifact_family: str,
        artifact_key: str,
        revision_id: str,
        payload_url: str,
        payload_sha256: str,
        channel_key: str = "stable",
        selector_key: str | None = None,
        target_ref: str | None = None,
        media_type: str | None = None,
        size_bytes: int | None = None,
        producer_kind: str = "unknown",
        producer_key: str = "default",
        provenance_key: str | None = None,
        producer_revision_id: str | None = None,
        source_revision_id: str | None = None,
        source_revision_kind: str | None = None,
        materialization_ref: str | None = None,
        build_ref: str | None = None,
        publisher_execution_id: str | None = None,
        idempotency_key: str | None = None,
        published_at_utc: str | None = None,
        metadata: JsonObject = {},
    ) -> HubArtifactRevision:
        """
        Publish one generic immutable artifact revision into Hub authority truth.

        Contract:
        - Generic artifacts store payload locks and producer provenance only.
        - WorkspaceRevision fields, when present, stay producer provenance and do not
          become Hub revision semantics.
        - Channel head movement is Hub-owned committed truth.
        """

        payload = {
            "artifact_family": artifact_family,
            "artifact_key": artifact_key,
            "revision_id": revision_id,
            "payload_url": payload_url,
            "payload_sha256": payload_sha256,
            "channel_key": channel_key,
            "selector_key": selector_key,
            "target_ref": target_ref,
            "media_type": media_type,
            "size_bytes": size_bytes,
            "producer_kind": producer_kind,
            "producer_key": producer_key,
            "provenance_key": provenance_key,
            "producer_revision_id": producer_revision_id,
            "source_revision_id": source_revision_id,
            "source_revision_kind": source_revision_kind,
            "materialization_ref": materialization_ref,
            "build_ref": build_ref,
            "publisher_execution_id": publisher_execution_id,
            "idempotency_key": idempotency_key,
            "published_at_utc": published_at_utc,
            "metadata": metadata,
        }
        result = await invoke_instance(orm_model=self, function_name="publish_artifact", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_hub_ontology.hub.hub_artifact import HubArtifactRevision

        if isinstance(value, HubArtifactRevision):
            return value
        return HubArtifactRevision.validate_invocation_value(value)

    async def record_code_package_publication(
        self,
        package_name: str,
        language: CodeLanguage,
        surface: str,
        revision_id: str,
        artifact_url: str,
        artifact_sha256: str,
        channel_key: str = "stable",
        code_package_id: UUID | None = None,
        artifact_revision_id: UUID | None = None,
        producer_provenance_id: UUID | None = None,
        descriptor_digest: str | None = None,
        artifact_size_bytes: int | None = None,
        media_type: str | None = None,
        download_handle: str | None = None,
        manifest_kind: str | None = None,
        manifest_relative_path: str | None = None,
        package_root: str | None = None,
        sources_root: str | None = None,
        fqn_prefix: str | None = None,
        version: str | None = None,
        published_at_utc: str | None = None,
        metadata: JsonObject = {},
    ) -> HubCodePackagePublication:
        """Record one authority-owned CodePackage publication row."""

        payload = {
            "package_name": package_name,
            "language": language,
            "surface": surface,
            "revision_id": revision_id,
            "artifact_url": artifact_url,
            "artifact_sha256": artifact_sha256,
            "channel_key": channel_key,
            "code_package_id": code_package_id,
            "artifact_revision_id": artifact_revision_id,
            "producer_provenance_id": producer_provenance_id,
            "descriptor_digest": descriptor_digest,
            "artifact_size_bytes": artifact_size_bytes,
            "media_type": media_type,
            "download_handle": download_handle,
            "manifest_kind": manifest_kind,
            "manifest_relative_path": manifest_relative_path,
            "package_root": package_root,
            "sources_root": sources_root,
            "fqn_prefix": fqn_prefix,
            "version": version,
            "published_at_utc": published_at_utc,
            "metadata": metadata,
        }
        result = await invoke_instance(orm_model=self, function_name="record_code_package_publication", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_hub_ontology.hub.hub_code_package_publication import HubCodePackagePublication

        if isinstance(value, HubCodePackagePublication):
            return value
        return HubCodePackagePublication.validate_invocation_value(value)

    async def publish_code_package(
        self,
        package_name: str,
        language: CodeLanguage,
        surface: str,
        revision_id: str,
        artifact_url: str,
        artifact_sha256: str,
        channel_key: str = "stable",
        code_package_id: UUID | None = None,
        descriptor_digest: str | None = None,
        artifact_size_bytes: int | None = None,
        media_type: str | None = None,
        download_handle: str | None = None,
        manifest_kind: str | None = None,
        manifest_relative_path: str | None = None,
        package_root: str | None = None,
        sources_root: str | None = None,
        fqn_prefix: str | None = None,
        version: str | None = None,
        producer_kind: str = "workspace",
        producer_key: str = "default",
        provenance_key: str | None = None,
        producer_revision_id: str | None = None,
        source_revision_id: str | None = None,
        source_revision_kind: str | None = None,
        materialization_ref: str | None = None,
        build_ref: str | None = None,
        publisher_execution_id: str | None = None,
        idempotency_key: str | None = None,
        published_at_utc: str | None = None,
        metadata: JsonObject = {},
    ) -> HubCodePackagePublication:
        """
        Publish one CodePackage artifact lock into Hub authority truth.

        Contract:
        - This is the king Hub model for package distribution.
        - CodePackage remains Code-owned semantic package truth.
        - Hub owns channel heads, artifact locks, provenance, and publication receipts.
        """

        payload = {
            "package_name": package_name,
            "language": language,
            "surface": surface,
            "revision_id": revision_id,
            "artifact_url": artifact_url,
            "artifact_sha256": artifact_sha256,
            "channel_key": channel_key,
            "code_package_id": code_package_id,
            "descriptor_digest": descriptor_digest,
            "artifact_size_bytes": artifact_size_bytes,
            "media_type": media_type,
            "download_handle": download_handle,
            "manifest_kind": manifest_kind,
            "manifest_relative_path": manifest_relative_path,
            "package_root": package_root,
            "sources_root": sources_root,
            "fqn_prefix": fqn_prefix,
            "version": version,
            "producer_kind": producer_kind,
            "producer_key": producer_key,
            "provenance_key": provenance_key,
            "producer_revision_id": producer_revision_id,
            "source_revision_id": source_revision_id,
            "source_revision_kind": source_revision_kind,
            "materialization_ref": materialization_ref,
            "build_ref": build_ref,
            "publisher_execution_id": publisher_execution_id,
            "idempotency_key": idempotency_key,
            "published_at_utc": published_at_utc,
            "metadata": metadata,
        }
        result = await invoke_instance(orm_model=self, function_name="publish_code_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_hub_ontology.hub.hub_code_package_publication import HubCodePackagePublication

        if isinstance(value, HubCodePackagePublication):
            return value
        return HubCodePackagePublication.validate_invocation_value(value)

    async def record_receipt(
        self,
        receipt_key: str,
        operation: str,
        status: HubPublicationReceiptStatus = HubPublicationReceiptStatus.accepted,
        publisher_execution_id: str | None = None,
        idempotency_key: str | None = None,
        artifact_revision_id: UUID | None = None,
        code_package_publication_id: UUID | None = None,
        authority_source_url: str | None = None,
        message: str | None = None,
        recorded_at_utc: str | None = None,
        detail: JsonObject = {},
    ) -> HubPublicationReceipt:
        """Record one Hub-owned authority receipt."""

        payload = {
            "receipt_key": receipt_key,
            "operation": operation,
            "status": status,
            "publisher_execution_id": publisher_execution_id,
            "idempotency_key": idempotency_key,
            "artifact_revision_id": artifact_revision_id,
            "code_package_publication_id": code_package_publication_id,
            "authority_source_url": authority_source_url,
            "message": message,
            "recorded_at_utc": recorded_at_utc,
            "detail": detail,
        }
        result = await invoke_instance(orm_model=self, function_name="record_receipt", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_hub_ontology.hub.hub_publication_receipt import HubPublicationReceipt

        if isinstance(value, HubPublicationReceipt):
            return value
        return HubPublicationReceipt.validate_invocation_value(value)


class HubAuthorityEnsureAuthorityInput(BaseModel):
    authority_key: str = Field(default="default")
    title: str | None = Field(default="Aware Hub")
    base_url: str | None = Field(default=None)
    description: str | None = Field(default=None)
    visibility: HubAuthorityVisibility = Field(default=HubAuthorityVisibility.public)


class HubAuthorityEnsureAuthorityOutput(BaseModel):
    value: HubAuthority


class HubAuthorityEnsureChannelInput(BaseModel):
    channel_key: str = Field(default="stable")
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    visibility: HubAuthorityVisibility = Field(default=HubAuthorityVisibility.public)


class HubAuthorityEnsureChannelOutput(BaseModel):
    value: HubChannel


class HubAuthorityEnsureArtifactInput(BaseModel):
    artifact_family: str
    artifact_key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    media_type: str | None = Field(default=None)


class HubAuthorityEnsureArtifactOutput(BaseModel):
    value: HubArtifact


class HubAuthorityPublishArtifactInput(BaseModel):
    artifact_family: str
    artifact_key: str
    revision_id: str
    payload_url: str
    payload_sha256: str
    channel_key: str = Field(default="stable")
    selector_key: str | None = Field(default=None)
    target_ref: str | None = Field(default=None)
    media_type: str | None = Field(default=None)
    size_bytes: int | None = Field(default=None)
    producer_kind: str = Field(default="unknown")
    producer_key: str = Field(default="default")
    provenance_key: str | None = Field(default=None)
    producer_revision_id: str | None = Field(default=None)
    source_revision_id: str | None = Field(default=None)
    source_revision_kind: str | None = Field(default=None)
    materialization_ref: str | None = Field(default=None)
    build_ref: str | None = Field(default=None)
    publisher_execution_id: str | None = Field(default=None)
    idempotency_key: str | None = Field(default=None)
    published_at_utc: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class HubAuthorityPublishArtifactOutput(BaseModel):
    value: HubArtifactRevision


class HubAuthorityRecordCodePackagePublicationInput(BaseModel):
    package_name: str
    language: CodeLanguage
    surface: str
    revision_id: str
    artifact_url: str
    artifact_sha256: str
    channel_key: str = Field(default="stable")
    code_package_id: UUID | None = Field(default=None)
    artifact_revision_id: UUID | None = Field(default=None)
    producer_provenance_id: UUID | None = Field(default=None)
    descriptor_digest: str | None = Field(default=None)
    artifact_size_bytes: int | None = Field(default=None)
    media_type: str | None = Field(default=None)
    download_handle: str | None = Field(default=None)
    manifest_kind: str | None = Field(default=None)
    manifest_relative_path: str | None = Field(default=None)
    package_root: str | None = Field(default=None)
    sources_root: str | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    version: str | None = Field(default=None)
    published_at_utc: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class HubAuthorityRecordCodePackagePublicationOutput(BaseModel):
    value: HubCodePackagePublication


class HubAuthorityPublishCodePackageInput(BaseModel):
    package_name: str
    language: CodeLanguage
    surface: str
    revision_id: str
    artifact_url: str
    artifact_sha256: str
    channel_key: str = Field(default="stable")
    code_package_id: UUID | None = Field(default=None)
    descriptor_digest: str | None = Field(default=None)
    artifact_size_bytes: int | None = Field(default=None)
    media_type: str | None = Field(default=None)
    download_handle: str | None = Field(default=None)
    manifest_kind: str | None = Field(default=None)
    manifest_relative_path: str | None = Field(default=None)
    package_root: str | None = Field(default=None)
    sources_root: str | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    version: str | None = Field(default=None)
    producer_kind: str = Field(default="workspace")
    producer_key: str = Field(default="default")
    provenance_key: str | None = Field(default=None)
    producer_revision_id: str | None = Field(default=None)
    source_revision_id: str | None = Field(default=None)
    source_revision_kind: str | None = Field(default=None)
    materialization_ref: str | None = Field(default=None)
    build_ref: str | None = Field(default=None)
    publisher_execution_id: str | None = Field(default=None)
    idempotency_key: str | None = Field(default=None)
    published_at_utc: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class HubAuthorityPublishCodePackageOutput(BaseModel):
    value: HubCodePackagePublication


class HubAuthorityRecordReceiptInput(BaseModel):
    receipt_key: str
    operation: str
    status: HubPublicationReceiptStatus = Field(default=HubPublicationReceiptStatus.accepted)
    publisher_execution_id: str | None = Field(default=None)
    idempotency_key: str | None = Field(default=None)
    artifact_revision_id: UUID | None = Field(default=None)
    code_package_publication_id: UUID | None = Field(default=None)
    authority_source_url: str | None = Field(default=None)
    message: str | None = Field(default=None)
    recorded_at_utc: str | None = Field(default=None)
    detail: JsonObject = Field(default_factory=JsonObject)


class HubAuthorityRecordReceiptOutput(BaseModel):
    value: HubPublicationReceipt


FUNCTIONS = {
    "HubAuthority": {
        "ensure_authority": {
            "canonical": {
                "name": "ensure_authority",
                "description": "Ensure one committed Hub authority root.\n\nContract:\n- Hub authority truth is commit-backed.\n- Identity is stable by `authority_key`.\n- This root owns channel heads, generic artifact locks, CodePackage publications,\n  and publication receipts.",
                "is_constructor": True,
            },
            "input": HubAuthorityEnsureAuthorityInput,
            "output": HubAuthorityEnsureAuthorityOutput,
        },
        "ensure_channel": {
            "canonical": {
                "name": "ensure_channel",
                "description": "Ensure one Hub-owned publication channel under this authority.",
                "is_constructor": False,
            },
            "input": HubAuthorityEnsureChannelInput,
            "output": HubAuthorityEnsureChannelOutput,
        },
        "ensure_artifact": {
            "canonical": {
                "name": "ensure_artifact",
                "description": "Ensure one Hub-owned artifact identity under this authority.",
                "is_constructor": False,
            },
            "input": HubAuthorityEnsureArtifactInput,
            "output": HubAuthorityEnsureArtifactOutput,
        },
        "publish_artifact": {
            "canonical": {
                "name": "publish_artifact",
                "description": "Publish one generic immutable artifact revision into Hub authority truth.\n\nContract:\n- Generic artifacts store payload locks and producer provenance only.\n- WorkspaceRevision fields, when present, stay producer provenance and do not\n  become Hub revision semantics.\n- Channel head movement is Hub-owned committed truth.",
                "is_constructor": False,
            },
            "input": HubAuthorityPublishArtifactInput,
            "output": HubAuthorityPublishArtifactOutput,
        },
        "record_code_package_publication": {
            "canonical": {
                "name": "record_code_package_publication",
                "description": "Record one authority-owned CodePackage publication row.",
                "is_constructor": False,
            },
            "input": HubAuthorityRecordCodePackagePublicationInput,
            "output": HubAuthorityRecordCodePackagePublicationOutput,
        },
        "publish_code_package": {
            "canonical": {
                "name": "publish_code_package",
                "description": "Publish one CodePackage artifact lock into Hub authority truth.\n\nContract:\n- This is the king Hub model for package distribution.\n- CodePackage remains Code-owned semantic package truth.\n- Hub owns channel heads, artifact locks, provenance, and publication receipts.",
                "is_constructor": False,
            },
            "input": HubAuthorityPublishCodePackageInput,
            "output": HubAuthorityPublishCodePackageOutput,
        },
        "record_receipt": {
            "canonical": {
                "name": "record_receipt",
                "description": "Record one Hub-owned authority receipt.",
                "is_constructor": False,
            },
            "input": HubAuthorityRecordReceiptInput,
            "output": HubAuthorityRecordReceiptOutput,
        },
    },
}

__all__ = [
    "HubAuthority",
    "HubAuthorityEnsureAuthorityInput",
    "HubAuthorityEnsureAuthorityOutput",
    "HubAuthorityEnsureChannelInput",
    "HubAuthorityEnsureChannelOutput",
    "HubAuthorityEnsureArtifactInput",
    "HubAuthorityEnsureArtifactOutput",
    "HubAuthorityPublishArtifactInput",
    "HubAuthorityPublishArtifactOutput",
    "HubAuthorityRecordCodePackagePublicationInput",
    "HubAuthorityRecordCodePackagePublicationOutput",
    "HubAuthorityPublishCodePackageInput",
    "HubAuthorityPublishCodePackageOutput",
    "HubAuthorityRecordReceiptInput",
    "HubAuthorityRecordReceiptOutput",
    "FUNCTIONS",
]
