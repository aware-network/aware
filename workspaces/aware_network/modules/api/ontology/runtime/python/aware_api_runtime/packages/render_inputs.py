from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from aware_meta.materialization.schemas import (
    MaterializationProfileInputFormat,
    MaterializationProfileInputRef,
)

from .models import (
    ApiProductRuntimeArtifactRef,
    ApiPublicPackageRenderJob,
    ApiServiceProtocolRenderJob,
)

_API_PUBLIC_PACKAGE_PROFILE_INPUT_KEYS = (
    "api.interface_spec",
    "api.invocation_manifest",
    "api.public_package_plan",
)
_API_PUBLIC_PACKAGE_OPTIONAL_PROFILE_INPUT_KEYS = ("api.external_python_type_index",)
_API_SERVICE_PROTOCOL_PROFILE_INPUT_KEYS = (
    "api.interface_spec",
    "api.invocation_manifest",
    "api.public_package_plan",
    "api.service_protocol_plan",
    "api.external_python_type_index",
)


def build_api_public_package_render_inputs(
    *,
    render_job: ApiPublicPackageRenderJob,
) -> ApiPublicPackageRenderJob:
    if render_job.materialization_config.profile_input_refs:
        raise ValueError(
            "public API package render job already has profile_input_refs; "
            + "render-input lowering is not idempotent."
        )

    artifact_refs = _resolve_profile_input_artifacts(
        runtime_artifacts=render_job.runtime_artifacts
    )
    materialization_config = render_job.materialization_config.model_copy(
        update={
            "profile_input_refs": [
                MaterializationProfileInputRef(
                    key=artifact.kind,
                    path=Path(artifact.relpath),
                    format=MaterializationProfileInputFormat.json,
                    required=True,
                )
                for artifact in artifact_refs
            ]
        }
    )
    return replace(render_job, materialization_config=materialization_config)


def build_api_service_protocol_render_inputs(
    *,
    render_job: ApiServiceProtocolRenderJob,
) -> ApiServiceProtocolRenderJob:
    if render_job.materialization_config.profile_input_refs:
        raise ValueError(
            "service protocol package render job already has profile_input_refs; "
            + "render-input lowering is not idempotent."
        )

    artifact_refs = _resolve_service_protocol_profile_input_artifacts(
        runtime_artifacts=render_job.runtime_artifacts
    )
    materialization_config = render_job.materialization_config.model_copy(
        update={
            "profile_input_refs": [
                MaterializationProfileInputRef(
                    key=artifact.kind,
                    path=Path(artifact.relpath),
                    format=MaterializationProfileInputFormat.json,
                    required=True,
                )
                for artifact in artifact_refs
            ]
        }
    )
    return replace(render_job, materialization_config=materialization_config)


def _resolve_profile_input_artifacts(
    *,
    runtime_artifacts: tuple[ApiProductRuntimeArtifactRef, ...],
) -> tuple[ApiProductRuntimeArtifactRef, ...]:
    artifacts_by_kind: dict[str, ApiProductRuntimeArtifactRef] = {}
    for artifact in runtime_artifacts:
        if artifact.kind in artifacts_by_kind:
            raise ValueError(
                f"Duplicate public API package runtime artifact kind: {artifact.kind!r}"
            )
        artifacts_by_kind[artifact.kind] = artifact

    missing = [
        key
        for key in _API_PUBLIC_PACKAGE_PROFILE_INPUT_KEYS
        if key not in artifacts_by_kind
    ]
    if missing:
        raise ValueError(
            "Missing public API package runtime artifacts required for render-input lowering: "
            + ", ".join(repr(key) for key in missing)
        )

    allowed_keys = (
        *_API_PUBLIC_PACKAGE_PROFILE_INPUT_KEYS,
        *_API_PUBLIC_PACKAGE_OPTIONAL_PROFILE_INPUT_KEYS,
    )
    unexpected = sorted(key for key in artifacts_by_kind if key not in allowed_keys)
    if unexpected:
        raise ValueError(
            "Unexpected public API package runtime artifacts for render-input lowering: "
            + ", ".join(repr(key) for key in unexpected)
        )

    return tuple(
        artifacts_by_kind[key] for key in allowed_keys if key in artifacts_by_kind
    )


def _resolve_service_protocol_profile_input_artifacts(
    *,
    runtime_artifacts: tuple[ApiProductRuntimeArtifactRef, ...],
) -> tuple[ApiProductRuntimeArtifactRef, ...]:
    artifacts_by_kind: dict[str, ApiProductRuntimeArtifactRef] = {}
    for artifact in runtime_artifacts:
        if artifact.kind in artifacts_by_kind:
            raise ValueError(
                f"Duplicate service protocol package runtime artifact kind: {artifact.kind!r}"
            )
        artifacts_by_kind[artifact.kind] = artifact

    missing = [
        key
        for key in _API_SERVICE_PROTOCOL_PROFILE_INPUT_KEYS
        if key not in artifacts_by_kind
    ]
    if missing:
        raise ValueError(
            "Missing service protocol package runtime artifacts required for render-input lowering: "
            + ", ".join(repr(key) for key in missing)
        )

    unexpected = sorted(
        key
        for key in artifacts_by_kind
        if key not in _API_SERVICE_PROTOCOL_PROFILE_INPUT_KEYS
    )
    if unexpected:
        raise ValueError(
            "Unexpected service protocol package runtime artifacts for render-input lowering: "
            + ", ".join(repr(key) for key in unexpected)
        )

    return tuple(
        artifacts_by_kind[key] for key in _API_SERVICE_PROTOCOL_PROFILE_INPUT_KEYS
    )


__all__ = [
    "build_api_public_package_render_inputs",
    "build_api_service_protocol_render_inputs",
]
