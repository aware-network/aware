# GENERATED CODE - DO NOT MODIFY BY HAND
# Thin typed generated API client wrapper over aware_api.invoker.AwareApiEndpointInvoker.
from __future__ import annotations

from typing import cast

from aware_api import AwareApiEndpointInvoker
from ._bindings import API_INTERFACE_SPEC, API_INVOCATION_MANIFEST
from ._bindings import (
    CODE__GENERATED_MATERIALIZATION_DELTA__FINGERPRINT_ENDPOINT_REF,
    CODE__GENERATED_MATERIALIZATION_DELTA__NORMALIZE_ENDPOINT_REF,
    CODE__GENERATED_MATERIALIZATION_DELTA__RESOLVE_PACKAGE_DELTA_ENDPOINT_REF,
    CODE__GENERATED_MATERIALIZATION_DELTA__VALIDATE_ENDPOINT_REF,
    CODE__GRAMMAR_ANCHOR_BINDING__RESOLVE_EVIDENCE_ENDPOINT_REF,
    CODE__GRAMMAR_ANCHOR_BINDING__VALIDATE_ENDPOINT_REF,
    CODE__GRAMMAR_ANCHOR_RENDER_DELTA__RESOLVE_DELTA_ENDPOINT_REF,
    CODE__GRAMMAR_PROFILE__RESOLVE_ENDPOINT_REF,
    CODE__PACKAGE_DELTA__FINGERPRINT_ENDPOINT_REF,
    CODE__PACKAGE_DELTA__NORMALIZE_ENDPOINT_REF,
    CODE__PACKAGE_LAYOUT__DESCRIBE_ENDPOINT_REF,
    CODE__PACKAGE_LAYOUT__DISCOVER_ENDPOINT_REF,
    CODE__PACKAGE_LAYOUT__VALIDATE_ENDPOINT_REF,
    CODE__SECTION_DELTA__FINGERPRINT_ENDPOINT_REF,
    CODE__SECTION_DELTA__NORMALIZE_ENDPOINT_REF,
    CODE__SECTION_DELTA__RESOLVE_PACKAGE_DELTA_ENDPOINT_REF,
    CODE__SECTION_DELTA__RESOLVE_RENDER_POLICY_ENDPOINT_REF,
    CODE__SECTION_DELTA__VALIDATE_ENDPOINT_REF,
    CODE__SEMANTIC_ANALYSIS__PREVIEW_PACKAGE_DELTA_ENDPOINT_REF,
    CODE__SEMANTIC_CONTRACT__DESCRIBE_ENDPOINT_REF,
    CODE__SEMANTIC_CONTRACT__FIND_MANIFEST_RESOLUTION_ENDPOINT_REF,
    CODE__SEMANTIC_CONTRACT__NORMALIZE_ENDPOINT_REF,
    CODE__SEMANTIC_CONTRACT__RESOLVE_SEMANTIC_SCOPE_ENDPOINT_REF,
    CODE__SEMANTIC_CONTRACT__VALIDATE_ENDPOINT_REF,
    CODE__SEMANTIC_SOURCE_MEANING__RESOLVE_DELTA_ENDPOINT_REF,
    CODE__SEMANTIC_SOURCE_MEANING__RESOLVE_ENDPOINT_REF,
    CODE__SEMANTIC_WORKFLOW_COVERAGE__RESOLVE_ENDPOINT_REF,
    CODE__SOURCE_OWNERSHIP__CLASSIFY_ENDPOINT_REF,
    CODE__SOURCE_PROJECTION__FINGERPRINT_ENDPOINT_REF,
    CODE__SOURCE_PROJECTION__NORMALIZE_ENDPOINT_REF,
    CODE__SOURCE_PROJECTION__RESOLVE_PACKAGE_DELTA_ENDPOINT_REF,
    CODE__SOURCE_PROJECTION__VALIDATE_ENDPOINT_REF,
)
from aware_code_service_dto.code.features.generated_materialization_delta import (
    FingerprintCodeGeneratedMaterializationDeltaRequest,
    FingerprintCodeGeneratedMaterializationDeltaResponse,
    NormalizeCodeGeneratedMaterializationDeltaRequest,
    NormalizeCodeGeneratedMaterializationDeltaResponse,
    ResolveCodeGeneratedMaterializationPackageDeltaRequest,
    ResolveCodeGeneratedMaterializationPackageDeltaResponse,
    ValidateCodeGeneratedMaterializationDeltaRequest,
    ValidateCodeGeneratedMaterializationDeltaResponse,
)
from aware_code_service_dto.code.features.grammar_anchor_binding import (
    ResolveCodeGrammarAnchorBindingEvidenceRequest,
    ResolveCodeGrammarAnchorBindingEvidenceResponse,
    ValidateCodeGrammarAnchorBindingRequest,
    ValidateCodeGrammarAnchorBindingResponse,
)
from aware_code_service_dto.code.features.grammar_anchor_render_delta import (
    ResolveCodeGrammarAnchorRenderDeltaRequest,
    ResolveCodeGrammarAnchorRenderDeltaResponse,
)
from aware_code_service_dto.code.features.grammar_profile import (
    ResolveCodeGrammarProfileRequest,
    ResolveCodeGrammarProfileResponse,
)
from aware_code_service_dto.code.features.package_delta import (
    FingerprintCodePackageDeltaRequest,
    FingerprintCodePackageDeltaResponse,
    NormalizeCodePackageDeltaRequest,
    NormalizeCodePackageDeltaResponse,
)
from aware_code_service_dto.code.features.package_layout import (
    DescribeCodePackageLayoutRequest,
    DescribeCodePackageLayoutResponse,
    DiscoverCodePackageLayoutsRequest,
    DiscoverCodePackageLayoutsResponse,
    ValidateCodePackageLayoutRequest,
    ValidateCodePackageLayoutResponse,
)
from aware_code_service_dto.code.features.section_delta import (
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
from aware_code_service_dto.code.features.semantic_analysis import (
    PreviewCodeSemanticAnalysisPackageDeltaRequest,
    PreviewCodeSemanticAnalysisPackageDeltaResponse,
)
from aware_code_service_dto.code.features.semantic_contract import (
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
from aware_code_service_dto.code.features.semantic_source_meaning import (
    ResolveCodeSemanticSourceDeltaMeaningRequest,
    ResolveCodeSemanticSourceDeltaMeaningResponse,
    ResolveCodeSemanticSourceMeaningRequest,
    ResolveCodeSemanticSourceMeaningResponse,
)
from aware_code_service_dto.code.features.semantic_workflow_coverage import (
    ResolveCodeSemanticWorkflowCoverageRequest,
    ResolveCodeSemanticWorkflowCoverageResponse,
)
from aware_code_service_dto.code.features.source_ownership import (
    ClassifyCodeSourceOwnershipRequest,
    ClassifyCodeSourceOwnershipResponse,
)
from aware_code_service_dto.code.features.source_projection import (
    FingerprintCodeSourceProjectionRequest,
    FingerprintCodeSourceProjectionResponse,
    NormalizeCodeSourceProjectionRequest,
    NormalizeCodeSourceProjectionResponse,
    ResolveCodeSourceProjectionPackageDeltaRequest,
    ResolveCodeSourceProjectionPackageDeltaResponse,
    ValidateCodeSourceProjectionRequest,
    ValidateCodeSourceProjectionResponse,
)


class CodeGeneratedMaterializationDeltaCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def fingerprint(
        self, request: FingerprintCodeGeneratedMaterializationDeltaRequest
    ) -> FingerprintCodeGeneratedMaterializationDeltaResponse:
        """Fingerprint renderer-generated materialization delta request and result evidence for preview and receipt correlation."""
        return cast(
            FingerprintCodeGeneratedMaterializationDeltaResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__GENERATED_MATERIALIZATION_DELTA__FINGERPRINT_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def normalize(
        self, request: NormalizeCodeGeneratedMaterializationDeltaRequest
    ) -> NormalizeCodeGeneratedMaterializationDeltaResponse:
        """Normalize renderer-generated materialization delta request and result evidence into stable Code API DTO shape."""
        return cast(
            NormalizeCodeGeneratedMaterializationDeltaResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__GENERATED_MATERIALIZATION_DELTA__NORMALIZE_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def resolve_package_delta(
        self, request: ResolveCodeGeneratedMaterializationPackageDeltaRequest
    ) -> ResolveCodeGeneratedMaterializationPackageDeltaResponse:
        """Resolve renderer-generated materialization delta result evidence into a CodePackageDelta."""
        return cast(
            ResolveCodeGeneratedMaterializationPackageDeltaResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__GENERATED_MATERIALIZATION_DELTA__RESOLVE_PACKAGE_DELTA_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def validate(
        self, request: ValidateCodeGeneratedMaterializationDeltaRequest
    ) -> ValidateCodeGeneratedMaterializationDeltaResponse:
        """Validate renderer-generated materialization delta request and result evidence before provider or consumer use."""
        return cast(
            ValidateCodeGeneratedMaterializationDeltaResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__GENERATED_MATERIALIZATION_DELTA__VALIDATE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class CodeGrammarAnchorBindingCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def resolve_evidence(
        self, request: ResolveCodeGrammarAnchorBindingEvidenceRequest
    ) -> ResolveCodeGrammarAnchorBindingEvidenceResponse:
        """Resolve grammar anchor fixtures into byte evidence and read-only graph/text drafts."""
        return cast(
            ResolveCodeGrammarAnchorBindingEvidenceResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__GRAMMAR_ANCHOR_BINDING__RESOLVE_EVIDENCE_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def validate(
        self, request: ValidateCodeGrammarAnchorBindingRequest
    ) -> ValidateCodeGrammarAnchorBindingResponse:
        """Validate grammar rule-field anchors that bind parsed source text to graph selectors."""
        return cast(
            ValidateCodeGrammarAnchorBindingResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__GRAMMAR_ANCHOR_BINDING__VALIDATE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class CodeGrammarAnchorRenderDeltaCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def resolve_delta(
        self, request: ResolveCodeGrammarAnchorRenderDeltaRequest
    ) -> ResolveCodeGrammarAnchorRenderDeltaResponse:
        """Resolve grammar-anchor graph-to-source replacements into guarded Code package deltas."""
        return cast(
            ResolveCodeGrammarAnchorRenderDeltaResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__GRAMMAR_ANCHOR_RENDER_DELTA__RESOLVE_DELTA_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class CodeGrammarProfileCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def resolve(self, request: ResolveCodeGrammarProfileRequest) -> ResolveCodeGrammarProfileResponse:
        """Resolve a Code-owned grammar profile from semantic-contract syntax lanes."""
        return cast(
            ResolveCodeGrammarProfileResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__GRAMMAR_PROFILE__RESOLVE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class CodePackageDeltaCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def fingerprint(self, request: FingerprintCodePackageDeltaRequest) -> FingerprintCodePackageDeltaResponse:
        """Fingerprint one CodePackageDelta for cache, status, materialization, and receipt correlation."""
        return cast(
            FingerprintCodePackageDeltaResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__PACKAGE_DELTA__FINGERPRINT_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def normalize(self, request: NormalizeCodePackageDeltaRequest) -> NormalizeCodePackageDeltaResponse:
        """Normalize raw package delta input into the public CodePackageDelta DTO shape."""
        return cast(
            NormalizeCodePackageDeltaResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__PACKAGE_DELTA__NORMALIZE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class CodePackageLayoutCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def describe(self, request: DescribeCodePackageLayoutRequest) -> DescribeCodePackageLayoutResponse:
        """Describe package layout and path-role contract truth for local filesystem classification."""
        return cast(
            DescribeCodePackageLayoutResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__PACKAGE_LAYOUT__DESCRIBE_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def discover(self, request: DiscoverCodePackageLayoutsRequest) -> DiscoverCodePackageLayoutsResponse:
        """Discover package layout contract truth for explicit manifest paths."""
        return cast(
            DiscoverCodePackageLayoutsResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__PACKAGE_LAYOUT__DISCOVER_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def validate(self, request: ValidateCodePackageLayoutRequest) -> ValidateCodePackageLayoutResponse:
        """Validate package layout and path-role contract truth before local filesystem classification."""
        return cast(
            ValidateCodePackageLayoutResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__PACKAGE_LAYOUT__VALIDATE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class CodeSectionDeltaCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def fingerprint(self, request: FingerprintCodeSectionDeltaRequest) -> FingerprintCodeSectionDeltaResponse:
        """Fingerprint one CodeSectionDeltaSet for semantic event and resolver receipts."""
        return cast(
            FingerprintCodeSectionDeltaResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__SECTION_DELTA__FINGERPRINT_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def normalize(self, request: NormalizeCodeSectionDeltaRequest) -> NormalizeCodeSectionDeltaResponse:
        """Normalize section/segment delta intent into the public Code API DTO shape."""
        return cast(
            NormalizeCodeSectionDeltaResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__SECTION_DELTA__NORMALIZE_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def resolve_package_delta(
        self, request: ResolveCodeSectionDeltaPackageDeltaRequest
    ) -> ResolveCodeSectionDeltaPackageDeltaResponse:
        """Resolve one CodeSectionDeltaSet into a CodePackageDelta through a Code resolver."""
        return cast(
            ResolveCodeSectionDeltaPackageDeltaResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__SECTION_DELTA__RESOLVE_PACKAGE_DELTA_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def resolve_render_policy(
        self, request: ResolveCodeSegmentRenderPolicyRequest
    ) -> ResolveCodeSegmentRenderPolicyResponse:
        """Resolve Code-owned segment render policies for section-delta value domains."""
        return cast(
            ResolveCodeSegmentRenderPolicyResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__SECTION_DELTA__RESOLVE_RENDER_POLICY_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def validate(self, request: ValidateCodeSectionDeltaRequest) -> ValidateCodeSectionDeltaResponse:
        """Validate section/segment delta intent before Code resolver execution."""
        return cast(
            ValidateCodeSectionDeltaResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__SECTION_DELTA__VALIDATE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class CodeSemanticAnalysisCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def preview_package_delta(
        self, request: PreviewCodeSemanticAnalysisPackageDeltaRequest
    ) -> PreviewCodeSemanticAnalysisPackageDeltaResponse:
        """Preview provider-owned semantic meaning for one CodePackageDelta without materialization."""
        return cast(
            PreviewCodeSemanticAnalysisPackageDeltaResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__SEMANTIC_ANALYSIS__PREVIEW_PACKAGE_DELTA_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class CodeSemanticContractCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def describe(self, request: DescribeCodeSemanticContractRequest) -> DescribeCodeSemanticContractResponse:
        """Describe one Code semantic contract by provider, package, or package FQN."""
        return cast(
            DescribeCodeSemanticContractResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__SEMANTIC_CONTRACT__DESCRIBE_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def find_manifest_resolution(
        self, request: FindCodeSemanticManifestResolutionRequest
    ) -> FindCodeSemanticManifestResolutionResponse:
        """Find semantic manifest-resolution descriptors through Code-owned contract truth."""
        return cast(
            FindCodeSemanticManifestResolutionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__SEMANTIC_CONTRACT__FIND_MANIFEST_RESOLUTION_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def normalize(self, request: NormalizeCodeSemanticContractRequest) -> NormalizeCodeSemanticContractResponse:
        """Normalize a runtime-adapted semantic contract into the public Code API DTO shape."""
        return cast(
            NormalizeCodeSemanticContractResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__SEMANTIC_CONTRACT__NORMALIZE_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def resolve_semantic_scope(
        self, request: ResolveCodeSemanticScopeRequest
    ) -> ResolveCodeSemanticScopeResponse:
        """Resolve provider-owned semantic scope through the Code-owned semantic scope registry."""
        return cast(
            ResolveCodeSemanticScopeResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__SEMANTIC_CONTRACT__RESOLVE_SEMANTIC_SCOPE_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def validate(self, request: ValidateCodeSemanticContractRequest) -> ValidateCodeSemanticContractResponse:
        """Validate an externally supplied Code semantic contract DTO before local or remote use."""
        return cast(
            ValidateCodeSemanticContractResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__SEMANTIC_CONTRACT__VALIDATE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class CodeSemanticSourceMeaningCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def resolve(
        self, request: ResolveCodeSemanticSourceMeaningRequest
    ) -> ResolveCodeSemanticSourceMeaningResponse:
        """Resolve declarative source meaning through Code-owned grammar source indexes."""
        return cast(
            ResolveCodeSemanticSourceMeaningResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__SEMANTIC_SOURCE_MEANING__RESOLVE_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def resolve_delta(
        self, request: ResolveCodeSemanticSourceDeltaMeaningRequest
    ) -> ResolveCodeSemanticSourceDeltaMeaningResponse:
        """Resolve declarative source meaning from CodePackageDelta plus explicit baseline context."""
        return cast(
            ResolveCodeSemanticSourceDeltaMeaningResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__SEMANTIC_SOURCE_MEANING__RESOLVE_DELTA_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class CodeSemanticWorkflowCoverageCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def resolve(
        self, request: ResolveCodeSemanticWorkflowCoverageRequest
    ) -> ResolveCodeSemanticWorkflowCoverageResponse:
        """Resolve Code-owned semantic workflow grammar/source/graph-binding coverage."""
        return cast(
            ResolveCodeSemanticWorkflowCoverageResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__SEMANTIC_WORKFLOW_COVERAGE__RESOLVE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class CodeSourceOwnershipCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def classify(self, request: ClassifyCodeSourceOwnershipRequest) -> ClassifyCodeSourceOwnershipResponse:
        """Classify observed paths against package ownership boundaries through Code-owned rules."""
        return cast(
            ClassifyCodeSourceOwnershipResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__SOURCE_OWNERSHIP__CLASSIFY_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class CodeSourceProjectionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def fingerprint(
        self, request: FingerprintCodeSourceProjectionRequest
    ) -> FingerprintCodeSourceProjectionResponse:
        """Fingerprint semantic source-projection request and result evidence for preview and receipt correlation."""
        return cast(
            FingerprintCodeSourceProjectionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__SOURCE_PROJECTION__FINGERPRINT_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def normalize(self, request: NormalizeCodeSourceProjectionRequest) -> NormalizeCodeSourceProjectionResponse:
        """Normalize semantic source-projection request and result evidence into stable Code API DTO shape."""
        return cast(
            NormalizeCodeSourceProjectionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__SOURCE_PROJECTION__NORMALIZE_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def resolve_package_delta(
        self, request: ResolveCodeSourceProjectionPackageDeltaRequest
    ) -> ResolveCodeSourceProjectionPackageDeltaResponse:
        """Resolve provider-produced source-projection result evidence into a CodePackageDelta."""
        return cast(
            ResolveCodeSourceProjectionPackageDeltaResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__SOURCE_PROJECTION__RESOLVE_PACKAGE_DELTA_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def validate(self, request: ValidateCodeSourceProjectionRequest) -> ValidateCodeSourceProjectionResponse:
        """Validate semantic source-projection request and result evidence before provider or consumer use."""
        return cast(
            ValidateCodeSourceProjectionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CODE__SOURCE_PROJECTION__VALIDATE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class CodeApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.generated_materialization_delta = CodeGeneratedMaterializationDeltaCapabilityClient(client)
        self.grammar_anchor_binding = CodeGrammarAnchorBindingCapabilityClient(client)
        self.grammar_anchor_render_delta = CodeGrammarAnchorRenderDeltaCapabilityClient(client)
        self.grammar_profile = CodeGrammarProfileCapabilityClient(client)
        self.package_delta = CodePackageDeltaCapabilityClient(client)
        self.package_layout = CodePackageLayoutCapabilityClient(client)
        self.section_delta = CodeSectionDeltaCapabilityClient(client)
        self.semantic_analysis = CodeSemanticAnalysisCapabilityClient(client)
        self.semantic_contract = CodeSemanticContractCapabilityClient(client)
        self.semantic_source_meaning = CodeSemanticSourceMeaningCapabilityClient(client)
        self.semantic_workflow_coverage = CodeSemanticWorkflowCoverageCapabilityClient(client)
        self.source_ownership = CodeSourceOwnershipCapabilityClient(client)
        self.source_projection = CodeSourceProjectionCapabilityClient(client)


class AwareCodeServiceApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.interface_spec = API_INTERFACE_SPEC
        self.invocation_manifest = API_INVOCATION_MANIFEST
        self.code = CodeApiClient(client)


__all__ = [
    "AwareCodeServiceApiClient",
    "CodeApiClient",
    "CodeGeneratedMaterializationDeltaCapabilityClient",
    "CodeGrammarAnchorBindingCapabilityClient",
    "CodeGrammarAnchorRenderDeltaCapabilityClient",
    "CodeGrammarProfileCapabilityClient",
    "CodePackageDeltaCapabilityClient",
    "CodePackageLayoutCapabilityClient",
    "CodeSectionDeltaCapabilityClient",
    "CodeSemanticAnalysisCapabilityClient",
    "CodeSemanticContractCapabilityClient",
    "CodeSemanticSourceMeaningCapabilityClient",
    "CodeSemanticWorkflowCoverageCapabilityClient",
    "CodeSourceOwnershipCapabilityClient",
    "CodeSourceProjectionCapabilityClient",
]
