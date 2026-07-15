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
from aware_hub_ontology.hub.hub_code_package_publication import HubCodePackagePublication

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_hub.handlers.impl.hub._helpers import (
    clean_optional,
    clean_required,
    enum_value,
    handler_session_or_none,
    json_object,
)
from aware_hub.stable_ids import stable_hub_code_package_publication_id
from aware_code_ontology.package.code_package import CodePackage
from aware_hub_ontology.hub.hub_artifact import HubArtifactRevision
from aware_hub_ontology.hub.hub_producer_provenance import HubProducerProvenance

# --- AWARE: USER_IMPORTS END


async def publish_via_hub_authority(
    hub_authority_id: UUID,
    package_name: str,
    language: CodeLanguage,
    surface: str,
    channel_key: str,
    revision_id: str,
    artifact_url: str,
    artifact_sha256: str,
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
    Create one Hub CodePackage publication.

    Contract:
    - CodePackage semantic truth remains Code-owned.
    - Hub publication records artifact lock, channel, provenance, and receipt truth.
    """

    # --- AWARE: LOGIC START publish_via_hub_authority
    package_name_norm = clean_required(package_name, "package_name")
    channel_key_norm = clean_required(channel_key, "channel_key")
    revision_key = clean_required(revision_id, "revision_id")
    artifact_url_norm = clean_required(artifact_url, "artifact_url")
    artifact_sha256_norm = clean_required(artifact_sha256, "artifact_sha256")
    publication_id = stable_hub_code_package_publication_id(
        hub_authority_id=hub_authority_id,
        channel_key=channel_key_norm,
        language=enum_value(language),
        package_name=package_name_norm,
        revision_id=revision_key,
        surface=enum_value(surface),
    )

    session = handler_session_or_none()
    if session is not None:
        existing = session.imap_get(HubCodePackagePublication, publication_id)
        if existing is not None:
            if (
                existing.hub_authority_id != hub_authority_id
                or existing.package_name != package_name_norm
                or enum_value(existing.language) != enum_value(language)
                or enum_value(existing.surface) != enum_value(surface)
                or existing.revision_id != revision_key
                or existing.artifact_url != artifact_url_norm
                or existing.artifact_sha256 != artifact_sha256_norm
            ):
                raise RuntimeError(
                    "HubCodePackagePublication.publish_via_hub_authority immutable payload mismatch: "
                    f"hub_code_package_publication_id={publication_id}"
                )
            return existing

    code_package = (
        session.imap_get(CodePackage, code_package_id) if session is not None and code_package_id is not None else None
    )
    artifact_revision = (
        session.imap_get(HubArtifactRevision, artifact_revision_id)
        if session is not None and artifact_revision_id is not None
        else None
    )
    producer_provenance = (
        session.imap_get(HubProducerProvenance, producer_provenance_id)
        if session is not None and producer_provenance_id is not None
        else None
    )

    return HubCodePackagePublication(
        id=publication_id,
        hub_authority_id=hub_authority_id,
        package_name=package_name_norm,
        language=language,
        surface=surface,
        channel_key=channel_key_norm,
        revision_id=revision_key,
        artifact_url=artifact_url_norm,
        artifact_sha256=artifact_sha256_norm,
        code_package=code_package,
        code_package_id=code_package_id,
        artifact_revision=artifact_revision,
        artifact_revision_id=artifact_revision_id,
        producer_provenance=producer_provenance,
        producer_provenance_id=producer_provenance_id,
        descriptor_digest=clean_optional(descriptor_digest),
        artifact_size_bytes=artifact_size_bytes,
        media_type=clean_optional(media_type),
        download_handle=clean_optional(download_handle),
        manifest_kind=manifest_kind,
        manifest_relative_path=clean_optional(manifest_relative_path),
        package_root=clean_optional(package_root),
        sources_root=clean_optional(sources_root),
        fqn_prefix=clean_optional(fqn_prefix),
        version=clean_optional(version),
        published_at_utc=clean_optional(published_at_utc),
        metadata=json_object(metadata),
    )
    # --- AWARE: LOGIC END publish_via_hub_authority
