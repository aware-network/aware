from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Api Ontology
from aware_api_ontology.api.api_package_language_package import ApiPackageLanguagePackage

# Code
from aware_code.types import JsonArray

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_api_ontology.stable_ids import stable_api_package_language_package_id

# --- AWARE: USER_IMPORTS END


async def build_via_api_package(
    api_package_id: UUID,
    code_package_id: UUID,
    package_name: str,
    language: CodeLanguage,
    import_root: str,
    manifest_relative_path: str,
    package_root: str = ".",
    role: str = "public_package",
    output_key: str = "python.public_package",
    include_paths: JsonArray = JsonArray(),
    exclude_paths: JsonArray = JsonArray(),
) -> ApiPackageLanguagePackage:
    """
    Create one API-owned generated language package declaration.

    Contract:
    - Parent `ApiPackage` scope is injected by propagation.
    - Identity is keyed by the attached generated CodePackage.
    - The payload is the canonical import/install contract for API consumers.
    - Consumers must not infer API generated packages from local layout or
      `aware.api.toml` target JSON alone.
    """

    # --- AWARE: LOGIC START build_via_api_package
    normalized_package_name = (package_name or "").strip()
    normalized_import_root = (import_root or "").strip()
    normalized_manifest_path = (manifest_relative_path or "").strip()
    if not normalized_package_name:
        raise RuntimeError("ApiPackageLanguagePackage.build_via_api_package requires " "non-empty package_name")
    if not normalized_import_root:
        raise RuntimeError("ApiPackageLanguagePackage.build_via_api_package requires " "non-empty import_root")
    if not normalized_manifest_path:
        raise RuntimeError(
            "ApiPackageLanguagePackage.build_via_api_package requires " "non-empty manifest_relative_path"
        )
    return ApiPackageLanguagePackage(
        id=stable_api_package_language_package_id(
            api_package_id=api_package_id,
            code_package_id=code_package_id,
        ),
        api_package_id=api_package_id,
        code_package_id=code_package_id,
        package_name=normalized_package_name,
        language=language,
        import_root=normalized_import_root,
        manifest_relative_path=normalized_manifest_path,
        package_root=(package_root or "").strip() or ".",
        role=(role or "").strip() or "public_package",
        output_key=(output_key or "").strip() or "python.public_package",
        include_paths=JsonArray(include_paths or []),
        exclude_paths=JsonArray(exclude_paths or []),
    )
    # --- AWARE: LOGIC END build_via_api_package
