from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
from time import perf_counter
from typing import cast

from aware_code.builder import build_code_from_content
from aware_code.parse.sections import collect_top_level_section_identity_descriptors
from aware_code.package.discovery import discover_packages_from_manifest_paths
from aware_code.package.schemas import CodePackageInfo
from aware_code.manifest_resolution import resolve_semantic_manifest
from aware_code.manifest_summary import (
    code_package_info_from_semantic_manifest_resolution,
)
from aware_code.module_plugin import AwareModulePlugin
from aware_code.package_surface import normalize_code_package_surface
from aware_code.segment.capability_registry import (
    DEFAULT_CODE_SECTION_SEGMENT_CAPABILITY_REGISTRY,
    CodeSectionSegmentCapabilityRegistry,
)
from aware_code.segment.render_policy import (
    CodeSegmentRenderPolicy as RuntimeCodeSegmentRenderPolicy,
    code_segment_render_policies,
    digest_matches as _segment_render_digest_matches,
    jsonable_policy_metadata,
    resolve_code_segment_render_policy,
    sha256_text_digest as _segment_render_sha256_digest,
)
from aware_code.segment.scanner import CodeSegmentScanner
from aware_code.semantic_contract import AWARE_CODE_SEMANTIC_CONTRACT
from aware_code.semantic_capability import (
    SEMANTIC_ANALYSIS_CAPABILITY,
    SemanticAnalysisCapabilityResult,
    SemanticAnalysisCapabilityRequest,
    SemanticCapabilityActionBinding,
    SemanticCapabilityChangePreview,
    SemanticCapabilityDependencyGraph,
    SemanticCapabilityDependencyRequirement,
    SemanticCapabilityDelta,
    SemanticCapabilityDiagnostic,
    SemanticCapabilityEvent,
    SemanticCapabilityEventVerb,
    SemanticCapabilityFunctionCallBinding,
    SemanticCapabilityTypedOperation,
)
from aware_code.semantic_materialization import (
    SEMANTIC_SOURCE_SESSION_CONTEXT_KEY,
    SemanticSourceSessionContext,
)
from aware_code.semantic_package.schemas import SemanticPackageDescriptor
from aware_code.semantic_scope import (
    SemanticScopeMaterializationDependency as RuntimeSemanticScopeMaterializationDependency,
    SemanticScopeRegistry,
    SemanticScopeResolution as RuntimeSemanticScopeResolution,
)
from aware_code.semantic_source_meaning import (
    CODE_SEMANTIC_SOURCE_DELTA_MEANING_CONTRACT_VERSION,
    CODE_SEMANTIC_SOURCE_MEANING_BINDING_CONTRACT_VERSION,
    CodeSemanticSourceIndexRef as RuntimeCodeSemanticSourceIndexRef,
    CodeSemanticSourceMeaningBinding as RuntimeCodeSemanticSourceMeaningBinding,
    CodeSemanticSourceMeaningContract as RuntimeCodeSemanticSourceMeaningContract,
    CodeSemanticSourceMeaningTypedOperationBinding as RuntimeCodeSemanticSourceMeaningTypedOperationBinding,
    resolve_code_semantic_source_delta_meaning,
    resolve_code_semantic_source_meaning,
)
from aware_code.module_plugin_registry import AwareModulePluginRegistry
from aware_code.module_semantic_contract import ModuleSemanticContract
from aware_code.source_index import (
    CodeGrammarGraphSelector,
    CodeGrammarSource,
    CodeGrammarSourceIndex,
    CodeGrammarSourceIndexCache,
    CodeGrammarTemplateValueBinding,
)
from aware_code.source_ownership import (
    CodeSourceOwnershipObservedPath as RuntimeCodeSourceOwnershipObservedPath,
    CodeSourceOwnershipPackageBinding as RuntimeCodeSourceOwnershipPackageBinding,
    classify_source_ownership,
)
from aware_code.setup_language_plugins import setup_code_plugins
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_plan import (
    CodePackageDelta as RuntimeCodePackageDelta,
)
from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_code_sdk.dto import (
    ClassifyCodeSourceOwnershipRequest,
    ClassifyCodeSourceOwnershipResponse,
    CodeGeneratedMaterializationActionBinding,
    CodeGeneratedMaterializationDeltaEntry,
    CodeGeneratedMaterializationDeltaMode,
    CodeGeneratedMaterializationDeltaRequest,
    CodeGeneratedMaterializationDeltaResult,
    CodeGeneratedMaterializationEventRef,
    CodeGeneratedMaterializationSkippedTarget,
    CodeGeneratedMaterializationTargetRef,
    CodeGeneratedRendererAnchorRef,
    CodeGeneratedRendererDeltaOperation,
    CodeGeneratedRendererDeltaOperationKind,
    ResolveCodeGrammarAnchorBindingEvidenceRequest,
    ResolveCodeGrammarAnchorBindingEvidenceResponse,
    ResolveCodeGrammarAnchorRenderDeltaRequest,
    ResolveCodeGrammarAnchorRenderDeltaResponse,
    CodeLanguage as ApiCodeLanguage,
    CodePackageDelta,
    CodePackageDeltaAuthorityKind,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
    CodePackageLayoutContract,
    CodePackageLayoutPathRole,
    CodePackagePathRole,
    CodeSemanticActionBinding,
    CodeSemanticAnalysisChangePreview,
    CodeSemanticAnalysisDependencyRequirement,
    CodeSemanticAnalysisDiagnostic,
    CodeSemanticSourceDeltaMeaningResolutionMode,
    CodeSemanticSourceIndexRef,
    CodeSemanticSourceMeaningBinding,
    CodeSemanticSourceMeaningContract,
    CodeSemanticSourceMeaningSource,
    CodeSemanticContract,
    CodeSemanticDelta,
    CodeSemanticEvent,
    CodeSemanticFunctionCallBinding,
    CodeSemanticTypedOperation,
    CodeSemanticManifestResolutionMatch,
    CodeSemanticMaterializationScopeDependency,
    CodeSemanticProviderBinding,
    CodeSemanticScopePackageRef,
    CodeSemanticScopeResolution,
    CodeSourceProjectionActionBinding,
    CodeSourceProjectionEventRef,
    CodeSourceProjectionRequest,
    CodeSourceProjectionResult,
    CodeSourceProjectionSkippedEvent,
    CodeSourceOwnershipClassification as ApiCodeSourceOwnershipClassification,
    CodeSourceOwnershipObservedPath,
    CodeSourceOwnershipPackageBinding,
    CodeSourceOwnershipPathMatch,
    CodeSourceOwnershipRequest,
    CodeSourceOwnershipResult,
    CodeSectionDeltaEntry,
    CodeSectionDeltaOperationKind,
    CodeSectionDeltaSet,
    CodeSectionRef,
    CodeSegmentRef,
    CodeSegmentContentDomain,
    CodeSegmentRenderPolicy,
    CodeSegmentRenderPolicyDiagnostic,
    CodeSegmentRenderPolicyResolutionStatus,
    DescribeCodePackageLayoutRequest,
    DescribeCodePackageLayoutResponse,
    DescribeCodeSemanticContractRequest,
    DescribeCodeSemanticContractResponse,
    DiscoverCodePackageLayoutsRequest,
    DiscoverCodePackageLayoutsResponse,
    FingerprintCodeGeneratedMaterializationDeltaRequest,
    FingerprintCodeGeneratedMaterializationDeltaResponse,
    FingerprintCodePackageDeltaRequest,
    FingerprintCodePackageDeltaResponse,
    FingerprintCodeSectionDeltaRequest,
    FingerprintCodeSectionDeltaResponse,
    FingerprintCodeSourceProjectionRequest,
    FingerprintCodeSourceProjectionResponse,
    FindCodeSemanticManifestResolutionRequest,
    FindCodeSemanticManifestResolutionResponse,
    NormalizeCodeGeneratedMaterializationDeltaRequest,
    NormalizeCodeGeneratedMaterializationDeltaResponse,
    NormalizeCodePackageDeltaRequest,
    NormalizeCodePackageDeltaResponse,
    NormalizeCodeSectionDeltaRequest,
    NormalizeCodeSectionDeltaResponse,
    NormalizeCodeSemanticContractRequest,
    NormalizeCodeSemanticContractResponse,
    NormalizeCodeSourceProjectionRequest,
    NormalizeCodeSourceProjectionResponse,
    PreviewCodeSemanticAnalysisPackageDeltaRequest,
    PreviewCodeSemanticAnalysisPackageDeltaResponse,
    ResolveCodeGeneratedMaterializationPackageDeltaRequest,
    ResolveCodeGeneratedMaterializationPackageDeltaResponse,
    ResolveCodeSemanticSourceDeltaMeaningRequest,
    ResolveCodeSemanticSourceDeltaMeaningResponse,
    ResolveCodeSemanticSourceMeaningRequest,
    ResolveCodeSemanticSourceMeaningResponse,
    ResolveCodeSemanticWorkflowCoverageRequest,
    ResolveCodeSemanticWorkflowCoverageResponse,
    ResolveCodeSemanticScopeRequest,
    ResolveCodeSemanticScopeResponse,
    ResolveCodeGrammarProfileRequest,
    ResolveCodeGrammarProfileResponse,
    ResolveCodeSectionDeltaPackageDeltaRequest,
    ResolveCodeSectionDeltaPackageDeltaResponse,
    ResolveCodeSegmentRenderPolicyRequest,
    ResolveCodeSegmentRenderPolicyResponse,
    ResolveCodeSourceProjectionPackageDeltaRequest,
    ResolveCodeSourceProjectionPackageDeltaResponse,
    ValidateCodeGeneratedMaterializationDeltaRequest,
    ValidateCodeGeneratedMaterializationDeltaResponse,
    ValidateCodeGrammarAnchorBindingRequest,
    ValidateCodeGrammarAnchorBindingResponse,
    ValidateCodePackageLayoutRequest,
    ValidateCodePackageLayoutResponse,
    ValidateCodeSectionDeltaRequest,
    ValidateCodeSectionDeltaResponse,
    ValidateCodeSemanticContractRequest,
    ValidateCodeSemanticContractResponse,
    ValidateCodeSourceProjectionRequest,
    ValidateCodeSourceProjectionResponse,
)
from aware_code_sdk.semantic_contract_spec import (
    render_code_semantic_contract_spec_declaration,
)
from aware_code_service_dto.code.features.view_state import (
    ResolveCodeEditorViewRequest,
    ResolveCodeEditorViewResponse,
    ResolveCodePackageSelectorViewRequest,
    ResolveCodePackageSelectorViewResponse,
)
from aware_types import JsonObject, JsonValue

from .grammar_anchor_binding import (
    resolve_code_grammar_anchor_binding_evidence,
    validate_code_grammar_anchor_binding,
)
from .grammar_anchor_render_delta import resolve_code_grammar_anchor_render_delta
from .grammar_profile import resolve_code_grammar_profile
from .ontology_replica_snapshot import (
    CodeReplicaReadModels,
    resolve_code_editor_view_response_from_ontology_replica,
    resolve_code_package_selector_view_response_from_ontology_replica,
)
from .semantic_workflow_coverage import resolve_code_semantic_workflow_coverage
from .semantic_contract_adapter import (
    code_semantic_contract_from_module_contract,
    code_semantic_provider_binding_from_module_contract,
    normalize_code_semantic_contract,
    validate_code_semantic_contract,
)

_CODE_PACKAGE_SURFACE_VALUES = frozenset(
    {
        "api",
        "docs",
        "economy",
        "experience",
        "package_manager",
        "representation",
        "runtime",
        "sdk",
        "service",
        "structure",
    }
)
_SEMANTIC_CONTRACT_MODULE_BY_PROVIDER_KEY = {
    "aware_api": "aware_api_runtime.semantic_contract",
    "aware_code": "aware_code.semantic_contract",
    "aware_service": "aware_service_runtime.semantic_contract",
}


def build_aware_code_service_protocol_handler(
    *,
    semantic_contract: ModuleSemanticContract | None = None,
    semantic_contracts: tuple[ModuleSemanticContract, ...] | None = None,
    section_segment_capability_registry: (
        CodeSectionSegmentCapabilityRegistry | None
    ) = None,
    code_replica_read_models: CodeReplicaReadModels | None = None,
) -> object:
    if semantic_contract is None and semantic_contracts is None:
        setup_code_plugins()
    return _AwareCodeServiceProtocolHandler(
        semantic_contracts=_resolve_semantic_contracts(
            semantic_contract=semantic_contract,
            semantic_contracts=semantic_contracts,
        ),
        section_segment_capability_registry=(
            section_segment_capability_registry
            or DEFAULT_CODE_SECTION_SEGMENT_CAPABILITY_REGISTRY
        ),
        code_replica_read_models=code_replica_read_models,
    )


@dataclass(frozen=True, slots=True)
class _AwareCodeApiProtocolHandler:
    grammar_anchor_binding: "_CodeGrammarAnchorBindingCapabilityHandler"
    grammar_anchor_render_delta: "_CodeGrammarAnchorRenderDeltaCapabilityHandler"
    grammar_profile: "_CodeGrammarProfileCapabilityHandler"
    semantic_contract: "_CodeSemanticContractCapabilityHandler"
    semantic_analysis: "_CodeSemanticAnalysisCapabilityHandler"
    semantic_source_meaning: "_CodeSemanticSourceMeaningCapabilityHandler"
    view_state: "_CodeViewStateCapabilityHandler"
    semantic_workflow_coverage: "_CodeSemanticWorkflowCoverageCapabilityHandler"
    package_delta: "_CodePackageDeltaCapabilityHandler"
    package_layout: "_CodePackageLayoutCapabilityHandler"
    section_delta: "_CodeSectionDeltaCapabilityHandler"
    source_projection: "_CodeSourceProjectionCapabilityHandler"
    generated_materialization_delta: (
        "_CodeGeneratedMaterializationDeltaCapabilityHandler"
    )
    source_ownership: "_CodeSourceOwnershipCapabilityHandler"


class _AwareCodeServiceProtocolHandler:
    def __init__(
        self,
        *,
        semantic_contracts: tuple[ModuleSemanticContract, ...],
        section_segment_capability_registry: CodeSectionSegmentCapabilityRegistry,
        code_replica_read_models: CodeReplicaReadModels | None,
    ) -> None:
        support = _CodeProtocolSupport(
            semantic_contracts=semantic_contracts,
            section_segment_capability_registry=section_segment_capability_registry,
            code_replica_read_models=code_replica_read_models,
        )
        self.code = _AwareCodeApiProtocolHandler(
            grammar_anchor_binding=(
                _CodeGrammarAnchorBindingCapabilityHandler(support=support)
            ),
            grammar_anchor_render_delta=(
                _CodeGrammarAnchorRenderDeltaCapabilityHandler(support=support)
            ),
            grammar_profile=_CodeGrammarProfileCapabilityHandler(support=support),
            semantic_contract=_CodeSemanticContractCapabilityHandler(support=support),
            semantic_analysis=_CodeSemanticAnalysisCapabilityHandler(support=support),
            semantic_source_meaning=(
                _CodeSemanticSourceMeaningCapabilityHandler(support=support)
            ),
            view_state=_CodeViewStateCapabilityHandler(support=support),
            semantic_workflow_coverage=(
                _CodeSemanticWorkflowCoverageCapabilityHandler(support=support)
            ),
            package_delta=_CodePackageDeltaCapabilityHandler(support=support),
            package_layout=_CodePackageLayoutCapabilityHandler(support=support),
            section_delta=_CodeSectionDeltaCapabilityHandler(support=support),
            source_projection=_CodeSourceProjectionCapabilityHandler(support=support),
            generated_materialization_delta=(
                _CodeGeneratedMaterializationDeltaCapabilityHandler(support=support)
            ),
            source_ownership=_CodeSourceOwnershipCapabilityHandler(support=support),
        )


@dataclass(frozen=True, slots=True)
class _CodeProtocolSupport:
    semantic_contracts: tuple[ModuleSemanticContract, ...]
    section_segment_capability_registry: CodeSectionSegmentCapabilityRegistry
    code_replica_read_models: CodeReplicaReadModels | None = None

    @property
    def primary_contract(self) -> ModuleSemanticContract:
        return self.semantic_contracts[0]

    def contract_dto(
        self,
        *,
        provider_key: str | None = None,
    ) -> CodeSemanticContract | None:
        contract = self.contract(provider_key=provider_key)
        if contract is None:
            return None
        return code_semantic_contract_from_module_contract(contract)

    def contract_dtos(self) -> tuple[CodeSemanticContract, ...]:
        return tuple(
            code_semantic_contract_from_module_contract(contract)
            for contract in self.semantic_contracts
        )

    def contract(
        self,
        *,
        provider_key: str | None = None,
    ) -> ModuleSemanticContract | None:
        if provider_key is None:
            return self.primary_contract
        for contract in self.semantic_contracts:
            if contract.provider_key == provider_key:
                return contract
        return None

    def provider_binding(
        self,
        *,
        provider_key: str | None = None,
        package_name: str | None = None,
        package_fqn: str | None = None,
    ) -> CodeSemanticProviderBinding:
        contract = self.contract(provider_key=provider_key) or self.primary_contract
        return code_semantic_provider_binding_from_module_contract(
            contract,
            package_name=package_name,
            package_fqn=package_fqn,
            provider_module=_semantic_contract_module_for_provider_key(
                contract.provider_key
            ),
        )

    def layout_contract(
        self,
        *,
        package_name: str | None = None,
        package_root: str | None = None,
        package_fqn: str | None = None,
    ) -> CodePackageLayoutContract:
        return CodePackageLayoutContract(
            package_name=package_name or package_fqn,
            package_root=(package_root or "."),
            sources_root=None,
            generated_roots=[".aware", "__pycache__"],
            manifest_relative_path=None,
            path_roles=[
                CodePackageLayoutPathRole(
                    role=CodePackagePathRole.authored_source,
                    include_patterns=["**/*.aware", "**/*.py", "**/*.toml"],
                    exclude_patterns=["**/.aware/**", "**/__pycache__/**"],
                    semantic_owner_hints=[self.primary_contract.provider_key],
                    metadata=JsonObject(
                        {"source": "aware_code_service.default_layout"}
                    ),
                ),
                CodePackageLayoutPathRole(
                    role=CodePackagePathRole.generated_metadata,
                    include_patterns=["**/.aware/**"],
                    exclude_patterns=[],
                    semantic_owner_hints=[self.primary_contract.provider_key],
                    metadata=JsonObject(
                        {"source": "aware_code_service.default_layout"}
                    ),
                ),
                CodePackageLayoutPathRole(
                    role=CodePackagePathRole.generated_code,
                    include_patterns=["**/__pycache__/**"],
                    exclude_patterns=[],
                    semantic_owner_hints=[self.primary_contract.provider_key],
                    metadata=JsonObject(
                        {"source": "aware_code_service.default_layout"}
                    ),
                ),
            ],
            metadata=JsonObject({"provider_key": self.primary_contract.provider_key}),
        )

    def manifest_resolution_matches(
        self,
        *,
        provider_key: str | None = None,
        manifest_kind: str | None = None,
        filename: str | None = None,
        workspace_manifest_kind: str | None = None,
    ) -> list[CodeSemanticManifestResolutionMatch]:
        matches: list[CodeSemanticManifestResolutionMatch] = []
        provider_filter = _optional_text(provider_key)
        manifest_filter = _optional_text(manifest_kind)
        filename_filter = _optional_text(filename)
        workspace_filter = _optional_text(workspace_manifest_kind)
        for contract in self.semantic_contracts:
            if provider_filter is not None and contract.provider_key != provider_filter:
                continue
            contract_dto = code_semantic_contract_from_module_contract(contract)
            for descriptor in contract_dto.manifest_resolution:
                if (
                    manifest_filter is not None
                    and descriptor.manifest_kind != manifest_filter
                ):
                    continue
                if (
                    filename_filter is not None
                    and descriptor.filename != filename_filter
                ):
                    continue
                if (
                    workspace_filter is not None
                    and descriptor.workspace_manifest_kind != workspace_filter
                ):
                    continue
                matches.append(
                    CodeSemanticManifestResolutionMatch(
                        provider_key=contract.provider_key,
                        semantic_contract=contract_dto,
                        manifest_resolution=descriptor,
                        semantic_contract_module=(
                            _semantic_contract_module_for_provider_key(
                                contract.provider_key
                            )
                        ),
                    )
                )
        return sorted(
            matches,
            key=lambda item: (
                item.manifest_resolution.priority,
                item.provider_key,
                item.manifest_resolution.semantic_owner,
                item.manifest_resolution.manifest_kind,
                item.manifest_resolution.filename,
            ),
        )


def _support_with_workspace_module_plugins(
    *,
    support: _CodeProtocolSupport,
    workspace_root: Path | None = None,
    module_roots: Sequence[Path] = (),
) -> _CodeProtocolSupport:
    _register_support_semantic_contract_plugins(support=support)
    if module_roots:
        AwareModulePluginRegistry.ensure_module_plugins_registered_from_module_roots(
            module_roots=tuple(module_roots),
            replace_existing=True,
        )
    elif workspace_root is not None:
        AwareModulePluginRegistry.ensure_module_plugins_registered_from_repo_root(
            repo_root=workspace_root,
            replace_existing=True,
        )
    registered_contracts = AwareModulePluginRegistry.get_module_semantic_contracts()
    if not registered_contracts:
        return support

    merged_by_provider = {
        contract.provider_key: contract for contract in registered_contracts
    }
    ordered: list[ModuleSemanticContract] = []
    for contract in support.semantic_contracts:
        ordered.append(merged_by_provider.pop(contract.provider_key, contract))
    ordered.extend(
        sorted(merged_by_provider.values(), key=lambda item: item.provider_key)
    )
    merged = tuple(ordered)
    if merged == support.semantic_contracts:
        return support
    return replace(support, semantic_contracts=merged)


def _register_support_semantic_contract_plugins(
    *,
    support: _CodeProtocolSupport,
) -> None:
    existing_provider_keys = set(AwareModulePluginRegistry.get_provider_keys())
    for contract in support.semantic_contracts:
        if contract.provider_key in existing_provider_keys:
            continue
        AwareModulePluginRegistry.register(
            AwareModulePlugin(
                provider_key=contract.provider_key,
                semantic_contract_module=_semantic_contract_module_for_provider_key(
                    contract.provider_key,
                ),
            )
        )
        existing_provider_keys.add(contract.provider_key)


@dataclass(frozen=True, slots=True)
class _SectionDeltaApplyOutcome:
    updated_text: str | None
    diagnostics: list[str]
    already_applied: bool = False


@dataclass(frozen=True, slots=True)
class _NestedMemberInsertTarget:
    insert_at: int | None
    diagnostics: list[str]
    already_applied: bool = False


_SEMANTIC_SOURCE_MEANING_SOURCE_INDEX_CACHE = CodeGrammarSourceIndexCache()


class _CodeGrammarProfileCapabilityHandler:
    def __init__(self, *, support: _CodeProtocolSupport) -> None:
        self._support = support

    async def resolve(
        self,
        request: ResolveCodeGrammarProfileRequest,
    ) -> ResolveCodeGrammarProfileResponse:
        return resolve_code_grammar_profile(
            request=request,
            available_semantic_contracts=self._support.contract_dtos(),
        )


class _CodeSemanticWorkflowCoverageCapabilityHandler:
    def __init__(self, *, support: _CodeProtocolSupport) -> None:
        self._support = support

    async def resolve(
        self,
        request: ResolveCodeSemanticWorkflowCoverageRequest,
    ) -> ResolveCodeSemanticWorkflowCoverageResponse:
        return resolve_code_semantic_workflow_coverage(
            request=request,
            available_semantic_contracts=self._support.contract_dtos(),
        )


class _CodeGrammarAnchorBindingCapabilityHandler:
    def __init__(self, *, support: _CodeProtocolSupport) -> None:
        self._support = support

    async def validate(
        self,
        request: ValidateCodeGrammarAnchorBindingRequest,
    ) -> ValidateCodeGrammarAnchorBindingResponse:
        _ = self._support
        return validate_code_grammar_anchor_binding(request=request)

    async def resolve_evidence(
        self,
        request: ResolveCodeGrammarAnchorBindingEvidenceRequest,
    ) -> ResolveCodeGrammarAnchorBindingEvidenceResponse:
        _ = self._support
        return resolve_code_grammar_anchor_binding_evidence(request=request)


