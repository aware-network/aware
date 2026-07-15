from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import tomllib
from uuid import UUID

from aware_service_runtime.service_api_dependency_routes import (
    ServiceApiDependencyRouteDescriptor,
    service_api_dependency_routes_from_payload,
)
from aware_environment_service.ontology_service_route_selector import (
    OntologyServiceApiRouteSelector,
)

_CONFIG_PATH_ENV = "AWARE_ENVIRONMENT_HOST_CONFIG_PATH"
_RETIRED_RUNTIME_MANIFEST_PATH_ENVS = (
    "AWARE_ENVIRONMENT_HOST_RUNTIME_MANIFEST_PATH",
    "AWARE_ENVIRONMENT_MANIFEST",
)
_WORKSPACE_REVISION_MATERIALIZED_ROOT_ENV = (
    "AWARE_ENVIRONMENT_HOST_WORKSPACE_REVISION_MATERIALIZED_ROOT"
)
_WORKSPACE_REVISION_MANIFEST_PATH_ENV = (
    "AWARE_ENVIRONMENT_HOST_WORKSPACE_REVISION_MANIFEST_PATH"
)
_ENVIRONMENT_PACKAGE_REF_JSON_ENV = "AWARE_ENVIRONMENT_HOST_PACKAGE_REF_JSON"
_RUNTIME_ARTIFACT_REFS_JSON_ENV = "AWARE_ENVIRONMENT_HOST_RUNTIME_ARTIFACT_REFS_JSON"
_RUNTIME_ARTIFACT_REFS_PATH_ENV = "AWARE_ENVIRONMENT_HOST_RUNTIME_ARTIFACT_REFS_PATH"
_SERVICE_API_DEPENDENCY_ROUTES_JSON_ENV = (
    "AWARE_ENVIRONMENT_HOST_SERVICE_API_DEPENDENCY_ROUTES_JSON"
)
_ONTOLOGY_SERVICE_ROUTE_PROVIDER_SERVICE_PACKAGE_ID_ENV = (
    "AWARE_ENVIRONMENT_HOST_ONTOLOGY_SERVICE_ROUTE_PROVIDER_SERVICE_PACKAGE_ID"
)
_ONTOLOGY_SERVICE_ROUTE_PROVIDER_SERVICE_PACKAGE_NAME_ENV = (
    "AWARE_ENVIRONMENT_HOST_ONTOLOGY_SERVICE_ROUTE_PROVIDER_SERVICE_PACKAGE_NAME"
)
_ONTOLOGY_SERVICE_ROUTE_PROVIDER_NODE_ID_ENV = (
    "AWARE_ENVIRONMENT_HOST_ONTOLOGY_SERVICE_ROUTE_PROVIDER_NODE_ID"
)
_ONTOLOGY_SERVICE_ROUTE_HOST_ID_ENV = (
    "AWARE_ENVIRONMENT_HOST_ONTOLOGY_SERVICE_ROUTE_HOST_ID"
)
_ONTOLOGY_SERVICE_ROUTE_CONNECTION_ID_ENV = (
    "AWARE_ENVIRONMENT_HOST_ONTOLOGY_SERVICE_ROUTE_CONNECTION_ID"
)
_ONTOLOGY_SERVICE_ROUTE_SERVICE_NAME_ENV = (
    "AWARE_ENVIRONMENT_HOST_ONTOLOGY_SERVICE_ROUTE_SERVICE_NAME"
)
_ONTOLOGY_SERVICE_ROUTE_PROVIDER_SET_ID_ENV = (
    "AWARE_ENVIRONMENT_HOST_ONTOLOGY_SERVICE_ROUTE_PROVIDER_SET_ID"
)
_ONTOLOGY_SERVICE_ROUTE_WORKSPACE_REVISION_ID_ENV = (
    "AWARE_ENVIRONMENT_HOST_ONTOLOGY_SERVICE_ROUTE_WORKSPACE_REVISION_ID"
)
_ONTOLOGY_SERVICE_ROUTE_WORKSPACE_DEPLOYMENT_REVISION_ID_ENV = (
    "AWARE_ENVIRONMENT_HOST_ONTOLOGY_SERVICE_ROUTE_WORKSPACE_DEPLOYMENT_REVISION_ID"
)
_ONTOLOGY_SERVICE_ROUTE_WORKSPACE_DEPLOYMENT_CHANNEL_ENV = (
    "AWARE_ENVIRONMENT_HOST_ONTOLOGY_SERVICE_ROUTE_WORKSPACE_DEPLOYMENT_CHANNEL"
)
_ONTOLOGY_SERVICE_ROUTE_WORKSPACE_DEPLOYMENT_ARTIFACT_KEY_ENV = (
    "AWARE_ENVIRONMENT_HOST_ONTOLOGY_SERVICE_ROUTE_WORKSPACE_DEPLOYMENT_ARTIFACT_KEY"
)
_SERVICE_API_ROUTE_REGISTRY_ENABLED_ENV = (
    "AWARE_ENVIRONMENT_HOST_SERVICE_API_ROUTE_REGISTRY_ENABLED"
)
_SERVICE_API_ROUTE_REGISTRY_NODE_ID_ENV = (
    "AWARE_ENVIRONMENT_HOST_SERVICE_API_ROUTE_REGISTRY_NODE_ID"
)
_SERVICE_API_ROUTE_REGISTRY_ENVIRONMENT_ID_ENV = (
    "AWARE_ENVIRONMENT_HOST_SERVICE_API_ROUTE_REGISTRY_ENVIRONMENT_ID"
)
_SERVICE_API_ROUTE_REGISTRY_REQUEST_TIMEOUT_S_ENV = (
    "AWARE_ENVIRONMENT_HOST_SERVICE_API_ROUTE_REGISTRY_REQUEST_TIMEOUT_S"
)
_META_TOPOLOGY_SUBSCRIBER_ENABLED_ENV = (
    "AWARE_ENVIRONMENT_META_TOPOLOGY_SUBSCRIBER_ENABLED"
)
_META_TOPOLOGY_SUBSCRIBER_ID_ENV = "AWARE_ENVIRONMENT_META_TOPOLOGY_SUBSCRIBER_ID"
_META_TOPOLOGY_PROJECTION_NAME_ENV = "AWARE_ENVIRONMENT_META_TOPOLOGY_PROJECTION_NAME"


