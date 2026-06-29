# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API client bindings for Python SDK wrappers.
from __future__ import annotations

from typing import Final

from aware_api.interface import LoadedApiInterface, load_api_interface_spec_payload
from aware_api.invocation import LoadedApiInvocationManifest, load_api_invocation_manifest_payload

API_PACKAGE_NAME: Final[str] = "code-service-api"
API_FQN_PREFIX: Final[str] = "aware_code_service_api"

API_INTERFACE_SPEC: Final[LoadedApiInterface] = load_api_interface_spec_payload(
    {
        "apis": [
            {
                "capabilities": [
                    {
                        "endpoints": [
                            {
                                "description": "Fingerprint renderer-generated "
                                "materialization delta request and "
                                "result evidence for preview and "
                                "receipt correlation.",
                                "discriminant": "code.generated_materialization_delta.fingerprint",
                                "name": "fingerprint",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.FingerprintCodeGeneratedMaterializationDeltaRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.FingerprintCodeGeneratedMaterializationDeltaResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "description": "Normalize renderer-generated "
                                "materialization delta request and "
                                "result evidence into stable Code API "
                                "DTO shape.",
                                "discriminant": "code.generated_materialization_delta.normalize",
                                "name": "normalize",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.NormalizeCodeGeneratedMaterializationDeltaRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.NormalizeCodeGeneratedMaterializationDeltaResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "description": "Resolve renderer-generated "
                                "materialization delta result evidence "
                                "into a CodePackageDelta.",
                                "discriminant": "code.generated_materialization_delta.resolve_package_delta",
                                "name": "resolve_package_delta",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeGeneratedMaterializationPackageDeltaRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeGeneratedMaterializationPackageDeltaResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "description": "Validate renderer-generated "
                                "materialization delta request and "
                                "result evidence before provider or "
                                "consumer use.",
                                "discriminant": "code.generated_materialization_delta.validate",
                                "name": "validate",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ValidateCodeGeneratedMaterializationDeltaRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ValidateCodeGeneratedMaterializationDeltaResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                        ],
                        "name": "generated_materialization_delta",
                        "source_path": "bindings/code.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Resolve grammar anchor fixtures into "
                                "byte evidence and read-only graph/text "
                                "drafts.",
                                "discriminant": "code.grammar_anchor_binding.resolve_evidence",
                                "name": "resolve_evidence",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeGrammarAnchorBindingEvidenceRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeGrammarAnchorBindingEvidenceResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "description": "Validate grammar rule-field anchors "
                                "that bind parsed source text to graph "
                                "selectors.",
                                "discriminant": "code.grammar_anchor_binding.validate",
                                "name": "validate",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ValidateCodeGrammarAnchorBindingRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ValidateCodeGrammarAnchorBindingResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                        ],
                        "name": "grammar_anchor_binding",
                        "source_path": "bindings/code.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Resolve grammar-anchor graph-to-source "
                                "replacements into guarded Code package "
                                "deltas.",
                                "discriminant": "code.grammar_anchor_render_delta.resolve_delta",
                                "name": "resolve_delta",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeGrammarAnchorRenderDeltaRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeGrammarAnchorRenderDeltaResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            }
                        ],
                        "name": "grammar_anchor_render_delta",
                        "source_path": "bindings/code.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Resolve a Code-owned grammar profile "
                                "from semantic-contract syntax lanes.",
                                "discriminant": "code.grammar_profile.resolve",
                                "name": "resolve",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeGrammarProfileRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeGrammarProfileResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            }
                        ],
                        "name": "grammar_profile",
                        "source_path": "bindings/code.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Fingerprint one CodePackageDelta for "
                                "cache, status, materialization, and "
                                "receipt correlation.",
                                "discriminant": "code.package_delta.fingerprint",
                                "name": "fingerprint",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.FingerprintCodePackageDeltaRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.FingerprintCodePackageDeltaResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "description": "Normalize raw package delta input into "
                                "the public CodePackageDelta DTO shape.",
                                "discriminant": "code.package_delta.normalize",
                                "name": "normalize",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.NormalizeCodePackageDeltaRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.NormalizeCodePackageDeltaResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                        ],
                        "name": "package_delta",
                        "source_path": "bindings/code.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Describe package layout and path-role "
                                "contract truth for local filesystem "
                                "classification.",
                                "discriminant": "code.package_layout.describe",
                                "name": "describe",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.DescribeCodePackageLayoutRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.DescribeCodePackageLayoutResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "description": "Discover package layout contract truth " "for explicit manifest paths.",
                                "discriminant": "code.package_layout.discover",
                                "name": "discover",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.DiscoverCodePackageLayoutsRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.DiscoverCodePackageLayoutsResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "description": "Validate package layout and path-role "
                                "contract truth before local filesystem "
                                "classification.",
                                "discriminant": "code.package_layout.validate",
                                "name": "validate",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ValidateCodePackageLayoutRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ValidateCodePackageLayoutResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                        ],
                        "name": "package_layout",
                        "source_path": "bindings/code.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Fingerprint one CodeSectionDeltaSet "
                                "for semantic event and resolver "
                                "receipts.",
                                "discriminant": "code.section_delta.fingerprint",
                                "name": "fingerprint",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.FingerprintCodeSectionDeltaRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.FingerprintCodeSectionDeltaResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "description": "Normalize section/segment delta intent "
                                "into the public Code API DTO shape.",
                                "discriminant": "code.section_delta.normalize",
                                "name": "normalize",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.NormalizeCodeSectionDeltaRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.NormalizeCodeSectionDeltaResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "description": "Resolve one CodeSectionDeltaSet into a "
                                "CodePackageDelta through a Code "
                                "resolver.",
                                "discriminant": "code.section_delta.resolve_package_delta",
                                "name": "resolve_package_delta",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeSectionDeltaPackageDeltaRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeSectionDeltaPackageDeltaResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "description": "Resolve Code-owned segment render "
                                "policies for section-delta value "
                                "domains.",
                                "discriminant": "code.section_delta.resolve_render_policy",
                                "name": "resolve_render_policy",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeSegmentRenderPolicyRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeSegmentRenderPolicyResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "description": "Validate section/segment delta intent "
                                "before Code resolver execution.",
                                "discriminant": "code.section_delta.validate",
                                "name": "validate",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ValidateCodeSectionDeltaRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ValidateCodeSectionDeltaResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                        ],
                        "name": "section_delta",
                        "source_path": "bindings/code.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Preview provider-owned semantic "
                                "meaning for one CodePackageDelta "
                                "without materialization.",
                                "discriminant": "code.semantic_analysis.preview_package_delta",
                                "name": "preview_package_delta",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.PreviewCodeSemanticAnalysisPackageDeltaRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.PreviewCodeSemanticAnalysisPackageDeltaResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            }
                        ],
                        "name": "semantic_analysis",
                        "source_path": "bindings/code.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Describe one Code semantic contract by "
                                "provider, package, or package FQN.",
                                "discriminant": "code.semantic_contract.describe",
                                "name": "describe",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.DescribeCodeSemanticContractRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.DescribeCodeSemanticContractResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "description": "Find semantic manifest-resolution "
                                "descriptors through Code-owned "
                                "contract truth.",
                                "discriminant": "code.semantic_contract.find_manifest_resolution",
                                "name": "find_manifest_resolution",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.FindCodeSemanticManifestResolutionRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.FindCodeSemanticManifestResolutionResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "description": "Normalize a runtime-adapted semantic "
                                "contract into the public Code API DTO "
                                "shape.",
                                "discriminant": "code.semantic_contract.normalize",
                                "name": "normalize",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.NormalizeCodeSemanticContractRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.NormalizeCodeSemanticContractResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "description": "Resolve provider-owned semantic scope "
                                "through the Code-owned semantic scope "
                                "registry.",
                                "discriminant": "code.semantic_contract.resolve_semantic_scope",
                                "name": "resolve_semantic_scope",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeSemanticScopeRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeSemanticScopeResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "description": "Validate an externally supplied Code "
                                "semantic contract DTO before local or "
                                "remote use.",
                                "discriminant": "code.semantic_contract.validate",
                                "name": "validate",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ValidateCodeSemanticContractRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ValidateCodeSemanticContractResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                        ],
                        "name": "semantic_contract",
                        "source_path": "bindings/code.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Resolve declarative source meaning "
                                "through Code-owned grammar source "
                                "indexes.",
                                "discriminant": "code.semantic_source_meaning.resolve",
                                "name": "resolve",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeSemanticSourceMeaningRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeSemanticSourceMeaningResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "description": "Resolve declarative source meaning "
                                "from CodePackageDelta plus explicit "
                                "baseline context.",
                                "discriminant": "code.semantic_source_meaning.resolve_delta",
                                "name": "resolve_delta",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeSemanticSourceDeltaMeaningRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeSemanticSourceDeltaMeaningResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                        ],
                        "name": "semantic_source_meaning",
                        "source_path": "bindings/code.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Resolve Code-owned semantic workflow "
                                "grammar/source/graph-binding coverage.",
                                "discriminant": "code.semantic_workflow_coverage.resolve",
                                "name": "resolve",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeSemanticWorkflowCoverageRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeSemanticWorkflowCoverageResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            }
                        ],
                        "name": "semantic_workflow_coverage",
                        "source_path": "bindings/code.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Classify observed paths against "
                                "package ownership boundaries through "
                                "Code-owned rules.",
                                "discriminant": "code.source_ownership.classify",
                                "name": "classify",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ClassifyCodeSourceOwnershipRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ClassifyCodeSourceOwnershipResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            }
                        ],
                        "name": "source_ownership",
                        "source_path": "bindings/code.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Fingerprint semantic source-projection "
                                "request and result evidence for "
                                "preview and receipt correlation.",
                                "discriminant": "code.source_projection.fingerprint",
                                "name": "fingerprint",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.FingerprintCodeSourceProjectionRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.FingerprintCodeSourceProjectionResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "description": "Normalize semantic source-projection "
                                "request and result evidence into "
                                "stable Code API DTO shape.",
                                "discriminant": "code.source_projection.normalize",
                                "name": "normalize",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.NormalizeCodeSourceProjectionRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.NormalizeCodeSourceProjectionResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "description": "Resolve provider-produced "
                                "source-projection result evidence into "
                                "a CodePackageDelta.",
                                "discriminant": "code.source_projection.resolve_package_delta",
                                "name": "resolve_package_delta",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeSourceProjectionPackageDeltaRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeSourceProjectionPackageDeltaResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "description": "Validate semantic source-projection "
                                "request and result evidence before "
                                "provider or consumer use.",
                                "discriminant": "code.source_projection.validate",
                                "name": "validate",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ValidateCodeSourceProjectionRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ValidateCodeSourceProjectionResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                        ],
                        "name": "source_projection",
                        "source_path": "bindings/code.apis.aware",
                    },
                ],
                "name": "code",
                "source_path": "bindings/code.apis.aware",
            }
        ],
        "fqn_prefix": "aware_code_service_api",
        "package_name": "code-service-api",
        "schema_version": 1,
    }
)

