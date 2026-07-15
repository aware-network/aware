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
    from aware_environment_ontology.environment.environment_session import EnvironmentSession
    from aware_experience_ontology.session.experience_session_profile import ExperienceSessionProfile
    from aware_identity_ontology.session.session import Session


class ExperienceSession(ORMModel):
    """
    Experience-owned committed resolution state for one child Identity Session.
    Contract:
    - Identity Session owns participation, roles, lifecycle, and providers.
    - EnvironmentSession owns shared thread/layout and Attention portals.
    - ExperienceSession owns session-local profile mount rows and local state.
    - Concrete visible/active state remains scoped through Attention and
    Experience view bindings; there is no session-global active projection.
    """

    # Relationships
    identity_session: Session | None = Field(default=None)
    environment_session: EnvironmentSession | None = Field(default=None)
    profiles: list[ExperienceSessionProfile] = Field(default_factory=list)

    # Attributes
    state: ExperienceSessionState

    # Foreign Keys
    environment_experience_id: UUID = Field(description="Foreign key for EnvironmentExperience.sessions")
    identity_session_id: UUID = Field(description="Foreign key for ExperienceSession.identity_session")
    environment_session_id: UUID = Field(description="Foreign key for ExperienceSession.environment_session")

    async def mount_profile(
        self, profile_id: UUID, status: str = "active", metadata_json: JsonObject | None = {}
    ) -> ExperienceSessionProfile:
        """
        Mount one applied Experience profile into this session.

        Contract:
        - Stable identity is ExperienceSession plus applied profile.
        - Many applied profiles may be mounted in one ExperienceSession.
        - Mounting does not select a global active profile or projection.
        """

        payload = {"profile_id": profile_id, "status": status, "metadata_json": metadata_json}
        result = await invoke_instance(orm_model=self, function_name="mount_profile", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.session.experience_session_profile import ExperienceSessionProfile

        if isinstance(value, ExperienceSessionProfile):
            return value
        return ExperienceSessionProfile.validate_invocation_value(value)

    @classmethod
    async def build_via_environment_experience(
        cls,
        environment_experience_id: UUID,
        identity_session_id: UUID,
        environment_session_id: UUID,
        state: ExperienceSessionState = ExperienceSessionState.active,
    ) -> ExperienceSession:
        """
        Construct one Experience session under EnvironmentExperience.

        Stable identity is EnvironmentExperience plus child Identity Session.
        Replaying the same child Identity Session resolves the same committed
        Experience session instead of creating a second authority.
        """

        payload = {
            "environment_experience_id": environment_experience_id,
            "identity_session_id": identity_session_id,
            "environment_session_id": environment_session_id,
            "state": state,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_environment_experience", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ExperienceSession):
            return value
        return ExperienceSession.validate_invocation_value(value)


class ExperienceSessionMountProfileInput(BaseModel):
    profile_id: UUID
    status: str = Field(default="active")
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class ExperienceSessionMountProfileOutput(BaseModel):
    value: ExperienceSessionProfile


class ExperienceSessionBuildViaEnvironmentExperienceInput(BaseModel):
    environment_experience_id: UUID = Field(description="Foreign key for EnvironmentExperience.sessions")
    identity_session_id: UUID
    environment_session_id: UUID
    state: ExperienceSessionState = Field(default=ExperienceSessionState.active)


class ExperienceSessionBuildViaEnvironmentExperienceOutput(BaseModel):
    value: ExperienceSession


FUNCTIONS = {
    "ExperienceSession": {
        "mount_profile": {
            "canonical": {
                "name": "mount_profile",
                "description": "Mount one applied Experience profile into this session.\n\nContract:\n- Stable identity is ExperienceSession plus applied profile.\n- Many applied profiles may be mounted in one ExperienceSession.\n- Mounting does not select a global active profile or projection.",
                "is_constructor": False,
            },
            "input": ExperienceSessionMountProfileInput,
            "output": ExperienceSessionMountProfileOutput,
        },
        "build_via_environment_experience": {
            "canonical": {
                "name": "build_via_environment_experience",
                "description": "Construct one Experience session under EnvironmentExperience.\n\nStable identity is EnvironmentExperience plus child Identity Session.\nReplaying the same child Identity Session resolves the same committed\nExperience session instead of creating a second authority.",
                "is_constructor": True,
            },
            "input": ExperienceSessionBuildViaEnvironmentExperienceInput,
            "output": ExperienceSessionBuildViaEnvironmentExperienceOutput,
        },
    },
}

__all__ = [
    "ExperienceSession",
    "ExperienceSessionMountProfileInput",
    "ExperienceSessionMountProfileOutput",
    "ExperienceSessionBuildViaEnvironmentExperienceInput",
    "ExperienceSessionBuildViaEnvironmentExperienceOutput",
    "FUNCTIONS",
]