_DEFAULT_META_TOPOLOGY_SUBSCRIBER_ID = "aware_environment.topology"
_DEFAULT_META_TOPOLOGY_PROJECTION_NAME = "EnvironmentProfile"


@dataclass(frozen=True, slots=True)
class EnvironmentHostArtifactRef:
    artifact_family: str
    artifact_key: str
    artifact_role: str
    required_for: tuple[str, ...] = ()
    status: str = "available"
    package_name: str | None = None
    revision_code_package_id: str | None = None
    semantic_package_commit_id: str | None = None
    source_code_package_id: str | None = None
    source_object_instance_graph_commit_id: str | None = None
    input_object_instance_graph_commit_id: str | None = None
    workspace_relative_path: str | None = None
    digest: str | None = None
    digest_algorithm: str | None = None
    media_type: str | None = None
    runtime_contract_version: str | None = None
    provider_payload: dict[str, object] = field(default_factory=dict)
    receipt: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class EnvironmentHostPackageRef:
    family_key: str
    package_kind: str
    package_name: str
    manifest_path: Path | None = None
    workspace_package_id: str | None = None
    semantic_package_id: str | None = None
    semantic_object_instance_graph_commit_id: str | None = None
    semantic_head_commit_id: str | None = None
    semantic_branch_id: str | None = None
    semantic_root_kind: str | None = None
    semantic_root_id: str | None = None
    semantic_root_object_instance_graph_commit_id: str | None = None
    source_code_package_id: str | None = None

    @property
    def has_semantic_identity(self) -> bool:
        return bool(self.semantic_package_id or self.semantic_root_id)


@dataclass(frozen=True, slots=True)
class EnvironmentHostWorkspaceRevisionConfig:
    materialized_workspace_root: Path | None = None
    manifest_path: Path | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentHostMetaTopologySubscriberConfig:
    enabled: bool = False
    subscriber_id: str = _DEFAULT_META_TOPOLOGY_SUBSCRIBER_ID
    topology_projection_name: str = _DEFAULT_META_TOPOLOGY_PROJECTION_NAME


@dataclass(frozen=True, slots=True)
class EnvironmentHostServiceApiRouteRegistryConfig:
    enabled: bool = False
    node_id: UUID | None = None
    environment_id: UUID | None = None
    request_timeout_s: float = 5.0


