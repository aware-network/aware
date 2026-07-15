from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from aware_api.invocation import ApiInvocationIndex, LoadedApiInvocationManifest
from aware_api.invoker import (
    ApiEndpointInvocation,
    ApiEndpointResponse,
    AwareApiEndpointInvoker,
    decode_api_endpoint_response_payload,
    resolve_api_endpoint_model_class,
)
from aware_code.language.contracts import CodeDiscoveryFile
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code.module_plugin_registry import AwareModulePluginRegistry
from aware_code.module_semantic_contract import (
    WorkspaceSemanticArtifactBinding,
    WorkspaceSemanticArtifactLeafOwnershipClaim,
    WorkspaceSemanticArtifactLeafOwnershipRequest,
    WorkspaceSemanticArtifactProduction,
)
from aware_code.package.discovery import discover_packages
from aware_code.package_surface import (
    code_package_surface_from_package_kind,
    code_package_surface_from_semantic_manifest_descriptor,
)
from aware_code.setup_language_plugins import setup_code_plugins
from aware_code_sdk.dto import (
    ClassifyCodeSourceOwnershipRequest,
    ClassifyCodeSourceOwnershipResponse,
    CodePackageLayoutContract,
    CodeSourceOwnershipObservedPath,
    CodeSourceOwnershipPackageBinding,
    CodeSourceOwnershipRequest,
    DiscoverCodePackageLayoutsRequest,
    DiscoverCodePackageLayoutsResponse,
    FindCodeSemanticManifestResolutionRequest,
    FindCodeSemanticManifestResolutionResponse,
    CodeSemanticScopePackageRef,
    ResolveCodeSemanticScopeRequest,
    ResolveCodeSemanticScopeResponse,
)
from aware_code_service_api import AwareCodeServiceApiClient
from aware_service_runtime.api_ingress.host_context import service_api_host_context
from aware_service_runtime.contracts import (
    ServiceGraphGateway,
    ServiceOperationContext,
)
from pydantic import BaseModel

from .api_service_protocol import (
    _discover_code_packages_from_manifest_paths_sync,
    _code_package_info_from_semantic_scope_ref,
    _code_semantic_scope_resolution,
    _layout_contract_from_code_package,
    _normalize_relative_path_text,
    _semantic_scope_blocked_response,
    _semantic_scope_request_diagnostics,
    _support_with_workspace_module_plugins,
    build_aware_code_service_protocol_handler,
    classify_code_source_ownership_request,
)

_SEMANTIC_CONTRACT_MODULE_BY_PROVIDER_KEY = {
    "aware_api": "aware_api_runtime.semantic_contract",
    "aware_code": "aware_code.semantic_contract",
    "aware_service": "aware_service_runtime.semantic_contract",
}


@dataclass(frozen=True, slots=True)
class LocalCodeServiceApiConfig:
    endpoint: str = "aware-code-service://local"
    request_timeout_s: float = 10.0
    service_name: str = "aware_code"


@dataclass(frozen=True, slots=True)
class _UnsupportedRawCodeTransport:
    endpoint: str

    async def invoke(
        self,
        invocation: ApiEndpointInvocation,
        *,
        timeout_s: float | None = None,
    ) -> ApiEndpointResponse:
        _ = (invocation, timeout_s)
        raise NotImplementedError(
            "Local Code service API client routes generated endpoint calls "
            "through the Code service protocol; raw transport invocation is "
            "intentionally unavailable."
        )


