from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.package.code_package_enums import CodePackageConfigOutputKind
from aware_code_ontology.package.code_package_config_output import CodePackageConfigOutput

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code.stable_ids import stable_code_package_config_output_id
from aware_code_ontology.package.code_package_config import CodePackageConfig
from aware_meta.runtime.handler_context import current_handler_session


def _normalize_required(value: str | None, *, field_name: str) -> str:
    normalized = (value or "").strip()
    if not normalized:
        raise RuntimeError(f"CodePackageConfigOutput requires non-empty {field_name}")
    return normalized


def _normalize_optional(value: str | None) -> str | None:
    return (value or "").strip() or None


def _normalize_required_for(values: list[str]) -> list[str]:
    return [normalized for value in values for normalized in [(value or "").strip()] if normalized]


# --- AWARE: USER_IMPORTS END


async def build_via_code_package_config(
    code_package_config_id: UUID,
    output_key: str,
    kind: CodePackageConfigOutputKind,
    producer_key: str | None = None,
    artifact_family: str | None = None,
    artifact_role: str | None = None,
    package_output_key: str | None = None,
    target_provider_key: str | None = None,
    target_input_key: str | None = None,
    target_semantic_owner: str | None = None,
    target_package_family: str | None = None,
    target_semantic_kind: str | None = None,
    media_type: str | None = None,
    runtime_contract_version: str | None = None,
    required_for: list[str] = [],
    required: bool = True,
) -> CodePackageConfigOutput:
    """
    Create one CodePackageConfig-scoped materialization output contract row.

    Contract:
    - Parent CodePackageConfig context is propagated by constructor lowering.
    - This describes declared outputs only.
    - CodePackageArtifact owns package output evidence emitted for a concrete CodePackage.
    - Workspace owns revision pins, materialization envelopes, and publication envelopes.
    """

    # --- AWARE: LOGIC START build_via_code_package_config
    normalized_output_key = _normalize_required(output_key, field_name="output_key")
    session = current_handler_session()
    parent = session.imap_get(CodePackageConfig, code_package_config_id)
    if parent is None:
        raise RuntimeError(
            "CodePackageConfigOutput.build_via_code_package_config requires existing CodePackageConfig: "
            + f"code_package_config_id={code_package_config_id}"
        )

    output_id = stable_code_package_config_output_id(
        code_package_config_id=code_package_config_id,
        output_key=normalized_output_key,
    )
    normalized_required_for = _normalize_required_for(required_for)
    existing = session.imap_get(CodePackageConfigOutput, output_id)
    if existing is None:
        return CodePackageConfigOutput(
            id=output_id,
            code_package_config_id=code_package_config_id,
            output_key=normalized_output_key,
            kind=kind,
            producer_key=_normalize_optional(producer_key),
            artifact_family=_normalize_optional(artifact_family),
            artifact_role=_normalize_optional(artifact_role),
            package_output_key=_normalize_optional(package_output_key),
            target_provider_key=_normalize_optional(target_provider_key),
            target_input_key=_normalize_optional(target_input_key),
            target_semantic_owner=_normalize_optional(target_semantic_owner),
            target_package_family=_normalize_optional(target_package_family),
            target_semantic_kind=_normalize_optional(target_semantic_kind),
            media_type=_normalize_optional(media_type),
            runtime_contract_version=_normalize_optional(runtime_contract_version),
            required_for=normalized_required_for,
            required=required,
        )

    if (
        existing.code_package_config_id != code_package_config_id
        or (existing.output_key or "").strip() != normalized_output_key
    ):
        raise RuntimeError(
            "CodePackageConfigOutput.build_via_code_package_config payload mismatch for existing output: "
            + f"code_package_config_output_id={output_id}"
        )
    existing.kind = kind
    existing.producer_key = _normalize_optional(producer_key)
    existing.artifact_family = _normalize_optional(artifact_family)
    existing.artifact_role = _normalize_optional(artifact_role)
    existing.package_output_key = _normalize_optional(package_output_key)
    existing.target_provider_key = _normalize_optional(target_provider_key)
    existing.target_input_key = _normalize_optional(target_input_key)
    existing.target_semantic_owner = _normalize_optional(target_semantic_owner)
    existing.target_package_family = _normalize_optional(target_package_family)
    existing.target_semantic_kind = _normalize_optional(target_semantic_kind)
    existing.media_type = _normalize_optional(media_type)
    existing.runtime_contract_version = _normalize_optional(runtime_contract_version)
    existing.required_for = normalized_required_for
    existing.required = required
    return existing
    # --- AWARE: LOGIC END build_via_code_package_config
