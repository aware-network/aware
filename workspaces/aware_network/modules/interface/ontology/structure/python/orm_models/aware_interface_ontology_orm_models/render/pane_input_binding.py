from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel


class PaneInputBinding(ORMModel):
    # Attributes
    payload_path: str
    source_node_key: str | None = Field(default=None)
    source_json_path: str | None = Field(default=None)
    literal_value: str | None = Field(default=None)

    # Foreign Keys
    pane_action_binding_id: UUID = Field(description="Foreign key for PaneActionBinding.input_bindings")
