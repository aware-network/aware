from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest

from aware_meta.semantic_contract import AWARE_META_SEMANTIC_CONTRACT
from aware_types import JsonObject
from aware_code_sdk import (
    AwareCodeSdk,
    CodeGrammarBackendDescriptor,
    CodeGrammarProfile,
    CodeGrammarProfileDiagnostic,
    CodeGrammarProfileResolutionStatus,
    CodeGrammarRuleBinding,
    CodePackageDelta,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
    CodePackageLayoutContract,
    CodePackageLayoutPathRole,
    CodePackagePathRole,
    CodeSdkPackageLayoutBinding,
    CodeSdkSemanticContractCatalog,
    CodeSemanticContract,
    CodeSemanticProviderBinding,
    CodeSemanticManifestResolutionDescriptor,
    CodeSemanticMaterializationScopeDependency,
    CodeSemanticPackageRoleDescriptor,
    CodeSectionDeltaEntry,
    CodeSegmentContentDomain,
    CodeSegmentRenderPolicyResolutionStatus,
    CodeSourceProjectionRequest,
    CodeSourceProjectionResult,
    DescribeCodePackageLayoutRequest,
    DescribeCodeSemanticContractRequest,
    FindCodeSemanticManifestResolutionRequest,
    NormalizeCodeSemanticContractRequest,
    PreviewCodeSemanticAnalysisPackageDeltaRequest,
    PreviewCodeSemanticAnalysisPackageDeltaResponse,
    ResolveCodeGrammarProfileRequest,
    ResolveCodeGrammarProfileResponse,
    ResolveCodeSegmentRenderPolicyRequest,
    ResolveCodeSegmentRenderPolicyResponse,
    CodeSemanticScopePackageRef,
    ResolveCodeSemanticScopeRequest,
    ResolveCodeSourceProjectionPackageDeltaRequest,
    ResolveCodeSourceProjectionPackageDeltaResponse,
    ValidateCodePackageLayoutRequest,
    ValidateCodeSemanticContractRequest,
    build_local_code_sdk_api_client,
    code_semantic_generated_code_package_declarations,
    normalize_code_semantic_contract,
    render_code_semantic_contract_spec_declaration,
)


def _package_delta(*relative_paths: str) -> CodePackageDelta:
    return CodePackageDelta(
        package_name="aware-code-test",
        package_root=".",
        paths=[
            CodePackageDeltaPath(
                relative_path=relative_path,
                kind=CodePackageDeltaKind.update,
                content_text=f"{relative_path}\n",
            )
            for relative_path in relative_paths
        ],
    )


class _FakeSemanticAnalysisCapabilityClient:
    def __init__(self) -> None:
        self.requests: list[PreviewCodeSemanticAnalysisPackageDeltaRequest] = []

    async def preview_package_delta(
        self,
        request: PreviewCodeSemanticAnalysisPackageDeltaRequest,
    ) -> PreviewCodeSemanticAnalysisPackageDeltaResponse:
        self.requests.append(request)
        return PreviewCodeSemanticAnalysisPackageDeltaResponse(
            success=True,
            previewed=True,
            provider_key=request.provider_key,
            semantic_owner=request.semantic_owner,
            available=True,
        )


class _FakeSourceProjectionCapabilityClient:
    def __init__(self) -> None:
        self.resolve_requests: list[
            ResolveCodeSourceProjectionPackageDeltaRequest
        ] = []

    async def resolve_package_delta(
        self,
        request: ResolveCodeSourceProjectionPackageDeltaRequest,
    ) -> ResolveCodeSourceProjectionPackageDeltaResponse:
        self.resolve_requests.append(request)
        return ResolveCodeSourceProjectionPackageDeltaResponse(
            success=True,
            resolved=True,
            path_count=1,
        )


class _FakeGrammarProfileCapabilityClient:
    def __init__(self) -> None:
        self.requests: list[ResolveCodeGrammarProfileRequest] = []

    async def resolve(
        self,
        request: ResolveCodeGrammarProfileRequest,
    ) -> ResolveCodeGrammarProfileResponse:
        self.requests.append(request)
        return ResolveCodeGrammarProfileResponse(
            success=True,
            status=CodeGrammarProfileResolutionStatus.resolved,
            resolved=True,
            profile=CodeGrammarProfile(
                profile_key=request.profile_key or "demo.profile",
                language=request.language,
                backend_key=request.backend_key,
            ),
        )


