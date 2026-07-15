from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonArray

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Service Ontology
from aware_service_ontology.service.service_package_implementation_package import ServicePackageImplementationPackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code_ontology.package.code_package import CodePackage
from aware_meta.runtime.handler_context import (
    current_handler_session,
)
from aware_service_ontology.stable_ids import (
    stable_service_package_implementation_package_id,
)


def _normalize_text(value: str | None, *, default: str | None = None) -> str | None:
    token = (value or "").strip()
    return token or default


# --- AWARE: USER_IMPORTS END


async def build_via_service_package(
    service_package_id: UUID,
    code_package_id: UUID,
    package_name: str,
    language: CodeLanguage,
    import_root: str,
    manifest_relative_path: str,
    package_root: str = ".",
    entrypoint: str | None = None,
    role: str = "service_bindings",
    include_paths: JsonArray = JsonArray(),
    exclude_paths: JsonArray = JsonArray(),
) -> ServicePackageImplementationPackage:
    """
    Create one ServicePackage-owned implementation package declaration.

    Contract:
    - Parent `ServicePackage` scope is injected by propagation.
    - Identity is keyed by the attached implementation `CodePackage`.
    - The payload is the canonical runtime import/install contract for ServiceHost activation.
    - Consumers must not infer implementation import roots from service names or workspace layout.
    """

    # --- AWARE: LOGIC START build_via_service_package
    normalized_package_name = _normalize_text(package_name)
    if normalized_package_name is None:
        raise RuntimeError("ServicePackageImplementationPackage.build requires non-empty package_name")
    normalized_import_root = _normalize_text(import_root)
    if normalized_import_root is None:
        raise RuntimeError("ServicePackageImplementationPackage.build requires non-empty import_root")
    normalized_manifest_relative_path = _normalize_text(manifest_relative_path)
    if normalized_manifest_relative_path is None:
        raise RuntimeError("ServicePackageImplementationPackage.build requires non-empty manifest_relative_path")
    normalized_package_root = _normalize_text(package_root, default=".")
    if normalized_package_root is None:
        normalized_package_root = "."
    normalized_role = _normalize_text(role, default="service_bindings")
    if normalized_role is None:
        normalized_role = "service_bindings"
    normalized_entrypoint = _normalize_text(entrypoint)
    include_paths_payload = JsonArray(include_paths or [])
    exclude_paths_payload = JsonArray(exclude_paths or [])

    bridge_id = stable_service_package_implementation_package_id(
        service_package_id=service_package_id,
        code_package_id=code_package_id,
    )
    session = current_handler_session()
    existing = session.imap_get(ServicePackageImplementationPackage, bridge_id)
    resolved_code_package = session.imap_get(CodePackage, code_package_id)
    if existing is not None:
        if existing.service_package_id != service_package_id or existing.code_package_id != code_package_id:
            raise RuntimeError(
                "ServicePackageImplementationPackage.build payload mismatch for existing bridge: "
                f"bridge_id={bridge_id}"
            )
        existing.package_name = normalized_package_name
        existing.language = language
        existing.import_root = normalized_import_root
        existing.manifest_relative_path = normalized_manifest_relative_path
        existing.package_root = normalized_package_root
        existing.entrypoint = normalized_entrypoint
        existing.role = normalized_role
        existing.include_paths = include_paths_payload
        existing.exclude_paths = exclude_paths_payload
        existing.code_package = resolved_code_package
        return existing

    return ServicePackageImplementationPackage.model_construct(
        id=bridge_id,
        service_package_id=service_package_id,
        code_package_id=code_package_id,
        code_package=resolved_code_package,
        package_name=normalized_package_name,
        language=language,
        import_root=normalized_import_root,
        manifest_relative_path=normalized_manifest_relative_path,
        package_root=normalized_package_root,
        entrypoint=normalized_entrypoint,
        role=normalized_role,
        include_paths=include_paths_payload,
        exclude_paths=exclude_paths_payload,
    )
    # --- AWARE: LOGIC END build_via_service_package