@dataclass(frozen=True, slots=True)
class EnvironmentHostAppConfig:
    runtime_artifact_refs: tuple[EnvironmentHostArtifactRef, ...] = ()
    workspace_revision: EnvironmentHostWorkspaceRevisionConfig = field(
        default_factory=EnvironmentHostWorkspaceRevisionConfig
    )
    environment_package_ref: EnvironmentHostPackageRef | None = None
    service_api_dependency_routes: tuple[ServiceApiDependencyRouteDescriptor, ...] = ()
    ontology_service_route: OntologyServiceApiRouteSelector = field(
        default_factory=OntologyServiceApiRouteSelector
    )
    service_api_route_registry: EnvironmentHostServiceApiRouteRegistryConfig = field(
        default_factory=EnvironmentHostServiceApiRouteRegistryConfig
    )
    meta_topology_subscriber: EnvironmentHostMetaTopologySubscriberConfig = field(
        default_factory=EnvironmentHostMetaTopologySubscriberConfig
    )

    @classmethod
    def from_env(cls) -> "EnvironmentHostAppConfig":
        return _build_app_config(file_config=_load_file_config_from_env())

    @classmethod
    def from_path(cls, path: str | Path) -> "EnvironmentHostAppConfig":
        return _build_app_config(file_config=_load_file_config(Path(path)))


@dataclass(frozen=True, slots=True)
class _FileConfig:
    source_path: Path
    runtime_artifact_refs: tuple[EnvironmentHostArtifactRef, ...] = ()
    workspace_revision_materialized_root: Path | None = None
    workspace_revision_manifest_path: Path | None = None
    environment_package_ref: EnvironmentHostPackageRef | None = None
    service_api_dependency_routes: tuple[ServiceApiDependencyRouteDescriptor, ...] = ()
    ontology_service_route: OntologyServiceApiRouteSelector = field(
        default_factory=OntologyServiceApiRouteSelector
    )
    service_api_route_registry: EnvironmentHostServiceApiRouteRegistryConfig = field(
        default_factory=EnvironmentHostServiceApiRouteRegistryConfig
    )
    meta_topology_subscriber: EnvironmentHostMetaTopologySubscriberConfig = field(
        default_factory=EnvironmentHostMetaTopologySubscriberConfig
    )


def _load_file_config_from_env() -> _FileConfig | None:
    raw_path = _clean(os.environ.get(_CONFIG_PATH_ENV))
    if not raw_path:
        return None
    return _load_file_config(Path(raw_path))


def _load_file_config(path: Path) -> _FileConfig:
    config_path = path.expanduser().resolve()
    payload = tomllib.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(
            f"Environment host config must be a TOML table: {config_path}"
        )
    base_dir = config_path.parent
    app = _table(payload.get("app"), section="app")
    workspace_revision = _table(
        payload.get("workspace_revision"),
        section="workspace_revision",
    )
    runtime_artifacts = _table(
        payload.get("runtime_artifacts"),
        section="runtime_artifacts",
    )
    package_ref_payload = _table(
        payload.get("environment_package_ref"),
        section="environment_package_ref",
    )
    meta_topology_payload = _table(
        payload.get("meta_topology_subscriber"),
        section="meta_topology_subscriber",
    )
    service_api_route_registry_payload = _table(
        payload.get("service_api_route_registry"),
        section="service_api_route_registry",
    )
    ontology_service_route_payload = _table(
        payload.get("ontology_service_route"),
        section="ontology_service_route",
    )
    _reject_retired_runtime_manifest_file_config(app, config_path=config_path)
    _reject_retired_workspace_revision_ocg_package_refs_file_config(
        workspace_revision,
        config_path=config_path,
    )
    return _FileConfig(
        source_path=config_path,
        workspace_revision_materialized_root=_read_optional_path(
            workspace_revision,
            key="materialized_workspace_root",
            base_dir=base_dir,
        ),
        workspace_revision_manifest_path=_read_optional_path(
            workspace_revision,
            key="manifest_path",
            base_dir=base_dir,
        ),
        runtime_artifact_refs=_artifact_refs_from_payload(
            runtime_artifacts.get("artifact_refs"),
        ),
        environment_package_ref=(
            _package_ref_from_payload(package_ref_payload, base_dir=base_dir)
            if package_ref_payload
            else None
        ),
        service_api_dependency_routes=service_api_dependency_routes_from_payload(
            payload.get("service_api_dependency_routes"),
            base_dir=base_dir,
        ),
        service_api_route_registry=_service_api_route_registry_from_payload(
            service_api_route_registry_payload
        ),
        ontology_service_route=_ontology_service_route_from_payload(
            ontology_service_route_payload
        ),
        meta_topology_subscriber=_meta_topology_subscriber_from_payload(
            meta_topology_payload
        ),
    )


