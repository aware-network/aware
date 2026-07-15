from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from ..interface.builder import ApiInterfaceSpecArtifact
from ..invocation.builder import ApiInvocationManifestArtifact
from .models import (
    ApiProductRuntimeArtifactRef,
    ApiPublicPackageLoweringHandoff,
    ApiPublicPackagePlan,
    ApiPublicPackagePlanArtifact,
    ApiServiceProtocolLoweringHandoff,
    ApiServiceProtocolPlan,
    ApiServiceProtocolPlanArtifact,
)

_API_PUBLIC_PACKAGE_LOWERING_SCHEMA_VERSION = 1
_API_SERVICE_PROTOCOL_LOWERING_SCHEMA_VERSION = 1

type _ArtifactRefLike = (
    ApiInterfaceSpecArtifact
    | ApiInvocationManifestArtifact
    | ApiPublicPackagePlanArtifact
    | ApiServiceProtocolPlanArtifact
)


def emit_api_public_package_plan_artifact(
    *,
    plan: ApiPublicPackagePlan,
    runtime_package_dir: Path,
    repo_root: Path,
) -> ApiPublicPackagePlanArtifact:
    runtime_package_dir = runtime_package_dir.resolve()
    repo_root = repo_root.resolve()
    runtime_package_dir.mkdir(parents=True, exist_ok=True)

    payload = _encode_public_package_plan(plan=plan)
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    digest = sha256(canonical).hexdigest()

    artifact_path = (runtime_package_dir / "api.public_package_plan.json").resolve()
    _ = artifact_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    relpath = artifact_path.relative_to(repo_root).as_posix()
    return ApiPublicPackagePlanArtifact(
        path=artifact_path,
        relpath=relpath,
        hash_sha256=digest,
    )


def build_api_public_package_lowering_handoff(
    *,
    plan: ApiPublicPackagePlan,
    interface_spec_artifact: ApiInterfaceSpecArtifact,
    invocation_manifest_artifact: ApiInvocationManifestArtifact,
    public_package_plan_artifact: ApiPublicPackagePlanArtifact,
    extra_runtime_artifacts: tuple[ApiProductRuntimeArtifactRef, ...] = (),
) -> ApiPublicPackageLoweringHandoff:
    return ApiPublicPackageLoweringHandoff(
        schema_version=_API_PUBLIC_PACKAGE_LOWERING_SCHEMA_VERSION,
        package_name=plan.package_name,
        fqn_prefix=plan.fqn_prefix,
        backend_handoff=plan.backend_handoff,
        runtime_artifacts=(
            _artifact_ref(
                kind="api.interface_spec",
                artifact=interface_spec_artifact,
            ),
            _artifact_ref(
                kind="api.invocation_manifest",
                artifact=invocation_manifest_artifact,
            ),
            _artifact_ref(
                kind="api.public_package_plan",
                artifact=public_package_plan_artifact,
            ),
            *extra_runtime_artifacts,
        ),
    )


def emit_api_service_protocol_plan_artifact(
    *,
    plan: ApiServiceProtocolPlan,
    runtime_package_dir: Path,
    repo_root: Path,
) -> ApiServiceProtocolPlanArtifact:
    runtime_package_dir = runtime_package_dir.resolve()
    repo_root = repo_root.resolve()
    runtime_package_dir.mkdir(parents=True, exist_ok=True)

    payload = _encode_service_protocol_plan(plan=plan)
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    digest = sha256(canonical).hexdigest()

    artifact_path = (runtime_package_dir / "api.service_protocol_plan.json").resolve()
    _ = artifact_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    relpath = artifact_path.relative_to(repo_root).as_posix()
    return ApiServiceProtocolPlanArtifact(
        path=artifact_path,
        relpath=relpath,
        hash_sha256=digest,
    )


def build_api_service_protocol_lowering_handoff(
    *,
    plan: ApiServiceProtocolPlan,
    interface_spec_artifact: ApiInterfaceSpecArtifact,
    invocation_manifest_artifact: ApiInvocationManifestArtifact,
    public_package_plan_artifact: ApiPublicPackagePlanArtifact,
    service_protocol_plan_artifact: ApiServiceProtocolPlanArtifact,
    extra_runtime_artifacts: tuple[ApiProductRuntimeArtifactRef, ...] = (),
) -> ApiServiceProtocolLoweringHandoff:
    return ApiServiceProtocolLoweringHandoff(
        schema_version=_API_SERVICE_PROTOCOL_LOWERING_SCHEMA_VERSION,
        package_name=plan.package_name,
        fqn_prefix=plan.fqn_prefix,
        backend_handoff=plan.backend_handoff,
        runtime_artifacts=(
            _artifact_ref(
                kind="api.interface_spec",
                artifact=interface_spec_artifact,
            ),
            _artifact_ref(
                kind="api.invocation_manifest",
                artifact=invocation_manifest_artifact,
            ),
            _artifact_ref(
                kind="api.public_package_plan",
                artifact=public_package_plan_artifact,
            ),
            _artifact_ref(
                kind="api.service_protocol_plan",
                artifact=service_protocol_plan_artifact,
            ),
            *extra_runtime_artifacts,
        ),
    )


def _artifact_ref(
    *,
    kind: str,
    artifact: _ArtifactRefLike,
) -> ApiProductRuntimeArtifactRef:
    return ApiProductRuntimeArtifactRef(
        kind=kind,
        relpath=artifact.relpath,
        hash_sha256=artifact.hash_sha256,
    )


