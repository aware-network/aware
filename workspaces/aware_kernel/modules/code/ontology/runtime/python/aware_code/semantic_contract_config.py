from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from uuid import UUID

from aware_code.module_semantic_contract import (
    ModuleSemanticContract,
    ModuleSemanticManifestResolutionDescriptor,
)
from aware_code.package_surface import normalize_code_package_surface
from aware_code.semantic_materialization import SEMANTIC_MATERIALIZATION_CAPABILITY
from aware_code.stable_ids import (
    code_package_source_config_key,
    stable_code_package_config_id,
    stable_code_package_config_input_id,
    stable_code_package_config_output_id,
    stable_code_package_config_runtime_context_id,
)
from aware_code_ontology.package.code_package_config import CodePackageConfig
from aware_code_ontology.package.code_package_config_input import CodePackageConfigInput
from aware_code_ontology.package.code_package_config_output import (
    CodePackageConfigOutput,
)
from aware_code_ontology.package.code_package_config_runtime_context import (
    CodePackageConfigRuntimeContext,
)
from aware_code_ontology.package.code_package_enums import (
    CodePackageConfigInputKind,
    CodePackageConfigOutputKind,
    CodePackageConfigRuntimeContextKind,
)

PACKAGE_MANAGER_PYPROJECT_MANIFEST_KIND = "package_manager_pyproject_toml"
PACKAGE_MANAGER_CODE_PACKAGE_SURFACE = "package_manager"
PYPROJECT_MANIFEST_FILENAME = "pyproject.toml"


@dataclass(frozen=True, slots=True)
class CodePackageConfigRef:
    config_id: UUID
    config_key: str
    manifest_kind: str
    surface: str


@dataclass(frozen=True, slots=True)
class CodePackageConfigDescriptor:
    ref: CodePackageConfigRef
    provider_key: str
    semantic_owner: str
    contract: str
    package_role: str | None
    manifest_filename: str
    semantic_package_family: str | None
    semantic_package_kind: str | None
    semantic_projection_name: str | None
    semantic_root_kind: str | None
    materialization_capability: str | None


def source_code_package_config_ref(
    *,
    manifest_kind: str,
    surface: str | None,
) -> CodePackageConfigRef:
    resolved_manifest_kind = _code_package_manifest_kind(manifest_kind)
    resolved_surface = _code_package_surface(surface) or "runtime"
    config_key = code_package_source_config_key(
        manifest_kind=resolved_manifest_kind,
        surface=resolved_surface,
    )
    return CodePackageConfigRef(
        config_id=stable_code_package_config_id(config_key=config_key),
        config_key=config_key,
        manifest_kind=resolved_manifest_kind,
        surface=resolved_surface,
    )


def package_manager_pyproject_code_package_config_ref() -> CodePackageConfigRef:
    """Return the manifest-only config ref for workspace root pyproject files."""

    return source_code_package_config_ref(
        manifest_kind=PACKAGE_MANAGER_PYPROJECT_MANIFEST_KIND,
        surface=PACKAGE_MANAGER_CODE_PACKAGE_SURFACE,
    )


def source_code_package_config_descriptor(
    *,
    manifest_kind: str,
    surface: str | None,
) -> CodePackageConfigDescriptor:
    resolved_manifest_kind = _code_package_manifest_kind(manifest_kind)
    resolved_surface = _code_package_surface(surface) or "runtime"
    contract, descriptor = _source_manifest_resolution_descriptor(
        manifest_kind=resolved_manifest_kind,
        surface=resolved_surface,
    )
    return code_package_config_descriptor_from_manifest_resolution_descriptor(
        provider_key=contract.provider_key,
        descriptor=descriptor,
        semantic_contract=contract,
        fallback_surface=resolved_surface,
    )


def code_package_config_ref_from_manifest_resolution_descriptor(
    *,
    descriptor: object,
    package_kind: str | None = None,
    fallback_surface: str | None = None,
) -> CodePackageConfigRef:
    return source_code_package_config_ref(
        manifest_kind=_required_text_attribute(descriptor, "manifest_kind"),
        surface=_surface_for_manifest_resolution_descriptor(
            descriptor=descriptor,
            package_kind=package_kind,
            fallback_surface=fallback_surface,
        ),
    )


