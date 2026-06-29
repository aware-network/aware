from __future__ import annotations

# Standard
from functools import lru_cache
from typing import ClassVar
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class CodeServiceRequest(BaseModel):
    """Shared request envelope for Code service operations."""

    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "describe_package_layout": "aware_code_service_dto.code.features.package_layout.DescribeCodePackageLayoutRequest",
        "discover_code_package_layouts": "aware_code_service_dto.code.features.package_layout.DiscoverCodePackageLayoutsRequest",
        "validate_package_layout": "aware_code_service_dto.code.features.package_layout.ValidateCodePackageLayoutRequest",
        "classify_source_ownership": "aware_code_service_dto.code.features.source_ownership.ClassifyCodeSourceOwnershipRequest",
        "resolve_semantic_workflow_coverage": "aware_code_service_dto.code.features.semantic_workflow_coverage.ResolveCodeSemanticWorkflowCoverageRequest",
        "normalize_package_delta": "aware_code_service_dto.code.features.package_delta.NormalizeCodePackageDeltaRequest",
        "resolve_grammar_anchor_render_delta": "aware_code_service_dto.code.features.grammar_anchor_render_delta.ResolveCodeGrammarAnchorRenderDeltaRequest",
        "fingerprint_package_delta": "aware_code_service_dto.code.features.package_delta.FingerprintCodePackageDeltaRequest",
        "resolve_grammar_profile": "aware_code_service_dto.code.features.grammar_profile.ResolveCodeGrammarProfileRequest",
        "preview_semantic_analysis_package_delta": "aware_code_service_dto.code.features.semantic_analysis.PreviewCodeSemanticAnalysisPackageDeltaRequest",
        "validate_source_projection": "aware_code_service_dto.code.features.source_projection.ValidateCodeSourceProjectionRequest",
        "normalize_source_projection": "aware_code_service_dto.code.features.source_projection.NormalizeCodeSourceProjectionRequest",
        "resolve_semantic_source_meaning": "aware_code_service_dto.code.features.semantic_source_meaning.ResolveCodeSemanticSourceMeaningRequest",
        "fingerprint_source_projection": "aware_code_service_dto.code.features.source_projection.FingerprintCodeSourceProjectionRequest",
        "resolve_source_projection_package_delta": "aware_code_service_dto.code.features.source_projection.ResolveCodeSourceProjectionPackageDeltaRequest",
        "validate_grammar_anchor_binding": "aware_code_service_dto.code.features.grammar_anchor_binding.ValidateCodeGrammarAnchorBindingRequest",
        "resolve_semantic_source_delta_meaning": "aware_code_service_dto.code.features.semantic_source_meaning.ResolveCodeSemanticSourceDeltaMeaningRequest",
        "resolve_grammar_anchor_binding_evidence": "aware_code_service_dto.code.features.grammar_anchor_binding.ResolveCodeGrammarAnchorBindingEvidenceRequest",
        "validate_section_delta": "aware_code_service_dto.code.features.section_delta.ValidateCodeSectionDeltaRequest",
        "normalize_section_delta": "aware_code_service_dto.code.features.section_delta.NormalizeCodeSectionDeltaRequest",
        "fingerprint_section_delta": "aware_code_service_dto.code.features.section_delta.FingerprintCodeSectionDeltaRequest",
        "resolve_section_delta_package_delta": "aware_code_service_dto.code.features.section_delta.ResolveCodeSectionDeltaPackageDeltaRequest",
        "resolve_segment_render_policy": "aware_code_service_dto.code.features.section_delta.ResolveCodeSegmentRenderPolicyRequest",
        "validate_generated_materialization_delta": "aware_code_service_dto.code.features.generated_materialization_delta.ValidateCodeGeneratedMaterializationDeltaRequest",
        "normalize_generated_materialization_delta": "aware_code_service_dto.code.features.generated_materialization_delta.NormalizeCodeGeneratedMaterializationDeltaRequest",
        "fingerprint_generated_materialization_delta": "aware_code_service_dto.code.features.generated_materialization_delta.FingerprintCodeGeneratedMaterializationDeltaRequest",
        "resolve_generated_materialization_package_delta": "aware_code_service_dto.code.features.generated_materialization_delta.ResolveCodeGeneratedMaterializationPackageDeltaRequest",
        "describe_semantic_contract": "aware_code_service_dto.code.features.semantic_contract.DescribeCodeSemanticContractRequest",
        "validate_semantic_contract": "aware_code_service_dto.code.features.semantic_contract.ValidateCodeSemanticContractRequest",
        "normalize_semantic_contract": "aware_code_service_dto.code.features.semantic_contract.NormalizeCodeSemanticContractRequest",
        "find_manifest_resolution": "aware_code_service_dto.code.features.semantic_contract.FindCodeSemanticManifestResolutionRequest",
        "resolve_semantic_scope": "aware_code_service_dto.code.features.semantic_contract.ResolveCodeSemanticScopeRequest",
    }

    @staticmethod
    @lru_cache(maxsize=None)
    def _resolve_fqn(fqn: str):
        from importlib import import_module

        module_name, class_name = fqn.rsplit(".", 1)
        return getattr(import_module(module_name), class_name)

    @classmethod
    def parse(cls, v, *, strict: bool = False):
        if isinstance(v, cls):
            return v
        if isinstance(v, dict):
            tag = v.get(cls._DISCRIMINATOR_KEY)
            fqn = cls._TAG_TO_TYPE.get(tag)
            if fqn:
                model_cls = cls._resolve_fqn(fqn)
                return model_cls.model_validate(v)
            if strict:
                raise ValueError(f"Unknown {cls.__name__} tag: {tag!r}")
            return UnknownCodeServiceRequest.model_validate(v)
        return cls.model_validate(v)


