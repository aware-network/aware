from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class FunctionCallResponseCommit(ORMModel):
    # Relationships
    object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(
        default=None, description="Association target reference to ObjectInstanceGraphCommit"
    )

    # Attributes
    position: int

    # Foreign Keys
    object_instance_graph_commit_id: UUID = Field(description="Join FK to ObjectInstanceGraphCommit")
    function_call_response_id: UUID = Field(description="Join FK to FunctionCallResponse")
