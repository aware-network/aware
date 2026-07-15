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

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_experience_ontology.session.experience_session import ExperienceSession


class InterfaceSessionExperienceSession(ORMModel):
    """
    InterfaceSession-owned portal to one committed ExperienceSession.
    Contract:
    - Interface owns only the mount/provenance row.
    - Experience owns ExperienceSession and all profile, Environment, lens,
    action, and downstream Attention resolution state.
    - One InterfaceSession may mount many ExperienceSessions.
    - The same ExperienceSession may be mounted by other InterfaceSessions.
    """

    # Relationships
    experience_session: ExperienceSession | None = Field(default=None)

    # Attributes
    status: str = Field(default="active")
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)

    # Foreign Keys
    interface_session_id: UUID = Field(description="Foreign key for InterfaceSession.experience_sessions")
    experience_session_id: UUID = Field(
        description="Foreign key for InterfaceSessionExperienceSession.experience_session"
    )

    @classmethod
    async def build_via_interface_session(
        cls,
        interface_session_id: UUID,
        experience_session_id: UUID,
        status: str = "active",
        metadata_json: JsonObject | None = {},
    ) -> InterfaceSessionExperienceSession:
        """
        Construct one InterfaceSession -> ExperienceSession portal row.

        Stable identity is InterfaceSession plus ExperienceSession. The target
        remains Experience-owned and no active-selection semantics are added.
        """

        payload = {
            "interface_session_id": interface_session_id,
            "experience_session_id": experience_session_id,
            "status": status,
            "metadata_json": metadata_json,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_interface_session", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, InterfaceSessionExperienceSession):
            return value
        return InterfaceSessionExperienceSession.validate_invocation_value(value)


class InterfaceSessionExperienceSessionBuildViaInterfaceSessionInput(BaseModel):
    interface_session_id: UUID = Field(description="Foreign key for InterfaceSession.experience_sessions")
    experience_session_id: UUID
    status: str = Field(default="active")
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class InterfaceSessionExperienceSessionBuildViaInterfaceSessionOutput(BaseModel):
    value: InterfaceSessionExperienceSession


FUNCTIONS = {
    "InterfaceSessionExperienceSession": {
        "build_via_interface_session": {
            "canonical": {
                "name": "build_via_interface_session",
                "description": "Construct one InterfaceSession -> ExperienceSession portal row.\n\nStable identity is InterfaceSession plus ExperienceSession. The target\nremains Experience-owned and no active-selection semantics are added.",
                "is_constructor": True,
            },
            "input": InterfaceSessionExperienceSessionBuildViaInterfaceSessionInput,
            "output": InterfaceSessionExperienceSessionBuildViaInterfaceSessionOutput,
        },
    },
}

__all__ = [
    "InterfaceSessionExperienceSession",
    "InterfaceSessionExperienceSessionBuildViaInterfaceSessionInput",
    "InterfaceSessionExperienceSessionBuildViaInterfaceSessionOutput",
    "FUNCTIONS",
]