def code_package_config_descriptor_from_manifest_resolution_descriptor(
    *,
    provider_key: str,
    descriptor: object,
    semantic_contract: object | None = None,
    package_kind: str | None = None,
    fallback_surface: str | None = None,
) -> CodePackageConfigDescriptor:
    config_ref = code_package_config_ref_from_manifest_resolution_descriptor(
        descriptor=descriptor,
        package_kind=package_kind,
        fallback_surface=fallback_surface,
    )
    semantic_owner = _required_text_attribute(descriptor, "semantic_owner")
    return CodePackageConfigDescriptor(
        ref=config_ref,
        provider_key=_required_text(provider_key, field_name="provider_key"),
        semantic_owner=semantic_owner,
        contract=_required_text_attribute(descriptor, "contract"),
        package_role=_optional_text(getattr(descriptor, "package_role", None)),
        manifest_filename=_required_text_attribute(descriptor, "filename"),
        semantic_package_family=_optional_text(
            getattr(descriptor, "semantic_package_family", None)
        ),
        semantic_package_kind=_optional_text(
            getattr(descriptor, "semantic_package_kind", None)
        ),
        semantic_projection_name=_optional_text(
            getattr(descriptor, "semantic_projection_name", None)
        ),
        semantic_root_kind=_optional_text(
            getattr(descriptor, "semantic_root_kind", None)
        ),
        materialization_capability=_materialization_capability_for_contract_object(
            semantic_contract=semantic_contract,
            semantic_owner=semantic_owner,
        ),
    )


def build_code_package_config_from_semantic_contract(
    *,
    contract: ModuleSemanticContract,
    manifest_resolution: ModuleSemanticManifestResolutionDescriptor,
    package_kind: str | None = None,
) -> CodePackageConfig:
    descriptor = code_package_config_descriptor_from_manifest_resolution_descriptor(
        provider_key=contract.provider_key,
        descriptor=manifest_resolution,
        semantic_contract=contract,
        package_kind=package_kind or manifest_resolution.semantic_package_kind,
    )
    config = CodePackageConfig(
        id=descriptor.ref.config_id,
        config_key=descriptor.ref.config_key,
        provider_key=descriptor.provider_key,
        semantic_owner=descriptor.semantic_owner,
        contract=descriptor.contract,
        package_role=descriptor.package_role,
        manifest_kind=descriptor.ref.manifest_kind,
        manifest_filename=descriptor.manifest_filename,
        semantic_package_family=descriptor.semantic_package_family,
        semantic_package_kind=descriptor.semantic_package_kind,
        semantic_projection_name=descriptor.semantic_projection_name,
        semantic_root_kind=descriptor.semantic_root_kind,
        default_surface=descriptor.ref.surface,
        materialization_capability=descriptor.materialization_capability,
    )
    config.inputs = list(
        _config_inputs_for_contract(
            contract=contract,
            semantic_owner=manifest_resolution.semantic_owner,
            code_package_config_id=config.id,
        )
    )
    config.outputs = list(
        _config_outputs_for_contract(
            contract=contract,
            semantic_owner=manifest_resolution.semantic_owner,
            code_package_config_id=config.id,
        )
    )
    config.runtime_contexts = list(
        _runtime_contexts_for_contract(
            contract=contract,
            semantic_owner=manifest_resolution.semantic_owner,
            code_package_config_id=config.id,
        )
    )
    return config


def build_code_package_configs_from_semantic_contract(
    *,
    contract: ModuleSemanticContract,
) -> tuple[CodePackageConfig, ...]:
    return tuple(
        build_code_package_config_from_semantic_contract(
            contract=contract,
            manifest_resolution=descriptor,
        )
        for descriptor in contract.manifest_resolution
    )


def code_package_config_for_id(config_id: UUID) -> CodePackageConfig | None:
    from aware_code.module_plugin_registry import AwareModulePluginRegistry

    matches: list[CodePackageConfig] = []
    for contract in AwareModulePluginRegistry.get_module_semantic_contracts():
        for config in build_code_package_configs_from_semantic_contract(
            contract=contract,
        ):
            if config.id == config_id:
                matches.append(config)

    if not matches:
        return None
    first = matches[0]
    conflicts = [
        config
        for config in matches[1:]
        if config.model_dump(mode="json", exclude={"packages"})
        != first.model_dump(mode="json", exclude={"packages"})
    ]
    if conflicts:
        provider_keys = tuple(config.provider_key for config in matches)
        raise RuntimeError(
            "Multiple semantic contracts lower to conflicting CodePackageConfig "
            f"payloads for code_package_config_id={config_id}: {provider_keys!r}"
        )
    return first


