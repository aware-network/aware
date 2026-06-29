from __future__ import annotations

from collections.abc import Callable, Iterable
import time
from uuid import UUID

from typing_extensions import override

# Code Runtime
from aware_code.builder import build_code_from_content
from aware_code.code_module_contract import CodeModuleContract
from aware_code.language_service_provider_descriptor import (
    LanguageServiceProviderDescriptor,
)
from aware_code.module_semantic_contract import ModuleSemanticContract
from aware_code.module_plugin import (
    AwareModulePackageSemanticBindingContract,
    AwareModulePackageSemanticContract,
)
from aware_code.package.discovery import CodePackagePathResolution
from aware_code.package.schemas import CodePackageInfo
from aware_code.package.test_inventory import (
    CodePackageTestInventory,
    CodePackageTestFrameworkInventory,
    CodePackageTestUnitInventory,
)
from aware_code.semantic_scope.schemas import SemanticScopeResolution
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.semantic_package.schemas import SemanticPackageDescriptor
from aware_code.symbol_table import CodeSymbolTable
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_plan import CodePackageDelta
from aware_code_ontology.code.code_section_enums import CodeSectionType

# Language Service
from aware_code.language_service.features.completion import CompletionMixin
from aware_code.language_service.features.code_actions import CodeActionsMixin
from aware_code.language_service.features.config_diagnostics import (
    ConfigDiagnosticsMixin,
)
from aware_code.language_service.features.diagnostics import DiagnosticsMixin
from aware_code.language_service.features.formatting import FormattingMixin
from aware_code.language_service.features.navigation import NavigationMixin
from aware_code.language_service.features.refactor import RefactorMixin
from aware_code.language_service.features.semantic_tokens import SemanticTokensMixin
from aware_code.language_service.features.symbols import SymbolsMixin
from aware_code.language_service.capability_scope import (
    CapabilityExecutionPlan,
    CapabilityExecutionScope,
    WorkspaceCapabilitySelection,
    WorkspaceCapabilityConfiguration,
)
from aware_code.language_service.document import DocumentContext, DocumentContextCache
from aware_code.language_service.perf import PerfTracer

# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph_delta import (
    ObjectConfigGraphDelta,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph

# Meta Runtime
from aware_meta.symbol_resolver import build_symbol_resolver
from aware_meta.graph.config.builder import build_import_aliases_by_code_id
from aware_meta.class_.config.builder import build_class_config_from_code
from aware_meta.enum.config.builder import build_enum_config_from_code

from aware_workspace.compiler.session import (
    WorkspaceCompilerSession,
    WorkspaceCompilerUpdate,
)
from aware_workspace.compiler.workspace import Workspace, WorkspaceSnapshot
from aware_workspace.compiler.workspace import (
    WorkspaceCapabilityOwnerBundle,
    WorkspaceCapabilityOwnerPlan,
    WorkspaceCapabilityOwnerParticipation,
    WorkspaceCapabilityOwnerPolicyPlan,
    WorkspaceCapabilityOwnerProfile,
    WorkspaceCapabilityOwnerPreset,
    WorkspaceModulePackagePlan,
    WorkspaceModulePackageResolution,
    WorkspaceModulePackageSemanticBinding,
    WorkspaceModulePackageSemanticContract,
)


_WORKSPACE_CAPABILITY_PAYLOAD_KEYS: tuple[tuple[str, str], ...] = (
    ("diagnostics", "diagnostics"),
    ("semantic_tokens", "semanticTokens"),
)


def _exported_symbol_surface(code: Code) -> tuple[str, ...]:
    """Return the exported symbol surface for change impact checks.

    We keep this intentionally small: type resolution primarily depends on the
    presence/absence of classes/enums. This lets the server decide whether a
    change should trigger cross-file diagnostics refresh without re-linting the
    world on every keystroke.
    """

    entries: list[str] = []
    for section in code.code_sections:
        if section.type == CodeSectionType.class_:
            cls = section.code_section_class
            if cls is None:
                continue
            name = cls.name
            if name:
                entries.append(f"class:{name}")
            continue
        if section.type == CodeSectionType.enum:
            enum = section.code_section_enum
            if enum is None:
                continue
            name = enum.name
            if name:
                entries.append(f"enum:{name}")
            continue
    return tuple(sorted(entries))


def _retarget_code_ids(*, code: Code, code_id: UUID) -> None:
    """Retarget a newly parsed Code instance to a stable code_id (per-URI within a snapshot).

    The code builder generates fresh UUIDs for Codes and CodeSections. For incremental editor
    updates we keep the original code_id stable so namespace and import alias bindings remain
    addressable without rebuilding the entire resolver on every keystroke.
    """

    code.id = code_id
    for section in code.code_sections:
        section.code_id = code_id


def _sorted_scope_values(values: frozenset[str] | None) -> list[str] | None:
    return sorted(values) if values is not None else None


def _sorted_selection_values(values: tuple[str, ...] | None) -> list[str] | None:
    return list(values) if values is not None else None


def _capability_execution_scope_payload(
    scope: CapabilityExecutionScope | None,
) -> dict[str, object] | None:
    if scope is None:
        return None
    return {
        "semanticOwners": _sorted_scope_values(scope.semantic_owners),
        "providerKeys": _sorted_scope_values(scope.provider_keys),
    }


def _semantic_package_descriptor_payload(
    descriptor: SemanticPackageDescriptor,
) -> dict[str, object]:
    return {
        "providerKey": descriptor.provider_key,
        "family": descriptor.family,
        "semanticKind": descriptor.semantic_kind,
        "packageName": descriptor.package_name,
        "manifestRelativePath": descriptor.manifest_relative_path,
        "provenanceFieldName": descriptor.provenance_field_name,
        "semanticScopeKeys": list(descriptor.semantic_scope_keys),
        "capabilityParticipation": [
            {
                "capability": participation.capability,
                "semanticOwner": participation.semantic_owner,
                "defaultEnabled": participation.default_enabled,
            }
            for participation in descriptor.capability_participation
        ],
        "capabilityProfiles": [
            {
                "capability": profile.capability,
                "name": profile.name,
                "semanticOwners": list(profile.semantic_owners),
                "defaultSelected": profile.default_selected,
            }
            for profile in descriptor.capability_profiles
        ],
        "capabilityBundles": [
            {
                "capability": bundle.capability,
                "name": bundle.name,
                "profileNames": list(bundle.profile_names),
            }
            for bundle in descriptor.capability_bundles
        ],
    }


