from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Experience Ontology
from aware_experience_ontology.session.experience_session_enums import ExperienceSessionState

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_experience_ontology.environment.environment_experience_profile import EnvironmentExperienceProfile
    from aware_experience_ontology.environment.environment_experience_profile_config import (
        EnvironmentExperienceProfileConfig,
    )
    from aware_experience_ontology.environment.environment_topology_seed import EnvironmentTopologySeed
    from aware_experience_ontology.session.experience_session import ExperienceSession


class EnvironmentExperience(ORMModel):
    """
    Canonical Experience namespace root.
    Purpose:
    - Own one deterministic `fqn_prefix` namespace for experience packages.
    - Scope Experience profile config keys under this root.
    - Keep Environment Environment topology stable and referential-only.
    """

    # Relationships
    profile_configs: list[EnvironmentExperienceProfileConfig] = Field(default_factory=list, exclude=True)
    profiles: list[EnvironmentExperienceProfile] = Field(default_factory=list, exclude=True)
    sessions: list[ExperienceSession] = Field(default_factory=list, exclude=True)
    topology_seeds: list[EnvironmentTopologySeed] = Field(default_factory=list, exclude=True)

    # Attributes
    description: str | None = Field(default=None)
    fqn_prefix: str
    title: str | None = Field(default=None)

    @classmethod
    async def build(
        cls, fqn_prefix: str, title: str | None = None, description: str | None = None
    ) -> EnvironmentExperience:
        """
        Create the canonical EnvironmentExperience namespace root.

        Notes:
        - Identity is derived from `fqn_prefix`.
        - This class is the Experience-owned root for profile composition.
        """

        payload = {"fqn_prefix": fqn_prefix, "title": title, "description": description}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentExperience):
            return value
        return EnvironmentExperience.validate_invocation_value(value)

    async def create_profile_config(
        self,
        environment_profile_config_id: UUID,
        key: str,
        environment_provider_grant_id: UUID | None = None,
        title: str | None = None,
        description: str | None = None,
        narrative: str | None = None,
    ) -> EnvironmentExperienceProfileConfig:
        """
        Create one reusable profile config under this EnvironmentExperience namespace.

        Contract:
        - Profile config identity is scoped by parent->child invocation path
          plus the target Environment EnvironmentProfileConfig.
        - Experience profile config references Environment topology config; it
          does not construct EnvironmentProfile/ProcessConfig/ThreadConfig.
        """

        payload = {
            "environment_profile_config_id": environment_profile_config_id,
            "key": key,
            "environment_provider_grant_id": environment_provider_grant_id,
            "title": title,
            "description": description,
            "narrative": narrative,
        }
        result = await invoke_instance(orm_model=self, function_name="create_profile_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.environment.environment_experience_profile_config import (
            EnvironmentExperienceProfileConfig,
        )

        if isinstance(value, EnvironmentExperienceProfileConfig):
            return value
        return EnvironmentExperienceProfileConfig.validate_invocation_value(value)

    async def create_profile(
        self,
        profile_config_id: UUID,
        environment_profile_id: UUID,
        status: str = "active",
        title: str | None = None,
        description: str | None = None,
        metadata_json: JsonObject | None = {},
    ) -> EnvironmentExperienceProfile:
        """
        Create one applied Experience profile bridge under this EnvironmentExperience namespace.

        Contract:
        - Applied profile identity is scoped by parent->child invocation path
          plus `(profile_config_id, environment_profile_id)`.
        - Reusable Experience policy remains on EnvironmentExperienceProfileConfig.
        - Concrete Environment sessions remain on Environment EnvironmentProfile
          until the session rail is added.
        """

        payload = {
            "profile_config_id": profile_config_id,
            "environment_profile_id": environment_profile_id,
            "status": status,
            "title": title,
            "description": description,
            "metadata_json": metadata_json,
        }
        result = await invoke_instance(orm_model=self, function_name="create_profile", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.environment.environment_experience_profile import EnvironmentExperienceProfile

        if isinstance(value, EnvironmentExperienceProfile):
            return value
        return EnvironmentExperienceProfile.validate_invocation_value(value)

    async def create_topology_seed(
        self,
        environment_experience_profile_config_id: UUID,
        key: str,
        title: str | None = None,
        description: str | None = None,
        narrative: str | None = None,
    ) -> EnvironmentTopologySeed:
        """
        Create one topology seed under this EnvironmentExperience namespace.

        Contract:
        - Seeds provide runtime process/thread/layout keys for genesis or named entrypoints.
        - Profile configs remain reusable policy and do not imply one runtime topology.
        """

        payload = {
            "environment_experience_profile_config_id": environment_experience_profile_config_id,
            "key": key,
            "title": title,
            "description": description,
            "narrative": narrative,
        }
        result = await invoke_instance(orm_model=self, function_name="create_topology_seed", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.environment.environment_topology_seed import EnvironmentTopologySeed

        if isinstance(value, EnvironmentTopologySeed):
            return value
        return EnvironmentTopologySeed.validate_invocation_value(value)

    async def start_session(
        self,
        identity_session_id: UUID,
        environment_session_id: UUID,
        state: ExperienceSessionState = ExperienceSessionState.active,
    ) -> ExperienceSession:
        """
        Start one commit-backed Experience session for a child Identity Session.

        Contract:
        - The child Identity Session owns participation, roles, and lifecycle.
        - EnvironmentSession supplies explicit shared-environment provenance.
        - ExperienceSession owns profile mount rows and local session state;
          visible/active view state remains scoped downstream.
        """

        payload = {
            "identity_session_id": identity_session_id,
            "environment_session_id": environment_session_id,
            "state": state,
        }
        result = await invoke_instance(orm_model=self, function_name="start_session", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.session.experience_session import ExperienceSession

        if isinstance(value, ExperienceSession):
            return value
        return ExperienceSession.validate_invocation_value(value)


class EnvironmentExperienceBuildInput(BaseModel):
    fqn_prefix: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)


class EnvironmentExperienceBuildOutput(BaseModel):
    value: EnvironmentExperience


class EnvironmentExperienceCreateProfileConfigInput(BaseModel):
    environment_profile_config_id: UUID
    key: str
    environment_provider_grant_id: UUID | None = Field(default=None)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    narrative: str | None = Field(default=None)


class EnvironmentExperienceCreateProfileConfigOutput(BaseModel):
    value: EnvironmentExperienceProfileConfig


class EnvironmentExperienceCreateProfileInput(BaseModel):
    profile_config_id: UUID
    environment_profile_id: UUID
    status: str = Field(default="active")
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class EnvironmentExperienceCreateProfileOutput(BaseModel):
    value: EnvironmentExperienceProfile


class EnvironmentExperienceCreateTopologySeedInput(BaseModel):
    environment_experience_profile_config_id: UUID
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    narrative: str | None = Field(default=None)


class EnvironmentExperienceCreateTopologySeedOutput(BaseModel):
    value: EnvironmentTopologySeed


class EnvironmentExperienceStartSessionInput(BaseModel):
    identity_session_id: UUID
    environment_session_id: UUID
    state: ExperienceSessionState = Field(default=ExperienceSessionState.active)


class EnvironmentExperienceStartSessionOutput(BaseModel):
    value: ExperienceSession


FUNCTIONS = {
    "EnvironmentExperience": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create the canonical EnvironmentExperience namespace root.\n\nNotes:\n- Identity is derived from `fqn_prefix`.\n- This class is the Experience-owned root for profile composition.",
                "is_constructor": True,
            },
            "input": EnvironmentExperienceBuildInput,
            "output": EnvironmentExperienceBuildOutput,
        },
        "create_profile_config": {
            "canonical": {
                "name": "create_profile_config",
                "description": "Create one reusable profile config under this EnvironmentExperience namespace.\n\nContract:\n- Profile config identity is scoped by parent->child invocation path\n  plus the target Environment EnvironmentProfileConfig.\n- Experience profile config references Environment topology config; it\n  does not construct EnvironmentProfile/ProcessConfig/ThreadConfig.",
                "is_constructor": False,
            },
            "input": EnvironmentExperienceCreateProfileConfigInput,
            "output": EnvironmentExperienceCreateProfileConfigOutput,
        },
        "create_profile": {
            "canonical": {
                "name": "create_profile",
                "description": "Create one applied Experience profile bridge under this EnvironmentExperience namespace.\n\nContract:\n- Applied profile identity is scoped by parent->child invocation path\n  plus `(profile_config_id, environment_profile_id)`.\n- Reusable Experience policy remains on EnvironmentExperienceProfileConfig.\n- Concrete Environment sessions remain on Environment EnvironmentProfile\n  until the session rail is added.",
                "is_constructor": False,
            },
            "input": EnvironmentExperienceCreateProfileInput,
            "output": EnvironmentExperienceCreateProfileOutput,
        },
        "create_topology_seed": {
            "canonical": {
                "name": "create_topology_seed",
                "description": "Create one topology seed under this EnvironmentExperience namespace.\n\nContract:\n- Seeds provide runtime process/thread/layout keys for genesis or named entrypoints.\n- Profile configs remain reusable policy and do not imply one runtime topology.",
                "is_constructor": False,
            },
            "input": EnvironmentExperienceCreateTopologySeedInput,
            "output": EnvironmentExperienceCreateTopologySeedOutput,
        },
        "start_session": {
            "canonical": {
                "name": "start_session",
                "description": "Start one commit-backed Experience session for a child Identity Session.\n\nContract:\n- The child Identity Session owns participation, roles, and lifecycle.\n- EnvironmentSession supplies explicit shared-environment provenance.\n- ExperienceSession owns profile mount rows and local session state;\n  visible/active view state remains scoped downstream.",
                "is_constructor": False,
            },
            "input": EnvironmentExperienceStartSessionInput,
            "output": EnvironmentExperienceStartSessionOutput,
        },
    },
}

__all__ = [
    "EnvironmentExperience",
    "EnvironmentExperienceBuildInput",
    "EnvironmentExperienceBuildOutput",
    "EnvironmentExperienceCreateProfileConfigInput",
    "EnvironmentExperienceCreateProfileConfigOutput",
    "EnvironmentExperienceCreateProfileInput",
    "EnvironmentExperienceCreateProfileOutput",
    "EnvironmentExperienceCreateTopologySeedInput",
    "EnvironmentExperienceCreateTopologySeedOutput",
    "EnvironmentExperienceStartSessionInput",
    "EnvironmentExperienceStartSessionOutput",
    "FUNCTIONS",
]
