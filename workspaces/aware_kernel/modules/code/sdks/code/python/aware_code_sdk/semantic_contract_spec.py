from __future__ import annotations

from hashlib import sha256
import json
from pathlib import PurePosixPath
from typing import Mapping, cast

from aware_code_sdk.dto import (
    CodeCapabilityBundleDescriptor,
    CodeCapabilityExecutionPolicyDescriptor,
    CodeCapabilityParticipationDescriptor,
    CodeCapabilityProfileDescriptor,
    CodeLanguage,
    CodeSemanticArtifactLeafOwnershipDescriptor,
    CodeSemanticContract,
    CodeSemanticGeneratedCodePackageDeclaration,
    CodeSemanticContractSpecDeclaration,
    CodeSemanticContractSpecSection,
    CodeSemanticManifestResolutionDescriptor,
    CodeSemanticMaterializationArtifactOutputDescriptor,
    CodeSemanticMaterializationCodePackageDeltaOutputDescriptor,
    CodeSemanticMaterializationExecutionContextDescriptor,
    CodeSemanticMaterializationInputDescriptor,
    CodeSemanticMaterializationPackageOutputDescriptor,
    CodeSemanticMaterializationRuntimeContextDescriptor,
    CodeSemanticMaterializationRuntimeDescriptor,
    CodeSemanticPackageRoleDescriptor,
    CodeSemanticProviderBinding,
    CodeSemanticRuntimeProjectionPackageDescriptor,
    CodeSemanticSyntaxLaneDescriptor,
    CodeSemanticWorkflowDescriptor,
    CodeSemanticWorkflowInstructionDescriptor,
)
from aware_types import JsonObject, JsonValue

_GENERATED_CODE_PACKAGE_PUBLIC_MANIFEST_KINDS = frozenset(
    {"pyproject_toml", "setup_py", "pubspec_yaml"}
)


def render_code_semantic_contract_spec_declaration(
    *,
    semantic_contract: CodeSemanticContract | object,
    provider_binding: CodeSemanticProviderBinding | None = None,
) -> CodeSemanticContractSpecDeclaration:
    """Render consumer-facing SPEC text from Code semantic contract truth."""

    source_contract_kind = type(semantic_contract).__name__
    semantic_contract = normalize_code_semantic_contract(semantic_contract)
    digest = _contract_digest(semantic_contract)
    generated_code_packages = code_semantic_generated_code_package_declarations(
        provider_binding=provider_binding,
    )
    sections = [
        _source_of_truth_section(
            semantic_contract=semantic_contract,
            provider_binding=provider_binding,
            digest=digest,
        ),
        _package_roles_section(semantic_contract),
        _manifest_resolution_section(semantic_contract),
        _capabilities_section(semantic_contract),
        _materialization_section(semantic_contract),
        _runtime_requirements_section(semantic_contract),
        _generated_code_packages_section(generated_code_packages),
        _semantic_workflows_section(semantic_contract),
        _artifact_ownership_section(semantic_contract),
    ]
    summary = (
        f"`{semantic_contract.provider_key}` declares "
        f"{len(semantic_contract.package_roles)} package role(s), "
        f"{len(semantic_contract.manifest_resolution)} manifest resolution(s), "
        f"{len(semantic_contract.materialization_inputs)} materialization input(s), "
        f"{len(semantic_contract.materialization_artifact_outputs)} artifact "
        "output(s), and "
        f"{len(semantic_contract.materialization_code_package_delta_outputs)} "
        "CodePackageDelta output(s), and "
        f"{len(generated_code_packages)} generated Code package declaration(s), and "
        f"{len(semantic_contract.semantic_workflows)} workflow(s)."
    )
    markdown = _markdown(
        title=f"Semantic Contract: {semantic_contract.provider_key}",
        summary=summary,
        sections=sections,
    )
    return CodeSemanticContractSpecDeclaration(
        provider_key=semantic_contract.provider_key,
        title=f"Semantic Contract: {semantic_contract.provider_key}",
        summary=summary,
        markdown=markdown,
        sections=sections,
        generated_code_packages=list(generated_code_packages),
        source_contract_digest=digest,
        metadata=JsonObject(
            {
                "source": "aware_code_sdk.semantic_contract_spec",
                "source_contract": source_contract_kind,
                "normalized_contract": "CodeSemanticContract",
                "spec_format": "markdown",
            }
        ),
    )


def code_semantic_generated_code_package_declarations(
    *,
    provider_binding: CodeSemanticProviderBinding | None = None,
    source_manifest_path: str | None = None,
    semantic_owner: str | None = None,
    semantic_package_metadata: Mapping[str, object] | None = None,
) -> tuple[CodeSemanticGeneratedCodePackageDeclaration, ...]:
    metadata = (
        semantic_package_metadata
        if semantic_package_metadata is not None
        else (
            provider_binding.semantic_package_metadata
            if provider_binding is not None
            else None
        )
    )
    if not isinstance(metadata, Mapping):
        return ()
    resolved_source_manifest_path = source_manifest_path
    if resolved_source_manifest_path is None and provider_binding is not None:
        resolved_source_manifest_path = provider_binding.manifest_relative_path
    package_root = _metadata_text(metadata, "package_root") or _parent_path(
        resolved_source_manifest_path
    )
    raw_targets = metadata.get("language_materialization_targets")
    if not isinstance(raw_targets, (list, tuple)):
        return ()
    declarations: list[CodeSemanticGeneratedCodePackageDeclaration] = []
    for raw_target in raw_targets:
        declaration = _generated_code_package_declaration_from_target(
            source_manifest_path=resolved_source_manifest_path,
            semantic_owner=semantic_owner,
            package_root=package_root,
            target=raw_target,
        )
        if declaration is not None:
            declarations.append(declaration)
    return tuple(
        sorted(
            declarations,
            key=lambda item: (
                item.manifest_path,
                item.package_name,
                item.language.value,
                item.role or "",
            ),
        )
    )


