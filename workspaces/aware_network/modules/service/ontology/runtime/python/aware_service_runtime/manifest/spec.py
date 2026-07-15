from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AwareServiceCompilationMode(str, Enum):
    raw_xor = "raw_xor"
    service_ontology = "service_ontology"


class AwareServiceDependencyKind(str, Enum):
    package = "package"
    api_service_protocol = "api_service_protocol"
    api_invocation = "api_invocation"


class AwareServiceHostActivationMode(str, Enum):
    materialize_and_load_committed = "materialize_and_load_committed"


class AwareServiceImplementationLanguage(str, Enum):
    python = "python"


class AwareServiceImplementationRole(str, Enum):
    service_bindings = "service_bindings"


class AwareServiceRuntimeRequirementKind(str, Enum):
    secret = "secret"
    config = "config"


class AwareServiceRuntimeToolchainKind(str, Enum):
    cli = "cli"


@dataclass(frozen=True, slots=True)
class AwareServiceTomlPackageSpec:
    package_name: str
    fqn_prefix: str
    version_number: int = 1
    title: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class AwareServiceTomlBuildSpec:
    sources_dir: str = "services"
    include_paths: list[str] = field(default_factory=lambda: ["**/*.aware"])
    exclude_paths: list[str] = field(default_factory=list)
    force_fresh_scan: bool = True
    compilation_mode: AwareServiceCompilationMode = AwareServiceCompilationMode.raw_xor


@dataclass(frozen=True, slots=True)
class AwareServiceTomlImplementationPackageSpec:
    package_name: str
    language: AwareServiceImplementationLanguage
    import_root: str
    manifest_path: str
    package_root: str = "."
    entrypoint: str | None = None
    role: AwareServiceImplementationRole = (
        AwareServiceImplementationRole.service_bindings
    )
    include_paths: list[str] = field(default_factory=list)
    exclude_paths: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class AwareServiceTomlImplementationSpec:
    packages: list[AwareServiceTomlImplementationPackageSpec] = field(
        default_factory=list
    )


@dataclass(frozen=True, slots=True)
class AwareServiceTomlApiProviderSetSpec:
    key: str
    title: str | None = None
    description: str | None = None
    membership_key: str | None = None


@dataclass(frozen=True, slots=True)
class AwareServiceTomlRouteAuthoritySelectorSpec:
    provider_set_id: str | None = None
    workspace_revision_id: str | None = None
    workspace_deployment_revision_id: str | None = None
    workspace_deployment_channel: str | None = None
    workspace_deployment_artifact_key: str | None = None

    @property
    def is_empty(self) -> bool:
        return not any(
            (
                self.provider_set_id,
                self.workspace_revision_id,
                self.workspace_deployment_revision_id,
                self.workspace_deployment_channel,
                self.workspace_deployment_artifact_key,
            )
        )

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {}
        if self.provider_set_id is not None:
            payload["provider_set_id"] = self.provider_set_id
        if self.workspace_revision_id is not None:
            payload["workspace_revision_id"] = self.workspace_revision_id
        if self.workspace_deployment_revision_id is not None:
            payload["workspace_deployment_revision_id"] = (
                self.workspace_deployment_revision_id
            )
        if self.workspace_deployment_channel is not None:
            payload["workspace_deployment_channel"] = self.workspace_deployment_channel
        if self.workspace_deployment_artifact_key is not None:
            payload["workspace_deployment_artifact_key"] = (
                self.workspace_deployment_artifact_key
            )
        return payload


@dataclass(frozen=True, slots=True)
class AwareServiceTomlDependencySpec:
    package_name: str
    version_number: int | None = None
    kind: AwareServiceDependencyKind = AwareServiceDependencyKind.package
    expected_hash_sha256: str | None = None
    route_authority_selector: AwareServiceTomlRouteAuthoritySelectorSpec | None = None


@dataclass(frozen=True, slots=True)
class AwareServiceTomlObjectConfigGraphPackageSpec:
    manifest: str
    role: str = "local_state"
    description: str | None = None
    expected_hash_sha256: str | None = None
    object_instance_graph_commit_id: str | None = None


