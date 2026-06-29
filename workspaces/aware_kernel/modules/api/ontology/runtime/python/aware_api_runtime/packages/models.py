from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.materialization.schemas import (
    MaterializationConfig,
    MaterializationSource,
)


@dataclass(frozen=True, slots=True)
class ApiProductBackendHandoff:
    materialization_source: MaterializationSource
    aware_package_kind: str
    expected_renderer_profile: str


@dataclass(frozen=True, slots=True)
class ApiPublicPackageRequestPlan:
    class_ref: str
    description: str | None
    source_path: str


@dataclass(frozen=True, slots=True)
class ApiPublicPackageResponsePlan:
    class_ref: str
    description: str | None
    source_path: str


@dataclass(frozen=True, slots=True)
class ApiPublicPackageStreamEventPlan:
    kind: str
    class_ref: str
    description: str | None
    source_path: str


@dataclass(frozen=True, slots=True)
class ApiPublicPackageStreamPlan:
    stream_mode: str
    description: str | None
    source_path: str
    events: tuple[ApiPublicPackageStreamEventPlan, ...]


@dataclass(frozen=True, slots=True)
class ApiPublicPackageEndpointPlan:
    api_name: str
    capability_name: str
    name: str
    discriminant: str
    description: str | None
    source_path: str
    request: ApiPublicPackageRequestPlan
    response: ApiPublicPackageResponsePlan | None
    stream: ApiPublicPackageStreamPlan | None


@dataclass(frozen=True, slots=True)
class ApiPublicPackageCapabilityPlan:
    api_name: str
    name: str
    description: str | None
    source_path: str
    endpoints: tuple[ApiPublicPackageEndpointPlan, ...]


@dataclass(frozen=True, slots=True)
class ApiPublicPackageApiPlan:
    name: str
    description: str | None
    source_path: str
    capabilities: tuple[ApiPublicPackageCapabilityPlan, ...]


@dataclass(frozen=True, slots=True)
class ApiPublicPackagePlan:
    schema_version: int
    package_name: str
    fqn_prefix: str
    backend_handoff: ApiProductBackendHandoff
    apis: tuple[ApiPublicPackageApiPlan, ...]


@dataclass(frozen=True, slots=True)
class ApiServiceProtocolEndpointFunctionPlan:
    name: str
    graph_target: str
    graph_capability_function_name: str
    graph_function_python_ref: str
    source_path: str
    graph_function_runtime_target: str | None = None
    call_target_kind: str | None = None
    exact_output_field_name: str | None = None


@dataclass(frozen=True, slots=True)
class ApiServiceProtocolEndpointPlan:
    api_name: str
    capability_name: str
    name: str
    endpoint_ref: str
    discriminant: str
    description: str | None
    source_path: str
    request: ApiPublicPackageRequestPlan
    response: ApiPublicPackageResponsePlan | None
    stream: ApiPublicPackageStreamPlan | None
    fulfillment_bindings: tuple[ApiServiceProtocolEndpointFunctionPlan, ...]


@dataclass(frozen=True, slots=True)
class ApiServiceProtocolCapabilityPlan:
    api_name: str
    name: str
    description: str | None
    source_path: str
    endpoints: tuple[ApiServiceProtocolEndpointPlan, ...]


@dataclass(frozen=True, slots=True)
class ApiServiceProtocolApiPlan:
    name: str
    description: str | None
    source_path: str
    capabilities: tuple[ApiServiceProtocolCapabilityPlan, ...]


@dataclass(frozen=True, slots=True)
class ApiServiceProtocolPlan:
    schema_version: int
    package_name: str
    fqn_prefix: str
    backend_handoff: ApiProductBackendHandoff
    apis: tuple[ApiServiceProtocolApiPlan, ...]


@dataclass(frozen=True, slots=True)
class ApiPublicPackagePlanArtifact:
    path: Path
    relpath: str
    hash_sha256: str


@dataclass(frozen=True, slots=True)
class ApiProductRuntimeArtifactRef:
    kind: str
    relpath: str
    hash_sha256: str


@dataclass(frozen=True, slots=True)
class ApiPublicPackageLoweringHandoff:
    schema_version: int
    package_name: str
    fqn_prefix: str
    backend_handoff: ApiProductBackendHandoff
    runtime_artifacts: tuple[ApiProductRuntimeArtifactRef, ...]


@dataclass(frozen=True, slots=True)
class ApiPublicPackageRenderTarget:
    target_language: CodeLanguage
    source_aware_toml_path: Path
    target_output_dir: Path
    package_root: Path
    package_name: str
    repo_root: Path | None = None
    dependency_repo_roots: tuple[Path, ...] = ()
    path_dependencies: tuple[tuple[str, Path], ...] = ()
    import_root: str | None = None
    version: str = "0.1.0"
    description: str | None = None
    renderer_kind: str | None = None
    manifest_path: Path | None = None


@dataclass(frozen=True, slots=True)
class ApiPublicPackageRenderJob:
    schema_version: int
    package_name: str
    fqn_prefix: str
    backend_handoff: ApiProductBackendHandoff
    target: ApiPublicPackageRenderTarget
    runtime_artifacts: tuple[ApiProductRuntimeArtifactRef, ...]
    materialization_config: MaterializationConfig


@dataclass(frozen=True, slots=True)
class ApiServiceProtocolPlanArtifact:
    path: Path
    relpath: str
    hash_sha256: str


@dataclass(frozen=True, slots=True)
class ApiServiceProtocolLoweringHandoff:
    schema_version: int
    package_name: str
    fqn_prefix: str
    backend_handoff: ApiProductBackendHandoff
    runtime_artifacts: tuple[ApiProductRuntimeArtifactRef, ...]


@dataclass(frozen=True, slots=True)
class ApiServiceProtocolRenderTarget:
    target_language: CodeLanguage
    source_aware_toml_path: Path
    target_output_dir: Path
    package_root: Path
    package_name: str
    import_root: str | None = None
    version: str = "0.1.0"
    description: str | None = None
    renderer_kind: str | None = None
    manifest_path: Path | None = None


@dataclass(frozen=True, slots=True)
class ApiServiceProtocolRenderJob:
    schema_version: int
    package_name: str
    fqn_prefix: str
    backend_handoff: ApiProductBackendHandoff
    target: ApiServiceProtocolRenderTarget
    runtime_artifacts: tuple[ApiProductRuntimeArtifactRef, ...]
    materialization_config: MaterializationConfig


__all__ = [
    "ApiProductBackendHandoff",
    "ApiProductRuntimeArtifactRef",
    "ApiPublicPackageApiPlan",
    "ApiPublicPackageCapabilityPlan",
    "ApiPublicPackageEndpointPlan",
    "ApiPublicPackageLoweringHandoff",
    "ApiPublicPackagePlan",
    "ApiPublicPackagePlanArtifact",
    "ApiPublicPackageRenderJob",
    "ApiPublicPackageRenderTarget",
    "ApiPublicPackageRequestPlan",
    "ApiPublicPackageResponsePlan",
    "ApiServiceProtocolLoweringHandoff",
    "ApiServiceProtocolApiPlan",
    "ApiServiceProtocolCapabilityPlan",
    "ApiServiceProtocolEndpointFunctionPlan",
    "ApiServiceProtocolEndpointPlan",
    "ApiServiceProtocolPlan",
    "ApiServiceProtocolPlanArtifact",
    "ApiServiceProtocolRenderJob",
    "ApiServiceProtocolRenderTarget",
    "ApiPublicPackageStreamEventPlan",
    "ApiPublicPackageStreamPlan",
]
