from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import TypeAlias, cast

from aware_code_sdk.dto import (
    CodePackageLayoutContract,
    CodePackageLayoutPathRole,
    CodePackagePathRole,
    CodeGrammarProfileDiagnostic,
    CodeGrammarProfileResolutionStatus,
    CodeSegmentRenderPolicyDiagnostic,
    CodeSegmentRenderPolicyResolutionStatus,
    CodeSemanticContract,
    CodeSemanticManifestResolutionDescriptor,
    CodeSemanticManifestResolutionMatch,
    CodeSemanticProviderBinding,
    ResolveCodeSemanticScopeRequest,
    ResolveCodeSemanticScopeResponse,
    DescribeCodePackageLayoutRequest,
    DescribeCodePackageLayoutResponse,
    DescribeCodeSemanticContractRequest,
    DescribeCodeSemanticContractResponse,
    DiscoverCodePackageLayoutsRequest,
    DiscoverCodePackageLayoutsResponse,
    FindCodeSemanticManifestResolutionRequest,
    FindCodeSemanticManifestResolutionResponse,
    FingerprintCodeGeneratedMaterializationDeltaRequest,
    FingerprintCodeGeneratedMaterializationDeltaResponse,
    FingerprintCodeSourceProjectionRequest,
    FingerprintCodeSourceProjectionResponse,
    CodeGrammarAnchorBindingResolutionStatus,
    NormalizeCodeSemanticContractRequest,
    NormalizeCodeSemanticContractResponse,
    NormalizeCodeGeneratedMaterializationDeltaRequest,
    NormalizeCodeGeneratedMaterializationDeltaResponse,
    NormalizeCodeSourceProjectionRequest,
    NormalizeCodeSourceProjectionResponse,
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
    ResolveCodeGeneratedMaterializationPackageDeltaRequest,
    ResolveCodeGeneratedMaterializationPackageDeltaResponse,
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
    ValidateCodeGeneratedMaterializationDeltaRequest,
    ValidateCodeGeneratedMaterializationDeltaResponse,
    ValidateCodeSourceProjectionRequest,
    ValidateCodeSourceProjectionResponse,
)
from aware_code_sdk.semantic_contract_spec import (
    render_code_semantic_contract_spec_declaration,
)
from aware_types import JsonObject, JsonValue

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


@dataclass(frozen=True, slots=True)
class CodeSdkPackageLayoutBinding:
    package_name: str | None = None
    package_root: str = "."
    sources_root: str | None = None
    surface: str | None = None
    manifest_relative_path: str | None = None
    package_fqn: str | None = None
    generated_roots: tuple[str, ...] = (".aware", "__pycache__")
    path_roles: tuple[CodePackageLayoutPathRole, ...] = ()
    metadata: Mapping[str, object] | None = None

    def to_layout_contract(self, *, provider_key: str) -> CodePackageLayoutContract:
        package_root = _normalize_relative_path(self.package_root)
        return CodePackageLayoutContract(
            package_name=self.package_name or self.package_fqn,
            package_root=package_root,
            sources_root=_optional_relative_path(self.sources_root),
            surface=_optional_surface(self.surface),
            generated_roots=[
                _normalize_layout_root(package_root=package_root, value=value)
                for value in self.generated_roots
            ],
            manifest_relative_path=_package_relative_path(
                package_root=package_root,
                value=self.manifest_relative_path,
            ),
            path_roles=list(self.path_roles)
            if self.path_roles
            else _default_path_roles(
                package_root=package_root,
                sources_root=self.sources_root,
                provider_key=provider_key,
            ),
            metadata=_json_object(
                _layout_metadata(
                    provider_key=provider_key,
                    package_fqn=self.package_fqn,
                    metadata=self.metadata,
                )
            ),
        )


PackageLayoutInput: TypeAlias = CodePackageLayoutContract | CodeSdkPackageLayoutBinding


@dataclass(frozen=True, slots=True)
class CodeSdkManifestResolutionMatch:
    provider_key: str
    semantic_contract: CodeSemanticContract
    manifest_resolution: CodeSemanticManifestResolutionDescriptor
    semantic_contract_module: str | None = None