@dataclass(frozen=True, slots=True)
class AwareServiceTomlOntologyPackageSpec:
    package_name: str
    fqn_prefix: str
    role: str = "replica"
    requirement_mode: str = "required"
    description: str | None = None
    expected_hash_sha256: str | None = None
    object_instance_graph_commit_id: str | None = None


@dataclass(frozen=True, slots=True)
class AwareServiceTomlHostSpec:
    service_surface: str = "service"
    activation_mode: AwareServiceHostActivationMode = (
        AwareServiceHostActivationMode.materialize_and_load_committed
    )
    materialize_on_start: bool = True
    contract: "AwareServiceTomlHostContractSpec" = field(
        default_factory=lambda: AwareServiceTomlHostContractSpec()
    )


@dataclass(frozen=True, slots=True)
class AwareServiceTomlHostContractSpec:
    entrypoint: str | None = None


@dataclass(frozen=True, slots=True)
class AwareServiceTomlRuntimeRequirementSpec:
    name: str
    kind: AwareServiceRuntimeRequirementKind
    required: bool = True
    sensitive: bool = False
    runtime_env: str | None = None
    resolver: str | None = None
    description: str | None = None
    allowed_values: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class AwareServiceTomlRuntimeToolchainSpec:
    name: str
    kind: AwareServiceRuntimeToolchainKind
    required: bool = True
    package: str | None = None
    version: str | None = None
    channel: str | None = None
    executable: str | None = None
    runtime_env: str | None = None
    description: str | None = None
    verify_commands: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class AwareServiceTomlRuntimeSpec:
    secrets_dir_env: str | None = None
    canonical_secrets_dir: str | None = None
    requirements: list[AwareServiceTomlRuntimeRequirementSpec] = field(
        default_factory=list
    )
    toolchains: list[AwareServiceTomlRuntimeToolchainSpec] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class AwareServiceTomlSpec:
    aware_service: int
    service: AwareServiceTomlPackageSpec
    build: AwareServiceTomlBuildSpec
    host: AwareServiceTomlHostSpec
    dependencies: list[AwareServiceTomlDependencySpec]
    object_config_graph_packages: list[AwareServiceTomlObjectConfigGraphPackageSpec] = (
        field(default_factory=list)
    )
    ontology_packages: list[AwareServiceTomlOntologyPackageSpec] = field(
        default_factory=list
    )
    implementation: AwareServiceTomlImplementationSpec = field(
        default_factory=AwareServiceTomlImplementationSpec
    )
    api_provider_sets: list[AwareServiceTomlApiProviderSetSpec] = field(
        default_factory=list
    )
    runtime: AwareServiceTomlRuntimeSpec = field(
        default_factory=AwareServiceTomlRuntimeSpec
    )


__all__ = [
    "AwareServiceCompilationMode",
    "AwareServiceDependencyKind",
    "AwareServiceTomlBuildSpec",
    "AwareServiceTomlApiProviderSetSpec",
    "AwareServiceTomlDependencySpec",
    "AwareServiceTomlHostSpec",
    "AwareServiceTomlHostContractSpec",
    "AwareServiceTomlImplementationPackageSpec",
    "AwareServiceTomlImplementationSpec",
    "AwareServiceTomlObjectConfigGraphPackageSpec",
    "AwareServiceTomlOntologyPackageSpec",
    "AwareServiceTomlPackageSpec",
    "AwareServiceTomlRuntimeRequirementSpec",
    "AwareServiceTomlRuntimeToolchainSpec",
    "AwareServiceTomlRuntimeSpec",
    "AwareServiceTomlRouteAuthoritySelectorSpec",
    "AwareServiceTomlSpec",
    "AwareServiceHostActivationMode",
    "AwareServiceImplementationLanguage",
    "AwareServiceImplementationRole",
    "AwareServiceRuntimeRequirementKind",
    "AwareServiceRuntimeToolchainKind",
]
