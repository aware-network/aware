from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

import aware_experience_sdk.local_host as local_host_mod
from aware_environment_service_api._bindings import (
    ENVIRONMENT__SESSION__RESOLVE_ATTENTION_ENDPOINT_REF,
)
from aware_experience_service_api._bindings import (
    EXPERIENCE__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING_ENDPOINT_REF,
    EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG_ENDPOINT_REF,
    EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE_ENDPOINT_REF,
    EXPERIENCE__SESSION_VIEW_FRAME__RESOLVE_EXPERIENCE_SESSION_VIEW_FRAME_ENDPOINT_REF,
)
from aware_experience_sdk import (
    build_local_experience_sdk_client as exported_build_local_experience_sdk_client,
)
from aware_experience_sdk.local_host import (
    DEFAULT_DEPENDENCY_PROVIDER_TOML_RELATIVE_PATHS,
    DEFAULT_IMPLEMENTATION_TOML_RELATIVE_PATHS,
    DEFAULT_READY_RELATIVE_PATH,
    DEFAULT_SOCKET_RELATIVE_PATH,
    DEFAULT_STATE_ROOT_RELATIVE_PATH,
    EXPERIENCE_API_ENDPOINT_REFS,
    EXPERIENCE_SDK_REPO_ROOT_ENV_VARS,
    build_local_experience_sdk_client,
    build_local_experience_service_host_app,
    install_local_experience_service_api_dependency_routes,
    resolve_local_experience_service_api_dependency_routes,
    resolve_local_experience_service_host_config,
)
from aware_experience_service_dto.experience.section_graph_binding.service_operation import (
    GetExperienceSectionGraphBindingCatalogResponse,
)
from aware_service_runtime.contracts import (
    ConfigureServiceApiDependencyRoutesHostControlRequest,
    ConfigureServiceApiDependencyRoutesHostControlResponse,
    RequestStatus,
    SERVICE_HOST_API_DISPATCH_SERVICE_ENDPOINT_REFS_KEY,
    SERVICE_HOST_API_DISPATCH_SERVICE_IDS_BY_NAME_KEY,
    SERVICE_HOST_API_DISPATCH_SERVICE_NAMES_KEY,
    SERVICE_HOST_API_DISPATCH_SERVICE_STREAM_ENDPOINT_REFS_KEY,
    SERVICE_HOST_CAPABILITY_API_DISPATCH,
    SERVICE_HOST_PROTOCOL_VERSION,
    ServiceHostBootstrapStatus,
    ServiceHostCapabilityAdvertisement,
    ServiceHostCapabilityState,
    ServiceHostHandshakeRequest,
    ServiceHostHandshakeResponse,
    ServiceHostReadiness,
    ServiceHostApiIngressRequest,
    ServiceHostControlRequest,
    ServiceHostControlResponse,
    ServiceOperationResponse,
)
from aware_service_runtime.service_api_dependency_routes import (
    ServiceApiDependencyRouteKind,
    service_api_dependency_routes_from_payload,
)
from aware_service_service import ServiceHostIpcServer


def _repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "aware.repo.toml").exists():
            return parent
    raise AssertionError("Could not locate repo root")


_REPO_ROOT = _repo_root()