def _build_app_config(*, file_config: _FileConfig | None) -> EnvironmentHostAppConfig:
    _reject_retired_runtime_manifest_env_config()
    _reject_retired_workspace_revision_ocg_package_refs_env_config()
    workspace_revision = EnvironmentHostWorkspaceRevisionConfig(
        materialized_workspace_root=(
            _resolve_optional_path(
                _clean(os.environ.get(_WORKSPACE_REVISION_MATERIALIZED_ROOT_ENV)),
                base_dir=Path.cwd(),
            )
            or (
                file_config.workspace_revision_materialized_root
                if file_config is not None
                else None
            )
        ),
        manifest_path=(
            _resolve_optional_path(
                _clean(os.environ.get(_WORKSPACE_REVISION_MANIFEST_PATH_ENV)),
                base_dir=Path.cwd(),
            )
            or (
                file_config.workspace_revision_manifest_path
                if file_config is not None
                else None
            )
        ),
    )
    package_ref = _package_ref_from_env() or (
        file_config.environment_package_ref if file_config is not None else None
    )
    service_api_dependency_routes = _service_api_dependency_routes_from_env() or (
        file_config.service_api_dependency_routes if file_config is not None else ()
    )
    file_service_api_route_registry = (
        file_config.service_api_route_registry
        if file_config is not None
        else EnvironmentHostServiceApiRouteRegistryConfig()
    )
    file_ontology_service_route = (
        file_config.ontology_service_route
        if file_config is not None
        else OntologyServiceApiRouteSelector()
    )
    file_meta_topology = (
        file_config.meta_topology_subscriber
        if file_config is not None
        else EnvironmentHostMetaTopologySubscriberConfig()
    )
    return EnvironmentHostAppConfig(
        runtime_artifact_refs=(
            _runtime_artifact_refs_from_env()
            or (file_config.runtime_artifact_refs if file_config is not None else ())
        ),
        workspace_revision=workspace_revision,
        environment_package_ref=package_ref,
        service_api_dependency_routes=service_api_dependency_routes,
        ontology_service_route=_ontology_service_route_from_env(
            file_config=file_ontology_service_route
        ),
        service_api_route_registry=_service_api_route_registry_from_env(
            file_config=file_service_api_route_registry
        ),
        meta_topology_subscriber=_meta_topology_subscriber_from_env(
            file_config=file_meta_topology
        ),
    )


def _reject_retired_runtime_manifest_env_config() -> None:
    configured = [
        env_name
        for env_name in _RETIRED_RUNTIME_MANIFEST_PATH_ENVS
        if _clean(os.environ.get(env_name))
    ]
    if configured:
        names = ", ".join(configured)
        raise RuntimeError(
            "Environment host runtime manifest config is retired "
            f"({names}). Provide ontology runtime artifact refs via "
            "AWARE_ENVIRONMENT_HOST_RUNTIME_ARTIFACT_REFS_JSON or "
            "AWARE_ENVIRONMENT_HOST_RUNTIME_ARTIFACT_REFS_PATH."
        )


def _reject_retired_runtime_manifest_file_config(
    app: dict[str, object],
    *,
    config_path: Path,
) -> None:
    if "runtime_manifest_path" not in app:
        return
    value = app.get("runtime_manifest_path")
    if value is not None and not isinstance(value, str):
        raise RuntimeError(
            "Environment host [app].runtime_manifest_path is retired "
            f"in {config_path}; remove the field and provide ontology runtime "
            "artifact refs in [runtime_artifacts].artifact_refs."
        )
    if _clean(value):
        raise RuntimeError(
            "Environment host [app].runtime_manifest_path is retired "
            f"in {config_path}. Provide ontology runtime artifact refs in "
            "[runtime_artifacts].artifact_refs instead."
        )