@dataclass(frozen=True, slots=True)
class CodeSdkSemanticContractCatalog:
    provider_key: str = "aware_code"
    provider_role: str = "code_semantic_contract"
    provider_name: str = "Aware Code"
    provider_module: str = "code"
    semantic_scope_keys: tuple[str, ...] = (
        "code.semantic_contract",
        "code.package_layout",
        "code.package_delta",
        "code.section_delta",
    )
    package_layouts: tuple[PackageLayoutInput, ...] = ()
    semantic_contracts: tuple[CodeSemanticContract, ...] = ()
    metadata: Mapping[str, object] | None = None
    _layouts_by_key: dict[str, CodePackageLayoutContract] = field(
        init=False,
        repr=False,
        compare=False,
    )
    _contracts_by_key: dict[str, CodeSemanticContract] = field(
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "_layouts_by_key", self._build_layout_index())
        object.__setattr__(self, "_contracts_by_key", self._build_contract_index())

    def semantic_contract(
        self,
        *,
        provider_key: str | None = None,
    ) -> CodeSemanticContract | None:
        key = _optional_key(provider_key)
        if key is not None:
            existing = self._contracts_by_key.get(key)
            if existing is not None:
                return existing
            if key != self.provider_key:
                return None

        if key is None and self.semantic_contracts:
            return self.semantic_contracts[0]

        return CodeSemanticContract(
            provider_key=self.provider_key,
            semantic_scope_keys=list(self.semantic_scope_keys),
            metadata=_json_object(
                {
                    "source": "aware_code_sdk.local_semantic_contract",
                    **dict(self.metadata or {}),
                }
            ),
        )

    def provider_binding(
        self,
        *,
        provider_key: str | None = None,
        package_name: str | None = None,
        package_fqn: str | None = None,
    ) -> CodeSemanticProviderBinding:
        contract = self.semantic_contract(provider_key=provider_key)
        resolved_provider_key = (
            contract.provider_key if contract is not None else self.provider_key
        )
        return CodeSemanticProviderBinding(
            provider_key=resolved_provider_key,
            provider_role=self.provider_role,
            provider_name=self.provider_name,
            provider_module=self.provider_module,
            package_fqn=package_fqn or package_name,
            semantic_package_metadata=_json_object(
                {"source": "aware_code_sdk.local_semantic_contract"}
            ),
        )

    def matching_manifest_resolution(
        self,
        *,
        provider_key: str | None = None,
        manifest_kind: str | None = None,
        filename: str | None = None,
        workspace_manifest_kind: str | None = None,
    ) -> tuple[CodeSdkManifestResolutionMatch, ...]:
        provider_filter = _optional_key(provider_key)
        manifest_filter = _optional_key(manifest_kind)
        filename_filter = _optional_key(filename)
        workspace_filter = _optional_key(workspace_manifest_kind)
        matches: list[CodeSdkManifestResolutionMatch] = []

        for contract in self._iter_semantic_contracts():
            if (
                provider_filter is not None
                and _optional_key(contract.provider_key) != provider_filter
            ):
                continue
            for descriptor in contract.manifest_resolution:
                if (
                    manifest_filter is not None
                    and _optional_key(descriptor.manifest_kind) != manifest_filter
                ):
                    continue
                if (
                    filename_filter is not None
                    and _optional_key(descriptor.filename) != filename_filter
                ):
                    continue
                if (
                    workspace_filter is not None
                    and _optional_key(descriptor.workspace_manifest_kind)
                    != workspace_filter
                ):
                    continue
                matches.append(
                    CodeSdkManifestResolutionMatch(
                        provider_key=contract.provider_key,
                        semantic_contract=contract,
                        manifest_resolution=descriptor,
                        semantic_contract_module=_metadata_string(
                            contract.metadata,
                            "semantic_contract_module",
                        ),
                    )
                )

        return tuple(
            sorted(
                matches,
                key=lambda item: (
                    item.manifest_resolution.priority,
                    item.provider_key,
                    item.manifest_resolution.semantic_owner,
                    item.manifest_resolution.manifest_kind,
                    item.manifest_resolution.filename,
                ),
            )
        )

    def layout_contract(
        self,
        *,
        provider_key: str | None = None,
        package_name: str | None = None,
        package_root: str | None = None,
        package_fqn: str | None = None,
    ) -> CodePackageLayoutContract:
        existing = self._layout_for(package_name=package_name, package_fqn=package_fqn)
        if existing is not None:
            return existing
        binding = CodeSdkPackageLayoutBinding(
            package_name=package_name or package_fqn,
            package_root=package_root or ".",
        )
        return binding.to_layout_contract(
            provider_key=provider_key or self.provider_key
        )

    def validate_semantic_contract(
        self,
        semantic_contract: CodeSemanticContract,
    ) -> tuple[str, ...]:
        diagnostics: list[str] = []
        if not semantic_contract.provider_key.strip():
            diagnostics.append("provider_key is required.")
        seen_resolution: set[tuple[str, str, str, str | None]] = set()
        for index, item in enumerate(semantic_contract.manifest_resolution):
            for field_name, value in (
                ("semantic_owner", item.semantic_owner),
                ("manifest_kind", item.manifest_kind),
                ("filename", item.filename),
                ("contract", item.contract),
                ("loader_module", item.loader_module),
                ("loader_name", item.loader_name),
            ):
                if value is None or not value.strip():
                    diagnostics.append(
                        f"manifest_resolution[{index}].{field_name} is required."
                    )
            if (
                item.code_package_surface is None
                or not item.code_package_surface.strip()
            ) and not item.code_package_surface_by_package_kind:
                diagnostics.append(
                    f"manifest_resolution[{index}] must declare "
                    "code_package_surface or code_package_surface_by_package_kind."
                )
            code_package_surface = item.code_package_surface or ""
            if (
                code_package_surface.strip()
                and code_package_surface.strip() not in _CODE_PACKAGE_SURFACE_VALUES
            ):
                diagnostics.append(
                    "manifest_resolution"
                    f"[{index}].code_package_surface is not a valid "
                    f"CodePackageSurface: {item.code_package_surface!r}."
                )
            diagnostics.extend(
                _code_package_surface_by_package_kind_diagnostics(
                    index=index,
                    value=item.code_package_surface_by_package_kind,
                )
            )
            key = (
                item.semantic_owner,
                item.manifest_kind,
                item.filename,
                item.workspace_manifest_kind,
            )
            if key in seen_resolution:
                diagnostics.append(
                    "duplicate manifest resolution: "
                    f"{item.semantic_owner}/{item.manifest_kind}/"
                    f"{item.filename}/{item.workspace_manifest_kind or ''}"
                )
            seen_resolution.add(key)
        return tuple(diagnostics)

    def validate_layout_contract(
        self,
        layout_contract: CodePackageLayoutContract,
    ) -> tuple[str, ...]:
        diagnostics: list[str] = []
        if not layout_contract.package_root.strip():
            diagnostics.append("package_root is required.")
        if (
            layout_contract.surface is not None
            and layout_contract.surface.strip()
            and layout_contract.surface.strip() not in _CODE_PACKAGE_SURFACE_VALUES
        ):
            diagnostics.append(
                f"surface is not a valid CodePackageSurface: "
                f"{layout_contract.surface!r}."
            )
        for index, path_role in enumerate(layout_contract.path_roles):
            if not path_role.include_patterns:
                diagnostics.append(
                    f"path_roles[{index}] must include at least one pattern."
                )
        return tuple(diagnostics)

    def discover_layout_contracts(
        self,
        *,
        manifest_paths: Iterable[str],
    ) -> tuple[tuple[CodePackageLayoutContract, ...], tuple[str, ...]]:
        layout_contracts: list[CodePackageLayoutContract] = []
        diagnostics: list[str] = []
        for manifest_path in manifest_paths:
            normalized_manifest_path = _normalize_relative_path(manifest_path)
            layout_contract = self._layout_for_manifest_path(
                manifest_path=normalized_manifest_path
            )
            if layout_contract is None:
                diagnostics.append(
                    "Code SDK package layout catalog has no manifest path: "
                    f"{normalized_manifest_path}"
                )
                continue
            layout_contracts.append(layout_contract)
        return tuple(layout_contracts), tuple(diagnostics)

    def _build_layout_index(self) -> dict[str, CodePackageLayoutContract]:
        layouts: dict[str, CodePackageLayoutContract] = {}
        for layout_input in self.package_layouts:
            layout = (
                layout_input.to_layout_contract(provider_key=self.provider_key)
                if isinstance(layout_input, CodeSdkPackageLayoutBinding)
                else layout_input
            )
            for key in _layout_keys(layout):
                layouts[key] = layout
        return layouts

    def _layout_for(
        self,
        *,
        package_name: str | None,
        package_fqn: str | None,
    ) -> CodePackageLayoutContract | None:
        for value in (package_name, package_fqn):
            key = _optional_key(value)
            if key is not None and key in self._layouts_by_key:
                return self._layouts_by_key[key]
        return None

    def _layout_for_manifest_path(
        self,
        *,
        manifest_path: str,
    ) -> CodePackageLayoutContract | None:
        for layout in self._layouts_by_key.values():
            if _optional_key(layout.manifest_relative_path) == manifest_path:
                return layout
        return None

    def _build_contract_index(self) -> dict[str, CodeSemanticContract]:
        contracts: dict[str, CodeSemanticContract] = {}
        for contract in self.semantic_contracts:
            key = _optional_key(contract.provider_key)
            if key is not None:
                contracts[key] = contract
        return contracts

    def _iter_semantic_contracts(self) -> tuple[CodeSemanticContract, ...]:
        if self.semantic_contracts:
            return self.semantic_contracts
        default = self.semantic_contract()
        return (default,) if default is not None else ()


