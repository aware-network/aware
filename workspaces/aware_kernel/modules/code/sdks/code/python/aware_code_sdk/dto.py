from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from aware_code_service_dto.code.features.package_common import CodePackagePathRole
from aware_code_service_dto.code.features.package_delta import (
    CodePackageDelta,
    CodePackageDeltaAuthorityKind,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
    CodePackageDeltaProducerRef,
    CodePackageDeltaProduction,
    FingerprintCodePackageDeltaRequest,
    FingerprintCodePackageDeltaResponse,
    NormalizeCodePackageDeltaRequest,
    NormalizeCodePackageDeltaResponse,
)
from aware_code_service_dto.code.features.package_distribution import CodeLanguage
from aware_code_service_dto.code.features.package_layout import (
    CodePackageLayoutContract as _GeneratedCodePackageLayoutContract,
    CodePackageLayoutPathRole,
    DescribeCodePackageLayoutRequest,
    DescribeCodePackageLayoutResponse,
    DiscoverCodePackageLayoutsRequest,
    DiscoverCodePackageLayoutsResponse,
    ValidateCodePackageLayoutRequest,
    ValidateCodePackageLayoutResponse,
)
from aware_code_service_dto.code.features.grammar_profile import (
    CodeGrammarAnchorCoverageDiagnostic,
    CodeGrammarBackendDescriptor,
    CodeGrammarProfile,
    CodeGrammarProfileDiagnostic,
    CodeGrammarProfileResolutionStatus,
    CodeGrammarRuleBinding,
    CodeGrammarRuleDeclaration,
    ResolveCodeGrammarProfileRequest,
    ResolveCodeGrammarProfileResponse,
)
from aware_code_service_dto.code.features.grammar_anchor_binding import (
    CodeGrammarAnchorBinding,
    CodeGrammarAnchorBindingDirection,
    CodeGrammarAnchorBindingResolutionStatus,
    CodeGrammarAnchorFixture,
    CodeGrammarAnchorGraphChangeDraft,
    CodeGrammarAnchorTextEvidence,
    CodeGrammarAnchorTextTargetEvidence,
    CodeGraphAttributeSelector,
    CodeGraphFieldSelector,
    ResolveCodeGrammarAnchorBindingEvidenceRequest,
    ResolveCodeGrammarAnchorBindingEvidenceResponse,
    ValidateCodeGrammarAnchorBindingRequest,
    ValidateCodeGrammarAnchorBindingResponse,
)
from aware_code_service_dto.code.features.grammar_anchor_render_delta import (
    CodeGrammarAnchorRenderEntry,
    CodeGrammarAnchorRenderReplacement,
    CodeGrammarAnchorRenderSpanTarget,
    CodeGrammarAnchorRenderSource,
    CodeGrammarAnchorRenderTargetKind,
    ResolveCodeGrammarAnchorRenderDeltaRequest,
    ResolveCodeGrammarAnchorRenderDeltaResponse,
)
from aware_code_service_dto.code.features.generated_materialization_delta import (
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
    FingerprintCodeGeneratedMaterializationDeltaRequest,
    FingerprintCodeGeneratedMaterializationDeltaResponse,
    NormalizeCodeGeneratedMaterializationDeltaRequest,
    NormalizeCodeGeneratedMaterializationDeltaResponse,
    ResolveCodeGeneratedMaterializationPackageDeltaRequest,
    ResolveCodeGeneratedMaterializationPackageDeltaResponse,
    ValidateCodeGeneratedMaterializationDeltaRequest,
    ValidateCodeGeneratedMaterializationDeltaResponse,
)
from aware_code_service_dto.code.features.semantic_analysis import (
    CodeSemanticActionBinding,
    CodeSemanticAnalysisChangePreview,
    CodeSemanticAnalysisDependencyRequirement,
    CodeSemanticAnalysisDiagnostic,
    CodeSemanticDelta,
    CodeSemanticEvent,
    CodeSemanticFunctionCallBinding,
    CodeSemanticTypedOperation,
    PreviewCodeSemanticAnalysisPackageDeltaRequest,
    PreviewCodeSemanticAnalysisPackageDeltaResponse,
)
from aware_code_service_dto.code.features.semantic_source_meaning import (
    CodeSemanticSourceDeltaMeaningInput,
    CodeSemanticSourceDeltaMeaningResolutionMode,
    CodeSemanticSourceIndexRef,
    CodeSemanticSourceMeaningBinding,
    CodeSemanticSourceMeaningContract,
    CodeSemanticSourceMeaningSource,
    ResolveCodeSemanticSourceDeltaMeaningRequest,
    ResolveCodeSemanticSourceDeltaMeaningResponse,
    ResolveCodeSemanticSourceMeaningRequest,
    ResolveCodeSemanticSourceMeaningResponse,
)
from aware_code_service_dto.code.features.semantic_workflow_coverage import (
    CodeSemanticWorkflowCoverageDiagnostic,
    CodeSemanticWorkflowCoverageEntry,
    CodeSemanticWorkflowCoverageStatus,
    CodeSemanticWorkflowGrammarRuleEvidence,
    CodeSemanticWorkflowGraphBindingCoverage,
    ResolveCodeSemanticWorkflowCoverageRequest,
    ResolveCodeSemanticWorkflowCoverageResponse,
)
from aware_code_service_dto.code.features.semantic_contract import (
    CodeCapabilityBundleDescriptor,
    CodeCapabilityExecutionPolicyDescriptor,
    CodeCapabilityParticipationDescriptor,
    CodeCapabilityProfileDescriptor,
    CodeSemanticArtifactLeafOwnershipDescriptor,
    CodeSemanticContract,
    CodeSemanticGeneratedCodePackageDeclaration,
    CodeSemanticContractSpecDeclaration,
    CodeSemanticContractSpecSection,
    CodeSemanticGrammarRuleDescriptor,
    CodeSemanticGrammarRuleFieldDescriptor,
    CodeSemanticManifestResolutionDescriptor,
    CodeSemanticManifestResolutionMatch,
    CodeSemanticMaterializationArtifactOutputDescriptor,
    CodeSemanticMaterializationCodePackageDeltaOutputDescriptor,
    CodeSemanticMaterializationExecutionContextDescriptor,
    CodeSemanticMaterializationInputDescriptor,
    CodeSemanticMaterializationPackageOutputDescriptor,
    CodeSemanticMaterializationRuntimeContextDescriptor,
    CodeSemanticMaterializationRuntimeDescriptor,
    CodeSemanticMaterializationScopeDependency,
    CodeSemanticPackageRoleDescriptor,
    CodeSemanticProviderBinding,
    CodeSemanticRuntimeProjectionPackageDescriptor,
    CodeSemanticScopePackageRef,
    CodeSemanticScopeResolution,
    CodeSemanticSyntaxLaneDescriptor,
    CodeSemanticWorkflowDescriptor,
    CodeSemanticWorkflowInstructionDescriptor,
    DescribeCodeSemanticContractRequest,
    DescribeCodeSemanticContractResponse,
    FindCodeSemanticManifestResolutionRequest,
    FindCodeSemanticManifestResolutionResponse,
    NormalizeCodeSemanticContractRequest,
    NormalizeCodeSemanticContractResponse,
    ResolveCodeSemanticScopeRequest,
    ResolveCodeSemanticScopeResponse,
    ValidateCodeSemanticContractRequest,
    ValidateCodeSemanticContractResponse,
)
from aware_code_service_dto.code.features.section_delta import (
    CodeNestedMemberInsertAnchor,
    CodeNestedMemberInsertPosition,
    CodeSectionDeltaEntry,
    CodeSectionDeltaOperationKind,
    CodeSectionDeltaSet,
    CodeSectionRef,
    CodeSegmentContentDomain,
    CodeSegmentRef,
    CodeSegmentRenderPolicy,
    CodeSegmentRenderPolicyDiagnostic,
    CodeSegmentRenderPolicyResolutionStatus,
    FingerprintCodeSectionDeltaRequest,
    FingerprintCodeSectionDeltaResponse,
    NormalizeCodeSectionDeltaRequest,
    NormalizeCodeSectionDeltaResponse,
    ResolveCodeSectionDeltaPackageDeltaRequest,
    ResolveCodeSectionDeltaPackageDeltaResponse,
    ResolveCodeSegmentRenderPolicyRequest,
    ResolveCodeSegmentRenderPolicyResponse,
    ValidateCodeSectionDeltaRequest,
    ValidateCodeSectionDeltaResponse,
)
from aware_code_service_dto.code.features.source_ownership import (
    ClassifyCodeSourceOwnershipRequest,
    ClassifyCodeSourceOwnershipResponse,
    CodeSourceOwnershipClassification,
    CodeSourceOwnershipObservedPath,
    CodeSourceOwnershipPackageBinding,
    CodeSourceOwnershipPathMatch,
    CodeSourceOwnershipRequest,
    CodeSourceOwnershipResult,
)
from aware_code_service_dto.code.features.source_projection import (
    CodeSourceProjectionActionBinding,
    CodeSourceProjectionEventRef,
    CodeSourceProjectionRequest,
    CodeSourceProjectionResult,
    CodeSourceProjectionSkippedEvent,
    FingerprintCodeSourceProjectionRequest,
    FingerprintCodeSourceProjectionResponse,
    NormalizeCodeSourceProjectionRequest,
    NormalizeCodeSourceProjectionResponse,
    ResolveCodeSourceProjectionPackageDeltaRequest,
    ResolveCodeSourceProjectionPackageDeltaResponse,
    ValidateCodeSourceProjectionRequest,
    ValidateCodeSourceProjectionResponse,
)
from aware_types import JsonObject


