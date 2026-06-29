from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.semantic.code_semantic_contract_profile import CodeSemanticContractProfile
from aware_code_ontology.semantic.code_semantic_contract_profile_import import CodeSemanticContractProfileImport

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from typing import TypeVar

from aware_code.stable_ids import stable_code_semantic_contract_profile_id
from aware_code_ontology.semantic.code_semantic_provider_registration import (
    CodeSemanticProviderRegistration,
)
from aware_meta.runtime.handler_context import current_handler_session

_T = TypeVar("_T")


def _normalize_required(value: str | None, *, field_name: str) -> str:
    normalized = (value or "").strip()
    if not normalized:
        raise RuntimeError(f"CodeSemanticContractProfile requires non-empty {field_name}")
    return normalized


def _normalize_optional(value: str | None) -> str | None:
    return (value or "").strip() or None


def _append_unique_by_id(items: list[_T], item: _T) -> _T:
    item_id = getattr(item, "id", None)
    for existing in items:
        if getattr(existing, "id", None) == item_id:
            return existing
    items.append(item)
    return item


# --- AWARE: USER_IMPORTS END


async def build(
    profile_key: str,
    title: str | None = None,
    description: str | None = None,
    semantic_provider_registration_ids: list[UUID] = [],
    status: str = "active",
) -> CodeSemanticContractProfile:
    """
    Build one Code-owned semantic contract profile.

    Contract:
    - Profiles group CodeSemanticProviderRegistration entries.
    - Profiles may compose other CodeSemanticContractProfile entries.
    - Workspace selects and snapshots resolved profiles but does not author
      provider registration or package binding truth.
    """

    # --- AWARE: LOGIC START build
    normalized_profile_key = _normalize_required(profile_key, field_name="profile_key")
    profile_id = stable_code_semantic_contract_profile_id(
        profile_key=normalized_profile_key,
    )
    session = current_handler_session()
    registrations: list[CodeSemanticProviderRegistration] = []
    for registration_id in semantic_provider_registration_ids or []:
        registration = session.imap_get(
            CodeSemanticProviderRegistration,
            registration_id,
        )
        if registration is None:
            raise RuntimeError(
                "CodeSemanticContractProfile requires existing "
                "CodeSemanticProviderRegistration in the active session: "
                f"semantic_provider_registration_id={registration_id}"
            )
        registrations.append(registration)
    normalized_status = (status or "").strip() or "active"
    existing = session.imap_get(CodeSemanticContractProfile, profile_id)
    if existing is not None:
        existing.profile_key = normalized_profile_key
        existing.title = _normalize_optional(title)
        existing.description = _normalize_optional(description)
        existing.status = normalized_status
        if registrations:
            merged = {entry.id: entry for entry in existing.semantic_provider_registrations}
            merged.update({entry.id: entry for entry in registrations})
            existing.semantic_provider_registrations = list(merged.values())
        return existing

    return CodeSemanticContractProfile(
        id=profile_id,
        profile_key=normalized_profile_key,
        title=_normalize_optional(title),
        description=_normalize_optional(description),
        semantic_provider_registrations=registrations,
        status=normalized_status,
    )
    # --- AWARE: LOGIC END build


async def attach_semantic_provider(
    code_semantic_contract_profile: CodeSemanticContractProfile, semantic_provider_registration_id: UUID
) -> CodeSemanticContractProfile:
    """
    Attach one existing CodeSemanticProviderRegistration to this profile.
    """

    # --- AWARE: LOGIC START attach_semantic_provider
    session = current_handler_session()
    registration = session.imap_get(
        CodeSemanticProviderRegistration,
        semantic_provider_registration_id,
    )
    if registration is None:
        raise RuntimeError(
            "CodeSemanticContractProfile.attach_semantic_provider requires existing "
            "CodeSemanticProviderRegistration in the active session: "
            f"semantic_provider_registration_id={semantic_provider_registration_id}"
        )
    _append_unique_by_id(
        code_semantic_contract_profile.semantic_provider_registrations,
        registration,
    )
    return code_semantic_contract_profile
    # --- AWARE: LOGIC END attach_semantic_provider


async def import_profile(
    code_semantic_contract_profile: CodeSemanticContractProfile,
    imported_profile_id: UUID,
    import_key: str,
    required: bool = True,
    status: str = "active",
) -> CodeSemanticContractProfileImport:
    """
    Compose this Code semantic contract profile with another Code profile.
    """

    # --- AWARE: LOGIC START import_profile
    created = await CodeSemanticContractProfileImport.build_via_code_semantic_contract_profile(
        code_semantic_contract_profile_id=code_semantic_contract_profile.id,
        imported_profile_id=imported_profile_id,
        import_key=import_key,
        required=required,
        status=status,
    )
    return _append_unique_by_id(code_semantic_contract_profile.profile_imports, created)
    # --- AWARE: LOGIC END import_profile