def normalize_code_semantic_contract(
    semantic_contract: CodeSemanticContract | object,
) -> CodeSemanticContract:
    """Normalize a local module contract shape into the generated Code DTO."""

    if isinstance(semantic_contract, CodeSemanticContract):
        return semantic_contract
    provider_key = _required_attr(semantic_contract, "provider_key")
    return CodeSemanticContract(
        provider_key=provider_key,
        semantic_scope_keys=_list_attr(semantic_contract, "semantic_scope_keys"),
        capability_participation=[
            CodeCapabilityParticipationDescriptor(
                capability=_required_attr(item, "capability"),
                semantic_owner=_required_attr(item, "semantic_owner"),
                metadata=_json_object_or_none(_attr(item, "metadata")),
            )
            for item in _items_attr(semantic_contract, "capability_participation")
        ],
        capability_execution_policy=[
            CodeCapabilityExecutionPolicyDescriptor(
                capability=_required_attr(item, "capability"),
                semantic_owner=_required_attr(item, "semantic_owner"),
                callable_module=_optional_str_attr(item, "callable_module"),
                callable_name=_optional_str_attr(item, "callable_name"),
                required_semantic_scope_keys=_list_attr(
                    item,
                    "required_semantic_scope_keys",
                ),
                priority=_int_attr(item, "priority", default=100),
                applies_when=_str_attr(item, "applies_when", default="always"),
            )
            for item in _items_attr(semantic_contract, "capability_execution_policy")
        ],
        capability_profiles=[
            CodeCapabilityProfileDescriptor(
                capability=_required_attr(item, "capability"),
                name=_required_attr(item, "name"),
                semantic_owners=_list_attr(item, "semantic_owners"),
                metadata=_json_object_or_none(_attr(item, "metadata")),
            )
            for item in _items_attr(semantic_contract, "capability_profiles")
        ],
        capability_bundles=[
            CodeCapabilityBundleDescriptor(
                capability=_required_attr(item, "capability"),
                name=_required_attr(item, "name"),
                capabilities=_list_attr(
                    item,
                    "capabilities",
                    fallback_name="profile_names",
                ),
                semantic_owners=_list_attr(item, "semantic_owners"),
                metadata=_json_object_or_none(_attr(item, "metadata")),
            )
            for item in _items_attr(semantic_contract, "capability_bundles")
        ],
        syntax_lanes=[
            CodeSemanticSyntaxLaneDescriptor(
                lane_key=_required_attr(item, "lane_key"),
                semantic_owner=_required_attr(item, "semantic_owner"),
                compiler_owner=_required_attr(item, "compiler_owner"),
                grammar_rules=_list_attr(item, "grammar_rules"),
                semantic_token_types=_list_attr(item, "semantic_token_types"),
                semantic_token_modifiers=_list_attr(item, "semantic_token_modifiers"),
            )
            for item in _items_attr(semantic_contract, "syntax_lanes")
        ],
        package_roles=[
            CodeSemanticPackageRoleDescriptor(
                role=_required_attr(item, "role"),
                contract=_required_attr(item, "contract"),
                package_kind=_optional_str_attr(item, "package_kind"),
                capabilities=_list_attr(item, "capabilities"),
                owns_manifest_kinds=_list_attr(item, "owns_manifest_kinds"),
            )
            for item in _items_attr(semantic_contract, "package_roles")
        ],
        semantic_workflows=[
            CodeSemanticWorkflowDescriptor(
                workflow_key=_required_attr(item, "workflow_key"),
                semantic_owner=_required_attr(item, "semantic_owner"),
                stage_keys=_list_attr(item, "stage_keys"),
                instructions=[
                    CodeSemanticWorkflowInstructionDescriptor(
                        instruction_key=_required_attr(
                            instruction,
                            "instruction_key",
                        ),
                        title=_required_attr(instruction, "title"),
                        body=_required_attr(instruction, "body"),
                        instruction_kind=_str_attr(
                            instruction,
                            "instruction_kind",
                            default="natural_language",
                        ),
                        audience=_str_attr(
                            instruction,
                            "audience",
                            default="agent",
                        ),
                        stage_keys=_list_attr(instruction, "stage_keys"),
                        required=_bool_attr(
                            instruction,
                            "required",
                            default=True,
                        ),
                        source_refs=_list_attr(instruction, "source_refs"),
                        metadata=_json_object_or_none(
                            _attr(instruction, "metadata"),
                        ),
                    )
                    for instruction in _items_attr(item, "instructions")
                ],
                description=_optional_str_attr(item, "description"),
                instruction_refs=_list_attr(item, "instruction_refs"),
                capability_refs=_list_attr(item, "capability_refs"),
                capability_profile_refs=_list_attr(item, "capability_profile_refs"),
                grammar_profile_refs=_list_attr(item, "grammar_profile_refs"),
                source_meaning_refs=_list_attr(item, "source_meaning_refs"),
                ontology_feature_refs=_list_attr(item, "ontology_feature_refs"),
                graph_binding_refs=_list_attr(item, "graph_binding_refs"),
                expected_artifact_refs=_list_attr(item, "expected_artifact_refs"),
                expected_proof_refs=_list_attr(item, "expected_proof_refs"),
                expected_receipt_refs=_list_attr(item, "expected_receipt_refs"),
                diagnostic_refs=_list_attr(item, "diagnostic_refs"),
                policy_refs=_list_attr(item, "policy_refs"),
                required=_bool_attr(item, "required", default=True),
                priority=_int_attr(item, "priority", default=100),
                provider_payload=_json_object_or_none(_attr(item, "provider_payload")),
            )
            for item in _items_attr(semantic_contract, "semantic_workflows")
        ],
        artifact_leaf_ownership=[
            CodeSemanticArtifactLeafOwnershipDescriptor(
                semantic_owner=_required_attr(item, "semantic_owner"),
                owner_manifest_kinds=_list_attr(item, "owner_manifest_kinds"),
                artifact_manifest_kinds=_list_attr(item, "artifact_manifest_kinds"),
                callable_module=_required_attr(item, "callable_module"),
                callable_name=_required_attr(item, "callable_name"),
                priority=_int_attr(item, "priority", default=100),
                ownership_role=_str_attr(
                    item,
                    "ownership_role",
                    default="semantic_generated_artifact",
                ),
            )
            for item in _items_attr(semantic_contract, "artifact_leaf_ownership")
        ],
        materialization_artifact_outputs=[
            CodeSemanticMaterializationArtifactOutputDescriptor(
                semantic_owner=_required_attr(item, "semantic_owner"),
                producer_key=_required_attr(item, "producer_key"),
                output_key=_required_attr(item, "output_key"),
                artifact_family=_required_attr(item, "artifact_family"),
                producer_provider_key=_optional_str_attr(
                    item,
                    "producer_provider_key",
                ),
                artifact_role=_str_attr(item, "artifact_role", default="runtime"),
                output_kind=_str_attr(item, "output_kind", default="artifact"),
                package_output_key=_optional_str_attr(item, "package_output_key"),
                artifact_relpath=_optional_str_attr(item, "artifact_relpath"),
                artifact_path_pattern=_optional_str_attr(
                    item,
                    "artifact_path_pattern",
                ),
                manifest_relpath=_optional_str_attr(item, "manifest_relpath"),
                media_type=_optional_str_attr(item, "media_type"),
                runtime_contract_version=_optional_str_attr(
                    item,
                    "runtime_contract_version",
                ),
                required_for=_list_attr(item, "required_for"),
                required=_bool_attr(item, "required", default=True),
                priority=_int_attr(item, "priority", default=100),
                provider_payload=_json_object_or_none(_attr(item, "provider_payload")),
            )
            for item in _items_attr(
                semantic_contract,
                "materialization_artifact_outputs",
            )
        ],
        materialization_code_package_delta_outputs=[
            CodeSemanticMaterializationCodePackageDeltaOutputDescriptor(
                semantic_owner=_required_attr(item, "semantic_owner"),
                producer_key=_required_attr(item, "producer_key"),
                output_key=_required_attr(item, "output_key"),
                producer_provider_key=_optional_str_attr(
                    item,
                    "producer_provider_key",
                ),
                authority_kind=_str_attr(
                    item,
                    "authority_kind",
                    default="semantic_materialization",
                ),
                package_output_key=_optional_str_attr(item, "package_output_key"),
                runtime_contract_version=_optional_str_attr(
                    item,
                    "runtime_contract_version",
                ),
                required_for=_list_attr(item, "required_for"),
                required=_bool_attr(item, "required", default=True),
                priority=_int_attr(item, "priority", default=100),
                provider_payload=_json_object_or_none(_attr(item, "provider_payload")),
            )
            for item in _items_attr(
                semantic_contract,
                "materialization_code_package_delta_outputs",
            )
        ],
        materialization_inputs=[
            CodeSemanticMaterializationInputDescriptor(
                semantic_owner=_required_attr(item, "semantic_owner"),
                input_key=_required_attr(item, "input_key"),
                input_kind=_str_attr(item, "input_kind", default="artifact"),
                artifact_family=_optional_str_attr(item, "artifact_family"),
                artifact_role=_optional_str_attr(item, "artifact_role"),
                package_family=_optional_str_attr(item, "package_family"),
                semantic_kind=_optional_str_attr(item, "semantic_kind"),
                runtime_contract_version=_optional_str_attr(
                    item,
                    "runtime_contract_version",
                ),
                callable_module=_optional_str_attr(item, "callable_module"),
                callable_name=_optional_str_attr(item, "callable_name"),
                required=_bool_attr(item, "required", default=True),
                priority=_int_attr(item, "priority", default=100),
                provider_payload=_json_object_or_none(_attr(item, "provider_payload")),
            )
            for item in _items_attr(semantic_contract, "materialization_inputs")
        ],
        materialization_package_outputs=[
            CodeSemanticMaterializationPackageOutputDescriptor(
                semantic_owner=_required_attr(item, "semantic_owner"),
                producer_key=_required_attr(item, "producer_key"),
                output_key=_required_attr(item, "output_key"),
                target_provider_key=_required_attr(item, "target_provider_key"),
                target_input_key=_required_attr(item, "target_input_key"),
                target_semantic_owner=_optional_str_attr(
                    item,
                    "target_semantic_owner",
                ),
                target_package_family=_optional_str_attr(
                    item,
                    "target_package_family",
                ),
                target_semantic_kind=_optional_str_attr(item, "target_semantic_kind"),
                input_artifact_producer_key=_optional_str_attr(
                    item,
                    "input_artifact_producer_key",
                ),
                input_artifact_output_key=_optional_str_attr(
                    item,
                    "input_artifact_output_key",
                ),
                input_artifact_family=_optional_str_attr(
                    item,
                    "input_artifact_family",
                ),
                runtime_contract_version=_optional_str_attr(
                    item,
                    "runtime_contract_version",
                ),
                required_for=_list_attr(item, "required_for"),
                required=_bool_attr(item, "required", default=True),
                priority=_int_attr(item, "priority", default=100),
                provider_payload=_json_object_or_none(_attr(item, "provider_payload")),
            )
            for item in _items_attr(
                semantic_contract,
                "materialization_package_outputs",
            )
        ],
        materialization_runtime=[
            CodeSemanticMaterializationRuntimeDescriptor(
                semantic_owner=_required_attr(item, "semantic_owner"),
                runtime_ontology_package_names=_list_attr(
                    item,
                    "runtime_ontology_package_names",
                ),
                lane_projection_name=_optional_str_attr(
                    item,
                    "lane_projection_name",
                ),
                required_projection_names=_list_attr(
                    item,
                    "required_projection_names",
                ),
                runtime_projection_packages=[
                    CodeSemanticRuntimeProjectionPackageDescriptor(
                        package_name=_required_attr(
                            runtime_package,
                            "package_name",
                        ),
                        projection_names=_list_attr(
                            runtime_package,
                            "projection_names",
                        ),
                    )
                    for runtime_package in _items_attr(
                        item,
                        "runtime_projection_packages",
                    )
                ],
                environment_handle=_optional_str_attr(item, "environment_handle"),
                include_package_dependency_closure=_bool_attr(
                    item,
                    "include_package_dependency_closure",
                    default=False,
                ),
                priority=_int_attr(item, "priority", default=100),
            )
            for item in _items_attr(semantic_contract, "materialization_runtime")
        ],
        materialization_runtime_context=[
            CodeSemanticMaterializationRuntimeContextDescriptor(
                semantic_owner=_required_attr(item, "semantic_owner"),
                callable_module=_required_attr(item, "callable_module"),
                callable_name=_required_attr(item, "callable_name"),
                required=_bool_attr(item, "required", default=False),
                priority=_int_attr(item, "priority", default=100),
                provider_payload=_json_object_or_none(_attr(item, "provider_payload")),
            )
            for item in _items_attr(
                semantic_contract,
                "materialization_runtime_context",
            )
        ],
        materialization_execution_context=[
            CodeSemanticMaterializationExecutionContextDescriptor(
                semantic_owner=_required_attr(item, "semantic_owner"),
                context_key=_required_attr(item, "context_key"),
                callable_module=_required_attr(item, "callable_module"),
                callable_name=_required_attr(item, "callable_name"),
                required=_bool_attr(item, "required", default=False),
                priority=_int_attr(item, "priority", default=100),
                provider_payload=_json_object_or_none(_attr(item, "provider_payload")),
            )
            for item in _items_attr(
                semantic_contract,
                "materialization_execution_context",
            )
        ],
        manifest_resolution=[
            CodeSemanticManifestResolutionDescriptor(
                semantic_owner=_required_attr(item, "semantic_owner"),
                manifest_kind=_required_attr(item, "manifest_kind"),
                filename=_required_attr(item, "filename"),
                contract=_required_attr(item, "contract"),
                loader_module=_required_attr(item, "loader_module"),
                loader_name=_required_attr(item, "loader_name"),
                workspace_manifest_kind=_optional_str_attr(
                    item,
                    "workspace_manifest_kind",
                ),
                package_role=_optional_str_attr(item, "package_role"),
                semantic_package_family=_optional_str_attr(
                    item,
                    "semantic_package_family",
                ),
                semantic_package_kind=_optional_str_attr(
                    item,
                    "semantic_package_kind",
                ),
                semantic_projection_name=_optional_str_attr(
                    item,
                    "semantic_projection_name",
                ),
                semantic_root_kind=_optional_str_attr(item, "semantic_root_kind"),
                code_package_surface=_optional_str_attr(item, "code_package_surface"),
                code_package_surface_by_package_kind=_json_object_or_none(
                    _attr(item, "code_package_surface_by_package_kind"),
                ),
                workspace_materialization_order=_optional_int_attr(
                    item,
                    "workspace_materialization_order",
                ),
                workspace_materialization_branch=_optional_str_attr(
                    item,
                    "workspace_materialization_branch",
                ),
                workspace_materialization_commit=_optional_bool_attr(
                    item,
                    "workspace_materialization_commit",
                ),
                workspace_materialization_primary=_optional_bool_attr(
                    item,
                    "workspace_materialization_primary",
                ),
                copy_code_package_metadata_keys=_list_attr(
                    item,
                    "copy_code_package_metadata_keys",
                ),
                semantic_package_metadata=_json_object_or_none(
                    _attr(item, "semantic_package_metadata"),
                ),
                priority=_int_attr(item, "priority", default=100),
            )
            for item in _items_attr(semantic_contract, "manifest_resolution")
        ],
        metadata=_json_object_or_none(_attr(semantic_contract, "metadata"))
        or JsonObject({"source": "aware_code_sdk.semantic_contract_spec"}),
    )