def _handshake_for_route_tests(config) -> ServiceHostHandshakeResponse:  # noqa: ANN001
    return ServiceHostHandshakeResponse(
        endpoint=config.endpoint,
        protocol_version=SERVICE_HOST_PROTOCOL_VERSION,
        host_id="aware-service-host-test",
        host_version="1.0.0",
        readiness=ServiceHostReadiness(
            is_ready=True,
            status=ServiceHostBootstrapStatus.ready,
        ),
        capabilities=(
            ServiceHostCapabilityAdvertisement(
                capability_id=SERVICE_HOST_CAPABILITY_API_DISPATCH,
                state=ServiceHostCapabilityState.available,
                detail_payload={
                    SERVICE_HOST_API_DISPATCH_SERVICE_NAMES_KEY: [
                        "aware_attention",
                        "aware_environment",
                        "aware_identity",
                        "aware_reactivity",
                        "aware_experience",
                    ],
                    SERVICE_HOST_API_DISPATCH_SERVICE_IDS_BY_NAME_KEY: {
                        "aware_attention": "11111111-1111-1111-1111-111111111111",
                        "aware_environment": "55555555-5555-5555-5555-555555555555",
                        "aware_identity": "44444444-4444-4444-4444-444444444444",
                        "aware_reactivity": "22222222-2222-2222-2222-222222222222",
                        "aware_experience": "33333333-3333-3333-3333-333333333333",
                    },
                    SERVICE_HOST_API_DISPATCH_SERVICE_ENDPOINT_REFS_KEY: {
                        "aware_attention": [
                            "attention.focus.activate",
                        ],
                        "aware_environment": [
                            ENVIRONMENT__SESSION__RESOLVE_ATTENTION_ENDPOINT_REF,
                        ],
                        "aware_identity": [
                            "identity.admission.admit_identity",
                        ],
                        "aware_reactivity": [
                            "reactivity.policy.ensure_bundle",
                            "reactivity.bridge.dispatch_event",
                        ],
                        "aware_experience": [
                            EXPERIENCE_API_ENDPOINT_REFS["ensure_session_handoff"],
                        ],
                    },
                    SERVICE_HOST_API_DISPATCH_SERVICE_STREAM_ENDPOINT_REFS_KEY: {
                        "aware_reactivity": [
                            "reactivity.bridge.watch_events",
                        ],
                    },
                },
            ),
        ),
    )


def test_local_experience_service_host_config_defaults_to_dynamics_services() -> None:
    config = resolve_local_experience_service_host_config(repo_root=_REPO_ROOT)

    assert config.socket_path == (_REPO_ROOT / DEFAULT_SOCKET_RELATIVE_PATH).resolve()
    assert (
        config.ready_file_path == (_REPO_ROOT / DEFAULT_READY_RELATIVE_PATH).resolve()
    )
    assert (
        config.state_root_path
        == (_REPO_ROOT / DEFAULT_STATE_ROOT_RELATIVE_PATH).resolve()
    )
    assert config.implementation_toml_paths == tuple(
        (_REPO_ROOT / path).resolve()
        for path in DEFAULT_IMPLEMENTATION_TOML_RELATIVE_PATHS
    )
    assert tuple(path.name for path in config.implementation_toml_paths) == (
        "aware.service.toml",
        "aware.service.toml",
        "aware.service.toml",
        "aware.service.toml",
        "aware.service.toml",
    )
    assert config.reference_experience_toml_paths == ()
    assert DEFAULT_DEPENDENCY_PROVIDER_TOML_RELATIVE_PATHS == (
        local_host_mod.DEFAULT_ENVIRONMENT_IMPLEMENTATION_TOML_RELATIVE_PATH,
        local_host_mod.DEFAULT_ATTENTION_IMPLEMENTATION_TOML_RELATIVE_PATH,
        local_host_mod.DEFAULT_IDENTITY_IMPLEMENTATION_TOML_RELATIVE_PATH,
        local_host_mod.DEFAULT_REACTIVITY_IMPLEMENTATION_TOML_RELATIVE_PATH,
    )
    assert config.environment_api_endpoint == "aware-environment-service://local"
    assert (
        EXPERIENCE_API_ENDPOINT_REFS["resolve_session_view_frame"]
        == EXPERIENCE__SESSION_VIEW_FRAME__RESOLVE_EXPERIENCE_SESSION_VIEW_FRAME_ENDPOINT_REF
    )
    assert (
        EXPERIENCE_API_ENDPOINT_REFS["get_layout_graph_binding_catalog"]
        == EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG_ENDPOINT_REF
    )
    assert (
        EXPERIENCE_API_ENDPOINT_REFS["get_layout_graph_binding_state"]
        == EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE_ENDPOINT_REF
    )
    assert (
        EXPERIENCE_API_ENDPOINT_REFS["activate_layout_graph_binding"]
        == EXPERIENCE__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING_ENDPOINT_REF
    )


def test_local_experience_service_host_config_uses_explicit_env_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for env_name in EXPERIENCE_SDK_REPO_ROOT_ENV_VARS:
        monkeypatch.delenv(env_name, raising=False)
    monkeypatch.setenv(EXPERIENCE_SDK_REPO_ROOT_ENV_VARS[0], str(tmp_path))

    config = resolve_local_experience_service_host_config()

    assert config.repo_root == tmp_path.resolve()


