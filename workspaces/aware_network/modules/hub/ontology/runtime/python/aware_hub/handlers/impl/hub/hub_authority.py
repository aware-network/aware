from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Hub Ontology
from aware_hub_ontology.hub.hub_enums import (
    HubAuthorityVisibility,
    HubPublicationReceiptStatus,
)
from aware_hub_ontology.hub.hub_artifact import (
    HubArtifact,
    HubArtifactRevision,
)
from aware_hub_ontology.hub.hub_authority import HubAuthority
from aware_hub_ontology.hub.hub_channel import HubChannel
from aware_hub_ontology.hub.hub_code_package_publication import HubCodePackagePublication
from aware_hub_ontology.hub.hub_publication_receipt import HubPublicationReceipt

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_hub.handlers.impl.hub._helpers import (
    append_if_missing,
    clean_optional,
    clean_required,
    derived_provenance_key,
    enum_value,
    handler_session_or_none,
    receipt_key_for,
)
from aware_hub.stable_ids import stable_hub_authority_id
from aware_hub.stable_ids import (
    stable_hub_artifact_id,
    stable_hub_channel_id,
)
from aware_hub_ontology.hub.hub_channel import HubChannelHead
from aware_hub_ontology.hub.hub_producer_provenance import HubProducerProvenance

# --- AWARE: USER_IMPORTS END