def _config_inputs_for_contract(
    *,
    contract: ModuleSemanticContract,
    semantic_owner: str,
    code_package_config_id: UUID,
) -> tuple[CodePackageConfigInput, ...]:
    return tuple(
        CodePackageConfigInput(
            id=stable_code_package_config_input_id(
                code_package_config_id=code_package_config_id,
                input_key=_required_text(descriptor.input_key, field_name="input_key"),
            ),
            code_package_config_id=code_package_config_id,
            input_key=_required_text(descriptor.input_key, field_name="input_key"),
            kind=_input_kind_for_descriptor(descriptor),
            artifact_family=_optional_text(descriptor.artifact_family),
            artifact_role=_optional_text(descriptor.artifact_role),
            package_family=_optional_text(descriptor.package_family),
            semantic_kind=_optional_text(descriptor.semantic_kind),
            runtime_contract_version=_optional_text(
                descriptor.runtime_contract_version
            ),
            required=bool(descriptor.required),
        )
        for descriptor in contract.materialization_inputs_for(
            semantic_owner=semantic_owner
        )
    )


def _config_outputs_for_contract(
    *,
    contract: ModuleSemanticContract,
    semantic_owner: str,
    code_package_config_id: UUID,
) -> tuple[CodePackageConfigOutput, ...]:
    rows: dict[str, CodePackageConfigOutput] = {}
    for descriptor in contract.materialization_artifact_outputs_for(
        semantic_owner=semantic_owner
    ):
        _put_output(
            rows,
            code_package_config_id=code_package_config_id,
            output_key=descriptor.output_key,
            kind=_output_kind_for_artifact_descriptor(descriptor),
            producer_key=descriptor.producer_key,
            artifact_family=descriptor.artifact_family,
            artifact_role=descriptor.artifact_role,
            package_output_key=descriptor.package_output_key,
            media_type=descriptor.media_type,
            runtime_contract_version=descriptor.runtime_contract_version,
            required_for=descriptor.required_for,
            required=descriptor.required,
        )
    for descriptor in contract.materialization_code_package_delta_outputs_for(
        semantic_owner=semantic_owner
    ):
        _put_output(
            rows,
            code_package_config_id=code_package_config_id,
            output_key=descriptor.output_key,
            kind=CodePackageConfigOutputKind.code_package_delta,
            producer_key=descriptor.producer_key,
            package_output_key=descriptor.package_output_key,
            runtime_contract_version=descriptor.runtime_contract_version,
            required_for=descriptor.required_for,
            required=descriptor.required,
        )
    for descriptor in contract.materialization_package_outputs_for(
        semantic_owner=semantic_owner
    ):
        _put_output(
            rows,
            code_package_config_id=code_package_config_id,
            output_key=descriptor.output_key,
            kind=CodePackageConfigOutputKind.package,
            producer_key=descriptor.producer_key,
            target_provider_key=descriptor.target_provider_key,
            target_input_key=descriptor.target_input_key,
            target_semantic_owner=descriptor.target_semantic_owner,
            target_package_family=descriptor.target_package_family,
            target_semantic_kind=descriptor.target_semantic_kind,
            runtime_contract_version=descriptor.runtime_contract_version,
            required_for=descriptor.required_for,
            required=descriptor.required,
        )
    return tuple(rows[key] for key in sorted(rows))


