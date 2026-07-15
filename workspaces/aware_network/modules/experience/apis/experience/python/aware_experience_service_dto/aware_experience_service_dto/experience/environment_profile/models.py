from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject


class ExperienceEnvironmentProfileProgramSpec(BaseModel):
    """
    Canonical DTOs for Experience-owned EnvironmentExperience profile provisioning.
    Ownership:
    - Experience API owns this transport boundary.
    - Experience runtime owns profile resolution/materialization semantics.
    - Environment may expose compatibility endpoints, but the target rail calls
    this Experience API/SDK facade instead of importing Experience internals.
    """

    # Attributes
    program_ref: str = Field(description="Canonical registry ref (`<experience_fqn_prefix>:<program_name>`).")


class ExperienceEnvironmentProfileProgramApplySpec(BaseModel):
    # Attributes
    key: str = Field(description="Stable key for one profile-owned apply declaration.")
    program_ref: str = Field(description="Must reference a program installed in `profile.programs`.")
    phase: str = Field(
        default="bootstrap", description="Execution phase bucket interpreted by Experience/runtime orchestration."
    )
    position: int | None = Field(default=None)
    message: str | None = Field(default=None)
    symbols: JsonObject = Field(
        default_factory=JsonObject,
        description="Free-form symbols later forwarded into the program invocation boundary.",
    )


class ExperienceEnvironmentProfileProgramApplyReceipt(BaseModel):
    # Attributes
    key: str
    phase: str = Field(default="bootstrap")
    program_ref: str
    position: int | None = Field(default=None)
    status: str
    error: str | None = Field(default=None)
    program_run_id: UUID | None = Field(default=None)
    turn_id: UUID | None = Field(default=None)
    deduped: bool = Field(default=False)
    resolved_branch_id: UUID | None = Field(default=None)
    resolved_projection_hash: str | None = Field(default=None)
    lane_resolution_source: str | None = Field(default=None)


class ExperienceEnvironmentProfileRoleSpec(BaseModel):
    # Attributes
    name: str = Field(description="Canonical RoleConfig key published by the selected experience profile.")
    description: str | None = Field(default=None)
    capabilities: list[str] = Field(
        default_factory=list, description="Capability refs use `<Class>` or `<Class>.<function>` suffixes."
    )


class ExperienceEnvironmentProfileActorSpec(BaseModel):
    # Attributes
    key: str = Field(description="Canonical ActorConfig key published by the selected experience profile.")
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    type: str | None = Field(default=None)
    role_names: list[str] = Field(default_factory=list, description="Must reference `profile.roles[].name`.")


class ExperienceEnvironmentProfileEventActionSpec(BaseModel):
    # Attributes
    action_experience_ref: str | None = Field(
        default=None, description="Experience ActionExperience ref or stable action key."
    )
    action_config_ref: str | None = Field(
        default=None, description="Reactivity ActionConfig ref. Used by the policy-provisioning follow-up."
    )
    program_ref: str | None = Field(
        default=None, description="Optional program ref for action-backed program dispatch."
    )


class ExperienceEnvironmentProfileEventSpec(BaseModel):
    # Attributes
    event_config_ref: str = Field(description="Reactivity EventConfig ref for this profile event vocabulary entry.")
    condition_config_refs: list[str] = Field(
        default_factory=list, description="Optional ConditionConfig refs that should emit this event."
    )
    actions: list[ExperienceEnvironmentProfileEventActionSpec] = Field(
        default_factory=list, description="Environment-scoped event -> action coupling declared by Experience."
    )


class ExperienceEnvironmentProfileProjectionIdentitySpec(BaseModel):
    # Attributes
    projection_identity_key: str = Field(
        description="Canonical OPG identity key (`{ocg_fqn_prefix}:{projection_name}`)."
    )
    view_key: str | None = Field(default=None)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    position: int | None = Field(default=None)
    is_default: bool = Field(default=False)


class ExperienceEnvironmentProfileLayoutConfigSpec(BaseModel):
    # Attributes
    layout_key: str = Field(description="Canonical Attention LayoutConfig key.")
    key: str | None = Field(default=None, description="Optional stable association key under the ThreadConfig.")
    position: int | None = Field(default=None)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)