class _FakeSectionDeltaCapabilityClient:
    def __init__(self) -> None:
        self.render_policy_requests: list[
            ResolveCodeSegmentRenderPolicyRequest
        ] = []

    async def resolve_render_policy(
        self,
        request: ResolveCodeSegmentRenderPolicyRequest,
    ) -> ResolveCodeSegmentRenderPolicyResponse:
        self.render_policy_requests.append(request)
        return ResolveCodeSegmentRenderPolicyResponse(
            success=True,
            status=CodeSegmentRenderPolicyResolutionStatus.resolved,
            resolved=True,
            policy_count=1,
        )


class _FakeCodeApiClient:
    def __init__(self) -> None:
        self.grammar_profile = _FakeGrammarProfileCapabilityClient()
        self.section_delta = _FakeSectionDeltaCapabilityClient()
        self.semantic_analysis = _FakeSemanticAnalysisCapabilityClient()
        self.source_projection = _FakeSourceProjectionCapabilityClient()


class _FakeApiClient:
    def __init__(self) -> None:
        self.code = _FakeCodeApiClient()


@pytest.mark.asyncio
async def test_local_code_sdk_describes_semantic_contract_without_service_runtime() -> None:
    api_client = build_local_code_sdk_api_client()

    response = await api_client.code.semantic_contract.describe(
        DescribeCodeSemanticContractRequest(include_layout=False)
    )

    assert response.success is True
    assert response.semantic_contract is not None
    assert response.semantic_contract.provider_key == "aware_code"
    assert response.layout_contract is None
    assert response.provider_binding is not None
    assert response.provider_binding.provider_key == "aware_code"


@pytest.mark.asyncio
async def test_local_code_sdk_renders_semantic_contract_spec_declaration() -> None:
    contract = CodeSemanticContract(
        provider_key="aware_demo",
        package_roles=[
            CodeSemanticPackageRoleDescriptor(
                role="aware_demo.provider",
                contract="aware.semantic_provider",
                package_kind="runtime",
                owns_manifest_kinds=["aware_demo_toml"],
            )
        ],
        manifest_resolution=[
            CodeSemanticManifestResolutionDescriptor(
                semantic_owner="aware_demo.provider",
                manifest_kind="aware_demo_toml",
                filename="aware.demo.toml",
                contract="aware.demo",
                loader_module="aware_demo.manifest",
                loader_name="load_aware_demo_toml",
                workspace_manifest_kind="demo",
                package_role="aware_demo.provider",
                semantic_package_family="demo",
                semantic_package_kind="demo_package",
                semantic_projection_name="DemoPackage",
                semantic_root_kind="demo",
                code_package_surface="runtime",
            )
        ],
    )
    sdk = AwareCodeSdk.local(
        catalog=CodeSdkSemanticContractCatalog(
            provider_key="aware_demo",
            semantic_contracts=(contract,),
        )
    )

    response = await sdk.describe_semantic_contract(
        DescribeCodeSemanticContractRequest(
            provider_key="aware_demo",
            package_name="aware-demo",
            include_layout=False,
            include_spec_declaration=True,
        )
    )
    helper_result = await sdk.describe_semantic_contract_spec(
        DescribeCodeSemanticContractRequest(
            provider_key="aware_demo",
            package_name="aware-demo",
        )
    )

    assert response.success is True
    assert response.spec_declaration is not None
    assert helper_result is not None
    assert helper_result.markdown == response.spec_declaration.markdown
    assert response.spec_declaration.provider_key == "aware_demo"
    assert response.spec_declaration.source_contract_digest
    assert "aware_demo.provider" in response.spec_declaration.markdown
    assert "aware_demo_toml" in response.spec_declaration.markdown
    assert "aware.demo.toml" in response.spec_declaration.markdown
    assert "CodeSemanticContract" in (
        response.spec_declaration.metadata or {}
    ).values()