class CodePackageManifestContract(BaseModel):
    """SDK-local manifest coordinates for package layout classification."""

    manifest_kind: str
    manifest_relative_path: str
    language: CodeLanguage
    package_manager_name: str | None = Field(default=None)
    package_manager_name_key: str | None = Field(default=None)
    dependency_names: list[str] = Field(default_factory=list)
    dependency_keys: list[str] = Field(default_factory=list)


class CodeSemanticPackageBindingContract(BaseModel):
    """SDK-local semantic package binding metadata kept out of service DTOs."""

    contract: str | None = Field(default=None)
    package_role: str | None = Field(default=None)
    provider_key: str | None = Field(default=None)
    package_name: str | None = Field(default=None)
    package_fqn: str | None = Field(default=None)
    semantic_owner: str | None = Field(default=None)
    semantic_contract_module: str | None = Field(default=None)
    semantic_package_family: str | None = Field(default=None)
    semantic_package_kind: str | None = Field(default=None)
    semantic_package_name: str | None = Field(default=None)
    semantic_projection_name: str | None = Field(default=None)
    semantic_provider_key: str | None = Field(default=None)
    semantic_root_kind: str | None = Field(default=None)
    workspace_manifest_kind: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodePackageConfigBindingContract(BaseModel):
    """SDK-local CodePackageConfig binding metadata for layout consumers."""

    code_package_config_id: UUID | str | None = Field(default=None)
    code_package_config_key: str | None = Field(default=None)
    manifest_kind: str | None = Field(default=None)
    package_role: str | None = Field(default=None)
    surface: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodePackageLayoutContract(_GeneratedCodePackageLayoutContract):
    """SDK facade over the generated layout DTO with local-only coordinates."""

    package_fqn: str | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    manifest: CodePackageManifestContract | None = Field(default=None)
    semantic_binding: CodeSemanticPackageBindingContract | None = Field(default=None)
    config_binding: CodePackageConfigBindingContract | None = Field(default=None)
    owned_file_paths: list[str] = Field(default_factory=list)