def _code_package_test_framework_payload(
    framework: CodePackageTestFrameworkInventory,
) -> dict[str, object]:
    return {
        "codeTestFrameworkId": str(framework.code_test_framework_id),
        "codePackageTestFrameworkId": str(framework.code_package_test_framework_id),
        "name": framework.name,
        "title": framework.title,
        "declarationKind": framework.declaration_kind,
        "declarationRef": framework.declaration_ref,
    }


def _code_package_test_unit_payload(
    unit: CodePackageTestUnitInventory,
) -> dict[str, object]:
    return {
        "codePackageCodeId": str(unit.code_package_code_id),
        "codeId": str(unit.code_id),
        "codeSectionId": str(unit.code_section_id),
        "codeTestFrameworkId": str(unit.code_test_framework_id),
        "codeTestId": str(unit.code_test_id),
        "codePackageTestId": str(unit.code_package_test_id),
        "codeTestUnitId": str(unit.code_test_unit_id),
        "frameworkName": unit.framework_name,
        "relativePath": unit.relative_path,
        "unitKey": unit.unit_key,
        "selector": unit.selector,
        "kind": unit.kind,
        "name": unit.name,
    }


def _code_package_test_inventory_payload(
    inventory: CodePackageTestInventory | None,
) -> dict[str, object] | None:
    if inventory is None:
        return None
    return {
        "codePackageId": str(inventory.code_package_id),
        "packageName": inventory.package_name,
        "language": inventory.language.value,
        "manifestKind": inventory.manifest_kind.value,
        "manifestRelativePath": inventory.manifest_relative_path,
        "packageRoot": inventory.package_root,
        "sourcesRoot": inventory.sources_root,
        "frameworks": [
            _code_package_test_framework_payload(framework)
            for framework in inventory.frameworks
        ],
        "units": [_code_package_test_unit_payload(unit) for unit in inventory.units],
    }


def _code_package_payload(
    code_package: CodePackageInfo | None,
    *,
    test_inventory: CodePackageTestInventory | None = None,
) -> dict[str, object] | None:
    if code_package is None:
        return None
    return {
        "name": code_package.name,
        "rootPath": code_package.root_path.as_posix(),
        "manifestPath": code_package.manifest_path.as_posix(),
        "language": code_package.language.value,
        "semanticPackageProviderKeys": sorted(
            {descriptor.provider_key for descriptor in code_package.semantic_packages}
        ),
        "semanticPackages": [
            _semantic_package_descriptor_payload(descriptor)
            for descriptor in code_package.semantic_packages
        ],
        "testInventory": _code_package_test_inventory_payload(test_inventory),
    }


def _workspace_capability_selection_payload(
    selection: WorkspaceCapabilitySelection,
) -> dict[str, object]:
    return {
        "ownerPresets": _sorted_selection_values(selection.owner_presets),
        "providerKeys": _sorted_scope_values(selection.provider_keys),
    }


def _capability_execution_plan_payload(
    plan: CapabilityExecutionPlan,
    *,
    configured_selection: WorkspaceCapabilitySelection,
) -> dict[str, object]:
    return {
        "workspaceSemanticPackageProviderKeys": _sorted_scope_values(
            plan.workspace_semantic_package_provider_keys
        ),
        "workspacePluginProviderKeys": _sorted_scope_values(
            plan.workspace_plugin_provider_keys
        ),
        "workspaceFallbackPluginProviderKeys": _sorted_scope_values(
            plan.workspace_fallback_plugin_provider_keys
        ),
        "packageResolution": _code_package_path_resolution_payload(
            plan.workspace_package_resolution,
            semantic_package_provider_keys=tuple(
                sorted(plan.workspace_semantic_package_provider_keys or ())
            ),
        ),
        "semanticScopes": _semantic_scope_resolutions_payload(
            plan.workspace_semantic_scope_resolutions
        ),
        "configuredSelection": _workspace_capability_selection_payload(
            configured_selection
        ),
        "configuredScope": _capability_execution_scope_payload(plan.configured_scope),
        "workspaceOwnerScope": _capability_execution_scope_payload(
            plan.workspace_owner_scope
        ),
        "workspaceResolvedScope": _capability_execution_scope_payload(
            plan.workspace_resolved_scope
        ),
        "effectiveScope": _capability_execution_scope_payload(plan.effective_scope),
        "providers": [
            {
                "providerKey": provider.provider_key,
                "semanticOwner": provider.semantic_owner,
                "requiredSemanticScopeKeys": list(
                    provider.required_semantic_scope_keys
                ),
                "missingSemanticScopeKeys": list(provider.missing_semantic_scope_keys),
                "priority": provider.priority,
                "appliesWhen": provider.applies_when,
                "workspaceActivation": provider.workspace_activation,
                "activatedByWorkspaceOwnerScope": provider.activated_by_workspace_owner_scope,
                "allowedByConfiguredScope": provider.allowed_by_configured_scope,
                "providerAvailable": provider.provider_available,
                "requiredSemanticScopesResolved": provider.required_semantic_scopes_resolved,
                "active": provider.active,
            }
            for provider in plan.providers
        ],
    }


def _workspace_capability_owner_preset_payload(
    preset: WorkspaceCapabilityOwnerPreset,
) -> dict[str, object]:
    return {
        "name": preset.name,
        "semanticOwners": list(preset.semantic_owners),
        "semanticPackageProviderKeys": list(preset.semantic_package_provider_keys),
        "defaultEnabledOnly": preset.default_enabled_only,
        "source": preset.source,
        "defaultSelected": preset.default_selected,
    }


def _workspace_capability_owner_profile_payload(
    item: WorkspaceCapabilityOwnerProfile,
) -> dict[str, object]:
    return {
        "name": item.name,
        "semanticOwners": list(item.semantic_owners),
        "defaultSelected": item.default_selected,
        "semanticPackageProviderKey": item.semantic_package_provider_key,
        "semanticPackageFamily": item.semantic_package_family,
        "semanticPackageKind": item.semantic_package_kind,
        "semanticPackageName": item.semantic_package_name,
        "manifestRelativePath": item.manifest_relative_path,
    }


def _workspace_capability_owner_bundle_payload(
    item: WorkspaceCapabilityOwnerBundle,
) -> dict[str, object]:
    return {
        "name": item.name,
        "profileNames": list(item.profile_names),
        "semanticOwners": list(item.semantic_owners),
        "unresolvedProfileNames": list(item.unresolved_profile_names),
        "semanticPackageProviderKey": item.semantic_package_provider_key,
        "semanticPackageFamily": item.semantic_package_family,
        "semanticPackageKind": item.semantic_package_kind,
        "semanticPackageName": item.semantic_package_name,
        "manifestRelativePath": item.manifest_relative_path,
    }