def test_code_sdk_renders_meta_module_semantic_contract_directly() -> None:
    contract = normalize_code_semantic_contract(AWARE_META_SEMANTIC_CONTRACT)
    spec = render_code_semantic_contract_spec_declaration(
        semantic_contract=AWARE_META_SEMANTIC_CONTRACT
    )

    assert contract.provider_key == "aware_meta"
    assert contract.materialization_code_package_delta_outputs
    assert (
        contract.materialization_code_package_delta_outputs[0].output_key
        == "generated_language_code_package_deltas"
    )
    assert spec.provider_key == "aware_meta"
    assert spec.metadata is not None
    assert spec.metadata["source_contract"] == "ModuleSemanticContract"
    assert spec.metadata["normalized_contract"] == "CodeSemanticContract"
    assert "CodePackageDelta outputs" in spec.markdown
    assert "aware_meta.object_config_graph.language_materialization" in spec.markdown
    assert "generated_language_code_package_deltas" in spec.markdown
    assert "ObjectConfigGraphPackage" in spec.markdown
    assert "workspace-semantic-materialization" in spec.markdown


def test_code_sdk_renders_generated_code_package_declarations() -> None:
    provider_binding = CodeSemanticProviderBinding(
        provider_key="aware_ontology",
        manifest_relative_path="modules/storage/ontology/aware.ontology.toml",
        semantic_package_metadata=JsonObject(
            {
                "package_root": "modules/storage/ontology",
                "language_materialization_targets": [
                    {
                        "role": "python_ontology",
                        "language": "python",
                        "output_dir": "structure/python/orm_runtime",
                        "import_root": "aware_storage_ontology",
                        "package_name": "aware-storage-ontology",
                        "materialization_source": "ontology",
                        "code_package_surface": "structure",
                        "renderer_profile": "orm_runtime",
                    },
                    {
                        "role": "sql_ontology",
                        "language": "sql",
                        "output_dir": "structure/sql/schema",
                        "import_root": "aware_storage_sql",
                        "package_name": "storage-ontology",
                        "materialization_source": "ontology",
                        "code_package_surface": "structure",
                    },
                ],
            }
        ),
    )

    spec = render_code_semantic_contract_spec_declaration(
        semantic_contract=CodeSemanticContract(provider_key="aware_ontology"),
        provider_binding=provider_binding,
    )
    helper_declarations = code_semantic_generated_code_package_declarations(
        provider_binding=provider_binding,
    )

    assert spec.generated_code_packages == list(helper_declarations)
    assert [
        (
            item.role,
            item.package_name,
            item.language.value,
            item.manifest_kind,
            item.manifest_path,
            item.public_checkout_default,
        )
        for item in spec.generated_code_packages
    ] == [
        (
            "python_ontology",
            "aware-storage-ontology",
            "python",
            "pyproject_toml",
            "modules/storage/ontology/structure/python/orm_runtime/pyproject.toml",
            True,
        ),
        (
            "sql_ontology",
            "storage-ontology",
            "sql",
            "generated_materialization",
            "modules/storage/ontology/structure/sql/schema",
            False,
        ),
    ]
    assert "Generated Code Packages" in spec.markdown
    assert "aware-storage-ontology" in spec.markdown