def _reject_retired_workspace_revision_ocg_package_refs_env_config() -> None:
    retired_envs = (
        "AWARE_ENVIRONMENT_HOST_WORKSPACE_REVISION_OCG_PACKAGE_REFS_JSON",
        "AWARE_ENVIRONMENT_HOST_WORKSPACE_REVISION_OCG_PACKAGE_REFS_PATH",
    )
    configured = [
        env_name for env_name in retired_envs if _clean(os.environ.get(env_name))
    ]
    if not configured:
        return
    names = ", ".join(configured)
    raise RuntimeError(
        "Environment host WorkspaceRevision OCG package refs are retired "
        f"({names}). Provide ontology runtime artifact refs via "
        "AWARE_ENVIRONMENT_HOST_RUNTIME_ARTIFACT_REFS_JSON or "
        "AWARE_ENVIRONMENT_HOST_RUNTIME_ARTIFACT_REFS_PATH."
    )


def _reject_retired_workspace_revision_ocg_package_refs_file_config(
    workspace_revision: dict[str, object],
    *,
    config_path: Path,
) -> None:
    if "object_config_graph_package_refs" not in workspace_revision:
        return
    raise RuntimeError(
        "Environment host [workspace_revision].object_config_graph_package_refs "
        f"is retired in {config_path}. Provide ontology runtime artifact refs in "
        "[runtime_artifacts].artifact_refs instead."
    )


def _runtime_artifact_refs_from_env() -> tuple[EnvironmentHostArtifactRef, ...]:
    payload = _json_payload_from_env_or_path(
        json_env=_RUNTIME_ARTIFACT_REFS_JSON_ENV,
        path_env=_RUNTIME_ARTIFACT_REFS_PATH_ENV,
        label="Environment host runtime_artifact_refs",
    )
    if payload is None:
        return ()
    return _artifact_refs_from_payload(payload)


def _artifact_refs_from_payload(
    payload: object,
) -> tuple[EnvironmentHostArtifactRef, ...]:
    if payload is None:
        return ()
    if not isinstance(payload, list):
        raise RuntimeError("Environment host runtime_artifact_refs must be a list.")
    refs: list[EnvironmentHostArtifactRef] = []
    for item in payload:
        if not isinstance(item, dict):
            raise RuntimeError(
                "Environment host runtime_artifact_refs entries must be tables."
            )
        refs.append(_artifact_ref_from_payload(item))
    return tuple(refs)


def _artifact_ref_from_payload(
    payload: dict[str, object],
) -> EnvironmentHostArtifactRef:
    return EnvironmentHostArtifactRef(
        artifact_family=_read_required_token(payload, key="artifact_family"),
        artifact_key=_read_required_token(payload, key="artifact_key"),
        artifact_role=_read_required_token(payload, key="artifact_role"),
        required_for=_read_optional_token_tuple(payload, key="required_for"),
        status=_read_optional_token(payload, key="status") or "available",
        package_name=_read_optional_token(payload, key="package_name"),
        revision_code_package_id=_read_optional_token(
            payload,
            key="revision_code_package_id",
        ),
        semantic_package_commit_id=_read_optional_token(
            payload,
            key="semantic_package_commit_id",
        ),
        source_code_package_id=_read_optional_token(
            payload,
            key="source_code_package_id",
        ),
        source_object_instance_graph_commit_id=_read_optional_token(
            payload,
            key="source_object_instance_graph_commit_id",
        ),
        input_object_instance_graph_commit_id=_read_optional_token(
            payload,
            key="input_object_instance_graph_commit_id",
        ),
        workspace_relative_path=_read_optional_token(
            payload,
            key="workspace_relative_path",
        ),
        digest=_read_optional_token(payload, key="digest"),
        digest_algorithm=_read_optional_token(payload, key="digest_algorithm"),
        media_type=_read_optional_token(payload, key="media_type"),
        runtime_contract_version=_read_optional_token(
            payload,
            key="runtime_contract_version",
        ),
        provider_payload=_read_optional_payload(payload, key="provider_payload"),
        receipt=_read_optional_payload(payload, key="receipt"),
    )


def _json_payload_from_env_or_path(
    *,
    json_env: str,
    path_env: str,
    label: str,
) -> object | None:
    raw_json = _clean(os.environ.get(json_env))
    if raw_json:
        return json.loads(raw_json)
    raw_path = _clean(os.environ.get(path_env))
    if not raw_path:
        return None
    path = Path(raw_path).expanduser().resolve()
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RuntimeError(f"{label} file is unreadable: {path}") from exc