def test_local_experience_service_host_config_requires_explicit_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for env_name in EXPERIENCE_SDK_REPO_ROOT_ENV_VARS:
        monkeypatch.delenv(env_name, raising=False)

    with pytest.raises(RuntimeError, match="repo root is required"):
        resolve_local_experience_service_host_config()


def test_build_local_experience_service_host_app_uses_servicehost_composition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def _fake_build_service_host_app(*, config):  # noqa: ANN001, ANN202
        captured["config"] = config
        return SimpleNamespace()

    monkeypatch.setattr(
        local_host_mod,
        "build_service_host_app",
        _fake_build_service_host_app,
    )
    config = resolve_local_experience_service_host_config(
        repo_root=_REPO_ROOT,
        socket_path=tmp_path / "experience.sock",
        reference_experience_toml_paths=(
            "workspaces/aware_network/modules/interface/experiences/aware_control/aware.experience.toml",
        ),
    )

    app = build_local_experience_service_host_app(config=config)

    assert isinstance(app, SimpleNamespace)
    app_config = captured["config"]
    assert getattr(app_config, "kernel_repo_root") == _REPO_ROOT
    assert getattr(app_config, "environment").api_endpoint == (
        "aware-environment-service://local"
    )
    assert getattr(app_config, "implementation_packages").toml_paths == tuple(
        (_REPO_ROOT / path).resolve()
        for path in DEFAULT_IMPLEMENTATION_TOML_RELATIVE_PATHS
    )
    assert getattr(app_config, "reference_packages").experience_toml_paths == (
        (
            _REPO_ROOT
            / "workspaces/aware_network/modules/interface/experiences/aware_control/aware.experience.toml"
        ).resolve(),
    )


def test_resolve_local_experience_service_api_dependency_routes_from_handshake(
    tmp_path: Path,
) -> None:
    config = resolve_local_experience_service_host_config(
        repo_root=_REPO_ROOT,
        socket_path=tmp_path / "experience.sock",
        ready_file_path=None,
        state_root_path=None,
    )
    routes = resolve_local_experience_service_api_dependency_routes(
        config=config,
        handshake=_handshake_for_route_tests(config),
        request_timeout_s=4.0,
    )

    assert {route.api_package_name for route in routes} == {
        "attention-service-api",
        "environment-service-api",
        "identity-service-api",
        "reactivity-service-api",
    }
    assert {route.provider_service_package_name for route in routes} == {
        "aware-attention-service",
        "aware-environment-service",
        "aware-identity-service",
        "aware-reactivity-service",
    }
    for route in routes:
        assert route.route_kind is ServiceApiDependencyRouteKind.LOCAL_SERVICE_HOST_IPC
        assert route.consumer_service_package_name == "aware-experience-service"
        assert route.socket_path == config.socket_path
        assert route.host_id == "aware-service-host-test"
        assert route.request_timeout_s == 4.0
    reactivity_route = next(
        route for route in routes if route.api_package_name == "reactivity-service-api"
    )
    assert reactivity_route.service_names == ("aware_reactivity",)
    assert reactivity_route.endpoint_refs_by_service == {
        "aware_reactivity": (
            "reactivity.bridge.dispatch_event",
            "reactivity.policy.ensure_bundle",
        )
    }
    assert reactivity_route.stream_endpoint_refs_by_service == {
        "aware_reactivity": ("reactivity.bridge.watch_events",)
    }
    identity_route = next(
        route for route in routes if route.api_package_name == "identity-service-api"
    )
    assert identity_route.service_names == ("aware_identity",)
    assert identity_route.endpoint_refs_by_service == {
        "aware_identity": ("identity.admission.admit_identity",)
    }
    environment_route = next(
        route for route in routes if route.api_package_name == "environment-service-api"
    )
    assert environment_route.service_names == ("aware_environment",)
    assert environment_route.endpoint_refs_by_service == {
        "aware_environment": (ENVIRONMENT__SESSION__RESOLVE_ATTENTION_ENDPOINT_REF,)
    }


