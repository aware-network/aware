from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Sdk Ontology
from aware_sdk_ontology.sdk.sdk_surface_method import SdkSurfaceMethod

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_sdk_ontology.stable_ids import stable_sdk_surface_method_id

# --- AWARE: USER_IMPORTS END


async def create_via_sdk_surface(
    sdk_surface_id: UUID,
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
    Create one deterministic SDK surface method.

    Contract:
    - Parent `SdkSurface` scope is injected by propagation.
    - `target_sdk_operation_id` points at local SDK operation truth.
    - `method_family` is a stable small taxonomy, not a product verb.
    - Effect and confirmation policy are explicit; runtime adapters must not
      infer safety from operation names once this metadata is present.
    """

    # --- AWARE: LOGIC START create_via_sdk_surface
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("SdkSurfaceMethod.create_via_sdk_surface requires non-empty name")
    normalized_operation_ref = (operation_ref or "").strip()
    if not normalized_operation_ref:
        raise RuntimeError("SdkSurfaceMethod.create_via_sdk_surface requires non-empty operation_ref")
    normalized_operation_name = (operation_name or "").strip()
    if not normalized_operation_name:
        raise RuntimeError("SdkSurfaceMethod.create_via_sdk_surface requires non-empty operation_name")
    normalized_method_family = (method_family or "").strip()
    if not normalized_method_family:
        raise RuntimeError("SdkSurfaceMethod.create_via_sdk_surface requires non-empty method_family")
    return SdkSurfaceMethod(
        id=stable_sdk_surface_method_id(
            sdk_surface_id=sdk_surface_id,
            name=normalized_name,
            target_sdk_operation_id=target_sdk_operation_id,
        ),
        sdk_surface_id=sdk_surface_id,
        name=normalized_name,
        target_sdk_operation_id=target_sdk_operation_id,
        operation_ref=normalized_operation_ref,
        operation_name=normalized_operation_name,
        method_family=normalized_method_family,
        effect=(effect or "").strip() or "read",
        mutation_scope=(mutation_scope or "").strip() or "none",
        confirmation_policy=(confirmation_policy or "").strip() or "none",
        execution_mode=(execution_mode or "").strip() or "request_response",
        runtime_binding_kind=(runtime_binding_kind or "").strip() or "unbound",
        description=(description or "").strip() or None,
    )
    # --- AWARE: LOGIC END create_via_sdk_surface
