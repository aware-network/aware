# GENERATED CODE - DO NOT MODIFY BY HAND
# Canonical stable-id derivations (UUIDv5).
from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

NS_HUB = uuid5(NAMESPACE_URL, "aware://hub/v1")


def stable_hub_artifact_id(*, hub_authority_id: UUID, artifact_family: str, artifact_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: hub_authority_id, artifact_family, artifact_key"""

    artifact_family_norm = (artifact_family or "").casefold().strip()
    artifact_key_norm = (artifact_key or "").casefold().strip()
    return uuid5(NS_HUB, f"aware:hub_artifact:{hub_authority_id}:{artifact_family_norm}:{artifact_key_norm}")


def stable_hub_artifact_revision_id(*, hub_artifact_id: UUID, revision_id: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: hub_artifact_id, revision_id"""

    revision_id_norm = (revision_id or "").casefold().strip()
    return uuid5(NS_HUB, f"aware:hub_artifact_revision:{hub_artifact_id}:{revision_id_norm}")


def stable_hub_authority_id(*, authority_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: authority_key"""

    authority_key_norm = (authority_key or "").casefold().strip()
    return uuid5(NS_HUB, f"aware:hub_authority:{authority_key_norm}")


def stable_hub_channel_id(*, hub_authority_id: UUID, channel_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: hub_authority_id, channel_key"""

    channel_key_norm = (channel_key or "").casefold().strip()
    return uuid5(NS_HUB, f"aware:hub_channel:{hub_authority_id}:{channel_key_norm}")


def stable_hub_channel_head_id(*, hub_channel_id: UUID, artifact_family: str, artifact_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: hub_channel_id, artifact_family, artifact_key"""

    artifact_family_norm = (artifact_family or "").casefold().strip()
    artifact_key_norm = (artifact_key or "").casefold().strip()
    return uuid5(NS_HUB, f"aware:hub_channel_head:{hub_channel_id}:{artifact_family_norm}:{artifact_key_norm}")


def stable_hub_code_package_publication_id(
    *, hub_authority_id: UUID, channel_key: str, language: str, package_name: str, revision_id: str, surface: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: hub_authority_id, channel_key, language, package_name, revision_id, surface"""

    channel_key_norm = (channel_key or "").casefold().strip()
    language_norm = (language or "").casefold().strip()
    package_name_norm = (package_name or "").casefold().strip()
    revision_id_norm = (revision_id or "").casefold().strip()
    surface_norm = (surface or "").casefold().strip()
    return uuid5(
        NS_HUB,
        f"aware:hub_code_package_publication:{hub_authority_id}:{channel_key_norm}:{language_norm}:{package_name_norm}:{revision_id_norm}:{surface_norm}",
    )


def stable_hub_producer_provenance_id(
    *, producer_key: str, producer_kind: str, provenance_key: str = "default"
) -> UUID:
    """Compiler-generated from class-attribute identity keys: producer_key, producer_kind, provenance_key"""

    producer_key_norm = (producer_key or "").casefold().strip()
    producer_kind_norm = (producer_kind or "").casefold().strip()
    provenance_key_norm = (provenance_key or "").casefold().strip() or "default"
    return uuid5(
        NS_HUB, f"aware:hub_producer_provenance:{producer_key_norm}:{producer_kind_norm}:{provenance_key_norm}"
    )


def stable_hub_publication_receipt_id(*, hub_authority_id: UUID, receipt_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: hub_authority_id, receipt_key"""

    receipt_key_norm = (receipt_key or "").casefold().strip()
    return uuid5(NS_HUB, f"aware:hub_publication_receipt:{hub_authority_id}:{receipt_key_norm}")


CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID: dict[str, tuple[str, tuple[str, ...]]] = {
    "2418d971-dcd9-5e3d-badf-d4cc126a2880": (
        "stable_hub_channel_head_id",
        ("hub_channel_id", "artifact_family", "artifact_key"),
    ),
    "2e5bda43-9982-5c0b-90bf-986faf62e150": ("stable_hub_publication_receipt_id", ("hub_authority_id", "receipt_key")),
    "3695e42f-2265-5c76-96e1-de713acdb5b2": (
        "stable_hub_code_package_publication_id",
        ("hub_authority_id", "channel_key", "language", "package_name", "revision_id", "surface"),
    ),
    "5f7af6dc-8ce0-5fda-89d4-269f36c3b2cf": (
        "stable_hub_producer_provenance_id",
        ("producer_key", "producer_kind", "provenance_key"),
    ),
    "6410c1d4-70b1-5564-bd1b-9e5ed9eacc71": (
        "stable_hub_artifact_id",
        ("hub_authority_id", "artifact_family", "artifact_key"),
    ),
    "bb47aa6f-aae9-56b6-9ca6-900c8c39d15b": ("stable_hub_authority_id", ("authority_key",)),
    "dbcf8e91-f0a8-5033-afd9-5c99b2a45cdc": ("stable_hub_channel_id", ("hub_authority_id", "channel_key")),
    "ed890bdc-70ee-5733-9e7b-781bd6a03fe0": ("stable_hub_artifact_revision_id", ("hub_artifact_id", "revision_id")),
}

__all__ = [
    "stable_hub_artifact_id",
    "stable_hub_artifact_revision_id",
    "stable_hub_authority_id",
    "stable_hub_channel_id",
    "stable_hub_channel_head_id",
    "stable_hub_code_package_publication_id",
    "stable_hub_producer_provenance_id",
    "stable_hub_publication_receipt_id",
    "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID",
]
