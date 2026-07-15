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
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_environment_ontology.environment.environment_profile_package import EnvironmentProfilePackage


class NodeConfigEnvironmentProfileMount(ORMModel):
    # Relationships
    environment_profile_package: EnvironmentProfilePackage | None = Field(default=None)

    # Attributes
    package_name: str = Field(description="Stable EnvironmentProfilePackage package name selected for install.")
    profile_key: str = Field(description="Authored EnvironmentProfileConfig key under the selected package.")
    mount_key: str = Field(description="Stable mount key under the Environment target.")
    mode: str = Field(default="mounted", description="Installation mode (`mounted`, `system`, `extension`, etc.).")
    position: int | None = Field(default=None, description="Ordered install hint.")

    # Foreign Keys
    node_config_environment_target_id: UUID = Field(
        description="Foreign key for NodeConfigEnvironmentTarget.profile_mounts"
    )
    environment_profile_package_id: UUID | None = Field(
        default=None, description="Foreign key for NodeConfigEnvironmentProfileMount.environment_profile_package"
    )

    @classmethod
    async def build_via_node_config_environment_target(
        cls,
        node_config_environment_target_id: UUID,
        profile_key: str,
        package_name: str,
        mount_key: str,
        mode: str = "mounted",
        position: int | None = None,
    ) -> NodeConfigEnvironmentProfileMount:
        """
        Create one Node-owned EnvironmentProfilePackage install mount.

        Contract:
        - Parent `NodeConfigEnvironmentTarget` scope is injected by propagation.
        - Identity is keyed by parent environment target plus `mount_key`.
        - `package_name` resolves the target EnvironmentProfilePackage portal.
        - `profile_key` selects the child EnvironmentProfileConfig key exported by that package.
        - The mount is an explicit Environment-owned OS profile install pointer.
        - Experience profiles are not represented here; they activate after Environment profile install.
        """

        payload = {
            "node_config_environment_target_id": node_config_environment_target_id,
            "profile_key": profile_key,
            "package_name": package_name,
            "mount_key": mount_key,
            "mode": mode,
            "position": position,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_node_config_environment_target", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, NodeConfigEnvironmentProfileMount):
            return value
        return NodeConfigEnvironmentProfileMount.validate_invocation_value(value)


class NodeConfigEnvironmentProfileMountBuildViaNodeConfigEnvironmentTargetInput(BaseModel):
    node_config_environment_target_id: UUID = Field(
        description="Foreign key for NodeConfigEnvironmentTarget.profile_mounts"
    )
    profile_key: str
    package_name: str
    mount_key: str
    mode: str = Field(default="mounted")
    position: int | None = Field(default=None)


class NodeConfigEnvironmentProfileMountBuildViaNodeConfigEnvironmentTargetOutput(BaseModel):
    value: NodeConfigEnvironmentProfileMount


FUNCTIONS = {
    "NodeConfigEnvironmentProfileMount": {
        "build_via_node_config_environment_target": {
            "canonical": {
                "name": "build_via_node_config_environment_target",
                "description": "Create one Node-owned EnvironmentProfilePackage install mount.\n\nContract:\n- Parent `NodeConfigEnvironmentTarget` scope is injected by propagation.\n- Identity is keyed by parent environment target plus `mount_key`.\n- `package_name` resolves the target EnvironmentProfilePackage portal.\n- `profile_key` selects the child EnvironmentProfileConfig key exported by that package.\n- The mount is an explicit Environment-owned OS profile install pointer.\n- Experience profiles are not represented here; they activate after Environment profile install.",
                "is_constructor": True,
            },
            "input": NodeConfigEnvironmentProfileMountBuildViaNodeConfigEnvironmentTargetInput,
            "output": NodeConfigEnvironmentProfileMountBuildViaNodeConfigEnvironmentTargetOutput,
        },
    },
}

__all__ = [
    "NodeConfigEnvironmentProfileMount",
    "NodeConfigEnvironmentProfileMountBuildViaNodeConfigEnvironmentTargetInput",
    "NodeConfigEnvironmentProfileMountBuildViaNodeConfigEnvironmentTargetOutput",
    "FUNCTIONS",
]