def _package_ref_from_env() -> EnvironmentHostPackageRef | None:
    raw_json = _clean(os.environ.get(_ENVIRONMENT_PACKAGE_REF_JSON_ENV))
    if not raw_json:
        return None
    payload = json.loads(raw_json)
    if not isinstance(payload, dict):
        raise RuntimeError(
            f"{_ENVIRONMENT_PACKAGE_REF_JSON_ENV} must contain a JSON object."
        )
    return _package_ref_from_payload(payload, base_dir=Path.cwd())


def _service_api_dependency_routes_from_env() -> tuple[
    ServiceApiDependencyRouteDescriptor,
    ...,
]:
    raw_json = _clean(os.environ.get(_SERVICE_API_DEPENDENCY_ROUTES_JSON_ENV))
    if not raw_json:
        return ()
    payload = json.loads(raw_json)
    return service_api_dependency_routes_from_payload(payload, base_dir=Path.cwd())


def _ontology_service_route_from_env(
    *,
    file_config: OntologyServiceApiRouteSelector,
) -> OntologyServiceApiRouteSelector:
    return OntologyServiceApiRouteSelector(
        provider_service_package_id=(
            _read_env_uuid(_ONTOLOGY_SERVICE_ROUTE_PROVIDER_SERVICE_PACKAGE_ID_ENV)
            or file_config.provider_service_package_id
        ),
        provider_service_package_name=(
            _clean(
                os.environ.get(
                    _ONTOLOGY_SERVICE_ROUTE_PROVIDER_SERVICE_PACKAGE_NAME_ENV
                )
            )
            or file_config.provider_service_package_name
        ),
        provider_node_id=(
            _read_env_uuid(_ONTOLOGY_SERVICE_ROUTE_PROVIDER_NODE_ID_ENV)
            or file_config.provider_node_id
        ),
        host_id=(
            _clean(os.environ.get(_ONTOLOGY_SERVICE_ROUTE_HOST_ID_ENV))
            or file_config.host_id
        ),
        route_connection_id=(
            _read_env_uuid(_ONTOLOGY_SERVICE_ROUTE_CONNECTION_ID_ENV)
            or file_config.route_connection_id
        ),
        service_name=(
            _clean(os.environ.get(_ONTOLOGY_SERVICE_ROUTE_SERVICE_NAME_ENV))
            or file_config.service_name
        ),
        provider_set_id=(
            _clean(os.environ.get(_ONTOLOGY_SERVICE_ROUTE_PROVIDER_SET_ID_ENV))
            or file_config.provider_set_id
        ),
        workspace_revision_id=(
            _read_env_uuid(_ONTOLOGY_SERVICE_ROUTE_WORKSPACE_REVISION_ID_ENV)
            or file_config.workspace_revision_id
        ),
        workspace_deployment_revision_id=(
            _clean(
                os.environ.get(
                    _ONTOLOGY_SERVICE_ROUTE_WORKSPACE_DEPLOYMENT_REVISION_ID_ENV
                )
            )
            or file_config.workspace_deployment_revision_id
        ),
        workspace_deployment_channel=(
            _clean(
                os.environ.get(_ONTOLOGY_SERVICE_ROUTE_WORKSPACE_DEPLOYMENT_CHANNEL_ENV)
            )
            or file_config.workspace_deployment_channel
        ),
        workspace_deployment_artifact_key=(
            _clean(
                os.environ.get(
                    _ONTOLOGY_SERVICE_ROUTE_WORKSPACE_DEPLOYMENT_ARTIFACT_KEY_ENV
                )
            )
            or file_config.workspace_deployment_artifact_key
        ),
    )


def _ontology_service_route_from_payload(
    payload: dict[str, object],
) -> OntologyServiceApiRouteSelector:
    return OntologyServiceApiRouteSelector(
        provider_service_package_id=_read_optional_uuid(
            payload,
            key="provider_service_package_id",
        ),
        provider_service_package_name=_read_optional_token(
            payload,
            key="provider_service_package_name",
        ),
        provider_node_id=_read_optional_uuid(payload, key="provider_node_id"),
        host_id=_read_optional_token(payload, key="host_id"),
        route_connection_id=_read_optional_uuid(
            payload,
            key="route_connection_id",
        ),
        service_name=_read_optional_token(payload, key="service_name"),
        provider_set_id=_read_optional_token(payload, key="provider_set_id"),
        workspace_revision_id=_read_optional_uuid(
            payload,
            key="workspace_revision_id",
        ),
        workspace_deployment_revision_id=_read_optional_token(
            payload,
            key="workspace_deployment_revision_id",
        ),
        workspace_deployment_channel=_read_optional_token(
            payload,
            key="workspace_deployment_channel",
        ),
        workspace_deployment_artifact_key=_read_optional_token(
            payload,
            key="workspace_deployment_artifact_key",
        ),
    )