def _workspace_capability_owner_participation_payload(
    item: WorkspaceCapabilityOwnerParticipation,
) -> dict[str, object]:
    return {
        "semanticOwner": item.semantic_owner,
        "defaultEnabled": item.default_enabled,
        "semanticPackageProviderKey": item.semantic_package_provider_key,
        "semanticPackageFamily": item.semantic_package_family,
        "semanticPackageKind": item.semantic_package_kind,
        "semanticPackageName": item.semantic_package_name,
        "manifestRelativePath": item.manifest_relative_path,
    }


def _workspace_capability_owner_payload(
    *,
    plan: WorkspaceCapabilityOwnerPlan,
    capability: str,
    policy: WorkspaceCapabilityOwnerPolicyPlan,
) -> dict[str, object]:
    return {
        **_workspace_capability_owner_policy_plan_payload(policy),
        "profiles": [
            _workspace_capability_owner_profile_payload(item)
            for item in plan.profiles_for_capability(capability=capability)
        ],
        "bundles": [
            _workspace_capability_owner_bundle_payload(item)
            for item in plan.bundles_for_capability(capability=capability)
        ],
        "participations": [
            _workspace_capability_owner_participation_payload(item)
            for item in plan.participations_for_capability(capability=capability)
        ],
    }


def _workspace_capability_owner_policy_plan_payload(
    plan: WorkspaceCapabilityOwnerPolicyPlan,
) -> dict[str, object]:
    return {
        "availableOwnerPresets": [
            _workspace_capability_owner_preset_payload(preset)
            for preset in plan.available_owner_presets
        ],
        "configuredOwnerPresets": _sorted_selection_values(
            plan.configured_owner_presets
        ),
        "resolvedOwnerPresets": _sorted_selection_values(plan.resolved_owner_presets),
        "unknownOwnerPresets": _sorted_selection_values(plan.unknown_owner_presets),
        "defaultSemanticOwners": (
            list(plan.default_semantic_owners)
            if plan.default_semantic_owners is not None
            else None
        ),
        "effectiveSemanticOwners": (
            list(plan.effective_semantic_owners)
            if plan.effective_semantic_owners is not None
            else None
        ),
    }


def _semantic_scope_resolutions_payload(
    resolutions: tuple[SemanticScopeResolution, ...],
) -> dict[str, object]:
    return {
        resolution.scope_key: {
            "providerKey": resolution.provider_key,
            **dict(resolution.payload),
        }
        for resolution in resolutions
    }


def _code_package_path_resolution_payload(
    resolution: CodePackagePathResolution | None,
    *,
    semantic_package_provider_keys: tuple[str, ...],
) -> dict[str, object] | None:
    if resolution is None:
        return None
    return {
        "documentPath": resolution.document_path.as_posix(),
        "nearestPackageRoot": (
            resolution.nearest_package_root.as_posix()
            if resolution.nearest_package_root is not None
            else None
        ),
        "nearestManifestPath": (
            resolution.nearest_manifest_path.as_posix()
            if resolution.nearest_manifest_path is not None
            else None
        ),
        "nearestManifestDeclaredInWorkspace": resolution.nearest_manifest_declared_in_workspace,
        "owningPackageRoot": (
            resolution.owning_package_root.as_posix()
            if resolution.owning_package_root is not None
            else None
        ),
        "owningManifestPath": (
            resolution.owning_manifest_path.as_posix()
            if resolution.owning_manifest_path is not None
            else None
        ),
        "authoritativeWorkspaceRoot": (
            resolution.authoritative_workspace_root.as_posix()
            if resolution.authoritative_workspace_root is not None
            else None
        ),
        "authoritativeWorkspaceManifestPath": (
            resolution.authoritative_workspace_manifest_path.as_posix()
            if resolution.authoritative_workspace_manifest_path is not None
            else None
        ),
        "workspaceMembershipRequired": resolution.workspace_membership_required,
        "semanticPackageProviderKeys": list(semantic_package_provider_keys),
    }


def _module_semantic_contract_payload(
    contract: ModuleSemanticContract,
) -> dict[str, object]:
    return {
        "providerKey": contract.provider_key,
        "semanticScopeKeys": list(contract.semantic_scope_keys),
        "packageRoles": [
            {
                "role": descriptor.role,
                "contract": descriptor.contract,
                "packageKind": descriptor.package_kind,
                "capabilities": list(descriptor.capabilities),
            }
            for descriptor in contract.package_roles
        ],
        "capabilityParticipation": [
            {
                "capability": descriptor.capability,
                "semanticOwner": descriptor.semantic_owner,
                "defaultEnabled": descriptor.default_enabled,
            }
            for descriptor in contract.capability_participation
        ],
        "capabilityExecutionPolicy": [
            {
                "capability": descriptor.capability,
                "semanticOwner": descriptor.semantic_owner,
                "callableName": descriptor.callable_name,
                "requiredSemanticScopeKeys": list(
                    descriptor.required_semantic_scope_keys
                ),
                "priority": descriptor.priority,
                "appliesWhen": descriptor.applies_when,
            }
            for descriptor in contract.capability_execution_policy
        ],
        "capabilityProfiles": [
            {
                "capability": descriptor.capability,
                "name": descriptor.name,
                "semanticOwners": list(descriptor.semantic_owners),
                "defaultSelected": descriptor.default_selected,
            }
            for descriptor in contract.capability_profiles
        ],
        "capabilityBundles": [
            {
                "capability": descriptor.capability,
                "name": descriptor.name,
                "profileNames": list(descriptor.profile_names),
            }
            for descriptor in contract.capability_bundles
        ],
        "syntaxLanes": [
            {
                "laneKey": lane.lane_key,
                "semanticOwner": lane.semantic_owner,
                "compilerOwner": lane.compiler_owner,
                "grammarRules": list(lane.grammar_rules),
                "semanticTokenTypes": list(lane.semantic_token_types),
                "semanticTokenModifiers": list(lane.semantic_token_modifiers),
            }
            for lane in contract.syntax_lanes
        ],
    }


def _language_service_provider_descriptor_payload(
    descriptor: LanguageServiceProviderDescriptor,
) -> dict[str, object]:
    return {
        "capability": descriptor.capability,
        "moduleProviderKey": descriptor.module_provider_key,
        "providerKey": descriptor.provider_key,
        "semanticOwner": descriptor.semantic_owner,
        "requiredSemanticScopeKeys": list(descriptor.required_semantic_scope_keys),
        "priority": descriptor.priority,
        "appliesWhen": descriptor.applies_when,
        "workspaceActivation": descriptor.workspace_activation,
    }