def test_code_sdk_facade_exports_grammar_profile_dtos() -> None:
    request = ResolveCodeGrammarProfileRequest(
        profile_key="aware_kernel.semantic_contracts",
        language="aware",
        backend_key="aware_kernel",
        provider_keys=["aware_meta"],
        semantic_contracts=[CodeSemanticContract(provider_key="aware_meta")],
    )
    profile = CodeGrammarProfile(
        profile_key="aware_kernel.semantic_contracts",
        language="aware",
        backend_key="aware_kernel",
        backend=CodeGrammarBackendDescriptor(
            backend_key="aware_kernel",
            language="aware",
            parser_kind="tree_sitter",
        ),
        provider_keys=["aware_meta"],
        lane_keys=["aware_meta.projection"],
        grammar_rules=["projection_def"],
        code_section_types=["projection"],
        rule_bindings=[
            CodeGrammarRuleBinding(
                rule_name="projection_def",
                provider_key="aware_meta",
                lane_key="aware_meta.projection",
                semantic_owner="aware_meta.projection",
                compiler_owner="aware_grammar",
                code_section_type="projection",
            )
        ],
    )
    response = ResolveCodeGrammarProfileResponse(
        success=True,
        status=CodeGrammarProfileResolutionStatus.resolved,
        resolved=True,
        profile=profile,
        diagnostics=[
            CodeGrammarProfileDiagnostic(
                severity="info",
                reason="resolved",
                message="profile resolved",
            )
        ],
        provider_count=1,
        lane_count=1,
        rule_count=1,
    )

    assert request.operation == "resolve_grammar_profile"
    assert request.semantic_contracts[0].provider_key == "aware_meta"
    assert response.status is CodeGrammarProfileResolutionStatus.resolved
    assert response.profile is not None
    assert response.profile.rule_bindings[0].rule_name == "projection_def"


def test_code_sdk_facade_exports_semantic_scope_dependency_dto() -> None:
    dependency = CodeSemanticMaterializationScopeDependency(
        package_name="home-devices-api",
        provider_key="aware_api",
        semantic_owner="aware_api.provider",
        manifest_kind="aware_api_toml",
        dependency_kind="api_package",
        semantic_package_family="api",
        semantic_package_kind="api_package",
        semantic_package_name="home-devices-api",
        source_refs=["apis/home/aware.api.toml"],
        reason="scope closure requires API semantic truth",
    )

    assert dependency.package_name == "home-devices-api"
    assert dependency.required_state == "materialized"
    assert dependency.provider_key == "aware_api"


def test_code_sdk_facade_exports_segment_render_policy_dtos() -> None:
    request = ResolveCodeSegmentRenderPolicyRequest(
        language="aware",
        section_type="function",
        segment_name="description_comment",
    )
    response = ResolveCodeSegmentRenderPolicyResponse(
        success=True,
        status=CodeSegmentRenderPolicyResolutionStatus.resolved,
        resolved=True,
        policy_count=1,
    )

    assert request.operation == "resolve_segment_render_policy"
    assert request.segment_name == "description_comment"
    assert response.status is CodeSegmentRenderPolicyResolutionStatus.resolved
    assert CodeSegmentContentDomain.semantic_segment_value.value == (
        "semantic_segment_value"
    )


@pytest.mark.asyncio
async def test_local_code_sdk_catalog_matches_manifest_resolution_descriptors() -> None:
    catalog = CodeSdkSemanticContractCatalog(
        semantic_contracts=(
            CodeSemanticContract(
                provider_key="aware_api",
                semantic_scope_keys=["api.semantic_contract"],
                manifest_resolution=[
                    CodeSemanticManifestResolutionDescriptor(
                        semantic_owner="aware_api.package",
                        manifest_kind="aware_api_toml",
                        filename="aware.api.toml",
                        contract="aware.api",
                        loader_module="aware_api_runtime.manifest.loader",
                        loader_name="load_aware_api_toml_spec",
                        workspace_manifest_kind="api",
                        semantic_package_family="api",
                        semantic_package_kind="api_package",
                        code_package_surface="api",
                        priority=20,
                    )
                ],
            ),
            CodeSemanticContract(
                provider_key="aware_ontology",
                semantic_scope_keys=["ontology.semantic_contract"],
                manifest_resolution=[
                    CodeSemanticManifestResolutionDescriptor(
                        semantic_owner="aware_ontology.package",
                        manifest_kind="aware_ontology_toml",
                        filename="aware.ontology.toml",
                        contract="aware.ontology",
                        loader_module="aware_ontology.manifest.loader",
                        loader_name="load_aware_ontology_toml_spec",
                        workspace_manifest_kind="ontology",
                        semantic_package_family="ontology",
                        semantic_package_kind="ontology_package",
                        code_package_surface="structure",
                        priority=10,
                    )
                ],
            ),
        )
    )
    api_client = build_local_code_sdk_api_client(catalog=catalog)

    response = await api_client.code.semantic_contract.describe(
        DescribeCodeSemanticContractRequest(
            provider_key="aware_api",
            include_layout=False,
        )
    )
    matches = catalog.matching_manifest_resolution(
        manifest_kind="aware_api_toml",
        filename="aware.api.toml",
        workspace_manifest_kind="api",
    )

    assert response.success is True
    assert response.semantic_contract is not None
    assert response.semantic_contract.provider_key == "aware_api"
    assert matches[0].provider_key == "aware_api"
    assert matches[0].manifest_resolution.loader_name == "load_aware_api_toml_spec"
    assert matches[0].manifest_resolution.code_package_surface == "api"