API_INVOCATION_MANIFEST: Final[LoadedApiInvocationManifest] = load_api_invocation_manifest_payload(
    {
        "apis": [
            {
                "capabilities": [
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Fingerprint renderer-generated "
                                "materialization delta request and "
                                "result evidence for preview and "
                                "receipt correlation.",
                                "discriminant": "code.generated_materialization_delta.fingerprint",
                                "endpoint_ref": "code.generated_materialization_delta.fingerprint",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "fingerprint",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.FingerprintCodeGeneratedMaterializationDeltaRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.generated_materialization_delta.FingerprintCodeGeneratedMaterializationDeltaRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.FingerprintCodeGeneratedMaterializationDeltaResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.generated_materialization_delta.FingerprintCodeGeneratedMaterializationDeltaResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Normalize renderer-generated "
                                "materialization delta request and "
                                "result evidence into stable Code API "
                                "DTO shape.",
                                "discriminant": "code.generated_materialization_delta.normalize",
                                "endpoint_ref": "code.generated_materialization_delta.normalize",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "normalize",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.NormalizeCodeGeneratedMaterializationDeltaRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.generated_materialization_delta.NormalizeCodeGeneratedMaterializationDeltaRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.NormalizeCodeGeneratedMaterializationDeltaResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.generated_materialization_delta.NormalizeCodeGeneratedMaterializationDeltaResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve renderer-generated "
                                "materialization delta result evidence "
                                "into a CodePackageDelta.",
                                "discriminant": "code.generated_materialization_delta.resolve_package_delta",
                                "endpoint_ref": "code.generated_materialization_delta.resolve_package_delta",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_package_delta",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeGeneratedMaterializationPackageDeltaRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.generated_materialization_delta.ResolveCodeGeneratedMaterializationPackageDeltaRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeGeneratedMaterializationPackageDeltaResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.generated_materialization_delta.ResolveCodeGeneratedMaterializationPackageDeltaResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Validate renderer-generated "
                                "materialization delta request and "
                                "result evidence before provider or "
                                "consumer use.",
                                "discriminant": "code.generated_materialization_delta.validate",
                                "endpoint_ref": "code.generated_materialization_delta.validate",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "validate",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ValidateCodeGeneratedMaterializationDeltaRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.generated_materialization_delta.ValidateCodeGeneratedMaterializationDeltaRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ValidateCodeGeneratedMaterializationDeltaResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.generated_materialization_delta.ValidateCodeGeneratedMaterializationDeltaResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                        ],
                        "name": "generated_materialization_delta",
                        "source_path": "bindings/code.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve grammar anchor fixtures into "
                                "byte evidence and read-only graph/text "
                                "drafts.",
                                "discriminant": "code.grammar_anchor_binding.resolve_evidence",
                                "endpoint_ref": "code.grammar_anchor_binding.resolve_evidence",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_evidence",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeGrammarAnchorBindingEvidenceRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.grammar_anchor_binding.ResolveCodeGrammarAnchorBindingEvidenceRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeGrammarAnchorBindingEvidenceResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.grammar_anchor_binding.ResolveCodeGrammarAnchorBindingEvidenceResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Validate grammar rule-field anchors "
                                "that bind parsed source text to graph "
                                "selectors.",
                                "discriminant": "code.grammar_anchor_binding.validate",
                                "endpoint_ref": "code.grammar_anchor_binding.validate",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "validate",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ValidateCodeGrammarAnchorBindingRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.grammar_anchor_binding.ValidateCodeGrammarAnchorBindingRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ValidateCodeGrammarAnchorBindingResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.grammar_anchor_binding.ValidateCodeGrammarAnchorBindingResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                        ],
                        "name": "grammar_anchor_binding",
                        "source_path": "bindings/code.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve grammar-anchor graph-to-source "
                                "replacements into guarded Code package "
                                "deltas.",
                                "discriminant": "code.grammar_anchor_render_delta.resolve_delta",
                                "endpoint_ref": "code.grammar_anchor_render_delta.resolve_delta",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_delta",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeGrammarAnchorRenderDeltaRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.grammar_anchor_render_delta.ResolveCodeGrammarAnchorRenderDeltaRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeGrammarAnchorRenderDeltaResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.grammar_anchor_render_delta.ResolveCodeGrammarAnchorRenderDeltaResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            }
                        ],
                        "name": "grammar_anchor_render_delta",
                        "source_path": "bindings/code.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve a Code-owned grammar profile "
                                "from semantic-contract syntax lanes.",
                                "discriminant": "code.grammar_profile.resolve",
                                "endpoint_ref": "code.grammar_profile.resolve",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeGrammarProfileRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.grammar_profile.ResolveCodeGrammarProfileRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeGrammarProfileResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.grammar_profile.ResolveCodeGrammarProfileResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            }
                        ],
                        "name": "grammar_profile",
                        "source_path": "bindings/code.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Fingerprint one CodePackageDelta for "
                                "cache, status, materialization, and "
                                "receipt correlation.",
                                "discriminant": "code.package_delta.fingerprint",
                                "endpoint_ref": "code.package_delta.fingerprint",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "fingerprint",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.FingerprintCodePackageDeltaRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.package_delta.FingerprintCodePackageDeltaRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.FingerprintCodePackageDeltaResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.package_delta.FingerprintCodePackageDeltaResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Normalize raw package delta input into "
                                "the public CodePackageDelta DTO shape.",
                                "discriminant": "code.package_delta.normalize",
                                "endpoint_ref": "code.package_delta.normalize",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "normalize",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.NormalizeCodePackageDeltaRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.package_delta.NormalizeCodePackageDeltaRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.NormalizeCodePackageDeltaResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.package_delta.NormalizeCodePackageDeltaResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                        ],
                        "name": "package_delta",
                        "source_path": "bindings/code.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Describe package layout and path-role "
                                "contract truth for local filesystem "
                                "classification.",
                                "discriminant": "code.package_layout.describe",
                                "endpoint_ref": "code.package_layout.describe",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "describe",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.DescribeCodePackageLayoutRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.package_layout.DescribeCodePackageLayoutRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.DescribeCodePackageLayoutResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.package_layout.DescribeCodePackageLayoutResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Discover package layout contract truth " "for explicit manifest paths.",
                                "discriminant": "code.package_layout.discover",
                                "endpoint_ref": "code.package_layout.discover",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "discover",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.DiscoverCodePackageLayoutsRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.package_layout.DiscoverCodePackageLayoutsRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.DiscoverCodePackageLayoutsResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.package_layout.DiscoverCodePackageLayoutsResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Validate package layout and path-role "
                                "contract truth before local filesystem "
                                "classification.",
                                "discriminant": "code.package_layout.validate",
                                "endpoint_ref": "code.package_layout.validate",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "validate",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ValidateCodePackageLayoutRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.package_layout.ValidateCodePackageLayoutRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ValidateCodePackageLayoutResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.package_layout.ValidateCodePackageLayoutResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                        ],
                        "name": "package_layout",
                        "source_path": "bindings/code.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Fingerprint one CodeSectionDeltaSet "
                                "for semantic event and resolver "
                                "receipts.",
                                "discriminant": "code.section_delta.fingerprint",
                                "endpoint_ref": "code.section_delta.fingerprint",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "fingerprint",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.FingerprintCodeSectionDeltaRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.section_delta.FingerprintCodeSectionDeltaRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.FingerprintCodeSectionDeltaResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.section_delta.FingerprintCodeSectionDeltaResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Normalize section/segment delta intent "
                                "into the public Code API DTO shape.",
                                "discriminant": "code.section_delta.normalize",
                                "endpoint_ref": "code.section_delta.normalize",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "normalize",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.NormalizeCodeSectionDeltaRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.section_delta.NormalizeCodeSectionDeltaRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.NormalizeCodeSectionDeltaResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.section_delta.NormalizeCodeSectionDeltaResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve one CodeSectionDeltaSet into a "
                                "CodePackageDelta through a Code "
                                "resolver.",
                                "discriminant": "code.section_delta.resolve_package_delta",
                                "endpoint_ref": "code.section_delta.resolve_package_delta",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_package_delta",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeSectionDeltaPackageDeltaRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.section_delta.ResolveCodeSectionDeltaPackageDeltaRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeSectionDeltaPackageDeltaResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.section_delta.ResolveCodeSectionDeltaPackageDeltaResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve Code-owned segment render "
                                "policies for section-delta value "
                                "domains.",
                                "discriminant": "code.section_delta.resolve_render_policy",
                                "endpoint_ref": "code.section_delta.resolve_render_policy",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_render_policy",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeSegmentRenderPolicyRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.section_delta.ResolveCodeSegmentRenderPolicyRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeSegmentRenderPolicyResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.section_delta.ResolveCodeSegmentRenderPolicyResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Validate section/segment delta intent "
                                "before Code resolver execution.",
                                "discriminant": "code.section_delta.validate",
                                "endpoint_ref": "code.section_delta.validate",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "validate",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ValidateCodeSectionDeltaRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.section_delta.ValidateCodeSectionDeltaRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ValidateCodeSectionDeltaResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.section_delta.ValidateCodeSectionDeltaResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                        ],
                        "name": "section_delta",
                        "source_path": "bindings/code.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Preview provider-owned semantic "
                                "meaning for one CodePackageDelta "
                                "without materialization.",
                                "discriminant": "code.semantic_analysis.preview_package_delta",
                                "endpoint_ref": "code.semantic_analysis.preview_package_delta",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "preview_package_delta",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.PreviewCodeSemanticAnalysisPackageDeltaRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.semantic_analysis.PreviewCodeSemanticAnalysisPackageDeltaRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.PreviewCodeSemanticAnalysisPackageDeltaResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.semantic_analysis.PreviewCodeSemanticAnalysisPackageDeltaResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            }
                        ],
                        "name": "semantic_analysis",
                        "source_path": "bindings/code.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Describe one Code semantic contract by "
                                "provider, package, or package FQN.",
                                "discriminant": "code.semantic_contract.describe",
                                "endpoint_ref": "code.semantic_contract.describe",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "describe",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.DescribeCodeSemanticContractRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.semantic_contract.DescribeCodeSemanticContractRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.DescribeCodeSemanticContractResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.semantic_contract.DescribeCodeSemanticContractResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Find semantic manifest-resolution "
                                "descriptors through Code-owned "
                                "contract truth.",
                                "discriminant": "code.semantic_contract.find_manifest_resolution",
                                "endpoint_ref": "code.semantic_contract.find_manifest_resolution",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "find_manifest_resolution",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.FindCodeSemanticManifestResolutionRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.semantic_contract.FindCodeSemanticManifestResolutionRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.FindCodeSemanticManifestResolutionResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.semantic_contract.FindCodeSemanticManifestResolutionResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Normalize a runtime-adapted semantic "
                                "contract into the public Code API DTO "
                                "shape.",
                                "discriminant": "code.semantic_contract.normalize",
                                "endpoint_ref": "code.semantic_contract.normalize",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "normalize",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.NormalizeCodeSemanticContractRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.semantic_contract.NormalizeCodeSemanticContractRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.NormalizeCodeSemanticContractResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.semantic_contract.NormalizeCodeSemanticContractResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve provider-owned semantic scope "
                                "through the Code-owned semantic scope "
                                "registry.",
                                "discriminant": "code.semantic_contract.resolve_semantic_scope",
                                "endpoint_ref": "code.semantic_contract.resolve_semantic_scope",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_semantic_scope",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeSemanticScopeRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.semantic_contract.ResolveCodeSemanticScopeRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeSemanticScopeResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.semantic_contract.ResolveCodeSemanticScopeResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Validate an externally supplied Code "
                                "semantic contract DTO before local or "
                                "remote use.",
                                "discriminant": "code.semantic_contract.validate",
                                "endpoint_ref": "code.semantic_contract.validate",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "validate",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ValidateCodeSemanticContractRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.semantic_contract.ValidateCodeSemanticContractRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ValidateCodeSemanticContractResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.semantic_contract.ValidateCodeSemanticContractResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                        ],
                        "name": "semantic_contract",
                        "source_path": "bindings/code.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve declarative source meaning "
                                "through Code-owned grammar source "
                                "indexes.",
                                "discriminant": "code.semantic_source_meaning.resolve",
                                "endpoint_ref": "code.semantic_source_meaning.resolve",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeSemanticSourceMeaningRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.semantic_source_meaning.ResolveCodeSemanticSourceMeaningRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeSemanticSourceMeaningResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.semantic_source_meaning.ResolveCodeSemanticSourceMeaningResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve declarative source meaning "
                                "from CodePackageDelta plus explicit "
                                "baseline context.",
                                "discriminant": "code.semantic_source_meaning.resolve_delta",
                                "endpoint_ref": "code.semantic_source_meaning.resolve_delta",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_delta",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeSemanticSourceDeltaMeaningRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.semantic_source_meaning.ResolveCodeSemanticSourceDeltaMeaningRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeSemanticSourceDeltaMeaningResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.semantic_source_meaning.ResolveCodeSemanticSourceDeltaMeaningResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                        ],
                        "name": "semantic_source_meaning",
                        "source_path": "bindings/code.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve Code-owned semantic workflow "
                                "grammar/source/graph-binding coverage.",
                                "discriminant": "code.semantic_workflow_coverage.resolve",
                                "endpoint_ref": "code.semantic_workflow_coverage.resolve",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeSemanticWorkflowCoverageRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.semantic_workflow_coverage.ResolveCodeSemanticWorkflowCoverageRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeSemanticWorkflowCoverageResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.semantic_workflow_coverage.ResolveCodeSemanticWorkflowCoverageResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            }
                        ],
                        "name": "semantic_workflow_coverage",
                        "source_path": "bindings/code.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Classify observed paths against "
                                "package ownership boundaries through "
                                "Code-owned rules.",
                                "discriminant": "code.source_ownership.classify",
                                "endpoint_ref": "code.source_ownership.classify",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "classify",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ClassifyCodeSourceOwnershipRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.source_ownership.ClassifyCodeSourceOwnershipRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ClassifyCodeSourceOwnershipResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.source_ownership.ClassifyCodeSourceOwnershipResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            }
                        ],
                        "name": "source_ownership",
                        "source_path": "bindings/code.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Fingerprint semantic source-projection "
                                "request and result evidence for "
                                "preview and receipt correlation.",
                                "discriminant": "code.source_projection.fingerprint",
                                "endpoint_ref": "code.source_projection.fingerprint",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "fingerprint",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.FingerprintCodeSourceProjectionRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.source_projection.FingerprintCodeSourceProjectionRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.FingerprintCodeSourceProjectionResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.source_projection.FingerprintCodeSourceProjectionResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Normalize semantic source-projection "
                                "request and result evidence into "
                                "stable Code API DTO shape.",
                                "discriminant": "code.source_projection.normalize",
                                "endpoint_ref": "code.source_projection.normalize",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "normalize",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.NormalizeCodeSourceProjectionRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.source_projection.NormalizeCodeSourceProjectionRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.NormalizeCodeSourceProjectionResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.source_projection.NormalizeCodeSourceProjectionResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve provider-produced "
                                "source-projection result evidence into "
                                "a CodePackageDelta.",
                                "discriminant": "code.source_projection.resolve_package_delta",
                                "endpoint_ref": "code.source_projection.resolve_package_delta",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_package_delta",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeSourceProjectionPackageDeltaRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.source_projection.ResolveCodeSourceProjectionPackageDeltaRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodeSourceProjectionPackageDeltaResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.source_projection.ResolveCodeSourceProjectionPackageDeltaResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Validate semantic source-projection "
                                "request and result evidence before "
                                "provider or consumer use.",
                                "discriminant": "code.source_projection.validate",
                                "endpoint_ref": "code.source_projection.validate",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "validate",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ValidateCodeSourceProjectionRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.source_projection.ValidateCodeSourceProjectionRequest",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ValidateCodeSourceProjectionResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.source_projection.ValidateCodeSourceProjectionResponse",
                                    "source_path": "bindings/code.apis.aware",
                                },
                                "source_path": "bindings/code.apis.aware",
                            },
                        ],
                        "name": "source_projection",
                        "source_path": "bindings/code.apis.aware",
                    },
                ],
                "name": "code",
                "source_path": "bindings/code.apis.aware",
            }
        ],
        "fqn_prefix": "aware_code_service_api",
        "package_name": "code-service-api",
        "schema_version": 1,
    }
)

