from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonArray

if TYPE_CHECKING:
    from aware_code_ontology.package.code_package import CodePackage
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit
    from aware_service_ontology.service.service_config import ServiceConfig
    from aware_service_ontology.service.service_package_implementation_package import (
        ServicePackageImplementationPackage,
    )
    from aware_service_ontology.service.service_package_object_config_graph_package import (
        ServicePackageObjectConfigGraphPackage,
    )
    from aware_service_ontology.service.service_package_ontology_package import ServicePackageOntologyPackage
    from aware_service_ontology.service.service_package_provided_api_package import ServicePackageProvidedApiPackage
    from aware_service_ontology.service.service_package_required_api_package import ServicePackageRequiredApiPackage


class ServicePackage(ORMModel):
    # Relationships
    source_code_package: CodePackage | None = Field(default=None)
    implementation_packages: list[ServicePackageImplementationPackage] = Field(default_factory=list)
    ontology_packages: list[ServicePackageOntologyPackage] = Field(default_factory=list)
    object_config_graph_packages: list[ServicePackageObjectConfigGraphPackage] = Field(default_factory=list)
    provided_api_packages: list[ServicePackageProvidedApiPackage] = Field(default_factory=list)
    required_api_packages: list[ServicePackageRequiredApiPackage] = Field(default_factory=list)
    service_config: ServiceConfig | None = Field(default=None)
    service_config_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Attributes
    activation_mode: str = Field(default="materialize_and_load_committed")
    aware_service_version: int = Field(default=1)
    compilation_mode: str = Field(default="raw_xor")
    dependencies: JsonArray = Field(default_factory=JsonArray)
    description: str | None = Field(default=None)
    exclude_paths: JsonArray = Field(default_factory=JsonArray)
    force_fresh_scan: bool = Field(default=True)
    fqn_prefix: str | None = Field(default=None)
    include_paths: JsonArray = Field(default_factory=JsonArray)
    manifest_relative_path: str | None = Field(default=None)
    materialize_on_start: bool = Field(default=True)
    name: str
    package_root: str = Field(default=".")
    service_surface: str = Field(default="service")
    sources_root: str = Field(default="services")
    title: str | None = Field(default=None)
    version_number: int = Field(default=1)

    # Foreign Keys
    source_code_package_id: UUID | None = Field(
        default=None, description="Foreign key for ServicePackage.source_code_package"
    )
    service_config_id: UUID = Field(description="Foreign key for ServicePackage.service_config")
    service_config_object_instance_graph_commit_id: UUID | None = Field(
        default=None, description="Foreign key for ServicePackage.service_config_object_instance_graph_commit"
    )

    @classmethod
    async def build(
        cls,
        name: str,
        service_config_id: UUID,
        service_config_object_instance_graph_commit_id: UUID | None = None,
        source_code_package_id: UUID | None = None,
        fqn_prefix: str | None = None,
        version_number: int = 1,
        title: str | None = None,
        description: str | None = None,
        aware_service_version: int = 1,
        manifest_relative_path: str | None = None,
        package_root: str = ".",
        sources_root: str = "services",
        include_paths: JsonArray = [],
        exclude_paths: JsonArray = [],
        force_fresh_scan: bool = True,
        compilation_mode: str = "raw_xor",
        service_surface: str = "service",
        activation_mode: str = "materialize_and_load_committed",
        materialize_on_start: bool = True,
        dependencies: JsonArray = [],
    ) -> ServicePackage:
        """
        Create the canonical Service-owned package root over an existing `ServiceConfig`.

        Contract:
        - Identity is keyed by Service package `name`.
        - `ServicePackage` is the package/public root over an existing canonical `ServiceConfig`.
        - `service_config_id` must point at the canonical ServiceConfig stable id for this package root.
        - `service_config_object_instance_graph_commit_id` pins the historical ObjectInstanceGraphCommit
          for the semantic ServiceConfig root so package consumers can replay exact service truth without
          resolving branch head.
        - `source_code_package_id` is the explicit raw-source provenance link for this semantic leaf
        package.
        - Manifest/build/host/dependency attributes mirror `aware.service.toml` so committed package truth
        can
          drive Workspace and Service runtime resolution without reopening authoring TOML.
        - Workspace will later mount `ServicePackage`, not raw `ServiceConfig`.
        """

        payload = {
            "name": name,
            "service_config_id": service_config_id,
            "service_config_object_instance_graph_commit_id": service_config_object_instance_graph_commit_id,
            "source_code_package_id": source_code_package_id,
            "fqn_prefix": fqn_prefix,
            "version_number": version_number,
            "title": title,
            "description": description,
            "aware_service_version": aware_service_version,
            "manifest_relative_path": manifest_relative_path,
            "package_root": package_root,
            "sources_root": sources_root,
            "include_paths": include_paths,
            "exclude_paths": exclude_paths,
            "force_fresh_scan": force_fresh_scan,
            "compilation_mode": compilation_mode,
            "service_surface": service_surface,
            "activation_mode": activation_mode,
            "materialize_on_start": materialize_on_start,
            "dependencies": dependencies,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServicePackage):
            return value
        return ServicePackage.validate_invocation_value(value)

    async def sync_manifest_truth(
        self,
        service_config_object_instance_graph_commit_id: UUID | None = None,
        source_code_package_id: UUID | None = None,
        fqn_prefix: str | None = None,
        version_number: int = 1,
        title: str | None = None,
        description: str | None = None,
        aware_service_version: int = 1,
        manifest_relative_path: str | None = None,
        package_root: str = ".",
        sources_root: str = "services",
        include_paths: JsonArray = [],
        exclude_paths: JsonArray = [],
        force_fresh_scan: bool = True,
        compilation_mode: str = "raw_xor",
        service_surface: str = "service",
        activation_mode: str = "materialize_and_load_committed",
        materialize_on_start: bool = True,
        dependencies: JsonArray = [],
    ) -> ServicePackage:
        """
        Sync mutable manifest/build/host/dependency truth onto an existing ServicePackage root.

        This keeps `build` create-only for empty package lanes while allowing committed package truth to
        follow the latest parsed `aware.service.toml` snapshot and pinned semantic ServiceConfig commit.
        """

        payload = {
            "service_config_object_instance_graph_commit_id": service_config_object_instance_graph_commit_id,
            "source_code_package_id": source_code_package_id,
            "fqn_prefix": fqn_prefix,
            "version_number": version_number,
            "title": title,
            "description": description,
            "aware_service_version": aware_service_version,
            "manifest_relative_path": manifest_relative_path,
            "package_root": package_root,
            "sources_root": sources_root,
            "include_paths": include_paths,
            "exclude_paths": exclude_paths,
            "force_fresh_scan": force_fresh_scan,
            "compilation_mode": compilation_mode,
            "service_surface": service_surface,
            "activation_mode": activation_mode,
            "materialize_on_start": materialize_on_start,
            "dependencies": dependencies,
        }
        result = await invoke_instance(orm_model=self, function_name="sync_manifest_truth", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServicePackage):
            return value
        return ServicePackage.validate_invocation_value(value)

    async def attach_provided_api_package(
        self,
        api_package_id: UUID,
        service_protocol_package_id: UUID,
        service_protocol_plan_hash_sha256: str,
        api_package_object_instance_graph_commit_id: UUID,
        description: str | None = None,
    ) -> ServicePackageProvidedApiPackage:
        """
        Attach one API package this ServicePackage provides.

        Contract:
        - This is the package-level provider rail for Node/service dependency resolution.
        - It declares which API packages this ServicePackage can fulfill through ServiceHost.
        - Provider truth must stay compatible with config-level `ServiceConfig -> ServiceConfigApi`
          fulfillment; it does not describe outgoing invocation.
        """

        payload = {
            "api_package_id": api_package_id,
            "service_protocol_package_id": service_protocol_package_id,
            "service_protocol_plan_hash_sha256": service_protocol_plan_hash_sha256,
            "api_package_object_instance_graph_commit_id": api_package_object_instance_graph_commit_id,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_provided_api_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_service_ontology.service.service_package_provided_api_package import ServicePackageProvidedApiPackage

        if isinstance(value, ServicePackageProvidedApiPackage):
            return value
        return ServicePackageProvidedApiPackage.validate_invocation_value(value)

    async def attach_object_config_graph_package(
        self,
        object_config_graph_package_id: UUID,
        manifest_relative_path: str,
        role: str = "local_state",
        package_kind: str = "state",
        object_config_graph_package_object_instance_graph_commit_id: UUID | None = None,
        expected_hash_sha256: str | None = None,
        description: str | None = None,
    ) -> ServicePackageObjectConfigGraphPackage:
        """
        Attach one Service-owned ObjectConfigGraphPackage to this ServicePackage.

        Contract:
        - This is service ownership truth, not a service dependency.
        - The child package is declared by `aware.service.toml` and materialized through the
          canonical ObjectConfigGraphPackage rail.
        - ServiceHost and WorkspaceRevision consumers can use the optional OIG commit pin to replay
          exact service-local DB/schema truth without reopening local manifests.
        """

        payload = {
            "object_config_graph_package_id": object_config_graph_package_id,
            "manifest_relative_path": manifest_relative_path,
            "role": role,
            "package_kind": package_kind,
            "object_config_graph_package_object_instance_graph_commit_id": object_config_graph_package_object_instance_graph_commit_id,
            "expected_hash_sha256": expected_hash_sha256,
            "description": description,
        }
        result = await invoke_instance(
            orm_model=self, function_name="attach_object_config_graph_package", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_service_ontology.service.service_package_object_config_graph_package import (
            ServicePackageObjectConfigGraphPackage,
        )

        if isinstance(value, ServicePackageObjectConfigGraphPackage):
            return value
        return ServicePackageObjectConfigGraphPackage.validate_invocation_value(value)

    async def attach_ontology_package(
        self,
        ontology_package_id: UUID,
        package_name: str,
        fqn_prefix: str,
        role: str = "replica",
        requirement_mode: str = "required",
        ontology_package_object_instance_graph_commit_id: UUID | None = None,
        expected_hash_sha256: str | None = None,
        description: str | None = None,
    ) -> ServicePackageOntologyPackage:
        """
        Attach one ontology package this ServicePackage requires as a replica.

        Contract:
        - This is package-level ontology replica requirement truth.
        - It declares which OntologyPackage must be available to ServiceHost as a
          read-only Service-owned ontology replica before required handler dispatch.
        - Required ontology truth must not imply this ServicePackage owns or mutates
          the ontology package. Ontology remains the write/DB authority.
        """

        payload = {
            "ontology_package_id": ontology_package_id,
            "package_name": package_name,
            "fqn_prefix": fqn_prefix,
            "role": role,
            "requirement_mode": requirement_mode,
            "ontology_package_object_instance_graph_commit_id": ontology_package_object_instance_graph_commit_id,
            "expected_hash_sha256": expected_hash_sha256,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_ontology_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_service_ontology.service.service_package_ontology_package import ServicePackageOntologyPackage

        if isinstance(value, ServicePackageOntologyPackage):
            return value
        return ServicePackageOntologyPackage.validate_invocation_value(value)

    async def attach_implementation_package(
        self,
        code_package_id: UUID,
        package_name: str,
        language: CodeLanguage,
        import_root: str,
        manifest_relative_path: str,
        package_root: str = ".",
        entrypoint: str | None = None,
        role: str = "service_bindings",
        include_paths: JsonArray = [],
        exclude_paths: JsonArray = [],
    ) -> ServicePackageImplementationPackage:
        """
        Attach one concrete implementation package owned by this ServicePackage.

        Contract:
        - The ServicePackage owns explicit language implementation packages as semantic package truth.
        - ServiceHost must resolve importable implementation code from this bridge, never from
          `fqn_prefix` guesses or workspace layout heuristics.
        - `code_package_id` points at the canonical CodePackage for the implementation package.
        - `package_root` and `manifest_relative_path` are workspace-revision relative contract payload.
        """

        payload = {
            "code_package_id": code_package_id,
            "package_name": package_name,
            "language": language,
            "import_root": import_root,
            "manifest_relative_path": manifest_relative_path,
            "package_root": package_root,
            "entrypoint": entrypoint,
            "role": role,
            "include_paths": include_paths,
            "exclude_paths": exclude_paths,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_implementation_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_service_ontology.service.service_package_implementation_package import (
            ServicePackageImplementationPackage,
        )

        if isinstance(value, ServicePackageImplementationPackage):
            return value
        return ServicePackageImplementationPackage.validate_invocation_value(value)

    async def attach_required_api_package(
        self, api_package_id: UUID, description: str | None = None
    ) -> ServicePackageRequiredApiPackage:
        """
        Attach one API package this ServicePackage requires for outgoing invocation.

        Contract:
        - This is the package-level consumer rail for generated SDK/API clients.
        - It declares which API packages this ServicePackage may invoke through Node service routing.
        - Required API truth must not imply this ServicePackage hosts or fulfills the API.
        """

        payload = {"api_package_id": api_package_id, "description": description}
        result = await invoke_instance(orm_model=self, function_name="attach_required_api_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_service_ontology.service.service_package_required_api_package import ServicePackageRequiredApiPackage

        if isinstance(value, ServicePackageRequiredApiPackage):
            return value
        return ServicePackageRequiredApiPackage.validate_invocation_value(value)


class ServicePackageBuildInput(BaseModel):
    name: str
    service_config_id: UUID
    service_config_object_instance_graph_commit_id: UUID | None = Field(default=None)
    source_code_package_id: UUID | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    version_number: int = Field(default=1)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    aware_service_version: int = Field(default=1)
    manifest_relative_path: str | None = Field(default=None)
    package_root: str = Field(default=".")
    sources_root: str = Field(default="services")
    include_paths: JsonArray = Field(default_factory=JsonArray)
    exclude_paths: JsonArray = Field(default_factory=JsonArray)
    force_fresh_scan: bool = Field(default=True)
    compilation_mode: str = Field(default="raw_xor")
    service_surface: str = Field(default="service")
    activation_mode: str = Field(default="materialize_and_load_committed")
    materialize_on_start: bool = Field(default=True)
    dependencies: JsonArray = Field(default_factory=JsonArray)


class ServicePackageBuildOutput(BaseModel):
    value: ServicePackage


class ServicePackageSyncManifestTruthInput(BaseModel):
    service_config_object_instance_graph_commit_id: UUID | None = Field(default=None)
    source_code_package_id: UUID | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    version_number: int = Field(default=1)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    aware_service_version: int = Field(default=1)
    manifest_relative_path: str | None = Field(default=None)
    package_root: str = Field(default=".")
    sources_root: str = Field(default="services")
    include_paths: JsonArray = Field(default_factory=JsonArray)
    exclude_paths: JsonArray = Field(default_factory=JsonArray)
    force_fresh_scan: bool = Field(default=True)
    compilation_mode: str = Field(default="raw_xor")
    service_surface: str = Field(default="service")
    activation_mode: str = Field(default="materialize_and_load_committed")
    materialize_on_start: bool = Field(default=True)
    dependencies: JsonArray = Field(default_factory=JsonArray)


class ServicePackageSyncManifestTruthOutput(BaseModel):
    value: ServicePackage


class ServicePackageAttachProvidedApiPackageInput(BaseModel):
    api_package_id: UUID
    service_protocol_package_id: UUID
    service_protocol_plan_hash_sha256: str
    api_package_object_instance_graph_commit_id: UUID
    description: str | None = Field(default=None)


class ServicePackageAttachProvidedApiPackageOutput(BaseModel):
    value: ServicePackageProvidedApiPackage


class ServicePackageAttachObjectConfigGraphPackageInput(BaseModel):
    object_config_graph_package_id: UUID
    manifest_relative_path: str
    role: str = Field(default="local_state")
    package_kind: str = Field(default="state")
    object_config_graph_package_object_instance_graph_commit_id: UUID | None = Field(default=None)
    expected_hash_sha256: str | None = Field(default=None)
    description: str | None = Field(default=None)


class ServicePackageAttachObjectConfigGraphPackageOutput(BaseModel):
    value: ServicePackageObjectConfigGraphPackage


class ServicePackageAttachOntologyPackageInput(BaseModel):
    ontology_package_id: UUID
    package_name: str
    fqn_prefix: str
    role: str = Field(default="replica")
    requirement_mode: str = Field(default="required")
    ontology_package_object_instance_graph_commit_id: UUID | None = Field(default=None)
    expected_hash_sha256: str | None = Field(default=None)
    description: str | None = Field(default=None)


class ServicePackageAttachOntologyPackageOutput(BaseModel):
    value: ServicePackageOntologyPackage


class ServicePackageAttachImplementationPackageInput(BaseModel):
    code_package_id: UUID
    package_name: str
    language: CodeLanguage
    import_root: str
    manifest_relative_path: str
    package_root: str = Field(default=".")
    entrypoint: str | None = Field(default=None)
    role: str = Field(default="service_bindings")
    include_paths: JsonArray = Field(default_factory=JsonArray)
    exclude_paths: JsonArray = Field(default_factory=JsonArray)


class ServicePackageAttachImplementationPackageOutput(BaseModel):
    value: ServicePackageImplementationPackage


class ServicePackageAttachRequiredApiPackageInput(BaseModel):
    api_package_id: UUID
    description: str | None = Field(default=None)


class ServicePackageAttachRequiredApiPackageOutput(BaseModel):
    value: ServicePackageRequiredApiPackage


FUNCTIONS = {
    "ServicePackage": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create the canonical Service-owned package root over an existing `ServiceConfig`.\n\nContract:\n- Identity is keyed by Service package `name`.\n- `ServicePackage` is the package/public root over an existing canonical `ServiceConfig`.\n- `service_config_id` must point at the canonical ServiceConfig stable id for this package root.\n- `service_config_object_instance_graph_commit_id` pins the historical ObjectInstanceGraphCommit\n  for the semantic ServiceConfig root so package consumers can replay exact service truth without\n  resolving branch head.\n- `source_code_package_id` is the explicit raw-source provenance link for this semantic leaf package.\n- Manifest/build/host/dependency attributes mirror `aware.service.toml` so committed package truth can\n  drive Workspace and Service runtime resolution without reopening authoring TOML.\n- Workspace will later mount `ServicePackage`, not raw `ServiceConfig`.",
                "is_constructor": True,
            },
            "input": ServicePackageBuildInput,
            "output": ServicePackageBuildOutput,
        },
        "sync_manifest_truth": {
            "canonical": {
                "name": "sync_manifest_truth",
                "description": "Sync mutable manifest/build/host/dependency truth onto an existing ServicePackage root.\n\nThis keeps `build` create-only for empty package lanes while allowing committed package truth to\nfollow the latest parsed `aware.service.toml` snapshot and pinned semantic ServiceConfig commit.",
                "is_constructor": False,
            },
            "input": ServicePackageSyncManifestTruthInput,
            "output": ServicePackageSyncManifestTruthOutput,
        },
        "attach_provided_api_package": {
            "canonical": {
                "name": "attach_provided_api_package",
                "description": "Attach one API package this ServicePackage provides.\n\nContract:\n- This is the package-level provider rail for Node/service dependency resolution.\n- It declares which API packages this ServicePackage can fulfill through ServiceHost.\n- Provider truth must stay compatible with config-level `ServiceConfig -> ServiceConfigApi`\n  fulfillment; it does not describe outgoing invocation.",
                "is_constructor": False,
            },
            "input": ServicePackageAttachProvidedApiPackageInput,
            "output": ServicePackageAttachProvidedApiPackageOutput,
        },
        "attach_object_config_graph_package": {
            "canonical": {
                "name": "attach_object_config_graph_package",
                "description": "Attach one Service-owned ObjectConfigGraphPackage to this ServicePackage.\n\nContract:\n- This is service ownership truth, not a service dependency.\n- The child package is declared by `aware.service.toml` and materialized through the\n  canonical ObjectConfigGraphPackage rail.\n- ServiceHost and WorkspaceRevision consumers can use the optional OIG commit pin to replay\n  exact service-local DB/schema truth without reopening local manifests.",
                "is_constructor": False,
            },
            "input": ServicePackageAttachObjectConfigGraphPackageInput,
            "output": ServicePackageAttachObjectConfigGraphPackageOutput,
        },
        "attach_ontology_package": {
            "canonical": {
                "name": "attach_ontology_package",
                "description": "Attach one ontology package this ServicePackage requires as a replica.\n\nContract:\n- This is package-level ontology replica requirement truth.\n- It declares which OntologyPackage must be available to ServiceHost as a\n  read-only Service-owned ontology replica before required handler dispatch.\n- Required ontology truth must not imply this ServicePackage owns or mutates\n  the ontology package. Ontology remains the write/DB authority.",
                "is_constructor": False,
            },
            "input": ServicePackageAttachOntologyPackageInput,
            "output": ServicePackageAttachOntologyPackageOutput,
        },
        "attach_implementation_package": {
            "canonical": {
                "name": "attach_implementation_package",
                "description": "Attach one concrete implementation package owned by this ServicePackage.\n\nContract:\n- The ServicePackage owns explicit language implementation packages as semantic package truth.\n- ServiceHost must resolve importable implementation code from this bridge, never from\n  `fqn_prefix` guesses or workspace layout heuristics.\n- `code_package_id` points at the canonical CodePackage for the implementation package.\n- `package_root` and `manifest_relative_path` are workspace-revision relative contract payload.",
                "is_constructor": False,
            },
            "input": ServicePackageAttachImplementationPackageInput,
            "output": ServicePackageAttachImplementationPackageOutput,
        },
        "attach_required_api_package": {
            "canonical": {
                "name": "attach_required_api_package",
                "description": "Attach one API package this ServicePackage requires for outgoing invocation.\n\nContract:\n- This is the package-level consumer rail for generated SDK/API clients.\n- It declares which API packages this ServicePackage may invoke through Node service routing.\n- Required API truth must not imply this ServicePackage hosts or fulfills the API.",
                "is_constructor": False,
            },
            "input": ServicePackageAttachRequiredApiPackageInput,
            "output": ServicePackageAttachRequiredApiPackageOutput,
        },
    },
}

__all__ = [
    "ServicePackage",
    "ServicePackageBuildInput",
    "ServicePackageBuildOutput",
    "ServicePackageSyncManifestTruthInput",
    "ServicePackageSyncManifestTruthOutput",
    "ServicePackageAttachProvidedApiPackageInput",
    "ServicePackageAttachProvidedApiPackageOutput",
    "ServicePackageAttachObjectConfigGraphPackageInput",
    "ServicePackageAttachObjectConfigGraphPackageOutput",
    "ServicePackageAttachOntologyPackageInput",
    "ServicePackageAttachOntologyPackageOutput",
    "ServicePackageAttachImplementationPackageInput",
    "ServicePackageAttachImplementationPackageOutput",
    "ServicePackageAttachRequiredApiPackageInput",
    "ServicePackageAttachRequiredApiPackageOutput",
    "FUNCTIONS",
]