__all__ = [
    "ClassifyCodeSourceOwnershipRequest",
    "ClassifyCodeSourceOwnershipResponse",
    "CodeCapabilityBundleDescriptor",
    "CodeCapabilityExecutionPolicyDescriptor",
    "CodeCapabilityParticipationDescriptor",
    "CodeCapabilityProfileDescriptor",
    "CodeGeneratedMaterializationActionBinding",
    "CodeGeneratedMaterializationDeltaEntry",
    "CodeGeneratedMaterializationDeltaMode",
    "CodeGeneratedMaterializationDeltaRequest",
    "CodeGeneratedMaterializationDeltaResult",
    "CodeGeneratedMaterializationEventRef",
    "CodeGeneratedMaterializationSkippedTarget",
    "CodeGeneratedMaterializationTargetRef",
    "CodeGeneratedRendererAnchorRef",
    "CodeGeneratedRendererDeltaOperation",
    "CodeGeneratedRendererDeltaOperationKind",
    "CodeGrammarBackendDescriptor",
    "CodeGrammarAnchorBinding",
    "CodeGrammarAnchorBindingDirection",
    "CodeGrammarAnchorBindingResolutionStatus",
    "CodeGrammarAnchorCoverageDiagnostic",
    "CodeGrammarAnchorFixture",
    "CodeGrammarAnchorGraphChangeDraft",
    "CodeGrammarAnchorRenderEntry",
    "CodeGrammarAnchorRenderReplacement",
    "CodeGrammarAnchorRenderSpanTarget",
    "CodeGrammarAnchorRenderSource",
    "CodeGrammarAnchorRenderTargetKind",
    "CodeGrammarAnchorTextEvidence",
    "CodeGrammarAnchorTextTargetEvidence",
    "CodeGrammarProfile",
    "CodeGrammarProfileDiagnostic",
    "CodeGrammarProfileResolutionStatus",
    "CodeGrammarRuleBinding",
    "CodeGrammarRuleDeclaration",
    "CodeGraphAttributeSelector",
    "CodeGraphFieldSelector",
    "CodeLanguage",
    "CodePackageDelta",
    "CodePackageDeltaAuthorityKind",
    "CodePackageDeltaKind",
    "CodePackageDeltaPath",
    "CodePackageDeltaProducerRef",
    "CodePackageDeltaProduction",
    "CodePackageConfigBindingContract",
    "CodePackageLayoutContract",
    "CodePackageLayoutPathRole",
    "CodePackageManifestContract",
    "CodePackagePathRole",
    "CodeSemanticPackageBindingContract",
    "CodeNestedMemberInsertAnchor",
    "CodeNestedMemberInsertPosition",
    "CodeSemanticActionBinding",
    "CodeSemanticAnalysisChangePreview",
    "CodeSemanticAnalysisDependencyRequirement",
    "CodeSemanticAnalysisDiagnostic",
    "CodeSemanticArtifactLeafOwnershipDescriptor",
    "CodeSemanticContract",
    "CodeSemanticGeneratedCodePackageDeclaration",
    "CodeSemanticContractSpecDeclaration",
    "CodeSemanticContractSpecSection",
    "CodeSemanticGrammarRuleDescriptor",
    "CodeSemanticGrammarRuleFieldDescriptor",
    "CodeSemanticDelta",
    "CodeSemanticEvent",
    "CodeSemanticFunctionCallBinding",
    "CodeSemanticTypedOperation",
    "CodeSemanticManifestResolutionDescriptor",
    "CodeSemanticManifestResolutionMatch",
    "CodeSemanticMaterializationArtifactOutputDescriptor",
    "CodeSemanticMaterializationCodePackageDeltaOutputDescriptor",
    "CodeSemanticMaterializationExecutionContextDescriptor",
    "CodeSemanticMaterializationInputDescriptor",
    "CodeSemanticMaterializationPackageOutputDescriptor",
    "CodeSemanticMaterializationRuntimeContextDescriptor",
    "CodeSemanticMaterializationRuntimeDescriptor",
    "CodeSemanticMaterializationScopeDependency",
    "CodeSemanticPackageRoleDescriptor",
    "CodeSemanticProviderBinding",
    "CodeSemanticRuntimeProjectionPackageDescriptor",
    "CodeSemanticScopePackageRef",
    "CodeSemanticScopeResolution",
    "CodeSemanticSourceDeltaMeaningInput",
    "CodeSemanticSourceDeltaMeaningResolutionMode",
    "CodeSemanticSourceIndexRef",
    "CodeSemanticSourceMeaningBinding",
    "CodeSemanticSourceMeaningContract",
    "CodeSemanticSourceMeaningSource",
    "CodeSemanticSyntaxLaneDescriptor",
    "CodeSemanticWorkflowDescriptor",
    "CodeSemanticWorkflowInstructionDescriptor",
    "CodeSemanticWorkflowCoverageDiagnostic",
    "CodeSemanticWorkflowCoverageEntry",
    "CodeSemanticWorkflowCoverageStatus",
    "CodeSemanticWorkflowGrammarRuleEvidence",
    "CodeSemanticWorkflowGraphBindingCoverage",
    "CodeSectionDeltaEntry",
    "CodeSectionDeltaOperationKind",
    "CodeSectionDeltaSet",
    "CodeSectionRef",
    "CodeSegmentContentDomain",
    "CodeSegmentRef",
    "CodeSegmentRenderPolicy",
    "CodeSegmentRenderPolicyDiagnostic",
    "CodeSegmentRenderPolicyResolutionStatus",
    "CodeSourceOwnershipClassification",
    "CodeSourceOwnershipObservedPath",
    "CodeSourceOwnershipPackageBinding",
    "CodeSourceOwnershipPathMatch",
    "CodeSourceOwnershipRequest",
    "CodeSourceOwnershipResult",
    "CodeSourceProjectionActionBinding",
    "CodeSourceProjectionEventRef",
    "CodeSourceProjectionRequest",
    "CodeSourceProjectionResult",
    "CodeSourceProjectionSkippedEvent",
    "DescribeCodePackageLayoutRequest",
    "DescribeCodePackageLayoutResponse",
    "DescribeCodeSemanticContractRequest",
    "DescribeCodeSemanticContractResponse",
    "DiscoverCodePackageLayoutsRequest",
    "DiscoverCodePackageLayoutsResponse",
    "FindCodeSemanticManifestResolutionRequest",
    "FindCodeSemanticManifestResolutionResponse",
    "FingerprintCodeGeneratedMaterializationDeltaRequest",
    "FingerprintCodeGeneratedMaterializationDeltaResponse",
    "FingerprintCodePackageDeltaRequest",
    "FingerprintCodePackageDeltaResponse",
    "FingerprintCodeSectionDeltaRequest",
    "FingerprintCodeSectionDeltaResponse",
    "FingerprintCodeSourceProjectionRequest",
    "FingerprintCodeSourceProjectionResponse",
    "NormalizeCodePackageDeltaRequest",
    "NormalizeCodePackageDeltaResponse",
    "NormalizeCodeGeneratedMaterializationDeltaRequest",
    "NormalizeCodeGeneratedMaterializationDeltaResponse",
    "NormalizeCodeSectionDeltaRequest",
    "NormalizeCodeSectionDeltaResponse",
    "NormalizeCodeSemanticContractRequest",
    "NormalizeCodeSemanticContractResponse",
    "NormalizeCodeSourceProjectionRequest",
    "NormalizeCodeSourceProjectionResponse",
    "PreviewCodeSemanticAnalysisPackageDeltaRequest",
    "PreviewCodeSemanticAnalysisPackageDeltaResponse",
    "ResolveCodeGrammarProfileRequest",
    "ResolveCodeGrammarProfileResponse",
    "ResolveCodeGrammarAnchorBindingEvidenceRequest",
    "ResolveCodeGrammarAnchorBindingEvidenceResponse",
    "ResolveCodeGrammarAnchorRenderDeltaRequest",
    "ResolveCodeGrammarAnchorRenderDeltaResponse",
    "ResolveCodeGeneratedMaterializationPackageDeltaRequest",
    "ResolveCodeGeneratedMaterializationPackageDeltaResponse",
    "ResolveCodeSectionDeltaPackageDeltaRequest",
    "ResolveCodeSectionDeltaPackageDeltaResponse",
    "ResolveCodeSegmentRenderPolicyRequest",
    "ResolveCodeSegmentRenderPolicyResponse",
    "ResolveCodeSemanticSourceDeltaMeaningRequest",
    "ResolveCodeSemanticSourceDeltaMeaningResponse",
    "ResolveCodeSemanticSourceMeaningRequest",
    "ResolveCodeSemanticSourceMeaningResponse",
    "ResolveCodeSemanticWorkflowCoverageRequest",
    "ResolveCodeSemanticWorkflowCoverageResponse",
    "ResolveCodeSemanticScopeRequest",
    "ResolveCodeSemanticScopeResponse",
    "ResolveCodeSourceProjectionPackageDeltaRequest",
    "ResolveCodeSourceProjectionPackageDeltaResponse",
    "ValidateCodePackageLayoutRequest",
    "ValidateCodePackageLayoutResponse",
    "ValidateCodeGeneratedMaterializationDeltaRequest",
    "ValidateCodeGeneratedMaterializationDeltaResponse",
    "ValidateCodeGrammarAnchorBindingRequest",
    "ValidateCodeGrammarAnchorBindingResponse",
    "ValidateCodeSectionDeltaRequest",
    "ValidateCodeSectionDeltaResponse",
    "ValidateCodeSemanticContractRequest",
    "ValidateCodeSemanticContractResponse",
    "ValidateCodeSourceProjectionRequest",
    "ValidateCodeSourceProjectionResponse",
]
