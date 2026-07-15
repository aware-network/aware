from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.package.code_package_enums import CodePackageConfigInputKind
from aware_code_ontology.package.code_package_config_input import CodePackageConfigInput

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code.stable_ids import stable_code_package_config_input_id
from aware_code_ontology.package.code_package_config import CodePackageConfig
from aware_meta.runtime.handler_context import current_handler_session


def _normalize_required(value: str | None, *, field_name: str) -> str:
    normalized = (value or "").strip()
    if not normalized:
        raise RuntimeError(f"CodePackageConfigInput requires non-empty {field_name}")
    return normalized


def _normalize_optional(value: str | None) -> str | None:
    return (value or "").strip() or None


# --- AWARE: USER_IMPORTS END


async def build_via_code_package_config(
    code_package_config_id: UUID,
    input_key: str,
    kind: CodePackageConfigInputKind,
    artifact_family: str | None = None,
    artifact_role: str | None = None,
    package_family: str | None = None,
    semantic_kind: str | None = None,
    runtime_contract_version: str | None = None,
    required: bool = True,
) -> CodePackageConfigInput:
    """
    Create one CodePackageConfig-scoped materialization input contract row.

    Contract:
    - Parent CodePackageConfig context is propagated by constructor lowering.
    - This describes input shape only; Workspace owns selected revisions and execution receipts.
    """

    # --- AWARE: LOGIC START build_via_code_package_config
    normalized_input_key = _normalize_required(input_key, field_name="input_key")
    session = current_handler_session()
    parent = session.imap_get(CodePackageConfig, code_package_config_id)
    if parent is None:
        raise RuntimeError(
            "CodePackageConfigInput.build_via_code_package_config requires existing CodePackageConfig: "
            + f"code_package_config_id={code_package_config_id}"
        )

    input_id = stable_code_package_config_input_id(
        code_package_config_id=code_package_config_id,
        input_key=normalized_input_key,
    )
    existing = session.imap_get(CodePackageConfigInput, input_id)
    if existing is None:
        return CodePackageConfigInput(
            id=input_id,
            code_package_config_id=code_package_config_id,
            input_key=normalized_input_key,
            kind=kind,
            artifact_family=_normalize_optional(artifact_family),
            artifact_role=_normalize_optional(artifact_role),
            package_family=_normalize_optional(package_family),
            semantic_kind=_normalize_optional(semantic_kind),
            runtime_contract_version=_normalize_optional(runtime_contract_version),
            required=required,
        )

    if (
        existing.code_package_config_id != code_package_config_id
        or (existing.input_key or "").strip() != normalized_input_key
    ):
        raise RuntimeError(
            "CodePackageConfigInput.build_via_code_package_config payload mismatch for existing input: "
            + f"code_package_config_input_id={input_id}"
        )
    existing.kind = kind
    existing.artifact_family = _normalize_optional(artifact_family)
    existing.artifact_role = _normalize_optional(artifact_role)
    existing.package_family = _normalize_optional(package_family)
    existing.semantic_kind = _normalize_optional(semantic_kind)
    existing.runtime_contract_version = _normalize_optional(runtime_contract_version)
    existing.required = required
    return existing
    # --- AWARE: LOGIC END build_via_code_package_config
