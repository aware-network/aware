from __future__ import annotations

from collections.abc import Awaitable, Sequence
from dataclasses import dataclass
from typing import Callable, Protocol, cast

from aware_code_sdk.dto import (
    ClassifyCodeSourceOwnershipRequest,
    ClassifyCodeSourceOwnershipResponse,
    CodeSourceOwnershipObservedPath,
    CodeSourceOwnershipPackageBinding,
    CodeSourceOwnershipRequest,
    DescribeCodePackageLayoutRequest,
    DescribeCodePackageLayoutResponse,
    DescribeCodeSemanticContractRequest,
    DescribeCodeSemanticContractResponse,
    DiscoverCodePackageLayoutsRequest,
    DiscoverCodePackageLayoutsResponse,
    FindCodeSemanticManifestResolutionRequest,
    FindCodeSemanticManifestResolutionResponse,
    FingerprintCodeSourceProjectionRequest,
    FingerprintCodeSourceProjectionResponse,
    FingerprintCodeGeneratedMaterializationDeltaRequest,
    FingerprintCodeGeneratedMaterializationDeltaResponse,
    NormalizeCodeSemanticContractRequest,
    NormalizeCodeSemanticContractResponse,
    NormalizeCodeSourceProjectionRequest,
    NormalizeCodeSourceProjectionResponse,
    NormalizeCodeGeneratedMaterializationDeltaRequest,
    NormalizeCodeGeneratedMaterializationDeltaResponse,
    CodeSemanticScopePackageRef,
    ResolveCodeGeneratedMaterializationPackageDeltaRequest,
    ResolveCodeGeneratedMaterializationPackageDeltaResponse,
    ResolveCodeSemanticScopeRequest,
    ResolveCodeSemanticScopeResponse,
    CodeSemanticContractSpecDeclaration,
    PreviewCodeSemanticAnalysisPackageDeltaRequest,
    PreviewCodeSemanticAnalysisPackageDeltaResponse,
    ResolveCodeSemanticSourceDeltaMeaningRequest,
    ResolveCodeSemanticSourceDeltaMeaningResponse,
    ResolveCodeSemanticSourceMeaningRequest,
    ResolveCodeSemanticSourceMeaningResponse,
    ResolveCodeGrammarAnchorBindingEvidenceRequest,
    ResolveCodeGrammarAnchorBindingEvidenceResponse,
    ResolveCodeGrammarAnchorRenderDeltaRequest,
    ResolveCodeGrammarAnchorRenderDeltaResponse,
    ResolveCodeGrammarProfileRequest,
    ResolveCodeGrammarProfileResponse,
    ResolveCodeSegmentRenderPolicyRequest,
    ResolveCodeSegmentRenderPolicyResponse,
    ResolveCodeSourceProjectionPackageDeltaRequest,
    ResolveCodeSourceProjectionPackageDeltaResponse,
    ValidateCodePackageLayoutRequest,
    ValidateCodePackageLayoutResponse,
    ValidateCodeGrammarAnchorBindingRequest,
    ValidateCodeGrammarAnchorBindingResponse,
    ValidateCodeSemanticContractRequest,
    ValidateCodeSemanticContractResponse,
    ValidateCodeSourceProjectionRequest,
    ValidateCodeSourceProjectionResponse,
    ValidateCodeGeneratedMaterializationDeltaRequest,
    ValidateCodeGeneratedMaterializationDeltaResponse,
)