CODE__GENERATED_MATERIALIZATION_DELTA__FINGERPRINT_ENDPOINT_REF: Final[str] = (
    "code.generated_materialization_delta.fingerprint"
)
CODE__GENERATED_MATERIALIZATION_DELTA__NORMALIZE_ENDPOINT_REF: Final[str] = (
    "code.generated_materialization_delta.normalize"
)
CODE__GENERATED_MATERIALIZATION_DELTA__RESOLVE_PACKAGE_DELTA_ENDPOINT_REF: Final[str] = (
    "code.generated_materialization_delta.resolve_package_delta"
)
CODE__GENERATED_MATERIALIZATION_DELTA__VALIDATE_ENDPOINT_REF: Final[str] = (
    "code.generated_materialization_delta.validate"
)
CODE__GRAMMAR_ANCHOR_BINDING__RESOLVE_EVIDENCE_ENDPOINT_REF: Final[str] = "code.grammar_anchor_binding.resolve_evidence"
CODE__GRAMMAR_ANCHOR_BINDING__VALIDATE_ENDPOINT_REF: Final[str] = "code.grammar_anchor_binding.validate"
CODE__GRAMMAR_ANCHOR_RENDER_DELTA__RESOLVE_DELTA_ENDPOINT_REF: Final[str] = (
    "code.grammar_anchor_render_delta.resolve_delta"
)
CODE__GRAMMAR_PROFILE__RESOLVE_ENDPOINT_REF: Final[str] = "code.grammar_profile.resolve"
CODE__PACKAGE_DELTA__FINGERPRINT_ENDPOINT_REF: Final[str] = "code.package_delta.fingerprint"
CODE__PACKAGE_DELTA__NORMALIZE_ENDPOINT_REF: Final[str] = "code.package_delta.normalize"
CODE__PACKAGE_LAYOUT__DESCRIBE_ENDPOINT_REF: Final[str] = "code.package_layout.describe"
CODE__PACKAGE_LAYOUT__DISCOVER_ENDPOINT_REF: Final[str] = "code.package_layout.discover"
CODE__PACKAGE_LAYOUT__VALIDATE_ENDPOINT_REF: Final[str] = "code.package_layout.validate"
CODE__SECTION_DELTA__FINGERPRINT_ENDPOINT_REF: Final[str] = "code.section_delta.fingerprint"
CODE__SECTION_DELTA__NORMALIZE_ENDPOINT_REF: Final[str] = "code.section_delta.normalize"
CODE__SECTION_DELTA__RESOLVE_PACKAGE_DELTA_ENDPOINT_REF: Final[str] = "code.section_delta.resolve_package_delta"
CODE__SECTION_DELTA__RESOLVE_RENDER_POLICY_ENDPOINT_REF: Final[str] = "code.section_delta.resolve_render_policy"
CODE__SECTION_DELTA__VALIDATE_ENDPOINT_REF: Final[str] = "code.section_delta.validate"
CODE__SEMANTIC_ANALYSIS__PREVIEW_PACKAGE_DELTA_ENDPOINT_REF: Final[str] = "code.semantic_analysis.preview_package_delta"
CODE__SEMANTIC_CONTRACT__DESCRIBE_ENDPOINT_REF: Final[str] = "code.semantic_contract.describe"
CODE__SEMANTIC_CONTRACT__FIND_MANIFEST_RESOLUTION_ENDPOINT_REF: Final[str] = (
    "code.semantic_contract.find_manifest_resolution"
)
CODE__SEMANTIC_CONTRACT__NORMALIZE_ENDPOINT_REF: Final[str] = "code.semantic_contract.normalize"
CODE__SEMANTIC_CONTRACT__RESOLVE_SEMANTIC_SCOPE_ENDPOINT_REF: Final[str] = (
    "code.semantic_contract.resolve_semantic_scope"
)
CODE__SEMANTIC_CONTRACT__VALIDATE_ENDPOINT_REF: Final[str] = "code.semantic_contract.validate"
CODE__SEMANTIC_SOURCE_MEANING__RESOLVE_DELTA_ENDPOINT_REF: Final[str] = "code.semantic_source_meaning.resolve_delta"
CODE__SEMANTIC_SOURCE_MEANING__RESOLVE_ENDPOINT_REF: Final[str] = "code.semantic_source_meaning.resolve"
CODE__SEMANTIC_WORKFLOW_COVERAGE__RESOLVE_ENDPOINT_REF: Final[str] = "code.semantic_workflow_coverage.resolve"
CODE__SOURCE_OWNERSHIP__CLASSIFY_ENDPOINT_REF: Final[str] = "code.source_ownership.classify"
CODE__SOURCE_PROJECTION__FINGERPRINT_ENDPOINT_REF: Final[str] = "code.source_projection.fingerprint"
CODE__SOURCE_PROJECTION__NORMALIZE_ENDPOINT_REF: Final[str] = "code.source_projection.normalize"
CODE__SOURCE_PROJECTION__RESOLVE_PACKAGE_DELTA_ENDPOINT_REF: Final[str] = "code.source_projection.resolve_package_delta"
CODE__SOURCE_PROJECTION__VALIDATE_ENDPOINT_REF: Final[str] = "code.source_projection.validate"

