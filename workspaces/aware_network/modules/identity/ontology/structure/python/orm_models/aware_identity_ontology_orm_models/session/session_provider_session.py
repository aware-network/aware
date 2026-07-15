from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_identity_ontology_orm_models.session.session_provider_session_config import SessionProviderSessionConfig
    from aware_meta_ontology_orm_models.class_.class_instance_identity import ClassInstanceIdentity
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_identity import ObjectInstanceGraphIdentity


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
