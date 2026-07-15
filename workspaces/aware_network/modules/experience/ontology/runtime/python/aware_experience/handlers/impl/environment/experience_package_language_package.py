from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonArray

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Experience Ontology
from aware_experience_ontology.environment.experience_package_language_package import ExperiencePackageLanguagePackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Code Ontology
from aware_code_ontology.package.code_package import CodePackage

# Experience Ontology
from aware_experience.stable_ids import stable_experience_package_language_package_id

# Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_experience_package(
    experience_package_id: UUID,
    code_package_id: UUID,
    package_name: str,
    language: CodeLanguage,
    import_root: str,
    manifest_relative_path: str,
    package_root: str = ".",
    sources_root: str | None = None,
    role: str = "view_model_package",
    output_key: str = "experience.language_contract.generated_code_packages",
    include_paths: JsonArray = JsonArray(),
    exclude_paths: JsonArray = JsonArray(),
) -> ExperiencePackageLanguagePackage:
    """
    Create one Experience-owned generated language package declaration.

    Contract:
    - Parent `ExperiencePackage` scope is injected by propagation.
    - Identity is keyed by the attached generated CodePackage.
    - The payload is the canonical import/install contract for Experience consumers.
    - Consumers must not infer generated Experience packages from local layout or
      `aware.experience.toml` targets alone.
    """

    # --- AWARE: LOGIC START build_via_experience_package
    normalized_package_name = (package_name or "").strip()
    if not normalized_package_name:
        raise RuntimeError(
            "ExperiencePackageLanguagePackage.build_via_experience_package " "requires non-empty package_name"
        )
    normalized_import_root = (import_root or "").strip()
    if not normalized_import_root:
        raise RuntimeError(
            "ExperiencePackageLanguagePackage.build_via_experience_package " "requires non-empty import_root"
        )
    normalized_manifest_relative_path = (manifest_relative_path or "").strip()
    if not normalized_manifest_relative_path:
        raise RuntimeError(
            "ExperiencePackageLanguagePackage.build_via_experience_package " "requires non-empty manifest_relative_path"
        )

    bridge_id = stable_experience_package_language_package_id(
        experience_package_id=experience_package_id,
        code_package_id=code_package_id,
    )
    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    resolved_code_package = session.imap_get(CodePackage, code_package_id) if session is not None else None
    if session is not None:
        existing = session.imap_get(ExperiencePackageLanguagePackage, bridge_id)
        if existing is not None:
            if existing.experience_package_id != experience_package_id or existing.code_package_id != code_package_id:
                raise RuntimeError(
                    "ExperiencePackageLanguagePackage.build_via_experience_package "
                    f"payload mismatch for existing bridge: bridge_id={bridge_id}"
                )
            existing.package_name = normalized_package_name
            existing.language = language
            existing.import_root = normalized_import_root
            existing.manifest_relative_path = normalized_manifest_relative_path
            existing.package_root = (package_root or "").strip() or "."
            existing.sources_root = (sources_root or "").strip() or None
            existing.role = (role or "").strip() or "view_model_package"
            existing.output_key = (output_key or "").strip() or "experience.language_contract.generated_code_packages"
            existing.include_paths = JsonArray(include_paths or [])
            existing.exclude_paths = JsonArray(exclude_paths or [])
            existing.code_package = resolved_code_package
            return existing

    return ExperiencePackageLanguagePackage.model_construct(
        id=bridge_id,
        experience_package_id=experience_package_id,
        code_package_id=code_package_id,
        code_package=resolved_code_package,
        package_name=normalized_package_name,
        language=language,
        import_root=normalized_import_root,
        manifest_relative_path=normalized_manifest_relative_path,
        package_root=(package_root or "").strip() or ".",
        sources_root=(sources_root or "").strip() or None,
        role=(role or "").strip() or "view_model_package",
        output_key=((output_key or "").strip() or "experience.language_contract.generated_code_packages"),
        include_paths=JsonArray(include_paths or []),
        exclude_paths=JsonArray(exclude_paths or []),
    )
    # --- AWARE: LOGIC END build_via_experience_package