async def ensure_authority(
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

    # --- AWARE: LOGIC START ensure_authority
    authority_key_norm = clean_required(authority_key, "authority_key")
    authority_id = stable_hub_authority_id(authority_key=authority_key_norm)
    session = handler_session_or_none()
    if session is not None:
        existing = session.imap_get(HubAuthority, authority_id)
        if existing is not None:
            if existing.authority_key != authority_key_norm:
                raise RuntimeError(f"HubAuthority.ensure_authority key mismatch: hub_authority_id={authority_id}")
            return existing

    return HubAuthority(
        id=authority_id,
        authority_key=authority_key_norm,
        title=clean_optional(title),
        base_url=clean_optional(base_url),
        description=clean_optional(description),
        visibility=visibility,
    )
    # --- AWARE: LOGIC END ensure_authority


async def ensure_channel(
    hub_authority: HubAuthority,
    channel_key: str = "stable",
    title: str | None = None,
    description: str | None = None,
    visibility: HubAuthorityVisibility = HubAuthorityVisibility.public,
) -> HubChannel:
    """
    Ensure one Hub-owned publication channel under this authority.
    """

    # --- AWARE: LOGIC START ensure_channel
    if hub_authority.id is None:
        raise RuntimeError("HubAuthority.ensure_channel requires HubAuthority.id")

    channel = await HubChannel.build_via_hub_authority(
        hub_authority_id=hub_authority.id,
        channel_key=channel_key,
        title=title,
        description=description,
        visibility=visibility,
    )
    append_if_missing(hub_authority.channels, channel)
    return channel
    # --- AWARE: LOGIC END ensure_channel


async def ensure_artifact(
    hub_authority: HubAuthority,
    artifact_family: str,
    artifact_key: str,
    title: str | None = None,
    description: str | None = None,
    media_type: str | None = None,
) -> HubArtifact:
    """
    Ensure one Hub-owned artifact identity under this authority.
    """

    # --- AWARE: LOGIC START ensure_artifact
    if hub_authority.id is None:
        raise RuntimeError("HubAuthority.ensure_artifact requires HubAuthority.id")

    artifact = await HubArtifact.build_via_hub_authority(
        hub_authority_id=hub_authority.id,
        artifact_family=artifact_family,
        artifact_key=artifact_key,
        title=title,
        description=description,
        media_type=media_type,
    )
    append_if_missing(hub_authority.artifacts, artifact)
    return artifact
    # --- AWARE: LOGIC END ensure_artifact


async def publish_artifact(
    hub_authority: HubAuthority,
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
    metadata: JsonObject = JsonObject(),
) -> HubArtifactRevision:
    """
    Publish one generic immutable artifact revision into Hub authority truth.

    Contract:
    - Generic artifacts store payload locks and producer provenance only.
    - WorkspaceRevision fields, when present, stay producer provenance and do not
      become Hub revision semantics.
    - Channel head movement is Hub-owned committed truth.
    """

    # --- AWARE: LOGIC START publish_artifact
    family = clean_required(artifact_family, "artifact_family")
    key = clean_required(artifact_key, "artifact_key")
    revision_key = clean_required(revision_id, "revision_id")
    payload_url_norm = clean_required(payload_url, "payload_url")
    payload_sha256_norm = clean_required(payload_sha256, "payload_sha256")
    channel_key_norm = clean_required(channel_key, "channel_key")
    provenance_key_norm = derived_provenance_key(
        explicit_key=provenance_key,
        revision_id=revision_key,
        producer_revision_id=producer_revision_id,
        source_revision_kind=source_revision_kind,
        source_revision_id=source_revision_id,
        materialization_ref=materialization_ref,
        build_ref=build_ref,
    )

    provenance = await HubProducerProvenance.build(
        producer_kind=producer_kind,
        producer_key=producer_key,
        provenance_key=provenance_key_norm,
        producer_revision_id=producer_revision_id,
        source_revision_id=source_revision_id,
        source_revision_kind=source_revision_kind,
        materialization_ref=materialization_ref,
        build_ref=build_ref,
        metadata=metadata,
    )
    session = handler_session_or_none()
    artifact_id = (
        stable_hub_artifact_id(
            hub_authority_id=hub_authority.id,
            artifact_family=family,
            artifact_key=key,
        )
        if hub_authority.id is not None
        else None
    )
    artifact_already_committed = (
        session.imap_get(HubArtifact, artifact_id) is not None
        if session is not None and artifact_id is not None
        else False
    )
    artifact = await ensure_artifact(
        hub_authority,
        artifact_family=family,
        artifact_key=key,
        title=key,
        media_type=media_type,
    )
    if artifact_already_committed:
        revision = await artifact.publish_revision(
            revision_id=revision_key,
            payload_url=payload_url_norm,
            payload_sha256=payload_sha256_norm,
            selector_key=selector_key,
            target_ref=target_ref,
            media_type=media_type,
            size_bytes=size_bytes,
            producer_provenance_id=provenance.id,
            published_at_utc=published_at_utc,
            metadata=metadata,
        )
    else:
        revision = await HubArtifactRevision.build_via_hub_artifact(
            hub_artifact_id=artifact.id,
            revision_id=revision_key,
            payload_url=payload_url_norm,
            payload_sha256=payload_sha256_norm,
            selector_key=selector_key,
            target_ref=target_ref,
            media_type=media_type,
            size_bytes=size_bytes,
            producer_provenance_id=provenance.id,
            published_at_utc=published_at_utc,
            metadata=metadata,
        )
        append_if_missing(artifact.revisions, revision)
    channel_id = (
        stable_hub_channel_id(hub_authority_id=hub_authority.id, channel_key=channel_key_norm)
        if hub_authority.id is not None
        else None
    )
    channel_already_committed = (
        session.imap_get(HubChannel, channel_id) is not None
        if session is not None and channel_id is not None
        else False
    )
    channel = await ensure_channel(hub_authority, channel_key=channel_key_norm)
    if channel_already_committed:
        await channel.upsert_head(
            artifact_family=family,
            artifact_key=key,
            revision_id=revision_key,
            selector_key=selector_key,
            artifact_revision_id=revision.id,
            updated_at_utc=published_at_utc,
        )
    else:
        head = await HubChannelHead.build_via_hub_channel(
            hub_channel_id=channel.id,
            artifact_family=family,
            artifact_key=key,
            revision_id=revision_key,
            selector_key=selector_key,
            artifact_revision_id=revision.id,
            updated_at_utc=published_at_utc,
        )
        append_if_missing(channel.heads, head)
    await record_receipt(
        hub_authority,
        receipt_key=idempotency_key
        or receipt_key_for(
            operation="publish_artifact",
            artifact_family=family,
            artifact_key=key,
            revision_id=revision_key,
        ),
        operation="publish_artifact",
        status=HubPublicationReceiptStatus.accepted,
        publisher_execution_id=publisher_execution_id,
        idempotency_key=idempotency_key,
        artifact_revision_id=revision.id,
        message=None,
        recorded_at_utc=published_at_utc,
        detail=metadata,
    )
    return revision
    # --- AWARE: LOGIC END publish_artifact


async def record_code_package_publication(
    hub_authority: HubAuthority,
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
    metadata: JsonObject = JsonObject(),
) -> HubCodePackagePublication:
    """
    Record one authority-owned CodePackage publication row.
    """

    # --- AWARE: LOGIC START record_code_package_publication
    if hub_authority.id is None:
        raise RuntimeError("HubAuthority.record_code_package_publication requires HubAuthority.id")

    publication = await HubCodePackagePublication.publish_via_hub_authority(
        hub_authority_id=hub_authority.id,
        package_name=package_name,
        language=language,
        surface=surface,
        channel_key=channel_key,
        revision_id=revision_id,
        artifact_url=artifact_url,
        artifact_sha256=artifact_sha256,
        code_package_id=code_package_id,
        artifact_revision_id=artifact_revision_id,
        producer_provenance_id=producer_provenance_id,
        descriptor_digest=descriptor_digest,
        artifact_size_bytes=artifact_size_bytes,
        media_type=media_type,
        download_handle=download_handle,
        manifest_kind=manifest_kind,
        manifest_relative_path=manifest_relative_path,
        package_root=package_root,
        sources_root=sources_root,
        fqn_prefix=fqn_prefix,
        version=version,
        published_at_utc=published_at_utc,
        metadata=metadata,
    )
    append_if_missing(hub_authority.code_package_publications, publication)
    return publication
    # --- AWARE: LOGIC END record_code_package_publication


async def publish_code_package(
    hub_authority: HubAuthority,
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
    metadata: JsonObject = JsonObject(),
) -> HubCodePackagePublication:
    """
    Publish one CodePackage artifact lock into Hub authority truth.

    Contract:
    - This is the king Hub model for package distribution.
    - CodePackage remains Code-owned semantic package truth.
    - Hub owns channel heads, artifact locks, provenance, and publication receipts.
    """

    # --- AWARE: LOGIC START publish_code_package
    package_name_norm = clean_required(package_name, "package_name")
    revision_key = clean_required(revision_id, "revision_id")
    artifact_url_norm = clean_required(artifact_url, "artifact_url")
    artifact_sha256_norm = clean_required(artifact_sha256, "artifact_sha256")
    channel_key_norm = clean_required(channel_key, "channel_key")
    language_key = enum_value(language)
    surface_key = enum_value(surface)
    artifact_family = "code-package"
    artifact_key = f"{language_key}:{surface_key}:{package_name_norm}"
    selector_key = f"{package_name_norm}:{language_key}:{surface_key}"
    target_ref = f"code-package:{package_name_norm}"
    provenance_key_norm = derived_provenance_key(
        explicit_key=provenance_key,
        revision_id=revision_key,
        producer_revision_id=producer_revision_id,
        source_revision_kind=source_revision_kind,
        source_revision_id=source_revision_id,
        materialization_ref=materialization_ref,
        build_ref=build_ref,
    )

    provenance = await HubProducerProvenance.build(
        producer_kind=producer_kind,
        producer_key=producer_key,
        provenance_key=provenance_key_norm,
        producer_revision_id=producer_revision_id,
        source_revision_id=source_revision_id,
        source_revision_kind=source_revision_kind,
        materialization_ref=materialization_ref,
        build_ref=build_ref,
        metadata=metadata,
    )
    session = handler_session_or_none()
    artifact_id = (
        stable_hub_artifact_id(
            hub_authority_id=hub_authority.id,
            artifact_family=artifact_family,
            artifact_key=artifact_key,
        )
        if hub_authority.id is not None
        else None
    )
    artifact_already_committed = (
        session.imap_get(HubArtifact, artifact_id) is not None
        if session is not None and artifact_id is not None
        else False
    )
    artifact = await ensure_artifact(
        hub_authority,
        artifact_family=artifact_family,
        artifact_key=artifact_key,
        title=package_name_norm,
        media_type=media_type,
    )
    if artifact_already_committed:
        revision = await artifact.publish_revision(
            revision_id=revision_key,
            payload_url=artifact_url_norm,
            payload_sha256=artifact_sha256_norm,
            selector_key=selector_key,
            target_ref=target_ref,
            media_type=media_type,
            size_bytes=artifact_size_bytes,
            producer_provenance_id=provenance.id,
            published_at_utc=published_at_utc,
            metadata=metadata,
        )
    else:
        revision = await HubArtifactRevision.build_via_hub_artifact(
            hub_artifact_id=artifact.id,
            revision_id=revision_key,
            payload_url=artifact_url_norm,
            payload_sha256=artifact_sha256_norm,
            selector_key=selector_key,
            target_ref=target_ref,
            media_type=media_type,
            size_bytes=artifact_size_bytes,
            producer_provenance_id=provenance.id,
            published_at_utc=published_at_utc,
            metadata=metadata,
        )
        append_if_missing(artifact.revisions, revision)
    append_if_missing(artifact.revisions, revision)
    revision.producer_provenance = provenance
    revision.producer_provenance_id = provenance.id
    publication = await record_code_package_publication(
        hub_authority,
        package_name=package_name_norm,
        language=language,
        surface=surface,
        revision_id=revision_key,
        artifact_url=artifact_url_norm,
        artifact_sha256=artifact_sha256_norm,
        channel_key=channel_key_norm,
        code_package_id=code_package_id,
        artifact_revision_id=revision.id,
        producer_provenance_id=provenance.id,
        descriptor_digest=descriptor_digest,
        artifact_size_bytes=artifact_size_bytes,
        media_type=media_type,
        download_handle=download_handle,
        manifest_kind=manifest_kind,
        manifest_relative_path=manifest_relative_path,
        package_root=package_root,
        sources_root=sources_root,
        fqn_prefix=fqn_prefix,
        version=version,
        published_at_utc=published_at_utc,
        metadata=metadata,
    )
    publication.artifact_revision = revision
    publication.artifact_revision_id = revision.id
    publication.producer_provenance = provenance
    publication.producer_provenance_id = provenance.id
    channel = await ensure_channel(hub_authority, channel_key=channel_key_norm)
    head = await HubChannelHead.build_via_hub_channel(
        hub_channel_id=channel.id,
        artifact_family=artifact_family,
        artifact_key=artifact_key,
        revision_id=revision_key,
        selector_key=selector_key,
        artifact_revision_id=revision.id,
        code_package_publication_id=publication.id,
        updated_at_utc=published_at_utc,
    )
    append_if_missing(channel.heads, head)
    head.artifact_revision = revision
    head.artifact_revision_id = revision.id
    head.code_package_publication = publication
    head.code_package_publication_id = publication.id
    receipt = await record_receipt(
        hub_authority,
        receipt_key=idempotency_key
        or receipt_key_for(
            operation="publish_code_package",
            artifact_family=artifact_family,
            artifact_key=artifact_key,
            revision_id=revision_key,
        ),
        operation="publish_code_package",
        status=HubPublicationReceiptStatus.accepted,
        publisher_execution_id=publisher_execution_id,
        idempotency_key=idempotency_key,
        artifact_revision_id=revision.id,
        code_package_publication_id=publication.id,
        recorded_at_utc=published_at_utc,
        detail=metadata,
    )
    receipt.artifact_revision = revision
    receipt.artifact_revision_id = revision.id
    receipt.code_package_publication = publication
    receipt.code_package_publication_id = publication.id
    return publication
    # --- AWARE: LOGIC END publish_code_package


async def record_receipt(
    hub_authority: HubAuthority,
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
    detail: JsonObject = JsonObject(),
) -> HubPublicationReceipt:
    """
    Record one Hub-owned authority receipt.
    """

    # --- AWARE: LOGIC START record_receipt
    if hub_authority.id is None:
        raise RuntimeError("HubAuthority.record_receipt requires HubAuthority.id")

    receipt = await HubPublicationReceipt.build_via_hub_authority(
        hub_authority_id=hub_authority.id,
        receipt_key=receipt_key,
        operation=operation,
        status=status,
        publisher_execution_id=publisher_execution_id,
        idempotency_key=idempotency_key,
        artifact_revision_id=artifact_revision_id,
        code_package_publication_id=code_package_publication_id,
        authority_source_url=authority_source_url,
        message=message,
        recorded_at_utc=recorded_at_utc,
        detail=detail,
    )
    append_if_missing(hub_authority.receipts, receipt)
    return receipt
    # --- AWARE: LOGIC END record_receipt
