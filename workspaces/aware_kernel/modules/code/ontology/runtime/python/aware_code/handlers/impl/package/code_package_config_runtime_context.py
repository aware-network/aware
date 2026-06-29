from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.package.code_package_enums import CodePackageConfigRuntimeContextKind
from aware_code_ontology.package.code_package_config_runtime_context import CodePackageConfigRuntimeContext

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code.stable_ids import stable_code_package_config_runtime_context_id
from aware_code_ontology.package.code_package_config import CodePackageConfig
from aware_meta.runtime.handler_context import current_handler_session


def _normalize_required(value: str | None, *, field_name: str) -> str:
    normalized = (value or "").strip()
    if not normalized:
        raise RuntimeError(f"CodePackageConfigRuntimeContext requires non-empty {field_name}")
    return normalized


def _normalize_optional(value: str | None) -> str | None:
    return (value or "").strip() or None


# --- AWARE: USER_IMPORTS END


async def build_via_code_package_config(
    code_package_config_id: UUID,
    context_key: str,
    kind: CodePackageConfigRuntimeContextKind,
    package_name: str | None = None,
    projection_name: str | None = None,
    runtime_contract_version: str | None = None,
    required: bool = True,
) -> CodePackageConfigRuntimeContext:
    """
    Create one CodePackageConfig-scoped runtime context contract row.

    Contract:
    - Parent CodePackageConfig context is propagated by constructor lowering.
    - This records runtime context shape; provider routing and deployment lifecycle stay outside Code.
    """

    # --- AWARE: LOGIC START build_via_code_package_config
    normalized_context_key = _normalize_required(context_key, field_name="context_key")
    session = current_handler_session()
    parent = session.imap_get(CodePackageConfig, code_package_config_id)
    if parent is None:
        raise RuntimeError(
            "CodePackageConfigRuntimeContext.build_via_code_package_config requires existing CodePackageConfig: "
            + f"code_package_config_id={code_package_config_id}"
        )

    context_id = stable_code_package_config_runtime_context_id(
        code_package_config_id=code_package_config_id,
        context_key=normalized_context_key,
    )
    existing = session.imap_get(CodePackageConfigRuntimeContext, context_id)
    if existing is None:
        return CodePackageConfigRuntimeContext(
            id=context_id,
            code_package_config_id=code_package_config_id,
            context_key=normalized_context_key,
            kind=kind,
            package_name=_normalize_optional(package_name),
            projection_name=_normalize_optional(projection_name),
            runtime_contract_version=_normalize_optional(runtime_contract_version),
            required=required,
        )

    if (
        existing.code_package_config_id != code_package_config_id
        or (existing.context_key or "").strip() != normalized_context_key
    ):
        raise RuntimeError(
            "CodePackageConfigRuntimeContext.build_via_code_package_config payload mismatch for existing context: "
            + f"code_package_config_runtime_context_id={context_id}"
        )
    existing.kind = kind
    existing.package_name = _normalize_optional(package_name)
    existing.projection_name = _normalize_optional(projection_name)
    existing.runtime_contract_version = _normalize_optional(runtime_contract_version)
    existing.required = required
    return existing
    # --- AWARE: LOGIC END build_via_code_package_config
