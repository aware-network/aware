from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch


class ProgramBranch(ORMModel):
    # Relationships
    object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None, exclude=True)

    # Attributes
    key: str | None = Field(default=None)
    is_active: bool = Field(default=True)
    view_key: str | None = Field(default=None)

    # Foreign Keys
    program_id: UUID = Field(description="Foreign key for Program.branches")
    object_instance_graph_branch_id: UUID = Field(
        description="Foreign key for ProgramBranch.object_instance_graph_branch"
    )