def _generated_code_package_declaration_from_target(
    *,
    source_manifest_path: str | None,
    semantic_owner: str | None,
    package_root: str,
    target: object,
) -> CodeSemanticGeneratedCodePackageDeclaration | None:
    if not isinstance(target, Mapping):
        return None
    language_text = _metadata_text(target, "language")
    package_name = _metadata_text(target, "package_name")
    output_dir = _metadata_text(target, "output_dir")
    if language_text is None or package_name is None or output_dir is None:
        return None
    try:
        language = CodeLanguage(language_text)
        normalized_output_dir = _relative_path(output_dir)
        normalized_package_root = _relative_path(package_root)
    except ValueError:
        return None
    source_is_runtime = target.get("source_is_runtime") is True
    generated_package_root = _join_paths(normalized_package_root, normalized_output_dir)
    manifest_kind, manifest_path = _generated_code_package_manifest(
        language=language,
        package_root=generated_package_root,
        source_is_runtime=source_is_runtime,
    )
    return CodeSemanticGeneratedCodePackageDeclaration(
        source_manifest_path=source_manifest_path,
        semantic_owner=semantic_owner,
        role=_metadata_text(target, "role"),
        language=language,
        package_name=package_name,
        package_root=generated_package_root,
        sources_root=_metadata_text(target, "import_root"),
        manifest_kind=manifest_kind,
        manifest_path=manifest_path,
        code_package_surface=(
            _metadata_text(target, "code_package_surface")
            or _metadata_text(target, "surface")
        ),
        materialization_source=_metadata_text(target, "materialization_source"),
        renderer_kind=_metadata_text(target, "renderer_kind"),
        renderer_profile=_metadata_text(target, "renderer_profile"),
        source_is_runtime=source_is_runtime,
        public_checkout_default=(
            not source_is_runtime
            and manifest_kind in _GENERATED_CODE_PACKAGE_PUBLIC_MANIFEST_KINDS
        ),
        metadata=JsonObject(
            {
                "source": "language_materialization_targets",
            }
        ),
    )


