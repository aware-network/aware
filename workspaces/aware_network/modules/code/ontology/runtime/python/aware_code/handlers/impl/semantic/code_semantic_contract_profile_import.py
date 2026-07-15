from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.semantic.code_semantic_contract_profile_import import CodeSemanticContractProfileImport

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code.stable_ids import stable_code_semantic_contract_profile_import_id
from aware_code_ontology.semantic.code_semantic_contract_profile import (
    CodeSemanticContractProfile,
)
from aware_meta.runtime.handler_context import current_handler_session


def _normalize_required(value: str | None, *, field_name: str) -> str:
    normalized = (value or "").strip()
    if not normalized:
        raise RuntimeError(f"CodeSemanticContractProfileImport requires non-empty {field_name}")
    return normalized


# --- AWARE: USER_IMPORTS END


async def build_via_code_semantic_contract_profile(
    code_semantic_contract_profile_id: UUID,
    imported_profile_id: UUID,
    import_key: str,
    required: bool = True,
    status: str = "active",
) -> CodeSemanticContractProfileImport:
    """
    Record one Code-level semantic contract profile composition edge.

    Contract:
    - Profile composition is Code semantic contract graph truth.
    - Workspace resolves composed profiles but does not model profile imports
      as workspace package dependencies.
    """

    # --- AWARE: LOGIC START build_via_code_semantic_contract_profile
    normalized_import_key = _normalize_required(import_key, field_name="import_key")
    import_id = stable_code_semantic_contract_profile_import_id(
        code_semantic_contract_profile_id=code_semantic_contract_profile_id,
        imported_profile_id=imported_profile_id,
        import_key=normalized_import_key,
    )
    session = current_handler_session()
    imported_profile = session.imap_get(CodeSemanticContractProfile, imported_profile_id)
    if imported_profile is None:
        raise RuntimeError(
            "CodeSemanticContractProfileImport requires existing imported "
            "CodeSemanticContractProfile in the active session: "
            f"imported_profile_id={imported_profile_id}"
        )
    normalized_status = (status or "").strip() or "active"
    existing = session.imap_get(CodeSemanticContractProfileImport, import_id)
    if existing is not None:
        if (
            existing.code_semantic_contract_profile_id != code_semantic_contract_profile_id
            or existing.imported_profile_id != imported_profile_id
        ):
            raise RuntimeError(
                "CodeSemanticContractProfileImport payload mismatch for existing "
                f"profile import: code_semantic_contract_profile_import_id={import_id}"
            )
        existing.imported_profile = imported_profile
        existing.import_key = normalized_import_key
        existing.required = bool(required)
        existing.status = normalized_status
        return existing

    return CodeSemanticContractProfileImport(
        id=import_id,
        code_semantic_contract_profile_id=code_semantic_contract_profile_id,
        imported_profile=imported_profile,
        imported_profile_id=imported_profile_id,
        import_key=normalized_import_key,
        required=bool(required),
        status=normalized_status,
    )
    # --- AWARE: LOGIC END build_via_code_semantic_contract_profile