def _service_api_route_registry_from_env(
    *,
    file_config: EnvironmentHostServiceApiRouteRegistryConfig,
) -> EnvironmentHostServiceApiRouteRegistryConfig:
    return EnvironmentHostServiceApiRouteRegistryConfig(
        enabled=_read_env_bool(
            _SERVICE_API_ROUTE_REGISTRY_ENABLED_ENV,
            default=file_config.enabled,
        ),
        node_id=(
            _read_env_uuid(_SERVICE_API_ROUTE_REGISTRY_NODE_ID_ENV)
            or file_config.node_id
        ),
        environment_id=(
            _read_env_uuid(_SERVICE_API_ROUTE_REGISTRY_ENVIRONMENT_ID_ENV)
            or file_config.environment_id
        ),
        request_timeout_s=(
            _read_env_float(_SERVICE_API_ROUTE_REGISTRY_REQUEST_TIMEOUT_S_ENV)
            or file_config.request_timeout_s
        ),
    )


def _service_api_route_registry_from_payload(
    payload: dict[str, object],
) -> EnvironmentHostServiceApiRouteRegistryConfig:
    return EnvironmentHostServiceApiRouteRegistryConfig(
        enabled=_read_optional_bool(payload, key="enabled", default=False),
        node_id=_read_optional_uuid(payload, key="node_id"),
        environment_id=_read_optional_uuid(payload, key="environment_id"),
        request_timeout_s=_read_optional_float(
            payload,
            key="request_timeout_s",
            default=5.0,
        ),
    )


def _meta_topology_subscriber_from_env(
    *,
    file_config: EnvironmentHostMetaTopologySubscriberConfig,
) -> EnvironmentHostMetaTopologySubscriberConfig:
    enabled = _read_env_bool(
        _META_TOPOLOGY_SUBSCRIBER_ENABLED_ENV,
        default=file_config.enabled,
    )
    subscriber_id = (
        _clean(os.environ.get(_META_TOPOLOGY_SUBSCRIBER_ID_ENV))
        or file_config.subscriber_id
        or _DEFAULT_META_TOPOLOGY_SUBSCRIBER_ID
    )
    topology_projection_name = (
        _clean(os.environ.get(_META_TOPOLOGY_PROJECTION_NAME_ENV))
        or file_config.topology_projection_name
        or _DEFAULT_META_TOPOLOGY_PROJECTION_NAME
    )
    return EnvironmentHostMetaTopologySubscriberConfig(
        enabled=enabled,
        subscriber_id=subscriber_id,
        topology_projection_name=topology_projection_name,
    )


def _meta_topology_subscriber_from_payload(
    payload: dict[str, object],
) -> EnvironmentHostMetaTopologySubscriberConfig:
    return EnvironmentHostMetaTopologySubscriberConfig(
        enabled=_read_optional_bool(payload, key="enabled", default=False),
        subscriber_id=(
            _read_optional_token(payload, key="subscriber_id")
            or _DEFAULT_META_TOPOLOGY_SUBSCRIBER_ID
        ),
        topology_projection_name=(
            _read_optional_token(payload, key="topology_projection_name")
            or _DEFAULT_META_TOPOLOGY_PROJECTION_NAME
        ),
    )


def _package_ref_from_payload(
    payload: dict[str, object],
    *,
    base_dir: Path,
) -> EnvironmentHostPackageRef:
    return EnvironmentHostPackageRef(
        family_key=_read_required_token(payload, key="family_key"),
        package_kind=_read_required_token(payload, key="package_kind"),
        package_name=_read_required_token(payload, key="package_name"),
        manifest_path=_read_optional_path(
            payload, key="manifest_path", base_dir=base_dir
        ),
        workspace_package_id=_read_optional_token(payload, key="workspace_package_id"),
        semantic_package_id=_read_optional_token(payload, key="semantic_package_id"),
        semantic_object_instance_graph_commit_id=_read_optional_token(
            payload,
            key="semantic_object_instance_graph_commit_id",
        ),
        semantic_head_commit_id=_read_optional_token(
            payload,
            key="semantic_head_commit_id",
        ),
        semantic_branch_id=_read_optional_token(payload, key="semantic_branch_id"),
        semantic_root_kind=_read_optional_token(payload, key="semantic_root_kind"),
        semantic_root_id=_read_optional_token(payload, key="semantic_root_id"),
        semantic_root_object_instance_graph_commit_id=_read_optional_token(
            payload,
            key="semantic_root_object_instance_graph_commit_id",
        ),
        source_code_package_id=_read_optional_token(
            payload, key="source_code_package_id"
        ),
    )