from aware_code_sdk.local_semantic_contract import (
    CodeSdkManifestResolutionMatch,
    CodeSdkPackageLayoutBinding,
    CodeSdkSemanticContractCatalog,
    LocalCodeSdkApiClient,
    PackageLayoutInput,
    build_local_code_sdk_api_client,
)
from aware_code_sdk.manifest_resolution import (
    BlockingCodeSdkManifestResolutionProvider,
    CodeSdkAsyncManifestResolutionProvider,
    CodeSdkManifestResolutionProvider,
    GeneratedCodeSdkAsyncManifestResolutionProvider,
    LocalCatalogCodeSdkManifestResolutionProvider,
)
from aware_code_sdk.module_manifest import (
    CodeSdkModuleManifestProvider,
    SemanticContractCodeSdkModuleManifestProvider,
)
from aware_code_sdk.package_layout import (
    BlockingCodeSdkPackageLayoutProvider,
    CodeSdkAsyncPackageLayoutProvider,
    CodeSdkDiscoveryFile,
    CodeSdkPackageLayoutProvider,
    GeneratedCodeSdkAsyncPackageLayoutProvider,
    LocalCatalogCodeSdkPackageLayoutProvider,
)
from aware_code_sdk.source_ownership import (
    BlockingCodeSdkSourceOwnershipProvider,
    CodeSdkAsyncSourceOwnershipProvider,
    CodeSdkSourceOwnershipProvider,
    GeneratedCodeSdkAsyncSourceOwnershipProvider,
)
from aware_code_sdk.semantic_ownership import (
    CodeSdkSemanticOwnershipProvider,
    ServiceBackedCodeSdkSemanticOwnershipProvider,
)
from aware_code_sdk.semantic_scope import (
    BlockingCodeSdkSemanticScopeProvider,
    CodeSdkAsyncSemanticScopeProvider,
    CodeSdkSemanticScopeProvider,
    GeneratedCodeSdkAsyncSemanticScopeProvider,
    LocalCatalogCodeSdkSemanticScopeProvider,
)


class CodeSdkSemanticContractCapabilityClient(Protocol):
    async def describe(
        self,
        request: DescribeCodeSemanticContractRequest,
    ) -> DescribeCodeSemanticContractResponse: ...

    async def find_manifest_resolution(
        self,
        request: FindCodeSemanticManifestResolutionRequest,
    ) -> FindCodeSemanticManifestResolutionResponse: ...

    async def resolve_semantic_scope(
        self,
        request: ResolveCodeSemanticScopeRequest,
    ) -> ResolveCodeSemanticScopeResponse: ...

    async def validate(
        self,
        request: ValidateCodeSemanticContractRequest,
    ) -> ValidateCodeSemanticContractResponse: ...

    async def normalize(
        self,
        request: NormalizeCodeSemanticContractRequest,
    ) -> NormalizeCodeSemanticContractResponse: ...


class CodeSdkSemanticAnalysisCapabilityClient(Protocol):
    async def preview_package_delta(
        self,
        request: PreviewCodeSemanticAnalysisPackageDeltaRequest,
    ) -> PreviewCodeSemanticAnalysisPackageDeltaResponse: ...


class CodeSdkSemanticSourceMeaningCapabilityClient(Protocol):
    async def resolve(
        self,
        request: ResolveCodeSemanticSourceMeaningRequest,
    ) -> ResolveCodeSemanticSourceMeaningResponse: ...

    async def resolve_delta(
        self,
        request: ResolveCodeSemanticSourceDeltaMeaningRequest,
    ) -> ResolveCodeSemanticSourceDeltaMeaningResponse: ...


class CodeSdkGrammarProfileCapabilityClient(Protocol):
    async def resolve(
        self,
        request: ResolveCodeGrammarProfileRequest,
    ) -> ResolveCodeGrammarProfileResponse: ...


class CodeSdkGrammarAnchorBindingCapabilityClient(Protocol):
    async def validate(
        self,
        request: ValidateCodeGrammarAnchorBindingRequest,
    ) -> ValidateCodeGrammarAnchorBindingResponse: ...

    async def resolve_evidence(
        self,
        request: ResolveCodeGrammarAnchorBindingEvidenceRequest,
    ) -> ResolveCodeGrammarAnchorBindingEvidenceResponse: ...


class CodeSdkGrammarAnchorRenderDeltaCapabilityClient(Protocol):
    async def resolve_delta(
        self,
        request: ResolveCodeGrammarAnchorRenderDeltaRequest,
    ) -> ResolveCodeGrammarAnchorRenderDeltaResponse: ...


class CodeSdkSectionDeltaCapabilityClient(Protocol):
    async def resolve_render_policy(
        self,
        request: ResolveCodeSegmentRenderPolicyRequest,
    ) -> ResolveCodeSegmentRenderPolicyResponse: ...


