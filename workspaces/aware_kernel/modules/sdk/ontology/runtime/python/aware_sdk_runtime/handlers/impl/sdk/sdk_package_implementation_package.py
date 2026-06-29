from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonArray

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Sdk Ontology
from aware_sdk_ontology.sdk.sdk_package_implementation_package import SdkPackageImplementationPackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_sdk_ontology.stable_ids import stable_sdk_package_implementation_package_id

# --- AWARE: USER_IMPORTS END


async def build_via_sdk_package(
    sdk_package_id: UUID,
    code_package_id: UUID,
    package_name: str,
    language: CodeLanguage,
    import_root: str,
    manifest_relative_path: str,
    package_root: str = ".",
    entrypoint: str | None = None,
    role: str = "public_package",
    include_paths: JsonArray = JsonArray(),
    exclude_paths: JsonArray = JsonArray(),
) -> SdkPackageImplementationPackage:
    """
    Create one SDK-owned language implementation package declaration.

    Contract:
    - Parent `SdkPackage` scope is injected by propagation.
    - Identity is keyed by the attached implementation `CodePackage`.
    - The payload is the canonical import/install contract for SDK consumers.
    - Consumers must not infer SDK implementation packages from local layout or target JSON alone.
    """

    # --- AWARE: LOGIC START build_via_sdk_package
    normalized_package_name = (package_name or "").strip()
    normalized_import_root = (import_root or "").strip()
    normalized_manifest_path = (manifest_relative_path or "").strip()
    if not normalized_package_name:
        raise RuntimeError("SdkPackageImplementationPackage.build_via_sdk_package requires " "non-empty package_name")
    if not normalized_import_root:
        raise RuntimeError("SdkPackageImplementationPackage.build_via_sdk_package requires " "non-empty import_root")
    if not normalized_manifest_path:
        raise RuntimeError(
            "SdkPackageImplementationPackage.build_via_sdk_package requires " "non-empty manifest_relative_path"
        )
    return SdkPackageImplementationPackage(
        id=stable_sdk_package_implementation_package_id(
            sdk_package_id=sdk_package_id,
            code_package_id=code_package_id,
        ),
        sdk_package_id=sdk_package_id,
        code_package_id=code_package_id,
        package_name=normalized_package_name,
        language=language,
        import_root=normalized_import_root,
        manifest_relative_path=normalized_manifest_path,
        package_root=(package_root or "").strip() or ".",
        entrypoint=(entrypoint or "").strip() or None,
        role=(role or "").strip() or "public_package",
        include_paths=JsonArray(include_paths or []),
        exclude_paths=JsonArray(exclude_paths or []),
    )
    # --- AWARE: LOGIC END build_via_sdk_package
