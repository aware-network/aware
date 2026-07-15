from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
import json
import os
from pathlib import Path
import signal
import sys
import time
from typing import Any, Sequence, cast
from uuid import UUID, uuid4

from aware_code.types import JsonObject
from aware_hub_service.artifact_authority import (
    HubArtifactProducerProvenance,
    PublishHubArtifactRequest,
    ResolveHubArtifactRequest,
)
from aware_comms import DuplexIpcEndpoint
from aware_hub_service.deployment_artifact_authority import (
    ResolveDeploymentArtifactRequest,
)
from aware_hub_service.state_root import isolated_hub_service_state
from aware_service_runtime.contracts import (
    SERVICE_HOST_PROTOCOL_VERSION,
    ServiceHostApiIngressRequest,
    ServiceHostHandshakeRequest,
)
from aware_service_runtime.duplex_client import ServiceHostDuplexClient
from aware_service_service import (
    ServiceHostApp,
    ServiceHostAppConfig,
    ServiceHostImplementationPackageConfig,
    ServiceHostIpcServer,
)

DEFAULT_SOCKET_RELATIVE_PATH = Path(".aware/services/hub/hub-service.sock")
DEFAULT_READY_RELATIVE_PATH = Path(".aware/services/hub/hub-service.ready.json")
DEFAULT_STATE_ROOT_RELATIVE_PATH = Path(".aware/services/hub/state")
DEFAULT_IMPLEMENTATION_TOML_RELATIVE_PATH = Path(
    "workspaces/aware_network/modules/hub/services/hub/aware.service.toml"
)
HUB_REPO_ROOT_ENV_VARS = (
    "AWARE_HUB_SERVICE_REPO_ROOT",
    "AWARE_HUB_REPO_ROOT",
    "AWARE_REPO_ROOT",
    "AWARE_REPOSITORY_ROOT",
)

HUB_API_SERVICE_NAME = "aware_hub"
HUB_ARTIFACT_PUBLISH_ENDPOINT_REF = "hub.artifact.publish"
HUB_ARTIFACT_RESOLVE_ENDPOINT_REF = "hub.artifact.resolve"
HUB_CODE_PACKAGE_PUBLISH_ENDPOINT_REF = "hub.code_package.publish"
HUB_DEPLOYMENT_ARTIFACT_RESOLVE_ENDPOINT_REF = "hub.deployment_artifact.resolve"
HUB_WORKSPACE_DEPLOYMENT_RESOLVE_ENDPOINT_REF = (
    HUB_DEPLOYMENT_ARTIFACT_RESOLVE_ENDPOINT_REF
)


@dataclass(frozen=True, slots=True)
class LocalHubServiceHostConfig:
    socket_path: Path
    implementation_toml_paths: tuple[Path, ...]
    runtime_manifest_path: Path | None
    ready_file_path: Path | None
    state_root_path: Path | None

    @property
    def endpoint(self) -> DuplexIpcEndpoint:
        return DuplexIpcEndpoint.unix_socket(socket_path=str(self.socket_path))


def resolve_local_hub_service_host_config(
    *,
    socket_path: str | Path | None = None,
    implementation_toml_paths: Sequence[str | Path] = (),
    runtime_manifest_path: str | Path | None = None,
    ready_file_path: str | Path | None = DEFAULT_READY_RELATIVE_PATH,
    state_root_path: str | Path | None = DEFAULT_STATE_ROOT_RELATIVE_PATH,
    repo_root: str | Path | None = None,
) -> LocalHubServiceHostConfig:
    root = _resolve_repo_root(repo_root)
    resolved_implementation_tomls = tuple(
        _resolve_path(root=root, value=value)
        for value in (
            implementation_toml_paths or (DEFAULT_IMPLEMENTATION_TOML_RELATIVE_PATH,)
        )
    )
    return LocalHubServiceHostConfig(
        socket_path=_resolve_path(
            root=root,
            value=socket_path or DEFAULT_SOCKET_RELATIVE_PATH,
        ),
        implementation_toml_paths=resolved_implementation_tomls,
        runtime_manifest_path=(
            _resolve_path(root=root, value=runtime_manifest_path)
            if runtime_manifest_path is not None
            else None
        ),
        ready_file_path=(
            _resolve_path(root=root, value=ready_file_path)
            if ready_file_path is not None
            else None
        ),
        state_root_path=(
            _resolve_path(root=root, value=state_root_path)
            if state_root_path is not None
            else None
        ),
    )


