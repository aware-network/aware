from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.package.code_package_enums import (
    CodePackageConfigInputKind,
    CodePackageConfigOutputKind,
    CodePackageConfigRuntimeContextKind,
)
from aware_code_ontology.package.code_package import CodePackage
from aware_code_ontology.package.code_package_config import CodePackageConfig
from aware_code_ontology.package.code_package_config_input import CodePackageConfigInput
from aware_code_ontology.package.code_package_config_output import CodePackageConfigOutput
from aware_code_ontology.package.code_package_config_runtime_context import CodePackageConfigRuntimeContext

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code.handlers.impl.package import (
    code_package_config_input as config_input_handler,
    code_package_config_output as config_output_handler,
    code_package_config_runtime_context as config_runtime_context_handler,
)
from aware_code.stable_ids import (
    stable_code_package_config_id,
    stable_code_package_id,
)
from aware_meta.runtime.handler_executor.execution_context import (
    current_meta_graph_handler_execution_context_or_none,
)
from aware_meta.runtime.handler_context import current_handler_session
from aware_meta.runtime.portal_context import (
    MetaPortalPendingConstructorRequest,
    current_handler_portal_client,
)


def _normalize_required(value: str | None, *, field_name: str) -> str:
    normalized = (value or "").strip()
    if not normalized:
        raise RuntimeError(f"CodePackageConfig requires non-empty {field_name}")
    return normalized


def _normalize_optional(value: str | None) -> str | None:
    return (value or "").strip() or None


def _append_unique_by_id(items: list[object], item: object) -> object:
    item_id = getattr(item, "id", None)
    for existing in items:
        if getattr(existing, "id", None) == item_id:
            return existing
    items.append(item)
    return item


async def _create_package_via_portal(
    *,
    code_package_config: CodePackageConfig,
    package_name: str,
    language: CodeLanguage,
    manifest_relative_path: str,
    package_root: str,
    sources_root: str | None,
    fqn_prefix: str | None,
    surface: str | None,
) -> CodePackage | None:
    if current_meta_graph_handler_execution_context_or_none() is None:
        return None

    package_id = stable_code_package_id(
        code_package_config_id=code_package_config.id,
        package_name=package_name,
        language=language,
    )
    language_value = language.value if isinstance(language, CodeLanguage) else str(language)
    resolved_surface = surface if surface is not None else code_package_config.default_surface
    result = await current_handler_portal_client().invoke_constructor_from_pending_field(
        MetaPortalPendingConstructorRequest(
            orm_class=CodePackageConfig,
            source_instance_id=code_package_config.id,
            source_object_id=code_package_config.id,
            reference_field_name="packages",
            function_name="build_via_code_package_config",
            payload={
                "code_package_config_id": code_package_config.id,
                "package_name": package_name,
                "language": language_value,
                "manifest_relative_path": manifest_relative_path,
                "package_root": package_root,
                "sources_root": sources_root,
                "fqn_prefix": fqn_prefix,
                "surface": resolved_surface,
            },
            target_object_id=package_id,
            commit=True,
        )
    )
    if getattr(result, "status", None) != "succeeded":
        raise RuntimeError(
            "CodePackageConfig.create_package portal constructor failed: "
            + (getattr(result, "error", None) or "unknown error")
        )
    return CodePackage(
        id=package_id,
        code_package_config_id=code_package_config.id,
        package_name=package_name,
        language=language,
        manifest_relative_path=manifest_relative_path,
        package_root=package_root,
        sources_root=sources_root,
        fqn_prefix=fqn_prefix,
        surface=resolved_surface,
    )


# --- AWARE: USER_IMPORTS END


async def build(
    config_key: str,
    provider_key: str,
    semantic_owner: str,
    contract: str,
    manifest_kind: str,
    manifest_filename: str,
    package_role: str | None = None,
    semantic_package_family: str | None = None,
    semantic_package_kind: str | None = None,
    semantic_projection_name: str | None = None,
    semantic_root_kind: str | None = None,
    default_surface: str | None = None,
    materialization_capability: str | None = None,
) -> CodePackageConfig:
    """
    Create one Code-owned package configuration contract.

    Contract:
    - Identity is stable by `config_key`.
    - Config owns semantic package kind, manifest kind, and materialization contract vocabulary.
    - Workspace consumes this contract but owns deployment selection, planning, execution, and receipts.
    - Concrete CodePackage rows are constructed under `packages` so package identity is config-scoped.
    """

    # --- AWARE: LOGIC START build
    normalized_config_key = _normalize_required(config_key, field_name="config_key")
    normalized_provider_key = _normalize_required(provider_key, field_name="provider_key")
    normalized_semantic_owner = _normalize_required(semantic_owner, field_name="semantic_owner")
    normalized_contract = _normalize_required(contract, field_name="contract")
    normalized_manifest_filename = _normalize_required(
        manifest_filename,
        field_name="manifest_filename",
    )

    config_id = stable_code_package_config_id(config_key=normalized_config_key)
    session = current_handler_session()
    existing = session.imap_get(CodePackageConfig, config_id)
    if existing is None:
        return CodePackageConfig(
            id=config_id,
            config_key=normalized_config_key,
            provider_key=normalized_provider_key,
            semantic_owner=normalized_semantic_owner,
            contract=normalized_contract,
            package_role=_normalize_optional(package_role),
            manifest_kind=manifest_kind,
            manifest_filename=normalized_manifest_filename,
            semantic_package_family=_normalize_optional(semantic_package_family),
            semantic_package_kind=_normalize_optional(semantic_package_kind),
            semantic_projection_name=_normalize_optional(semantic_projection_name),
            semantic_root_kind=_normalize_optional(semantic_root_kind),
            default_surface=default_surface,
            materialization_capability=_normalize_optional(materialization_capability),
        )

    if (existing.config_key or "").strip() != normalized_config_key:
        raise RuntimeError(
            "CodePackageConfig.build payload mismatch for existing config: " + f"code_package_config_id={config_id}"
        )
    existing.provider_key = normalized_provider_key
    existing.semantic_owner = normalized_semantic_owner
    existing.contract = normalized_contract
    existing.package_role = _normalize_optional(package_role)
    existing.manifest_kind = manifest_kind
    existing.manifest_filename = normalized_manifest_filename
    existing.semantic_package_family = _normalize_optional(semantic_package_family)
    existing.semantic_package_kind = _normalize_optional(semantic_package_kind)
    existing.semantic_projection_name = _normalize_optional(semantic_projection_name)
    existing.semantic_root_kind = _normalize_optional(semantic_root_kind)
    existing.default_surface = default_surface
    existing.materialization_capability = _normalize_optional(materialization_capability)
    return existing
    # --- AWARE: LOGIC END build