def _generated_code_package_manifest(
    *,
    language: CodeLanguage,
    package_root: str,
    source_is_runtime: bool,
) -> tuple[str, str]:
    if source_is_runtime:
        return "generated_materialization", package_root
    if language == CodeLanguage.python:
        return "pyproject_toml", _join_paths(package_root, "pyproject.toml")
    if language == CodeLanguage.dart:
        return "pubspec_yaml", _join_paths(package_root, "pubspec.yaml")
    return "generated_materialization", package_root


def _parent_path(value: str | None) -> str:
    if value is None:
        return "."
    try:
        parent = PurePosixPath(_relative_path(value)).parent.as_posix()
    except ValueError:
        return "."
    return "." if parent in {"", "."} else parent


def _join_paths(*parts: str) -> str:
    normalized_parts = [part.strip("/") for part in parts if part.strip("/")]
    return "/".join(normalized_parts) or "."


def _relative_path(value: str) -> str:
    path = PurePosixPath(value.strip().replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"path must be relative: {value!r}")
    normalized = path.as_posix().strip("/")
    return "." if normalized in {"", "."} else normalized


def _metadata_text(metadata: Mapping[object, object], key: str) -> str | None:
    value = metadata.get(key)
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _source_of_truth_section(
    *,
    semantic_contract: CodeSemanticContract,
    provider_binding: CodeSemanticProviderBinding | None,
    digest: str,
) -> CodeSemanticContractSpecSection:
    lines = [
        f"- Provider key: `{semantic_contract.provider_key}`",
        f"- Source contract digest: `{digest}`",
    ]
    if semantic_contract.semantic_scope_keys:
        lines.append(
            "- Semantic scope keys: "
            f"{_code_list(semantic_contract.semantic_scope_keys)}"
        )
    if provider_binding is not None:
        lines.extend(
            line
            for line in (
                _optional_line("Provider role", provider_binding.provider_role),
                _optional_line("Provider name", provider_binding.provider_name),
                _optional_line("Provider module", provider_binding.provider_module),
                _optional_line("Package FQN", provider_binding.package_fqn),
                _optional_line("Manifest kind", provider_binding.manifest_kind),
                _optional_line(
                    "Manifest path",
                    provider_binding.manifest_relative_path,
                ),
            )
            if line is not None
        )
    return _section(
        section_key="source_of_truth",
        title="Source Of Truth",
        body="\n".join(lines),
        item_count=1,
        source_fields=[
            "provider_key",
            "semantic_scope_keys",
            "provider_binding",
        ],
    )


