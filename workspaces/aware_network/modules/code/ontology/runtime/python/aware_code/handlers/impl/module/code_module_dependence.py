from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.module.code_module_dependence import CodeModuleDependence

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code.stable_ids import (
    stable_code_module_dependence_id,
)
from aware_code_ontology.module.code_module import CodeModule
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_code_module(code_module_id: UUID, name: str) -> CodeModuleDependence:
    """
    Create a deterministic dependency association under one CodeModule.

    Contract:
    - Parent CodeModule scope is injected by propagation.
    - Target CodeModule identity is resolved by `CodeModule.build(name)`.
    """

    # --- AWARE: LOGIC START build_via_code_module
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("CodeModuleDependence.build_via_code_module requires non-empty name")

    association_id = stable_code_module_dependence_id(
        code_module_id=code_module_id,
        name=normalized_name,
    )
    target_module = await CodeModule.build(name=normalized_name, languages=[])

    session = current_handler_session()
    existing = session.imap_get(CodeModuleDependence, association_id)
    if existing is not None:
        if existing.code_module_id != code_module_id or existing.dependence_id != target_module.id:
            raise RuntimeError(
                "CodeModuleDependence.build_via_code_module payload mismatch for existing association: "
                f"code_module_dependence_id={association_id}"
            )
        return existing

    return CodeModuleDependence(
        id=association_id,
        name=normalized_name,
        code_module_id=code_module_id,
        dependence_id=target_module.id,
        dependence=target_module,
    )
    # --- AWARE: LOGIC END build_via_code_module