def _runtime_contexts_for_contract(
    *,
    contract: ModuleSemanticContract,
    semantic_owner: str,
    code_package_config_id: UUID,
) -> tuple[CodePackageConfigRuntimeContext, ...]:
    rows: dict[str, CodePackageConfigRuntimeContext] = {}
    for descriptor in contract.materialization_runtime_for(
        semantic_owner=semantic_owner
    ):
        for package_name in descriptor.runtime_ontology_package_names:
            _put_runtime_context(
                rows,
                code_package_config_id=code_package_config_id,
                context_key=f"ontology_package:{package_name}",
                kind=CodePackageConfigRuntimeContextKind.ontology_package,
                package_name=package_name,
            )
        if descriptor.lane_projection_name is not None:
            _put_runtime_context(
                rows,
                code_package_config_id=code_package_config_id,
                context_key=f"lane_projection:{descriptor.lane_projection_name}",
                kind=CodePackageConfigRuntimeContextKind.projection,
                projection_name=descriptor.lane_projection_name,
            )
        for projection_name in descriptor.required_projection_names:
            _put_runtime_context(
                rows,
                code_package_config_id=code_package_config_id,
                context_key=f"projection:{projection_name}",
                kind=CodePackageConfigRuntimeContextKind.projection,
                projection_name=projection_name,
            )
        for projection_package in descriptor.runtime_projection_packages:
            package_name = projection_package.package_name
            _put_runtime_context(
                rows,
                code_package_config_id=code_package_config_id,
                context_key=f"ontology_package:{package_name}",
                kind=CodePackageConfigRuntimeContextKind.ontology_package,
                package_name=package_name,
            )
            for projection_name in projection_package.projection_names:
                _put_runtime_context(
                    rows,
                    code_package_config_id=code_package_config_id,
                    context_key=f"projection_package:{package_name}:{projection_name}",
                    kind=CodePackageConfigRuntimeContextKind.projection,
                    package_name=package_name,
                    projection_name=projection_name,
                )
        if descriptor.environment_handle is not None:
            _put_runtime_context(
                rows,
                code_package_config_id=code_package_config_id,
                context_key=f"environment:{descriptor.environment_handle}",
                kind=CodePackageConfigRuntimeContextKind.environment,
                runtime_contract_version=descriptor.environment_handle,
            )
    for descriptor in contract.materialization_runtime_context_for(
        semantic_owner=semantic_owner
    ):
        _put_runtime_context(
            rows,
            code_package_config_id=code_package_config_id,
            context_key=(
                "runtime_context:"
                f"{descriptor.callable_module}.{descriptor.callable_name}"
            ),
            kind=CodePackageConfigRuntimeContextKind.execution_context,
            required=descriptor.required,
        )
    for descriptor in contract.materialization_execution_context_for(
        semantic_owner=semantic_owner
    ):
        _put_runtime_context(
            rows,
            code_package_config_id=code_package_config_id,
            context_key=f"execution_context:{descriptor.context_key}",
            kind=CodePackageConfigRuntimeContextKind.execution_context,
            required=descriptor.required,
        )
    return tuple(rows[key] for key in sorted(rows))


def _put_output(
    rows: dict[str, CodePackageConfigOutput],
    *,
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
    required_for: tuple[str, ...] = (),
    required: bool = True,
) -> None:
    normalized_output_key = _required_text(output_key, field_name="output_key")
    rows.setdefault(
        normalized_output_key,
        CodePackageConfigOutput(
            id=stable_code_package_config_output_id(
                code_package_config_id=code_package_config_id,
                output_key=normalized_output_key,
            ),
            code_package_config_id=code_package_config_id,
            output_key=normalized_output_key,
            kind=kind,
            producer_key=_optional_text(producer_key),
            artifact_family=_optional_text(artifact_family),
            artifact_role=_optional_text(artifact_role),
            package_output_key=_optional_text(package_output_key),
            target_provider_key=_optional_text(target_provider_key),
            target_input_key=_optional_text(target_input_key),
            target_semantic_owner=_optional_text(target_semantic_owner),
            target_package_family=_optional_text(target_package_family),
            target_semantic_kind=_optional_text(target_semantic_kind),
            media_type=_optional_text(media_type),
            runtime_contract_version=_optional_text(runtime_contract_version),
            required_for=list(required_for),
            required=bool(required),
        ),
    )


def _put_runtime_context(
    rows: dict[str, CodePackageConfigRuntimeContext],
    *,
    code_package_config_id: UUID,
    context_key: str,
    kind: CodePackageConfigRuntimeContextKind,
    package_name: str | None = None,
    projection_name: str | None = None,
    runtime_contract_version: str | None = None,
    required: bool = True,
) -> None:
    normalized_context_key = _required_text(context_key, field_name="context_key")
    rows.setdefault(
        normalized_context_key,
        CodePackageConfigRuntimeContext(
            id=stable_code_package_config_runtime_context_id(
                code_package_config_id=code_package_config_id,
                context_key=normalized_context_key,
            ),
            code_package_config_id=code_package_config_id,
            context_key=normalized_context_key,
            kind=kind,
            package_name=_optional_text(package_name),
            projection_name=_optional_text(projection_name),
            runtime_contract_version=_optional_text(runtime_contract_version),
            required=bool(required),
        ),
    )