def _package_roles_section(
    semantic_contract: CodeSemanticContract,
) -> CodeSemanticContractSpecSection:
    if not semantic_contract.package_roles:
        body = "No package roles are declared."
    else:
        lines = []
        for item in semantic_contract.package_roles:
            lines.append(
                f"- `{item.role}` owns contract `{item.contract}`"
                f"{_suffix('package kind', item.package_kind)}"
                f"{_suffix('manifest kinds', _join_values(item.owns_manifest_kinds))}"
                f"{_suffix('capabilities', _join_values(item.capabilities))}."
            )
        body = "\n".join(lines)
    return _section(
        section_key="package_roles",
        title="Package Roles",
        body=body,
        item_count=len(semantic_contract.package_roles),
        source_fields=["package_roles"],
    )


def _manifest_resolution_section(
    semantic_contract: CodeSemanticContract,
) -> CodeSemanticContractSpecSection:
    if not semantic_contract.manifest_resolution:
        body = "No manifest resolution entries are declared."
    else:
        lines = []
        for item in semantic_contract.manifest_resolution:
            surface = item.code_package_surface
            if surface is None and item.code_package_surface_by_package_kind:
                surface = json.dumps(
                    dict(item.code_package_surface_by_package_kind),
                    sort_keys=True,
                )
            workspace_bits = [
                _key_value("order", item.workspace_materialization_order),
                _key_value("branch", item.workspace_materialization_branch),
                _key_value("commit", item.workspace_materialization_commit),
                _key_value("primary", item.workspace_materialization_primary),
            ]
            lines.append(
                f"- `{item.manifest_kind}` via `{item.filename}` resolves "
                f"`{item.contract}` for `{item.semantic_owner}`"
                f"{_suffix('role', item.package_role)}"
                f"{_suffix('family', item.semantic_package_family)}"
                f"{_suffix('kind', item.semantic_package_kind)}"
                f"{_suffix('projection', item.semantic_projection_name)}"
                f"{_suffix('root', item.semantic_root_kind)}"
                f"{_suffix('surface', surface)}"
                f"{_suffix('workspace', _join_values(workspace_bits))}."
            )
        body = "\n".join(lines)
    return _section(
        section_key="manifest_resolution",
        title="Manifest Resolution",
        body=body,
        item_count=len(semantic_contract.manifest_resolution),
        source_fields=["manifest_resolution"],
    )