@pytest.mark.asyncio
async def test_local_code_sdk_api_finds_manifest_resolution_descriptors() -> None:
    api_client = build_local_code_sdk_api_client(
        catalog=CodeSdkSemanticContractCatalog(
            semantic_contracts=(
                CodeSemanticContract(
                    provider_key="aware_api",
                    semantic_scope_keys=["api.semantic_contract"],
                    metadata=cast(
                        JsonObject,
                        {
                            "semantic_contract_module": (
                                "aware_api_runtime.semantic_contract"
                            )
                        },
                    ),
                    manifest_resolution=[
                        CodeSemanticManifestResolutionDescriptor(
                            semantic_owner="aware_api.provider",
                            manifest_kind="aware_api_toml",
                            filename="aware.api.toml",
                            contract="aware.api",
                            loader_module="aware_api_runtime.manifest.loader",
                            loader_name="load_aware_api_toml_spec",
                            workspace_manifest_kind="api",
                            semantic_package_family="api",
                            semantic_package_kind="api_package",
                            code_package_surface="api",
                            priority=20,
                        )
                    ],
                ),
            )
        )
    )

    response = await api_client.code.semantic_contract.find_manifest_resolution(
        FindCodeSemanticManifestResolutionRequest(
            manifest_kind="aware_api_toml",
            filename="aware.api.toml",
            workspace_manifest_kind="api",
        )
    )

    assert response.success is True
    assert len(response.matches) == 1
    assert response.matches[0].provider_key == "aware_api"
    assert response.matches[0].semantic_contract.provider_key == "aware_api"
    assert response.matches[0].semantic_contract_module == (
        "aware_api_runtime.semantic_contract"
    )


@pytest.mark.asyncio
async def test_local_code_sdk_describe_fails_closed_for_unknown_provider() -> None:
    api_client = build_local_code_sdk_api_client(
        catalog=CodeSdkSemanticContractCatalog(
            semantic_contracts=(CodeSemanticContract(provider_key="aware_api"),)
        )
    )

    response = await api_client.code.semantic_contract.describe(
        DescribeCodeSemanticContractRequest(
            provider_key="missing_provider",
            include_layout=False,
        )
    )

    assert response.success is False
    assert response.semantic_contract is None
    assert response.error == (
        "Unknown Code semantic contract provider: missing_provider"
    )


@pytest.mark.asyncio
async def test_local_code_sdk_describes_bound_package_layout() -> None:
    api_client = build_local_code_sdk_api_client(
        package_layouts=(
            CodeSdkPackageLayoutBinding(
                package_name="aware_demo_ontology",
                package_root="modules/demo/structure/ontology",
                sources_root="modules/demo/structure/ontology/aware",
                surface="structure",
                manifest_relative_path="modules/demo/structure/ontology/aware.toml",
            ),
        )
    )

    response = await api_client.code.semantic_contract.describe(
        DescribeCodeSemanticContractRequest(
            package_name="aware_demo_ontology",
            include_layout=True,
        )
    )

    assert response.success is True
    assert response.layout_contract is not None
    assert response.layout_contract.package_root == "modules/demo/structure/ontology"
    assert response.layout_contract.sources_root == (
        "modules/demo/structure/ontology/aware"
    )
    assert response.layout_contract.surface == "structure"
    assert response.layout_contract.manifest_relative_path == "aware.toml"
    assert response.layout_contract.path_roles[0].role is (
        CodePackagePathRole.authored_source
    )
    assert response.layout_contract.path_roles[0].include_patterns == [
        "aware/*.aware",
        "aware/**/*.aware",
        "aware/*.py",
        "aware/**/*.py",
    ]


