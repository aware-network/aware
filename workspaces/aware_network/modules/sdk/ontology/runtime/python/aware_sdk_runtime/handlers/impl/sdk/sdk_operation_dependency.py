from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Sdk Ontology
from aware_sdk_ontology.sdk.sdk_operation_dependency import SdkOperationDependency

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_sdk_ontology.stable_ids import stable_sdk_operation_dependency_id

# --- AWARE: USER_IMPORTS END


async def create_via_sdk_operation(
    sdk_operation_id: UUID,
    target_sdk_operation_id: UUID,
    target_operation_ref: str,
    target_sdk_name: str,
    target_operation_name: str,
    target_package_name: str | None = None,
    role: str = "dependency",
    order: int = 1,
    required: bool = True,
    description: str | None = None,
) -> SdkOperationDependency:
    """
    Create one deterministic SDK operation dependency edge.

    Contract:
    - Parent `SdkOperation` scope is injected by propagation.
    - `target_sdk_operation_id` points at the canonical target operation identity.
    - `target_operation_ref` preserves authored `sdk_name.operation_name` syntax.
    - External operation refs must be backed by a declared `SdkPackageDependency`.
    - Runtime composition may use this edge; API endpoint bindings remain ingress truth.
    """

    # --- AWARE: LOGIC START create_via_sdk_operation
    normalized_target_operation_ref = (target_operation_ref or "").strip()
    if not normalized_target_operation_ref:
        raise RuntimeError(
            "SdkOperationDependency.create_via_sdk_operation requires " + "non-empty target_operation_ref"
        )
    normalized_target_sdk_name = (target_sdk_name or "").strip()
    if not normalized_target_sdk_name:
        raise RuntimeError("SdkOperationDependency.create_via_sdk_operation requires " + "non-empty target_sdk_name")
    normalized_target_operation_name = (target_operation_name or "").strip()
    if not normalized_target_operation_name:
        raise RuntimeError(
            "SdkOperationDependency.create_via_sdk_operation requires " + "non-empty target_operation_name"
        )
    expected_ref = f"{normalized_target_sdk_name}.{normalized_target_operation_name}"
    if normalized_target_operation_ref != expected_ref:
        raise RuntimeError(
            "SdkOperationDependency target_operation_ref must match "
            + f"target sdk/name: expected={expected_ref!r} "
            + f"actual={normalized_target_operation_ref!r}"
        )
    return SdkOperationDependency(
        id=stable_sdk_operation_dependency_id(
            sdk_operation_id=sdk_operation_id,
            target_sdk_operation_id=target_sdk_operation_id,
        ),
        sdk_operation_id=sdk_operation_id,
        target_sdk_operation_id=target_sdk_operation_id,
        target_operation_ref=normalized_target_operation_ref,
        target_sdk_name=normalized_target_sdk_name,
        target_operation_name=normalized_target_operation_name,
        target_package_name=(target_package_name or "").strip() or None,
        role=(role or "").strip() or "dependency",
        order=order,
        required=required,
        description=(description or "").strip() or None,
    )
    # --- AWARE: LOGIC END create_via_sdk_operation