def _capabilities_section(
    semantic_contract: CodeSemanticContract,
) -> CodeSemanticContractSpecSection:
    groups: list[str] = []
    if semantic_contract.capability_participation:
        groups.append(
            "Capability participation:\n"
            + "\n".join(
                f"- `{item.capability}` is owned by `{item.semantic_owner}`."
                for item in semantic_contract.capability_participation
            )
        )
    if semantic_contract.capability_execution_policy:
        groups.append(
            "Execution policy:\n"
            + "\n".join(
                f"- `{item.capability}` / `{item.semantic_owner}` runs "
                f"`{_callable_ref(item.callable_module, item.callable_name)}` "
                f"with priority `{item.priority}` when `{item.applies_when}`."
                for item in semantic_contract.capability_execution_policy
            )
        )
    if semantic_contract.capability_profiles:
        groups.append(
            "Capability profiles:\n"
            + "\n".join(
                f"- `{item.capability}` profile `{item.name}` selects "
                f"{_code_list(item.semantic_owners)}."
                for item in semantic_contract.capability_profiles
            )
        )
    if semantic_contract.capability_bundles:
        groups.append(
            "Capability bundles:\n"
            + "\n".join(
                f"- `{item.capability}` bundle `{item.name}` includes "
                f"{_code_list(item.capabilities)}."
                for item in semantic_contract.capability_bundles
            )
        )
    body = "\n\n".join(groups) if groups else "No capabilities are declared."
    return _section(
        section_key="capabilities",
        title="Capabilities",
        body=body,
        item_count=(
            len(semantic_contract.capability_participation)
            + len(semantic_contract.capability_execution_policy)
            + len(semantic_contract.capability_profiles)
            + len(semantic_contract.capability_bundles)
        ),
        source_fields=[
            "capability_participation",
            "capability_execution_policy",
            "capability_profiles",
            "capability_bundles",
        ],
    )


