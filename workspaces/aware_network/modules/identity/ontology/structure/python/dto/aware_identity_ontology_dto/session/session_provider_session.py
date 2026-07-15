from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_identity_ontology_dto.session.session_provider_session_config import SessionProviderSessionConfig
    from aware_meta_ontology_dto.class_.class_instance_identity import ClassInstanceIdentity
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_identity import ObjectInstanceGraphIdentity


class SessionProviderSession(BaseModel):
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
