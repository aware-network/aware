from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

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
    from aware_environment_ontology.environment.environment_config import EnvironmentConfig
    from aware_node_ontology.node.node_config_environment_profile_mount import NodeConfigEnvironmentProfileMount


class NodeConfigEnvironmentTarget(ORMModel):
    # Relationships
    environment_config: EnvironmentConfig | None = Field(default=None)
    profile_mounts: list[NodeConfigEnvironmentProfileMount] = Field(default_factory=list)

    # Attributes
    environment_handle: str

    # Foreign Keys
    node_config_id: UUID = Field(description="Foreign key for NodeConfig.environment_targets")
    environment_config_id: UUID | None = Field(
        default=None, description="Foreign key for NodeConfigEnvironmentTarget.environment_config"
    )

    async def add_profile_mount(
        self, profile_key: str, package_name: str, mount_key: str, mode: str = "mounted", position: int | None = None
    ) -> NodeConfigEnvironmentProfileMount:
        """
        Attach one EnvironmentProfilePackage install mount under this Environment target.

        Contract:
        - Mounts select EnvironmentProfilePackage install specs, not Experience profiles.
        - `package_name/profile_key` remain stable authored refs; Node does not store
          raw package ids.
        - Experience lenses activate later through Experience/session rails after
          Environment has applied its OS profile.
        """

        payload = {
            "profile_key": profile_key,
            "package_name": package_name,
            "mount_key": mount_key,
            "mode": mode,
            "position": position,
        }
        result = await invoke_instance(orm_model=self, function_name="add_profile_mount", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_node_ontology.node.node_config_environment_profile_mount import NodeConfigEnvironmentProfileMount

        if isinstance(value, NodeConfigEnvironmentProfileMount):
            return value
        return NodeConfigEnvironmentProfileMount.validate_invocation_value(value)

    @classmethod
    async def build_via_node_config(cls, node_config_id: UUID, environment_handle: str) -> NodeConfigEnvironmentTarget:
        """
        Create one Node-owned environment target by canonical environment selection.

        Contract:
        - Parent `NodeConfig` scope is injected by propagation.
        - Identity is keyed by `(node_config_id, environment_handle)`.
        - `environment_handle` resolves the target `EnvironmentConfig` portal.
        - Environment profile package mounts are explicit optional pointers.
        """

        payload = {"node_config_id": node_config_id, "environment_handle": environment_handle}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_node_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, NodeConfigEnvironmentTarget):
            return value
        return NodeConfigEnvironmentTarget.validate_invocation_value(value)


class NodeConfigEnvironmentTargetAddProfileMountInput(BaseModel):
    profile_key: str
    package_name: str
    mount_key: str
    mode: str = Field(default="mounted")
    position: int | None = Field(default=None)


class NodeConfigEnvironmentTargetAddProfileMountOutput(BaseModel):
    value: NodeConfigEnvironmentProfileMount


class NodeConfigEnvironmentTargetBuildViaNodeConfigInput(BaseModel):
    node_config_id: UUID = Field(description="Foreign key for NodeConfig.environment_targets")
    environment_handle: str


class NodeConfigEnvironmentTargetBuildViaNodeConfigOutput(BaseModel):
    value: NodeConfigEnvironmentTarget


FUNCTIONS = {
    "NodeConfigEnvironmentTarget": {
        "add_profile_mount": {
            "canonical": {
                "name": "add_profile_mount",
                "description": "Attach one EnvironmentProfilePackage install mount under this Environment target.\n\nContract:\n- Mounts select EnvironmentProfilePackage install specs, not Experience profiles.\n- `package_name/profile_key` remain stable authored refs; Node does not store\n  raw package ids.\n- Experience lenses activate later through Experience/session rails after\n  Environment has applied its OS profile.",
                "is_constructor": False,
            },
            "input": NodeConfigEnvironmentTargetAddProfileMountInput,
            "output": NodeConfigEnvironmentTargetAddProfileMountOutput,
        },
        "build_via_node_config": {
            "canonical": {
                "name": "build_via_node_config",
                "description": "Create one Node-owned environment target by canonical environment selection.\n\nContract:\n- Parent `NodeConfig` scope is injected by propagation.\n- Identity is keyed by `(node_config_id, environment_handle)`.\n- `environment_handle` resolves the target `EnvironmentConfig` portal.\n- Environment profile package mounts are explicit optional pointers.",
                "is_constructor": True,
            },
            "input": NodeConfigEnvironmentTargetBuildViaNodeConfigInput,
            "output": NodeConfigEnvironmentTargetBuildViaNodeConfigOutput,
        },
    },
}

__all__ = [
    "NodeConfigEnvironmentTarget",
    "NodeConfigEnvironmentTargetAddProfileMountInput",
    "NodeConfigEnvironmentTargetAddProfileMountOutput",
    "NodeConfigEnvironmentTargetBuildViaNodeConfigInput",
    "NodeConfigEnvironmentTargetBuildViaNodeConfigOutput",
    "FUNCTIONS",
]
