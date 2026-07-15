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
    from aware_identity_ontology.session.session_provider_session_config import SessionProviderSessionConfig
    from aware_meta_ontology.class_.class_instance_identity import ClassInstanceIdentity
    from aware_meta_ontology.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch
    from aware_meta_ontology.graph.instance.object_instance_graph_identity import ObjectInstanceGraphIdentity


class SessionProviderSession(ORMModel):
    """
    Concrete provider capability attached to one shared Identity Session.
    Contract:
    - Parent constructor is Session.
    - Points to SessionProviderSessionConfig for provider/config eligibility.
    - Provider-specific object state is referenced through generic Meta graph
    portals and/or an opaque bridge ref.
    - Identity does not import Environment, Conversation, Workflow, Workspace,
    Attention, or provider service ontology.
    """

    # Relationships
    provider_session_config: SessionProviderSessionConfig | None = Field(default=None)
    provider_object_instance_graph_identity: ObjectInstanceGraphIdentity | None = Field(default=None)
    provider_class_instance_identity: ClassInstanceIdentity | None = Field(default=None)
    provider_object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None)

    # Attributes
    provider_session_key: str
    provider_session_ref: str | None = Field(default=None)
    status: str = Field(default="active")
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)

    # Foreign Keys
    session_id: UUID = Field(description="Foreign key for Session.provider_sessions")
    provider_session_config_id: UUID = Field(
        description="Foreign key for SessionProviderSession.provider_session_config"
    )
    provider_object_instance_graph_identity_id: UUID | None = Field(
        default=None, description="Foreign key for SessionProviderSession.provider_object_instance_graph_identity"
    )
    provider_class_instance_identity_id: UUID | None = Field(
        default=None, description="Foreign key for SessionProviderSession.provider_class_instance_identity"
    )
    provider_object_instance_graph_branch_id: UUID | None = Field(
        default=None, description="Foreign key for SessionProviderSession.provider_object_instance_graph_branch"
    )

    @classmethod
    async def create_via_session(
        cls,
        session_id: UUID,
        provider_session_config_id: UUID,
        provider_session_key: str,
        provider_session_ref: str | None = None,
        provider_object_instance_graph_identity_id: UUID | None = None,
        provider_class_instance_identity_id: UUID | None = None,
        provider_object_instance_graph_branch_id: UUID | None = None,
        status: str = "active",
        metadata_json: JsonObject | None = {},
    ) -> SessionProviderSession:
        """
        Attach one concrete provider capability to the parent Identity Session.

        Contract:
        - Stable identity is `(session_id, provider_session_config_id,
          provider_session_key)`.
        - This is not session ownership; many provider sessions may attach to
          one Identity Session.
        """

        payload = {
            "session_id": session_id,
            "provider_session_config_id": provider_session_config_id,
            "provider_session_key": provider_session_key,
            "provider_session_ref": provider_session_ref,
            "provider_object_instance_graph_identity_id": provider_object_instance_graph_identity_id,
            "provider_class_instance_identity_id": provider_class_instance_identity_id,
            "provider_object_instance_graph_branch_id": provider_object_instance_graph_branch_id,
            "status": status,
            "metadata_json": metadata_json,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_session", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SessionProviderSession):
            return value
        return SessionProviderSession.validate_invocation_value(value)


class SessionProviderSessionCreateViaSessionInput(BaseModel):
    session_id: UUID = Field(description="Foreign key for Session.provider_sessions")
    provider_session_config_id: UUID
    provider_session_key: str
    provider_session_ref: str | None = Field(default=None)
    provider_object_instance_graph_identity_id: UUID | None = Field(default=None)
    provider_class_instance_identity_id: UUID | None = Field(default=None)
    provider_object_instance_graph_branch_id: UUID | None = Field(default=None)
    status: str = Field(default="active")
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class SessionProviderSessionCreateViaSessionOutput(BaseModel):
    value: SessionProviderSession


FUNCTIONS = {
    "SessionProviderSession": {
        "create_via_session": {
            "canonical": {
                "name": "create_via_session",
                "description": "Attach one concrete provider capability to the parent Identity Session.\n\nContract:\n- Stable identity is `(session_id, provider_session_config_id,\n  provider_session_key)`.\n- This is not session ownership; many provider sessions may attach to\n  one Identity Session.",
                "is_constructor": True,
            },
            "input": SessionProviderSessionCreateViaSessionInput,
            "output": SessionProviderSessionCreateViaSessionOutput,
        },
    },
}

__all__ = [
    "SessionProviderSession",
    "SessionProviderSessionCreateViaSessionInput",
    "SessionProviderSessionCreateViaSessionOutput",
    "FUNCTIONS",
]
