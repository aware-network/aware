from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.module.code_module_code_package import CodeModuleCodePackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code.stable_ids import stable_code_module_code_package_id
from aware_code_ontology.package.code_package import CodePackage
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_code_module(
    code_module_id: UUID,
    code_package_id: UUID,
    module_package_id: str | None = None,
    module_package_kind: str | None = None,
    module_relative_package_root: str | None = None,
    manifest_relative_path: str | None = None,
    visibility: str = "module",
    semantic_contract_role: str | None = None,
    semantic_contract_name: str | None = None,
    semantic_contract_provider_key: str | None = None,
    semantic_contract_module: str | None = None,
    semantic_contract_owns_manifest_kinds: list[str] = [],
    semantic_contract_capabilities: list[str] = [],
    mirrors_ontology: bool = False,
) -> CodeModuleCodePackage:
    """
    Attach an existing standalone CodePackage under this CodeModule.

    Contract:
    - `CodePackage` remains standalone raw/source package identity.
    - `CodeModuleCodePackage` is the module-local package slot emitted from
      `aware.module.toml` package inventory.
    - Semantic contract fields are declarative package-role metadata only;
      executable bindings remain package-local contract/runtime truth.
    """

    # --- AWARE: LOGIC START build_via_code_module
    def _normalize_optional(value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    def _normalize_list(values: list[str]) -> list[str]:
        ordered: dict[str, str] = {}
        for value in values:
            normalized = value.strip()
            if normalized:
                _ = ordered.setdefault(normalized, normalized)
        return [ordered[key] for key in sorted(ordered)]

    normalized_module_relative_package_root = _normalize_optional(module_relative_package_root)
    normalized_manifest_relative_path = _normalize_optional(manifest_relative_path)
    normalized_visibility = (visibility or "").strip() or "module"
    normalized_semantic_contract_role = _normalize_optional(semantic_contract_role)
    normalized_semantic_contract_name = _normalize_optional(semantic_contract_name)
    normalized_semantic_contract_provider_key = _normalize_optional(semantic_contract_provider_key)
    normalized_semantic_contract_module = _normalize_optional(semantic_contract_module)
    normalized_semantic_contract_owns_manifest_kinds = _normalize_list(semantic_contract_owns_manifest_kinds)
    normalized_semantic_contract_capabilities = _normalize_list(semantic_contract_capabilities)

    session = current_handler_session()
    code_package = session.imap_get(CodePackage, code_package_id)
    if code_package is None:
        raise RuntimeError(
            "CodeModuleCodePackage.build_via_code_module requires existing CodePackage "
            "in the active session identity map: "
            f"code_package_id={code_package_id}"
        )

    assoc_id = stable_code_module_code_package_id(
        code_module_id=code_module_id,
        code_package_id=code_package_id,
    )
    existing = session.imap_get(CodeModuleCodePackage, assoc_id)
    if existing is not None:
        if existing.code_module_id != code_module_id or existing.code_package_id != code_package_id:
            raise RuntimeError(
                "CodeModuleCodePackage.build_via_code_module payload mismatch for existing association: "
                f"code_module_code_package_id={assoc_id}"
            )
        if existing.code_package is None:
            existing.code_package = code_package
        if module_package_id is not None:
            existing.module_package_id = module_package_id
        if module_package_kind is not None:
            existing.module_package_kind = module_package_kind
        if normalized_module_relative_package_root is not None:
            existing.module_relative_package_root = normalized_module_relative_package_root
        if normalized_manifest_relative_path is not None:
            existing.manifest_relative_path = normalized_manifest_relative_path
        if normalized_semantic_contract_role is not None:
            existing.semantic_contract_role = normalized_semantic_contract_role
        if normalized_semantic_contract_name is not None:
            existing.semantic_contract_name = normalized_semantic_contract_name
        if normalized_semantic_contract_provider_key is not None:
            existing.semantic_contract_provider_key = normalized_semantic_contract_provider_key
        if normalized_semantic_contract_module is not None:
            existing.semantic_contract_module = normalized_semantic_contract_module
        if normalized_semantic_contract_owns_manifest_kinds:
            existing.semantic_contract_owns_manifest_kinds = normalized_semantic_contract_owns_manifest_kinds
        if normalized_semantic_contract_capabilities:
            existing.semantic_contract_capabilities = normalized_semantic_contract_capabilities
        if existing.visibility != normalized_visibility:
            existing.visibility = normalized_visibility
        if existing.mirrors_ontology != mirrors_ontology:
            existing.mirrors_ontology = mirrors_ontology
        return existing

    return CodeModuleCodePackage(
        id=assoc_id,
        code_module_id=code_module_id,
        code_package=code_package,
        code_package_id=code_package_id,
        module_package_id=module_package_id,
        module_package_kind=module_package_kind,
        module_relative_package_root=normalized_module_relative_package_root,
        manifest_relative_path=normalized_manifest_relative_path,
        visibility=normalized_visibility,
        semantic_contract_role=normalized_semantic_contract_role,
        semantic_contract_name=normalized_semantic_contract_name,
        semantic_contract_provider_key=normalized_semantic_contract_provider_key,
        semantic_contract_module=normalized_semantic_contract_module,
        semantic_contract_owns_manifest_kinds=normalized_semantic_contract_owns_manifest_kinds,
        semantic_contract_capabilities=normalized_semantic_contract_capabilities,
        mirrors_ontology=mirrors_ontology,
    )
    # --- AWARE: LOGIC END build_via_code_module