def build_local_hub_service_host_app(
    *,
    config: LocalHubServiceHostConfig,
) -> ServiceHostApp:
    return ServiceHostApp(
        config=ServiceHostAppConfig(
            implementation_packages=ServiceHostImplementationPackageConfig(
                toml_paths=config.implementation_toml_paths,
            ),
            runtime_manifest_path=config.runtime_manifest_path,
        )
    )


async def serve_local_hub_service_host(
    *,
    config: LocalHubServiceHostConfig,
) -> dict[str, object]:
    if config.state_root_path is None:
        return await _serve_local_hub_service_host_in_active_state(config=config)

    with isolated_hub_service_state(
        state_root_path=config.state_root_path,
        persistence_backend="fs",
    ):
        return await _serve_local_hub_service_host_in_active_state(config=config)


async def _serve_local_hub_service_host_in_active_state(
    *,
    config: LocalHubServiceHostConfig,
) -> dict[str, object]:
    app = build_local_hub_service_host_app(config=config)
    server = ServiceHostIpcServer(app=app, endpoint=config.endpoint)
    loaded_services = await server.start()
    ready_payload = _build_ready_payload(
        config=config,
        app=app,
        loaded_services=loaded_services,
    )
    _write_ready_file(config=config, payload=ready_payload)
    print(json.dumps(ready_payload, sort_keys=True), flush=True)
    try:
        await _wait_for_shutdown_signal()
    finally:
        await server.close()
    return ready_payload


async def probe_local_hub_service_host(
    *,
    socket_path: str | Path,
    operation: str,
    artifact_key: str | None = None,
    channel: str = "stable",
    revision_id: str | None = None,
    authority_base_url: str | None = None,
    index_url: str | None = None,
    repeat: int = 1,
    timeout_s: float | None = 30.0,
) -> list[dict[str, object]]:
    endpoint = DuplexIpcEndpoint.unix_socket(socket_path=str(Path(socket_path)))
    client = ServiceHostDuplexClient(endpoint=endpoint)
    normalized_operation = _normalize_operation(operation)
    results: list[dict[str, object]] = []
    for index in range(max(repeat, 1)):
        started = time.perf_counter()
        if normalized_operation == "handshake":
            response = await client.send_handshake(
                request=ServiceHostHandshakeRequest(
                    supported_protocol_versions=(SERVICE_HOST_PROTOCOL_VERSION,)
                ),
                timeout_s=timeout_s,
            )
            payload = {
                "host_id": response.host_id,
                "protocol_version": response.protocol_version,
                "readiness": {
                    "is_ready": response.readiness.is_ready,
                    "status": response.readiness.status.value,
                    "reason": response.readiness.reason,
                    "detail_payload": response.readiness.detail_payload,
                },
                "capabilities": [
                    {
                        "capability_id": item.capability_id,
                        "state": item.state.value,
                        "detail_payload": item.detail_payload,
                    }
                    for item in response.capabilities
                ],
            }
            status = "succeeded"
            error = None
        else:
            request = build_hub_api_ingress_request(
                artifact_key=artifact_key,
                channel=channel,
                revision_id=revision_id,
                authority_base_url=authority_base_url,
                index_url=index_url,
            )
            response = await client.send_api_ingress_request(
                request=request,
                timeout_s=timeout_s,
            )
            payload = cast(object, response.response_payload)
            status = response.status.value
            error = response.error
        results.append(
            {
                "operation": normalized_operation,
                "iteration": index + 1,
                "duration_s": round(time.perf_counter() - started, 6),
                "status": status,
                "error": error,
                "payload": payload,
            }
        )
    return results


def build_hub_api_ingress_request(
    *,
    actor_id: UUID | None = None,
    artifact_family: str = "workspace-deployment",
    artifact_key: str | None = None,
    channel: str = "stable",
    revision_id: str | None = None,
    authority_base_url: str | None = None,
    index_url: str | None = None,
) -> ServiceHostApiIngressRequest:
    payload = ResolveDeploymentArtifactRequest(
        request_id=uuid4(),
        artifact_family=artifact_family,
        artifact_key=artifact_key,
        channel=channel,
        revision_id=revision_id,
        authority_base_url=authority_base_url,
        index_url=index_url,
    ).model_dump(mode="json", exclude_none=False)
    return ServiceHostApiIngressRequest(
        actor_id=actor_id,
        endpoint_ref=HUB_DEPLOYMENT_ARTIFACT_RESOLVE_ENDPOINT_REF,
        discriminant=HUB_DEPLOYMENT_ARTIFACT_RESOLVE_ENDPOINT_REF,
        request_payload=cast(JsonObject, payload),
    )