def _materialization_section(
    semantic_contract: CodeSemanticContract,
) -> CodeSemanticContractSpecSection:
    groups: list[str] = []
    if semantic_contract.materialization_inputs:
        groups.append(
            "Inputs:\n"
            + "\n".join(
                f"- `{item.input_key}` accepts `{item.input_kind}` for "
                f"`{item.semantic_owner}`"
                f"{_suffix('artifact family', item.artifact_family)}"
                f"{_suffix('package family', item.package_family)}"
                f"{_suffix('semantic kind', item.semantic_kind)}."
                for item in semantic_contract.materialization_inputs
            )
        )
    if semantic_contract.materialization_artifact_outputs:
        groups.append(
            "Artifact outputs:\n"
            + "\n".join(
                f"- `{item.producer_key}` emits `{item.output_key}` as "
                f"`{item.artifact_family}`"
                f"{_suffix('producer provider', item.producer_provider_key)}"
                f"{_suffix('role', item.artifact_role)}"
                f"{_suffix('path', item.artifact_relpath)}"
                f"{_suffix('pattern', item.artifact_path_pattern)}"
                f"{_suffix('required for', _join_values(item.required_for))}."
                for item in semantic_contract.materialization_artifact_outputs
            )
        )
    if semantic_contract.materialization_code_package_delta_outputs:
        groups.append(
            "CodePackageDelta outputs:\n"
            + "\n".join(
                f"- `{item.producer_key}` emits `{item.output_key}` as "
                f"`{item.authority_kind}`"
                f"{_suffix('producer provider', item.producer_provider_key)}"
                f"{_suffix('package output', item.package_output_key)}"
                f"{_suffix('required for', _join_values(item.required_for))}."
                for item in (
                    semantic_contract.materialization_code_package_delta_outputs
                )
            )
        )
    if semantic_contract.materialization_package_outputs:
        groups.append(
            "Package outputs:\n"
            + "\n".join(
                f"- `{item.producer_key}` emits `{item.output_key}` for "
                f"`{item.target_provider_key}:{item.target_input_key}`"
                f"{_suffix('target owner', item.target_semantic_owner)}"
                f"{_suffix('target family', item.target_package_family)}"
                f"{_suffix('target kind', item.target_semantic_kind)}."
                for item in semantic_contract.materialization_package_outputs
            )
        )
    body = "\n\n".join(groups) if groups else "No materialization I/O is declared."
    return _section(
        section_key="materialization",
        title="Materialization",
        body=body,
        item_count=(
            len(semantic_contract.materialization_inputs)
            + len(semantic_contract.materialization_artifact_outputs)
            + len(semantic_contract.materialization_code_package_delta_outputs)
            + len(semantic_contract.materialization_package_outputs)
        ),
        source_fields=[
            "materialization_inputs",
            "materialization_artifact_outputs",
            "materialization_code_package_delta_outputs",
            "materialization_package_outputs",
        ],
    )


def _runtime_requirements_section(
    semantic_contract: CodeSemanticContract,
) -> CodeSemanticContractSpecSection:
    groups: list[str] = []
    if semantic_contract.materialization_runtime:
        groups.append(
            "Runtime requirements:\n"
            + "\n".join(
                f"- `{item.semantic_owner}` requires ontology packages "
                f"{_code_list(item.runtime_ontology_package_names)}"
                f"{_suffix('lane projection', item.lane_projection_name)}"
                f"{_suffix('required projections', _join_values(item.required_projection_names))}"
                f"{_suffix('environment', item.environment_handle)}."
                for item in semantic_contract.materialization_runtime
            )
        )
    if semantic_contract.materialization_runtime_context:
        groups.append(
            "Runtime context resolvers:\n"
            + "\n".join(
                f"- `{item.semantic_owner}` uses "
                f"`{_callable_ref(item.callable_module, item.callable_name)}`"
                f"{_suffix('required', item.required)}."
                for item in semantic_contract.materialization_runtime_context
            )
        )
    if semantic_contract.materialization_execution_context:
        groups.append(
            "Execution context resolvers:\n"
            + "\n".join(
                f"- `{item.context_key}` for `{item.semantic_owner}` uses "
                f"`{_callable_ref(item.callable_module, item.callable_name)}`"
                f"{_suffix('required', item.required)}."
                for item in semantic_contract.materialization_execution_context
            )
        )
    body = "\n\n".join(groups) if groups else "No runtime requirements are declared."
    return _section(
        section_key="runtime_requirements",
        title="Runtime Requirements",
        body=body,
        item_count=(
            len(semantic_contract.materialization_runtime)
            + len(semantic_contract.materialization_runtime_context)
            + len(semantic_contract.materialization_execution_context)
        ),
        source_fields=[
            "materialization_runtime",
            "materialization_runtime_context",
            "materialization_execution_context",
        ],
    )


def _generated_code_packages_section(
    generated_code_packages: tuple[CodeSemanticGeneratedCodePackageDeclaration, ...],
) -> CodeSemanticContractSpecSection:
    if not generated_code_packages:
        body = "No generated Code package declarations are available."
    else:
        lines = []
        for item in generated_code_packages:
            lines.append(
                f"- `{item.package_name}` / `{item.language.value}`"
                f"{_suffix('role', item.role)}"
                f"{_suffix('manifest', item.manifest_path)}"
                f"{_suffix('package root', item.package_root)}"
                f"{_suffix('sources root', item.sources_root)}"
                f"{_suffix('surface', item.code_package_surface)}"
                f"{_suffix('public checkout', item.public_checkout_default)}."
            )
        body = "\n".join(lines)
    return _section(
        section_key="generated_code_packages",
        title="Generated Code Packages",
        body=body,
        item_count=len(generated_code_packages),
        source_fields=[
            "provider_binding.semantic_package_metadata.language_materialization_targets"
        ],
    )


def _semantic_workflows_section(
    semantic_contract: CodeSemanticContract,
) -> CodeSemanticContractSpecSection:
    if not semantic_contract.semantic_workflows:
        body = "No semantic workflows are declared."
    else:
        lines = []
        for item in semantic_contract.semantic_workflows:
            instruction_keys = [
                instruction.instruction_key for instruction in item.instructions
            ]
            lines.append(
                f"- `{item.workflow_key}` for `{item.semantic_owner}` covers "
                f"stages {_code_list(item.stage_keys)}"
                f"{_suffix('instructions', _join_values(instruction_keys))}"
                f"{_suffix('expected artifacts', _join_values(item.expected_artifact_refs))}"
                f"{_suffix('proofs', _join_values(item.expected_proof_refs))}"
                f"{_suffix('receipts', _join_values(item.expected_receipt_refs))}."
            )
        body = "\n".join(lines)
    return _section(
        section_key="semantic_workflows",
        title="Semantic Workflows",
        body=body,
        item_count=len(semantic_contract.semantic_workflows),
        source_fields=["semantic_workflows"],
    )