class CodeSdkSourceProjectionCapabilityClient(Protocol):
    async def validate(
        self,
        request: ValidateCodeSourceProjectionRequest,
    ) -> ValidateCodeSourceProjectionResponse: ...

    async def normalize(
        self,
        request: NormalizeCodeSourceProjectionRequest,
    ) -> NormalizeCodeSourceProjectionResponse: ...

    async def fingerprint(
        self,
        request: FingerprintCodeSourceProjectionRequest,
    ) -> FingerprintCodeSourceProjectionResponse: ...

    async def resolve_package_delta(
        self,
        request: ResolveCodeSourceProjectionPackageDeltaRequest,
    ) -> ResolveCodeSourceProjectionPackageDeltaResponse: ...


class CodeSdkGeneratedMaterializationDeltaCapabilityClient(Protocol):
    async def validate(
        self,
        request: ValidateCodeGeneratedMaterializationDeltaRequest,
    ) -> ValidateCodeGeneratedMaterializationDeltaResponse: ...

    async def normalize(
        self,
        request: NormalizeCodeGeneratedMaterializationDeltaRequest,
    ) -> NormalizeCodeGeneratedMaterializationDeltaResponse: ...

    async def fingerprint(
        self,
        request: FingerprintCodeGeneratedMaterializationDeltaRequest,
    ) -> FingerprintCodeGeneratedMaterializationDeltaResponse: ...

    async def resolve_package_delta(
        self,
        request: ResolveCodeGeneratedMaterializationPackageDeltaRequest,
    ) -> ResolveCodeGeneratedMaterializationPackageDeltaResponse: ...


class CodeSdkPackageLayoutCapabilityClient(Protocol):
    async def describe(
        self,
        request: DescribeCodePackageLayoutRequest,
    ) -> DescribeCodePackageLayoutResponse: ...

    async def discover(
        self,
        request: DiscoverCodePackageLayoutsRequest,
    ) -> DiscoverCodePackageLayoutsResponse: ...

    async def validate(
        self,
        request: ValidateCodePackageLayoutRequest,
    ) -> ValidateCodePackageLayoutResponse: ...


class CodeSdkSourceOwnershipCapabilityClient(Protocol):
    async def classify(
        self,
        request: ClassifyCodeSourceOwnershipRequest,
    ) -> ClassifyCodeSourceOwnershipResponse: ...


class CodeSdkCodeApiClient(Protocol):
    @property
    def grammar_anchor_binding(
        self,
    ) -> CodeSdkGrammarAnchorBindingCapabilityClient: ...

    @property
    def grammar_anchor_render_delta(
        self,
    ) -> CodeSdkGrammarAnchorRenderDeltaCapabilityClient: ...

    @property
    def grammar_profile(self) -> CodeSdkGrammarProfileCapabilityClient: ...

    @property
    def semantic_contract(self) -> CodeSdkSemanticContractCapabilityClient: ...

    @property
    def semantic_analysis(self) -> CodeSdkSemanticAnalysisCapabilityClient: ...

    @property
    def semantic_source_meaning(
        self,
    ) -> CodeSdkSemanticSourceMeaningCapabilityClient: ...

    @property
    def section_delta(self) -> CodeSdkSectionDeltaCapabilityClient: ...

    @property
    def source_projection(self) -> CodeSdkSourceProjectionCapabilityClient: ...

    @property
    def generated_materialization_delta(
        self,
    ) -> CodeSdkGeneratedMaterializationDeltaCapabilityClient: ...

    @property
    def package_layout(self) -> CodeSdkPackageLayoutCapabilityClient: ...


class CodeSdkApiClient(Protocol):
    @property
    def code(self) -> CodeSdkCodeApiClient: ...


