from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Sdk Ontology
from aware_sdk_ontology.sdk.sdk_surface import SdkSurface
from aware_sdk_ontology.sdk.sdk_surface_method import SdkSurfaceMethod

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_sdk_ontology.stable_ids import stable_sdk_surface_id

# --- AWARE: USER_IMPORTS END


async def add_method(
    sdk_surface: SdkSurface,
    name: str,
    target_sdk_operation_id: UUID,
    operation_ref: str,
    operation_name: str,
    method_family: str,
    effect: str = "read",
    mutation_scope: str = "none",
    confirmation_policy: str = "none",
    execution_mode: str = "request_response",
    runtime_binding_kind: str = "unbound",
    description: str | None = None,
) -> SdkSurfaceMethod:
    """
    Add one stable method under this SDK surface.
    """

    # --- AWARE: LOGIC START add_method
    method = await SdkSurfaceMethod.create_via_sdk_surface(
        sdk_surface_id=sdk_surface.id,
        name=name,
        target_sdk_operation_id=target_sdk_operation_id,
        operation_ref=operation_ref,
        operation_name=operation_name,
        method_family=method_family,
        effect=effect,
        mutation_scope=mutation_scope,
        confirmation_policy=confirmation_policy,
        execution_mode=execution_mode,
        runtime_binding_kind=runtime_binding_kind,
        description=description,
    )
    if all(existing.id != method.id for existing in sdk_surface.methods):
        sdk_surface.methods.append(method)
    return method
    # --- AWARE: LOGIC END add_method


async def build_via_sdk_config(
    sdk_config_id: UUID, name: str, title: str | None = None, description: str | None = None
) -> SdkSurface:
    """
    Create one SDK-owned conceptual surface.

    Contract:
    - Identity is scoped by parent `SdkConfig` and surface `name`.
    - Surface names are stable conceptual groups, not command paths.
    - Methods bind the surface to SDK operations and effect policy.
    """

    # --- AWARE: LOGIC START build_via_sdk_config
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("SdkSurface.build_via_sdk_config requires non-empty name")
    normalized_title = (title or "").strip() or None
    normalized_description = (description or "").strip() or None
    return SdkSurface(
        id=stable_sdk_surface_id(
            sdk_config_id=sdk_config_id,
            name=normalized_name,
        ),
        sdk_config_id=sdk_config_id,
        name=normalized_name,
        title=normalized_title,
        description=normalized_description,
    )
    # --- AWARE: LOGIC END build_via_sdk_config
