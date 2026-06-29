from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.semantic.code_semantic_package_binding import CodeSemanticPackageBinding

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code.stable_ids import stable_code_semantic_package_binding_id
from aware_code_ontology.package.code_package import CodePackage
from aware_meta.runtime.handler_context import current_handler_session


def _normalize_required(value: str | None, *, field_name: str) -> str:
    normalized = (value or "").strip()
    if not normalized:
        raise RuntimeError(f"CodeSemanticPackageBinding requires non-empty {field_name}")
    return normalized


def _normalize_optional(value: str | None) -> str | None:
    return (value or "").strip() or None


def _normalize_string_list(values: list[str]) -> list[str]:
    ordered: dict[str, str] = {}
    for value in values or []:
        normalized = (value or "").strip()
        if normalized:
            ordered.setdefault(normalized, normalized)
    return [ordered[key] for key in sorted(ordered)]


# --- AWARE: USER_IMPORTS END


async def build_via_code_semantic_provider_registration(
    code_semantic_provider_registration_id: UUID,
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
    Record one Code-owned package-slot semantic contract binding.

    Contract:
    - The source CodePackage remains standalone package truth.
    - Semantic fields are derived from CodePackageConfig and
      CodeModuleCodePackage package-slot metadata.
    - Workspace may reference this binding in resolution receipts, but does
      not author or duplicate the binding.
    """

    # --- AWARE: LOGIC START build_via_code_semantic_provider_registration
    normalized_module_package_id = _normalize_required(module_package_id, field_name="module_package_id")
    normalized_semantic_contract_role = _normalize_required(semantic_contract_role, field_name="semantic_contract_role")
    normalized_semantic_contract_name = _normalize_required(semantic_contract_name, field_name="semantic_contract_name")
    binding_id = stable_code_semantic_package_binding_id(
        code_semantic_provider_registration_id=code_semantic_provider_registration_id,
        code_package_id=code_package_id,
        module_package_id=normalized_module_package_id,
        semantic_contract_name=normalized_semantic_contract_name,
        semantic_contract_role=normalized_semantic_contract_role,
    )
    session = current_handler_session()
    code_package = session.imap_get(CodePackage, code_package_id)
    if code_package is None:
        raise RuntimeError(
            "CodeSemanticPackageBinding requires existing CodePackage in the "
            f"active session: code_package_id={code_package_id}"
        )
    normalized_owned_manifest_kinds = _normalize_string_list(owned_manifest_kinds)
    normalized_capabilities = _normalize_string_list(capabilities)
    normalized_status = (status or "").strip() or "bound"
    existing = session.imap_get(CodeSemanticPackageBinding, binding_id)
    if existing is not None:
        if (
            existing.code_semantic_provider_registration_id != code_semantic_provider_registration_id
            or existing.code_package_id != code_package_id
        ):
            raise RuntimeError(
                "CodeSemanticPackageBinding payload mismatch for existing binding: "
                f"code_semantic_package_binding_id={binding_id}"
            )
        existing.code_package = code_package
        existing.module_package_id = normalized_module_package_id
        existing.semantic_contract_role = normalized_semantic_contract_role
        existing.semantic_contract_name = normalized_semantic_contract_name
        existing.code_package_config_key = _normalize_optional(code_package_config_key)
        existing.code_module_name = _normalize_optional(code_module_name)
        existing.module_package_kind = _normalize_optional(module_package_kind)
        existing.module_relative_package_root = _normalize_optional(module_relative_package_root)
        existing.manifest_relative_path = _normalize_optional(manifest_relative_path)
        existing.semantic_contract_module = _normalize_optional(semantic_contract_module)
        existing.owned_manifest_kinds = normalized_owned_manifest_kinds
        existing.capabilities = normalized_capabilities
        existing.status = normalized_status
        return existing

    return CodeSemanticPackageBinding(
        id=binding_id,
        code_semantic_provider_registration_id=code_semantic_provider_registration_id,
        code_package=code_package,
        code_package_id=code_package_id,
        module_package_id=normalized_module_package_id,
        semantic_contract_role=normalized_semantic_contract_role,
        semantic_contract_name=normalized_semantic_contract_name,
        code_package_config_key=_normalize_optional(code_package_config_key),
        code_module_name=_normalize_optional(code_module_name),
        module_package_kind=_normalize_optional(module_package_kind),
        module_relative_package_root=_normalize_optional(module_relative_package_root),
        manifest_relative_path=_normalize_optional(manifest_relative_path),
        semantic_contract_module=_normalize_optional(semantic_contract_module),
        owned_manifest_kinds=normalized_owned_manifest_kinds,
        capabilities=normalized_capabilities,
        status=normalized_status,
    )
    # --- AWARE: LOGIC END build_via_code_semantic_provider_registration