@pytest.mark.asyncio
async def test_local_code_sdk_package_layout_describe_accepts_request_root() -> None:
    api_client = build_local_code_sdk_api_client()

    response = await api_client.code.package_layout.describe(
        DescribeCodePackageLayoutRequest(
            package_name="aware_demo_ontology",
            package_root="modules/demo/structure/ontology",
        )
    )

    assert response.success is True
    assert response.layout_contract is not None
    assert response.layout_contract.package_name == "aware_demo_ontology"
    assert response.layout_contract.package_root == "modules/demo/structure/ontology"


@pytest.mark.asyncio
async def test_local_code_sdk_validates_semantic_contract_and_layout() -> None:
    api_client = build_local_code_sdk_api_client()

    semantic_response = await api_client.code.semantic_contract.validate(
        ValidateCodeSemanticContractRequest(
            semantic_contract=CodeSemanticContract(provider_key="")
        )
    )
    layout_response = await api_client.code.package_layout.validate(
        ValidateCodePackageLayoutRequest(
            layout_contract=CodePackageLayoutContract(
                package_root="modules/demo",
                surface="invalid",
                path_roles=[
                    CodePackageLayoutPathRole(
                        role=CodePackagePathRole.authored_source,
                    )
                ],
            )
        )
    )

    assert semantic_response.success is False
    assert semantic_response.valid is False
    assert semantic_response.diagnostics == ["provider_key is required."]
    assert layout_response.success is False
    assert layout_response.valid is False
    assert layout_response.diagnostics == [
        "surface is not a valid CodePackageSurface: 'invalid'.",
        "path_roles[0] must include at least one pattern."
    ]


@pytest.mark.asyncio
async def test_aware_code_sdk_catalog_facade_uses_same_local_client() -> None:
    sdk = AwareCodeSdk.local()

    semantic_response = await sdk.describe_semantic_contract()
    assert semantic_response.semantic_contract is not None
    normalized = await sdk.api_client.code.semantic_contract.normalize(
        NormalizeCodeSemanticContractRequest(
            semantic_contract=semantic_response.semantic_contract
        )
    )

    assert semantic_response.success is True
    assert normalized.success is True
    assert normalized.semantic_contract == semantic_response.semantic_contract


@pytest.mark.asyncio
async def test_aware_code_sdk_facade_previews_semantic_analysis_package_delta() -> None:
    api_client = _FakeApiClient()
    sdk = AwareCodeSdk(api_client=cast(Any, api_client))

    response = await sdk.preview_semantic_analysis_package_delta(
        PreviewCodeSemanticAnalysisPackageDeltaRequest(
            provider_key="aware_demo",
            semantic_owner="aware_demo.package",
            delta=_package_delta("demo.aware"),
        )
    )

    assert response.success is True
    assert response.previewed is True
    assert response.available is True
    assert response.provider_key == "aware_demo"
    assert api_client.code.semantic_analysis.requests[0].delta.paths[
        0
    ].relative_path == "demo.aware"


@pytest.mark.asyncio
async def test_aware_code_sdk_facade_resolves_grammar_profile() -> None:
    api_client = _FakeApiClient()
    sdk = AwareCodeSdk(api_client=cast(Any, api_client))

    response = await sdk.resolve_grammar_profile(
        ResolveCodeGrammarProfileRequest(
            profile_key="demo.profile",
            provider_keys=["aware_demo"],
        )
    )

    assert response.success is True
    assert response.resolved is True
    assert response.profile is not None
    assert response.profile.profile_key == "demo.profile"
    assert api_client.code.grammar_profile.requests[0].provider_keys == [
        "aware_demo"
    ]


@pytest.mark.asyncio
async def test_aware_code_sdk_facade_resolves_segment_render_policy() -> None:
    api_client = _FakeApiClient()
    sdk = AwareCodeSdk(api_client=cast(Any, api_client))

    response = await sdk.resolve_segment_render_policy(
        ResolveCodeSegmentRenderPolicyRequest(
            language="aware",
            section_type="function",
            segment_name="description_comment",
        )
    )

    assert response.success is True
    assert response.resolved is True
    assert (
        api_client.code.section_delta.render_policy_requests[0].segment_name
        == "description_comment"
    )


