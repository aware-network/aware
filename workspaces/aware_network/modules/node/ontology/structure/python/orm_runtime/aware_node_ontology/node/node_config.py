from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_node_ontology.node.node_config_environment_target import NodeConfigEnvironmentTarget
    from aware_node_ontology.node.node_config_interface_target import NodeConfigInterfaceTarget
    from aware_node_ontology.node.node_config_ontology_target import NodeConfigOntologyTarget
    from aware_node_ontology.node.node_config_service_target import NodeConfigServiceTarget


class NodeConfig(ORMModel):
    # Relationships
    environment_targets: list[NodeConfigEnvironmentTarget] = Field(default_factory=list)
    ontology_targets: list[NodeConfigOntologyTarget] = Field(default_factory=list)
    service_targets: list[NodeConfigServiceTarget] = Field(default_factory=list)
    interface_targets: list[NodeConfigInterfaceTarget] = Field(default_factory=list)

    # Attributes
    name: str
    description: str | None = Field(default=None)

    @classmethod
    async def build(cls, name: str, description: str | None = None) -> NodeConfig:
        """
        Create the canonical Node-owned desired hosted-composition root.

        Contract:
        - Identity is keyed by semantic Node package/config `name`.
        - `NodeConfig` remains desired-state truth only; it does not point at live `NetworkNode`
          runtime state.
        - Hosted composition is attached through contained target objects keyed by stable semantic
          names rather than raw relationship-id primitives.
        """

        payload = {"name": name, "description": description}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, NodeConfig):
            return value
        return NodeConfig.validate_invocation_value(value)

    async def attach_environment_target(self, environment_handle: str) -> NodeConfigEnvironmentTarget:
        """
        Attach one canonical Environment target by stable environment handle.

        Contract:
        - Parent `NodeConfig` scope is injected by propagation.
        - Target identity is resolved from `environment_handle`.
        - Environment profile package mounts are installed separately by explicit
          Node environment profile declarations.
        """

        payload = {"environment_handle": environment_handle}
        result = await invoke_instance(orm_model=self, function_name="attach_environment_target", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_node_ontology.node.node_config_environment_target import NodeConfigEnvironmentTarget

        if isinstance(value, NodeConfigEnvironmentTarget):
            return value
        return NodeConfigEnvironmentTarget.validate_invocation_value(value)

    async def attach_environment_profile_mount(
        self,
        environment_handle: str,
        profile_key: str,
        package_name: str,
        mount_key: str,
        mode: str = "mounted",
        position: int | None = None,
    ) -> NodeConfigEnvironmentTarget:
        """
        Attach an Environment target and one explicit EnvironmentProfilePackage install mount.

        Contract:
        - Allows explicit EnvironmentProfilePackage install pointers in Node config.
        - Existing target is reused by `environment_handle`.
        - Mounts select OS profile install specs only; Experience lenses activate later.
        """

        payload = {
            "environment_handle": environment_handle,
            "profile_key": profile_key,
            "package_name": package_name,
            "mount_key": mount_key,
            "mode": mode,
            "position": position,
        }
        result = await invoke_instance(
            orm_model=self, function_name="attach_environment_profile_mount", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_node_ontology.node.node_config_environment_target import NodeConfigEnvironmentTarget

        if isinstance(value, NodeConfigEnvironmentTarget):
            return value
        return NodeConfigEnvironmentTarget.validate_invocation_value(value)

    async def attach_service_config(self, service_name: str) -> NodeConfigServiceTarget:
        """
        Attach one canonical `ServiceConfig` target by stable service name.

        Contract:
        - Parent `NodeConfig` scope is injected by propagation.
        - Target identity is resolved from `service_name`.
        - Node keeps desired hosted composition local while Service keeps runtime semantics.
        """

        payload = {"service_name": service_name}
        result = await invoke_instance(orm_model=self, function_name="attach_service_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_node_ontology.node.node_config_service_target import NodeConfigServiceTarget

        if isinstance(value, NodeConfigServiceTarget):
            return value
        return NodeConfigServiceTarget.validate_invocation_value(value)

    async def attach_ontology_package(self, package_name: str) -> NodeConfigOntologyTarget:
        """
        Attach one canonical `OntologyPackage` target by stable package name.

        Contract:
        - Parent `NodeConfig` scope is injected by propagation.
        - Target identity is resolved from `package_name`.
        - Node keeps desired hosted composition local while Ontology keeps
          semantic package/runtime meaning.
        """

        payload = {"package_name": package_name}
        result = await invoke_instance(orm_model=self, function_name="attach_ontology_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_node_ontology.node.node_config_ontology_target import NodeConfigOntologyTarget

        if isinstance(value, NodeConfigOntologyTarget):
            return value
        return NodeConfigOntologyTarget.validate_invocation_value(value)

    async def attach_interface_config(self, interface_name: str) -> NodeConfigInterfaceTarget:
        """
        Attach one canonical `InterfaceConfig` target by stable interface name.

        Contract:
        - Parent `NodeConfig` scope is injected by propagation.
        - Target identity is resolved from `interface_name`.
        - Node keeps desired hosted composition local while Interface keeps runtime semantics.
        """

        payload = {"interface_name": interface_name}
        result = await invoke_instance(orm_model=self, function_name="attach_interface_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_node_ontology.node.node_config_interface_target import NodeConfigInterfaceTarget

        if isinstance(value, NodeConfigInterfaceTarget):
            return value
        return NodeConfigInterfaceTarget.validate_invocation_value(value)


class NodeConfigBuildInput(BaseModel):
    name: str
    description: str | None = Field(default=None)


class NodeConfigBuildOutput(BaseModel):
    value: NodeConfig


class NodeConfigAttachEnvironmentTargetInput(BaseModel):
    environment_handle: str


class NodeConfigAttachEnvironmentTargetOutput(BaseModel):
    value: NodeConfigEnvironmentTarget


class NodeConfigAttachEnvironmentProfileMountInput(BaseModel):
    environment_handle: str
    profile_key: str
    package_name: str
    mount_key: str
    mode: str = Field(default="mounted")
    position: int | None = Field(default=None)


class NodeConfigAttachEnvironmentProfileMountOutput(BaseModel):
    value: NodeConfigEnvironmentTarget


class NodeConfigAttachServiceConfigInput(BaseModel):
    service_name: str


class NodeConfigAttachServiceConfigOutput(BaseModel):
    value: NodeConfigServiceTarget


class NodeConfigAttachOntologyPackageInput(BaseModel):
    package_name: str


class NodeConfigAttachOntologyPackageOutput(BaseModel):
    value: NodeConfigOntologyTarget


class NodeConfigAttachInterfaceConfigInput(BaseModel):
    interface_name: str


class NodeConfigAttachInterfaceConfigOutput(BaseModel):
    value: NodeConfigInterfaceTarget


FUNCTIONS = {
    "NodeConfig": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create the canonical Node-owned desired hosted-composition root.\n\nContract:\n- Identity is keyed by semantic Node package/config `name`.\n- `NodeConfig` remains desired-state truth only; it does not point at live `NetworkNode`\n  runtime state.\n- Hosted composition is attached through contained target objects keyed by stable semantic\n  names rather than raw relationship-id primitives.",
                "is_constructor": True,
            },
            "input": NodeConfigBuildInput,
            "output": NodeConfigBuildOutput,
        },
        "attach_environment_target": {
            "canonical": {
                "name": "attach_environment_target",
                "description": "Attach one canonical Environment target by stable environment handle.\n\nContract:\n- Parent `NodeConfig` scope is injected by propagation.\n- Target identity is resolved from `environment_handle`.\n- Environment profile package mounts are installed separately by explicit\n  Node environment profile declarations.",
                "is_constructor": False,
            },
            "input": NodeConfigAttachEnvironmentTargetInput,
            "output": NodeConfigAttachEnvironmentTargetOutput,
        },
        "attach_environment_profile_mount": {
            "canonical": {
                "name": "attach_environment_profile_mount",
                "description": "Attach an Environment target and one explicit EnvironmentProfilePackage install mount.\n\nContract:\n- Allows explicit EnvironmentProfilePackage install pointers in Node config.\n- Existing target is reused by `environment_handle`.\n- Mounts select OS profile install specs only; Experience lenses activate later.",
                "is_constructor": False,
            },
            "input": NodeConfigAttachEnvironmentProfileMountInput,
            "output": NodeConfigAttachEnvironmentProfileMountOutput,
        },
        "attach_service_config": {
            "canonical": {
                "name": "attach_service_config",
                "description": "Attach one canonical `ServiceConfig` target by stable service name.\n\nContract:\n- Parent `NodeConfig` scope is injected by propagation.\n- Target identity is resolved from `service_name`.\n- Node keeps desired hosted composition local while Service keeps runtime semantics.",
                "is_constructor": False,
            },
            "input": NodeConfigAttachServiceConfigInput,
            "output": NodeConfigAttachServiceConfigOutput,
        },
        "attach_ontology_package": {
            "canonical": {
                "name": "attach_ontology_package",
                "description": "Attach one canonical `OntologyPackage` target by stable package name.\n\nContract:\n- Parent `NodeConfig` scope is injected by propagation.\n- Target identity is resolved from `package_name`.\n- Node keeps desired hosted composition local while Ontology keeps\n  semantic package/runtime meaning.",
                "is_constructor": False,
            },
            "input": NodeConfigAttachOntologyPackageInput,
            "output": NodeConfigAttachOntologyPackageOutput,
        },
        "attach_interface_config": {
            "canonical": {
                "name": "attach_interface_config",
                "description": "Attach one canonical `InterfaceConfig` target by stable interface name.\n\nContract:\n- Parent `NodeConfig` scope is injected by propagation.\n- Target identity is resolved from `interface_name`.\n- Node keeps desired hosted composition local while Interface keeps runtime semantics.",
                "is_constructor": False,
            },
            "input": NodeConfigAttachInterfaceConfigInput,
            "output": NodeConfigAttachInterfaceConfigOutput,
        },
    },
}

__all__ = [
    "NodeConfig",
    "NodeConfigBuildInput",
    "NodeConfigBuildOutput",
    "NodeConfigAttachEnvironmentTargetInput",
    "NodeConfigAttachEnvironmentTargetOutput",
    "NodeConfigAttachEnvironmentProfileMountInput",
    "NodeConfigAttachEnvironmentProfileMountOutput",
    "NodeConfigAttachServiceConfigInput",
    "NodeConfigAttachServiceConfigOutput",
    "NodeConfigAttachOntologyPackageInput",
    "NodeConfigAttachOntologyPackageOutput",
    "NodeConfigAttachInterfaceConfigInput",
    "NodeConfigAttachInterfaceConfigOutput",
    "FUNCTIONS",
]