@dataclass(frozen=True, slots=True)
class AwareCodeSdk:
    api_client: CodeSdkApiClient

    @classmethod
    def local(
        cls,
        *,
        catalog: CodeSdkSemanticContractCatalog | None = None,
        package_layouts: tuple[PackageLayoutInput, ...] = (),
    ) -> "AwareCodeSdk":
        return cls(
            api_client=build_local_code_sdk_api_client(
                catalog=catalog,
                package_layouts=package_layouts,
            )
        )

    async def describe_semantic_contract(
        self,
        request: DescribeCodeSemanticContractRequest | None = None,
    ) -> DescribeCodeSemanticContractResponse:
        return await self.api_client.code.semantic_contract.describe(
            request or DescribeCodeSemanticContractRequest()
        )

    async def describe_semantic_contract_spec(
        self,
        request: DescribeCodeSemanticContractRequest | None = None,
    ) -> CodeSemanticContractSpecDeclaration | None:
        resolved_request = (
            (request or DescribeCodeSemanticContractRequest()).model_copy(
                update={
                    "include_layout": False,
                    "include_spec_declaration": True,
                }
            )
        )
        response = await self.describe_semantic_contract(resolved_request)
        return response.spec_declaration

    async def describe_package_layout(
        self,
        request: DescribeCodePackageLayoutRequest,
    ) -> DescribeCodePackageLayoutResponse:
        return await self.api_client.code.package_layout.describe(request)

    async def preview_semantic_analysis_package_delta(
        self,
        request: PreviewCodeSemanticAnalysisPackageDeltaRequest,
    ) -> PreviewCodeSemanticAnalysisPackageDeltaResponse:
        return await self.api_client.code.semantic_analysis.preview_package_delta(
            request
        )

    async def resolve_semantic_source_meaning(
        self,
        request: ResolveCodeSemanticSourceMeaningRequest,
    ) -> ResolveCodeSemanticSourceMeaningResponse:
        return await self.api_client.code.semantic_source_meaning.resolve(request)

    async def resolve_semantic_source_delta_meaning(
        self,
        request: ResolveCodeSemanticSourceDeltaMeaningRequest,
    ) -> ResolveCodeSemanticSourceDeltaMeaningResponse:
        return await self.api_client.code.semantic_source_meaning.resolve_delta(request)

    async def resolve_grammar_profile(
        self,
        request: ResolveCodeGrammarProfileRequest,
    ) -> ResolveCodeGrammarProfileResponse:
        return await self.api_client.code.grammar_profile.resolve(request)

    async def validate_grammar_anchor_binding(
        self,
        request: ValidateCodeGrammarAnchorBindingRequest,
    ) -> ValidateCodeGrammarAnchorBindingResponse:
        return await self.api_client.code.grammar_anchor_binding.validate(request)

    async def resolve_grammar_anchor_binding_evidence(
        self,
        request: ResolveCodeGrammarAnchorBindingEvidenceRequest,
    ) -> ResolveCodeGrammarAnchorBindingEvidenceResponse:
        return await self.api_client.code.grammar_anchor_binding.resolve_evidence(
            request
        )

    async def resolve_grammar_anchor_render_delta(
        self,
        request: ResolveCodeGrammarAnchorRenderDeltaRequest,
    ) -> ResolveCodeGrammarAnchorRenderDeltaResponse:
        return await self.api_client.code.grammar_anchor_render_delta.resolve_delta(
            request
        )

    async def resolve_segment_render_policy(
        self,
        request: ResolveCodeSegmentRenderPolicyRequest,
    ) -> ResolveCodeSegmentRenderPolicyResponse:
        return await self.api_client.code.section_delta.resolve_render_policy(request)

    async def validate_source_projection(
        self,
        request: ValidateCodeSourceProjectionRequest,
    ) -> ValidateCodeSourceProjectionResponse:
        return await self.api_client.code.source_projection.validate(request)

    async def normalize_source_projection(
        self,
        request: NormalizeCodeSourceProjectionRequest,
    ) -> NormalizeCodeSourceProjectionResponse:
        return await self.api_client.code.source_projection.normalize(request)

    async def fingerprint_source_projection(
        self,
        request: FingerprintCodeSourceProjectionRequest,
    ) -> FingerprintCodeSourceProjectionResponse:
        return await self.api_client.code.source_projection.fingerprint(request)

    async def resolve_source_projection_package_delta(
        self,
        request: ResolveCodeSourceProjectionPackageDeltaRequest,
    ) -> ResolveCodeSourceProjectionPackageDeltaResponse:
        return await self.api_client.code.source_projection.resolve_package_delta(
            request
        )

    async def validate_generated_materialization_delta(
        self,
        request: ValidateCodeGeneratedMaterializationDeltaRequest,
    ) -> ValidateCodeGeneratedMaterializationDeltaResponse:
        return await self.api_client.code.generated_materialization_delta.validate(
            request
        )

    async def normalize_generated_materialization_delta(
        self,
        request: NormalizeCodeGeneratedMaterializationDeltaRequest,
    ) -> NormalizeCodeGeneratedMaterializationDeltaResponse:
        return await self.api_client.code.generated_materialization_delta.normalize(
            request
        )

    async def fingerprint_generated_materialization_delta(
        self,
        request: FingerprintCodeGeneratedMaterializationDeltaRequest,
    ) -> FingerprintCodeGeneratedMaterializationDeltaResponse:
        return await self.api_client.code.generated_materialization_delta.fingerprint(
            request
        )

    async def resolve_generated_materialization_package_delta(
        self,
        request: ResolveCodeGeneratedMaterializationPackageDeltaRequest,
    ) -> ResolveCodeGeneratedMaterializationPackageDeltaResponse:
        return await (
            self.api_client.code.generated_materialization_delta.resolve_package_delta(
                request
            )
        )

    async def discover_package_layouts(
        self,
        request: DiscoverCodePackageLayoutsRequest | None = None,
        *,
        workspace_root: str = ".",
        manifest_paths: tuple[str, ...] = (),
    ) -> DiscoverCodePackageLayoutsResponse:
        resolved_request = request or DiscoverCodePackageLayoutsRequest(
            workspace_root=workspace_root,
            manifest_paths=list(manifest_paths),
        )
        return await self.api_client.code.package_layout.discover(resolved_request)

    async def discover_package_layouts_for_files(
        self,
        *,
        workspace_root: str = ".",
        files: Sequence[CodeSdkDiscoveryFile] = (),
    ) -> DiscoverCodePackageLayoutsResponse:
        package_layout = self.api_client.code.package_layout
        discover = getattr(package_layout, "discover_package_layouts_for_files", None)
        if not callable(discover):
            raise TypeError(
                "Code SDK API client does not expose observed-file package "
                "layout discovery."
            )
        typed_discover = cast(
            Callable[..., Awaitable[DiscoverCodePackageLayoutsResponse]],
            discover,
        )
        return cast(
            DiscoverCodePackageLayoutsResponse,
            await typed_discover(
                workspace_root=workspace_root,
                files=files,
            ),
        )

    async def classify_source_ownership(
        self,
        request: ClassifyCodeSourceOwnershipRequest | None = None,
        *,
        workspace_root: str | None = None,
        package_bindings: Sequence[CodeSourceOwnershipPackageBinding] = (),
        observed_paths: Sequence[CodeSourceOwnershipObservedPath] = (),
        strict: bool = True,
    ) -> ClassifyCodeSourceOwnershipResponse:
        resolved_request = request or ClassifyCodeSourceOwnershipRequest(
            ownership_request=CodeSourceOwnershipRequest(
                workspace_root=workspace_root,
                package_bindings=list(package_bindings),
                observed_paths=list(observed_paths),
                strict=strict,
            )
        )
        source_ownership = cast(
            CodeSdkSourceOwnershipCapabilityClient | None,
            getattr(self.api_client.code, "source_ownership", None),
        )
        if source_ownership is None:
            raise TypeError(
                "Code SDK API client does not expose code.source_ownership."
            )
        return await source_ownership.classify(resolved_request)

    def source_ownership_provider(self) -> CodeSdkSourceOwnershipProvider:
        local_provider = _local_source_ownership_provider(api_client=self.api_client)
        if local_provider is not None:
            return local_provider
        return BlockingCodeSdkSourceOwnershipProvider(
            async_provider=self.async_source_ownership_provider(),
        )

    def async_source_ownership_provider(self) -> CodeSdkAsyncSourceOwnershipProvider:
        return GeneratedCodeSdkAsyncSourceOwnershipProvider(client=self)

    def semantic_ownership_provider(self) -> CodeSdkSemanticOwnershipProvider:
        local_provider = _local_semantic_ownership_provider(
            api_client=self.api_client,
        )
        if local_provider is not None:
            return ServiceBackedCodeSdkSemanticOwnershipProvider(
                raw_provider=local_provider,
            )
        raise TypeError(
            "Code SDK API client does not expose semantic ownership provider."
        )

    def semantic_scope_provider(self) -> CodeSdkSemanticScopeProvider:
        local_client = self.api_client
        if isinstance(local_client, LocalCodeSdkApiClient):
            return LocalCatalogCodeSdkSemanticScopeProvider()
        local_provider = _local_semantic_scope_provider(api_client=local_client)
        if local_provider is not None:
            return local_provider
        return BlockingCodeSdkSemanticScopeProvider(
            async_provider=self.async_semantic_scope_provider(),
        )

    def async_semantic_scope_provider(self) -> CodeSdkAsyncSemanticScopeProvider:
        return GeneratedCodeSdkAsyncSemanticScopeProvider(client=self)

    def package_layout_provider(self) -> CodeSdkPackageLayoutProvider:
        local_client = self.api_client
        if isinstance(local_client, LocalCodeSdkApiClient):
            return LocalCatalogCodeSdkPackageLayoutProvider(
                catalog=local_client.catalog,
            )
        local_provider = _local_package_layout_provider(api_client=local_client)
        if local_provider is not None:
            return local_provider
        return BlockingCodeSdkPackageLayoutProvider(
            async_provider=self.async_package_layout_provider(),
        )

    def async_package_layout_provider(self) -> CodeSdkAsyncPackageLayoutProvider:
        return GeneratedCodeSdkAsyncPackageLayoutProvider(client=self)

    def matching_manifest_resolution(
        self,
        *,
        provider_key: str | None = None,
        manifest_kind: str | None = None,
        filename: str | None = None,
        workspace_manifest_kind: str | None = None,
    ) -> tuple[CodeSdkManifestResolutionMatch, ...]:
        local_client = self.api_client
        if not isinstance(local_client, LocalCodeSdkApiClient):
            raise TypeError(
                "matching_manifest_resolution is available only on the "
                "catalog-backed local Code SDK client; use "
                "find_manifest_resolution for generated API clients."
            )
        return local_client.catalog.matching_manifest_resolution(
            provider_key=provider_key,
            manifest_kind=manifest_kind,
            filename=filename,
            workspace_manifest_kind=workspace_manifest_kind,
        )

    def manifest_resolution_provider(self) -> CodeSdkManifestResolutionProvider:
        local_client = self.api_client
        if isinstance(local_client, LocalCodeSdkApiClient):
            return LocalCatalogCodeSdkManifestResolutionProvider(
                catalog=local_client.catalog,
            )
        local_provider = _local_manifest_resolution_provider(api_client=local_client)
        if local_provider is not None:
            return local_provider
        return BlockingCodeSdkManifestResolutionProvider(
            async_provider=self.async_manifest_resolution_provider(),
        )

    def module_manifest_provider(self) -> CodeSdkModuleManifestProvider:
        return SemanticContractCodeSdkModuleManifestProvider(
            manifest_resolution_provider=self.manifest_resolution_provider(),
        )

    def async_manifest_resolution_provider(
        self,
    ) -> CodeSdkAsyncManifestResolutionProvider:
        return GeneratedCodeSdkAsyncManifestResolutionProvider(client=self)

    async def find_manifest_resolution(
        self,
        request: FindCodeSemanticManifestResolutionRequest | None = None,
        *,
        provider_key: str | None = None,
        manifest_kind: str | None = None,
        filename: str | None = None,
        workspace_manifest_kind: str | None = None,
    ) -> FindCodeSemanticManifestResolutionResponse:
        resolved_request = request or FindCodeSemanticManifestResolutionRequest(
            provider_key=provider_key,
            manifest_kind=manifest_kind,
            filename=filename,
            workspace_manifest_kind=workspace_manifest_kind,
        )
        return await self.api_client.code.semantic_contract.find_manifest_resolution(
            resolved_request
        )

    async def resolve_semantic_scope(
        self,
        request: ResolveCodeSemanticScopeRequest | None = None,
        *,
        package_ref: CodeSemanticScopePackageRef | None = None,
        workspace_root: str = ".",
        provider_keys: Sequence[str] = (),
        scope_keys: Sequence[str] = (),
    ) -> ResolveCodeSemanticScopeResponse:
        if request is None:
            if package_ref is None:
                raise ValueError("package_ref is required.")
            request = ResolveCodeSemanticScopeRequest(
                package_ref=package_ref,
                workspace_root=workspace_root,
                provider_keys=list(provider_keys),
                scope_keys=list(scope_keys),
            )
        return await self.api_client.code.semantic_contract.resolve_semantic_scope(
            request
        )