def _table(value: object, *, section: str) -> dict[str, object]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise RuntimeError(
            f"Environment host config section [{section}] must be a table."
        )
    return value


def _read_required_token(payload: dict[str, object], *, key: str) -> str:
    token = _read_optional_token(payload, key=key)
    if token is None:
        raise RuntimeError(
            f"Environment host package ref field {key!r} must be a non-empty string."
        )
    return token


def _read_optional_token(payload: dict[str, object], *, key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise RuntimeError(
            f"Environment host config field {key!r} must be a string when set."
        )
    return _clean(value) or None


def _read_optional_token_tuple(
    payload: dict[str, object],
    *,
    key: str,
) -> tuple[str, ...]:
    value = payload.get(key)
    if value is None:
        return ()
    if isinstance(value, str):
        token = _clean(value)
        return (token,) if token else ()
    if not isinstance(value, list):
        raise RuntimeError(
            f"Environment host config field {key!r} must be a string list when set."
        )
    tokens: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise RuntimeError(
                f"Environment host config field {key!r} must be a string list."
            )
        token = _clean(item)
        if token:
            tokens.append(token)
    return tuple(tokens)


def _read_optional_payload(
    payload: dict[str, object],
    *,
    key: str,
) -> dict[str, object]:
    value = payload.get(key)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise RuntimeError(f"Environment host config field {key!r} must be a table.")
    return {str(raw_key): item for raw_key, item in value.items()}


def _read_optional_bool(
    payload: dict[str, object],
    *,
    key: str,
    default: bool,
) -> bool:
    value = payload.get(key)
    if value is None:
        return default
    if not isinstance(value, bool):
        raise RuntimeError(
            f"Environment host config field {key!r} must be a bool when set."
        )
    return value


def _read_env_bool(name: str, *, default: bool) -> bool:
    raw_value = _clean(os.environ.get(name))
    if not raw_value:
        return default
    normalized = raw_value.lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(f"{name} must be a boolean token when set.")


def _read_env_float(name: str) -> float | None:
    raw_value = _clean(os.environ.get(name))
    if not raw_value:
        return None
    try:
        return float(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be numeric when set.") from exc


def _read_env_uuid(name: str) -> UUID | None:
    raw_value = _clean(os.environ.get(name))
    if not raw_value:
        return None
    try:
        return UUID(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a UUID when set.") from exc


def _read_optional_float(
    payload: dict[str, object],
    *,
    key: str,
    default: float,
) -> float:
    value = payload.get(key)
    if value is None:
        return default
    if not isinstance(value, int | float):
        raise RuntimeError(
            f"Environment host config field {key!r} must be numeric when set."
        )
    return float(value)


def _read_optional_uuid(payload: dict[str, object], *, key: str) -> UUID | None:
    token = _read_optional_token(payload, key=key)
    if token is None:
        return None
    try:
        return UUID(token)
    except ValueError as exc:
        raise RuntimeError(
            f"Environment host config field {key!r} must be a UUID when set."
        ) from exc


def _read_optional_path(
    payload: dict[str, object],
    *,
    key: str,
    base_dir: Path,
) -> Path | None:
    return _resolve_optional_path(
        _read_optional_token(payload, key=key),
        base_dir=base_dir,
    )


def _resolve_optional_path(raw_value: str | None, *, base_dir: Path) -> Path | None:
    cleaned = _clean(raw_value)
    if not cleaned:
        return None
    path = Path(cleaned).expanduser()
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve()


def _clean(value: str | None) -> str:
    return (value or "").strip()


__all__ = [
    "EnvironmentHostAppConfig",
    "EnvironmentHostArtifactRef",
    "EnvironmentHostMetaTopologySubscriberConfig",
    "EnvironmentHostPackageRef",
    "EnvironmentHostServiceApiRouteRegistryConfig",
    "EnvironmentHostWorkspaceRevisionConfig",
    "OntologyServiceApiRouteSelector",
]