def _code_module_contract_payload(
    contract: CodeModuleContract,
) -> dict[str, object]:
    return {
        "providerKey": contract.provider_key,
        "packages": [
            {
                "id": package.id,
                "kind": package.kind,
                "manifest": package.manifest,
                "visibility": package.visibility,
                "semanticContract": _workspace_module_package_semantic_contract_payload(
                    package.semantic_contract
                ),
                "semanticBindings": [
                    _workspace_module_package_semantic_binding_payload(binding)
                    for binding in package.semantic_bindings
                ],
                "mirrorsOntology": package.mirrors_ontology,
            }
            for package in contract.packages
        ],
        "capabilityContractModule": contract.capability_contract_module,
        "capabilityExecutionModule": contract.capability_execution_module,
        "semanticContractModule": contract.semantic_contract_module,
        "codePackageMaterializationContractModule": (
            contract.code_package_materialization_contract_module
        ),
        "workspaceFallbackCapabilities": sorted(
            {
                policy.capability
                for policy in contract.capability_policy
                if policy.workspace_fallback
            }
        ),
        "languageServiceProviderKeys": [
            descriptor.provider_key
            for descriptor in contract.language_service_provider_descriptors
        ],
    }


def _workspace_module_package_plan_payload(
    item: WorkspaceModulePackagePlan,
) -> dict[str, object]:
    return {
        "source": item.source,
        "moduleId": item.module_id,
        "moduleRootRelativePath": item.module_root_relative_path,
        "moduleTomlRelativePath": item.module_toml_relative_path,
        "packageId": item.package_id,
        "packageKind": item.package_kind,
        "packageName": item.package_name,
        "fqnPrefix": item.fqn_prefix,
        "manifestRelativePath": item.manifest_relative_path,
        "packageRootRelativePath": item.package_root_relative_path,
        "sourcesRootRelativePath": item.sources_root_relative_path,
        "declaredDependencyPackageNames": list(item.declared_dependency_package_names),
        "sourceFiles": list(item.source_files),
        "visibility": item.visibility,
        "semanticContract": _workspace_module_package_semantic_contract_payload(
            item.semantic_contract
        ),
        "semanticBindings": [
            _workspace_module_package_semantic_binding_payload(binding)
            for binding in item.semantic_bindings
        ],
        "mirrorsOntology": item.mirrors_ontology,
    }


def _workspace_module_package_semantic_binding_payload(
    item: (
        WorkspaceModulePackageSemanticBinding
        | AwareModulePackageSemanticBindingContract
    ),
) -> dict[str, object]:
    implemented = item.binding_module is not None
    return {
        "role": item.role,
        "contract": item.contract,
        "bindingModule": item.binding_module,
        "capabilities": list(item.capabilities),
        "callable": item.callable_name,
        "implemented": implemented,
        "implementationState": "implemented" if implemented else "declared",
    }


def _workspace_module_package_semantic_contract_payload(
    item: (
        WorkspaceModulePackageSemanticContract
        | AwareModulePackageSemanticContract
        | None
    ),
) -> dict[str, object] | None:
    if item is None:
        return None
    return {
        "role": item.role,
        "contract": item.contract,
        "providerKey": item.provider_key,
        "module": item.module,
        "bindings": [
            {
                "capability": binding.capability,
                "module": binding.module,
                "callable": binding.callable,
            }
            for binding in item.bindings
        ],
        "implemented": bool(item.bindings),
        "implementationState": "implemented" if item.bindings else "declared",
    }


def _workspace_module_package_resolution_payload(
    item: WorkspaceModulePackageResolution | None,
) -> dict[str, object] | None:
    if item is None:
        return None
    return {
        "source": item.source,
        "moduleId": item.module_id,
        "moduleRootRelativePath": item.module_root_relative_path,
        "moduleTomlRelativePath": item.module_toml_relative_path,
        "packageId": item.package_id,
        "packageKind": item.package_kind,
        "packageName": item.package_name,
        "fqnPrefix": item.fqn_prefix,
        "documentRelativePath": item.document_relative_path,
        "packageRelativePath": item.package_relative_path,
        "manifestRelativePath": item.manifest_relative_path,
        "packageRootRelativePath": item.package_root_relative_path,
        "sourcesRootRelativePath": item.sources_root_relative_path,
        "declaredDependencyPackageNames": list(item.declared_dependency_package_names),
        "visibility": item.visibility,
        "sourceFileDeclared": item.source_file_declared,
        "semanticContract": _workspace_module_package_semantic_contract_payload(
            item.semantic_contract
        ),
        "semanticBindings": [
            _workspace_module_package_semantic_binding_payload(binding)
            for binding in item.semantic_bindings
        ],
        "mirrorsOntology": item.mirrors_ontology,
    }


def _workspace_capability_owner_plan_payload(
    plan: WorkspaceCapabilityOwnerPlan,
    *,
    capability_policies: dict[str, WorkspaceCapabilityOwnerPolicyPlan],
) -> dict[str, object]:
    payload: dict[str, object] = {
        "semanticPackageProviderKeys": list(plan.semantic_package_provider_keys),
        "pluginProviderKeys": list(plan.plugin_provider_keys),
        "fallbackPluginProviderKeys": list(plan.fallback_plugin_provider_keys),
        "capabilityContractModules": list(plan.capability_contract_modules),
        "capabilityExecutionModules": list(plan.capability_execution_modules),
        "semanticContractModules": list(plan.semantic_contract_modules),
        "codeModuleContracts": [
            _code_module_contract_payload(contract)
            for contract in plan.code_module_contracts
        ],
        "workspaceModulePackages": [
            _workspace_module_package_plan_payload(item)
            for item in plan.workspace_module_packages
        ],
        "modulePackageResolution": _workspace_module_package_resolution_payload(
            plan.module_package_resolution
        ),
        "moduleCapabilityContracts": [
            {
                "providerKey": contract.provider_key,
                "contractModule": contract.contract_module,
                "capabilities": [
                    {
                        "capability": descriptor.capability,
                        "semanticOwner": descriptor.semantic_owner,
                        "resolvedProviderKey": descriptor.resolved_provider_key,
                        "requiredSemanticScopeKeys": list(
                            descriptor.required_semantic_scope_keys
                        ),
                        "priority": descriptor.priority,
                        "appliesWhen": descriptor.applies_when,
                        "workspaceActivation": descriptor.workspace_activation,
                        "defaultEnabled": descriptor.default_enabled,
                    }
                    for descriptor in contract.capability_metadata
                ],
            }
            for contract in plan.module_capability_contracts
        ],
        "moduleSemanticContracts": [
            _module_semantic_contract_payload(contract)
            for contract in plan.module_semantic_contracts
        ],
        "capabilityProviderDescriptors": [
            _language_service_provider_descriptor_payload(descriptor)
            for descriptor in plan.capability_provider_descriptors
        ],
        "packageResolution": _code_package_path_resolution_payload(
            plan.package_resolution,
            semantic_package_provider_keys=plan.semantic_package_provider_keys,
        ),
        "semanticScopes": _semantic_scope_resolutions_payload(
            plan.semantic_scope_resolutions
        ),
    }
    for capability, payload_key in _WORKSPACE_CAPABILITY_PAYLOAD_KEYS:
        payload[payload_key] = _workspace_capability_owner_payload(
            plan=plan,
            capability=capability,
            policy=capability_policies[capability],
        )
    return payload