def _local_manifest_resolution_provider(
    *,
    api_client: CodeSdkApiClient,
) -> CodeSdkManifestResolutionProvider | None:
    for candidate in (api_client, getattr(api_client, "_client", None)):
        provider_factory = getattr(candidate, "manifest_resolution_provider", None)
        if not callable(provider_factory):
            continue
        provider = provider_factory()
        if provider is not None:
            return cast(CodeSdkManifestResolutionProvider, provider)
    return None


def _local_package_layout_provider(
    *,
    api_client: CodeSdkApiClient,
) -> CodeSdkPackageLayoutProvider | None:
    for candidate in (api_client, getattr(api_client, "_client", None)):
        provider_factory = getattr(candidate, "package_layout_provider", None)
        if not callable(provider_factory):
            continue
        provider = provider_factory()
        if provider is not None:
            return cast(CodeSdkPackageLayoutProvider, provider)
    return None


def _local_source_ownership_provider(
    *,
    api_client: CodeSdkApiClient,
) -> CodeSdkSourceOwnershipProvider | None:
    for candidate in (api_client, getattr(api_client, "_client", None)):
        provider_factory = getattr(candidate, "source_ownership_provider", None)
        if not callable(provider_factory):
            continue
        provider = provider_factory()
        if provider is not None:
            return cast(CodeSdkSourceOwnershipProvider, provider)
    return None