class _CodeGrammarAnchorRenderDeltaCapabilityHandler:
    def __init__(self, *, support: _CodeProtocolSupport) -> None:
        self._support = support

    async def resolve_delta(
        self,
        request: ResolveCodeGrammarAnchorRenderDeltaRequest,
    ) -> ResolveCodeGrammarAnchorRenderDeltaResponse:
        _ = self._support
        return resolve_code_grammar_anchor_render_delta(request=request)


class _CodeSemanticContractCapabilityHandler:
    def __init__(self, *, support: _CodeProtocolSupport) -> None:
        self._support = support

    async def describe(
        self,
        request: DescribeCodeSemanticContractRequest,
    ) -> DescribeCodeSemanticContractResponse:
        contract = self._support.contract_dto(provider_key=request.provider_key)
        if contract is None:
            return DescribeCodeSemanticContractResponse(
                request_id=request.request_id,
                success=False,
                error=(
                    "Unknown Code semantic contract provider: "
                    f"{request.provider_key}"
                ),
            )
        provider_binding = self._support.provider_binding(
            provider_key=request.provider_key,
            package_name=request.package_name,
            package_fqn=request.package_fqn,
        )
        return DescribeCodeSemanticContractResponse(
            request_id=request.request_id,
            success=True,
            semantic_contract=contract,
            layout_contract=(
                self._support.layout_contract(
                    package_name=request.package_name,
                    package_fqn=request.package_fqn,
                )
                if request.include_layout
                else None
            ),
            provider_binding=provider_binding,
            spec_declaration=(
                render_code_semantic_contract_spec_declaration(
                    semantic_contract=contract,
                    provider_binding=provider_binding,
                )
                if request.include_spec_declaration
                else None
            ),
        )

    async def find_manifest_resolution(
        self,
        request: FindCodeSemanticManifestResolutionRequest,
    ) -> FindCodeSemanticManifestResolutionResponse:
        matches = self._support.manifest_resolution_matches(
            provider_key=request.provider_key,
            manifest_kind=request.manifest_kind,
            filename=request.filename,
            workspace_manifest_kind=request.workspace_manifest_kind,
        )
        return FindCodeSemanticManifestResolutionResponse(
            request_id=request.request_id,
            success=True,
            matches=matches,
        )

    async def resolve_semantic_scope(
        self,
        request: ResolveCodeSemanticScopeRequest,
    ) -> ResolveCodeSemanticScopeResponse:
        diagnostics = _semantic_scope_request_diagnostics(request)
        if diagnostics:
            return _semantic_scope_blocked_response(
                request=request,
                diagnostics=diagnostics,
            )

        try:
            workspace_root = Path(request.workspace_root or ".").expanduser().resolve()
            code_package = _code_package_info_from_semantic_scope_ref(
                request.package_ref,
            )
        except (TypeError, ValueError) as exc:
            return _semantic_scope_blocked_response(
                request=request,
                diagnostics=(f"{type(exc).__name__}: {exc}",),
            )

        resolutions = SemanticScopeRegistry.resolve(
            code_package,
            workspace_root=workspace_root,
            provider_keys=request.provider_keys or None,
            scope_keys=request.scope_keys or None,
        )
        result = [
            _code_semantic_scope_resolution(resolution) for resolution in resolutions
        ]
        return ResolveCodeSemanticScopeResponse(
            request_id=request.request_id,
            success=True,
            resolved=bool(result),
            resolutions=result,
            diagnostics=[],
            resolution_count=len(result),
        )

    async def validate(
        self,
        request: ValidateCodeSemanticContractRequest,
    ) -> ValidateCodeSemanticContractResponse:
        diagnostics = validate_code_semantic_contract(
            request.semantic_contract,
            require_runtime_compatible=request.strict,
        )
        valid = not diagnostics
        return ValidateCodeSemanticContractResponse(
            request_id=request.request_id,
            success=valid,
            valid=valid,
            diagnostics=diagnostics,
        )

    async def normalize(
        self,
        request: NormalizeCodeSemanticContractRequest,
    ) -> NormalizeCodeSemanticContractResponse:
        normalized = normalize_code_semantic_contract(request.semantic_contract)
        return NormalizeCodeSemanticContractResponse(
            request_id=request.request_id,
            success=True,
            semantic_contract=normalized,
        )


def _semantic_scope_request_diagnostics(
    request: ResolveCodeSemanticScopeRequest,
) -> tuple[str, ...]:
    diagnostics: list[str] = []
    if not request.package_ref.package_name.strip():
        diagnostics.append("package_ref.package_name is required.")
    if not request.package_ref.package_root.strip():
        diagnostics.append("package_ref.package_root is required.")
    if not request.package_ref.manifest_path.strip():
        diagnostics.append("package_ref.manifest_path is required.")
    if not (request.workspace_root or ".").strip():
        diagnostics.append("workspace_root is required.")
    return tuple(diagnostics)


def _semantic_scope_blocked_response(
    *,
    request: ResolveCodeSemanticScopeRequest,
    diagnostics: Sequence[str],
) -> ResolveCodeSemanticScopeResponse:
    message = "; ".join(diagnostics)
    return ResolveCodeSemanticScopeResponse(
        request_id=request.request_id,
        success=False,
        error=message,
        resolved=False,
        resolutions=[],
        diagnostics=list(diagnostics),
        resolution_count=0,
    )


def _code_package_info_from_semantic_scope_ref(
    package_ref: CodeSemanticScopePackageRef,
) -> CodePackageInfo:
    return CodePackageInfo(
        name=package_ref.package_name.strip(),
        root_path=Path(package_ref.package_root.strip()),
        manifest_path=Path(package_ref.manifest_path.strip()),
        language=CodeLanguage(_enum_text(package_ref.language)),
        metadata=dict(package_ref.metadata or {}),
        semantic_packages=_semantic_package_descriptors_from_payloads(
            package_ref.semantic_packages,
        ),
    )


def _semantic_package_descriptors_from_payloads(
    payloads: Sequence[Mapping[str, object]],
) -> tuple[SemanticPackageDescriptor, ...]:
    descriptors: list[SemanticPackageDescriptor] = []
    for index, payload in enumerate(payloads):
        try:
            descriptors.append(
                SemanticPackageDescriptor.model_validate(dict(payload)),
            )
        except Exception as exc:
            raise ValueError(
                f"package_ref.semantic_packages[{index}] is invalid: {exc}"
            ) from exc
    return tuple(descriptors)


def _code_semantic_scope_resolution(
    resolution: RuntimeSemanticScopeResolution,
) -> CodeSemanticScopeResolution:
    return CodeSemanticScopeResolution(
        scope_key=resolution.scope_key,
        provider_key=resolution.provider_key,
        payload=_json_object_from_mapping(resolution.payload) or JsonObject({}),
        materialization_dependencies=[
            _code_semantic_materialization_scope_dependency(dependency)
            for dependency in resolution.materialization_dependencies
        ],
        metadata=JsonObject(
            {
                "source": "aware_code.semantic_scope.registry",
                "runtime_payload_available": resolution.runtime_value is not None,
            }
        ),
    )


def _code_semantic_materialization_scope_dependency(
    dependency: RuntimeSemanticScopeMaterializationDependency,
) -> CodeSemanticMaterializationScopeDependency:
    return CodeSemanticMaterializationScopeDependency(
        package_name=dependency.package_name,
        provider_key=dependency.provider_key,
        semantic_owner=dependency.semantic_owner,
        manifest_kind=dependency.manifest_kind,
        dependency_kind=dependency.dependency_kind,
        required_state=dependency.required_state,
        semantic_package_family=dependency.semantic_package_family,
        semantic_package_kind=dependency.semantic_package_kind,
        semantic_package_name=dependency.semantic_package_name,
        source_refs=list(dependency.source_refs),
        reason=dependency.reason,
        metadata=_json_object_from_mapping(dependency.metadata),
    )


class _CodeSemanticAnalysisCapabilityHandler:
    def __init__(self, *, support: _CodeProtocolSupport) -> None:
        self._support = support

    async def preview_package_delta(
        self,
        request: PreviewCodeSemanticAnalysisPackageDeltaRequest,
    ) -> PreviewCodeSemanticAnalysisPackageDeltaResponse:
        normalized_delta = _normalize_package_delta(request.delta)
        delta_fingerprint = _fingerprint_package_delta(normalized_delta)
        provider_key = _optional_text(request.provider_key) or (
            _optional_text(request.semantic_contract.provider_key)
            if request.semantic_contract is not None
            else None
        )
        if provider_key is None:
            return _semantic_analysis_preview_blocked_response(
                request=request,
                delta_fingerprint=delta_fingerprint,
                blockers=("provider_key_or_semantic_contract_provider_key_required",),
                error=(
                    "semantic_analysis.preview_package_delta requires "
                    "provider_key or semantic_contract.provider_key."
                ),
            )

        resolved_provider = _resolve_semantic_analysis_provider(
            provider_key=provider_key,
            semantic_owner=_optional_text(request.semantic_owner),
        )
        if resolved_provider is None:
            return _semantic_analysis_preview_blocked_response(
                request=request,
                delta_fingerprint=delta_fingerprint,
                provider_key=provider_key,
                semantic_owner=_optional_text(request.semantic_owner),
                blockers=("semantic_analysis_provider_unavailable",),
                error=(
                    "No semantic_analysis provider is registered for "
                    f"{provider_key!r}."
                ),
            )

        analysis_request = SemanticAnalysisCapabilityRequest(
            package_root=_semantic_analysis_package_root(
                request=request,
                delta=normalized_delta,
            ),
            source_files=_semantic_analysis_source_files(
                request=request,
                delta=normalized_delta,
            ),
            manifest_path=_semantic_analysis_manifest_path(
                request=request,
                delta=normalized_delta,
            ),
            workspace_root=_semantic_analysis_workspace_root(request),
            code_package_delta=_runtime_code_package_delta(normalized_delta),
            dependency_graphs=tuple(
                SemanticCapabilityDependencyGraph(
                    package_name=dependency.package_name,
                    graph_kind=dependency.graph_kind,
                    graph=dict(dependency.graph),
                    provider_key=_optional_text(dependency.provider_key),
                    semantic_owner=_optional_text(dependency.semantic_owner),
                    semantic_branch_id=_optional_text(dependency.semantic_branch_id),
                    semantic_projection_name=_optional_text(
                        dependency.semantic_projection_name
                    ),
                    semantic_projection_hash=_optional_text(
                        dependency.semantic_projection_hash
                    ),
                    semantic_object_instance_graph_commit_id=_optional_text(
                        dependency.semantic_object_instance_graph_commit_id
                    ),
                    semantic_root_object_instance_graph_commit_id=_optional_text(
                        dependency.semantic_root_object_instance_graph_commit_id
                    ),
                    metadata=dict(dependency.metadata or {}),
                )
                for dependency in request.dependency_graphs
            ),
            metadata={
                "source": "aware_code_service.semantic_analysis.preview_package_delta",
                "delta_fingerprint": delta_fingerprint,
                "provider_key": provider_key,
                **dict(request.metadata or {}),
            },
        )
        provider = _semantic_analysis_provider_callable(resolved_provider)
        semantic_owner = _semantic_analysis_provider_owner(resolved_provider)
        if provider is None:
            return _semantic_analysis_preview_blocked_response(
                request=request,
                delta_fingerprint=delta_fingerprint,
                provider_key=provider_key,
                semantic_owner=semantic_owner,
                blockers=("semantic_analysis_provider_invalid",),
                error="Resolved semantic_analysis provider is not callable.",
            )

        try:
            raw_result = provider(analysis_request)
        except Exception as exc:
            return _semantic_analysis_preview_blocked_response(
                request=request,
                delta_fingerprint=delta_fingerprint,
                provider_key=provider_key,
                semantic_owner=semantic_owner,
                blockers=("semantic_analysis_provider_execution_failed",),
                error=f"{type(exc).__name__}: {exc}",
            )
        if not isinstance(raw_result, SemanticAnalysisCapabilityResult):
            return _semantic_analysis_preview_blocked_response(
                request=request,
                delta_fingerprint=delta_fingerprint,
                provider_key=provider_key,
                semantic_owner=semantic_owner,
                blockers=("semantic_analysis_provider_result_invalid",),
                error=(
                    "semantic_analysis provider returned "
                    f"{type(raw_result).__name__}, expected "
                    "SemanticAnalysisCapabilityResult."
                ),
            )

        diagnostics = tuple(
            _code_semantic_analysis_diagnostic(diagnostic)
            for diagnostic in raw_result.diagnostics
        )
        blockers = tuple(
            f"diagnostic:{diagnostic.code}"
            for diagnostic in raw_result.diagnostics
            if diagnostic.severity.casefold() in {"error", "fatal"}
        )
        return PreviewCodeSemanticAnalysisPackageDeltaResponse(
            request_id=request.request_id,
            success=not blockers,
            previewed=True,
            provider_key=raw_result.provider_key,
            semantic_owner=raw_result.semantic_owner,
            delta_fingerprint=delta_fingerprint,
            diagnostics=list(diagnostics),
            change_preview=_code_semantic_analysis_change_preview(
                raw_result.change_preview,
            ),
            blockers=list(blockers),
            available=not blockers,
            provider_payload=(
                _json_object_from_value(raw_result.payload)
                if request.include_provider_payload
                else None
            ),
        )


class _CodeSemanticSourceMeaningCapabilityHandler:
    def __init__(self, *, support: _CodeProtocolSupport) -> None:
        self._support = support

    async def resolve(
        self,
        request: ResolveCodeSemanticSourceMeaningRequest,
    ) -> ResolveCodeSemanticSourceMeaningResponse:
        _ = self._support
        handler_started_at = perf_counter()
        phase_timings_s: dict[str, float] = {}
        phase_started_at = perf_counter()
        diagnostics = [
            *_semantic_source_meaning_source_hash_diagnostics(
                label="current_sources",
                sources=request.current_sources,
            ),
            *_semantic_source_meaning_source_hash_diagnostics(
                label="baseline_sources",
                sources=request.baseline_sources,
            ),
        ]
        _record_code_service_phase_timing(
            phase_timings_s=phase_timings_s,
            key="source_hash_diagnostics_s",
            started_at=phase_started_at,
        )
        if diagnostics:
            return _semantic_source_meaning_blocked_response(
                request=request,
                diagnostics=tuple(diagnostics),
            )
        try:
            phase_started_at = perf_counter()
            contract = _runtime_semantic_source_meaning_contract(request.contract)
            _record_code_service_phase_timing(
                phase_timings_s=phase_timings_s,
                key="runtime_contract_s",
                started_at=phase_started_at,
            )
            phase_started_at = perf_counter()
            session_context = _semantic_source_meaning_session_context(
                metadata=request.metadata,
            )
            _record_code_service_phase_timing(
                phase_timings_s=phase_timings_s,
                key="session_context_s",
                started_at=phase_started_at,
            )
            phase_started_at = perf_counter()
            current_source_index = _semantic_source_meaning_source_index(
                request.current_sources,
                session_context=session_context,
            )
            _record_code_service_phase_timing(
                phase_timings_s=phase_timings_s,
                key="current_source_index_s",
                started_at=phase_started_at,
            )
            phase_started_at = perf_counter()
            baseline_source_index = (
                _semantic_source_meaning_source_index(
                    request.baseline_sources,
                    session_context=session_context,
                )
                if request.baseline_sources
                else None
            )
            _record_code_service_phase_timing(
                phase_timings_s=phase_timings_s,
                key="baseline_source_index_s",
                started_at=phase_started_at,
            )
            phase_started_at = perf_counter()
            resolution = resolve_code_semantic_source_meaning(
                contract=contract,
                current_source_index=current_source_index,
                baseline_source_index=baseline_source_index,
                include_noop=request.include_noop,
            )
            _record_code_service_phase_timing(
                phase_timings_s=phase_timings_s,
                key="runtime_resolve_s",
                started_at=phase_started_at,
            )
        except (TypeError, ValueError) as exc:
            return _semantic_source_meaning_blocked_response(
                request=request,
                diagnostics=(f"{type(exc).__name__}: {exc}",),
            )

        phase_started_at = perf_counter()
        semantic_deltas = [
            _code_semantic_delta(delta) for delta in resolution.semantic_deltas
        ]
        _record_code_service_phase_timing(
            phase_timings_s=phase_timings_s,
            key="semantic_delta_dto_s",
            started_at=phase_started_at,
        )
        phase_started_at = perf_counter()
        semantic_events = [
            _code_semantic_event(event) for event in resolution.semantic_events
        ]
        _record_code_service_phase_timing(
            phase_timings_s=phase_timings_s,
            key="semantic_event_dto_s",
            started_at=phase_started_at,
        )
        phase_started_at = perf_counter()
        typed_operations = [
            _code_semantic_typed_operation(operation)
            for operation in resolution.typed_operations
        ]
        _record_code_service_phase_timing(
            phase_timings_s=phase_timings_s,
            key="typed_operation_dto_s",
            started_at=phase_started_at,
        )
        phase_started_at = perf_counter()
        change_preview = _code_semantic_analysis_change_preview(
            resolution.change_preview(),
        )
        _record_code_service_phase_timing(
            phase_timings_s=phase_timings_s,
            key="change_preview_dto_s",
            started_at=phase_started_at,
        )
        _record_code_service_phase_timing(
            phase_timings_s=phase_timings_s,
            key="total_s",
            started_at=handler_started_at,
        )
        phase_started_at = perf_counter()
        source_index_evidence = _semantic_source_index_evidence_json_object(
            resolution.source_index_evidence,
            service_phase_timings_s=phase_timings_s,
        )
        _record_code_service_phase_timing(
            phase_timings_s=phase_timings_s,
            key="source_index_evidence_dto_s",
            started_at=phase_started_at,
        )
        source_index_evidence["service_phase_timings_s"] = cast(
            JsonValue,
            dict(phase_timings_s),
        )
        return ResolveCodeSemanticSourceMeaningResponse(
            request_id=request.request_id,
            success=resolution.resolved,
            error=None if resolution.resolved else "; ".join(resolution.diagnostics),
            resolved=resolution.resolved,
            status=resolution.status,
            diagnostics=list(resolution.diagnostics),
            contract_version=CODE_SEMANTIC_SOURCE_MEANING_BINDING_CONTRACT_VERSION,
            provider_key=resolution.contract.provider_key,
            semantic_owner=resolution.contract.semantic_owner,
            binding_count=resolution.binding_count,
            resolved_binding_count=resolution.resolved_binding_count,
            changed_binding_count=resolution.changed_binding_count,
            semantic_deltas=semantic_deltas,
            semantic_events=semantic_events,
            typed_operations=typed_operations,
            change_preview=change_preview,
            source_index_evidence=source_index_evidence,
            metadata=JsonObject(
                {
                    "source": ("aware_code_service.semantic_source_meaning.resolve"),
                    "runtime_contract": ("aware_code.semantic_source_meaning"),
                }
            ),
        )

    async def resolve_delta(
        self,
        request: ResolveCodeSemanticSourceDeltaMeaningRequest,
    ) -> ResolveCodeSemanticSourceDeltaMeaningResponse:
        _ = self._support
        handler_started_at = perf_counter()
        phase_timings_s: dict[str, float] = {}
        phase_started_at = perf_counter()
        normalized_delta = _normalize_package_delta(request.input.delta)
        _record_code_service_phase_timing(
            phase_timings_s=phase_timings_s,
            key="normalize_package_delta_s",
            started_at=phase_started_at,
        )
        phase_started_at = perf_counter()
        diagnostics = [
            *_semantic_source_meaning_source_hash_diagnostics(
                label="input.current_sources",
                sources=request.input.current_sources,
            ),
            *_semantic_source_meaning_source_hash_diagnostics(
                label="input.baseline_sources",
                sources=request.input.baseline_sources,
            ),
        ]
        _record_code_service_phase_timing(
            phase_timings_s=phase_timings_s,
            key="source_hash_diagnostics_s",
            started_at=phase_started_at,
        )
        if diagnostics:
            return _semantic_source_delta_meaning_blocked_response(
                request=request,
                diagnostics=tuple(diagnostics),
                required_context=(),
            )
        try:
            phase_started_at = perf_counter()
            contract = _runtime_semantic_source_meaning_contract(request.contract)
            _record_code_service_phase_timing(
                phase_timings_s=phase_timings_s,
                key="runtime_contract_s",
                started_at=phase_started_at,
            )
            phase_started_at = perf_counter()
            session_context = _semantic_source_meaning_session_context(
                metadata=request.metadata,
            )
            _record_code_service_phase_timing(
                phase_timings_s=phase_timings_s,
                key="session_context_s",
                started_at=phase_started_at,
            )
            phase_started_at = perf_counter()
            runtime_delta = _runtime_code_package_delta(normalized_delta)
            _record_code_service_phase_timing(
                phase_timings_s=phase_timings_s,
                key="runtime_delta_s",
                started_at=phase_started_at,
            )
            phase_started_at = perf_counter()
            baseline_sources = tuple(
                _runtime_semantic_source_meaning_source(source)
                for source in request.input.baseline_sources
            )
            _record_code_service_phase_timing(
                phase_timings_s=phase_timings_s,
                key="baseline_sources_s",
                started_at=phase_started_at,
            )
            phase_started_at = perf_counter()
            current_sources = tuple(
                _runtime_semantic_source_meaning_source(source)
                for source in request.input.current_sources
            )
            _record_code_service_phase_timing(
                phase_timings_s=phase_timings_s,
                key="current_sources_s",
                started_at=phase_started_at,
            )
            phase_started_at = perf_counter()
            baseline_source_index_ref = _runtime_semantic_source_index_ref(
                request.input.baseline_source_index_ref
            )
            current_source_index_ref = _runtime_semantic_source_index_ref(
                request.input.current_source_index_ref
            )
            _record_code_service_phase_timing(
                phase_timings_s=phase_timings_s,
                key="source_index_refs_s",
                started_at=phase_started_at,
            )
            phase_started_at = perf_counter()
            resolution = resolve_code_semantic_source_delta_meaning(
                contract=contract,
                code_package_delta=runtime_delta,
                baseline_sources=baseline_sources,
                current_sources=current_sources,
                baseline_source_index_ref=baseline_source_index_ref,
                current_source_index_ref=current_source_index_ref,
                session_context=session_context,
                include_noop=request.include_noop,
            )
            _record_code_service_phase_timing(
                phase_timings_s=phase_timings_s,
                key="runtime_resolve_s",
                started_at=phase_started_at,
            )
        except (TypeError, ValueError) as exc:
            return _semantic_source_delta_meaning_blocked_response(
                request=request,
                diagnostics=(f"{type(exc).__name__}: {exc}",),
                required_context=(),
            )

        phase_started_at = perf_counter()
        semantic_deltas = [
            _code_semantic_delta(delta) for delta in resolution.semantic_deltas
        ]
        _record_code_service_phase_timing(
            phase_timings_s=phase_timings_s,
            key="semantic_delta_dto_s",
            started_at=phase_started_at,
        )
        phase_started_at = perf_counter()
        semantic_events = [
            _code_semantic_event(event) for event in resolution.semantic_events
        ]
        _record_code_service_phase_timing(
            phase_timings_s=phase_timings_s,
            key="semantic_event_dto_s",
            started_at=phase_started_at,
        )
        phase_started_at = perf_counter()
        typed_operations = [
            _code_semantic_typed_operation(operation)
            for operation in resolution.typed_operations
        ]
        _record_code_service_phase_timing(
            phase_timings_s=phase_timings_s,
            key="typed_operation_dto_s",
            started_at=phase_started_at,
        )
        phase_started_at = perf_counter()
        change_preview = _code_semantic_analysis_change_preview(
            resolution.change_preview(),
        )
        _record_code_service_phase_timing(
            phase_timings_s=phase_timings_s,
            key="change_preview_dto_s",
            started_at=phase_started_at,
        )
        _record_code_service_phase_timing(
            phase_timings_s=phase_timings_s,
            key="total_s",
            started_at=handler_started_at,
        )
        phase_started_at = perf_counter()
        source_index_evidence = _semantic_source_index_evidence_json_object(
            resolution.source_index_evidence,
            service_phase_timings_s=phase_timings_s,
        )
        _record_code_service_phase_timing(
            phase_timings_s=phase_timings_s,
            key="source_index_evidence_dto_s",
            started_at=phase_started_at,
        )
        source_index_evidence["service_phase_timings_s"] = cast(
            JsonValue,
            dict(phase_timings_s),
        )
        return ResolveCodeSemanticSourceDeltaMeaningResponse(
            request_id=request.request_id,
            success=resolution.resolved,
            error=None if resolution.resolved else "; ".join(resolution.diagnostics),
            resolved=resolution.resolved,
            status=resolution.status,
            meaning_resolution_mode=CodeSemanticSourceDeltaMeaningResolutionMode(
                resolution.meaning_resolution_mode
            ),
            diagnostics=list(resolution.diagnostics),
            required_context=list(resolution.required_context),
            contract_version=CODE_SEMANTIC_SOURCE_DELTA_MEANING_CONTRACT_VERSION,
            provider_key=resolution.contract.provider_key,
            semantic_owner=resolution.contract.semantic_owner,
            binding_count=resolution.binding_count,
            resolved_binding_count=resolution.resolved_binding_count,
            changed_binding_count=resolution.changed_binding_count,
            semantic_deltas=semantic_deltas,
            semantic_events=semantic_events,
            typed_operations=typed_operations,
            change_preview=change_preview,
            source_index_evidence=source_index_evidence,
            metadata=JsonObject(
                {
                    "source": (
                        "aware_code_service.semantic_source_meaning.resolve_delta"
                    ),
                    "runtime_contract": ("aware_code.semantic_source_delta_meaning"),
                }
            ),
        )