def _surface_for_manifest_resolution_descriptor(
    *,
    descriptor: object,
    package_kind: str | None,
    fallback_surface: str | None,
) -> str:
    direct = _code_package_surface(getattr(descriptor, "code_package_surface", None))
    if direct is not None:
        return direct
    surface_by_kind = getattr(
        descriptor,
        "code_package_surface_by_package_kind",
        None,
    )
    normalized_package_kind = _optional_text(package_kind)
    if normalized_package_kind is not None and isinstance(surface_by_kind, Mapping):
        by_kind = _code_package_surface(surface_by_kind.get(normalized_package_kind))
        if by_kind is not None:
            return by_kind
    fallback = _code_package_surface(fallback_surface)
    return fallback or "runtime"


def _source_manifest_resolution_descriptor(
    *,
    manifest_kind: str,
    surface: str,
) -> tuple[ModuleSemanticContract, ModuleSemanticManifestResolutionDescriptor]:
    from aware_code.module_plugin_registry import AwareModulePluginRegistry

    AwareModulePluginRegistry.ensure_builtin_plugins_registered()
    matches: list[
        tuple[ModuleSemanticContract, ModuleSemanticManifestResolutionDescriptor]
    ] = []
    for contract in AwareModulePluginRegistry.get_module_semantic_contracts():
        for descriptor in contract.manifest_resolution_for(
            manifest_kind=manifest_kind,
        ):
            descriptor_surface = _declared_surface_for_manifest_resolution_descriptor(
                descriptor=descriptor,
                package_kind=None,
            )
            descriptor_surfaces = _declared_surfaces_for_manifest_resolution_descriptor(
                descriptor=descriptor,
            )
            if descriptor_surface != surface and surface not in descriptor_surfaces:
                continue
            matches.append((contract, descriptor))
    if not matches:
        raise LookupError(
            "No semantic contract manifest-resolution descriptor owns "
            f"manifest_kind={manifest_kind!r} surface={surface!r}"
        )
    matches.sort(
        key=lambda item: (
            item[1].priority,
            item[0].provider_key,
            item[1].semantic_owner,
            item[1].manifest_kind,
        )
    )
    first = matches[0]
    conflicts = [
        item
        for item in matches[1:]
        if (
            item[0].provider_key,
            item[1].semantic_owner,
            item[1].manifest_kind,
            item[1].filename,
        )
        != (
            first[0].provider_key,
            first[1].semantic_owner,
            first[1].manifest_kind,
            first[1].filename,
        )
    ]
    if conflicts:
        conflict_keys = tuple(
            (
                item[0].provider_key,
                item[1].semantic_owner,
                item[1].manifest_kind,
                item[1].filename,
            )
            for item in matches
        )
        raise RuntimeError(
            "Multiple semantic contracts own the same code package config "
            f"manifest/surface: {conflict_keys!r}"
        )
    return first


def _declared_surface_for_manifest_resolution_descriptor(
    *,
    descriptor: ModuleSemanticManifestResolutionDescriptor,
    package_kind: str | None,
) -> str | None:
    direct = _code_package_surface(descriptor.code_package_surface)
    if direct is not None:
        return direct
    surface_by_kind = descriptor.code_package_surface_by_package_kind
    normalized_package_kind = _optional_text(package_kind)
    if normalized_package_kind is None or not isinstance(surface_by_kind, Mapping):
        return None
    return _code_package_surface(surface_by_kind.get(normalized_package_kind))


def _declared_surfaces_for_manifest_resolution_descriptor(
    *,
    descriptor: ModuleSemanticManifestResolutionDescriptor,
) -> frozenset[str]:
    surfaces: set[str] = set()
    direct = _code_package_surface(descriptor.code_package_surface)
    if direct is not None:
        surfaces.add(direct)
    surface_by_kind = descriptor.code_package_surface_by_package_kind
    if isinstance(surface_by_kind, Mapping):
        for value in surface_by_kind.values():
            surface = _code_package_surface(value)
            if surface is not None:
                surfaces.add(surface)
    return frozenset(surfaces)