def _local_semantic_ownership_provider(
    *,
    api_client: CodeSdkApiClient,
) -> object | None:
    for candidate in (api_client, getattr(api_client, "_client", None)):
        provider_factory = getattr(candidate, "semantic_ownership_provider", None)
        if not callable(provider_factory):
            continue
        provider = provider_factory()
        if provider is not None:
            return provider
    return None


def _local_semantic_scope_provider(
    *,
    api_client: CodeSdkApiClient,
) -> CodeSdkSemanticScopeProvider | None:
    for candidate in (api_client, getattr(api_client, "_client", None)):
        provider_factory = getattr(candidate, "semantic_scope_provider", None)
        if not callable(provider_factory):
            continue
        provider = provider_factory()
        if provider is not None:
            return cast(CodeSdkSemanticScopeProvider, provider)
    return None


__all__ = [
    "AwareCodeSdk",
    "BlockingCodeSdkManifestResolutionProvider",
    "BlockingCodeSdkPackageLayoutProvider",
    "BlockingCodeSdkSemanticScopeProvider",
    "BlockingCodeSdkSourceOwnershipProvider",
    "CodeSdkApiClient",
    "CodeSdkAsyncManifestResolutionProvider",
    "CodeSdkAsyncPackageLayoutProvider",
    "CodeSdkAsyncSourceOwnershipProvider",
    "CodeSdkCodeApiClient",
    "CodeSdkDiscoveryFile",
    "CodeSdkGeneratedMaterializationDeltaCapabilityClient",
    "CodeSdkGrammarProfileCapabilityClient",
    "CodeSdkManifestResolutionMatch",
    "CodeSdkManifestResolutionProvider",
    "CodeSdkModuleManifestProvider",
    "CodeSdkPackageLayoutBinding",
    "CodeSdkPackageLayoutCapabilityClient",
    "CodeSdkPackageLayoutProvider",
    "CodeSdkSectionDeltaCapabilityClient",
    "CodeSdkSemanticAnalysisCapabilityClient",
    "CodeSdkSemanticContractCatalog",
    "CodeSdkSemanticContractCapabilityClient",
    "CodeSdkSemanticScopeProvider",
    "CodeSdkAsyncSemanticScopeProvider",
    "CodeSdkSemanticSourceMeaningCapabilityClient",
    "CodeSdkSemanticOwnershipProvider",
    "CodeSdkSourceOwnershipCapabilityClient",
    "CodeSdkSourceOwnershipProvider",
    "GeneratedCodeSdkAsyncManifestResolutionProvider",
    "GeneratedCodeSdkAsyncPackageLayoutProvider",
    "GeneratedCodeSdkAsyncSemanticScopeProvider",
    "GeneratedCodeSdkAsyncSourceOwnershipProvider",
    "LocalCatalogCodeSdkSemanticScopeProvider",
    "LocalCodeSdkApiClient",
    "LocalCatalogCodeSdkPackageLayoutProvider",
    "LocalCatalogCodeSdkManifestResolutionProvider",
    "ServiceBackedCodeSdkSemanticOwnershipProvider",
    "SemanticContractCodeSdkModuleManifestProvider",
    "build_local_code_sdk_api_client",
]