class _CodeViewStateCapabilityHandler:
    def __init__(self, *, support: _CodeProtocolSupport) -> None:
        self._support = support

    async def resolve_package_selector(
        self,
        request: ResolveCodePackageSelectorViewRequest,
    ) -> ResolveCodePackageSelectorViewResponse:
        return await resolve_code_package_selector_view_response_from_ontology_replica(
            request,
            models=self._support.code_replica_read_models,
        )

    async def resolve_editor(
        self,
        request: ResolveCodeEditorViewRequest,
    ) -> ResolveCodeEditorViewResponse:
        return await resolve_code_editor_view_response_from_ontology_replica(
            request,
            models=self._support.code_replica_read_models,
        )


class _CodePackageDeltaCapabilityHandler:
    def __init__(self, *, support: _CodeProtocolSupport) -> None:
        self._support = support

    async def normalize(
        self,
        request: NormalizeCodePackageDeltaRequest,
    ) -> NormalizeCodePackageDeltaResponse:
        _ = self._support
        normalized = _normalize_package_delta(request.delta)
        return NormalizeCodePackageDeltaResponse(
            request_id=request.request_id,
            success=True,
            delta=normalized,
        )

    async def fingerprint(
        self,
        request: FingerprintCodePackageDeltaRequest,
    ) -> FingerprintCodePackageDeltaResponse:
        if request.algorithm != "sha256":
            return FingerprintCodePackageDeltaResponse(
                request_id=request.request_id,
                success=False,
                error=f"Unsupported CodePackageDelta fingerprint algorithm: {request.algorithm}",
                fingerprint=None,
                path_count=len(request.delta.paths),
            )
        normalized = _normalize_package_delta(request.delta)
        payload = normalized.model_dump(mode="json", exclude_none=True)
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return FingerprintCodePackageDeltaResponse(
            request_id=request.request_id,
            success=True,
            fingerprint=sha256(canonical).hexdigest(),
            path_count=len(normalized.paths),
        )


class _CodePackageLayoutCapabilityHandler:
    def __init__(self, *, support: _CodeProtocolSupport) -> None:
        self._support = support

    async def describe(
        self,
        request: DescribeCodePackageLayoutRequest,
    ) -> DescribeCodePackageLayoutResponse:
        return DescribeCodePackageLayoutResponse(
            request_id=request.request_id,
            success=True,
            layout_contract=self._support.layout_contract(
                package_name=request.package_name,
                package_root=request.package_root,
                package_fqn=request.package_fqn,
            ),
        )

    async def discover(
        self,
        request: DiscoverCodePackageLayoutsRequest,
    ) -> DiscoverCodePackageLayoutsResponse:
        workspace_root = Path(request.workspace_root or ".").expanduser().resolve()
        support = _support_with_workspace_module_plugins(
            support=self._support,
            workspace_root=workspace_root,
        )
        setup_code_plugins()
        discovered_packages = await _discover_code_packages_from_manifest_paths(
            workspace_root=workspace_root,
            manifest_paths=tuple(request.manifest_paths),
            support=support,
        )
        layouts_by_manifest_path = {
            package.manifest_path.as_posix(): _layout_contract_from_code_package(
                package=package,
                provider_key=support.primary_contract.provider_key,
            )
            for package in discovered_packages
        }
        layout_contracts: list[CodePackageLayoutContract] = []
        diagnostics: list[str] = []
        for manifest_path in request.manifest_paths:
            normalized_manifest_path = _normalize_relative_path_text(manifest_path)
            layout_contract = layouts_by_manifest_path.get(normalized_manifest_path)
            if layout_contract is None:
                diagnostics.append(
                    "Code package manifest was not resolved by language discovery: "
                    f"{normalized_manifest_path}"
                )
                continue
            layout_contracts.append(layout_contract)
        return DiscoverCodePackageLayoutsResponse(
            request_id=request.request_id,
            success=not diagnostics,
            layout_contracts=layout_contracts,
            diagnostics=diagnostics,
        )

    async def validate(
        self,
        request: ValidateCodePackageLayoutRequest,
    ) -> ValidateCodePackageLayoutResponse:
        diagnostics = _validate_package_layout(request.layout_contract)
        valid = not diagnostics
        return ValidateCodePackageLayoutResponse(
            request_id=request.request_id,
            success=valid,
            valid=valid,
            diagnostics=diagnostics,
        )


class _CodeSectionDeltaCapabilityHandler:
    def __init__(self, *, support: _CodeProtocolSupport) -> None:
        self._support = support

    async def validate(
        self,
        request: ValidateCodeSectionDeltaRequest,
    ) -> ValidateCodeSectionDeltaResponse:
        _ = self._support
        diagnostics = _validate_section_delta_set(
            request.delta_set,
            strict=request.strict,
            require_resolver_inputs=True,
            registry=self._support.section_segment_capability_registry,
        )
        valid = not diagnostics
        return ValidateCodeSectionDeltaResponse(
            request_id=request.request_id,
            success=valid,
            valid=valid,
            diagnostics=diagnostics,
            entry_count=len(request.delta_set.entries),
        )

    async def normalize(
        self,
        request: NormalizeCodeSectionDeltaRequest,
    ) -> NormalizeCodeSectionDeltaResponse:
        _ = self._support
        return NormalizeCodeSectionDeltaResponse(
            request_id=request.request_id,
            success=True,
            delta_set=_normalize_section_delta_set(request.delta_set),
        )

    async def fingerprint(
        self,
        request: FingerprintCodeSectionDeltaRequest,
    ) -> FingerprintCodeSectionDeltaResponse:
        _ = self._support
        if request.algorithm != "sha256":
            return FingerprintCodeSectionDeltaResponse(
                request_id=request.request_id,
                success=False,
                error=(
                    "Unsupported CodeSectionDeltaSet fingerprint algorithm: "
                    f"{request.algorithm}"
                ),
                fingerprint=None,
                entry_count=len(request.delta_set.entries),
            )
        normalized = _normalize_section_delta_set(request.delta_set)
        payload = normalized.model_dump(mode="json", exclude_none=True)
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return FingerprintCodeSectionDeltaResponse(
            request_id=request.request_id,
            success=True,
            fingerprint=sha256(canonical).hexdigest(),
            entry_count=len(normalized.entries),
        )

    async def resolve_package_delta(
        self,
        request: ResolveCodeSectionDeltaPackageDeltaRequest,
    ) -> ResolveCodeSectionDeltaPackageDeltaResponse:
        _ = (self._support, request.layout_contract, request.semantic_contract)
        normalized = _normalize_section_delta_set(request.delta_set)
        diagnostics = _validate_section_delta_set(
            normalized,
            strict=request.strict,
            require_resolver_inputs=True,
            registry=self._support.section_segment_capability_registry,
        )
        if diagnostics:
            return ResolveCodeSectionDeltaPackageDeltaResponse(
                request_id=request.request_id,
                success=False,
                resolved=False,
                package_delta=None,
                diagnostics=diagnostics,
                entry_count=len(normalized.entries),
                path_count=0,
            )

        resolved_delta, resolve_diagnostics = _resolve_section_delta_set(
            normalized,
            strict=request.strict,
            registry=self._support.section_segment_capability_registry,
        )
        resolved = resolved_delta is not None and not resolve_diagnostics
        return ResolveCodeSectionDeltaPackageDeltaResponse(
            request_id=request.request_id,
            success=resolved,
            resolved=resolved,
            package_delta=resolved_delta,
            diagnostics=resolve_diagnostics,
            entry_count=len(normalized.entries),
            path_count=len(resolved_delta.paths) if resolved_delta is not None else 0,
        )

    async def resolve_render_policy(
        self,
        request: ResolveCodeSegmentRenderPolicyRequest,
    ) -> ResolveCodeSegmentRenderPolicyResponse:
        policies = code_segment_render_policies(
            language=_optional_text(request.language),
            section_type=_optional_text(request.section_type),
            segment_name=_optional_text(request.segment_name),
        )
        diagnostics: list[CodeSegmentRenderPolicyDiagnostic] = []
        if request.strict and not policies:
            diagnostics.append(
                CodeSegmentRenderPolicyDiagnostic(
                    reason="segment_render_policy_unavailable",
                    message=(
                        "Code does not expose a segment render policy for "
                        "the requested language/section/segment."
                    ),
                    language=_optional_text(request.language),
                    section_type=_optional_text(request.section_type),
                    segment_name=_optional_text(request.segment_name),
                )
            )
        resolved = not diagnostics and bool(policies)
        return ResolveCodeSegmentRenderPolicyResponse(
            request_id=request.request_id,
            success=not diagnostics,
            status=(
                CodeSegmentRenderPolicyResolutionStatus.resolved
                if resolved
                else CodeSegmentRenderPolicyResolutionStatus.blocked
            ),
            resolved=resolved,
            policies=[
                _code_segment_render_policy_dto(policy=policy) for policy in policies
            ],
            diagnostics=diagnostics,
            policy_count=len(policies),
        )


class _CodeSourceProjectionCapabilityHandler:
    def __init__(self, *, support: _CodeProtocolSupport) -> None:
        self._support = support

    async def validate(
        self,
        request: ValidateCodeSourceProjectionRequest,
    ) -> ValidateCodeSourceProjectionResponse:
        _ = self._support
        normalized_projection = _normalize_source_projection_request(request.projection)
        normalized_result = (
            _normalize_source_projection_result(request.result)
            if request.result is not None
            else None
        )
        diagnostics = _validate_source_projection(
            projection=normalized_projection,
            result=normalized_result,
            strict=request.strict,
            registry=self._support.section_segment_capability_registry,
        )
        valid = not diagnostics
        return ValidateCodeSourceProjectionResponse(
            request_id=request.request_id,
            success=valid,
            valid=valid,
            diagnostics=diagnostics,
            event_count=len(normalized_projection.events),
            action_count=len(normalized_projection.action_bindings),
            skipped_event_count=(
                len(normalized_result.skipped_events)
                if normalized_result is not None
                else 0
            ),
            has_delta_set=(
                normalized_result is not None
                and normalized_result.delta_set is not None
            ),
        )

    async def normalize(
        self,
        request: NormalizeCodeSourceProjectionRequest,
    ) -> NormalizeCodeSourceProjectionResponse:
        _ = self._support
        return NormalizeCodeSourceProjectionResponse(
            request_id=request.request_id,
            success=True,
            projection=_normalize_source_projection_request(request.projection),
            result=(
                _normalize_source_projection_result(request.result)
                if request.result is not None
                else None
            ),
        )

    async def fingerprint(
        self,
        request: FingerprintCodeSourceProjectionRequest,
    ) -> FingerprintCodeSourceProjectionResponse:
        _ = self._support
        if request.algorithm != "sha256":
            return FingerprintCodeSourceProjectionResponse(
                request_id=request.request_id,
                success=False,
                error=(
                    "Unsupported CodeSourceProjection fingerprint algorithm: "
                    f"{request.algorithm}"
                ),
                fingerprint=None,
                event_count=len(request.projection.events),
                action_count=len(request.projection.action_bindings),
                has_delta_set=(
                    request.result is not None and request.result.delta_set is not None
                ),
            )
        normalized_projection = _normalize_source_projection_request(request.projection)
        normalized_result = (
            _normalize_source_projection_result(request.result)
            if request.result is not None
            else None
        )
        payload: dict[str, object] = {
            "projection": normalized_projection.model_dump(
                mode="json",
                exclude_none=True,
            ),
        }
        if normalized_result is not None:
            payload["result"] = normalized_result.model_dump(
                mode="json",
                exclude_none=True,
            )
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return FingerprintCodeSourceProjectionResponse(
            request_id=request.request_id,
            success=True,
            fingerprint=sha256(canonical).hexdigest(),
            event_count=len(normalized_projection.events),
            action_count=len(normalized_projection.action_bindings),
            has_delta_set=(
                normalized_result is not None
                and normalized_result.delta_set is not None
            ),
        )

    async def resolve_package_delta(
        self,
        request: ResolveCodeSourceProjectionPackageDeltaRequest,
    ) -> ResolveCodeSourceProjectionPackageDeltaResponse:
        _ = (self._support, request.layout_contract, request.semantic_contract)
        normalized_projection = _normalize_source_projection_request(request.projection)
        normalized_result = _normalize_source_projection_result(request.result)
        diagnostics = _validate_source_projection(
            projection=normalized_projection,
            result=normalized_result,
            strict=request.strict,
            registry=self._support.section_segment_capability_registry,
        )
        (
            grammar_anchor_request,
            grammar_anchor_diagnostics,
        ) = _source_projection_grammar_anchor_render_delta_request(
            projection=normalized_projection,
            result=normalized_result,
        )
        for diagnostic in grammar_anchor_diagnostics:
            if diagnostic not in diagnostics:
                diagnostics.append(diagnostic)
        if grammar_anchor_request is not None:
            if not normalized_result.projected:
                diagnostics.append(
                    "result.projected must be true for source_projection "
                    "grammar-anchor package-delta resolution."
                )
            if diagnostics:
                return ResolveCodeSourceProjectionPackageDeltaResponse(
                    request_id=request.request_id,
                    success=False,
                    resolved=False,
                    package_delta=None,
                    diagnostics=diagnostics,
                    event_count=len(normalized_projection.events),
                    action_count=len(normalized_projection.action_bindings),
                    skipped_event_count=len(normalized_result.skipped_events),
                    entry_count=0,
                    path_count=0,
                )
            grammar_anchor_response = resolve_code_grammar_anchor_render_delta(
                request=grammar_anchor_request,
            )
            resolved = (
                grammar_anchor_response.success
                and grammar_anchor_response.resolved
                and grammar_anchor_response.package_delta is not None
            )
            return ResolveCodeSourceProjectionPackageDeltaResponse(
                request_id=request.request_id,
                success=resolved,
                resolved=resolved,
                package_delta=(
                    _source_projection_package_delta_with_metadata(
                        grammar_anchor_response.package_delta,
                        metadata={
                            "source_projection_mode": "grammar_anchor_first",
                            "source_projection_renderer": (
                                "grammar_anchor_render_delta"
                            ),
                            "source_projection_compatibility_fallback": False,
                            "render_entry_count": (
                                grammar_anchor_response.render_entry_count
                            ),
                        },
                    )
                    if grammar_anchor_response.package_delta is not None
                    else None
                ),
                diagnostics=[
                    f"grammar_anchor_render_delta.{diagnostic}"
                    for diagnostic in grammar_anchor_response.diagnostics
                ],
                event_count=len(normalized_projection.events),
                action_count=len(normalized_projection.action_bindings),
                skipped_event_count=len(normalized_result.skipped_events),
                entry_count=grammar_anchor_response.render_entry_count,
                path_count=grammar_anchor_response.path_count,
            )

        resolution_delta_set = _source_projection_resolution_delta_set(
            projection=normalized_projection,
            result=normalized_result,
        )
        hydration_diagnostics: list[str] = []
        if resolution_delta_set is not None:
            (
                resolution_delta_set,
                hydration_diagnostics,
            ) = _hydrate_section_delta_set_resolver_inputs(
                resolution_delta_set,
                registry=self._support.section_segment_capability_registry,
            )
            diagnostics.extend(
                f"result.delta_set.{diagnostic}" for diagnostic in hydration_diagnostics
            )
        if resolution_delta_set is None:
            required_delta_diagnostic = (
                "result.delta_set is required when result.projected is true."
            )
            if required_delta_diagnostic not in diagnostics:
                diagnostics.append(
                    "result.delta_set is required for source_projection "
                    "package-delta resolution."
                )
        elif not normalized_result.projected:
            diagnostics.append(
                "result.projected must be true for source_projection "
                "package-delta resolution."
            )

        if diagnostics or resolution_delta_set is None:
            return ResolveCodeSourceProjectionPackageDeltaResponse(
                request_id=request.request_id,
                success=False,
                resolved=False,
                package_delta=None,
                diagnostics=diagnostics,
                event_count=len(normalized_projection.events),
                action_count=len(normalized_projection.action_bindings),
                skipped_event_count=len(normalized_result.skipped_events),
                entry_count=(
                    len(resolution_delta_set.entries)
                    if resolution_delta_set is not None
                    else 0
                ),
                path_count=0,
            )

        resolver_diagnostics = _validate_section_delta_set(
            resolution_delta_set,
            strict=request.strict,
            require_resolver_inputs=True,
            registry=self._support.section_segment_capability_registry,
        )
        if resolver_diagnostics:
            return ResolveCodeSourceProjectionPackageDeltaResponse(
                request_id=request.request_id,
                success=False,
                resolved=False,
                package_delta=None,
                diagnostics=[
                    f"result.delta_set.{diagnostic}"
                    for diagnostic in resolver_diagnostics
                ],
                event_count=len(normalized_projection.events),
                action_count=len(normalized_projection.action_bindings),
                skipped_event_count=len(normalized_result.skipped_events),
                entry_count=len(resolution_delta_set.entries),
                path_count=0,
            )

        resolved_delta, resolve_diagnostics = _resolve_section_delta_set(
            resolution_delta_set,
            strict=request.strict,
            registry=self._support.section_segment_capability_registry,
        )
        resolved = resolved_delta is not None and not resolve_diagnostics
        return ResolveCodeSourceProjectionPackageDeltaResponse(
            request_id=request.request_id,
            success=resolved,
            resolved=resolved,
            package_delta=_source_projection_package_delta_with_metadata(
                resolved_delta,
                metadata={
                    "source_projection_mode": "section_delta_compatibility",
                    "source_projection_compatibility_fallback": True,
                },
            ),
            diagnostics=[
                f"result.delta_set.{diagnostic}" for diagnostic in resolve_diagnostics
            ],
            event_count=len(normalized_projection.events),
            action_count=len(normalized_projection.action_bindings),
            skipped_event_count=len(normalized_result.skipped_events),
            entry_count=len(resolution_delta_set.entries),
            path_count=len(resolved_delta.paths) if resolved_delta is not None else 0,
        )


class _CodeGeneratedMaterializationDeltaCapabilityHandler:
    def __init__(self, *, support: _CodeProtocolSupport) -> None:
        self._support = support

    async def validate(
        self,
        request: ValidateCodeGeneratedMaterializationDeltaRequest,
    ) -> ValidateCodeGeneratedMaterializationDeltaResponse:
        normalized_delta_request = _normalize_generated_materialization_delta_request(
            request.delta_request,
        )
        normalized_result = (
            _normalize_generated_materialization_delta_result(request.result)
            if request.result is not None
            else None
        )
        diagnostics = _validate_generated_materialization_delta(
            delta_request=normalized_delta_request,
            result=normalized_result,
            strict=request.strict,
            registry=self._support.section_segment_capability_registry,
        )
        valid = not diagnostics
        return ValidateCodeGeneratedMaterializationDeltaResponse(
            request_id=request.request_id,
            success=valid,
            valid=valid,
            diagnostics=diagnostics,
            event_count=len(normalized_delta_request.events),
            action_count=len(normalized_delta_request.action_bindings),
            target_count=len(normalized_delta_request.targets),
            entry_count=(
                len(normalized_result.entries) if normalized_result is not None else 0
            ),
            skipped_target_count=(
                len(normalized_result.skipped_targets)
                if normalized_result is not None
                else 0
            ),
            renderer_operation_count=(
                _generated_materialization_renderer_operation_count(
                    normalized_result,
                )
            ),
            package_delta_entry_count=_generated_materialization_package_delta_count(
                normalized_result,
            ),
            grammar_anchor_render_entry_count=(
                _generated_materialization_grammar_anchor_render_count(
                    normalized_result,
                )
            ),
            section_delta_entry_count=_generated_materialization_section_delta_count(
                normalized_result,
            ),
        )

    async def normalize(
        self,
        request: NormalizeCodeGeneratedMaterializationDeltaRequest,
    ) -> NormalizeCodeGeneratedMaterializationDeltaResponse:
        _ = self._support
        return NormalizeCodeGeneratedMaterializationDeltaResponse(
            request_id=request.request_id,
            success=True,
            delta_request=_normalize_generated_materialization_delta_request(
                request.delta_request,
            ),
            result=(
                _normalize_generated_materialization_delta_result(request.result)
                if request.result is not None
                else None
            ),
        )

    async def fingerprint(
        self,
        request: FingerprintCodeGeneratedMaterializationDeltaRequest,
    ) -> FingerprintCodeGeneratedMaterializationDeltaResponse:
        _ = self._support
        if request.algorithm != "sha256":
            return FingerprintCodeGeneratedMaterializationDeltaResponse(
                request_id=request.request_id,
                success=False,
                error=(
                    "Unsupported CodeGeneratedMaterializationDelta fingerprint "
                    f"algorithm: {request.algorithm}"
                ),
                fingerprint=None,
                event_count=len(request.delta_request.events),
                action_count=len(request.delta_request.action_bindings),
                target_count=len(request.delta_request.targets),
                entry_count=(
                    len(request.result.entries) if request.result is not None else 0
                ),
                renderer_operation_count=(
                    _generated_materialization_renderer_operation_count(
                        request.result,
                    )
                ),
                package_delta_entry_count=(
                    _generated_materialization_package_delta_count(request.result)
                ),
                grammar_anchor_render_entry_count=(
                    _generated_materialization_grammar_anchor_render_count(
                        request.result,
                    )
                ),
                section_delta_entry_count=(
                    _generated_materialization_section_delta_count(request.result)
                ),
            )
        normalized_delta_request = _normalize_generated_materialization_delta_request(
            request.delta_request,
        )
        normalized_result = (
            _normalize_generated_materialization_delta_result(request.result)
            if request.result is not None
            else None
        )
        payload: dict[str, object] = {
            "delta_request": normalized_delta_request.model_dump(
                mode="json",
                exclude_none=True,
            ),
        }
        if normalized_result is not None:
            payload["result"] = normalized_result.model_dump(
                mode="json",
                exclude_none=True,
            )
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return FingerprintCodeGeneratedMaterializationDeltaResponse(
            request_id=request.request_id,
            success=True,
            fingerprint=sha256(canonical).hexdigest(),
            event_count=len(normalized_delta_request.events),
            action_count=len(normalized_delta_request.action_bindings),
            target_count=len(normalized_delta_request.targets),
            entry_count=(
                len(normalized_result.entries) if normalized_result is not None else 0
            ),
            renderer_operation_count=(
                _generated_materialization_renderer_operation_count(
                    normalized_result,
                )
            ),
            package_delta_entry_count=(
                _generated_materialization_package_delta_count(normalized_result)
            ),
            grammar_anchor_render_entry_count=(
                _generated_materialization_grammar_anchor_render_count(
                    normalized_result,
                )
            ),
            section_delta_entry_count=(
                _generated_materialization_section_delta_count(normalized_result)
            ),
        )

    async def resolve_package_delta(
        self,
        request: ResolveCodeGeneratedMaterializationPackageDeltaRequest,
    ) -> ResolveCodeGeneratedMaterializationPackageDeltaResponse:
        _ = (self._support, request.layout_contract, request.semantic_contract)
        normalized_delta_request = _normalize_generated_materialization_delta_request(
            request.delta_request,
        )
        normalized_result = _normalize_generated_materialization_delta_result(
            request.result,
        )
        diagnostics = _validate_generated_materialization_delta(
            delta_request=normalized_delta_request,
            result=normalized_result,
            strict=request.strict,
            registry=self._support.section_segment_capability_registry,
        )
        if not normalized_result.available:
            diagnostics.append(
                "result.available must be true for generated materialization "
                "package-delta resolution."
            )

        if diagnostics:
            return ResolveCodeGeneratedMaterializationPackageDeltaResponse(
                request_id=request.request_id,
                success=False,
                resolved=False,
                package_delta=None,
                diagnostics=diagnostics,
                event_count=len(normalized_delta_request.events),
                action_count=len(normalized_delta_request.action_bindings),
                target_count=len(normalized_delta_request.targets),
                skipped_target_count=len(normalized_result.skipped_targets),
                entry_count=len(normalized_result.entries),
                path_count=0,
                renderer_operation_count=(
                    _generated_materialization_renderer_operation_count(
                        normalized_result,
                    )
                ),
                package_delta_entry_count=(
                    _generated_materialization_package_delta_count(
                        normalized_result,
                    )
                ),
                grammar_anchor_render_entry_count=(
                    _generated_materialization_grammar_anchor_render_count(
                        normalized_result,
                    )
                ),
                section_delta_entry_count=(
                    _generated_materialization_section_delta_count(
                        normalized_result,
                    )
                ),
            )

        resolved_delta, resolve_diagnostics = (
            _resolve_generated_materialization_package_delta(
                delta_request=normalized_delta_request,
                result=normalized_result,
                strict=request.strict,
                registry=self._support.section_segment_capability_registry,
            )
        )
        resolved = resolved_delta is not None and not resolve_diagnostics
        return ResolveCodeGeneratedMaterializationPackageDeltaResponse(
            request_id=request.request_id,
            success=resolved,
            resolved=resolved,
            package_delta=resolved_delta,
            diagnostics=resolve_diagnostics,
            event_count=len(normalized_delta_request.events),
            action_count=len(normalized_delta_request.action_bindings),
            target_count=len(normalized_delta_request.targets),
            skipped_target_count=len(normalized_result.skipped_targets),
            entry_count=len(normalized_result.entries),
            path_count=len(resolved_delta.paths) if resolved_delta is not None else 0,
            renderer_operation_count=(
                _generated_materialization_renderer_operation_count(
                    normalized_result,
                )
            ),
            package_delta_entry_count=(
                _generated_materialization_package_delta_count(normalized_result)
            ),
            grammar_anchor_render_entry_count=(
                _generated_materialization_grammar_anchor_render_count(
                    normalized_result,
                )
            ),
            section_delta_entry_count=(
                _generated_materialization_section_delta_count(normalized_result)
            ),
        )


