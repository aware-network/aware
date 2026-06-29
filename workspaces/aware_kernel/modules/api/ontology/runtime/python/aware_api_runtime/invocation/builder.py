from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Sequence

from ..models import APIOwnership
from .spec import (
    ApiInvocationApiSpec,
    ApiInvocationCapabilitySpec,
    ApiInvocationEndpointSpec,
    ApiInvocationFulfillmentBindingSpec,
    ApiInvocationManifest,
    ApiInvocationRequestSpec,
    ApiInvocationResponseSpec,
    ApiInvocationStreamEventSpec,
    ApiInvocationStreamSpec,
)

_API_INVOCATION_SCHEMA_VERSION = 1
_API_SHARED_CLIENT_BACKEND = "aware_api.invoker.AwareApiEndpointInvoker"
_API_SHARED_CLIENT_OPERATION = "invoke_api_endpoint"
_API_ADDRESSING_STRATEGY = "session_bound"
_API_INVOCATION_KIND = "shared_client_endpoint"


@dataclass(frozen=True, slots=True)
class ApiInvocationManifestArtifact:
    path: Path
    relpath: str
    hash_sha256: str


def build_api_invocation_manifest(
    *,
    package_name: str,
    fqn_prefix: str,
    api_ownership: Sequence[APIOwnership],
) -> ApiInvocationManifest:
    return ApiInvocationManifest(
        schema_version=_API_INVOCATION_SCHEMA_VERSION,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        apis=[
            ApiInvocationApiSpec(
                name=api.name,
                source_path=api.source_path,
                capabilities=[
                    ApiInvocationCapabilitySpec(
                        name=capability.name,
                        source_path=capability.source_path,
                        description=capability.description,
                        endpoints=[
                            ApiInvocationEndpointSpec(
                                name=endpoint.name,
                                source_path=endpoint.source_path,
                                endpoint_ref=_build_endpoint_ref(
                                    api_name=api.name,
                                    capability_name=capability.name,
                                    endpoint_name=endpoint.name,
                                ),
                                discriminant=_build_endpoint_ref(
                                    api_name=api.name,
                                    capability_name=capability.name,
                                    endpoint_name=endpoint.name,
                                ),
                                invocation_kind=_API_INVOCATION_KIND,
                                client_backend=_API_SHARED_CLIENT_BACKEND,
                                client_operation=_API_SHARED_CLIENT_OPERATION,
                                addressing_strategy=_API_ADDRESSING_STRATEGY,
                                description=endpoint.description,
                                request=ApiInvocationRequestSpec(
                                    class_ref=endpoint.request_config.class_ref,
                                    source_path=endpoint.request_config.source_path,
                                    description=endpoint.request_config.description,
                                ),
                                response=(
                                    ApiInvocationResponseSpec(
                                        class_ref=endpoint.request_config.response_config.class_ref,
                                        source_path=endpoint.request_config.response_config.source_path,
                                        description=endpoint.request_config.response_config.description,
                                    )
                                    if endpoint.request_config.response_config is not None
                                    else None
                                ),
                                stream=(
                                    ApiInvocationStreamSpec(
                                        stream_mode=endpoint.request_config.stream_config.stream_mode,
                                        source_path=endpoint.request_config.stream_config.source_path,
                                        description=endpoint.request_config.stream_config.description,
                                        events=[
                                            ApiInvocationStreamEventSpec(
                                                kind=event.kind,
                                                class_ref=event.class_ref,
                                                source_path=event.source_path,
                                                description=event.description,
                                            )
                                            for event in endpoint.request_config.stream_config.event_configs
                                        ],
                                    )
                                    if endpoint.request_config.stream_config is not None
                                    else None
                                ),
                                fulfillment_bindings=[
                                    ApiInvocationFulfillmentBindingSpec(
                                        name=function.name,
                                        graph_target=function.graph_target,
                                        graph_capability_function_name=function.graph_capability_function_name,
                                        source_path=function.source_path,
                                    )
                                    for function in endpoint.functions
                                ],
                            )
                            for endpoint in capability.endpoints
                        ],
                    )
                    for capability in api.capabilities
                ],
            )
            for api in api_ownership
        ],
    )


def emit_api_invocation_manifest_artifact(
    *,
    manifest: ApiInvocationManifest,
    runtime_package_dir: Path,
    repo_root: Path,
) -> ApiInvocationManifestArtifact:
    runtime_package_dir = runtime_package_dir.resolve()
    repo_root = repo_root.resolve()
    runtime_package_dir.mkdir(parents=True, exist_ok=True)

    payload = manifest.model_dump(mode="json", exclude_none=True)
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = sha256(canonical).hexdigest()

    artifact_path = (runtime_package_dir / "api.invocation_manifest.json").resolve()
    _ = artifact_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    relpath = artifact_path.relative_to(repo_root).as_posix()
    return ApiInvocationManifestArtifact(path=artifact_path, relpath=relpath, hash_sha256=digest)


def _build_endpoint_ref(
    *,
    api_name: str,
    capability_name: str,
    endpoint_name: str,
) -> str:
    return ".".join((api_name, capability_name, endpoint_name))


__all__ = [
    "ApiInvocationManifestArtifact",
    "build_api_invocation_manifest",
    "emit_api_invocation_manifest_artifact",
]
