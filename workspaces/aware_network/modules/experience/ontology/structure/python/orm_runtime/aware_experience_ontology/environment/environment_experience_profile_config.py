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
    from aware_environment_ontology.environment.environment_profile_config import EnvironmentProfileConfig
    from aware_environment_ontology.environment.environment_provider_grant import EnvironmentProviderGrant
    from aware_experience_ontology.environment.environment_experience_actor import EnvironmentExperienceActorConfig
    from aware_experience_ontology.environment.environment_experience_event import EnvironmentExperienceEvent
    from aware_experience_ontology.environment.environment_experience_process_config import (
        EnvironmentExperienceProcessConfig,
    )
    from aware_experience_ontology.environment.environment_experience_projection import EnvironmentExperienceProjection
    from aware_experience_ontology.environment.environment_experience_view_event_transition import (
        EnvironmentExperienceViewEventTransition,
    )
    from aware_storage_ontology.blob.storage_blob import StorageBlob


class EnvironmentExperienceProfileConfig(ORMModel):
    """
    Reusable Experience policy/config over one Environment EnvironmentProfileConfig.
    Purpose:
    - Bind Experience actor, projection, event, and policy semantics to stable
    Environment Environment topology config.
    - Keep EnvironmentProfileConfig/ProcessConfig/ThreadConfig construction in
    Environment while Experience config declares how it participates.
    Contract:
    - This object references Environment EnvironmentProfileConfig and optional
    EnvironmentProviderGrant truth.
    - It never constructs Environment topology config or applied EnvironmentProfile state.
    - Process/thread participation is represented by Experience config bridge
    objects keyed to Environment ProcessConfig/ThreadConfig.
    """

    # Relationships
    environment_profile_config: EnvironmentProfileConfig | None = Field(default=None, exclude=True)
    environment_provider_grant: EnvironmentProviderGrant | None = Field(default=None, exclude=True)
    actors: list[EnvironmentExperienceActorConfig] = Field(default_factory=list, exclude=True)
    experiences: list[EnvironmentExperienceProjection] = Field(default_factory=list, exclude=True)
    events: list[EnvironmentExperienceEvent] = Field(default_factory=list, exclude=True)
    view_event_transitions: list[EnvironmentExperienceViewEventTransition] = Field(
        default_factory=list,
        exclude=True,
        description="Experience-owned View -> Event -> View transition policies.\nContract:\n- The target is always a ProjectionExperienceSectionGraphBinding.\n- Attention focus is reached only through that binding, never directly here.",
    )
    process_configs: list[EnvironmentExperienceProcessConfig] = Field(default_factory=list, exclude=True)
    image: StorageBlob | None = Field(
        default=None,
        exclude=True,
        description="Optional experience-level image used as a default for territory surfaces.\nContract:\n- Image bytes are uploaded out-of-band (data-plane).\n- Commits reference StorageBlob metadata only.",
    )

    # Attributes
    description: str | None = Field(default=None)
    narrative: str | None = Field(
        default=None, description="Canonical experience-level narrative used by experience selection and AI context."
    )
    key: str = Field(description="Stable profile key (recommended: `control.default`, `coordination.default`, etc).")
    title: str | None = Field(default=None)

    # Foreign Keys
    environment_experience_id: UUID = Field(description="Foreign key for EnvironmentExperience.profile_configs")
    environment_profile_config_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceProfileConfig.environment_profile_config"
    )
    environment_provider_grant_id: UUID | None = Field(
        default=None, description="Foreign key for EnvironmentExperienceProfileConfig.environment_provider_grant"
    )
    image_id: UUID | None = Field(default=None, description="Foreign key for EnvironmentExperienceProfileConfig.image")

    async def add_process_config(
        self,
        process_config_id: UUID,
        key: str,
        title: str | None = None,
        description: str | None = None,
        position: int | None = None,
        narrative: str | None = None,
        intent: str | None = None,
    ) -> EnvironmentExperienceProcessConfig:
        """
        Attach one Experience config bridge for an Environment ProcessConfig.

        Contract:
        - `process_config_id` references Environment-owned topology config.
        - This function never constructs ProcessConfig.
        - Mutates only this profile config's Experience bridge membership.
        """

        payload = {
            "process_config_id": process_config_id,
            "key": key,
            "title": title,
            "description": description,
            "position": position,
            "narrative": narrative,
            "intent": intent,
        }
        result = await invoke_instance(orm_model=self, function_name="add_process_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.environment.environment_experience_process_config import (
            EnvironmentExperienceProcessConfig,
        )

        if isinstance(value, EnvironmentExperienceProcessConfig):
            return value
        return EnvironmentExperienceProcessConfig.validate_invocation_value(value)

    async def add_actor_config(self, actor_config_id: UUID) -> EnvironmentExperienceActorConfig:
        """Attach one ActorConfig association edge under this EnvironmentExperienceProfileConfig."""

        payload = {"actor_config_id": actor_config_id}
        result = await invoke_instance(orm_model=self, function_name="add_actor_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.environment.environment_experience_actor import EnvironmentExperienceActorConfig

        if isinstance(value, EnvironmentExperienceActorConfig):
            return value
        return EnvironmentExperienceActorConfig.validate_invocation_value(value)

    async def add_projection_experience(self, projection_experience_id: UUID) -> EnvironmentExperienceProjection:
        """Attach one ProjectionExperience association edge under this EnvironmentExperienceProfileConfig."""

        payload = {"projection_experience_id": projection_experience_id}
        result = await invoke_instance(orm_model=self, function_name="add_projection_experience", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.environment.environment_experience_projection import (
            EnvironmentExperienceProjection,
        )

        if isinstance(value, EnvironmentExperienceProjection):
            return value
        return EnvironmentExperienceProjection.validate_invocation_value(value)

    async def add_event(self, event_config_id: UUID) -> EnvironmentExperienceEvent:
        """Attach one EventConfig association edge under this EnvironmentExperienceProfileConfig."""

        payload = {"event_config_id": event_config_id}
        result = await invoke_instance(orm_model=self, function_name="add_event", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.environment.environment_experience_event import EnvironmentExperienceEvent

        if isinstance(value, EnvironmentExperienceEvent):
            return value
        return EnvironmentExperienceEvent.validate_invocation_value(value)

    async def add_view_event_transition(
        self,
        source_view_id: UUID,
        trigger_event_id: UUID,
        target_section_graph_binding_id: UUID,
        transition_key: str,
        name: str | None = None,
        rationale: str | None = None,
        idempotency_policy: str | None = None,
    ) -> EnvironmentExperienceViewEventTransition:
        """
        Attach one Experience-owned View -> Event -> View transition policy.

        Contract:
        - `source_view_id` is the currently focused ProjectionExperienceView.
        - `trigger_event_id` is the profile-config-owned EnvironmentExperienceEvent emitted by Reactivity.
        - `target_section_graph_binding_id` points to the target view/graph/layout section contract.
        - This contract does not talk to Attention directly; runtime focus activation goes through
          ProjectionExperienceSectionGraphBinding.
        """

        payload = {
            "source_view_id": source_view_id,
            "trigger_event_id": trigger_event_id,
            "target_section_graph_binding_id": target_section_graph_binding_id,
            "transition_key": transition_key,
            "name": name,
            "rationale": rationale,
            "idempotency_policy": idempotency_policy,
        }
        result = await invoke_instance(orm_model=self, function_name="add_view_event_transition", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.environment.environment_experience_view_event_transition import (
            EnvironmentExperienceViewEventTransition,
        )

        if isinstance(value, EnvironmentExperienceViewEventTransition):
            return value
        return EnvironmentExperienceViewEventTransition.validate_invocation_value(value)

    async def update_title(self, title: str | None = None) -> None:
        """
        Replace or clear the title of this Experience profile config.

        Contract:
        - Mutates only the invoked EnvironmentExperienceProfileConfig.
        - `null` explicitly clears the title.
        - Description, narrative, identity, and relationship fields are preserved.
        """

        payload = {"title": title}
        await invoke_instance(orm_model=self, function_name="update_title", payload=payload)
        return None

    async def update_picture(
        self,
        image_id: UUID | None = None,
        image_sha: str | None = None,
        image_mime_type: str | None = None,
        image_size_bytes: int | None = None,
    ) -> None:
        """
        Updates (or clears) the experience profile config image.

        Contract:
        - Raw bytes are uploaded out-of-band via HTTP file operations.
        - Commits must reference commit-backed StorageBlob metadata only.
        - When setting a picture, image_sha/image_mime_type/image_size_bytes must be provided together.

        Parameters:
            image_id: Optional uploaded blob id to assert against image_sha-derived stable id.
            image_sha: SHA-256 hex digest of uploaded bytes.
            image_mime_type: MIME type of uploaded bytes.
            image_size_bytes: Size of uploaded bytes.
        Returns: None.
        """

        payload = {
            "image_id": image_id,
            "image_sha": image_sha,
            "image_mime_type": image_mime_type,
            "image_size_bytes": image_size_bytes,
        }
        await invoke_instance(orm_model=self, function_name="update_picture", payload=payload)
        return None

    @classmethod
    async def build_via_environment_experience(
        cls,
        environment_experience_id: UUID,
        environment_profile_config_id: UUID,
        key: str,
        environment_provider_grant_id: UUID | None = None,
        title: str | None = None,
        description: str | None = None,
        narrative: str | None = None,
    ) -> EnvironmentExperienceProfileConfig:
        """
        Construct one canonical EnvironmentExperienceProfileConfig under EnvironmentExperience.

        Contract:
        - Identity is derived from parent path plus `(environment_profile_config_id, key)`.
        - The target EnvironmentProfileConfig is Environment-owned reusable topology truth.
        - `environment_provider_grant_id` records the approved Environment provider
          grant when present; it does not make Environment depend on Experience.
        """

        payload = {
            "environment_experience_id": environment_experience_id,
            "environment_profile_config_id": environment_profile_config_id,
            "key": key,
            "environment_provider_grant_id": environment_provider_grant_id,
            "title": title,
            "description": description,
            "narrative": narrative,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_environment_experience", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentExperienceProfileConfig):
            return value
        return EnvironmentExperienceProfileConfig.validate_invocation_value(value)


class EnvironmentExperienceProfileConfigAddProcessConfigInput(BaseModel):
    process_config_id: UUID
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    position: int | None = Field(default=None)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)


class EnvironmentExperienceProfileConfigAddProcessConfigOutput(BaseModel):
    value: EnvironmentExperienceProcessConfig


class EnvironmentExperienceProfileConfigAddActorConfigInput(BaseModel):
    actor_config_id: UUID


class EnvironmentExperienceProfileConfigAddActorConfigOutput(BaseModel):
    value: EnvironmentExperienceActorConfig


class EnvironmentExperienceProfileConfigAddProjectionExperienceInput(BaseModel):
    projection_experience_id: UUID


class EnvironmentExperienceProfileConfigAddProjectionExperienceOutput(BaseModel):
    value: EnvironmentExperienceProjection


class EnvironmentExperienceProfileConfigAddEventInput(BaseModel):
    event_config_id: UUID


class EnvironmentExperienceProfileConfigAddEventOutput(BaseModel):
    value: EnvironmentExperienceEvent


class EnvironmentExperienceProfileConfigAddViewEventTransitionInput(BaseModel):
    source_view_id: UUID
    trigger_event_id: UUID
    target_section_graph_binding_id: UUID
    transition_key: str
    name: str | None = Field(default=None)
    rationale: str | None = Field(default=None)
    idempotency_policy: str | None = Field(default=None)


class EnvironmentExperienceProfileConfigAddViewEventTransitionOutput(BaseModel):
    value: EnvironmentExperienceViewEventTransition


class EnvironmentExperienceProfileConfigUpdateTitleInput(BaseModel):
    title: str | None = Field(default=None)


class EnvironmentExperienceProfileConfigUpdateTitleOutput(BaseModel):
    pass


class EnvironmentExperienceProfileConfigUpdatePictureInput(BaseModel):
    image_id: UUID | None = Field(default=None)
    image_sha: str | None = Field(default=None)
    image_mime_type: str | None = Field(default=None)
    image_size_bytes: int | None = Field(default=None)


class EnvironmentExperienceProfileConfigUpdatePictureOutput(BaseModel):
    pass


class EnvironmentExperienceProfileConfigBuildViaEnvironmentExperienceInput(BaseModel):
    environment_experience_id: UUID = Field(description="Foreign key for EnvironmentExperience.profile_configs")
    environment_profile_config_id: UUID
    key: str
    environment_provider_grant_id: UUID | None = Field(default=None)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    narrative: str | None = Field(default=None)


class EnvironmentExperienceProfileConfigBuildViaEnvironmentExperienceOutput(BaseModel):
    value: EnvironmentExperienceProfileConfig


FUNCTIONS = {
    "EnvironmentExperienceProfileConfig": {
        "add_process_config": {
            "canonical": {
                "name": "add_process_config",
                "description": "Attach one Experience config bridge for an Environment ProcessConfig.\n\nContract:\n- `process_config_id` references Environment-owned topology config.\n- This function never constructs ProcessConfig.\n- Mutates only this profile config's Experience bridge membership.",
                "is_constructor": False,
            },
            "input": EnvironmentExperienceProfileConfigAddProcessConfigInput,
            "output": EnvironmentExperienceProfileConfigAddProcessConfigOutput,
        },
        "add_actor_config": {
            "canonical": {
                "name": "add_actor_config",
                "description": "Attach one ActorConfig association edge under this EnvironmentExperienceProfileConfig.",
                "is_constructor": False,
            },
            "input": EnvironmentExperienceProfileConfigAddActorConfigInput,
            "output": EnvironmentExperienceProfileConfigAddActorConfigOutput,
        },
        "add_projection_experience": {
            "canonical": {
                "name": "add_projection_experience",
                "description": "Attach one ProjectionExperience association edge under this EnvironmentExperienceProfileConfig.",
                "is_constructor": False,
            },
            "input": EnvironmentExperienceProfileConfigAddProjectionExperienceInput,
            "output": EnvironmentExperienceProfileConfigAddProjectionExperienceOutput,
        },
        "add_event": {
            "canonical": {
                "name": "add_event",
                "description": "Attach one EventConfig association edge under this EnvironmentExperienceProfileConfig.",
                "is_constructor": False,
            },
            "input": EnvironmentExperienceProfileConfigAddEventInput,
            "output": EnvironmentExperienceProfileConfigAddEventOutput,
        },
        "add_view_event_transition": {
            "canonical": {
                "name": "add_view_event_transition",
                "description": "Attach one Experience-owned View -> Event -> View transition policy.\n\nContract:\n- `source_view_id` is the currently focused ProjectionExperienceView.\n- `trigger_event_id` is the profile-config-owned EnvironmentExperienceEvent emitted by Reactivity.\n- `target_section_graph_binding_id` points to the target view/graph/layout section contract.\n- This contract does not talk to Attention directly; runtime focus activation goes through\n  ProjectionExperienceSectionGraphBinding.",
                "is_constructor": False,
            },
            "input": EnvironmentExperienceProfileConfigAddViewEventTransitionInput,
            "output": EnvironmentExperienceProfileConfigAddViewEventTransitionOutput,
        },
        "update_title": {
            "canonical": {
                "name": "update_title",
                "description": "Replace or clear the title of this Experience profile config.\n\nContract:\n- Mutates only the invoked EnvironmentExperienceProfileConfig.\n- `null` explicitly clears the title.\n- Description, narrative, identity, and relationship fields are preserved.",
                "is_constructor": False,
            },
            "input": EnvironmentExperienceProfileConfigUpdateTitleInput,
            "output": EnvironmentExperienceProfileConfigUpdateTitleOutput,
        },
        "update_picture": {
            "canonical": {
                "name": "update_picture",
                "description": "Updates (or clears) the experience profile config image.\n\nContract:\n- Raw bytes are uploaded out-of-band via HTTP file operations.\n- Commits must reference commit-backed StorageBlob metadata only.\n- When setting a picture, image_sha/image_mime_type/image_size_bytes must be provided together.\n\nParameters:\n    image_id: Optional uploaded blob id to assert against image_sha-derived stable id.\n    image_sha: SHA-256 hex digest of uploaded bytes.\n    image_mime_type: MIME type of uploaded bytes.\n    image_size_bytes: Size of uploaded bytes.\nReturns: None.",
                "is_constructor": False,
            },
            "input": EnvironmentExperienceProfileConfigUpdatePictureInput,
            "output": EnvironmentExperienceProfileConfigUpdatePictureOutput,
        },
        "build_via_environment_experience": {
            "canonical": {
                "name": "build_via_environment_experience",
                "description": "Construct one canonical EnvironmentExperienceProfileConfig under EnvironmentExperience.\n\nContract:\n- Identity is derived from parent path plus `(environment_profile_config_id, key)`.\n- The target EnvironmentProfileConfig is Environment-owned reusable topology truth.\n- `environment_provider_grant_id` records the approved Environment provider\n  grant when present; it does not make Environment depend on Experience.",
                "is_constructor": True,
            },
            "input": EnvironmentExperienceProfileConfigBuildViaEnvironmentExperienceInput,
            "output": EnvironmentExperienceProfileConfigBuildViaEnvironmentExperienceOutput,
        },
    },
}

__all__ = [
    "EnvironmentExperienceProfileConfig",
    "EnvironmentExperienceProfileConfigAddProcessConfigInput",
    "EnvironmentExperienceProfileConfigAddProcessConfigOutput",
    "EnvironmentExperienceProfileConfigAddActorConfigInput",
    "EnvironmentExperienceProfileConfigAddActorConfigOutput",
    "EnvironmentExperienceProfileConfigAddProjectionExperienceInput",
    "EnvironmentExperienceProfileConfigAddProjectionExperienceOutput",
    "EnvironmentExperienceProfileConfigAddEventInput",
    "EnvironmentExperienceProfileConfigAddEventOutput",
    "EnvironmentExperienceProfileConfigAddViewEventTransitionInput",
    "EnvironmentExperienceProfileConfigAddViewEventTransitionOutput",
    "EnvironmentExperienceProfileConfigUpdateTitleInput",
    "EnvironmentExperienceProfileConfigUpdateTitleOutput",
    "EnvironmentExperienceProfileConfigUpdatePictureInput",
    "EnvironmentExperienceProfileConfigUpdatePictureOutput",
    "EnvironmentExperienceProfileConfigBuildViaEnvironmentExperienceInput",
    "EnvironmentExperienceProfileConfigBuildViaEnvironmentExperienceOutput",
    "FUNCTIONS",
]