def _input_kind_for_descriptor(descriptor: object) -> CodePackageConfigInputKind:
    raw_kind = _optional_text(getattr(descriptor, "input_kind", None))
    resolved = _input_kind(raw_kind)
    if resolved is not None:
        return resolved
    if _optional_text(getattr(descriptor, "artifact_family", None)) is not None:
        return CodePackageConfigInputKind.artifact
    if _optional_text(getattr(descriptor, "package_family", None)) is not None:
        return CodePackageConfigInputKind.package
    if raw_kind is not None and "delta" in raw_kind:
        return CodePackageConfigInputKind.delta
    if raw_kind is not None and "graph" in raw_kind:
        return CodePackageConfigInputKind.graph
    return CodePackageConfigInputKind.artifact


def _output_kind_for_artifact_descriptor(
    descriptor: object,
) -> CodePackageConfigOutputKind:
    raw_kind = _optional_text(getattr(descriptor, "output_kind", None))
    resolved = _output_kind(raw_kind)
    return resolved or CodePackageConfigOutputKind.artifact


def _materialization_capability_for_owner(
    *,
    contract: ModuleSemanticContract,
    semantic_owner: str,
) -> str | None:
    for descriptor in contract.capability_participation_for(
        capability=SEMANTIC_MATERIALIZATION_CAPABILITY
    ):
        if descriptor.semantic_owner == semantic_owner:
            return SEMANTIC_MATERIALIZATION_CAPABILITY
    return None


def _materialization_capability_for_contract_object(
    *,
    semantic_contract: object | None,
    semantic_owner: str,
) -> str | None:
    if semantic_contract is None:
        return None
    capability_participation = getattr(
        semantic_contract,
        "capability_participation",
        (),
    )
    for descriptor in capability_participation or ():
        if (
            getattr(descriptor, "capability", None)
            == SEMANTIC_MATERIALIZATION_CAPABILITY
            and getattr(descriptor, "semantic_owner", None) == semantic_owner
        ):
            return SEMANTIC_MATERIALIZATION_CAPABILITY
    return None


def _code_package_manifest_kind(value: str) -> str:
    return _required_text(str(value), field_name="manifest_kind")


def _code_package_surface(
    value: object,
) -> str | None:
    return normalize_code_package_surface(_optional_text(value))


def _input_kind(value: object) -> CodePackageConfigInputKind | None:
    normalized = _optional_text(value)
    if normalized is None:
        return None
    try:
        return CodePackageConfigInputKind(normalized)
    except ValueError:
        return None


def _output_kind(value: object) -> CodePackageConfigOutputKind | None:
    normalized = _optional_text(value)
    if normalized is None:
        return None
    try:
        return CodePackageConfigOutputKind(normalized)
    except ValueError:
        return None


def _required_text_attribute(target: object, attribute_name: str) -> str:
    return _required_text(
        getattr(target, attribute_name, None),
        field_name=attribute_name,
    )


def _required_text(value: object, *, field_name: str) -> str:
    normalized = _optional_text(value)
    if normalized is None:
        raise RuntimeError(f"CodePackageConfig lowering requires {field_name}")
    return normalized


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(
        value,
        (
            CodePackageConfigInputKind,
            CodePackageConfigOutputKind,
            CodePackageConfigRuntimeContextKind,
        ),
    ):
        return value.value
    normalized = str(value).strip()
    return normalized or None


__all__ = [
    "CodePackageConfigDescriptor",
    "CodePackageConfigRef",
    "PACKAGE_MANAGER_CODE_PACKAGE_SURFACE",
    "PACKAGE_MANAGER_PYPROJECT_MANIFEST_KIND",
    "PYPROJECT_MANIFEST_FILENAME",
    "build_code_package_config_from_semantic_contract",
    "build_code_package_configs_from_semantic_contract",
    "code_package_config_for_id",
    "code_package_config_descriptor_from_manifest_resolution_descriptor",
    "code_package_config_ref_from_manifest_resolution_descriptor",
    "package_manager_pyproject_code_package_config_ref",
    "source_code_package_config_descriptor",
    "source_code_package_config_ref",
]