_STALE_SNAPSHOT_FORCE_REBUILD_S = 1.0


class LanguageService(
    DiagnosticsMixin,
    ConfigDiagnosticsMixin,
    FormattingMixin,
    NavigationMixin,
    RefactorMixin,
    SymbolsMixin,
    CompletionMixin,
    CodeActionsMixin,
    SemanticTokensMixin,
):
    _workspace: Workspace
    _compiler_session: WorkspaceCompilerSession
    _compiler_updates_enabled: bool
    _snapshot_is_stale: bool
    _snapshot_stale_since: float | None
    _snapshot_stale_focus_uri: str | None
    _perf: PerfTracer
    _doc_cache: DocumentContextCache
    _snapshot: WorkspaceSnapshot | None
    _last_build_error: str | None
    _last_focus_uri: str | None
    _last_compiler_update: WorkspaceCompilerUpdate | None
    _last_code_package_delta: CodePackageDelta | None
    _last_object_config_graph: ObjectConfigGraph | None
    _last_object_config_graph_delta: ObjectConfigGraphDelta | None
    _workspace_capability_configuration: WorkspaceCapabilityConfiguration
    _workspace_capability_configuration_revision: int
    _workspace_capability_revision: int
    _capability_execution_plan_cache: dict[
        tuple[str, str, int, int], CapabilityExecutionPlan
    ]
    _workspace_capability_plan_payload_cache: dict[
        tuple[str, int, int], dict[str, object]
    ]

    def __init__(
        self,
        *,
        workspace: Workspace,
        compiler_session: WorkspaceCompilerSession | None = None,
        perf: PerfTracer | None = None,
    ) -> None:
        self._workspace = workspace
        self._compiler_session = compiler_session or WorkspaceCompilerSession(
            workspace=workspace
        )
        self._compiler_updates_enabled = False
        self._snapshot_is_stale = False
        self._snapshot_stale_since = None
        self._snapshot_stale_focus_uri = None
        self._perf = perf or PerfTracer()
        self._doc_cache = DocumentContextCache()
        self._snapshot = None
        self._last_build_error = None
        self._last_focus_uri = None
        self._last_compiler_update = None
        self._last_code_package_delta = None
        self._last_object_config_graph = None
        self._last_object_config_graph_delta = None
        self._workspace_capability_configuration = WorkspaceCapabilityConfiguration()
        self._workspace_capability_configuration_revision = 0
        self._workspace_capability_revision = workspace.capability_resolution_revision
        self._capability_execution_plan_cache = {}
        self._workspace_capability_plan_payload_cache = {}

    @property
    def workspace(self) -> Workspace:
        return self._workspace

    @property
    def snapshot(self) -> WorkspaceSnapshot | None:
        return self._snapshot

    @property
    def perf(self) -> PerfTracer:
        return self._perf

    @property
    def workspace_capability_configuration(self) -> WorkspaceCapabilityConfiguration:
        return self._workspace_capability_configuration

    @property
    def compiler_session(self) -> WorkspaceCompilerSession:
        return self._compiler_session

    def set_workspace_capability_configuration(
        self,
        *,
        configuration: WorkspaceCapabilityConfiguration,
    ) -> None:
        self._workspace_capability_configuration = configuration
        self._workspace_capability_configuration_revision += 1
        self._invalidate_workspace_capability_plan_caches()

    def configure_workspace_capabilities(
        self,
        *,
        diagnostics_owner_presets: Iterable[str] | None = None,
        diagnostics_provider_keys: Iterable[str] | None = None,
        semantic_tokens_owner_presets: Iterable[str] | None = None,
        semantic_tokens_provider_keys: Iterable[str] | None = None,
    ) -> None:
        self.set_workspace_capability_configuration(
            configuration=WorkspaceCapabilityConfiguration(
                diagnostics=WorkspaceCapabilitySelection.from_iterables(
                    owner_presets=diagnostics_owner_presets,
                    provider_keys=diagnostics_provider_keys,
                ),
                semantic_tokens=WorkspaceCapabilitySelection.from_iterables(
                    owner_presets=semantic_tokens_owner_presets,
                    provider_keys=semantic_tokens_provider_keys,
                ),
            )
        )

    def workspace_capability_plan_for_uri(self, *, uri: str) -> dict[str, object]:
        self._sync_workspace_capability_plan_cache_revision()
        cache_key = (
            uri,
            self._workspace_capability_configuration_revision,
            self._workspace_capability_revision,
        )
        cached = self._workspace_capability_plan_payload_cache.get(cache_key)
        if cached is not None:
            return cached

        workspace_owner_plan = self._workspace.capability_owner_plan_for_uri(uri=uri)
        code_package = workspace_owner_plan.code_package
        configured_selections: dict[str, WorkspaceCapabilitySelection] = {
            "diagnostics": self._workspace_capability_configuration.diagnostics,
            "semantic_tokens": self._workspace_capability_configuration.semantic_tokens,
        }
        capability_plan_builders: dict[str, Callable[..., CapabilityExecutionPlan]] = {
            "diagnostics": self.diagnostics_capability_plan,
            "semantic_tokens": self.semantic_tokens_capability_plan,
        }
        capability_plans: dict[str, CapabilityExecutionPlan] = {}
        capability_policies: dict[str, WorkspaceCapabilityOwnerPolicyPlan] = {}
        for capability, configured_selection in configured_selections.items():
            capability_plans[capability] = capability_plan_builders[capability](uri=uri)
            capability_policies[capability] = workspace_owner_plan.owner_policy_plan(
                capability=capability,
                configured_owner_presets=configured_selection.owner_presets,
            )
        payload: dict[str, object] = {
            "uri": uri,
            "workspaceRoot": str(self._workspace.workspace_root),
            "language": self._workspace.language.value,
            "codePackage": _code_package_payload(
                code_package,
                test_inventory=workspace_owner_plan.code_package_test_inventory,
            ),
            "workspaceOwnerPlan": _workspace_capability_owner_plan_payload(
                workspace_owner_plan,
                capability_policies=capability_policies,
            ),
        }
        for capability, payload_key in _WORKSPACE_CAPABILITY_PAYLOAD_KEYS:
            payload[payload_key] = _capability_execution_plan_payload(
                capability_plans[capability],
                configured_selection=configured_selections[capability],
            )
        self._workspace_capability_plan_payload_cache[cache_key] = payload
        return payload

    def is_aware_config_uri(self, uri: str) -> bool:
        return self._is_aware_config_uri(uri)

    def set_compiler_updates_enabled(self, enabled: bool) -> None:
        """Toggle compiler-session updates on didOpen/didSave boundaries.

        VS Code / Cursor should keep this disabled (default) so editor features do
        not trigger full OCG compilation work. Studio / Node clients can enable it
        when they need `aware/compilerUpdateAvailable` deltas.
        """

        self._compiler_updates_enabled = bool(enabled)

    def rebuild_snapshot(self, *, focus_uri: str | None = None) -> None:
        """Rebuild the symbol snapshot without producing compiler update records."""
        with self._perf.span("service.rebuild_snapshot", focus_uri=focus_uri):
            self._rebuild_snapshot_only(focus_uri=focus_uri)

    def _mark_snapshot_stale(self, *, focus_uri: str | None) -> None:
        if not self._snapshot_is_stale:
            self._snapshot_stale_since = time.monotonic()
        elif self._snapshot_stale_since is None:
            self._snapshot_stale_since = time.monotonic()
        self._snapshot_is_stale = True
        if focus_uri:
            self._snapshot_stale_focus_uri = focus_uri

    @override
    def _document_context(self, *, uri: str, document_text: str) -> DocumentContext:
        version = self._workspace.open_document_version(uri=uri)
        return self._doc_cache.get(uri=uri, version=version, text=document_text)

    def _code_key_for_uri(self, *, uri: str) -> str:
        if self._snapshot is not None:
            rel_path = self._snapshot.rel_path_by_uri.get(uri)
            if rel_path:
                return rel_path
        path = self._workspace.uri_to_path(uri)
        try:
            return path.relative_to(self._workspace.workspace_root).as_posix()
        except Exception:
            return path.as_posix()

    @property
    def last_compiler_update(self) -> WorkspaceCompilerUpdate | None:
        return self._last_compiler_update

    @property
    def last_code_package_delta(self) -> CodePackageDelta | None:
        return self._last_code_package_delta

    @property
    def last_object_config_graph(self) -> ObjectConfigGraph | None:
        return self._last_object_config_graph

    @property
    def last_object_config_graph_delta(self) -> ObjectConfigGraphDelta | None:
        return self._last_object_config_graph_delta

    def refresh(
        self, *, focus_uri: str | None = None, reason: str = "manual"
    ) -> WorkspaceCompilerUpdate | None:
        with self._perf.span("service.refresh", focus_uri=focus_uri, reason=reason):
            self._rebuild_full(focus_uri=focus_uri, reason=reason)
            return self._last_compiler_update

    def open_document(
        self,
        *,
        uri: str,
        version: int,
        text: str,
        defer_snapshot_rebuild: bool = False,
    ) -> None:
        with self._perf.span("service.open_document", uri=uri):
            self._last_focus_uri = uri
            self._doc_cache.evict(uri=uri)
            if self._is_aware_config_uri(uri):
                self._workspace.open_document(uri=uri, version=version, text=text)
                return
        # Opening a document with the exact on-disk contents shouldn't force a full rebuild.
        # We still track the overlay for LSP correctness (hover/definition use open-doc text),
        # but we avoid compiler churn when switching between files without edits.
        try:
            disk_text = self._workspace.get_document_text(uri)
        except Exception:
            disk_text = None

        self._workspace.open_document(uri=uri, version=version, text=text)
        self._validate_document_text(uri=uri, text=text)

        if self._snapshot is None or uri not in self._snapshot.codes_by_uri:
            if self._compiler_updates_enabled:
                self._rebuild_full(focus_uri=uri, reason="open")
            elif defer_snapshot_rebuild:
                self._mark_snapshot_stale(focus_uri=uri)
            else:
                self._rebuild_snapshot_only(focus_uri=uri)
            return

        if disk_text is None or disk_text != text:
            if self._compiler_updates_enabled:
                self._rebuild_full(focus_uri=uri, reason="open")
            elif defer_snapshot_rebuild:
                self._mark_snapshot_stale(focus_uri=uri)
            else:
                self._rebuild_snapshot_only(focus_uri=uri)

    def change_document(self, *, uri: str, version: int, text: str) -> bool:
        with self._perf.span("service.change_document", uri=uri):
            self._last_focus_uri = uri
            self._doc_cache.evict(uri=uri)
            if self._is_aware_config_uri(uri):
                self._workspace.change_document(uri=uri, version=version, text=text)
                return False

            old_surface: tuple[str, ...] | None = None
            if self._snapshot is not None:
                old_code = self._snapshot.codes_by_uri.get(uri)
                if old_code is not None:
                    old_surface = _exported_symbol_surface(old_code)

            self._workspace.change_document(uri=uri, version=version, text=text)
            self._validate_document_text(uri=uri, text=text)
            # Avoid rebuilding the entire workspace on every keystroke. We keep the
            # snapshot/resolver incremental for editor features, and only run the
            # full compiler session on open/save boundaries.
            if self._snapshot is None:
                self._rebuild_snapshot_only(focus_uri=uri)
                if self._snapshot is None:
                    return True
                new_code = self._snapshot.codes_by_uri.get(uri)
                if new_code is None:
                    return True
                return old_surface != _exported_symbol_surface(new_code)
            if self._last_build_error:
                return False
            if not self._update_snapshot_for_uri(uri=uri, text=text):
                self._rebuild_snapshot_only(focus_uri=uri)
                return True

            new_code = self._snapshot.codes_by_uri.get(uri)
            if new_code is None:
                return True
            return old_surface != _exported_symbol_surface(new_code)

    def close_document(self, *, uri: str) -> None:
        with self._perf.span("service.close_document", uri=uri):
            if self._last_focus_uri == uri:
                self._last_focus_uri = None
            self._doc_cache.evict(uri=uri)
            self._invalidate_workspace_capability_plan_caches_for_uri(uri=uri)
            if self._is_aware_config_uri(uri):
                self._workspace.close_document(uri=uri)
                return
        # Avoid rebuilding when closing an unmodified overlay. This keeps file navigation snappy.
        try:
            overlay_text = self._workspace.get_document_text(uri)
        except Exception:
            overlay_text = None

        self._workspace.close_document(uri=uri)
        # Clear any transient parse errors from open-doc overlays.
        self._last_build_error = None

        if self._snapshot is None:
            return

        try:
            disk_text = self._workspace.get_document_text(uri)
        except Exception:
            disk_text = None

        if overlay_text is None or disk_text is None:
            if self._compiler_updates_enabled:
                self._rebuild_full(focus_uri=uri, reason="close")
            else:
                self._rebuild_snapshot_only(focus_uri=uri)
            return
        if overlay_text != disk_text:
            if self._compiler_updates_enabled:
                self._rebuild_full(focus_uri=uri, reason="close")
            else:
                self._rebuild_snapshot_only(focus_uri=uri)

    def save_document(self, *, uri: str, text: str | None = None) -> None:
        with self._perf.span("service.save_document", uri=uri):
            self._last_focus_uri = uri
            self._doc_cache.evict(uri=uri)
            if self._is_aware_config_uri(uri):
                if text is not None:
                    self._workspace.change_document(uri=uri, version=0, text=text)
                    try:
                        _ = self._workspace.write_document_text(uri=uri, text=text)
                    except Exception:
                        pass
                try:
                    self._workspace.invalidate_environment_index_for_uri(uri=uri)
                except Exception:
                    pass
                if self._compiler_updates_enabled:
                    self._rebuild_full(focus_uri=uri, reason="save")
                else:
                    # Avoid blocking save/format-on-save on potentially expensive snapshot rebuilds.
                    # The LSP server will debounce a rebuild after config saves.
                    self._mark_snapshot_stale(focus_uri=uri)
                return
            if text is not None:
                # Some clients include the saved text payload. Treat it as an overlay update so
                # compiler inputs stay deterministic even if the filesystem write lags.
                self._workspace.change_document(uri=uri, version=0, text=text)
                self._validate_document_text(uri=uri, text=text)
            if self._compiler_updates_enabled:
                self._rebuild_full(focus_uri=uri, reason="save")
                return

            # Editor mode: avoid full compiler work; keep the symbol snapshot fresh.
            if text is None:
                try:
                    text = self._workspace.get_document_text(uri)
                except Exception:
                    text = None
            if text is None:
                self._rebuild_snapshot_only(focus_uri=uri)
                return
            if self._snapshot is None or not self._update_snapshot_for_uri(
                uri=uri, text=text
            ):
                self._rebuild_snapshot_only(focus_uri=uri)

    def watched_files_changed(
        self, *, uris: list[str], invalidate_environment_index: bool = False
    ) -> None:
        """Handle filesystem change notifications (new/renamed/deleted `.aware` files).

        These events originate from LSP clients (VS Code/Cursor, Studio) via
        `workspace/didChangeWatchedFiles`. We invalidate the environment cache and rebuild
        the symbol snapshot so cross-file resolution picks up new files without requiring
        a server restart or opening every file manually.
        """
        if not uris:
            return

        for uri in uris:
            self._doc_cache.evict(uri=uri)
            self._invalidate_workspace_capability_plan_caches_for_uri(uri=uri)

        if invalidate_environment_index:
            for uri in uris:
                try:
                    self._workspace.invalidate_environment_index_for_uri(uri=uri)
                except Exception:
                    continue

        config_uris = [u for u in uris if self._is_aware_config_uri(u)]
        if config_uris:
            # Config changes can affect package dependency closure and therefore the active
            # structural file set. Mark the snapshot stale and rebuild lazily (or via server-side
            # debounce) rather than blocking file-watcher notification handling.
            self._mark_snapshot_stale(focus_uri=config_uris[0])
            return
        focus_uri = (
            (config_uris[0] if config_uris else None) or self._last_focus_uri or uris[0]
        )

        # If we don't have a snapshot (or it doesn't include a changed file), fall back to
        # a snapshot rebuild so new files become visible.
        if self._snapshot is None or any(
            uri not in self._snapshot.codes_by_uri for uri in uris
        ):
            self._rebuild_snapshot_only(focus_uri=focus_uri)
            return

        # Otherwise update the snapshot incrementally for closed-file changes.
        for uri in uris:
            try:
                text = self._workspace.get_document_text(uri)
            except Exception:
                continue
            if not self._update_snapshot_for_uri(uri=uri, text=text):
                self._rebuild_snapshot_only(focus_uri=focus_uri)
                return

    def _validate_document_text(self, *, uri: str, text: str) -> None:
        sections_index = CodeSectionBuilderIndex()
        symbol_table = CodeSymbolTable()
        try:
            _ = build_code_from_content(
                sections_index=sections_index,
                content=text,
                code_key=self._code_key_for_uri(uri=uri),
                language=self._workspace.language,
                symbol_table=symbol_table,
            )
            self._last_build_error = None
        except Exception as exc:
            self._last_build_error = str(exc)

    @override
    def _cached_capability_execution_plan(
        self,
        *,
        capability: str,
        uri: str,
        build: Callable[[], CapabilityExecutionPlan],
    ) -> CapabilityExecutionPlan:
        self._sync_workspace_capability_plan_cache_revision()
        cache_key = (
            capability,
            uri,
            self._workspace_capability_configuration_revision,
            self._workspace_capability_revision,
        )
        cached = self._capability_execution_plan_cache.get(cache_key)
        if cached is not None:
            return cached
        plan = build()
        self._capability_execution_plan_cache[cache_key] = plan
        return plan

    def _invalidate_workspace_capability_plan_caches(self) -> None:
        self._capability_execution_plan_cache.clear()
        self._workspace_capability_plan_payload_cache.clear()

    def _invalidate_workspace_capability_plan_caches_for_uri(self, *, uri: str) -> None:
        execution_keys = [
            key for key in self._capability_execution_plan_cache if key[1] == uri
        ]
        for key in execution_keys:
            self._capability_execution_plan_cache.pop(key, None)
        payload_keys = [
            key
            for key in self._workspace_capability_plan_payload_cache
            if key[0] == uri
        ]
        for key in payload_keys:
            self._workspace_capability_plan_payload_cache.pop(key, None)

    def _sync_workspace_capability_plan_cache_revision(self) -> None:
        current_revision = self._workspace.capability_resolution_revision
        if current_revision == self._workspace_capability_revision:
            return
        self._workspace_capability_revision = current_revision
        self._invalidate_workspace_capability_plan_caches()

    @override
    def _ensure_snapshot_for_uri(self, *, uri: str) -> None:
        """Ensure the current snapshot includes the given URI (rebuild if necessary)."""
        if self._is_aware_config_uri(uri):
            return
        if self._snapshot is None:
            focus = self._snapshot_stale_focus_uri or uri
            self._rebuild_snapshot_only(focus_uri=focus)
            return
        if uri not in self._snapshot.codes_by_uri:
            focus = self._snapshot_stale_focus_uri or uri
            self._rebuild_snapshot_only(focus_uri=focus)
            return
        # When the snapshot is marked stale (typically due to aware.toml changes), avoid rebuilding
        # synchronously inside LSP request handlers. The stdio server debounces rebuilds while idle.
        if self._snapshot_is_stale:
            if self._snapshot_stale_since is None:
                return
            if (
                time.monotonic() - self._snapshot_stale_since
            ) < _STALE_SNAPSHOT_FORCE_REBUILD_S:
                return
            focus = self._snapshot_stale_focus_uri or uri
            self._rebuild_snapshot_only(focus_uri=focus)
            return

    def _rebuild_snapshot_only(self, *, focus_uri: str | None = None) -> None:
        """(Re)build the workspace snapshot without producing compiler update records."""
        current_error = self._last_build_error
        try:
            self._snapshot = self._workspace.build_snapshot(focus_uri=focus_uri)
        except Exception as exc:
            self._snapshot = None
            self._last_build_error = str(exc)
            return
        self._snapshot_is_stale = False
        self._snapshot_stale_focus_uri = None
        self._snapshot_stale_since = None
        self._last_build_error = current_error

    def _update_snapshot_for_uri(self, *, uri: str, text: str) -> bool:
        if self._snapshot is None:
            return False

        old_code = self._snapshot.codes_by_uri.get(uri)
        if old_code is None:
            return False
        code_id = old_code.id
        ns = self._snapshot.namespace_by_code_id.get(code_id)
        if ns is None:
            return False
        rel_path = self._snapshot.rel_path_by_uri.get(uri)
        if rel_path is None:
            return False

        with self._perf.span("service.parse_code", uri=uri):
            sections_index = CodeSectionBuilderIndex()
            symbol_table = CodeSymbolTable()
            try:
                new_code = build_code_from_content(
                    sections_index=sections_index,
                    content=text,
                    code_key=rel_path,
                    language=self._workspace.language,
                    symbol_table=symbol_table,
                )
            except Exception as exc:
                self._last_build_error = str(exc)
                return False

        _retarget_code_ids(code=new_code, code_id=code_id)

        old_surface = _exported_symbol_surface(old_code)
        new_surface = _exported_symbol_surface(new_code)
        surface_changed = old_surface != new_surface

        # Update in-place (fast path) so we avoid copying large dicts per keystroke.
        self._snapshot.codes_by_uri[uri] = new_code
        self._snapshot.text_by_uri[uri] = text

        # Import alias updates are resolver inputs (per-code scope).
        imports_changed = False
        new_import_aliases: dict[str, str] = {}
        try:
            by_code = build_import_aliases_by_code_id([(rel_path, new_code)])
            new_import_aliases = dict(by_code.get(code_id) or {})
        except Exception:
            new_import_aliases = {}

        try:
            old_import_aliases = dict(
                self._snapshot.fqn_resolver.import_aliases_for_code_id(code_id)
            )
        except Exception:
            old_import_aliases = {}
        imports_changed = new_import_aliases != old_import_aliases

        if not surface_changed:
            # Keep resolver indices stable; update per-code aliases and refresh class/enum payloads
            # for existing fqns so member completion/hover stays accurate while typing.
            if imports_changed:
                try:
                    self._snapshot.fqn_resolver.set_import_aliases_for_code_id(
                        code_id, new_import_aliases
                    )
                except Exception:
                    pass

            try:
                for section in new_code.code_sections:
                    if (
                        section.type == CodeSectionType.class_
                        and section.code_section_class is not None
                    ):
                        cls_cfg = build_class_config_from_code(
                            section.code_section_class, parent_class_id=None
                        )
                        fqn = ns.fqn(cls_cfg.name)
                        self._snapshot.fqn_resolver.update_class_config_for_fqn(
                            fqn, cls_cfg
                        )
                    if (
                        section.type == CodeSectionType.enum
                        and section.code_section_enum is not None
                    ):
                        enum_cfg = build_enum_config_from_code(
                            code_section_enum=section.code_section_enum,
                            namespace=ns,
                        )
                        fqn = ns.fqn(enum_cfg.name)
                        self._snapshot.fqn_resolver.update_enum_config_for_fqn(
                            fqn, enum_cfg
                        )
            except Exception:
                # Best-effort: completion/hover should not break typing.
                pass

            return True

        # Slow path: exported surface changed, rebuild resolver so global resolution updates.
        with self._perf.span("service.rebuild_symbol_resolver", uri=uri):
            file_codes = sorted(
                (
                    (self._snapshot.rel_path_by_uri[u], c)
                    for u, c in self._snapshot.codes_by_uri.items()
                ),
                key=lambda item: item[0],
            )
            fqn_resolver = build_symbol_resolver(
                file_codes=file_codes,
                namespace_by_code_id=self._snapshot.namespace_by_code_id,
            )

        # Replace the snapshot wrapper so the new resolver is visible (fields are frozen).
        self._snapshot = WorkspaceSnapshot(
            context=self._snapshot.context,
            fqn_resolver=fqn_resolver,
            codes_by_uri=self._snapshot.codes_by_uri,
            text_by_uri=self._snapshot.text_by_uri,
            uri_by_code_id=self._snapshot.uri_by_code_id,
            namespace_by_code_id=self._snapshot.namespace_by_code_id,
            rel_path_by_uri=self._snapshot.rel_path_by_uri,
        )
        return True

    @override
    def _rebuild_full(
        self, *, focus_uri: str | None = None, reason: str = "change"
    ) -> None:
        current_error = self._last_build_error
        try:
            update = self._compiler_session.update(focus_uri=focus_uri, reason=reason)
        except Exception as exc:
            self._snapshot = None
            self._last_build_error = str(exc)
            self._last_compiler_update = None
            self._last_code_package_delta = None
            self._last_object_config_graph = None
            self._last_object_config_graph_delta = None
            return

        self._snapshot = update.snapshot
        # Preserve document-parse errors; compiler update is allowed to succeed even when a single
        # open document fails to parse (best-effort).
        self._last_build_error = current_error

        self._last_compiler_update = update
        self._last_code_package_delta = update.record.workspace_delta.code_package_delta
        self._last_object_config_graph = update.object_config_graph
        self._last_object_config_graph_delta = update.record.object_config_graph_delta