ENDPOINT_REF_BY_NAME: Final[dict[str, str]] = {
    "code.generated_materialization_delta.fingerprint": CODE__GENERATED_MATERIALIZATION_DELTA__FINGERPRINT_ENDPOINT_REF,
    "code.generated_materialization_delta.normalize": CODE__GENERATED_MATERIALIZATION_DELTA__NORMALIZE_ENDPOINT_REF,
    "code.generated_materialization_delta.resolve_package_delta": CODE__GENERATED_MATERIALIZATION_DELTA__RESOLVE_PACKAGE_DELTA_ENDPOINT_REF,
    "code.generated_materialization_delta.validate": CODE__GENERATED_MATERIALIZATION_DELTA__VALIDATE_ENDPOINT_REF,
    "code.grammar_anchor_binding.resolve_evidence": CODE__GRAMMAR_ANCHOR_BINDING__RESOLVE_EVIDENCE_ENDPOINT_REF,
    "code.grammar_anchor_binding.validate": CODE__GRAMMAR_ANCHOR_BINDING__VALIDATE_ENDPOINT_REF,
    "code.grammar_anchor_render_delta.resolve_delta": CODE__GRAMMAR_ANCHOR_RENDER_DELTA__RESOLVE_DELTA_ENDPOINT_REF,
    "code.grammar_profile.resolve": CODE__GRAMMAR_PROFILE__RESOLVE_ENDPOINT_REF,
    "code.package_delta.fingerprint": CODE__PACKAGE_DELTA__FINGERPRINT_ENDPOINT_REF,
    "code.package_delta.normalize": CODE__PACKAGE_DELTA__NORMALIZE_ENDPOINT_REF,
    "code.package_layout.describe": CODE__PACKAGE_LAYOUT__DESCRIBE_ENDPOINT_REF,
    "code.package_layout.discover": CODE__PACKAGE_LAYOUT__DISCOVER_ENDPOINT_REF,
    "code.package_layout.validate": CODE__PACKAGE_LAYOUT__VALIDATE_ENDPOINT_REF,
    "code.section_delta.fingerprint": CODE__SECTION_DELTA__FINGERPRINT_ENDPOINT_REF,
    "code.section_delta.normalize": CODE__SECTION_DELTA__NORMALIZE_ENDPOINT_REF,
    "code.section_delta.resolve_package_delta": CODE__SECTION_DELTA__RESOLVE_PACKAGE_DELTA_ENDPOINT_REF,
    "code.section_delta.resolve_render_policy": CODE__SECTION_DELTA__RESOLVE_RENDER_POLICY_ENDPOINT_REF,
    "code.section_delta.validate": CODE__SECTION_DELTA__VALIDATE_ENDPOINT_REF,
    "code.semantic_analysis.preview_package_delta": CODE__SEMANTIC_ANALYSIS__PREVIEW_PACKAGE_DELTA_ENDPOINT_REF,
    "code.semantic_contract.describe": CODE__SEMANTIC_CONTRACT__DESCRIBE_ENDPOINT_REF,
    "code.semantic_contract.find_manifest_resolution": CODE__SEMANTIC_CONTRACT__FIND_MANIFEST_RESOLUTION_ENDPOINT_REF,
    "code.semantic_contract.normalize": CODE__SEMANTIC_CONTRACT__NORMALIZE_ENDPOINT_REF,
    "code.semantic_contract.resolve_semantic_scope": CODE__SEMANTIC_CONTRACT__RESOLVE_SEMANTIC_SCOPE_ENDPOINT_REF,
    "code.semantic_contract.validate": CODE__SEMANTIC_CONTRACT__VALIDATE_ENDPOINT_REF,
    "code.semantic_source_meaning.resolve_delta": CODE__SEMANTIC_SOURCE_MEANING__RESOLVE_DELTA_ENDPOINT_REF,
    "code.semantic_source_meaning.resolve": CODE__SEMANTIC_SOURCE_MEANING__RESOLVE_ENDPOINT_REF,
    "code.semantic_workflow_coverage.resolve": CODE__SEMANTIC_WORKFLOW_COVERAGE__RESOLVE_ENDPOINT_REF,
    "code.source_ownership.classify": CODE__SOURCE_OWNERSHIP__CLASSIFY_ENDPOINT_REF,
    "code.source_projection.fingerprint": CODE__SOURCE_PROJECTION__FINGERPRINT_ENDPOINT_REF,
    "code.source_projection.normalize": CODE__SOURCE_PROJECTION__NORMALIZE_ENDPOINT_REF,
    "code.source_projection.resolve_package_delta": CODE__SOURCE_PROJECTION__RESOLVE_PACKAGE_DELTA_ENDPOINT_REF,
    "code.source_projection.validate": CODE__SOURCE_PROJECTION__VALIDATE_ENDPOINT_REF,
}