class UnknownCodeServiceRequest(CodeServiceRequest):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class CodeServiceResponse(BaseModel):
    """Shared response envelope for Code service operations."""

    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    success: bool = Field(default=True)
    info: str | None = Field(default=None)
    error: str | None = Field(default=None)
    warnings: list[str] = Field(default_factory=list)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "describe_package_layout": "aware_code_service_dto.code.features.package_layout.DescribeCodePackageLayoutResponse",
        "discover_code_package_layouts": "aware_code_service_dto.code.features.package_layout.DiscoverCodePackageLayoutsResponse",
        "classify_source_ownership": "aware_code_service_dto.code.features.source_ownership.ClassifyCodeSourceOwnershipResponse",
        "validate_package_layout": "aware_code_service_dto.code.features.package_layout.ValidateCodePackageLayoutResponse",
        "resolve_semantic_workflow_coverage": "aware_code_service_dto.code.features.semantic_workflow_coverage.ResolveCodeSemanticWorkflowCoverageResponse",
        "resolve_grammar_anchor_render_delta": "aware_code_service_dto.code.features.grammar_anchor_render_delta.ResolveCodeGrammarAnchorRenderDeltaResponse",
        "normalize_package_delta": "aware_code_service_dto.code.features.package_delta.NormalizeCodePackageDeltaResponse",
        "fingerprint_package_delta": "aware_code_service_dto.code.features.package_delta.FingerprintCodePackageDeltaResponse",
        "resolve_grammar_profile": "aware_code_service_dto.code.features.grammar_profile.ResolveCodeGrammarProfileResponse",
        "preview_semantic_analysis_package_delta": "aware_code_service_dto.code.features.semantic_analysis.PreviewCodeSemanticAnalysisPackageDeltaResponse",
        "resolve_semantic_source_meaning": "aware_code_service_dto.code.features.semantic_source_meaning.ResolveCodeSemanticSourceMeaningResponse",
        "validate_source_projection": "aware_code_service_dto.code.features.source_projection.ValidateCodeSourceProjectionResponse",
        "resolve_semantic_source_delta_meaning": "aware_code_service_dto.code.features.semantic_source_meaning.ResolveCodeSemanticSourceDeltaMeaningResponse",
        "normalize_source_projection": "aware_code_service_dto.code.features.source_projection.NormalizeCodeSourceProjectionResponse",
        "validate_grammar_anchor_binding": "aware_code_service_dto.code.features.grammar_anchor_binding.ValidateCodeGrammarAnchorBindingResponse",
        "fingerprint_source_projection": "aware_code_service_dto.code.features.source_projection.FingerprintCodeSourceProjectionResponse",
        "resolve_grammar_anchor_binding_evidence": "aware_code_service_dto.code.features.grammar_anchor_binding.ResolveCodeGrammarAnchorBindingEvidenceResponse",
        "resolve_source_projection_package_delta": "aware_code_service_dto.code.features.source_projection.ResolveCodeSourceProjectionPackageDeltaResponse",
        "validate_section_delta": "aware_code_service_dto.code.features.section_delta.ValidateCodeSectionDeltaResponse",
        "normalize_section_delta": "aware_code_service_dto.code.features.section_delta.NormalizeCodeSectionDeltaResponse",
        "fingerprint_section_delta": "aware_code_service_dto.code.features.section_delta.FingerprintCodeSectionDeltaResponse",
        "resolve_section_delta_package_delta": "aware_code_service_dto.code.features.section_delta.ResolveCodeSectionDeltaPackageDeltaResponse",
        "resolve_segment_render_policy": "aware_code_service_dto.code.features.section_delta.ResolveCodeSegmentRenderPolicyResponse",
        "validate_generated_materialization_delta": "aware_code_service_dto.code.features.generated_materialization_delta.ValidateCodeGeneratedMaterializationDeltaResponse",
        "normalize_generated_materialization_delta": "aware_code_service_dto.code.features.generated_materialization_delta.NormalizeCodeGeneratedMaterializationDeltaResponse",
        "fingerprint_generated_materialization_delta": "aware_code_service_dto.code.features.generated_materialization_delta.FingerprintCodeGeneratedMaterializationDeltaResponse",
        "resolve_generated_materialization_package_delta": "aware_code_service_dto.code.features.generated_materialization_delta.ResolveCodeGeneratedMaterializationPackageDeltaResponse",
        "describe_semantic_contract": "aware_code_service_dto.code.features.semantic_contract.DescribeCodeSemanticContractResponse",
        "validate_semantic_contract": "aware_code_service_dto.code.features.semantic_contract.ValidateCodeSemanticContractResponse",
        "normalize_semantic_contract": "aware_code_service_dto.code.features.semantic_contract.NormalizeCodeSemanticContractResponse",
        "find_manifest_resolution": "aware_code_service_dto.code.features.semantic_contract.FindCodeSemanticManifestResolutionResponse",
        "resolve_semantic_scope": "aware_code_service_dto.code.features.semantic_contract.ResolveCodeSemanticScopeResponse",
    }

    @staticmethod
    @lru_cache(maxsize=None)
    def _resolve_fqn(fqn: str):
        from importlib import import_module

        module_name, class_name = fqn.rsplit(".", 1)
        return getattr(import_module(module_name), class_name)

    @classmethod
    def parse(cls, v, *, strict: bool = False):
        if isinstance(v, cls):
            return v
        if isinstance(v, dict):
            tag = v.get(cls._DISCRIMINATOR_KEY)
            fqn = cls._TAG_TO_TYPE.get(tag)
            if fqn:
                model_cls = cls._resolve_fqn(fqn)
                return model_cls.model_validate(v)
            if strict:
                raise ValueError(f"Unknown {cls.__name__} tag: {tag!r}")
            return UnknownCodeServiceResponse.model_validate(v)
        return cls.model_validate(v)


class UnknownCodeServiceResponse(CodeServiceResponse):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}