@pytest.mark.asyncio
async def test_aware_code_sdk_facade_resolves_source_projection_package_delta() -> None:
    api_client = _FakeApiClient()
    sdk = AwareCodeSdk(api_client=cast(Any, api_client))

    response = await sdk.resolve_source_projection_package_delta(
        ResolveCodeSourceProjectionPackageDeltaRequest(
            projection=CodeSourceProjectionRequest(
                provider_key="aware_demo",
                events=[],
                action_bindings=[],
            ),
            result=CodeSourceProjectionResult(
                provider_key="aware_demo",
                projected=True,
            ),
        )
    )

    assert response.success is True
    assert response.resolved is True
    assert response.path_count == 1
    assert (
        api_client.code.source_projection.resolve_requests[0]
        .projection.provider_key
        == "aware_demo"
    )


@pytest.mark.asyncio
async def test_aware_code_sdk_catalog_semantic_analysis_fails_closed_without_service_runtime() -> None:
    sdk = AwareCodeSdk.local()

    response = await sdk.preview_semantic_analysis_package_delta(
        PreviewCodeSemanticAnalysisPackageDeltaRequest(
            provider_key="aware_demo",
            delta=_package_delta("demo.aware"),
        )
    )

    assert response.success is False
    assert response.previewed is False
    assert response.available is False
    assert response.blockers == ["semantic_analysis_provider_execution_unavailable"]


@pytest.mark.asyncio
async def test_aware_code_sdk_catalog_grammar_profile_fails_closed_without_service_runtime() -> None:
    sdk = AwareCodeSdk.local()

    response = await sdk.resolve_grammar_profile(
        ResolveCodeGrammarProfileRequest(provider_keys=["aware_demo"])
    )

    assert response.success is False
    assert response.resolved is False
    assert response.status is CodeGrammarProfileResolutionStatus.blocked
    assert response.diagnostics[0].reason == (
        "grammar_profile_requires_code_service"
    )


@pytest.mark.asyncio
async def test_aware_code_sdk_catalog_segment_render_policy_fails_closed_without_service_runtime() -> None:
    sdk = AwareCodeSdk.local()

    response = await sdk.resolve_segment_render_policy(
        ResolveCodeSegmentRenderPolicyRequest(
            language="aware",
            section_type="function",
            segment_name="description_comment",
        )
    )

    assert response.success is False
    assert response.resolved is False
    assert response.status is CodeSegmentRenderPolicyResolutionStatus.blocked
    assert response.diagnostics[0].reason == (
        "segment_render_policy_requires_code_service"
    )


def test_aware_code_sdk_catalog_semantic_scope_provider_fails_closed_without_service_runtime() -> None:
    sdk = AwareCodeSdk.local()

    response = sdk.semantic_scope_provider().resolve_semantic_scope(
        ResolveCodeSemanticScopeRequest(
            package_ref=CodeSemanticScopePackageRef(
                package_name="aware-demo",
                manifest_path="modules/demo/structure/ontology/aware.toml",
            )
        )
    )

    assert response.success is False
    assert response.resolved is False
    assert response.diagnostics == ["semantic_scope_requires_code_service"]


def test_code_sdk_import_boundary_excludes_service_and_runtime() -> None:
    source_root = Path(__file__).resolve().parents[1] / "aware_code_sdk"
    forbidden_tokens = (
        "aware_code_service_api" + ".models",
        "aware_code" + "_api",
        "from aware_code import",
        "import aware_code",
        "aware_code.",
        "from aware_code" + "_service import",
        "import aware_code" + "_service",
        "aware_code" + "_service.",
        "aware_code_service_protocol",
    )
    offenders: list[str] = []
    for path in sorted(source_root.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            if token in text:
                offenders.append(f"{path.relative_to(source_root.parent)}:{token}")

    assert offenders == []
    assert CodePackageDelta.__module__.startswith("aware_code_service_dto.")
    assert CodeSectionDeltaEntry.__module__.startswith("aware_code_service_dto.")