def _encode_public_package_plan(*, plan: ApiPublicPackagePlan) -> dict[str, object]:
    return {
        "schema_version": plan.schema_version,
        "package_name": plan.package_name,
        "fqn_prefix": plan.fqn_prefix,
        "backend_handoff": {
            "materialization_source": plan.backend_handoff.materialization_source.value,
            "aware_package_kind": plan.backend_handoff.aware_package_kind,
            "expected_renderer_profile": plan.backend_handoff.expected_renderer_profile,
        },
        "apis": [
            {
                "name": api.name,
                "description": api.description,
                "source_path": api.source_path,
                "capabilities": [
                    {
                        "api_name": capability.api_name,
                        "name": capability.name,
                        "description": capability.description,
                        "source_path": capability.source_path,
                        "endpoints": [
                            {
                                "api_name": endpoint.api_name,
                                "capability_name": endpoint.capability_name,
                                "name": endpoint.name,
                                "discriminant": endpoint.discriminant,
                                "description": endpoint.description,
                                "source_path": endpoint.source_path,
                                "request": {
                                    "class_ref": endpoint.request.class_ref,
                                    "description": endpoint.request.description,
                                    "source_path": endpoint.request.source_path,
                                },
                                "response": (
                                    {
                                        "class_ref": endpoint.response.class_ref,
                                        "description": endpoint.response.description,
                                        "source_path": endpoint.response.source_path,
                                    }
                                    if endpoint.response is not None
                                    else None
                                ),
                                "stream": (
                                    {
                                        "stream_mode": endpoint.stream.stream_mode,
                                        "description": endpoint.stream.description,
                                        "source_path": endpoint.stream.source_path,
                                        "events": [
                                            {
                                                "kind": event.kind,
                                                "class_ref": event.class_ref,
                                                "description": event.description,
                                                "source_path": event.source_path,
                                            }
                                            for event in endpoint.stream.events
                                        ],
                                    }
                                    if endpoint.stream is not None
                                    else None
                                ),
                            }
                            for endpoint in capability.endpoints
                        ],
                    }
                    for capability in api.capabilities
                ],
            }
            for api in plan.apis
        ],
    }


def _encode_service_protocol_plan(*, plan: ApiServiceProtocolPlan) -> dict[str, object]:
    return {
        "schema_version": plan.schema_version,
        "package_name": plan.package_name,
        "fqn_prefix": plan.fqn_prefix,
        "backend_handoff": {
            "materialization_source": plan.backend_handoff.materialization_source.value,
            "aware_package_kind": plan.backend_handoff.aware_package_kind,
            "expected_renderer_profile": plan.backend_handoff.expected_renderer_profile,
        },
        "apis": [
            {
                "name": api.name,
                "description": api.description,
                "source_path": api.source_path,
                "capabilities": [
                    {
                        "api_name": capability.api_name,
                        "name": capability.name,
                        "description": capability.description,
                        "source_path": capability.source_path,
                        "endpoints": [
                            {
                                "api_name": endpoint.api_name,
                                "capability_name": endpoint.capability_name,
                                "name": endpoint.name,
                                "endpoint_ref": endpoint.endpoint_ref,
                                "discriminant": endpoint.discriminant,
                                "description": endpoint.description,
                                "source_path": endpoint.source_path,
                                "request": {
                                    "class_ref": endpoint.request.class_ref,
                                    "description": endpoint.request.description,
                                    "source_path": endpoint.request.source_path,
                                },
                                "response": (
                                    {
                                        "class_ref": endpoint.response.class_ref,
                                        "description": endpoint.response.description,
                                        "source_path": endpoint.response.source_path,
                                    }
                                    if endpoint.response is not None
                                    else None
                                ),
                                "stream": (
                                    {
                                        "stream_mode": endpoint.stream.stream_mode,
                                        "description": endpoint.stream.description,
                                        "source_path": endpoint.stream.source_path,
                                        "events": [
                                            {
                                                "kind": event.kind,
                                                "class_ref": event.class_ref,
                                                "description": event.description,
                                                "source_path": event.source_path,
                                            }
                                            for event in endpoint.stream.events
                                        ],
                                    }
                                    if endpoint.stream is not None
                                    else None
                                ),
                                "fulfillment_bindings": [
                                    {
                                        "name": binding.name,
                                        "graph_target": binding.graph_target,
                                        "graph_capability_function_name": binding.graph_capability_function_name,
                                        "graph_function_python_ref": binding.graph_function_python_ref,
                                        "graph_function_runtime_target": binding.graph_function_runtime_target,
                                        "call_target_kind": binding.call_target_kind,
                                        "exact_output_field_name": binding.exact_output_field_name,
                                        "source_path": binding.source_path,
                                    }
                                    for binding in endpoint.fulfillment_bindings
                                ],
                            }
                            for endpoint in capability.endpoints
                        ],
                    }
                    for capability in api.capabilities
                ],
            }
            for api in plan.apis
        ],
    }


__all__ = [
    "ApiPublicPackagePlanArtifact",
    "ApiServiceProtocolPlanArtifact",
    "build_api_public_package_lowering_handoff",
    "build_api_service_protocol_lowering_handoff",
    "emit_api_public_package_plan_artifact",
    "emit_api_service_protocol_plan_artifact",
]