@pytest.mark.asyncio
async def test_install_local_experience_service_api_dependency_routes_uses_host_control(
    tmp_path: Path,
) -> None:
    config = resolve_local_experience_service_host_config(
        repo_root=_REPO_ROOT,
        socket_path=tmp_path / "experience.sock",
        ready_file_path=None,
        state_root_path=None,
    )
    recorded: dict[str, object] = {}

    class _FakeExperienceServiceHostApp:
        plugin_services = ("aware_experience",)

        async def start(self) -> tuple[str, ...]:
            return self.plugin_services

        async def close(self) -> None:
            recorded["closed"] = True

        async def handle_handshake(
            self,
            *,
            request: ServiceHostHandshakeRequest,
            endpoint,
        ) -> ServiceHostHandshakeResponse:  # noqa: ANN001
            _ = request
            assert endpoint == config.endpoint
            return _handshake_for_route_tests(config)

        async def handle_host_control_request(
            self,
            *,
            request: ServiceHostControlRequest,
        ) -> ServiceHostControlResponse:
            assert isinstance(
                request,
                ConfigureServiceApiDependencyRoutesHostControlRequest,
            )
            routes = service_api_dependency_routes_from_payload(request.routes)
            recorded["routes"] = routes
            return ConfigureServiceApiDependencyRoutesHostControlResponse(
                status=RequestStatus.succeeded,
                route_count=len(routes),
            )

    server = ServiceHostIpcServer(
        app=cast(Any, _FakeExperienceServiceHostApp()),
        endpoint=config.endpoint,
    )

    await server.start()
    try:
        result = await install_local_experience_service_api_dependency_routes(
            config=config,
            request_timeout_s=2.0,
        )
    finally:
        await server.close()

    assert result.route_count == 4
    assert result.routes == recorded["routes"]
    assert result.handshake.host_id == "aware-service-host-test"
    assert {route.api_package_name for route in result.routes} == {
        "attention-service-api",
        "environment-service-api",
        "identity-service-api",
        "reactivity-service-api",
    }
    assert recorded["closed"] is True


@pytest.mark.asyncio
async def test_experience_sdk_routes_catalog_request_over_local_servicehost_ipc(
    tmp_path: Path,
) -> None:
    recorded: dict[str, object] = {}

    class _FakeExperienceServiceHostApp:
        plugin_services = ("aware_experience",)

        async def start(self) -> tuple[str, ...]:
            return self.plugin_services

        async def close(self) -> None:
            recorded["closed"] = True

        async def handle_duplex_api_ingress_request(
            self,
            *,
            request,
            emit_event,
        ):  # noqa: ANN001, ANN202
            _ = emit_event
            recorded["request"] = request
            return ServiceOperationResponse(
                status=RequestStatus.succeeded,
                response_payload={
                    "operation": "get_experience_section_graph_binding_catalog",
                    "success": True,
                    "experience_name": request.request_payload["experience_name"],
                    "catalog_revision": "local-servicehost-smoke",
                    "bindings": [],
                },
            )

    config = resolve_local_experience_service_host_config(
        repo_root=_REPO_ROOT,
        socket_path=tmp_path / "experience.sock",
        ready_file_path=None,
        state_root_path=None,
    )
    server = ServiceHostIpcServer(
        app=cast(Any, _FakeExperienceServiceHostApp()),
        endpoint=config.endpoint,
    )

    await server.start()
    try:
        sdk = build_local_experience_sdk_client(
            config=config,
            request_timeout_s=2.0,
        )
        response = await sdk.get_section_graph_binding_catalog(
            experience_name="aware_conversations",
            binding_keys=["conversations.active"],
        )
    finally:
        await server.close()

    assert isinstance(response, GetExperienceSectionGraphBindingCatalogResponse)
    assert response.experience_name == "aware_conversations"
    assert response.catalog_revision == "local-servicehost-smoke"
    request = cast(ServiceHostApiIngressRequest, recorded["request"])
    assert (
        request.endpoint_ref
        == EXPERIENCE_API_ENDPOINT_REFS["get_section_graph_binding_catalog"]
    )
    assert (
        request.discriminant
        == EXPERIENCE_API_ENDPOINT_REFS["get_section_graph_binding_catalog"]
    )
    assert request.request_payload["operation"] == (
        "get_experience_section_graph_binding_catalog"
    )
    assert request.request_payload["experience_name"] == "aware_conversations"
    assert request.request_payload["binding_keys"] == ["conversations.active"]
    assert recorded["closed"] is True


def test_experience_sdk_top_level_local_host_export_is_lazy() -> None:
    assert (
        exported_build_local_experience_sdk_client
        is local_host_mod.build_local_experience_sdk_client
    )