def build_hub_artifact_publish_api_ingress_request(
    *,
    actor_id: UUID | None = None,
    artifact_family: str,
    artifact_key: str,
    revision_id: str,
    channel: str = "stable",
    authority_base_url: str | None = None,
    index_url: str | None = None,
    payload_url: str | None = None,
    payload_sha256: str | None = None,
    payload_size_bytes: int | None = None,
    payload_media_type: str | None = None,
    payload_contract: str | None = None,
    payload_json: JsonObject | None = None,
    payload_bytes_base64: str | None = None,
    payload_source_url: str | None = None,
    selector_key: str | None = None,
    target_ref: str | None = None,
    producer: HubArtifactProducerProvenance | JsonObject | None = None,
    publisher_execution_id: str | None = None,
    idempotency_key: str | None = None,
    published_at_utc: str | None = None,
    metadata: JsonObject | None = None,
) -> ServiceHostApiIngressRequest:
    payload = PublishHubArtifactRequest(
        request_id=uuid4(),
        artifact_family=artifact_family,
        artifact_key=artifact_key,
        revision_id=revision_id,
        channel=channel,
        authority_base_url=authority_base_url,
        index_url=index_url,
        payload_url=payload_url,
        payload_sha256=payload_sha256,
        payload_size_bytes=payload_size_bytes,
        payload_media_type=payload_media_type,
        payload_contract=payload_contract,
        payload_json=payload_json,
        payload_bytes_base64=payload_bytes_base64,
        payload_source_url=payload_source_url,
        selector_key=selector_key,
        target_ref=target_ref,
        producer=cast(Any, producer),
        publisher_execution_id=publisher_execution_id,
        idempotency_key=idempotency_key,
        published_at_utc=published_at_utc,
        metadata=metadata or JsonObject(),
    ).model_dump(mode="json", exclude_none=False)
    return ServiceHostApiIngressRequest(
        actor_id=actor_id,
        endpoint_ref=HUB_ARTIFACT_PUBLISH_ENDPOINT_REF,
        discriminant=HUB_ARTIFACT_PUBLISH_ENDPOINT_REF,
        request_payload=cast(JsonObject, payload),
    )


def build_hub_artifact_resolve_api_ingress_request(
    *,
    actor_id: UUID | None = None,
    artifact_family: str,
    artifact_key: str,
    channel: str = "stable",
    revision_id: str | None = None,
    authority_base_url: str | None = None,
    index_url: str | None = None,
) -> ServiceHostApiIngressRequest:
    payload = ResolveHubArtifactRequest(
        request_id=uuid4(),
        artifact_family=artifact_family,
        artifact_key=artifact_key,
        channel=channel,
        revision_id=revision_id,
        authority_base_url=authority_base_url,
        index_url=index_url,
    ).model_dump(mode="json", exclude_none=False)
    return ServiceHostApiIngressRequest(
        actor_id=actor_id,
        endpoint_ref=HUB_ARTIFACT_RESOLVE_ENDPOINT_REF,
        discriminant=HUB_ARTIFACT_RESOLVE_ENDPOINT_REF,
        request_payload=cast(JsonObject, payload),
    )


def _build_ready_payload(
    *,
    config: LocalHubServiceHostConfig,
    app: ServiceHostApp,
    loaded_services: Sequence[str],
) -> dict[str, object]:
    return {
        "service": "hub",
        "socket_path": config.socket_path.as_posix(),
        "runtime_manifest_path": (
            config.runtime_manifest_path.as_posix()
            if config.runtime_manifest_path is not None
            else None
        ),
        "state_root_path": (
            config.state_root_path.as_posix()
            if config.state_root_path is not None
            else None
        ),
        "implementation_toml_paths": [
            path.as_posix() for path in config.implementation_toml_paths
        ],
        "plugin_services": sorted(loaded_services),
        "activated_implementation_services": list(
            app.activated_implementation_service_names
        ),
        "activated_endpoint_refs_by_service": {
            key: list(value)
            for key, value in app.activated_implementation_endpoint_refs_by_service.items()
        },
    }