def _artifact_ownership_section(
    semantic_contract: CodeSemanticContract,
) -> CodeSemanticContractSpecSection:
    if not semantic_contract.artifact_leaf_ownership:
        body = "No generated artifact leaf ownership rules are declared."
    else:
        lines = []
        for item in semantic_contract.artifact_leaf_ownership:
            lines.append(
                f"- `{item.semantic_owner}` claims `{item.ownership_role}` for "
                f"owner manifests {_code_list(item.owner_manifest_kinds)} and "
                f"artifact manifests {_code_list(item.artifact_manifest_kinds)} "
                f"through `{_callable_ref(item.callable_module, item.callable_name)}`."
            )
        body = "\n".join(lines)
    return _section(
        section_key="artifact_ownership",
        title="Artifact Ownership",
        body=body,
        item_count=len(semantic_contract.artifact_leaf_ownership),
        source_fields=["artifact_leaf_ownership"],
    )


def _section(
    *,
    section_key: str,
    title: str,
    body: str,
    item_count: int,
    source_fields: list[str],
) -> CodeSemanticContractSpecSection:
    return CodeSemanticContractSpecSection(
        section_key=section_key,
        title=title,
        body=body,
        item_count=item_count,
        source_fields=source_fields,
    )


def _markdown(
    *,
    title: str,
    summary: str,
    sections: list[CodeSemanticContractSpecSection],
) -> str:
    blocks = [f"# {title}", summary]
    blocks.extend(f"## {section.title}\n\n{section.body}" for section in sections)
    return "\n\n".join(blocks).rstrip() + "\n"


def _contract_digest(semantic_contract: CodeSemanticContract) -> str:
    payload = semantic_contract.model_dump(
        mode="json",
        exclude_none=True,
        exclude_defaults=False,
    )
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _attr(source: object, name: str) -> object | None:
    return getattr(source, name, None)


def _required_attr(source: object, name: str) -> str:
    value = _optional_str_attr(source, name)
    if value is None:
        raise TypeError(
            f"semantic contract field `{name}` is required on "
            f"{type(source).__name__}"
        )
    return value


def _optional_str_attr(source: object, name: str) -> str | None:
    value = _attr(source, name)
    if value is None:
        return None
    return _text(value)


def _str_attr(source: object, name: str, *, default: str) -> str:
    return _optional_str_attr(source, name) or default


def _optional_bool_attr(source: object, name: str) -> bool | None:
    value = _attr(source, name)
    if value is None:
        return None
    return bool(value)


def _bool_attr(source: object, name: str, *, default: bool) -> bool:
    value = _optional_bool_attr(source, name)
    if value is None:
        return default
    return value


def _optional_int_attr(source: object, name: str) -> int | None:
    value = _attr(source, name)
    if value is None:
        return None
    return int(value)


def _int_attr(source: object, name: str, *, default: int) -> int:
    value = _optional_int_attr(source, name)
    if value is None:
        return default
    return value


def _items_attr(source: object, name: str) -> list[object]:
    value = _attr(source, name)
    if value is None:
        return []
    if isinstance(value, list | tuple):
        return list(value)
    return [value]


def _list_attr(
    source: object,
    name: str,
    *,
    fallback_name: str | None = None,
) -> list[str]:
    value = _attr(source, name)
    if value is None and fallback_name is not None:
        value = _attr(source, fallback_name)
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list | tuple):
        return [str(item) for item in value]
    return [str(value)]


def _json_object_or_none(value: object | None) -> JsonObject | None:
    if value is None or not isinstance(value, Mapping):
        return None
    payload = dict(value)
    if not payload:
        return None
    return JsonObject(cast(dict[str, JsonValue], payload))


def _optional_line(label: str, value: object) -> str | None:
    text = _text(value)
    if text is None:
        return None
    return f"- {label}: `{text}`"


def _suffix(label: str, value: object) -> str:
    text = _text(value)
    if text is None:
        return ""
    return f"; {label} `{text}`"


def _key_value(label: str, value: object) -> str | None:
    text = _text(value)
    if text is None:
        return None
    return f"{label}={text}"


def _callable_ref(module: str | None, name: str | None) -> str:
    if module and name:
        return f"{module}.{name}"
    return module or name or "not_declared"


def _join_values(values: object) -> str | None:
    if not isinstance(values, list):
        if isinstance(values, tuple):
            values = list(values)
        else:
            return _text(values)
    normalized = [str(item) for item in values if _text(item) is not None]
    if not normalized:
        return None
    return ", ".join(normalized)


def _code_list(values: list[str]) -> str:
    if not values:
        return "`none`"
    return ", ".join(f"`{value}`" for value in values)


def _text(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return str(value)


__all__ = [
    "code_semantic_generated_code_package_declarations",
    "normalize_code_semantic_contract",
    "render_code_semantic_contract_spec_declaration",
]
