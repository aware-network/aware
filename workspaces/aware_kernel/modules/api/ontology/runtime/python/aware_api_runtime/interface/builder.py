from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Sequence

from ..models import APIOwnership
from .spec import (
    ApiInterfaceApiSpec,
    ApiInterfaceCapabilitySpec,
    ApiInterfaceEndpointSpec,
    ApiInterfaceRequestSpec,
    ApiInterfaceResponseSpec,
    ApiInterfaceSpec,
    ApiInterfaceStreamEventSpec,
    ApiInterfaceStreamSpec,
)


@dataclass(frozen=True, slots=True)
class ApiInterfaceSpecArtifact:
    path: Path
    relpath: str
    hash_sha256: str


def build_api_interface_spec(
    *,
    package_name: str,
    fqn_prefix: str,
    api_ownership: Sequence[APIOwnership],
) -> ApiInterfaceSpec:
    return ApiInterfaceSpec(
        schema_version=1,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        apis=[
            ApiInterfaceApiSpec(
                name=api.name,
                source_path=api.source_path,
                capabilities=[
                    ApiInterfaceCapabilitySpec(
                        name=capability.name,
                        source_path=capability.source_path,
                        description=capability.description,
                        endpoints=[
                            ApiInterfaceEndpointSpec(
                                name=endpoint.name,
                                source_path=endpoint.source_path,
                                description=endpoint.description,
                                discriminant=_build_endpoint_discriminant(
                                    api_name=api.name,
                                    capability_name=capability.name,
                                    endpoint_name=endpoint.name,
                                ),
                                request=ApiInterfaceRequestSpec(
                                    class_ref=endpoint.request_config.class_ref,
                                    source_path=endpoint.request_config.source_path,
                                    description=endpoint.request_config.description,
                                ),
                                response=(
                                    ApiInterfaceResponseSpec(
                                        class_ref=endpoint.request_config.response_config.class_ref,
                                        source_path=endpoint.request_config.response_config.source_path,
                                        description=endpoint.request_config.response_config.description,
                                    )
                                    if endpoint.request_config.response_config is not None
                                    else None
                                ),
                                stream=(
                                    ApiInterfaceStreamSpec(
                                        stream_mode=endpoint.request_config.stream_config.stream_mode,
                                        source_path=endpoint.request_config.stream_config.source_path,
                                        description=endpoint.request_config.stream_config.description,
                                        events=[
                                            ApiInterfaceStreamEventSpec(
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


def emit_api_interface_spec_artifact(
    *,
    spec: ApiInterfaceSpec,
    runtime_package_dir: Path,
    repo_root: Path,
) -> ApiInterfaceSpecArtifact:
    runtime_package_dir = runtime_package_dir.resolve()
    repo_root = repo_root.resolve()
    runtime_package_dir.mkdir(parents=True, exist_ok=True)

    payload = spec.model_dump(mode="json", exclude_none=True)
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = sha256(canonical).hexdigest()

    artifact_path = (runtime_package_dir / "api.interface_spec.json").resolve()
    _ = artifact_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    relpath = artifact_path.relative_to(repo_root).as_posix()
    return ApiInterfaceSpecArtifact(path=artifact_path, relpath=relpath, hash_sha256=digest)


def _build_endpoint_discriminant(
    *,
    api_name: str,
    capability_name: str,
    endpoint_name: str,
) -> str:
    return ".".join((api_name, capability_name, endpoint_name))


__all__ = [
    "ApiInterfaceSpecArtifact",
    "build_api_interface_spec",
    "emit_api_interface_spec_artifact",
]