class _CodeSourceOwnershipCapabilityHandler:
    def __init__(self, *, support: _CodeProtocolSupport) -> None:
        self._support = support

    async def classify(
        self,
        request: ClassifyCodeSourceOwnershipRequest,
    ) -> ClassifyCodeSourceOwnershipResponse:
        _ = self._support
        return classify_code_source_ownership_request(request)


def classify_code_source_ownership_request(
    request: ClassifyCodeSourceOwnershipRequest,
) -> ClassifyCodeSourceOwnershipResponse:
    normalized_request = _normalize_source_ownership_request(request.ownership_request)
    result = classify_source_ownership(
        package_bindings=tuple(
            _runtime_source_ownership_binding(binding)
            for binding in normalized_request.package_bindings
        ),
        observed_paths=tuple(
            _runtime_source_ownership_observed_path(observed_path)
            for observed_path in normalized_request.observed_paths
        ),
        strict=normalized_request.strict,
    )
    api_result = CodeSourceOwnershipResult(
        matches=[
            CodeSourceOwnershipPathMatch(
                path=match.path,
                classification=ApiCodeSourceOwnershipClassification(
                    match.classification.value
                ),
                package_name=match.package_name,
                manifest_relative_path=match.manifest_relative_path,
                package_root=match.package_root,
                sources_root=match.sources_root,
                package_relative_path=match.package_relative_path,
                binding_index=match.binding_index,
                language=match.language,
                is_structural=match.is_structural,
            )
            for match in result.matches
        ],
        diagnostics=list(result.diagnostics),
        package_count=result.package_count,
        path_count=result.path_count,
        source_owned_path_count=result.source_owned_path_count,
        generated_fallout_path_count=result.generated_fallout_path_count,
        unmapped_path_count=result.unmapped_path_count,
        metadata=normalized_request.metadata,
    )
    return ClassifyCodeSourceOwnershipResponse(
        request_id=request.request_id,
        success=not result.diagnostics,
        ownership_result=api_result,
    )


def _normalize_source_ownership_request(
    ownership_request: CodeSourceOwnershipRequest,
) -> CodeSourceOwnershipRequest:
    return CodeSourceOwnershipRequest(
        workspace_root=_optional_path_text(ownership_request.workspace_root),
        package_bindings=sorted(
            (
                CodeSourceOwnershipPackageBinding(
                    package_name=binding.package_name.strip(),
                    package_root=_optional_path_text(binding.package_root) or ".",
                    sources_root=_optional_path_text(binding.sources_root),
                    manifest_relative_path=_optional_path_text(
                        binding.manifest_relative_path
                    ),
                    language=_optional_text(binding.language),
                    surface=_optional_text(binding.surface),
                    manifest_kind=_optional_text(binding.manifest_kind),
                    generated_roots=sorted(
                        root
                        for root in (
                            _optional_path_text(root)
                            for root in binding.generated_roots
                        )
                        if root is not None
                    ),
                    owned_file_paths=sorted(
                        path
                        for path in (
                            _optional_path_text(path)
                            for path in binding.owned_file_paths
                        )
                        if path is not None
                    ),
                    metadata=binding.metadata,
                )
                for binding in ownership_request.package_bindings
            ),
            key=_source_ownership_binding_sort_key,
        ),
        observed_paths=sorted(
            (
                CodeSourceOwnershipObservedPath(
                    path=_optional_path_text(observed_path.path) or ".",
                    language=_optional_text(observed_path.language),
                    is_structural=observed_path.is_structural,
                    metadata=observed_path.metadata,
                )
                for observed_path in ownership_request.observed_paths
            ),
            key=lambda item: item.path,
        ),
        strict=ownership_request.strict,
        metadata=ownership_request.metadata,
    )


def _layout_contract_from_code_package(
    *,
    package: CodePackageInfo,
    provider_key: str,
) -> CodePackageLayoutContract:
    manifest_kind = _metadata_text(package.metadata, "manifest_kind")
    sources_root = _metadata_text(package.metadata, "source_root") or _metadata_text(
        package.metadata, "sources_root"
    )
    metadata: dict[str, object] = {
        "provider_key": provider_key,
        "language": package.language.value,
        "manifest_kind": manifest_kind,
    }
    for key, value in package.metadata.items():
        if key in {"code_package_surface", "surface"} or value is None:
            continue
        metadata[key] = _jsonable_code_metadata(value)
    return CodePackageLayoutContract(
        package_name=package.name,
        package_root=package.root_path.as_posix(),
        sources_root=sources_root,
        surface=_layout_surface_from_code_package(package),
        generated_roots=_generated_roots_from_code_package(package),
        manifest_relative_path=package.manifest_path.as_posix(),
        path_roles=[
            CodePackageLayoutPathRole(
                role=CodePackagePathRole.authored_source,
                include_patterns=_authored_include_patterns_from_code_package(package),
                exclude_patterns=_generated_exclude_patterns_from_code_package(package),
                semantic_owner_hints=[provider_key],
                metadata=JsonObject(
                    {"source": "aware_code_service.package_layout.discover"}
                ),
            ),
            CodePackageLayoutPathRole(
                role=CodePackagePathRole.generated_metadata,
                include_patterns=_generated_include_patterns_from_code_package(package),
                exclude_patterns=[],
                semantic_owner_hints=[provider_key],
                metadata=JsonObject(
                    {"source": "aware_code_service.package_layout.discover"}
                ),
            ),
        ],
        metadata=JsonObject(cast(dict[str, JsonValue], metadata)),
    )


def _layout_surface_from_code_package(package: CodePackageInfo) -> str | None:
    return normalize_code_package_surface(package.metadata.get("code_package_surface"))


async def _discover_code_packages_from_manifest_paths(
    *,
    workspace_root: Path,
    manifest_paths: tuple[str, ...],
    support: _CodeProtocolSupport,
) -> list[CodePackageInfo]:
    aware_packages, generic_manifest_paths = (
        _aware_code_packages_and_generic_manifest_paths(
            workspace_root=workspace_root,
            manifest_paths=manifest_paths,
            support=support,
        )
    )
    generic_packages: list[CodePackageInfo] = []
    if generic_manifest_paths:
        generic_packages = await asyncio.to_thread(
            discover_packages_from_manifest_paths,
            workspace_root=workspace_root,
            manifest_paths=generic_manifest_paths,
        )
    return [*aware_packages, *generic_packages]


def _discover_code_packages_from_manifest_paths_sync(
    *,
    workspace_root: Path,
    manifest_paths: tuple[str, ...],
    support: _CodeProtocolSupport,
) -> list[CodePackageInfo]:
    aware_packages, generic_manifest_paths = (
        _aware_code_packages_and_generic_manifest_paths(
            workspace_root=workspace_root,
            manifest_paths=manifest_paths,
            support=support,
        )
    )
    generic_packages: list[CodePackageInfo] = []
    if generic_manifest_paths:
        generic_packages = discover_packages_from_manifest_paths(
            workspace_root=workspace_root,
            manifest_paths=generic_manifest_paths,
        )
    return [*aware_packages, *generic_packages]


def _aware_code_packages_and_generic_manifest_paths(
    *,
    workspace_root: Path,
    manifest_paths: tuple[str, ...],
    support: _CodeProtocolSupport,
) -> tuple[list[CodePackageInfo], list[str]]:
    aware_packages: list[CodePackageInfo] = []
    generic_manifest_paths: list[str] = []
    for manifest_path in manifest_paths:
        if _is_aware_manifest_path(manifest_path):
            code_package = _code_package_from_aware_semantic_manifest(
                workspace_root=workspace_root,
                manifest_path=manifest_path,
                support=support,
            )
            if code_package is not None:
                aware_packages.append(code_package)
            continue
        generic_manifest_paths.append(manifest_path)
    return aware_packages, generic_manifest_paths


def _code_package_from_aware_semantic_manifest(
    *,
    workspace_root: Path,
    manifest_path: str,
    support: _CodeProtocolSupport,
) -> CodePackageInfo | None:
    resolved_manifest_path = (workspace_root / manifest_path).resolve()
    try:
        resolution = resolve_semantic_manifest(
            manifest_path=resolved_manifest_path,
            contracts=support.semantic_contracts,
        )
    except Exception:
        return None
    return code_package_info_from_semantic_manifest_resolution(
        resolution=resolution,
        workspace_root=workspace_root,
        manifest_relative_path=manifest_path,
    )


def _is_aware_manifest_path(manifest_path: str) -> bool:
    name = Path(manifest_path).name
    return name == "aware.toml" or (
        name.startswith("aware.") and name.endswith(".toml")
    )


def _authored_include_patterns_from_code_package(
    package: CodePackageInfo,
) -> list[str]:
    if package.language is CodeLanguage.python:
        return ["**/*.py", "**/*.toml"]
    if package.language is CodeLanguage.dart:
        return ["**/*.dart", "**/*.yaml", "**/*.toml"]
    if package.language is CodeLanguage.aware:
        return ["**/*.aware", "**/*.toml"]
    return ["**/*"]


def _generated_roots_from_code_package(package: CodePackageInfo) -> list[str]:
    roots = [".aware", "__pycache__"]
    raw_generated_roots = package.metadata.get("generated_roots")
    if isinstance(raw_generated_roots, (list, tuple)):
        roots.extend(
            value
            for value in raw_generated_roots
            if isinstance(value, str) and value.strip()
        )
    return sorted(set(roots))


def _generated_include_patterns_from_code_package(
    package: CodePackageInfo,
) -> list[str]:
    return [
        root if root.endswith("/**") else f"{root}/**"
        for root in _generated_roots_from_code_package(package)
    ]


def _generated_exclude_patterns_from_code_package(
    package: CodePackageInfo,
) -> list[str]:
    return _generated_include_patterns_from_code_package(package)


def _metadata_text(metadata: dict[str, object], key: str) -> str | None:
    value = metadata.get(key)
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _normalize_relative_path_text(path: str) -> str:
    return str(PurePosixPath(str(path).replace("\\", "/")))