async def create_package(
    code_package_config: CodePackageConfig,
    package_name: str,
    language: CodeLanguage,
    manifest_relative_path: str,
    package_root: str,
    sources_root: str | None = None,
    fqn_prefix: str | None = None,
    surface: str | None = None,
) -> CodePackage:
    """
    Create one concrete CodePackage under this CodePackageConfig.

    Contract:
    - Parent CodePackageConfig context is propagated by constructor lowering.
    - Runtime package layout remains instance payload.
    - `surface` is an optional package override; consumers fall back to `default_surface`.
    """

    # --- AWARE: LOGIC START create_package
    created_via_portal = await _create_package_via_portal(
        code_package_config=code_package_config,
        package_name=package_name,
        language=language,
        manifest_relative_path=manifest_relative_path,
        package_root=package_root,
        sources_root=sources_root,
        fqn_prefix=fqn_prefix,
        surface=surface,
    )
    if created_via_portal is not None:
        return created_via_portal

    created = await CodePackage.build_via_code_package_config(
        code_package_config_id=code_package_config.id,
        package_name=package_name,
        language=language,
        manifest_relative_path=manifest_relative_path,
        package_root=package_root,
        sources_root=sources_root,
        fqn_prefix=fqn_prefix,
        surface=surface if surface is not None else code_package_config.default_surface,
    )
    return _append_unique_by_id(code_package_config.packages, created)
    # --- AWARE: LOGIC END create_package


async def add_input(
    code_package_config: CodePackageConfig,
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
    Declare one typed materialization input accepted by this package config.
    """

    # --- AWARE: LOGIC START add_input
    created = await config_input_handler.build_via_code_package_config(
        code_package_config_id=code_package_config.id,
        input_key=input_key,
        kind=kind,
        artifact_family=artifact_family,
        artifact_role=artifact_role,
        package_family=package_family,
        semantic_kind=semantic_kind,
        runtime_contract_version=runtime_contract_version,
        required=required,
    )
    return _append_unique_by_id(code_package_config.inputs, created)
    # --- AWARE: LOGIC END add_input


async def add_output(
    code_package_config: CodePackageConfig,
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
    Declare one typed materialization output emitted by this package config.
    """

    # --- AWARE: LOGIC START add_output
    created = await config_output_handler.build_via_code_package_config(
        code_package_config_id=code_package_config.id,
        output_key=output_key,
        kind=kind,
        producer_key=producer_key,
        artifact_family=artifact_family,
        artifact_role=artifact_role,
        package_output_key=package_output_key,
        target_provider_key=target_provider_key,
        target_input_key=target_input_key,
        target_semantic_owner=target_semantic_owner,
        target_package_family=target_package_family,
        target_semantic_kind=target_semantic_kind,
        media_type=media_type,
        runtime_contract_version=runtime_contract_version,
        required_for=required_for,
        required=required,
    )
    return _append_unique_by_id(code_package_config.outputs, created)
    # --- AWARE: LOGIC END add_output


async def add_runtime_context(
    code_package_config: CodePackageConfig,
    context_key: str,
    kind: CodePackageConfigRuntimeContextKind,
    package_name: str | None = None,
    projection_name: str | None = None,
    runtime_contract_version: str | None = None,
    required: bool = True,
) -> CodePackageConfigRuntimeContext:
    """
    Declare one typed runtime context required by this package config.
    """

    # --- AWARE: LOGIC START add_runtime_context
    created = await config_runtime_context_handler.build_via_code_package_config(
        code_package_config_id=code_package_config.id,
        context_key=context_key,
        kind=kind,
        package_name=package_name,
        projection_name=projection_name,
        runtime_contract_version=runtime_contract_version,
        required=required,
    )
    return _append_unique_by_id(code_package_config.runtime_contexts, created)
    # --- AWARE: LOGIC END add_runtime_context