def _write_ready_file(
    *,
    config: LocalHubServiceHostConfig,
    payload: dict[str, object],
) -> None:
    if config.ready_file_path is None:
        return
    config.ready_file_path.parent.mkdir(parents=True, exist_ok=True)
    config.ready_file_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


async def _wait_for_shutdown_signal() -> None:
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()
    for item in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(item, stop_event.set)
        except NotImplementedError:  # pragma: no cover - Windows fallback.
            pass
        except RuntimeError:  # pragma: no cover - non-main-thread fallback.
            pass
    await stop_event.wait()


def _resolve_path(*, root: Path, value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def _normalize_operation(value: str) -> str:
    normalized = value.strip().lower().replace("_", "-")
    if normalized == "handshake":
        return normalized
    if normalized == "resolve-deployment-artifact":
        return "resolve_deployment_artifact"
    if normalized == "resolve-workspace-deployment":
        return "resolve_deployment_artifact"
    if normalized == "resolve_deployment_artifact":
        return normalized
    if normalized == "resolve_workspace_deployment":
        return "resolve_deployment_artifact"
    raise ValueError(
        "Unsupported hub operation "
        f"{value!r}; expected handshake or resolve-deployment-artifact."
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aware-hub-service-host",
        description="Local Hub service host and probe harness.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve = subparsers.add_parser("serve", help="Run a local Hub service host.")
    serve.add_argument("--repo-root", default=None)
    serve.add_argument("--socket-path", default=None)
    serve.add_argument("--implementation-toml", action="append", default=[])
    serve.add_argument("--runtime-manifest-path", default=None)
    serve.add_argument("--ready-file", default=str(DEFAULT_READY_RELATIVE_PATH))
    serve.add_argument("--no-ready-file", action="store_true")
    serve.add_argument("--state-root", default=str(DEFAULT_STATE_ROOT_RELATIVE_PATH))
    serve.add_argument(
        "--no-isolated-state",
        action="store_true",
        help="Use the ambient active state instead of a local service state root.",
    )

    probe = subparsers.add_parser("probe", help="Probe a running Hub service host.")
    probe.add_argument(
        "operation",
        choices=(
            "handshake",
            "resolve-deployment-artifact",
            "resolve-workspace-deployment",
        ),
    )
    probe.add_argument("--repo-root", default=None)
    probe.add_argument("--socket-path", default=str(DEFAULT_SOCKET_RELATIVE_PATH))
    probe.add_argument("--artifact-key", default=None)
    probe.add_argument("--channel", default="stable")
    probe.add_argument("--revision-id", default=None)
    probe.add_argument("--authority-base-url", default=None)
    probe.add_argument("--index-url", default=None)
    probe.add_argument("--repeat", type=int, default=1)
    probe.add_argument("--timeout-s", type=float, default=30.0)
    return parser


async def _main_async(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.command == "serve":
        config = resolve_local_hub_service_host_config(
            socket_path=args.socket_path,
            implementation_toml_paths=tuple(args.implementation_toml),
            runtime_manifest_path=args.runtime_manifest_path,
            ready_file_path=(None if args.no_ready_file else args.ready_file),
            state_root_path=(None if args.no_isolated_state else args.state_root),
            repo_root=args.repo_root,
        )
        await serve_local_hub_service_host(config=config)
        return 0

    socket_path = _resolve_path(
        root=_resolve_repo_root(args.repo_root),
        value=args.socket_path,
    )
    results = await probe_local_hub_service_host(
        socket_path=socket_path,
        operation=args.operation,
        artifact_key=args.artifact_key,
        channel=args.channel,
        revision_id=args.revision_id,
        authority_base_url=args.authority_base_url,
        index_url=args.index_url,
        repeat=args.repeat,
        timeout_s=args.timeout_s,
    )
    for item in results:
        print(json.dumps(item, sort_keys=True), flush=True)
    return 0


def _resolve_repo_root(repo_root: str | Path | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).expanduser().resolve()

    for env_var in HUB_REPO_ROOT_ENV_VARS:
        raw = os.environ.get(env_var)
        if raw is not None and raw.strip():
            return Path(raw).expanduser().resolve()

    joined_env_vars = ", ".join(HUB_REPO_ROOT_ENV_VARS)
    raise RuntimeError(
        "Hub local ServiceHost requires an explicit repo_root or one of "
        f"{joined_env_vars} for relative service/probe paths."
    )


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return asyncio.run(_main_async(argv))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