def _jsonable_code_metadata(value: object) -> object:
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, dict):
        return {str(key): _jsonable_code_metadata(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable_code_metadata(item) for item in value]
    raw_value = getattr(value, "value", None)
    if isinstance(raw_value, str):
        return raw_value
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _record_code_service_phase_timing(
    *,
    phase_timings_s: dict[str, float],
    key: str,
    started_at: float,
) -> None:
    phase_timings_s[key] = round(max(perf_counter() - started_at, 0.0), 6)


def _semantic_source_index_evidence_json_object(
    source_index_evidence: Mapping[str, object],
    *,
    service_phase_timings_s: Mapping[str, float] | None = None,
) -> JsonObject:
    payload = {
        str(key): _jsonable_code_metadata(value)
        for key, value in source_index_evidence.items()
    }
    if service_phase_timings_s is not None:
        payload["service_phase_timings_s"] = {
            str(key): float(value) for key, value in service_phase_timings_s.items()
        }
    return JsonObject(cast(dict[str, JsonValue], payload))


def _runtime_source_ownership_binding(
    binding: CodeSourceOwnershipPackageBinding,
) -> RuntimeCodeSourceOwnershipPackageBinding:
    return RuntimeCodeSourceOwnershipPackageBinding(
        package_name=binding.package_name,
        package_root=binding.package_root,
        sources_root=binding.sources_root,
        manifest_relative_path=binding.manifest_relative_path,
        language=binding.language,
        surface=binding.surface,
        manifest_kind=binding.manifest_kind,
        generated_roots=tuple(binding.generated_roots),
        owned_file_paths=frozenset(binding.owned_file_paths),
        metadata=dict(binding.metadata or {}),
    )


def _runtime_source_ownership_observed_path(
    observed_path: CodeSourceOwnershipObservedPath,
) -> RuntimeCodeSourceOwnershipObservedPath:
    return RuntimeCodeSourceOwnershipObservedPath(
        path=observed_path.path,
        language=observed_path.language,
        is_structural=observed_path.is_structural,
        metadata=dict(observed_path.metadata or {}),
    )


def _source_ownership_binding_sort_key(
    binding: CodeSourceOwnershipPackageBinding,
) -> tuple[str, ...]:
    return (
        binding.package_root,
        binding.package_name,
        binding.manifest_relative_path or "",
    )


def _normalize_package_delta(delta: CodePackageDelta) -> CodePackageDelta:
    normalized_paths = sorted(
        (
            CodePackageDeltaPath.model_validate(path.model_dump(mode="json"))
            for path in delta.paths
        ),
        key=lambda item: item.relative_path,
    )
    return CodePackageDelta(
        package_name=delta.package_name,
        package_root=delta.package_root,
        sources_root=delta.sources_root,
        manifest_relative_path=delta.manifest_relative_path,
        authority=delta.authority or CodePackageDeltaAuthorityKind.code_package_delta,
        authority_kind=(
            delta.authority_kind
            or (
                delta.authority.value
                if delta.authority is not None
                else "code_package_delta"
            )
        ),
        source_revision_id=delta.source_revision_id,
        production=delta.production,
        paths=normalized_paths,
        warnings=list(delta.warnings),
        metadata=delta.metadata,
    )


def _fingerprint_package_delta(delta: CodePackageDelta) -> str:
    payload = delta.model_dump(mode="json", exclude_none=True)
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(canonical).hexdigest()


def _runtime_code_package_delta(delta: CodePackageDelta) -> RuntimeCodePackageDelta:
    return RuntimeCodePackageDelta.model_validate(
        delta.model_dump(mode="json", exclude_none=True)
    )


def _resolve_semantic_analysis_provider(
    *,
    provider_key: str,
    semantic_owner: str | None,
) -> object | None:
    resolved = AwareModulePluginRegistry.resolve_semantic_capability_provider(
        provider_key=provider_key,
        capability=SEMANTIC_ANALYSIS_CAPABILITY,
        semantic_owner=semantic_owner,
    )
    if resolved is not None:
        return resolved

    providers = AwareModulePluginRegistry.resolve_language_service_capability_execution_providers(
        capability=SEMANTIC_ANALYSIS_CAPABILITY,
        module_provider_keys=(provider_key,),
    )
    for provider in providers:
        descriptor = getattr(provider, "descriptor", None)
        descriptor_owner = _optional_text(getattr(descriptor, "semantic_owner", None))
        if semantic_owner is None or descriptor_owner == semantic_owner:
            return provider
    return None


def _semantic_analysis_provider_callable(
    resolved_provider: object,
) -> Callable[[SemanticAnalysisCapabilityRequest], object] | None:
    provider = getattr(resolved_provider, "provider", None)
    if not callable(provider):
        return None
    return cast(Callable[[SemanticAnalysisCapabilityRequest], object], provider)


def _semantic_analysis_provider_owner(resolved_provider: object) -> str | None:
    owner = _optional_text(getattr(resolved_provider, "semantic_owner", None))
    if owner is not None:
        return owner
    descriptor = getattr(resolved_provider, "descriptor", None)
    return _optional_text(getattr(descriptor, "semantic_owner", None))


def _semantic_analysis_workspace_root(
    request: PreviewCodeSemanticAnalysisPackageDeltaRequest,
) -> Path:
    return Path(request.workspace_root or ".").expanduser().resolve()


def _semantic_analysis_package_root(
    *,
    request: PreviewCodeSemanticAnalysisPackageDeltaRequest,
    delta: CodePackageDelta,
) -> Path:
    raw_path = request.package_root or delta.package_root or "."
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (_semantic_analysis_workspace_root(request) / path).resolve()


def _semantic_analysis_manifest_path(
    *,
    request: PreviewCodeSemanticAnalysisPackageDeltaRequest,
    delta: CodePackageDelta,
) -> Path | None:
    raw_path = request.manifest_path or delta.manifest_relative_path
    if raw_path is None or not raw_path.strip():
        return None
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (_semantic_analysis_workspace_root(request) / path).resolve()


def _semantic_analysis_source_files(
    *,
    request: PreviewCodeSemanticAnalysisPackageDeltaRequest,
    delta: CodePackageDelta,
) -> tuple[Path, ...]:
    source_files = tuple(_optional_path_text(path) for path in request.source_files)
    resolved = tuple(Path(path) for path in source_files if path is not None)
    if resolved:
        return resolved
    return tuple(
        Path(path.relative_path)
        for path in delta.paths
        if _optional_path_text(path.relative_path) is not None
    )


def _semantic_analysis_preview_blocked_response(
    *,
    request: PreviewCodeSemanticAnalysisPackageDeltaRequest,
    delta_fingerprint: str,
    blockers: tuple[str, ...],
    error: str,
    provider_key: str | None = None,
    semantic_owner: str | None = None,
) -> PreviewCodeSemanticAnalysisPackageDeltaResponse:
    return PreviewCodeSemanticAnalysisPackageDeltaResponse(
        request_id=request.request_id,
        success=False,
        error=error,
        previewed=False,
        provider_key=provider_key,
        semantic_owner=semantic_owner,
        delta_fingerprint=delta_fingerprint,
        blockers=list(blockers),
        available=False,
    )


def _semantic_source_meaning_blocked_response(
    *,
    request: ResolveCodeSemanticSourceMeaningRequest,
    diagnostics: tuple[str, ...],
) -> ResolveCodeSemanticSourceMeaningResponse:
    return ResolveCodeSemanticSourceMeaningResponse(
        request_id=request.request_id,
        success=False,
        error="; ".join(diagnostics),
        resolved=False,
        status="blocked",
        diagnostics=list(diagnostics),
        contract_version=CODE_SEMANTIC_SOURCE_MEANING_BINDING_CONTRACT_VERSION,
        provider_key=request.contract.provider_key,
        semantic_owner=request.contract.semantic_owner,
        binding_count=len(request.contract.bindings),
        source_index_evidence=JsonObject({}),
        metadata=JsonObject(
            {"source": "aware_code_service.semantic_source_meaning.resolve"}
        ),
    )


def _semantic_source_delta_meaning_blocked_response(
    *,
    request: ResolveCodeSemanticSourceDeltaMeaningRequest,
    diagnostics: tuple[str, ...],
    required_context: tuple[str, ...],
) -> ResolveCodeSemanticSourceDeltaMeaningResponse:
    return ResolveCodeSemanticSourceDeltaMeaningResponse(
        request_id=request.request_id,
        success=False,
        error="; ".join((*diagnostics, *required_context)),
        resolved=False,
        status="blocked",
        meaning_resolution_mode=CodeSemanticSourceDeltaMeaningResolutionMode.blocked,
        diagnostics=list(diagnostics),
        required_context=list(required_context),
        contract_version=CODE_SEMANTIC_SOURCE_DELTA_MEANING_CONTRACT_VERSION,
        provider_key=request.contract.provider_key,
        semantic_owner=request.contract.semantic_owner,
        binding_count=len(request.contract.bindings),
        source_index_evidence=JsonObject({}),
        metadata=JsonObject(
            {"source": "aware_code_service.semantic_source_meaning.resolve_delta"}
        ),
    )


def _runtime_semantic_source_meaning_contract(
    contract: CodeSemanticSourceMeaningContract,
) -> RuntimeCodeSemanticSourceMeaningContract:
    supported_languages = tuple(
        language.strip()
        for language in contract.supported_languages
        if language.strip()
    ) or ("aware",)
    return RuntimeCodeSemanticSourceMeaningContract(
        provider_key=contract.provider_key,
        semantic_owner=contract.semantic_owner,
        grammar_profile_key=_optional_text(contract.grammar_profile_key),
        supported_languages=supported_languages,
        bindings=tuple(
            _runtime_semantic_source_meaning_binding(binding)
            for binding in contract.bindings
        ),
        metadata=dict(contract.metadata or {}),
    )


def _runtime_semantic_source_meaning_binding(
    binding: CodeSemanticSourceMeaningBinding,
) -> RuntimeCodeSemanticSourceMeaningBinding:
    return RuntimeCodeSemanticSourceMeaningBinding(
        binding_key=binding.binding_key,
        language=binding.language,
        grammar_profile_key=_optional_text(binding.grammar_profile_key),
        grammar_rule_name=binding.grammar_rule_name,
        anchor_field_path=binding.anchor_field_path,
        graph_selector=CodeGrammarGraphSelector.from_object(binding.graph_selector),
        semantic_subject_type=binding.semantic_subject_type,
        semantic_key_template=binding.semantic_key_template,
        semantic_field=binding.semantic_field,
        anchor_role=_optional_text(binding.anchor_role),
        value_domain=_optional_text(binding.value_domain),
        event_key_template=_optional_text(binding.event_key_template),
        event_type=binding.event_type,
        condition_keys=tuple(binding.condition_keys),
        template_value_bindings=tuple(
            CodeGrammarTemplateValueBinding(
                value_key=item.value_key,
                field_path=item.field_path,
                grammar_rule_name=_optional_text(item.grammar_rule_name),
                required=item.required,
            )
            for item in binding.template_value_bindings
        ),
        typed_operation_bindings=tuple(
            RuntimeCodeSemanticSourceMeaningTypedOperationBinding(
                operation_key_template=_optional_text(item.operation_key_template),
                event_verbs=tuple(
                    cast(SemanticCapabilityEventVerb, verb) for verb in item.event_verbs
                ),
                operation_family=cast(
                    SemanticCapabilityEventVerb | None,
                    _optional_text(item.operation_family),
                ),
                semantic_operation_type=item.semantic_operation_type,
                semantic_subject_type=_optional_text(item.semantic_subject_type),
                field_path=_optional_text(item.field_path),
                requires_baseline_object_identity=(
                    item.requires_baseline_object_identity
                ),
                contract_source=_optional_text(item.contract_source),
                semantic_apply_boundary=_optional_text(item.semantic_apply_boundary),
                preview_only=item.preview_only,
                fallback_required=item.fallback_required,
                fallback_reason=_optional_text(item.fallback_reason),
                generated_materialization_intent=(
                    dict(item.generated_materialization_intent)
                    if item.generated_materialization_intent is not None
                    else None
                ),
            )
            for item in binding.typed_operation_bindings
        ),
        required=binding.required,
        metadata=dict(binding.metadata or {}),
    )


def _runtime_semantic_source_index_ref(
    ref: CodeSemanticSourceIndexRef | None,
) -> RuntimeCodeSemanticSourceIndexRef | None:
    if ref is None:
        return None
    return RuntimeCodeSemanticSourceIndexRef(
        ref_kind=ref.ref_kind,
        cache_kind=_optional_text(ref.cache_kind),
        cache_key=_optional_text(ref.cache_key),
        source_session_id=_optional_text(ref.source_session_id),
        source_delta_fingerprint=_optional_text(ref.source_delta_fingerprint),
        package_name=_optional_text(ref.package_name),
        source_revision_id=_optional_text(ref.source_revision_id),
        source_keys=tuple(ref.source_keys),
        source_hashes=dict(ref.source_hashes or {}),
        metadata=dict(ref.metadata or {}),
    )


def _semantic_source_meaning_source_index(
    sources: list[CodeSemanticSourceMeaningSource],
    *,
    session_context: SemanticSourceSessionContext | None,
) -> CodeGrammarSourceIndex:
    return _SEMANTIC_SOURCE_MEANING_SOURCE_INDEX_CACHE.get_or_build(
        sources=tuple(
            _runtime_semantic_source_meaning_source(source) for source in sources
        ),
        session_context=session_context,
    )


def _runtime_semantic_source_meaning_source(
    source: CodeSemanticSourceMeaningSource,
) -> CodeGrammarSource:
    return CodeGrammarSource(
        source_key=source.source_key,
        source_text=source.source_text,
        language=source.language,
        grammar_profile_key=_optional_text(source.grammar_profile_key),
        relative_path=_optional_text(source.relative_path),
    )


def _semantic_source_meaning_session_context(
    *,
    metadata: Mapping[str, object] | None,
) -> SemanticSourceSessionContext | None:
    if not isinstance(metadata, Mapping):
        return None
    payload = metadata.get(SEMANTIC_SOURCE_SESSION_CONTEXT_KEY)
    if payload is None:
        return None
    return SemanticSourceSessionContext.from_payload(payload)


def _semantic_source_meaning_source_hash_diagnostics(
    *,
    label: str,
    sources: list[CodeSemanticSourceMeaningSource],
) -> tuple[str, ...]:
    diagnostics: list[str] = []
    for index, source in enumerate(sources):
        before_hash = _optional_text(source.before_hash)
        if before_hash is None:
            continue
        actual_hash = _sha256_digest(source.source_text)
        if before_hash != actual_hash:
            diagnostics.append(
                f"{label}[{index}].before_hash mismatch for "
                f"{source.source_key!r}: expected {before_hash}, got {actual_hash}."
            )
    return tuple(diagnostics)


def _code_semantic_analysis_diagnostic(
    diagnostic: SemanticCapabilityDiagnostic,
) -> CodeSemanticAnalysisDiagnostic:
    return CodeSemanticAnalysisDiagnostic(
        severity=diagnostic.severity,
        code=diagnostic.code,
        message=diagnostic.message,
        source_path=diagnostic.source_path,
        metadata=_json_object_from_mapping(diagnostic.metadata),
    )


def _code_semantic_analysis_change_preview(
    preview: SemanticCapabilityChangePreview,
) -> CodeSemanticAnalysisChangePreview:
    return CodeSemanticAnalysisChangePreview(
        changed_source_files=list(preview.changed_source_files),
        affected_semantic_keys=list(preview.affected_semantic_keys),
        required_materializations=list(preview.required_materializations),
        required_semantic_dependencies=[
            _code_semantic_analysis_dependency_requirement(dependency)
            for dependency in preview.required_semantic_dependencies
        ],
        semantic_deltas=[
            _code_semantic_delta(delta) for delta in preview.semantic_deltas
        ],
        semantic_events=[
            _code_semantic_event(event) for event in preview.semantic_events
        ],
        typed_operations=[
            _code_semantic_typed_operation(operation)
            for operation in preview.typed_operations
        ],
        action_bindings=[
            _code_semantic_action_binding(binding)
            for binding in preview.action_bindings
        ],
        metadata=_json_object_from_mapping(preview.metadata),
    )


def _code_semantic_analysis_dependency_requirement(
    dependency: SemanticCapabilityDependencyRequirement,
) -> CodeSemanticAnalysisDependencyRequirement:
    return CodeSemanticAnalysisDependencyRequirement(
        dependency_key=dependency.dependency_key,
        provider_key=dependency.provider_key,
        package_name=dependency.package_name,
        required_state=dependency.required_state,
        dependency_kind=dependency.dependency_kind,
        semantic_owner=dependency.semantic_owner,
        manifest_kind=dependency.manifest_kind,
        package_selector=_json_object_from_mapping(dependency.package_selector),
        reason=dependency.reason,
        source_refs=list(dependency.source_refs),
        metadata=_json_object_from_mapping(dependency.metadata),
    )


def _code_semantic_delta(delta: SemanticCapabilityDelta) -> CodeSemanticDelta:
    return CodeSemanticDelta(
        delta_key=delta.delta_key,
        semantic_key=delta.semantic_key,
        verb=delta.verb,
        subject_type=delta.subject_type,
        source=delta.source,
        source_refs=list(delta.source_refs),
        before_payload=_json_object_from_mapping(delta.before_payload),
        after_payload=_json_object_from_mapping(delta.after_payload),
        metadata=_json_object_from_mapping(delta.metadata),
    )


def _code_semantic_event(event: SemanticCapabilityEvent) -> CodeSemanticEvent:
    return CodeSemanticEvent(
        event_key=event.event_key,
        semantic_key=event.semantic_key,
        verb=event.verb,
        subject_type=event.subject_type,
        source=event.source,
        event_type=event.event_type,
        source_refs=list(event.source_refs),
        delta_keys=list(event.delta_keys),
        condition_keys=list(event.condition_keys),
        payload=_json_object_from_mapping(event.payload),
        metadata=_json_object_from_mapping(event.metadata),
    )


def _code_semantic_typed_operation(
    operation: SemanticCapabilityTypedOperation,
) -> CodeSemanticTypedOperation:
    return CodeSemanticTypedOperation(
        operation_key=operation.operation_key,
        operation_family=operation.operation_family,
        semantic_operation_type=operation.semantic_operation_type,
        semantic_key=operation.semantic_key,
        semantic_subject_type=operation.semantic_subject_type,
        field_path=operation.field_path,
        event_key=operation.event_key,
        source=operation.source,
        source_refs=list(operation.source_refs),
        before_payload=_json_object_from_mapping(operation.before_payload),
        after_payload=_json_object_from_mapping(operation.after_payload),
        requires_baseline_object_identity=(operation.requires_baseline_object_identity),
        metadata=_json_object_from_mapping(operation.metadata),
    )


def _code_semantic_action_binding(
    binding: SemanticCapabilityActionBinding,
) -> CodeSemanticActionBinding:
    return CodeSemanticActionBinding(
        action_key=binding.action_key,
        event_key=binding.event_key,
        action_type=binding.action_type,
        description=binding.description,
        function_call_binding=(
            _code_semantic_function_call_binding(binding.function_call_binding)
            if binding.function_call_binding is not None
            else None
        ),
        metadata=_json_object_from_mapping(binding.metadata),
    )


def _code_semantic_function_call_binding(
    binding: SemanticCapabilityFunctionCallBinding,
) -> CodeSemanticFunctionCallBinding:
    return CodeSemanticFunctionCallBinding(
        binding_key=binding.binding_key,
        event_key=binding.event_key,
        function_ref=binding.function_ref,
        receiver_semantic_key_template=binding.receiver_semantic_key_template,
        argument_bindings=_json_object_from_mapping(binding.argument_bindings),
        argument_ref_bindings=_json_object_from_mapping(binding.argument_ref_bindings),
        constant_arguments=_json_object_from_mapping(binding.constant_arguments),
        result_semantic_key_template=binding.result_semantic_key_template,
        metadata=_json_object_from_mapping(binding.metadata),
    )


def _json_object_from_mapping(
    value: Mapping[str, object] | None,
) -> JsonObject | None:
    if value is None:
        return None
    return JsonObject(
        cast(
            dict[str, JsonValue],
            {str(key): _jsonable_code_metadata(item) for key, item in value.items()},
        )
    )


def _json_object_items(
    existing: Mapping[str, object] | None,
    updates: Mapping[str, object],
) -> dict[str, JsonValue]:
    payload: dict[str, object] = {}
    if existing is not None:
        payload.update(existing)
    payload.update(updates)
    return cast(
        dict[str, JsonValue],
        {str(key): _jsonable_code_metadata(item) for key, item in payload.items()},
    )


def _code_segment_render_policy_dto(
    *,
    policy: RuntimeCodeSegmentRenderPolicy,
) -> CodeSegmentRenderPolicy:
    return CodeSegmentRenderPolicy(
        policy_key=policy.policy_key,
        language=policy.language,
        section_type=policy.section_type,
        segment_name=policy.segment_name,
        content_text_domain=CodeSegmentContentDomain(policy.content_text_domain),
        rendered_content_text_domain=CodeSegmentContentDomain(
            policy.rendered_content_text_domain,
        ),
        before_hash_domains=[
            CodeSegmentContentDomain(domain) for domain in policy.before_hash_domains
        ],
        after_hash_domain=CodeSegmentContentDomain(policy.after_hash_domain),
        parser_segment_scope=policy.parser_segment_scope,
        renderer_key=policy.renderer_key,
        metadata=JsonObject(
            cast(
                dict[str, JsonValue],
                {
                    str(key): _jsonable_code_metadata(value)
                    for key, value in jsonable_policy_metadata(policy).items()
                },
            )
        ),
    )


def _json_object_from_value(value: object) -> JsonObject | None:
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        model_dump = getattr(value, "model_dump")
        if callable(model_dump):
            value = model_dump(mode="json", exclude_none=True)
    if isinstance(value, Mapping):
        return _json_object_from_mapping(value)
    return JsonObject({"value": str(value)})


def _validate_package_layout(layout: CodePackageLayoutContract) -> list[str]:
    diagnostics: list[str] = []
    if not layout.package_root.strip():
        diagnostics.append("package_root is required.")
    surface = (layout.surface or "").strip()
    if (
        surface
        and normalize_code_package_surface(surface) == surface
        and surface not in _CODE_PACKAGE_SURFACE_VALUES
    ):
        diagnostics.append(
            f"surface is not a supported CodePackageSurface: {layout.surface!r}."
        )
    for index, path_role in enumerate(layout.path_roles):
        if not path_role.include_patterns:
            diagnostics.append(
                f"path_roles[{index}] must include at least one pattern."
            )
    return diagnostics


def _normalize_section_delta_set(delta_set: CodeSectionDeltaSet) -> CodeSectionDeltaSet:
    normalized_entries = sorted(
        (
            CodeSectionDeltaEntry.model_validate(entry.model_dump(mode="json"))
            for entry in delta_set.entries
        ),
        key=_section_delta_entry_sort_key,
    )
    return CodeSectionDeltaSet(
        package_name=delta_set.package_name,
        package_root=_optional_path_text(delta_set.package_root),
        sources_root=_optional_path_text(delta_set.sources_root),
        baseline_fingerprint=delta_set.baseline_fingerprint,
        baseline_fingerprint_algorithm=delta_set.baseline_fingerprint_algorithm
        or "sha256",
        production=delta_set.production,
        entries=normalized_entries,
        warnings=sorted(delta_set.warnings),
        metadata=delta_set.metadata,
    )


def _section_delta_entry_sort_key(entry: CodeSectionDeltaEntry) -> tuple[str, ...]:
    section = entry.section_ref
    segment = entry.segment_ref
    return (
        _enum_text(entry.operation),
        section.package_name or "",
        section.relative_path,
        section.section_type,
        section.qualname or "",
        section.identity_hash or "",
        segment.segment_name if segment is not None else "",
        entry.semantic_key or "",
        entry.event_ref or "",
    )


def _hydrate_section_delta_set_resolver_inputs(
    delta_set: CodeSectionDeltaSet,
    *,
    registry: CodeSectionSegmentCapabilityRegistry,
) -> tuple[CodeSectionDeltaSet, list[str]]:
    package_root_text = _optional_path_text(delta_set.package_root)
    if package_root_text is None:
        return delta_set, []
    base_path = _section_delta_base_path(
        package_root=package_root_text,
        sources_root=delta_set.sources_root,
    )
    entries: list[CodeSectionDeltaEntry] = []
    diagnostics: list[str] = []
    file_text_by_path: dict[str, str] = {}
    for index, entry in enumerate(delta_set.entries):
        hydrated_entry, entry_diagnostics = (
            _hydrate_section_delta_entry_resolver_inputs(
                entry,
                index=index,
                base_path=base_path,
                file_text_by_path=file_text_by_path,
                registry=registry,
            )
        )
        entries.append(hydrated_entry)
        diagnostics.extend(entry_diagnostics)
    if not diagnostics and entries == list(delta_set.entries):
        return delta_set, []
    return (
        CodeSectionDeltaSet(
            package_name=delta_set.package_name,
            package_root=delta_set.package_root,
            sources_root=delta_set.sources_root,
            baseline_fingerprint=delta_set.baseline_fingerprint,
            baseline_fingerprint_algorithm=delta_set.baseline_fingerprint_algorithm,
            production=delta_set.production,
            entries=entries,
            warnings=delta_set.warnings,
            metadata=delta_set.metadata,
        ),
        diagnostics,
    )


def _hydrate_section_delta_entry_resolver_inputs(
    entry: CodeSectionDeltaEntry,
    *,
    index: int,
    base_path: Path,
    file_text_by_path: dict[str, str],
    registry: CodeSectionSegmentCapabilityRegistry,
) -> tuple[CodeSectionDeltaEntry, list[str]]:
    segment_ref = entry.segment_ref
    if segment_ref is None or (
        segment_ref.byte_start is not None and segment_ref.byte_end is not None
    ):
        return entry, []
    prefix = f"entries[{index}]"
    section_ref = entry.section_ref
    capability = registry.capability_for_section_type(section_ref.section_type)
    if capability is not None and not capability.is_builtin:
        return entry, []
    language_text = _optional_text(section_ref.language)
    if language_text is None:
        return entry, []
    try:
        language = CodeLanguage(language_text)
        section_type = CodeSectionType(section_ref.section_type)
    except ValueError as exc:
        return entry, [f"{prefix}.section_ref parser validation failed: {exc}"]

    relative_path = _safe_relative_path(
        section_ref.relative_path,
        context=f"{prefix}.section_ref.relative_path",
    )
    if relative_path is None:
        return entry, [f"{prefix}.section_ref.relative_path is invalid."]
    if relative_path not in file_text_by_path:
        resolved_path = _resolve_safe_child(base=base_path, relative_path=relative_path)
        if resolved_path is None:
            return entry, [f"{prefix}.section_ref.relative_path escapes package root."]
        if not resolved_path.is_file():
            return entry, [
                f"{prefix}.section_ref.relative_path does not exist: {relative_path}"
            ]
        file_text_by_path[relative_path] = resolved_path.read_text(encoding="utf-8")

    try:
        setup_code_plugins()
        code = build_code_from_content(
            sections_index=CodeSectionBuilderIndex(),
            content=file_text_by_path[relative_path],
            code_key=relative_path,
            language=language,
            symbol_table=CodeSymbolTable(),
        )
    except Exception as exc:
        return entry, [f"{prefix}.section_ref parser validation failed: {exc}"]

    candidates = [
        section
        for section in code.code_sections
        if section.type == section_type
        and (
            not section_ref.identity_hash
            or section.identity_hash == section_ref.identity_hash
        )
        and (not section_ref.qualname or section.qualname == section_ref.qualname)
    ]
    if not candidates:
        return entry, [f"{prefix}.section_ref did not match parsed section truth."]
    if len(candidates) > 1:
        return entry, [f"{prefix}.section_ref matched multiple parsed sections."]

    segment = CodeSegmentScanner.get_segment_from_section(
        candidates[0],
        segment_ref.segment_name,
    )
    if segment is None:
        return entry, [
            (
                f"{prefix}.segment_ref.segment_name "
                f"{segment_ref.segment_name!r} did not match parsed segment truth."
            )
        ]
    if segment.byte_start is None or segment.byte_end is None:
        return entry, [f"{prefix}.segment_ref byte_start and byte_end are unavailable."]

    current_bytes = file_text_by_path[relative_path].encode("utf-8")
    segment_text = current_bytes[segment.byte_start : segment.byte_end].decode("utf-8")
    segment_payload = segment_ref.model_dump(mode="json")
    segment_payload["byte_start"] = segment.byte_start
    segment_payload["byte_end"] = segment.byte_end
    segment_payload["before_segment_hash"] = (
        segment_ref.before_segment_hash or _sha256_digest(segment_text)
    )
    rendered_entry = _section_delta_entry_with_segment_render_policy(
        entry=entry,
        language=language,
        section_type=section_type,
        segment_text=segment_text,
        segment_payload=segment_payload,
    )
    if rendered_entry is not None:
        return rendered_entry, []
    entry_payload = entry.model_dump(mode="json")
    entry_payload["segment_ref"] = CodeSegmentRef.model_validate(
        segment_payload
    ).model_dump(mode="json")
    return CodeSectionDeltaEntry.model_validate(entry_payload), []


def _section_delta_entry_with_segment_render_policy(
    *,
    entry: CodeSectionDeltaEntry,
    language: CodeLanguage,
    section_type: CodeSectionType,
    segment_text: str,
    segment_payload: dict[str, object],
) -> CodeSectionDeltaEntry | None:
    segment_ref = entry.segment_ref
    content_text = entry.content_text
    if segment_ref is None or content_text is None:
        return None
    policy = resolve_code_segment_render_policy(
        language=language.value,
        section_type=section_type.value,
        segment_name=segment_ref.segment_name,
    )
    if policy is None or policy.raw_segment_is_policy_owned(content_text):
        return None

    requested_semantic_text = policy.semantic_text_from_content_text(content_text)
    requested_semantic_hash = _segment_render_sha256_digest(requested_semantic_text)
    if not _segment_render_digest_matches(entry.after_hash, requested_semantic_hash):
        return None

    current_semantic_text = policy.semantic_text_from_raw_segment(segment_text)
    current_semantic_hash = _segment_render_sha256_digest(current_semantic_text)
    current_raw_hash = _sha256_digest(segment_text)
    before_segment_hash = segment_ref.before_segment_hash
    semantic_already_applied = current_semantic_text == requested_semantic_text
    if semantic_already_applied:
        raw_replacement_text = segment_text
        next_before_segment_hash = before_segment_hash or current_raw_hash
    elif _segment_render_digest_matches(
        before_segment_hash,
        current_semantic_hash,
    ) or _sha256_matches(before_segment_hash, current_raw_hash):
        raw_replacement_text = policy.render_raw_segment(
            semantic_text=requested_semantic_text,
            current_raw_segment=segment_text,
        )
        next_before_segment_hash = current_raw_hash
    else:
        return None

    rendered_segment_payload = dict(segment_payload)
    rendered_segment_payload["before_segment_hash"] = next_before_segment_hash
    rendered_segment_payload["metadata"] = JsonObject(
        _json_object_items(
            segment_ref.metadata,
            {
                "segment_render_policy_key": policy.policy_key,
                "segment_render_policy_language": policy.language,
                "segment_render_policy_section_type": policy.section_type,
                "segment_render_policy_segment_name": policy.segment_name,
            },
        )
    )
    entry_payload = entry.model_dump(mode="json")
    entry_payload["segment_ref"] = CodeSegmentRef.model_validate(
        rendered_segment_payload
    ).model_dump(mode="json")
    entry_payload["content_text"] = raw_replacement_text
    entry_payload["after_hash"] = _sha256_digest(raw_replacement_text)
    entry_payload["metadata"] = JsonObject(
        _json_object_items(
            entry.metadata,
            {
                "segment_render_policy_key": policy.policy_key,
                "content_text_domain": policy.content_text_domain,
                "rendered_content_text_domain": "raw_segment_text",
                "semantic_content_text": requested_semantic_text,
                "semantic_after_hash": requested_semantic_hash,
                "current_semantic_text_hash": current_semantic_hash,
                "semantic_already_applied": semantic_already_applied,
            },
        )
    )
    return CodeSectionDeltaEntry.model_validate(entry_payload)


def _validate_section_delta_set(
    delta_set: CodeSectionDeltaSet,
    *,
    strict: bool,
    require_resolver_inputs: bool,
    registry: CodeSectionSegmentCapabilityRegistry,
) -> list[str]:
    diagnostics: list[str] = []
    if strict and not delta_set.entries:
        diagnostics.append("entries must include at least one section delta.")
    if delta_set.baseline_fingerprint_algorithm != "sha256":
        diagnostics.append(
            "baseline_fingerprint_algorithm must be sha256 when provided."
        )
    if require_resolver_inputs and _optional_path_text(delta_set.package_root) is None:
        diagnostics.append("package_root is required for section-delta resolution.")

    for index, entry in enumerate(delta_set.entries):
        diagnostics.extend(
            _validate_section_delta_entry(
                entry,
                index=index,
                require_resolver_inputs=require_resolver_inputs,
                registry=registry,
            )
        )
    return diagnostics


def _normalize_source_projection_request(
    projection: CodeSourceProjectionRequest,
) -> CodeSourceProjectionRequest:
    return CodeSourceProjectionRequest(
        provider_key=projection.provider_key.strip(),
        semantic_owner=_optional_text(projection.semantic_owner),
        package_name=_optional_text(projection.package_name),
        package_root=_optional_path_text(projection.package_root),
        sources_root=_optional_path_text(projection.sources_root),
        product_intent=_optional_text(projection.product_intent),
        target_language=_optional_text(projection.target_language),
        baseline_fingerprint=projection.baseline_fingerprint,
        baseline_fingerprint_algorithm=(
            projection.baseline_fingerprint_algorithm or "sha256"
        ),
        layout_contract=projection.layout_contract,
        semantic_contract=projection.semantic_contract,
        events=sorted(
            (
                CodeSourceProjectionEventRef.model_validate(
                    event.model_dump(mode="json")
                )
                for event in projection.events
            ),
            key=_source_projection_event_sort_key,
        ),
        action_bindings=sorted(
            (
                CodeSourceProjectionActionBinding.model_validate(
                    binding.model_dump(mode="json")
                )
                for binding in projection.action_bindings
            ),
            key=_source_projection_action_sort_key,
        ),
        source_refs=sorted(projection.source_refs),
        metadata=projection.metadata,
    )


def _normalize_source_projection_result(
    result: CodeSourceProjectionResult,
) -> CodeSourceProjectionResult:
    return CodeSourceProjectionResult(
        provider_key=result.provider_key.strip(),
        semantic_owner=_optional_text(result.semantic_owner),
        projected=result.projected,
        delta_set=(
            _normalize_section_delta_set(result.delta_set)
            if result.delta_set is not None
            else None
        ),
        diagnostics=sorted(result.diagnostics),
        skipped_events=sorted(
            (
                CodeSourceProjectionSkippedEvent.model_validate(
                    skipped.model_dump(mode="json")
                )
                for skipped in result.skipped_events
            ),
            key=_source_projection_skipped_sort_key,
        ),
        fingerprint=result.fingerprint,
        receipt_refs=sorted(result.receipt_refs),
        metadata=result.metadata,
    )


def _source_projection_resolution_delta_set(
    *,
    projection: CodeSourceProjectionRequest,
    result: CodeSourceProjectionResult,
) -> CodeSectionDeltaSet | None:
    if result.delta_set is None:
        return None

    delta_set = _normalize_section_delta_set(result.delta_set)
    return CodeSectionDeltaSet(
        package_name=delta_set.package_name or projection.package_name,
        package_root=delta_set.package_root or projection.package_root,
        sources_root=delta_set.sources_root or projection.sources_root,
        baseline_fingerprint=(
            delta_set.baseline_fingerprint or projection.baseline_fingerprint
        ),
        baseline_fingerprint_algorithm=(
            delta_set.baseline_fingerprint_algorithm
            or projection.baseline_fingerprint_algorithm
            or "sha256"
        ),
        production=delta_set.production,
        entries=delta_set.entries,
        warnings=delta_set.warnings,
        metadata=delta_set.metadata,
    )


def _source_projection_grammar_anchor_render_delta_request(
    *,
    projection: CodeSourceProjectionRequest,
    result: CodeSourceProjectionResult,
) -> tuple[ResolveCodeGrammarAnchorRenderDeltaRequest | None, list[str]]:
    payload = _source_projection_grammar_anchor_render_delta_payload(
        projection=projection,
        result=result,
    )
    if payload is None:
        return None, []
    try:
        return ResolveCodeGrammarAnchorRenderDeltaRequest.model_validate(payload), []
    except Exception as exc:
        return None, [
            "result.metadata.grammar_anchor_render_delta_request is invalid: " f"{exc}"
        ]


def _source_projection_grammar_anchor_render_delta_payload(
    *,
    projection: CodeSourceProjectionRequest,
    result: CodeSourceProjectionResult,
) -> Mapping[str, object] | None:
    for metadata in (result.metadata, projection.metadata):
        if not isinstance(metadata, Mapping):
            continue
        value = metadata.get("grammar_anchor_render_delta_request")
        if isinstance(value, Mapping):
            return value
    return None


def _source_projection_package_delta_with_metadata(
    package_delta: CodePackageDelta | None,
    *,
    metadata: Mapping[str, object],
) -> CodePackageDelta | None:
    if package_delta is None:
        return None
    merged_metadata = _json_object_items(package_delta.metadata, metadata)
    return package_delta.model_copy(
        update={
            "metadata": JsonObject(merged_metadata),
        }
    )


def _validate_source_projection(
    *,
    projection: CodeSourceProjectionRequest,
    result: CodeSourceProjectionResult | None,
    strict: bool,
    registry: CodeSectionSegmentCapabilityRegistry,
) -> list[str]:
    diagnostics: list[str] = []
    if not projection.provider_key:
        diagnostics.append("projection.provider_key is required.")
    if projection.baseline_fingerprint_algorithm != "sha256":
        diagnostics.append(
            "projection.baseline_fingerprint_algorithm must be sha256 when provided."
        )
    if strict and not projection.events:
        diagnostics.append("projection.events must include at least one event.")
    if strict and not projection.action_bindings:
        diagnostics.append(
            "projection.action_bindings must include at least one source_projection action."
        )

    event_keys = {event.event_key for event in projection.events}
    for index, event in enumerate(projection.events):
        if not event.event_key.strip():
            diagnostics.append(f"projection.events[{index}].event_key is required.")
    for index, action in enumerate(projection.action_bindings):
        if not action.action_key.strip():
            diagnostics.append(
                f"projection.action_bindings[{index}].action_key is required."
            )
        if action.action_type != "source_projection":
            diagnostics.append(
                f"projection.action_bindings[{index}].action_type must be "
                "source_projection."
            )
        if action.event_key not in event_keys:
            diagnostics.append(
                f"projection.action_bindings[{index}].event_key does not match "
                "projection.events."
            )

    if result is not None:
        diagnostics.extend(
            _validate_source_projection_result(
                projection=projection,
                result=result,
                registry=registry,
            )
        )
    return diagnostics


def _validate_source_projection_result(
    *,
    projection: CodeSourceProjectionRequest,
    result: CodeSourceProjectionResult,
    registry: CodeSectionSegmentCapabilityRegistry,
) -> list[str]:
    diagnostics: list[str] = []
    if not result.provider_key:
        diagnostics.append("result.provider_key is required.")
    if result.provider_key and result.provider_key != projection.provider_key:
        diagnostics.append("result.provider_key must match projection.provider_key.")
    has_grammar_anchor_request = (
        _source_projection_grammar_anchor_render_delta_payload(
            projection=projection,
            result=result,
        )
        is not None
    )
    if result.projected and result.delta_set is None and not has_grammar_anchor_request:
        diagnostics.append(
            "result.delta_set is required when result.projected is true."
        )
    if has_grammar_anchor_request:
        diagnostics.extend(
            _source_projection_grammar_anchor_render_delta_request(
                projection=projection,
                result=result,
            )[1]
        )
    if result.delta_set is not None:
        diagnostics.extend(
            f"result.delta_set.{diagnostic}"
            for diagnostic in _validate_section_delta_set(
                result.delta_set,
                strict=result.projected,
                require_resolver_inputs=False,
                registry=registry,
            )
        )
    return diagnostics


def _source_projection_event_sort_key(
    event: CodeSourceProjectionEventRef,
) -> tuple[str, ...]:
    return (
        event.event_key,
        event.semantic_key or "",
        event.verb or "",
        event.subject_type or "",
        event.source or "",
    )


def _source_projection_action_sort_key(
    action: CodeSourceProjectionActionBinding,
) -> tuple[str, ...]:
    return (
        action.event_key,
        action.action_key,
        action.action_type,
        action.policy_key or "",
    )


def _source_projection_skipped_sort_key(
    skipped: CodeSourceProjectionSkippedEvent,
) -> tuple[str, ...]:
    return (
        skipped.event_key or "",
        skipped.action_key or "",
        skipped.semantic_key or "",
        skipped.reason,
    )


def _normalize_generated_materialization_delta_request(
    delta_request: CodeGeneratedMaterializationDeltaRequest,
) -> CodeGeneratedMaterializationDeltaRequest:
    return CodeGeneratedMaterializationDeltaRequest(
        provider_key=delta_request.provider_key.strip(),
        semantic_owner=_optional_text(delta_request.semantic_owner),
        package_name=_optional_text(delta_request.package_name),
        package_root=_optional_path_text(delta_request.package_root),
        sources_root=_optional_path_text(delta_request.sources_root),
        product_intent=_optional_text(delta_request.product_intent),
        baseline_fingerprint=delta_request.baseline_fingerprint,
        baseline_fingerprint_algorithm=(
            delta_request.baseline_fingerprint_algorithm or "sha256"
        ),
        layout_contract=delta_request.layout_contract,
        semantic_contract=delta_request.semantic_contract,
        events=sorted(
            (
                CodeGeneratedMaterializationEventRef(
                    event_key=event.event_key.strip(),
                    semantic_key=_optional_text(event.semantic_key),
                    verb=_optional_text(event.verb),
                    subject_type=_optional_text(event.subject_type),
                    source=_optional_text(event.source),
                    source_refs=sorted(
                        ref
                        for ref in (
                            _optional_path_text(ref) for ref in event.source_refs
                        )
                        if ref is not None
                    ),
                    payload=event.payload,
                    metadata=event.metadata,
                )
                for event in delta_request.events
            ),
            key=_generated_materialization_event_sort_key,
        ),
        action_bindings=sorted(
            (
                CodeGeneratedMaterializationActionBinding(
                    action_key=binding.action_key.strip(),
                    event_key=binding.event_key.strip(),
                    action_type=binding.action_type.strip(),
                    target=(
                        _normalize_generated_materialization_target(binding.target)
                        if binding.target is not None
                        else None
                    ),
                    policy_key=_optional_text(binding.policy_key),
                    renderer_key=_optional_text(binding.renderer_key),
                    metadata=binding.metadata,
                )
                for binding in delta_request.action_bindings
            ),
            key=_generated_materialization_action_sort_key,
        ),
        targets=sorted(
            (
                _normalize_generated_materialization_target(target)
                for target in delta_request.targets
            ),
            key=_generated_materialization_target_sort_key,
        ),
        metadata=delta_request.metadata,
    )


def _normalize_generated_materialization_delta_result(
    result: CodeGeneratedMaterializationDeltaResult,
) -> CodeGeneratedMaterializationDeltaResult:
    return CodeGeneratedMaterializationDeltaResult(
        provider_key=result.provider_key.strip(),
        semantic_owner=_optional_text(result.semantic_owner),
        available=result.available,
        mode=result.mode,
        entries=sorted(
            (
                _normalize_generated_materialization_delta_entry(entry)
                for entry in result.entries
            ),
            key=_generated_materialization_entry_sort_key,
        ),
        skipped_targets=sorted(
            (
                CodeGeneratedMaterializationSkippedTarget(
                    target=(
                        _normalize_generated_materialization_target(skipped.target)
                        if skipped.target is not None
                        else None
                    ),
                    reason=skipped.reason.strip(),
                    event_refs=sorted(skipped.event_refs),
                    metadata=skipped.metadata,
                )
                for skipped in result.skipped_targets
            ),
            key=_generated_materialization_skipped_sort_key,
        ),
        diagnostics=sorted(result.diagnostics),
        fingerprint=result.fingerprint,
        receipt_refs=sorted(result.receipt_refs),
        metadata=result.metadata,
    )


def _normalize_generated_materialization_target(
    target: CodeGeneratedMaterializationTargetRef,
) -> CodeGeneratedMaterializationTargetRef:
    return CodeGeneratedMaterializationTargetRef(
        target_key=_optional_text(target.target_key),
        target_index=target.target_index,
        provider_key=_optional_text(target.provider_key),
        semantic_owner=_optional_text(target.semantic_owner),
        target_language=_optional_text(target.target_language),
        package_name=_optional_text(target.package_name),
        package_root=_optional_path_text(target.package_root),
        sources_root=_optional_path_text(target.sources_root),
        renderer_key=_optional_text(target.renderer_key),
        renderer_kind=_optional_text(target.renderer_kind),
        renderer_profile=_optional_text(target.renderer_profile),
        materialization_source=_optional_text(target.materialization_source),
        artifact_family=_optional_text(target.artifact_family),
        artifact_role=_optional_text(target.artifact_role),
        output_key=_optional_text(target.output_key),
        relative_path=_optional_path_text(target.relative_path),
        metadata=target.metadata,
    )


def _normalize_generated_materialization_delta_entry(
    entry: CodeGeneratedMaterializationDeltaEntry,
) -> CodeGeneratedMaterializationDeltaEntry:
    return CodeGeneratedMaterializationDeltaEntry(
        entry_key=_optional_text(entry.entry_key),
        mode=entry.mode,
        target=_normalize_generated_materialization_target(entry.target),
        package_delta=(
            _normalize_package_delta(entry.package_delta)
            if entry.package_delta is not None
            else None
        ),
        grammar_anchor_render_delta=entry.grammar_anchor_render_delta,
        section_delta=(
            _normalize_section_delta_set(entry.section_delta)
            if entry.section_delta is not None
            else None
        ),
        artifact_family=_optional_text(entry.artifact_family),
        artifact_role=_optional_text(entry.artifact_role),
        artifact_key=_optional_text(entry.artifact_key),
        relative_path=_optional_path_text(entry.relative_path),
        before_hash=entry.before_hash,
        after_hash=entry.after_hash,
        renderer_operations=sorted(
            (
                _normalize_generated_renderer_delta_operation(operation)
                for operation in entry.renderer_operations
            ),
            key=_generated_renderer_delta_operation_sort_key,
        ),
        event_refs=sorted(entry.event_refs),
        semantic_keys=sorted(entry.semantic_keys),
        diagnostics=sorted(entry.diagnostics),
        metadata=entry.metadata,
    )


def _normalize_generated_renderer_delta_operation(
    operation: CodeGeneratedRendererDeltaOperation,
) -> CodeGeneratedRendererDeltaOperation:
    return CodeGeneratedRendererDeltaOperation(
        operation_key=_optional_text(operation.operation_key),
        kind=operation.kind,
        target=(
            _normalize_generated_materialization_target(operation.target)
            if operation.target is not None
            else None
        ),
        anchor=(
            _normalize_generated_renderer_anchor(operation.anchor)
            if operation.anchor is not None
            else None
        ),
        renderer_key=_optional_text(operation.renderer_key),
        renderer_profile=_optional_text(operation.renderer_profile),
        before_hash=operation.before_hash,
        after_hash=operation.after_hash,
        content_text=operation.content_text,
        replacement_text=operation.replacement_text,
        event_refs=sorted(operation.event_refs),
        semantic_keys=sorted(operation.semantic_keys),
        diagnostics=sorted(operation.diagnostics),
        metadata=operation.metadata,
    )


def _normalize_generated_renderer_anchor(
    anchor: CodeGeneratedRendererAnchorRef,
) -> CodeGeneratedRendererAnchorRef:
    return CodeGeneratedRendererAnchorRef(
        anchor_key=anchor.anchor_key.strip(),
        anchor_path=_optional_text(anchor.anchor_path),
        anchor_role=_optional_text(anchor.anchor_role),
        renderer_key=_optional_text(anchor.renderer_key),
        renderer_profile=_optional_text(anchor.renderer_profile),
        materialization_source=_optional_text(anchor.materialization_source),
        target_language=_optional_text(anchor.target_language),
        section_type=_optional_text(anchor.section_type),
        segment_name=_optional_text(anchor.segment_name),
        graph_selector=anchor.graph_selector,
        metadata=anchor.metadata,
    )


def _validate_generated_materialization_delta(
    *,
    delta_request: CodeGeneratedMaterializationDeltaRequest,
    result: CodeGeneratedMaterializationDeltaResult | None,
    strict: bool,
    registry: CodeSectionSegmentCapabilityRegistry,
) -> list[str]:
    diagnostics: list[str] = []
    if not delta_request.provider_key:
        diagnostics.append("delta_request.provider_key is required.")
    if delta_request.baseline_fingerprint_algorithm != "sha256":
        diagnostics.append(
            "delta_request.baseline_fingerprint_algorithm must be sha256 "
            "when provided."
        )
    if strict and not delta_request.events:
        diagnostics.append("delta_request.events must include at least one event.")
    if strict and not delta_request.targets:
        diagnostics.append(
            "delta_request.targets must include at least one generated target."
        )

    event_keys = {event.event_key for event in delta_request.events}
    for index, event in enumerate(delta_request.events):
        if not event.event_key:
            diagnostics.append(f"delta_request.events[{index}].event_key is required.")
    for index, binding in enumerate(delta_request.action_bindings):
        if not binding.action_key:
            diagnostics.append(
                f"delta_request.action_bindings[{index}].action_key is required."
            )
        if binding.action_type != "generated_materialization_delta":
            diagnostics.append(
                f"delta_request.action_bindings[{index}].action_type must be "
                "generated_materialization_delta."
            )
        if binding.event_key not in event_keys:
            diagnostics.append(
                f"delta_request.action_bindings[{index}].event_key does not "
                "match delta_request.events."
            )
        if binding.target is not None:
            diagnostics.extend(
                _validate_generated_materialization_target(
                    binding.target,
                    prefix=f"delta_request.action_bindings[{index}].target",
                )
            )
    for index, target in enumerate(delta_request.targets):
        diagnostics.extend(
            _validate_generated_materialization_target(
                target,
                prefix=f"delta_request.targets[{index}]",
            )
        )

    if result is not None:
        diagnostics.extend(
            _validate_generated_materialization_delta_result(
                delta_request=delta_request,
                result=result,
                event_keys=event_keys,
                strict=strict,
                registry=registry,
            )
        )
    return diagnostics


def _validate_generated_materialization_delta_result(
    *,
    delta_request: CodeGeneratedMaterializationDeltaRequest,
    result: CodeGeneratedMaterializationDeltaResult,
    event_keys: set[str],
    strict: bool,
    registry: CodeSectionSegmentCapabilityRegistry,
) -> list[str]:
    diagnostics: list[str] = []
    if not result.provider_key:
        diagnostics.append("result.provider_key is required.")
    if result.provider_key and result.provider_key != delta_request.provider_key:
        diagnostics.append("result.provider_key must match delta_request.provider_key.")
    if result.available and not result.entries and not result.skipped_targets:
        diagnostics.append(
            "result.entries or result.skipped_targets are required when "
            "result.available is true."
        )

    for index, entry in enumerate(result.entries):
        diagnostics.extend(
            _validate_generated_materialization_delta_entry(
                entry,
                index=index,
                event_keys=event_keys,
                strict=strict,
                registry=registry,
            )
        )
    for index, skipped in enumerate(result.skipped_targets):
        if not skipped.reason:
            diagnostics.append(f"result.skipped_targets[{index}].reason is required.")
        for event_ref in skipped.event_refs:
            if event_ref not in event_keys:
                diagnostics.append(
                    f"result.skipped_targets[{index}].event_refs contains unknown "
                    f"event key: {event_ref}"
                )
        if skipped.target is not None:
            diagnostics.extend(
                _validate_generated_materialization_target(
                    skipped.target,
                    prefix=f"result.skipped_targets[{index}].target",
                )
            )
    return diagnostics


def _validate_generated_materialization_delta_entry(
    entry: CodeGeneratedMaterializationDeltaEntry,
    *,
    index: int,
    event_keys: set[str],
    strict: bool,
    registry: CodeSectionSegmentCapabilityRegistry,
) -> list[str]:
    diagnostics: list[str] = []
    prefix = f"result.entries[{index}]"
    diagnostics.extend(
        _validate_generated_materialization_target(
            entry.target,
            prefix=f"{prefix}.target",
        )
    )
    for event_ref in entry.event_refs:
        if event_ref not in event_keys:
            diagnostics.append(
                f"{prefix}.event_refs contains unknown event key: {event_ref}"
            )
    if (
        entry.mode is CodeGeneratedMaterializationDeltaMode.package_delta_ready
        and entry.package_delta is None
    ):
        diagnostics.append(
            f"{prefix}.package_delta is required when mode is package_delta_ready."
        )
    if (
        entry.mode is CodeGeneratedMaterializationDeltaMode.section_delta_ready
        and entry.section_delta is None
    ):
        diagnostics.append(
            f"{prefix}.section_delta is required when mode is section_delta_ready."
        )
    if (
        entry.mode is CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
        and entry.grammar_anchor_render_delta is None
    ):
        diagnostics.append(
            f"{prefix}.grammar_anchor_render_delta is required when mode is "
            "grammar_anchor_render_ready."
        )
    if entry.package_delta is not None and not entry.package_delta.paths:
        diagnostics.append(f"{prefix}.package_delta.paths must not be empty.")
    if entry.section_delta is not None:
        diagnostics.extend(
            f"{prefix}.section_delta.{diagnostic}"
            for diagnostic in _validate_section_delta_set(
                entry.section_delta,
                strict=(
                    strict
                    and entry.mode
                    is CodeGeneratedMaterializationDeltaMode.section_delta_ready
                ),
                require_resolver_inputs=False,
                registry=registry,
            )
        )
    for operation_index, operation in enumerate(entry.renderer_operations):
        diagnostics.extend(
            _validate_generated_renderer_delta_operation(
                operation,
                prefix=f"{prefix}.renderer_operations[{operation_index}]",
                event_keys=event_keys,
            )
        )
    return diagnostics


def _validate_generated_renderer_delta_operation(
    operation: CodeGeneratedRendererDeltaOperation,
    *,
    prefix: str,
    event_keys: set[str],
) -> list[str]:
    diagnostics: list[str] = []
    if operation.target is not None:
        diagnostics.extend(
            _validate_generated_materialization_target(
                operation.target,
                prefix=f"{prefix}.target",
            )
        )
    for event_ref in operation.event_refs:
        if event_ref not in event_keys:
            diagnostics.append(
                f"{prefix}.event_refs contains unknown event key: {event_ref}"
            )
    if (
        operation.kind
        is not CodeGeneratedRendererDeltaOperationKind.fallback_full_render
        and operation.anchor is None
    ):
        diagnostics.append(f"{prefix}.anchor is required for renderer operations.")
    if operation.anchor is not None and not operation.anchor.anchor_key.strip():
        diagnostics.append(f"{prefix}.anchor.anchor_key is required.")
    if (
        operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
        and operation.content_text is None
        and operation.replacement_text is None
    ):
        diagnostics.append(
            f"{prefix}.content_text or replacement_text is required "
            "for replace_anchor."
        )
    return diagnostics


def _validate_generated_materialization_target(
    target: CodeGeneratedMaterializationTargetRef,
    *,
    prefix: str,
) -> list[str]:
    if any(
        (
            target.target_key,
            target.renderer_key,
            target.output_key,
            target.artifact_family,
            target.relative_path,
        )
    ):
        return []
    return [
        (
            f"{prefix} must include target_key, renderer_key, output_key, "
            "artifact_family, or relative_path."
        )
    ]


def _generated_materialization_event_sort_key(
    event: CodeGeneratedMaterializationEventRef,
) -> tuple[str, ...]:
    return (
        event.event_key,
        event.semantic_key or "",
        event.verb or "",
        event.subject_type or "",
        event.source or "",
    )


def _generated_materialization_action_sort_key(
    action: CodeGeneratedMaterializationActionBinding,
) -> tuple[str, ...]:
    target = action.target
    return (
        action.event_key,
        action.action_key,
        action.action_type,
        action.policy_key or "",
        action.renderer_key or "",
        target.target_key if target is not None and target.target_key else "",
        target.relative_path if target is not None and target.relative_path else "",
    )


def _generated_materialization_target_sort_key(
    target: CodeGeneratedMaterializationTargetRef,
) -> tuple[str, ...]:
    return (
        target.package_name or "",
        target.target_key or "",
        f"{target.target_index:012d}" if target.target_index is not None else "",
        target.renderer_key or "",
        target.artifact_family or "",
        target.artifact_role or "",
        target.output_key or "",
        target.relative_path or "",
    )


def _generated_materialization_entry_sort_key(
    entry: CodeGeneratedMaterializationDeltaEntry,
) -> tuple[str, ...]:
    target = entry.target
    return (
        entry.entry_key or "",
        _enum_text(entry.mode),
        target.package_name or "",
        target.target_key or "",
        target.renderer_key or "",
        entry.artifact_family or "",
        entry.artifact_role or "",
        entry.artifact_key or "",
        entry.relative_path or "",
    )


def _generated_materialization_skipped_sort_key(
    skipped: CodeGeneratedMaterializationSkippedTarget,
) -> tuple[str, ...]:
    target = skipped.target
    return (
        skipped.reason,
        target.target_key if target is not None and target.target_key else "",
        target.relative_path if target is not None and target.relative_path else "",
    )


def _generated_materialization_package_delta_count(
    result: CodeGeneratedMaterializationDeltaResult | None,
) -> int:
    if result is None:
        return 0
    return sum(1 for entry in result.entries if entry.package_delta is not None)


def _generated_materialization_grammar_anchor_render_count(
    result: CodeGeneratedMaterializationDeltaResult | None,
) -> int:
    if result is None:
        return 0
    return sum(
        1 for entry in result.entries if entry.grammar_anchor_render_delta is not None
    )


def _generated_materialization_section_delta_count(
    result: CodeGeneratedMaterializationDeltaResult | None,
) -> int:
    if result is None:
        return 0
    return sum(1 for entry in result.entries if entry.section_delta is not None)


def _generated_materialization_renderer_operation_count(
    result: CodeGeneratedMaterializationDeltaResult | None,
) -> int:
    if result is None:
        return 0
    return sum(len(entry.renderer_operations) for entry in result.entries)


def _resolve_generated_materialization_package_delta(
    *,
    delta_request: CodeGeneratedMaterializationDeltaRequest,
    result: CodeGeneratedMaterializationDeltaResult,
    strict: bool,
    registry: CodeSectionSegmentCapabilityRegistry,
) -> tuple[CodePackageDelta | None, list[str]]:
    resolved_deltas: list[CodePackageDelta] = []
    diagnostics: list[str] = []

    for index, entry in enumerate(result.entries):
        prefix = f"result.entries[{index}]"
        if entry.package_delta is not None:
            resolved_deltas.append(
                _generated_materialization_package_delta_entry(
                    delta_request=delta_request,
                    entry=entry,
                    index=index,
                )
            )
            continue

        if entry.grammar_anchor_render_delta is not None:
            grammar_delta, grammar_diagnostics = (
                _generated_materialization_grammar_anchor_render_delta_entry(
                    delta_request=delta_request,
                    entry=entry,
                    index=index,
                )
            )
            diagnostics.extend(
                f"{prefix}.grammar_anchor_render_delta.{diagnostic}"
                for diagnostic in grammar_diagnostics
            )
            if grammar_delta is not None:
                resolved_deltas.append(grammar_delta)
            continue

        if entry.section_delta is not None:
            section_delta, section_diagnostics = (
                _generated_materialization_section_delta_entry(
                    delta_request=delta_request,
                    entry=entry,
                )
            )
            diagnostics.extend(
                f"{prefix}.section_delta.{diagnostic}"
                for diagnostic in section_diagnostics
            )
            if section_delta is None:
                continue
            hydrated_delta, hydration_diagnostics = (
                _hydrate_section_delta_set_resolver_inputs(
                    section_delta,
                    registry=registry,
                )
            )
            diagnostics.extend(
                f"{prefix}.section_delta.{diagnostic}"
                for diagnostic in hydration_diagnostics
            )
            resolver_diagnostics = _validate_section_delta_set(
                hydrated_delta,
                strict=strict,
                require_resolver_inputs=True,
                registry=registry,
            )
            diagnostics.extend(
                f"{prefix}.section_delta.{diagnostic}"
                for diagnostic in resolver_diagnostics
            )
            if resolver_diagnostics:
                continue
            resolved_delta, resolve_diagnostics = _resolve_section_delta_set(
                hydrated_delta,
                strict=strict,
                registry=registry,
            )
            diagnostics.extend(
                f"{prefix}.section_delta.{diagnostic}"
                for diagnostic in resolve_diagnostics
            )
            if resolved_delta is not None:
                resolved_deltas.append(resolved_delta)
            continue

        diagnostics.append(
            _generated_materialization_unresolved_entry_diagnostic(
                entry=entry,
                prefix=prefix,
            )
        )

    if diagnostics:
        return None, diagnostics
    if not resolved_deltas:
        return None, [
            "result.entries must include package_delta, grammar_anchor_render_delta, "
            "or section_delta evidence for generated materialization package-delta "
            "resolution."
        ]
    return _merge_generated_materialization_package_deltas(
        delta_request=delta_request,
        result=result,
        deltas=resolved_deltas,
    )


def _generated_materialization_grammar_anchor_render_delta_entry(
    *,
    delta_request: CodeGeneratedMaterializationDeltaRequest,
    entry: CodeGeneratedMaterializationDeltaEntry,
    index: int,
) -> tuple[CodePackageDelta | None, list[str]]:
    if entry.grammar_anchor_render_delta is None:
        return None, ["grammar_anchor_render_delta is required."]
    grammar_request = _generated_materialization_grammar_anchor_render_request(
        delta_request=delta_request,
        entry=entry,
    )
    response = resolve_code_grammar_anchor_render_delta(request=grammar_request)
    if response.package_delta is None or not response.success or not response.resolved:
        diagnostics = list(response.diagnostics)
        if not diagnostics:
            diagnostics.append("grammar-anchor render delta did not resolve.")
        return None, diagnostics
    metadata = _json_object_items(
        response.package_delta.metadata,
        {
            "source": "code.generated_materialization_delta.resolve_package_delta",
            "resolver": "aware_code_service.generated_materialization_delta",
            "entry_index": index,
            "entry_key": entry.entry_key,
            "entry_mode": _enum_text(entry.mode),
            "generated_materialization_renderer": "grammar_anchor_render_delta",
            "render_entry_count": response.render_entry_count,
        },
    )
    return (
        response.package_delta.model_copy(
            update={
                "package_name": (
                    response.package_delta.package_name
                    or entry.target.package_name
                    or delta_request.package_name
                ),
                "package_root": (
                    response.package_delta.package_root
                    or entry.target.package_root
                    or delta_request.package_root
                ),
                "sources_root": (
                    response.package_delta.sources_root
                    or entry.target.sources_root
                    or delta_request.sources_root
                ),
                "authority": CodePackageDeltaAuthorityKind.code_package_delta,
                "authority_kind": CodePackageDeltaAuthorityKind.code_package_delta.value,
                "metadata": JsonObject(metadata),
            }
        ),
        [],
    )


def _generated_materialization_grammar_anchor_render_request(
    *,
    delta_request: CodeGeneratedMaterializationDeltaRequest,
    entry: CodeGeneratedMaterializationDeltaEntry,
) -> ResolveCodeGrammarAnchorRenderDeltaRequest:
    assert entry.grammar_anchor_render_delta is not None
    grammar_request = entry.grammar_anchor_render_delta
    return grammar_request.model_copy(
        update={
            "package_name": (
                grammar_request.package_name
                or entry.target.package_name
                or delta_request.package_name
            ),
            "package_root": (
                grammar_request.package_root
                or entry.target.package_root
                or delta_request.package_root
            ),
            "sources_root": (
                grammar_request.sources_root
                or entry.target.sources_root
                or delta_request.sources_root
            ),
            "baseline_fingerprint": (
                grammar_request.baseline_fingerprint
                or delta_request.baseline_fingerprint
            ),
            "baseline_fingerprint_algorithm": (
                grammar_request.baseline_fingerprint_algorithm
                or delta_request.baseline_fingerprint_algorithm
                or "sha256"
            ),
        }
    )


def _generated_materialization_package_delta_entry(
    *,
    delta_request: CodeGeneratedMaterializationDeltaRequest,
    entry: CodeGeneratedMaterializationDeltaEntry,
    index: int,
) -> CodePackageDelta:
    assert entry.package_delta is not None
    normalized = _normalize_package_delta(entry.package_delta)
    metadata = _json_object_items(
        normalized.metadata,
        {
            "source": "code.generated_materialization_delta.resolve_package_delta",
            "resolver": "aware_code_service.generated_materialization_delta",
            "entry_index": index,
            "entry_key": entry.entry_key,
            "entry_mode": _enum_text(entry.mode),
        },
    )
    return normalized.model_copy(
        update={
            "package_name": (
                normalized.package_name
                or entry.target.package_name
                or delta_request.package_name
            ),
            "package_root": (
                normalized.package_root
                or entry.target.package_root
                or delta_request.package_root
            ),
            "sources_root": (
                normalized.sources_root
                or entry.target.sources_root
                or delta_request.sources_root
            ),
            "authority": CodePackageDeltaAuthorityKind.code_package_delta,
            "authority_kind": CodePackageDeltaAuthorityKind.code_package_delta.value,
            "metadata": JsonObject(metadata),
        }
    )


def _generated_materialization_section_delta_entry(
    *,
    delta_request: CodeGeneratedMaterializationDeltaRequest,
    entry: CodeGeneratedMaterializationDeltaEntry,
) -> tuple[CodeSectionDeltaSet | None, list[str]]:
    if entry.section_delta is None:
        return None, ["section_delta is required."]
    delta_set = _normalize_section_delta_set(entry.section_delta)
    return (
        CodeSectionDeltaSet(
            package_name=(
                delta_set.package_name
                or entry.target.package_name
                or delta_request.package_name
            ),
            package_root=(
                delta_set.package_root
                or entry.target.package_root
                or delta_request.package_root
            ),
            sources_root=(
                delta_set.sources_root
                or entry.target.sources_root
                or delta_request.sources_root
            ),
            baseline_fingerprint=(
                delta_set.baseline_fingerprint or delta_request.baseline_fingerprint
            ),
            baseline_fingerprint_algorithm=(
                delta_set.baseline_fingerprint_algorithm
                or delta_request.baseline_fingerprint_algorithm
                or "sha256"
            ),
            production=delta_set.production,
            entries=delta_set.entries,
            warnings=delta_set.warnings,
            metadata=delta_set.metadata,
        ),
        [],
    )


def _generated_materialization_unresolved_entry_diagnostic(
    *,
    entry: CodeGeneratedMaterializationDeltaEntry,
    prefix: str,
) -> str:
    has_fallback_operation = any(
        operation.kind is CodeGeneratedRendererDeltaOperationKind.fallback_full_render
        for operation in entry.renderer_operations
    )
    if (
        entry.mode is CodeGeneratedMaterializationDeltaMode.fallback_full_render
        or has_fallback_operation
    ):
        return (
            f"{prefix} fallback_full_render cannot be resolved into a guarded "
            "CodePackageDelta without package_delta, grammar_anchor_render_delta, "
            "or section_delta evidence."
        )
    return (
        f"{prefix} must include package_delta, grammar_anchor_render_delta, or "
        "section_delta evidence for generated materialization package-delta "
        "resolution."
    )


def _merge_generated_materialization_package_deltas(
    *,
    delta_request: CodeGeneratedMaterializationDeltaRequest,
    result: CodeGeneratedMaterializationDeltaResult,
    deltas: list[CodePackageDelta],
) -> tuple[CodePackageDelta | None, list[str]]:
    diagnostics: list[str] = []
    package_name = _single_delta_identity_value(
        deltas=deltas,
        attr="package_name",
        fallback=delta_request.package_name,
        diagnostics=diagnostics,
    )
    package_root = _single_delta_identity_value(
        deltas=deltas,
        attr="package_root",
        fallback=delta_request.package_root,
        diagnostics=diagnostics,
    )
    sources_root = _single_delta_identity_value(
        deltas=deltas,
        attr="sources_root",
        fallback=delta_request.sources_root,
        diagnostics=diagnostics,
    )
    if diagnostics:
        return None, diagnostics

    paths_by_relative_path: dict[str, CodePackageDeltaPath] = {}
    warnings: list[str] = []
    for delta_index, delta in enumerate(deltas):
        warnings.extend(delta.warnings)
        for path in delta.paths:
            existing = paths_by_relative_path.get(path.relative_path)
            if existing is not None and _package_delta_path_identity(
                existing
            ) != _package_delta_path_identity(path):
                diagnostics.append(
                    "generated materialization package-delta conflict for "
                    f"path {path.relative_path!r} at delta index {delta_index}."
                )
                continue
            if existing is None:
                paths_by_relative_path[path.relative_path] = (
                    CodePackageDeltaPath.model_validate(
                        path.model_dump(mode="json", exclude_none=True)
                    )
                )
    if diagnostics:
        return None, diagnostics

    mode = "mixed"
    package_count = _generated_materialization_package_delta_count(result)
    grammar_count = _generated_materialization_grammar_anchor_render_count(result)
    section_count = _generated_materialization_section_delta_count(result)
    if package_count and not grammar_count and not section_count:
        mode = "package_delta_direct"
    elif grammar_count and not package_count and not section_count:
        mode = "grammar_anchor_render"
    elif section_count and not package_count and not grammar_count:
        mode = "section_delta_compatibility"

    merged = CodePackageDelta(
        package_name=package_name,
        package_root=package_root,
        sources_root=sources_root,
        authority=CodePackageDeltaAuthorityKind.code_package_delta,
        authority_kind=CodePackageDeltaAuthorityKind.code_package_delta.value,
        production=next(
            (delta.production for delta in deltas if delta.production is not None),
            None,
        ),
        paths=[paths_by_relative_path[path] for path in sorted(paths_by_relative_path)],
        warnings=sorted(set(warnings)),
        metadata=JsonObject(
            _json_object_items(
                None,
                {
                    "source": (
                        "code.generated_materialization_delta." "resolve_package_delta"
                    ),
                    "resolver": "aware_code_service.generated_materialization_delta",
                    "generated_materialization_mode": mode,
                    "entry_count": len(result.entries),
                    "package_delta_entry_count": package_count,
                    "grammar_anchor_render_entry_count": grammar_count,
                    "section_delta_entry_count": section_count,
                    "renderer_operation_count": (
                        _generated_materialization_renderer_operation_count(result)
                    ),
                },
            )
        ),
    )
    return _normalize_package_delta(merged), []


def _single_delta_identity_value(
    *,
    deltas: list[CodePackageDelta],
    attr: str,
    fallback: str | None,
    diagnostics: list[str],
) -> str | None:
    values = {
        value
        for value in (getattr(delta, attr) for delta in deltas)
        if isinstance(value, str) and value
    }
    if len(values) > 1:
        diagnostics.append(
            f"generated materialization package deltas disagree on {attr}: "
            f"{sorted(values)}."
        )
        return None
    if values:
        return next(iter(values))
    return fallback


def _package_delta_path_identity(path: CodePackageDeltaPath) -> Mapping[str, object]:
    return {
        "relative_path": path.relative_path,
        "kind": _enum_text(path.kind),
        "content_text": path.content_text,
        "content_plan": (
            path.content_plan.model_dump(mode="json", exclude_none=True)
            if path.content_plan is not None
            else None
        ),
        "before_hash": path.before_hash,
        "after_hash": path.after_hash,
        "language": _enum_text(path.language) if path.language is not None else None,
        "is_structural": path.is_structural,
        "path_role": _enum_text(path.path_role),
    }


def _generated_renderer_delta_operation_sort_key(
    operation: CodeGeneratedRendererDeltaOperation,
) -> tuple[str, ...]:
    return (
        operation.operation_key or "",
        _enum_text(operation.kind),
        operation.anchor.anchor_key if operation.anchor is not None else "",
        operation.renderer_key or "",
    )


def _validate_section_delta_entry(
    entry: CodeSectionDeltaEntry,
    *,
    index: int,
    require_resolver_inputs: bool,
    registry: CodeSectionSegmentCapabilityRegistry,
) -> list[str]:
    diagnostics: list[str] = []
    prefix = f"entries[{index}]"
    operation = _enum_text(entry.operation)
    supported_operations = {
        CodeSectionDeltaOperationKind.replace_segment.value,
        CodeSectionDeltaOperationKind.insert_before_section.value,
        CodeSectionDeltaOperationKind.insert_after_section.value,
    }
    if operation not in supported_operations:
        diagnostics.append(
            f"{prefix}.operation {operation!r} is not supported by "
            "the first Code section-delta resolver."
        )

    section_ref = entry.section_ref
    relative_path = _safe_relative_path(
        section_ref.relative_path,
        context=f"{prefix}.section_ref.relative_path",
    )
    if relative_path is None:
        diagnostics.append(f"{prefix}.section_ref.relative_path is invalid.")
    if not section_ref.section_type.strip():
        diagnostics.append(f"{prefix}.section_ref.section_type is required.")
    if (
        not section_ref.identity_hash
        and not section_ref.qualname
        and section_ref.section_id is None
    ):
        diagnostics.append(
            f"{prefix}.section_ref requires identity_hash, qualname, or section_id."
        )

    if operation == CodeSectionDeltaOperationKind.replace_segment.value:
        if entry.nested_member_insert_anchor is not None:
            diagnostics.append(
                f"{prefix}.nested_member_insert_anchor must be empty for "
                "replace_segment."
            )
        if entry.segment_ref is None:
            diagnostics.append(f"{prefix}.segment_ref is required for replace_segment.")
        else:
            segment_ref = entry.segment_ref
            diagnostics.extend(
                _validate_section_segment_capability(
                    section_type=section_ref.section_type,
                    segment_name=segment_ref.segment_name,
                    prefix=prefix,
                    registry=registry,
                )
            )
            if require_resolver_inputs and (
                segment_ref.byte_start is None or segment_ref.byte_end is None
            ):
                diagnostics.append(
                    f"{prefix}.segment_ref byte_start and byte_end are required."
                )
            elif (
                require_resolver_inputs
                and segment_ref.byte_start is not None
                and segment_ref.byte_end is not None
                and (
                    segment_ref.byte_start < 0
                    or segment_ref.byte_end < segment_ref.byte_start
                )
            ):
                diagnostics.append(f"{prefix}.segment_ref byte range is invalid.")
            if not segment_ref.segment_name.strip():
                diagnostics.append(f"{prefix}.segment_ref.segment_name is required.")
        if entry.content_text is None:
            diagnostics.append(
                f"{prefix}.content_text is required for replace_segment."
            )
    elif operation in {
        CodeSectionDeltaOperationKind.insert_before_section.value,
        CodeSectionDeltaOperationKind.insert_after_section.value,
    }:
        if entry.segment_ref is not None:
            diagnostics.append(f"{prefix}.segment_ref must be empty for {operation}.")
        if entry.content_text is None:
            diagnostics.append(f"{prefix}.content_text is required for {operation}.")
        if entry.nested_member_insert_anchor is not None:
            diagnostics.extend(
                _validate_nested_member_insert_anchor(
                    entry=entry,
                    index=index,
                    operation=operation,
                )
            )
    elif entry.nested_member_insert_anchor is not None:
        diagnostics.append(
            f"{prefix}.nested_member_insert_anchor is only supported for section "
            "insert operations."
        )

    for field_name, value in (
        ("before_hash", entry.before_hash),
        ("after_hash", entry.after_hash),
        (
            "segment_ref.before_segment_hash",
            entry.segment_ref.before_segment_hash if entry.segment_ref else None,
        ),
    ):
        if value is not None and _normalize_sha256_digest(value) is None:
            diagnostics.append(f"{prefix}.{field_name} must be a sha256 digest.")

    return diagnostics


def _validate_section_segment_capability(
    *,
    section_type: str,
    segment_name: str,
    prefix: str,
    registry: CodeSectionSegmentCapabilityRegistry,
) -> list[str]:
    normalized_section_type = section_type.strip()
    normalized_segment_name = segment_name.strip()
    if not normalized_section_type or not normalized_segment_name:
        return []

    capability = registry.capability_for_section_type(normalized_section_type)
    if capability is None:
        supported_section_types = ", ".join(registry.supported_section_types())
        return [
            (
                f"{prefix}.section_ref.section_type {normalized_section_type!r} "
                "has no Code section-segment capability registration. "
                f"supported section types: {supported_section_types}."
            )
        ]
    if capability.supports_segment(normalized_segment_name):
        return []

    supported_segments = ", ".join(capability.segment_names)
    return [
        (
            f"{prefix}.segment_ref.segment_name {normalized_segment_name!r} "
            f"is not registered for section_type {normalized_section_type!r}. "
            f"supported segments: {supported_segments}."
        )
    ]


def _validate_nested_member_insert_anchor(
    *,
    entry: CodeSectionDeltaEntry,
    index: int,
    operation: str,
) -> list[str]:
    prefix = f"entries[{index}]"
    section_ref = entry.section_ref
    anchor = entry.nested_member_insert_anchor
    if anchor is None:
        return []

    diagnostics: list[str] = []
    if operation != CodeSectionDeltaOperationKind.insert_after_section.value:
        diagnostics.append(
            f"{prefix}.nested_member_insert_anchor only supports "
            "insert_after_section in v0."
        )
    language = _optional_text(section_ref.language)
    if language not in {
        CodeLanguage.aware.value,
        CodeLanguage.python.value,
    }:
        diagnostics.append(
            f"{prefix}.section_ref.language must be 'aware' or 'python' for "
            "nested_member_insert_anchor."
        )
    if _optional_text(section_ref.section_type) != CodeSectionType.class_.value:
        diagnostics.append(
            f"{prefix}.section_ref.section_type must be 'class' for "
            "nested_member_insert_anchor."
        )
    if _optional_text(anchor.member_section_type) != CodeSectionType.function.value:
        diagnostics.append(
            f"{prefix}.nested_member_insert_anchor.member_section_type must be "
            "'function' in v0."
        )
    if _enum_text(anchor.insert_position) != "end":
        diagnostics.append(
            f"{prefix}.nested_member_insert_anchor.insert_position must be 'end' "
            "in v0."
        )
    return diagnostics


def _resolve_section_delta_set(
    delta_set: CodeSectionDeltaSet,
    *,
    strict: bool,
    registry: CodeSectionSegmentCapabilityRegistry,
) -> tuple[CodePackageDelta | None, list[str]]:
    package_root_text = _optional_path_text(delta_set.package_root)
    if package_root_text is None:
        return None, ["package_root is required for section-delta resolution."]

    base_path = _section_delta_base_path(
        package_root=package_root_text,
        sources_root=delta_set.sources_root,
    )
    file_text_by_path: dict[str, str] = {}
    original_text_by_path: dict[str, str] = {}
    already_applied_entry_count_by_path: dict[str, int] = {}
    diagnostics: list[str] = []

    for index, entry in enumerate(delta_set.entries):
        relative_path = _safe_relative_path(
            entry.section_ref.relative_path,
            context=f"entries[{index}].section_ref.relative_path",
        )
        if relative_path is None:
            diagnostics.append(
                f"entries[{index}].section_ref.relative_path is invalid."
            )
            continue
        if relative_path not in file_text_by_path:
            resolved_path = _resolve_safe_child(
                base=base_path, relative_path=relative_path
            )
            if resolved_path is None:
                diagnostics.append(
                    f"entries[{index}].section_ref.relative_path escapes package root."
                )
                continue
            if not resolved_path.is_file():
                diagnostics.append(
                    f"entries[{index}].section_ref.relative_path does not exist: "
                    f"{relative_path}"
                )
                continue
            text = resolved_path.read_text(encoding="utf-8")
            file_text_by_path[relative_path] = text
            original_text_by_path[relative_path] = text

        outcome = _apply_section_delta_entry(
            entry,
            index=index,
            current_text=file_text_by_path[relative_path],
            strict=strict,
            registry=registry,
        )
        diagnostics.extend(outcome.diagnostics)
        if outcome.updated_text is not None:
            file_text_by_path[relative_path] = outcome.updated_text
            if outcome.already_applied:
                already_applied_entry_count_by_path[relative_path] = (
                    already_applied_entry_count_by_path.get(relative_path, 0) + 1
                )

    if diagnostics:
        return None, diagnostics

    paths = [
        CodePackageDeltaPath(
            relative_path=relative_path,
            kind=CodePackageDeltaKind.update,
            content_text=updated_text,
            before_hash=_sha256_digest(original_text_by_path[relative_path]),
            after_hash=_sha256_digest(updated_text),
            language=_path_language_for_entries(delta_set.entries, relative_path),
            is_structural=True,
            path_role=CodePackagePathRole.authored_source,
            production=delta_set.production,
            metadata=JsonObject(
                {
                    "source": "code.section_delta.resolve_package_delta",
                    "resolver": "aware_code_service.section_delta",
                    "entry_count": _entry_count_for_path(
                        delta_set.entries, relative_path
                    ),
                    "already_applied_entry_count": (
                        already_applied_entry_count_by_path.get(relative_path, 0)
                    ),
                    "all_entries_already_applied": (
                        already_applied_entry_count_by_path.get(relative_path, 0)
                        == _entry_count_for_path(delta_set.entries, relative_path)
                    ),
                }
            ),
        )
        for relative_path, updated_text in sorted(file_text_by_path.items())
    ]
    return (
        _normalize_package_delta(
            CodePackageDelta(
                package_name=delta_set.package_name,
                package_root=delta_set.package_root,
                sources_root=delta_set.sources_root,
                authority=CodePackageDeltaAuthorityKind.code_package_delta,
                authority_kind=CodePackageDeltaAuthorityKind.code_package_delta.value,
                production=delta_set.production,
                paths=paths,
                warnings=list(delta_set.warnings),
                metadata=JsonObject(
                    {
                        "source": "code.section_delta.resolve_package_delta",
                        "resolver": "aware_code_service.section_delta",
                    }
                ),
            )
        ),
        [],
    )


def _apply_section_delta_entry(
    entry: CodeSectionDeltaEntry,
    *,
    index: int,
    current_text: str,
    strict: bool,
    registry: CodeSectionSegmentCapabilityRegistry,
) -> _SectionDeltaApplyOutcome:
    _ = strict
    prefix = f"entries[{index}]"
    diagnostics = _validate_section_match(
        entry=entry,
        index=index,
        current_text=current_text,
        registry=registry,
    )
    if diagnostics:
        return _SectionDeltaApplyOutcome(updated_text=None, diagnostics=diagnostics)

    operation = _enum_text(entry.operation)
    if operation in {
        CodeSectionDeltaOperationKind.insert_before_section.value,
        CodeSectionDeltaOperationKind.insert_after_section.value,
    }:
        return _apply_section_insert_delta_entry(
            entry=entry,
            index=index,
            current_text=current_text,
            operation=operation,
        )

    segment_ref = entry.segment_ref
    replacement_text = entry.content_text
    if segment_ref is None or replacement_text is None:
        return _SectionDeltaApplyOutcome(
            updated_text=None,
            diagnostics=[f"{prefix} is missing segment_ref or content_text."],
        )
    if segment_ref.byte_start is None or segment_ref.byte_end is None:
        return _SectionDeltaApplyOutcome(
            updated_text=None,
            diagnostics=[f"{prefix}.segment_ref byte_start and byte_end are required."],
        )

    byte_start = segment_ref.byte_start
    byte_end = segment_ref.byte_end
    if byte_start < 0 or byte_end < byte_start:
        return _SectionDeltaApplyOutcome(
            updated_text=None,
            diagnostics=[f"{prefix}.segment_ref byte range is invalid."],
        )

    current_bytes = current_text.encode("utf-8")
    if byte_end > len(current_bytes):
        return _SectionDeltaApplyOutcome(
            updated_text=None,
            diagnostics=[f"{prefix}.segment_ref byte range exceeds source length."],
        )

    before_segment_text = current_bytes[byte_start:byte_end].decode("utf-8")
    before_segment_hash = _sha256_digest(before_segment_text)
    if not _sha256_matches(segment_ref.before_segment_hash, before_segment_hash):
        if before_segment_text == replacement_text and _sha256_matches(
            entry.after_hash, before_segment_hash
        ):
            return _SectionDeltaApplyOutcome(
                updated_text=current_text,
                diagnostics=[],
                already_applied=True,
            )
        return _SectionDeltaApplyOutcome(
            updated_text=None,
            diagnostics=[f"{prefix}.segment_ref.before_segment_hash mismatch."],
        )
    if not _sha256_matches(entry.before_hash, _sha256_digest(current_text)):
        return _SectionDeltaApplyOutcome(
            updated_text=None,
            diagnostics=[f"{prefix}.before_hash mismatch."],
        )
    if not _sha256_matches(entry.after_hash, _sha256_digest(replacement_text)):
        return _SectionDeltaApplyOutcome(
            updated_text=None,
            diagnostics=[f"{prefix}.after_hash mismatch."],
        )

    updated_bytes = (
        current_bytes[:byte_start]
        + replacement_text.encode("utf-8")
        + current_bytes[byte_end:]
    )
    return _SectionDeltaApplyOutcome(
        updated_text=updated_bytes.decode("utf-8"),
        diagnostics=[],
    )


def _apply_section_insert_delta_entry(
    *,
    entry: CodeSectionDeltaEntry,
    index: int,
    current_text: str,
    operation: str,
) -> _SectionDeltaApplyOutcome:
    prefix = f"entries[{index}]"
    insert_text = entry.content_text
    if insert_text is None:
        return _SectionDeltaApplyOutcome(
            updated_text=None,
            diagnostics=[f"{prefix}.content_text is required for {operation}."],
        )
    if entry.nested_member_insert_anchor is not None:
        return _apply_nested_member_insert_delta_entry(
            entry=entry,
            index=index,
            current_text=current_text,
            operation=operation,
        )
    spans, diagnostics = _section_match_spans_for_entry(
        entry=entry,
        index=index,
        current_text=current_text,
    )
    if diagnostics:
        return _SectionDeltaApplyOutcome(updated_text=None, diagnostics=diagnostics)
    if len(spans) != 1:
        return _SectionDeltaApplyOutcome(
            updated_text=None,
            diagnostics=[f"{prefix}.section_ref matched multiple parsed sections."],
        )
    if not _sha256_matches(entry.before_hash, _sha256_digest(current_text)):
        return _SectionDeltaApplyOutcome(
            updated_text=None,
            diagnostics=[f"{prefix}.before_hash mismatch."],
        )
    if not _sha256_matches(entry.after_hash, _sha256_digest(insert_text)):
        return _SectionDeltaApplyOutcome(
            updated_text=None,
            diagnostics=[f"{prefix}.after_hash mismatch."],
        )
    byte_start, byte_end = spans[0]
    insert_at = (
        byte_start
        if operation == CodeSectionDeltaOperationKind.insert_before_section.value
        else byte_end
    )
    current_bytes = current_text.encode("utf-8")
    insert_bytes = insert_text.encode("utf-8")
    if operation == CodeSectionDeltaOperationKind.insert_before_section.value:
        existing_start = max(0, insert_at - len(insert_bytes))
        if current_bytes[existing_start:insert_at] == insert_bytes:
            return _SectionDeltaApplyOutcome(
                updated_text=current_text,
                diagnostics=[],
                already_applied=True,
            )
    elif current_bytes[insert_at : insert_at + len(insert_bytes)] == insert_bytes:
        return _SectionDeltaApplyOutcome(
            updated_text=current_text,
            diagnostics=[],
            already_applied=True,
        )
    updated_bytes = current_bytes[:insert_at] + insert_bytes + current_bytes[insert_at:]
    return _SectionDeltaApplyOutcome(
        updated_text=updated_bytes.decode("utf-8"),
        diagnostics=[],
    )


def _apply_nested_member_insert_delta_entry(
    *,
    entry: CodeSectionDeltaEntry,
    index: int,
    current_text: str,
    operation: str,
) -> _SectionDeltaApplyOutcome:
    prefix = f"entries[{index}]"
    insert_text = entry.content_text
    if insert_text is None:
        return _SectionDeltaApplyOutcome(
            updated_text=None,
            diagnostics=[f"{prefix}.content_text is required for {operation}."],
        )
    diagnostics = _validate_nested_member_insert_anchor(
        entry=entry,
        index=index,
        operation=operation,
    )
    if diagnostics:
        return _SectionDeltaApplyOutcome(updated_text=None, diagnostics=diagnostics)

    target = _nested_member_insert_target_for_entry(
        entry=entry,
        index=index,
        current_text=current_text,
        insert_text=insert_text,
    )
    if target.diagnostics:
        return _SectionDeltaApplyOutcome(
            updated_text=None,
            diagnostics=target.diagnostics,
        )
    if target.already_applied:
        return _SectionDeltaApplyOutcome(
            updated_text=current_text,
            diagnostics=[],
            already_applied=True,
        )
    if target.insert_at is None:
        return _SectionDeltaApplyOutcome(
            updated_text=None,
            diagnostics=[f"{prefix}.nested_member_insert_anchor did not resolve."],
        )
    if not _sha256_matches(entry.before_hash, _sha256_digest(current_text)):
        return _SectionDeltaApplyOutcome(
            updated_text=None,
            diagnostics=[f"{prefix}.before_hash mismatch."],
        )
    if not _sha256_matches(entry.after_hash, _sha256_digest(insert_text)):
        return _SectionDeltaApplyOutcome(
            updated_text=None,
            diagnostics=[f"{prefix}.after_hash mismatch."],
        )

    current_bytes = current_text.encode("utf-8")
    insert_bytes = insert_text.encode("utf-8")
    updated_bytes = (
        current_bytes[: target.insert_at]
        + insert_bytes
        + current_bytes[target.insert_at :]
    )
    return _SectionDeltaApplyOutcome(
        updated_text=updated_bytes.decode("utf-8"),
        diagnostics=[],
    )


def _nested_member_insert_target_for_entry(
    *,
    entry: CodeSectionDeltaEntry,
    index: int,
    current_text: str,
    insert_text: str,
) -> _NestedMemberInsertTarget:
    prefix = f"entries[{index}]"
    section_ref = entry.section_ref
    anchor = entry.nested_member_insert_anchor
    if anchor is None:
        return _NestedMemberInsertTarget(
            insert_at=None,
            diagnostics=[f"{prefix}.nested_member_insert_anchor is required."],
        )
    try:
        setup_code_plugins()
        language = CodeLanguage(section_ref.language or "")
        parent_section_type = CodeSectionType(section_ref.section_type)
        member_section_type = CodeSectionType(anchor.member_section_type)
        code = build_code_from_content(
            sections_index=CodeSectionBuilderIndex(),
            content=current_text,
            code_key="inline://nested-member-insert",
            language=language,
            symbol_table=CodeSymbolTable(),
        )
    except ValueError as exc:
        return _NestedMemberInsertTarget(
            insert_at=None,
            diagnostics=[f"{prefix}.section_ref parser validation failed: {exc}"],
        )
    except Exception as exc:
        return _NestedMemberInsertTarget(
            insert_at=None,
            diagnostics=[f"{prefix}.section_ref parser validation failed: {exc}"],
        )

    parents = [
        section
        for section in code.code_sections
        if _builder_section_matches_ref(
            section=section,
            section_type=parent_section_type,
            section_ref=section_ref,
        )
    ]
    if not parents:
        return _NestedMemberInsertTarget(
            insert_at=None,
            diagnostics=[f"{prefix}.section_ref did not match parsed section truth."],
        )
    if len(parents) > 1:
        return _NestedMemberInsertTarget(
            insert_at=None,
            diagnostics=[f"{prefix}.section_ref matched multiple parsed sections."],
        )

    parent = parents[0]
    current_bytes = current_text.encode("utf-8")
    existing_member = _nested_member_section_for_anchor(
        sections=tuple(code.code_sections),
        parent_section=parent,
        member_section_type=member_section_type,
        anchor=anchor,
    )
    if existing_member is not None:
        existing_text = _builder_section_source_text(
            section=existing_member,
            source_bytes=current_bytes,
        )
        if _normalize_inserted_member_text(existing_text) == (
            _normalize_inserted_member_text(insert_text)
        ):
            return _NestedMemberInsertTarget(
                insert_at=None,
                diagnostics=[],
                already_applied=True,
            )
        return _NestedMemberInsertTarget(
            insert_at=None,
            diagnostics=[
                (
                    f"{prefix}.nested_member_insert_anchor.member_qualname "
                    "already exists with different content."
                )
            ],
        )

    parent_segment = parent.content_part_text_segment
    if parent_segment.byte_start is None or parent_segment.byte_end is None:
        return _NestedMemberInsertTarget(
            insert_at=None,
            diagnostics=[
                f"{prefix}.nested_member_insert_anchor parent byte range is unavailable."
            ],
        )
    insert_at = _nested_member_insert_position(
        language=language,
        parent_start=parent_segment.byte_start,
        parent_end=parent_segment.byte_end,
        source_bytes=current_bytes,
    )
    if insert_at is None:
        return _NestedMemberInsertTarget(
            insert_at=None,
            diagnostics=[
                (
                    f"{prefix}.nested_member_insert_anchor did not resolve before "
                    "class closing brace."
                )
            ],
        )
    return _NestedMemberInsertTarget(
        insert_at=insert_at,
        diagnostics=[],
    )


def _nested_member_insert_position(
    *,
    language: CodeLanguage,
    parent_start: int,
    parent_end: int,
    source_bytes: bytes,
) -> int | None:
    if language is CodeLanguage.python:
        if source_bytes[parent_end : parent_end + 2] == b"\r\n":
            return parent_end + 2
        if source_bytes[parent_end : parent_end + 1] == b"\n":
            return parent_end + 1
        return parent_end
    if language is CodeLanguage.aware:
        parent_bytes = source_bytes[parent_start:parent_end]
        closing_brace_offset = parent_bytes.rfind(b"}")
        if closing_brace_offset >= 0:
            return parent_start + closing_brace_offset
    return None


def _builder_section_matches_ref(
    *,
    section: object,
    section_type: CodeSectionType,
    section_ref: CodeSectionRef,
) -> bool:
    return (
        getattr(section, "type", None) == section_type
        and (
            not section_ref.identity_hash
            or getattr(section, "identity_hash", None) == section_ref.identity_hash
        )
        and (
            not section_ref.qualname
            or getattr(section, "qualname", None) == section_ref.qualname
        )
    )


def _nested_member_section_for_anchor(
    *,
    sections: tuple[object, ...],
    parent_section: object,
    member_section_type: CodeSectionType,
    anchor: object,
) -> object | None:
    anchor_member_qualname = getattr(anchor, "member_qualname", None)
    member_qualname = (
        _optional_text(anchor_member_qualname)
        if isinstance(anchor_member_qualname, str)
        else None
    )
    if member_qualname is None:
        return None
    parent_segment = getattr(parent_section, "content_part_text_segment", None)
    if parent_segment is None:
        return None
    parent_start = getattr(parent_segment, "byte_start", None)
    parent_end = getattr(parent_segment, "byte_end", None)
    if not isinstance(parent_start, int) or not isinstance(parent_end, int):
        return None
    for section in sections:
        if (
            getattr(section, "type", None) != member_section_type
            or getattr(section, "qualname", None) != member_qualname
        ):
            continue
        segment = getattr(section, "content_part_text_segment", None)
        if segment is None:
            continue
        member_start = getattr(segment, "byte_start", None)
        member_end = getattr(segment, "byte_end", None)
        if (
            isinstance(member_start, int)
            and isinstance(member_end, int)
            and parent_start <= member_start
            and member_end <= parent_end
        ):
            return section
    return None


def _builder_section_source_text(*, section: object, source_bytes: bytes) -> str:
    segment = getattr(section, "content_part_text_segment", None)
    if segment is None:
        return ""
    byte_start = getattr(segment, "byte_start", None)
    byte_end = getattr(segment, "byte_end", None)
    if not isinstance(byte_start, int) or not isinstance(byte_end, int):
        return ""
    return source_bytes[byte_start:byte_end].decode("utf-8")


def _normalize_inserted_member_text(value: str) -> str:
    return value.strip()


def _validate_section_match(
    *,
    entry: CodeSectionDeltaEntry,
    index: int,
    current_text: str,
    registry: CodeSectionSegmentCapabilityRegistry,
) -> list[str]:
    prefix = f"entries[{index}]"
    section_ref = entry.section_ref
    if not section_ref.language:
        return []

    try:
        setup_code_plugins()
        language = CodeLanguage(section_ref.language)
        section_type = CodeSectionType(section_ref.section_type)
        descriptors = collect_top_level_section_identity_descriptors(
            content=current_text,
            language=language,
        )
    except ValueError as exc:
        capability = registry.capability_for_section_type(section_ref.section_type)
        if capability is not None and not capability.is_builtin:
            return []
        return [f"{prefix}.section_ref parser validation failed: {exc}"]
    except Exception as exc:
        return [f"{prefix}.section_ref parser validation failed: {exc}"]

    candidates = [
        descriptor
        for descriptor in descriptors
        if descriptor.section_type is section_type
        and (
            not section_ref.identity_hash
            or descriptor.identity_hash == section_ref.identity_hash
        )
        and (not section_ref.qualname or descriptor.qualname == section_ref.qualname)
    ]
    if not candidates:
        builder_candidates = _builder_section_match_spans(
            current_text=current_text,
            language=language,
            section_type=section_type,
            section_ref=section_ref,
        )
        if not builder_candidates:
            return [f"{prefix}.section_ref did not match parsed section truth."]
        segment_ref = entry.segment_ref
        if (
            segment_ref is None
            or segment_ref.byte_start is None
            or segment_ref.byte_end is None
        ):
            return []
        if any(
            byte_start <= segment_ref.byte_start and segment_ref.byte_end <= byte_end
            for byte_start, byte_end in builder_candidates
        ):
            return []
        if _builder_section_segment_matches(
            current_text=current_text,
            language=language,
            section_type=section_type,
            section_ref=section_ref,
            segment_name=segment_ref.segment_name,
            byte_start=segment_ref.byte_start,
            byte_end=segment_ref.byte_end,
        ):
            return []
        return [f"{prefix}.segment_ref byte range is outside the parsed section."]

    if not candidates:
        return [f"{prefix}.section_ref did not match parsed section truth."]

    segment_ref = entry.segment_ref
    if (
        segment_ref is None
        or segment_ref.byte_start is None
        or segment_ref.byte_end is None
    ):
        return []
    if any(
        descriptor.byte_start <= segment_ref.byte_start
        and segment_ref.byte_end <= descriptor.byte_end
        for descriptor in candidates
    ):
        return []
    if _builder_section_segment_matches(
        current_text=current_text,
        language=language,
        section_type=section_type,
        section_ref=section_ref,
        segment_name=segment_ref.segment_name,
        byte_start=segment_ref.byte_start,
        byte_end=segment_ref.byte_end,
    ):
        return []
    return [f"{prefix}.segment_ref byte range is outside the parsed section."]


def _section_match_spans_for_entry(
    *,
    entry: CodeSectionDeltaEntry,
    index: int,
    current_text: str,
) -> tuple[tuple[tuple[int, int], ...], list[str]]:
    prefix = f"entries[{index}]"
    section_ref = entry.section_ref
    if not section_ref.language:
        return (), [f"{prefix}.section_ref.language is required."]
    try:
        setup_code_plugins()
        language = CodeLanguage(section_ref.language)
        section_type = CodeSectionType(section_ref.section_type)
        descriptors = collect_top_level_section_identity_descriptors(
            content=current_text,
            language=language,
        )
    except ValueError as exc:
        return (), [f"{prefix}.section_ref parser validation failed: {exc}"]
    except Exception as exc:
        return (), [f"{prefix}.section_ref parser validation failed: {exc}"]

    spans = tuple(
        (descriptor.byte_start, descriptor.byte_end)
        for descriptor in descriptors
        if descriptor.section_type is section_type
        and (
            not section_ref.identity_hash
            or descriptor.identity_hash == section_ref.identity_hash
        )
        and (not section_ref.qualname or descriptor.qualname == section_ref.qualname)
    )
    if spans:
        return spans, []

    spans = _builder_section_match_spans(
        current_text=current_text,
        language=language,
        section_type=section_type,
        section_ref=section_ref,
    )
    if spans:
        return spans, []
    return (), [f"{prefix}.section_ref did not match parsed section truth."]


def _builder_section_match_spans(
    *,
    current_text: str,
    language: CodeLanguage,
    section_type: CodeSectionType,
    section_ref: CodeSectionRef,
) -> tuple[tuple[int, int], ...]:
    try:
        code = build_code_from_content(
            sections_index=CodeSectionBuilderIndex(),
            content=current_text,
            code_key="inline://section-match",
            language=language,
            symbol_table=CodeSymbolTable(),
        )
    except Exception:
        return ()
    spans: list[tuple[int, int]] = []
    for section in code.code_sections:
        segment = section.content_part_text_segment
        if (
            section.type == section_type
            and (
                not section_ref.identity_hash
                or section.identity_hash == section_ref.identity_hash
            )
            and (not section_ref.qualname or section.qualname == section_ref.qualname)
            and segment.byte_start is not None
            and segment.byte_end is not None
        ):
            spans.append((segment.byte_start, segment.byte_end))
    return tuple(spans)


def _builder_section_segment_matches(
    *,
    current_text: str,
    language: CodeLanguage,
    section_type: CodeSectionType,
    section_ref: CodeSectionRef,
    segment_name: str,
    byte_start: int,
    byte_end: int,
) -> bool:
    try:
        code = build_code_from_content(
            sections_index=CodeSectionBuilderIndex(),
            content=current_text,
            code_key="inline://section-segment-match",
            language=language,
            symbol_table=CodeSymbolTable(),
        )
    except Exception:
        return False
    for section in code.code_sections:
        if (
            section.type != section_type
            or (
                section_ref.identity_hash
                and section.identity_hash != section_ref.identity_hash
            )
            or (section_ref.qualname and section.qualname != section_ref.qualname)
        ):
            continue
        segment = CodeSegmentScanner.get_segment_from_section(
            section,
            segment_name,
        )
        if (
            segment is not None
            and segment.byte_start == byte_start
            and segment.byte_end == byte_end
        ):
            return True
    return False


def _section_delta_base_path(*, package_root: str, sources_root: str | None) -> Path:
    base = Path(package_root)
    sources = _optional_path_text(sources_root)
    if sources is not None:
        base = base / sources
    return base.resolve()


def _resolve_safe_child(*, base: Path, relative_path: str) -> Path | None:
    target = (base / relative_path).resolve()
    try:
        target.relative_to(base)
    except ValueError:
        return None
    return target


def _path_language_for_entries(
    entries: list[CodeSectionDeltaEntry],
    relative_path: str,
) -> ApiCodeLanguage | None:
    for entry in entries:
        if entry.section_ref.relative_path == relative_path:
            language = _optional_text(entry.section_ref.language)
            if language is not None:
                try:
                    return ApiCodeLanguage(language)
                except ValueError:
                    return None
    return None


def _entry_count_for_path(
    entries: list[CodeSectionDeltaEntry],
    relative_path: str,
) -> int:
    return sum(
        1 for entry in entries if entry.section_ref.relative_path == relative_path
    )


def _optional_path_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    return text.replace("\\", "/")


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None


def _resolve_semantic_contracts(
    *,
    semantic_contract: ModuleSemanticContract | None,
    semantic_contracts: tuple[ModuleSemanticContract, ...] | None,
) -> tuple[ModuleSemanticContract, ...]:
    if semantic_contracts:
        return semantic_contracts
    if semantic_contract is not None:
        return (semantic_contract,)
    contracts = tuple(AwareModulePluginRegistry.get_module_semantic_contracts())
    if not contracts:
        return (AWARE_CODE_SEMANTIC_CONTRACT,)
    code_contracts = tuple(
        contract
        for contract in contracts
        if contract.provider_key == AWARE_CODE_SEMANTIC_CONTRACT.provider_key
    )
    non_code_contracts = tuple(
        contract
        for contract in contracts
        if contract.provider_key != AWARE_CODE_SEMANTIC_CONTRACT.provider_key
    )
    if not code_contracts:
        return (AWARE_CODE_SEMANTIC_CONTRACT, *contracts)
    return (*code_contracts, *non_code_contracts)


def _semantic_contract_module_for_provider_key(provider_key: str) -> str:
    module = AwareModulePluginRegistry.semantic_contract_module_for_provider_key(
        provider_key,
    )
    if module is not None:
        return module
    explicit_module = _SEMANTIC_CONTRACT_MODULE_BY_PROVIDER_KEY.get(provider_key)
    if explicit_module is not None:
        return explicit_module
    return f"{provider_key}.semantic_contract"


def _safe_relative_path(value: str, *, context: str) -> str | None:
    _ = context
    text = _optional_path_text(value)
    if text is None:
        return None
    path = PurePosixPath(text)
    if path.is_absolute() or ".." in path.parts:
        return None
    return str(path)


def _sha256_digest(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _normalize_sha256_digest(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip().lower()
    if text.startswith("sha256:"):
        text = text.split(":", 1)[1]
    if len(text) != 64:
        return None
    if not all(ch in "0123456789abcdef" for ch in text):
        return None
    return text


def _sha256_matches(expected: str | None, actual: str) -> bool:
    expected_digest = _normalize_sha256_digest(expected)
    if expected_digest is None:
        return True
    actual_digest = _normalize_sha256_digest(actual)
    return actual_digest == expected_digest


def _enum_text(value: object) -> str:
    raw_value = getattr(value, "value", value)
    return raw_value if isinstance(raw_value, str) else str(raw_value)


__all__ = [
    "build_aware_code_service_protocol_handler",
    "classify_code_source_ownership_request",
]