__all__ = [
    "API_FQN_PREFIX",
    "API_INTERFACE_SPEC",
    "API_INVOCATION_MANIFEST",
    "API_PACKAGE_NAME",
    "ENDPOINT_REF_BY_NAME",
    "CODE__GENERATED_MATERIALIZATION_DELTA__FINGERPRINT_ENDPOINT_REF",
    "CODE__GENERATED_MATERIALIZATION_DELTA__NORMALIZE_ENDPOINT_REF",
    "CODE__GENERATED_MATERIALIZATION_DELTA__RESOLVE_PACKAGE_DELTA_ENDPOINT_REF",
    "CODE__GENERATED_MATERIALIZATION_DELTA__VALIDATE_ENDPOINT_REF",
    "CODE__GRAMMAR_ANCHOR_BINDING__RESOLVE_EVIDENCE_ENDPOINT_REF",
    "CODE__GRAMMAR_ANCHOR_BINDING__VALIDATE_ENDPOINT_REF",
    "CODE__GRAMMAR_ANCHOR_RENDER_DELTA__RESOLVE_DELTA_ENDPOINT_REF",
    "CODE__GRAMMAR_PROFILE__RESOLVE_ENDPOINT_REF",
    "CODE__PACKAGE_DELTA__FINGERPRINT_ENDPOINT_REF",
    "CODE__PACKAGE_DELTA__NORMALIZE_ENDPOINT_REF",
    "CODE__PACKAGE_LAYOUT__DESCRIBE_ENDPOINT_REF",
    "CODE__PACKAGE_LAYOUT__DISCOVER_ENDPOINT_REF",
    "CODE__PACKAGE_LAYOUT__VALIDATE_ENDPOINT_REF",
    "CODE__SECTION_DELTA__FINGERPRINT_ENDPOINT_REF",
    "CODE__SECTION_DELTA__NORMALIZE_ENDPOINT_REF",
    "CODE__SECTION_DELTA__RESOLVE_PACKAGE_DELTA_ENDPOINT_REF",
    "CODE__SECTION_DELTA__RESOLVE_RENDER_POLICY_ENDPOINT_REF",
    "CODE__SECTION_DELTA__VALIDATE_ENDPOINT_REF",
    "CODE__SEMANTIC_ANALYSIS__PREVIEW_PACKAGE_DELTA_ENDPOINT_REF",
    "CODE__SEMANTIC_CONTRACT__DESCRIBE_ENDPOINT_REF",
    "CODE__SEMANTIC_CONTRACT__FIND_MANIFEST_RESOLUTION_ENDPOINT_REF",
    "CODE__SEMANTIC_CONTRACT__NORMALIZE_ENDPOINT_REF",
    "CODE__SEMANTIC_CONTRACT__RESOLVE_SEMANTIC_SCOPE_ENDPOINT_REF",
    "CODE__SEMANTIC_CONTRACT__VALIDATE_ENDPOINT_REF",
    "CODE__SEMANTIC_SOURCE_MEANING__RESOLVE_DELTA_ENDPOINT_REF",
    "CODE__SEMANTIC_SOURCE_MEANING__RESOLVE_ENDPOINT_REF",
    "CODE__SEMANTIC_WORKFLOW_COVERAGE__RESOLVE_ENDPOINT_REF",
    "CODE__SOURCE_OWNERSHIP__CLASSIFY_ENDPOINT_REF",
    "CODE__SOURCE_PROJECTION__FINGERPRINT_ENDPOINT_REF",
    "CODE__SOURCE_PROJECTION__NORMALIZE_ENDPOINT_REF",
    "CODE__SOURCE_PROJECTION__RESOLVE_PACKAGE_DELTA_ENDPOINT_REF",
    "CODE__SOURCE_PROJECTION__VALIDATE_ENDPOINT_REF",
]