class LocalCodeSdkSemanticContractCapabilityClient:
    def __init__(self, *, catalog: CodeSdkSemanticContractCatalog) -> None:
        self._catalog = catalog

    async def describe(
        self,
        request: DescribeCodeSemanticContractRequest,
    ) -> DescribeCodeSemanticContractResponse:
        contract = self._catalog.semantic_contract(provider_key=request.provider_key)
        if contract is None:
            return DescribeCodeSemanticContractResponse(
                request_id=request.request_id,
                success=False,
                error=f"Unknown Code semantic contract provider: {request.provider_key}",
            )
        provider_binding = self._catalog.provider_binding(
            provider_key=request.provider_key,
            package_name=request.package_name,
            package_fqn=request.package_fqn,
        )
        return DescribeCodeSemanticContractResponse(
            request_id=request.request_id,
            success=True,
            semantic_contract=contract,
            layout_contract=(
                self._catalog.layout_contract(
                    provider_key=contract.provider_key,
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

    async def validate(
        self,
        request: ValidateCodeSemanticContractRequest,
    ) -> ValidateCodeSemanticContractResponse:
        diagnostics = self._catalog.validate_semantic_contract(
            request.semantic_contract
        )
        return ValidateCodeSemanticContractResponse(
            request_id=request.request_id,
            success=not diagnostics,
            valid=not diagnostics,
            diagnostics=list(diagnostics),
        )

    async def find_manifest_resolution(
        self,
        request: FindCodeSemanticManifestResolutionRequest,
    ) -> FindCodeSemanticManifestResolutionResponse:
        return FindCodeSemanticManifestResolutionResponse(
            request_id=request.request_id,
            success=True,
            matches=[
                CodeSemanticManifestResolutionMatch(
                    provider_key=match.provider_key,
                    semantic_contract=match.semantic_contract,
                    manifest_resolution=match.manifest_resolution,
                    semantic_contract_module=match.semantic_contract_module,
                )
                for match in self._catalog.matching_manifest_resolution(
                    provider_key=request.provider_key,
                    manifest_kind=request.manifest_kind,
                    filename=request.filename,
                    workspace_manifest_kind=request.workspace_manifest_kind,
                )
            ],
        )

    async def resolve_semantic_scope(
        self,
        request: ResolveCodeSemanticScopeRequest,
    ) -> ResolveCodeSemanticScopeResponse:
        return ResolveCodeSemanticScopeResponse(
            request_id=request.request_id,
            success=False,
            error=(
                "Catalog-backed local Code SDK cannot execute semantic scope "
                "providers; provide a service-backed Code SDK client."
            ),
            resolved=False,
            diagnostics=["semantic_scope_requires_code_service"],
            resolution_count=0,
        )

    async def normalize(
        self,
        request: NormalizeCodeSemanticContractRequest,
    ) -> NormalizeCodeSemanticContractResponse:
        return NormalizeCodeSemanticContractResponse(
            request_id=request.request_id,
            success=True,
            semantic_contract=request.semantic_contract,
        )


class LocalCodeSdkPackageLayoutCapabilityClient:
    def __init__(self, *, catalog: CodeSdkSemanticContractCatalog) -> None:
        self._catalog = catalog

    async def describe(
        self,
        request: DescribeCodePackageLayoutRequest,
    ) -> DescribeCodePackageLayoutResponse:
        return DescribeCodePackageLayoutResponse(
            request_id=request.request_id,
            success=True,
            layout_contract=self._catalog.layout_contract(
                package_name=request.package_name,
                package_root=request.package_root,
                package_fqn=request.package_fqn,
            ),
        )

    async def discover(
        self,
        request: DiscoverCodePackageLayoutsRequest,
    ) -> DiscoverCodePackageLayoutsResponse:
        layout_contracts, diagnostics = self._catalog.discover_layout_contracts(
            manifest_paths=request.manifest_paths,
        )
        return DiscoverCodePackageLayoutsResponse(
            request_id=request.request_id,
            success=not diagnostics,
            layout_contracts=list(layout_contracts),
            diagnostics=list(diagnostics),
        )

    async def validate(
        self,
        request: ValidateCodePackageLayoutRequest,
    ) -> ValidateCodePackageLayoutResponse:
        diagnostics = self._catalog.validate_layout_contract(request.layout_contract)
        return ValidateCodePackageLayoutResponse(
            request_id=request.request_id,
            success=not diagnostics,
            valid=not diagnostics,
            diagnostics=list(diagnostics),
        )


class LocalCodeSdkSemanticAnalysisCapabilityClient:
    async def preview_package_delta(
        self,
        request: PreviewCodeSemanticAnalysisPackageDeltaRequest,
    ) -> PreviewCodeSemanticAnalysisPackageDeltaResponse:
        return PreviewCodeSemanticAnalysisPackageDeltaResponse(
            request_id=request.request_id,
            success=False,
            error=(
                "Catalog-backed local Code SDK cannot execute "
                "semantic_analysis providers; provide a service-backed Code SDK "
                "client."
            ),
            previewed=False,
            provider_key=request.provider_key,
            semantic_owner=request.semantic_owner,
            blockers=["semantic_analysis_provider_execution_unavailable"],
            available=False,
        )


class LocalCodeSdkSemanticSourceMeaningCapabilityClient:
    async def resolve(
        self,
        request: ResolveCodeSemanticSourceMeaningRequest,
    ) -> ResolveCodeSemanticSourceMeaningResponse:
        return ResolveCodeSemanticSourceMeaningResponse(
            request_id=request.request_id,
            success=False,
            error=(
                "Catalog-backed local Code SDK cannot resolve semantic source "
                "meaning; provide a service-backed Code SDK client."
            ),
            resolved=False,
            status="blocked",
            diagnostics=["semantic_source_meaning_requires_code_service"],
            provider_key=request.contract.provider_key,
            semantic_owner=request.contract.semantic_owner,
            binding_count=len(request.contract.bindings),
            source_index_evidence=JsonObject({}),
        )

    async def resolve_delta(
        self,
        request: ResolveCodeSemanticSourceDeltaMeaningRequest,
    ) -> ResolveCodeSemanticSourceDeltaMeaningResponse:
        return ResolveCodeSemanticSourceDeltaMeaningResponse(
            request_id=request.request_id,
            success=False,
            error=(
                "Catalog-backed local Code SDK cannot resolve semantic source "
                "delta meaning; provide a service-backed Code SDK client."
            ),
            resolved=False,
            status="blocked",
            diagnostics=["semantic_source_delta_meaning_requires_code_service"],
            required_context=["code_service"],
            provider_key=request.contract.provider_key,
            semantic_owner=request.contract.semantic_owner,
            binding_count=len(request.contract.bindings),
            source_index_evidence=JsonObject({}),
        )


class LocalCodeSdkGrammarProfileCapabilityClient:
    async def resolve(
        self,
        request: ResolveCodeGrammarProfileRequest,
    ) -> ResolveCodeGrammarProfileResponse:
        return ResolveCodeGrammarProfileResponse(
            request_id=request.request_id,
            success=False,
            error=(
                "Catalog-backed local Code SDK cannot resolve grammar profiles; "
                "provide a service-backed Code SDK client."
            ),
            status=CodeGrammarProfileResolutionStatus.blocked,
            resolved=False,
            diagnostics=[
                CodeGrammarProfileDiagnostic(
                    reason="grammar_profile_requires_code_service",
                    message=(
                        "Catalog-backed local Code SDK cannot execute the "
                        "Aware grammar backend."
                    ),
                )
            ],
            provider_count=len(request.semantic_contracts),
            lane_count=sum(
                len(contract.syntax_lanes)
                for contract in request.semantic_contracts
            ),
            rule_count=0,
        )


class LocalCodeSdkGrammarAnchorBindingCapabilityClient:
    async def validate(
        self,
        request: ValidateCodeGrammarAnchorBindingRequest,
    ) -> ValidateCodeGrammarAnchorBindingResponse:
        return ValidateCodeGrammarAnchorBindingResponse(
            request_id=request.request_id,
            success=False,
            error=(
                "Catalog-backed local Code SDK cannot validate grammar-anchor "
                "bindings; provide a service-backed Code SDK client."
            ),
            valid=False,
            status=CodeGrammarAnchorBindingResolutionStatus.blocked,
            diagnostics=["grammar_anchor_binding_requires_code_service"],
            binding_count=len(request.bindings),
            fixture_count=len(request.fixtures),
            evidence=[],
        )

    async def resolve_evidence(
        self,
        request: ResolveCodeGrammarAnchorBindingEvidenceRequest,
    ) -> ResolveCodeGrammarAnchorBindingEvidenceResponse:
        return ResolveCodeGrammarAnchorBindingEvidenceResponse(
            request_id=request.request_id,
            success=False,
            error=(
                "Catalog-backed local Code SDK cannot resolve grammar-anchor "
                "binding evidence; provide a service-backed Code SDK client."
            ),
            resolved=False,
            status=CodeGrammarAnchorBindingResolutionStatus.blocked,
            diagnostics=["grammar_anchor_binding_evidence_requires_code_service"],
            evidence=[],
            graph_change_drafts=[],
            text_targets=[],
            binding_count=len(request.bindings),
            fixture_count=len(request.fixtures),
            evidence_count=0,
        )


class LocalCodeSdkGrammarAnchorRenderDeltaCapabilityClient:
    async def resolve_delta(
        self,
        request: ResolveCodeGrammarAnchorRenderDeltaRequest,
    ) -> ResolveCodeGrammarAnchorRenderDeltaResponse:
        return ResolveCodeGrammarAnchorRenderDeltaResponse(
            request_id=request.request_id,
            success=False,
            error=(
                "Catalog-backed local Code SDK cannot resolve grammar-anchor "
                "render deltas; provide a service-backed Code SDK client."
            ),
            resolved=False,
            status=CodeGrammarAnchorBindingResolutionStatus.blocked,
            diagnostics=["grammar_anchor_render_delta_requires_code_service"],
            render_entries=[],
            package_delta=None,
            binding_count=len(request.bindings),
            source_count=len(request.sources),
            replacement_count=len(request.replacements),
            render_entry_count=0,
            path_count=0,
        )


class LocalCodeSdkSectionDeltaCapabilityClient:
    async def resolve_render_policy(
        self,
        request: ResolveCodeSegmentRenderPolicyRequest,
    ) -> ResolveCodeSegmentRenderPolicyResponse:
        return ResolveCodeSegmentRenderPolicyResponse(
            request_id=request.request_id,
            success=False,
            error=(
                "Catalog-backed local Code SDK cannot resolve segment render "
                "policies; provide a service-backed Code SDK client."
            ),
            status=CodeSegmentRenderPolicyResolutionStatus.blocked,
            resolved=False,
            policies=[],
            diagnostics=[
                CodeSegmentRenderPolicyDiagnostic(
                    reason="segment_render_policy_requires_code_service",
                    message=(
                        "Catalog-backed local Code SDK cannot execute the "
                        "Code segment render policy resolver."
                    ),
                    language=request.language,
                    section_type=request.section_type,
                    segment_name=request.segment_name,
                )
            ],
            policy_count=0,
        )


class LocalCodeSdkSourceProjectionCapabilityClient:
    async def validate(
        self,
        request: ValidateCodeSourceProjectionRequest,
    ) -> ValidateCodeSourceProjectionResponse:
        return ValidateCodeSourceProjectionResponse(
            request_id=request.request_id,
            success=False,
            valid=False,
            diagnostics=["source_projection_requires_code_service"],
            event_count=len(request.projection.events),
            action_count=len(request.projection.action_bindings),
            has_delta_set=request.result is not None
            and request.result.delta_set is not None,
        )

    async def normalize(
        self,
        request: NormalizeCodeSourceProjectionRequest,
    ) -> NormalizeCodeSourceProjectionResponse:
        return NormalizeCodeSourceProjectionResponse(
            request_id=request.request_id,
            success=True,
            projection=request.projection,
            result=request.result,
        )

    async def fingerprint(
        self,
        request: FingerprintCodeSourceProjectionRequest,
    ) -> FingerprintCodeSourceProjectionResponse:
        return FingerprintCodeSourceProjectionResponse(
            request_id=request.request_id,
            success=False,
            error=(
                "Catalog-backed local Code SDK cannot fingerprint source "
                "projection; provide a service-backed Code SDK client."
            ),
            event_count=len(request.projection.events),
            action_count=len(request.projection.action_bindings),
            has_delta_set=request.result is not None
            and request.result.delta_set is not None,
        )

    async def resolve_package_delta(
        self,
        request: ResolveCodeSourceProjectionPackageDeltaRequest,
    ) -> ResolveCodeSourceProjectionPackageDeltaResponse:
        return ResolveCodeSourceProjectionPackageDeltaResponse(
            request_id=request.request_id,
            success=False,
            resolved=False,
            diagnostics=["source_projection_package_delta_requires_code_service"],
            event_count=len(request.projection.events),
            action_count=len(request.projection.action_bindings),
            skipped_event_count=len(request.result.skipped_events),
            entry_count=(
                len(request.result.delta_set.entries)
                if request.result.delta_set is not None
                else 0
            ),
        )


class LocalCodeSdkGeneratedMaterializationDeltaCapabilityClient:
    async def validate(
        self,
        request: ValidateCodeGeneratedMaterializationDeltaRequest,
    ) -> ValidateCodeGeneratedMaterializationDeltaResponse:
        result = request.result
        return ValidateCodeGeneratedMaterializationDeltaResponse(
            request_id=request.request_id,
            success=False,
            valid=False,
            diagnostics=["generated_materialization_delta_requires_code_service"],
            event_count=len(request.delta_request.events),
            action_count=len(request.delta_request.action_bindings),
            target_count=len(request.delta_request.targets),
            entry_count=len(result.entries) if result is not None else 0,
            skipped_target_count=(
                len(result.skipped_targets) if result is not None else 0
            ),
            renderer_operation_count=(
                sum(len(entry.renderer_operations) for entry in result.entries)
                if result is not None
                else 0
            ),
            package_delta_entry_count=(
                sum(1 for entry in result.entries if entry.package_delta is not None)
                if result is not None
                else 0
            ),
            section_delta_entry_count=(
                sum(1 for entry in result.entries if entry.section_delta is not None)
                if result is not None
                else 0
            ),
        )

    async def normalize(
        self,
        request: NormalizeCodeGeneratedMaterializationDeltaRequest,
    ) -> NormalizeCodeGeneratedMaterializationDeltaResponse:
        return NormalizeCodeGeneratedMaterializationDeltaResponse(
            request_id=request.request_id,
            success=True,
            delta_request=request.delta_request,
            result=request.result,
        )

    async def fingerprint(
        self,
        request: FingerprintCodeGeneratedMaterializationDeltaRequest,
    ) -> FingerprintCodeGeneratedMaterializationDeltaResponse:
        result = request.result
        return FingerprintCodeGeneratedMaterializationDeltaResponse(
            request_id=request.request_id,
            success=False,
            error=(
                "Catalog-backed local Code SDK cannot fingerprint generated "
                "materialization deltas; provide a service-backed Code SDK client."
            ),
            fingerprint=None,
            event_count=len(request.delta_request.events),
            action_count=len(request.delta_request.action_bindings),
            target_count=len(request.delta_request.targets),
            entry_count=len(result.entries) if result is not None else 0,
            renderer_operation_count=(
                sum(len(entry.renderer_operations) for entry in result.entries)
                if result is not None
                else 0
            ),
            package_delta_entry_count=(
                sum(1 for entry in result.entries if entry.package_delta is not None)
                if result is not None
                else 0
            ),
            section_delta_entry_count=(
                sum(1 for entry in result.entries if entry.section_delta is not None)
                if result is not None
                else 0
            ),
        )

    async def resolve_package_delta(
        self,
        request: ResolveCodeGeneratedMaterializationPackageDeltaRequest,
    ) -> ResolveCodeGeneratedMaterializationPackageDeltaResponse:
        result = request.result
        return ResolveCodeGeneratedMaterializationPackageDeltaResponse(
            request_id=request.request_id,
            success=False,
            resolved=False,
            diagnostics=[
                "generated_materialization_package_delta_requires_code_service"
            ],
            event_count=len(request.delta_request.events),
            action_count=len(request.delta_request.action_bindings),
            target_count=len(request.delta_request.targets),
            skipped_target_count=len(result.skipped_targets),
            entry_count=len(result.entries),
            renderer_operation_count=sum(
                len(entry.renderer_operations) for entry in result.entries
            ),
            package_delta_entry_count=sum(
                1 for entry in result.entries if entry.package_delta is not None
            ),
            section_delta_entry_count=sum(
                1 for entry in result.entries if entry.section_delta is not None
            ),
        )


class LocalCodeSdkCodeApiClient:
    def __init__(self, *, catalog: CodeSdkSemanticContractCatalog) -> None:
        self.grammar_anchor_binding = (
            LocalCodeSdkGrammarAnchorBindingCapabilityClient()
        )
        self.grammar_anchor_render_delta = (
            LocalCodeSdkGrammarAnchorRenderDeltaCapabilityClient()
        )
        self.grammar_profile = LocalCodeSdkGrammarProfileCapabilityClient()
        self.semantic_contract = LocalCodeSdkSemanticContractCapabilityClient(
            catalog=catalog
        )
        self.semantic_analysis = LocalCodeSdkSemanticAnalysisCapabilityClient()
        self.semantic_source_meaning = (
            LocalCodeSdkSemanticSourceMeaningCapabilityClient()
        )
        self.section_delta = LocalCodeSdkSectionDeltaCapabilityClient()
        self.source_projection = LocalCodeSdkSourceProjectionCapabilityClient()
        self.generated_materialization_delta = (
            LocalCodeSdkGeneratedMaterializationDeltaCapabilityClient()
        )
        self.package_layout = LocalCodeSdkPackageLayoutCapabilityClient(
            catalog=catalog
        )


class LocalCodeSdkApiClient:
    def __init__(self, *, catalog: CodeSdkSemanticContractCatalog | None = None) -> None:
        self.catalog = catalog or CodeSdkSemanticContractCatalog()
        self.code = LocalCodeSdkCodeApiClient(catalog=self.catalog)


def build_local_code_sdk_api_client(
    *,
    catalog: CodeSdkSemanticContractCatalog | None = None,
    package_layouts: Iterable[PackageLayoutInput] = (),
) -> LocalCodeSdkApiClient:
    resolved_catalog = catalog or CodeSdkSemanticContractCatalog(
        package_layouts=tuple(package_layouts)
    )
    return LocalCodeSdkApiClient(catalog=resolved_catalog)


def _default_path_roles(
    *,
    package_root: str,
    sources_root: str | None,
    provider_key: str,
) -> list[CodePackageLayoutPathRole]:
    source_prefix = _package_relative_path(package_root=package_root, value=sources_root)
    authored_patterns = (
        [
            f"{source_prefix}/*.aware",
            f"{source_prefix}/**/*.aware",
            f"{source_prefix}/*.py",
            f"{source_prefix}/**/*.py",
        ]
        if source_prefix is not None and source_prefix != "."
        else ["**/*.aware", "**/*.py", "**/*.toml"]
    )
    return [
        CodePackageLayoutPathRole(
            role=CodePackagePathRole.authored_source,
            include_patterns=authored_patterns,
            exclude_patterns=["**/.aware/**", "**/__pycache__/**"],
            semantic_owner_hints=[provider_key],
            metadata=_json_object(
                {"source": "aware_code_sdk.local_semantic_contract.default_layout"}
            ),
        ),
        CodePackageLayoutPathRole(
            role=CodePackagePathRole.generated_metadata,
            include_patterns=[".aware/**", "**/.aware/**"],
            semantic_owner_hints=[provider_key],
            metadata=_json_object(
                {"source": "aware_code_sdk.local_semantic_contract.default_layout"}
            ),
        ),
        CodePackageLayoutPathRole(
            role=CodePackagePathRole.generated_code,
            include_patterns=["__pycache__/**", "**/__pycache__/**"],
            semantic_owner_hints=[provider_key],
            metadata=_json_object(
                {"source": "aware_code_sdk.local_semantic_contract.default_layout"}
            ),
        ),
    ]


def _layout_keys(layout: CodePackageLayoutContract) -> tuple[str, ...]:
    return tuple(
        key
        for key in (
            _optional_key(layout.package_name),
            _metadata_string(layout.metadata, "package_fqn"),
            _optional_key(layout.manifest_relative_path),
            _optional_key(layout.package_root),
        )
        if key is not None
    )


def _optional_key(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None


def _optional_relative_path(value: str | None) -> str | None:
    if value is None:
        return None
    return _normalize_relative_path(value)


def _optional_surface(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    if text not in _CODE_PACKAGE_SURFACE_VALUES:
        raise ValueError(f"Code package surface is not supported: {value!r}.")
    return text


def _normalize_relative_path(value: str) -> str:
    text = value.strip().replace("\\", "/")
    parts: list[str] = []
    for part in text.split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            raise ValueError("Code SDK package paths must not escape their root.")
        parts.append(part)
    return "/".join(parts) or "."


def _normalize_layout_root(*, package_root: str, value: str) -> str:
    root = _normalize_relative_path(value)
    if package_root == ".":
        return root
    if root == package_root or root.startswith(package_root.rstrip("/") + "/"):
        return root
    return f"{package_root.rstrip('/')}/{root}"


def _package_relative_path(*, package_root: str, value: str | None) -> str | None:
    path = _optional_relative_path(value)
    if path is None:
        return None
    if package_root == ".":
        return path
    if path == package_root:
        return "."
    prefix = package_root.rstrip("/") + "/"
    if path.startswith(prefix):
        return path.removeprefix(prefix) or "."
    return path


def _metadata_string(metadata: JsonObject | None, key: str) -> str | None:
    if metadata is None:
        return None
    value = metadata.get(key)
    return value if isinstance(value, str) else None


def _code_package_surface_by_package_kind_diagnostics(
    *,
    index: int,
    value: Mapping[str, object] | None,
) -> list[str]:
    if value is None:
        return []
    diagnostics: list[str] = []
    for package_kind, surface in sorted(value.items()):
        if not package_kind.strip():
            diagnostics.append(
                f"manifest_resolution[{index}]."
                "code_package_surface_by_package_kind key is required."
            )
            continue
        if not isinstance(surface, str) or not surface.strip():
            diagnostics.append(
                f"manifest_resolution[{index}]."
                f"code_package_surface_by_package_kind[{package_kind!r}] "
                "must be a non-empty string."
            )
            continue
        if surface.strip() not in _CODE_PACKAGE_SURFACE_VALUES:
            diagnostics.append(
                f"manifest_resolution[{index}]."
                f"code_package_surface_by_package_kind[{package_kind!r}] "
                f"is not a valid CodePackageSurface: {surface!r}."
            )
    return diagnostics


def _layout_metadata(
    *,
    provider_key: str,
    package_fqn: str | None,
    metadata: Mapping[str, object] | None,
) -> dict[str, object]:
    values: dict[str, object] = {
        "provider_key": provider_key,
        "source": "aware_code_sdk.local_semantic_contract",
        **dict(metadata or {}),
    }
    if package_fqn is not None:
        values["package_fqn"] = package_fqn
    return values


def _json_object(values: Mapping[str, object]) -> JsonObject:
    return JsonObject(cast(dict[str, JsonValue], dict(values)))


__all__ = [
    "CodeSdkManifestResolutionMatch",
    "CodeSdkPackageLayoutBinding",
    "CodeSdkSemanticContractCatalog",
    "LocalCodeSdkApiClient",
    "LocalCodeSdkCodeApiClient",
    "LocalCodeSdkPackageLayoutCapabilityClient",
    "LocalCodeSdkSectionDeltaCapabilityClient",
    "LocalCodeSdkSemanticContractCapabilityClient",
    "PackageLayoutInput",
    "build_local_code_sdk_api_client",
]
