from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.function.function_config_invocation_enums import (
    FunctionInvocationKind,
    FunctionInvocationRootKind,
)
from aware_meta_ontology.function.function_config_invocation import FunctionConfigInvocation

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta
from aware_meta_ontology.stable_ids import stable_function_config_invocation_id

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create_via_function_config(
    function_config_id: UUID,
    position: int,
    kind: FunctionInvocationKind,
    target_function_config_id: UUID,
    relationship_fingerprint: str = "owner",
    class_config_relationship_id: UUID | None = None,
    root_invocation_id: UUID | None = None,
    root_kind: FunctionInvocationRootKind = FunctionInvocationRootKind.owner,
    capture_name: str | None = None,
) -> FunctionConfigInvocation:
    """
    Create deterministic FunctionConfigInvocation under a parent FunctionConfig path.

    Contract:
    - Parent FunctionConfig ownership is propagated by traversal lowering.
    - Constructor identity keys are
      `(position, kind, target_function_config_id, relationship_fingerprint)` plus propagated parent
    context.
    - `class_config_relationship_id` remains relationship metadata (nullable for owner-local
    invocations).
    - Standalone target constructors still rely on `class_config_relationship_id` for caller-owned
      containment/path routing even when the target function name itself stays semantic (no `_via_*`
    requirement).
    """

    # --- AWARE: LOGIC START create_via_function_config
    relationship_fingerprint_n = (relationship_fingerprint or "").strip()
    if class_config_relationship_id is None:
        if relationship_fingerprint_n and relationship_fingerprint_n != "owner":
            raise RuntimeError(
                "FunctionConfigInvocation.create_via_function owner-local invocation "
                "requires relationship_fingerprint='owner' when class_config_relationship_id is null"
            )
        relationship_fingerprint_n = "owner"
    else:
        expected = str(class_config_relationship_id)
        if not relationship_fingerprint_n or relationship_fingerprint_n == "owner":
            relationship_fingerprint_n = expected
        elif relationship_fingerprint_n != expected:
            raise RuntimeError(
                "FunctionConfigInvocation.create_via_function relationship_fingerprint mismatch for "
                "class_config_relationship_id: "
                f"fingerprint={relationship_fingerprint_n!r} expected={expected!r}"
            )

    kind_value = str(getattr(kind, "value", kind))
    invocation_id = stable_function_config_invocation_id(
        function_config_id=function_config_id,
        position=position,
        kind=kind_value,
        target_function_config_id=target_function_config_id,
        relationship_fingerprint=relationship_fingerprint_n,
    )

    session = current_handler_session()
    existing = session.imap_get(FunctionConfigInvocation, invocation_id)
    if existing is not None:
        if (
            existing.function_config_id != function_config_id
            or existing.position != position
            or existing.kind != kind
            or existing.target_function_config_id != target_function_config_id
            or existing.class_config_relationship_id != class_config_relationship_id
            or existing.root_invocation_id != root_invocation_id
            or existing.root_kind != root_kind
            or (existing.capture_name or None) != (capture_name or None)
        ):
            raise RuntimeError(
                "FunctionConfigInvocation.create_via_function payload mismatch for existing invocation: "
                f"invocation_id={invocation_id}"
            )
        return existing

    return FunctionConfigInvocation(
        id=invocation_id,
        function_config_id=function_config_id,
        position=position,
        kind=kind,
        target_function_config_id=target_function_config_id,
        class_config_relationship_id=class_config_relationship_id,
        root_invocation_id=root_invocation_id,
        root_kind=root_kind,
        capture_name=capture_name,
    )
    # --- AWARE: LOGIC END create_via_function_config