@dataclass(frozen=True, slots=True)
class LocalCodeServiceManifestResolutionProvider:
    """Synchronous manifest resolver over the in-process Code service handler."""

    handler: object
    module_roots: tuple[Path, ...] = ()

    def find_manifest_resolution(
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
        support = _semantic_contract_support(handler=self.handler)
        if self.module_roots:
            support = _support_with_workspace_module_plugins(
                support=support,
                module_roots=self.module_roots,
            )
        return FindCodeSemanticManifestResolutionResponse(
            request_id=resolved_request.request_id,
            success=True,
            matches=support.manifest_resolution_matches(
                provider_key=resolved_request.provider_key,
                manifest_kind=resolved_request.manifest_kind,
                filename=resolved_request.filename,
                workspace_manifest_kind=resolved_request.workspace_manifest_kind,
            ),
        )


@dataclass(frozen=True, slots=True)
class LocalCodeServicePackageLayoutProvider:
    """Synchronous package-layout resolver over the in-process Code service handler."""

    handler: object
    module_roots: tuple[Path, ...] = ()

    def discover_package_layouts(
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
        support = _package_layout_support(handler=self.handler)
        resolved_workspace_root = (
            Path(resolved_request.workspace_root or ".").expanduser().resolve()
        )
        support = _support_with_workspace_module_plugins(
            support=support,
            workspace_root=resolved_workspace_root if not self.module_roots else None,
            module_roots=self.module_roots,
        )
        setup_code_plugins()
        discovered_packages = _discover_code_packages_from_manifest_paths_sync(
            workspace_root=resolved_workspace_root,
            manifest_paths=tuple(resolved_request.manifest_paths),
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
        for manifest_path in resolved_request.manifest_paths:
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
            request_id=resolved_request.request_id,
            success=not diagnostics,
            layout_contracts=cast(Any, layout_contracts),
            diagnostics=diagnostics,
        )

    def discover_package_layouts_for_files(
        self,
        *,
        workspace_root: str = ".",
        files: Sequence[object] = (),
    ) -> DiscoverCodePackageLayoutsResponse:
        resolved_workspace_root = Path(workspace_root or ".").expanduser().resolve()
        support = _package_layout_support(handler=self.handler)
        support = _support_with_workspace_module_plugins(
            support=support,
            workspace_root=resolved_workspace_root if not self.module_roots else None,
            module_roots=self.module_roots,
        )
        setup_code_plugins()
        discovered_packages = discover_packages(
            workspace_root=resolved_workspace_root,
            files=tuple(_code_discovery_file(file) for file in files),
        )
        return DiscoverCodePackageLayoutsResponse(
            success=True,
            layout_contracts=[
                _layout_contract_from_code_package(
                    package=package,
                    provider_key=support.primary_contract.provider_key,
                )
                for package in discovered_packages
            ],
            diagnostics=[],
        )


@dataclass(frozen=True, slots=True)
class LocalCodeServiceSemanticScopeProvider:
    """Synchronous semantic-scope resolver over the Code runtime registry."""

    handler: object

    def resolve_semantic_scope(
        self,
        request: ResolveCodeSemanticScopeRequest | None = None,
        *,
        package_ref: CodeSemanticScopePackageRef | None = None,
        workspace_root: str = ".",
        provider_keys: Sequence[str] = (),
        scope_keys: Sequence[str] = (),
    ) -> ResolveCodeSemanticScopeResponse:
        from aware_code.semantic_scope import SemanticScopeRegistry

        _ = self.handler
        if request is None:
            if package_ref is None:
                raise ValueError("package_ref is required.")
            request = ResolveCodeSemanticScopeRequest(
                package_ref=package_ref,
                workspace_root=workspace_root,
                provider_keys=list(provider_keys),
                scope_keys=list(scope_keys),
            )
        diagnostics = _semantic_scope_request_diagnostics(request)
        if diagnostics:
            return _semantic_scope_blocked_response(
                request=request,
                diagnostics=diagnostics,
            )
        code_package = _code_package_info_from_semantic_scope_ref(
            request.package_ref,
        )
        result = [
            _code_semantic_scope_resolution(resolution)
            for resolution in SemanticScopeRegistry.resolve(
                code_package,
                workspace_root=Path(
                    request.workspace_root or ".",
                )
                .expanduser()
                .resolve(),
                provider_keys=request.provider_keys or None,
                scope_keys=request.scope_keys or None,
            )
        ]
        return ResolveCodeSemanticScopeResponse(
            request_id=request.request_id,
            success=True,
            resolved=bool(result),
            resolutions=result,
            diagnostics=[],
            resolution_count=len(result),
        )


@dataclass(frozen=True, slots=True)
class LocalCodeServiceSourceOwnershipProvider:
    """Synchronous source-ownership classifier over Code service rules."""

    handler: object

    def classify_source_ownership(
        self,
        request: ClassifyCodeSourceOwnershipRequest | None = None,
        *,
        workspace_root: str | None = None,
        package_bindings: Sequence[CodeSourceOwnershipPackageBinding] = (),
        observed_paths: Sequence[CodeSourceOwnershipObservedPath] = (),
        strict: bool = True,
    ) -> ClassifyCodeSourceOwnershipResponse:
        _ = self.handler
        return classify_code_source_ownership_request(
            request
            or ClassifyCodeSourceOwnershipRequest(
                ownership_request=CodeSourceOwnershipRequest(
                    workspace_root=workspace_root,
                    package_bindings=list(package_bindings),
                    observed_paths=list(observed_paths),
                    strict=strict,
                )
            )
        )


@dataclass(frozen=True, slots=True)
class LocalCodeServiceSemanticOwnershipProvider:
    """Synchronous semantic ownership adapter over Code runtime contracts."""

    handler: object

    def semantic_provider_ownerships_for_manifest_kind(
        self,
        *,
        manifest_kind: str,
    ) -> tuple[dict[str, object], ...]:
        manifest_kind_value = manifest_kind.strip()
        if not manifest_kind_value:
            return ()
        _support_with_workspace_module_plugins(
            support=_semantic_contract_support(handler=self.handler),
        )
        ownerships: dict[tuple[str, str, str, str], dict[str, object]] = {}
        AwareModulePluginRegistry.ensure_builtin_plugins_registered()
        for plugin in AwareModulePluginRegistry.get_plugins():
            module_contract = (
                AwareModulePluginRegistry.module_semantic_contract_for_provider_key(
                    plugin.provider_key,
                )
            )
            semantic_contract_module = _semantic_contract_module_for_provider_key(
                plugin.provider_key,
            )
            if module_contract is not None:
                for descriptor in module_contract.manifest_resolution_for(
                    manifest_kind=manifest_kind_value,
                ):
                    package_role = (
                        module_contract.package_role_for(role=descriptor.package_role)
                        if descriptor.package_role is not None
                        else module_contract.package_role_for(
                            role=descriptor.semantic_owner,
                        )
                    )
                    if package_role is None:
                        continue
                    if package_role.contract != "aware.semantic_provider":
                        continue
                    owned_manifest_kinds = tuple(
                        item.strip()
                        for item in package_role.owns_manifest_kinds
                        if item.strip()
                    )
                    if manifest_kind_value not in owned_manifest_kinds:
                        continue
                    ownership = _semantic_provider_ownership_payload(
                        provider_key=module_contract.provider_key,
                        role=package_role.role,
                        contract=package_role.contract,
                        module=semantic_contract_module,
                        code_package_surface=(
                            code_package_surface_from_semantic_manifest_descriptor(
                                descriptor,
                            )
                        ),
                        code_package_surface_by_package_kind=(
                            dict(descriptor.code_package_surface_by_package_kind)
                            if descriptor.code_package_surface_by_package_kind
                            is not None
                            else None
                        ),
                        owned_manifest_kind_count=len(owned_manifest_kinds),
                    )
                    ownerships[_semantic_provider_ownership_key(ownership)] = ownership
                for package_role in module_contract.package_roles:
                    if package_role.contract != "aware.semantic_provider":
                        continue
                    owned_manifest_kinds = tuple(
                        item.strip()
                        for item in package_role.owns_manifest_kinds
                        if item.strip()
                    )
                    if manifest_kind_value not in owned_manifest_kinds:
                        continue
                    ownership = _semantic_provider_ownership_payload(
                        provider_key=module_contract.provider_key,
                        role=package_role.role,
                        contract=package_role.contract,
                        module=semantic_contract_module,
                        code_package_surface=code_package_surface_from_package_kind(
                            package_role.package_kind,
                        ),
                        code_package_surface_by_package_kind=None,
                        owned_manifest_kind_count=len(owned_manifest_kinds),
                    )
                    ownerships.setdefault(
                        _semantic_provider_ownership_key(ownership),
                        ownership,
                    )
            for package in plugin.packages:
                semantic_contract = package.semantic_contract
                if semantic_contract is None:
                    continue
                if semantic_contract.contract != "aware.semantic_provider":
                    continue
                owned_manifest_kinds = tuple(
                    item.strip()
                    for item in semantic_contract.owns_manifest_kinds
                    if item.strip()
                )
                if manifest_kind_value not in owned_manifest_kinds:
                    continue
                ownership = _semantic_provider_ownership_payload(
                    provider_key=semantic_contract.provider_key,
                    role=semantic_contract.role,
                    contract=semantic_contract.contract,
                    module=semantic_contract.module,
                    code_package_surface=code_package_surface_from_package_kind(
                        package.kind,
                    ),
                    code_package_surface_by_package_kind=None,
                    owned_manifest_kind_count=len(owned_manifest_kinds),
                )
                ownerships.setdefault(
                    _semantic_provider_ownership_key(ownership),
                    ownership,
                )
        return tuple(
            sorted(
                ownerships.values(),
                key=lambda item: (
                    _payload_required_int(item, "owned_manifest_kind_count"),
                    _payload_required_str(item, "provider_key"),
                    _payload_required_str(item, "role"),
                    _payload_required_str(item, "module"),
                ),
            )
        )

    def claim_semantic_artifact_leaf(
        self,
        *,
        workspace_root: str,
        owner: Mapping[str, object] | object,
        leaf: Mapping[str, object] | object,
    ) -> dict[str, object] | None:
        _support_with_workspace_module_plugins(
            support=_semantic_contract_support(handler=self.handler),
        )
        owner_binding = _semantic_artifact_binding_from_payload(owner)
        leaf_binding = _semantic_artifact_binding_from_payload(leaf)
        if not _is_strict_descendant_path(
            path=leaf_binding.package_root,
            root=owner_binding.package_root,
        ):
            return None
        provider_key = owner_binding.semantic_contract_provider_key
        semantic_owner = owner_binding.semantic_contract_role
        if provider_key is None or semantic_owner is None:
            return None
        resolvers = AwareModulePluginRegistry.resolve_semantic_artifact_leaf_ownership_resolvers(
            provider_key=provider_key,
            semantic_owner=semantic_owner,
            owner_manifest_kind=owner_binding.manifest_kind,
            artifact_manifest_kind=leaf_binding.manifest_kind,
        )
        if not resolvers:
            return None
        request = WorkspaceSemanticArtifactLeafOwnershipRequest(
            workspace_root=Path(workspace_root).expanduser().resolve(),
            owner=owner_binding,
            leaf=leaf_binding,
        )
        for resolver in resolvers:
            try:
                claim = resolver.resolver(request=request)
            except Exception:
                continue
            if _semantic_artifact_leaf_claim_is_valid(
                claim=claim,
                owner_binding=owner_binding,
                leaf_binding=leaf_binding,
            ):
                return _semantic_artifact_leaf_claim_payload(claim)
        return None


class LocalCodeServiceAwareApiClient(AwareApiEndpointInvoker):
    """Generated API invoker over one in-process Code service protocol."""

    def __init__(
        self,
        *,
        handler: object | None = None,
        operation_context: ServiceOperationContext | None = None,
        graph_gateway: ServiceGraphGateway | None = None,
        endpoint: str = "aware-code-service://local",
        request_timeout_s: float = 10.0,
        service_name: str = "aware_code",
        module_roots: Sequence[str | Path] = (),
    ) -> None:
        self._module_roots = tuple(
            Path(module_root).expanduser().resolve() for module_root in module_roots
        )
        if handler is None and self._module_roots:
            AwareModulePluginRegistry.ensure_module_plugins_registered_from_module_roots(
                module_roots=self._module_roots,
                replace_existing=True,
            )
        self._handler = handler or build_aware_code_service_protocol_handler()
        self._operation_context = operation_context
        self._graph_gateway = graph_gateway
        self._local_config = LocalCodeServiceApiConfig(
            endpoint=endpoint,
            request_timeout_s=request_timeout_s,
            service_name=service_name,
        )
        super().__init__(
            _UnsupportedRawCodeTransport(endpoint=self._local_config.endpoint)
        )

    @property
    def local_config(self) -> LocalCodeServiceApiConfig:
        return self._local_config

    def manifest_resolution_provider(
        self,
    ) -> LocalCodeServiceManifestResolutionProvider:
        return LocalCodeServiceManifestResolutionProvider(
            handler=self._handler,
            module_roots=self._module_roots,
        )

    def package_layout_provider(self) -> LocalCodeServicePackageLayoutProvider:
        return LocalCodeServicePackageLayoutProvider(
            handler=self._handler,
            module_roots=self._module_roots,
        )

    def semantic_scope_provider(self) -> LocalCodeServiceSemanticScopeProvider:
        return LocalCodeServiceSemanticScopeProvider(handler=self._handler)

    def source_ownership_provider(self) -> LocalCodeServiceSourceOwnershipProvider:
        return LocalCodeServiceSourceOwnershipProvider(handler=self._handler)

    def semantic_ownership_provider(self) -> LocalCodeServiceSemanticOwnershipProvider:
        return LocalCodeServiceSemanticOwnershipProvider(handler=self._handler)

    async def invoke_api_endpoint(
        self,
        *,
        manifest: LoadedApiInvocationManifest | ApiInvocationIndex,
        request_payload: BaseModel | Mapping[str, Any],
        endpoint_ref: str | None = None,
        discriminant: str | None = None,
        api_name: str | None = None,
        capability_name: str | None = None,
        endpoint_name: str | None = None,
        timeout_s: float | None = None,
    ) -> Any:
        _ = timeout_s or self._local_config.request_timeout_s
        prepared = self.prepare_api_endpoint_invocation(
            manifest=manifest,
            request_payload=request_payload,
            endpoint_ref=endpoint_ref,
            discriminant=discriminant,
            api_name=api_name,
            capability_name=capability_name,
            endpoint_name=endpoint_name,
        )
        request_model = resolve_api_endpoint_model_class(
            prepared.request_python_model_ref or prepared.request_class_ref
        )
        request = request_model.model_validate(dict(prepared.request_payload))
        response = await self._dispatch(
            endpoint_ref=prepared.endpoint.endpoint_ref,
            request=request,
        )
        response_payload = (
            response.model_dump(mode="json")
            if isinstance(response, BaseModel)
            else response
        )
        return decode_api_endpoint_response_payload(
            prepared=prepared,
            response_payload=response_payload,
        )

    async def _dispatch(
        self,
        *,
        endpoint_ref: str,
        request: BaseModel,
    ) -> object:
        if self._operation_context is None:
            return await dispatch_code_service_protocol_endpoint(
                handler=self._handler,
                endpoint_ref=endpoint_ref,
                request=request,
            )
        with service_api_host_context(
            operation_context=self._operation_context,
            graph_gateway=self._graph_gateway,
            service_name=self._local_config.service_name,
        ):
            return await dispatch_code_service_protocol_endpoint(
                handler=self._handler,
                endpoint_ref=endpoint_ref,
                request=request,
            )


async def dispatch_code_service_protocol_endpoint(
    *,
    handler: object,
    endpoint_ref: str,
    request: BaseModel,
) -> object:
    parts = tuple(part.strip() for part in endpoint_ref.split(".") if part.strip())
    if len(parts) != 3 or parts[0] != "code":
        raise ValueError(
            "Code service protocol endpoint refs must use "
            f"`code.<capability>.<endpoint>`, got {endpoint_ref!r}."
        )
    _, capability_name, endpoint_name = parts
    code_handler = getattr(handler, "code", None)
    capability_handler = getattr(code_handler, capability_name, None)
    endpoint_handler = getattr(capability_handler, endpoint_name, None)
    if not callable(endpoint_handler):
        raise ValueError(
            "Code service protocol handler does not expose endpoint "
            f"{endpoint_ref!r}."
        )
    typed_endpoint_handler = cast(
        Callable[[BaseModel], Awaitable[object]],
        endpoint_handler,
    )
    return await typed_endpoint_handler(request)


def _semantic_contract_support(*, handler: object) -> Any:
    code_handler = getattr(handler, "code", None)
    semantic_contract_handler = getattr(code_handler, "semantic_contract", None)
    support = getattr(semantic_contract_handler, "_support", None)
    if support is None or not callable(
        getattr(support, "manifest_resolution_matches", None)
    ):
        raise ValueError(
            "Local Code service handler does not expose semantic-contract "
            "manifest-resolution support."
        )
    return support


def _package_layout_support(*, handler: object) -> Any:
    code_handler = getattr(handler, "code", None)
    package_layout_handler = getattr(code_handler, "package_layout", None)
    support = getattr(package_layout_handler, "_support", None)
    if support is None:
        raise ValueError(
            "Local Code service handler does not expose package-layout support."
        )
    return support


def _code_discovery_file(file: object) -> CodeDiscoveryFile:
    return CodeDiscoveryFile(
        relative_path=str(getattr(file, "relative_path", "")),
        file_content=str(getattr(file, "file_content", "")),
        language=_code_discovery_language(getattr(file, "language", None)),
    )


def _code_discovery_language(value: object) -> CodeLanguage | None:
    if isinstance(value, CodeLanguage):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return CodeLanguage(value.strip())
        except ValueError:
            return None
    return None


def _semantic_contract_module_for_provider_key(provider_key: str) -> str:
    module = AwareModulePluginRegistry.semantic_contract_module_for_provider_key(
        provider_key,
    )
    if module is not None:
        return module
    return _SEMANTIC_CONTRACT_MODULE_BY_PROVIDER_KEY.get(provider_key, "")


def _semantic_provider_ownership_payload(
    *,
    provider_key: str,
    role: str,
    contract: str,
    module: str,
    code_package_surface: str | None,
    code_package_surface_by_package_kind: Mapping[str, str] | None,
    owned_manifest_kind_count: int,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "provider_key": provider_key,
        "role": role,
        "contract": contract,
        "module": module,
        "owned_manifest_kind_count": owned_manifest_kind_count,
    }
    if code_package_surface is not None:
        payload["code_package_surface"] = code_package_surface
    if code_package_surface_by_package_kind is not None:
        payload["code_package_surface_by_package_kind"] = dict(
            code_package_surface_by_package_kind,
        )
    return payload


def _semantic_provider_ownership_key(
    payload: Mapping[str, object],
) -> tuple[str, str, str, str]:
    return (
        _payload_required_str(payload, "provider_key"),
        _payload_required_str(payload, "role"),
        _payload_required_str(payload, "contract"),
        _payload_required_str(payload, "module"),
    )


def _semantic_artifact_binding_from_payload(
    value: Mapping[str, object] | object,
) -> WorkspaceSemanticArtifactBinding:
    if isinstance(value, WorkspaceSemanticArtifactBinding):
        return value
    payload = _payload_mapping(value)
    return WorkspaceSemanticArtifactBinding(
        module_id=_payload_optional_str(payload, "module_id"),
        package_name=_payload_required_str(payload, "package_name"),
        language=_payload_required_str(payload, "language"),
        surface=_payload_required_str(payload, "surface"),
        manifest_kind=_payload_required_str(payload, "manifest_kind"),
        manifest_relative_path=_payload_required_str(
            payload,
            "manifest_relative_path",
        ),
        package_root=_payload_required_str(payload, "package_root"),
        sources_root=_payload_required_str(payload, "sources_root"),
        package_kind=_payload_optional_str(payload, "package_kind"),
        semantic_contract_provider_key=_payload_optional_str(
            payload,
            "semantic_contract_provider_key",
        ),
        semantic_contract_role=_payload_optional_str(
            payload,
            "semantic_contract_role",
        ),
        semantic_contract_name=_payload_optional_str(
            payload,
            "semantic_contract_name",
        ),
        semantic_contract_module=_payload_optional_str(
            payload,
            "semantic_contract_module",
        ),
    )


def _semantic_artifact_leaf_claim_is_valid(
    *,
    claim: WorkspaceSemanticArtifactLeafOwnershipClaim | None,
    owner_binding: WorkspaceSemanticArtifactBinding,
    leaf_binding: WorkspaceSemanticArtifactBinding,
) -> bool:
    if claim is None or not claim.owned:
        return False
    return (
        claim.owner_semantic_package_manifest == owner_binding.manifest_relative_path
        and claim.artifact_manifest_kind == leaf_binding.manifest_kind
        and claim.artifact_package_root == leaf_binding.package_root
    )


def _semantic_artifact_leaf_claim_payload(
    claim: WorkspaceSemanticArtifactLeafOwnershipClaim | None,
) -> dict[str, object] | None:
    if claim is None or not claim.owned:
        return None
    payload: dict[str, object] = {
        "owned": claim.owned,
        "owner_semantic_package_manifest": (claim.owner_semantic_package_manifest),
        "ownership_role": claim.ownership_role,
        "artifact_manifest_kind": claim.artifact_manifest_kind,
        "artifact_package_root": claim.artifact_package_root,
    }
    production = _semantic_artifact_production_payload(claim.production)
    if production is not None:
        payload["production"] = production
    return payload


def _semantic_artifact_production_payload(
    production: WorkspaceSemanticArtifactProduction | None,
) -> dict[str, object] | None:
    if production is None:
        return None
    payload: dict[str, object] = {
        "provider_key": production.provider_key,
        "producer_key": production.producer_key,
    }
    for key, value in (
        ("producer_kind", production.producer_kind),
        ("provider_payload", production.provider_payload),
        ("input_code_package_id", production.input_code_package_id),
        (
            "input_object_instance_graph_commit_id",
            production.input_object_instance_graph_commit_id,
        ),
        ("input_digest", production.input_digest),
        ("output_digest", production.output_digest),
        ("emission_payload", production.emission_payload),
    ):
        if value is not None:
            payload[key] = dict(value) if isinstance(value, Mapping) else value
    return payload


def _payload_mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    raise TypeError(f"Expected mapping payload, got {type(value).__name__}.")


def _payload_required_str(mapping: Mapping[str, object], key: str) -> str:
    value = mapping.get(key)
    if isinstance(value, str) and value.strip():
        return value
    raise ValueError(f"semantic ownership payload requires {key!r}.")


def _payload_optional_str(mapping: Mapping[str, object], key: str) -> str | None:
    value = mapping.get(key)
    return value if isinstance(value, str) and value.strip() else None


def _payload_required_int(mapping: Mapping[str, object], key: str) -> int:
    value = mapping.get(key)
    if isinstance(value, int):
        return value
    raise ValueError(f"semantic ownership payload requires integer {key!r}.")


def _is_strict_descendant_path(*, path: str, root: str) -> bool:
    normalized_path = Path(path).as_posix().strip().strip("/")
    normalized_root = Path(root).as_posix().strip().strip("/")
    return bool(
        normalized_root
        and normalized_path != normalized_root
        and normalized_path.startswith(f"{normalized_root}/")
    )


def build_local_code_service_api_client(
    *,
    handler: object | None = None,
    operation_context: ServiceOperationContext | None = None,
    graph_gateway: ServiceGraphGateway | None = None,
    endpoint: str = "aware-code-service://local",
    request_timeout_s: float = 10.0,
    service_name: str = "aware_code",
    module_roots: Sequence[str | Path] = (),
) -> AwareCodeServiceApiClient:
    return AwareCodeServiceApiClient(
        LocalCodeServiceAwareApiClient(
            handler=handler,
            operation_context=operation_context,
            graph_gateway=graph_gateway,
            endpoint=endpoint,
            request_timeout_s=request_timeout_s,
            service_name=service_name,
            module_roots=module_roots,
        )
    )


__all__ = [
    "LocalCodeServiceApiConfig",
    "LocalCodeServiceAwareApiClient",
    "LocalCodeServiceManifestResolutionProvider",
    "LocalCodeServicePackageLayoutProvider",
    "LocalCodeServiceSemanticScopeProvider",
    "LocalCodeServiceSemanticOwnershipProvider",
    "LocalCodeServiceSourceOwnershipProvider",
    "build_local_code_service_api_client",
    "dispatch_code_service_protocol_endpoint",
]
