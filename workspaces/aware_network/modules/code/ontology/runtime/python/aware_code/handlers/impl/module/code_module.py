from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.module.code_module import CodeModule
from aware_code_ontology.module.code_module_code_package import CodeModuleCodePackage
from aware_code_ontology.module.code_module_dependence import CodeModuleDependence

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code.stable_ids import stable_code_module_id
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build(
    name: str,
    languages: list[CodeLanguage],
    aware_module_version: int = 1,
    manifest_relative_path: str = "aware.module.toml",
    manifest_hash: str | None = None,
) -> CodeModule:
    """
    Create deterministic CodeModule identity by name.
    """

    # --- AWARE: LOGIC START build
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("CodeModule.build requires non-empty name")
    if aware_module_version < 1:
        raise RuntimeError("CodeModule.build requires positive aware_module_version")
    normalized_manifest_relative_path = (manifest_relative_path or "").strip()
    if not normalized_manifest_relative_path:
        raise RuntimeError("CodeModule.build requires non-empty manifest_relative_path")
    normalized_manifest_hash = (manifest_hash or "").strip() or None

    def _normalize_languages(values: object) -> list[CodeLanguage]:
        ordered: dict[str, CodeLanguage] = {}
        if isinstance(values, list):
            for value in values:
                if not isinstance(value, CodeLanguage):
                    continue
                _ = ordered.setdefault(value.value, value)
        return [ordered[key] for key in sorted(ordered)]

    module_id = stable_code_module_id(name=normalized_name)
    session = current_handler_session()
    normalized_languages = _normalize_languages(languages)
    existing = session.imap_get(CodeModule, module_id)
    if existing is not None:
        existing_name = (existing.name or "").strip()
        if existing_name != normalized_name:
            raise RuntimeError(f"CodeModule.build payload mismatch for existing module: code_module_id={module_id}")
        if existing.aware_module_version != aware_module_version:
            existing.aware_module_version = aware_module_version
        if existing.manifest_relative_path != normalized_manifest_relative_path:
            existing.manifest_relative_path = normalized_manifest_relative_path
        if normalized_manifest_hash is not None:
            existing.manifest_hash = normalized_manifest_hash
        if normalized_languages:
            merged: dict[str, CodeLanguage] = {language.value: language for language in existing.languages}
            for language in normalized_languages:
                _ = merged.setdefault(language.value, language)
            existing.languages = [merged[key] for key in sorted(merged)]
        return existing

    return CodeModule(
        id=module_id,
        name=normalized_name,
        languages=normalized_languages,
        aware_module_version=aware_module_version,
        manifest_relative_path=normalized_manifest_relative_path,
        manifest_hash=normalized_manifest_hash,
    )
    # --- AWARE: LOGIC END build


async def create_dependency(code_module: CodeModule, name: str) -> CodeModuleDependence:
    """
    Create a deterministic dependency edge to another CodeModule.
    """

    # --- AWARE: LOGIC START create_dependency
    code_module_id = code_module.id
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("CodeModule.create_dependency requires non-empty name")

    created = await CodeModuleDependence.build_via_code_module(
        code_module_id=code_module_id,
        name=normalized_name,
    )
    for existing in code_module.dependences:
        if existing.id == created.id:
            return existing
    code_module.dependences.append(created)
    return created
    # --- AWARE: LOGIC END create_dependency


async def attach_package(
    code_module: CodeModule,
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
    Attach an existing CodePackage under this CodeModule.

    Contract:
    - `CodeModule` is a semantic package bundle only.
    - `CodePackage` remains standalone package truth.
    - `CodeModuleCodePackage` carries module-local package slot metadata so
      Workspace can mount resolved module packages without owning semantic
      package-family vocabulary.
    """

    # --- AWARE: LOGIC START attach_package
    created_package = await CodeModuleCodePackage.build_via_code_module(
        code_module_id=code_module.id,
        code_package_id=code_package_id,
        module_package_id=module_package_id,
        module_package_kind=module_package_kind,
        module_relative_package_root=module_relative_package_root,
        manifest_relative_path=manifest_relative_path,
        visibility=visibility,
        semantic_contract_role=semantic_contract_role,
        semantic_contract_name=semantic_contract_name,
        semantic_contract_provider_key=semantic_contract_provider_key,
        semantic_contract_module=semantic_contract_module,
        semantic_contract_owns_manifest_kinds=semantic_contract_owns_manifest_kinds,
        semantic_contract_capabilities=semantic_contract_capabilities,
        mirrors_ontology=mirrors_ontology,
    )
    for existing in code_module.code_module_code_packages:
        if existing.id == created_package.id:
            return existing
    code_module.code_module_code_packages.append(created_package)
    return created_package
    # --- AWARE: LOGIC END attach_package
