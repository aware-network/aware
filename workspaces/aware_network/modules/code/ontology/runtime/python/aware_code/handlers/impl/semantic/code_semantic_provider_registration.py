from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.semantic.code_semantic_package_binding import CodeSemanticPackageBinding
from aware_code_ontology.semantic.code_semantic_provider_registration import CodeSemanticProviderRegistration

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from typing import TypeVar

from aware_code.stable_ids import stable_code_semantic_provider_registration_id
from aware_code_ontology.module.code_module import CodeModule
from aware_meta.runtime.handler_context import current_handler_session

_T = TypeVar("_T")


def _normalize_required(value: str | None, *, field_name: str) -> str:
    normalized = (value or "").strip()
    if not normalized:
        raise RuntimeError(f"CodeSemanticProviderRegistration requires non-empty {field_name}")
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
    code_module_id: UUID, provider_key: str, semantic_contract_module: str | None = None, status: str = "registered"
) -> CodeSemanticProviderRegistration:
    """
    Register Code-owned semantic contract provider participation.

    Contract:
    - Provider registration is anchored to CodeModule truth, not
      WorkspaceCodeModulePin.
    - Package-slot participation is recorded by CodeSemanticPackageBinding.
    - Workspace consumes resolved provider records through revision
      receipts only.
    """

    # --- AWARE: LOGIC START build
    normalized_provider_key = _normalize_required(provider_key, field_name="provider_key")
    registration_id = stable_code_semantic_provider_registration_id(
        code_module_id=code_module_id,
        provider_key=normalized_provider_key,
    )
    session = current_handler_session()
    code_module = session.imap_get(CodeModule, code_module_id)
    if code_module is None:
        raise RuntimeError(
            "CodeSemanticProviderRegistration requires existing CodeModule in the "
            f"active session: code_module_id={code_module_id}"
        )
    normalized_status = (status or "").strip() or "registered"
    existing = session.imap_get(CodeSemanticProviderRegistration, registration_id)
    if existing is not None:
        if existing.code_module_id != code_module_id:
            raise RuntimeError(
                "CodeSemanticProviderRegistration payload mismatch for existing "
                f"registration: code_semantic_provider_registration_id={registration_id}"
            )
        existing.code_module = code_module
        existing.provider_key = normalized_provider_key
        existing.semantic_contract_module = _normalize_optional(semantic_contract_module)
        existing.status = normalized_status
        return existing

    return CodeSemanticProviderRegistration(
        id=registration_id,
        code_module=code_module,
        code_module_id=code_module_id,
        provider_key=normalized_provider_key,
        semantic_contract_module=_normalize_optional(semantic_contract_module),
        status=normalized_status,
    )
    # --- AWARE: LOGIC END build


async def bind_semantic_package(
    code_semantic_provider_registration: CodeSemanticProviderRegistration,
    code_package_id: UUID,
    module_package_id: str,
    semantic_contract_role: str,
    semantic_contract_name: str,
    code_package_config_key: str | None = None,
    code_module_name: str | None = None,
    module_package_kind: str | None = None,
    module_relative_package_root: str | None = None,
    manifest_relative_path: str | None = None,
    semantic_contract_module: str | None = None,
    owned_manifest_kinds: list[str] = [],
    capabilities: list[str] = [],
    status: str = "bound",
) -> CodeSemanticPackageBinding:
    """
    Attach one Code-owned semantic package binding under this provider.
    """

    # --- AWARE: LOGIC START bind_semantic_package
    created = await CodeSemanticPackageBinding.build_via_code_semantic_provider_registration(
        code_semantic_provider_registration_id=code_semantic_provider_registration.id,
        code_package_id=code_package_id,
        module_package_id=module_package_id,
        semantic_contract_role=semantic_contract_role,
        semantic_contract_name=semantic_contract_name,
        code_package_config_key=code_package_config_key,
        code_module_name=code_module_name,
        module_package_kind=module_package_kind,
        module_relative_package_root=module_relative_package_root,
        manifest_relative_path=manifest_relative_path,
        semantic_contract_module=semantic_contract_module,
        owned_manifest_kinds=owned_manifest_kinds,
        capabilities=capabilities,
        status=status,
    )
    return _append_unique_by_id(
        code_semantic_provider_registration.semantic_package_bindings,
        created,
    )
    # --- AWARE: LOGIC END bind_semantic_package