class ExperienceEnvironmentProfileThreadSpec(BaseModel):
    # Attributes
    key: str = Field(description="Reusable ThreadConfig key under the target ProcessConfig.")
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    workspace_view_key: str | None = Field(default=None)
    position: int | None = Field(default=None)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    state_prompt_template: str | None = Field(default=None)
    projection_identities: list[ExperienceEnvironmentProfileProjectionIdentitySpec] = Field(default_factory=list)
    layout_configs: list[ExperienceEnvironmentProfileLayoutConfigSpec] = Field(default_factory=list)


class ExperienceEnvironmentProfileProcessSpec(BaseModel):
    # Attributes
    key: str = Field(description="Reusable ProcessConfig key under the profile.")
    type: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    shape: str | None = Field(default=None)
    position: int | None = Field(default=None)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    thread_configs: list[ExperienceEnvironmentProfileThreadSpec] = Field(default_factory=list)


class ExperienceEnvironmentProfileTopologyLayoutSeedSpec(BaseModel):
    # Attributes
    layout_key: str = Field(description="Must reference a layout candidate declared in the selected ThreadConfig.")
    key: str | None = Field(default=None)
    position: int | None = Field(default=None)
    activate_on_seed: bool = Field(default=False)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)


class ExperienceEnvironmentProfileTopologyThreadSeedSpec(BaseModel):
    # Attributes
    thread_config_key: str = Field(description="Must reference a ThreadConfig key under the selected ProcessConfig.")
    thread_key: str = Field(description="Runtime Thread.key for this concrete seed instance.")
    key: str | None = Field(default=None)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    position: int | None = Field(default=None)
    is_main: bool = Field(default=False)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    layout_seeds: list[ExperienceEnvironmentProfileTopologyLayoutSeedSpec] = Field(default_factory=list)


class ExperienceEnvironmentProfileTopologyProcessSeedSpec(BaseModel):
    # Attributes
    process_config_key: str = Field(description="Must reference a ProcessConfig key under the selected profile.")
    process_key: str = Field(description="Runtime Process.key for this concrete seed instance.")
    key: str | None = Field(default=None)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    position: int | None = Field(default=None)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    thread_seeds: list[ExperienceEnvironmentProfileTopologyThreadSeedSpec] = Field(default_factory=list)


class ExperienceEnvironmentProfileTopologySeedSpec(BaseModel):
    # Attributes
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    narrative: str | None = Field(default=None)
    process_seeds: list[ExperienceEnvironmentProfileTopologyProcessSeedSpec] = Field(default_factory=list)


class ExperienceEnvironmentProfileRuntimeMountReceipt(BaseModel):
    # Attributes
    environment_id: UUID
    environment_experience_profile_id: UUID
    environment_experience_profile_mount_id: UUID | None = Field(default=None)
    mount_key: str | None = Field(default=None)
    topology_seed_key: str
    process_config_id: UUID | None = Field(default=None)
    process_key: str
    process_id: UUID
    thread_config_id: UUID | None = Field(default=None)
    thread_key: str
    thread_id: UUID
    thread_layout_config_id: UUID | None = Field(default=None)
    layout_key: str | None = Field(default=None)
    layout_config_id: UUID | None = Field(default=None)
    layout_id: UUID | None = Field(default=None)
    thread_layout_id: UUID | None = Field(default=None)
    activate_on_seed: bool = Field(default=False)
    status: str = Field(default="succeeded")


class ExperienceEnvironmentProfileSpec(BaseModel):
    # Attributes
    key: str | None = Field(default=None)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    narrative: str | None = Field(default=None)
    roles: list[ExperienceEnvironmentProfileRoleSpec] = Field(default_factory=list)
    actors: list[ExperienceEnvironmentProfileActorSpec] = Field(default_factory=list)
    events: list[ExperienceEnvironmentProfileEventSpec] = Field(
        default_factory=list, description="Profile-scoped Reactivity event/action vocabulary owned by Experience."
    )
    programs: list[ExperienceEnvironmentProfileProgramSpec] = Field(default_factory=list)
    program_applies: list[ExperienceEnvironmentProfileProgramApplySpec] = Field(default_factory=list)
    process_configs: list[ExperienceEnvironmentProfileProcessSpec] = Field(default_factory=list)
